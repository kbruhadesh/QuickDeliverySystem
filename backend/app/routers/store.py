from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.db_models.store import Store
from app.db_models.product import Product
from app.schemas.store import StoreResponse
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/store", tags=["Store"])


# 🔍 GET STORES BY PINCODE OR ALL
@router.get("/", response_model=list[StoreResponse])
def get_stores(pincode: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if pincode:
        stores = db.query(Store).filter(Store.pincode == pincode).all()
    else:
        stores = db.query(Store).all()
    return stores


# 🛒 GET PRODUCTS BY STORE
@router.get("/{store_id}/products", response_model=list[ProductResponse])
def get_products(store_id: int, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.store_id == store_id).all()
    return products


# 🎯 FILTER PRODUCTS BY CATEGORY
@router.get("/{store_id}/products/filter", response_model=list[ProductResponse])
def filter_products(store_id: int, category: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter(
        Product.store_id == store_id,
        Product.category == category
    ).all()

    return products
