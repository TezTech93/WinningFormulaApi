# routers/parlays.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.parlay import Parlay, ParlaySelection, ParlayStatus
from managers.parlay_manager import ParlayManager

router = APIRouter(tags=["Parlays"])

class ParlaySelectionCreate(BaseModel):
    game_id: str
    selection_type: str
    selection_value: str
    odds: float
    order: int = 0

class ParlayCreate(BaseModel):
    sport: str
    name: Optional[str] = None
    bet_amount: float = Field(10.0, ge=0.01)
    selections: List[ParlaySelectionCreate]
    metadata: Optional[dict] = None

class ParlayResponse(BaseModel):
    id: int
    sport: str
    name: Optional[str]
    bet_amount: float
    total_odds: float
    potential_payout: float
    potential_profit: float
    status: str
    selections_count: int
    created_at: str

@router.post("/parlays", response_model=ParlayResponse, status_code=status.HTTP_201_CREATED)
async def create_parlay(
    parlay_data: ParlayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new parlay"""
    parlay_manager = ParlayManager(db)
    
    # Calculate odds and payout
    selections_list = [s.selection_value for s in parlay_data.selections]
    total_odds = parlay_manager.calculate_parlay_odds(selections_list)
    payout_result = parlay_manager.calculate_payout(parlay_data.bet_amount, selections_list)
    
    # Create parlay
    parlay = Parlay(
        user_id=current_user.id,
        sport=parlay_data.sport,
        name=parlay_data.name,
        bet_amount=parlay_data.bet_amount,
        total_odds=total_odds,
        potential_payout=payout_result['payout'],
        potential_profit=payout_result['profit'],
        status=ParlayStatus.PENDING,
        selections_count=len(parlay_data.selections),
        metadata=parlay_data.metadata
    )
    db.add(parlay)
    db.flush()
    
    # Create selections
    for selection_data in parlay_data.selections:
        selection = ParlaySelection(
            parlay_id=parlay.id,
            game_id=selection_data.game_id,
            selection_type=selection_data.selection_type,
            selection_value=selection_data.selection_value,
            odds=selection_data.odds,
            order=selection_data.order
        )
        db.add(selection)
    
    db.commit()
    db.refresh(parlay)
    
    return {
        "id": parlay.id,
        "sport": parlay.sport,
        "name": parlay.name,
        "bet_amount": parlay.bet_amount,
        "total_odds": parlay.total_odds,
        "potential_payout": parlay.potential_payout,
        "potential_profit": parlay.potential_profit,
        "status": parlay.status.value,
        "selections_count": parlay.selections_count,
        "created_at": parlay.created_at.isoformat()
    }

@router.get("/parlays", response_model=List[ParlayResponse])
async def get_parlays(
    sport: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all parlays for current user"""
    query = db.query(Parlay).filter(Parlay.user_id == current_user.id)
    
    if sport:
        query = query.filter(Parlay.sport == sport)
    if status:
        query = query.filter(Parlay.status == status)
    
    parlays = query.order_by(Parlay.created_at.desc()).all()
    
    return [{
        "id": p.id,
        "sport": p.sport,
        "name": p.name,
        "bet_amount": p.bet_amount,
        "total_odds": p.total_odds,
        "potential_payout": p.potential_payout,
        "potential_profit": p.potential_profit,
        "status": p.status.value,
        "selections_count": p.selections_count,
        "created_at": p.created_at.isoformat()
    } for p in parlays]

@router.get("/parlays/{parlay_id}", response_model=ParlayResponse)
async def get_parlay(
    parlay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific parlay"""
    parlay = db.query(Parlay).filter(
        Parlay.id == parlay_id,
        Parlay.user_id == current_user.id
    ).first()
    
    if not parlay:
        raise HTTPException(status_code=404, detail="Parlay not found")
    
    return {
        "id": parlay.id,
        "sport": parlay.sport,
        "name": parlay.name,
        "bet_amount": parlay.bet_amount,
        "total_odds": parlay.total_odds,
        "potential_payout": parlay.potential_payout,
        "potential_profit": parlay.potential_profit,
        "status": parlay.status.value,
        "selections_count": parlay.selections_count,
        "created_at": parlay.created_at.isoformat()
    }

@router.delete("/parlays/{parlay_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parlay(
    parlay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a parlay"""
    parlay = db.query(Parlay).filter(
        Parlay.id == parlay_id,
        Parlay.user_id == current_user.id
    ).first()
    
    if not parlay:
        raise HTTPException(status_code=404, detail="Parlay not found")
    
    db.delete(parlay)
    db.commit()