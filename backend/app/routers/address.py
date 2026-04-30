from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models.address import Address
from app.db_models.user import User
from app.schemas.address import AddressCreate, AddressResponse
from app.utils.jwt_handler import decode_access_token

router = APIRouter(prefix="/address", tags=["Address"])


# 🔑 Helper function (avoid repeating code)
def get_user_from_token(token: str, db: Session):
    payload = decode_access_token(token)
    email = payload.get("sub")

    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ➕ ADD ADDRESS
@router.post("/")
def add_address(address: AddressCreate, token: str, db: Session = Depends(get_db)):
    user = get_user_from_token(token, db)

    new_address = Address(
        user_id=user.id,
        street=address.street,
        city=address.city,
        state=address.state,
        pincode=address.pincode
    )

    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    return {"message": "Address added"}


# 📄 GET ADDRESSES (FIXED RESPONSE)
@router.get("/", response_model=list[AddressResponse])
def get_addresses(token: str, db: Session = Depends(get_db)):
    user = get_user_from_token(token, db)

    addresses = db.query(Address).filter(Address.user_id == user.id).all()

    return [AddressResponse.from_orm(addr) for addr in addresses]


# ❌ DELETE ADDRESS
@router.delete("/{address_id}")
def delete_address(address_id: int, token: str, db: Session = Depends(get_db)):
    user = get_user_from_token(token, db)

    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == user.id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    db.delete(address)
    db.commit()

    return {"message": "Address deleted"}
