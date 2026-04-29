from pydantic import BaseModel


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

    class Config:
        from_attributes = True