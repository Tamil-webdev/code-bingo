"""Board and BoardTile models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TileStatus(str, enum.Enum):
    UNANSWERED = "unanswered"
    CORRECT = "correct"
    WRONG = "wrong"
    BINGO = "bingo"


class Board(Base):
    __tablename__ = "boards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    round_id = Column(UUID(as_uuid=True), ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    size = Column(Integer, nullable=False, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    round = relationship("Round")
    team = relationship("Team")
    tiles = relationship("BoardTile", back_populates="board", cascade="all, delete-orphan", order_by="BoardTile.position")


class BoardTile(Base):
    __tablename__ = "board_tiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(UUID(as_uuid=True), ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    position = Column(Integer, nullable=False)  # 0-based index: row * size + col
    row = Column(Integer, nullable=False)
    col = Column(Integer, nullable=False)
    status = Column(SAEnum(TileStatus), default=TileStatus.UNANSWERED)
    answered_at = Column(DateTime, nullable=True)
    is_bingo_part = Column(Boolean, default=False)

    # Relationships
    board = relationship("Board", back_populates="tiles")
    question = relationship("Question")
