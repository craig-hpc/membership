import frappe

MEMBERSHIP_ROLES = ("Membership Manager", "Membership User", "System Manager")


def get_company():
	company = frappe.defaults.get_defaults().company
	if company:
		return company

	company = frappe.get_list("Company", limit=1)
	if company:
		return company[0].name

	return None


def check_app_permission():
	"""Decide whether the Membership tile shows on the Apps screen for the current user."""
	if frappe.session.user == "Administrator":
		return True

	if frappe.get_cached_value("User", frappe.session.user, "user_type") == "Website User":
		return False

	if set(MEMBERSHIP_ROLES) & set(frappe.get_roles()):
		return True

	return any(
		frappe.has_permission(doctype, ptype="read")
		for doctype in ("Member", "Membership", "Donation", "Donor")
	)


def before_tests():
	"""Create an Australian test company if the test site has none."""
	from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
	from membership.install import after_install
	from membership.membership.australia import get_financial_year

	frappe.clear_cache()
	fy_start, fy_end = get_financial_year()
	if not frappe.get_list("Company"):
		setup_complete(
			{
				"currency": "AUD",
				"full_name": "Test User",
				"company_name": "Bush Care Australia",
				"timezone": "Australia/Perth",
				"company_abbr": "BCA",
				"industry": "Non Profit",
				"country": "Australia",
				"fy_start_date": str(fy_start),
				"fy_end_date": str(fy_end),
				"language": "english",
				"company_tagline": "Testing",
				"email": "test@example.com",
				"password": "test",
				"chart_of_accounts": "Standard",
			}
		)

	after_install()
	frappe.db.commit()  # nosemgrep
