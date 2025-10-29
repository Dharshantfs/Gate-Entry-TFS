# Copyright (c) 2025, Gurudatt Kulkarni and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
	"""
	Create custom fields after app installation
	Note: This may fail silently if ERPNext is not installed yet.
	Custom fields will be created when setup_custom_fields is run manually.
	"""
	try:
		create_gate_pass_custom_fields()
	except Exception as e:
		# Log error but don't fail installation if ERPNext doctypes don't exist yet
		frappe.log_error(
			message=f"Could not create custom fields during installation: {str(e)!r}\n"
			"This is expected if ERPNext is not installed yet. "
			"Run 'bench execute gate_entry.setup.setup_custom_fields.setup' after ERPNext is installed.",
			title="Gate Entry Installation - Custom Fields Skipped",
		)
		print(
			"Note: Custom fields not created. "
			"Run 'bench execute gate_entry.setup.setup_custom_fields.setup' after ERPNext is installed."
		)


def create_gate_pass_custom_fields():
	"""
	Create custom fields in Purchase Receipt and Subcontracting Receipt
	to link back to Gate Pass

	Note: Gate Pass is added to ignore_links_on_delete in hooks.py,
	which allows Purchase Receipts and Subcontracting Receipts to be deleted
	even when linked to Gate Pass.
	"""
	custom_fields = {
		"Purchase Receipt": [
			{
				"fieldname": "gate_pass",
				"label": "Gate Pass",
				"fieldtype": "Link",
				"options": "Gate Pass",
				"insert_after": "supplier_delivery_note",
				"read_only": 1,
				"no_copy": 1,
				"print_hide": 1,
				"translatable": 0,
			}
		],
		"Subcontracting Receipt": [
			{
				"fieldname": "gate_pass",
				"label": "Gate Pass",
				"fieldtype": "Link",
				"options": "Gate Pass",
				"insert_after": "supplier_delivery_note",
				"read_only": 1,
				"no_copy": 1,
				"print_hide": 1,
				"translatable": 0,
			}
		],
	}

	create_custom_fields(custom_fields, update=True)
	# Manual commit in installation script to ensure fields are saved
	# nosemgrep
	frappe.db.commit()
