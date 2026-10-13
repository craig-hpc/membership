import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

ROLES = ("Membership Manager", "Membership User", "Membership Portal User")

DEFAULT_DONOR_TYPES = ("Individual", "Business", "Trust or Foundation", "Government")

MEMBERSHIP_ITEM_GROUP = "Memberships"


def after_install():
	create_roles()
	make_custom_fields()
	create_default_donor_types()
	setup_default_settings()
	frappe.clear_cache()


def after_migrate():
	# keep custom fields in step with the app on every `bench migrate`
	create_roles()
	make_custom_fields()


def before_uninstall():
	delete_custom_fields()


def create_roles():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc(
				{
					"doctype": "Role",
					"role_name": role,
					"desk_access": 0 if role == "Membership Portal User" else 1,
				}
			).insert(ignore_permissions=True)


def get_custom_fields():
	return {
		"Company": [
			{
				"fieldname": "nfp_registration_section",
				"label": _("Not-for-profit Registration (Australia)"),
				"fieldtype": "Section Break",
				"insert_after": "registration_details",
				"collapsible": 1,
			},
			{
				"fieldname": "abn",
				"label": _("ABN"),
				"fieldtype": "Data",
				"insert_after": "nfp_registration_section",
				"description": _("Australian Business Number. Printed on donation receipts."),
			},
			{
				"fieldname": "acnc_registered",
				"label": _("Registered with the ACNC"),
				"fieldtype": "Check",
				"insert_after": "abn",
			},
			{
				"fieldname": "nfp_registration_column_break",
				"fieldtype": "Column Break",
				"insert_after": "acnc_registered",
			},
			{
				"fieldname": "is_deductible_gift_recipient",
				"label": _("Endorsed as a Deductible Gift Recipient (DGR)"),
				"fieldtype": "Check",
				"insert_after": "nfp_registration_column_break",
				"description": _("Only DGRs can issue tax deductible donation receipts."),
			},
			{
				"fieldname": "dgr_fund_name",
				"label": _("DGR Fund Name"),
				"fieldtype": "Data",
				"insert_after": "is_deductible_gift_recipient",
				"depends_on": "eval:doc.is_deductible_gift_recipient",
				"description": _(
					"If gifts are received by a separate public fund, enter its name. Otherwise the company name is used on receipts."
				),
			},
		],
	}


def make_custom_fields(update=True):
	create_custom_fields(get_custom_fields(), update=update)


def delete_custom_fields():
	for doctype, fields in get_custom_fields().items():
		for field in fields:
			name = f"{doctype}-{field['fieldname']}"
			if frappe.db.exists("Custom Field", name):
				frappe.delete_doc("Custom Field", name, ignore_missing=True, force=True)
		frappe.clear_cache(doctype=doctype)


def create_default_donor_types():
	for donor_type in DEFAULT_DONOR_TYPES:
		if not frappe.db.exists("Donor Type", donor_type):
			frappe.get_doc({"doctype": "Donor Type", "donor_type": donor_type}).insert(
				ignore_permissions=True
			)


def setup_default_settings():
	"""Fill in sensible defaults so the settings form can be saved straight away."""
	settings = frappe.get_single("Membership Settings")
	company = frappe.defaults.get_global_default("company") or frappe.db.get_value("Company", {}, "name")

	if company:
		settings.company = settings.company or company
		settings.donation_company = settings.donation_company or company

	settings.billing_cycle = settings.billing_cycle or "Yearly"
	settings.default_donor_type = settings.default_donor_type or "Individual"

	settings.flags.ignore_mandatory = True
	settings.flags.ignore_permissions = True
	settings.save()
