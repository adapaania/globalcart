# TicketFlow — ITSM REST API

A lean IT Service Management (ITSM) ticketing API. Budget-first: **FastAPI +
Uvicorn + SQLite + SQLAlchemy Core + Pydantic v2**. No PostgreSQL, no Redis, no
Celery, no Docker, no external auth provider, no paid APIs.

**🚀 Live deployment:** https://ticketflow-production-1ea7.up.railway.app

## Data model

**Ticket** — `id`, `title`, `description`, `status`, `priority`, `created_by`,
`assigned_to`, `resolution`, `created_at`, `updated_at`
**Comment** — `id`, `ticket_id`, `author`, `body`, `created_at`

- **status:** `open`, `in_progress`, `resolved`, `closed`
- **priority:** `low`, `medium`, `high`, `critical`

## Auth

Every endpoint **except `GET /health`** requires a static Bearer token:

```
Authorization: Bearer <TICKETFLOW_API_TOKEN>
```

The token is read from the `TICKETFLOW_API_TOKEN` environment variable — no JWT
library, no secret hardcoded in source.

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET`  | `/health` | ❌ | Health check |
| `GET`  | `/tickets` | ✅ | List tickets; `?status=` and `?priority=` filters |
| `GET`  | `/tickets/{id}` | ✅ | Get a single ticket (with comments) |
| `GET`  | `/tickets/search?q=` | ✅ | Full-text search on title + description |
| `POST` | `/tickets` | ✅ | Create a ticket → **201** |
| `POST` | `/tickets/{id}/update` | ✅ | Update `status` / `priority` / `assigned_to` |
| `POST` | `/tickets/{id}/comment` | ✅ | Add a comment → **201** |
| `POST` | `/tickets/{id}/close` | ✅ | Close with a `resolution` note |

Status codes: `200`, `201` (create), `400` (bad enum / no fields),
`401` (bad/missing token), `404` (not found), `422` (schema validation).

## Run locally

```bash
cd apps/ticketflow/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then edit TICKETFLOW_API_TOKEN
export $(grep -v '^#' .env | xargs)
uvicorn main:app --reload --port 8001
```

SQLite DB and tables are created automatically on startup.

Interactive docs: <http://localhost:8001/docs>

## Quick test

```bash
TOKEN=your-token
BASE=http://localhost:8001

curl $BASE/health

curl -X POST $BASE/tickets -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"VPN down","description":"Cannot connect from home","priority":"high","created_by":"jdoe"}'

curl "$BASE/tickets?status=open" -H "Authorization: Bearer $TOKEN"
curl "$BASE/tickets/search?q=vpn" -H "Authorization: Bearer $TOKEN"

curl -X POST $BASE/tickets/1/update -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"status":"in_progress","assigned_to":"tier1"}'

curl -X POST $BASE/tickets/1/comment -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"author":"tier1","body":"Investigating."}'

curl -X POST $BASE/tickets/1/close -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"resolution":"Restarted VPN gateway."}'
```

## Deploy (free tier)

**Railway / Render** — a `Procfile` is included:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Set `TICKETFLOW_API_TOKEN` (and optionally `DATABASE_URL`) as environment
variables in the dashboard. The platform injects `PORT` automatically.
