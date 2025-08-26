# app/main.py

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database.db import Base, engine
from app.models.ticket import Ticket
from app.routers import ticket
from app.utils.country_names import country_name_map  # словарь кода -> название

# ---------- Фильтры для Jinja2 ----------

# Преобразование кода страны в флаг (🇺🇸, 🇷🇺 и т.д.)
def get_flag(country_code: str) -> str:
    """
    Возвращает флаг-эмодзи по коду страны (например, 'US' -> 🇺🇸).
    """
    if not country_code or len(country_code) != 2:
        return "🏳️"  # fallback
    return chr(127397 + ord(country_code[0].upper())) + chr(127397 + ord(country_code[1].upper()))

# Название страны по коду
def get_country_name(code: str) -> str:
    """
    Возвращает полное название страны по её коду.
    """
    return country_name_map.get(code.upper(), code)

# ---------- Инициализация FastAPI и Jinja2 ----------

app = FastAPI()

# Указываем папку с шаблонами
templates = Jinja2Templates(directory="templates")

# Регистрируем пользовательские фильтры
templates.env.filters["country_name"] = get_country_name
templates.env.filters["get_flag"] = get_flag

# Создаём таблицы в БД (если ещё не созданы)
Base.metadata.create_all(bind=engine)

# Подключаем маршруты
app.include_router(ticket.router)

# Подключение статики
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploaded_tickets", StaticFiles(directory="uploaded_tickets"), name="uploaded_tickets")

# ---------- Главные страницы ----------

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Отображает главную страницу с билетами.
    """
    return templates.TemplateResponse("all_tickets.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """
    Отображает админ-панель.
    """
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})
