from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_current_user
from models.players import Player

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/")
async def get_players(
    sport: str = Query(..., description="Sport: nfl, nba, mlb, nhl, ncaaf, ncaab"),
    team_id: int = Query(None, description="Filter by team ID"),
    search: str = Query(None, description="Search by name"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Player).filter(Player.sport == sport)
    if team_id:
        query = query.filter(Player.team_id == team_id)
    if search:
        query = query.filter(
            (Player.first_name.ilike(f"%{search}%")) |
            (Player.last_name.ilike(f"%{search}%"))
        )
    players = query.order_by(Player.last_name, Player.first_name).all()
    return [{
        "id": p.id,
        "name": f"{p.first_name} {p.last_name}".strip(),
        "first_name": p.first_name,
        "last_name": p.last_name,
        "position": p.position,
        "team_id": p.team_id,
        "jersey_number": p.jersey_number,
    } for p in players]

@router.get("/nfl/csv")
async def get_nfl_players():
    from services.csv_players_service import get_all_nfl_players_from_csv
    all_nfl_players = get_all_nfl_players_from_csv()
    return {'players':all_nfl_players}