"""RAG ingestion (Week 2 scaffold).

Loads the markdown documents under ``knowledge-base/`` (policies + runbooks),
chunks them, embeds them, and writes them to a vector store used by the
retriever. Implementation lands in Week 2.
"""
from __future__ import annotations

import os

KNOWLEDGE_BASE_DIR = os.getenv(
    "KNOWLEDGE_BASE_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "knowledge-base"),
)


def ingest(knowledge_base_dir: str = KNOWLEDGE_BASE_DIR) -> int:
    """Chunk + embed all KB docs into the vector store. Returns chunk count.

    TODO (Week 2): read markdown, split into chunks, embed, and upsert.
    """
    raise NotImplementedError("rag.ingest.ingest is a Week 2 scaffold.")


if __name__ == "__main__":
    print("RAG ingest scaffold — implementation coming in Week 2.")
