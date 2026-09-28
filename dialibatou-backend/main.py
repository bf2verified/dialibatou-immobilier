"""
DIALIBATOU BTP IMMOBILIER — API FastAPI + PostgreSQL
Lancement : uvicorn main:app --reload --port 8001
Swagger  : http://localhost:8001/docs
"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import Base, engine
import models  # noqa: F401  (enregistre les tables sur Base)
from routers import auth, lots, messages, properties, uploads

BASE_DIR = Path(__file__).resolve().parent

# Creation des tables au demarrage (idempotent)
Base.metadata.create_all(engine)

app = FastAPI(
    title="DIALIBATOU BTP IMMOBILIER API",
    description="API du site immobilier — proprietes, lots, messages, upload, auth JWT.",
    version="1.0.0",
)

# --- CORS : frontends autorises (localhost:5500/8000 + URLs de production) ---
default_origins = (
    "http://localhost:5500,http://127.0.0.1:5500,"
    "http://localhost:8000,http://127.0.0.1:8000"
)
allow_origins = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", default_origins).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# --- Routes ---
app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(lots.router)
app.include_router(messages.router)
app.include_router(uploads.router)


@app.get("/api/health")
def health():
    """Sante de l'API (attendu par backend_test.py)."""
    return {"status": "ok", "service": "DIALIBATOU BTP API"}


# --- Fichiers uploades : servis en statique (/uploads/images/..., /uploads/videos/...) ---
app.mount("/uploads", StaticFiles(directory=str(BASE_DIR / "uploads")), name="uploads")
