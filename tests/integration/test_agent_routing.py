"""Integration tests for agent routing (Week 2/3 scaffold).

The agent orchestrator is not implemented yet; these tests are skipped until
the supervisor / L1 / L2 flow lands. They also serve as executable
documentation of the golden-ticket expectations.
"""
import json
import os

import pytest

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "..", "golden-tickets")

pytestmark = pytest.mark.skip(reason="Agent orchestrator not implemented yet (Week 2/3).")


def _load(name):
    with open(os.path.join(GOLDEN_DIR, name)) as f:
        return json.load(f)


def test_stuck_order_routes_to_l1():
    ticket = _load("gc_stuck_order.json")
    # TODO (Week 2/3): assert supervisor routes this to L1 and it calls sync.
    assert ticket["expected_route"] == "L1"


def test_mfa_reset_routes_to_l1():
    ticket = _load("mfa_reset_request.json")
    assert ticket["expected_route"] == "L1"


def test_account_locked_routes_expected():
    ticket = _load("account_locked.json")
    assert ticket["expected_route"] in ("L1", "L2")
