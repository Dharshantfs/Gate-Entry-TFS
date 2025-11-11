# Copyright (c) 2025, Gurudatt Kulkarni and Contributors
# See license.txt


from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from gate_entry.gate_entry.doctype.gate_pass.gate_pass import (
	get_delivery_note_items,
	get_sales_invoice_items,
)


class TestGatePass(FrappeTestCase):
	def test_sales_invoice_items_exclude_financial_fields(self):
		with patch(
			"gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_doc"
		) as get_doc:
			item = SimpleNamespace(
				item_code="ITEM-001",
				item_name="Widget",
				description="Sample",
				uom="Nos",
				stock_uom="Nos",
				conversion_factor=1,
				qty=5,
				warehouse="Stores - CO",
				cost_center="Main - CO",
				rate=100,
				amount=500,
				project=None,
				delivery_date=None,
				name="SINV-ITEM-001",
			)
			mock_doc = SimpleNamespace(
				items=[item],
				get=lambda field, default=None: [item] if field == "items" else default,
			)
			get_doc.return_value = mock_doc

			items = get_sales_invoice_items("SINV-0001")

		self.assertEqual(len(items), 1)
		data = items[0]
		self.assertNotIn("rate", data)
		self.assertNotIn("amount", data)
		self.assertEqual(data["dispatched_qty"], 5)
		self.assertEqual(data["warehouse"], "Stores - CO")

	def test_delivery_note_items_exclude_financial_fields(self):
		with patch(
			"gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_doc"
		) as get_doc:
			item = SimpleNamespace(
				item_code="ITEM-002",
				item_name="Gadget",
				description="Sample",
				uom="Nos",
				stock_uom="Nos",
				conversion_factor=1,
				qty=3,
				warehouse="Finished - CO",
				target_warehouse=None,
				cost_center="Main - CO",
				rate=200,
				amount=600,
				project=None,
				schedule_date=None,
				name="DN-ITEM-001",
			)
			mock_doc = SimpleNamespace(
				items=[item],
				get=lambda field, default=None: [item] if field == "items" else default,
			)
			get_doc.return_value = mock_doc

			items = get_delivery_note_items("DN-0001")

		self.assertEqual(len(items), 1)
		data = items[0]
		self.assertNotIn("rate", data)
		self.assertNotIn("amount", data)
		self.assertEqual(data["dispatched_qty"], 3)
		self.assertEqual(data["warehouse"], "Finished - CO")
