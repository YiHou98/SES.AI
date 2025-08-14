import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 项目元数据
    PROJECT_NAME: str = "LLM RAG Framework"
    API_V1_STR: str = "/api/v1"

    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # Redis 配置
    REDIS_URL: str = os.getenv("REDIS_URL")

    # JWT 认证配置
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"

    # RAG 和 LLM 配置
    VECTOR_STORE_PATH: str = "./vector_store"
    DEFAULT_MODEL: str = "claude-3-5-sonnet-20240620"
    PREMIUM_MODEL_DEFAULT: str = "claude-3-5-sonnet-20240620" # Use the latest Sonnet as the default for premium
    
    
    # 用户等级配置
    FREE_TIER_DAILY_LIMIT: int = 10

    # LLM模型成本配置（每1M tokens的USD价格）
    MODEL_COSTS: dict = {
        "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
        "claude-opus-4-1-20250805": {"input": 15.00, "output": 75.00}
    }

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        case_sensitive = True

settings = Settings()