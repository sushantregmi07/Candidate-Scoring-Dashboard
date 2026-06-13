from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.dependencies import require_admin
from app.models import User
from app.schemas import (
    AISummaryOut,
    CandidateAdminOut,
    CandidateListResponse,
    CandidateOut,
    InternalNotesUpdate,
    ScoreAdminOut,
    ScoreCreate,
    ScoreOut,
)
from app.services import candidate_service

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("", response_model=CandidateListResponse)
async def list_candidates(
    status: Optional[str] = Query(None, description="Filter by status"),
    role_applied: Optional[str] = Query(None, description="Filter by role applied"),
    skill: Optional[str] = Query(None, description="Filter by skill"),
    keyword: Optional[str] = Query(None, description="Search name or email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await candidate_service.list_candidates(
        db,
        status_filter=status,
        role_applied=role_applied,
        skill=skill,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )

    if current_user.role == "admin":
        result["items"] = [
            CandidateAdminOut.model_validate(c) for c in result["items"]
        ]
    else:
        result["items"] = [
            CandidateOut.model_validate(c) for c in result["items"]
        ]

    return result


@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = await candidate_service.get_candidate(db, candidate_id)
    scores = candidate_service.filter_scores_for_user(candidate, current_user)

    if current_user.role == "admin":
        candidate_data = CandidateAdminOut.model_validate(candidate).model_dump()
    else:
        candidate_data = CandidateOut.model_validate(candidate).model_dump()

    if current_user.role == "admin":
        candidate_data["scores"] = [
            {
                **ScoreAdminOut.model_validate(s).model_dump(),
                "reviewer_username": s.reviewer.username if s.reviewer else None,
                "reviewer_email": s.reviewer.email if s.reviewer else None,
            }
            for s in scores
        ]
    else:
        candidate_data["scores"] = [
            ScoreOut.model_validate(s).model_dump() for s in scores
        ]

    user_summary = await candidate_service.get_user_summary(
        db, candidate_id, current_user.id
    )
    candidate_data["ai_summary"] = user_summary

    return candidate_data


@router.post("/{candidate_id}/scores", response_model=ScoreOut, status_code=201)
async def submit_score(
    candidate_id: str,
    payload: ScoreCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await candidate_service.create_score(
        db,
        candidate_id=candidate_id,
        category=payload.category,
        score_value=payload.score,
        reviewer_id=current_user.id,
        note=payload.note,
    )


@router.patch("/{candidate_id}/notes")
async def update_notes(
    candidate_id: str,
    payload: InternalNotesUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    candidate = await candidate_service.update_internal_notes(
        db, candidate_id, payload.notes
    )
    return CandidateAdminOut.model_validate(candidate)


@router.post("/{candidate_id}/summary", response_model=AISummaryOut)
async def generate_summary(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    summary = await candidate_service.generate_ai_summary(
        db, candidate_id, current_user
    )
    return AISummaryOut(candidate_id=summary.candidate_id, summary=summary.summary)


@router.delete("/{candidate_id}", status_code=200)
async def archive_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    candidate = await candidate_service.soft_delete_candidate(db, candidate_id)
    return {"detail": "Candidate archived", "id": candidate.id}
