# TicketFlow API Contract

**Live URL:** `https://ticketflow-production-1ea7.up.railway.app`  
**Local dev:** `http://localhost:8001`  
**Status:** ✅ **Implemented and deployed**

**Auth:** All endpoints except `GET /health` require an `Authorization: Bearer <token>` header. The token is validated against the `TICKETFLOW_API_TOKEN` environment variable.

---

## Endpoints

### `GET /health`
Health check — **no auth required**.

**Response (200)**
```json
{
  "status": "ok",
  "service": "ticketflow",
  "time": "2026-08-05T16:59:27.157604"
}
```

---

### `GET /tickets`
List all tickets. Supports optional query filters:
- `?status=` — filter by status (`open`, `in_progress`, `resolved`, `closed`)
- `?priority=` — filter by priority (`low`, `medium`, `high`, `critical`)

**Response (200)**
```json
{
  "count": 2,
  "tickets": [
    {
      "id": 1,
      "title": "VPN down",
      "description": "Cannot connect from home",
      "status": "open",
      "priority": "high",
      "created_by": "jdoe",
      "assigned_to": null,
      "resolution": null,
      "created_at": "2026-08-05T16:58:01.123456",
      "updated_at": "2026-08-05T16:58:01.123456"
    }
  ]
}
```

**400** — Invalid status or priority enum value.

---

### `GET /tickets/search?q=`
Full-text (LIKE) search over ticket `title` and `description`.

**Response (200)**
```json
{
  "query": "vpn",
  "count": 1,
  "tickets": [ { "id": 1, "title": "VPN down", "..." } ]
}
```

**422** — Missing `q` query parameter.

---

### `GET /tickets/{ticket_id}`
Get a single ticket by ID (includes all comments).

**Response (200)**
```json
{
  "id": 1,
  "title": "VPN down",
  "description": "Cannot connect from home",
  "status": "in_progress",
  "priority": "high",
  "created_by": "jdoe",
  "assigned_to": "tier1",
  "resolution": null,
  "created_at": "2026-08-05T16:58:01.123456",
  "updated_at": "2026-08-05T16:59:15.654321",
  "comments": [
    {
      "id": 1,
      "ticket_id": 1,
      "author": "tier1",
      "body": "Investigating VPN gateway.",
      "created_at": "2026-08-05T16:59:10.123456"
    }
  ]
}
```

**404** — Ticket not found.

---

### `POST /tickets`
Create a new ticket. Returns **201 Created**.

**Request**
```json
{
  "title": "VPN down",
  "description": "Cannot connect from home",
  "priority": "high",
  "created_by": "jdoe",
  "assigned_to": null
}
```

**Response (201)**
```json
{
  "id": 1,
  "title": "VPN down",
  "status": "open",
  "priority": "high",
  "created_by": "jdoe",
  "assigned_to": null,
  "resolution": null,
  "created_at": "2026-08-05T16:58:01.123456",
  "updated_at": "2026-08-05T16:58:01.123456",
  "comments": []
}
```

**400** — Invalid priority.  
**422** — Missing required fields (e.g., `title`).

---

### `POST /tickets/{ticket_id}/update`
Update a ticket's `status`, `priority`, and/or `assigned_to` (partial update).

**Request** (any subset of these fields)
```json
{
  "status": "in_progress",
  "priority": "high",
  "assigned_to": "tier1"
}
```

**Response (200)** — Full updated ticket (with comments).

**400** — Invalid status/priority enum value or no fields provided.  
**404** — Ticket not found.

---

### `POST /tickets/{ticket_id}/comment`
Add a comment to a ticket. Returns **201 Created**.

**Request**
```json
{
  "author": "tier1",
  "body": "Investigating VPN gateway."
}
```

**Response (201)** — Full updated ticket (with the new comment included).

**404** — Ticket not found.  
**422** — Missing `body` or empty body.

---

### `POST /tickets/{ticket_id}/close`
Close a ticket with a resolution note.

**Request**
```json
{
  "resolution": "Restarted VPN gateway. User reconnected."
}
```

**Response (200)** — Ticket with `status` set to `closed` and `resolution` populated.

**404** — Ticket not found.  
**422** — Missing `resolution`.

---

## Enums

- **status:** `open`, `in_progress`, `resolved`, `closed`
- **priority:** `low`, `medium`, `high`, `critical`

---

## Quick test

```bash
TOKEN=<your-token>
BASE=https://ticketflow-production-1ea7.up.railway.app

# Health (no auth)
curl $BASE/health

# Create ticket
curl -X POST $BASE/tickets -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"VPN down","description":"Cannot connect from home","priority":"high","created_by":"jdoe"}'

# List tickets
curl $BASE/tickets -H "Authorization: Bearer $TOKEN"

# Search
curl "$BASE/tickets/search?q=vpn" -H "Authorization: Bearer $TOKEN"

# Update ticket
curl -X POST $BASE/tickets/1/update -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress","assigned_to":"tier1"}'

# Add comment
curl -X POST $BASE/tickets/1/comment -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"author":"tier1","body":"Investigating."}'

# Close ticket
curl -X POST $BASE/tickets/1/close -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resolution":"Restarted VPN gateway."}'
```

---

**Related:** [`apps/ticketflow/backend/README.md`](../../apps/ticketflow/backend/README.md)
