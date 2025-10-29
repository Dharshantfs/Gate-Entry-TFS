// Copyright (c) 2025, Gurudatt Kulkarni and contributors
// For license information, please see license.txt

frappe.ui.form.on("Gate Pass", {
	onload_post_render(frm) {
		// Initialize the custom UI component after form is fully rendered
		if (!frm.gate_pass_ui && window.GatePassCustomUI) {
			frm.gate_pass_ui = new window.GatePassCustomUI(frm);
		}
	},

	refresh(frm) {
		// Initialize the custom UI component if not already done
		if (!frm.gate_pass_ui && window.GatePassCustomUI) {
			frm.gate_pass_ui = new window.GatePassCustomUI(frm);
		} else if (frm.gate_pass_ui) {
			// Refresh the UI to show updated data
			frm.gate_pass_ui.refresh();
		}

		// Auto-populate security guard name with current user
		if (frm.is_new() && !frm.doc.security_guard_name) {
			frm.set_value(
				"security_guard_name",
				frappe.session.user_fullname || frappe.session.user
			);
		}

		// Auto-populate gate pass date and time
		if (frm.is_new() && !frm.doc.gate_pass_date) {
			frm.set_value("gate_pass_date", frappe.datetime.get_today());
			frm.set_value("gate_pass_time", frappe.datetime.now_time());
		}

		// Auto-populate gate entry date and time
		if (frm.is_new() && !frm.doc.gate_entry_date) {
			frm.set_value("gate_entry_date", frappe.datetime.get_today());
			frm.set_value("gate_entry_time", frappe.datetime.now_time());
		}

		// Hide the gate_pass_table field (it's for backend only)
		frm.toggle_display("gate_pass_table", false);

		// Show "Create Receipt" buttons after submission
		if (frm.doc.docstatus === 1) {
			setup_receipt_buttons(frm);
		}

		// Filter Document Reference to show only relevant doctypes
		frm.set_query("document_reference", function () {
			return {
				filters: {
					name: ["in", ["Purchase Order", "Subcontracting Order"]],
				},
			};
		});

		// Filter Reference Number based on Document Reference
		if (frm.doc.document_reference) {
			frm.set_query("reference_number", function () {
				return {
					filters: {
						docstatus: 1, // Only show submitted documents
					},
				};
			});
		}
	},

	after_save(frm) {
		// Reload the form to ensure child table data is properly loaded
		// Then refresh the custom UI
		frappe.after_ajax(() => {
			if (frm.gate_pass_ui) {
				frm.gate_pass_ui.refresh();
			}
		});
	},

	document_reference(frm) {
		// Clear reference number when document reference changes
		if (frm.doc.reference_number) {
			frm.set_value("reference_number", "");
		}
		// Refresh custom UI
		if (frm.gate_pass_ui) {
			frm.gate_pass_ui.refresh();
		}
	},

	reference_number(frm) {
		// Fetch address display from reference document
		if (frm.doc.document_reference && frm.doc.reference_number) {
			frappe.call({
				method: "gate_entry.gate_entry.doctype.gate_pass.gate_pass.get_address",
				args: {
					document_reference: frm.doc.document_reference,
					reference_number: frm.doc.reference_number,
				},
				callback: function (response) {
					if (response.message) {
						frm.set_value("address_display", response.message);
					}
				},
			});
		}

		// Refresh custom UI to show/hide Add Item button
		if (frm.gate_pass_ui) {
			frm.gate_pass_ui.refresh();
		}
	},
});

/**
 * Setup receipt creation buttons
 */
function setup_receipt_buttons(frm) {
	// Check if receipt already created
	const purchase_receipt_created = frm.doc.purchase_receipt;
	const subcontracting_receipt_created = frm.doc.subcontracting_receipt;

	// Show appropriate button based on document reference type
	if (frm.doc.document_reference === "Purchase Order") {
		if (!purchase_receipt_created) {
			frm.add_custom_button(__("Create Purchase Receipt"), function () {
				create_purchase_receipt(frm);
			}).addClass("btn-primary");
		} else {
			// Show link to created receipt
			frm.add_custom_button(__("View Purchase Receipt"), function () {
				frappe.set_route("Form", "Purchase Receipt", frm.doc.purchase_receipt);
			});
		}
	} else if (frm.doc.document_reference === "Subcontracting Order") {
		if (!subcontracting_receipt_created) {
			frm.add_custom_button(__("Create Subcontracting Receipt"), function () {
				create_subcontracting_receipt(frm);
			}).addClass("btn-primary");
		} else {
			// Show link to created receipt
			frm.add_custom_button(__("View Subcontracting Receipt"), function () {
				frappe.set_route("Form", "Subcontracting Receipt", frm.doc.subcontracting_receipt);
			});
		}
	}
}

/**
 * Create Purchase Receipt from Gate Pass
 */
function create_purchase_receipt(frm) {
	frappe.confirm(__("Create Purchase Receipt from this Gate Pass?"), function () {
		frappe.call({
			method: "gate_entry.gate_entry.doctype.gate_pass.gate_pass.create_purchase_receipt",
			args: {
				gate_pass_name: frm.doc.name,
			},
			freeze: true,
			freeze_message: __("Creating Purchase Receipt..."),
			callback: function (r) {
				if (r.message) {
					frappe.show_alert({
						message: __("Purchase Receipt {0} created successfully", [r.message]),
						indicator: "green",
					});
					// Redirect to the new Purchase Receipt
					frappe.set_route("Form", "Purchase Receipt", r.message);
				}
			},
		});
	});
}

/**
 * Create Subcontracting Receipt from Gate Pass
 */
function create_subcontracting_receipt(frm) {
	frappe.confirm(__("Create Subcontracting Receipt from this Gate Pass?"), function () {
		frappe.call({
			method: "gate_entry.gate_entry.doctype.gate_pass.gate_pass.create_subcontracting_receipt",
			args: {
				gate_pass_name: frm.doc.name,
			},
			freeze: true,
			freeze_message: __("Creating Subcontracting Receipt..."),
			callback: function (r) {
				if (r.message) {
					frappe.show_alert({
						message: __("Subcontracting Receipt {0} created successfully", [
							r.message,
						]),
						indicator: "green",
					});
					// Redirect to the new Subcontracting Receipt
					frappe.set_route("Form", "Subcontracting Receipt", r.message);
				}
			},
		});
	});
}
