# models/gameline.py
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base

class Sport(str, enum.Enum):
    NFL = "nfl"
    NBA = "nba"
    MLB = "mlb"
    NHL = "nhl"
    NCAAF = "ncaaf"
    NCAAB = "ncaab"

class Gameline(Base):
    __tablename__ = "gamelines"
    
    id = Column(Integer, primary_key=True, index=True)
    sport = Column(String(10), nullable=False)
    source = Column(String(50), nullable=False)  # espn_bets, draftkings, etc.
    game_id = Column(String(50), nullable=False)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    home_abbr = Column(String(10), nullable=False)
    away_abbr = Column(String(10), nullable=False)
    home_ml = Column(Integer, nullable=True)
    away_ml = Column(Integer, nullable=True)
    home_spread = Column(Float, nullable=True)
    away_spread = Column(Float, nullable=True)
    home_spread_odds = Column(Integer, nullable=True)
    away_spread_odds = Column(Integer, nullable=True)
    total = Column(Float, nullable=True)
    over_odds = Column(Integer, nullable=True)
    under_odds = Column(Integer, nullable=True)
    game_date = Column(DateTime, nullable=False)
    start_time = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())