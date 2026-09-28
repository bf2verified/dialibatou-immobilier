"""
Schemas Pydantic (validation stricte de tous les inputs de l'API).
Rgle forte : AUCUN base64 (data:) dans im[] / vd[] — les fichiers passent
par /api/upload et sont stockes sur disque.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

# Enumerations cote frontend (index.html : TY, NB)
PROPERTY_TYPES = ["Appartement", "Villa", "Terrain", "Bureau", "Commerce", "Magasin", "Studio"]
TRANSACTIONS = ["Vente", "Location"]
LOT_STATUSES = ["Disponible", "Limité", "Épuisé"]
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")
VIDEO_EXTENSIONS = (".mp4", ".webm", ".mov", ".m4v")


def _reject_data_uri(value: str, field: str) -> str:
    """Interdit les data URLs (base64) : les fichiers passent par /api/upload."""
    if value.strip().lower().startswith("data:"):
        raise ValueError(f"{field} : les data URLs base64 sont interdites, utilisez /api/upload")
    if not (value.startswith("/") or value.startswith("http://") or value.startswith("https://")):
        raise ValueError(f"{field} doit etre une URL relative (/uploads/...) ou absolue (http...)")
    return value


class Agent(BaseModel):
    na: str = Field(default="Mame Cheikh Ndiaye", max_length=255)
    ph: str = Field(default="+221 77 709 61 44", max_length=50)


class Video(BaseModel):
    type: Literal["url", "file"]
    src: str = Field(min_length=1, max_length=2000)
    name: Optional[str] = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def check_src(self):
        if self.type == "file":
            _reject_data_uri(self.src, "video src")
        elif not self.src.startswith(("http://", "https://")):
            raise ValueError("video url : doit commencer par http(s)://")
        return self


class PropertyBase(BaseModel):
    ti: str = Field(min_length=1, max_length=255)
    de: Optional[str] = Field(default="", max_length=10000)
    ty: str = Field(default="Appartement")
    tr: str = Field(default="Vente")
    pr: int = Field(default=0, ge=0, le=1_000_000_000_000)
    nb: str = Field(min_length=1, max_length=100)
    su: Optional[int] = Field(default=0, ge=0, le=1_000_000)
    ro: Optional[int] = Field(default=0, ge=0, le=1000)
    be: Optional[int] = Field(default=0, ge=0, le=1000)
    ba: Optional[int] = Field(default=0, ge=0, le=1000)
    fe: list[str] = Field(default_factory=list, max_length=100)
    im: list[str] = Field(default_factory=list, max_length=60)
    vd: list[Video] = Field(default_factory=list, max_length=20)
    ft: bool = False
    vi: int = Field(default=0, ge=0)
    ag: Optional[Agent] = None

    @field_validator("ty")
    @classmethod
    def validate_ty(cls, v: str) -> str:
        if v not in PROPERTY_TYPES:
            raise ValueError(f"ty doit etre l'un de {PROPERTY_TYPES}")
        return v

    @field_validator("tr")
    @classmethod
    def validate_tr(cls, v: str) -> str:
        if v not in TRANSACTIONS:
            raise ValueError(f"tr doit etre l'un de {TRANSACTIONS}")
        return v

    @field_validator("im")
    @classmethod
    def validate_im(cls, v: list[str]) -> list[str]:
        return [_reject_data_uri(url, "image") for url in v]

    @field_validator("fe")
    @classmethod
    def validate_fe(cls, v: list[str]) -> list[str]:
        for item in v:
            if len(item) > 255:
                raise ValueError("equipement trop long (255 max)")
        return v


class PropertyCreate(PropertyBase):
    pass


class PropertyOut(PropertyBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LotBase(BaseModel):
    loc: str = Field(min_length=1, max_length=100)
    zone: Optional[str] = Field(default="", max_length=100)
    lots: int = Field(ge=0, le=1_000_000)
    dispo: int = Field(ge=0, le=1_000_000)
    su: int = Field(ge=0, le=1_000_000)
    pr: int = Field(ge=0, le=1_000_000_000_000)
    st: str = "Disponible"
    fe: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("st")
    @classmethod
    def validate_st(cls, v: str) -> str:
        if v not in LOT_STATUSES:
            raise ValueError(f"st doit etre l'un de {LOT_STATUSES}")
        return v

    @model_validator(mode="after")
    def check_dispo(self):
        if self.dispo > self.lots:
            raise ValueError("dispo ne peut pas depasser le nombre total de lots")
        return self


class LotCreate(LotBase):
    pass


class LotOut(LotBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=50)
    subject: Optional[str] = Field(default=None, max_length=255)
    message: str = Field(min_length=1, max_length=5000)


class MessageUpdate(BaseModel):
    read: bool


class MessageOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    subject: Optional[str] = None
    message: str
    read: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class UploadResponse(BaseModel):
    url: str
    filename: str
    size: int


class ViewResponse(BaseModel):
    id: int
    views: int
