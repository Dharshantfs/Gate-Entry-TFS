// Copyright (c) 2025, Gurudatt Kulkarni and contributors
// For license information, please see license.txt

frappe.ui.form.on("Gate Pass", {
	refresh(frm) {
        // Add custom HTML section
        if (!frm.custom_ui) {
            console.log(frm.fields_dict)
            frm.custom_ui = $('<div class="custom-ui"></div>').appendTo(frm.fields_dict.custom_ui.$wrapper);
            frm.custom_ui.html(`
                <div class="card">
                    <h3>Custom UI Section</h3>
                    <p>Document: ${frm.doc.name}</p>
                </div>
            `);
        }
	},

    custom_get_items(frm) {
        frappe.call({
            method: "gate_entry.gate_entry.doctype.gate_pass.gate_pass.get_items",
            args: {
                document_reference: frm.doc.document_reference,
                reference_number: frm.doc.reference_number
            },
            callback: function(response) {
                if (response.message) {
                    console.log("Items fetched:", response.message);
                    frm.clear_table("items");
                }
            }
        });
    },
    reference_number: function(frm) {
        frappe.call({
            method: "gate_entry.gate_entry.doctype.gate_pass.gate_pass.get_address",
            args: {
                document_reference: frm.doc.document_reference,
                reference_number: frm.doc.reference_number
            },
            callback: function(response) {
                if (response.message) {
                    console.log("Address fetched:", response.message);
                    frm.set_value("address_display", response.message);
                    frm.refresh_field("address_display");
                }
            }
        });
    }
});

