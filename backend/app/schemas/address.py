from pydantic import BaseModel
from typing import Optional


class AddressCreate(BaseModel):
    street: str
    city: str
    state: str
    pincode: str


class AddressResponse(BaseModel):
    id: int
    street: str
    city: str
    state: str
    pincode: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True