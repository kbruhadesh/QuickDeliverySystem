import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.db_models.store import Store

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@127.0.0.1:5432/drone_delivery")

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
        {"name": "Banjara Hills Node", "pincode": "500034", "address": "Road 12, Banjara Hills, Hyderabad", "lat": 17.410816, "lng": 78.437314},
        {"name": "Gachibowli Hub", "pincode": "500032", "address": "Telecom Nagar, Gachibowli, Hyderabad", "lat": 17.4361, "lng": 78.3667},
        {"name": "Hi-Tech City Express", "pincode": "500081", "address": "Mindspace IT Park, HITEC City, Hyderabad", "lat": 17.4474, "lng": 78.3762},
        {"name": "Hanamkonda Central", "pincode": "506001", "address": "Subedari, Hanamkonda", "lat": 17.994015, "lng": 79.548116},
        {"name": "Warangal Fort Hub", "pincode": "506008", "address": "Fort Road, Warangal", "lat": 17.956121, "lng": 79.614708},
        {"name": "Vallikavu Express (Amritapuri)", "pincode": "690546", "address": "Amritapuri Campus, Vallikavu", "lat": 9.0936, "lng": 76.4912},
        {"name": "Kollam Beach Node", "pincode": "691001", "address": "Kollam Beach Road, Kollam", "lat": 8.88113, "lng": 76.58469}
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

    # Remove the older duplicate name that was used before the canonical store list.
    db.execute(text("""
        DELETE FROM stores
        WHERE name = 'Vallikavu Express'
          AND EXISTS (
              SELECT 1 FROM stores
              WHERE name = 'Vallikavu Express (Amritapuri)'
          )
    """))

    # Keep the API product endpoints useful for every store. The frontend has the
    # same catalog hardcoded today, but the database should still be complete.
    db.execute(text("""
        SELECT setval(
            pg_get_serial_sequence('products', 'id'),
            COALESCE((SELECT MAX(id) FROM products), 1),
            true
        )
    """))
    db.execute(text("""
        WITH catalog(name, category, price) AS (
            VALUES
                ('Farm Fresh Milk', 'Dairy', 30.0),
                ('Whole Wheat Bread', 'Bakery', 45.0),
                ('Bananas (Robusta)', 'Fruits', 50.0),
                ('Red Tomatoes', 'Vegetables', 40.0),
                ('Potato Chips - Salted', 'Snacks', 35.0),
                ('Cold Brew Coffee', 'Drinks', 120.0),
                ('Organic Eggs', 'Dairy', 65.0),
                ('Dark Chocolate', 'Snacks', 100.0)
        )
        INSERT INTO products (store_id, name, category, price)
        SELECT s.id, c.name, c.category, c.price
        FROM stores s
        CROSS JOIN catalog c
        WHERE NOT EXISTS (
            SELECT 1
            FROM products p
            WHERE p.store_id = s.id
              AND p.name = c.name
        )
    """))

    db.commit()
    print("Stores seeded successfully into PostgreSQL!")
    db.close()

if __name__ == "__main__":
    seed_stores()
