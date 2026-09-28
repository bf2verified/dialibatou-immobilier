"""
CRUD /api/lots — lotissements de la cooperative.
Lecture publique ; ecriture protegee par JWT admin.
"""
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Admin, Lot
from routers.auth import get_current_user
from schemas import LotCreate, LotOut

router = APIRouter(prefix="/api/lots", tags=["lots"])

AdminDep = Annotated[Admin, Depends(get_current_user)]
DbDep = Annotated[Session, Depends(get_db)]


@router.get("", response_model=List[LotOut])
def get_lots(db: DbDep):
    return db.query(Lot).order_by(Lot.id).all()


@router.get("/{lot_id}", response_model=LotOut)
def get_lot(lot_id: int, db: DbDep):
    lot = db.get(Lot, lot_id)
    if lot is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    return lot


@router.post("", response_model=LotOut, status_code=200)
def create_lot(body: LotCreate, db: DbDep, _: AdminDep):
    lot = Lot(**body.model_dump())
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot


@router.put("/{lot_id}", response_model=LotOut)
def update_lot(lot_id: int, body: LotCreate, db: DbDep, _: AdminDep):
    lot = db.get(Lot, lot_id)
    if lot is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    for key, value in body.model_dump().items():
        setattr(lot, key, value)
    db.commit()
    db.refresh(lot)
    return lot


@router.delete("/{lot_id}")
def delete_lot(lot_id: int, db: DbDep, _: AdminDep):
    lot = db.get(Lot, lot_id)
    if lot is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    db.delete(lot)
    db.commit()
    return {"message": "Lot deleted successfully"}
