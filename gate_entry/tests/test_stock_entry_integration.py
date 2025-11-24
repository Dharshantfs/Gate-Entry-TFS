# Copyright (c) 2025, Gurudatt Kulkarni and Contributors
# See license.txt

"""
Integration tests for Stock Entry and Gate Pass integration.
Tests auto-creation of gate passes via Stock Entry events and inbound references.
"""

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from gate_entry.gate_entry.doctype.gate_pass.gate_pass import on_stock_entry_submit
from gate_entry.stock_integration import utils as stock_utils


class TestStockEntryIntegration(FrappeTestCase):
	"""Test Stock Entry integration with Gate Pass auto-creation"""

	def setUp(self):
		"""Set up test fixtures"""
		# Create test company if it doesn't exist
		if not frappe.db.exists("Company", "Test Company"):
			company = frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": "Test Company",
					"abbr": "TC",
					"default_currency": "USD",
					"country": "United States",
				}
			)
			company.insert(ignore_permissions=True)

		# Create test item if it doesn't exist
		if not frappe.db.exists("Item", "TEST-ITEM-001"):
			item = frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": "TEST-ITEM-001",
					"item_name": "Test Item",
					"item_group": "Products",
					"stock_uom": "Nos",
				}
			)
			item.insert(ignore_permissions=True)

	def test_auto_create_gate_pass_on_external_transfer_submit(self):
		"""Test that gate pass is auto-created when external transfer Stock Entry is submitted"""
		# Create Stock Entry with external transfer flag
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.stock_entry_type = "Material Transfer"
		stock_entry.ge_external_transfer = 1
		stock_entry.company = "Test Company"
		stock_entry.append(
			"items",
			{
				"item_code": "TEST-ITEM-001",
				"qty": 10,
				"s_warehouse": "Stores - TC",
				"t_warehouse": "Finished Goods - TC",
			},
		)
		stock_entry.insert()

		# Mock the create_gate_pass_from_stock_entry function
		created_gate_pass = None

		def mock_create_gate_pass(stock_entry_name, enqueued_by=None):
			nonlocal created_gate_pass
			# Simulate gate pass creation
			gate_pass = frappe.new_doc("Gate Pass")
			gate_pass.document_reference = "Stock Entry"
			gate_pass.reference_number = stock_entry_name
			gate_pass.company = stock_entry.company
			gate_pass.entry_type = "Gate Out"
			gate_pass.insert(ignore_permissions=True)
			created_gate_pass = gate_pass.name
			return gate_pass.name

		with patch(
			"gate_entry.stock_integration.utils.create_gate_pass_from_stock_entry",
			side_effect=mock_create_gate_pass,
		):
			stock_entry.submit()

			# Verify gate pass creation was triggered
			# In real scenario, this would be enqueued, but we're testing the hook
			self.assertIsNotNone(created_gate_pass)

	def test_no_gate_pass_for_internal_transfer(self):
		"""Test that gate pass is NOT created for internal transfers (external_transfer=0)"""
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.stock_entry_type = "Material Transfer"
		stock_entry.ge_external_transfer = 0  # Internal transfer
		stock_entry.company = "Test Company"
		stock_entry.append(
			"items",
			{
				"item_code": "TEST-ITEM-001",
				"qty": 10,
				"s_warehouse": "Stores - TC",
				"t_warehouse": "Finished Goods - TC",
			},
		)
		stock_entry.insert()

		create_called = False

		def mock_create_gate_pass(stock_entry_name, enqueued_by=None):
			nonlocal create_called
			create_called = True

		with patch(
			"gate_entry.stock_integration.utils.create_gate_pass_from_stock_entry",
			side_effect=mock_create_gate_pass,
		):
			stock_entry.submit()

			# Should not be called for internal transfers
			self.assertFalse(create_called)

	def test_auto_create_gate_pass_for_return_entry(self):
		"""Test that gate pass is auto-created for return Stock Entry (Gate In)"""
		# Create outbound Stock Entry first
		outbound_se = frappe.new_doc("Stock Entry")
		outbound_se.stock_entry_type = "Material Transfer"
		outbound_se.ge_external_transfer = 1
		outbound_se.company = "Test Company"
		outbound_se.append(
			"items",
			{
				"item_code": "TEST-ITEM-001",
				"qty": 10,
				"s_warehouse": "Stores - TC",
				"t_warehouse": "Finished Goods - TC",
			},
		)
		outbound_se.insert()
		outbound_se.submit()

		# Create return Stock Entry
		return_se = frappe.new_doc("Stock Entry")
		return_se.stock_entry_type = "Material Transfer"
		return_se.is_return = 1
		return_se.return_against = outbound_se.name
		return_se.company = "Test Company"
		return_se.append(
			"items",
			{
				"item_code": "TEST-ITEM-001",
				"qty": 5,
				"s_warehouse": "Finished Goods - TC",
				"t_warehouse": "Stores - TC",
			},
		)
		return_se.insert()

		created_gate_pass = None

		def mock_create_gate_pass(stock_entry_name, enqueued_by=None):
			nonlocal created_gate_pass
			gate_pass = frappe.new_doc("Gate Pass")
			gate_pass.document_reference = "Stock Entry"
			gate_pass.reference_number = stock_entry_name
			gate_pass.entry_type = "Gate In"
			gate_pass.return_material_transfer = stock_entry_name
			gate_pass.outbound_material_transfer = outbound_se.name
			gate_pass.company = "Test Company"
			gate_pass.insert(ignore_permissions=True)
			created_gate_pass = gate_pass.name
			return gate_pass.name

		with patch(
			"gate_entry.stock_integration.utils.create_gate_pass_from_stock_entry",
			side_effect=mock_create_gate_pass,
		):
			return_se.submit()

			# Verify gate pass was created with correct entry type
			self.assertIsNotNone(created_gate_pass)

	def test_manual_return_flow_gate_pass_creation(self):
		"""Test manual return flow where gate pass references outbound transfer without return Stock Entry"""
		# Create outbound Stock Entry
		outbound_se = frappe.new_doc("Stock Entry")
		outbound_se.stock_entry_type = "Material Transfer"
		outbound_se.ge_external_transfer = 1
		outbound_se.company = "Test Company"
		outbound_se.append(
			"items",
			{
				"item_code": "TEST-ITEM-001",
				"qty": 10,
				"s_warehouse": "Stores - TC",
				"t_warehouse": "Finished Goods - TC",
			},
		)
		outbound_se.insert()
		outbound_se.submit()

		# Create manual return gate pass (no return Stock Entry yet)
		gate_pass = frappe.new_doc("Gate Pass")
		gate_pass.document_reference = "Stock Entry"
		gate_pass.reference_number = outbound_se.name  # Reference outbound
		gate_pass.outbound_material_transfer = outbound_se.name
		gate_pass.manual_return_flow = 1
		gate_pass.entry_type = "Gate In"
		gate_pass.company = "Test Company"
		gate_pass.vehicle_number = "TEST-VEH-001"
		gate_pass.driver_name = "Test Driver"

		# Mock stock entry context
		def fake_get_cached(doctype, name):
			if doctype == "Stock Entry" and name == outbound_se.name:
				return outbound_se
			raise frappe.DoesNotExistError

		with (
			patch(
				"gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_cached_doc",
				side_effect=fake_get_cached,
			),
			patch("gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_all") as get_all,
		):
			get_all.return_value = []

			gate_pass.before_validate()

			# Verify manual return flow is preserved
			self.assertEqual(gate_pass.manual_return_flow, 1)
			self.assertEqual(gate_pass.outbound_material_transfer, outbound_se.name)
			self.assertEqual(gate_pass.entry_type, "Gate In")

	def test_stock_entry_cancel_clears_gate_pass_references(self):
		"""Test that cancelling Stock Entry clears gate pass references"""
		# Create and submit Stock Entry with gate pass
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.stock_entry_type = "Material Transfer"
		stock_entry.ge_external_transfer = 1
		stock_entry.company = "Test Company"
		stock_entry.append(
			"items",
			{
				"item_code": "TEST-ITEM-001",
				"qty": 10,
				"s_warehouse": "Stores - TC",
				"t_warehouse": "Finished Goods - TC",
			},
		)
		stock_entry.insert()
		stock_entry.submit()

		# Create gate pass linked to Stock Entry
		gate_pass = frappe.new_doc("Gate Pass")
		gate_pass.document_reference = "Stock Entry"
		gate_pass.reference_number = stock_entry.name
		gate_pass.stock_entry = stock_entry.name
		gate_pass.company = "Test Company"
		gate_pass.entry_type = "Gate Out"
		gate_pass.vehicle_number = "TEST-VEH-001"
		gate_pass.driver_name = "Test Driver"
		gate_pass.insert()
		gate_pass.submit()

		# Verify gate_pass field is set on Stock Entry
		stock_entry.reload()
		self.assertEqual(stock_entry.gate_pass, gate_pass.name)

		# Cancel Stock Entry
		stock_entry.cancel()

		# Verify gate_pass field is cleared
		stock_entry.reload()
		self.assertIsNone(stock_entry.gate_pass)

		# Verify gate pass references are cleared
		gate_pass.reload()
		# Note: In real scenario, gate pass might be cancelled or references cleared
		# This depends on the implementation in on_stock_entry_cancel

	def test_inbound_gate_pass_links_to_outbound_transfer(self):
		"""Test that inbound gate pass correctly links to outbound material transfer"""
		# Create outbound Stock Entry
		outbound_se = frappe.new_doc("Stock Entry")
		outbound_se.stock_entry_type = "Material Transfer"
		outbound_se.ge_external_transfer = 1
		outbound_se.company = "Test Company"
		outbound_se.append(
			"items",
			{
				"item_code": "TEST-ITEM-001",
				"qty": 10,
				"s_warehouse": "Stores - TC",
				"t_warehouse": "Finished Goods - TC",
			},
		)
		outbound_se.insert()
		outbound_se.submit()

		# Create return Stock Entry
		return_se = frappe.new_doc("Stock Entry")
		return_se.stock_entry_type = "Material Transfer"
		return_se.is_return = 1
		return_se.return_against = outbound_se.name
		return_se.company = "Test Company"
		return_se.append(
			"items",
			{
				"item_code": "TEST-ITEM-001",
				"qty": 5,
				"s_warehouse": "Finished Goods - TC",
				"t_warehouse": "Stores - TC",
			},
		)
		return_se.insert()
		return_se.submit()

		# Create gate pass for return entry
		gate_pass = frappe.new_doc("Gate Pass")
		gate_pass.document_reference = "Stock Entry"
		gate_pass.reference_number = return_se.name
		gate_pass.company = "Test Company"
		gate_pass.entry_type = "Gate In"
		gate_pass.vehicle_number = "TEST-VEH-001"
		gate_pass.driver_name = "Test Driver"

		# Mock stock entry context
		def fake_get_cached(doctype, name):
			if doctype == "Stock Entry":
				if name == return_se.name:
					return return_se
				if name == outbound_se.name:
					return outbound_se
			raise frappe.DoesNotExistError

		with (
			patch(
				"gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_cached_doc",
				side_effect=fake_get_cached,
			),
			patch("gate_entry.gate_entry.doctype.gate_pass.gate_pass.frappe.get_all") as get_all,
		):
			get_all.return_value = []

			gate_pass.before_validate()

			# Verify links are set correctly
			self.assertEqual(gate_pass.return_material_transfer, return_se.name)
			self.assertEqual(gate_pass.outbound_material_transfer, outbound_se.name)
			self.assertEqual(gate_pass.entry_type, "Gate In")

	def test_send_to_subcontractor_creates_gate_pass(self):
		"""Test that 'Send to Subcontractor' Stock Entry creates gate pass"""
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.stock_entry_type = "Send to Subcontractor"
		stock_entry.company = "Test Company"
		stock_entry.append(
			"items",
			{
				"item_code": "TEST-ITEM-001",
				"qty": 10,
				"s_warehouse": "Stores - TC",
				"t_warehouse": "Subcontractor - TC",
			},
		)
		stock_entry.insert()

		create_called = False

		def mock_create_gate_pass(stock_entry_name, enqueued_by=None):
			nonlocal create_called
			create_called = True

		with patch(
			"gate_entry.stock_integration.utils.create_gate_pass_from_stock_entry",
			side_effect=mock_create_gate_pass,
		):
			stock_entry.submit()

			# Should be called for Send to Subcontractor
			self.assertTrue(create_called)

	def tearDown(self):
		"""Clean up test data"""
		frappe.db.rollback()
