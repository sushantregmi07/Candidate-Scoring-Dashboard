from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Auth ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    """Registration payload — intentionally has NO role field."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Candidates ───────────────────────────────────────────────────────────────

class CandidateBase(BaseModel):
    name: str
    email: EmailStr
    role_applied: str
    status: str = "new"
    skills: list[str] = []


class CandidateOut(CandidateBase):
    id: str
    ai_summary: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CandidateAdminOut(CandidateOut):
    """Extended view for admins — includes internal_notes."""
    internal_notes: Optional[str] = None


class CandidateListResponse(BaseModel):
    items: list[CandidateOut]
    total: int
    page: int
    page_size: int
    pages: int


class InternalNotesUpdate(BaseModel):
    notes: str


# ── Scores ───────────────────────────────────────────────────────────────────

class ScoreCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    score: int = Field(..., ge=1, le=5)
    note: Optional[str] = None


class ScoreOut(BaseModel):
    id: str
    candidate_id: str
    category: str
    score: int
    reviewer_id: str
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── AI Summary ───────────────────────────────────────────────────────────────

class AISummaryOut(BaseModel):
    candidate_id: str
    summary: str
