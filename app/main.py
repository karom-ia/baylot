# app/main.py

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database.db import Base, engine
from app.models.ticket import Ticket
from app.routers import ticket
from app.utils.country_names import country_name_map
from sqlalchemy.orm import Session
from app.database.db import get_db

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

# Измененный корневой маршрут - теперь он получает билеты из базы данных
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    db: Session = next(get_db())
    try:
        # Получаем все билеты из базы данных
        tickets = db.query(Ticket).order_by(Ticket.id.desc()).all()
        
        # Получаем билеты-победители для выделенного отображения
        featured_tickets = db.query(Ticket).filter(Ticket.is_winner == True).order_by(Ticket.id.desc()).all()
        
        return templates.TemplateResponse(
            "all_tickets.html",
            {
                "request": request,
                "tickets": tickets,
                "featured_tickets": featured_tickets,
                "winners_only": False
            }
        )
    finally:
        db.close()

# Маршрут для поиска билетов
@app.get("/tickets/all/html", response_class=HTMLResponse)
async def all_tickets_html(
    request: Request,
    number: str = None,
    winners_only: bool = False
):
    db: Session = next(get_db())
    try:
        query = db.query(Ticket)
        found = None
        
        if number:
            query = query.filter(Ticket.ticket_number.contains(number))
            found = query.first() is not None
        
        if winners_only:
            query = query.filter(Ticket.is_winner == True)
        
        tickets = query.order_by(Ticket.id.desc()).all()
        featured_tickets = []
        
        return templates.TemplateResponse(
            "all_tickets.html",
            {
                "request": request,
                "tickets": tickets,
                "featured_tickets": featured_tickets,
                "winners_only": winners_only,
                "number": number,
                "found": found
            }
        )
    finally:
        db.close()

# Маршрут для получения количества билетов (используется в AJAX запросе)
@app.get("/tickets/count")
async def get_tickets_count():
    db: Session = next(get_db())
    try:
        count = db.query(Ticket).count()
        return {"count": count}
    finally:
        db.close()

# Админка
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})