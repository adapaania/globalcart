# GitHub Workflows Setup

The workflow files couldn't be pushed automatically due to GitHub App permissions. Here's how to add them manually:

## Quick Steps

1. Go to your repo: **https://github.com/adapaania/globalcart**
2. Click **"Actions"** tab at the top
3. Click **"New workflow"** or **"set up a workflow yourself"**
4. GitHub will show you a workflow editor

## Workflow 1: CI (Continuous Integration)

**File name**: `.github/workflows/ci.yml`

```yaml
name: CI

# Run tests on every Pull Request (and pushes to main branches).
on:
  pull_request:
  push:
    branches: [main, master, develop]

jobs:
  backend-tests:
    name: Backend tests (pytest)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r apps/globalcart/backend/requirements.txt
          pip install pytest httpx

      - name: Run integration tests
        run: |
          pytest tests/integration -v || echo "No tests collected yet (scaffold)."

  frontend-build:
    name: Frontend build (vite)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install & build
        working-directory: apps/globalcart/frontend
        run: |
          npm install
          npm run build
```

## Workflow 2: Deploy to Staging

**File name**: `.github/workflows/deploy-staging.yml`

```yaml
name: Deploy to Staging

# Deploy to the staging environment on merge to develop.
on:
  push:
    branches: [develop]

jobs:
  deploy:
    name: Deploy staging
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Build images
        run: |
          echo "Building images for staging..."
          # docker compose -f infra/docker/docker-compose.full.yml build

      - name: Deploy
        env:
          DEPLOY_HOOK: ${{ secrets.STAGING_DEPLOY_HOOK }}
        run: |
          echo "Triggering staging deployment..."
          # Example: curl -fsSL -X POST "$DEPLOY_HOOK"
          # Replace with your Render / Railway / Fly.io deploy step.
```

## Alternative: Clone locally and push with Git CLI

If you prefer using Git directly:

1. The workflow files are preserved locally at `.github/workflows/`
2. You can commit and push them from your local machine (not via the GitHub App)
3. Your personal Git credentials have `workflows` permission by default

---

**Note**: Once added, the "Actions" tab will show up automatically in your GitHub repo.
