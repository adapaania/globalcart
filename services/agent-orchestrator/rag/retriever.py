"""RAG retriever (Week 2 scaffold).

Given a query (e.g. ticket text), returns the most relevant knowledge-base
chunks (policies / runbooks) to ground the agent's decision. Implementation
lands in Week 2.
"""
from __future__ import annotations

from typing import Any, Dict, List


class Retriever:
    """Semantic retriever over the ingested knowledge base."""

    def __init__(self, top_k: int = 4) -> None:
        self.top_k = top_k

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Return the top-k relevant chunks for the query.

        TODO (Week 2): embed the query and search the vector store.
        """
        raise NotImplementedError("Retriever.search is a Week 2 scaffold.")


if __name__ == "__main__":
    print("RAG retriever scaffold — implementation coming in Week 2.")
