# ADR-001: Tech Stack

- **Status:** Accepted
- **Date:** 2026-07-21
- **Deciders:** Project maintainers

## Context

We need a stack for a multi-app "Agentic IT Support" simulation used for
teaching. It must be quick to run locally, easy to containerize, approachable
for students, and friendly to LLM-agent integration via clean HTTP APIs.

## Decision

- **Backend:** FastAPI (Python 3.11) + SQLAlchemy + SQLite.
  - Fast to build, automatic OpenAPI docs, minimal boilerplate.
  - SQLite keeps local dev zero-config; can swap to Postgres later via
    `DATABASE_URL`.
- **Frontend:** React + Vite + Tailwind CSS.
  - Fast dev server, simple component model, utility-first styling.
- **Orchestration:** Docker + Docker Compose per app, plus a full-stack compose
  in `infra/docker`.
- **Agent orchestrator:** Python service that calls each app via HTTP tools and
  grounds decisions with RAG over the `knowledge-base/`.
- **Monorepo layout:** `apps/`, `services/`, `knowledge-base/`, `infra/`,
  `tests/`, `docs/` — clear separation, shared CI.

## Consequences

**Positive**
- One language (Python) across backends and the agent lowers the learning curve.
- Clean per-app APIs make the agent integration realistic and testable.
- Compose files make the whole system reproducible.

**Trade-offs**
- SQLite is not for production concurrency — acceptable for a simulation; the
  `DATABASE_URL` seam allows switching to Postgres.
- A monorepo needs discipline (branching, CODEOWNERS) as it grows — addressed in
  [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Alternatives considered

- **Node/Express everywhere:** rejected to keep the agent + backends in one
  language.
- **Django:** heavier than needed for small API surfaces.
- **Next.js full-stack:** couples frontend and backend more than we want for the
  tools-over-APIs teaching goal.
