from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.utils.template_engine import templates
from app.database.db import Base, engine, get_db
from app.models.ticket import Ticket
from app.routers import ticket
from app.utils.country_names import country_name_map

from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import secrets
import os
from dotenv import load_dotenv

# ✅ Явно указываем путь к .env (внутри папки app)
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

# --- ЛОГ ---
print("🔐 Загрузка .env из:", dotenv_path)
print("🔐 DOCS_USERNAME:", os.getenv("DOCS_USERNAME"))
print("🔐 DOCS_PASSWORD:", "✔️" if os.getenv("DOCS_PASSWORD") else "❌ Не задано")

# 🔐 Защита DOCS
DOCS_USERNAME = os.getenv("DOCS_USERNAME")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD")
security = HTTPBasic()

def protect_docs(credentials: HTTPBasicCredentials = Depends(security)):
    if not DOCS_USERNAME or not DOCS_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail="DOCS_USERNAME и DOCS_PASSWORD не заданы в .env"
        )
    correct_username = secrets.compare_digest(credentials.username, DOCS_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, DOCS_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные",
            headers={"WWW-Authenticate": "Basic"},
        )

# 🎯 Приложение
app = FastAPI(
    docs_url=None,
    redoc_url=None
)

# --- Фильтры шаблона ---
def get_country_name(code: str):
    return country_name_map.get(code.upper(), code)

templates.env.filters["country_name"] = get_country_name

# --- Инициализация базы ---
Base.metadata.create_all(bind=engine)

# --- Роутеры и статика ---
app.include_router(ticket.router)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploaded_tickets", StaticFiles(directory="uploaded_tickets"), name="uploaded_tickets")

# --- Защищённый доступ к документации ---
@app.get("/docs", include_in_schema=False)
def custom_swagger_ui(credentials: HTTPBasicCredentials = Depends(protect_docs)):
    return get_swagger_ui_html(openapi_url=app.openapi_url, title="Metabase API Docs")

@app.get("/redoc", include_in_schema=False)
def custom_redoc(credentials: HTTPBasicCredentials = Depends(protect_docs)):
    return get_redoc_html(openapi_url=app.openapi_url, title="Metabase API Redoc")

# --- Главная страница ---
@app.get("/")
async def read_root(request: Request, db: Session = Depends(get_db)):
    tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
    featured_tickets = db.query(Ticket).filter(Ticket.is_featured == True).all()
    return templates.TemplateResponse("all_tickets.html", {
        "request": request,
        "tickets": tickets,
        "featured_tickets": featured_tickets,
        "number": None,
        "winners_only": False,
        "found": None,
    })

# --- Страницы ---
@app.get("/admin")
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})
