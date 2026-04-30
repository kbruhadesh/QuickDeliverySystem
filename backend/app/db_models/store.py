from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    pincode = Column(String, index=True)
    address = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)