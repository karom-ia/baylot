from logging.config import fileConfig
import sys
import os

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Добавляем путь к корню проекта, чтобы можно было импортировать app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импорт базы и моделей
from app.database.db import Base
from app.models.ticket import Ticket

# Это объект конфигурации Alembic, который предоставляет доступ к .ini настройкам
config = context.config

# Интерпретируем конфигурационный файл для Python логирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Назначаем metadata из моделей (нужно для autogenerate)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в offline-режиме."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запуск миграций в online-режиме."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
