import psycopg2
from passlib.context import CryptContext
import uuid

# Database connection
conn = psycopg2.connect("postgresql://postgres:password@127.0.0.1:5432/drone_delivery")
cur = conn.cursor()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password_hash = pwd_context.hash("admin")

email = "test@hdl.com"
user_id = str(uuid.uuid4())

try:
    cur.execute("INSERT INTO users (id, email, password_hash, full_name, role) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (email) DO UPDATE SET role = 'admin', password_hash = %s", 
                (user_id, email, password_hash, "Admin User", "admin", password_hash))
    conn.commit()
    print(f"Admin user {email} created/updated successfully.")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
