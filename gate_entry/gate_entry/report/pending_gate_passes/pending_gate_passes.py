"""Pending Gate Passes report."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

import frappe
from frappe import _
from frappe.utils import cint, cstr, date_diff, flt, getdate, nowdate

from gate_entry.gate_entry.doctype.gate_pass.gate_pass import get_gst_settings, is_generated_status

INBOUND_REFERENCES = {"Purchase Order", "Subcontracting Order"}
OUTBOUND_REFERENCES = {"Sales Invoice", "Delivery Note"}
REFERENCE_PARTY_FIELDS = {
	"Purchase Order": ("supplier", "supplier_name"),
	"Subcontracting Order": ("supplier", "supplier_name"),
	"Sales Invoice": ("customer", "customer_name"),
	"Delivery Note": ("customer", "customer_name"),
}
REFERENCE_TOTAL_FIELDS = (
	"rounded_total",
	"grand_total",
	"base_grand_total",
	"net_total",
	"total",
	"base_total",
)


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
			"label": _("Direction"),
			"fieldname": "direction",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Status"),
			"fieldname": "pending_reason",
			"fieldtype": "Data",
			"width": 200,
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
			"label": _("Party"),
			"fieldname": "party_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Compliance Status"),
			"fieldname": "compliance_status",
			"fieldtype": "Data",
			"width": 180,
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

	entry_type_filter = filters.get("entry_type")
	document_reference_filter = filters.get("document_reference")

	inbound_rows = fetch_inbound_pending(filters, entry_type_filter, document_reference_filter)
	outbound_rows = fetch_outbound_pending(filters, entry_type_filter, document_reference_filter)

	rows = inbound_rows + outbound_rows
	if not rows:
		return []

	# Sort by pending date (newest first) then by Gate Pass ID
	rows.sort(key=lambda row: (resolve_pending_date(row), row.gate_pass), reverse=True)

	parties = get_reference_parties(rows)
	gst_settings = get_gst_settings() if outbound_rows else frappe._dict()
	reference_totals: dict[tuple[str, str], float] = {}

	today = getdate(nowdate())
	data: list[dict[str, object]] = []

	for row in rows:
		party_key = (row.document_reference, row.reference_number)
		party_details = parties.get(party_key, {})
		party_name = (
			party_details.get("party_name")
			or party_details.get("party")
			or row.get("supplier")
			or ""
		)

		if filters.get("customer"):
			if row.entry_type == "Gate In":
				continue
			if party_details.get("party") != filters.customer:
				continue

		if filters.get("supplier") and row.entry_type == "Gate Out":
			continue

		pending_date = resolve_pending_date(row)
		aging = date_diff(today, pending_date)

		if row.entry_type == "Gate In":
			pending_reason = _("Awaiting Receipt")
			compliance_status = "-"
			compliance_pending = False
		else:
			pending_reason, compliance_status, compliance_pending = evaluate_outbound_pending(
				row, gst_settings, reference_totals
			)

		data.append(
			{
				"gate_pass": row.gate_pass,
				"direction": row.entry_type,
				"pending_reason": pending_reason,
				"gate_pass_date": pending_date,
				"reference_document": row.document_reference,
				"reference_number": row.reference_number,
				"party_name": party_name,
				"compliance_status": compliance_status,
				"total_items": int(row.total_items or 0),
				"aging": aging,
				"aging_color": get_aging_color(aging),
				"compliance_pending": compliance_pending,
			}
		)

	return data


def fetch_inbound_pending(
	filters: frappe._dict,
	entry_type_filter: str | None,
	document_reference_filter: str | None,
) -> list[frappe._dict]:
	"""Return pending inbound gate passes (awaiting receipts)."""

	if entry_type_filter and entry_type_filter not in ("", "Gate In", None):
		return []

	if document_reference_filter and document_reference_filter not in INBOUND_REFERENCES:
		return []

	conditions = [
		"gp.docstatus = 1",
		"gp.entry_type = 'Gate In'",
		"ifnull(gp.purchase_receipt, '') = ''",
		"ifnull(gp.subcontracting_receipt, '') = ''",
	]

	values: dict[str, object] = {}

	if document_reference_filter:
		conditions.append("gp.document_reference = %(document_reference)s")
		values["document_reference"] = document_reference_filter
	else:
		allowed_inbound = "', '".join(sorted(INBOUND_REFERENCES))
		conditions.append(f"gp.document_reference in ('{allowed_inbound}')")

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

	return frappe.db.sql(
		f"""
        SELECT
            gp.name AS gate_pass,
            gp.entry_type,
            gp.docstatus,
            gp.gate_pass_date,
            gp.creation,
            COALESCE(gp.gate_pass_date, DATE(gp.creation)) AS pending_date,
            gp.document_reference,
            gp.reference_number,
            gp.supplier,
            gp.company,
            NULL AS e_invoice_status,
            NULL AS e_waybill_status,
            COUNT(gpit.name) AS total_items
        FROM `tabGate Pass` gp
        LEFT JOIN `tabGate Pass Table` gpit ON gpit.parent = gp.name
        WHERE {where_clause}
        GROUP BY gp.name
        ORDER BY pending_date DESC, gp.name DESC
        """,
		values,
		as_dict=True,
	)


def fetch_outbound_pending(
	filters: frappe._dict,
	entry_type_filter: str | None,
	document_reference_filter: str | None,
) -> list[frappe._dict]:
	"""Return outbound gate passes awaiting submission or compliance."""

	if entry_type_filter and entry_type_filter not in ("", "Gate Out", None):
		return []

	if document_reference_filter and document_reference_filter not in OUTBOUND_REFERENCES:
		return []

	if filters.get("supplier"):
		return []

	conditions = [
		"gp.docstatus = 0",
		"gp.entry_type = 'Gate Out'",
	]
	values: dict[str, object] = {}

	if document_reference_filter:
		conditions.append("gp.document_reference = %(document_reference)s")
		values["document_reference"] = document_reference_filter
	else:
		allowed_outbound = "', '".join(sorted(OUTBOUND_REFERENCES))
		conditions.append(f"gp.document_reference in ('{allowed_outbound}')")

	if filters.get("from_date"):
		conditions.append("COALESCE(gp.gate_pass_date, DATE(gp.creation)) >= %(from_date)s")
		values["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("COALESCE(gp.gate_pass_date, DATE(gp.creation)) <= %(to_date)s")
		values["to_date"] = filters.to_date

	if filters.get("company"):
		conditions.append("gp.company = %(company)s")
		values["company"] = filters.company

	where_clause = " AND ".join(conditions)

	return frappe.db.sql(
		f"""
        SELECT
            gp.name AS gate_pass,
            gp.entry_type,
            gp.docstatus,
            gp.gate_pass_date,
            gp.creation,
            COALESCE(gp.gate_pass_date, DATE(gp.creation)) AS pending_date,
            gp.document_reference,
            gp.reference_number,
            gp.supplier,
            gp.company,
            gp.e_invoice_status,
            gp.e_waybill_status,
            COUNT(gpit.name) AS total_items
        FROM `tabGate Pass` gp
        LEFT JOIN `tabGate Pass Table` gpit ON gpit.parent = gp.name
        WHERE {where_clause}
        GROUP BY gp.name
        ORDER BY pending_date DESC, gp.name DESC
        """,
		values,
		as_dict=True,
	)


def get_reference_parties(rows: Iterable[frappe._dict]) -> dict[tuple[str, str], dict[str, str | None]]:
	"""Fetch supplier/customer details for the provided reference documents."""

	reference_numbers: dict[str, set[str]] = defaultdict(set)
	for row in rows:
		if not row.document_reference or not row.reference_number:
			continue
		if row.document_reference not in REFERENCE_PARTY_FIELDS:
			continue
		reference_numbers[row.document_reference].add(row.reference_number)

	party_details: dict[tuple[str, str], dict[str, str | None]] = {}
	for document_reference, names in reference_numbers.items():
		if not names:
			continue
		party_field, party_name_field = REFERENCE_PARTY_FIELDS[document_reference]
		records = frappe.get_all(
			document_reference,
			filters={"name": ["in", list(names)]},
			fields=["name", party_field, party_name_field],
		)
		for record in records:
			party = record.get(party_field)
			party_name = record.get(party_name_field) or party
			party_details[(document_reference, record.name)] = {
				"party": party,
				"party_name": party_name,
			}

	return party_details


def evaluate_outbound_pending(
	row: frappe._dict,
	gst_settings: frappe._dict,
	reference_totals: dict[tuple[str, str], float],
) -> tuple[str, str, bool]:
	"""Return (reason, status string, is_compliance_pending) for outbound rows."""

	missing, status_text = evaluate_compliance_state(row, gst_settings, reference_totals)

	if missing:
		pending_reason = _("Compliance pending")
	else:
		pending_reason = _("Awaiting Guard Submission") if row.docstatus == 0 else _("Pending Review")

	return pending_reason, status_text, bool(missing)


def evaluate_compliance_state(
	row: frappe._dict,
	gst_settings: frappe._dict,
	reference_totals: dict[tuple[str, str], float],
) -> tuple[list[str], str]:
	"""Evaluate compliance requirements and statuses for outbound gate passes."""

	document_reference = row.document_reference
	if document_reference not in OUTBOUND_REFERENCES:
		return [], "-"

	threshold = flt(gst_settings.get("e_waybill_threshold") or 0)
	total = (
		get_reference_total_cached(reference_totals, document_reference, row.reference_number)
		if threshold
		else 0
	)
	compliance_required = bool(threshold) and flt(total) >= threshold

	statuses: list[str] = []
	missing: list[str] = []

	if document_reference == "Sales Invoice":
		if compliance_required:
			status = normalise_compliance_status(row.e_invoice_status, default=_("Not Generated"))
			statuses.append(_("E-Invoice: {0}").format(status))
			if not is_generated_status(row.e_invoice_status):
				missing.append(_("E-Invoice"))
		else:
			statuses.append(_("E-Invoice: Not Required"))
	else:
		statuses.append(_("E-Invoice: Not Applicable"))

	require_ewaybill = compliance_required
	if document_reference == "Delivery Note" and not cint(gst_settings.get("enable_e_waybill_from_dn")):
		require_ewaybill = False

	if require_ewaybill:
		status = normalise_compliance_status(row.e_waybill_status, default=_("Not Generated"))
		statuses.append(_("E-Way Bill: {0}").format(status))
		if not is_generated_status(row.e_waybill_status):
			missing.append(_("E-Way Bill"))
	else:
		statuses.append(_("E-Way Bill: Not Required"))

	return missing, ", ".join(statuses) if statuses else "-"


def get_reference_total_cached(
	cache: dict[tuple[str, str], float],
	document_reference: str | None,
	reference_number: str | None,
) -> float:
	"""Fetch and cache monetary total for a reference document."""

	key = (document_reference or "", reference_number or "")
	if key in cache:
		return cache[key]

	if not document_reference or not reference_number:
		cache[key] = 0
		return 0

	values = frappe.db.get_value(
		document_reference,
		reference_number,
		REFERENCE_TOTAL_FIELDS,
		as_dict=True,
	)
	total = 0
	if values:
		for fieldname in REFERENCE_TOTAL_FIELDS:
			value = values.get(fieldname)
			if value:
				total = flt(value)
				break

	cache[key] = total
	return total


def normalise_compliance_status(value: str | None, *, default: str) -> str:
	"""Format compliance status text for display."""

	if not value:
		return default

	return cstr(value).strip().title()


def resolve_pending_date(row: frappe._dict):
	"""Determine the best available date for aging calculations."""

	for fieldname in ("pending_date", "gate_pass_date"):
		if row.get(fieldname):
			return getdate(row.get(fieldname))

	if row.get("creation"):
		return getdate(row.creation)

	return getdate(nowdate())


def get_report_summary(data: Iterable[dict[str, object]]) -> list[dict[str, object]]:
	"""Build summary widgets for the report."""

	data = list(data)
	if not data:
		return []

	total_items = sum(int(row.get("total_items", 0) or 0) for row in data)
	total_pending = len(data)
	inbound_pending = sum(1 for row in data if row.get("direction") == "Gate In")
	outbound_pending = sum(1 for row in data if row.get("direction") == "Gate Out")
	compliance_pending = sum(1 for row in data if row.get("compliance_pending"))

	return [
		{
			"label": _("Pending Gate Passes"),
			"value": total_pending,
			"indicator": "blue",
			"datatype": "Int",
		},
		{
			"label": _("Inbound Awaiting Receipt"),
			"value": inbound_pending,
			"indicator": "orange" if inbound_pending else "green",
			"datatype": "Int",
		},
		{
			"label": _("Outbound Awaiting Submission"),
			"value": outbound_pending,
			"indicator": "orange" if outbound_pending else "green",
			"datatype": "Int",
		},
		{
			"label": _("Compliance Pending"),
			"value": compliance_pending,
			"indicator": "red" if compliance_pending else "green",
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
