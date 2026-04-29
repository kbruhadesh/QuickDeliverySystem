from sqlalchemy import Column, Integer, String
from app.database import Base

class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    pincode = Column(String, index=True)
    address = Column(String)