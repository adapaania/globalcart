# Agent Orchestrator (Week 2/3 — the agent brain)

> **Status: 🚧 Scaffold / planned.** Structure is in place; logic lands in Week 2/3.

The orchestrator is the "brain" of the Agentic IT Support simulation. It
receives a ticket, decides how to handle it, calls the right tools against the
downstream apps (GlobalCart, TicketFlow, Employee Self-Service), and grounds its
reasoning in the knowledge base via RAG.

## Architecture

```
        ┌─────────────┐
Ticket →│ Supervisor  │  classify + route
        └──────┬──────┘
        ┌──────┴───────┐
        ▼              ▼
   ┌─────────┐   ┌─────────┐
   │ L1 Agent│   │ L2 Agent│
   └────┬────┘   └────┬────┘
        │  tools + RAG │
        ▼              ▼
  GlobalCart / TicketFlow / Identity APIs
```

## Structure

```
agent-orchestrator/
├── agents/
│   ├── supervisor.py   # routes tickets to L1/L2
│   ├── l1_agent.py     # routine, automatable requests
│   └── l2_agent.py     # complex / escalated requests
├── tools/
│   ├── ticketflow_tools.py
│   ├── globalcart_tools.py
│   └── identity_tools.py
├── rag/
│   ├── ingest.py       # chunk + embed knowledge-base docs
│   └── retriever.py    # semantic retrieval
├── main.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Environment (planned)

| Variable               | Description                                | Default                 |
|------------------------|--------------------------------------------|-------------------------|
| `GLOBALCART_BASE_URL`  | GlobalCart API base URL                    | `http://localhost:8000` |
| `TICKETFLOW_BASE_URL`  | TicketFlow API base URL                    | `http://localhost:8001` |
| `IDENTITY_BASE_URL`    | Employee Self-Service API base URL         | `http://localhost:8002` |
| `KNOWLEDGE_BASE_DIR`   | Path to the `knowledge-base/` directory    | repo `knowledge-base/`  |
| `OPENAI_API_KEY`       | LLM provider key (Week 2/3)                | —                       |
