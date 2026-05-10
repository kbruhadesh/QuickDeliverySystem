from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str
    phone: str
