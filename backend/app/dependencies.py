from fastapi import Depends, HTTPException, status

from app.auth import get_current_user
from app.models import User


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_reviewer(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in ("reviewer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer access required",
        )
    return current_user
