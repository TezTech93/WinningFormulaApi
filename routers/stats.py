# routers/stats.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.team import Team
from services.csv_stats_service import CSVStatsService

router = APIRouter(prefix="/stats", tags=["stats"])
csv_service = CSVStatsService()
SUPPORTED_SPORTS = ["nfl", "nba", "nhl", "mlb", "ncaaf", "ncaab"]

# ---------- Public Stats Endpoints ----------

@router.get("/team/season")
async def get_team_season_stats(
    sport: str = Query(..., description="Sport: nfl, nba, nhl, mlb, ncaaf, ncaab"),
    team_name: str = Query(..., description="Full team name (e.g., Detroit Lions)"),
    year: int = Query(..., description="Season year (e.g., 2025)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get season totals, averages, and record for a specific team from its CSV file.
    """
    if sport not in SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")

    # Look up team abbreviation from the database
    team = db.query(Team).filter(Team.sport == sport, Team.name == team_name).first()
    if not team:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_name}' not found in {sport}. Please check the name."
        )

    stats = csv_service.get_team_season_stats(sport, year, team.abbreviation)
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"No stats found for {team_name} ({team.abbreviation}) in {sport} {year}. The CSV file may be missing on GitHub or locally."
        )

    return {
        "team": team_name,
        "abbreviation": team.abbreviation,
        **stats  # includes sport, year, games_played, record, totals, averages
    }


@router.get("/team/trends")
async def get_team_trends(
    sport: str = Query(..., description="Sport"),
    team_name: str = Query(..., description="Full team name"),
    start_year: int = Query(2021, description="First year"),
    end_year: int = Query(2026, description="Last year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get season statistics across multiple years for a team.
    """
    if sport not in SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")

    team = db.query(Team).filter(Team.sport == sport, Team.name == team_name).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")

    results = []
    for year in range(start_year, end_year + 1):
        stats = csv_service.get_team_season_stats(sport, year, team.abbreviation)
        if stats:
            results.append(stats)

    return {
        "sport": sport,
        "team": team_name,
        "abbreviation": team.abbreviation,
        "years_range": [start_year, end_year],
        "seasons": results
    }


@router.get("/available")
async def get_available_files(
    sport: Optional[str] = Query(None, description="Filter by sport"),
    current_user: User = Depends(get_current_user)
):
    """
    List all CSV files currently cached locally.
    """
    if sport and sport not in SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")

    available = csv_service.list_available_files(sport)
    total = sum(len(teams) for years in available.values() for teams in years.values())
    return {
        "available": available,
        "total_files": total
    }


# ---------- Admin Sync Endpoints ----------

@router.post("/sync/{sport}/{year}/{abbr}")
async def sync_team_csv(
    sport: str,
    year: int,
    abbr: str,
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger download of a specific team's CSV from GitHub.
    """
    if sport not in SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")

    success = csv_service.download_csv(sport, year, abbr.upper())
    if success:
        return {"message": f"Successfully synced {sport}/{year}/{abbr.upper()}.csv"}
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync {sport}/{year}/{abbr.upper()}.csv. Check GitHub URL and network."
        )


@router.post("/sync/all")
async def sync_all_csv(
    current_user: User = Depends(get_current_user)
):
    """
    Sync all teams for all sports and all years (2021-2026).
    Note: This may take a while and hit GitHub rate limits.
    """
    results = {}
    for sport in SUPPORTED_SPORTS:
        results[sport] = {}
        # You would need a list of all team abbreviations per sport.
        # Since we don't have that here, we rely on the database.
        # Better to sync on demand (individual teams) rather than all.
        return {
            "message": "Use /sync/{sport}/{year}/{abbr} for individual teams, or implement a team list from the database."
        }
    return results

# routers/stats.py (add this)

@router.get("/games/{sport}/{year}/{abbr}")
async def get_team_game_stats(
    sport: str,
    year: int,
    abbr: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get raw game-by-game stats for a team from the CSV file.
    Returns a list of game rows with columns as keys.
    """
    if sport not in SUPPORTED_SPORTS:
        raise HTTPException(400, f"Unsupported sport: {sport}")

    # Optionally, validate that the team exists in the database
    team = db.query(Team).filter(Team.sport == sport, Team.abbreviation == abbr.upper()).first()
    if not team:
        raise HTTPException(404, f"Team '{abbr}' not found in {sport}")

    stats = csv_service.get_team_season_stats(sport, year, abbr)
    if not stats:
        raise HTTPException(404, f"No stats found for {abbr} in {sport} {year}")

    # Return the game rows
    return {
        "sport": sport,
        "year": year,
        "team": abbr.upper(),
        "games": stats.get("game_rows", []),
        "record": stats.get("record", {}),
        "totals": stats.get("totals", {}),
        "averages": stats.get("averages", {})
    }