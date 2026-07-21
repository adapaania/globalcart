"""Identity / Employee Self-Service tools for the agent (Week 2/3 scaffold).

Wrappers around the ESS identity API for MFA resets, password resets, and
account-lockout handling. Implementation lands in Week 2/3.
"""
from __future__ import annotations

import os
from typing import Any, Dict

IDENTITY_BASE_URL = os.getenv("IDENTITY_BASE_URL", "http://localhost:8002")


def get_employee(employee_id: str) -> Dict[str, Any]:
    """GET /api/employees/{employee_id}."""
    raise NotImplementedError("identity_tools.get_employee is a Week 2/3 scaffold.")


def reset_mfa(employee_id: str) -> Dict[str, Any]:
    """POST /api/employees/{employee_id}/mfa/reset."""
    raise NotImplementedError("identity_tools.reset_mfa is a Week 2/3 scaffold.")


def reset_password(employee_id: str) -> Dict[str, Any]:
    """POST /api/employees/{employee_id}/password/reset."""
    raise NotImplementedError("identity_tools.reset_password is a Week 2/3 scaffold.")


def unlock_account(employee_id: str) -> Dict[str, Any]:
    """POST /api/employees/{employee_id}/unlock."""
    raise NotImplementedError("identity_tools.unlock_account is a Week 2/3 scaffold.")
