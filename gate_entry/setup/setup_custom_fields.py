# Copyright (c) 2025, Gurudatt Kulkarni and contributors
# For license information, please see license.txt

"""
Script to add Gate Pass custom fields to Purchase Receipt and Subcontracting Receipt

Run this script using:
bench execute gate_entry.setup.setup_custom_fields.setup
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def setup():
	"""
	Main function to setup custom fields
	"""
	create_gate_pass_custom_fields()
	print("Gate Pass custom fields created successfully!")


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
				"search_index": 1,
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
				"search_index": 1,
			}
		],
	}

	create_custom_fields(custom_fields, update=True)
	frappe.db.commit()

	print("Custom fields created:")
	print("  - Purchase Receipt: gate_pass field")
	print("  - Subcontracting Receipt: gate_pass field")


if __name__ == "__main__":
	setup()
