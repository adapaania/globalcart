"""
TicketFlow — IT Service Management (ITSM) REST API
==================================================

A lean, budget-first ticketing system built with FastAPI + SQLAlchemy Core +
SQLite. No paid services, no external auth provider, no Docker required.

Auth:   All endpoints except GET /health require an
        `Authorization: Bearer <token>` header. The token is validated against
        the TICKETFLOW_API_TOKEN environment variable.

Run:    uvicorn main:app --reload
"""
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    func,
    insert,
    or_,
    select,
    update,
)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ticketflow.db")
API_TOKEN = os.getenv("TICKETFLOW_API_TOKEN", "changeme-local-dev-token")

VALID_STATUSES = {"open", "in_progress", "resolved", "closed"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}


def _utcnow() -> datetime:
    """Timezone-aware UTC timestamp (stored naive for SQLite portability)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# --------------------------------------------------------------------------- #
# Database (SQLAlchemy Core — no ORM, no Alembic)
# --------------------------------------------------------------------------- #
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
metadata = MetaData()

tickets = Table(
    "tickets",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", String(255), nullable=False),
    Column("description", Text, nullable=False, default=""),
    Column("status", String(20), nullable=False, default="open"),
    Column("priority", String(20), nullable=False, default="medium"),
    Column("created_by", String(120), nullable=False, default=""),
    Column("assigned_to", String(120), nullable=True),
    Column("resolution", Text, nullable=True),
    Column("created_at", DateTime, nullable=False, default=_utcnow),
    Column("updated_at", DateTime, nullable=False, default=_utcnow),
)

comments = Table(
    "comments",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ticket_id", Integer, ForeignKey("tickets.id"), nullable=False, index=True),
    Column("author", String(120), nullable=False, default=""),
    Column("body", Text, nullable=False),
    Column("created_at", DateTime, nullable=False, default=_utcnow),
)


# --------------------------------------------------------------------------- #
# Pydantic v2 schemas
# --------------------------------------------------------------------------- #
class TicketCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=10_000)
    priority: str = Field(default="medium")
    created_by: str = Field(default="", max_length=120)
    assigned_to: Optional[str] = Field(default=None, max_length=120)


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None


class CommentCreate(BaseModel):
    author: str = Field(default="", max_length=120)
    body: str = Field(..., min_length=1, max_length=10_000)


class TicketClose(BaseModel):
    resolution: str = Field(..., min_length=1, max_length=10_000)


# --------------------------------------------------------------------------- #
# App + auth dependency
# --------------------------------------------------------------------------- #
app = FastAPI(
    title="TicketFlow ITSM API",
    version="1.0.0",
    description="A lean IT Service Management ticketing API (FastAPI + SQLite).",
)

_bearer = HTTPBearer(auto_error=False)


def require_token(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> None:
    """Validate the static Bearer token against TICKETFLOW_API_TOKEN."""
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Use 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if creds.credentials != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.on_event("startup")
def on_startup() -> None:
    """Auto-create the SQLite database and tables on startup."""
    metadata.create_all(engine)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _row_to_dict(row) -> dict:
    return dict(row._mapping)


def _get_ticket_or_404(conn, ticket_id: int) -> dict:
    row = conn.execute(select(tickets).where(tickets.c.id == ticket_id)).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found.",
        )
    return _row_to_dict(row)


def _serialize_ticket(conn, ticket: dict, include_comments: bool = False) -> dict:
    out = dict(ticket)
    if include_comments:
        rows = conn.execute(
            select(comments)
            .where(comments.c.ticket_id == ticket["id"])
            .order_by(comments.c.created_at.asc())
        ).all()
        out["comments"] = [_row_to_dict(r) for r in rows]
    return out


# --------------------------------------------------------------------------- #
# Read endpoints
# --------------------------------------------------------------------------- #
@app.get("/health", tags=["system"])
def health() -> dict:
    """Health check — no auth required."""
    return {"status": "ok", "service": "ticketflow", "time": _utcnow().isoformat()}


@app.get("/tickets", tags=["tickets"], dependencies=[Depends(require_token)])
def list_tickets(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    priority: Optional[str] = Query(default=None),
) -> dict:
    """List all tickets. Optional ?status= and ?priority= filters."""
    if status_filter is not None and status_filter not in VALID_STATUSES:
        raise HTTPException(400, f"Invalid status. Allowed: {sorted(VALID_STATUSES)}")
    if priority is not None and priority not in VALID_PRIORITIES:
        raise HTTPException(400, f"Invalid priority. Allowed: {sorted(VALID_PRIORITIES)}")

    stmt = select(tickets)
    if status_filter is not None:
        stmt = stmt.where(tickets.c.status == status_filter)
    if priority is not None:
        stmt = stmt.where(tickets.c.priority == priority)
    stmt = stmt.order_by(tickets.c.created_at.desc())

    with engine.begin() as conn:
        rows = conn.execute(stmt).all()
        return {"count": len(rows), "tickets": [_row_to_dict(r) for r in rows]}


@app.get("/tickets/search", tags=["tickets"], dependencies=[Depends(require_token)])
def search_tickets(q: str = Query(..., min_length=1)) -> dict:
    """Full-text (LIKE) search over ticket title and description."""
    pattern = f"%{q}%"
    stmt = (
        select(tickets)
        .where(or_(tickets.c.title.ilike(pattern), tickets.c.description.ilike(pattern)))
        .order_by(tickets.c.created_at.desc())
    )
    with engine.begin() as conn:
        rows = conn.execute(stmt).all()
        return {"query": q, "count": len(rows), "tickets": [_row_to_dict(r) for r in rows]}


@app.get("/tickets/{ticket_id}", tags=["tickets"], dependencies=[Depends(require_token)])
def get_ticket(ticket_id: int) -> dict:
    """Get a single ticket by ID (includes its comments)."""
    with engine.begin() as conn:
        ticket = _get_ticket_or_404(conn, ticket_id)
        return _serialize_ticket(conn, ticket, include_comments=True)


# --------------------------------------------------------------------------- #
# Write endpoints
# --------------------------------------------------------------------------- #
@app.post(
    "/tickets",
    tags=["tickets"],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_token)],
)
def create_ticket(payload: TicketCreate) -> dict:
    """Create a new ticket."""
    if payload.priority not in VALID_PRIORITIES:
        raise HTTPException(400, f"Invalid priority. Allowed: {sorted(VALID_PRIORITIES)}")

    now = _utcnow()
    values = {
        "title": payload.title,
        "description": payload.description,
        "status": "open",
        "priority": payload.priority,
        "created_by": payload.created_by,
        "assigned_to": payload.assigned_to,
        "resolution": None,
        "created_at": now,
        "updated_at": now,
    }
    with engine.begin() as conn:
        result = conn.execute(insert(tickets).values(**values))
        new_id = result.inserted_primary_key[0]
        ticket = _get_ticket_or_404(conn, new_id)
        return _serialize_ticket(conn, ticket, include_comments=True)


@app.post(
    "/tickets/{ticket_id}/update",
    tags=["tickets"],
    dependencies=[Depends(require_token)],
)
def update_ticket(ticket_id: int, payload: TicketUpdate) -> dict:
    """Update a ticket's status, priority, and/or assigned_to."""
    if payload.status is not None and payload.status not in VALID_STATUSES:
        raise HTTPException(400, f"Invalid status. Allowed: {sorted(VALID_STATUSES)}")
    if payload.priority is not None and payload.priority not in VALID_PRIORITIES:
        raise HTTPException(400, f"Invalid priority. Allowed: {sorted(VALID_PRIORITIES)}")

    changes = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not changes:
        raise HTTPException(400, "No updatable fields provided.")

    with engine.begin() as conn:
        _get_ticket_or_404(conn, ticket_id)
        changes["updated_at"] = _utcnow()
        conn.execute(update(tickets).where(tickets.c.id == ticket_id).values(**changes))
        ticket = _get_ticket_or_404(conn, ticket_id)
        return _serialize_ticket(conn, ticket, include_comments=True)


@app.post(
    "/tickets/{ticket_id}/comment",
    tags=["tickets"],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_token)],
)
def add_comment(ticket_id: int, payload: CommentCreate) -> dict:
    """Add a comment to a ticket (stored in the comments table)."""
    now = _utcnow()
    with engine.begin() as conn:
        _get_ticket_or_404(conn, ticket_id)
        conn.execute(
            insert(comments).values(
                ticket_id=ticket_id,
                author=payload.author,
                body=payload.body,
                created_at=now,
            )
        )
        # bump the ticket's updated_at so activity is reflected
        conn.execute(
            update(tickets).where(tickets.c.id == ticket_id).values(updated_at=now)
        )
        ticket = _get_ticket_or_404(conn, ticket_id)
        return _serialize_ticket(conn, ticket, include_comments=True)


@app.post(
    "/tickets/{ticket_id}/close",
    tags=["tickets"],
    dependencies=[Depends(require_token)],
)
def close_ticket(ticket_id: int, payload: TicketClose) -> dict:
    """Close a ticket with a resolution note."""
    now = _utcnow()
    with engine.begin() as conn:
        _get_ticket_or_404(conn, ticket_id)
        conn.execute(
            update(tickets)
            .where(tickets.c.id == ticket_id)
            .values(status="closed", resolution=payload.resolution, updated_at=now)
        )
        ticket = _get_ticket_or_404(conn, ticket_id)
        return _serialize_ticket(conn, ticket, include_comments=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001")),
        reload=bool(os.getenv("RELOAD", "")),
    )
