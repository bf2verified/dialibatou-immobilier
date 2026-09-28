"""
Uploads multipart — fichiers physiques sur disque, JAMAIS de base64 en DB.
POST /api/upload/image  (max 5 Mo)   -> {"url": "/uploads/images/<uuid>.jpg"}
POST /api/upload/video  (max 50 Mo)  -> {"url": "/uploads/videos/<uuid>.mp4"}
Proteges par JWT admin. Les URL relatives sont prefixees par le frontend
avec API_URL.
"""
import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from models import Admin
from routers.auth import get_current_user
from schemas import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, UploadResponse

router = APIRouter(prefix="/api/upload", tags=["upload"])

AdminDep = Annotated[Admin, Depends(get_current_user)]

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "uploads" / "images"
VIDEOS_DIR = BASE_DIR / "uploads" / "videos"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

MAX_IMAGE_BYTES = 5 * 1024 * 1024    # 5 Mo
MAX_VIDEO_BYTES = 50 * 1024 * 1024   # 50 Mo


def _save(file: UploadFile, dest_dir: Path, extensions: tuple[str, ...],
          max_bytes: int, allowed_prefix: str) -> UploadResponse:
    original = file.filename or ""
    ext = Path(original).suffix.lower()
    if ext not in extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non autorisee : {ext} (autorisées : {', '.join(extensions)})",
        )
    if not (file.content_type or "").startswith(allowed_prefix):
        raise HTTPException(status_code=400, detail=f"Type MIME invalide : {file.content_type}")

    contents = file.file.read(max_bytes + 1)
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux (max {max_bytes // (1024 * 1024)} MB)",
        )
    if not contents:
        raise HTTPException(status_code=400, detail="Fichier vide")

    filename = f"{uuid.uuid4().hex}{ext}"
    (dest_dir / filename).write_bytes(contents)
    folder = dest_dir.name  # "images" ou "videos"
    return UploadResponse(
        url=f"/uploads/{folder}/{filename}", filename=original, size=len(contents)
    )


@router.post("/image", response_model=UploadResponse, status_code=200)
def upload_image(file: Annotated[UploadFile, File(...)], _: AdminDep):
    return _save(file, IMAGES_DIR, IMAGE_EXTENSIONS, MAX_IMAGE_BYTES, "image/")


@router.post("/video", response_model=UploadResponse, status_code=200)
def upload_video(file: Annotated[UploadFile, File(...)], _: AdminDep):
    return _save(file, VIDEOS_DIR, VIDEO_EXTENSIONS, MAX_VIDEO_BYTES, "video/")
