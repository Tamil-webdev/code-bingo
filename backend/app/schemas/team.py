"""Team schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TeamMemberCreate(BaseModel):
    name: str
    email: Optional[str] = None
    role_in_team: Optional[str] = None


class TeamMemberResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    role_in_team: Optional[str] = None

    class Config:
        from_attributes = True


class TeamCreate(BaseModel):
    team_name: str
    college_name: Optional[str] = None
    username: str
    password: str
    members: Optional[List[TeamMemberCreate]] = []


class TeamUpdate(BaseModel):
    team_name: Optional[str] = None
    college_name: Optional[str] = None
    members: Optional[List[TeamMemberCreate]] = None


class TeamResponse(BaseModel):
    id: str
    team_name: str
    college_name: Optional[str] = None
    username: str
    members: List[TeamMemberResponse] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TeamBulkImport(BaseModel):
    """Schema for bulk CSV import."""
    teams: List[TeamCreate]


class TeamCredentials(BaseModel):
    team_name: str
    username: str
    password: str
    college_name: Optional[str] = None
