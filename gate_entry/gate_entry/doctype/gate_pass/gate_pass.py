# Copyright (c) 2025, Gurudatt Kulkarni and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class GatePass(Document):
	def before_save(self):
		"""
		Clean up driver contact field if it only contains the default country code
		"""
		if self.driver_contact:
			# Remove any whitespace and check if only contains default country code
			cleaned_contact = self.driver_contact.strip().replace(" ", "").replace("-", "")
			if cleaned_contact in ["+91", ""]:
				self.driver_contact = None

@frappe.whitelist()
def get_items(document_reference, reference_number):
	"""
	Fetch items from the reference document (Purchase Order, Sales Order, etc.)
	"""
	items = []
	if document_reference == "Purchase Order":
		items = frappe.get_all("Purchase Order Item", filters={"parent": reference_number}, fields=["*"])
	elif document_reference == "Sales Order":
		items = frappe.get_all("Sales Order Item", filters={"parent": reference_number}, fields=["*"])
	elif document_reference == "Delivery Note":
		items = frappe.get_all("Delivery Note Item", filters={"parent": reference_number}, fields=["*"])
	elif document_reference == "Purchase Receipt":
		items = frappe.get_all("Purchase Receipt Item", filters={"parent": reference_number}, fields=["*"])
	elif document_reference == "Sales Invoice":
		items = frappe.get_all("Sales Invoice Item", filters={"parent": reference_number}, fields=["*"])
	elif document_reference == "Stock Entry":
		items = frappe.get_all("Stock Entry Detail", filters={"parent": reference_number}, fields=["*"])
	else:
		frappe.throw("Unsupported Document Reference")
	return items

@frappe.whitelist()
def get_address(document_reference, reference_number):
	"""
	Fetch address from the reference document
	"""
	address = ""
	if document_reference == "Purchase Order":
		address = frappe.get_all("Purchase Order", filters={"name": reference_number}, fields=["address_display"])
		if address:
			address = address[0]["address_display"]
	return address