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

# Жёстко прописанные логин и пароль
DOCS_USERNAME = "admin"
DOCS_PASSWORD = "secre123"
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

# Пересоздаем таблицы с нуля
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

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
    db: Session = Depends(get_db),
    status: bool = False,
    support: bool = False,
    about: bool = False,
    archiv: bool = False
):
    # Просто все билеты
    tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
    featured_tickets = db.query(Ticket).filter(Ticket.is_featured == True).all()
    
    return templates.TemplateResponse("all_tickets.html", {
        "request": request,
        "tickets": tickets,
        "featured_tickets": featured_tickets,
        "archived_tickets": [],
        "number": None,
        "winners_only": False,
        "found": None,
        "status_page": status,
        "support_page": support,
        "about_page": about,
        "archiv_page": archiv,
    })

@app.get("/tickets/all/html")
async def get_all_tickets_html(
    request: Request,
    db: Session = Depends(get_db),
    number: str = None,
    winners_only: bool = False,
    status: bool = False,
    support: bool = False,
    about: bool = False,
    archiv: bool = False
):
    query = db.query(Ticket)
    
    if number:
        query = query.filter(Ticket.ticket_number.ilike(f"%{number}%"))
    
    if winners_only:
        query = query.filter(Ticket.is_winner == True)
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    featured_tickets = db.query(Ticket).filter(Ticket.is_featured == True).all()
    
    found = None
    if number:
        found = any(number.lower() in ticket.ticket_number.lower() for ticket in tickets)
    
    return templates.TemplateResponse("all_tickets.html", {
        "request": request,
        "tickets": tickets,
        "featured_tickets": featured_tickets,
        "archived_tickets": [],
        "number": number,
        "winners_only": winners_only,
        "found": found,
        "status_page": status,
        "support_page": support,
        "about_page": about,
        "archiv_page": archiv,
    })

@app.get("/admin")
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    winner_tickets = db.query(Ticket).filter(Ticket.is_winner == True).order_by(Ticket.created_at.desc()).all()
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "winner_tickets": winner_tickets
    })