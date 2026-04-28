from dataclasses import dataclass
from typing import Optional

@dataclass
class Drone:
    id: str
    max_payload: float  # kg
    battery_capacity: float  # mAh or percentage baseline
    latitude: float
    longitude: float

@dataclass
class Order:
    id: str
    package_weight: float  # kg
    pickup_latitude: float
    pickup_longitude: float
    delivery_latitude: float
    delivery_longitude: float
