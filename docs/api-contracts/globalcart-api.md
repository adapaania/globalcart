# GlobalCart API Contract

**Base URL (local):** `http://localhost:8000`
**Status:** ✅ Implemented

## Endpoints

### `GET /api/orders`
List all orders with optional filtering and pagination.

**Query Parameters:**
- `status` (optional) — filter by order status: `PROCESSING`, `SHIPPED`, `DELIVERED`, `HELD`, `PENDING`
- `payment_status` (optional) — filter by payment status: `SUCCESS`, `PENDING`, `FAILED`
- `limit` (optional, default 100) — max results per page
- `offset` (optional, default 0) — pagination offset

**200**
```json
{
  "total": 4,
  "limit": 100,
  "offset": 0,
  "count": 4,
  "orders": [
    {
      "order_id": "GC-3030",
      "customer_name": "Diana Green",
      "customer_email": "diana.green@example.com",
      "status": "PENDING",
      "payment_status": "PENDING",
      "total_amount": 79.99,
      "items": [...],
      "created_at": "2026-07-22T10:05:00",
      "updated_at": "2026-07-22T10:05:00"
    }
  ]
}
```

**Examples:**
```bash
# List all orders
curl https://globalcart-production.up.railway.app/api/orders

# Filter by status
curl https://globalcart-production.up.railway.app/api/orders?status=PROCESSING

# Filter by payment status
curl https://globalcart-production.up.railway.app/api/orders?payment_status=SUCCESS

# Pagination
curl https://globalcart-production.up.railway.app/api/orders?limit=10&offset=0

# Combined filters
curl https://globalcart-production.up.railway.app/api/orders?status=DELIVERED&payment_status=SUCCESS
```

---

### `GET /health`
Health probe.

**200**
```json
{ "status": "ok" }
```

---

### `GET /api/orders/{order_id}`
Customer-facing order details and timeline. **Does not** expose internal system
logs.

**200**
```json
{
  "order_id": "GC-1001",
  "customer_name": "Alice Johnson",
  "customer_email": "alice.johnson@example.com",
  "status": "DELIVERED",
  "payment_status": "SUCCESS",
  "total_amount": 149.99,
  "items": [
    { "sku": "PROD-101", "name": "Wireless Headphones", "qty": 1, "price": 99.99 }
  ],
  "created_at": "2026-07-15T10:00:00",
  "updated_at": "2026-07-18T10:00:00",
  "events": [
    {
      "id": 1,
      "timestamp": "2026-07-15T10:00:00",
      "event_type": "ORDER_PLACED",
      "description": "Order placed by customer.",
      "actor": "customer"
    }
  ]
}
```

**404** — order not found.

---

### `GET /api/diagnostics/{order_id}`
Internal state: system logs, extracted error codes, and a recommended action.

**200**
```json
{
  "order_id": "GC-1042",
  "status": "PROCESSING",
  "payment_status": "SUCCESS",
  "system_logs": [
    {
      "id": 5,
      "timestamp": "2026-07-19T22:10:00",
      "level": "ERROR",
      "message": "Validation_Error: Warehouse_API_Timeout while dispatching fulfillment request.",
      "internal_code": "Validation_Error: Warehouse_API_Timeout"
    }
  ],
  "error_codes": ["Validation_Error: Warehouse_API_Timeout"],
  "recommended_action": "Warehouse API timed out during fulfillment. Trigger a manual sync ..."
}
```

**404** — order not found.

---

### `POST /api/orders/{order_id}/sync`
Simulates a manual sync. If the order is stuck in `PROCESSING`, advances it to
`SHIPPED`, appends a `MANUAL_SYNC` timeline event, and logs the action.

**200 (advanced)**
```json
{
  "synced": true,
  "message": "Order was stuck in PROCESSING and has been advanced to SHIPPED.",
  "order": { "order_id": "GC-1042", "status": "SHIPPED", "...": "..." }
}
```

**200 (no-op)**
```json
{
  "synced": false,
  "message": "No sync action needed. Order status is 'DELIVERED'.",
  "order": { "...": "..." }
}
```

**404** — order not found.

### `POST /api/orders/push`
Bulk data-ingest / upsert. Accepts a batch of records; for each one, **updates**
the order if `order_id` already exists (fields overwritten, `events`/`logs`
appended), otherwise **creates** it (using the supplied `order_id` if given and
free, else an auto-generated `GC-XXXX`). Lets an external system push and modify
GlobalCart data in a single call.

**Request**
```json
{
  "orders": [
    {
      "order_id": "GC-5001",
      "customer_name": "Ext System",
      "customer_email": "ext@example.com",
      "total_amount": 250.0,
      "status": "PROCESSING",
      "payment_status": "SUCCESS",
      "items": [{ "sku": "PROD-1", "name": "Widget", "qty": 2, "price": 125.0 }],
      "events": [{ "event_type": "IMPORTED", "description": "Synced from ERP", "actor": "erp" }],
      "logs": [{ "level": "INFO", "message": "Imported via push", "internal_code": "OK_IMPORT" }]
    },
    { "customer_name": "No-id order (auto GC-XXXX)", "customer_email": "a@b.com", "total_amount": 10 },
    { "order_id": "GC-1001", "status": "HELD" }
  ]
}
```

**200**
```json
{
  "pushed": 3,
  "created": ["GC-5001", "GC-3031"],
  "updated": ["GC-1001"],
  "orders": [ { "order_id": "GC-5001", "...": "..." } ]
}
```

**422** — invalid enum value or empty `orders` list.

---

## Enums

- **status:** `PROCESSING`, `SHIPPED`, `DELIVERED`, `HELD`, `PENDING`
- **payment_status:** `SUCCESS`, `PENDING`, `FAILED`
- **log level:** `INFO`, `WARN`, `ERROR`

## Demo order IDs

| Order ID  | Scenario                                             |
|-----------|------------------------------------------------------|
| `GC-1001` | Normal delivered order, all green.                   |
| `GC-1042` | Payment OK, stuck in PROCESSING (warehouse timeout). |
| `GC-2020` | HELD high-value order ($5,200).                      |
| `GC-3030` | PENDING, SKU out of stock.                           |
