# app/main.py

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from app.utils.template_engine import templates
from app.database.db import Base, engine
from app.models.ticket import Ticket
from app.routers import ticket
from app.utils.country_names import country_name_map
import os
print("DATABASE_URL:", os.getenv("DATABASE_URL"))


def get_country_name(code: str):
    """
    Возвращает полное название страны по её коду.
    """
    return country_name_map.get(code.upper(), code)

# Применяем фильтр к шаблонам Jinja2
templates.env.filters["country_name"] = get_country_name

app = FastAPI()

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

# Подключение роутеров
app.include_router(ticket.router)

# Подключение статических файлов (CSS, JS, изображения)
# Файлы из папки `static` будут доступны по URL /static/...
app.mount("/static", StaticFiles(directory="static"), name="static")
# Файлы из папки `uploaded_tickets` будут доступны по URL /uploaded_tickets/...
app.mount("/uploaded_tickets", StaticFiles(directory="uploaded_tickets"), name="uploaded_tickets")


# ---- ИЗМЕНЁННЫЙ КОД: ТЕПЕРЬ ГЛАВНАЯ СТРАНИЦА ПОКАЗЫВАЕТ HTML ----

# Корень: отображает ваш главный HTML-файл (admin_dashboard.html)
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

# ------------------------------------------------------------------

# Админка: этот маршрут уже был настроен правильно
@app.get("/admin")
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

