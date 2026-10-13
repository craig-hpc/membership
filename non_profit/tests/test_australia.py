import datetime

from frappe.tests import UnitTestCase
from non_profit.non_profit.australia import (
	AUCTION_CONTRIBUTION,
	EVENT_CONTRIBUTION,
	GIFT,
	format_abn,
	get_deductible_amount,
	get_financial_year,
	get_financial_year_label,
	is_valid_abn,
)


class TestABN(UnitTestCase):
	def test_valid_abns(self):
		for abn in ("51 824 753 556", "51824753556", "53 004 085 616"):
			self.assertTrue(is_valid_abn(abn), abn)

	def test_invalid_abns(self):
		for abn in ("51 824 753 557", "1234567890", "", None, "abcdefghijk", "00000000000"):
			self.assertFalse(is_valid_abn(abn), abn)

	def test_format(self):
		self.assertEqual(format_abn("51824753556"), "51 824 753 556")
		self.assertEqual(format_abn(" 51-824-753-556 "), "51 824 753 556")


class TestFinancialYear(UnitTestCase):
	def test_second_half_of_calendar_year(self):
		self.assertEqual(
			get_financial_year("2026-10-13"), (datetime.date(2026, 7, 1), datetime.date(2027, 6, 30))
		)
		self.assertEqual(get_financial_year_label("2026-07-01"), "2026-27")

	def test_first_half_of_calendar_year(self):
		self.assertEqual(
			get_financial_year("2026-06-30"), (datetime.date(2025, 7, 1), datetime.date(2026, 6, 30))
		)
		self.assertEqual(get_financial_year_label("2026-01-15"), "2025-26")


class TestDeductibleAmount(UnitTestCase):
	def test_gift_is_fully_deductible(self):
		self.assertEqual(get_deductible_amount(GIFT, 50), 50)
		# no minimum since 1 July 2024
		self.assertEqual(get_deductible_amount(GIFT, 1), 1)

	def test_gift_with_benefit_is_not_deductible(self):
		self.assertEqual(get_deductible_amount(GIFT, 50, 10), 0)

	def test_event_contribution_ato_example(self):
		# ATO example: $420 contribution, $80 benefit -> $340 deductible
		self.assertEqual(get_deductible_amount(EVENT_CONTRIBUTION, 420, 80), 340)

	def test_event_contribution_must_exceed_150(self):
		self.assertEqual(get_deductible_amount(EVENT_CONTRIBUTION, 150, 10), 0)

	def test_benefit_over_20_percent(self):
		self.assertEqual(get_deductible_amount(EVENT_CONTRIBUTION, 300, 61), 0)
		self.assertEqual(get_deductible_amount(EVENT_CONTRIBUTION, 300, 60), 240)

	def test_benefit_over_150_cap(self):
		self.assertEqual(get_deductible_amount(AUCTION_CONTRIBUTION, 2000, 151), 0)
		self.assertEqual(get_deductible_amount(AUCTION_CONTRIBUTION, 2000, 150), 1850)
