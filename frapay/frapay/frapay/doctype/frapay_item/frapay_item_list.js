frappe.listview_settings["Frapay Item"] = {
	add_fields: ["active", "stock_available", "availability"],
	get_indicator(doc) {
		if (!doc.active) {
			return [__("Inactive"), "gray", "active,=,0"];
		}
		if (doc.availability === "Out of Stock") {
			return [__("Out of Stock"), "red", "availability,=,Out of Stock"];
		}
		if (doc.availability === "Low Stock") {
			return [__("Low Stock"), "orange", "availability,=,Low Stock"];
		}
		return [__("In Stock"), "green", "availability,=,In Stock"];
	},
};
