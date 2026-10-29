import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("Order ID"), "fieldname": "order_id", "fieldtype": "Link", "options": "Frapay Purchase", "width": 120},
		{"label": _("Purchase Date"), "fieldname": "purchase_date", "fieldtype": "Date", "width": 110},
		{"label": _("Item ID"), "fieldname": "item_id", "fieldtype": "Link", "options": "Frapay Item", "width": 110},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 170},
		{"label": _("Item Type"), "fieldname": "type_name", "fieldtype": "Link", "options": "Frapay Item Type", "width": 130},
		{"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Int", "width": 90},
		{"label": _("Stock After Purchase"), "fieldname": "stock_after", "fieldtype": "Int", "width": 140},
		{"label": _("Current Stock"), "fieldname": "current_stock", "fieldtype": "Int", "width": 110},
		{"label": _("Availability"), "fieldname": "availability", "fieldtype": "Data", "width": 110},
		{"label": _("Item Status"), "fieldname": "item_status", "fieldtype": "Data", "width": 90},
	]


def get_data(filters):
	conditions, values = [], {}

	if filters.order_id:
		conditions.append("p.name = %(order_id)s")
		values["order_id"] = filters.order_id
	if filters.item:
		conditions.append("pi.item = %(item)s")
		values["item"] = filters.item
	if filters.from_date:
		conditions.append("p.purchase_date >= %(from_date)s")
		values["from_date"] = filters.from_date
	if filters.to_date:
		conditions.append("p.purchase_date <= %(to_date)s")
		values["to_date"] = filters.to_date

	where = ("AND " + " AND ".join(conditions)) if conditions else ""

	# JOIN: Purchase + Purchase Items + Items + Item Types
	# (Inactive items still show up here - purchase history is never hidden.)
	return frappe.db.sql(
		f"""
		SELECT p.name AS order_id, p.purchase_date,
		       i.name AS item_id, i.item_name, it.type_name, pi.quantity,
		       pi.stock_after, i.stock_available AS current_stock, i.availability,
		       CASE WHEN i.active = 1 THEN 'Active' ELSE 'Inactive' END AS item_status
		FROM `tabFrapay Purchase` p
		JOIN `tabFrapay Purchase Item` pi
		  ON p.name = pi.parent AND pi.parenttype = 'Frapay Purchase'
		JOIN `tabFrapay Item` i ON pi.item = i.name
		JOIN `tabFrapay Item Type` it ON i.item_type = it.name
		WHERE 1 = 1 {where}
		ORDER BY p.purchase_date DESC, p.name DESC, pi.idx
		""",
		values,
		as_dict=True,
	)
