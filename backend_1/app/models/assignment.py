from sqlalchemy import Column, Integer, ForeignKey, String
from app.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(Integer, ForeignKey("orders.id"))
    drone_id = Column(Integer, ForeignKey("drones.id"))

    status = Column(String, default="assigned")