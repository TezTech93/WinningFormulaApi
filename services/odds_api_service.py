# services/odds_api_service.py
"""
Fetches upcoming gamelines from the-odds-api.com and prepares them
for storage via GamelineManager.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
from sqlalchemy.orm import Session
import models
from core.config import settings
from models.team import Team

logger = logging.getLogger(__name__)


class OddsAPIService:
    BASE_URL = "https://api.the-odds-api.com/v4/sports"

    # Map internal sport codes to Odds API keys
    SPORT_KEY_MAP = {
        "nfl":   "americanfootball_nfl",
        "nba":   "basketball_nba",
        "mlb":   "baseball_mlb",
        "nhl":   "icehockey_nhl",
        "ncaaf": "americanfootball_ncaaf",
        "ncaab": "basketball_ncaab",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ODDS_API_KEY
        if not self.api_key:
            logger.warning("ODDS_API_KEY is not set – Odds API calls will fail.")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def fetch_gamelines(self, sport: str) -> List[Dict[str, Any]]:
        """Return a list of gameline dicts ready for GamelineManager.upsert_gameline."""
        sport_key = self.SPORT_KEY_MAP.get(sport)
        if not sport_key:
            logger.error("Unsupported sport for Odds API: %s", sport)
            return []

        params = {
            "apiKey": self.api_key,
            "regions": "us",
            "oddsFormat": "american",
            "markets": "h2h,spreads,totals",
        }
        url = f"{self.BASE_URL}/{sport_key}/odds"

        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.error("Odds API request failed for %s: %s", sport, e)
            return []

        games: List[Dict[str, Any]] = []
        for event in data:
            game = self._parse_event(event, sport)
            if game:
                games.append(game)

        logger.info("Odds API: fetched %d games for %s", len(games), sport)
        return games

    def store_gamelines(
        self,
        sport: str,
        db: Session,
        games: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """Fetch (or accept pre-fetched) games, resolve team IDs, and upsert."""
        from managers.gameline_manager import GamelineManager

        if games is None:
            games = self.fetch_gamelines(sport)

        if not games:
            return 0

        manager = GamelineManager(db)
        stored = 0

        for game in games:
            game = self._resolve_teams(game, db)
            # Skip games whose teams we couldn't resolve
            if game.get("home_team_id") is None or game.get("away_team_id") is None:
                logger.debug("Skipping unresolved game: %s vs %s",
                             game.get("away_team_id"), game.get("home_team_id"))
                continue

            if not game.get("game_id"):
                game["game_id"] = f"{sport}_{datetime.utcnow().timestamp()}"

            manager.upsert_gameline(game)
            stored += 1

        db.commit()
        logger.info("Stored %d gamelines for %s", stored, sport)
        return stored

    # ------------------------------------------------------------------ #
    # Parsing / helpers
    # ------------------------------------------------------------------ #

    def _parse_event(self, event: Dict[str, Any], sport: str) -> Optional[Dict[str, Any]]:
        home_team = event.get("home_team") or ""
        away_team = event.get("away_team") or ""
        game_id = event.get("id")
        commence = event.get("commence_time")

        game_date = None
        start_time = None
        if commence:
            try:
                dt = datetime.fromisoformat(commence.replace("Z", "+00:00"))
                game_date = dt.isoformat()
                start_time = dt.strftime("%I:%M %p")
            except Exception:
                pass

        bookmakers = event.get("bookmakers", [])
        if not bookmakers:
            return None
        # Prefer DraftKings, otherwise first book
        book = next((b for b in bookmakers if b.get("key") == "draftkings"), bookmakers[0])
        markets = {m.get("key"): m for m in book.get("markets", [])}

        def outcome(market_key: str, name: str):
            m = markets.get(market_key)
            if not m:
                return None
            for o in m.get("outcomes", []):
                if o.get("name") == name:
                    return o
            return None

        h2h_home = outcome("h2h", home_team)
        h2h_away = outcome("h2h", away_team)
        sp_home = outcome("spreads", home_team)
        sp_away = outcome("spreads", away_team)
        over = outcome("totals", "Over")
        under = outcome("totals", "Under")

        return {
            "sport": sport,
            "source": "odds_api",
            "game_id": game_id,
            "game_date": game_date,
            "start_time": start_time,
            # store names for now – resolver converts to IDs
            "home_team_id": home_team,
            "away_team_id": away_team,
            "home_abbr": None,
            "away_abbr": None,
            "home_ml": h2h_home.get("price") if h2h_home else None,
            "away_ml": h2h_away.get("price") if h2h_away else None,
            "home_spread": sp_home.get("point") if sp_home else None,
            "away_spread": sp_away.get("point") if sp_away else None,
            "home_spread_odds": sp_home.get("price") if sp_home else None,
            "away_spread_odds": sp_away.get("price") if sp_away else None,
            "total": over.get("point") if over else None,
            "over_odds": over.get("price") if over else None,
            "under_odds": under.get("price") if under else None,
        }

    def _resolve_teams(self, game: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Convert team names/abbrs to team IDs using the Team table."""
        sport = game.get("sport")
        if not sport:
            return game

        for side in ("home", "away"):
            key_id = f"{side}_team_id"
            key_abbr = f"{side}_abbr"
            val = game.get(key_id)

            if isinstance(val, int):
                # Already resolved
                continue
            if not val:
                continue

            team = (
                db.query(Team)
                .filter(
                    Team.sport == sport,
                    (Team.name.ilike(val)) | (Team.abbreviation.ilike(val)),
                )
                .first()
            )
            if team:
                game[key_id] = team.id
                game[key_abbr] = team.abbreviation
            else:
                game[key_id] = None

        return game