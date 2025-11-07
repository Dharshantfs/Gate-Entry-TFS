frappe.query_reports["Material Reconciliation"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "document_type",
			label: __("Document Type"),
			fieldtype: "Select",
			options: ["All", "Purchase Order", "Subcontracting Order"],
			default: "All",
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_default("company"),
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, column, data);

		if (column.fieldname === "discrepancy" && data) {
			const hasDiscrepancy = data.has_discrepancy;
			const color = hasDiscrepancy ? "red" : "green";
			value = `<span class="indicator-pill ${color}">${data.discrepancy}</span>`;
		}

		return value;
	},
};
