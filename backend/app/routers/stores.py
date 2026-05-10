from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.db_models.store import Store

router = APIRouter(prefix="/stores", tags=["Stores"])

class StoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    pincode: str
    address: str
    latitude: float = None
    longitude: float = None

@router.get("/", response_model=List[StoreResponse])
def get_stores(db: Session = Depends(get_db)):
    try:
        stores = db.query(Store).all()
        return stores
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
