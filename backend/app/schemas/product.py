from pydantic import BaseModel, ConfigDict

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    category: str
    store_id: int
