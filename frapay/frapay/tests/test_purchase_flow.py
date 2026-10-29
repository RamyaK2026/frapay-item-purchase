"""End-to-end checks for the assignment's business rules.

Run with:  bench --site <site> run-tests --app frapay
"""

import frappe
from frappe.utils import today

try:  # Frappe v16
	from frappe.tests import IntegrationTestCase as BaseTestCase
except ImportError:  # Frappe v14 / v15
	from frappe.tests.utils import FrappeTestCase as BaseTestCase


def make_type(name="Electronics"):
	if not frappe.db.exists("Frapay Item Type", name):
		frappe.get_doc({"doctype": "Frapay Item Type", "type_name": name}).insert()
	return name


def make_item(name, stock, active=1, item_type="Electronics"):
	make_type(item_type)
	return frappe.get_doc(
		{
			"doctype": "Frapay Item",
			"item_name": name,
			"item_type": item_type,
			"purchase_date": today(),
			"stock_available": stock,
			"active": active,
		}
	).insert()


def make_purchase(*lines, save=True):
	doc = frappe.get_doc(
		{
			"doctype": "Frapay Purchase",
			"purchase_date": today(),
			"items": [{"item": item.name, "quantity": qty} for item, qty in lines],
		}
	)
	return doc.insert() if save else doc


def stock(item):
	return frappe.db.get_value("Frapay Item", item.name, "stock_available")


class TestPurchaseFlow(BaseTestCase):
	def test_purchase_deducts_stock_and_sets_availability(self):
		laptop, mouse = make_item("T Laptop", 10), make_item("T Mouse", 20)
		po = make_purchase((laptop, 2), (mouse, 5))
		self.assertTrue(po.order_id.startswith("PO-"))
		self.assertEqual(stock(laptop), 8)
		self.assertEqual(stock(mouse), 15)
		self.assertEqual(frappe.db.get_value("Frapay Item", laptop.name, "availability"), "In Stock")

	def test_insufficient_stock_rejected_and_nothing_saved(self):
		laptop, mouse = make_item("T Laptop2", 8), make_item("T Mouse2", 20)
		with self.assertRaises(frappe.ValidationError):
			make_purchase((mouse, 5), (laptop, 15))
		self.assertEqual(stock(laptop), 8)
		self.assertEqual(stock(mouse), 20)  # the valid line must not have been applied
		self.assertFalse(frappe.db.exists("Frapay Purchase Item", {"item": laptop.name}))

	def test_exact_stock_allowed_and_goes_out_of_stock(self):
		item = make_item("T Exact", 4)
		make_purchase((item, 4))
		self.assertEqual(stock(item), 0)
		self.assertEqual(frappe.db.get_value("Frapay Item", item.name, "availability"), "Out of Stock")

	def test_update_adjusts_stock_by_difference(self):
		item = make_item("T Adjust", 10)
		po = make_purchase((item, 3))
		self.assertEqual(stock(item), 7)

		po.items[0].quantity = 5  # 3 -> 5 : deduct 2 more
		po.save()
		self.assertEqual(stock(item), 5)

		po.reload()
		po.items[0].quantity = 2  # 5 -> 2 : return 3
		po.save()
		self.assertEqual(stock(item), 8)

	def test_update_cannot_exceed_stock(self):
		item = make_item("T UpdLimit", 10)
		po = make_purchase((item, 3))  # stock 7
		po.items[0].quantity = 11  # needs 8 more, only 7 left
		with self.assertRaises(frappe.ValidationError):
			po.save()
		self.assertEqual(stock(item), 7)

	def test_removed_line_returns_stock_and_new_line_deducts(self):
		a, b = make_item("T LineA", 10), make_item("T LineB", 10)
		po = make_purchase((a, 4))
		po.items = []
		po.append("items", {"item": b.name, "quantity": 6})
		po.save()
		self.assertEqual(stock(a), 10)
		self.assertEqual(stock(b), 4)

	def test_inactive_item_blocked(self):
		item = make_item("T Inactive", 10, active=0)
		with self.assertRaises(frappe.ValidationError):
			make_purchase((item, 1))
		self.assertEqual(stock(item), 10)

	def test_quantity_must_be_positive(self):
		item = make_item("T Qty", 10)
		for qty in (0, -3):
			with self.assertRaises(frappe.ValidationError):
				make_purchase((item, qty))

	def test_duplicate_items_rejected(self):
		item = make_item("T Dup", 10)
		with self.assertRaises(frappe.ValidationError):
			make_purchase((item, 1), (item, 2))

	def test_purchase_needs_at_least_one_item(self):
		doc = frappe.get_doc({"doctype": "Frapay Purchase", "purchase_date": today(), "items": []})
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_purchase_cannot_be_deleted(self):
		item = make_item("T NoDelete", 10)
		po = make_purchase((item, 1))
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Frapay Purchase", po.name, force=True)
		self.assertTrue(frappe.db.exists("Frapay Purchase", po.name))
		self.assertEqual(stock(item), 9)

	def test_used_item_cannot_be_deleted_but_unused_can(self):
		used, unused = make_item("T Used", 10), make_item("T Unused", 10)
		make_purchase((used, 1))
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Frapay Item", used.name)
		frappe.delete_doc("Frapay Item", unused.name)
		self.assertFalse(frappe.db.exists("Frapay Item", unused.name))

	def test_item_validation(self):
		make_type()
		base = {"doctype": "Frapay Item", "purchase_date": today(), "item_type": "Electronics"}
		with self.assertRaises(frappe.ValidationError):  # missing name
			frappe.get_doc({**base, "item_name": "  ", "stock_available": 1}).insert()
		with self.assertRaises(frappe.ValidationError):  # negative stock
			frappe.get_doc({**base, "item_name": "T Neg", "stock_available": -1}).insert()
		with self.assertRaises(frappe.ValidationError):  # invalid type
			frappe.get_doc({**base, "item_name": "T BadType", "item_type": "Nope", "stock_available": 1}).insert()

	def test_item_type_in_use_cannot_be_deleted(self):
		make_item("T TypeUse", 1, item_type="Stationery")
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Frapay Item Type", "Stationery")

	def test_purchase_details_api_uses_join(self):
		from frapay.api import get_purchase

		item = make_item("T Join", 10)
		po = make_purchase((item, 2))
		data = get_purchase(po.name)
		self.assertEqual(data["items"][0]["type_name"], "Electronics")
		self.assertEqual(data["items"][0]["quantity"], 2)
		self.assertEqual(data["items"][0]["current_stock"], 8)
