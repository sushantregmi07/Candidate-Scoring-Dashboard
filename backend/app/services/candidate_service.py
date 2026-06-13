import asyncio
import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Candidate, Score, Summary, User


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
        base = base.where(Candidate.role_applied.ilike(f"%{role_applied}%"))
    if skill:
        base = base.where(Candidate.skills.ilike(f"%{skill}%"))
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

    result = await db.execute(
        select(Score).where(
            Score.candidate_id == candidate_id,
            Score.reviewer_id == reviewer_id,
            Score.category == category,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.score = score_value
        existing.note = note
        await db.flush()
        await db.refresh(existing)
        return existing

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


async def soft_delete_candidate(
    db: AsyncSession,
    candidate_id: str,
) -> Candidate:
    candidate = await get_candidate(db, candidate_id)
    candidate.status = "archived"
    candidate.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(candidate)
    return candidate


async def get_user_summary(
    db: AsyncSession,
    candidate_id: str,
    user_id: str,
) -> Optional[str]:
    result = await db.execute(
        select(Summary).where(
            Summary.candidate_id == candidate_id,
            Summary.user_id == user_id,
        )
    )
    row = result.scalar_one_or_none()
    return row.summary if row else None


async def generate_ai_summary(
    db: AsyncSession,
    candidate_id: str,
    current_user: User,
) -> Summary:
    candidate = await get_candidate(db, candidate_id)

    await asyncio.sleep(2)

    skills_str = ", ".join(candidate.skills) if candidate.skills else "not specified"

    is_admin = current_user.role == "admin"
    if is_admin:
        relevant_scores = candidate.scores
    else:
        relevant_scores = [s for s in candidate.scores if s.reviewer_id == current_user.id]

    score_analysis = ""
    recommendation = ""

    if relevant_scores:
        category_scores: dict[str, list[int]] = {}
        for s in relevant_scores:
            category_scores.setdefault(s.category, []).append(s.score)

        overall_avg = sum(s.score for s in relevant_scores) / len(relevant_scores)

        breakdown_parts = []
        for cat in sorted(category_scores.keys()):
            scores_list = category_scores[cat]
            cat_avg = sum(scores_list) / len(scores_list)
            if is_admin:
                breakdown_parts.append(
                    f"{cat}: {cat_avg:.1f}/5 ({len(scores_list)} "
                    f"review{'s' if len(scores_list) > 1 else ''})"
                )
            else:
                breakdown_parts.append(f"{cat}: {cat_avg:.1f}/5")

        if is_admin:
            reviewer_ids = {s.reviewer_id for s in relevant_scores}
            score_analysis = (
                f" Based on evaluations from {len(reviewer_ids)} "
                f"reviewer{'s' if len(reviewer_ids) > 1 else ''} across "
                f"{len(category_scores)} "
                f"categor{'y' if len(category_scores) == 1 else 'ies'}, "
                f"the overall average score is {overall_avg:.1f}/5. "
                f"Category breakdown — {'; '.join(breakdown_parts)}."
            )
        else:
            score_analysis = (
                f" Your evaluation covers {len(category_scores)} "
                f"categor{'y' if len(category_scores) == 1 else 'ies'} "
                f"with an average score of {overall_avg:.1f}/5. "
                f"Scores — {'; '.join(breakdown_parts)}."
            )

        if overall_avg >= 4.0:
            recommendation = (
                " The candidate demonstrates strong performance and is "
                "recommended for advancement to the next stage."
            )
        elif overall_avg >= 3.0:
            recommendation = (
                " The candidate shows solid potential with room for growth. "
                "Consider a follow-up evaluation focused on weaker categories."
            )
        else:
            recommendation = (
                " Current scores indicate areas of concern. "
                "A detailed review is recommended before proceeding further."
            )
    else:
        if is_admin:
            recommendation = (
                " No scores have been submitted by any reviewer yet. "
                "The candidate should be evaluated before making a decision."
            )
        else:
            recommendation = (
                " You have not submitted any scores for this candidate yet. "
                "Please score the candidate before generating a summary."
            )

    summary_text = (
        f"{candidate.name} applied for the {candidate.role_applied} position. "
        f"Their current status is '{candidate.status}'. "
        f"Key skills include: {skills_str}."
        f"{score_analysis}{recommendation}"
    )

    result = await db.execute(
        select(Summary).where(
            Summary.candidate_id == candidate_id,
            Summary.user_id == current_user.id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.summary = summary_text
        existing.created_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(existing)
        return existing

    new_summary = Summary(
        candidate_id=candidate_id,
        user_id=current_user.id,
        summary=summary_text,
    )
    db.add(new_summary)
    await db.flush()
    await db.refresh(new_summary)
    return new_summary
