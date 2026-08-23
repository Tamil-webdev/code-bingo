"""Tournament model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, Enum as SAEnum
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TournamentStatus(str, enum.Enum):
    DRAFT = "draft"
    REGISTRATION = "registration"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(300), nullable=False)
    room_code = Column(String(12), unique=True, nullable=True, index=True)
    description = Column(Text, nullable=True)
    status = Column(SAEnum(TournamentStatus), default=TournamentStatus.DRAFT)
    registration_start = Column(DateTime, nullable=True)
    registration_end = Column(DateTime, nullable=True)
    max_teams = Column(Integer, default=50)
    num_rounds = Column(Integer, default=3)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rounds = relationship("Round", back_populates="tournament", cascade="all, delete-orphan", order_by="Round.order")
