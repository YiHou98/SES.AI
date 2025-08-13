from typing import Generator
from datetime import datetime, timedelta
from functools import lru_cache
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import redis
import os
from jose import jwt
from app.core.logging_config import get_logger

logger = get_logger(__name__)

from app.core.config import settings
from app.models.user import User
from app.schemas.token import TokenPayload
from app.db.session import SessionLocal
from app.services.rag_service import RAGService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    logger.warning(f"Could not connect to Redis. Rate limiting will be disabled. Error: {e}")
    redis_client = None

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(sub=payload.get("sub"))
        if token_data.sub is None:
            raise credentials_exception
    except (jwt.JWTError, ValueError):
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(token_data.sub)).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def rate_limit_dependency(user: User = Depends(get_current_active_user)) -> Generator[User, None, None]:
    if user.tier.value != "free" or not redis_client:
        yield user
        return

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    key = f"usage:{user.id}:{today_str}"
    
    try:
        current_usage = redis_client.get(key)
        
        if current_usage is None:
            now = datetime.utcnow()
            midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_until_midnight = int((midnight - now).total_seconds())
            
            redis_client.setex(key, seconds_until_midnight, 0)
            current_usage = 0
        
        current_usage = int(current_usage)

        if current_usage >= settings.FREE_TIER_DAILY_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily limit of {settings.FREE_TIER_DAILY_LIMIT} requests exceeded for today."
            )

    except (redis.exceptions.RedisError, ConnectionRefusedError) as e:
        logger.warning(f"Redis error during rate limiting. Allowing request. Error: {e}")
        yield user
        return

    yield user
    
    try:
        redis_client.incr(key)
    except (redis.exceptions.RedisError, ConnectionRefusedError) as e:
        logger.warning(f"Failed to increment usage for user {user.id}. Error: {e}")
        pass

@lru_cache()
def get_rag_service() -> RAGService:
    os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
    return RAGService()