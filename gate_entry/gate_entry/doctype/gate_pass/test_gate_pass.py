# Copyright (c) 2025, Gurudatt Kulkarni and Contributors
# See license.txt


from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import cint

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

	def test_multi_pass_allocation_partial_quantities(self):
		"""Test that multiple gate passes can allocate partial quantities from same stock entry"""
		gate_pass1 = GatePass(frappe._dict(doctype="Gate Pass"))
		gate_pass1.name = "GP-001"

		gate_pass2 = GatePass(frappe._dict(doctype="Gate Pass"))
		gate_pass2.name = "GP-002"

		# Mock existing allocations: GP-001 already allocated 3 units
		def fake_get_all(doctype, filters=None, or_filters=None, pluck=None):
			if pluck:
				return ["GP-001"]  # Existing gate pass
			return ["GP-001"]

		def fake_db_get_all(*args, **kwargs):
			# First call: existing allocations from GP-001
			# Second call: updated allocations including GP-002
			if not hasattr(fake_db_get_all, "call_count"):
				fake_db_get_all.call_count = 0
			fake_db_get_all.call_count += 1

			if fake_db_get_all.call_count == 1:
				return [frappe._dict(order_item_name="STE-ITEM-1", total=3)]
			else:
				return [frappe._dict(order_item_name="STE-ITEM-1", total=5)]

		with (
			patch(
				"gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_all", side_effect=fake_get_all
			),
			patch("gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.db.get_all") as db_get_all,
		):
			db_get_all.side_effect = fake_db_get_all

			# First gate pass allocated 3 units
			result1 = gate_pass1.get_existing_stock_entry_allocations("STE-001", "Gate Out")
			self.assertEqual(result1, {"STE-ITEM-1": 3})

			# Second gate pass should see existing 3 units and can allocate remaining
			result2 = gate_pass2.get_existing_stock_entry_allocations("STE-001", "Gate Out")
			self.assertEqual(result2, {"STE-ITEM-1": 3})

	def test_multi_pass_allocation_exceeds_balance(self):
		"""Test that gate pass validation prevents over-allocation across multiple passes"""
		stock_entry = frappe._dict(
			name="STE-001",
			docstatus=1,
			items=[
				frappe._dict(
					name="STE-ITEM-1",
					item_code="ITEM-001",
					qty=10,
					transfer_qty=10,
				)
			],
			company="Test Company",
			stock_entry_type="Material Transfer",
		)

		gate_pass = frappe.new_doc("Gate Pass")
		gate_pass.document_reference = "Stock Entry"
		gate_pass.reference_number = "STE-001"
		gate_pass.company = "Test Company"
		gate_pass.entry_type = "Gate Out"

		# Mock existing allocation of 8 units
		def fake_get_all(doctype, filters=None, or_filters=None, pluck=None):
			return ["GP-EXISTING"]

		def fake_db_get_all(*args, **kwargs):
			return [frappe._dict(order_item_name="STE-ITEM-1", total=8)]

		def fake_get_cached(doctype, name):
			if doctype == "Stock Entry" and name == "STE-001":
				return stock_entry
			raise frappe.DoesNotExistError

		with (
			patch(
				"gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_cached_doc",
				side_effect=fake_get_cached,
			),
			patch(
				"gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_all", side_effect=fake_get_all
			),
			patch("gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.db.get_all") as db_get_all,
		):
			db_get_all.side_effect = fake_db_get_all

			gate_pass.before_validate()
			# Try to allocate 5 units when only 2 remain (10 - 8 = 2)
			gate_pass.gate_pass_table[0].dispatched_qty = 5
			gate_pass.gate_pass_table[0].order_item_name = "STE-ITEM-1"

			# Should raise validation error
			with self.assertRaises(frappe.ValidationError) as context:
				gate_pass.validate()

			self.assertIn("exceeds remaining balance", str(context.exception))

	def test_discrepancy_logging_validation(self):
		"""Test discrepancy quantity validation"""
		gate_pass = frappe.new_doc("Gate Pass")
		gate_pass.document_reference = "Stock Entry"
		gate_pass.reference_number = "STE-001"
		gate_pass.company = "Test Company"
		gate_pass.entry_type = "Gate In"
		gate_pass.has_discrepancy = 1

		# Add item with received quantity
		gate_pass.append(
			"gate_pass_table",
			{
				"item_code": "ITEM-001",
				"received_qty": 10,
				"dispatched_qty": 0,
			},
		)

		# Test: Lost + Damaged cannot exceed total quantity
		gate_pass.lost_quantity = 6
		gate_pass.damaged_quantity = 5  # Total = 11, exceeds 10

		with self.assertRaises(frappe.ValidationError) as context:
			gate_pass.validate_discrepancy_quantities()

		self.assertIn("cannot exceed movement quantity", str(context.exception))

		# Test: Negative quantities not allowed
		gate_pass.lost_quantity = -1
		gate_pass.damaged_quantity = 0

		with self.assertRaises(frappe.ValidationError) as context:
			gate_pass.validate_discrepancy_quantities()

		self.assertIn("cannot be negative", str(context.exception))

		# Test: Valid discrepancy
		gate_pass.lost_quantity = 3
		gate_pass.damaged_quantity = 2  # Total = 5, within 10
		gate_pass.validate_discrepancy_quantities()  # Should not raise

	def test_discrepancy_fields_cleanup(self):
		"""Test that discrepancy fields are cleared when has_discrepancy is unchecked"""
		gate_pass = frappe.new_doc("Gate Pass")
		gate_pass.has_discrepancy = 1
		gate_pass.lost_quantity = 5
		gate_pass.damaged_quantity = 3
		gate_pass.discrepancy_notes = "Test notes"

		# Uncheck discrepancy
		gate_pass.has_discrepancy = 0
		gate_pass.cleanup_discrepancy_fields()

		self.assertEqual(gate_pass.lost_quantity, 0)
		self.assertEqual(gate_pass.damaged_quantity, 0)
		self.assertIsNone(gate_pass.discrepancy_notes)

	def test_cancel_clears_stock_entry_reference(self):
		"""Test that cancelling gate pass clears Stock Entry reference"""
		gate_pass = frappe.new_doc("Gate Pass")
		gate_pass.document_reference = "Stock Entry"
		gate_pass.reference_number = "STE-001"
		gate_pass.stock_entry = "STE-001"
		gate_pass.company = "Test Company"
		gate_pass.entry_type = "Gate Out"

		# Mock Stock Entry exists
		def fake_db_exists(doctype, name):
			return doctype == "Stock Entry" and name == "STE-001"

		def fake_db_get_value(doctype, name, field):
			if doctype == "Stock Entry" and name == "STE-001" and field == "gate_pass":
				return "GP-001"
			return None

		def fake_db_set_value(doctype, name, field, value, **kwargs):
			# Verify that gate_pass field is cleared
			if doctype == "Stock Entry" and name == "STE-001" and field == "gate_pass":
				self.assertIsNone(value)

		with (
			patch(
				"gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.db.exists",
				side_effect=fake_db_exists,
			),
			patch(
				"gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.db.get_value",
				side_effect=fake_db_get_value,
			),
			patch(
				"gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.db.set_value",
				side_effect=fake_db_set_value,
			),
		):
			gate_pass.name = "GP-001"
			gate_pass.clear_stock_entry_reference()

	def test_cancel_manual_return_flow_clears_references(self):
		"""Test that cancelling manual return flow gate pass clears outbound_material_transfer"""
		gate_pass = frappe.new_doc("Gate Pass")
		gate_pass.document_reference = "Stock Entry"
		gate_pass.reference_number = "STE-OUT-001"
		gate_pass.outbound_material_transfer = "STE-OUT-001"
		gate_pass.manual_return_flow = 1
		gate_pass.entry_type = "Gate In"
		gate_pass.company = "Test Company"
		gate_pass.name = "GP-001"

		# Mock on_cancel behavior
		def fake_db_set(doctype, name, field, value, **kwargs):
			if doctype == "Gate Pass" and name == "GP-001":
				if field == "outbound_material_transfer":
					self.assertIsNone(value)
				elif field == "reference_number":
					self.assertIsNone(value)

		with patch("gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.db.set_value") as db_set:
			# Simulate on_cancel behavior for manual return flow
			if (
				cint(gate_pass.manual_return_flow) == 1
				and gate_pass.entry_type == "Gate In"
				and not gate_pass.return_material_transfer
				and gate_pass.document_reference == "Stock Entry"
			):
				gate_pass.db_set("outbound_material_transfer", None, update_modified=False)
				gate_pass.db_set("reference_number", None, update_modified=False)

			# Verify db_set was called with None values
			calls = [call for call in db_set.call_args_list if call[0][2] is None]
			self.assertGreater(len(calls), 0)
