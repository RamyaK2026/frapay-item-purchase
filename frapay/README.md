# Frapay – Item & Purchase Management (ERPNext / Frappe)

A Frappe custom app for **Items, Item Types, multi-line Purchases, stock availability and purchase history**.
Python backend + MariaDB/MySQL, running inside ERPNext. This is the assignment re-implemented on the Frappe
framework instead of Node.js/Express.

## How the assignment maps to Frappe

| Assignment | Frapay |
|---|---|
| `item_types` table | DocType **Frapay Item Type** → table `tabFrapay Item Type` (`id` = `type_name`) |
| `items` table | DocType **Frapay Item** → `tabFrapay Item` (`item_type_id` = `item_type`, `active` check) |
| `purchases` table | DocType **Frapay Purchase** → `tabFrapay Purchase` (`order_id` = `name`, e.g. `PO-00001`) |
| `purchase_items` table | Child table **Frapay Purchase Item** → `tabFrapay Purchase Item` (`purchase_id` = `parent`) |
| Express REST routes | `/api/resource/<DocType>` (Frappe built-in CRUD) + `/api/method/frapay.api.*` |
| React/HTML frontend | Frappe Desk forms, list views, reports (`Item Stock Availability`, `Purchase Details`) |
| MySQL transaction | Frappe wraps each save in one DB transaction; any error rolls everything back |

## Business rules implemented (all on the server, in Python)

* Item: name required, item type must exist, date valid, stock ≥ 0, Active/Inactive.
* Availability: `> 5` In Stock, `1–5` Low Stock, `0` Out of Stock (stored, filterable, coloured in list view).
* Purchase: auto Order ID (`PO-00001`…), ≥ 1 line, item must exist and be **Active**, quantity > 0 (whole number),
  duplicate items in one order are **rejected**, quantity ≤ available stock.
* Create → stock deducted. **Update** → stock adjusted by the *difference* (3→5 deducts 2, 5→2 returns 3;
  removed lines return stock; new lines deduct). Stock can never go negative.
* Item rows are locked (`SELECT … FOR UPDATE`) during validation so concurrent purchases cannot oversell.
* **Purchases cannot be deleted**: no delete permission for any role, `on_trash` throws (403), no delete endpoint,
  no delete button.
* **Items**: deletion is refused (409) once the item appears in any purchase – deactivate instead. Inactive items stay
  visible in purchase details but cannot be selected. Item types in use cannot be deleted.
* Errors: 400 validation, 403 purchase delete, 404 not found, 409 insufficient stock / in-use conflicts.

## Prerequisites

* Python 3.10+ (3.11 recommended)
* MariaDB 10.6+ (or MySQL 8 as supported by your Frappe version)
* Frappe / ERPNext **v15** (bench 5.x), Node 18+ and Redis (only because bench needs them for the Desk assets)

## Install

```bash
# 1. Get the app into your bench (path to this folder, or a git URL)
cd ~/frappe-bench-v2
bench get-app /path/to/frapay            # or: bench get-app https://github.com/<you>/frapay

# 2. Install on your site (creates tables via DocType sync = the "migration")
bench --site <your-site> install-app frapay

# 3. (Optional) demo data matching the assignment example
bench --site <your-site> execute frapay.setup.install.load_sample_data

# 4. Start
bench start
```

Open `http://<site>:<port>/app/frapay`. Database credentials are the site's own (`sites/<site>/site_config.json`,
set when you ran `bench new-site`); nothing extra to configure. After pulling updates: `bench --site <site> migrate`.

Default Item Types created on install: Electronics, Furniture, Clothing, Grocery, Stationery.
Roles: **Frapay Manager** (full, except purchase delete), **Frapay User** (create/edit items & purchases),
**System Manager**.

## Using it (Desk)

1. **Item Type** list → add types.
2. **Frapay Item** → New: name, type, purchase date, stock, Active. Actions menu → *Activate/Deactivate*.
3. **Frapay Purchase** → New: pick items & quantities in the grid (inactive items are filtered out) → Save.
   Order ID is generated; each line shows *Stock After Purchase*.
4. Reopen a purchase, change quantities → Save → stock adjusts by the difference.
5. Reports: **Item Stock Availability** (Item ⨝ Item Type) and **Purchase Details** (Purchase ⨝ Purchase Items ⨝
   Items ⨝ Item Types, filter by Order ID).

## SQL JOINs

See `frapay/api.py` and `frapay/frapay/report/*/*.py`. Example (Purchase Details):

```sql
SELECT p.name AS order_id, p.purchase_date, i.name AS item_id, i.item_name, it.type_name, pi.quantity
FROM `tabFrapay Purchase` p
JOIN `tabFrapay Purchase Item` pi ON p.name = pi.parent AND pi.parenttype = 'Frapay Purchase'
JOIN `tabFrapay Item` i ON pi.item = i.name
JOIN `tabFrapay Item Type` it ON i.item_type = it.name
WHERE p.name = %s;
```

## API

See [API.md](API.md) and the Postman collection [Frapay.postman_collection.json](Frapay.postman_collection.json).

## Tests

```bash
bench --site <site> set-config allow_tests true      # once, dev sites only
bench --site <site> run-tests --app frapay
```

Covers: stock deduction, rejection with no partial save, 3→5→2 adjustment, inactive items, quantity rules,
duplicates, no purchase delete, item delete rule, JOIN API.

## Screenshots

Capture these from your running site for the submission: Item list (with indicators), Item form, Purchase form with
several lines, an "Insufficient stock" error, Purchase Details report, Item Stock Availability report.
