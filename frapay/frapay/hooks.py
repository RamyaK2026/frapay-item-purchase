app_name = "frapay"
app_title = "Frapay"
app_publisher = "Frapay"
app_description = "Item & Purchase Management for ERPNext - items, item types, multi-line purchases with stock validation"
app_email = "support@example.com"
app_license = "mit"

# Runs once on `bench --site <site> install-app frapay`
# Creates the default Item Types (Electronics, Furniture, ...).
after_install = "frapay.setup.install.after_install"

# Purchases are historical transactions: no delete hook is exposed anywhere.
# (Deletion is additionally blocked in the DocType controller - see
#  frapay/frapay/doctype/frapay_purchase/frapay_purchase.py)
