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
	Get items from Purchase Order with pending quantities and all item details
	"""
	# Check if this is a Rate Contract (has_unit_price_items flag)
	po_doc = frappe.get_doc("Purchase Order", purchase_order)
	is_rate_contract = po_doc.get("has_unit_price_items", 0)

	# Fetch items from Purchase Order with all fields
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
				"stock_uom": po_item.stock_uom,
				"conversion_factor": flt(po_item.conversion_factor) or 1.0,
				"ordered_qty": ordered_qty,
				"received_qty": flt(total_received),
				"pending_qty": max(0, pending_qty),
				"is_rate_contract": is_rate_contract,
				# Pricing details
				"rate": flt(po_item.rate),
				"amount": flt(po_item.amount),
				# Warehouse and location
				"warehouse": po_item.warehouse,
				"rejected_warehouse": None,  # Will be set during receipt
				# Accounting details
				"expense_account": po_item.expense_account,
				"cost_center": po_item.cost_center,
				# Reference details
				"project": po_item.project,
				"schedule_date": po_item.schedule_date,
				# Other details
				"bom": po_item.bom if hasattr(po_item, "bom") else None,
				"order_item_name": po_item.name,  # Store the Purchase Order Item name
			}
		)

	return items


def get_subcontracting_order_items(subcontracting_order):
	"""
	Get items from Subcontracting Order with pending quantities and all item details
	"""
	# Fetch items from Subcontracting Order with all fields
	so_items = frappe.get_all(
		"Subcontracting Order Item", filters={"parent": subcontracting_order, "docstatus": 1}, fields=["*"]
	)

	items = []
	for so_item in so_items:
		# Use received_qty from Subcontracting Order Item (maintained by ERPNext)
		total_received = flt(so_item.received_qty)
		ordered_qty = flt(so_item.qty)
		pending_qty = ordered_qty - total_received

		items.append(
			{
				"item_code": so_item.item_code,
				"item_name": so_item.item_name,
				"description": so_item.description or "",
				"uom": so_item.stock_uom,  # Subcontracting uses stock_uom
				"stock_uom": so_item.stock_uom,
				"conversion_factor": flt(so_item.conversion_factor) or 1.0,
				"ordered_qty": ordered_qty,
				"received_qty": total_received,
				"pending_qty": max(0, pending_qty),
				"is_rate_contract": False,  # Subcontracting orders are not rate contracts
				# Pricing details
				"rate": flt(so_item.rate),
				"amount": flt(so_item.amount),
				# Warehouse and location
				"warehouse": so_item.warehouse,
				"rejected_warehouse": None,  # Will be set during receipt
				# Accounting details
				"expense_account": so_item.expense_account,
				"cost_center": so_item.cost_center,
				# Reference details
				"project": so_item.project,
				"schedule_date": so_item.schedule_date,
				# Other details
				"bom": so_item.bom or "",
				"include_exploded_items": so_item.include_exploded_items or 0,
				"order_item_name": so_item.name,  # Store the Subcontracting Order Item name
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
	Maps all fields from Purchase Order Item and uses received quantities from Gate Pass

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

	# Get Purchase Order document for header-level fields
	purchase_order = frappe.get_doc("Purchase Order", gate_pass.reference_number)

	# Create Purchase Receipt with header mapping from Purchase Order
	pr = frappe.new_doc("Purchase Receipt")
	pr.supplier = gate_pass.supplier
	pr.company = gate_pass.company
	pr.gate_pass = gate_pass_name
	if gate_pass.get("supplier_delivery_note"):
		pr.supplier_delivery_note = gate_pass.supplier_delivery_note

	# Map additional header fields from Purchase Order
	pr.supplier_warehouse = purchase_order.supplier_warehouse
	pr.currency = purchase_order.currency
	pr.conversion_rate = purchase_order.conversion_rate
	pr.buying_price_list = purchase_order.buying_price_list
	pr.price_list_currency = purchase_order.price_list_currency
	pr.plc_conversion_rate = purchase_order.plc_conversion_rate
	pr.ignore_pricing_rule = purchase_order.ignore_pricing_rule
	pr.set_warehouse = purchase_order.set_warehouse
	pr.supplier_address = purchase_order.supplier_address
	pr.address_display = purchase_order.address_display
	pr.contact_person = purchase_order.contact_person
	pr.contact_display = purchase_order.contact_display
	pr.contact_mobile = purchase_order.contact_mobile
	pr.contact_email = purchase_order.contact_email
	pr.shipping_address = purchase_order.shipping_address
	pr.shipping_address_display = purchase_order.shipping_address_display

	# set the vehicle number and driver name from gate pass
	pr.vehicle_no = gate_pass.vehicle_number
	pr.driver_name = gate_pass.driver_name

	# Add items - fetch complete details from Purchase Order Item and override quantities from Gate Pass
	for gate_pass_item in gate_pass.gate_pass_table:
		# Get the original Purchase Order Item
		po_item = frappe.get_doc("Purchase Order Item", gate_pass_item.order_item_name)

		# Calculate quantities based on received quantity from Gate Pass
		received_qty = flt(gate_pass_item.received_qty)
		conversion_factor = flt(po_item.conversion_factor) or 1.0
		received_stock_qty = received_qty * conversion_factor

		# Build Purchase Receipt Item with all fields from PO Item that exist in PR Item
		pr_item = {
			# Basic item details from PO
			"item_code": po_item.item_code,
			"item_name": po_item.item_name,
			"description": po_item.description,
			"item_group": po_item.item_group,
			"brand": po_item.brand,
			"image": po_item.image,
			# UOM and conversion
			"uom": po_item.uom,
			"stock_uom": po_item.stock_uom,
			"conversion_factor": conversion_factor,
			# Quantities - from Gate Pass
			"qty": received_qty,
			"received_qty": received_qty,
			"stock_qty": received_stock_qty,
			"received_stock_qty": received_stock_qty,
			# Pricing from PO (base values will be calculated by set_missing_values)
			"rate": flt(po_item.rate),
			"price_list_rate": flt(po_item.price_list_rate),
			"base_rate": flt(po_item.base_rate),
			"base_price_list_rate": flt(po_item.base_price_list_rate),
			"discount_percentage": flt(po_item.discount_percentage),
			"discount_amount": flt(po_item.discount_amount),
			"margin_type": po_item.margin_type,
			"margin_rate_or_amount": flt(po_item.margin_rate_or_amount),
			# Warehouse - prefer from Gate Pass, fallback to PO
			"warehouse": gate_pass_item.warehouse or po_item.warehouse,
			"from_warehouse": po_item.from_warehouse if po_item.get("from_warehouse") else None,
			# Accounting from PO
			"expense_account": po_item.expense_account,
			"cost_center": po_item.cost_center,
			# Reference fields from PO
			"project": po_item.project if po_item.get("project") else None,
			"schedule_date": po_item.schedule_date if po_item.get("schedule_date") else None,
			# Material Request references
			"material_request": po_item.material_request if po_item.get("material_request") else None,
			"material_request_item": po_item.material_request_item
			if po_item.get("material_request_item")
			else None,
			# Sales Order references (for drop-ship scenarios)
			"sales_order": po_item.sales_order if po_item.get("sales_order") else None,
			"sales_order_item": po_item.sales_order_item if po_item.get("sales_order_item") else None,
			# Manufacturing references
			"bom": po_item.bom if po_item.get("bom") else None,
			"wip_composite_asset": po_item.wip_composite_asset
			if po_item.get("wip_composite_asset")
			else None,
			# Manufacturer details
			"manufacturer": po_item.manufacturer if po_item.get("manufacturer") else None,
			"manufacturer_part_no": po_item.manufacturer_part_no
			if po_item.get("manufacturer_part_no")
			else None,
			"supplier_part_no": po_item.supplier_part_no if po_item.get("supplier_part_no") else None,
			# Asset fields
			"is_fixed_asset": po_item.is_fixed_asset if po_item.get("is_fixed_asset") else 0,
			"asset_location": po_item.asset_location if po_item.get("asset_location") else None,
			"asset_category": po_item.asset_category if po_item.get("asset_category") else None,
			# Tax
			"item_tax_template": po_item.item_tax_template if po_item.get("item_tax_template") else None,
			"item_tax_rate": po_item.item_tax_rate if po_item.get("item_tax_rate") else None,
			"gst_treatment": po_item.gst_treatment if po_item.get("gst_treatment") else None,
			# Other fields
			"product_bundle": po_item.product_bundle if po_item.get("product_bundle") else None,
			"is_free_item": po_item.is_free_item if po_item.get("is_free_item") else 0,
			# Order linking - Critical for PO-PR linkage
			"purchase_order": gate_pass.reference_number,
			"purchase_order_item": gate_pass_item.order_item_name,
		}

		# Add rejected_warehouse only if specified in Gate Pass
		if gate_pass_item.get("rejected_warehouse"):
			pr_item["rejected_warehouse"] = gate_pass_item.rejected_warehouse

		# Add apply_tds if present in PO
		if po_item.get("apply_tds"):
			pr_item["apply_tds"] = po_item.apply_tds

		pr.append("items", pr_item)

	# Set missing values and calculate totals (mimics ERPNext's set_missing_values)
	pr.run_method("set_missing_values")
	# pr.run_method("calculate_taxes_and_totals")

	pr.insert()

	# Update Gate Pass with receipt reference
	gate_pass.purchase_receipt = pr.name
	gate_pass.save(ignore_permissions=True)

	return pr.name


@frappe.whitelist()
def create_subcontracting_receipt(gate_pass_name):
	"""
	Create Subcontracting Receipt from Gate Pass
	Uses proper field mapping between Subcontracting Order and Subcontracting Receipt
	following ERPNext's standard mapper pattern

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

	if gate_pass.subcontracting_receipt:
		frappe.throw(_("Subcontracting Receipt has already been created for this Gate Pass"))

	if gate_pass.document_reference != "Subcontracting Order":
		frappe.throw(_("This Gate Pass is not for a Subcontracting Order"))

	# Get Subcontracting Order document for header-level fields
	subcontracting_order = frappe.get_doc("Subcontracting Order", gate_pass.reference_number)

	# Create Subcontracting Receipt with proper header field mapping
	sr = frappe.new_doc("Subcontracting Receipt")

	# Primary fields
	sr.supplier = subcontracting_order.supplier
	sr.company = subcontracting_order.company
	sr.vehicle_no = gate_pass.vehicle_number

	# Reference to Gate Pass
	sr.gate_pass = gate_pass_name
	if gate_pass.get("supplier_delivery_note"):
		sr.supplier_delivery_note = gate_pass.supplier_delivery_note

	# Map header fields from Subcontracting Order to Subcontracting Receipt
	# Following ERPNext's standard field mapping (see make_subcontracting_receipt in subcontracting_order.py)
	header_field_map = {
		# Warehouse fields
		"supplier_warehouse": "supplier_warehouse",
		"set_warehouse": "set_warehouse",
		# Address and contact fields
		"supplier_address": "supplier_address",
		"address_display": "address_display",
		"contact_person": "contact_person",
		"contact_display": "contact_display",
		"contact_mobile": "contact_mobile",
		"contact_email": "contact_email",
		"shipping_address": "shipping_address",
		"shipping_address_display": "shipping_address_display",
		"billing_address": "billing_address",
		"billing_address_display": "billing_address_display",
		# Project and cost center
		"project": "project",
		"cost_center": "cost_center",
		# Print and display settings
		"letter_head": "letter_head",
		"select_print_heading": "select_print_heading",
		# Additional costs
		"distribute_additional_costs_based_on": "distribute_additional_costs_based_on",
		# Critical: Purchase Order reference (needed for proper linking)
		"purchase_order": "purchase_order",
	}

	for source_field, target_field in header_field_map.items():
		if subcontracting_order.get(source_field):
			sr.set(target_field, subcontracting_order.get(source_field))

	# Add items - Map fields from Subcontracting Order Item to Subcontracting Receipt Item
	# Following ERPNext's field mapping standard
	for gate_pass_item in gate_pass.gate_pass_table:
		# Get the original Subcontracting Order Item
		so_item = frappe.get_doc("Subcontracting Order Item", gate_pass_item.order_item_name)

		# Calculate quantities based on received quantity from Gate Pass
		received_qty = flt(gate_pass_item.received_qty)
		conversion_factor = flt(so_item.conversion_factor) or 1.0

		# Build Subcontracting Receipt Item with proper field mapping
		# Only map fields that exist in both Subcontracting Order Item and Subcontracting Receipt Item
		sr_item = {
			# Basic item details
			"item_code": so_item.item_code,
			"item_name": so_item.item_name,
			"description": so_item.description,
			# Brand and image (exist in SR Item)
			"brand": so_item.brand if so_item.get("brand") else None,
			"image": so_item.image if so_item.get("image") else None,
			# UOM and conversion
			"stock_uom": so_item.stock_uom,
			"conversion_factor": conversion_factor,
			# Quantities - from Gate Pass
			"qty": received_qty,
			"received_qty": received_qty,
			# Pricing from Subcontracting Order Item
			"rate": flt(so_item.rate),
			# Cost breakdown fields (specific to subcontracting)
			"rm_cost_per_qty": flt(so_item.rm_cost_per_qty) if so_item.get("rm_cost_per_qty") else 0,
			"service_cost_per_qty": flt(so_item.service_cost_per_qty)
			if so_item.get("service_cost_per_qty")
			else 0,
			"additional_cost_per_qty": flt(so_item.additional_cost_per_qty)
			if so_item.get("additional_cost_per_qty")
			else 0,
			# Warehouse - prefer from Gate Pass, fallback to Subcontracting Order
			"warehouse": gate_pass_item.warehouse or so_item.warehouse,
			# Accounting fields
			"expense_account": so_item.expense_account if so_item.get("expense_account") else None,
			"cost_center": so_item.cost_center if so_item.get("cost_center") else None,
			# Reference fields
			"project": so_item.project if so_item.get("project") else None,
			"schedule_date": so_item.schedule_date if so_item.get("schedule_date") else None,
			# Subcontracting specific fields - Critical for subcontracting workflow
			"bom": so_item.bom,
			"include_exploded_items": so_item.include_exploded_items
			if so_item.get("include_exploded_items")
			else 0,
			# Manufacturer details
			"manufacturer": so_item.manufacturer if so_item.get("manufacturer") else None,
			"manufacturer_part_no": so_item.manufacturer_part_no
			if so_item.get("manufacturer_part_no")
			else None,
			# Other fields
			"page_break": so_item.page_break if so_item.get("page_break") else 0,
			"job_card": so_item.job_card if so_item.get("job_card") else None,
			# Critical linking fields - Required for proper SO-SR linkage and status updates
			"subcontracting_order": gate_pass.reference_number,
			"subcontracting_order_item": gate_pass_item.order_item_name,
			# Purchase Order references - Critical for proper linking to PO
			"purchase_order": subcontracting_order.purchase_order,
			"purchase_order_item": so_item.purchase_order_item
			if so_item.get("purchase_order_item")
			else None,
		}

		# Add rejected_warehouse only if specified in Gate Pass
		if gate_pass_item.get("rejected_warehouse"):
			sr_item["rejected_warehouse"] = gate_pass_item.rejected_warehouse

		sr.append("items", sr_item)

	# Copy additional costs table if present
	if subcontracting_order.get("additional_costs"):
		for cost in subcontracting_order.additional_costs:
			sr.append(
				"additional_costs",
				{
					"expense_account": cost.expense_account,
					"description": cost.description,
					"amount": cost.amount,
					"base_amount": cost.base_amount if cost.get("base_amount") else None,
				},
			)

	# Set missing values and calculate totals
	# This will populate supplied_items, calculate rates, and perform all necessary calculations
	sr.run_method("set_missing_values")

	# Insert the Subcontracting Receipt
	sr.insert()

	# Update Gate Pass with receipt reference
	gate_pass.subcontracting_receipt = sr.name
	gate_pass.save(ignore_permissions=True)

	return sr.name


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
