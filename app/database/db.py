from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()  # Загружаем переменные из .env

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"👉 DATABASE_URL = {DATABASE_URL}")  # ← временно для отладки

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL not set or .env not found")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
