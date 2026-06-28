# routers/gamelines.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from core.database import get_db
from core.dependencies import get_current_user
from managers.gameline_manager import GamelineManager
from services.sports_api import SportsAPIService
from models.user import User
from models.gameline import Gameline

router = APIRouter(prefix="/gamelines", tags=["gamelines"])
sports_api = SportsAPIService()

@router.get("/{sport}")
async def get_gamelines(
    sport: str,
    source: Optional[str] = Query(None, description="Sportsbook source"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get gamelines for a specific sport"""
    # First try to get from database cache
    gameline_manager = GamelineManager(db)
    db_gamelines = gameline_manager.get_gamelines_by_sport(sport, source)
    
    # If we have recent data (within 5 minutes), return it
    if db_gamelines and (datetime.now() - db_gamelines[0].updated_at).seconds < 300:
        return {
            'sport': sport,
            'source': source or 'cached',
            'games': [g.__dict__ for g in db_gamelines],
            'cached': True
        }
    
    # Otherwise fetch from API
    gamelines_data = await sports_api.fetch_gamelines(sport, source or 'espn_bets')
    if not gamelines_data:
        # Return cached data even if old
        if db_gamelines:
            return {
                'sport': sport,
                'source': source or 'cached',
                'games': [g.__dict__ for g in db_gamelines],
                'cached': True,
                'stale': True
            }
        raise HTTPException(status_code=404, detail=f"No gamelines found for {sport}")
    
    # Store in database
    for game in gamelines_data.get('games', []):
        gameline_manager.upsert_gameline({
            **game,
            'sport': sport,
            'source': source or 'espn_bets'
        })
    
    return gamelines_data

@router.get("/{sport}/game/{game_id}")
async def get_game_lines(
    sport: str,
    game_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get gamelines for a specific game"""
    gameline_manager = GamelineManager(db)
    gameline = gameline_manager.get_gamelines_by_game(game_id)
    if not gameline:
        raise HTTPException(status_code=404, detail="Game not found")
    return gameline.__dict__

@router.post("/refresh/{sport}")
async def refresh_gamelines(
    sport: str,
    source: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Force refresh gamelines from API"""
    gamelines_data = await sports_api.fetch_gamelines(sport, source or 'espn_bets')
    if not gamelines_data:
        raise HTTPException(status_code=404, detail=f"No gamelines found for {sport}")
    
    gameline_manager = GamelineManager(db)
    for game in gamelines_data.get('games', []):
        gameline_manager.upsert_gameline({
            **game,
            'sport': sport,
            'source': source or 'espn_bets'
        })
    
    return {'message': f'Gamelines refreshed for {sport}', 'count': len(gamelines_data.get('games', []))}