import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate, nowdate
from non_profit.non_profit.doctype.membership.membership import (
	get_membership_end_date,
	set_expired_status,
)
from non_profit.tests.utils import get_company, get_membership_type, make_member, setup_settings


class TestMembership(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.company = get_company()

	def setUp(self):
		setup_settings(self.company)
		self.member = make_member()

	def make_membership(self, **kwargs):
		values = {
			"doctype": "Membership",
			"member": self.member.name,
			"membership_type": get_membership_type(),
			"paid": 1,
		}
		values.update(kwargs)
		return frappe.get_doc(values).insert()

	def test_end_dates_for_each_billing_cycle(self):
		self.assertEqual(get_membership_end_date("2026-07-01", "Yearly"), getdate("2027-06-30"))
		self.assertEqual(get_membership_end_date("2026-07-15", "Monthly"), getdate("2026-08-14"))
		self.assertEqual(get_membership_end_date("2026-07-15", "Quarterly"), getdate("2026-10-14"))
		self.assertEqual(
			get_membership_end_date("2026-10-13", "Financial Year (1 July to 30 June)"),
			getdate("2027-06-30"),
		)
		self.assertEqual(
			get_membership_end_date("2026-03-01", "Financial Year (1 July to 30 June)"),
			getdate("2026-06-30"),
		)

	def test_defaults_from_membership_type_and_company(self):
		membership = self.make_membership()
		self.assertEqual(membership.currency, "AUD")
		self.assertEqual(membership.amount, 110)
		self.assertEqual(membership.company, self.company.name)
		self.assertEqual(getdate(membership.from_date), getdate(nowdate()))
		self.assertEqual(membership.membership_status, "Current")

	def test_unpaid_membership_is_pending(self):
		membership = self.make_membership(paid=0)
		self.assertEqual(membership.membership_status, "Pending")

	def test_member_summary_is_updated(self):
		membership = self.make_membership()
		self.member.reload()
		self.assertEqual(self.member.membership_status, "Current")
		self.assertEqual(getdate(self.member.membership_expiry_date), getdate(membership.to_date))
		self.assertEqual(getdate(self.member.member_since), getdate(membership.from_date))

	def test_renewal_starts_after_current_membership(self):
		first = self.make_membership()
		renewal = self.make_membership()
		self.assertEqual(getdate(renewal.from_date), getdate(add_days(first.to_date, 1)))
		self.assertEqual(renewal.membership_status, "New")

		self.member.reload()
		self.assertEqual(getdate(self.member.membership_expiry_date), getdate(renewal.to_date))

	def test_scheduler_marks_expired(self):
		membership = self.make_membership(
			from_date=add_days(nowdate(), -400), to_date=add_days(nowdate(), -35)
		)
		self.assertEqual(membership.membership_status, "Expired")

		frappe.db.set_value("Membership", membership.name, "membership_status", "Current")
		set_expired_status()
		self.assertEqual(frappe.db.get_value("Membership", membership.name, "membership_status"), "Expired")

		self.member.reload()
		self.assertEqual(self.member.membership_status, "Expired")

	def test_invoice_with_gst_included(self):
		membership = self.make_membership()
		invoice = membership.generate_invoice(save=True)

		self.assertEqual(invoice.docstatus, 1)
		self.assertEqual(invoice.customer, self.member.customer)
		self.assertEqual(invoice.currency, "AUD")
		self.assertEqual(invoice.grand_total, 110)
		self.assertEqual(invoice.total_taxes_and_charges, 10)
		self.assertEqual(invoice.net_total, 100)
		self.assertEqual(frappe.db.get_value("Membership", membership.name, "invoice"), invoice.name)

	def test_invoice_with_payment_entry(self):
		membership = self.make_membership()
		invoice = membership.generate_invoice(save=True, with_payment_entry=True)
		invoice.reload()
		self.assertEqual(invoice.outstanding_amount, 0)
