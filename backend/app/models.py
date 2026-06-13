import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    username = Column(String(255), nullable=False, default="")
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        SAEnum("reviewer", "admin", name="user_role"),
        nullable=False,
        default="reviewer",
    )
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    scores = relationship("Score", back_populates="reviewer", lazy="selectin")


class Candidate(Base):
    __tablename__ = "candidates"
    __table_args__ = (
        Index("ix_candidates_status", "status"),
        Index("ix_candidates_role_applied", "role_applied"),
    )

    id = Column(String(36), primary_key=True, default=_new_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role_applied = Column(String(255), nullable=False)
    status = Column(
        SAEnum("new", "reviewed", "hired", "rejected", "archived", name="candidate_status"),
        nullable=False,
        default="new",
    )
    skills = Column(JSON, nullable=False, default=list)
    internal_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    scores = relationship("Score", back_populates="candidate", lazy="selectin")


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (
        Index("ix_scores_candidate_id", "candidate_id"),
    )

    id = Column(String(36), primary_key=True, default=_new_uuid)
    candidate_id = Column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    category = Column(String(100), nullable=False)
    score = Column(Integer, nullable=False)
    reviewer_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    candidate = relationship("Candidate", back_populates="scores")
    reviewer = relationship("User", back_populates="scores")


class Summary(Base):
    __tablename__ = "summaries"
    __table_args__ = (
        UniqueConstraint("candidate_id", "user_id", name="uq_summary_candidate_user"),
    )

    id = Column(String(36), primary_key=True, default=_new_uuid)
    candidate_id = Column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
