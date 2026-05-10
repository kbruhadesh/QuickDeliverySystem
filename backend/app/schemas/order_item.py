from pydantic import BaseModel, ConfigDict
from uuid import UUID

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: UUID
    product_id: int
    quantity: int
    price: float
