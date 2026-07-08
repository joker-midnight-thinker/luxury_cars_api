import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

# Берём URL из переменной окружения (на Render она будет задана вручную)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://luxuryuser:mypassword@localhost:5432/luxurycars")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()