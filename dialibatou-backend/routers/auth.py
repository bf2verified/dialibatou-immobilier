"""
Authentification admin : bcrypt + JWT (PyJWT).
POST /api/auth/login  ->  {"access_token": ..., "token_type": "bearer"}
Le mot de passe n'existe JAMAIS en clair : uniquement le hash bcrypt en table admins.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
from models import Admin
from schemas import LoginRequest, TokenResponse

router = APIRouter(tags=["auth"])

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-a-changer")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))  # 12 h
DEFAULT_ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
# Aucun mot de passe par defaut : sans ADMIN_PASSWORD dans le .env, l'admin
# n'est PAS cree automatiquement (evite un mot de passe devitable dans le code).
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()

bearer_scheme = HTTPBearer(auto_error=True)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def ensure_default_admin(db: Session):
    """Cree l'admin par defaut si la table est vide (idempotent).

    Refuse de creer un compte si aucun ADMIN_PASSWORD n'est configure :
    un mot de passe devitable dans le code serait une faille.
    """
    admin = db.query(Admin).filter(Admin.username == DEFAULT_ADMIN_USERNAME).first()
    if admin is not None:
        return admin
    if not DEFAULT_ADMIN_PASSWORD:
        return None
    admin = Admin(
        username=DEFAULT_ADMIN_USERNAME,
        password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def create_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> Admin:
    """Dependance : verifie le header Authorization: Bearer <JWT>."""
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        username = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton JWT invalide ou expire",
            headers={"WWW-Authenticate": "Bearer"},
        )
    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin is None:
        raise HTTPException(status_code=401, detail="Administrateur introuvable")
    return admin


@router.post("/api/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    """Connexion admin -> retourne un JWT (headers: Authorization: Bearer <token>)."""
    admin = db.query(Admin).filter(Admin.username == body.username).first() or ensure_default_admin(db)
    if admin is None:
        raise HTTPException(
            status_code=503,
            detail="Aucun administrateur configure : renseignez ADMIN_PASSWORD dans le .env puis relancez seed.py",
        )
    if not verify_password(body.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    return TokenResponse(
        access_token=create_access_token(admin.username), username=admin.username
    )
