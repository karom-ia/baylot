from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class TicketSchema(BaseModel):
    id: UUID
    ticket_number: str
    holder_info: Optional[str]
    social_link: Optional[str]
    wallet_address: Optional[str]
    image_url: Optional[str]
    is_winner: bool
    is_featured: bool
    status: str
    prize_description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
