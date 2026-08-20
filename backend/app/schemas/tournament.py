"""Tournament schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RoundCreate(BaseModel):
    name: str
    order: int = 0
    board_size: int = 5
    timer_seconds: int = 600
    difficulty: str = "mixed"
    num_questions: int = 25
    qualification_count: int = 10
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class RoundUpdate(BaseModel):
    name: Optional[str] = None
    board_size: Optional[int] = None
    timer_seconds: Optional[int] = None
    difficulty: Optional[str] = None
    num_questions: Optional[int] = None
    qualification_count: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class RoundResponse(BaseModel):
    id: str
    tournament_id: str
    name: str
    order: int
    board_size: int
    timer_seconds: int
    difficulty: str
    num_questions: int
    qualification_count: int
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    participant_count: int = 0

    class Config:
        from_attributes = True


class TournamentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None
    max_teams: int = 50
    num_rounds: int = 3
    rounds: Optional[List[RoundCreate]] = []


class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None
    max_teams: Optional[int] = None
    status: Optional[str] = None


class TournamentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None
    max_teams: int
    num_rounds: int
    rounds: List[RoundResponse] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TournamentListResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    max_teams: int
    num_rounds: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
