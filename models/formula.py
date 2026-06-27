# models/formula.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from core.database import Base

class FormulaType(str, enum.Enum):
    RANKING = "ranking"
    METRIC = "metric"
    MONTE_CARLO = "monte_carlo"

class UserFormula(Base):
    __tablename__ = "user_formulas"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    formula_name = Column(String(100), nullable=False)
    formula = Column(Text, nullable=False)
    formula_type = Column(Enum(FormulaType), default=FormulaType.RANKING)
    sport = Column(String(10), nullable=False)
    description = Column(Text, nullable=True)
    accuracy_score = Column(Integer, default=0)
    simulation_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="formulas")