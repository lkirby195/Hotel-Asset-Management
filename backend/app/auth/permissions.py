from fastapi import Depends, HTTPException, status

from app.models.user import User


def require_role(min_role: str):
    """FastAPI dependency factory that enforces a minimum role level."""

    async def _check_role(current_user: User = Depends()) -> User:
        if not current_user.has_role(min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {min_role} role or higher",
            )
        return current_user

    return _check_role
