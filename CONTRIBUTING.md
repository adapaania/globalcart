# Contributing

Thanks for contributing to the Agentic IT Support simulation! This guide covers
branching, commits, PRs, and local checks.

## Repository layout

```
apps/                 # independent business apps (globalcart, ticketflow, ess)
services/             # agent-orchestrator (the agent brain)
knowledge-base/       # policies + runbooks (RAG source)
infra/                # docker + deployment config
tests/                # integration tests + golden tickets
docs/                 # architecture, API contracts, ADRs, demo scripts
```

## Branching model

- `main` — stable, deployable.
- `develop` — integration branch; merges here deploy to **staging**.
- Feature work branches off `develop`:
  - `feature/<short-description>`
  - `fix/<short-description>`
  - `chore/<short-description>`
  - `docs/<short-description>`

Open PRs into `develop` (or `main` for hotfixes).

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(globalcart): add manual sync endpoint
fix(frontend): correct status badge color for HELD
docs(adr): record tech-stack decision
test(globalcart): cover diagnostics error codes
chore(ci): cache npm install
```

## Local development

### GlobalCart (implemented)

```bash
# Backend
cd apps/globalcart/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd apps/globalcart/frontend
npm install
npm run dev -- --host
```

Or the whole app with Docker:

```bash
cd apps/globalcart && docker-compose up --build
```

## Running checks before you push

```bash
# Backend tests
pip install pytest httpx
pytest tests/integration -v

# Frontend build
cd apps/globalcart/frontend && npm install && npm run build
```

CI runs these on every PR (`.github/workflows/ci.yml`). PRs must be green.

## Pull requests

1. Fill out the PR template checklist.
2. Keep PRs focused and reasonably small.
3. Update docs / API contracts when behavior changes.
4. Never commit secrets or `.env` files.

## Code style

- **Python:** PEP 8, type hints where practical, docstrings on public functions.
- **JS/React:** functional components + hooks; keep components small.
- Prefer clarity over cleverness; comment non-obvious logic.
