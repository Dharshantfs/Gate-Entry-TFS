/**
 * Gate Entry Stock Entry Enhancements
 *
 * Adds UX hints for Material Transfer transactions that require gate documentation.
 * The behaviour is delivered entirely via the gate_entry module so ERPNext core remains untouched.
 */

const GATE_ENTRY_MATERIAL_TRANSFER = "Material Transfer";

frappe.ui.form.on("Stock Entry", {
	onload(frm) {
		setup_external_transfer_behaviour(frm);
	},
	refresh(frm) {
		setup_external_transfer_behaviour(frm);
	},
	stock_entry_type(frm) {
		setup_external_transfer_behaviour(frm, { resetFlag: true });
	},
	ge_external_transfer(frm) {
		handle_external_transfer_toggle(frm);
	},
});

/**
 * Primary setup routine that makes sure UI hints stay in sync with current state.
 *
 * @param {frappe.ui.Form} frm
 * @param {{ resetFlag?: boolean }} [options]
 */
function setup_external_transfer_behaviour(frm, options = {}) {
	if (!frm || frm.doc.doctype !== "Stock Entry") {
		return;
	}

	const isMaterialTransfer = frm.doc.stock_entry_type === GATE_ENTRY_MATERIAL_TRANSFER;
	const externalTransferEnabled = cint(frm.doc.ge_external_transfer);

	// Reset the checkbox if users switch away from Material Transfer
	if (!isMaterialTransfer && externalTransferEnabled) {
		frm.set_value("ge_external_transfer", 0);
	}

	// When the type changes back to Material Transfer ensure the user sees the helper note
	if (options.resetFlag && isMaterialTransfer) {
		show_external_transfer_prompt(frm, { onlyIfUnset: true });
	}

	update_dashboard_indicator(frm, isMaterialTransfer, externalTransferEnabled);
	toggle_instruction_placeholder(frm, externalTransferEnabled);
}

/**
 * Handle manual toggling of the External Transfer checkbox.
 *
 * @param {frappe.ui.Form} frm
 */
function handle_external_transfer_toggle(frm) {
	if (!frm || frm.doc.doctype !== "Stock Entry") {
		return;
	}

	const externalTransferEnabled = cint(frm.doc.ge_external_transfer) === 1;

	if (externalTransferEnabled) {
		show_external_transfer_prompt(frm);
		update_dashboard_indicator(frm, true, true);
		toggle_instruction_placeholder(frm, true);
	} else {
		update_dashboard_indicator(frm, true, false);
		toggle_instruction_placeholder(frm, false);
	}
}

/**
 * Display a toast and optional dialog nudging the user to review gate requirements.
 *
 * @param {frappe.ui.Form} frm
 * @param {{ onlyIfUnset?: boolean }} [options]
 */
function show_external_transfer_prompt(frm, options = {}) {
	const alreadyAcknowledged =
		(frm.doc.__onload && frm.doc.__onload.__ge_external_prompt_shown) ||
		frm.meta.__ge_external_prompt_shown;

	if (options.onlyIfUnset && alreadyAcknowledged) {
		return;
	}

	const instructionField = frm.get_field("ge_gate_pass_instruction");
	if (instructionField && !instructionField.df.description) {
		instructionField.df.description = __(
			"Share vehicle details or packaging notes for the gate team."
		);
		instructionField.refresh();
	}

	frappe.show_alert({
		message: __(
			"External movement flagged. A Gate Pass will be prepared when this entry is submitted."
		),
		indicator: "orange",
	});

	frm.meta.__ge_external_prompt_shown = true;
}

/**
 * Display a dashboard indicator to highlight external transfers.
 *
 * @param {frappe.ui.Form} frm
 * @param {boolean} isMaterialTransfer
 * @param {boolean} externalTransferEnabled
 */
function update_dashboard_indicator(frm, isMaterialTransfer, externalTransferEnabled) {
	if (!frm.dashboard) {
		return;
	}

	frm.dashboard.clear_headline();
	frm.dashboard.clear_comment();

	if (!isMaterialTransfer) {
		return;
	}

	const indicatorColor = externalTransferEnabled ? "orange" : "blue";
	const indicatorLabel = externalTransferEnabled
		? __("External Transfer: Gate Pass Required")
		: __("Internal Transfer: Gate Pass Not Required");

	frm.dashboard.add_indicator(indicatorLabel, indicatorColor);
}

/**
 * When external transfer is enabled, provide a placeholder to guide users.
 *
 * @param {frappe.ui.Form} frm
 * @param {boolean} externalTransferEnabled
 */
function toggle_instruction_placeholder(frm, externalTransferEnabled) {
	const field = frm.get_field("ge_gate_pass_instruction");
	if (!field) {
		return;
	}

	const htmlField = field.$wrapper ? field.$wrapper.find("textarea") : null;
	if (htmlField && htmlField.length) {
		const placeholderText = externalTransferEnabled
			? __("Notes for gate: e.g. vehicle no, driver, package count")
			: "";
		htmlField.attr("placeholder", placeholderText);
	}
}
