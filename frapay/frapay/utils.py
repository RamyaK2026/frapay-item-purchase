from frappe.utils import cint

LOW_STOCK_THRESHOLD = 5


def get_availability(stock):
	"""Stock > 5 -> In Stock, 1..5 -> Low Stock, 0 -> Out of Stock."""
	stock = cint(stock)
	if stock <= 0:
		return "Out of Stock"
	if stock <= LOW_STOCK_THRESHOLD:
		return "Low Stock"
	return "In Stock"
