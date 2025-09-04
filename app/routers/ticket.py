from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile,
    File, Form, Query, Request, Header
)
from fastapi.responses import HTMLResponse, JSONResponse
from app.utils.template_engine import templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.db import get_db
from app.models.ticket import Ticket
from app.schemas.ticket import TicketSchema
import shutil
import os
from uuid import uuid4, UUID
from werkzeug.utils import secure_filename
import httpx
from datetime import datetime
from app.config import ADMIN_KEY, SOLANA_WALLET_ADDRESS

router = APIRouter(prefix="/tickets", tags=["Tickets"])

UPLOAD_DIR = "uploaded_tickets"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ Новый маршрут для проверки транзакции
@router.get("/check-transaction")
async def check_transaction(tx_hash: str):
    """
    Проверяет транзакцию в блокчейне Solana на валидность.
    """
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
    db: AsyncSession = Depends(get_db)
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
    await db.commit()
    await db.refresh(new_ticket)

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

@router.post("/{ticket_id}/archive")
async def archive_ticket(
    ticket_id: UUID,
    admin_key: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await db.execute(select(Ticket).filter(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if not ticket.is_winner:
        raise HTTPException(status_code=400, detail="Only winner tickets can be archived")
    
    ticket.is_archived = True
    ticket.archived_at = datetime.now()
    await db.commit()
    
    return {"message": "Ticket archived successfully", "ticket_id": ticket_id}

@router.post("/{ticket_id}/unarchive")
async def unarchive_ticket(
    ticket_id: UUID,
    admin_key: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await db.execute(select(Ticket).filter(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.is_archived = False
    ticket.archived_at = None
    await db.commit()
    
    return {"message": "Ticket unarchived successfully", "ticket_id": ticket_id}

@router.get("/search")
async def search_ticket(number: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).filter(
        Ticket.ticket_number == number,
        Ticket.is_archived == False
    ))
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.put("/{ticket_number}/winner")
async def declare_winner(
    ticket_number: str,
    prize_description: str = Query(...),
    admin_key: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await db.execute(select(Ticket).filter(
        Ticket.ticket_number == ticket_number,
        Ticket.is_archived == False
    ))
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.is_winner = True
    ticket.status = "winner"
    ticket.prize_description = prize_description
    await db.commit()
    await db.refresh(ticket)
    
    return {
        "detail": f"Ticket '{ticket_number}' marked as winner",
        "prize": prize_description
    }

@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: UUID,
    admin_key: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await db.execute(select(Ticket).filter(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    image_path = ticket.image_url.lstrip("/")
    if os.path.exists(image_path):
        os.remove(image_path)

    await db.delete(ticket)
    await db.commit()
    
    return {
        "detail": f"Ticket {ticket_id} deleted",
        "archived": ticket.is_archived
    }

@router.delete("/all/", response_model=dict)
async def delete_all_tickets(x_admin_key: str = Header(...), db: AsyncSession = Depends(get_db)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Access denied: Invalid admin key")

    result = await db.execute(select(Ticket).filter(Ticket.is_archived == False))
    tickets = result.scalars().all()
    
    for ticket in tickets:
        await db.delete(ticket)
    
    await db.commit()
    
    return {
        "status": "success", 
        "deleted_count": len(tickets),
        "message": f"Deleted {len(tickets)} non-archived tickets. Archived tickets were preserved."
    }

@router.delete("/archived/all/", response_model=dict)
async def delete_all_archived_tickets(x_admin_key: str = Header(...), db: AsyncSession = Depends(get_db)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Access denied: Invalid admin key")

    result = await db.execute(select(Ticket).filter(Ticket.is_archived == True))
    tickets = result.scalars().all()
    
    for ticket in tickets:
        await db.delete(ticket)
    
    await db.commit()
    
    return {
        "status": "success", 
        "deleted_count": len(tickets),
        "message": f"Deleted {len(tickets)} archived tickets."
    }

@router.delete("/archived/{ticket_id}")
async def delete_archived_ticket(
    ticket_id: UUID,
    x_admin_key: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Access denied: Invalid admin key")

    result = await db.execute(select(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.is_archived == True
    ))
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Archived ticket not found")

    image_path = ticket.image_url.lstrip("/")
    if os.path.exists(image_path):
        os.remove(image_path)

    await db.delete(ticket)
    await db.commit()
    
    return {
        "detail": f"Archived ticket {ticket_id} deleted",
        "message": "Archived ticket was permanently deleted"
    }

@router.get("/winners/html", response_class=HTMLResponse)
async def show_winners(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).filter(
        Ticket.is_winner == True,
        Ticket.is_archived == False
    ).order_by(Ticket.created_at.desc()))
    winners = result.scalars().all()

    html = """
    <html>
        <head>
            <title>Победители</title>
            <style>
                body { font-family: sans-serif; background: #f8f9fa; padding: 20px; }
                .winner-list { display: flex; flex-direction: column; gap: 20px; max-width: 700px; margin: auto; }
                .winner-card {
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    padding: 15px;
                    display: flex;
                    align-items: flex-start;
                    gap: 20px;
                }
                .winner-card img {
                    max-width: 180px;
                    max-height: 180px;
                    border-radius: 8px;
                    border: 1px solid #ccc;
                }
                .ticket-number {
                    font-size: 18px;
                    font-weight: bold;
                    color: #333;
                }
                .holder-info {
                    font-size: 14px;
                    margin-top: 4px;
                    color: #555;
                }
                .created-at {
                    font-size: 14px;
                    color: #777;
                }
                .prize-info {
                    font-size: 15px;
                    color: #000;
                    margin-top: 6px;
                    font-weight: bold;
                }
                .claim-buttons a {
                    margin-right: 10px;
                    display: inline-block;
                    padding: 6px 12px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    font-size: 14px;
                }
                .claim-buttons a:hover {
                    background-color: #0056b3;
                }
            </style>
        </head>
        <body>
            <h2 style="text-align:center;">🏆 Победители</h2>
            <div class="winner-list">
    """

    for ticket in winners:
        created = ticket.created_at.strftime('%d.%m.%Y %H:%M') if ticket.created_at else "—"
        holder = ticket.holder_info or "—"
        prize = ticket.prize_description or "—"
        html += f"""
        <div class="winner-card">
            <img src="{ticket.image_url}" alt="ticket">
            <div>
                <div class="ticket-number">Билет: {ticket.ticket_number}</div>
                <div class="holder-info">Владелец: {holder}</div>
                <div class="prize-info">Приз: {prize}</div>
                <div class="created-at">Дата: {created}</div>
                <div class="claim-buttons" style="margin-top: 10px;">
                    <a href="https://t.me/BabaySupport" target="_blank">Telegram</a>
                    <a href="https://wa.me/992987654321" target="_blank">WhatsApp</a>
                    <a href="mailto:babay@support.com" target="_blank">Email</a>
                </div>
            </div>
        </div>
        """

    html += """
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html)

@router.get("/search/html", response_class=HTMLResponse)
async def search_ticket_form(request: Request):
    return templates.TemplateResponse("search_form.html", {"request": request})

@router.get("/search/result", response_class=HTMLResponse)
async def search_ticket_result(request: Request, number: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).filter(
        Ticket.ticket_number == number,
        Ticket.is_archived == False
    ))
    ticket = result.scalar_one_or_none()
    
    return templates.TemplateResponse("search_result.html", {
        "request": request,
        "ticket": ticket,
        "not_found": ticket is None
    })

@router.get("/all/html", response_class=HTMLResponse)
async def show_all_tickets(
    request: Request,
    number: str = Query(None),
    winners_only: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Ticket).filter(Ticket.is_archived == False)
    found = None

    if number:
        stmt = stmt.filter(Ticket.ticket_number.ilike(f"%{number}%"))
        result = await db.execute(stmt)
        found = result.scalars().first() is not None

    if winners_only:
        stmt = stmt.filter(Ticket.is_winner == True)

    result = await db.execute(stmt.order_by(Ticket.created_at.desc()))
    tickets = result.scalars().all()

    result = await db.execute(select(Ticket).filter(
        Ticket.is_featured == True,
        Ticket.is_archived == False
    ))
    featured_tickets = result.scalars().all()

    result = await db.execute(select(Ticket).filter(Ticket.is_archived == False))
    total_tickets_count = len(result.scalars().all())

    return templates.TemplateResponse("all_tickets.html", {
        "request": request,
        "tickets": tickets,
        "number": number,
        "winners_only": winners_only,
        "found": found,
        "featured_tickets": featured_tickets,
        "total_tickets_count": total_tickets_count
    })

@router.put("/{ticket_id}/feature")
async def feature_ticket(
    ticket_id: UUID,
    is_featured: bool = Query(...),
    admin_key: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await db.execute(select(Ticket).filter(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.is_featured = is_featured
    await db.commit()
    await db.refresh(ticket)
    
    return {"detail": f"Ticket {ticket_id} featured = {is_featured}"}

@router.get("/count")
async def get_ticket_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).filter(Ticket.is_archived == False))
    count = len(result.scalars().all())
    return {"count": count}

@router.get("/create", response_class=HTMLResponse)
async def create_ticket_form(request: Request):
    return templates.TemplateResponse("create_ticket.html", {"request": request})

@router.get("/last_ticket", response_model=TicketSchema)
async def get_last_ticket(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).filter(
        Ticket.is_archived == False
    ).order_by(Ticket.created_at.desc()))
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="No tickets found")
    return ticket

@router.get("/archived")
async def get_archived_tickets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).filter(
        Ticket.is_archived == True
    ).order_by(Ticket.archived_at.desc()))
    archived_tickets = result.scalars().all()
    return archived_tickets