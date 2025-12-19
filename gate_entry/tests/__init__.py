# Copyright (c) 2025, Gurudatt Kulkarni and contributors
# For license information, please see license.txt

from functools import partial

import frappe
from erpnext.accounts.utils import get_fiscal_year
from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
from frappe.test_runner import make_test_objects
from frappe.utils import getdate
from frappe.utils.nestedset import get_root_of


def before_tests():
	"""Set up test environment for Gate Entry module."""
	frappe.clear_cache()

	# Set up company if it doesn't exist
	company_name = "Wind Power LLP"
	if not frappe.db.a_row_exists("Company"):
		today = getdate()
		year = today.year if today.month > 3 else today.year - 1

		setup_complete(
			{
				"currency": "INR",
				"full_name": "Test User",
				"company_name": company_name,
				"timezone": "Asia/Kolkata",
				"company_abbr": "WP",
				"industry": "Manufacturing",
				"country": "India",
				"fy_start_date": f"{year}-04-01",
				"fy_end_date": f"{year + 1}-03-31",
				"language": "English",
				"company_tagline": "Testing",
				"email": "test@example.com",
				"password": "test",
				"chart_of_accounts": "Standard",
				"company_gstin": "24AAQCA8719H1ZC",
				"default_gst_rate": "18.0",
				"enable_audit_trail": 0,
			}
		)
	set_default_settings_for_tests()
	create_test_records()
	set_default_company_for_tests()
	frappe.db.commit()
	frappe.clear_cache()
	frappe.flags.country = "India"
	frappe.flags.skip_test_records = True
	frappe.enqueue = partial(frappe.enqueue, now=True)


def set_default_settings_for_tests():
	"""Set default settings required for Gate Entry tests."""
	# Set default groups (like ERPNext and india_compliance)
	for key in ("Customer Group", "Supplier Group", "Item Group", "Territory"):
		frappe.db.set_default(frappe.scrub(key), get_root_of(key))

	# Stock Settings
	frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 1)

	# Ensure default UOM is set (in case ensure_uoms didn't set it)
	if frappe.db.exists("UOM", "Nos"):
		frappe.db.set_single_value("Stock Settings", "stock_uom", "Nos")

	# Enable Sandbox Mode in GST Settings
	if frappe.db.exists("GST Settings"):
		frappe.db.set_single_value("GST Settings", "sandbox_mode", 1)


def create_test_records():
	"""Create test records from test_records.json if it exists."""
	try:
		import os

		test_records_path = frappe.get_app_path("gate_entry", "tests", "test_records.json")
		if os.path.exists(test_records_path):
			test_records = frappe.get_file_json(test_records_path)

			for doctype, data in test_records.items():
				make_test_objects(doctype, data)
				if doctype == "Company":
					add_companies_to_fiscal_year(data)
	except Exception as exc:
		frappe.log_error(
			message=f"Failed to create test records: {exc}",
			title="Gate Entry Test Setup - Test Records",
		)


def set_default_company_for_tests():
	"""Set default company and configure it for tests."""
	company_name = "Wind Power LLP"
	# stock settings
	frappe.db.set_value(
		"Company",
		company_name,
		{
			"enable_perpetual_inventory": 1,
			"default_inventory_account": "Stock In Hand - WP",
			"stock_adjustment_account": "Stock Adjustment - WP",
			"stock_received_but_not_billed": "Stock Received But Not Billed - WP",
		},
	)

	# set default company
	global_defaults = frappe.get_single("Global Defaults")
	global_defaults.default_company = company_name
	global_defaults.save()


def add_companies_to_fiscal_year(data):
	fy = get_fiscal_year(getdate(), as_dict=True)
	doc = frappe.get_doc("Fiscal Year", fy.name)
	fy_companies = [row.company for row in doc.companies]

	for company in data:
		if (company_name := company["company_name"]) not in fy_companies:
			doc.append("companies", {"company": company_name})

	doc.save(ignore_permissions=True)
