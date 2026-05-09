from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    street = Column(String)
    city = Column(String)
    state = Column(String)
    pincode = Column(String)
    latitude = Column(Float, nullable=True)   # Geocoded from Nominatim at save time
    longitude = Column(Float, nullable=True)  # Geocoded from Nominatim at save time

    user = relationship("User")