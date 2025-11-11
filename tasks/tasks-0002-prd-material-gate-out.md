## Relevant Files

- `gate_entry/gate_entry/doctype/gate_pass/gate_pass.py` - Server-side logic for gate pass creation, validation, and document linkage.
- `gate_entry/gate_entry/doctype/gate_pass/gate_pass.js` - Client-side form scripting that drives auto-population and guard UI behaviour.
- `gate_entry/gate_entry/doctype/gate_pass/gate_pass.json` - Doctype schema; update field properties and add new selections if required.
- `gate_entry/gate_entry/report/gate_register/gate_register.py` - Gate register report script; extend to cover outbound sales dispatches.
- `gate_entry/public/js/gate_pass_custom_ui.js` - Gate Pass Item table custom ui and handling logic.
- `gate_entry/public/css/gate_pass.css` - Gate Pass Item table supporting css file.
- `gate_entry/gate_entry/report/material_reconciliation/material_reconciliation.py` - Material reconciliation report logic; ensure outbound entries are reconciled.
- `gate_entry/gate_entry/report/pending_gate_passes/pending_gate_passes.py` - Pending gate passes report; include outbound documents in queues.
- `gate_entry/gate_entry/doctype/gate_pass/test_gate_pass.py` - Automated tests for gate pass workflows.

### Notes

- Unit tests should typically be placed alongside the code files they are testing (e.g., `gate_pass.py` and `test_gate_pass.py` in the same directory).
- Use `bench --site <site-name> run-tests --doctype "Gate Pass"` to run server-side tests for this module.

## Tasks

- [ ] 1.0 Extend Gate Pass backend to support Sales Invoice and Delivery Note outbound flow
  - [x] 1.1 Review existing purchase/subcontract inbound implementation to understand current document linkage patterns and reused utilities.
  - [x] 1.2 Add support in `gate_pass.py` for selecting `Sales Invoice` or `Delivery Note`, fetching core header data, and assigning reference metadata to the gate pass.
  - [x] 1.3 Populate gate pass item child table from the reference document and enforce read-only dispatched quantities with appropriate validation errors on manual edits.
  - [x] 1.4 Ensure vehicle and driver fields remain editable when source data is missing, while tracking auto-filled values in the audit log.
- [ ] 2.0 Update Gate Pass UI for outbound guard experience and auto-population
  - [x] 2.1 Update `gate_pass.js` (and related form components) to drive document picker behaviour, trigger auto-fetch of items, vehicle, driver details, and current dispatch timestamp.
  - [x] 2.2 Adjust form layout to emphasise read-only dispatched quantities, hide unnecessary purchase-specific fields, and guide guards with helper text.
  - [x] 2.3 Add UI state for compliance warnings so guards clearly see why submission is blocked and what documents are missing.
  - [x] 2.4 Verify that workflow behaves correctly on mobile or touch terminals commonly used at the gate.
- [ ] 3.0 Enforce compliance checks and notifications for outbound submissions
  - [x] 3.1 Pull e-invoice and e-way bill status fields from the reference sales document during validation and store them on the gate pass for reporting.
  - [x] 3.2 Implement hard block logic in `gate_pass.py` that compares document value against `GST Settings.e_waybill_threshold`; prevent submission if required documents are missing.
  - [ ] 3.3 Assign the creator of the reference document to the gate pass (or the source document) when submission fails, and send a notification detailing missing compliance steps. *(De-scoped per latest direction)*
  - [ ] 3.4 Cover compliance validation paths with automated tests in `test_gate_pass.py`. *(Notification coverage no longer required.)*
- [x] 4.0 Enhance reporting for outbound gate pass visibility
  - [x] 4.1 Update `gate_register` report queries/filters to include outbound sales-based gate passes with clear direction indicators.
  - [x] 4.2 Extend `material_reconciliation` calculations to reconcile dispatched quantities from sales documents against inventory movement.
  - [x] 4.3 Ensure `pending_gate_passes` highlights outbound documents awaiting compliance completion or guard submission.
  - [x] 4.4 Add report tests or fixtures if the reporting framework supports them; otherwise provide manual verification steps.
- [x] 5.0 Validate ERPNext configurations, permissions, and audit logging
  - [x] 5.1 Confirm security guard roles have access to referenced sales documents and necessary GST settings without exposing sensitive financial data.
  - [x] 5.2 Document assumptions and required setup (e.g., vehicle/driver fields on Sales Invoice/Delivery Note, GST threshold configuration) in module README or internal wiki.
  - [x] 5.3 Verify audit trail entries capture auto-filled values, compliance warnings, and submission attempts for future audits.

### Manual Verification Notes

1. **Gate Register**
   - Load the report with `Entry Type` filter set to “Gate Out” and `Reference Type` “Sales Invoice” to confirm outbound passes appear with the new `Direction`, `Source Document`, and `Party` columns.
   - Validate that the `Material Summary` column shows dispatched quantities (matching the sales document) and that dynamic links open the source documents.
   - Review the summary widgets to ensure inbound/outbound counts reflect the visible dataset.
2. **Material Reconciliation**
   - Run the report for document type “Sales Invoice” and verify that `Gate Pass Qty` matches the corresponding `Reference Qty` pulled from sales documents.
   - Switch the filter to “Delivery Note” and ensure discrepancies surface when dispatched quantities differ.
   - Confirm inbound (Purchase/Subcontract) scenarios still reconcile as before.
3. **Pending Gate Passes**
   - Create or reuse draft Gate Out passes with missing e-invoice/e-way bill details; the report should flag them with a red `Compliance Status` pill and “Compliance pending” reason.
   - Generate a compliant draft (all documents generated) and confirm it shifts to “Awaiting Guard Submission” with a green status pill.
   - Validate that submitted inbound passes without receipts continue to appear under “Awaiting Receipt,” and summary widgets reflect compliance counts.

