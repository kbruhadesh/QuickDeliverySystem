from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests

from app.database import get_db
from app.db_models.address import Address
from app.db_models.user import User
from app.schemas.address import AddressCreate, AddressResponse
from app.utils.jwt_handler import decode_access_token

router = APIRouter(prefix="/address", tags=["Address"])


# 🔑 Helper function
def get_user_from_token(token: str, db: Session):
    payload = decode_access_token(token)
    email = payload.get("sub")

    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def geocode_address(street: str, city: str, state: str, pincode: str):
    """
    Use Nominatim to geocode an address to lat/lon.
    Returns (lat, lon) or (None, None) if not found.
    """
    query = f"{street}, {city}, {state} {pincode}, India"
    try:
        res = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"format": "json", "q": query, "limit": 1},
            headers={"User-Agent": "HDL-DroneDelivery/1.0"},
            timeout=5
        )
        data = res.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"Geocoding failed: {e}")

    # Fallback: try just pincode
    try:
        res = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"format": "json", "q": f"{pincode}, India", "limit": 1},
            headers={"User-Agent": "HDL-DroneDelivery/1.0"},
            timeout=5
        )
        data = res.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"Pincode geocoding fallback failed: {e}")

    return None, None


# ➕ ADD ADDRESS — geocodes at save time
@router.post("/")
def add_address(address: AddressCreate, token: str, db: Session = Depends(get_db)):
    user = get_user_from_token(token, db)

    lat, lon = geocode_address(address.street, address.city, address.state, address.pincode)

    new_address = Address(
        user_id=user.id,
        street=address.street,
        city=address.city,
        state=address.state,
        pincode=address.pincode,
        latitude=lat,
        longitude=lon
    )

    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    return {
        "message": "Address added",
        "geocoded": lat is not None,
        "latitude": lat,
        "longitude": lon
    }


# 📄 GET ADDRESSES
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
