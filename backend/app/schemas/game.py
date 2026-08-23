"""Game-related schemas (board, attempts, scoring, leaderboard)."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Board schemas
class BoardTileResponse(BaseModel):
    id: str
    position: int
    row: int
    col: int
    status: str
    question_number: int = 0
    difficulty: str = ""
    answered_at: Optional[datetime] = None
    is_bingo_part: bool = False

    class Config:
        from_attributes = True


class BoardResponse(BaseModel):
    id: str
    round_id: str
    team_id: str
    size: int
    tiles: List[BoardTileResponse] = []
    bingo_lines: List[List[int]] = []  # List of positions that form bingos

    class Config:
        from_attributes = True


# Attempt schemas
class SubmitAnswerRequest(BaseModel):
    tile_id: str
    answer: str
    time_taken_seconds: float = 0.0


class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    points_earned: int
    new_score: int
    new_bingo_count: int
    bingo_lines: List[List[int]] = []
    tile_status: str


# Score schemas
class ScoreResponse(BaseModel):
    team_id: str
    team_name: str
    round_id: str
    total_score: int
    correct_answers: int
    wrong_answers: int
    bingo_count: int
    accuracy: float
    avg_response_time: float
    completion_percentage: float

    class Config:
        from_attributes = True


# Leaderboard schemas
class LeaderboardEntryResponse(BaseModel):
    rank: int
    team_id: str
    team_name: str
    score: int
    bingo_count: int
    correct_answers: int
    total_questions: int
    accuracy: float
    completion_percentage: float
    avg_time: float

    class Config:
        from_attributes = True


class LeaderboardResponse(BaseModel):
    round_id: str
    round_name: str
    entries: List[LeaderboardEntryResponse] = []
    last_updated: Optional[datetime] = None


# Qualification schemas
class QualificationResponse(BaseModel):
    team_id: str
    team_name: str
    tournament_id: str
    round_id: str
    status: str
    final_rank: Optional[int] = None
    final_score: int = 0

    class Config:
        from_attributes = True


# Dashboard stats
class AdminDashboardStats(BaseModel):
    total_tournaments: int = 0
    active_tournaments: int = 0
    total_teams: int = 0
    total_questions: int = 0
    total_rounds: int = 0
    active_rounds: int = 0
    online_teams: int = 0


class TeamDashboardStats(BaseModel):
    team_name: str
    current_tournament_id: Optional[str] = None
    current_tournament: Optional[str] = None
    current_tournament_status: Optional[str] = None
    current_round: Optional[str] = None
    current_score: int = 0
    current_rank: int = 0
    bingo_count: int = 0
    qualification_status: str = "pending"
    remaining_time: int = 0
