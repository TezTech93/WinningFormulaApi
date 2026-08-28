# models/player.py
from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from core.database import Base

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    sport = Column(String(10), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    position = Column(String(20), nullable=True)
    jersey_number = Column(String(5), nullable=True)
    # Sport-specific stats stored as JSON
    stats = Column(JSON, nullable=True)  # e.g., {"ppg": 25.3, "rpg": 8.1}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    team = relationship("Team", back_populates="players")