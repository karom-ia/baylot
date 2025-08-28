from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.utils.template_engine import templates
from app.database.db import Base, engine, SessionLocal, get_db
from app.models.ticket import Ticket
from app.routers import ticket
from app.utils.country_names import country_name_map
import os

print("DATABASE_URL:", os.getenv("DATABASE_URL"))

def get_country_name(code: str):
    return country_name_map.get(code.upper(), code)

templates.env.filters["country_name"] = get_country_name

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(ticket.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploaded_tickets", StaticFiles(directory="uploaded_tickets"), name="uploaded_tickets")


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


@app.get("/admin")
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})
