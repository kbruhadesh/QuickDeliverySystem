from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = []
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    pickup_address: Optional[str] = None
    delivery_address: Optional[str] = None
    package_description: Optional[str] = None
    package_weight: Optional[float] = 1.0

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    estimated_delivery_time: Optional[datetime] = None
    actual_delivery_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    route_path: Optional[List[List[float]]] = None
    eta_minutes: Optional[float] = None

class OrderResponse(BaseModel):
    id: str
    order_number: Optional[str] = None
    total_amount: float
    status: str
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    pickup_address: Optional[str] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    delivery_address: Optional[str] = None
    package_weight: Optional[float] = None
    package_description: Optional[str] = None
    items_summary: Optional[str] = None
    priority: Optional[str] = "standard"
    estimated_delivery_time: Optional[datetime] = None
    actual_delivery_time: Optional[datetime] = None
    route_path: Optional[List[List[float]]] = None
    eta_minutes: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True