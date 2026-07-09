from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
import time
from collections import defaultdict
import models
import schemas
import auth
from database import engine, get_db, SessionLocal

# Создаем таблицы при первом запуске
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Luxury Cars API")

def rate_limiter(limit: int, seconds: int):
    # У каждого инстанса лимитера своя независимая история запросов по IP
    history = defaultdict(list)
    
    def dependency(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        # Очищаем старые записи вне временного интервала
        history[client_ip] = [t for t in history[client_ip] if now - t < seconds]
        if len(history[client_ip]) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Слишком много запросов. Пожалуйста, попробуйте позже."
            )
        history[client_ip].append(now)
    return dependency

# Настройка CORS в зависимости от окружения
ENV = os.getenv("ENV", "development")
if ENV == "production":
    ALLOWED_ORIGINS = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://redline-motors.ru"
    ]
else:
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = auth.verify_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен или время действия истекло",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload["sub"]
    db_admin = db.query(models.Admin).filter(models.Admin.username == username).first()
    if not db_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Администратор не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return db_admin

# Авто-создание дефолтного администратора при запуске, если таблица пуста
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        if db.query(models.Admin).count() == 0:
            default_user = os.getenv("ADMIN_USERNAME", "admin")
            default_pass = os.getenv("ADMIN_PASSWORD", "adminpassword123")
            hashed = auth.get_password_hash(default_pass)
            db_admin = models.Admin(username=default_user, password_hash=hashed)
            db.add(db_admin)
            db.commit()
            print(f"[*] Инициализация: Создан администратор по умолчанию: {default_user} / {default_pass}")
    except Exception as e:
        print(f"Ошибка при создании дефолтного администратора: {e}")
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Luxury Cars API is running"}

# --- ПУБЛИЧНЫЕ ЭНДПОИНТЫ ---

@app.get("/api/cars", response_model=list[schemas.CarResponse])
def get_cars(db: Session = Depends(get_db)):
    return db.query(models.Car).all()

@app.get("/api/cars/{car_id}", response_model=schemas.CarResponse)
def get_car(car_id: str, db: Session = Depends(get_db)):
    car = db.query(models.Car).filter(models.Car.car_id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    return car

@app.post("/api/orders", response_model=schemas.OrderResponse, dependencies=[Depends(rate_limiter(5, 60))])
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    db_order = models.Order(**order.model_dump())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.post("/api/feedbacks", response_model=schemas.FeedbackResponse, dependencies=[Depends(rate_limiter(3, 60))])
def create_feedback(fb: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    db_fb = models.Feedback(**fb.model_dump())
    db.add(db_fb)
    db.commit()
    db.refresh(db_fb)
    return db_fb

# --- АВТОРИЗАЦИЯ ---

@app.post("/api/auth/login", response_model=schemas.AdminToken)
def login(credentials: schemas.AdminLogin, db: Session = Depends(get_db)):
    db_admin = db.query(models.Admin).filter(models.Admin.username == credentials.username).first()
    if not db_admin or not auth.verify_password(credentials.password, db_admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    token = auth.create_access_token(data={"sub": db_admin.username})
    return {"access_token": token, "token_type": "bearer"}

# --- ПАНЕЛЬ АДМИНИСТРАТОРА (ТРЕБУЕТ JWT-ТОКЕН) ---

@app.get("/api/admin/orders", response_model=list[schemas.OrderResponse])
def get_admin_orders(db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    return db.query(models.Order).order_by(models.Order.created_at.desc()).all()

@app.patch("/api/admin/orders/{order_id}", response_model=schemas.OrderResponse)
def update_admin_order(order_id: int, status_update: schemas.OrderStatusUpdate, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    db_order.status = status_update.status
    db.commit()
    db.refresh(db_order)
    return db_order

@app.delete("/api/admin/orders/{order_id}")
def delete_admin_order(order_id: int, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    db.delete(db_order)
    db.commit()
    return {"message": "Заказ успешно удален"}

@app.get("/api/admin/feedbacks", response_model=list[schemas.FeedbackResponse])
def get_admin_feedbacks(db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    return db.query(models.Feedback).order_by(models.Feedback.created_at.desc()).all()

@app.delete("/api/admin/feedbacks/{feedback_id}")
def delete_admin_feedback(feedback_id: int, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    db_fb = db.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()
    if not db_fb:
        raise HTTPException(status_code=404, detail="Обращение не найдено")
    db.delete(db_fb)
    db.commit()
    return {"message": "Обращение успешно удалено"}