from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.config import DATABASE_URL
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Убедитесь что DATABASE_URL начинается с postgresql+asyncpg://
if DATABASE_URL:
    if not DATABASE_URL.startswith('postgresql+asyncpg://'):
        # Автоматически исправляем URL если нужно
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
    logger.info(f"Database URL: {DATABASE_URL}")
else:
    raise ValueError("DATABASE_URL is not set in environment variables")

# Создаем асинхронный engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    poolclass=NullPool,
    future=True,
    pool_pre_ping=True,  # ← ДОБАВЬТЕ ЭТУ ОПЦИЮ для проверки соединения
    pool_recycle=3600,   # ← Пересоздаем соединения каждые 60 минут
)

# Асинхронная сессия
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

async def get_db():
    """
    Асинхронный генератор сессий для Dependency Injection
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # ← Автоматический коммит при успехе
        except Exception as e:
            await session.rollback()  # ← Откат при ошибке
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()