# core/config.py
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://winning_formula_db_user:4uchZZZiRrCv8e4FL2ykAc8Rmu1J0pBQ@dpg-d94s4afaqgkc73eami1g-a/winning_formula_db"
    )
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "khi-my-guy-always365")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    # Sports API URLs
    NFL_API_URL: str = os.getenv("NFL_API_URL", "https://nflapi.onrender.com")
    NBA_API_URL: str = os.getenv("NBA_API_URL", "https://nbaapi-ksvt.onrender.com")
    MLB_API_URL: str = os.getenv("MLB_API_URL", "https://mlbapi.onrender.com")
    NHL_API_URL: str = os.getenv("NHL_API_URL", "https://nhlapi.onrender.com")
    NCAAF_API_URL: str = os.getenv("NCAAF_API_URL", "https://ncaafapi2.onrender.com")
    NCAAB_API_URL: str = os.getenv("NCAAB_API_URL", "https://ncaabapi.onrender.com")
    
    # User tiers
    TIER_LIMITS: dict = {
        "FREE": 50,
        "PAID": 500,
        "PLUS": 2000
    }
    
    # Cache settings
    CACHE_EXPIRY_MINUTES: int = 5
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()