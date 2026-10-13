"""Australian rules used across the app: ABNs, financial years and deductible gifts.

References (Australian Taxation Office):
- DGR receipts must show the organisation's name, its ABN and that the receipt is for a gift.
- Contributions at an eligible fundraising event or auction are deductible only if the
  contribution is more than $150 and the GST-inclusive value of the benefit received is no more
  than the lesser of 20% of the contribution and $150. The deductible amount is the
  contribution minus the value of the benefit.
- From 1 July 2024 there is no minimum gift amount for deductibility.
"""

import datetime

import frappe
from frappe import _
from frappe.utils import flt, getdate

ABN_WEIGHTS = (10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19)

GIFT = "Gift"
EVENT_CONTRIBUTION = "Fundraising Event Contribution"
AUCTION_CONTRIBUTION = "Auction Contribution"

MINOR_BENEFIT_CAP = 150
MINOR_BENEFIT_PERCENT = 20
MINIMUM_CONTRIBUTION = 150


# ABN
# ---


def clean_abn(abn: str | None) -> str:
	return "".join(ch for ch in (abn or "") if ch.isdigit())


def is_valid_abn(abn: str | None) -> bool:
	"""Check an ABN with the ATO's modulus 89 checksum."""
	digits = clean_abn(abn)
	if len(digits) != 11:
		return False

	numbers = [int(d) for d in digits]
	numbers[0] -= 1
	return sum(n * w for n, w in zip(numbers, ABN_WEIGHTS, strict=True)) % 89 == 0


def format_abn(abn: str | None) -> str:
	"""Format an ABN the way the ATO prints it: `51 824 753 556`."""
	digits = clean_abn(abn)
	if len(digits) != 11:
		return abn or ""
	return f"{digits[:2]} {digits[2:5]} {digits[5:8]} {digits[8:]}"


def validate_abn(abn: str | None, label: str | None = None) -> str | None:
	"""Throw if `abn` is set and invalid, otherwise return it in the standard format."""
	if not abn:
		return abn

	if not is_valid_abn(abn):
		frappe.throw(
			_("{0} {1} is not a valid Australian Business Number.").format(
				label or _("ABN"), frappe.bold(abn)
			),
			title=_("Invalid ABN"),
		)

	return format_abn(abn)


def validate_company_abn(doc, method=None):
	"""`Company.validate` hook."""
	if doc.get("abn"):
		doc.abn = validate_abn(doc.abn)
		if not doc.tax_id and doc.country == "Australia":
			doc.tax_id = doc.abn


# Financial year
# --------------


def get_financial_year(date=None) -> tuple[datetime.date, datetime.date]:
	"""Return the Australian financial year (1 July to 30 June) that contains `date`."""
	date = getdate(date)
	start_year = date.year if date.month >= 7 else date.year - 1
	return datetime.date(start_year, 7, 1), datetime.date(start_year + 1, 6, 30)


def get_financial_year_label(date=None) -> str:
	start, end = get_financial_year(date)
	return f"{start.year}-{str(end.year)[-2:]}"


# Deductible gifts
# ----------------


def get_deductible_amount(gift_type: str, amount: float, benefit_value: float = 0) -> float:
	"""Return the tax deductible part of a donation under the ATO rules.

	`benefit_value` is the GST-inclusive market value of anything the donor received in return,
	for example a dinner ticket or the item won at an auction.
	"""
	amount = flt(amount)
	benefit_value = flt(benefit_value)

	if amount <= 0:
		return 0

	if gift_type in (None, "", GIFT):
		# a gift must not give the donor a material benefit
		return 0 if benefit_value > 0 else amount

	if gift_type in (EVENT_CONTRIBUTION, AUCTION_CONTRIBUTION):
		if amount <= MINIMUM_CONTRIBUTION:
			return 0

		benefit_limit = min(amount * MINOR_BENEFIT_PERCENT / 100, MINOR_BENEFIT_CAP)
		if benefit_value > benefit_limit:
			return 0

		return flt(amount - benefit_value, 2)

	return 0


def company_is_dgr(company: str | None) -> bool:
	if not company:
		return False
	return bool(frappe.get_cached_value("Company", company, "is_deductible_gift_recipient"))
