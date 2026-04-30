import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db_models import store, product, drone, address
from app.database import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/drone_delivery")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed():
    db = SessionLocal()
    
    # Initialize tables
    Base.metadata.create_all(bind=engine)

    # Add default stores if empty
    if not db.query(store.Store).first():
        s1 = store.Store(name="HDL Hi-Tech City Hub", address="Hi-Tech City Main Road", pincode="500081", lat=17.4435, lon=78.3772)
        s2 = store.Store(name="HDL Banjara Hills Hub", address="Road No. 12", pincode="500034", lat=17.4156, lon=78.4347)
        db.add_all([s1, s2])
        db.commit()
        
        # Add products
        p1 = product.Product(store_id=s1.id, name="Milk 1L", category="dairy", price=65.0, weight_kg=1.0, inventory=100)
        p2 = product.Product(store_id=s1.id, name="Bread", category="bakery", price=40.0, weight_kg=0.4, inventory=50)
        p3 = product.Product(store_id=s2.id, name="Milk 1L", category="dairy", price=65.0, weight_kg=1.0, inventory=100)
        db.add_all([p1, p2, p3])
        db.commit()
        print("✅ Added Stores & Products!")

    # Add drones if empty
    if not db.query(drone.Drone).first():
        d1 = drone.Drone(id="D-01", status="available", battery=100.0, current_lat=17.4435, current_lon=78.3772)
        d2 = drone.Drone(id="D-02", status="available", battery=95.0, current_lat=17.4156, current_lon=78.4347)
        d3 = drone.Drone(id="D-03", status="available", battery=80.0, current_lat=17.4435, current_lon=78.3772)
        db.add_all([d1, d2, d3])
        db.commit()
        print("✅ Added Drones!")

    db.close()
    print("Database seeding complete!")

if __name__ == "__main__":
    seed()
