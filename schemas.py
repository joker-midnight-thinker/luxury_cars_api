from pydantic import BaseModel, EmailStr
from datetime import datetime

class CarBase(BaseModel):
    brand: str
    model: str
    year: int
    price: float
    image_url: str

class CarCreate(CarBase):
    pass

class CarResponse(CarBase):
    id: int

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: str | None = None
    car_model: str
    color: str | None = None
    comments: str | None = None

class OrderResponse(BaseModel):
    id: int
    customer_name: str
    customer_phone: str
    customer_email: str | None
    car_model: str
    color: str | None
    comments: str | None
    created_at: datetime
    status: str

    class Config:
        from_attributes = True