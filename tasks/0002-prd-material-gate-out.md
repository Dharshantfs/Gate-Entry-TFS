# Product Requirements Document: Material Gate Out via Sales Documents

## 1. Introduction / Overview
The Gate Pass module currently supports inbound material control tied to Purchase Orders and Subcontracting Orders. This iteration extends the module to handle outbound material dispatches initiated from `Sales Invoice` and `Delivery Note` documents. The security guard at the dispatch gate must be able to quickly select the correct sales document, confirm vehicle and driver details, and generate a gate pass without manually keying item quantities. The goal is to streamline the gate-out workflow, reduce data entry errors, and maintain compliance checks before materials leave the facility.

## 2. Goals
- Provide a guard-friendly workflow to create a gate pass for outbound shipments using either a `Sales Invoice` or a `Delivery Note`.
- Auto-populate vehicle, driver, dispatch timing, and line items from the referenced sales document to minimize manual input.
- Prevent manual overrides of dispatched quantities at the gate to ensure data integrity with the sales document.
- Ensure gate passes warn staff if required compliance documents (e-invoice, e-way bill) are missing before dispatch.
- Reflect outbound gate pass data across existing reports (`Gate Register`, `Material Reconciliation`, `Pending Gate Passes`).

## 3. User Stories
- As a **security guard**, I want to select a `Sales Invoice` or `Delivery Note` and have all relevant details auto-filled so I can process vehicles quickly.
- As a **security guard**, I want dispatched quantities to reflect the source document so I do not accidentally alter what was approved for shipment.
- As a **dispatch supervisor**, I want to be alerted if compliance documents are missing so I can resolve the issue before material leaves the premises.
- As a **materials manager**, I want outbound gate passes to appear in existing reports so I can reconcile movement of stock without using multiple systems.

## 4. Functional Requirements
1. The Gate Pass creation form must provide a selector for `Document Type` with options `Sales Invoice` and `Delivery Note`, and a field to search the corresponding document.
2. Upon selecting the reference document:
   - Fetch and populate vehicle number, driver name, and driver contact from the source document (if present).
   - Default the dispatch date and time to the current system timestamp (editable if necessary for back-dated entries).
   - Populate the gate pass item table with item code/name, description, UOM, and quantity from the source document.
3. The item table on the gate pass must display dispatched quantity as a **read-only** field; guards cannot modify item quantities or add/remove rows.
4. Gate pass numbering and metadata must continue to align with existing outbound/inbound configurations (reuse current numbering conventions).
5. Display a prominent warning message if either the e-invoice or e-way bill status for the referenced sales document indicates “Not Generated” or equivalent.
6. The gate pass cannot be submitted while the compliance warning is present unless the user acknowledges the warning (exact behavior to be decided under Open Questions).
7. Ensure vehicle and driver fields remain editable in case the guard needs to correct missing data; if the source document lacks these fields, leave them blank but highlight that information is required.
8. Update the `Gate Register`, `Material Reconciliation`, and `Pending Gate Passes` reports to include outbound records generated from sales documents, ensuring filters and totals reflect the new workflow.
9. Preserve existing validation rules for inbound gate passes while adding outbound-specific checks.
10. Log all auto-populated fields and data overrides (if allowed) in the audit trail for traceability.

## 5. Non-Goals (Out of Scope)
- Creating new report types or dashboards specific to material gate-out (only updates to existing reports are required).
- Supporting outbound gate passes for documents other than sales invoices or delivery notes.
- Modifying the core structure or lifecycle of `Sales Invoice` or `Delivery Note` doctypes beyond fields needed for auto-population.
- Integrating with third-party logistics systems or hardware (e.g., RFID readers, ANPR cameras).

## 6. Design Considerations
- Gate Pass form should visually differentiate auto-filled, read-only dispatched quantities to reduce guard confusion.
- Provide clear callouts around the compliance warning to prevent accidental submissions.
- If both `Sales Invoice` and `Delivery Note` exist for the same order, consider a note or hint to choose the document that reflects final dispatch quantities.

## 7. Technical Considerations
- Reuse existing controller logic in `gate_pass.py` for document linkage, adding branches for `Sales Invoice` and `Delivery Note`.
- Ensure the new outbound flow respects permission rules and role profiles assigned to security guards.
- Confirm the reports consume a shared data source so additions for outbound flow do not duplicate logic.
- Validate compliance fields by checking e-invoice and e-way bill statuses against ERPNext hooks/APIs already used by sales documents.
- Consider background jobs or caching if fetching large document data causes latency at the gate.

## 8. Success Metrics
- ≥90% of outbound gate passes created without manual edits to item quantities.
- Average gate pass creation time (from document selection to submission) reduced by 30% compared to manual entry baseline.
- Zero gate passes submitted without e-invoice/e-way bill when required (tracked via compliance warning logs).
- Positive feedback from security guards during user acceptance testing (qualitative survey).

## 9. Open Questions
- Should submission be hard-blocked when compliance documents are missing, or can guards override with acknowledgment? If override allowed, who is notified?
  - Based on e_waybill_threshold field in the GST Settings page if the value of the Sales Invoice or Delivery Note is more than the threshold then submission must be hard blocked and on failure of submission the user who created the reference document must be notified by assigning the user name to the reference document.
- How should the system behave if both e-invoice and e-way bill are not required for certain dispatches (e.g., low-value shipments)? Is there a configurable rule set?
  - Yes there is a setting in GST Settings Page called e_waybill_threshold if the value of Sales Invoice / Delivery Note is above this threshold then do not allow the submission of Gate Pass, clearly throw an error that required documents are not generated.
- Do we need to log the vehicle/driver auto-fill source (Sales Invoice vs Delivery Note) for auditing purposes? Yes
- Are there scenarios where the guard must attach additional documents (e.g., manual gate challans) before allowing dispatch? No

