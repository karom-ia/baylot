from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session  # ← ДОБАВЬТЕ scoped_session
from sqlalchemy.ext.declarative import declarative_base
from app.config import DATABASE_URL

# Используйте пул соединений для совместимости
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()