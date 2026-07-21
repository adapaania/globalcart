# Identity (Employee Self-Service) API Contract (draft)

**Base URL (local):** `http://localhost:8002`
**Status:** 🚧 Planned (Week 1)

> Draft contract for the upcoming Employee Self-Service (ESS) app. Subject to
> change during implementation.

## Endpoints

### `GET /api/employees/{id}`
Look up an employee and account state.

**200**
```json
{
  "id": "E-1001",
  "name": "Carlos Diaz",
  "email": "carlos.diaz@example.com",
  "account_type": "standard",
  "account_state": "LOCKED",
  "failed_attempts": 5,
  "locked_until": "2026-07-21T18:00:00",
  "mfa_enrolled": true
}
```

---

### `POST /api/employees/{id}/mfa/reset`
Reset MFA enrollment. Requires prior identity verification
(see [MFA Reset Policy](../../knowledge-base/policies/mfa-reset-policy.md)).

---

### `POST /api/employees/{id}/password/reset`
Trigger a password reset
(see [Password Reset Policy](../../knowledge-base/policies/password-reset-policy.md)).

---

### `POST /api/employees/{id}/unlock`
Unlock a locked account
(see [Account Lockout Runbook](../../knowledge-base/runbooks/account-lockout-runbook.md)).

## Enums (draft)

- **account_type:** `standard`, `privileged`
- **account_state:** `ACTIVE`, `LOCKED`, `DISABLED`
