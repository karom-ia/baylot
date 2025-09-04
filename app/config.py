from dotenv import load_dotenv
import os

# Принудительная загрузка .env
load_dotenv(override=True)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secre123") 
ADMIN_KEY = os.getenv("ADMIN_KEY", "MySuperSecretKeyForDeleteAll2133")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
DATABASE_URL = os.getenv("DATABASE_URL")
SOLANA_WALLET_ADDRESS = os.getenv("SOLANA_WALLET_ADDRESS", "4NuDayX7fiZT4Teo9HGBNqCRKNV6bRsPFAY6JkjYC9rN")