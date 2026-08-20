"""Leaderboard entry model for real-time ranking."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship
from app.database import Base


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    round_id = Column(UUID(as_uuid=True), ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    rank = Column(Integer, default=0)
    team_name = Column(String(200), nullable=False)
    score = Column(Integer, default=0)
    bingo_count = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    completion_percentage = Column(Float, default=0.0)
    avg_time = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team")
    round = relationship("Round")
