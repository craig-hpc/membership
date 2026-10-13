"""Shared fixtures for the membership tests: an Australian company with the accounts we need."""

import frappe
from frappe.utils import nowdate
from membership.membership.australia import get_financial_year

COMPANY = "_Test NP Australia"
ABBR = "_TNPA"
VALID_ABN = "51 824 753 556"  # the ATO's published example ABN


def get_or_create(doctype, filters, values=None):
	name = frappe.db.get_value(doctype, filters)
	if name:
		return name
	doc = frappe.get_doc({"doctype": doctype, **filters, **(values or {})})
	doc.insert(ignore_permissions=True)
	return doc.name


def ensure_fiscal_year():
	today = nowdate()
	if frappe.db.get_value(
		"Fiscal Year", {"year_start_date": ("<=", today), "year_end_date": (">=", today), "disabled": 0}
	):
		return

	start, end = get_financial_year(today)
	frappe.get_doc(
		{
			"doctype": "Fiscal Year",
			"year": f"NP {start.year}-{end.year}",
			"year_start_date": start,
			"year_end_date": end,
		}
	).insert(ignore_permissions=True)


def leaf(doctype, parent_field, fallback_name):
	"""Return a non-group record of a tree doctype, creating one if needed."""
	name = frappe.db.get_value(doctype, {"is_group": 0})
	if name:
		return name

	root = frappe.db.get_value(doctype, {"is_group": 1, parent_field: ("in", ("", None))})
	doc = frappe.get_doc(
		{
			"doctype": doctype,
			frappe.scrub(doctype) + "_name": fallback_name,
			parent_field: root,
			"is_group": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def get_company():
	ensure_fiscal_year()

	if not frappe.db.exists("Company", COMPANY):
		frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": COMPANY,
				"abbr": ABBR,
				"country": "Australia",
				"default_currency": "AUD",
				"create_chart_of_accounts_based_on": "Standard Template",
				"chart_of_accounts": "Standard",
			}
		).insert(ignore_permissions=True)

	company = frappe.get_doc("Company", COMPANY)
	company.abn = VALID_ABN
	company.is_deductible_gift_recipient = 1
	company.acnc_registered = 1
	company.save(ignore_permissions=True)
	return company


def get_account(company, filters, create_as=None):
	name = frappe.db.get_value("Account", {"company": company.name, "is_group": 0, **filters})
	if name or not create_as:
		return name

	parent = frappe.db.get_value(
		"Account", {"company": company.name, "is_group": 1, "root_type": create_as["root_type"]}
	)
	doc = frappe.get_doc(
		{
			"doctype": "Account",
			"company": company.name,
			"parent_account": parent,
			"is_group": 0,
			**create_as,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def get_cash_account(company):
	return get_account(company, {"account_type": "Cash"}) or get_account(company, {"account_type": "Bank"})


def get_donation_income_account(company):
	return get_account(
		company,
		{"account_name": "Donations"},
		create_as={"account_name": "Donations", "root_type": "Income", "report_type": "Profit and Loss"},
	)


def get_gst_template(company):
	"""A GST-inclusive 10% sales tax template for the test company."""
	title = "_Test NP GST Inclusive"
	existing = frappe.db.get_value(
		"Sales Taxes and Charges Template", {"title": title, "company": company.name}
	)
	if existing:
		return existing

	gst_account = get_account(
		company,
		{"account_name": "GST Collected"},
		create_as={
			"account_name": "GST Collected",
			"root_type": "Liability",
			"report_type": "Balance Sheet",
			"account_type": "Tax",
		},
	)
	doc = frappe.get_doc(
		{
			"doctype": "Sales Taxes and Charges Template",
			"title": title,
			"company": company.name,
			"taxes": [
				{
					"charge_type": "On Net Total",
					"account_head": gst_account,
					"description": "GST",
					"rate": 10,
					"included_in_print_rate": 1,
					"cost_center": company.cost_center,
				}
			],
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def ensure_selling_defaults():
	settings = frappe.get_single("Selling Settings")
	changed = False
	if not settings.customer_group:
		settings.customer_group = leaf("Customer Group", "parent_customer_group", "_Test NP Customers")
		changed = True
	if not settings.territory:
		settings.territory = leaf("Territory", "parent_territory", "_Test NP Territory")
		changed = True
	if changed:
		settings.flags.ignore_mandatory = True
		settings.save(ignore_permissions=True)


def get_membership_item():
	item_code = "_Test NP Annual Membership"
	if not frappe.db.exists("Item", item_code):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": item_code,
				"item_name": "Annual Membership",
				"item_group": leaf("Item Group", "parent_item_group", "_Test NP Services"),
				"stock_uom": frappe.db.get_value("UOM", {"name": "Nos"}) or frappe.db.get_value("UOM", {}),
				"is_stock_item": 0,
				"include_item_in_manufacturing": 0,
			}
		).insert(ignore_permissions=True)
	return item_code


def get_membership_type(amount=110):
	name = "_Test NP Standard"
	if not frappe.db.exists("Membership Type", name):
		frappe.get_doc(
			{
				"doctype": "Membership Type",
				"membership_type": name,
				"amount": amount,
				"linked_item": get_membership_item(),
			}
		).insert(ignore_permissions=True)
	return name


def setup_settings(company, billing_cycle="Yearly", **extra):
	from membership.install import create_default_donor_types

	create_default_donor_types()
	settings = frappe.get_single("Membership Settings")
	settings.update(
		{
			"company": company.name,
			"donation_company": company.name,
			"default_donor_type": "Individual",
			"billing_cycle": billing_cycle,
			"allow_invoicing": 1,
			"membership_debit_account": company.default_receivable_account,
			"membership_payment_account": get_cash_account(company),
			"membership_taxes_and_charges_template": get_gst_template(company),
			"automate_donation_payment_entries": 1,
			"donation_payment_account": get_cash_account(company),
			"donation_income_account": get_donation_income_account(company),
			"donation_cost_center": company.cost_center,
			"send_donation_receipt": 0,
			"send_email": 0,
			**extra,
		}
	)
	settings.save(ignore_permissions=True)
	return settings


def make_member(name="Jane Citizen", email=None):
	from membership.membership.doctype.member.member import create_member

	ensure_selling_defaults()
	email = email or f"{frappe.scrub(name)}.{frappe.generate_hash(length=6)}@example.com"
	return create_member(frappe._dict(fullname=name, email=email, plan_id=get_membership_type()))


def make_donor(name="Sam Giver", email=None, donor_type="Individual"):
	from membership.install import create_default_donor_types

	create_default_donor_types()
	email = email or f"{frappe.scrub(name)}.{frappe.generate_hash(length=6)}@example.com"
	return frappe.get_doc(
		{"doctype": "Donor", "donor_name": name, "email": email, "donor_type": donor_type}
	).insert(ignore_permissions=True)
