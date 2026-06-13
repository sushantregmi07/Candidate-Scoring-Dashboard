import asyncio
import math
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Candidate, Score, User


async def list_candidates(
    db: AsyncSession,
    *,
    status_filter: Optional[str] = None,
    role_applied: Optional[str] = None,
    skill: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    page_size = min(page_size, 50)
    page = max(page, 1)

    base = select(Candidate).where(Candidate.deleted_at.is_(None))

    if status_filter:
        base = base.where(Candidate.status == status_filter)
    if role_applied:
        base = base.where(Candidate.role_applied == role_applied)
    if skill:
        base = base.where(Candidate.skills.like(f'%"{skill}"%'))
    if keyword:
        pattern = f"%{keyword}%"
        base = base.where(
            or_(
                Candidate.name.ilike(pattern),
                Candidate.email.ilike(pattern),
            )
        )

    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    items_q = base.order_by(Candidate.created_at.desc()).limit(page_size).offset(offset)
    result = await db.execute(items_q)
    candidates = result.scalars().all()

    return {
        "items": candidates,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total > 0 else 0,
    }


async def get_candidate(
    db: AsyncSession,
    candidate_id: str,
) -> Candidate:
    q = (
        select(Candidate)
        .where(Candidate.id == candidate_id, Candidate.deleted_at.is_(None))
        .options(selectinload(Candidate.scores).selectinload(Score.reviewer))
    )
    result = await db.execute(q)
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )
    return candidate


def filter_scores_for_user(candidate: Candidate, current_user: User) -> list[Score]:
    if current_user.role == "admin":
        return candidate.scores
    return [s for s in candidate.scores if s.reviewer_id == current_user.id]


async def create_score(
    db: AsyncSession,
    candidate_id: str,
    category: str,
    score_value: int,
    reviewer_id: str,
    note: Optional[str] = None,
) -> Score:
    await get_candidate(db, candidate_id)

    new_score = Score(
        candidate_id=candidate_id,
        category=category,
        score=score_value,
        reviewer_id=reviewer_id,
        note=note,
    )
    db.add(new_score)
    await db.flush()
    await db.refresh(new_score)
    return new_score


async def update_internal_notes(
    db: AsyncSession,
    candidate_id: str,
    notes: str,
) -> Candidate:
    candidate = await get_candidate(db, candidate_id)
    candidate.internal_notes = notes
    await db.flush()
    await db.refresh(candidate)
    return candidate


async def generate_ai_summary(
    db: AsyncSession,
    candidate_id: str,
) -> Candidate:
    candidate = await get_candidate(db, candidate_id)

    await asyncio.sleep(2)

    score_lines = ""
    if candidate.scores:
        avg = sum(s.score for s in candidate.scores) / len(candidate.scores)
        score_lines = (
            f" They have received {len(candidate.scores)} score(s) "
            f"with an average rating of {avg:.1f}/5."
        )

    skills_str = ", ".join(candidate.skills) if candidate.skills else "not specified"

    candidate.ai_summary = (
        f"{candidate.name} applied for the {candidate.role_applied} position. "
        f"Their current status is '{candidate.status}'. "
        f"Key skills include: {skills_str}."
        f"{score_lines} "
        f"Overall, the candidate shows promise and should be evaluated further "
        f"based on the specific requirements of the role."
    )
    await db.flush()
    await db.refresh(candidate)
    return candidate
