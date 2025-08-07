# app/main.py

from fastapi import FastAPI, Request, Form, UploadFile, File, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.db import Base, engine, get_db
from app.models.ticket import Ticket
from app.routers import ticket
from app.utils.country_names import country_name_map
import os
from typing import Optional

def get_country_name(code: str):
    """Возвращает полное название страны по её коду."""
    return country_name_map.get(code.upper(), code)

templates = Jinja2Templates(directory="templates")
templates.env.filters["country_name"] = get_country_name

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(ticket.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploaded_tickets", StaticFiles(directory="uploaded_tickets"), name="uploaded_tickets")

# Главная страница со всеми билетами
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    tickets = db.query(Ticket).order_by(Ticket.id.desc()).all()
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

# Форма создания билета
@app.get("/tickets/add", response_class=HTMLResponse)
async def add_ticket_form(request: Request):
    return templates.TemplateResponse("create_ticket.html", {"request": request})

# Обработка создания билета
@app.post("/tickets/create")
async def create_ticket(
    request: Request,
    ticket_number: str = Form(...),
    holder_info: Optional[str] = Form(None),
    social_link: Optional[str] = Form(None),
    wallet_address: Optional[str] = Form(None),
    country_code: Optional[str] = Form(None),
    is_winner: bool = Form(False),
    prize_description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Сохраняем изображение
    upload_dir = "uploaded_tickets"
    os.makedirs(upload_dir, exist_ok=True)
    file_location = f"{upload_dir}/{file.filename}"
    
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    
    # Создаем билет в базе данных
    ticket = Ticket(
        ticket_number=ticket_number,
        holder_info=holder_info,
        social_link=social_link,
        wallet_address=wallet_address,
        country_code=country_code,
        is_winner=is_winner,
        prize_description=prize_description,
        image_url=f"/uploaded_tickets/{file.filename}"
    )
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    return templates.TemplateResponse(
        "ticket_success.html",
        {
            "request": request,
            "ticket": ticket,
            "status": "Активен"
        }
    )

# Поиск билетов
@app.get("/tickets/all/html", response_class=HTMLResponse)
async def all_tickets_html(
    request: Request,
    number: Optional[str] = None,
    winners_only: bool = False,
    db: Session = Depends(get_db)
):
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

# Форма поиска билета
@app.get("/tickets/search/html", response_class=HTMLResponse)
async def search_ticket_form(request: Request):
    return templates.TemplateResponse("search_form.html", {"request": request})

# Результаты поиска билета
@app.get("/tickets/search/result", response_class=HTMLResponse)
async def search_ticket_result(
    request: Request,
    number: str,
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.ticket_number == number).first()
    
    return templates.TemplateResponse(
        "search_result.html",
        {
            "request": request,
            "ticket": ticket,
            "not_found": ticket is None
        }
    )

# Список победителей
@app.get("/tickets/winners/html", response_class=HTMLResponse)
async def winners_list(request: Request, db: Session = Depends(get_db)):
    tickets = db.query(Ticket).filter(Ticket.is_winner == True).order_by(Ticket.id.desc()).all()
    
    return templates.TemplateResponse(
        "all_tickets.html",
        {
            "request": request,
            "tickets": tickets,
            "featured_tickets": [],
            "winners_only": True
        }
    )

# Количество билетов (для AJAX)
@app.get("/tickets/count")
async def get_tickets_count(db: Session = Depends(get_db)):
    count = db.query(Ticket).count()
    return {"count": count}

# Админ-панель
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

    # Админ-панель
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

# Форма создания билета в админке
@app.get("/admin/create-ticket", response_class=HTMLResponse)
async def admin_create_ticket(request: Request):
    return templates.TemplateResponse("create_ticket.html", {"request": request})

# Поиск билетов в админке
@app.get("/admin/search-ticket", response_class=HTMLResponse)
async def admin_search_ticket(request: Request):
    return templates.TemplateResponse("search_form.html", {"request": request})

# Список победителей в админке
@app.get("/admin/winners", response_class=HTMLResponse)
async def admin_winners(request: Request, db: Session = Depends(get_db)):
    tickets = db.query(Ticket).filter(Ticket.is_winner == True).order_by(Ticket.id.desc()).all()
    return templates.TemplateResponse("all_tickets.html", {
        "request": request,
        "tickets": tickets,
        "featured_tickets": [],
        "winners_only": True
    })