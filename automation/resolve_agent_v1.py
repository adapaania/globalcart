#!/usr/bin/env python3
"""
Agentic GlobalCart Resolver — auto-discovers open tickets (or accepts specific
ticket IDs), diagnoses the underlying order, and attempts to FIX the issue in
GlobalCart, then closes the loop on the ticket via TicketFlow's real endpoints.

TicketFlow endpoints used:
- GET  /tickets                    -> list all tickets
- GET  /tickets/{ticket_id}        -> get single ticket + comments
- POST /tickets/{ticket_id}/update -> update status/priority/assignee
- POST /tickets/{ticket_id}/comment-> add a comment
- POST /tickets/{ticket_id}/close  -> close with resolution
"""
from __future__ import annotations
import os, sys, json, time, sqlite3, requests, argparse
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from langchain.tools import tool
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# -----------------------
# .env loader
# -----------------------
try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
    _p = find_dotenv(usecwd=True)
    if _p:
        load_dotenv(_p, override=False)
except Exception:
    if os.path.exists(".env"):
        for ln in open(".env", "r", encoding="utf-8"):
            ln = ln.strip()
            if not ln or ln.startswith("#") or "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            k = k.strip(); v = v.strip().strip("'\"")
            if os.getenv(k) is None:
                os.environ[k] = v

# -----------------------
# Config
# -----------------------
ROUTELLM_API_KEY = os.getenv("ROUTELLM_API_KEY", "")
ROUTELLM_BASE = os.getenv("ROUTELLM_BASE", "https://routellm.abacus.ai/v1").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

GLOBALCART_BASE = os.getenv("GLOBALCART_BASE", "https://globalcart-production.up.railway.app").rstrip("/")
TICKETFLOW_BASE = os.getenv("TICKETFLOW_BASE_URL", "").rstrip("/")
TICKETFLOW_TOKEN = os.getenv("TICKETFLOW_API_TOKEN", "")

SQLITE_DB = os.getenv("RESOLVER_DB", "resolved_tickets.db")
LOG_FILE = os.getenv("LOG_FILE", "ticket_audit.log")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "20"))
RATE_LIMIT_SECONDS = float(os.getenv("RATE_LIMIT_SECONDS", "0.8"))

if not TICKETFLOW_BASE or not TICKETFLOW_TOKEN:
    print("ERROR: TICKETFLOW_BASE_URL and TICKETFLOW_API_TOKEN must be set. Exiting.")
    sys.exit(2)

TF_HEADERS = {"Accept": "application/json", "Authorization": f"Bearer {TICKETFLOW_TOKEN}"}

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
    except Exception:
        pass

def init_db(path: str = SQLITE_DB):
    conn = sqlite3.connect(path, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resolved_tickets (
            ticket_id TEXT PRIMARY KEY,
            order_id TEXT,
            action TEXT,
            resolved_at TEXT,
            result TEXT
        )
    """)
    conn.commit()
    return conn

def already_resolved(conn: sqlite3.Connection, ticket_id: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM resolved_tickets WHERE ticket_id = ?", (ticket_id,))
    return cur.fetchone() is not None

def mark_resolved(conn, ticket_id, order_id, action, result):
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO resolved_tickets(ticket_id,order_id,action,resolved_at,result) VALUES (?,?,?,?,?)",
        (ticket_id, order_id, action, now_iso(), json.dumps(result))
    )
    conn.commit()

def call_tool_compat(tool_obj, arg: str) -> str:
    last_exc = None
    for attr in ("run", "__wrapped__", "func"):
        try:
            if hasattr(tool_obj, attr):
                return getattr(tool_obj, attr)(arg)
        except Exception as e:
            last_exc = e
    try:
        return tool_obj(arg)
    except Exception as e:
        last_exc = e
    raise RuntimeError(f"Failed to invoke tool. Last error: {last_exc}") from last_exc

# -----------------------
# Ticket tools (exact TicketFlow endpoints)
# -----------------------
@tool
def list_tickets_tool(_: str = "") -> str:
    """
    Returns JSON list (string) of tickets from TicketFlow (GET /tickets),
    filtered to open/unresolved ones where a status field is present.
    Call without args.
    """
    url = f"{TICKETFLOW_BASE}/tickets"
    try:
        r = requests.get(url, headers=TF_HEADERS, timeout=HTTP_TIMEOUT)
        if r.status_code != 200:
            append_audit({"action":"list_tickets_failed","status":r.status_code,"body":r.text[:500]})
            return f"ERROR: status {r.status_code}: {r.text[:500]}"
        data = r.json()
        if isinstance(data, dict):
            items = None
            for key in ("tickets", "items", "data", "results"):
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    break
            items = items if items is not None else [data]
        elif isinstance(data, list):
            items = data
        else:
            items = []

        open_statuses = {"open", "new", "pending", "in_progress", "assigned"}
        closed_statuses = {"closed", "resolved", "done", "cancelled"}
        filtered = [
            t for t in items
            if str(t.get("status", "")).strip().lower() not in closed_statuses
        ]
        result = filtered if filtered else items
        return json.dumps(result)
    except Exception as e:
        append_audit({"action":"list_tickets_error","error":str(e)})
        return f"ERROR: {e}"

@tool
def get_ticket_tool(ticket_id: str) -> str:
    """
    Fetch a ticket's details + comments from TicketFlow (GET /tickets/{ticket_id}).
    Returns JSON string or error.
    """
    if not ticket_id:
        return "ERROR: ticket_id required"
    url = f"{TICKETFLOW_BASE}/tickets/{ticket_id}"
    try:
        r = requests.get(url, headers=TF_HEADERS, timeout=HTTP_TIMEOUT)
        if r.status_code == 200:
            return r.text
        return f"ERROR: status {r.status_code}: {r.text[:500]}"
    except Exception as e:
        return f"ERROR: {e}"

@tool
def update_ticket_tool(ticket_id_and_payload: str) -> str:
    """
    Updates status/priority/assignee via POST /tickets/{ticket_id}/update.
    Input format: "TICKET_ID|{JSON_PAYLOAD}"
    Example: 'TCK-101|{"status": "resolved", "priority": "low"}'
    """
    if not ticket_id_and_payload or "|" not in ticket_id_and_payload:
        return "ERROR: expected 'TICKET_ID|{json_payload}'"
    ticket_id, payload_str = ticket_id_and_payload.split("|", 1)
    ticket_id = ticket_id.strip()
    try:
        payload = json.loads(payload_str.strip())
    except Exception as e:
        return f"ERROR: invalid JSON payload: {e}"

    url = f"{TICKETFLOW_BASE}/tickets/{ticket_id}/update"
    try:
        r = requests.post(url, headers={**TF_HEADERS, "Content-Type":"application/json"}, json=payload, timeout=HTTP_TIMEOUT)
        if r.status_code in (200, 201, 204):
            append_audit({"action":"ticket_updated","ticket_id":ticket_id,"payload":payload})
            return f"OK: ticket {ticket_id} updated -> {json.dumps(payload)}"
        append_audit({"action":"ticket_update_failed","ticket_id":ticket_id,"status":r.status_code,"body":r.text[:500]})
        return f"ERROR: update failed status {r.status_code}: {r.text[:500]}"
    except Exception as e:
        append_audit({"action":"ticket_update_error","ticket_id":ticket_id,"error":str(e)})
        return f"ERROR: {e}"

@tool
def add_ticket_comment_tool(ticket_id_and_comment: str) -> str:
    """
    Adds a comment to a ticket via POST /tickets/{ticket_id}/comment.
    Input format: "TICKET_ID|COMMENT_TEXT"
    """
    if not ticket_id_and_comment or "|" not in ticket_id_and_comment:
        return "ERROR: expected 'TICKET_ID|COMMENT_TEXT'"
    ticket_id, comment = ticket_id_and_comment.split("|", 1)
    ticket_id = ticket_id.strip(); comment = comment.strip()
    url = f"{TICKETFLOW_BASE}/tickets/{ticket_id}/comment"
    try:
        r = requests.post(url, headers={**TF_HEADERS, "Content-Type":"application/json"},
                           json={"comment": comment}, timeout=HTTP_TIMEOUT)
        if r.status_code in (200, 201, 204):
            append_audit({"action":"comment_added","ticket_id":ticket_id,"comment":comment})
            return f"OK: comment added to ticket {ticket_id}"
        return f"ERROR: comment failed status {r.status_code}: {r.text[:500]}"
    except Exception as e:
        return f"ERROR: {e}"

@tool
def close_ticket_tool(ticket_id_and_resolution: str) -> str:
    """
    Closes a ticket with a resolution via POST /tickets/{ticket_id}/close.
    Input format: "TICKET_ID|RESOLUTION_TEXT"
    """
    if not ticket_id_and_resolution or "|" not in ticket_id_and_resolution:
        return "ERROR: expected 'TICKET_ID|RESOLUTION_TEXT'"
    ticket_id, resolution = ticket_id_and_resolution.split("|", 1)
    ticket_id = ticket_id.strip(); resolution = resolution.strip()
    url = f"{TICKETFLOW_BASE}/tickets/{ticket_id}/close"
    try:
        r = requests.post(url, headers={**TF_HEADERS, "Content-Type":"application/json"},
                           json={"resolution": resolution}, timeout=HTTP_TIMEOUT)
        if r.status_code in (200, 201, 204):
            append_audit({"action":"ticket_closed","ticket_id":ticket_id,"resolution":resolution})
            return f"OK: ticket {ticket_id} closed. Resolution: {resolution}"
        append_audit({"action":"ticket_close_failed","ticket_id":ticket_id,"status":r.status_code,"body":r.text[:500]})
        return f"ERROR: close failed status {r.status_code}: {r.text[:500]}"
    except Exception as e:
        append_audit({"action":"ticket_close_error","ticket_id":ticket_id,"error":str(e)})
        return f"ERROR: {e}"

# -----------------------
# Order read tools
# -----------------------
@tool
def get_order_tool(order_id: str) -> str:
    """Returns full order JSON for given order_id or an error string."""
    if not order_id:
        return "ERROR: order_id required"
    try:
        r = requests.get(f"{GLOBALCART_BASE}/api/orders/{order_id}", headers={"Accept":"application/json"}, timeout=HTTP_TIMEOUT)
        if r.status_code == 200:
            return json.dumps(r.json())
        return f"ERROR: status {r.status_code}: {r.text[:1000]}"
    except Exception as e:
        return f"ERROR: {e}"

@tool
def get_diagnostics_tool(order_id: str) -> str:
    """Returns diagnostics JSON for order_id."""
    if not order_id:
        return "ERROR: order_id required"
    try:
        r = requests.get(f"{GLOBALCART_BASE}/api/diagnostics/{order_id}", headers={"Accept":"application/json"}, timeout=HTTP_TIMEOUT)
        if r.status_code == 200:
            return json.dumps(r.json())
        return f"ERROR: status {r.status_code}: {r.text[:1000]}"
    except Exception as e:
        return f"ERROR: {e}"

# -----------------------
# Order FIX tools
# -----------------------
@tool
def sync_order_tool(order_id: str) -> str:
    """
    Calls POST /api/orders/{id}/sync to fix stuck/inconsistent orders.
    Returns JSON response or error.
    """
    if not order_id:
        return "ERROR: order_id required"
    url = f"{GLOBALCART_BASE}/api/orders/{order_id}/sync"
    try:
        r = requests.post(url, headers={"Accept":"application/json"}, timeout=HTTP_TIMEOUT)
        if r.status_code in (200, 201, 202):
            try:
                resp = r.json()
            except Exception:
                resp = {"status": r.status_code}
            append_audit({"action":"order_synced","order_id":order_id,"response":resp})
            return json.dumps(resp)
        append_audit({"action":"order_sync_failed","order_id":order_id,"status":r.status_code,"body":r.text[:1000]})
        return f"ERROR: sync failed status {r.status_code}: {r.text[:500]}"
    except Exception as e:
        append_audit({"action":"order_sync_error","order_id":order_id,"error":str(e)})
        return f"ERROR: {e}"

@tool
def patch_order_tool(order_id_and_patch: str) -> str:
    """
    Applies a targeted field fix via PATCH /api/orders/{id}.
    Input format: "ORDER_ID|{JSON_PATCH_BODY}"
    Example: 'GC-2020|{"status": "PROCESSING"}'
    """
    if not order_id_and_patch or "|" not in order_id_and_patch:
        return "ERROR: expected 'ORDER_ID|{json_patch}'"
    order_id, patch_str = order_id_and_patch.split("|", 1)
    order_id = order_id.strip()
    try:
        patch_body = json.loads(patch_str.strip())
    except Exception as e:
        return f"ERROR: invalid JSON patch body: {e}"

    url = f"{GLOBALCART_BASE}/api/orders/{order_id}"
    try:
        r = requests.patch(url, headers={"Accept":"application/json","Content-Type":"application/json"}, json=patch_body, timeout=HTTP_TIMEOUT)
        if r.status_code in (200, 201, 204):
            try:
                resp = r.json()
            except Exception:
                resp = {"status": r.status_code}
            append_audit({"action":"order_patched","order_id":order_id,"patch":patch_body,"response":resp})
            return json.dumps(resp)
        append_audit({"action":"order_patch_failed","order_id":order_id,"patch":patch_body,"status":r.status_code,"body":r.text[:1000]})
        return f"ERROR: patch failed status {r.status_code}: {r.text[:500]}"
    except Exception as e:
        append_audit({"action":"order_patch_error","order_id":order_id,"error":str(e)})
        return f"ERROR: {e}"

@tool
def mark_ticket_resolved_locally(ticket_id_order_id_action: str) -> str:
    """
    Records a resolution in the local idempotency DB so the same ticket isn't
    re-processed. Input format: "TICKET_ID|ORDER_ID|ACTION"
    """
    try:
        ticket_id, order_id, action = ticket_id_order_id_action.split("|", 2)
    except Exception:
        return "ERROR: expected 'TICKET_ID|ORDER_ID|ACTION'"
    conn = init_db()
    mark_resolved(conn, ticket_id.strip(), order_id.strip(), action.strip(), {"marked_by":"agent"})
    conn.close()
    return f"OK: recorded resolution for ticket {ticket_id}"

# -----------------------
# LLM & Agent
# -----------------------
llm = ChatOpenAI(api_key=ROUTELLM_API_KEY, base_url=ROUTELLM_BASE, model=LLM_MODEL, temperature=0)

system_prompt = """
You are GlobalCart Resolver Agent (L2/L3). Given a ticket_id, your job is to actually FIX the
underlying order issue in GlobalCart, then close the loop on the ticket.

Workflow:
1. Call get_ticket_tool(ticket_id) to read the ticket (title/description contain the order_id).
2. Extract the order_id from the ticket description.
3. Call get_order_tool(order_id) and get_diagnostics_tool(order_id) to understand the current state.
4. Decide the fix:
   - If diagnostics show a stuck/inconsistent order (e.g. inventory check failed, stuck PENDING/HELD),
     call sync_order_tool(order_id).
   - If a specific field is wrong and sync won't fix it, call
     patch_order_tool("ORDER_ID|{\\"field\\": \\"value\\"}") with a minimal, targeted patch.
   - Do NOT invent destructive changes (no deleting orders, no changing customer_email/payment amounts).
     If the fix is not safe to automate, say so and recommend human review instead of guessing.
5. After a successful fix, re-fetch the order to confirm the state changed as expected.
6. Call add_ticket_comment_tool("TICKET_ID|<summary of diagnosis and fix applied>").
7. Call close_ticket_tool("TICKET_ID|<one-line resolution summary>") to close the ticket.
   (Use update_ticket_tool instead if you only need to change status/priority without closing.)
8. Call mark_ticket_resolved_locally("TICKET_ID|ORDER_ID|ACTION_TAKEN") to record it.
9. Summarize what was wrong, what you did, and the verification result.

Always be explicit about which tool you called and why. If a step fails, stop and explain,
do not guess or fabricate order data.
"""

agent = create_agent(
    model=llm,
    tools=[
        list_tickets_tool, get_ticket_tool, get_order_tool, get_diagnostics_tool,
        sync_order_tool, patch_order_tool,
        update_ticket_tool, add_ticket_comment_tool, close_ticket_tool,
        mark_ticket_resolved_locally,
    ],
    system_prompt=system_prompt,
)

# -----------------------
# Runner
# -----------------------
def invoke_agent_user_prompt(user_text: str) -> None:
    response = agent.invoke({"messages":[{"role":"user","content": user_text}]})
    print("\n" + "="*70)
    print("USER:"); print(user_text)
    print("\n" + "="*70)
    print("AGENT OUTPUT / MESSAGES:")
    for msg in response["messages"]:
        print("\n---"); print(type(msg).__name__)
        if hasattr(msg, "content"):
            print(msg.content)
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print("\nTool calls:"); print(msg.tool_calls)
    print("="*70 + "\n")

def parse_args(argv: List[str]):
    p = argparse.ArgumentParser(prog="ResolveAgent", description="Agentic GlobalCart Resolver (fixes orders from tickets)")
    p.add_argument("--tickets", "-t", required=False, default=None,
                   help="Comma-separated ticket IDs to resolve. If omitted, all open tickets are fetched automatically.")
    return p.parse_args(argv)

def main(argv: List[str]):
    args = parse_args(argv)

    if args.tickets:
        ticket_ids = [s.strip() for s in args.tickets.split(",") if s.strip()]
    else:
        print("No --tickets provided. Auto-fetching open tickets from TicketFlow...")
        raw = call_tool_compat(list_tickets_tool, "")
        if raw.startswith("ERROR"):
            print(raw)
            return
        arr = json.loads(raw)
        ticket_ids = [
            str(t.get("id") or t.get("ticket_id") or t.get("ticketId"))
            for t in arr
            if (t.get("id") or t.get("ticket_id") or t.get("ticketId"))
        ]

    if not ticket_ids:
        print("No open tickets found to resolve.")
        return

    print(f"Tickets to resolve: {ticket_ids}")
    for tid in ticket_ids:
        conn = init_db()
        if already_resolved(conn, tid):
            conn.close()
            print(f"[SKIP] Ticket {tid} already resolved locally.")
            continue
        conn.close()
        prompt = f"Resolve ticket {tid}: fetch it, find the order, diagnose, apply a safe fix, verify, and close the ticket."
        invoke_agent_user_prompt(prompt)
        time.sleep(RATE_LIMIT_SECONDS)

if __name__ == "__main__":
    main(sys.argv[1:])