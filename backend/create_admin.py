import sys
import os
import uuid

# Add the parent directory to sys.path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.database import SessionLocal
from app.models import User
from app.utils.security import hash_password

def create_admin():
    db = SessionLocal()
    email = "test@hdl.com"
    password = "admin"
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        print(f"User {email} already exists. Updating role to admin...")
        existing_user.role = "admin"
        existing_user.password_hash = hash_password(password)
        db.commit()
        print("User updated successfully.")
        return

    admin_user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password(password),
        full_name="System Admin",
        role="admin"
    )
    
    db.add(admin_user)
    db.commit()
    print(f"Admin user created successfully: {email}")
    db.close()

if __name__ == "__main__":
    create_admin()
