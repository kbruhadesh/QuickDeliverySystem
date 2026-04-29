from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.store import Store
from app.models.product import Product
from app.schemas.store import StoreResponse
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/store", tags=["Store"])


# 🔍 GET STORES BY PINCODE
@router.get("/", response_model=list[StoreResponse])
def get_stores(pincode: str, db: Session = Depends(get_db)):
    stores = db.query(Store).filter(Store.pincode == pincode).all()
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