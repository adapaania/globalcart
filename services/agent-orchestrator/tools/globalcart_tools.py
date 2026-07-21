"""GlobalCart tools for the agent (Week 2/3 scaffold).

Thin client wrappers around the GlobalCart backend API so agents can look up
orders, read diagnostics, and trigger a manual sync. Implementation (real HTTP
calls + typed results) lands in Week 2/3.
"""
from __future__ import annotations

import os
from typing import Any, Dict

GLOBALCART_BASE_URL = os.getenv("GLOBALCART_BASE_URL", "http://localhost:8000")


def get_order(order_id: str) -> Dict[str, Any]:
    """GET /api/orders/{order_id} — customer-facing order details + events."""
    raise NotImplementedError("globalcart_tools.get_order is a Week 2/3 scaffold.")


def get_diagnostics(order_id: str) -> Dict[str, Any]:
    """GET /api/diagnostics/{order_id} — internal logs, error codes, action."""
    raise NotImplementedError("globalcart_tools.get_diagnostics is a Week 2/3 scaffold.")


def sync_order(order_id: str) -> Dict[str, Any]:
    """POST /api/orders/{order_id}/sync — re-dispatch a stuck order."""
    raise NotImplementedError("globalcart_tools.sync_order is a Week 2/3 scaffold.")
