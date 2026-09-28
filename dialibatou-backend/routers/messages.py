"""
Messages de contact — POST public (formulaire du site), GET/PUT/DELETE admin (JWT).
Resout le bug B7 : les messages sont desormais visibles par l'admin,
plus stockes uniquement dans le localStorage du visiteur.

Anti-spam : limitation en memoire (par IP et par email, fenetre glissante d'1 h).
A desactiver en developp si besoin : RATE_LIMIT_ENABLED=false
"""
import os
import time
from collections import defaultdict
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from models import Admin, Message
from routers.auth import get_current_user
from schemas import MessageCreate, MessageOut, MessageUpdate

router = APIRouter(prefix="/api/messages", tags=["messages"])

AdminDep = Annotated[Admin, Depends(get_current_user)]
DbDep = Annotated[Session, Depends(get_db)]

RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
MAX_PER_IP = int(os.getenv("MESSAGES_PER_HOUR_IP", "5"))
MAX_PER_EMAIL = int(os.getenv("MESSAGES_PER_HOUR_EMAIL", "3"))
WINDOW = 3600  # 1 heure

_hits = defaultdict(list)


def _is_limited(key: str, limit: int) -> bool:
    """Fenetre glissante : True si la limite est atteinte (et n'enregistre pas)."""
    now = time.time()
    hits = [t for t in _hits.get(key, []) if now - t < WINDOW]
    _hits[key] = hits
    if len(hits) >= limit:
        return True
    hits.append(now)
    return False


@router.post("", response_model=MessageOut, status_code=200)
def create_message(body: MessageCreate, request: Request, db: DbDep):
    """Recoit un message du formulaire de contact (public, limite anti-spam)."""
    if RATE_LIMIT_ENABLED:
        ip = request.client.host if request.client else "unknown"
        if _is_limited(f"ip:{ip}", MAX_PER_IP) or _is_limited(f"mail:{body.email.lower()}", MAX_PER_EMAIL):
            raise HTTPException(
                status_code=429,
                detail="Trop de messages envoyés récemment. Merci de réessayer dans une heure "
                       "ou de nous appeler directement.",
                headers={"Retry-After": str(WINDOW)},
            )
    msg = Message(**body.model_dump())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@router.get("", response_model=List[MessageOut])
def get_messages(db: DbDep, _: AdminDep):
    """Liste des messages, du plus recent au plus ancien (admin)."""
    return db.query(Message).order_by(Message.created_at.desc()).all()


@router.put("/{msg_id}", response_model=MessageOut)
def update_message(msg_id: int, body: MessageUpdate, db: DbDep, _: AdminDep):
    """Marquer lu/non-lu (admin)."""
    msg = db.get(Message, msg_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.read = body.read
    db.commit()
    db.refresh(msg)
    return msg


@router.delete("/{msg_id}")
def delete_message(msg_id: int, db: DbDep, _: AdminDep):
    msg = db.get(Message, msg_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(msg)
    db.commit()
    return {"message": "Message deleted successfully"}
