# Agentic IT Support Simulation

A teaching monorepo for building an **agentic IT support system** step by step.
It contains several simulated business applications, a shared knowledge base of
policies and runbooks, and an agent orchestrator that (in later weeks) resolves
support tickets by calling those apps' APIs and grounding its decisions in the
knowledge base via RAG.

> **Where we are today:** the **GlobalCart** app (`apps/globalcart`) is fully
> implemented and demoable. The other apps, the agent orchestrator, and the RAG
> pipeline are scaffolded and land over the coming weeks.

## Repository structure

```
agentic-it-support-simulation/
├── .github/                  # CI, deploy, PR & issue templates
├── apps/
│   ├── globalcart/           # ✅ Order Management System (implemented)
│   ├── ticketflow/           # 🚧 IT Service Desk (Week 1)
│   └── employee-self-service/# 🚧 Identity / IAM portal (Week 1)
├── services/
│   └── agent-orchestrator/   # 🚧 Supervisor + L1/L2 agents, tools, RAG (Week 2/3)
├── knowledge-base/           # Policies + runbooks (RAG source)
├── infra/                    # Docker (full stack) + deployment config
├── tests/                    # Integration tests + golden tickets
├── docs/                     # Architecture, API contracts, ADRs, demo scripts
├── .env.example              # Root shared env template
├── CONTRIBUTING.md
└── README.md
```

## Quick start — GlobalCart

```bash
cd apps/globalcart
docker-compose up --build
```

- **Frontend UI:** http://localhost:5173
- **Backend API:** http://localhost:8000  (health: `/health`)

See [`apps/globalcart/README.md`](./apps/globalcart/README.md) for full details,
local (non-Docker) setup, the demo order IDs, and API docs.

### Run the whole stack (as apps come online)

```bash
docker compose -f infra/docker/docker-compose.full.yml up --build
```

## Running tests

```bash
pip install -r apps/globalcart/backend/requirements.txt pytest httpx
pytest tests/integration -v
```

GlobalCart tests run today; TicketFlow and agent-routing tests are skipped until
those components are implemented.

## Documentation

- [System architecture](./docs/architecture/system-diagram.md)
- API contracts:
  [GlobalCart](./docs/api-contracts/globalcart-api.md) ·
  [TicketFlow](./docs/api-contracts/ticketflow-api.md) ·
  [Identity](./docs/api-contracts/identity-api.md)
- [ADR-001: Tech stack](./docs/decisions/ADR-001-tech-stack.md)
- [Week 1 demo script](./docs/demo-scripts/week1-demo.md)
- [Knowledge base](./knowledge-base) — policies & runbooks

## Roadmap

| Week    | Deliverable                                                            |
|---------|------------------------------------------------------------------------|
| Week 0  | ✅ GlobalCart app (orders, diagnostics, manual sync) + monorepo scaffold |
| Week 1  | 🚧 TicketFlow + Employee Self-Service apps                             |
| Week 2  | 🚧 Knowledge base + RAG ingestion & retrieval                          |
| Week 2/3| 🚧 Agent orchestrator: supervisor + L1/L2 agents, tools, routing       |

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for branching, commit conventions, and
local checks.
