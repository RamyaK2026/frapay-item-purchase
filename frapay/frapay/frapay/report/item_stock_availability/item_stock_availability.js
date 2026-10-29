frappe.query_reports["Item Stock Availability"] = {
	filters: [
		{ fieldname: "item_type", label: __("Item Type"), fieldtype: "Link", options: "Frapay Item Type" },
		{
			fieldname: "availability",
			label: __("Availability"),
			fieldtype: "Select",
			options: "\nIn Stock\nLow Stock\nOut of Stock",
		},
		{ fieldname: "status", label: __("Status"), fieldtype: "Select", options: "\nActive\nInactive" },
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "availability" && data) {
			const color = { "In Stock": "green", "Low Stock": "orange", "Out of Stock": "red" }[data.availability];
			if (color) value = `<span class="indicator-pill ${color}">${data.availability}</span>`;
		}
		return value;
	},
};
