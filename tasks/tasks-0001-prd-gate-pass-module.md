# Task List: ERPNext Gate Pass Module Implementation

## Overview
This task list implements the requirements defined in `0001-prd-gate-pass-module.md`. The implementation focuses on Gate In functionality for Purchase Orders and Subcontracting Orders with seamless conversion to Purchase Receipts and Subcontracting Receipts.

## Current State Assessment
- ✅ Gate Pass DocType exists with basic structure
- ✅ Gate Pass Table child table exists
- ✅ Basic get_items() whitelisted method exists
- ✅ Custom HTML field placeholder exists
- ❌ No reports implemented yet
- ❌ Limited Purchase Order/Subcontracting Order integration
- ❌ No receipt creation functionality
- ❌ No proper role-based permissions

## Relevant Files

### DocTypes
- `gate_entry/gate_entry/doctype/gate_pass/gate_pass.json` - Gate Pass DocType definition (modify)
- `gate_entry/gate_entry/doctype/gate_pass/gate_pass.py` - Server-side controller (modify)
- `gate_entry/gate_entry/doctype/gate_pass/gate_pass.js` - Client-side scripts (modify)
- `gate_entry/gate_entry/doctype/gate_pass/test_gate_pass.py` - Unit tests (modify)
- `gate_entry/gate_entry/doctype/gate_pass_table/gate_pass_table.json` - Child table definition (modify)

### Reports
- `gate_entry/gate_entry/report/pending_gate_passes/` - Pending Gate Passes report (create)
- `gate_entry/gate_entry/report/pending_gate_passes/pending_gate_passes.py` - Report logic (create)
- `gate_entry/gate_entry/report/pending_gate_passes/pending_gate_passes.js` - Report filters (create)
- `gate_entry/gate_entry/report/gate_register/` - Gate Register report (create)
- `gate_entry/gate_entry/report/gate_register/gate_register.py` - Report logic (create)
- `gate_entry/gate_entry/report/gate_register/gate_register.js` - Report filters (create)
- `gate_entry/gate_entry/report/material_reconciliation/` - Material Reconciliation report (create)
- `gate_entry/gate_entry/report/material_reconciliation/material_reconciliation.py` - Report logic (create)
- `gate_entry/gate_entry/report/material_reconciliation/material_reconciliation.js` - Report filters (create)

### Custom Fields
- `gate_entry/gate_entry/custom_fields/purchase_receipt.py` - Custom fields for Purchase Receipt (create)
- `gate_entry/gate_entry/custom_fields/subcontracting_receipt.py` - Custom fields for Subcontracting Receipt (create)

### Fixtures
- `gate_entry/fixtures/custom_field.json` - Custom field definitions (create)
- `gate_entry/fixtures/property_setter.json` - Property setters if needed (create)

### Configuration
- `gate_entry/hooks.py` - App hooks configuration (modify)

### UI Assets
- `gate_entry/public/js/gate_pass_custom_ui.js` - Custom HTML UI for items list (create)
- `gate_entry/public/css/gate_pass.css` - Custom styles for Gate Pass form (create)

### Notes
- Follow Frappe/ERPNext coding conventions and naming standards
- Use ES6 JavaScript syntax for client-side scripts
- Ensure all whitelisted methods have proper permission checks
- Write comprehensive docstrings for all Python methods
- Add validation messages that are user-friendly

## Tasks

- [ ] 1.0 Update Gate Pass DocType Structure and Fields
  - [ ] 1.1 Modify `gate_pass.json` to update naming series to "GP-.####" format for fiscal year 2025-26
  - [ ] 1.2 Update Entry Type field to default to "Gate In" and make it read-only for initial stage
  - [ ] 1.3 Rename and restructure Reference Document fields (document_reference, reference_number) to match PRD specifications
  - [ ] 1.4 Add/update Supplier and Supplier Address fields with auto-fetch functionality. Auto fetch the Supplier and Supplier Address from the Document Reference and Reference Number field. For example. If Purchase Order DocType is selected and a Purchase Order is selected in Reference Number then use both these to fetch the supplier from the reference document. 
  - [ ] 1.5 Ensure Vehicle Number and Driver Name fields are mandatory
  - [ ] 1.6 Add Driver Contact Number field (Phone type, optional)
  - [ ] 1.7 Update Security Guard Name field to auto-populate with current user (frappe.session.user)
  - [ ] 1.8 Add/verify Gate Entry Time field (Time type, auto-populated)
  - [ ] 1.9 Add Company field as mandatory (Link to Company)
  - [ ] 1.10 Add status indicator fields: workflow_state or custom status field to track "Draft", "Submitted", "Receipt Created"
  - [ ] 1.11 Add reference fields to store created receipt details (purchase_receipt_reference, subcontracting_receipt_reference)
  - [ ] 1.12 Organize fields into logical sections as per PRD Design Considerations (4 main sections)
  - [ ] 1.13 Set proper field dependencies using `depends_on` expressions
  - [ ] 1.14 Update `is_submittable` to 1 and configure appropriate submission behavior

- [ ] 2.0 Implement Custom HTML UI for Items Management
  - [ ] 2.1 Create `gate_entry/public/js/gate_pass_custom_ui.js` for custom items UI component
  - [ ] 2.2 Design todo-list style HTML structure with Item Code, Item Name, and Received Qty columns
  - [ ] 2.3 Implement +/- icons for adding/removing items from the list
  - [ ] 2.4 Add (i) info icon that shows additional details (UOM, Ordered Qty, Pending Qty, Description) in a popover/tooltip
  - [ ] 2.5 Create `gate_entry/public/css/gate_pass.css` with styles for custom UI (modern, clean look)
  - [ ] 2.6 Implement color coding: red for items with pending quantity > 0, green for fully received items
  - [ ] 2.7 Add client-side validation to ensure only items from selected document reference can be added
  - [ ] 2.8 Implement real-time quantity validation (prevent over-receipt, ensure qty > 0)
  - [ ] 2.9 Ensure mobile responsiveness for tablet/phone usage by security guards
  - [ ] 2.10 Sync custom UI data with hidden `gate_pass_table` child table field for backend processing
  - [ ] 2.11 Handle form refresh and data persistence when switching between draft saves
  - [ ] 2.12 Add event listeners for form state changes (new, load, refresh, after_save)

- [ ] 3.0 Develop Purchase Order and Subcontracting Order Integration
  - [ ] 3.1 Update `get_items()` whitelisted method in `gate_pass.py` to accept document_reference and reference_number parameters
  - [ ] 3.2 Implement Purchase Order item fetching with fields: item_code, item_name, description, uom, qty (ordered quantity)
  - [ ] 3.3 Implement Subcontracting Order item fetching with same field structure as PO
  - [ ] 3.4 Create helper method `calculate_pending_quantity()` to compute pending qty for each item
  - [ ] 3.5 Query existing Gate Passes and Purchase Receipts to determine already received quantities
  - [ ] 3.6 Return JSON structure with item details including ordered_qty, received_qty, pending_qty
  - [ ] 3.7 Add permission check in `get_items()` to ensure user has read access to reference document
  - [ ] 3.8 Implement client-side `get_items` button click handler in `gate_pass.js`
  - [ ] 3.9 Position "Get Items" button below Reference Number field as per PRD
  - [ ] 3.10 Show/hide "Get Items" button based on whether reference_number is selected
  - [ ] 3.11 Implement auto-fetch of Supplier and Supplier Address when reference_number changes
  - [ ] 3.12 Add client-side filter for Reference Number dropdown to show only submitted POs/Subcontracting Orders
  - [ ] 3.13 Handle partial item selection - allow users to remove unwanted items before saving
  - [ ] 3.14 Display loading indicator while fetching items from server
  - [ ] 3.15 Show user-friendly error messages if reference document is invalid or has no items

- [ ] 4.0 Build Receipt Creation Functionality (Purchase Receipt & Subcontracting Receipt)
  - [ ] 4.1 Create whitelisted method `create_purchase_receipt()` in `gate_pass.py`
  - [ ] 4.2 Implement logic to create new Purchase Receipt document from Gate Pass data
  - [ ] 4.3 Map Gate Pass items to Purchase Receipt items with received quantities
  - [ ] 4.4 Set Supplier, Company, posting_date, posting_time from Gate Pass
  - [ ] 4.5 Add gate_pass_reference custom field link in created Purchase Receipt
  - [ ] 4.6 Handle item-level details: UOM, quantity, warehouse (use default warehouse)
  - [ ] 4.7 Return created Purchase Receipt name and redirect user to the new document
  - [ ] 4.8 Update Gate Pass status to "Receipt Created" after successful PR creation
  - [ ] 4.9 Store Purchase Receipt reference in Gate Pass (purchase_receipt_reference field)
  - [ ] 4.10 Add validation to prevent duplicate receipt creation from same Gate Pass
  - [ ] 4.11 Create whitelisted method `create_subcontracting_receipt()` in `gate_pass.py`
  - [ ] 4.12 Implement Subcontracting Receipt creation logic (mirror Purchase Receipt flow)
  - [ ] 4.13 Map appropriate fields specific to Subcontracting Receipt DocType
  - [ ] 4.14 Add client-side button "Create Purchase Receipt" in `gate_pass.js` (visible after submission)
  - [ ] 4.15 Add client-side button "Create Subcontracting Receipt" in `gate_pass.js`
  - [ ] 4.16 Show appropriate button based on document_reference type (PO vs Subcontracting Order)
  - [ ] 4.17 Disable "Create Receipt" buttons if receipt already created
  - [ ] 4.18 Position "Create Receipt" buttons at the top of form after submission
  - [ ] 4.19 Add confirmation dialog before creating receipt ("Create Purchase Receipt from this Gate Pass?")
  - [ ] 4.20 Show success message with link to created receipt document
  - [ ] 4.21 Refresh Gate Pass form after receipt creation to show updated status
  - [ ] 4.22 Handle error scenarios gracefully (insufficient permissions, validation failures)

- [ ] 5.0 Implement Reports and Analytics
  - [ ] 5.1 Create report directory: `gate_entry/gate_entry/report/pending_gate_passes/`
  - [ ] 5.2 Create `pending_gate_passes.json` with report metadata (is_standard, ref_doctype, columns)
  - [ ] 5.3 Implement `pending_gate_passes.py` with execute() method returning columns and data
  - [ ] 5.4 Query Gate Passes with status "Submitted" (not yet converted to receipts)
  - [ ] 5.5 Display columns: Gate Pass ID, Date, Reference Document, Reference Number, Supplier, Total Items, Aging (days)
  - [ ] 5.6 Create `pending_gate_passes.js` with filters: date range, supplier, company
  - [ ] 5.7 Calculate aging as (today - gate_pass_date) in days
  - [ ] 5.8 Add color indicators for aging (green < 1 day, yellow 1-2 days, red > 2 days)
  - [ ] 5.9 Create report directory: `gate_entry/gate_entry/report/gate_register/`
  - [ ] 5.10 Create `gate_register.json` with report metadata
  - [ ] 5.11 Implement `gate_register.py` showing daily log of all gate pass activities
  - [ ] 5.12 Display columns: Date, Time, Gate Pass ID, Entry Type, Vehicle Number, Driver Name, Supplier, Material Summary
  - [ ] 5.13 Create `gate_register.js` with filters: date range, entry type, supplier, vehicle number
  - [ ] 5.14 Format Material Summary as comma-separated list of items
  - [ ] 5.15 Enable Excel/PDF export functionality for Gate Register
  - [ ] 5.16 Create report directory: `gate_entry/gate_entry/report/material_reconciliation/`
  - [ ] 5.17 Create `material_reconciliation.json` with report metadata
  - [ ] 5.18 Implement `material_reconciliation.py` comparing gate pass vs receipt quantities
  - [ ] 5.19 Display columns: PO/SO Number, Item Code, Item Name, Gate Pass Qty, Receipt Qty, Discrepancy
  - [ ] 5.20 Highlight discrepancies in red where gate_pass_qty != receipt_qty
  - [ ] 5.21 Create `material_reconciliation.js` with filters: date range, document type, supplier
  - [ ] 5.22 Group results by Purchase Order / Subcontracting Order
  - [ ] 5.23 Add summary row showing total discrepancies

- [ ] 6.0 Configure Permissions and Roles
  - [ ] 6.1 Create custom role "Gate User" in ERPNext (if not exists)
  - [ ] 6.2 Add Gate User role permissions to Gate Pass: Create, Read, Submit (level 0)
  - [ ] 6.3 Configure Store Manager role permissions: Create, Read, Submit, Cancel (level 0)
  - [ ] 6.4 Configure Purchase User role permissions: Read only (level 0)
  - [ ] 6.5 Ensure System Manager has all permissions (level 0)
  - [ ] 6.6 Set permission level 1 for amend operation (only Store Manager and System Manager)
  - [ ] 6.7 Add role permissions via `gate_pass.json` permissions array
  - [ ] 6.8 Create permission query conditions if needed (user should only see their company's gate passes)
  - [ ] 6.9 Add has_permission() method in `gate_pass.py` if custom permission logic needed
  - [ ] 6.10 Configure report permissions: all roles should access reports
  - [ ] 6.11 Restrict receipt creation methods to Store Manager and System Manager roles only
  - [ ] 6.12 Add permission checks in whitelisted methods using frappe.has_permission()

- [ ] 7.0 Add Validations and Business Rules
  - [ ] 7.1 Implement validate() method in GatePass class in `gate_pass.py`
  - [ ] 7.2 Validate that at least one item exists in gate_pass_table before submission
  - [ ] 7.3 Validate that received_quantity > 0 for all items in the child table
  - [ ] 7.4 Ensure reference_number is selected when document_reference is set
  - [ ] 7.5 Validate that reference document (PO/SO) is in "Submitted" state
  - [ ] 7.6 Add validation to check vehicle_number and driver_name are not empty
  - [ ] 7.7 Implement on_submit() method to update status to "Submitted"
  - [ ] 7.8 Implement on_cancel() method to handle cancellation (update status, clear references)
  - [ ] 7.9 Validate that receipt hasn't been created before allowing cancellation
  - [ ] 7.10 Add validation in receipt creation methods to check Gate Pass is in submitted state
  - [ ] 7.11 Prevent multiple receipt creation from same Gate Pass (check receipt_reference field)
  - [ ] 7.12 Validate posting_date and posting_time are not in future
  - [ ] 7.13 Add before_save() hook to auto-populate security_guard_name with current user if empty
  - [ ] 7.14 Auto-populate posting_date and posting_time if not provided
  - [ ] 7.15 Validate supplier matches the supplier in reference document
  - [ ] 7.16 Add business rule: received quantities should not exceed ordered quantities (warning, not error)
  - [ ] 7.17 Implement client-side validation in `gate_pass.js` for immediate user feedback
  - [ ] 7.18 Show validation messages in user-friendly format with field highlighting

- [ ] 8.0 Create Custom Fields for Integration Points
  - [ ] 8.1 Create directory: `gate_entry/gate_entry/custom_fields/`
  - [ ] 8.2 Create `__init__.py` in custom_fields directory
  - [ ] 8.3 Create `purchase_receipt.py` to define custom fields for Purchase Receipt DocType
  - [ ] 8.4 Add custom field: `gate_pass_reference` (Link to Gate Pass) in Purchase Receipt
  - [ ] 8.5 Set field properties: read_only=1, insert_after="supplier", label="Gate Pass Reference"
  - [ ] 8.6 Create `subcontracting_receipt.py` to define custom fields for Subcontracting Receipt
  - [ ] 8.7 Add custom field: `gate_pass_reference` (Link to Gate Pass) in Subcontracting Receipt
  - [ ] 8.8 Set field properties same as Purchase Receipt
  - [ ] 8.9 Create installation method to add custom fields during app installation
  - [ ] 8.10 Create `gate_entry/gate_entry/setup.py` with after_install hook
  - [ ] 8.11 Implement `create_custom_fields()` method that uses frappe.get_doc to create custom fields
  - [ ] 8.12 Add fixtures configuration in `hooks.py` to export custom fields
  - [ ] 8.13 Configure fixtures: `fixtures = ["Custom Field"]`
  - [ ] 8.14 Update hooks.py with after_install hook pointing to setup.after_install
  - [ ] 8.15 Test custom field creation on a fresh installation
  - [ ] 8.16 Add doc_events hook in `hooks.py` to link Gate Pass when PR/SR is created
  - [ ] 8.17 Verify custom fields appear correctly in Purchase Receipt and Subcontracting Receipt forms

---

## Implementation Guidelines

### Testing Strategy
- Test each task incrementally before moving to the next
- Create test Purchase Orders and Subcontracting Orders for validation
- Verify all workflows: Create Gate Pass → Submit → Create Receipt
- Test partial deliveries (multiple Gate Passes for one PO)
- Validate permission-based access for different roles
- Test reports with various filters and date ranges

### Code Quality
- Follow PEP 8 style guide for Python code
- Use ESLint configured settings for JavaScript
- Add comprehensive docstrings to all methods
- Comment complex business logic
- Use meaningful variable and function names
- Handle all error cases gracefully

### Performance Considerations
- Index critical fields: reference_number, posting_date, status
- Optimize database queries (avoid N+1 queries)
- Use frappe.db.get_all() with specific fields instead of get_doc() where possible
- Cache reference document data when fetching items
- Limit report queries with proper date ranges

### User Experience
- Show loading indicators for async operations
- Provide clear success/error messages
- Auto-refresh forms after state changes
- Disable/hide irrelevant buttons based on context
- Ensure mobile-friendly layouts
- Use intuitive field labels and help text

---

**Status**: Sub-tasks generated. Ready for implementation.

