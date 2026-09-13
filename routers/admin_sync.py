# routers/admin_sync.py
"""
Admin-only sync endpoints.
Protect with the ADMIN_SYNC_TOKEN environment variable.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from services.odds_api_service import OddsAPIService
from services.sports_stats_fetcher import SportsStatsFetcher

router = APIRouter(prefix="/admin/sync", tags=["Admin Sync"])

odds_service = OddsAPIService()
stats_fetcher = SportsStatsFetcher()

SUPPORTED_SPORTS = ["nfl", "nba", "mlb", "nhl", "ncaaf", "ncaab"]


def require_admin_token(x_admin_token: str = Header(None)):
    """Simple header-based auth for admin sync endpoints."""
    if not settings.ADMIN_SYNC_TOKEN:
        raise HTTPException(500, "ADMIN_SYNC_TOKEN is not configured")
    if x_admin_token != settings.ADMIN_SYNC_TOKEN:
        raise HTTPException(403, "Invalid admin token")


# ---------------------------------------------------------------------- #
# Gamelines
# ---------------------------------------------------------------------- #
@router.post("/gamelines/{sport}")
async def sync_gamelines(
    sport: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_token),
):
    """Fetch gamelines for a sport from the Odds API and store them."""
    if sport not in SUPPORTED_SPORTS:
        raise HTTPException(400, f"Unsupported sport: {sport}")

    count = odds_service.store_gamelines(sport, db)
    return {"sport": sport, "stored": count}


@router.post("/gamelines/all")
async def sync_all_gamelines(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_token),
):
    results = {}
    for sport in SUPPORTED_SPORTS:
        try:
            results[sport] = odds_service.store_gamelines(sport, db)
        except Exception as e:
            results[sport] = f"error: {e}"
    return {"results": results}


# ---------------------------------------------------------------------- #
# Stats
# ---------------------------------------------------------------------- #
@router.post("/stats/{sport}/{year}")
async def sync_stats(
    sport: str,
    year: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_token),
):
    """Fetch stats for a sport/year and write per-team CSVs."""
    if sport not in SUPPORTED_SPORTS:
        raise HTTPException(400, f"Unsupported sport: {sport}")

    written = stats_fetcher.fetch_and_save(sport, year, db)
    return {"sport": sport, "year": year, "files_written": written}


@router.post("/stats/all/{year}")
async def sync_all_stats(
    year: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_token),
):
    results = {}
    for sport in SUPPORTED_SPORTS:
        try:
            results[sport] = stats_fetcher.fetch_and_save(sport, year, db)
        except Exception as e:
            results[sport] = f"error: {e}"
    return {"year": year, "results": results}

from managers.gameline_manager import GamelineManager

@router.post("/cleanup")
async def cleanup_gamelines(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_token),
):
    """Purge past games and remove duplicates."""
    gm = GamelineManager(db)
    dupes = gm.dedupe_gamelines()
    old = gm.purge_past_games(buffer_hours=3)
    return {
        "duplicates_removed": dupes,
        "past_games_removed": old,
    }