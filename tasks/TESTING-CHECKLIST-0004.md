# Testing Checklist: Update Reports with Stock Entry Integration

This document provides a comprehensive testing checklist for validating the Stock Entry integration in all three reports.

## Pre-Testing Setup

1. Ensure you have test data:
   - At least 2-3 Stock Entries (Material Transfer type)
   - At least 2-3 Stock Entries (Send to Subcontractor type)
   - Gate Passes created from these Stock Entries
   - Gate Passes with other document types (Purchase Order, Sales Invoice, etc.)
   - At least one cancelled Stock Entry (for exclusion testing)
   - Return material transfers (inbound Gate Passes with outbound_material_transfer reference)

## Test Scenarios

### 1. Pending Gate Passes Report

#### 1.1 Basic Stock Entry Display
- [ ] Open Pending Gate Passes report
- [ ] Verify Stock Entry-based gate passes show:
  - Stock Entry column with clickable link
  - Stock Entry Type column (Material Transfer or Send to Subcontractor)
  - Source Warehouses column (comma-separated if multiple)
  - Target Warehouses column (comma-separated if multiple)
  - Stock Entry Posting Date column
  - Item Details column showing item codes and quantities

#### 1.2 Filters
- [ ] Test "Reference Type" filter with "Stock Entry" option
- [ ] Test "Stock Entry Type" filter:
  - Select "Material Transfer" - verify only Material Transfer gate passes shown
  - Select "Send to Subcontractor" - verify only Send to Subcontractor gate passes shown
  - Leave empty - verify all Stock Entry types shown
- [ ] Test "Stock Entry" filter (Link field):
  - Select a specific Stock Entry - verify only gate passes for that Stock Entry shown
- [ ] Verify filters work in combination (e.g., Stock Entry Type + Date Range)

#### 1.3 Backward Compatibility
- [ ] Verify non-Stock Entry gate passes (Purchase Order, Sales Invoice, etc.) still display correctly
- [ ] Verify Stock Entry columns show empty/null for non-Stock Entry gate passes
- [ ] Verify existing filters (supplier, customer, company) still work for all document types

#### 1.4 Cancelled Stock Entries
- [ ] Create a Gate Pass from a Stock Entry
- [ ] Cancel the Stock Entry
- [ ] Run Pending Gate Passes report
- [ ] Verify the cancelled Stock Entry's gate pass does NOT appear in results

#### 1.5 Mixed Document Types
- [ ] Run report with no filters
- [ ] Verify both Stock Entry and non-Stock Entry gate passes appear
- [ ] Verify Stock Entry columns populated only for Stock Entry gate passes

### 2. Gate Register Report

#### 2.1 Basic Stock Entry Display
- [ ] Open Gate Register report
- [ ] Verify Stock Entry-based gate passes show:
  - Stock Entry column with clickable link
  - Stock Entry Type column
  - SE Posting Date and SE Posting Time columns
  - From Warehouses column (all source warehouses, comma-separated)
  - To Warehouses column (all target warehouses, comma-separated)
  - Outbound Transfer column (for return material transfers)

#### 2.2 Warehouse Aggregation
- [ ] Create a Stock Entry with multiple items having different source/target warehouses
- [ ] Create a Gate Pass from this Stock Entry
- [ ] Run Gate Register report
- [ ] Verify "From Warehouses" shows ALL source warehouses (comma-separated)
- [ ] Verify "To Warehouses" shows ALL target warehouses (comma-separated)

#### 2.3 Return Material Transfers
- [ ] Create an outbound Stock Entry and Gate Pass
- [ ] Create a return Stock Entry and inbound Gate Pass (linked via outbound_material_transfer)
- [ ] Run Gate Register report
- [ ] Verify the inbound Gate Pass shows the original outbound Stock Entry in "Outbound Transfer" column

#### 2.4 Filters
- [ ] Test "Source Type" filter with "Stock Entry" option
- [ ] Test "Stock Entry Type" filter (should only appear when Source Type = Stock Entry)
- [ ] Test "Warehouse" filter:
  - Select a warehouse - verify only gate passes for Stock Entries using that warehouse shown
  - Test with source warehouse
  - Test with target warehouse
- [ ] Verify filters work in combination

#### 2.5 Material Summary
- [ ] Verify material summary includes Stock Entry item-level details when available
- [ ] Verify material summary format is readable and accurate

#### 2.6 Backward Compatibility
- [ ] Verify non-Stock Entry gate passes display correctly
- [ ] Verify Stock Entry columns show empty/null for non-Stock Entry gate passes
- [ ] Verify existing functionality (party display, vehicle details) still works

### 3. Material Reconciliation Report

#### 3.1 Basic Stock Entry Reconciliation
- [ ] Open Material Reconciliation report
- [ ] Select "Stock Entry" in Document Type filter
- [ ] Verify report shows:
  - Stock Entry column with clickable link
  - Stock Entry Type column
  - Warehouses column (comma-separated)
  - Item Code and Item Name columns
  - Gate Pass Qty column
  - Reference Qty column (allocated quantities)
  - Discrepancy column

#### 3.2 Allocated Quantities Calculation
- [ ] Create a Stock Entry with multiple items
- [ ] Create multiple Gate Passes from the same Stock Entry (partial allocations)
- [ ] Run Material Reconciliation report
- [ ] Verify "Reference Qty" = Sum of all Gate Pass quantities for each item
- [ ] Verify "Gate Pass Qty" matches "Reference Qty" (since allocated = sum of gate passes)
- [ ] Verify discrepancy is 0 (or matches any lost/damaged quantities if recorded)

#### 3.3 Return Material Transfers
- [ ] Create outbound Stock Entry with Gate Pass
- [ ] Create return Stock Entry (inbound) with Gate Pass
- [ ] Run Material Reconciliation report
- [ ] Verify return transfers are handled correctly
- [ ] Verify allocated quantities calculated correctly for returns

#### 3.4 Filters
- [ ] Test "Document Type" filter with "Stock Entry" option
- [ ] Test "Stock Entry Type" filter (should only appear when Document Type = Stock Entry)
- [ ] Test "Stock Entry" filter (Link field)
- [ ] Verify filters work in combination

#### 3.5 Mixed Document Types
- [ ] Run report with "All" document type
- [ ] Verify Stock Entry rows appear alongside Purchase Order, Sales Invoice, etc.
- [ ] Verify existing reconciliation logic still works for non-Stock Entry documents

#### 3.6 Cancelled Stock Entries
- [ ] Verify cancelled Stock Entries are excluded from reconciliation
- [ ] Verify no errors occur when cancelled Stock Entry is referenced

### 4. Performance Testing

#### 4.1 Large Dataset
- [ ] Create 1000+ Gate Passes (mix of Stock Entry and non-Stock Entry)
- [ ] Run each report
- [ ] Verify report loads in < 5 seconds
- [ ] Verify no timeout errors

#### 4.2 Query Optimization
- [ ] Monitor database queries during report execution
- [ ] Verify LEFT JOINs are used (not multiple queries)
- [ ] Verify indexes are utilized

### 5. Edge Cases

#### 5.1 Stock Entry with No Items
- [ ] Create a Stock Entry with no items (if possible)
- [ ] Create a Gate Pass from it
- [ ] Verify reports handle gracefully (no errors)

#### 5.2 Stock Entry with Single Warehouse
- [ ] Create Stock Entry where all items use same source/target warehouse
- [ ] Verify warehouse columns display correctly (not duplicated)

#### 5.3 Stock Entry with Multiple Warehouses
- [ ] Create Stock Entry with items using 5+ different warehouses
- [ ] Verify all warehouses appear in comma-separated format
- [ ] Verify warehouse filter works correctly

#### 5.4 Missing Stock Entry Reference
- [ ] Create a Gate Pass with `document_reference = "Stock Entry"` but invalid `reference_number`
- [ ] Verify reports handle gracefully (show empty/null values, no errors)

#### 5.5 Stock Entry Links
- [ ] Click on Stock Entry link in any report
- [ ] Verify Stock Entry form opens correctly
- [ ] Verify correct Stock Entry is displayed

### 6. UI/UX Testing

#### 6.1 Column Display
- [ ] Verify all Stock Entry columns are visible and properly labeled
- [ ] Verify column widths are appropriate
- [ ] Verify columns are in logical order (after reference columns, before party columns)

#### 6.2 Filter Visibility
- [ ] Verify Stock Entry filters only appear when relevant (using depends_on)
- [ ] Verify filter labels are clear and understandable

#### 6.3 Data Formatting
- [ ] Verify dates display correctly
- [ ] Verify quantities display with appropriate precision
- [ ] Verify warehouse lists are readable (comma-separated, not too long)

### 7. Integration Testing

#### 7.1 End-to-End Flow
- [ ] Create Stock Entry (Material Transfer, External Transfer checked)
- [ ] Submit Stock Entry (Gate Pass auto-created)
- [ ] View in Pending Gate Passes report - verify appears correctly
- [ ] Submit Gate Pass
- [ ] View in Gate Register report - verify appears correctly
- [ ] View in Material Reconciliation report - verify reconciliation correct

#### 7.2 Return Flow
- [ ] Create outbound Stock Entry and Gate Pass
- [ ] Create return Stock Entry and inbound Gate Pass
- [ ] Verify all three reports show return transfer correctly
- [ ] Verify outbound_material_transfer link is displayed

## Known Issues / Notes

- Stock Entry type filter in Pending Gate Passes is now optimized to run in SQL query
- Warehouse filter in Gate Register requires finding matching Stock Entries first, then filtering Gate Passes
- Material Reconciliation allocated quantities = sum of Gate Pass quantities (as per PRD requirement)

## Success Criteria

✅ All three reports successfully display Stock Entry information  
✅ Report load times remain under 5 seconds for 1000+ records  
✅ Zero errors when displaying mixed document types  
✅ 100% backward compatibility maintained  
✅ All filters work correctly  
✅ Cancelled Stock Entries excluded from all reports  
✅ Warehouse aggregation shows all warehouses correctly  
✅ Item-level details display in all reports  

