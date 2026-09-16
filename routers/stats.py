# routers/stats.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.team import Team, TeamStats
from services.csv_stats_service import CSVStatsService

router = APIRouter(prefix="/stats", tags=["stats"])
csv_service = CSVStatsService()
SUPPORTED_SPORTS = ["nfl", "nba", "nhl", "mlb", "ncaaf", "ncaab"]


# ---------- Slug → DB abbreviation map ----------
# Lets the API accept both DB codes ("OSU") and human slugs ("ohio-state").
SLUG_TO_ABBR = {
    "ncaaf": {
        "ohio-state": "OSU",
        "michigan-state": "MSU",
        "penn-state": "PSU",
        "notre-dame": "ND",
        "north-carolina": "UNC",
        "north-carolina-state": "NCST",
        "florida-state": "FSU",
        "wake-forest": "WAKE",
        "virginia-tech": "VT",
        "boise-state": "BSU",
        "fresno-state": "FRES",
        "san-diego-state": "SDSU",
        "san-jose-state": "SJSU",
        "colorado-state": "CSU",
        "washington-state": "WSU",
        "oregon-state": "ORST",
        "arizona-state": "ASU",
        "iowa-state": "ISU",
        "kansas-state": "KSU",
        "oklahoma-state": "OKST",
        "app-state": "APP",
        "georgia-state": "GAST",
        "kennesaw-state": "KENN",
        "jacksonville-state": "JVST",
        "new-mexico-state": "NMSU",
        "sam-houston": "SHSU",
        "utah-state": "USU",
        "weber-state": "WEB",
        "youngstown-state": "YSU",
    },
    "ncaab": {
        "michigan-state": "MSU",
        "ohio-state": "OSU",
        "penn-state": "PSU",
        "notre-dame": "ND",
        "north-carolina": "UNC",
        "nc-state": "NCST",
        "florida-state": "FSU",
        "wake-forest": "WAKE",
        "virginia-tech": "VT",
        "boise-state": "BSU",
        "fresno-state": "FRES",
        "san-diego-state": "SDSU",
        "colorado-state": "CSU",
        "washington-state": "WSU",
        "oregon-state": "ORST",
        "arizona-state": "ASU",
        "iowa-state": "ISU",
        "kansas-state": "KSU",
        "oklahoma-state": "OKST",
        "georgia-state": "GAST",
        "wichita-state": "WICH",
        "murray-state": "MURR",
        "indiana-state": "INST",
        "illinois-state": "ILST",
        "missouri-state": "MOSU",
        "north-dakota-state": "NDSU",
        "south-dakota-state": "SDSU",
        "sam-houston-state": "SHSU",
    },
    "nfl": {
        "green-bay": "GB",
        "new-england": "NE",
        "new-york-giants": "NYG",
        "new-york-jets": "NYJ",
        "san-francisco": "SF",
        "tampa-bay": "TB",
        "kansas-city": "KC",
    },
    "mlb": {
        "new-york-yankees": "NYY",
        "new-york-mets": "NYM",
        "chicago-white-sox": "CWS",
        "chicago-cubs": "CHC",
        "los-angeles-angels": "LAA",
        "los-angeles-dodgers": "LAD",
        "san-francisco": "SF",
        "san-diego": "SD",
        "tampa-bay": "TB",
        "kansas-city": "KC",
        "st-louis": "STL",
    },
    "nba": {
        "los-angeles-lakers": "LAL",
        "los-angeles-clippers": "LAC",
        "golden-state": "GSW",
        "new-york-knicks": "NYK",
        "brooklyn": "BKN",
        "san-antonio": "SAS",
        "oklahoma-city": "OKC",
        "new-orleans": "NOP",
        "portland": "POR",
    },
    "nhl": {
        "detroit": "DET",
        "toronto": "TOR",
        "montreal": "MTL",
        "new-york-rangers": "NYR",
        "new-york-islanders": "NYI",
        "new-jersey": "NJD",
        "tampa-bay": "TB",
        "los-angeles": "LAK",
        "san-jose": "SJS",
    },
}


def _resolve_abbr(sport: str, abbr: str) -> str:
    """Accept either a DB abbreviation ('OSU') or a slug ('ohio-state')."""
    a = abbr.upper().strip()
    slug = abbr.lower().strip()
    mapping = SLUG_TO_ABBR.get(sport, {})
    return mapping.get(slug, a)


# ---------- Public Stats Endpoints ----------

@router.get("/team/season")
async def get_team_season_stats(
    sport: str = Query(..., description="Sport: nfl, nba, nhl, mlb, ncaaf, ncaab"),
    team_name: str = Query(..., description="Full team name (e.g., Detroit Lions)"),
    year: int = Query(..., description="Season year (e.g., 2025)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if sport not in SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")

    team = db.query(Team).filter(Team.sport == sport, Team.name == team_name).first()
    if not team:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_name}' not found in {sport}. Please check the name.",
        )

    stats = csv_service.get_team_season_stats(sport, year, team.abbreviation)
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"No stats found for {team_name} ({team.abbreviation}) in {sport} {year}.",
        )

    return {"team": team_name, "abbreviation": team.abbreviation, **stats}


@router.get("/team/trends")
async def get_team_trends(
    sport: str = Query(..., description="Sport"),
    team_name: str = Query(..., description="Full team name"),
    start_year: int = Query(2021, description="First year"),
    end_year: int = Query(2026, description="Last year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
        "seasons": results,
    }


@router.get("/available")
async def get_available_files(
    sport: Optional[str] = Query(None, description="Filter by sport"),
    current_user: User = Depends(get_current_user),
):
    if sport and sport not in SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
    available = csv_service.list_available_files(sport)
    total = sum(len(teams) for years in available.values() for teams in years.values())
    return {"available": available, "total_files": total}


# ---------- Admin Sync Endpoints ----------

@router.post("/sync/{sport}/{year}/{abbr}")
async def sync_team_csv(
    sport: str,
    year: int,
    abbr: str,
    current_user: User = Depends(get_current_user),
):
    if sport not in SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")

    success = csv_service.download_csv(sport, year, abbr.upper())
    if success:
        return {"message": f"Successfully synced {sport}/{year}/{abbr.upper()}.csv"}
    raise HTTPException(
        status_code=500,
        detail=f"Failed to sync {sport}/{year}/{abbr.upper()}.csv.",
    )


@router.post("/sync/all")
async def sync_all_csv(current_user: User = Depends(get_current_user)):
    return {
        "message": "Use /sync/{sport}/{year}/{abbr} for individual teams."
    }


# ---------- Game-by-game stats (DB first, CSV fallback) ----------

@router.get("/games/{sport}/{year}/{abbr}")
async def get_team_game_stats(
    sport: str,
    year: int,
    abbr: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if sport not in SUPPORTED_SPORTS:
        raise HTTPException(400, f"Unsupported sport: {sport}")

    resolved = _resolve_abbr(sport, abbr)

    team = (
        db.query(Team)
        .filter(Team.sport == sport, Team.abbreviation == resolved)
        .first()
    )
    if not team:
        raise HTTPException(404, f"Team '{abbr}' not found in {sport}")

    # 1) DB first
    row = (
        db.query(TeamStats)
        .filter(
            TeamStats.team_id == team.id,
            TeamStats.year == year,
            TeamStats.season_type == "regular",
        )
        .first()
    )
    if row and row.stats:
        return {
            "sport": sport,
            "year": year,
            "team": team.abbreviation,
            "source": "database",
            **row.stats,
        }

    # 2) CSV fallback
    stats = csv_service.get_team_season_stats(sport, year, team.abbreviation)
    if not stats:
        raise HTTPException(404, f"No stats found for {team.abbreviation} in {sport} {year}")

    return {
        "sport": sport,
        "year": year,
        "team": team.abbreviation,
        "source": "csv",
        "games": stats.get("game_rows", []),
        "record": stats.get("record", {}),
        "totals": stats.get("totals", {}),
        "averages": stats.get("averages", {}),
        "games_played": stats.get("games_played", 0),
    }