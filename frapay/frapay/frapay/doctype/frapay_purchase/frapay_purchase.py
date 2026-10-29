import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate

from frapay.exceptions import (
	FrapayConflictError,
	FrapayValidationError,
	PurchaseDeletionError,
)
from frapay.utils import get_availability


class FrapayPurchase(Document):
	"""A purchase / order header with many item lines.

	Transaction handling
	--------------------
	Frappe wraps every document insert/save in a single database transaction and
	rolls back on any exception. ``validate`` (checks + row locks) and
	``on_update`` (stock write) run inside that same transaction, together with the
	purchase and purchase-item inserts, so either everything is saved or nothing is.

	Stock handling (create AND update)
	----------------------------------
	For every item we compute ``diff = new_qty - previously_saved_qty``
	(previously saved = 0 on create, 0 for newly added lines, and the new qty is 0
	for removed lines). Stock is reduced by ``diff`` - so raising 3 -> 5 deducts 2
	more, lowering 5 -> 2 returns 3, removing a line returns all of it.
	The purchase is rejected if ``diff`` would push stock below zero.
	"""

	def validate(self):
		self.order_id = self.name
		self.validate_purchase_date()
		self.validate_lines()
		self.plan_stock_changes()
		self.total_quantity = sum(cint(row.quantity) for row in self.items)

	# ------------------------------------------------------------------ checks
	def validate_purchase_date(self):
		if not self.purchase_date:
			frappe.throw(_("Purchase date is required"), FrapayValidationError)
		try:
			getdate(self.purchase_date)
		except Exception:
			frappe.throw(_("Purchase date is invalid"), FrapayValidationError)

	def validate_lines(self):
		if not self.items:
			frappe.throw(_("Purchase must contain at least one item"), FrapayValidationError)

		seen = set()
		for row in self.items:
			if not row.item:
				frappe.throw(_("Row {0}: Item is required").format(row.idx), FrapayValidationError)

			# Duplicate items in one order are rejected (consistent, explicit rule).
			if row.item in seen:
				frappe.throw(
					_(
						"Row {0}: Item {1} is added more than once in this order. "
						"Combine the quantities into a single line."
					).format(row.idx, frappe.bold(row.item)),
					FrapayValidationError,
				)
			seen.add(row.item)

			qty = flt(row.quantity)
			if qty <= 0:
				frappe.throw(
					_("Row {0}: Quantity must be greater than zero").format(row.idx),
					FrapayValidationError,
				)
			if qty != int(qty):
				frappe.throw(
					_("Row {0}: Quantity must be a whole number").format(row.idx),
					FrapayValidationError,
				)
			row.quantity = int(qty)

	# ------------------------------------------------------------ stock logic
	def get_saved_quantities(self):
		"""Quantity per item as currently stored in the database (before this save)."""
		if self.is_new():
			return {}
		rows = frappe.db.sql(
			"""
			SELECT item, SUM(quantity) AS qty
			FROM `tabFrapay Purchase Item`
			WHERE parent = %s AND parenttype = 'Frapay Purchase'
			GROUP BY item
			""",
			(self.name,),
			as_dict=True,
		)
		return {r.item: cint(r.qty) for r in rows}

	def plan_stock_changes(self):
		old_qty = self.get_saved_quantities()
		new_qty = {row.item: cint(row.quantity) for row in self.items}

		changes = {}
		# Lock rows in a stable order (prevents deadlocks, and prevents two
		# concurrent purchases from both passing the stock check).
		for item in sorted(set(old_qty) | set(new_qty)):
			item_row = frappe.db.get_value(
				"Frapay Item",
				item,
				["name", "item_name", "stock_available", "active"],
				as_dict=True,
				for_update=True,
			)
			if not item_row:
				if item in new_qty:
					frappe.throw(
						_("Item not found: {0}").format(frappe.bold(item)),
						frappe.DoesNotExistError,
					)
				continue  # historical line of an item that no longer exists

			prev = old_qty.get(item, 0)
			new = new_qty.get(item, 0)
			diff = new - prev
			stock = cint(item_row.stock_available)

			if diff > 0 and not cint(item_row.active):
				frappe.throw(
					_("Item {0} is inactive and cannot be purchased").format(
						frappe.bold(item_row.item_name)
					),
					FrapayValidationError,
				)

			new_stock = stock - diff
			if new_stock < 0:
				frappe.throw(
					_(
						"Insufficient stock for {0}. Requested: {1}, available: {2}"
					).format(frappe.bold(item_row.item_name), new, stock + prev),
					FrapayConflictError,
				)

			changes[item] = (diff, new_stock)

		self.flags.stock_changes = changes

		for row in self.items:
			row.item_name = frappe.db.get_value("Frapay Item", row.item, "item_name")
			row.item_type = frappe.db.get_value("Frapay Item", row.item, "item_type")
			row.stock_after = changes[row.item][1]

	def on_update(self):
		for item, (diff, new_stock) in (self.flags.stock_changes or {}).items():
			if diff == 0:
				continue
			frappe.db.set_value(
				"Frapay Item",
				item,
				{"stock_available": new_stock, "availability": get_availability(new_stock)},
			)

	# --------------------------------------------------------------- deletion
	def on_trash(self):
		frappe.throw(
			_(
				"Purchases are historical transactions and cannot be deleted. "
				"Use a cancellation workflow if one is required."
			),
			PurchaseDeletionError,
		)
