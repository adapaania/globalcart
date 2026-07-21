"""Supervisor agent (Week 2/3 scaffold).

The supervisor is the top-level router. It classifies an incoming ticket and
delegates to the appropriate tier (L1 for routine/automatable requests, L2 for
complex or escalated ones). Implementation lands in Week 2/3.
"""
from __future__ import annotations

from typing import Any, Dict


class SupervisorAgent:
    """Routes tickets to the correct downstream agent."""

    def __init__(self, l1_agent: Any = None, l2_agent: Any = None) -> None:
        self.l1_agent = l1_agent
        self.l2_agent = l2_agent

    def route(self, ticket: Dict[str, Any]) -> str:
        """Return the name of the agent that should handle the ticket.

        TODO (Week 2/3): replace heuristic with an LLM-based classifier that
        reads the ticket text, retrieves relevant runbooks/policies via RAG,
        and decides the tier.
        """
        raise NotImplementedError("SupervisorAgent.route is a Week 2/3 scaffold.")


if __name__ == "__main__":
    print("SupervisorAgent scaffold — implementation coming in Week 2/3.")
