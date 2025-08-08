# app/database/db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# URL для вашей базы данных SQLite.
# Замените на вашу строку подключения к базе данных, если вы используете другую.
SQLALCHEMY_DATABASE_URL = "sqlite:///./ticket_system.db"

# Создание движка SQLAlchemy
# connect_args={"check_same_thread": False} необходимо для SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Создание класса сессии. Это будет класс для каждой сессии базы данных.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей SQLAlchemy.
Base = declarative_base()

def get_db():
    """
    Создает сессию базы данных и закрывает ее после использования.
    Эта функция используется как зависимость в маршрутах FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
