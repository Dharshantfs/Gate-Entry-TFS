## Introduction

Extend the `gate_entry` app so that ERPNext Stock Entries of type **Send to Subcontractor** and **Material Transfer** flow seamlessly through gate operations. The feature must cover both outbound dispatches and inbound receipts, ensuring physical movements match authorised stock documents while reducing manual gate paperwork.

## Goals

- Achieve full gate coverage for Stock Entries using the supported types.
- Remove manual gate pass preparation for standard subcontracting and transfer movements.
- Prevent gate-logged quantities from ever exceeding the authorised Stock Entry amounts.

## User Stories

- As a Stores Executive, when I submit a Stock Entry (Send to Subcontractor or Material Transfer), I want the system to create an outbound gate pass automatically so the gate team receives dispatch instructions without re-entry. For Material Transfers, the Stock Entry must include an “External Transfer” checkbox; only when ticked should the system generate the gate pass (initially in `Draft`) because some transfers happen entirely within the plant.
- As a Security Guard, I want gate passes to show vehicle and item details so I can verify what is leaving or entering the plant.
- As a Stores Executive handling partial shipments, I want to split a Stock Entry across multiple gate passes while staying within the approved total.
- As a Stores Executive, I want to manually initiate a gate pass and link it to an existing Stock Entry when exceptional movements occur.
- As a Stores Executive, I want to cancel a gate pass that did not physically occur without cancelling the underlying Stock Entry.
- As a Quality Controller, I want to log lost or damaged material at the gate so the organisation can investigate discrepancies.
- As a Stores Executive receiving returning material, I want to use the original outbound Material Transfer as the reference for the inbound gate pass when the return Stock Entry is created only after the material re-enters the gate.

## Functional Requirements

1. **Scope detection:** Identify Stock Entries of type `Send to Subcontractor` and `Material Transfer` as eligible for gate integration.
2. **Automated gate pass creation:** On submission of an eligible Stock Entry, auto-create an outbound gate pass with document number, warehouses, party information, item rows, and quantities. For `Material Transfer`, only create the gate pass when the Stock Entry carries the “External Transfer” checkbox; newly created gate passes must start in `Draft` status.
3. **Inbound coverage:** Support inbound gate passes for returning material. These may be auto-created when the corresponding inbound Stock Entry is submitted, or manually created beforehand. Users must be able to reference the prior outbound Material Transfer when the inbound Stock Entry is prepared post-arrival.
4. **Multiple gate passes per Stock Entry:** Allow multiple gate passes against a single Stock Entry (for partial dispatch or receipt) while enforcing that the cumulative quantity per item never exceeds the Stock Entry total.
5. **Manual initiation:** Permit manual creation of gate passes that pull data from an existing Stock Entry, subject to the same quantity controls.
6. **Quantity validation:** Enforce remaining-quantity calculations per item at creation and submission of gate passes; reject attempts that overrun the available balance.
7. **Vehicle details capture:** Require fields for vehicle number, driver details, and related identifiers; reuse existing `gate_entry` UI components.
8. **Discrepancy logging:** Provide inputs to capture lost or damaged quantities, remarks, and responsibility without altering Stock Entry quantities.
9. **Status lifecycle:** Maintain statuses such as `Draft`, `Ready to Dispatch/Receive`, `In Transit`, `Completed`, and `Cancelled`, consistent with current app behaviour.
10. **Cancellation:** Enable cancellation or rejection of gate passes independently of the Stock Entry. Cancelled passes must release their reserved quantities back into the remaining balance.
11. **Document links:** Maintain bidirectional references between gate passes and their Stock Entry, including child-row identifiers where applicable.
12. **Audit trail:** Track all quantity allocations, updates, cancellations, and discrepancy records with timestamps and user IDs.
13. **Permissions:** Respect existing `gate_entry` role permissions; no additional approval workflow is required.
14. **Notifications (optional):** If notifications exist, alert relevant roles upon auto-created gate passes. Otherwise, note as future enhancement.
15. **Reporting integration:** Ensure newly created gate passes appear in current `gate_entry` reports without extra configuration.

## Non-Goals

- Do not support any Stock Entry types beyond `Send to Subcontractor` and `Material Transfer`.
- Do not introduce hardware integrations (e.g., weighing bridge, RFID) or modify existing valuation/accounting flows.
- Do not redesign the UI beyond the required field additions and validations.

## Design Considerations

- Follow existing `gate_entry` layouts for forms and listings.
- Present Stock Entry metadata (document number, warehouses, posting date, parties) prominently for gate staff.
- Maintain responsive design suitable for tablets or other gate devices.

## Technical Considerations

- Hook gate pass auto-creation into Stock Entry submission events, preferably via asynchronous jobs to keep submissions snappy.
- Store references to Stock Entry `name`, `stock_entry_type`, and row-level data in gate pass child tables.
- Reuse ERPNext utilities for quantity aggregation and validation wherever possible.
- Inherit existing permission logic within `gate_entry` for any new doctypes or fields.
- Reuse or extend existing discrepancy/comment models; add a dedicated child table only if necessary.
- Surface any asynchronous creation failures to the submitting user for manual recovery.

## Success Metrics

- 90% reduction in manual gate pass creation for subcontracting and external material transfers within three months.
- Zero audit findings where gate quantity exceeds Stock Entry quantity.
- ≥80% positive feedback from stores and gate personnel on reduced paperwork during the first month of use.

## Open Questions

- None.

