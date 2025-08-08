from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
import os

# 1. Сначала создаем экземпляр приложения
app = FastAPI()

# 2. Затем настраиваем шаблоны
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# 3. Только потом импортируем модули, которые используют app
from app.database.db import get_db, Base
from app.models.ticket import Ticket

# 4. Инициализация БД (должна быть после определения Base)
try:
    Base.metadata.create_all(bind=get_db().bind)
except Exception as e:
    print(f"Ошибка при создании таблиц: {e}")

# 5. Регистрация маршрутов
@app.get("/test")
async def test():
    return {"status": "OK", "message": "Тестовый маршрут работает"}

@app.get("/")
async def root(request: Request, db: Session = Depends(get_db)):
    return {"message": "Главная страница работает"}

@app.get("/admin")
async def admin(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

# 6. Подключение статических файлов
static_dir = Path(__file__).parent / "static"
upload_dir = Path(__file__).parent.parent / "uploaded_tickets"

static_dir.mkdir(exist_ok=True)
upload_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/uploaded_tickets", StaticFiles(directory=upload_dir), name="uploads")