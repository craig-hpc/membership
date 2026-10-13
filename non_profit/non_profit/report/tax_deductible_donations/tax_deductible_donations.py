# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Donations per donor for one Australian financial year, for annual tax statements."""

import frappe
from frappe import _
from frappe.utils import flt
from non_profit.non_profit.australia import get_financial_year_label


def execute(filters=None):
	filters = frappe._dict(filters or {})
	filters.financial_year = filters.financial_year or get_financial_year_label()

	if filters.show_donations:
		return get_donation_columns(), get_donations(filters)

	return get_summary_columns(), get_summary(filters)


def get_donations(filters):
	conditions = {"docstatus": 1, "financial_year": filters.financial_year}
	if filters.company:
		conditions["company"] = filters.company
	if filters.donor:
		conditions["donor"] = filters.donor

	return frappe.get_all(
		"Donation",
		filters=conditions,
		fields=[
			"name",
			"donor",
			"donor_name",
			"email",
			"date",
			"gift_type",
			"currency",
			"amount",
			"benefit_value",
			"deductible_amount",
			"is_tax_deductible",
			"paid",
		],
		order_by="date asc",
	)


def get_summary(filters):
	summary = {}
	for row in get_donations(filters):
		donor = summary.setdefault(
			row.donor,
			frappe._dict(
				donor=row.donor,
				donor_name=row.donor_name,
				email=row.email,
				currency=row.currency,
				donations=0,
				amount=0,
				deductible_amount=0,
			),
		)
		donor.donations += 1
		donor.amount += flt(row.amount)
		donor.deductible_amount += flt(row.deductible_amount)

	return sorted(summary.values(), key=lambda d: (d.donor_name or d.donor or "").lower())


def get_summary_columns():
	return [
		{"label": _("Donor"), "fieldname": "donor", "fieldtype": "Link", "options": "Donor", "width": 200},
		{"label": _("Donor Name"), "fieldname": "donor_name", "fieldtype": "Data", "width": 180},
		{"label": _("Email"), "fieldname": "email", "fieldtype": "Data", "width": 200},
		{"label": _("Donations"), "fieldname": "donations", "fieldtype": "Int", "width": 100},
		{
			"label": _("Total Received"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		{
			"label": _("Tax Deductible"),
			"fieldname": "deductible_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		{
			"label": _("Currency"),
			"fieldname": "currency",
			"fieldtype": "Link",
			"options": "Currency",
			"hidden": 1,
		},
	]


def get_donation_columns():
	return [
		{
			"label": _("Donation"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Donation",
			"width": 160,
		},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
		{"label": _("Donor"), "fieldname": "donor", "fieldtype": "Link", "options": "Donor", "width": 180},
		{"label": _("Donor Name"), "fieldname": "donor_name", "fieldtype": "Data", "width": 160},
		{"label": _("Type"), "fieldname": "gift_type", "fieldtype": "Data", "width": 190},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Benefit Value"),
			"fieldname": "benefit_value",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Tax Deductible"),
			"fieldname": "deductible_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
		{"label": _("Paid"), "fieldname": "paid", "fieldtype": "Check", "width": 70},
		{
			"label": _("Currency"),
			"fieldname": "currency",
			"fieldtype": "Link",
			"options": "Currency",
			"hidden": 1,
		},
	]
