# PRD: Update Existing Reports with Stock Entry Integration

## Introduction/Overview

The Gate Entry app currently has three reports (Pending Gate Passes, Gate Register, and Material Reconciliation) that track gate pass activities. With the Stock Entry integration now implemented (PRD-0003), Gate Passes can be created from Stock Entries for Material Transfers and Send to Subcontractor operations. However, the existing reports do not display Stock Entry information, limiting visibility into material movements originating from Stock Entries.

This feature will enhance all three reports to show Stock Entry references, aggregate data from Stock Entry sources, and provide better visibility into material movements across the organization.

## Goals

1. Display Stock Entry references in all three reports when Gate Passes are linked to Stock Entries
2. Aggregate and display Stock Entry metadata (type, warehouses, posting dates) in reports
3. Include Stock Entry quantities in Material Reconciliation report for accurate comparison
4. Maintain full backward compatibility with existing Gate Passes that reference other document types
5. Improve operational visibility into material movements originating from Stock Entries

## User Stories

- As a Store Manager, when I view the Pending Gate Passes report, I want to see which Stock Entry each gate pass is linked to so I can track material movements from their source documents.
- As a Security Guard, when I review the Gate Register, I want to see Stock Entry details (type, warehouses) so I can understand the context of each material movement.
- As a Quality Controller, when I run the Material Reconciliation report, I want to see Stock Entry quantities compared with Gate Pass quantities so I can identify discrepancies in Stock Entry-based movements.
- As a Store Manager, I want to filter reports by Stock Entry type (Material Transfer, Send to Subcontractor) so I can focus on specific movement categories.
- As a Store Manager, I want to see warehouse information from Stock Entries in reports so I can track material flow between locations.
- As a Store Manager, I want reports to show both outbound and return Stock Entry references so I can track complete material transfer cycles.

## Functional Requirements

### 1. Pending Gate Passes Report Updates

1. The report **must** display a "Stock Entry" column when `document_reference = "Stock Entry"`, showing the Stock Entry name as a clickable link.
2. The report **must** display a "Stock Entry Type" column showing "Material Transfer" or "Send to Subcontractor" for Stock Entry-based gate passes.
3. The report **must** display "Source Warehouses" and "Target Warehouses" columns for Stock Entry-based gate passes, showing all source and target warehouses from the Stock Entry (comma-separated if multiple).
4. The report **must** show Stock Entry posting date in addition to gate pass date for better chronological tracking.
5. The report **must** maintain all existing columns and functionality for non-Stock Entry gate passes.
6. The report **must** support filtering by Stock Entry type (Material Transfer, Send to Subcontractor, or All).
7. The report **must** support filtering by Stock Entry name/ID.
8. The report **must** aggregate Stock Entry metadata efficiently without impacting report performance.
9. The report **must** display Stock Entry item-level details (item code, item name, quantity, UOM) for each gate pass item when linked to Stock Entry.
10. The report **must** exclude cancelled Stock Entries from the report results (filter where `docstatus != 2`).

### 2. Gate Register Report Updates

11. The report **must** display a "Stock Entry" column when `document_reference = "Stock Entry"`, showing the Stock Entry name as a clickable link.
12. The report **must** display a "Stock Entry Type" column for Stock Entry-based gate passes.
13. The report **must** display "From Warehouses" and "To Warehouses" columns for Stock Entry-based gate passes, showing all source and target warehouses from the Stock Entry (comma-separated if multiple).
14. The report **must** show Stock Entry posting date and time when available.
15. The report **must** display "Outbound Transfer" reference for return material transfers, showing the original outbound Stock Entry.
16. The report **must** maintain all existing columns and functionality for non-Stock Entry gate passes.
17. The report **must** support filtering by Stock Entry type.
18. The report **must** support filtering by warehouse (source or target).
19. The report **must** format material summary to include Stock Entry context when applicable.
20. The report **must** display Stock Entry item-level details in the material summary when available.
21. The report **must** exclude cancelled Stock Entries from the report results (filter where `docstatus != 2`).

### 3. Material Reconciliation Report Updates

22. The report **must** include Stock Entry as a supported document type in reconciliation calculations.
23. The report **must** aggregate Stock Entry allocated item quantities (quantities already allocated to Gate Passes) for comparison with Gate Pass quantities, not total Stock Entry quantities.
24. The report **must** display Stock Entry reference number and type in the report columns.
25. The report **must** calculate discrepancies between Stock Entry allocated quantities and Gate Pass quantities per item.
26. The report **must** display Stock Entry item-level details (item code, item name, allocated quantity, UOM) for each reconciliation row.
27. The report **must** handle return material transfers by comparing return Stock Entry allocated quantities with inbound Gate Pass quantities.
28. The report **must** support filtering by Stock Entry type.
29. The report **must** support filtering by Stock Entry name/ID.
30. The report **must** maintain all existing reconciliation logic for Purchase Orders, Subcontracting Orders, Sales Invoices, and Delivery Notes.
31. The report **must** show all warehouse information (comma-separated if multiple) for Stock Entry-based reconciliations.
32. The report **must** exclude cancelled Stock Entries from reconciliation calculations (filter where `docstatus != 2`).

### 4. Data Aggregation Requirements

33. The system **must** efficiently query Stock Entry data using optimized SQL queries or cached lookups.
34. The system **must** aggregate Stock Entry item quantities correctly, accounting for partial allocations across multiple Gate Passes.
35. The system **must** handle all Stock Entry warehouses (source and target) and display them as comma-separated lists when multiple warehouses exist in a single Stock Entry.
36. The system **must** retrieve Stock Entry posting dates and times for chronological display.
37. The system **must** handle Stock Entry types (Material Transfer, Send to Subcontractor) and display them correctly.
38. The system **must** support both outbound and return Stock Entry references in data aggregation.
39. The system **must** retrieve and display Stock Entry item-level details (item code, item name, quantity, UOM) in reports.
40. The system **must** filter out cancelled Stock Entries (`docstatus = 2`) from all report queries and aggregations.
41. The system **must** calculate allocated quantities for Stock Entry items by summing quantities across all linked Gate Passes for Material Reconciliation.

### 5. Backward Compatibility

42. All reports **must** continue to work exactly as before for Gate Passes that reference Purchase Orders, Subcontracting Orders, Sales Invoices, or Delivery Notes.
43. Stock Entry columns **must** only appear or be populated when `document_reference = "Stock Entry"`.
44. Existing filters and functionality **must** remain unchanged for non-Stock Entry gate passes.
45. Report performance **must** not degrade for existing report queries.
46. The system **must** handle Gate Passes with missing Stock Entry references gracefully (show empty/null values).

### 6. User Interface

47. Stock Entry columns **must** be clearly labeled and positioned logically within each report.
48. Stock Entry links **must** open the Stock Entry form in a new tab/window when clicked.
49. The report filters **must** include Stock Entry-specific options without cluttering the interface.
50. The system **must** provide tooltips or help text explaining Stock Entry-related columns when applicable.

## Non-Goals (Out of Scope)

- Modifying the core Gate Pass DocType structure (only report display changes)
- Adding new report types or dashboards
- Real-time synchronization with Stock Entry changes (reports show current state)
- Modifying Stock Entry creation or validation logic
- Adding approval workflows or notifications
- Exporting reports to external systems or APIs
- Adding chart/visualization components to reports

## Design Considerations

- **Column Placement**: Stock Entry columns should be placed after existing reference columns but before party/vehicle columns for logical grouping.
- **Performance**: Use efficient JOINs or subqueries to fetch Stock Entry data. Consider caching frequently accessed Stock Entry metadata.
- **Filter Organization**: Add Stock Entry filters in a logical section without disrupting existing filter layout.
- **Data Display**: Show Stock Entry information in a consistent format across all three reports.
- **Responsive Design**: Ensure report tables remain readable on standard screen sizes with additional columns.

## Technical Considerations

- **Database Queries**: Extend existing report SQL queries to LEFT JOIN with `tabStock Entry` table when `document_reference = "Stock Entry"`.
- **Field Mapping**: Map Stock Entry fields to report columns:
  - `name` → Stock Entry reference
  - `stock_entry_type` → Stock Entry Type
  - `posting_date` → Stock Entry Posting Date
  - `posting_time` → Stock Entry Posting Time
  - All source warehouses from items (comma-separated) → From Warehouses
  - All target warehouses from items (comma-separated) → To Warehouses
  - Item-level details from `tabStock Entry Detail` → Item Code, Item Name, Quantity, UOM
- **Quantity Aggregation**: For Material Reconciliation, aggregate Stock Entry allocated item quantities (sum of quantities across all linked Gate Passes) and compare with Gate Pass item quantities, accounting for partial allocations. Do not use total Stock Entry quantities.
- **Cancelled Stock Entries**: Filter out cancelled Stock Entries (`docstatus = 2`) in all queries using `WHERE se.docstatus != 2` or equivalent conditions.
- **Return Transfers**: Handle `outbound_material_transfer` and `return_material_transfer` fields to show complete transfer cycles.
- **Constants**: Update `gate_entry.constants` if needed to include Stock Entry in reference lists.
- **Report Filters**: Extend report JavaScript files to add Stock Entry-specific filter options.
- **Performance Optimization**: Use database indexes on `document_reference` and `reference_number` fields. Consider materialized views or caching for large datasets.

## Success Metrics

- All three reports successfully display Stock Entry information for Stock Entry-based Gate Passes
- Report load times remain under 5 seconds for datasets with up to 10,000 Gate Passes
- Zero errors or data inconsistencies when displaying mixed Gate Pass types (Stock Entry and non-Stock Entry)
- 100% backward compatibility maintained for existing report functionality
- Users can successfully filter and analyze Stock Entry-based material movements within 2 weeks of deployment

## Resolved Decisions

The following decisions have been made based on requirements clarification:

1. **Item-Level Details**: Reports will show Stock Entry item-level details (item code, item name, quantity, UOM) rather than only aggregate document-level information. This provides better visibility into material movements.

2. **Material Reconciliation Quantity Comparison**: The Material Reconciliation report will compare Gate Pass quantities against Stock Entry allocated quantities (quantities already allocated to Gate Passes), not total Stock Entry quantities. This ensures accurate reconciliation of what has actually been processed through the gate.

3. **Warehouse Display**: All warehouses from a Stock Entry will be displayed (comma-separated if multiple), not just the primary source/target warehouse. This provides complete visibility into material flow across all warehouses involved in the transfer.

4. **Cancelled Stock Entries**: Cancelled Stock Entries will be excluded from all reports (filtered out where `docstatus = 2`). This ensures reports only show active, valid material movements.

