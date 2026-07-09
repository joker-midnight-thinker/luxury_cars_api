import os
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import OperationalError

load_dotenv()

# Приоритет: PostgreSQL из ENV -> SQLite по умолчанию
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://luxuryuser:mypassword@localhost:5432/luxurycars")

# Пытаемся подключиться к PostgreSQL. Если падает — переключаемся на SQLite.
try:
    if DATABASE_URL.startswith("postgresql"):
        # Проверяем подключение с коротким таймаутом (2 секунды)
        temp_engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 2})
        with temp_engine.connect() as conn:
            pass
        engine = temp_engine
        print("Подключение к PostgreSQL прошло успешно.")
    else:
        raise ValueError("Используется не-PostgreSQL URL")
except (OperationalError, Exception) as e:
    print(f"Не удалось подключиться к PostgreSQL: {e}. Переключение на SQLite...")
    DATABASE_URL = "sqlite:///./luxurycars.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    retries = 3
    db = None
    for attempt in range(retries):
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            break
        except Exception as e:
            if db:
                db.close()
            if attempt == retries - 1:
                db = SessionLocal()
            else:
                time.sleep(1)
    try:
        yield db
    finally:
        if db:
            db.close()