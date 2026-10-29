import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate

from frapay.exceptions import FrapayConflictError, FrapayValidationError
from frapay.utils import get_availability


class FrapayItem(Document):
	def validate(self):
		self.item_name = (self.item_name or "").strip()
		if not self.item_name:
			frappe.throw(_("Item name is required"), FrapayValidationError)

		if not self.item_type or not frappe.db.exists("Frapay Item Type", self.item_type):
			frappe.throw(_("Invalid item type"), FrapayValidationError)

		if not self.purchase_date:
			frappe.throw(_("Purchase date is required"), FrapayValidationError)
		try:
			getdate(self.purchase_date)
		except Exception:
			frappe.throw(_("Purchase date is invalid"), FrapayValidationError)

		if self.stock_available is None or cint(self.stock_available) < 0:
			frappe.throw(_("Stock cannot be negative"), FrapayValidationError)
		self.stock_available = cint(self.stock_available)

		self.availability = get_availability(self.stock_available)

	def on_trash(self):
		# An item that already appears in a purchase must stay for audit.
		# Deactivate it instead (Inactive items stay visible in purchase history).
		if frappe.db.exists("Frapay Purchase Item", {"item": self.name}):
			frappe.throw(
				_(
					"Item {0} is used in purchase history and cannot be deleted. "
					"Mark it Inactive instead."
				).format(frappe.bold(self.item_name)),
				FrapayConflictError,
			)
