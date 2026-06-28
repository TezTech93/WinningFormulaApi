# routers/stats.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from managers.team_manager import TeamManager
from services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/team/{team_id}/trends")
async def get_team_trends(
    team_id: int,
    num_games: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get team trends from recent games"""
    team_manager = TeamManager(db)
    team = team_manager.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    stats_service = StatsService(db)
    trends = stats_service.get_team_trends(team_id, num_games)
    
    return {
        'team': {
            'id': team.id,
            'name': team.name,
            'abbreviation': team.abbreviation
        },
        'trends': trends,
        'games_analyzed': num_games
    }

@router.get("/team/{team_id}/recent")
async def get_team_recent_games(
    team_id: int,
    num_games: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a team's recent game results"""
    team_manager = TeamManager(db)
    team = team_manager.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    stats_service = StatsService(db)
    recent = stats_service.get_team_recent_performance(team_id, num_games)
    
    return {
        'team': {
            'id': team.id,
            'name': team.name,
            'abbreviation': team.abbreviation
        },
        'recent_games': recent,
        'count': len(recent)
    }

@router.get("/team/{team_id}/season/{year}")
async def get_team_season_stats(
    team_id: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a team's stats for a specific season"""
    team_manager = TeamManager(db)
    team = team_manager.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    stats_service = StatsService(db)
    stats = stats_service.get_team_stats_by_season(team_id, year)
    
    return {
        'team': {
            'id': team.id,
            'name': team.name,
            'abbreviation': team.abbreviation
        },
        'year': year,
        'stats': stats or {}
    }

@router.get("/team/head-to-head")
async def get_head_to_head(
    team1_id: int,
    team2_id: int,
    num_games: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get head-to-head results between two teams"""
    team_manager = TeamManager(db)
    team1 = team_manager.get_team_by_id(team1_id)
    team2 = team_manager.get_team_by_id(team2_id)
    
    if not team1 or not team2:
        raise HTTPException(status_code=404, detail="One or both teams not found")
    
    # Get head-to-head games
    gameline_manager = GamelineManager(db)
    games = db.query(Gameline).filter(
        or_(
            and_(
                Gameline.home_team_id == team1_id,
                Gameline.away_team_id == team2_id
            ),
            and_(
                Gameline.home_team_id == team2_id,
                Gameline.away_team_id == team1_id
            )
        ),
        Gameline.is_completed == True
    ).order_by(Gameline.game_date.desc()).limit(num_games).all()
    
    results = []
    team1_wins = 0
    team2_wins = 0
    
    for game in games:
        is_team1_home = game.home_team_id == team1_id
        team1_score = game.home_score if is_team1_home else game.away_score
        team2_score = game.away_score if is_team1_home else game.home_score
        
        if team1_score > team2_score:
            team1_wins += 1
        else:
            team2_wins += 1
        
        results.append({
            'date': game.game_date.isoformat(),
            'team1_score': team1_score,
            'team2_score': team2_score,
            'winner': team1.abbreviation if team1_score > team2_score else team2.abbreviation
        })
    
    return {
        'team1': {
            'id': team1.id,
            'name': team1.name,
            'abbreviation': team1.abbreviation,
            'wins': team1_wins
        },
        'team2': {
            'id': team2.id,
            'name': team2.name,
            'abbreviation': team2.abbreviation,
            'wins': team2_wins
        },
        'total_games': len(results),
        'recent_results': results
    }