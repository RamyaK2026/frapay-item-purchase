"""Custom REST endpoints (JOIN-based reads + item activation).

Standard CRUD is already exposed by Frappe at /api/resource/<DocType> and goes
through the DocType controllers, so all backend validation applies to it too.
These endpoints live at /api/method/frapay.api.<name>.

Table mapping used in the JOINs (assignment table -> Frappe table):
  item_types      -> `tabFrapay Item Type`      (id == name == type_name)
  items           -> `tabFrapay Item`           (item_type_id == item_type)
  purchases       -> `tabFrapay Purchase`       (order_id == name)
  purchase_items  -> `tabFrapay Purchase Item`  (purchase_id == parent, item_id == item)
"""

import frappe
from frappe import _
from frappe.utils import cint

from frapay.exceptions import FrapayValidationError


@frappe.whitelist(methods=["GET"])
def get_items(item_type=None, active=None, availability=None, search=None):
	"""Item list with Item Type resolved through a JOIN."""
	frappe.has_permission("Frapay Item", "read", throw=True)

	conditions, values = [], {}
	if item_type:
		conditions.append("i.item_type = %(item_type)s")
		values["item_type"] = item_type
	if active not in (None, ""):
		conditions.append("i.active = %(active)s")
		values["active"] = cint(active)
	if availability:
		conditions.append("i.availability = %(availability)s")
		values["availability"] = availability
	if search:
		conditions.append("i.item_name LIKE %(search)s")
		values["search"] = f"%{search}%"
	where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

	return frappe.db.sql(
		f"""
		SELECT i.name AS id, i.item_name AS name, it.type_name, i.purchase_date,
		       i.stock_available, i.availability, i.active
		FROM `tabFrapay Item` i
		JOIN `tabFrapay Item Type` it ON i.item_type = it.name
		{where}
		ORDER BY i.item_name
		""",
		values,
		as_dict=True,
	)


@frappe.whitelist(methods=["GET"])
def get_item(item):
	"""One item with its type (JOIN) and the purchases it appears in."""
	frappe.has_permission("Frapay Item", "read", throw=True)

	rows = frappe.db.sql(
		"""
		SELECT i.name AS id, i.item_name AS name, it.type_name, i.purchase_date,
		       i.stock_available, i.availability, i.active
		FROM `tabFrapay Item` i
		JOIN `tabFrapay Item Type` it ON i.item_type = it.name
		WHERE i.name = %s
		""",
		(item,),
		as_dict=True,
	)
	if not rows:
		frappe.throw(_("Item not found"), frappe.DoesNotExistError)

	result = rows[0]
	result["purchases"] = frappe.db.sql(
		"""
		SELECT p.name AS order_id, p.purchase_date, pi.quantity
		FROM `tabFrapay Purchase` p
		JOIN `tabFrapay Purchase Item` pi ON p.name = pi.parent
		WHERE pi.item = %s AND pi.parenttype = 'Frapay Purchase'
		ORDER BY p.purchase_date DESC, p.name DESC
		""",
		(item,),
		as_dict=True,
	)
	return result


@frappe.whitelist(methods=["GET"])
def get_purchases():
	"""Purchase list with line count and total quantity (JOIN + GROUP BY)."""
	frappe.has_permission("Frapay Purchase", "read", throw=True)

	return frappe.db.sql(
		"""
		SELECT p.name AS order_id, p.purchase_date,
		       COUNT(pi.name) AS line_count, SUM(pi.quantity) AS total_quantity
		FROM `tabFrapay Purchase` p
		JOIN `tabFrapay Purchase Item` pi
		  ON p.name = pi.parent AND pi.parenttype = 'Frapay Purchase'
		GROUP BY p.name, p.purchase_date
		ORDER BY p.purchase_date DESC, p.name DESC
		""",
		as_dict=True,
	)


@frappe.whitelist(methods=["GET"])
def get_purchase(order_id):
	"""Purchase Details: Purchase + Purchase Items + Items + Item Types (4-table JOIN)."""
	frappe.has_permission("Frapay Purchase", "read", throw=True)

	rows = frappe.db.sql(
		"""
		SELECT p.name AS order_id, p.purchase_date,
		       i.name AS item_id, i.item_name, it.type_name, pi.quantity,
		       pi.stock_after, i.stock_available AS current_stock,
		       i.availability, i.active
		FROM `tabFrapay Purchase` p
		JOIN `tabFrapay Purchase Item` pi
		  ON p.name = pi.parent AND pi.parenttype = 'Frapay Purchase'
		JOIN `tabFrapay Item` i ON pi.item = i.name
		JOIN `tabFrapay Item Type` it ON i.item_type = it.name
		WHERE p.name = %s
		ORDER BY pi.idx
		""",
		(order_id,),
		as_dict=True,
	)
	if not rows:
		frappe.throw(_("Purchase not found"), frappe.DoesNotExistError)

	return {
		"order_id": rows[0].order_id,
		"purchase_date": rows[0].purchase_date,
		"items": rows,
	}


@frappe.whitelist(methods=["GET"])
def get_stock():
	"""Stock / Availability view."""
	return get_items()


@frappe.whitelist(methods=["POST"])
def set_item_active(item, active):
	"""Activate / deactivate an item (the preferred alternative to deleting it)."""
	frappe.has_permission("Frapay Item", "write", throw=True)

	if not frappe.db.exists("Frapay Item", item):
		frappe.throw(_("Item not found"), frappe.DoesNotExistError)
	if str(active).lower() not in ("0", "1", "true", "false"):
		frappe.throw(_("active must be 0 or 1"), FrapayValidationError)

	doc = frappe.get_doc("Frapay Item", item)
	doc.active = 1 if str(active).lower() in ("1", "true") else 0
	doc.save()
	return {"id": doc.name, "active": doc.active}
