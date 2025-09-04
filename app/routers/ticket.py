from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile,
    File, Form, Query, Request, Header
)
from fastapi.responses import HTMLResponse
from app.utils.template_engine import templates
from sqlalchemy.orm import Session
from app.database.db import SessionLocal
from app.models.ticket import Ticket
from fastapi.responses import JSONResponse
from fastapi import Request
from app.schemas.ticket import TicketSchema
import shutil
import os
from uuid import uuid4, UUID
from werkzeug.utils import secure_filename
import httpx
from pydantic import BaseModel
from datetime import datetime
from app.config import ADMIN_KEY, SOLANA_WALLET_ADDRESS  # Импортируем из config

router = APIRouter(prefix="/tickets", tags=["Tickets"])

UPLOAD_DIR = "uploaded_tickets"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Новый маршрут для проверки транзакции
@router.get("/check-transaction")
async def check_transaction(tx_hash: str):
    """
    Проверяет транзакцию в блокчейне Solana на валидность.
    """
    SOLANA_API_URL = "https://api.mainnet-beta.solana.com"
    required_amount_lamports = 500_000_000  # 1 SOL = 1,000,000,000 Lamports

    if not tx_hash:
        raise HTTPException(status_code=400, detail="Transaction hash is missing.")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SOLANA_API_URL,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getConfirmedTransaction",
                    "params": [tx_hash]
                }
            )
            response.raise_for_status()
            tx_data = response.json().get("result")

            if not tx_data:
                raise HTTPException(status_code=404, detail="Transaction not found.")

            # Проверка получателя и суммы
            is_valid = False
            for instruction in tx_data['transaction']['message']['instructions']:
                if (
                    instruction.get('programId') == '11111111111111111111111111111111'
                    and instruction.get('parsed', {}).get('info', {}).get('destination') == SOLANA_WALLET_ADDRESS
                    and instruction.get('parsed', {}).get('info', {}).get('lamports') >= required_amount_lamports
                ):
                    is_valid = True
                    break

            if is_valid:
                return {"status": "success", "detail": "Transaction is valid."}
            else:
                raise HTTPException(status_code=400, detail="Transaction is not valid or does not meet the requirements (1 SOL to the correct address).")

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP Error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.post("/create")
async def create_ticket(
    request: Request,
    admin_key: str = Query(...),
    ticket_number: str = Form(...),
    holder_info: str = Form(None),
    social_link: str = Form(None),
    wallet_address: str = Form(None),
    country_code: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    filename = secure_filename(f"{uuid4().hex}_{file.filename}")
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_url = f"/{UPLOAD_DIR}/{filename}"

    new_ticket = Ticket(
        ticket_number=ticket_number.replace("baylot:", "").strip(),
        holder_info=holder_info,
        social_link=social_link,
        wallet_address=wallet_address,
        image_url=image_url,
        country_code=country_code,
        status="active"
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse("ticket_success.html", {
            "request": request,
            "ticket": new_ticket
        })
    else:
        return JSONResponse(content={
            "id": str(new_ticket.id),
            "ticket_number": new_ticket.ticket_number,
            "holder_info": new_ticket.holder_info,
            "social_link": new_ticket.social_link,
            "wallet_address": new_ticket.wallet_address,
            "image_url": new_ticket.image_url,
            "is_winner": new_ticket.is_winner,
            "is_featured": new_ticket.is_featured,
            "status": new_ticket.status,
            "prize_description": new_ticket.prize_description,
            "created_at": new_ticket.created_at.isoformat(),
        })

# Остальные функции остаются без изменений, но используют ADMIN_KEY из config...
# [Остальной код остается таким же, но везде заменяем ADMIN_KEY на импортированную переменную]