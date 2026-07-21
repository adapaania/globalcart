# Runbook: GlobalCart Known Errors

**Runbook ID:** RB-GC-001
**Applies to:** GlobalCart Order Management System
**Severity:** Varies

This runbook maps GlobalCart internal error codes (from
`GET /api/diagnostics/{order_id}`) to their meaning and remediation.

## Known error codes

### `Validation_Error: Warehouse_API_Timeout`
- **Meaning:** The warehouse fulfillment API timed out; the order is stuck in
  `PROCESSING` even though payment succeeded.
- **Impact:** Order not dispatched.
- **Resolution (L1):** Trigger a manual sync —
  `POST /api/orders/{order_id}/sync`. This re-dispatches and moves the order to
  `SHIPPED`. Verify the new status and add a work note.
- **If sync fails twice:** escalate to L2 (warehouse integration).

### `HIGH_VALUE_ORDER`
- **Meaning:** Order value exceeded the auto-approval threshold and was placed
  on `HELD` for manual financial verification.
- **Impact:** Order paused pending review.
- **Resolution (L2):** Route to the finance team for verification; do **not**
  auto-release. Once verified, finance releases the hold.

### `SKU_OUT_OF_STOCK`
- **Meaning:** One or more line-item SKUs are unavailable in all fulfillment
  centers; order remains `PENDING`.
- **Impact:** Cannot fulfill as-is.
- **Resolution (L1):** Confirm stock, then offer the customer a substitute,
  backorder, or refund. If restock ETA is known, communicate it. Escalate to L2
  for high-value or bulk orders.

## General triage

1. `GET /api/orders/{id}` for the customer-facing state + timeline.
2. `GET /api/diagnostics/{id}` for internal logs, `error_codes`, and
   `recommended_action`.
3. Follow the code-specific resolution above.
4. Record the action on the ticket and verify the outcome.

## Related

- [GlobalCart API contract](../../docs/api-contracts/globalcart-api.md)
- [Escalation Matrix](./escalation-matrix.md)
