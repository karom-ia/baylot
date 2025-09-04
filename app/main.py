from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.utils.template_engine import templates
from app.database.db import Base, engine, get_db
from app.models.ticket import Ticket
from app.routers import ticket
from app.utils.country_names import country_name_map
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import secrets
import logging
import os
from dotenv import load_dotenv
from pathlib import Path

# Загружаем переменные окружения
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем логин и пароль из .env
DOCS_USERNAME = os.getenv("ADMIN_USERNAME")
DOCS_PASSWORD = os.getenv("ADMIN_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY")

security = HTTPBasic()

def protect_docs(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, DOCS_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, DOCS_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные",
            headers={"WWW-Authenticate": "Basic"},
        )

app = FastAPI(
    docs_url=None,
    redoc_url=None,
)

def get_country_name(code: str):
    return country_name_map.get(code.upper(), code)
templates.env.filters["country_name"] = get_country_name

app.include_router(ticket.router)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploaded_tickets", StaticFiles(directory="uploaded_tickets"), name="uploaded_tickets")

@app.get("/docs", include_in_schema=False)
def custom_swagger_ui(credentials: HTTPBasicCredentials = Depends(protect_docs)):
    return get_swagger_ui_html(openapi_url=app.openapi_url, title="Metabase API Docs")

@app.get("/redoc", include_in_schema=False)
def custom_redoc(credentials: HTTPBasicCredentials = Depends(protect_docs)):
    return get_redoc_html(openapi_url=app.openapi_url, title="Metabase API Redoc")

@app.get("/")
async def read_root(
    request: Request, 
    db: AsyncSession = Depends(get_db),
    status: bool = False,
    support: bool = False,
    about: bool = False,
    archiv: bool = False,
    prizes: bool = False
):
    # Активные билеты (неархивированные)
    result = await db.execute(select(Ticket).filter(Ticket.is_archived == False).order_by(Ticket.created_at.desc()))
    tickets = result.scalars().all()
    
    # Избранные билеты
    result = await db.execute(select(Ticket).filter(Ticket.is_featured == True, Ticket.is_archived == False))
    featured_tickets = result.scalars().all()
    
    # Архивные билеты
    result = await db.execute(select(Ticket).filter(Ticket.is_archived == True).order_by(Ticket.archived_at.desc()))
    archived_tickets = result.scalars().all()
    
    # Отладочная информация
    logger.info(f"Active tickets: {len(tickets)}, Archived tickets: {len(archived_tickets)}")
    logger.info(f"Archived tickets IDs: {[str(t.id) for t in archived_tickets]}")
    
    return templates.TemplateResponse("all_tickets.html", {
        "request": request,
        "tickets": tickets,
        "featured_tickets": featured_tickets,
        "archived_tickets": archived_tickets,
        "number": None,
        "winners_only": False,
        "found": None,
        "status_page": status,
        "support_page": support,
        "about_page": about,
        "archiv_page": archiv,
        "prizes_page": prizes
    })

@app.get("/tickets/all/html")
async def get_all_tickets_html(
    request: Request,
    db: AsyncSession = Depends(get_db),
    number: str = None,
    winners_only: bool = False,
    status: bool = False,
    support: bool = False,
    about: bool = False,
    archiv: bool = False,
    prizes: bool = False
):
    # Базовый запрос
    stmt = select(Ticket).filter(Ticket.is_archived == False)
    
    if number:
        stmt = stmt.filter(Ticket.ticket_number.ilike(f"%{number}%"))
    
    if winners_only:
        stmt = stmt.filter(Ticket.is_winner == True)
    
    # Выполняем запрос
    result = await db.execute(stmt.order_by(Ticket.created_at.desc()))
    tickets = result.scalars().all()
    
    # Избранные билеты
    result = await db.execute(select(Ticket).filter(Ticket.is_featured == True, Ticket.is_archived == False))
    featured_tickets = result.scalars().all()
    
    # Архивные билеты
    result = await db.execute(select(Ticket).filter(Ticket.is_archived == True).order_by(Ticket.archived_at.desc()))
    archived_tickets = result.scalars().all()
    
    found = None
    if number:
        found = any(number.lower() in ticket.ticket_number.lower() for ticket in tickets)
    
    return templates.TemplateResponse("all_tickets.html", {
        "request": request,
        "tickets": tickets,
        "featured_tickets": featured_tickets,
        "archived_tickets": archived_tickets,
        "number": number,
        "winners_only": winners_only,
        "found": found,
        "status_page": status,
        "support_page": support,
        "about_page": about,
        "archiv_page": archiv,
        "prizes_page": prizes
    })

@app.get("/admin")
async def admin_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).filter(Ticket.is_winner == True).order_by(Ticket.created_at.desc()))
    winner_tickets = result.scalars().all()
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "winner_tickets": winner_tickets
    })

# Эндпоинт для получения архивных билетов (API)
@app.get("/archived-tickets")
async def get_archived_tickets_api(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).filter(Ticket.is_archived == True).order_by(Ticket.archived_at.desc()))
    archived_tickets = result.scalars().all()
    return archived_tickets

# Эндпоинт для статистики
@app.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Общее количество билетов
    result = await db.execute(select(Ticket))
    total_tickets = len(result.scalars().all())
    
    # Победители
    result = await db.execute(select(Ticket).filter(Ticket.is_winner == True))
    winner_tickets = len(result.scalars().all())
    
    # Архивные
    result = await db.execute(select(Ticket).filter(Ticket.is_archived == True))
    archived_tickets = len(result.scalars().all())
    
    # Избранные
    result = await db.execute(select(Ticket).filter(Ticket.is_featured == True))
    featured_tickets = len(result.scalars().all())
    
    return {
        "total_tickets": total_tickets,
        "winner_tickets": winner_tickets,
        "archived_tickets": archived_tickets,
        "featured_tickets": featured_tickets
    }