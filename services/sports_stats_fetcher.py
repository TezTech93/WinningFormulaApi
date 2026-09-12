# services/sports_stats_fetcher.py
"""
Fetches team stats for each supported sport using the appropriate package
and writes per-team CSVs into data/{sport}/{year}/.

Paths and filenames match what CSVStatsService expects.
"""
import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from sqlalchemy.orm import Session
import models
from core.config import settings
from models.team import Team

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")


class SportsStatsFetcher:
    """Unified stats fetcher – one method per sport."""

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------------ #
    # Paths
    # ------------------------------------------------------------------ #
    def _team_csv_path(self, sport: str, year: int, abbr: str) -> Path:
        p = self.data_dir / sport / str(year) / f"{abbr.upper()}_{year}_stats.csv"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def fetch_and_save(self, sport: str, year: int, db: Session) -> int:
        """
        Fetch stats for all teams in the given sport/year and write per-team CSVs.
        Returns number of files written.
        """
        method = getattr(self, f"_fetch_{sport}", None)
        if method is None:
            logger.error("No fetcher implemented for sport: %s", sport)
            return 0
        return method(year, db)

    # ------------------------------------------------------------------ #
    # NFL – nflreadpy
    # ------------------------------------------------------------------ #
    def _fetch_nfl(self, year: int, db: Session) -> int:
        try:
            import nflreadpy as nfl
        except ImportError:
            logger.error("nflreadpy not installed")
            return 0

        logger.info("Fetching NFL schedules for %s", year)
        schedules = nfl.load_schedules(seasons=[year])
        df = schedules.to_pandas() if hasattr(schedules, "to_pandas") else schedules

        # Get team abbreviations from DB
        teams = db.query(Team).filter(Team.sport == "nfl").all()
        written = 0

        for team in teams:
            abbr = team.abbreviation.upper()
            # Filter games involving this team
            mask = (df["home_team"] == abbr) | (df["away_team"] == abbr)
            games = df[mask].copy()
            if games.empty:
                continue

            rows = self._nfl_games_to_rows(games, abbr)
            path = self._team_csv_path("nfl", year, abbr)
            self._write_rows(path, rows)
            written += 1

        logger.info("NFL: wrote %d team CSVs", written)
        return written

    def _nfl_games_to_rows(self, games, abbr: str):
        rows = []
        for _, g in games.iterrows():
            is_home = g["home_team"] == abbr
            team_score = g["home_score"] if is_home else g["away_score"]
            opp_score = g["away_score"] if is_home else g["home_score"]
            opp = g["away_team"] if is_home else g["home_team"]
            result = "W" if team_score > opp_score else ("L" if team_score < opp_score else "T")
            rows.append({
                "Rk": len(rows) + 1,
                "Gtm": g.get("week", ""),
                "Date": g.get("gameday", ""),
                "Opp": opp,
                "Rslt": result,
                "Tm": team_score,
                "Opp": opp_score,  # duplicated column – rename below
            })
        # rename second "Opp" to avoid collision – use Opp_Score
        for r in rows:
            r["Opp_Score"] = r.pop("Opp")
        return rows

    # ------------------------------------------------------------------ #
    # NBA – nba_api (one call per team game log)
    # ------------------------------------------------------------------ #
    def _fetch_nba(self, year: int, db: Session) -> int:
        try:
            from nba_api.stats.endpoints import teamgamelogs
            from nba_api.stats.static import teams as nba_teams
        except ImportError:
            logger.error("nba_api not installed")
            return 0

        season = f"{year - 1}-{str(year)[2:]}"  # e.g. 2024-25
        db_teams = db.query(Team).filter(Team.sport == "nba").all()
        id_map = {t["abbreviation"]: t["id"] for t in nba_teams.get_teams()}

        written = 0
        for team in db_teams:
            nba_id = id_map.get(team.abbreviation.upper())
            if not nba_id:
                continue
            try:
                logs = teamgamelogs.TeamGameLogs(
                    team_id_nullable=nba_id,
                    season_nullable=season,
                    season_type_nullable="Regular Season",
                )
                df = logs.get_data_frames()[0]
                if df.empty:
                    continue
                rows = df.to_dict(orient="records")
                path = self._team_csv_path("nba", year, team.abbreviation)
                self._write_rows(path, rows)
                written += 1
            except Exception as e:
                logger.warning("NBA fetch failed for %s: %s", team.abbreviation, e)
        logger.info("NBA: wrote %d team CSVs", written)
        return written

    # ------------------------------------------------------------------ #
    # MLB – pybaseball
    # ------------------------------------------------------------------ #
    def _fetch_mlb(self, year: int, db: Session) -> int:
        try:
            from pybaseball import schedule_and_record
        except ImportError:
            logger.error("pybaseball not installed")
            return 0

        db_teams = db.query(Team).filter(Team.sport == "mlb").all()
        written = 0
        for team in db_teams:
            try:
                df = schedule_and_record(year, team.abbreviation.upper())
                if df is None or df.empty:
                    continue
                rows = df.to_dict(orient="records")
                path = self._team_csv_path("mlb", year, team.abbreviation)
                self._write_rows(path, rows)
                written += 1
            except Exception as e:
                logger.warning("MLB fetch failed for %s: %s", team.abbreviation, e)
        logger.info("MLB: wrote %d team CSVs", written)
        return written

    # ------------------------------------------------------------------ #
    # NHL – nhl-api-py
    # ------------------------------------------------------------------ #
    def _fetch_nhl(self, year: int, db: Session) -> int:
        try:
            from nhlpy import NHLClient
        except ImportError:
            logger.error("nhl-api-py not installed")
            return 0

        client = NHLClient()
        db_teams = db.query(Team).filter(Team.sport == "nhl").all()
        written = 0
        for team in db_teams:
            try:
                schedule = client.teams.team_schedule(team_abbr=team.abbreviation.upper())
                games = schedule.get("games", []) if isinstance(schedule, dict) else []
                if not games:
                    continue
                rows = []
                for g in games:
                    rows.append({
                        "Date": g.get("gameDate", ""),
                        "Opp": g.get("opponent", {}).get("abbrev", ""),
                        "Tm": g.get("homeTeam", {}).get("score", 0),
                        "Opp_Score": g.get("awayTeam", {}).get("score", 0),
                    })
                path = self._team_csv_path("nhl", year, team.abbreviation)
                self._write_rows(path, rows)
                written += 1
            except Exception as e:
                logger.warning("NHL fetch failed for %s: %s", team.abbreviation, e)
        logger.info("NHL: wrote %d team CSVs", written)
        return written

    # ------------------------------------------------------------------ #
    # NCAAF – CFBD via direct HTTP (no SDK, no pydantic conflict)
    # ------------------------------------------------------------------ #
    def _fetch_ncaaf(self, year: int, db: Session) -> int:
        if not settings.CFBD_API_KEY:
            logger.error("CFBD_API_KEY not set – cannot fetch NCAAF")
            return 0

        headers = {
            "Authorization": f"Bearer {settings.CFBD_API_KEY}",
            "Accept": "application/json",
        }
        url = "https://api.collegefootballdata.com/games"
        params = {"year": year, "seasonType": "regular", "classification": "fbs"}

        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            r.raise_for_status()
            games = r.json()
        except Exception as e:
            logger.error("CFBD fetch failed: %s", e)
            return 0

        db_teams = db.query(Team).filter(Team.sport == "ncaaf").all()
        written = 0
        for team in db_teams:
            name = team.name.lower()
            team_games = [
                g for g in games
                if g.get("homeTeam", "").lower() == name
                or g.get("awayTeam", "").lower() == name
            ]
            if not team_games:
                continue

            rows = []
            for g in team_games:
                is_home = g.get("homeTeam", "").lower() == name
                tm = g.get("homePoints") if is_home else g.get("awayPoints")
                op = g.get("awayPoints") if is_home else g.get("homePoints")
                opp_name = g.get("awayTeam") if is_home else g.get("homeTeam")
                if tm is None or op is None:
                    continue
                result = "W" if tm > op else ("L" if tm < op else "T")
                rows.append({
                    "Rk": len(rows) + 1,
                    "Week": g.get("week", ""),
                    "Date": g.get("startDate", ""),
                    "Opp": opp_name,
                    "Rslt": result,
                    "Tm": tm,
                    "Opp_Score": op,
                })
            if rows:
                path = self._team_csv_path("ncaaf", year, team.abbreviation)
                self._write_rows(path, rows)
                written += 1
        logger.info("NCAAF: wrote %d team CSVs", written)
        return written

    # ------------------------------------------------------------------ #
    # NCAAB – CBBpy (scraper, no pydantic)
    # ------------------------------------------------------------------ #
    def _fetch_ncaab(self, year: int, db: Session) -> int:
        try:
            import cbbpy.mens_scraper as scraper
        except ImportError:
            logger.error("CBBpy not installed")
            return 0

        db_teams = db.query(Team).filter(Team.sport == "ncaab").all()
        written = 0
        for team in db_teams:
            try:
                info, box, _ = scraper.get_games_team(
                    team=team.name, season=year, info=True, box=True, pbp=False
                )
                if info is None or info.empty:
                    continue
                rows = info.to_dict(orient="records")
                path = self._team_csv_path("ncaab", year, team.abbreviation)
                self._write_rows(path, rows)
                written += 1
            except Exception as e:
                logger.warning("NCAAB fetch failed for %s: %s", team.abbreviation, e)
        logger.info("NCAAB: wrote %d team CSVs", written)
        return written

    # ------------------------------------------------------------------ #
    # CSV writer
    # ------------------------------------------------------------------ #
    def _write_rows(self, path: Path, rows: list):
        if not rows:
            return
        # Use the union of all keys, preserving first-seen order
        keys = []
        for row in rows:
            for k in row.keys():
                if k not in keys:
                    keys.append(k)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        logger.debug("Wrote %s (%d rows)", path, len(rows))