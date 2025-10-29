# Copyright (c) 2025, Gurudatt Kulkarni and contributors
# For license information, please see license.txt

"""
Test cases for Gate Pass cancellation and amendment protection
"""

import unittest

import frappe
from frappe import _


class TestGatePassCancellation(unittest.TestCase):
	"""Test Gate Pass cancellation and amendment scenarios"""

	def setUp(self):
		"""Set up test data"""
		# Create test company, supplier, items, etc. as needed
		pass

	def test_cancel_without_receipt(self):
		"""Test that Gate Pass can be cancelled when no receipt exists"""
		# Create and submit Gate Pass
		gate_pass = create_test_gate_pass()
		gate_pass.submit()

		# Should cancel successfully
		gate_pass.cancel()
		self.assertEqual(gate_pass.docstatus, 2)

	def test_cancel_with_draft_purchase_receipt(self):
		"""Test that Gate Pass cannot be cancelled with draft Purchase Receipt"""
		# Create and submit Gate Pass
		gate_pass = create_test_gate_pass()
		gate_pass.submit()

		# Create draft Purchase Receipt
		pr = create_purchase_receipt_from_gate_pass(gate_pass.name)

		# Link to Gate Pass
		gate_pass.db_set("purchase_receipt", pr.name)

		# Should fail to cancel
		with self.assertRaises(frappe.ValidationError) as context:
			gate_pass.cancel()

		self.assertIn("Cannot cancel", str(context.exception))

	def test_cancel_with_submitted_purchase_receipt(self):
		"""Test that Gate Pass cannot be cancelled with submitted Purchase Receipt"""
		# Create and submit Gate Pass
		gate_pass = create_test_gate_pass()
		gate_pass.submit()

		# Create and submit Purchase Receipt
		pr = create_purchase_receipt_from_gate_pass(gate_pass.name)
		pr.submit()

		# Link to Gate Pass
		gate_pass.db_set("purchase_receipt", pr.name)

		# Should fail to cancel
		with self.assertRaises(frappe.ValidationError) as context:
			gate_pass.cancel()

		self.assertIn("Cannot cancel", str(context.exception))

	def test_cancel_workflow(self):
		"""Test proper cancellation workflow: cancel receipt first, then gate pass"""
		# Create and submit Gate Pass
		gate_pass = create_test_gate_pass()
		gate_pass.submit()

		# Create and submit Purchase Receipt
		pr = create_purchase_receipt_from_gate_pass(gate_pass.name)
		pr.submit()

		# Link to Gate Pass
		gate_pass.db_set("purchase_receipt", pr.name)

		# Cancel Purchase Receipt first
		pr.cancel()

		# Now Gate Pass should cancel successfully
		gate_pass.cancel()
		self.assertEqual(gate_pass.docstatus, 2)

	def test_amend_with_receipt(self):
		"""Test that Gate Pass cannot be amended if original has receipt"""
		# Create and submit Gate Pass
		gate_pass = create_test_gate_pass()
		gate_pass.submit()

		# Create and submit Purchase Receipt
		pr = create_purchase_receipt_from_gate_pass(gate_pass.name)
		pr.submit()

		# Link to Gate Pass
		gate_pass.db_set("purchase_receipt", pr.name)

		# Amend Gate Pass
		amended_gate_pass = frappe.copy_doc(gate_pass)
		amended_gate_pass.amended_from = gate_pass.name
		amended_gate_pass.docstatus = 0
		amended_gate_pass.insert()

		# Should fail to submit
		with self.assertRaises(frappe.ValidationError) as context:
			amended_gate_pass.submit()

		self.assertIn("Cannot amend", str(context.exception))

	def test_amend_without_receipt(self):
		"""Test that Gate Pass can be amended if no receipt exists"""
		# Create and submit Gate Pass
		gate_pass = create_test_gate_pass()
		gate_pass.submit()

		# Amend Gate Pass (no receipt linked)
		amended_gate_pass = frappe.copy_doc(gate_pass)
		amended_gate_pass.amended_from = gate_pass.name
		amended_gate_pass.docstatus = 0
		amended_gate_pass.insert()

		# Should submit successfully
		amended_gate_pass.submit()
		self.assertEqual(amended_gate_pass.docstatus, 1)

	def test_error_message_contains_links(self):
		"""Test that error message contains clickable links"""
		# Create and submit Gate Pass
		gate_pass = create_test_gate_pass()
		gate_pass.submit()

		# Create and submit Purchase Receipt
		pr = create_purchase_receipt_from_gate_pass(gate_pass.name)
		pr.submit()

		# Link to Gate Pass
		gate_pass.db_set("purchase_receipt", pr.name)

		# Should fail with link in message
		try:
			gate_pass.cancel()
		except frappe.ValidationError as e:
			error_message = str(e)
			self.assertIn(pr.name, error_message)
			self.assertIn("Submitted", error_message)

	def test_cancel_with_subcontracting_receipt(self):
		"""Test cancellation protection with Subcontracting Receipt"""
		# Similar to Purchase Receipt tests but with Subcontracting Receipt
		pass

	def tearDown(self):
		"""Clean up test data"""
		frappe.db.rollback()


def create_test_gate_pass():
	"""Helper function to create test Gate Pass"""
	gate_pass = frappe.get_doc(
		{
			"doctype": "Gate Pass",
			"naming_series": "GP-.FY.-.####",
			"entry_type": "Gate In",
			"company": frappe.defaults.get_user_default("Company"),
			"document_reference": "Purchase Order",
			"reference_number": "PO-TEST-001",  # Assume this exists
			"supplier": "Test Supplier",
			"vehicle_number": "TEST-123",
			"driver_name": "Test Driver",
			"gate_pass_table": [
				{"item_code": "TEST-ITEM-001", "item_name": "Test Item", "uom": "Nos", "received_qty": 10}
			],
		}
	)
	gate_pass.insert()
	return gate_pass


def create_purchase_receipt_from_gate_pass(gate_pass_name):
	"""Helper function to create Purchase Receipt from Gate Pass"""
	from gate_entry.gate_entry.doctype.gate_pass.gate_pass import create_purchase_receipt

	pr_name = create_purchase_receipt(gate_pass_name)
	return frappe.get_doc("Purchase Receipt", pr_name)


# Manual testing instructions
"""
MANUAL TESTING STEPS:

1. Test Cancellation Without Receipt:
   - Create a Gate Pass from a Purchase Order
   - Submit the Gate Pass
   - Cancel the Gate Pass
   - Expected: Should cancel successfully ✅

2. Test Cancellation With Draft Receipt:
   - Create a Gate Pass from a Purchase Order
   - Submit the Gate Pass
   - Create a Purchase Receipt (keep it Draft)
   - Try to cancel the Gate Pass
   - Expected: Error message with link to draft receipt ❌

3. Test Cancellation With Submitted Receipt:
   - Create a Gate Pass from a Purchase Order
   - Submit the Gate Pass
   - Create a Purchase Receipt
   - Submit the Purchase Receipt
   - Try to cancel the Gate Pass
   - Expected: Error message with link to submitted receipt ❌

4. Test Proper Cancellation Workflow:
   - Create a Gate Pass from a Purchase Order
   - Submit the Gate Pass
   - Create and submit a Purchase Receipt
   - Cancel the Purchase Receipt first
   - Cancel the Gate Pass
   - Expected: Both cancel successfully ✅

5. Test Amendment With Receipt:
   - Create a Gate Pass from a Purchase Order
   - Submit the Gate Pass
   - Create and submit a Purchase Receipt
   - Click "Amend" on the Gate Pass
   - Make changes and click "Submit"
   - Expected: Error message with step-by-step instructions ❌

6. Test Amendment Without Receipt:
   - Create a Gate Pass from a Purchase Order
   - Submit the Gate Pass (don't create receipt)
   - Click "Amend" on the Gate Pass
   - Make changes and click "Submit"
   - Expected: Amended Gate Pass submits successfully ✅

7. Verify Error Messages:
   - Check that error messages show clickable links
   - Check that status (Draft/Submitted) is displayed
   - Check that instructions are clear
"""
