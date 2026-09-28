"""
Modeles SQLAlchemy — tables de dialibatou_db (schema identique au DDL fourni).
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ti: Mapped[str] = mapped_column(String(255), nullable=False)          # titre
    de: Mapped[str | None] = mapped_column(Text)                          # description
    ty: Mapped[str] = mapped_column(String(50), nullable=False)           # type
    tr: Mapped[str] = mapped_column(String(20), nullable=False)           # transaction
    pr: Mapped[int] = mapped_column(BigInteger, nullable=False)           # prix FCFA
    nb: Mapped[str] = mapped_column(String(100), nullable=False)          # quartier
    su: Mapped[int | None] = mapped_column(Integer)                       # surface m2
    ro: Mapped[int | None] = mapped_column(Integer)                       # pieces
    be: Mapped[int | None] = mapped_column(Integer)                       # chambres
    ba: Mapped[int | None] = mapped_column(Integer)                       # salles de bain
    fe: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)  # equipements
    im: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)  # images (/uploads/...)
    vd: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)  # videos
    ft: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # vedette
    vi: Mapped[int] = mapped_column(Integer, nullable=False, default=0)       # vues
    ag: Mapped[dict | None] = mapped_column(JSONB)                            # agent {na, ph}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    views: Mapped[list["PropertyView"]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )


class Lot(Base):
    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loc: Mapped[str] = mapped_column(String(100), nullable=False)
    zone: Mapped[str | None] = mapped_column(String(100))
    lots: Mapped[int] = mapped_column(Integer, nullable=False)
    dispo: Mapped[int] = mapped_column(Integer, nullable=False)
    su: Mapped[int] = mapped_column(Integer, nullable=False)
    pr: Mapped[int] = mapped_column(BigInteger, nullable=False)
    st: Mapped[str] = mapped_column(String(30), nullable=False, default="Disponible")
    fe: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    subject: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PropertyView(Base):
    __tablename__ = "property_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False
    )
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    property: Mapped["Property"] = relationship(back_populates="views")


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
