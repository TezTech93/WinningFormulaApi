# routers/strategies.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.strategy import UserStrategy, StrategyType, StrategyTip

router = APIRouter(tags=["Strategies"])

class StrategyCreate(BaseModel):
    strategy_name: str
    strategy_type: str
    description: Optional[str] = None
    target_amount: Optional[float] = None
    bankroll: Optional[float] = None
    unit_size: Optional[float] = None
    risk_percentage: float = 3.0

class StrategyResponse(BaseModel):
    id: int
    strategy_name: str
    strategy_type: str
    description: Optional[str]
    target_amount: Optional[float]
    bankroll: Optional[float]
    unit_size: Optional[float]
    risk_percentage: float
    is_active: int
    created_at: str

@router.post("/strategies", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy_data: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new strategy"""
    strategy = UserStrategy(
        user_id=current_user.id,
        strategy_name=strategy_data.strategy_name,
        strategy_type=StrategyType(strategy_data.strategy_type),
        description=strategy_data.description,
        target_amount=strategy_data.target_amount,
        bankroll=strategy_data.bankroll,
        unit_size=strategy_data.unit_size,
        risk_percentage=strategy_data.risk_percentage
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
    return {
        "id": strategy.id,
        "strategy_name": strategy.strategy_name,
        "strategy_type": strategy.strategy_type.value,
        "description": strategy.description,
        "target_amount": strategy.target_amount,
        "bankroll": strategy.bankroll,
        "unit_size": strategy.unit_size,
        "risk_percentage": strategy.risk_percentage,
        "is_active": strategy.is_active,
        "created_at": strategy.created_at.isoformat()
    }

@router.get("/strategies/tips", response_model=List[dict])
async def get_strategy_tips(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get strategy tips"""
    query = db.query(StrategyTip)
    if category:
        query = query.filter(StrategyTip.category == category)
    
    tips = query.order_by(StrategyTip.order).all()
    
    return [{
        "id": t.id,
        "category": t.category,
        "title": t.title,
        "description": t.description,
        "difficulty": t.difficulty,
        "icon": t.icon
    } for t in tips]

@router.get("/strategies", response_model=List[StrategyResponse])
async def get_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all strategies for current user"""
    strategies = db.query(UserStrategy).filter(
        UserStrategy.user_id == current_user.id
    ).order_by(UserStrategy.created_at.desc()).all()
    
    return [{
        "id": s.id,
        "strategy_name": s.strategy_name,
        "strategy_type": s.strategy_type.value,
        "description": s.description,
        "target_amount": s.target_amount,
        "bankroll": s.bankroll,
        "unit_size": s.unit_size,
        "risk_percentage": s.risk_percentage,
        "is_active": s.is_active,
        "created_at": s.created_at.isoformat()
    } for s in strategies]

@router.put("/strategies/{strategy_id}/toggle")
async def toggle_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle strategy active status"""
    strategy = db.query(UserStrategy).filter(
        UserStrategy.id == strategy_id,
        UserStrategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    strategy.is_active = 0 if strategy.is_active else 1
    db.commit()
    
    return {"message": "Strategy toggled", "is_active": strategy.is_active}