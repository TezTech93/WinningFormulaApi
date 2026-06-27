# core/config.py
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./winners_formula.db")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "khi-my-guy-always365")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Sports APIs
    NFL_API_URL: str = "https://nflapi.onrender.com"
    NBA_API_URL: str = "https://nbaapi-ksvt.onrender.com"
    MLB_API_URL: str = "https://mlbapi.onrender.com"
    NHL_API_URL: str = "https://nhlapi.onrender.com"
    NCAAF_API_URL: str = "https://ncaafapi2.onrender.com"
    NCAAB_API_URL: str = "https://ncaabapi.onrender.com"
    
    # User tiers
    TIER_LIMITS: dict = {
        "FREE": 50,
        "PAID": 500,
        "PLUS": 2000
    }
    
    # Redis for caching (optional)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)
    
    class Config:
        env_file = ".env"

settings = Settings()