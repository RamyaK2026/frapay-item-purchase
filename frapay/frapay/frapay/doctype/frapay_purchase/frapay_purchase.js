frappe.ui.form.on("Frapay Purchase", {
	setup(frm) {
		// Inactive items must not be selectable for a purchase.
		frm.set_query("item", "items", () => ({ filters: { active: 1 } }));
	},

	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(
			__("Purchase Details"),
			() => frappe.set_route("query-report", "Purchase Details", { order_id: frm.doc.name }),
			__("View")
		);
	},
});

frappe.ui.form.on("Frapay Purchase Item", {
	item(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.item) return;

		const duplicate = (frm.doc.items || []).some((r) => r.name !== row.name && r.item === row.item);
		if (duplicate) {
			frappe.msgprint(__("Item {0} is already in this order. Combine the quantities.", [row.item]));
			frappe.model.set_value(cdt, cdn, "item", null);
			return;
		}

		frappe.db.get_value("Frapay Item", row.item, ["stock_available", "item_name"]).then((r) => {
			const stock = r.message.stock_available;
			frappe.show_alert({
				message: __("{0}: {1} in stock", [r.message.item_name, stock]),
				indicator: stock > 0 ? "green" : "red",
			});
		});
	},

	quantity(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.quantity != null && row.quantity <= 0) {
			frappe.msgprint(__("Quantity must be greater than zero"));
		}
	},
});
