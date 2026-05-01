from app.database import SessionLocal, engine
from app.db_models.drone import Drone
from app.db_models.product import Product
from app.db_models.store import Store
from app.database import Base

def seed_initial_data():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        stores = [
            {"name": "Banjara Hills Node", "pincode": "500034", "address": "Road 12, Banjara Hills, Hyderabad", "latitude": 17.4122, "longitude": 78.4436},
            {"name": "Gachibowli Hub", "pincode": "500032", "address": "Telecom Nagar, Gachibowli, Hyderabad", "latitude": 17.4401, "longitude": 78.3489},
            {"name": "Hi-Tech City Express", "pincode": "500081", "address": "Mindspace IT Park, Hyderabad", "latitude": 17.4474, "longitude": 78.3762},
            {"name": "Hanamkonda Central", "pincode": "506001", "address": "Subedari, Hanamkonda", "latitude": 18.0044, "longitude": 79.5581},
            {"name": "Warangal Fort Hub", "pincode": "506008", "address": "Fort Road, Warangal", "latitude": 17.9689, "longitude": 79.5941},
            {"name": "Vallikavu Express", "pincode": "690546", "address": "Amritapuri Campus, Vallikavu", "latitude": 9.0939, "longitude": 76.4918},
            {"name": "Kollam Beach Node", "pincode": "691001", "address": "Kollam Beach Road, Kollam", "latitude": 8.8853, "longitude": 76.5865},
        ]

        for data in stores:
            existing = db.query(Store).filter(Store.name == data["name"]).first()
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                db.add(Store(**data))
        db.commit()

        default_store = db.query(Store).filter(Store.name == "Banjara Hills Node").first()
        store_id = default_store.id if default_store else 1
        
        products = [
            {"id": 1, "name": "Farm Fresh Milk", "price": 30, "category": "Dairy", "store_id": store_id},
            {"id": 2, "name": "Whole Wheat Bread", "price": 45, "category": "Bakery", "store_id": store_id},
            {"id": 3, "name": "Bananas (Robusta)", "price": 50, "category": "Fruits", "store_id": store_id},
            {"id": 4, "name": "Red Tomatoes", "price": 40, "category": "Vegetables", "store_id": store_id},
            {"id": 5, "name": "Potato Chips - Salted", "price": 35, "category": "Snacks", "store_id": store_id},
            {"id": 6, "name": "Cold Brew Coffee", "price": 120, "category": "Drinks", "store_id": store_id},
            {"id": 7, "name": "Organic Eggs", "price": 65, "category": "Dairy", "store_id": store_id},
            {"id": 8, "name": "Dark Chocolate", "price": 100, "category": "Snacks", "store_id": store_id},
        ]
        for data in products:
            existing = db.query(Product).filter(Product.id == data["id"]).first()
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                db.add(Product(**data))

        drones = [
            {"id": 1, "battery": 100.0, "max_payload": 5.0, "status": "available", "latitude": 17.4122, "longitude": 78.4436},
            {"id": 2, "battery": 95.0, "max_payload": 5.0, "status": "available", "latitude": 18.0044, "longitude": 79.5581},
            {"id": 3, "battery": 90.0, "max_payload": 3.0, "status": "available", "latitude": 9.0939, "longitude": 76.4918},
        ]
        for data in drones:
            existing = db.query(Drone).filter(Drone.id == data["id"]).first()
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                db.add(Drone(**data))
        db.commit()
        print("Initial data seeded successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_initial_data()
