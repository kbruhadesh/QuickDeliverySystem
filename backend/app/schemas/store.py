from pydantic import BaseModel
from typing import Optional

class StoreResponse(BaseModel):
    id: int
    name: str
    pincode: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True