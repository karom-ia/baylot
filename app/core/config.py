# app/core/config.py

from dotenv import load_dotenv
import os

load_dotenv()

ADMIN_KEY = os.getenv("ADMIN_KEY")
