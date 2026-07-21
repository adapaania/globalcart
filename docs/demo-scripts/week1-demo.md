# Week 1 Demo Script

A ~10-minute walkthrough of what's working today: the **GlobalCart** app and the
monorepo scaffolding for the weeks ahead.

## 0. Setup (before the demo)

```bash
cd apps/globalcart
docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend:  http://localhost:8000  (health: `/health`)

## 1. The happy path — `GC-1001` (~1 min)

1. Search `GC-1001`.
2. Show status **DELIVERED**, payment **SUCCESS**, item table, and the full
   timeline. "This is what a healthy order looks like."

## 2. The stuck order — `GC-1042` (~3 min)

1. Search `GC-1042`. Status is **PROCESSING**, payment **SUCCESS**.
2. "Customer paid but nothing shipped — why?" Click **Show System Logs**.
3. Point out the `ERROR` log `Validation_Error: Warehouse_API_Timeout` and the
   **Recommended Action**.
4. Click **Sync Order**. Watch it advance to **SHIPPED** with a new
   *"Manual sync triggered by agent"* timeline event.
5. "In Week 2/3, the **agent** will read these diagnostics and call this exact
   sync tool automatically."

## 3. Needs a human — `GC-2020` and `GC-3030` (~2 min)

1. Search `GC-2020`: **HELD**, $5,200. Logs show `HIGH_VALUE_ORDER` (WARN).
   "This one routes to L2 → finance, not auto-resolved."
2. Search `GC-3030`: **PENDING**. Logs show `SKU_OUT_OF_STOCK`.
   "Business decision required — substitute, backorder, or refund."

## 4. The bigger picture (~3 min)

1. Show the repo structure: `apps/`, `services/agent-orchestrator`,
   `knowledge-base/`, `tests/`, `docs/`.
2. Open `knowledge-base/runbooks/globalcart-known-errors.md` — "these error codes
   map to runbook steps the agent will retrieve via RAG."
3. Open `tests/golden-tickets/gc_stuck_order.json` — "these are the scenarios the
   agent must handle correctly; CI will check routing."
4. Run the tests:
   ```bash
   pytest tests/integration -v
   ```
   Show GlobalCart tests passing and the agent/ticketflow tests skipped
   (coming next).

## Talking points

- Each app is independent with a clean API → realistic tool integration.
- The agent will act **through** these APIs, grounded by the knowledge base.
- Tiered autonomy: automate the routine (L1), escalate the rest (L2 → human).
