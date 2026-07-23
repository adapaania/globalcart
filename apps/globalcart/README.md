# GlobalCart — Order Management System

A simulated internal Order Management application for the fictional "GlobalCart"
retailer. It lets a support agent look up an order, review its customer-facing
timeline, inspect internal system logs & diagnostics, and trigger a manual sync
to unstick orders.

- **Backend:** FastAPI + SQLAlchemy (SQLite)
- **Frontend:** React + Vite + Tailwind CSS
- **Orchestration:** Docker Compose

> 🌐 **Live demo:** https://globalcart-production.up.railway.app
> Try order IDs `GC-1001`, `GC-1042`, `GC-2020`, `GC-3030`.

### Deploying (single-service, Railway)

The included root [`Dockerfile`](./Dockerfile) is a multi-stage build that
compiles the Vite frontend and serves it directly from FastAPI, so the whole
app runs from **one URL / one container**. FastAPI serves `/api/*` and falls
back to the SPA `index.html` for all other routes. The server binds to `$PORT`
(injected by Railway) and defaults to `8000` locally.

```bash
railway up      # from apps/globalcart/
railway domain  # generate the public URL
```

---

## Quick Start (Docker)

```bash
docker-compose up --build
```

Then open the app in your browser:

- **Frontend UI:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API health check:** http://localhost:8000/health

The backend auto-creates the SQLite database and seeds it with the demo orders
on first startup (only when the database is empty).

To stop:

```bash
docker-compose down
```

---

## Running Locally (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The database is seeded automatically on startup. To seed manually:

```bash
python seed_data.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host
```

The Vite dev server proxies `/api` to `http://localhost:8000` (override with the
`VITE_API_TARGET` environment variable).

---

## Test Order IDs

| Order ID  | Scenario                                                                 |
|-----------|--------------------------------------------------------------------------|
| `GC-1001` | Normal order — DELIVERED, payment SUCCESS. Everything green.             |
| `GC-1042` | Payment SUCCESS but stuck in PROCESSING. System log ERROR `Validation_Error: Warehouse_API_Timeout`. Use **Sync Order** to advance it to SHIPPED. |
| `GC-2020` | HELD high-value order ($5,200). System log WARN `HIGH_VALUE_ORDER: Manual financial verification required`. |
| `GC-3030` | PENDING order. System log ERROR `SKU_OUT_OF_STOCK: Item PROD-887 unavailable`. |

---

## API Endpoints

| Method | Path                              | Description                                                                                     |
|--------|-----------------------------------|-------------------------------------------------------------------------------------------------|
| `GET`  | `/health`                         | Health check. Returns `{"status": "ok"}`.                                                       |
| `GET`  | `/api/orders/{order_id}`          | Full customer-facing order: details + timeline events. **Excludes** internal system logs.       |
| `GET`  | `/api/diagnostics/{order_id}`     | Internal state: system logs, extracted `error_codes`, and a `recommended_action`.               |
| `POST` | `/api/orders/{order_id}/sync`     | Simulates a manual sync. If the order is stuck in `PROCESSING`, moves it to `SHIPPED`, appends a "Manual sync triggered by agent" timeline event, and returns the updated order. |

### Example requests

```bash
# Get an order
curl http://localhost:8000/api/orders/GC-1042

# Get diagnostics (internal logs + recommended action)
curl http://localhost:8000/api/diagnostics/GC-1042

# Manually sync a stuck order
curl -X POST http://localhost:8000/api/orders/GC-1042/sync
```

---

## Data Model

- **Order** — `order_id`, customer name/email, `status`
  (PROCESSING / SHIPPED / DELIVERED / HELD / PENDING), `payment_status`
  (SUCCESS / PENDING / FAILED), `total_amount`, `items` (JSON), timestamps.
- **OrderEvent** — customer-facing timeline events (`event_type`, `description`, `actor`).
- **SystemLog** — internal logs (`level` INFO/WARN/ERROR, `message`, `internal_code`).

---

## Project Structure

```
globalcart/
├── backend/          # FastAPI + SQLAlchemy + SQLite
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── seed_data.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/         # React + Vite + Tailwind
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── components/
│   │   └── index.css
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```
