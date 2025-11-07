"""Pending Gate Passes report."""

from __future__ import annotations

from typing import Iterable

import frappe
from frappe import _
from frappe.utils import date_diff, getdate, nowdate


def execute(filters: dict | None = None):
    """Run the Pending Gate Passes report."""

    report_filters = frappe._dict(filters or {})
    columns = get_columns()
    data = get_data(report_filters)
    report_summary = get_report_summary(data)

    return columns, data, None, None, report_summary


def get_columns() -> list[dict[str, object]]:
    """Return column definitions for the report."""

    return [
        {
            "label": _("Gate Pass ID"),
            "fieldname": "gate_pass",
            "fieldtype": "Link",
            "options": "Gate Pass",
            "width": 160,
        },
        {
            "label": _("Date"),
            "fieldname": "gate_pass_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("Reference Document"),
            "fieldname": "reference_document",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("Reference Number"),
            "fieldname": "reference_number",
            "fieldtype": "Dynamic Link",
            "options": "reference_document",
            "width": 180,
        },
        {
            "label": _("Supplier"),
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 200,
        },
        {
            "label": _("Total Items"),
            "fieldname": "total_items",
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "label": _("Aging (Days)"),
            "fieldname": "aging",
            "fieldtype": "Int",
            "width": 110,
        },
    ]


def get_data(filters: frappe._dict) -> list[dict[str, object]]:
    """Fetch report rows based on user filters."""

    conditions: list[str] = ["gp.docstatus = 1"]
    # Gate pass is pending when no receipt is linked yet
    conditions.append("ifnull(gp.purchase_receipt, '') = ''")
    conditions.append("ifnull(gp.subcontracting_receipt, '') = ''")

    values: dict[str, object] = {}

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

    where_clause = " AND ".join(conditions)

    rows = frappe.db.sql(
        f"""
        SELECT
            gp.name AS gate_pass,
            gp.gate_pass_date,
            gp.document_reference,
            gp.reference_number,
            gp.supplier,
            COUNT(gpit.name) AS total_items
        FROM `tabGate Pass` gp
        LEFT JOIN `tabGate Pass Table` gpit ON gpit.parent = gp.name
        WHERE {where_clause}
        GROUP BY gp.name
        ORDER BY gp.gate_pass_date DESC, gp.name DESC
        """,
        values,
        as_dict=True,
    )

    today = getdate(nowdate())
    data: list[dict[str, object]] = []

    for row in rows:
        gate_pass_date = getdate(row.gate_pass_date)
        aging = date_diff(today, gate_pass_date)
        data.append(
            {
                "gate_pass": row.gate_pass,
                "gate_pass_date": gate_pass_date,
                "reference_document": row.document_reference,
                "reference_number": row.reference_number,
                "supplier": row.supplier,
                "total_items": int(row.total_items or 0),
                "aging": aging,
                "aging_color": get_aging_color(aging),
            }
        )

    return data


def get_report_summary(data: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    """Build summary widgets for the report."""

    data = list(data)
    if not data:
        return []

    total_items = sum(int(row.get("total_items", 0) or 0) for row in data)
    total_pending = len(data)

    return [
        {
            "label": _("Pending Gate Passes"),
            "value": total_pending,
            "indicator": "blue",
            "datatype": "Int",
        },
        {
            "label": _("Total Items"),
            "value": total_items,
            "indicator": "orange",
            "datatype": "Int",
        },
    ]


def get_aging_color(aging: int) -> str:
    """Return indicator color for the given aging value."""

    if aging <= 0:
        return "green"

    if aging <= 1:
        return "orange"

    return "red"

