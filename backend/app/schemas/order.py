from pydantic import BaseModel
from typing import List


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    pickup_latitude: float = None
    pickup_longitude: float = None
    delivery_latitude: float = None
    delivery_longitude: float = None


from datetime import datetime

class OrderResponse(BaseModel):
    id: int
    total_amount: float
    status: str
    pickup_latitude: float = None
    pickup_longitude: float = None
    delivery_latitude: float = None
    delivery_longitude: float = None
    created_at: datetime

    class Config:
        from_attributes = True