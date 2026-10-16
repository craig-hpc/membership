from frappe import _

app_name = "membership"
app_title = "Membership"
app_publisher = "HealthyPC - original by Frappe Technologies"
app_description = "Memberships, donations, volunteers and chapters for not-for-profit organisations"
app_email = "support@healthypc.com.au"
app_license = "MIT"
required_apps = ["frappe/erpnext"]
app_logo_url = "/assets/membership/images/membership-logo.svg"
app_home = "/desk/memberships"

# Shows the app on the v16 Apps screen. Without this the app has no tile on the
# desktop, even though its doctypes and workspace still work.
add_to_apps_screen = [
	{
		"name": app_name,
		"logo": app_logo_url,
		"title": app_title,
		"route": app_home,
		"has_permission": "membership.membership.utils.check_app_permission",
	}
]

# Installation
# ------------

after_install = "membership.install.after_install"
after_migrate = "membership.install.after_migrate"
before_uninstall = "membership.install.before_uninstall"

# Jinja (print formats)
# ---------------------

jinja = {
	"methods": [
		"membership.membership.doctype.donation.donation.get_donation_receipt_context",
	],
}

# Document events
# ---------------

doc_events = {
	"Company": {
		"validate": "membership.membership.australia.validate_company_abn",
	},
}

# Scheduled tasks
# ---------------

scheduler_events = {
	"daily": [
		"membership.membership.doctype.membership.membership.set_expired_status",
	],
}

# Testing
# -------

before_tests = "membership.membership.utils.before_tests"

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
		"role": "Membership Portal User",
	},
]
