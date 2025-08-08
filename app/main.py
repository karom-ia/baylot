# app/main.py

from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.db import Base, engine, get_db
from app.models.ticket import Ticket
from pathlib import Path
import os
from typing import Optional
import traceback
from pydantic import BaseModel, HttpUrl

# **Важно:** Замените этот ключ на свой собственный, надежный пароль
ADMIN_KEY = "MySuperSecretKeyForDelete2233"

def get_country_name(code: str):
    """Возвращает полное название страны по её коду."""
    try:
        from app.utils.country_names import country_name_map
        return country_name_map.get(code.upper(), code)
    except ImportError:
        return code

# Инициализация приложения
app = FastAPI()

# Настройка шаблонов Jinja2
templates = Jinja2Templates(directory="templates")
templates.env.filters["country_name"] = get_country_name

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

# Настройка папок для статических файлов и загрузок
static_dir = Path("static")
upload_dir = Path("uploaded_tickets")

# Создание папок, если их нет
static_dir.mkdir(exist_ok=True)
upload_dir.mkdir(exist_ok=True)

# Монтирование статических директорий
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/uploaded_tickets", StaticFiles(directory=upload_dir), name="uploaded_tickets")

# Главная страница - показывает все билеты
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
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

# Админ-панель
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

# Страница с формой для создания билета
@app.get("/admin/create-ticket", response_class=HTMLResponse)
async def create_ticket_form(request: Request):
    return templates.TemplateResponse("create_ticket.html", {"request": request})

# Новый маршрут для обработки формы
@app.post("/admin/create-ticket")
async def create_ticket_from_form(
    request: Request,
    admin_key: str = Form(...),
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
    # Проверка ключа администратора
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid admin key")

    try:
        if db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first():
            raise HTTPException(status_code=400, detail="Билет с таким номером уже существует")

        file_ext = Path(file.filename).suffix
        new_filename = f"{ticket_number}{file_ext}"
        file_path = upload_dir / new_filename
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

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

        return RedirectResponse(url="/admin", status_code=303)
        
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Pydantic модель для API
class TicketCreateAPI(BaseModel):
    ticket_number: str
    holder_info: Optional[str] = None
    social_link: Optional[str] = None
    wallet_address: Optional[str] = None
    country_code: Optional[str] = None
    is_winner: bool = False
    prize_description: Optional[str] = None
    image_url: HttpUrl

# Маршрут для API (если нужно создавать билеты не из формы, а через JSON)
@app.post("/admin/create-ticket/{admin_key}")
async def create_ticket_api(
    admin_key: str,
    ticket: TicketCreateAPI,
    db: Session = Depends(get_db)
):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid admin key")

    try:
        if db.query(Ticket).filter(Ticket.ticket_number == ticket.ticket_number).first():
            raise HTTPException(status_code=400, detail="Билет с таким номером уже существует")
        
        new_ticket = Ticket(
            ticket_number=ticket.ticket_number,
            holder_info=ticket.holder_info,
            social_link=ticket.social_link,
            wallet_address=ticket.wallet_address,
            country_code=ticket.country_code,
            is_winner=ticket.is_winner,
            prize_description=ticket.prize_description,
            image_url=ticket.image_url
        )

        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)

        return {"message": "Ticket created successfully", "ticket_id": new_ticket.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ticket/{ticket_id}", response_class=HTMLResponse)
async def view_ticket(ticket_id: int, request: Request, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Билет не найден")
    return templates.TemplateResponse("ticket_view.html", {"request": request, "ticket": ticket})

@app.get("/admin/winners", response_class=HTMLResponse)
async def admin_winners(request: Request, db: Session = Depends(get_db)):
    tickets = db.query(Ticket).filter(Ticket.is_winner == True).order_by(Ticket.id.desc()).all()
    return templates.TemplateResponse("all_tickets.html", {
        "request": request,
        "tickets": tickets,
        "featured_tickets": [],
        "winners_only": True
    })

@app.get("/admin/search-ticket", response_class=HTMLResponse)
async def admin_search_ticket(request: Request):
    return templates.TemplateResponse("search_form.html", {"request": request})
