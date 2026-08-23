"""Team and TeamMember models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id", ondelete="SET NULL"), nullable=True, index=True)
    team_name = Column(String(200), nullable=False, index=True)
    college_name = Column(String(300), nullable=True)
    logo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="team", uselist=False)
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=True)
    role_in_team = Column(String(100), nullable=True)  # e.g., "Captain", "Member"
    order = Column(Integer, default=0)

    # Relationships
    team = relationship("Team", back_populates="members")
