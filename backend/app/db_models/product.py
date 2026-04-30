from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)
    category = Column(String)

    store_id = Column(Integer, ForeignKey("stores.id"))