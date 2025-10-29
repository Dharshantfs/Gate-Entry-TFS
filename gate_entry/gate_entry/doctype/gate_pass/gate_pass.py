# Copyright (c) 2025, Gurudatt Kulkarni and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate, nowtime


class GatePass(Document):
	def before_save(self):
		"""
		Auto-populate fields before saving
		"""
		# Auto-populate security guard name with current user
		if not self.security_guard_name:
			user_fullname = frappe.get_value("User", frappe.session.user, "full_name")
			self.security_guard_name = user_fullname or frappe.session.user

		# Auto-populate gate pass date and time
		if not self.gate_pass_date:
			self.gate_pass_date = nowdate()

		if not self.gate_pass_time:
			self.gate_pass_time = nowtime()

		# Auto-populate gate entry date and time
		if not self.gate_entry_date:
			self.gate_entry_date = nowdate()

		if not self.gate_entry_time:
			self.gate_entry_time = nowtime()

		# Clean up driver contact field if it only contains the default country code
		if self.driver_contact:
			cleaned_contact = self.driver_contact.strip().replace(" ", "").replace("-", "")
			if cleaned_contact in ["+91", ""]:
				self.driver_contact = None

	def validate(self):
		"""
		Validate the Gate Pass document
		"""
		# Validate that at least one item exists
		if not self.gate_pass_table or len(self.gate_pass_table) == 0:
			frappe.throw(_("Please add at least one item to the Gate Pass"))

		# Validate received quantities
		for item in self.gate_pass_table:
			if flt(item.received_qty) <= 0:
				frappe.throw(
					_("Received quantity for item {0} must be greater than zero").format(item.item_code)
				)

		# Validate reference document
		if self.document_reference and self.reference_number:
			self.validate_reference_document()

		# Validate supplier matches reference document
		self.validate_supplier()

	def validate_reference_document(self):
		"""
		Validate that the reference document is submitted
		"""
		doc = frappe.get_doc(self.document_reference, self.reference_number)
		if doc.docstatus != 1:
			frappe.throw(_("Reference document {0} must be submitted").format(self.reference_number))

	def validate_supplier(self):
		"""
		Validate that supplier matches the reference document supplier
		"""
		if self.document_reference and self.reference_number and self.supplier:
			doc = frappe.get_doc(self.document_reference, self.reference_number)
			if hasattr(doc, "supplier") and doc.supplier != self.supplier:
				frappe.throw(_("Supplier does not match the reference document"))

	def on_submit(self):
		"""
		Actions to perform on submission
		"""
		# Check if this is an amended document with linked receipts
		if self.amended_from:
			self.check_receipts_in_amended_document()

		frappe.msgprint(_("Gate Pass submitted successfully"))

	def before_cancel(self):
		"""
		Prevent cancellation if Purchase Receipt or Subcontracting Receipt exists
		"""
		self.check_linked_receipts_before_cancel()

	def check_receipts_in_amended_document(self):
		"""
		Prevent amendment if the original Gate Pass has linked receipts
		"""
		if not self.amended_from:
			return

		# Get the original Gate Pass
		original_doc = frappe.get_doc("Gate Pass", self.amended_from)

		linked_receipts = []

		# Check for Purchase Receipt
		if original_doc.purchase_receipt:
			receipt_status = frappe.db.get_value(
				"Purchase Receipt", original_doc.purchase_receipt, "docstatus"
			)
			if receipt_status == 1:  # Submitted
				linked_receipts.append(
					{
						"doctype": "Purchase Receipt",
						"name": original_doc.purchase_receipt,
						"status": "Submitted",
					}
				)

		# Check for Subcontracting Receipt
		if original_doc.subcontracting_receipt:
			receipt_status = frappe.db.get_value(
				"Subcontracting Receipt", original_doc.subcontracting_receipt, "docstatus"
			)
			if receipt_status == 1:  # Submitted
				linked_receipts.append(
					{
						"doctype": "Subcontracting Receipt",
						"name": original_doc.subcontracting_receipt,
						"status": "Submitted",
					}
				)

		if linked_receipts:
			self.throw_amendment_error(linked_receipts)

	def check_linked_receipts_before_cancel(self):
		"""
		Check if any Purchase Receipt or Subcontracting Receipt is linked
		"""
		linked_receipts = []

		# Check for Purchase Receipt
		if self.purchase_receipt:
			receipt_status = frappe.db.get_value("Purchase Receipt", self.purchase_receipt, "docstatus")
			if receipt_status == 1:  # Submitted
				linked_receipts.append(
					{"doctype": "Purchase Receipt", "name": self.purchase_receipt, "status": "Submitted"}
				)
			elif receipt_status == 0:  # Draft
				linked_receipts.append(
					{"doctype": "Purchase Receipt", "name": self.purchase_receipt, "status": "Draft"}
				)

		# Check for Subcontracting Receipt
		if self.subcontracting_receipt:
			receipt_status = frappe.db.get_value(
				"Subcontracting Receipt", self.subcontracting_receipt, "docstatus"
			)
			if receipt_status == 1:  # Submitted
				linked_receipts.append(
					{
						"doctype": "Subcontracting Receipt",
						"name": self.subcontracting_receipt,
						"status": "Submitted",
					}
				)
			elif receipt_status == 0:  # Draft
				linked_receipts.append(
					{
						"doctype": "Subcontracting Receipt",
						"name": self.subcontracting_receipt,
						"status": "Draft",
					}
				)

		if linked_receipts:
			self.throw_cancellation_error(linked_receipts)

	def throw_cancellation_error(self, linked_receipts):
		"""
		Throw error with list of linked receipts
		"""
		message = _(
			"<b>Cannot cancel this Gate Pass because the following receipt(s) are linked to it:</b><br><br>"
		)

		for receipt in linked_receipts:
			receipt_link = frappe.utils.get_link_to_form(receipt["doctype"], receipt["name"])
			message += _("• {0} - Status: <b>{1}</b><br>").format(receipt_link, receipt["status"])

		message += _("<br><b>Action Required:</b><br>")
		message += _("Please cancel the linked receipt(s) first, then you can cancel this Gate Pass.")

		frappe.throw(message, title=_("Cannot Cancel Gate Pass"))

	def throw_amendment_error(self, linked_receipts):
		"""
		Throw error preventing amendment when receipts exist
		"""
		message = _(
			"<b>Cannot amend this Gate Pass because the following receipt(s) were created from it:</b><br><br>"
		)

		for receipt in linked_receipts:
			receipt_link = frappe.utils.get_link_to_form(receipt["doctype"], receipt["name"])
			message += _("• {0} - Status: <b>{1}</b><br>").format(receipt_link, receipt["status"])

		message += _("<br><b>Action Required:</b><br>")
		message += _("To amend this Gate Pass, please follow these steps:<br>")
		message += _("1. Cancel the linked receipt(s)<br>")
		message += _("2. Cancel this Gate Pass<br>")
		message += _("3. Create a new Gate Pass with the correct details<br>")
		message += _("4. Create a new receipt from the new Gate Pass")

		frappe.throw(message, title=_("Cannot Amend Gate Pass"))


@frappe.whitelist()
def get_items(document_reference, reference_number):
	"""
	Fetch items from the reference document with pending quantities

	Args:
		document_reference: DocType name (Purchase Order or Subcontracting Order)
		reference_number: Document name

	Returns:
		List of items with ordered, received, and pending quantities
	"""
	if not document_reference or not reference_number:
		frappe.throw(_("Document Reference and Reference Number are required"))

	# Check permissions
	if not frappe.has_permission(document_reference, "read"):
		frappe.throw(_("You don't have permission to access {0}").format(document_reference))

	items = []

	if document_reference == "Purchase Order":
		items = get_purchase_order_items(reference_number)
	elif document_reference == "Subcontracting Order":
		items = get_subcontracting_order_items(reference_number)
	else:
		frappe.throw(_("Unsupported Document Reference: {0}").format(document_reference))

	return items


def get_purchase_order_items(purchase_order):
	"""
	Get items from Purchase Order with pending quantities
	"""
	# Check if this is a Rate Contract (has_unit_price_items flag)
	po_doc = frappe.get_doc("Purchase Order", purchase_order)
	is_rate_contract = po_doc.get("has_unit_price_items", 0)

	# Fetch items from Purchase Order
	po_items = frappe.get_all(
		"Purchase Order Item", filters={"parent": purchase_order, "docstatus": 1}, fields=["*"]
	)

	items = []
	for po_item in po_items:
		# Calculate total received (Purchase Receipts + Gate Passes)
		total_received = flt(po_item.received_qty)

		# For Rate Contracts, pending quantity cannot be calculated
		# since ordered quantity is 0
		if is_rate_contract:
			pending_qty = 0  # Not applicable for rate contracts
			ordered_qty = 0
		else:
			ordered_qty = flt(po_item.qty)
			pending_qty = ordered_qty - total_received

		items.append(
			{
				"item_code": po_item.item_code,
				"item_name": po_item.item_name,
				"description": po_item.description or "",
				"uom": po_item.uom,
				"ordered_qty": ordered_qty,
				"received_qty": flt(total_received),
				"pending_qty": max(0, pending_qty),
				"is_rate_contract": is_rate_contract,  # Flag for client-side validation
			}
		)

	return items


def get_subcontracting_order_items(subcontracting_order):
	"""
	Get items from Subcontracting Order with pending quantities
	"""
	# Fetch items from Subcontracting Order
	so_items = frappe.get_all(
		"Subcontracting Order Item", filters={"parent": subcontracting_order, "docstatus": 1}, fields=["*"]
	)

	items = []
	for so_item in so_items:
		# Calculate pending quantity from gate passes
		gate_pass_qty = get_gate_pass_received_qty(
			subcontracting_order, so_item.item_code, "Subcontracting Order"
		)

		# Calculate total received
		total_received = flt(so_item.received_qty) + flt(gate_pass_qty)
		pending_qty = flt(so_item.qty) - total_received

		items.append(
			{
				"item_code": so_item.item_code,
				"item_name": so_item.item_name,
				"description": so_item.description or "",
				"uom": so_item.uom,
				"ordered_qty": flt(so_item.qty),
				"received_qty": flt(total_received),
				"pending_qty": max(0, pending_qty),
			}
		)

	return items


def get_gate_pass_received_qty(reference_number, item_code, document_reference="Purchase Order"):
	"""
	Calculate total received quantity from existing gate passes for this item

	Args:
		reference_number: Reference document name
		item_code: Item code
		document_reference: DocType name (default: Purchase Order)

	Returns:
		Total received quantity from gate passes
	"""
	gate_passes = frappe.get_all(
		"Gate Pass",
		filters={
			"reference_number": reference_number,
			"document_reference": document_reference,
			"docstatus": ["!=", 2],  # Exclude cancelled
		},
		fields=["name"],
	)

	total_qty = 0
	for gp in gate_passes:
		items = frappe.get_all(
			"Gate Pass Table", filters={"parent": gp.name, "item_code": item_code}, fields=["received_qty"]
		)
		for item in items:
			total_qty += flt(item.received_qty)

	return total_qty


@frappe.whitelist()
def get_address(document_reference, reference_number):
	"""
	Fetch address display from the reference document
	"""
	if not document_reference or not reference_number:
		return ""

	address = ""

	if document_reference == "Purchase Order":
		po = frappe.get_value("Purchase Order", reference_number, "address_display")
		address = po or ""
	elif document_reference == "Subcontracting Order":
		so = frappe.get_value("Subcontracting Order", reference_number, "address_display")
		address = so or ""

	return address


@frappe.whitelist()
def create_purchase_receipt(gate_pass_name):
	"""
	Create Purchase Receipt from Gate Pass

	Args:
		gate_pass_name: Name of the Gate Pass

	Returns:
		Name of the created Purchase Receipt
	"""
	# Check permissions
	if not frappe.has_permission("Purchase Receipt", "create"):
		frappe.throw(_("You don't have permission to create Purchase Receipt"))

	# Get Gate Pass
	gate_pass = frappe.get_doc("Gate Pass", gate_pass_name)

	# Validate Gate Pass
	if gate_pass.docstatus != 1:
		frappe.throw(_("Gate Pass must be submitted before creating Purchase Receipt"))

	if gate_pass.purchase_receipt:
		frappe.throw(_("Purchase Receipt has already been created for this Gate Pass"))

	if gate_pass.document_reference != "Purchase Order":
		frappe.throw(_("This Gate Pass is not for a Purchase Order"))

	# Create Purchase Receipt
	pr = frappe.new_doc("Purchase Receipt")
	pr.supplier = gate_pass.supplier
	pr.company = gate_pass.company
	pr.posting_date = gate_pass.gate_pass_date
	pr.posting_time = gate_pass.gate_pass_time
	pr.set_posting_time = 1
	pr.gate_pass = gate_pass_name

	# Add items
	for item in gate_pass.gate_pass_table:
		pr.append(
			"items",
			{
				"item_code": item.item_code,
				"item_name": item.item_name,
				"description": item.description,
				"uom": item.uom,
				"qty": item.received_qty,
				"received_qty": item.received_qty,
				"purchase_order": gate_pass.reference_number,
				"purchase_order_item": get_po_item_name(gate_pass.reference_number, item.item_code),
			},
		)

	pr.insert()

	# Update Gate Pass with receipt reference
	gate_pass.purchase_receipt = pr.name
	gate_pass.save(ignore_permissions=True)

	# No manual commit needed - Frappe will auto-commit at end of request

	return pr.name


@frappe.whitelist()
def create_subcontracting_receipt(gate_pass_name):
	"""
	Create Subcontracting Receipt from Gate Pass

	Args:
		gate_pass_name: Name of the Gate Pass

	Returns:
		Name of the created Subcontracting Receipt
	"""
	# Check permissions
	if not frappe.has_permission("Subcontracting Receipt", "create"):
		frappe.throw(_("You don't have permission to create Subcontracting Receipt"))

	# Get Gate Pass
	gate_pass = frappe.get_doc("Gate Pass", gate_pass_name)

	# Validate Gate Pass
	if gate_pass.docstatus != 1:
		frappe.throw(_("Gate Pass must be submitted before creating Subcontracting Receipt"))

	if gate_pass.subcontracting_receipt_reference:
		frappe.throw(_("Subcontracting Receipt has already been created for this Gate Pass"))

	if gate_pass.document_reference != "Subcontracting Order":
		frappe.throw(_("This Gate Pass is not for a Subcontracting Order"))

	# Create Subcontracting Receipt
	sr = frappe.new_doc("Subcontracting Receipt")
	sr.supplier = gate_pass.supplier
	sr.company = gate_pass.company
	sr.posting_date = gate_pass.gate_pass_date
	sr.posting_time = gate_pass.gate_pass_time
	sr.set_posting_time = 1
	sr.subcontracting_order = gate_pass.reference_number
	sr.gate_pass = gate_pass_name

	# Add items
	for item in gate_pass.gate_pass_table:
		sr.append(
			"items",
			{
				"item_code": item.item_code,
				"item_name": item.item_name,
				"description": item.description,
				"uom": item.uom,
				"qty": item.received_qty,
				"received_qty": item.received_qty,
				"subcontracting_order": gate_pass.reference_number,
			},
		)

	sr.insert()

	# Update Gate Pass with receipt reference
	gate_pass.subcontracting_receipt = sr.name
	gate_pass.save(ignore_permissions=True)

	# No manual commit needed - Frappe will auto-commit at end of request

	return sr.name


def get_po_item_name(purchase_order, item_code):
	"""
	Get Purchase Order Item name for linking
	"""
	po_item = frappe.get_value(
		"Purchase Order Item", {"parent": purchase_order, "item_code": item_code}, "name"
	)
	return po_item


# Document Event Handlers for Purchase Receipt and Subcontracting Receipt
# ------------------------------------------------------------------------
# Note: Gate Pass is in ignore_links_on_delete (hooks.py) which allows
# Purchase Receipts and Subcontracting Receipts to be deleted even when linked.
# These handlers clean up the Gate Pass references when receipts are deleted/cancelled.


def on_purchase_receipt_trash(doc, method):
	"""
	Clear Gate Pass reference when Purchase Receipt is deleted
	"""
	if doc.get("gate_pass"):
		clear_gate_pass_reference(doc.get("gate_pass"), "purchase_receipt")


def on_purchase_receipt_cancel(doc, method):
	"""
	Clear Gate Pass reference when Purchase Receipt is cancelled
	"""
	if doc.get("gate_pass"):
		clear_gate_pass_reference(doc.get("gate_pass"), "purchase_receipt")


def on_subcontracting_receipt_trash(doc, method):
	"""
	Clear Gate Pass reference when Subcontracting Receipt is deleted
	"""
	if doc.get("gate_pass"):
		clear_gate_pass_reference(doc.get("gate_pass"), "subcontracting_receipt")


def on_subcontracting_receipt_cancel(doc, method):
	"""
	Clear Gate Pass reference when Subcontracting Receipt is cancelled
	"""
	if doc.get("gate_pass"):
		clear_gate_pass_reference(doc.get("gate_pass"), "subcontracting_receipt")


def clear_gate_pass_reference(gate_pass_name, field_name):
	"""
	Clear the receipt reference from Gate Pass

	Args:
		gate_pass_name: Name of the Gate Pass
		field_name: The field name in Gate Pass (purchase_receipt or subcontracting_receipt)
	"""
	if not gate_pass_name or not frappe.db.exists("Gate Pass", gate_pass_name):
		return

	try:
		# Clear the reference field in Gate Pass
		frappe.db.set_value("Gate Pass", gate_pass_name, field_name, None, update_modified=False)

		frappe.msgprint(
			_("Gate Pass {0} has been updated. The receipt reference has been cleared.").format(
				frappe.utils.get_link_to_form("Gate Pass", gate_pass_name)
			)
		)
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(), title=_("Error clearing Gate Pass reference"), exception=e
		)
