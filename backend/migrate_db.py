import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@127.0.0.1:5432/drone_delivery")
engine = create_engine(DATABASE_URL)

migrations = [
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS items_summary TEXT;",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS total_amount FLOAT DEFAULT 0.0;",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS route_path JSONB;",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS eta_minutes INTEGER;",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS start_time TIMESTAMP;"
]

with engine.connect() as conn:
    for m in migrations:
        try:
            print(f"Executing: {m}")
            conn.execute(text(m))
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")

print("Migration completed.")
