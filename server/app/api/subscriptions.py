from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User, UserTier
from app.crud import crud_user
from app.schemas.user import UserResponse

router = APIRouter()

@router.post("/upgrade", response_model=UserResponse)
def upgrade_subscription(
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_active_user)
):
    """
    Mock endpoint to upgrade a user to the Premium tier.
    In a real application, this would be triggered by a payment webhook.
    """
    if user.tier == UserTier.PREMIUM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already on the Premium tier."
        )
    
    updated_user = crud_user.update_user_tier(db, user=user, tier=UserTier.PREMIUM)
    return updated_user

@router.post("/cancel", response_model=UserResponse)
def cancel_subscription(
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_active_user)
):
    """
    Mock endpoint to downgrade a user to the Free tier.
    """
    if user.tier == UserTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already on the Free tier."
        )
    
    updated_user = crud_user.update_user_tier(db, user=user, tier=UserTier.FREE)
    return updated_user