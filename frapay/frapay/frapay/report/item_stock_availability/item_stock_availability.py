import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("Item ID"), "fieldname": "item_id", "fieldtype": "Link", "options": "Frapay Item", "width": 110},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 180},
		{"label": _("Item Type"), "fieldname": "type_name", "fieldtype": "Link", "options": "Frapay Item Type", "width": 140},
		{"label": _("Purchase Date"), "fieldname": "purchase_date", "fieldtype": "Date", "width": 110},
		{"label": _("Current Stock"), "fieldname": "stock_available", "fieldtype": "Int", "width": 110},
		{"label": _("Availability"), "fieldname": "availability", "fieldtype": "Data", "width": 110},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
	]


def get_data(filters):
	conditions, values = [], {}

	if filters.item_type:
		conditions.append("i.item_type = %(item_type)s")
		values["item_type"] = filters.item_type
	if filters.availability:
		conditions.append("i.availability = %(availability)s")
		values["availability"] = filters.availability
	if filters.status == "Active":
		conditions.append("i.active = 1")
	elif filters.status == "Inactive":
		conditions.append("i.active = 0")

	where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

	# JOIN: Item + Item Type
	return frappe.db.sql(
		f"""
		SELECT i.name AS item_id, i.item_name, it.type_name, i.purchase_date,
		       i.stock_available, i.availability,
		       CASE WHEN i.active = 1 THEN 'Active' ELSE 'Inactive' END AS status
		FROM `tabFrapay Item` i
		JOIN `tabFrapay Item Type` it ON i.item_type = it.name
		{where}
		ORDER BY i.item_name
		""",
		values,
		as_dict=True,
	)
