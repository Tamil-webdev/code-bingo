"""Certificate model for participation and winner certificates."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy import Uuid as UUID
from app.database import Base
import enum


class CertificateType(str, enum.Enum):
    PARTICIPATION = "participation"
    WINNER = "winner"
    RUNNER_UP = "runner_up"
    QUALIFIER = "qualifier"


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    certificate_type = Column(SAEnum(CertificateType), nullable=False)
    certificate_url = Column(String(500), nullable=True)
    certificate_data = Column(Text, nullable=True)  # base64 encoded PDF
    issued_at = Column(DateTime, default=datetime.utcnow)
