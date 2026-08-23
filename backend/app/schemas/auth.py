"""Authentication schemas."""

from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class LoginRequest(BaseModel):
    username: str
    password: str


class FirebaseAuthRequest(BaseModel):
    id_token: str
    team_name: Optional[str] = None


class RegisterRequest(BaseModel):
    email: str
    password: str
    team_name: str


class RoomJoinRequest(BaseModel):
    room_code: str
    team_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str
    team_id: Optional[str] = None
    team_name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True
