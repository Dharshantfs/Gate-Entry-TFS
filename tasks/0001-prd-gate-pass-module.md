# Product Requirements Document: ERPNext Gate Pass Module

## 1. Introduction/Overview

The Gate Pass Module is a comprehensive solution for managing and tracking material movement in and out of organizational premises. This module addresses critical needs around security, compliance, audit requirements, and inventory control by providing a systematic way to record, track, and reconcile material movements at the gate level.

In the initial stage, the module will focus on inward material movements (Gate In) for Purchase Orders and Subcontracting Orders. The system will enable security personnel and store managers to create gate passes when materials arrive, and seamlessly convert these gate passes into Purchase Receipts or Subcontracting Receipts for inventory management.

**Problem Statement:** Organizations lack a systematic way to track material entry at the gate level, leading to discrepancies between physical material received and inventory records, compliance issues, and security concerns.

**Goal:** Provide a robust gate management system that ensures all material movements are documented, validated, and seamlessly integrated with the procurement and inventory management workflow.

## 2. Goals

1. Enable tracking of all inward material movements at the organizational gate
2. Provide a secure and auditable record of material receipt with timestamps and personnel details
3. Integrate gate pass creation with existing Purchase Order and Subcontracting Order workflows
4. Facilitate seamless conversion of gate passes to Purchase Receipts/Subcontracting Receipts
5. Support multiple partial deliveries against a single Purchase Order or Subcontracting Order
6. Capture comprehensive details including vehicle, personnel, material, and attachments
7. Provide reporting capabilities for pending gate passes, gate register, and reconciliation
8. Establish role-based access control for gate pass operations

## 3. User Stories

### Security Personnel
- As a **security guard**, I want to create a gate pass when a vendor arrives with material, so that all inward movements are documented at the gate level
- As a **security guard**, I want to capture vehicle details and driver information, so that we have a complete record of who delivered the material
- As a **security guard**, I want to select a Purchase Order and see pending items, so that I can create a gate pass for the received material
- As a **security guard**, I want to create gate passes for Subcontracting Orders, so that raw material sent to subcontractors and finished goods received can be tracked

### Store/Inventory Manager
- As a **store manager**, I want to enter actual quantities received at the gate, so that discrepancies can be identified early
- As a **store manager**, I want to convert a submitted gate pass to a Purchase Receipt, so that the inventory is updated in the system
- As a **store manager**, I want to see all pending gate passes that haven't been converted to receipts, so that I can ensure timely inventory updates

### Purchase Department
- As a **purchase officer**, I want to view a gate register showing all material received against my Purchase Orders, so that I can track delivery performance
- As a **purchase officer**, I want to create multiple partial gate passes for a single Purchase Order, so that partial deliveries can be handled efficiently
- As a **purchase officer**, I want to see material received vs gate pass reconciliation reports, so that I can identify any discrepancies

### Subcontracting Manager
- As a **subcontracting manager**, I want to convert gate passes to Subcontracting Receipts, so that inventory is updated correctly

## 4. Functional Requirements

### 4.1 Gate Pass DocType

1. The system **must** provide a new DocType called "Gate Pass" with the following fields:
   - Gate Pass ID (auto-generated with naming series) 2025-26/00001
   - Entry Type (Select: "Gate In" - for initial stage)
   - Gate Pass Date and Time (auto-populated with current date/time, editable)

2. The system **must** capture reference document information:
   - Reference DocType (Link field based on DocType)
   - Reference Number (Dynamic Link field based on selected DocType)
   - Supplier (auto-fetched from reference document)
   - Supplier Address (auto-fetched from reference document)
   - Show the Address Display from the Reference Number document.

3. The system **must** capture vehicle and personnel details:
   - Vehicle Number (Data field, mandatory)
   - Driver Name (Data field, mandatory)
   - Driver Contact Number (Phone field, optional)
   - Security Guard Name (Data field, auto-populated with current user, editable)
   - Gate Entry Time (Time field, auto-populated)

4. The system **must** capture material details in a child table:
   - Item Code (Link to Item, fetched from reference document)
   - Item Name (fetched from Item)
   - Description (fetched from reference document)
   - UOM (Unit of Measurement)
   - Ordered Quantity (fetched from reference document, read-only)
   - Received Quantity (editable by user)
   - Pending Quantity (calculated: Ordered - Already Received against PO/SO)


### 4.2 Purchase Order Integration

7. When a user selects a Purchase Order in the Document Reference field, the system **must**:
   - Fetch all submitted Purchase Orders in the drop down of Reference Number dynamic link field.
   - Auto-populate the Supplier and Supplier Address, on selecting a Purchase Order in Reference Number field
   - Show a button "Get Items"
   - Display all items from the selected Purchase Order with their ordered quantities

8. The "Get Items from Purchase Order" button **must**:
   - Fetch all items from the Purchase Order
   - Display ordered quantity for each item
   - Calculate and display pending quantity (items not yet received via other gate passes/receipts)
   - Allow user to manually enter the received quantity for each item

9.  The system **must** allow users to:
   - Select specific items from the Purchase Order (partial entry)
   - Modify the received quantity for each item
   - Remove items not received in this delivery

10. The system **must** validate that:
    - Received quantity is entered for at least one item
    - Received quantity is greater than zero in case of normal Purchase Orders, incase of Rate Contracts the quantity in Purchase Order will be 0 and will have a flag called 'has_unit_price_items' in that case the validation be relaxed.

### 4.3 Subcontracting Order Integration

11. When a user selects a Subcontracting Order in the Document Reference field, the system **must**:
    - Fetch all submitted Subcontracting Orders in the drop down of Reference Number dynamic link field.
    - Auto-populate the Supplier and Supplier Address based on selected Subcontracting Order in the Reference Number field
    - Show a button "Get Items"
    - Display all items from the selected Subcontracting Order with their ordered quantities

12. The functionality for Subcontracting Orders **must** mirror the Purchase Order integration:
    - Fetch items with ordered and pending quantities
    - Allow partial item selection and quantity entry
    - Apply same validations as Purchase Orders

### 4.4 Gate Pass Submission and Status Management

13. A Gate Pass **must** start in "Draft" status when created

14. When a Gate Pass is submitted, the system **must**:
    - Change status to "Submitted"
    - Make all fields read-only except for action buttons
    - Show a button "Create Purchase Receipt" (for PO) or "Create Subcontracting Receipt" (for SO)

15. The system **must** allow multiple gate passes to be created for the same Purchase Order or Subcontracting Order to support partial deliveries

16. When a Purchase Receipt or Subcontracting Receipt is created from a Gate Pass, the status **must** change to "Receipt Created"

### 4.5 Purchase Receipt Creation

17. When the "Create Purchase Receipt" button is clicked, the system **must**:
    - Create a new Purchase Receipt document
    - Auto-populate all items from the Gate Pass with their received quantities
    - Link the Gate Pass reference in a custom field in Purchase Receipt
    - Set the Supplier, Company, and other header details from the Gate Pass
    - Copy item-level details including UOM, quantity, and remarks

18. The Purchase Receipt **must**:
    - Allow users to modify quantities if there are discrepancies between gate entry and actual store receipt
    - Maintain reference to the source Gate Pass
    - Follow standard ERPNext Purchase Receipt submission workflow

19. After successful Purchase Receipt creation, the system **must**:
    - Update Gate Pass status to "Receipt Created"
    - Store the Purchase Receipt reference in the Gate Pass
    - Prevent creation of duplicate Purchase Receipts from the same Gate Pass

### 4.6 Subcontracting Receipt Creation

20. When the "Create Subcontracting Receipt" button is clicked, the system **must**:
    - Create a new Subcontracting Receipt document
    - Auto-populate all items from the Gate Pass with their received quantities
    - Link the Gate Pass reference in a custom field in Subcontracting Receipt
    - Set the Supplier, Company, and other header details from the Gate Pass
    - Copy item-level details including UOM, quantity, and remarks

21. The Subcontracting Receipt **must**:
    - Allow users to modify quantities if there are discrepancies
    - Maintain reference to the source Gate Pass
    - Follow standard ERPNext Subcontracting Receipt submission workflow

22. After successful Subcontracting Receipt creation, the system **must**:
    - Update Gate Pass status to "Receipt Created"
    - Store the Subcontracting Receipt reference in the Gate Pass
    - Prevent creation of duplicate Subcontracting Receipts from the same Gate Pass

### 4.7 Permissions and Role-Based Access

23. The system **must** define the following roles with specific permissions:
    - **Gate User**: Can create, read, and submit Gate Passes
    - **Store Manager**: Can create, read, submit Gate Passes and create Receipts
    - **Purchase User**: Can read Gate Passes
    - **System Manager**: Full access to all Gate Pass operations

24. Role permissions **must** be configured as:
    - Gate User: Create, Read, Submit (no amend or cancel)
    - Store Manager: Create, Read, Submit, Create Receipt, Cancel
    - Purchase User: Read only
    - System Manager: All permissions

### 4.8 Reports and Tracking

25. The system **must** provide a "Pending Gate Passes" report showing:
    - All Gate Passes in "Submitted" status (not yet converted to Receipts)
    - Gate Pass ID, Date, Reference Document, Supplier, Items, Quantities
    - Aging (days since gate pass submission)
    - Filterable by date range, supplier, company

26. The system **must** provide a "Gate Register" report showing:
    - Daily log of all gate pass activities
    - Date, Time, Gate Pass ID, Entry Type, Vehicle Number, Supplier, Material Summary
    - Filterable by date range, entry type, supplier
    - Exportable to Excel/PDF

27. The system **must** provide a "Material Received vs Gate Pass Reconciliation" report showing:
    - Comparison between gate pass quantities and receipt quantities
    - Discrepancies highlighted for review
    - Purchase Order/Subcontracting Order wise summary
    - Filterable by date range, document type, supplier

### 4.9 Dashboard and Quick Actions

28. The system **should** provide a Gate Pass dashboard showing:
    - Count of pending gate passes
    - Today's gate entries
    - Recent gate pass activities
    - Quick links to create new gate pass

## 5. Non-Goals (Out of Scope for Initial Stage)

1. **Gate Out functionality** - Outward material movements will not be implemented in the initial stage
2. **Returnable Gate Pass** - Material that needs to come back will not be handled
3. **Non-returnable Gate Pass** - Classification beyond Gate In will not be implemented
4. **Material received without prior PO** - Emergency purchases without Purchase Orders are not supported
5. **Over-receipt handling** - System will not allow receiving more than ordered quantity
6. **Approval workflow** - No mandatory approval process before gate pass submission
7. **Date validations** - No strict validation for gate pass date vs receipt date
8. **Automatic gate pass closure** - System will not auto-close gate passes if material never received
9. **Integration with weighbridge systems** - Weight capture via external systems is out of scope
10. **Barcode/QR code scanning** - Material identification via barcode is not included
11. **Email notifications** - Automated alerts for pending gate passes not included in initial stage

## 6. Design Considerations

### 6.1 User Interface
- The Gate Pass form should follow standard ERPNext form layouts
- Use a clean, intuitive design with logical field grouping:
  - Section 1: Gate Pass Information (Entry Type, Date, Status)
  - Section 2: Reference Document & Reference Number (DocType, Name, Supplier)
  - Section 3: Vehicle & Personnel Details
  - Section 4: Material Details (child table) (Don't use the inbuilt Frappe Table, but create a custom HTML UI which resembles an editable list. It must have Item Code and Received Qty field only visible so that Users see the items clearly, An (i) Icon for more information about the item)

### 6.2 Child Table Layout
- Items child table should display columns:
  - Item Code | Item Name | Received Qty 
- Use color coding for pending quantities (red if pending > 0, green if fully received)

### 6.3 Action Buttons
- Place "Get Items" button prominently below Reference Number field.
- Place "Create Receipt" button at the top of the form after submission
- Disable "Create Receipt" button if receipt already created.

### 6.4 Mobile Responsiveness
- Forms should be mobile-friendly for security guards using tablets/phones at the gate

## 7. Technical Considerations

### 7.1 DocType Structure
- Create a new module called "Gate Entry"
- Gate Pass should be a submittable DocType
- Use standard ERPNext naming series with prefix "GP-"
- Child table for items should be a custom html UI which looks like a To Do list with a +/- icons to add/remove items. The items that should be able to be added must come from only selected document reference.

### 7.2 Custom Fields
- Add custom field in Purchase Receipt: `gate_pass_reference` (Link to Gate Pass)
- Add custom field in Subcontracting Receipt: `gate_pass_reference` (Link to Gate Pass)

### 7.3 Server-Side Scripts
- Write Python controller methods for:
  - `get_items_from_purchase_order()` - Fetch PO items with pending quantities
  - `get_items_from_subcontracting_order()` - Fetch SO items with pending quantities
  - `create_purchase_receipt()` - Generate PR from Gate Pass
  - `create_subcontracting_receipt()` - Generate SR from Gate Pass
  - `validate()` - Validate received quantities and business rules

### 7.4 Client-Side Scripts
- JavaScript for dynamic field behavior:
  - Auto-fetch supplier on reference document selection
  - Calculate pending quantities on-the-fly
  - Show/hide buttons based on status
  - Refresh form after receipt creation

### 7.5 Database Queries
- Optimize queries for calculating pending quantities
- Index fields: reference_name, reference_doctype, status, posting_date
- Consider performance for organizations with high gate pass volume

### 7.6 Integration Points
- Purchase Order: Read item details, quantities, supplier
- Subcontracting Order: Read item details, quantities, supplier
- Purchase Receipt: Create new document, link gate pass
- Subcontracting Receipt: Create new document, link gate pass
- Item Master: Fetch item details, UOM
- Supplier Master: Fetch supplier information

### 7.7 Hooks Configuration
- Configure appropriate hooks in `hooks.py`:
  - Document events for status updates
  - Permissions setup
  - Report registration

## 8. Success Metrics

1. **Adoption Rate**: 90% of all material receipts should have corresponding gate passes within 3 months of launch
2. **Discrepancy Reduction**: 50% reduction in inventory discrepancies between gate entry and store receipt
3. **Audit Compliance**: 100% of material movements should have documented gate passes with timestamps
4. **Time Efficiency**: Average time to create a gate pass should be less than 3 minutes
5. **Partial Delivery Handling**: System should successfully handle multiple partial deliveries for at least 80% of Purchase Orders
6. **Report Utilization**: Gate register and reconciliation reports should be used by at least 70% of active users
7. **User Satisfaction**: Achieve at least 4 out of 5 rating from security personnel and store managers on ease of use
8. **Receipt Conversion Rate**: At least 95% of submitted gate passes should be converted to receipts within 24 hours

## 9. Open Questions

1. **Photography Requirements**: What is the minimum number of photos required per gate pass? Should there be validation for mandatory photos? No photograp requirements

2. **Gate Pass Cancellation**: Under what circumstances should a gate pass be cancelled? Should cancelled gate passes be included in reports? No cancelled  gate passes in reports

3. **Retention Policy**: How long should gate pass records be retained? Are there any legal/compliance requirements for record retention? No compliance requriements but let erpnext handle it

4. **Printing Format**: Do we need a printable gate pass format that can be handed to the driver? What information should it include? Out of Scope

5. **Security Integration**: Should the system integrate with any physical security systems (boom barriers, CCTV, etc.)? Out of Scope

6. **Weighbridge Integration**: Is weighbridge integration needed in a future phase? If yes, what would be the expected workflow? Out of Scope

7. **Gate Pass Amendment**: After submission, if there's an error, should users be able to amend gate passes or only cancel and recreate? Yes users should be able to Amend using the usual frappe framework document flow.

8. **Multiple Gates**: For organizations with multiple entry/exit gates, should gate passes be tagged to specific gates? Out of Scope

9. **Offline Mode**: Should the system support offline gate pass creation for scenarios where network is unavailable at the gate? Out of Scope

10. **Notification System**: Should specific users be notified when gate passes are pending for more than X hours? Out of Scope

11. **Inspector Qualification**: Should there be a validation that the Inspector must be from a predefined list of qualified personnel? Out of Scope

12. **Item Inspection Integration**: Should the gate pass integrate with ERPNext's Quality Inspection module? Out of Scope

---

## Appendix: Future Enhancements (Post Initial Stage)

Based on the future scope discussion, the following features are planned for subsequent releases:

### Phase 2: Outward Material Movements
- Gate Out for Sales Returns (customer returning material)
- Gate Out for material sent for repairs/testing
- Gate Out for sample/demo material movements
- Returnable vs Non-returnable classification

### Phase 3: Advanced Features
- Email notifications for pending gate passes
- Approval workflow configuration
- Barcode/QR code scanning support
- Integration with weighbridge systems
- Multiple gate management
- Offline mode with synchronization

### Phase 4: Analytics and Intelligence
- Predictive analytics for material arrival times
- Vendor performance tracking based on gate pass data
- Automated discrepancy alerts
- Mobile app for gate personnel

---

**Document Version**: 1.0  
**Created**: October 17, 2025  
**Status**: Approved for Development  
**Target Audience**: Junior Developers, QA Team, Product Managers

