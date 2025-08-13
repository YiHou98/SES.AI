from sqlalchemy.orm import Session
from app.models.user import User, UserTier

def update_user_tier(db: Session, user: User, tier: UserTier) -> User:
    """
    Updates the subscription tier for a given user.
    """
    user.tier = tier
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user_model_preference(db: Session, user: User, model: str) -> User:
    """
    Updates the selected model for a given user.
    """
    user.selected_model = model
    db.add(user)
    db.commit()
    db.refresh(user)
    return user