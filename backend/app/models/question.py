"""Question and QuestionOption models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    GUESS_OUTPUT = "guess_output"
    FILL_BLANK = "fill_blank"
    TRUE_FALSE = "true_false"
    DEBUG_CODE = "debug_code"
    ARRANGE_CODE = "arrange_code"
    SELECT_COMPLEXITY = "select_complexity"
    CODE_TRACING = "code_tracing"


class QuestionDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ProgrammingLanguage(str, enum.Enum):
    PYTHON = "python"
    JAVA = "java"
    C = "c"
    CPP = "cpp"
    SQL = "sql"
    HTML = "html"
    JAVASCRIPT = "javascript"
    MIXED = "mixed"


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_text = Column(Text, nullable=False)
    code_snippet = Column(Text, nullable=True)
    question_type = Column(SAEnum(QuestionType), nullable=False)
    language = Column(SAEnum(ProgrammingLanguage), nullable=False)
    difficulty = Column(SAEnum(QuestionDifficulty), nullable=False)
    correct_answer = Column(String(500), nullable=False)
    explanation = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    time_limit = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan", order_by="QuestionOption.order")


class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(Text, nullable=False)
    option_label = Column(String(10), nullable=False)  # A, B, C, D
    is_correct = Column(Boolean, default=False)
    order = Column(Integer, default=0)

    # Relationships
    question = relationship("Question", back_populates="options")
