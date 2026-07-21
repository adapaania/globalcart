# Access Request Policy

**Policy ID:** POL-ACC-001
**Owner:** Identity & Access Management (IAM)
**Last reviewed:** 2026-01-15

## Purpose

Governs how employees request access to systems, applications, and data, and
how those requests are approved and provisioned.

## Policy

1. **Least privilege:** users receive the minimum access required for their role.
2. **Approval chain:** every request needs approval from the resource owner and,
   for sensitive systems, the requester's manager.
3. **Role-based access (RBAC):** prefer role assignment over individual grants.
4. **Segregation of duties:** conflicting permissions (e.g. create + approve
   payments) must not be granted to the same user.
5. **Time-bound access:** elevated/temporary access must have an expiry date.
6. **Recertification:** access is reviewed quarterly; unused access is revoked.

## Automatable by agent?

⚠️ **Partially.** The agent may gather the request, validate the role, and open
a TicketFlow approval workflow, but **provisioning requires approver sign-off**.
Sensitive-system requests always route to L2. See the
[Escalation Matrix](../runbooks/escalation-matrix.md).

## Related

- [MFA Reset Policy](./mfa-reset-policy.md)
- [Escalation Matrix](../runbooks/escalation-matrix.md)
