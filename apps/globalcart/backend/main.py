"""FastAPI application entrypoint for the GlobalCart Order Management System.

Wires together the CORS middleware, database bootstrap/seeding on startup,
and the ``orders`` and ``diagnostics`` route modules.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base, SessionLocal
from models import Order
from seed_data import seed_database
from routes import orders, diagnostics

app = FastAPI(title="GlobalCart Order Management System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Create tables and seed the database if it is empty."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Order).count() == 0:
            seed_database(db)
            print("[startup] Database seeded with demo orders.")
        else:
            print("[startup] Database already contains orders; skipping seed.")
    finally:
        db.close()


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


app.include_router(orders.router)
app.include_router(diagnostics.router)
