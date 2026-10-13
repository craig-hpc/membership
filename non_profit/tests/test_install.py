import frappe
from frappe.tests import IntegrationTestCase
from non_profit.non_profit.utils import check_app_permission
from non_profit.tests.utils import VALID_ABN, get_company


class TestInstall(IntegrationTestCase):
	def test_roles_and_custom_fields(self):
		for role in ("Non Profit Manager", "Non Profit Member", "Non Profit Portal User"):
			self.assertTrue(frappe.db.exists("Role", role), role)

		meta = frappe.get_meta("Company")
		for fieldname in ("abn", "acnc_registered", "is_deductible_gift_recipient", "dgr_fund_name"):
			self.assertTrue(meta.has_field(fieldname), fieldname)

	def test_navigation_records(self):
		self.assertTrue(frappe.db.exists("Workspace", "Non Profit"))
		self.assertTrue(frappe.db.exists("Sidebar", "Non Profit"))
		self.assertTrue(frappe.db.exists("Dock", {"app": "non_profit", "standard": 1}))
		self.assertTrue(frappe.db.exists("Print Format", "Australian Donation Receipt"))

	def test_apps_screen_entry(self):
		hooks = frappe.get_hooks("add_to_apps_screen", app_name="non_profit")
		self.assertEqual(hooks[0]["route"], "/desk/non-profit")
		self.assertTrue(check_app_permission())

	def test_company_abn(self):
		company = get_company()
		self.assertEqual(company.abn, VALID_ABN)

		company.abn = "12 345 678 901"
		self.assertRaises(frappe.ValidationError, company.save)
