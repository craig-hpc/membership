# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.contacts.address_and_contact import load_address_and_contact
from frappe.model.document import Document
from frappe.utils import validate_email_address
from membership.membership.australia import validate_abn


class Donor(Document):
	def onload(self):
		"""Load address and contacts in `__onload`"""
		load_address_and_contact(self)

	def validate(self):
		if self.email:
			self.email = self.email.strip()
			validate_email_address(self.email, True)

		if self.abn:
			self.abn = validate_abn(self.abn)
