from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.models.user import User
from app.crud import crud_user
from app.schemas.user import UserResponse, UserUsage
from app.core.config import settings

router = APIRouter()

@router.post("/me/model", response_model=UserResponse)
def update_model_preference(
    model: str,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_active_user)
):
    """
    Allows a user to update their preferred LLM model.
    """
    if user.tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only premium users can select a model."
        )
    
    allowed_models = ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"]
    if model not in allowed_models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model selected. Allowed models are: {', '.join(allowed_models)}"
        )

    updated_user = crud_user.update_user_model_preference(db, user=user, model=model)
    return updated_user

@router.get("/me/usage", response_model=UserUsage)
def get_user_usage(
    user: User = Depends(deps.get_current_active_user)
):
    """
    Get the current user's daily API usage.
    """
    # If the user is premium, they have unlimited usage.
    if user.tier == "premium":
        return {"limit": "Unlimited", "used": 0, "remaining": "Unlimited"}

    # For free users, check Redis.
    if deps.redis_client:
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"usage:{user.id}:{today_str}"
        
        # Get the current usage count. If the key doesn't exist, it means 0 calls were made.
        current_usage = int(deps.redis_client.get(key) or 0)
        
        limit = settings.FREE_TIER_DAILY_LIMIT
        remaining = limit - current_usage

        return {"limit": limit, "used": current_usage, "remaining": remaining}
    
    # Fallback if Redis is not available
    return {"limit": settings.FREE_TIER_DAILY_LIMIT, "used": 0, "remaining": settings.FREE_TIER_DAILY_LIMIT}