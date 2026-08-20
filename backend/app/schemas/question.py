"""Question schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class QuestionOptionCreate(BaseModel):
    option_text: str
    option_label: str  # A, B, C, D
    is_correct: bool = False
    order: int = 0


class QuestionOptionResponse(BaseModel):
    id: str
    option_text: str
    option_label: str
    is_correct: bool
    order: int

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    question_text: str
    code_snippet: Optional[str] = None
    question_type: str
    language: str
    difficulty: str
    correct_answer: str
    explanation: Optional[str] = None
    tags: Optional[List[str]] = []
    time_limit: int = 60
    options: List[QuestionOptionCreate] = []


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    code_snippet: Optional[str] = None
    question_type: Optional[str] = None
    language: Optional[str] = None
    difficulty: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    time_limit: Optional[int] = None
    options: Optional[List[QuestionOptionCreate]] = None


class QuestionResponse(BaseModel):
    id: str
    question_text: str
    code_snippet: Optional[str] = None
    question_type: str
    language: str
    difficulty: str
    correct_answer: str
    explanation: Optional[str] = None
    tags: List[str] = []
    time_limit: int
    is_active: bool
    options: List[QuestionOptionResponse] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuestionForTeam(BaseModel):
    """Question view for teams - hides correct answer."""
    id: str
    question_text: str
    code_snippet: Optional[str] = None
    question_type: str
    language: str
    difficulty: str
    time_limit: int
    options: List[dict] = []  # Without is_correct

    class Config:
        from_attributes = True


class QuestionFilter(BaseModel):
    language: Optional[str] = None
    difficulty: Optional[str] = None
    question_type: Optional[str] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None
    page: int = 1
    per_page: int = 20
