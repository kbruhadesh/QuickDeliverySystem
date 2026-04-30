from pydantic import BaseModel

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    category: str
    store_id: int

    class Config:
        from_attributes = True