# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.utils import date_diff, getdate, nowdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("Member"), "fieldname": "member", "fieldtype": "Link", "options": "Member", "width": 150},
		{"label": _("Member Name"), "fieldname": "member_name", "fieldtype": "Data", "width": 180},
		{"label": _("Email"), "fieldname": "email_id", "fieldtype": "Data", "width": 200},
		{
			"label": _("Membership Type"),
			"fieldname": "membership_type",
			"fieldtype": "Link",
			"options": "Membership Type",
			"width": 140,
		},
		{
			"label": _("Membership"),
			"fieldname": "membership",
			"fieldtype": "Link",
			"options": "Membership",
			"width": 160,
		},
		{"label": _("Expires On"), "fieldname": "to_date", "fieldtype": "Date", "width": 110},
		{"label": _("Days Left"), "fieldname": "days_left", "fieldtype": "Int", "width": 90},
	]


def get_data(filters):
	from_date = getdate(filters.from_date or nowdate())
	to_date = getdate(filters.to_date or nowdate())

	membership_filters = {"paid": 1, "membership_status": ("!=", "Cancelled")}
	if filters.membership_type:
		membership_filters["membership_type"] = filters.membership_type

	# latest paid membership per member decides when they lapse
	latest = {}
	for row in frappe.get_all(
		"Membership",
		filters=membership_filters,
		fields=["name", "member", "membership_type", "to_date"],
		order_by="to_date desc",
	):
		if row.member and row.member not in latest:
			latest[row.member] = row

	expiring = [m for m in latest.values() if from_date <= getdate(m.to_date) <= to_date]
	if not expiring:
		return []

	members = {
		m.name: m
		for m in frappe.get_all(
			"Member",
			filters={"name": ("in", [m.member for m in expiring])},
			fields=["name", "member_name", "email_id"],
		)
	}

	today = getdate(nowdate())
	data = []
	for m in sorted(expiring, key=lambda m: getdate(m.to_date)):
		member = members.get(m.member) or frappe._dict()
		data.append(
			{
				"member": m.member,
				"member_name": member.member_name,
				"email_id": member.email_id,
				"membership_type": m.membership_type,
				"membership": m.name,
				"to_date": m.to_date,
				"days_left": date_diff(m.to_date, today),
			}
		)

	return data
