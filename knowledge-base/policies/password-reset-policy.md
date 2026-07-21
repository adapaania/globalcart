# Password Reset Policy

**Policy ID:** POL-PWD-001
**Owner:** Identity & Access Management (IAM)
**Last reviewed:** 2026-01-15

## Purpose

Defines the rules for resetting user passwords, including complexity, identity
verification, and rate limits.

## Policy

1. **Identity verification** is required before any reset (recovery email OTP or
   security questions; manager confirmation for privileged accounts).
2. **Password complexity:** minimum 12 characters, mix of upper/lower/number/
   symbol, not in the breached-password list, not reused from the last 10.
3. **Temporary passwords** must be changed at first login and expire in 24h.
4. **Rate limit:** no more than 3 self-service resets per 24 hours; further
   attempts require agent assistance.
5. **Lockout interaction:** if the account is locked, follow the
   [Account Lockout Runbook](../runbooks/account-lockout-runbook.md) first.
6. All resets are logged and audited.

## Automatable by agent?

✅ **Yes** for standard accounts after identity verification. Privileged
accounts require L2 + manager approval.

## Related

- [MFA Reset Policy](./mfa-reset-policy.md)
- [Account Lockout Runbook](../runbooks/account-lockout-runbook.md)
