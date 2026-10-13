# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_link_to_form, getdate
from membership.membership.australia import (
	GIFT,
	company_is_dgr,
	get_deductible_amount,
	get_financial_year_label,
)

DEFAULT_RECEIPT_PRINT_FORMAT = "Australian Donation Receipt"


class Donation(Document):
	def validate(self):
		if not self.donor or not frappe.db.exists("Donor", self.donor):
			# for web forms
			user_type = frappe.db.get_value("User", frappe.session.user, "user_type")
			if user_type == "Website User":
				self.create_donor_for_website_user()
			else:
				frappe.throw(_("Please select a Donor"))

		if not self.company:
			self.company = get_company_for_donations()

		if not self.currency and self.company:
			self.currency = frappe.get_cached_value("Company", self.company, "default_currency")

		if flt(self.amount) <= 0:
			frappe.throw(_("Donation amount must be greater than zero"))

		self.set_tax_deductibility()

	def set_tax_deductibility(self):
		self.gift_type = self.gift_type or GIFT
		if self.gift_type == GIFT:
			self.benefit_value = 0

		if flt(self.benefit_value) < 0:
			frappe.throw(_("Value of Benefit Received cannot be negative"))

		if flt(self.benefit_value) > flt(self.amount):
			frappe.throw(_("Value of Benefit Received cannot be more than the amount"))

		self.financial_year = get_financial_year_label(self.date)

		if company_is_dgr(self.company):
			self.deductible_amount = get_deductible_amount(self.gift_type, self.amount, self.benefit_value)
		else:
			self.deductible_amount = 0

		self.is_tax_deductible = 1 if flt(self.deductible_amount) > 0 else 0

	def create_donor_for_website_user(self):
		donor_name = frappe.get_value("Donor", dict(email=frappe.session.user))

		if not donor_name:
			user = frappe.get_doc("User", frappe.session.user)
			donor = frappe.get_doc(
				dict(
					doctype="Donor",
					donor_type=self.get("donor_type")
					or frappe.db.get_single_value("Membership Settings", "default_donor_type"),
					email=frappe.session.user,
					donor_name=user.get_fullname(),
				)
			).insert(ignore_permissions=True)
			donor_name = donor.name

		if self.get("__islocal"):
			self.donor = donor_name

	def on_submit(self):
		if self.paid:
			self.create_journal_entry()
		self.send_receipt_if_enabled()

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Payment Ledger Entry")
		self.cancel_journal_entry()

	def on_payment_authorized(self, *args, **kwargs):
		"""Called by the Payments app when an online payment for this donation succeeds."""
		self.db_set("paid", 1)
		self.load_from_db()
		if self.docstatus == 1:
			self.create_journal_entry()

	@frappe.whitelist()
	def mark_paid(self, payment_reference=None, posting_date=None):
		"""Record payment for a submitted donation that was entered as unpaid."""
		self.check_permission("submit")
		if self.docstatus != 1:
			frappe.throw(_("Submit the donation first"))
		if self.paid:
			frappe.throw(_("This donation is already marked as paid"))

		if payment_reference:
			self.db_set("payment_id", payment_reference)
		self.db_set("paid", 1)
		return self.create_journal_entry(posting_date=posting_date)

	def create_journal_entry(self, posting_date=None):
		"""Debit the deposit account, credit donation income. Donations carry no GST."""
		settings = frappe.get_single("Membership Settings")
		if not settings.automate_donation_payment_entries or self.journal_entry:
			return

		settings_link = get_link_to_form("Membership Settings", "Membership Settings")
		if not settings.donation_income_account:
			frappe.throw(_("You need to set <b>Donation Income Account</b> in {0}").format(settings_link))

		deposit_account = self.get_deposit_account(settings)
		if not deposit_account:
			frappe.throw(_("You need to set <b>Deposit To</b> account in {0}").format(settings_link))

		posting_date = getdate(posting_date or self.date)
		cost_center = settings.donation_cost_center or frappe.get_cached_value(
			"Company", self.company, "cost_center"
		)
		amount = flt(self.amount, self.precision("amount"))
		remark = _("Donation {0} from {1}").format(self.name, self.donor_name or self.donor)

		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Bank Entry"
		je.company = self.company
		je.posting_date = posting_date
		je.cheque_no = self.payment_id or self.name
		je.cheque_date = posting_date
		je.user_remark = remark
		je.append(
			"accounts",
			{
				"account": deposit_account,
				"debit_in_account_currency": amount,
				"cost_center": cost_center,
				"user_remark": remark,
			},
		)
		je.append(
			"accounts",
			{
				"account": settings.donation_income_account,
				"credit_in_account_currency": amount,
				"cost_center": cost_center,
				"user_remark": remark,
			},
		)
		je.flags.ignore_permissions = True
		je.insert()
		je.submit()

		self.db_set("journal_entry", je.name)
		return je.name

	def get_deposit_account(self, settings):
		if self.mode_of_payment:
			account = frappe.db.get_value(
				"Mode of Payment Account",
				{"parent": self.mode_of_payment, "company": self.company},
				"default_account",
			)
			if account:
				return account

		return settings.donation_payment_account

	def cancel_journal_entry(self):
		if not self.journal_entry:
			return

		je = frappe.get_doc("Journal Entry", self.journal_entry)
		if je.docstatus == 1:
			je.flags.ignore_permissions = True
			je.cancel()

	def send_receipt_if_enabled(self):
		if not frappe.db.get_single_value("Membership Settings", "send_donation_receipt"):
			return
		if not self.email:
			return

		try:
			self.send_receipt()
		except Exception:
			frappe.log_error(title=_("Could not email receipt for donation {0}").format(self.name))

	@frappe.whitelist()
	def send_receipt(self):
		"""Email the donation receipt to the donor."""
		self.check_permission("read")
		if self.docstatus != 1:
			frappe.throw(_("Submit the donation before sending a receipt"))
		if not self.email:
			frappe.throw(
				_("Email address of donor {0} is missing").format(get_link_to_form("Donor", self.donor))
			)

		print_format = (
			frappe.db.get_single_value("Membership Settings", "donation_receipt_print_format")
			or DEFAULT_RECEIPT_PRINT_FORMAT
		)
		company_name = frappe.get_cached_value("Company", self.company, "company_name") or self.company

		frappe.sendmail(
			recipients=[self.email],
			subject=_("Receipt for your donation to {0}").format(company_name),
			message=_("Dear {0},<br><br>Thank you for your donation. Your receipt is attached.").format(
				self.donor_name or self.donor
			),
			attachments=[frappe.attach_print(self.doctype, self.name, print_format=print_format)],
			reference_doctype=self.doctype,
			reference_name=self.name,
			now=bool(frappe.flags.in_test),
		)
		frappe.msgprint(_("Receipt emailed to {0}").format(self.email), alert=True)


def get_donor(email):
	donors = frappe.get_all("Donor", filters={"email": email}, order_by="creation desc", limit=1)
	if donors:
		return frappe.get_doc("Donor", donors[0].name)
	return None


def get_company_for_donations():
	company = frappe.db.get_single_value("Membership Settings", "donation_company")
	if not company:
		from membership.membership.utils import get_company

		company = get_company()
	return company


def get_donation_receipt_context(doc):
	"""Values for the receipt print format, kept here so the template stays simple."""
	from membership.membership.australia import format_abn

	company = frappe.get_cached_doc("Company", doc.company)
	return frappe._dict(
		organisation=company.get("dgr_fund_name") or company.company_name,
		company_name=company.company_name,
		abn=format_abn(company.get("abn") or company.get("tax_id")),
		is_dgr=bool(company.get("is_deductible_gift_recipient")),
	)
