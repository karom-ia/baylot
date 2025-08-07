# app/main.py

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database.db import Base, engine
from app.models.ticket import Ticket
from app.routers import ticket
from app.utils.country_names import country_name_map

def get_country_name(code: str):
    """
    Возвращает полное название страны по её коду.
    """
    return country_name_map.get(code.upper(), code)

# Объявляем, где находятся ваши HTML-файлы
# Убедитесь, что папка 'templates' существует и содержит ваши HTML-файлы.
templates = Jinja2Templates(directory="templates")

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


# ---- ИЗМЕНЁННЫЙ КОД: ГЛАВНАЯ СТРАНИЦА ПОКАЗЫВАЕТ ВАШ ОСНОВНОЙ САЙТ (all_tickets.html) ----

# Корень: отображает ваш основной HTML-файл (all_tickets.html)
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Обрабатывает запросы к корневому URL (например, http://www.metabase.info/).
    Возвращает ваш основной HTML-файл сайта (all_tickets.html).
    """
    return templates.TemplateResponse("all_tickets.html", {"request": request})

# -------------------------------------------------------------------------------------

# Админка: теперь дашборд будет доступен по адресу /admin
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """
    Обрабатывает запросы к URL дашборда (например, http://www.metabase.info/admin).
    Возвращает HTML-файл админ-панели управления билетами (admin_dashboard.html).
    """
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

