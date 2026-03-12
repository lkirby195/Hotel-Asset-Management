import logging
import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.clerk import verify_clerk_token
from app.config import settings
from app.db.engine import async_session_factory
from app.models.user import User

logger = logging.getLogger(__name__)


async def get_current_user_claims(request: Request) -> dict:
    """Extract and verify Clerk JWT from Authorization header.

    In development mode with no CLERK_SECRET_KEY configured, accepts a
    special ``X-Dev-User-Email`` header to bypass JWT verification.
    This NEVER activates in production.
    """
    # --- Dev bypass: no Clerk key configured ---------------------------------
    if settings.environment == "development" and not settings.clerk_secret_key:
        dev_email = request.headers.get("X-Dev-User-Email")
        if dev_email:
            logger.warning("DEV AUTH BYPASS: using X-Dev-User-Email=%s", dev_email)
            return {"sub": f"dev_{dev_email}", "email": dev_email, "_dev_bypass": True}
    # -------------------------------------------------------------------------

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = auth_header.split(" ", 1)[1]
    try:
        return await verify_clerk_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_current_user(
    claims: dict = Depends(get_current_user_claims),
) -> User:
    """Resolve the internal User from Clerk JWT claims.

    This fetches the user from DB in a separate session (without RLS)
    so we can discover the tenant_id for subsequent queries.
    """
    async with async_session_factory() as session:
        # Dev bypass: look up by email instead of clerk_id
        if claims.get("_dev_bypass"):
            email = claims["email"]
            result = await session.execute(
                select(User)
                .options(selectinload(User.properties))
                .where(User.email == email, User.is_active == True)  # noqa: E712
            )
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Dev user '{email}' not found in database",
                )
            return user

        clerk_id = claims.get("sub")
        if not clerk_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")

        result = await session.execute(
            select(User)
            .options(selectinload(User.properties))
            .where(User.clerk_id == clerk_id, User.is_active == True)  # noqa: E712
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user


async def get_db_session(
    current_user: User = Depends(get_current_user),
) -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession with RLS tenant context set."""
    async with async_session_factory() as session:
        # Set the tenant context for row-level security
        await session.execute(
            text(f"SET LOCAL app.current_tenant_id = '{current_user.tenant_id}'")
        )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def require_role(min_role: str):
    """Dependency factory that checks if the current user meets the minimum role."""

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_role(min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {min_role} role or higher",
            )
        return current_user

    return _check


async def require_property_access(
    property_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
) -> uuid.UUID:
    """Verify the current user has access to the specified property."""
    if current_user.role == "executive" or current_user.role == "admin":
        return property_id

    user_property_ids = {p.id for p in current_user.properties}
    if property_id not in user_property_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this property",
        )
    return property_id
