from pydantic import BaseModel, ConfigDict
from typing import Optional


class AddressCreate(BaseModel):
    street: str
    city: str
    state: str
    pincode: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    street: str
    city: str
    state: str
    pincode: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
