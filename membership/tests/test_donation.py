import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import nowdate
from membership.membership.australia import get_financial_year_label
from membership.membership.report.tax_deductible_donations.tax_deductible_donations import execute
from membership.tests.utils import (
	VALID_ABN,
	get_cash_account,
	get_company,
	get_donation_income_account,
	make_donor,
	setup_settings,
)


class TestDonation(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.company = get_company()

	def setUp(self):
		setup_settings(self.company)
		self.donor = make_donor()

	def make_donation(self, submit=True, **kwargs):
		values = {
			"doctype": "Donation",
			"donor": self.donor.name,
			"company": self.company.name,
			"date": nowdate(),
			"amount": 100,
			"paid": 1,
		}
		values.update(kwargs)
		doc = frappe.get_doc(values).insert()
		if submit:
			doc.submit()
		return doc

	def test_gift_to_dgr_is_deductible(self):
		donation = self.make_donation(submit=False)
		self.assertEqual(donation.currency, "AUD")
		self.assertEqual(donation.gift_type, "Gift")
		self.assertTrue(donation.is_tax_deductible)
		self.assertEqual(donation.deductible_amount, 100)
		self.assertEqual(donation.financial_year, get_financial_year_label(nowdate()))

	def test_not_deductible_when_company_is_not_dgr(self):
		frappe.db.set_value("Company", self.company.name, "is_deductible_gift_recipient", 0)
		frappe.clear_document_cache("Company", self.company.name)
		try:
			donation = self.make_donation(submit=False)
			self.assertFalse(donation.is_tax_deductible)
			self.assertEqual(donation.deductible_amount, 0)
		finally:
			frappe.db.set_value("Company", self.company.name, "is_deductible_gift_recipient", 1)
			frappe.clear_document_cache("Company", self.company.name)

	def test_event_contribution(self):
		donation = self.make_donation(
			submit=False, gift_type="Fundraising Event Contribution", amount=420, benefit_value=80
		)
		self.assertTrue(donation.is_tax_deductible)
		self.assertEqual(donation.deductible_amount, 340)

	def test_journal_entry_on_submit_and_cancel(self):
		donation = self.make_donation(amount=250, payment_id="BANK-REF-1")
		self.assertTrue(donation.journal_entry)

		gl = frappe.get_all(
			"GL Entry",
			filters={"voucher_no": donation.journal_entry, "is_cancelled": 0},
			fields=["account", "debit", "credit"],
		)
		by_account = {row.account: row for row in gl}
		self.assertEqual(by_account[get_cash_account(self.company)].debit, 250)
		self.assertEqual(by_account[get_donation_income_account(self.company)].credit, 250)

		donation.cancel()
		self.assertEqual(frappe.db.get_value("Journal Entry", donation.journal_entry, "docstatus"), 2)

	def test_unpaid_donation_marked_paid_later(self):
		donation = self.make_donation(paid=0)
		self.assertFalse(donation.journal_entry)

		donation.mark_paid(payment_reference="EFT-123")
		donation.reload()
		self.assertTrue(donation.paid)
		self.assertTrue(donation.journal_entry)
		self.assertEqual(donation.payment_id, "EFT-123")

	def test_receipt_renders_ato_details(self):
		donation = self.make_donation()
		html = frappe.get_print("Donation", donation.name, print_format="Australian Donation Receipt")
		self.assertIn(VALID_ABN, html)
		self.assertIn("This receipt is for a gift", html)

	def test_donor_abn_validation(self):
		donor = make_donor(name="Acme Pty Ltd", donor_type="Business")
		donor.abn = "51824753556"
		donor.save()
		self.assertEqual(donor.abn, VALID_ABN)

		donor.abn = "51 824 753 557"
		self.assertRaises(frappe.ValidationError, donor.save)

	def test_tax_deductible_donations_report(self):
		self.make_donation(amount=100)
		self.make_donation(amount=50)

		_columns, data = execute(
			{"company": self.company.name, "financial_year": get_financial_year_label(nowdate())}
		)
		row = next(r for r in data if r.donor == self.donor.name)
		self.assertEqual(row.donations, 2)
		self.assertEqual(row.amount, 150)
		self.assertEqual(row.deductible_amount, 150)
