# TicketFlow API Contract (draft)

**Base URL (local):** `http://localhost:8001`
**Status:** 🚧 Planned (Week 1)

> This is a draft contract for the upcoming TicketFlow app. Endpoints and
> schemas may change as it is implemented.

## Endpoints

### `POST /api/tickets`
Create a ticket.

**Request**
```json
{
  "subject": "Locked out of my account",
  "body": "I can't log in after several attempts.",
  "requester_email": "carlos.diaz@example.com",
  "channel": "phone",
  "priority": "medium"
}
```

**201**
```json
{ "id": "TF-1001", "status": "OPEN", "assignee": null, "created_at": "..." }
```

---

### `GET /api/tickets/{id}`
Fetch a ticket (with comments/work notes).

---

### `PATCH /api/tickets/{id}`
Update status and/or assignee.

**Request**
```json
{ "status": "IN_PROGRESS", "assignee": "l1-agent" }
```

---

### `POST /api/tickets/{id}/comments`
Add a comment / work note.

**Request**
```json
{ "author": "l1-agent", "body": "Verified identity; unlocking account." }
```

## Enums (draft)

- **status:** `OPEN`, `IN_PROGRESS`, `PENDING`, `RESOLVED`, `CLOSED`
- **priority:** `low`, `medium`, `high`, `urgent`
