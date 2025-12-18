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

	# Ensure Transit Warehouse Type exists (required for Company default warehouses)
	ensure_transit_warehouse_type()

	# Ensure required UOMs exist before creating items
	ensure_uoms()

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
			}
		)
		# Ensure UOMs still exist after setup_complete (it might reset things)
		ensure_uoms()

		add_company_to_fiscal_year(company_name)

	# Enable all roles for admin (like ERPNext does)
	_enable_all_roles_for_admin()

	set_default_settings_for_tests()
	create_test_records()
	set_default_company_for_tests()
	ensure_warehouses_exist()
	frappe.db.commit()
	frappe.clear_cache()

	frappe.flags.skip_test_records = True
	frappe.enqueue = partial(frappe.enqueue, now=True)


def ensure_transit_warehouse_type():
	"""Ensure 'Transit' Warehouse Type exists (required for Company default warehouses)."""
	try:
		frappe.reload_doc("stock", "doctype", "warehouse_type")
		if not frappe.db.exists("Warehouse Type", "Transit"):
			doc = frappe.new_doc("Warehouse Type")
			doc.name = "Transit"
			doc.insert(ignore_permissions=True)
	except Exception as exc:
		frappe.log_error(
			message=f"Failed to create Transit Warehouse Type: {exc}",
			title="Gate Entry Test Setup - Warehouse Type",
		)


def ensure_uoms():
	"""Ensure required Unit of Measures exist before creating test items."""
	required_uoms = ["Nos", "Kg", "Ltr", "Box", "Pcs"]
	default_uom = "Nos"

	try:
		frappe.reload_doc("setup", "doctype", "UOM")
		for uom_name in required_uoms:
			if not frappe.db.exists("UOM", uom_name):
				doc = frappe.get_doc({"doctype": "UOM", "uom_name": uom_name})
				doc.insert(ignore_permissions=True)

		# Verify UOMs were created
		for uom_name in required_uoms:
			if not frappe.db.exists("UOM", uom_name):
				raise Exception(f"Failed to create UOM: {uom_name}")

		# Set default UOM in Stock Settings
		if frappe.db.exists("UOM", default_uom):
			frappe.reload_doc("stock", "doctype", "stock_settings")
			frappe.db.set_single_value("Stock Settings", "stock_uom", default_uom)
	except Exception as exc:
		frappe.log_error(
			message=f"Failed to create UOMs: {exc}",
			title="Gate Entry Test Setup - UOM",
		)
		# Re-raise to prevent silent failures
		raise


def add_company_to_fiscal_year(company_name):
	try:
		# Get the current Fiscal Year (created by setup_complete)
		fy = get_fiscal_year(getdate(), as_dict=True)
		if not fy:
			return

		doc = frappe.get_doc("Fiscal Year", fy.name)
		fy_companies = [row.company for row in doc.companies]

		# Add company if not already present
		if company_name not in fy_companies:
			doc.append("companies", {"company": company_name})
			doc.save(ignore_permissions=True)
	except Exception as exc:
		frappe.log_error(
			message=f"Failed to add company to Fiscal Year: {exc}",
			title="Gate Entry Test Setup - Fiscal Year",
		)
		# Don't re-raise - this is best-effort, but log for debugging


def _enable_all_roles_for_admin():
	"""Enable all roles for Administrator user (like ERPNext does)."""
	try:
		from frappe.desk.page.setup_wizard.setup_wizard import add_all_roles_to

		all_roles = set(frappe.db.get_values("Role", pluck="name"))
		admin_roles = set(
			frappe.db.get_values("Has Role", {"parent": "Administrator"}, fieldname="role", pluck="role")
		)

		if all_roles.difference(admin_roles):
			add_all_roles_to("Administrator")
	except Exception as exc:
		frappe.log_error(
			message=f"Failed to enable all roles for admin: {exc}",
			title="Gate Entry Test Setup - Roles",
		)


def set_default_settings_for_tests():
	"""Set default settings required for Gate Entry tests."""
	# Set default groups (like ERPNext and india_compliance)
	for key in ("Customer Group", "Supplier Group", "Item Group", "Territory"):
		frappe.db.set_default(frappe.scrub(key), get_root_of(key))

	# Stock Settings
	frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 1)
	frappe.db.set_single_value("Stock Settings", "auto_insert_price_list_rate_if_missing", 0)

	# Ensure default UOM is set (in case ensure_uoms didn't set it)
	if frappe.db.exists("UOM", "Nos"):
		frappe.db.set_single_value("Stock Settings", "stock_uom", "Nos")


def create_test_records():
	"""Create test records from test_records.json if it exists."""
	try:
		import os

		test_records_path = frappe.get_app_path("gate_entry", "tests", "test_records.json")
		if os.path.exists(test_records_path):
			test_records = frappe.get_file_json(test_records_path)

			for doctype, data in test_records.items():
				make_test_objects(doctype, data)
	except Exception as exc:
		frappe.log_error(
			message=f"Failed to create test records: {exc}",
			title="Gate Entry Test Setup - Test Records",
		)


def set_default_company_for_tests():
	"""Set default company and configure it for tests."""
	company_name = "Wind Power LLP"
	if frappe.db.exists("Company", company_name):
		# Set default company
		global_defaults = frappe.get_single("Global Defaults")
		global_defaults.default_company = company_name
		global_defaults.save()

		# Configure stock settings for the company
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


def ensure_warehouses_exist():
	"""Ensure default warehouses exist for the test company."""
	company_name = "Wind Power LLP"
	company_abbr = "WP"

	if not frappe.db.exists("Company", company_name):
		return

	try:
		from frappe import _

		# Reload company to trigger on_update which creates warehouses
		company = frappe.get_doc("Company", company_name)

		# Check if any warehouse exists for this company
		existing_warehouses = frappe.db.get_all(
			"Warehouse", filters={"company": company_name}, fields=["name"], limit=1
		)

		# If no warehouses exist, trigger company.on_update() to create default warehouses
		if not existing_warehouses:
			company.flags.ignore_validate = True
			company.save(ignore_permissions=True)

		# Verify warehouses exist, create if missing
		required_warehouses = [
			{"name": "Stores", "is_group": 0},
			{"name": "Finished Goods", "is_group": 0},
			{"name": "Work In Progress", "is_group": 0},
			{"name": "Goods In Transit", "is_group": 0, "warehouse_type": "Transit"},
			{"name": "Subcontractor", "is_group": 0},
		]

		# Get parent warehouse (All Warehouses)
		parent_warehouse = frappe.db.get_value(
			"Warehouse", {"warehouse_name": "All Warehouses", "company": company_name}, "name"
		)

		if not parent_warehouse:
			# Create parent warehouse first
			parent_wh = frappe.get_doc(
				{
					"doctype": "Warehouse",
					"warehouse_name": "All Warehouses",
					"is_group": 1,
					"company": company_name,
				}
			)
			parent_wh.flags.ignore_permissions = True
			parent_wh.flags.ignore_mandatory = True
			parent_wh.insert()
			parent_warehouse = parent_wh.name
		for wh_info in required_warehouses:
			warehouse_full_name = f"{wh_info['name']} - {company_abbr}"
			# Check by full name (with abbreviation) first
			if not frappe.db.exists("Warehouse", warehouse_full_name):
				# Also check by warehouse_name and company
				if not frappe.db.exists(
					"Warehouse", {"warehouse_name": wh_info["name"], "company": company_name}
				):
					warehouse = frappe.get_doc(
						{
							"doctype": "Warehouse",
							"warehouse_name": wh_info["name"],
							"is_group": wh_info.get("is_group", 0),
							"company": company_name,
							"parent_warehouse": parent_warehouse,
							"warehouse_type": wh_info.get("warehouse_type"),
						}
					)
					warehouse.flags.ignore_permissions = True
					warehouse.flags.ignore_mandatory = True
					warehouse.insert(ignore_permissions=True)

	except Exception as exc:
		frappe.log_error(
			message=f"Failed to ensure warehouses exist: {exc}",
			title="Gate Entry Test Setup - Warehouses",
		)
		# Re-raise to make test failures visible
		raise
