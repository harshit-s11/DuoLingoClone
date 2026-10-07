"""Shared FastAPI dependencies."""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.hearts import calculate_heart_regen


def get_current_user_dep(
    x_user_id: int = Header(default=1, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    """Resolve authenticated user from X-User-Id header and lazily compute heart regeneration."""
    user = db.query(User).filter(User.id == x_user_id).first()
    if not user:
        # Fallback to user 1 if specified ID not found
        user = db.query(User).filter(User.id == 1).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Lazily update hearts whenever user is accessed
    user = calculate_heart_regen(user, db)
    return user
