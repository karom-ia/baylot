# app/schemas/ticket.py

from pydantic import BaseModel, HttpUrl
from typing import Optional

# Pydantic модель для создания билета
# Используется для валидации данных, которые приходят в POST-запросе
class TicketCreateAPI(BaseModel):
    ticket_number: str
    holder_info: Optional[str] = None
    social_link: Optional[str] = None
    wallet_address: Optional[str] = None
    country_code: Optional[str] = None
    is_winner: bool = False
    prize_description: Optional[str] = None
    # image_url должен быть обязательным для API
    image_url: HttpUrl

    class Config:
        from_attributes = True

# Pydantic модель для отображения билета
# Используется для сериализации данных, отправляемых клиенту
class Ticket(BaseModel):
    id: int
    ticket_number: str
    holder_info: Optional[str] = None
    social_link: Optional[str] = None
    wallet_address: Optional[str] = None
    country_code: Optional[str] = None
    is_winner: bool
    prize_description: Optional[str] = None
    image_url: str

    class Config:
        from_attributes = True
