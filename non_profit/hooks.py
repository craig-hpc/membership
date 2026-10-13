from frappe import _

app_name = "non_profit"
app_title = "Non Profit"
app_publisher = "Frappe Technologies Pvt Ltd"
app_description = "Memberships, donations, volunteers and chapters for not-for-profit organisations"
app_email = "developers@frappe.io"
app_license = "MIT"
required_apps = ["frappe/erpnext"]
app_logo_url = "/assets/non_profit/images/non-profit-logo.svg"
app_home = "/desk/non-profit"

# Shows the app on the v16 Apps screen. Without this the app has no tile on the
# desktop, even though its doctypes and workspace still work.
add_to_apps_screen = [
	{
		"name": app_name,
		"logo": app_logo_url,
		"title": app_title,
		"route": app_home,
		"has_permission": "non_profit.non_profit.utils.check_app_permission",
	}
]

# Installation
# ------------

after_install = "non_profit.install.after_install"
after_migrate = "non_profit.install.after_migrate"
before_uninstall = "non_profit.install.before_uninstall"

# Jinja (print formats)
# ---------------------

jinja = {
	"methods": [
		"non_profit.non_profit.doctype.donation.donation.get_donation_receipt_context",
	],
}

# Document events
# ---------------

doc_events = {
	"Company": {
		"validate": "non_profit.non_profit.australia.validate_company_abn",
	},
}

# Scheduled tasks
# ---------------

scheduler_events = {
	"daily": [
		"non_profit.non_profit.doctype.membership.membership.set_expired_status",
	],
}

# Testing
# -------

before_tests = "non_profit.non_profit.utils.before_tests"

# Global search
# -------------

global_search_doctypes = {
	"Default": [
		{"doctype": "Member", "index": 1},
		{"doctype": "Membership", "index": 2},
		{"doctype": "Donor", "index": 3},
		{"doctype": "Donation", "index": 4},
		{"doctype": "Volunteer", "index": 5},
		{"doctype": "Chapter", "index": 6},
		{"doctype": "Grant Application", "index": 7},
		{"doctype": "Membership Type", "index": 8},
		{"doctype": "Donor Type", "index": 9},
		{"doctype": "Volunteer Type", "index": 10},
	]
}

# Portal
# ------

standard_portal_menu_items = [
	{
		"title": _("Chapters"),
		"route": "/chapters",
		"reference_doctype": "Chapter",
		"role": "Non Profit Portal User",
	},
]
