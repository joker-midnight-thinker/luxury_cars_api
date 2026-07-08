from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base


class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, index=True)
    model = Column(String)
    year = Column(Integer)
    price = Column(Float)
    image_url = Column(String)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String)
    customer_phone = Column(String)
    customer_email = Column(String, nullable=True)
    car_model = Column(String)
    color = Column(String, nullable=True)
    comments = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="new")