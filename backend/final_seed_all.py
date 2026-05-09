from app.database import SessionLocal, engine
from app.models import Drone, Base
from app.db_models.store import Store
import uuid

def final_seed():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Update/Create Stores (Hubs)
        stores_data = [
            {"name": "Banjara Hills Node", "pincode": "500034", "pickup_latitude": 17.4122, "pickup_longitude": 78.4436},
            {"name": "Gachibowli Hub", "pincode": "500032", "pickup_latitude": 17.4401, "pickup_longitude": 78.3489},
            {"name": "Hi-Tech City Express", "pincode": "500081", "pickup_latitude": 17.4474, "pickup_longitude": 78.3762},
            {"name": "Hanamkonda Central", "pincode": "506001", "pickup_latitude": 18.0044, "pickup_longitude": 79.5581},
            {"name": "Warangal Fort Hub", "pincode": "506008", "pickup_latitude": 17.9689, "pickup_longitude": 79.5941},
            {"name": "Vallikavu Express (Amritapuri)", "pincode": "690546", "pickup_latitude": 9.0939, "pickup_longitude": 76.4918},
            {"name": "Kollam Beach Node", "pincode": "691001", "pickup_latitude": 8.8853, "pickup_longitude": 76.5865}
        ]

        # NOTE: Store model fields are actually 'latitude' and 'longitude' in app/db_models/store.py 
        # but in app/models.py they might be different. Let's check app/models.py again.
        # Wait, I don't see Store in app/models.py. It must be in app/db_models/store.py.
        # Let's use 'latitude' and 'longitude'.

        for data in stores_data:
            s = db.query(Store).filter(Store.name == data["name"]).first()
            if not s:
                s = Store(name=data["name"], pincode=data["pincode"], latitude=data["pickup_latitude"], longitude=data["pickup_longitude"])
                db.add(s)
            else:
                s.latitude = data["pickup_latitude"]
                s.longitude = data["pickup_longitude"]
        
        db.commit()
        print("✅ Hubs seeded.")

        # 2. Update/Create Drones at Hubs
        # We'll clear old drones to avoid duplicates/confusion if they have non-UUID IDs
        db.query(Drone).delete()
        db.commit()

        drones_to_add = []
        for i, data in enumerate(stores_data):
            d = Drone(
                drone_id=f"HDL-DRONE-{i+1:03d}",
                model="DJI M300 RTK",
                max_payload=5.0,
                max_range=30.0,
                battery_capacity=5000,
                current_battery=100.0,
                status="idle",
                latitude=data["pickup_latitude"],
                longitude=data["pickup_longitude"],
                altitude=0.0,
                speed=0.0
            )
            drones_to_add.append(d)
        
        db.add_all(drones_to_add)
        db.commit()
        print(f"✅ {len(drones_to_add)} Drones seeded at Hub locations.")

    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    final_seed()
