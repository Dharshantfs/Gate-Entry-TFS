"""Gate Register report."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

import frappe
from frappe import _


def execute(filters: dict | None = None):
	"""Run the Gate Register report."""

	report_filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(report_filters)
	report_summary = get_report_summary(data)

	return columns, data, None, None, report_summary


def get_columns() -> list[dict[str, object]]:
	"""Return the Gate Register column configuration."""

	return [
		{
			"label": _("Date"),
			"fieldname": "gate_entry_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Time"),
			"fieldname": "gate_entry_time",
			"fieldtype": "Time",
			"width": 90,
		},
		{
			"label": _("Gate Pass ID"),
			"fieldname": "gate_pass",
			"fieldtype": "Link",
			"options": "Gate Pass",
			"width": 160,
		},
		{
			"label": _("Entry Type"),
			"fieldname": "entry_type",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Vehicle Number"),
			"fieldname": "vehicle_number",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Driver Name"),
			"fieldname": "driver_name",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 200,
		},
		{
			"label": _("Material Summary"),
			"fieldname": "material_summary",
			"fieldtype": "Data",
			"width": 400,
		},
	]


def get_data(filters: frappe._dict) -> list[dict[str, object]]:
	"""Query Gate Pass data and compose material summaries."""

	gate_pass_filters: dict[str, object] = {"docstatus": ["<", 2]}

	if filters.get("from_date") and filters.get("to_date"):
		gate_pass_filters["gate_entry_date"] = [
			"between",
			[filters.from_date, filters.to_date],
		]
	elif filters.get("from_date"):
		gate_pass_filters["gate_entry_date"] = [">=", filters.from_date]
	elif filters.get("to_date"):
		gate_pass_filters["gate_entry_date"] = ["<=", filters.to_date]

	if filters.get("entry_type"):
		gate_pass_filters["entry_type"] = filters.entry_type

	if filters.get("supplier"):
		gate_pass_filters["supplier"] = filters.supplier

	if filters.get("vehicle_number"):
		gate_pass_filters["vehicle_number"] = ["like", f"%{filters.vehicle_number}%"]

	if filters.get("company"):
		gate_pass_filters["company"] = filters.company

	gate_passes = frappe.get_all(
		"Gate Pass",
		filters=gate_pass_filters,
		fields=[
			"name",
			"gate_entry_date",
			"gate_entry_time",
			"entry_type",
			"vehicle_number",
			"driver_name",
			"supplier",
		],
		order_by="gate_entry_date desc, gate_entry_time desc, name desc",
	)

	if not gate_passes:
		return []

	gate_pass_names = [gp.name for gp in gate_passes]
	items = frappe.get_all(
		"Gate Pass Table",
		filters={"parent": ["in", gate_pass_names]},
		fields=["parent", "item_code", "item_name", "received_qty", "uom"],
		order_by="parent asc, idx asc",
	)

	items_by_parent: dict[str, list[dict[str, object]]] = defaultdict(list)
	for item in items:
		items_by_parent[item.parent].append(item)

	data: list[dict[str, object]] = []
	for gate_pass in gate_passes:
		material_summary = build_material_summary(items_by_parent.get(gate_pass.name, []))

		data.append(
			{
				"gate_entry_date": gate_pass.gate_entry_date,
				"gate_entry_time": gate_pass.gate_entry_time,
				"gate_pass": gate_pass.name,
				"entry_type": gate_pass.entry_type,
				"vehicle_number": gate_pass.vehicle_number,
				"driver_name": gate_pass.driver_name,
				"supplier": gate_pass.supplier,
				"material_summary": material_summary,
			}
		)

	return data


def build_material_summary(items: Iterable[dict[str, object]]) -> str:
	"""Create the comma-separated material summary string."""

	summary: list[str] = []
	for item in items:
		qty = item.get("received_qty") or 0
		qty_formatted = frappe.format_value(qty, {"fieldtype": "Float", "precision": 3})
		uom = item.get("uom") or ""
		qty_with_uom = f"{qty_formatted} {uom}".strip()
		summary.append(f"{item.get('item_code')} ({qty_with_uom})")

	return ", ".join(summary) if summary else "-"


def get_report_summary(data: Iterable[dict[str, object]]) -> list[dict[str, object]]:
	"""Return summary widgets for the register."""

	data = list(data)
	if not data:
		return []

	return [
		{
			"label": _("Gate Passes"),
			"value": len(data),
			"indicator": "blue",
			"datatype": "Int",
		}
	]
