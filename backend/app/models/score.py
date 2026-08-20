"""Score model for tracking team scores per round."""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Float, ForeignKey
from sqlalchemy import Uuid as UUID
from app.database import Base


class Score(Base):
    __tablename__ = "scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    round_id = Column(UUID(as_uuid=True), ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False)
    total_score = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)
    bingo_count = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    avg_response_time = Column(Float, default=0.0)
    completion_percentage = Column(Float, default=0.0)
    fastest_correct_bonus = Column(Integer, default=0)
    hard_question_bonus = Column(Integer, default=0)
    perfect_round_bonus = Column(Integer, default=0)
    completion_time = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
