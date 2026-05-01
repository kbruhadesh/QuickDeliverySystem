import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.db_models.store import Store

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://tejaramidi@localhost:5432/drone_delivery")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_stores():
    # Create the table if it doesn't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Try adding columns if they don't exist
    try:
        db.execute(text("ALTER TABLE stores ADD COLUMN latitude FLOAT;"))
        db.commit()
    except Exception as e:
        db.rollback()
        
    try:
        db.execute(text("ALTER TABLE stores ADD COLUMN longitude FLOAT;"))
        db.commit()
    except Exception as e:
        db.rollback()

    # Seed the 7 real stores requested by user
    stores_data = [
        {"name": "Banjara Hills Node", "pincode": "500034", "address": "Road 12, Banjara Hills", "lat": 17.4122, "lng": 78.4436},
        {"name": "Gachibowli Hub", "pincode": "500032", "address": "Telecom Nagar, Gachibowli", "lat": 17.4401, "lng": 78.3489},
        {"name": "Hi-Tech City Express", "pincode": "500081", "address": "Mindspace IT Park", "lat": 17.4474, "lng": 78.3762},
        {"name": "Hanamkonda Central", "pincode": "506001", "address": "Subedari, Hanamkonda", "lat": 18.0044, "lng": 79.5581},
        {"name": "Warangal Fort Hub", "pincode": "506008", "address": "Fort Road, Warangal", "lat": 17.9689, "lng": 79.5941},
        {"name": "Vallikavu Express (Amritapuri)", "pincode": "690546", "address": "Amritapuri Campus", "lat": 9.0939, "lng": 76.4918},
        {"name": "Kollam Beach Node", "pincode": "691001", "address": "Kollam Beach Road", "lat": 8.8853, "lng": 76.5865}
    ]

    for data in stores_data:
        # Check if store exists by name
        res = db.execute(text("SELECT id FROM stores WHERE name = :name"), {"name": data["name"]}).fetchone()
        if res:
            store_id = res[0]
            print(f"Updating store: {data['name']} (ID: {store_id})")
            db.execute(text("""
                UPDATE stores 
                SET pincode = :pincode, address = :address, latitude = :lat, longitude = :lng
                WHERE id = :id
            """), {
                "pincode": data["pincode"],
                "address": data["address"],
                "lat": data["lat"],
                "lng": data["lng"],
                "id": store_id
            })
        else:
            print(f"Inserting new store: {data['name']}")
            db.execute(text("""
                INSERT INTO stores (name, pincode, address, latitude, longitude)
                VALUES (:name, :pincode, :address, :lat, :lng)
            """), data)
            
    db.commit()
    print("Stores seeded successfully into PostgreSQL!")
    db.close()

if __name__ == "__main__":
    seed_stores()
