# MFA Reset Policy

**Policy ID:** POL-MFA-001
**Owner:** Identity & Access Management (IAM)
**Last reviewed:** 2026-01-15

## Purpose

Defines when and how a user's multi-factor authentication (MFA) enrollment may
be reset, and what identity verification is required first.

## Scope

Applies to all employees and contractors with a corporate identity in the
Employee Self-Service (ESS) system.

## Policy

1. **Identity verification is mandatory** before any MFA reset. The requester
   must pass at least **two** of:
   - Confirmation of a one-time code sent to the registered recovery email.
   - Answering pre-registered security questions.
   - Manager confirmation (for high-privilege accounts).
2. **Self-service resets** are permitted only when the user can authenticate
   with their primary password AND the recovery email.
3. **Agent-assisted resets** require a verified TicketFlow ticket and a logged
   identity-verification step.
4. **High-privilege accounts** (admin, finance, executive) additionally require
   manager approval recorded on the ticket.
5. All MFA resets are logged and audited for 12 months.

## Automatable by agent?

✅ **Yes**, for standard accounts once identity verification passes. Escalate
high-privilege accounts to L2 for manager approval (see the
[Escalation Matrix](../runbooks/escalation-matrix.md)).

## Related

- [Account Lockout Runbook](../runbooks/account-lockout-runbook.md)
- [Password Reset Policy](./password-reset-policy.md)
