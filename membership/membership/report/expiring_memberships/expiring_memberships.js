// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Expiring Memberships"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("Expiring From"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("Expiring To"),
			fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), 60),
			reqd: 1,
		},
		{
			fieldname: "membership_type",
			label: __("Membership Type"),
			fieldtype: "Link",
			options: "Membership Type",
		},
	],
};
