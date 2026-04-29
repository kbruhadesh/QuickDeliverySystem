from pydantic import BaseModel

class StoreResponse(BaseModel):
    id: int
    name: str
    pincode: str
    address: str

    class Config:
        from_attributes = True