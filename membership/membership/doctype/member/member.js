// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Member", {
	refresh(frm) {
		frappe.dynamic_link = { doc: frm.doc, fieldname: "name", doctype: "Member" };

		frm.toggle_display(["address_html", "contact_html"], !frm.doc.__islocal);

		if (frm.doc.__islocal) {
			frappe.contacts.clear_address_and_contact(frm);
			return;
		}

		frappe.contacts.render_address_and_contact(frm);

		frm.add_custom_button(__("New Membership"), () => {
			frappe.new_doc("Membership", {
				member: frm.doc.name,
				membership_type: frm.doc.membership_type,
			});
		});

		if (frm.doc.customer) {
			frm.add_custom_button(
				__("Accounting Ledger"),
				() => {
					frappe.set_route("query-report", "General Ledger", {
						party_type: "Customer",
						party: frm.doc.customer,
					});
				},
				__("View")
			);

			frm.add_custom_button(
				__("Accounts Receivable"),
				() => {
					frappe.set_route("query-report", "Accounts Receivable", {
						party_type: "Customer",
						party: [frm.doc.customer],
					});
				},
				__("View")
			);
		} else {
			frm.add_custom_button(__("Create Customer"), () => {
				frm.call("make_customer_and_link").then(() => frm.reload_doc());
			});
		}

		if (frm.doc.membership_status) {
			const colours = { Current: "green", Pending: "orange", Expired: "gray", Cancelled: "red" };
			frm.dashboard.add_indicator(
				__(frm.doc.membership_status),
				colours[frm.doc.membership_status] || "blue"
			);
		}
	},
});
