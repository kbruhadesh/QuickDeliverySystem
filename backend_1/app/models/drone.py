from sqlalchemy import Column, Integer, Float, String
from app.database import Base


class Drone(Base):
    __tablename__ = "drones"

    id = Column(Integer, primary_key=True, index=True)

    battery = Column(Float)        # %
    max_payload = Column(Float)    # weight capacity
    status = Column(String)        # available / busy