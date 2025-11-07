"""Material Reconciliation report."""

from __future__ import annotations

from typing import Iterable, NamedTuple

import frappe
from frappe import _
from frappe.utils import flt


class Key(NamedTuple):
    """Composite key used for aggregations."""

    document_reference: str
    reference_number: str
    item_code: str


def execute(filters: dict | None = None):
    """Run the Material Reconciliation report."""

    report_filters = frappe._dict(filters or {})
    columns = get_columns()
    data = get_data(report_filters)
    report_summary = get_report_summary(data)

    return columns, data, None, None, report_summary


def get_columns() -> list[dict[str, object]]:
    """Define report columns."""

    return [
        {
            "label": _("PO/SO Number"),
            "fieldname": "po_so_number",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 150,
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Gate Pass Qty"),
            "fieldname": "gate_pass_qty",
            "fieldtype": "Float",
            "width": 140,
        },
        {
            "label": _("Receipt Qty"),
            "fieldname": "receipt_qty",
            "fieldtype": "Float",
            "width": 140,
        },
        {
            "label": _("Discrepancy"),
            "fieldname": "discrepancy",
            "fieldtype": "Float",
            "width": 140,
        },
    ]


def get_data(filters: frappe._dict) -> list[dict[str, object]]:
    """Collect and merge data from Gate Passes and Receipts."""

    document_reference_filter = normalise_document_type(filters.get("document_type"))

    gate_pass_map = get_gate_pass_totals(filters, document_reference_filter)
    receipt_map = get_receipt_totals(filters, document_reference_filter)

    keys = set(gate_pass_map) | set(receipt_map)
    item_name_cache: dict[str, str] = {}

    data: list[dict[str, object]] = []
    for key in sorted(keys):
        gate_pass_row = gate_pass_map.get(key)
        receipt_row = receipt_map.get(key)

        gate_pass_qty = flt(gate_pass_row.get("gate_pass_qty") if gate_pass_row else 0)
        receipt_qty = flt(receipt_row.get("receipt_qty") if receipt_row else 0)
        discrepancy = gate_pass_qty - receipt_qty

        item_name = determine_item_name(gate_pass_row, receipt_row, item_name_cache)

        data.append(
            {
                "po_so_number": format_reference_label(key.document_reference, key.reference_number),
                "item_code": key.item_code,
                "item_name": item_name,
                "gate_pass_qty": gate_pass_qty,
                "receipt_qty": receipt_qty,
                "discrepancy": discrepancy,
                "has_discrepancy": abs(discrepancy) > 1e-6,
            }
        )

    return data


def normalise_document_type(value: str | None) -> str | None:
    """Return the canonical document reference value."""

    if not value or value in {"All", ""}:
        return None

    if value in {"Purchase Order", "Subcontracting Order"}:
        return value

    frappe.throw(_("Unsupported document type filter: {0}").format(value))
    return None


def get_gate_pass_totals(filters: frappe._dict, document_reference_filter: str | None):
    """Aggregate Gate Pass quantities."""

    conditions = ["gp.docstatus = 1"]
    values: dict[str, object] = {}

    if document_reference_filter:
        conditions.append("gp.document_reference = %(document_reference)s")
        values["document_reference"] = document_reference_filter
    else:
        conditions.append("gp.document_reference in ('Purchase Order', 'Subcontracting Order')")

    if filters.get("from_date"):
        conditions.append("gp.gate_pass_date >= %(from_date)s")
        values["from_date"] = filters.from_date

    if filters.get("to_date"):
        conditions.append("gp.gate_pass_date <= %(to_date)s")
        values["to_date"] = filters.to_date

    if filters.get("supplier"):
        conditions.append("gp.supplier = %(supplier)s")
        values["supplier"] = filters.supplier

    if filters.get("company"):
        conditions.append("gp.company = %(company)s")
        values["company"] = filters.company

    query = f"""
        SELECT
            gp.document_reference,
            gp.reference_number,
            gpit.item_code,
            gpit.item_name,
            SUM(gpit.received_qty) AS gate_pass_qty
        FROM `tabGate Pass` gp
        JOIN `tabGate Pass Table` gpit ON gpit.parent = gp.name
        WHERE {' AND '.join(conditions)}
        GROUP BY gp.document_reference, gp.reference_number, gpit.item_code
    """

    results = frappe.db.sql(query, values, as_dict=True)

    gate_pass_map: dict[Key, dict[str, object]] = {}
    for row in results:
        key = Key(row.document_reference, row.reference_number, row.item_code)
        gate_pass_map[key] = row

    return gate_pass_map


def get_receipt_totals(filters: frappe._dict, document_reference_filter: str | None):
    """Aggregate receipt quantities from Purchase Receipts and Subcontracting Receipts."""

    receipt_map: dict[Key, dict[str, object]] = {}

    if document_reference_filter in (None, "Purchase Order"):
        receipt_map.update(get_purchase_receipt_totals(filters))

    if document_reference_filter in (None, "Subcontracting Order"):
        receipt_map.update(get_subcontracting_receipt_totals(filters))

    return receipt_map


def get_purchase_receipt_totals(filters: frappe._dict):
    """Aggregate Purchase Receipt quantities keyed by Purchase Order and Item."""

    conditions = ["pr.docstatus = 1", "pri.purchase_order is not null"]
    values: dict[str, object] = {}

    if filters.get("from_date"):
        conditions.append("pr.posting_date >= %(pr_from_date)s")
        values["pr_from_date"] = filters.from_date

    if filters.get("to_date"):
        conditions.append("pr.posting_date <= %(pr_to_date)s")
        values["pr_to_date"] = filters.to_date

    if filters.get("supplier"):
        conditions.append("pr.supplier = %(pr_supplier)s")
        values["pr_supplier"] = filters.supplier

    if filters.get("company"):
        conditions.append("pr.company = %(pr_company)s")
        values["pr_company"] = filters.company

    query = f"""
        SELECT
            pri.purchase_order AS reference_number,
            pri.item_code,
            IFNULL(pri.item_name, '') AS item_name,
            SUM(pri.qty) AS receipt_qty
        FROM `tabPurchase Receipt Item` pri
        JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
        WHERE {' AND '.join(conditions)}
        GROUP BY pri.purchase_order, pri.item_code
    """

    results = frappe.db.sql(query, values, as_dict=True)

    receipt_map: dict[Key, dict[str, object]] = {}
    for row in results:
        key = Key("Purchase Order", row.reference_number, row.item_code)
        receipt_map[key] = row

    return receipt_map


def get_subcontracting_receipt_totals(filters: frappe._dict):
    """Aggregate Subcontracting Receipt quantities keyed by Subcontracting Order and Item."""

    conditions = ["sr.docstatus = 1", "sri.subcontracting_order is not null"]
    values: dict[str, object] = {}

    if filters.get("from_date"):
        conditions.append("sr.posting_date >= %(sr_from_date)s")
        values["sr_from_date"] = filters.from_date

    if filters.get("to_date"):
        conditions.append("sr.posting_date <= %(sr_to_date)s")
        values["sr_to_date"] = filters.to_date

    if filters.get("supplier"):
        conditions.append("sr.supplier = %(sr_supplier)s")
        values["sr_supplier"] = filters.supplier

    if filters.get("company"):
        conditions.append("sr.company = %(sr_company)s")
        values["sr_company"] = filters.company

    query = f"""
        SELECT
            sri.subcontracting_order AS reference_number,
            sri.item_code,
            IFNULL(sri.item_name, '') AS item_name,
            SUM(sri.qty) AS receipt_qty
        FROM `tabSubcontracting Receipt Item` sri
        JOIN `tabSubcontracting Receipt` sr ON sr.name = sri.parent
        WHERE {' AND '.join(conditions)}
        GROUP BY sri.subcontracting_order, sri.item_code
    """

    results = frappe.db.sql(query, values, as_dict=True)

    receipt_map: dict[Key, dict[str, object]] = {}
    for row in results:
        key = Key("Subcontracting Order", row.reference_number, row.item_code)
        receipt_map[key] = row

    return receipt_map


def determine_item_name(
    gate_pass_row: dict[str, object] | None,
    receipt_row: dict[str, object] | None,
    cache: dict[str, str],
) -> str:
    """Resolve an item name from available sources, with caching."""

    if gate_pass_row and gate_pass_row.get("item_name"):
        return gate_pass_row.get("item_name")

    if receipt_row and receipt_row.get("item_name"):
        return receipt_row.get("item_name")

    item_code = None
    if gate_pass_row and gate_pass_row.get("item_code"):
        item_code = gate_pass_row.get("item_code")
    elif receipt_row and receipt_row.get("item_code"):
        item_code = receipt_row.get("item_code")

    if not item_code:
        return ""

    if item_code not in cache:
        cache[item_code] = frappe.db.get_value("Item", item_code, "item_name") or ""

    return cache[item_code]


def get_report_summary(data: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    """Build summary indicators for the reconciliation report."""

    data = list(data)
    if not data:
        return []

    total_gate_pass_qty = sum(flt(row.get("gate_pass_qty"), 6) for row in data)
    total_receipt_qty = sum(flt(row.get("receipt_qty"), 6) for row in data)
    total_discrepancy = sum(flt(row.get("discrepancy"), 6) for row in data)

    indicator = "red" if abs(total_discrepancy) > 1e-6 else "green"

    return [
        {
            "label": _("Total Gate Pass Qty"),
            "value": total_gate_pass_qty,
            "indicator": "blue",
            "datatype": "Float",
        },
        {
            "label": _("Total Receipt Qty"),
            "value": total_receipt_qty,
            "indicator": "green",
            "datatype": "Float",
        },
        {
            "label": _("Total Discrepancy"),
            "value": total_discrepancy,
            "indicator": indicator,
            "datatype": "Float",
        },
    ]


def format_reference_label(document_reference: str, reference_number: str) -> str:
    """Format the PO/SO label shown in the report."""

    if document_reference == "Purchase Order":
        prefix = _("PO")
    elif document_reference == "Subcontracting Order":
        prefix = _("SO")
    else:
        prefix = document_reference

    return f"{reference_number} ({prefix})"

