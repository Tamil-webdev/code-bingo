"""User model for admin and team authentication."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy import Uuid as UUID
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEAM = "team"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    firebase_uid = Column(String(128), unique=True, nullable=True, index=True)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.TEAM)
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Prevent duplicate logins - store current session token
    current_session_token = Column(String(500), nullable=True)
