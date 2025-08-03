# app/main.py

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from app.utils.template_engine import templates
from app.database.db import Base, engine
from app.models.ticket import Ticket
from app.routers import ticket
from app.utils.template_engine import templates  # готовый с фильтром
from app.utils.country_names import country_name_map

def get_country_name(code: str):
    return country_name_map.get(code.upper(), code)

templates.env.filters["country_name"] = get_country_name


app = FastAPI()

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Подключение роутеров
app.include_router(ticket.router)

# Статика
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploaded_tickets", StaticFiles(directory="uploaded_tickets"), name="uploaded_tickets")



# Корень
@app.get("/")
def read_root():
    return {"message": "Ticket System API работает!"}

# Админка
@app.get("/admin")
def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})
