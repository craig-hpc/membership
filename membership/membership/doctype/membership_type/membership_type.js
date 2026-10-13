// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Membership Type", {
	refresh(frm) {
		frm.set_query("linked_item", () => {
			return { filters: { is_stock_item: 0 } };
		});
	},
});
