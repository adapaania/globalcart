"""L1 (Tier-1) agent (Week 2/3 scaffold).

Handles routine, well-documented, automatable requests — e.g. password resets,
MFA resets, account-lockout checks, and known GlobalCart order issues — using
the available tools and RAG-retrieved runbooks. Escalates to L2 when unsure.
"""
from __future__ import annotations

from typing import Any, Dict


class L1Agent:
    """First-line automated support agent."""

    def __init__(self, tools: Any = None, retriever: Any = None) -> None:
        self.tools = tools
        self.retriever = retriever

    def handle(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to resolve the ticket; return a result/escalation decision.

        TODO (Week 2/3): implement the reason-act loop with tool calls and RAG.
        """
        raise NotImplementedError("L1Agent.handle is a Week 2/3 scaffold.")


if __name__ == "__main__":
    print("L1Agent scaffold — implementation coming in Week 2/3.")
