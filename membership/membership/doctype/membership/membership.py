# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, add_years, get_link_to_form, getdate, nowdate
from membership.membership.australia import get_financial_year

RENEWAL_WINDOW_DAYS = 30


class Membership(Document):
	def validate(self):
		if not self.member or not frappe.db.exists("Member", self.member):
			# for web forms
			user_type = frappe.db.get_value("User", frappe.session.user, "user_type")
			if user_type == "Website User":
				self.create_member_from_website_user()
			else:
				frappe.throw(_("Please select a Member"))

		self.set_defaults()
		self.validate_membership_period()
		self.set_status()

	def on_update(self):
		self.update_member()

	def after_delete(self):
		self.update_member()

	def set_defaults(self):
		if not self.company:
			self.company = get_company_for_memberships()

		if not self.currency and self.company:
			self.currency = frappe.get_cached_value("Company", self.company, "default_currency")

		if not self.amount and self.membership_type:
			self.amount = frappe.get_cached_value("Membership Type", self.membership_type, "amount")

	def create_member_from_website_user(self):
		member_name = frappe.get_value("Member", dict(email_id=frappe.session.user))

		if not member_name:
			user = frappe.get_doc("User", frappe.session.user)
			member = frappe.get_doc(
				dict(
					doctype="Member",
					email_id=frappe.session.user,
					membership_type=self.membership_type,
					member_name=user.get_fullname(),
				)
			).insert(ignore_permissions=True)
			member_name = member.name

		if self.get("__islocal"):
			self.member = member_name

	def validate_membership_period(self):
		# an existing paid membership decides where a renewal starts
		last_membership = get_last_membership(self.member)

		if self.is_new() and last_membership and last_membership.name != self.name:
			if frappe.session.user != "Administrator" and not frappe.has_permission(
				"Membership", "write", throw=False
			):
				# self-service renewals only in the last 30 days of a membership
				if getdate(add_days(last_membership.to_date, -RENEWAL_WINDOW_DAYS)) > getdate(nowdate()):
					frappe.throw(
						_("You can only renew if your membership expires within {0} days").format(
							RENEWAL_WINDOW_DAYS
						)
					)

			if getdate(last_membership.to_date) >= getdate(self.from_date or nowdate()):
				# a renewal starts the day after the current membership ends
				self.from_date = add_days(last_membership.to_date, 1)
				self.to_date = None

		if not self.from_date:
			self.from_date = nowdate()

		from_date_moved = (
			not self.is_new()
			and self.has_value_changed("from_date")
			and not self.has_value_changed("to_date")
		)
		if not self.to_date or from_date_moved:
			self.to_date = get_membership_end_date(self.from_date)

		if getdate(self.to_date) < getdate(self.from_date):
			frappe.throw(_("Membership end date cannot be before its start date"))

	def set_status(self):
		if self.membership_status == "Cancelled":
			return

		today = getdate(nowdate())
		if getdate(self.to_date) < today:
			self.membership_status = "Expired"
		elif not self.paid:
			self.membership_status = "Pending"
		elif getdate(self.from_date) > today:
			self.membership_status = "New"
		else:
			self.membership_status = "Current"

	def update_member(self):
		if self.member and frappe.db.exists("Member", self.member):
			frappe.get_doc("Member", self.member).update_membership_summary()

	def on_payment_authorized(self, status_changed_to=None):
		"""Called by the Payments app when an online payment for this membership succeeds."""
		if status_changed_to not in ("Completed", "Authorized"):
			return

		self.load_from_db()
		self.db_set("paid", 1)
		self.set_status()
		self.db_set("membership_status", self.membership_status)
		self.update_member()

		settings = frappe.get_single("Membership Settings")
		if settings.allow_invoicing and settings.automate_membership_invoicing:
			self.generate_invoice(with_payment_entry=settings.automate_membership_payment_entries, save=True)

	@frappe.whitelist()
	def generate_invoice(self, save=True, with_payment_entry=False):
		if not (self.paid or self.currency or self.amount):
			frappe.throw(
				_("The payment for this membership is not paid. To generate invoice fill the payment details")
			)

		if self.invoice:
			frappe.throw(_("An invoice is already linked to this document"))

		member = frappe.get_doc("Member", self.member)
		if not member.customer:
			frappe.throw(_("No customer linked to member {0}").format(frappe.bold(self.member)))

		plan = frappe.get_doc("Membership Type", self.membership_type)
		settings = frappe.get_single("Membership Settings")
		self.validate_membership_type_and_settings(plan, settings)

		invoice = make_invoice(self, member, plan, settings)
		self.reload()
		self.invoice = invoice.name

		if with_payment_entry:
			self.make_payment_entry(settings, invoice)

		if save:
			self.save()

		return invoice

	def validate_membership_type_and_settings(self, plan, settings):
		settings_link = get_link_to_form("Membership Settings", "Membership Settings")

		if not settings.allow_invoicing:
			frappe.throw(_("Enable <b>Allow Invoicing for Memberships</b> in {0}").format(settings_link))

		if not settings.membership_debit_account:
			frappe.throw(_("You need to set <b>Receivable Account</b> in {0}").format(settings_link))

		if not settings.company:
			frappe.throw(_("You need to set <b>Company</b> for invoicing in {0}").format(settings_link))

		if not plan.linked_item:
			frappe.throw(
				_("Please set a Linked Item for the Membership Type {0}").format(
					get_link_to_form("Membership Type", self.membership_type)
				)
			)

	def make_payment_entry(self, settings, invoice):
		if not settings.membership_payment_account:
			frappe.throw(
				_("You need to set <b>Payment Account</b> for Membership in {0}").format(
					get_link_to_form("Membership Settings", "Membership Settings")
				)
			)

		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		pe = get_payment_entry(dt="Sales Invoice", dn=invoice.name, bank_amount=invoice.grand_total)
		pe.paid_to = settings.membership_payment_account
		pe.reference_no = self.payment_id or self.name
		pe.reference_date = getdate()
		pe.flags.ignore_mandatory = True
		pe.save()
		pe.submit()
		return pe

	@frappe.whitelist()
	def send_acknowlement(self):
		settings = frappe.get_single("Membership Settings")
		if not settings.send_email:
			frappe.throw(
				_("You need to enable <b>Send Acknowledge Email</b> in {0}").format(
					get_link_to_form("Membership Settings", "Membership Settings")
				)
			)

		member = frappe.get_doc("Member", self.member)
		if not member.email_id:
			frappe.throw(
				_("Email address of member {0} is missing").format(get_link_to_form("Member", self.member))
			)

		email = member.email_id
		attachments = [
			frappe.attach_print("Membership", self.name, print_format=settings.membership_print_format)
		]

		if self.invoice and settings.send_invoice:
			attachments.append(
				frappe.attach_print("Sales Invoice", self.invoice, print_format=settings.inv_print_format)
			)

		email_template = frappe.get_doc("Email Template", settings.email_template)
		context = {"doc": self, "member": member}

		email_args = {
			"recipients": [email],
			"message": frappe.render_template(email_template.get("response"), context),
			"subject": frappe.render_template(email_template.get("subject"), context),
			"attachments": attachments,
			"reference_doctype": self.doctype,
			"reference_name": self.name,
		}

		if not frappe.flags.in_test:
			frappe.enqueue(method=frappe.sendmail, queue="short", timeout=300, is_async=True, **email_args)
		else:
			frappe.sendmail(**email_args)

	def generate_and_send_invoice(self):
		self.generate_invoice(save=False)
		self.send_acknowlement()


def get_membership_end_date(from_date, billing_cycle=None):
	billing_cycle = billing_cycle or (
		frappe.db.get_single_value("Membership Settings", "billing_cycle") or "Yearly"
	)
	from_date = getdate(from_date)

	if billing_cycle == "Monthly":
		return add_days(add_months(from_date, 1), -1)
	if billing_cycle == "Quarterly":
		return add_days(add_months(from_date, 3), -1)
	if billing_cycle.startswith("Financial Year"):
		return get_financial_year(from_date)[1]

	return add_days(add_years(from_date, 1), -1)


def make_invoice(membership, member, plan, settings):
	invoice = frappe.get_doc(
		{
			"doctype": "Sales Invoice",
			"customer": member.customer,
			"debit_to": settings.membership_debit_account,
			"currency": membership.currency,
			"company": settings.company,
			"is_pos": 0,
			"items": [{"item_code": plan.linked_item, "rate": membership.amount, "qty": 1}],
		}
	)

	if settings.get("membership_taxes_and_charges_template"):
		invoice.taxes_and_charges = settings.membership_taxes_and_charges_template

	invoice.set_missing_values()
	if invoice.taxes_and_charges and not invoice.get("taxes"):
		invoice.append_taxes_from_master()

	invoice.insert()
	invoice.submit()

	frappe.msgprint(_("Sales Invoice created successfully"))

	return invoice


def get_company_for_memberships():
	company = frappe.db.get_single_value("Membership Settings", "company")
	if not company:
		from membership.membership.utils import get_company

		company = get_company()
	return company


def set_expired_status():
	"""Daily: mark memberships whose end date has passed as Expired."""
	expired = frappe.get_all(
		"Membership",
		filters={
			"membership_status": ("not in", ("Cancelled", "Expired")),
			"to_date": ("<", nowdate()),
		},
		fields=["name", "member"],
	)

	for row in expired:
		frappe.db.set_value("Membership", row.name, "membership_status", "Expired", update_modified=False)

	for member in {row.member for row in expired if row.member}:
		if frappe.db.exists("Member", member):
			frappe.get_doc("Member", member).update_membership_summary()


def get_last_membership(member):
	"""Returns last membership if exists"""
	if not member:
		return None

	last_membership = frappe.get_all(
		"Membership",
		fields=["name", "to_date", "membership_type"],
		filters={"member": member, "paid": 1, "membership_status": ("!=", "Cancelled")},
		order_by="to_date desc",
		limit=1,
	)

	if last_membership:
		return last_membership[0]
