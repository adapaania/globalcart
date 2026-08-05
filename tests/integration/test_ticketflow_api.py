"""Integration tests for the TicketFlow ITSM API.

Spins up the FastAPI app against a fresh temporary SQLite database and a known
API token, then exercises the read/write endpoints and the Bearer-token guard.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "apps", "ticketflow", "backend"
)

TOKEN = "test-token-123"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture()
def client():
    """Fresh app + fresh SQLite DB per test."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["TICKETFLOW_API_TOKEN"] = TOKEN

    sys.path.insert(0, os.path.abspath(BACKEND_DIR))
    if "main" in sys.modules:
        del sys.modules["main"]
    main = importlib.import_module("main")

    with TestClient(main.app) as c:
        yield c

    sys.path.remove(os.path.abspath(BACKEND_DIR))
    os.remove(db_path)


def test_health_no_auth(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_auth_required(client):
    assert client.get("/tickets").status_code == 401
    assert client.get("/tickets", headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_create_and_get_ticket(client):
    r = client.post(
        "/tickets",
        headers=AUTH,
        json={"title": "VPN down", "description": "Cannot connect", "priority": "high", "created_by": "jdoe"},
    )
    assert r.status_code == 201
    tid = r.json()["id"]
    assert r.json()["status"] == "open"

    g = client.get(f"/tickets/{tid}", headers=AUTH)
    assert g.status_code == 200
    assert g.json()["title"] == "VPN down"
    assert g.json()["comments"] == []


def test_create_validation(client):
    assert client.post("/tickets", headers=AUTH, json={"title": "x", "priority": "urgent"}).status_code == 400
    assert client.post("/tickets", headers=AUTH, json={"description": "no title"}).status_code == 422


def test_get_missing_404(client):
    assert client.get("/tickets/9999", headers=AUTH).status_code == 404


def test_filters_and_search(client):
    client.post("/tickets", headers=AUTH, json={"title": "VPN down", "description": "vpn issue", "priority": "high"})
    client.post("/tickets", headers=AUTH, json={"title": "Printer jam", "description": "printer", "priority": "low"})

    assert client.get("/tickets", headers=AUTH).json()["count"] == 2
    assert client.get("/tickets?priority=high", headers=AUTH).json()["count"] == 1
    assert client.get("/tickets?status=nope", headers=AUTH).status_code == 400
    assert client.get("/tickets/search?q=printer", headers=AUTH).json()["count"] == 1


def test_update_comment_close(client):
    tid = client.post("/tickets", headers=AUTH, json={"title": "VPN down", "priority": "high"}).json()["id"]

    u = client.post(f"/tickets/{tid}/update", headers=AUTH, json={"status": "in_progress", "assigned_to": "tier1"})
    assert u.status_code == 200
    assert u.json()["status"] == "in_progress"
    assert u.json()["assigned_to"] == "tier1"

    cm = client.post(f"/tickets/{tid}/comment", headers=AUTH, json={"author": "tier1", "body": "Investigating."})
    assert cm.status_code == 201
    assert len(cm.json()["comments"]) == 1

    cl = client.post(f"/tickets/{tid}/close", headers=AUTH, json={"resolution": "Restarted gateway."})
    assert cl.status_code == 200
    assert cl.json()["status"] == "closed"
    assert cl.json()["resolution"] == "Restarted gateway."
