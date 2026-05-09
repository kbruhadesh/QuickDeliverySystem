import sys
import os
import requests
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append("/Users/tejaramidi/Documents/Teja Documents/6th Sem/1.Projects/QuickDeliverySystem-main/backend")

from app.database import SessionLocal
# Import all models to avoid registry errors
from app.db_models.user import User
from app.db_models.address import Address
from app.db_models.order import Order
from app.db_models.store import Store
from app.db_models.product import Product

def geocode_address(street, city, state, pincode):
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
        print(f"Geocoding failed for {query}: {e}")
    return None, None

def mass_geocode():
    db = SessionLocal()
    try:
        # Find addresses with missing coordinates
        missing = db.query(Address).filter((Address.latitude == None) | (Address.longitude == None)).all()
        print(f"Found {len(missing)} addresses missing coordinates.")
        
        for addr in missing:
            print(f"Geocoding: {addr.street}, {addr.city}...")
            lat, lon = geocode_address(addr.street, addr.city, addr.state, addr.pincode)
            if lat and lon:
                addr.latitude = lat
                addr.longitude = lon
                print(f"✓ Geocoded: {addr.street} -> {lat}, {lon}")
            else:
                # Second attempt with just pincode
                lat, lon = geocode_address("", "", "", addr.pincode)
                if lat and lon:
                    addr.latitude = lat
                    addr.longitude = lon
                    print(f"✓ Geocoded (Pincode fallback): {addr.pincode} -> {lat}, {lon}")
                else:
                    print(f"✗ Failed to geocode: {addr.street}")
        
        db.commit()
        print("Done!")
    finally:
        db.close()

if __name__ == "__main__":
    mass_geocode()
