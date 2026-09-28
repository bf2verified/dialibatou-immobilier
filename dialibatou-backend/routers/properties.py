"""
CRUD /api/properties — compatible backend_test.py (POST/DELETE -> 200).
Lecture publique ; ecriture protègee par JWT admin.
"""
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Admin, Property, PropertyView
from routers.auth import get_current_user
from schemas import PropertyCreate, PropertyOut, ViewResponse

router = APIRouter(prefix="/api/properties", tags=["properties"])

AdminDep = Annotated[Admin, Depends(get_current_user)]
DbDep = Annotated[Session, Depends(get_db)]


@router.get("", response_model=List[PropertyOut])
def get_properties(db: DbDep):
    """Liste complete des proprietes (ordre d'insertion : seed en premier)."""
    return db.query(Property).order_by(Property.id).all()


@router.get("/{prop_id}", response_model=PropertyOut)
def get_property(prop_id: int, db: DbDep):
    prop = db.get(Property, prop_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@router.post("", response_model=PropertyOut, status_code=200)
def create_property(body: PropertyCreate, db: DbDep, _: AdminDep):
    prop = Property(**body.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


@router.put("/{prop_id}", response_model=PropertyOut)
def update_property(prop_id: int, body: PropertyCreate, db: DbDep, _: AdminDep):
    prop = db.get(Property, prop_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found")
    for key, value in body.model_dump().items():
        setattr(prop, key, value)
    db.commit()
    db.refresh(prop)
    return prop


@router.delete("/{prop_id}")
def delete_property(prop_id: int, db: DbDep, _: AdminDep):
    prop = db.get(Property, prop_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found")
    db.delete(prop)  # property_views supprimes en cascade
    db.commit()
    return {"message": "Property deleted successfully"}


@router.post("/{prop_id}/view", response_model=ViewResponse)
def add_view(prop_id: int, db: DbDep):
    """Incremente le compteur de vues + trace dans property_views (public)."""
    prop = db.get(Property, prop_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found")
    prop.vi = (prop.vi or 0) + 1
    db.add(PropertyView(property_id=prop.id))
    db.commit()
    db.refresh(prop)
    return ViewResponse(id=prop.id, views=prop.vi)
