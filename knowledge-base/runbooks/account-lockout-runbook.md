# Runbook: Account Lockout

**Runbook ID:** RB-LOCK-001
**Applies to:** Employee Self-Service (identity) accounts
**Severity:** Medium

## Symptoms

- User reports "account locked" or repeated failed logins.
- Identity API returns account state `LOCKED`.

## Diagnosis

1. Look up the employee: `GET /api/employees/{id}`.
2. Check `failed_attempts`, `locked_until`, and `last_login`.
3. Determine the cause:
   - Too many failed attempts (most common).
   - Suspicious login / risk flag (escalate — do **not** auto-unlock).
   - Stale cached credentials on a device.

## Resolution

| Cause                         | Action                                                        | Tier |
|-------------------------------|---------------------------------------------------------------|------|
| Too many failed attempts      | Verify identity, then `POST /api/employees/{id}/unlock`.      | L1   |
| Forgotten password            | Follow the [Password Reset Policy](../policies/password-reset-policy.md). | L1 |
| Suspicious / risk-flagged     | Do **not** unlock. Escalate to security.                      | L2   |
| Repeated lockouts (device)    | Unlock + advise clearing cached credentials; open follow-up.  | L1   |

## Verification

- Confirm account state returns to `ACTIVE`.
- Confirm the user can authenticate.
- Add a work note to the TicketFlow ticket and resolve.

## Related

- [MFA Reset Policy](../policies/mfa-reset-policy.md)
- [Escalation Matrix](./escalation-matrix.md)
