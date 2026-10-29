"""Exceptions carrying the HTTP status codes the assignment asks for.

Frappe's request handler uses ``http_status_code`` on the exception class, so
REST calls (/api/resource/...) and whitelisted methods return:

* 400 - validation errors
* 403 - forbidden operations (purchase deletion)
* 404 - missing records (frappe.DoesNotExistError, built in)
* 409 - business conflicts (insufficient stock, item used in history)
"""

import frappe


class FrapayValidationError(frappe.ValidationError):
	http_status_code = 400


class FrapayConflictError(frappe.ValidationError):
	http_status_code = 409


class PurchaseDeletionError(frappe.ValidationError):
	http_status_code = 403
