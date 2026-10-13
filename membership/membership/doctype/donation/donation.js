// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Donation", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && !frm.doc.paid) {
			frm.add_custom_button(__("Mark as Paid"), () => frm.events.mark_paid(frm));
		}

		if (frm.doc.docstatus === 1 && frm.doc.email) {
			frm.add_custom_button(__("Email Receipt"), () => {
				frm.call({ doc: frm.doc, method: "send_receipt", freeze: true });
			});
		}

		if (frm.doc.docstatus === 1) {
			frm.dashboard.add_indicator(
				frm.doc.is_tax_deductible
					? __("Tax deductible: {0}", [
							format_currency(frm.doc.deductible_amount, frm.doc.currency),
						])
					: __("Not tax deductible"),
				frm.doc.is_tax_deductible ? "green" : "gray"
			);
		}
	},

	gift_type(frm) {
		if (frm.doc.gift_type === "Gift") {
			frm.set_value("benefit_value", 0);
		}
	},

	mark_paid(frm) {
		const dialog = new frappe.ui.Dialog({
			title: __("Record Payment"),
			fields: [
				{
					fieldname: "payment_reference",
					fieldtype: "Data",
					label: __("Payment Reference"),
					default: frm.doc.payment_id,
				},
				{
					fieldname: "posting_date",
					fieldtype: "Date",
					label: __("Date Received"),
					default: frappe.datetime.get_today(),
					reqd: 1,
				},
			],
			primary_action_label: __("Mark as Paid"),
			primary_action(values) {
				frm.call({
					doc: frm.doc,
					method: "mark_paid",
					args: values,
					freeze: true,
				}).then(() => {
					dialog.hide();
					frm.reload_doc();
				});
			},
		});
		dialog.show();
	},
});
