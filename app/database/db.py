# app/database/db.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL вашей базы данных.
# Для простоты я использовал SQLite, которая хранит данные в файле.
# Вы можете изменить это на 'postgresql://user:password@host/dbname' для PostgreSQL.
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# Создаем движок SQLAlchemy.
# connect_args нужен только для SQLite.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Создаем класс SessionLocal, который будет использоваться для сессий.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем базовый класс для моделей SQLAlchemy.
Base = declarative_base()


# Эта функция-генератор — и есть та самая get_db, которую вы импортировали.
# Она открывает сессию, возвращает ее и закрывает после использования.
def get_db():
    db = SessionLocal()
    try:
        # 'yield' передает управление в функцию, которая вызвала get_db.
        # Например, в ваш API-эндпоинт.
        yield db
    finally:
        # После завершения запроса (даже если произошла ошибка),
        # сессия базы данных закрывается.
        db.close()
