// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Membership", {
	refresh(frm) {
		if (frm.doc.__islocal) return;

		if (!frm.doc.invoice) {
			frm.add_custom_button(__("Generate Invoice"), () => {
				frm.call({
					doc: frm.doc,
					method: "generate_invoice",
					args: { save: true },
					freeze: true,
					freeze_message: __("Creating Membership Invoice"),
				}).then(() => frm.reload_doc());
			});
		}

		frappe.db.get_single_value("Non Profit Settings", "send_email").then((val) => {
			if (val) {
				frm.add_custom_button(__("Send Acknowledgement"), () => {
					frm.call("send_acknowlement").then(() => frm.reload_doc());
				});
			}
		});
	},

	membership_type(frm) {
		if (!frm.doc.membership_type) return;
		frappe.db.get_value("Membership Type", frm.doc.membership_type, "amount").then((r) => {
			if (r.message) frm.set_value("amount", r.message.amount);
		});
	},
});
