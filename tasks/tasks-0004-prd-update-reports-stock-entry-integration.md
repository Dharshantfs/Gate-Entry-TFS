# Task List: Update Existing Reports with Stock Entry Integration

## Overview
This task list implements the requirements defined in `0004-prd-update-reports-stock-entry-integration.md`. The implementation focuses on enhancing all three existing reports (Pending Gate Passes, Gate Register, and Material Reconciliation) to display Stock Entry information, aggregate Stock Entry data, and provide filtering capabilities while maintaining full backward compatibility.

## Current State Assessment
- ✅ Three reports exist: Pending Gate Passes, Gate Register, Material Reconciliation
- ✅ Reports support Purchase Orders, Subcontracting Orders, Sales Invoices, and Delivery Notes
- ✅ Stock Entry integration exists in Gate Pass DocType (from PRD-0003)
- ✅ Constants file defines reference types and party fields
- ❌ Reports do not display Stock Entry information
- ❌ Reports do not filter by Stock Entry type or name
- ❌ Material Reconciliation does not include Stock Entry quantities
- ❌ No warehouse aggregation from Stock Entries

## Relevant Files

- `gate_entry/gate_entry/constants.py` - Constants file (modified to add Stock Entry to ALL_REFERENCES)
- `gate_entry/gate_entry/stock_integration/report_utils.py` - New utility file for Stock Entry report functions (created)
- `gate_entry/gate_entry/report/pending_gate_passes/pending_gate_passes.py` - Pending Gate Passes report logic (modified to add Stock Entry columns, filters, and data aggregation)
- `gate_entry/gate_entry/report/pending_gate_passes/pending_gate_passes.js` - Pending Gate Passes report filters (modified to add Stock Entry filters)
- `gate_entry/gate_entry/report/gate_register/gate_register.py` - Gate Register report logic (modified to add Stock Entry columns, warehouse aggregation, and filters)
- `gate_entry/gate_entry/report/gate_register/gate_register.js` - Gate Register report filters (modified to add Stock Entry type and warehouse filters)
- `gate_entry/gate_entry/report/material_reconciliation/material_reconciliation.py` - Material Reconciliation report logic (modified to add Stock Entry allocated quantities calculation and columns)
- `gate_entry/gate_entry/report/material_reconciliation/material_reconciliation.js` - Material Reconciliation report filters (modified to add Stock Entry filters)

### Notes

- All reports follow a pattern: Python file contains `execute()` function and data aggregation logic, JavaScript file contains filter definitions and formatters
- Stock Entry data must be joined using LEFT JOIN to maintain backward compatibility
- Cancelled Stock Entries (`docstatus = 2`) must be excluded from all queries
- Warehouse information must be aggregated from `tabStock Entry Detail` table
- Allocated quantities for Material Reconciliation must be calculated by summing Gate Pass quantities per Stock Entry item

## Tasks

- [x] 1.0 Update Constants and Shared Utilities
  - [x] 1.1 Update `gate_entry/constants.py` to add "Stock Entry" to `ALL_REFERENCES` constant
  - [x] 1.2 Create utility function `get_stock_entry_metadata()` to fetch Stock Entry header data (type, posting_date, posting_time)
  - [x] 1.3 Create utility function `get_stock_entry_warehouses()` to aggregate all source and target warehouses from Stock Entry items (returns comma-separated lists)
  - [x] 1.4 Create utility function `get_stock_entry_item_details()` to fetch item-level details (item_code, item_name, quantity, uom) from Stock Entry
  - [x] 1.5 Create utility function `get_stock_entry_allocated_quantities()` to calculate allocated quantities per item by summing Gate Pass quantities for Material Reconciliation
  - [x] 1.6 Add helper function to check if Stock Entry is cancelled (`docstatus = 2`) and should be excluded

- [x] 2.0 Enhance Pending Gate Passes Report
  - [x] 2.1 Update `pending_gate_passes.py` `get_columns()` to add Stock Entry columns: "Stock Entry" (Link), "Stock Entry Type" (Data), "Source Warehouses" (Data), "Target Warehouses" (Data), "Stock Entry Posting Date" (Date)
  - [x] 2.2 Modify `fetch_inbound_pending()` to LEFT JOIN with `tabStock Entry` when `document_reference = "Stock Entry"` and exclude cancelled Stock Entries (`se.docstatus != 2`)
  - [x] 2.3 Modify `fetch_outbound_pending()` to LEFT JOIN with `tabStock Entry` when `document_reference = "Stock Entry"` and exclude cancelled Stock Entries
  - [x] 2.4 Add Stock Entry metadata fields to SELECT queries: `se.name AS stock_entry`, `se.stock_entry_type`, `se.posting_date AS se_posting_date`
  - [x] 2.5 Create function `get_stock_entry_data_for_pending()` to aggregate Stock Entry warehouses and item details for each gate pass
  - [x] 2.6 Update `get_data()` to populate Stock Entry columns in data rows when `document_reference = "Stock Entry"`
  - [x] 2.7 Update `fetch_inbound_pending()` and `fetch_outbound_pending()` to handle Stock Entry filter in `document_reference_filter` parameter
  - [x] 2.8 Add Stock Entry type filter condition to WHERE clauses when `filters.get("stock_entry_type")` is provided
  - [x] 2.9 Add Stock Entry name/ID filter condition when `filters.get("stock_entry")` is provided
  - [x] 2.10 Update `pending_gate_passes.js` to add "Stock Entry" option to `document_reference` filter dropdown
  - [x] 2.11 Add new filter field `stock_entry_type` with options: "", "Material Transfer", "Send to Subcontractor"
  - [x] 2.12 Add new filter field `stock_entry` (Link to Stock Entry) for filtering by specific Stock Entry
  - [x] 2.13 Update formatter in `pending_gate_passes.js` to handle Stock Entry link formatting (make clickable)

- [x] 3.0 Enhance Gate Register Report
  - [x] 3.1 Update `gate_register.py` `get_columns()` to add Stock Entry columns: "Stock Entry" (Link), "Stock Entry Type" (Data), "From Warehouses" (Data), "To Warehouses" (Data), "Stock Entry Posting Date" (Date), "Stock Entry Posting Time" (Time), "Outbound Transfer" (Link) for returns
  - [x] 3.2 Modify `get_data()` to LEFT JOIN with `tabStock Entry` when filtering for Stock Entry-based gate passes
  - [x] 3.3 Create function `get_stock_entry_data_for_register()` to fetch and aggregate Stock Entry metadata (type, warehouses, posting dates) for gate passes
  - [x] 3.4 Update warehouse aggregation to use `get_stock_entry_warehouses()` utility to get all warehouses (comma-separated)
  - [x] 3.5 Add logic to populate "Outbound Transfer" column from `outbound_material_transfer` field for return material transfers
  - [x] 3.6 Update `get_data()` to exclude cancelled Stock Entries in WHERE clause when joining with Stock Entry table
  - [x] 3.7 Update material summary building to include Stock Entry item-level details when available
  - [x] 3.8 Add Stock Entry type filter to `gate_pass_filters` when `filters.get("stock_entry_type")` is provided
  - [x] 3.9 Add warehouse filter logic to filter by source or target warehouse from Stock Entry items
  - [x] 3.10 Update `gate_register.js` to add "Stock Entry" option to `document_reference` filter dropdown
  - [x] 3.11 Add new filter field `stock_entry_type` with options: "", "Material Transfer", "Send to Subcontractor"
  - [x] 3.12 Add new filter field `warehouse` (Link to Warehouse) for filtering by source or target warehouse

- [x] 4.0 Enhance Material Reconciliation Report
  - [x] 4.1 Update `material_reconciliation.py` `get_columns()` to add "Stock Entry" column (Link) and ensure Stock Entry reference is displayed in "Reference Document" column
  - [x] 4.2 Update `SUPPORTED_DOCUMENT_REFERENCES` to include "Stock Entry"
  - [x] 4.3 Create function `get_stock_entry_allocated_totals()` to aggregate Stock Entry allocated quantities per item (sum of Gate Pass quantities)
  - [x] 4.4 Implement allocated quantity calculation: query all Gate Passes linked to Stock Entry and sum quantities per item_code
  - [x] 4.5 Update `get_receipt_totals()` to call `get_stock_entry_allocated_totals()` when `document_reference_filter` is None or "Stock Entry"
  - [x] 4.6 Modify `get_stock_entry_allocated_totals()` to handle return material transfers by checking `outbound_material_transfer` and `return_material_transfer` fields
  - [x] 4.7 Update `get_gate_pass_totals()` to include Stock Entry in document_reference filter conditions
  - [x] 4.8 Add Stock Entry metadata (type, warehouses) to reconciliation data rows
  - [x] 4.9 Update `get_data()` to populate Stock Entry item-level details (item_code, item_name, allocated quantity, UOM) in reconciliation rows
  - [x] 4.10 Ensure `get_stock_entry_allocated_totals()` excludes cancelled Stock Entries (`docstatus != 2`)
  - [x] 4.11 Update `normalise_document_type()` to accept "Stock Entry" as valid document type
  - [x] 4.12 Add warehouse information aggregation for Stock Entry-based reconciliations (comma-separated if multiple)
  - [x] 4.13 Update `material_reconciliation.js` to add "Stock Entry" option to `document_type` filter dropdown
  - [x] 4.14 Add new filter field `stock_entry_type` with options: "All", "Material Transfer", "Send to Subcontractor"
  - [x] 4.15 Add new filter field `stock_entry` (Link to Stock Entry) for filtering by specific Stock Entry
  - [x] 4.16 Update formatter to handle Stock Entry link formatting if needed

- [x] 5.0 Testing and Validation
  - [x] 5.1 Test Pending Gate Passes report with Stock Entry-based gate passes (both Material Transfer and Send to Subcontractor)
  - [x] 5.2 Test Pending Gate Passes report with mixed document types (Stock Entry + Purchase Order) to verify backward compatibility
  - [x] 5.3 Test Pending Gate Passes report filters: Stock Entry type filter, Stock Entry name filter
  - [x] 5.4 Verify cancelled Stock Entries are excluded from Pending Gate Passes report
  - [x] 5.5 Test Gate Register report with Stock Entry gate passes and verify warehouse aggregation (all warehouses shown, comma-separated)
  - [x] 5.6 Test Gate Register report with return material transfers to verify "Outbound Transfer" column
  - [x] 5.7 Test Gate Register report filters: Stock Entry type, warehouse filter
  - [x] 5.8 Verify Gate Register report maintains all existing functionality for non-Stock Entry gate passes
  - [x] 5.9 Test Material Reconciliation report with Stock Entry allocated quantities calculation
  - [x] 5.10 Verify Material Reconciliation allocated quantities match sum of Gate Pass quantities per Stock Entry item
  - [x] 5.11 Test Material Reconciliation with return material transfers
  - [x] 5.12 Test Material Reconciliation with mixed document types to ensure existing logic still works
  - [x] 5.13 Verify cancelled Stock Entries are excluded from Material Reconciliation
  - [x] 5.14 Test report performance with large datasets (1000+ gate passes) to ensure queries remain efficient
  - [x] 5.15 Verify all Stock Entry columns show empty/null values for non-Stock Entry gate passes (backward compatibility)
  - [x] 5.16 Test item-level details display in all three reports
  - [x] 5.17 Verify Stock Entry links are clickable and open Stock Entry form correctly
  - [x] 5.18 Test edge cases: Stock Entry with no items, Stock Entry with single warehouse, Stock Entry with multiple warehouses

