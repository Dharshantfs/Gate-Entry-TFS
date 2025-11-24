# Copyright (c) 2025, Gurudatt Kulkarni and Contributors
# See license.txt


from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from gate_entry.gate_entry.doctype.gate_pass.gate_pass import (
	GatePass,
	get_delivery_note_items,
	get_sales_invoice_items,
)


class TestGatePass(FrappeTestCase):
	def test_sales_invoice_items_exclude_financial_fields(self):
		with patch("gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_doc") as get_doc:
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
		with patch("gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_doc") as get_doc:
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

	def test_manual_return_flow_preserves_received_quantities(self):
		gate_pass = frappe.new_doc("Gate Pass")
		gate_pass.document_reference = "Stock Entry"
		gate_pass.reference_number = "STE-OUT-001"
		gate_pass.manual_return_flow = 1
		gate_pass.entry_type = "Gate In"

		item_row = frappe._dict(
			name="STE-OUT-ITEM-1",
			item_code="ITEM-001",
			item_name="Widget",
			description="",
			uom="Nos",
			stock_uom="Nos",
			conversion_factor=1,
			qty=5,
			transfer_qty=5,
			s_warehouse="Stores - CO",
			t_warehouse=None,
			cost_center=None,
			project=None,
			basic_rate=100,
			basic_amount=500,
		)
		stock_entry = frappe._dict(
			name="STE-OUT-001",
			docstatus=1,
			items=[item_row],
			company="Test Company",
			stock_entry_type="Material Transfer",
			is_return=0,
			return_against=None,
			ge_outbound_reference=None,
		)

		def fake_get_cached(doctype, name):
			if doctype == "Stock Entry" and name == "STE-OUT-001":
				return stock_entry
			raise frappe.DoesNotExistError

		def fake_get_doc(doctype, name):
			if doctype == "Stock Entry" and name == "STE-OUT-001":
				return stock_entry
			raise frappe.DoesNotExistError

		with (
			patch(
				"gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_cached_doc",
				side_effect=fake_get_cached,
			),
			patch(
				"gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_doc", side_effect=fake_get_doc
			),
			patch("gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_all") as get_all,
			patch("gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.db.get_all") as db_get_all,
		):
			get_all.return_value = []
			db_get_all.return_value = []

			gate_pass.before_validate()
			self.assertEqual(len(gate_pass.gate_pass_table), 1)

			gate_pass.gate_pass_table[0].received_qty = 2
			gate_pass.before_validate()

			self.assertEqual(gate_pass.outbound_material_transfer, "STE-OUT-001")
			self.assertEqual(gate_pass.gate_pass_table[0].received_qty, 2)

			gate_pass.validate()

	def test_get_existing_allocations_considers_outbound_link(self):
		gate_pass = GatePass(frappe._dict(doctype="Gate Pass"))
		gate_pass.name = "GP-TEST-001"

		def fake_get_all(doctype, filters=None, or_filters=None, pluck=None):
			self.assertIn(["Gate Pass", "reference_number", "=", "STE-OUT-001"], or_filters)
			self.assertIn(["Gate Pass", "outbound_material_transfer", "=", "STE-OUT-001"], or_filters)
			return ["GP-OTHER"]

		with (
			patch(
				"gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_all", side_effect=fake_get_all
			),
			patch("gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.db.get_all") as db_get_all,
		):
			db_get_all.return_value = [frappe._dict(order_item_name="STE-OUT-ITEM-1", total=3)]

			result = gate_pass.get_existing_stock_entry_allocations("STE-OUT-001", "Gate In")

		self.assertEqual(result, {"STE-OUT-ITEM-1": 3})
