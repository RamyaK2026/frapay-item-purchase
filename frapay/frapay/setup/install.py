import frappe
from frappe.utils import today

DEFAULT_ITEM_TYPES = ["Electronics", "Furniture", "Clothing", "Grocery", "Stationery"]

SAMPLE_ITEMS = [
	# (item_name, item_type, stock)
	("Laptop", "Electronics", 10),
	("Mouse", "Electronics", 20),
	("Keyboard", "Electronics", 30),
	("Chair", "Furniture", 15),
]


def after_install():
	create_item_types()


def create_item_types():
	for type_name in DEFAULT_ITEM_TYPES:
		if not frappe.db.exists("Frapay Item Type", type_name):
			frappe.get_doc({"doctype": "Frapay Item Type", "type_name": type_name}).insert(
				ignore_permissions=True
			)


def load_sample_data():
	"""Optional demo data (matches the assignment's end-to-end example).

	bench --site <site> execute frapay.setup.install.load_sample_data
	"""
	create_item_types()
	for item_name, item_type, stock in SAMPLE_ITEMS:
		if frappe.db.exists("Frapay Item", {"item_name": item_name}):
			continue
		frappe.get_doc(
			{
				"doctype": "Frapay Item",
				"item_name": item_name,
				"item_type": item_type,
				"purchase_date": today(),
				"stock_available": stock,
				"active": 1,
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()
