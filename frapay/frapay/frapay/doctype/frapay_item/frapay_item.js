frappe.ui.form.on("Frapay Item", {
	refresh(frm) {
		if (frm.is_new()) return;

		// Status indicator next to the title
		if (!frm.doc.active) {
			frm.dashboard.add_indicator(__("Inactive"), "gray");
		} else {
			const colors = { "In Stock": "green", "Low Stock": "orange", "Out of Stock": "red" };
			frm.dashboard.add_indicator(
				__("{0}: {1}", [frm.doc.availability, frm.doc.stock_available]),
				colors[frm.doc.availability] || "blue"
			);
		}

		// Activate / Deactivate
		const label = frm.doc.active ? __("Deactivate") : __("Activate");
		frm.add_custom_button(
			label,
			() => {
				if (frm.is_dirty()) {
					frappe.msgprint(__("Please save your changes first."));
					return;
				}
				frappe.call({
					method: "frapay.api.set_item_active",
					args: { item: frm.doc.name, active: frm.doc.active ? 0 : 1 },
					callback: () => frm.reload_doc(),
				});
			},
			__("Actions")
		);

		// Purchase history of this item (JOIN report)
		frm.add_custom_button(
			__("Purchase History"),
			() => frappe.set_route("query-report", "Purchase Details", { item: frm.doc.name }),
			__("View")
		);
	},
});
