"""Integration tests for the GlobalCart API.

Runs the real FastAPI app in-process via Starlette's TestClient against a
fresh, seeded SQLite database.
"""
import os
import sys
import importlib

import pytest

# Make the globalcart backend importable regardless of where pytest is invoked.
BACKEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "apps", "globalcart", "backend")
)
sys.path.insert(0, BACKEND_DIR)


@pytest.fixture(scope="module")
def client():
    # Use a throwaway DB file for the test run.
    test_db = os.path.join(BACKEND_DIR, "test_globalcart.db")
    if os.path.exists(test_db):
        os.remove(test_db)
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db}"

    from fastapi.testclient import TestClient
    import main as gc_main

    importlib.reload(gc_main)

    with TestClient(gc_main.app) as c:  # triggers startup -> seeding
        yield c

    if os.path.exists(test_db):
        os.remove(test_db)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_get_known_order(client):
    r = client.get("/api/orders/GC-1001")
    assert r.status_code == 200
    data = r.json()
    assert data["order_id"] == "GC-1001"
    assert data["status"] == "DELIVERED"
    assert len(data["events"]) >= 3
    # Customer-facing payload must NOT expose internal system logs.
    assert "system_logs" not in data


def test_get_unknown_order_404(client):
    r = client.get("/api/orders/DOES-NOT-EXIST")
    assert r.status_code == 404


def test_diagnostics_exposes_error_codes(client):
    r = client.get("/api/diagnostics/GC-1042")
    assert r.status_code == 200
    data = r.json()
    assert "system_logs" in data
    assert any("Warehouse_API_Timeout" in c for c in data["error_codes"])
    assert data["recommended_action"]


def test_sync_advances_stuck_order(client):
    # GC-1042 starts stuck in PROCESSING.
    before = client.get("/api/orders/GC-1042").json()
    assert before["status"] == "PROCESSING"

    synced = client.post("/api/orders/GC-1042/sync").json()
    assert synced["synced"] is True
    assert synced["order"]["status"] == "SHIPPED"

    # A second sync is a no-op.
    again = client.post("/api/orders/GC-1042/sync").json()
    assert again["synced"] is False
