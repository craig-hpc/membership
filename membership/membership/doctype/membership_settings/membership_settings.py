# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class MembershipSettings(Document):
	def validate(self):
		self.validate_account_company("membership_debit_account", self.company)
		self.validate_account_company("membership_payment_account", self.company)
		self.validate_account_company("donation_payment_account", self.donation_company)
		self.validate_account_company("donation_income_account", self.donation_company)

	def validate_account_company(self, fieldname, company):
		account = self.get(fieldname)
		if not (account and company):
			return

		account_company = frappe.get_cached_value("Account", account, "company")
		if account_company != company:
			frappe.throw(
				_("{0}: account {1} belongs to company {2}, not {3}").format(
					_(self.meta.get_label(fieldname)),
					frappe.bold(account),
					frappe.bold(account_company),
					frappe.bold(company),
				)
			)
