import os
import shutil
from uuid import uuid4, UUID
from datetime import datetime

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile,
    File, Form, Query, Request, Header
)
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename
import httpx
from dotenv import load_dotenv

from app.database.db import SessionLocal
from app.models.ticket import Ticket
from app.utils.template_engine import templates
from app.schemas.ticket import TicketSchema
from starlette.status import HTTP_303_SEE_OTHER

# Загружаем переменные из .env
load_dotenv()

# 🔐 Секреты из .env
ADMIN_KEY = os.getenv("ADMIN_KEY")
SOLANA_WALLET_ADDRESS = os.getenv("SOLANA_WALLET_ADDRESS")

router = APIRouter(prefix="/tickets", tags=["Tickets"])
UPLOAD_DIR = "uploaded_tickets"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/check-transaction")
async def check_transaction(tx_hash: str):
    SOLANA_API_URL = "https://api.mainnet-beta.solana.com"
    required_amount_lamports = 500_000_000

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

# 🔒 Все остальные места с admin_key...
# ВНИМАНИЕ: повторяется в каждом методе — сравнение с ADMIN_KEY
# Ниже примеры (оставшиеся функции не менялись, кроме использования ADMIN_KEY):

@router.post("/{ticket_id}/archive")
def archive_ticket(
    ticket_id: UUID,
    admin_key: str = Query(...),
    db: Session = Depends(get_db)
):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if not ticket.is_winner:
        raise HTTPException(status_code=400, detail="Only winner tickets can be archived")

    ticket.is_archived = True
    ticket.archived_at = datetime.now()
    db.commit()

    return {"message": "Ticket archived successfully", "ticket_id": ticket_id}

# 🔑 Пример для заголовка:
@router.delete("/all/", response_model=dict)
def delete_all_tickets(x_admin_key: str = Header(...), db: Session = Depends(get_db)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Access denied: Invalid admin key")

    deleted_count = db.query(Ticket).filter(Ticket.is_archived == False).delete()
    db.commit()

    return {
        "status": "success", 
        "deleted_count": deleted_count,
        "message": f"Deleted {deleted_count} non-archived tickets. Archived tickets were preserved."
    }

# ❗ Продолжи использовать `ADMIN_KEY` и `SOLANA_WALLET_ADDRESS` из .env во всех местах — они уже подгружены.
