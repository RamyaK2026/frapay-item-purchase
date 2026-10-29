frappe.query_reports["Purchase Details"] = {
	filters: [
		{ fieldname: "order_id", label: __("Order ID"), fieldtype: "Link", options: "Frapay Purchase" },
		{ fieldname: "item", label: __("Item"), fieldtype: "Link", options: "Frapay Item" },
		{ fieldname: "from_date", label: __("From Date"), fieldtype: "Date" },
		{ fieldname: "to_date", label: __("To Date"), fieldtype: "Date" },
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
