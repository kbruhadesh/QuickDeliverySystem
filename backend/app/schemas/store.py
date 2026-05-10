from pydantic import BaseModel, ConfigDict
from typing import Optional

class StoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    pincode: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
