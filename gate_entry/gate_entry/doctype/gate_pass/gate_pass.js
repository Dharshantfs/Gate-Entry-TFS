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
					name: [
						"in",
						["Purchase Order", "Subcontracting Order", "Sales Invoice", "Delivery Note"],
					],
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

		refresh_compliance_status(frm);
	},
	onload(frm){
		frm.set_query("document_reference", function () {
			return {
				filters: {
					name: [
						"in",
						["Purchase Order", "Subcontracting Order", "Sales Invoice", "Delivery Note"],
					],
				},
			};
		});
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

		// Update entry type locally for better UX
		if (is_outbound_reference(frm.doc.document_reference)) {
			frm.set_value("entry_type", "Gate Out");
			frm.set_value("supplier", null);
			frm.set_value("supplier_delivery_note", null);
		} else {
			frm.set_value("entry_type", "Gate In");
		}

		// Clear items when document type changes
		frm.clear_table("gate_pass_table");
		frm.refresh_field("gate_pass_table");

		clear_compliance_status(frm);

		// Refresh custom UI
		if (frm.gate_pass_ui) {
			frm.gate_pass_ui.refresh();
		}
	},

	reference_number(frm) {
		// Fetch address display from reference document
		if (frm.doc.document_reference && frm.doc.reference_number) {
			load_reference_details(frm);

			if (is_outbound_reference(frm.doc.document_reference)) {
				load_reference_items(frm);
				refresh_compliance_status(frm);
			} else {
				clear_compliance_status(frm);
			}
		} else {
			clear_compliance_status(frm);
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

function load_reference_details(frm) {
	frappe.call({
		method: "gate_entry.gate_entry.doctype.gate_pass.gate_pass.get_reference_details",
		args: {
			document_reference: frm.doc.document_reference,
			reference_number: frm.doc.reference_number,
		},
		callback(response) {
			const details = response.message;
			console.log("Details: ", details);
			if (!details) {
				return;
			}

			const updates = {};

			if (details.company && !frm.doc.company) {
				updates.company = details.company;
			}

			if (details.address_display) {
				updates.address_display = details.address_display;
			}

			updates.e_invoice_status = details.e_invoice_status || null;
			updates.e_invoice_reference = details.e_invoice_reference || null;
			updates.e_waybill_status = details.e_waybill_status || null;
			updates.e_waybill_number = details.e_waybill_number || null;

			if (details.vehicle_number && !frm.doc.vehicle_number) {
				updates.vehicle_number = details.vehicle_number;
			}
			if (details.driver_name && !frm.doc.driver_name) {
				updates.driver_name = details.driver_name;
			}
			if (details.driver_contact && !frm.doc.driver_contact) {
				updates.driver_contact = details.driver_contact;
			}
			if (is_outbound_reference(frm.doc.document_reference)) {
				updates.supplier = null;
				updates.supplier_delivery_note = null;

			} else if (details.party_type === "Supplier" && details.party) {
				updates.supplier = details.party;
				if (details.supplier_delivery_note) {
					updates.supplier_delivery_note = details.supplier_delivery_note;
				}
			}
			console.log("Updates: ", updates);
			frm.set_value(updates).then(() => {
				frm.refresh();
			});
		},
	});
}

function load_reference_items(frm) {
	frappe.call({
		method: "gate_entry.gate_entry.doctype.gate_pass.gate_pass.get_items",
		args: {
			document_reference: frm.doc.document_reference,
			reference_number: frm.doc.reference_number,
		},
		freeze: true,
		freeze_message: __("Loading items from reference document..."),
		callback(response) {
			const items = response.message || [];
			set_gate_pass_items(frm, items);
		},
	});
}

function set_gate_pass_items(frm, items) {
	frm.clear_table("gate_pass_table");

	(items || []).forEach((item) => {
		const row = frm.add_child("gate_pass_table");
		row.item_code = item.item_code;
		row.item_name = item.item_name || "";
		row.description = item.description || "";
		row.uom = item.uom || "";
		row.stock_uom = item.stock_uom || "";
		row.conversion_factor = item.conversion_factor || 1.0;
		row.ordered_qty = item.ordered_qty || 0;
		row.received_qty = item.received_qty || 0;
		row.dispatched_qty = item.dispatched_qty || 0;
		row.pending_qty = item.pending_qty || 0;
		row.is_rate_contract = item.is_rate_contract || 0;
		row.rate = item.rate || 0;
		const qty_for_amount = is_outbound_reference(frm.doc.document_reference)
			? item.dispatched_qty || 0
			: item.received_qty || 0;
		row.amount = qty_for_amount * (item.rate || 0);
		row.warehouse = item.warehouse || "";
		row.rejected_warehouse = item.rejected_warehouse || "";
		row.expense_account = item.expense_account || "";
		row.cost_center = item.cost_center || "";
		row.project = item.project || "";
		row.schedule_date = item.schedule_date || "";
		row.bom = item.bom || "";
		row.include_exploded_items = item.include_exploded_items || 0;
		row.order_item_name = item.order_item_name || "";
	});

	frm.refresh_field("gate_pass_table");

	if (frm.gate_pass_ui) {
		frm.gate_pass_ui.refresh();
	}
}

function is_outbound_reference(documentReference) {
	return ["Sales Invoice", "Delivery Note"].includes(documentReference);
}

function refresh_compliance_status(frm) {
	const field = frm.fields_dict?.compliance_status_html;
	if (!field) {
		return;
	}

	if (!frm.doc.document_reference || !frm.doc.reference_number || !is_outbound_reference(frm.doc.document_reference)) {
		clear_compliance_status(frm);
		return;
	}

	frappe.call({
		method: "gate_entry.gate_entry.doctype.gate_pass.gate_pass.get_outbound_compliance_status",
		args: {
			document_reference: frm.doc.document_reference,
			reference_number: frm.doc.reference_number,
			gate_pass: frm.doc.name || null,
		},
		callback(response) {
			const status = response.message;
			set_compliance_status(field, status);
		},
	});
}

function clear_compliance_status(frm) {
	const field = frm.fields_dict?.compliance_status_html;
	if (!field) {
		return;
	}
	set_compliance_status(field, null);
}

function set_compliance_status(field, status) {
	const wrapper = field.$wrapper;
	if (!wrapper || wrapper.length === 0) {
		return;
	}
	if (!status) {
		wrapper.empty();
		return;
	}

	const level = status.level || "info";
	const title = frappe.utils.escape_html(status.title || "");
	const messages = Array.isArray(status.messages) ? status.messages : [];
	const description = status.description ? frappe.utils.escape_html(status.description) : "";

	let icon = "info-circle";
	if (level === "success") {
		icon = "check-circle";
	} else if (level === "warning") {
		icon = "exclamation-triangle";
	} else if (level === "error") {
		icon = "times-circle";
	}

	const body = [];
	if (title) {
		body.push(`<div class="compliance-banner-title">${title}</div>`);
	}

	if (description) {
		body.push(`<div class="compliance-banner-description">${description}</div>`);
	}

	if (messages.length) {
		const listItems = messages
			.map((message) => `<li>${frappe.utils.escape_html(message)}</li>`)
			.join("");
		body.push(`<ul class="compliance-banner-list">${listItems}</ul>`);
	}

	if (!body.length) {
		body.push(`<div class="compliance-banner-description">${__("No compliance information available.")}</div>`);
	}

	const html = `
		<div class="compliance-banner compliance-${level}">
			<div class="compliance-banner-icon">
				<i class="fa fa-${icon}"></i>
			</div>
			<div class="compliance-banner-body">
				${body.join("")}
			</div>
		</div>
	`;

	wrapper.html(html);
}
