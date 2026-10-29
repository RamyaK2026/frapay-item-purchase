# Frapay API

Base URL: `http://<site>:<port>`. Authenticate with an API key/secret (User → API Access → Generate Keys):

```
Authorization: token <api_key>:<api_secret>
Content-Type: application/json
```

Standard CRUD is Frappe's REST resource API (all server validation applies). Item/type/purchase IDs are
document names: items `ITM-00001`, purchases `PO-00001`, item types = their name (e.g. `Electronics`).

## Item Types

| Action | Request |
|---|---|
| List | `GET /api/resource/Frapay Item Type?fields=["name","type_name"]` |
| Create | `POST /api/resource/Frapay Item Type` `{"type_name":"Electronics"}` |
| Update | `PUT /api/resource/Frapay Item Type/Electronics` `{"description":"..."}` |
| Delete | `DELETE /api/resource/Frapay Item Type/Electronics` → **409** if items use it |

## Items

| Action | Request |
|---|---|
| Create | `POST /api/resource/Frapay Item` `{"item_name":"Laptop","item_type":"Electronics","purchase_date":"2026-10-29","stock_available":10,"active":1}` |
| List (JOIN) | `GET /api/method/frapay.api.get_items?item_type=Electronics&active=1&availability=In Stock&search=lap` |
| Detail (JOIN + purchases) | `GET /api/method/frapay.api.get_item?item=ITM-00001` |
| Update | `PUT /api/resource/Frapay Item/ITM-00001` `{"stock_available":25}` |
| Activate / Deactivate | `POST /api/method/frapay.api.set_item_active` `{"item":"ITM-00001","active":0}` |
| Delete | `DELETE /api/resource/Frapay Item/ITM-00001` → **409** if used in any purchase (deactivate instead) |
| Stock / availability | `GET /api/method/frapay.api.get_stock` |

## Purchases

| Action | Request |
|---|---|
| Create | `POST /api/resource/Frapay Purchase` (below) |
| List | `GET /api/method/frapay.api.get_purchases` |
| Details (4-table JOIN) | `GET /api/method/frapay.api.get_purchase?order_id=PO-00001` |
| Update | `PUT /api/resource/Frapay Purchase/PO-00001` with the **full** `items` list |
| Delete | **Not allowed** – `DELETE /api/resource/Frapay Purchase/PO-00001` → **403** |

Create:

```json
{
  "purchase_date": "2026-10-29",
  "items": [
    {"item": "ITM-00001", "quantity": 2},
    {"item": "ITM-00002", "quantity": 5},
    {"item": "ITM-00004", "quantity": 3}
  ]
}
```

Response `data.name` is the Order ID (`PO-00001`). Stock after: Laptop 10→8, Mouse 20→15, Chair 15→12.

Update (3 → 5 of an item deducts 2 more; 5 → 2 returns 3). Send the complete list; lines you omit are removed
and their stock returned:

```json
{"items": [{"item": "ITM-00001", "quantity": 5}]}
```

## Errors

Frappe returns `{"exc_type": "...", "_server_messages": "[...]"}` with the status below.

| Situation | Message | HTTP |
|---|---|---|
| Missing item name | Item name is required | 400 |
| Bad item type | Invalid item type | 400 |
| Negative stock | Stock cannot be negative | 400 |
| Item not found | Item not found | 404 |
| Inactive item | Item *X* is inactive and cannot be purchased | 400 |
| Quantity ≤ 0 | Row N: Quantity must be greater than zero | 400 |
| Empty / duplicate lines | Purchase must contain at least one item / Row N: Item … added more than once | 400 |
| Insufficient stock | Insufficient stock for *X*. Requested: 15, available: 8 | 409 |
| Delete a purchase | Purchases are historical transactions and cannot be deleted | 403 |
| Delete used item / type | … is used in purchase history… / … is used by N item(s) | 409 |
| Unexpected DB error | Generic server error (no SQL details unless `developer_mode`) | 500 |
