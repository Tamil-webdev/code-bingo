"""Round and RoundParticipant models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class RoundStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MIXED = "mixed"


class Round(Base):
    __tablename__ = "rounds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    order = Column(Integer, nullable=False, default=0)
    board_size = Column(Integer, default=5)  # 3, 4, 5, or 6
    timer_seconds = Column(Integer, default=600)  # 10 minutes default
    difficulty = Column(SAEnum(Difficulty), default=Difficulty.MIXED)
    num_questions = Column(Integer, default=25)
    qualification_count = Column(Integer, default=10)
    status = Column(SAEnum(RoundStatus), default=RoundStatus.PENDING)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tournament = relationship("Tournament", back_populates="rounds")
    participants = relationship("RoundParticipant", back_populates="round", cascade="all, delete-orphan")


class RoundParticipant(Base):
    __tablename__ = "round_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    round_id = Column(UUID(as_uuid=True), ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    is_qualified = Column(Integer, default=0)  # 0=pending, 1=qualified, -1=eliminated
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    round = relationship("Round", back_populates="participants")
    team = relationship("Team")
