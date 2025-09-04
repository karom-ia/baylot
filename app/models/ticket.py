import uuid
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.database.db import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number = Column(String, unique=True, index=True, nullable=False)
    country_code = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    status = Column(String, default="active")
    is_winner = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)  # ✅ Должно быть
    holder_info = Column(String, nullable=True)
    prize_description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    archived_at = Column(DateTime(timezone=True), nullable=True)  # ✅ Должно быть
    social_link = Column(String, nullable=True)
    wallet_address = Column(String, nullable=True)