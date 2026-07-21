"""TicketFlow tools for the agent (Week 2/3 scaffold).

Wrappers around the TicketFlow API for creating, reading, updating, and
commenting on tickets. Implementation lands in Week 2/3.
"""
from __future__ import annotations

import os
from typing import Any, Dict

TICKETFLOW_BASE_URL = os.getenv("TICKETFLOW_BASE_URL", "http://localhost:8001")


def create_ticket(payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /api/tickets."""
    raise NotImplementedError("ticketflow_tools.create_ticket is a Week 2/3 scaffold.")


def get_ticket(ticket_id: str) -> Dict[str, Any]:
    """GET /api/tickets/{ticket_id}."""
    raise NotImplementedError("ticketflow_tools.get_ticket is a Week 2/3 scaffold.")


def update_ticket(ticket_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    """PATCH /api/tickets/{ticket_id} — update status / assignee."""
    raise NotImplementedError("ticketflow_tools.update_ticket is a Week 2/3 scaffold.")


def add_comment(ticket_id: str, body: str) -> Dict[str, Any]:
    """POST /api/tickets/{ticket_id}/comments."""
    raise NotImplementedError("ticketflow_tools.add_comment is a Week 2/3 scaffold.")
