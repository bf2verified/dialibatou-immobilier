#!/usr/bin/env python3
"""
Seed de dialibatou_db :
  - 60 proprietes (extraites du site)
  - 8 lotissements cooperative
  - 1 admin (mot de passe hashé bcrypt, jamais en clair)

Usage (depuis dialibatou-backend/) :
  python seed.py           # insere seulement si les tables sont vides
  python seed.py --force   # reinitialise proprietes + lots (messages conserves)
"""
import json
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
import models  # noqa: F401
from routers.auth import ensure_default_admin

BASE_DIR = Path(__file__).resolve().parent
SEED_FILE = BASE_DIR / "seed_data.json"

PROPERTY_COLUMNS = {
    "ti", "de", "ty", "tr", "pr", "nb", "su", "ro", "be", "ba",
    "fe", "im", "vd", "ft", "vi", "ag",
}
LOT_COLUMNS = {"loc", "zone", "lots", "dispo", "su", "pr", "st", "fe"}


def load_seed() -> dict:
    if not SEED_FILE.exists():
        sys.exit(f"Fichier introuvable : {SEED_FILE}")
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    assert len(data["properties"]) == 60, "seed_data.json doit contenir 60 proprietes"
    assert len(data["lots"]) == 8, "seed_data.json doit contenir 8 lots"
    return data


def seed(force: bool = False) -> None:
    Base.metadata.create_all(engine)
    data = load_seed()
    db: Session = SessionLocal()
    try:
        if force:
            db.query(models.Property).delete()
            db.query(models.Lot).delete()
            db.commit()

        if db.query(models.Property).count() == 0:
            for raw in data["properties"]:
                row = {k: v for k, v in raw.items() if k in PROPERTY_COLUMNS}
                db.add(models.Property(**row))
            db.commit()
            print(f"[OK] {len(data['properties'])} proprietes inserees")
        else:
            print("[--] proprietes deja presentes (ignoré, utiliser --force pour reseed)")

        if db.query(models.Lot).count() == 0:
            for raw in data["lots"]:
                row = {k: v for k, v in raw.items() if k in LOT_COLUMNS}
                db.add(models.Lot(**row))
            db.commit()
            print(f"[OK] {len(data['lots'])} lots inseres")
        else:
            print("[--] lots deja presents (ignoré, utiliser --force pour reseed)")

        admin = ensure_default_admin(db)
        print(f"[OK] admin cree/verifie : {admin.username} (hash bcrypt en base)")

        print(
            f"\nResume : {db.query(models.Property).count()} proprietes, "
            f"{db.query(models.Lot).count()} lots, "
            f"{db.query(models.Admin).count()} admin(s)"
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed(force="--force" in sys.argv)
