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

templates = Jinja2Templates(directory="templates")
templates.env.filters["country_name"] = get_country_name

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(ticket.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploaded_tickets", StaticFiles(directory="uploaded_tickets"), name="uploaded_tickets")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Корневой маршрут: отображает список всех билетов.
    """
    return templates.TemplateResponse("all_tickets.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """
    Маршрут для дашборда.
    """
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

# ---- НОВЫЙ КОД: МАРШРУТ ДЛЯ СОЗДАНИЯ БИЛЕТА ----
@app.get("/create_ticket", response_class=HTMLResponse)
async def create_ticket_page(request: Request):
    """
    Маршрут для страницы создания нового билета.
    """
    return templates.TemplateResponse("create_ticket.html", {"request": request})
# ---------------------------------------------------
