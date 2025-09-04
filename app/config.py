from dotenv import load_dotenv
import os
from pathlib import Path

# Попробуем загрузить из разных мест
env_paths = [
    Path(__file__).parent.parent / '.env',  # Локальная разработка
    Path('/etc/secrets/.env'),              # Render secrets
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break
else:
    # Если файл .env не найден, используем переменные окружения
    pass

# Конфигурация - используем os.getenv() который работает и с файлами и с переменными окружения
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_KEY = os.getenv("ADMIN_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
SOLANA_WALLET_ADDRESS = os.getenv("SOLANA_WALLET_ADDRESS")

# Валидация только в продакшене
if os.getenv("ENV") == "production":
    missing_vars = []
    for var_name, var_value in [
        ("ADMIN_USERNAME", ADMIN_USERNAME),
        ("ADMIN_PASSWORD", ADMIN_PASSWORD),
        ("ADMIN_KEY", ADMIN_KEY),
        ("SECRET_KEY", SECRET_KEY),
        ("DATABASE_URL", DATABASE_URL)
    ]:
        if not var_value:
            missing_vars.append(var_name)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")