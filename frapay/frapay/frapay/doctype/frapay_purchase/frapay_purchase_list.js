frappe.listview_settings["Frapay Purchase"] = {
	add_fields: ["total_quantity", "purchase_date"],
	// Purchases are historical: no bulk delete is offered (and the server blocks it anyway).
	hide_name_column: false,
};
