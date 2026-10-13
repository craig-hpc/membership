# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.contacts.address_and_contact import load_address_and_contact
from frappe.model.document import Document
from frappe.utils import validate_email_address


class Member(Document):
	def onload(self):
		"""Load address and contacts in `__onload`"""
		load_address_and_contact(self)

	def validate(self):
		if self.email_id:
			self.email_id = self.email_id.strip()
			validate_email_address(self.email_id, True)

	@frappe.whitelist()
	def make_customer_and_link(self):
		self.check_permission("write")

		if self.customer:
			frappe.msgprint(_("A customer is already linked to this Member"))
			return self.customer

		self.customer = create_customer(
			frappe._dict({"fullname": self.member_name, "email": self.email_id}), member=self.name
		)
		self.save()
		frappe.msgprint(_("Customer {0} has been created successfully.").format(self.customer))
		return self.customer

	def update_membership_summary(self):
		"""Refresh status, expiry and 'member since' from this member's memberships."""
		memberships = frappe.get_all(
			"Membership",
			filters={"member": self.name},
			fields=["from_date", "to_date", "membership_status", "paid"],
			order_by="to_date desc",
		)

		paid = [m for m in memberships if m.paid and m.membership_status != "Cancelled"]
		latest = paid[0] if paid else (memberships[0] if memberships else None)

		values = {
			"membership_expiry_date": paid[0].to_date if paid else None,
			"member_since": min(m.from_date for m in paid) if paid else None,
			"membership_status": latest.membership_status if latest else None,
		}
		if latest and latest.membership_status == "New":
			values["membership_status"] = "Current"

		self.db_set(values, update_modified=False)


def create_member(user_details):
	user_details = frappe._dict(user_details)
	member = frappe.new_doc("Member")
	member.update(
		{
			"member_name": user_details.fullname,
			"email_id": user_details.email,
			"membership_type": user_details.plan_id,
		}
	)

	member.insert(ignore_permissions=True)
	member.customer = create_customer(user_details, member.name)
	member.save(ignore_permissions=True)

	return member


def create_customer(user_details, member=None):
	customer = frappe.new_doc("Customer")
	customer.customer_name = user_details.fullname
	customer.customer_type = "Individual"
	customer.customer_group = frappe.db.get_single_value("Selling Settings", "customer_group")
	customer.territory = frappe.db.get_single_value("Selling Settings", "territory")
	customer.flags.ignore_mandatory = True
	customer.insert(ignore_permissions=True)

	try:
		frappe.db.savepoint("contact_creation")
		contact = frappe.new_doc("Contact")
		contact.first_name = user_details.fullname
		if user_details.mobile:
			contact.add_phone(user_details.mobile, is_primary_phone=1, is_primary_mobile_no=1)
		if user_details.email:
			contact.add_email(user_details.email, is_primary=1)

		contact.append("links", {"link_doctype": "Customer", "link_name": customer.name})
		if member:
			contact.append("links", {"link_doctype": "Member", "link_name": member})

		contact.insert(ignore_permissions=True)

	except frappe.DuplicateEntryError:
		frappe.db.rollback(save_point="contact_creation")

	except Exception:
		frappe.db.rollback(save_point="contact_creation")
		frappe.log_error(title=_("Contact Creation Failed"))

	return customer.name
