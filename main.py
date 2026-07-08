from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models
import schemas
from database import engine, get_db

# Создаем таблицы при первом запуске
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Luxury Cars API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5501",
        "http://127.0.0.1:5501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Luxury Cars API is running"}

@app.get("/api/cars", response_model=list[schemas.CarResponse])
def get_cars(db: Session = Depends(get_db)):
    return db.query(models.Car).all()

@app.post("/api/cars", response_model=schemas.CarResponse)
def create_car(car: schemas.CarCreate, db: Session = Depends(get_db)):
    db_car = models.Car(**car.model_dump())
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    return db_car

# 🆕 НОВЫЙ ЭНДПОИНТ ДЛЯ ПРЕДЗАКАЗА
@app.post("/api/orders", response_model=schemas.OrderResponse)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    # Создаем новый заказ
    db_order = models.Order(**order.model_dump())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/api/orders", response_model=list[schemas.OrderResponse])
def get_orders(db: Session = Depends(get_db)):
    # Получить все заказы (для админки)
    return db.query(models.Order).order_by(models.Order.created_at.desc()).all()