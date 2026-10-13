// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Non Profit Settings", {
	refresh(frm) {
		frm.set_query("inv_print_format", () => ({ filters: { doc_type: "Sales Invoice" } }));
		frm.set_query("membership_print_format", () => ({ filters: { doc_type: "Membership" } }));
		frm.set_query("donation_receipt_print_format", () => ({ filters: { doc_type: "Donation" } }));

		frm.set_query("membership_debit_account", () => ({
			filters: { account_type: "Receivable", is_group: 0, company: frm.doc.company },
		}));

		frm.set_query("membership_payment_account", () => ({
			filters: { account_type: ["in", ["Bank", "Cash"]], is_group: 0, company: frm.doc.company },
		}));

		frm.set_query("membership_taxes_and_charges_template", () => ({
			filters: { company: frm.doc.company, disabled: 0 },
		}));

		frm.set_query("donation_payment_account", () => ({
			filters: {
				account_type: ["in", ["Bank", "Cash"]],
				is_group: 0,
				company: frm.doc.donation_company,
			},
		}));

		frm.set_query("donation_income_account", () => ({
			filters: { root_type: "Income", is_group: 0, company: frm.doc.donation_company },
		}));

		frm.set_query("donation_cost_center", () => ({
			filters: { is_group: 0, company: frm.doc.donation_company },
		}));
	},
});
