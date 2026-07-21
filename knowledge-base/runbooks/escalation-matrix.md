# Runbook: Escalation Matrix

**Runbook ID:** RB-ESC-001
**Purpose:** Defines who handles what, and when to escalate between tiers.

## Tiers

| Tier | Who / What                | Handles                                                        |
|------|---------------------------|----------------------------------------------------------------|
| L1   | First-line automated agent| Routine, documented, automatable requests.                     |
| L2   | Second-line automated agent| Complex, multi-step, or judgement-heavy requests.             |
| L3   | Human specialist          | Anything requiring human authority, approval, or investigation.|

## Routing rules

| Scenario                                   | Route to | Reason                              |
|--------------------------------------------|----------|-------------------------------------|
| Password reset (standard account)          | L1       | Documented + automatable            |
| MFA reset (standard account)               | L1       | Documented + automatable            |
| MFA / password reset (privileged account)  | L2 → L3  | Needs manager approval              |
| Account locked (failed attempts)           | L1       | Unlock after identity verification  |
| Account locked (risk / suspicious)         | L2 → security | Potential compromise           |
| GlobalCart stuck order (warehouse timeout) | L1       | Manual sync resolves it             |
| GlobalCart HELD high-value order           | L2 → finance | Financial verification          |
| GlobalCart SKU out of stock (high value)   | L2       | Business decision on substitute     |
| Access request (sensitive system)          | L2 → owner | Requires approver sign-off        |
| Anything unresolved after 2 L1 attempts    | L2       | Avoid loops                         |
| Suspected security incident                | L3 (human) | Human authority required          |

## Escalation etiquette

1. Summarize what was tried and the current state.
2. Attach relevant diagnostics / error codes.
3. Reference the applicable policy or runbook.
4. Set ticket priority per impact and urgency.

## Related

- [MFA Reset Policy](../policies/mfa-reset-policy.md)
- [Access Request Policy](../policies/access-request-policy.md)
- [GlobalCart Known Errors](./globalcart-known-errors.md)
