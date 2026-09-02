#!/usr/bin/env python3
"""
GlobalCart Automation - Create tickets for all orders (idempotent)

Fixes:
- Safely loads .env using python-dotenv if available, otherwise falls back to a lightweight .env parser.
- Prints loaded values (without secrets) to help debug env issues.
- Keeps existing behavior (dry-run by default; use --force or CREATE_ALL=true to actually create).
"""
from __future__ import annotations
import os
import sys
import json
import time
import argparse
import sqlite3
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

# -----------------------
# Robust .env loader (uses python-dotenv if available; otherwise a safe fallback)
# -----------------------
def load_env_file_fallback(path: str = ".env") -> None:
    """
    Lightweight .env parser: sets variables into os.environ only if not already set.
    Supports lines like: KEY=VALUE, KEY="VALUE", and ignores comments / blank lines.
    """
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                # strip surrounding quotes if present
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                # only set if not already present in environment
                if os.getenv(key) is None:
                    os.environ[key] = val
    except Exception:
        # do not crash on .env read errors
        pass

# Try to use python-dotenv if present
try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
    _dotenv_path = find_dotenv(usecwd=True)
    if _dotenv_path:
        load_dotenv(_dotenv_path, override=False)
    else:
        # fallback to manual parser if file not found by find_dotenv
        load_env_file_fallback(".env")
except Exception:
    # python-dotenv not installed -- use fallback parser
    load_env_file_fallback(".env")

# -----------------------
# Config (env)
# -----------------------
ROUTELLM_API_KEY = os.getenv("ROUTELLM_API_KEY")  # optional
ROUTELLM_BASE = os.getenv("ROUTELLM_BASE", "https://routellm.abacus.ai/v1").rstrip("/")
GLOBALCART_BASE = os.getenv("GLOBALCART_BASE", "https://globalcart-production.up.railway.app").rstrip("/")
TICKETFLOW_BASE = os.getenv("TICKETFLOW_BASE_URL", os.getenv("TICKETFLOW_BASE", "")).rstrip("/")
TICKETFLOW_TOKEN = os.getenv("TICKETFLOW_API_TOKEN", os.getenv("TICKETFLOW_TOKEN", ""))

LOG_FILE = os.getenv("LOG_FILE", "ticket_audit.log")
SQLITE_DB = os.getenv("SQLITE_DB", "created_tickets.db")
RATE_LIMIT_SECONDS = float(os.getenv("RATE_LIMIT_SECONDS", "0.8"))
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "20"))
CREATE_ALL_ENV = os.getenv("CREATE_ALL", "false").lower() == "true"

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")  # not used for full auto-create by default

# Print a short debug line (do NOT print secrets)
def dbg_env():
    print(f"[{now_iso()}] CONFIG: GLOBALCART_BASE={GLOBALCART_BASE} TICKETFLOW_BASE={TICKETFLOW_BASE or '<not set>'} TOKEN_SET={'yes' if TICKETFLOW_TOKEN else 'no'} CREATE_ALL={CREATE_ALL_ENV}")

# Headers for API requests
GLOBAL_HEADERS = {"Accept": "application/json"}
TF_HEADERS = {"Accept": "application/json"}
if TICKETFLOW_TOKEN:
    TF_HEADERS["Authorization"] = f"Bearer {TICKETFLOW_TOKEN}"

# Candidate endpoints (tries API-first to avoid frontend HTML)
ORDER_LIST_PATHS = [
    "/api/orders",
    "/api/v1/orders",
    "/orders",
]

ORDER_GET_PATHS = [
    "/api/orders/{id}",
    "/api/v1/orders/{id}",
    "/orders/{id}",
]

DIAG_GET_PATHS = [
    "/api/diagnostics/{id}",
    "/api/v1/diagnostics/{id}",
    "/diagnostics/{id}",
]

TICKET_CREATE_PATHS = [
    "/tickets",
    "/api/tickets",
    "/api/v1/tickets",
]

# -----------------------
# Utilities
# -----------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def append_audit(entry: Dict[str, Any]):
    entry.setdefault("_logged_at", now_iso())
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[{now_iso()}] WARN: failed to write audit log: {e}")

def safe_request(method: str, url: str, **kwargs) -> requests.Response:
    kwargs.setdefault("timeout", HTTP_TIMEOUT)
    try:
        return requests.request(method, url, **kwargs)
    except Exception as e:
        raise RuntimeError(f"HTTP request failed for {url}: {e}")

# -----------------------
# SQLite Idempotency store
# -----------------------
def init_db(path: str = SQLITE_DB):
    conn = sqlite3.connect(path, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS created_tickets (
            order_id TEXT PRIMARY KEY,
            ticket_id TEXT,
            created_at TEXT,
            payload TEXT
        )
    """)
    conn.commit()
    return conn

def mark_ticket_created(conn: sqlite3.Connection, order_id: str, ticket_id: str, payload: Dict[str, Any]):
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO created_tickets(order_id, ticket_id, created_at, payload) VALUES (?, ?, ?, ?)",
        (order_id, str(ticket_id), now_iso(), json.dumps(payload))
    )
    conn.commit()

def get_ticket_record(conn: sqlite3.Connection, order_id: str) -> Optional[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT order_id, ticket_id, created_at, payload FROM created_tickets WHERE order_id = ?", (order_id,))
    row = cur.fetchone()
    if not row:
        return None
    return {"order_id": row[0], "ticket_id": row[1], "created_at": row[2], "payload": json.loads(row[3])}

# -----------------------
# GlobalCart: list & fetch orders
# -----------------------
def find_working_list_endpoint(base: str) -> Optional[str]:
    headers = {"Accept": "application/json"}
    for p in ORDER_LIST_PATHS:
        url = base.rstrip("/") + p
        try:
            r = safe_request("GET", url, headers=headers)
        except Exception:
            continue
        if r.status_code == 200:
            ctype = r.headers.get("Content-Type", "")
            if "application/json" in ctype:
                return url
            # try to parse anyway
            try:
                _ = r.json()
                return url
            except Exception:
                continue
    return None

def fetch_all_orders(base: str) -> List[Dict[str, Any]]:
    url = find_working_list_endpoint(base)
    if not url:
        raise RuntimeError(f"No working orders list endpoint found at base {base}")
    r = safe_request("GET", url, headers={"Accept":"application/json"})
    r.raise_for_status()
    data = r.json()
    # Expecting list or dict with items
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # common patterns: {"orders": [...]} or {"items": [...]}
        for key in ("orders", "items", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # fallback: return list with dict if single order
        return [data]
    return []

def get_order_diagnostics(base: str, order_id: str) -> Optional[Dict[str, Any]]:
    headers = {"Accept": "application/json"}
    for p in DIAG_GET_PATHS:
        url = base.rstrip("/") + p.format(id=order_id)
        try:
            r = safe_request("GET", url, headers=headers)
        except Exception:
            continue
        if r.status_code == 200:
            try:
                return r.json()
            except Exception:
                continue
    return None

# -----------------------
# TicketFlow: create ticket (tries path variants)
# -----------------------
def find_ticket_create_endpoint(base: str) -> Optional[str]:
    for p in TICKET_CREATE_PATHS:
        url = base.rstrip("/") + p
        try:
            r = safe_request("OPTIONS", url, headers=TF_HEADERS)
        except Exception:
            # Try a POST probe with minimal payload (may return 400/422)
            try:
                r2 = safe_request("POST", url, headers={**TF_HEADERS, "Content-Type":"application/json"},
                                  json={"title":"probe","description":"probe"}, timeout=5)
                if r2.status_code in (200, 201, 400, 422):
                    return url
            except Exception:
                continue
            continue
        if r.status_code not in (404, 301, 302):
            return url
    return None

def create_ticket_at_endpoint(create_url: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        r = safe_request("POST", create_url, headers={**TF_HEADERS, "Content-Type":"application/json"}, json=payload)
    except Exception as e:
        print(f"[{now_iso()}] create_ticket error calling {create_url}: {e}")
        append_audit({"action":"tf_post_error", "url": create_url, "error": str(e)})
        return None
    if r.status_code in (200, 201):
        try:
            return r.json()
        except Exception:
            return {"status": r.status_code}
    else:
        print(f"[{now_iso()}] create_ticket -> HTTP {r.status_code} : {r.text[:300]}")
        append_audit({"action":"tf_create_failed", "status": r.status_code, "body": r.text[:1000], "payload_sample": {k: payload.get(k) for k in ("title", "priority")}})
        return None

# -----------------------
# Ticket payload builder
# -----------------------
def build_ticket_payload(order: Dict[str, Any], diagnostics: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    order_id = order.get("order_id") or order.get("id") or order.get("orderId") or order.get("order_id")
    if not order_id:
        order_id = json.dumps(order)[:32]
    short_summary = order.get("status") or order.get("payment_status") or order.get("customer_name") or ""
    title = f"[GC] Order {order_id} - {short_summary}"[:120]
    desc_parts = [
        f"Order ID: {order_id}",
        "",
        "Order snapshot:",
        json.dumps(order, indent=2),
        "",
        "Diagnostics:",
        json.dumps(diagnostics or {}, indent=2),
        "",
        f"(Auto-created by GlobalCart Automation at {now_iso()})"
    ]
    description = "\n".join(desc_parts)
    priority = "high" if ("failed" in str(order.get("payment_status","")).lower() or "shipped" in str(order.get("status","")).lower()) else "medium"
    return {"title": title, "description": description, "priority": priority, "created_by": "autobot"}

# -----------------------
# Main process: iterate orders & create tickets
# -----------------------
def create_tickets_for_all(force: bool = False, dry_run: bool = True):
    conn = init_db(SQLITE_DB)
    try:
        orders = fetch_all_orders(GLOBALCART_BASE)
    except Exception as e:
        print(f"[{now_iso()}] ERROR fetching orders list: {e}")
        append_audit({"action":"fetch_orders_failed", "error": str(e)})
        return

    if not orders:
        print(f"[{now_iso()}] No orders returned from GlobalCart.")
        return

    ticket_create_url = find_ticket_create_endpoint(TICKETFLOW_BASE) if TICKETFLOW_BASE else None
    if not ticket_create_url:
        print(f"[{now_iso()}] WARNING: could not find a TicketFlow create endpoint at base {TICKETFLOW_BASE or '<not set>'}.")
        append_audit({"action":"no_tf_endpoint", "base": TICKETFLOW_BASE})
        ticket_create_url = None

    total = len(orders)
    print(f"[{now_iso()}] Found {total} orders. Starting processing. dry_run={dry_run}, force={force}")
    for i, order in enumerate(orders, start=1):
        order_id = order.get("order_id") or order.get("id") or order.get("orderId")
        if not order_id:
            print(f"[{now_iso()}] Skipping malformed order entry at index {i}")
            append_audit({"action":"skip_malformed", "index": i, "order": order})
            continue

        existing = get_ticket_record(conn, order_id)
        if existing:
            print(f"[{now_iso()}] Already created ticket {existing['ticket_id']} for order {order_id}; skipping.")
            continue

        diagnostics = get_order_diagnostics(GLOBALCART_BASE, order_id)
        payload = build_ticket_payload(order, diagnostics)

        if dry_run:
            print(f"[{now_iso()}] DRY-RUN: would create ticket for order {order_id} -> title: {payload['title']}")
            append_audit({"action":"dry_run_payload", "order_id": order_id, "payload": payload})
            continue

        if not ticket_create_url:
            print(f"[{now_iso()}] No TicketFlow create endpoint; cannot create ticket for order {order_id}.")
            append_audit({"action":"create_skipped_no_tf_endpoint", "order_id": order_id, "payload": payload})
            continue

        if not force and not CREATE_ALL_ENV:
            print(f"[{now_iso()}] Auto-creation disabled (set CREATE_ALL=true or use --force). Skipping order {order_id}.")
            append_audit({"action":"create_skipped_not_confirmed", "order_id": order_id})
            continue

        created = create_ticket_at_endpoint(ticket_create_url, payload)
        if created:
            tid = created.get("id") or created.get("ticket_id") or created.get("ticketId") or created.get("ticket") or None
            mark_ticket_created(conn, order_id, tid or "<​unknown>", payload)
            append_audit({"action":"created", "order_id": order_id, "ticket": created})
            print(f"[{now_iso()}] Created ticket for order {order_id} (ticket_id={tid}) [{i}/{total}]")
        else:
            append_audit({"action":"create_failed", "order_id": order_id, "payload": payload})
            print(f"[{now_iso()}] Failed to create ticket for order {order_id} [{i}/{total}]")

        time.sleep(RATE_LIMIT_SECONDS)

    conn.close()
    print(f"[{now_iso()}] Processing complete. See {LOG_FILE} and {SQLITE_DB} for audit and idempotency records.")

# -----------------------
# CLI
# -----------------------
def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create tickets for all GlobalCart orders (idempotent).")
    p.add_argument("--force", action="store_true", help="Force ticket creation regardless of env; must be used to actually create when not using CREATE_ALL=true")
    p.add_argument("--dry-run", action="store_true", default=False, help="Dry run (show payloads) - overrides CREATE_ALL/force")
    p.add_argument("--limit", type=int, default=0, help="Limit number of orders to process (0 = all)")
    p.add_argument("--verbose", action="store_true", help="Verbose debug prints")
    return p.parse_args(argv)

def main(argv: List[str]):
    args = parse_args(argv)
    dry_run_effective = args.dry_run or (not (args.force or CREATE_ALL_ENV))
    if args.verbose:
        dbg_env()

    # If limit provided, run limited flow
    if args.limit:
        conn = init_db(SQLITE_DB)
        try:
            orders = fetch_all_orders(GLOBALCART_BASE)
        except Exception as e:
            print(f"[{now_iso()}] ERROR fetching orders: {e}")
            return
        to_process = orders[: args.limit]
        print(f"[{now_iso()}] Will process {len(to_process)} of {len(orders)} orders (limit={args.limit}). dry_run={dry_run_effective}, force={args.force}")
        ticket_create_url = find_ticket_create_endpoint(TICKETFLOW_BASE) if TICKETFLOW_BASE else None
        if not ticket_create_url:
            print(f"[{now_iso()}] WARNING: ticket create endpoint not found; creations will be skipped.")
            append_audit({"action":"no_tf_endpoint", "base": TICKETFLOW_BASE})
            ticket_create_url = None
        for order in to_process:
            order_id = order.get("order_id") or order.get("id") or order.get("orderId")
            if not order_id:
                continue
            existing = get_ticket_record(conn, order_id)
            if existing:
                print(f"[{now_iso()}] Already created for {order_id}; skipping")
                continue
            diagnostics = get_order_diagnostics(GLOBALCART_BASE, order_id)
            payload = build_ticket_payload(order, diagnostics)
            if dry_run_effective:
                print(f"[{now_iso()}] DRY-RUN would create ticket for {order_id}: {payload['title']}")
                append_audit({"action":"dry_run_payload", "order_id": order_id, "payload": payload})
                continue
            if not (args.force or CREATE_ALL_ENV):
                print(f"[{now_iso()}] Not creating {order_id} - use --force or set CREATE_ALL=true")
                continue
            if not ticket_create_url:
                print(f"[{now_iso()}] No TF endpoint; cannot create for {order_id}")
                continue
            created = create_ticket_at_endpoint(ticket_create_url, payload)
            if created:
                tid = created.get("id") or created.get("ticket_id") or created.get("ticketId") or created.get("ticket")
                mark_ticket_created(conn, order_id, tid or "<​unknown>", payload)
                append_audit({"action":"created", "order_id": order_id, "ticket": created})
                print(f"[{now_iso()}] Created ticket {tid} for {order_id}")
            else:
                append_audit({"action":"create_failed", "order_id": order_id, "payload": payload})
                print(f"[{now_iso()}] Create failed for {order_id}")
            time.sleep(RATE_LIMIT_SECONDS)
        conn.close()
        print(f"[{now_iso()}] Limited run complete.")
        return

    # normal full-run
    create_tickets_for_all(force=args.force, dry_run=dry_run_effective)

if __name__ == "__main__":
    main(sys.argv[1:])