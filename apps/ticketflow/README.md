# TicketFlow — IT Service Desk (Week 1, coming next)

> **Status: 🚧 Scaffold / planned.** This app is part of Week 1 and is not yet implemented.

TicketFlow is the simulated IT Service Management (ITSM) system for the Agentic
IT Support simulation. It will expose a ticketing API (create, read, update,
assign, comment, resolve) that the agent orchestrator uses as its primary
system of record for support tickets.

## Planned stack

- **Backend:** FastAPI + SQLAlchemy (SQLite for local dev)
- **Frontend:** React + Vite + Tailwind CSS
- **Orchestration:** Docker Compose

## Planned structure

```
ticketflow/
├── backend/          # FastAPI ticket API
├── frontend/         # React agent console
├── docker-compose.yml
├── .env.example
└── README.md
```

## Planned API (draft)

| Method | Path                        | Description                     |
|--------|-----------------------------|---------------------------------|
| `POST` | `/api/tickets`              | Create a ticket                 |
| `GET`  | `/api/tickets/{id}`         | Get a ticket                    |
| `PATCH`| `/api/tickets/{id}`         | Update status / assignee        |
| `POST` | `/api/tickets/{id}/comments`| Add a comment / work note       |

See [`docs/api-contracts/ticketflow-api.md`](../../docs/api-contracts/ticketflow-api.md)
for the authoritative contract.
