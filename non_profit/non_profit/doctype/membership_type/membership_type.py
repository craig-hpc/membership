# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class MembershipType(Document):
	def validate(self):
		if flt(self.amount) < 0:
			frappe.throw(_("Amount cannot be negative"))

		if self.linked_item:
			is_stock_item = frappe.db.get_value("Item", self.linked_item, "is_stock_item")
			if is_stock_item:
				frappe.throw(_("The Linked Item should be a service item"))
