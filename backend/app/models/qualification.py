"""Qualification model for tracking team advancement."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy import Uuid as UUID
from app.database import Base
import enum


class QualificationStatus(str, enum.Enum):
    PENDING = "pending"
    QUALIFIED = "qualified"
    ELIMINATED = "eliminated"


class Qualification(Base):
    __tablename__ = "qualifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    round_id = Column(UUID(as_uuid=True), ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    status = Column(SAEnum(QualificationStatus), default=QualificationStatus.PENDING)
    final_rank = Column(Integer, nullable=True)
    final_score = Column(Integer, default=0)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
