from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import re

class CarBase(BaseModel):
    car_id: str
    brand: str
    title: str
    price: str
    preorder_url: str | None = None
    images: list[str] = []
    specs: list[dict] = []

class CarCreate(CarBase):
    pass

class CarResponse(CarBase):
    id: int

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=100)
    customer_phone: str
    customer_email: str | None = None
    car_model: str
    color: str | None = None
    comments: str | None = Field(None, max_length=1000)

    @field_validator('customer_phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^\+?[0-9\s\-()]{10,20}$", v):
            raise ValueError('Некорректный формат телефона. Должно быть от 10 до 20 цифр.')
        return v

    @field_validator('customer_email')
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v:
            v = v.strip()
            if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v):
                raise ValueError('Некорректный адрес электронной почты.')
        return v if v else None

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

class OrderStatusUpdate(BaseModel):
    status: str

class FeedbackCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str
    email: str | None = None
    message: str | None = Field(None, max_length=1000)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^\+?[0-9\s\-()]{10,20}$", v):
            raise ValueError('Некорректный формат телефона. Должно быть от 10 до 20 цифр.')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v:
            v = v.strip()
            if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v):
                raise ValueError('Некорректный адрес электронной почты.')
        return v if v else None

class FeedbackResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: str | None
    message: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminToken(BaseModel):
    access_token: str
    token_type: str = "bearer"