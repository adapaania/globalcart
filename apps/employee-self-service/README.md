# Employee Self-Service (ESS) — Identity & Access Portal (Week 1, coming next)

> **Status: 🚧 Scaffold / planned.** This app is part of Week 1 and is not yet implemented.

The Employee Self-Service app simulates an identity and access management (IAM)
portal. It will provide the identity APIs the agent uses to handle common IT
requests such as MFA resets, password resets, account-lockout checks, and
access requests.

## Planned stack

- **Backend:** FastAPI + SQLAlchemy (SQLite for local dev)
- **Frontend:** React + Vite + Tailwind CSS
- **Orchestration:** Docker Compose

## Planned structure

```
employee-self-service/
├── backend/          # FastAPI identity API
├── frontend/         # React self-service portal
├── docker-compose.yml
├── .env.example
└── README.md
```

## Planned API (draft)

| Method | Path                             | Description                          |
|--------|----------------------------------|--------------------------------------|
| `GET`  | `/api/employees/{id}`            | Look up an employee / account state  |
| `POST` | `/api/employees/{id}/mfa/reset`  | Reset MFA enrollment                 |
| `POST` | `/api/employees/{id}/password/reset` | Trigger a password reset         |
| `POST` | `/api/employees/{id}/unlock`     | Unlock a locked account              |

See [`docs/api-contracts/identity-api.md`](../../docs/api-contracts/identity-api.md)
for the authoritative contract.
