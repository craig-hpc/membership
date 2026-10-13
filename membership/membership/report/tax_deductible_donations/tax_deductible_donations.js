// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

function current_financial_year() {
	const today = frappe.datetime.str_to_obj(frappe.datetime.get_today());
	const start = today.getMonth() >= 6 ? today.getFullYear() : today.getFullYear() - 1;
	return `${start}-${String(start + 1).slice(-2)}`;
}

frappe.query_reports["Tax Deductible Donations"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "financial_year",
			label: __("Financial Year"),
			fieldtype: "Data",
			default: current_financial_year(),
			description: __("Australian financial year, for example 2025-26"),
			reqd: 1,
		},
		{
			fieldname: "donor",
			label: __("Donor"),
			fieldtype: "Link",
			options: "Donor",
		},
		{
			fieldname: "show_donations",
			label: __("Show Each Donation"),
			fieldtype: "Check",
		},
	],
};
