"""
Connexion PostgreSQL pour DIALIBATOU BTP IMMOBILIER.
SQLAlchemy 2.x + psycopg 3 (PostgreSQL local, pgAdmin : dialibatou_db)
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent

# Charge dialibatou-backend/.env (DATABASE_URL, JWT_SECRET, ...)
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/dialibatou_db",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base de declarative commune a tous les modeles SQLAlchemy."""


def get_db():
    """Dependance FastAPI : fournit une Session SQLAlchemy par requete."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
