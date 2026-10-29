import frappe
from frappe import _
from frappe.model.document import Document

from frapay.exceptions import FrapayConflictError, FrapayValidationError


class FrapayItemType(Document):
	def validate(self):
		self.type_name = (self.type_name or "").strip()
		if not self.type_name:
			frappe.throw(_("Item type name is required"), FrapayValidationError)

	def on_trash(self):
		# item_types 1 -> many items: never orphan an item.
		count = frappe.db.count("Frapay Item", {"item_type": self.name})
		if count:
			frappe.throw(
				_("Item type {0} is used by {1} item(s) and cannot be deleted").format(
					frappe.bold(self.name), count
				),
				FrapayConflictError,
			)
