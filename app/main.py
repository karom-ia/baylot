# app/main.py

from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database.db import Base, engine, get_db
from app.models.ticket import Ticket
from app.routers import ticket
from app.utils.country_names import country_name_map
import os
import traceback
from typing import Optional
from pathlib import Path

def get_country_name(code: str):
    """Возвращает полное название страны по её коду."""
    return country_name_map.get(code.upper(), code)

# Инициализация шаблонов
templates = Jinja2Templates(directory="templates")
templates.env.filters["country_name"] = get_country_name

app = FastAPI()

# Создание таблиц в базе данных
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы базы данных успешно созданы")
except Exception as e:
    print(f"❌ Ошибка при создании таблиц: {e}")
    traceback.print_exc()

# Подключение роутеров и статических файлов
app.include_router(ticket.router)

# Создаем директории для статических файлов, если они не существуют
Path("static").mkdir(exist_ok=True)
Path("uploaded_tickets").mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploaded_tickets", StaticFiles(directory="uploaded_tickets"), name="uploaded_tickets")

# Главная страница со всеми билетами
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    try:
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
    except SQLAlchemyError as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Ошибка при загрузке билетов")

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
    try:
        # Проверяем, существует ли билет с таким номером
        existing_ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()
        if existing_ticket:
            raise HTTPException(status_code=400, detail="Билет с таким номером уже существует")

        # Сохраняем изображение
        upload_dir = "uploaded_tickets"
        Path(upload_dir).mkdir(exist_ok=True)
        
        # Генерируем уникальное имя файла
        file_ext = Path(file.filename).suffix
        new_filename = f"{ticket_number}{file_ext}"
        file_location = f"{upload_dir}/{new_filename}"
        
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
            image_url=f"/uploaded_tickets/{new_filename}"
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
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Поиск билетов
@app.get("/tickets/all/html", response_class=HTMLResponse)
async def all_tickets_html(
    request: Request,
    number: Optional[str] = None,
    winners_only: bool = False,
    db: Session = Depends(get_db)
):
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
    except SQLAlchemyError as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Ошибка при поиске билетов")

# Админ-панель
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

# Дополнительные маршруты для админки
@app.get("/admin/create-ticket", response_class=HTMLResponse)
async def admin_create_ticket(request: Request):
    return templates.TemplateResponse("create_ticket.html", {"request": request})

@app.get("/admin/search-ticket", response_class=HTMLResponse)
async def admin_search_ticket(request: Request):
    return templates.TemplateResponse("search_form.html", {"request": request})

@app.get("/admin/winners", response_class=HTMLResponse)
async def admin_winners(request: Request, db: Session = Depends(get_db)):
    try:
        tickets = db.query(Ticket).filter(Ticket.is_winner == True).order_by(Ticket.id.desc()).all()
        return templates.TemplateResponse("all_tickets.html", {
            "request": request,
            "tickets": tickets,
            "featured_tickets": [],
            "winners_only": True
        })
    except SQLAlchemyError as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Ошибка при загрузке победителей")

# Диагностический маршрут
@app.get("/health-check")
async def health_check(db: Session = Depends(get_db)):
    try:
        ticket_count = db.query(Ticket).count()
        return {
            "status": "healthy",
            "ticket_count": ticket_count,
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))