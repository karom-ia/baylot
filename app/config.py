from dotenv import load_dotenv
import os
from pathlib import Path

# Загружаем .env из корневой директории
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Конфигурация
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_KEY = os.getenv("ADMIN_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
SOLANA_WALLET_ADDRESS = os.getenv("SOLANA_WALLET_ADDRESS")

# Валидация
if not all([ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_KEY, SECRET_KEY, DATABASE_URL]):
    raise ValueError("Missing required environment variables")