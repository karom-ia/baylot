# app/database/db.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Строка подключения к PostgreSQL
# ЗАМЕНИ ПАРОЛЬ И ПРИ НЕОБХОДИМОСТИ host/port
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:My-fmpg1@localhost:5432/ticket_system"

# Создаем движок SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Сессия для взаимодействия с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс моделей
Base = declarative_base()

# Функция для зависимости FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
