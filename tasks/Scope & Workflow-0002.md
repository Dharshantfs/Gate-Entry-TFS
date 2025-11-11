Scope & Workflow
C) Allow both Sales Invoice and Delivery Note (current understanding)
Security Guard Workflow
4) Different flow (describe) -
Guard selects the document, loads items automatically
and the dispatched quantity will only be a read only field as
the sales invoice is already generated and security guard must
not alter the dispatched quantity.
Pre-Filled Fields
i) Vehicle number from the Sales Invoice or Delivery Note based on the document reference.
ii) Driver name and contact number from the Sales Invoice or Delivery Note based on the document reference.
iii) Dispatch date/time defaults to current
iv) Items will be fetched from the Sales Invoice or Delivery Note based on the document reference.
Reporting
α) Update existing Gate Pass reports only - No new reports are needed. Gate Register, Material Reconciliation, Pending Gate Passes.
Constraints/Compliance
Any regulatory logging/approvals needed before gate out? Yes
Details: Add a validation on the Gate Pass document to check if e-invoice and e-way bill are generated for the Sales Invoice or Delivery Note based on the document reference. If not, then show a warning message text on gate pass document.
