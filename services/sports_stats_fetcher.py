# services/sports_stats_fetcher.py
"""
Fetches team stats for each supported sport using the appropriate package
and persists them BOTH to per-team CSVs and to the TeamStats DB table.

Paths and filenames match what CSVStatsService expects.
"""
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from sqlalchemy.orm import Session

import models  # noqa: F401 – registers all SQLAlchemy models
from core.config import settings
from models.team import Team, TeamStats

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")

# Baseball Reference codes used by pybaseball differ from ESPN codes.
PYBASEBALL_ABBR_MAP = {
    "CWS": "CHW",
    "KC":  "KCR",
    "SD":  "SDP",
    "SF":  "SFG",
    "TB":  "TBR",
    "WSH": "WSN",
}

# Columns that must NOT be summed when computing totals/averages.
NON_NUMERIC_COLS = {
    "Rk", "Gtm", "Date", "Opp", "Opponent", "Rslt", "Result",
    "Week", "Day", "Location", "Home", "W-L", "Streak",
    "Tm_Abbr", "G#", "Team", "Player",
}


# ====================================================================== #
# Aggregation helper (module-level so it is easy to unit-test)
# ====================================================================== #
def compute_aggregates(rows: list) -> dict:
    """
    Given raw game rows, compute record, totals, averages.
    Prefers the explicit `Rslt` column when present; otherwise falls back
    to comparing Tm vs Opp_Score.
    """
    record = {"W": 0, "L": 0, "T": 0}
    totals: dict = {}
    counts: dict = {}

    for row in rows:
        rslt = str(row.get("Rslt", "")).strip().upper()
        if rslt in ("W", "L", "T"):
            record[rslt] += 1
        else:
            try:
                tm = float(row.get("Tm", 0) or 0)
                opp = float(row.get("Opp_Score", 0) or 0)
                if tm > opp:
                    record["W"] += 1
                elif tm < opp:
                    record["L"] += 1
                else:
                    record["T"] += 1
            except (TypeError, ValueError):
                pass

        for col, val in row.items():
            if col in NON_NUMERIC_COLS:
                continue
            if val is None or val == "" or val == "-":
                continue
            try:
                num = float(val)
            except (TypeError, ValueError):
                continue
            totals.setdefault(col, 0.0)
            counts.setdefault(col, 0)
            totals[col] += num
            counts[col] += 1

    averages = {
        col: round(totals[col] / counts[col], 2)
        for col in totals
        if counts[col] > 0
    }
    return {
        "record": record,
        "totals": totals,
        "averages": averages,
        "games_played": len(rows),
    }


# ====================================================================== #
# Main fetcher class
# ====================================================================== #
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
        method = getattr(self, f"_fetch_{sport}", None)
        if method is None:
            logger.error("No fetcher implemented for sport: %s", sport)
            return 0
        return method(year, db)

    # ------------------------------------------------------------------ #
    # Persistence helper
    # ------------------------------------------------------------------ #
    def _persist(
        self,
        sport: str,
        year: int,
        team: Team,
        rows: list,
        db: Session,
    ) -> bool:
        """Write CSV + upsert into TeamStats."""
        if not rows:
            return False

        # 1) Local CSV cache (still useful; used as a fallback by CSVStatsService)
        path = self._team_csv_path(sport, year, team.abbreviation)
        self._write_rows(path, rows)

        # 2) Upsert into TeamStats
        agg = compute_aggregates(rows)
        payload = {
            "team_abbr": team.abbreviation.upper(),
            "sport": sport,
            "year": year,
            "games_played": agg["games_played"],
            "record": agg["record"],
            "totals": agg["totals"],
            "averages": agg["averages"],
            "game_rows": rows,
        }

        existing = (
            db.query(TeamStats)
            .filter(
                TeamStats.team_id == team.id,
                TeamStats.year == year,
                TeamStats.season_type == "regular",
            )
            .first()
        )
        if existing:
            existing.stats = payload
            existing.updated_at = datetime.utcnow()
        else:
            db.add(
                TeamStats(
                    team_id=team.id,
                    year=year,
                    season_type="regular",
                    stats=payload,
                )
            )
        db.commit()
        return True

    # ================================================================== #
    # NFL – nflreadpy
    # ================================================================== #
    def _fetch_nfl(self, year: int, db: Session) -> int:
        try:
            import nflreadpy as nfl
        except ImportError:
            logger.error("nflreadpy not installed")
            return 0

        logger.info("Fetching NFL schedules for %s", year)
        schedules = nfl.load_schedules(seasons=[year])
        df = schedules.to_pandas() if hasattr(schedules, "to_pandas") else schedules

        teams = db.query(Team).filter(Team.sport == "nfl").all()
        written = 0
        for team in teams:
            abbr = team.abbreviation.upper()
            mask = (df["home_team"] == abbr) | (df["away_team"] == abbr)
            games = df[mask]
            if games.empty:
                continue
            rows = self._nfl_games_to_rows(games, abbr)
            if self._persist("nfl", year, team, rows, db):
                written += 1
        logger.info("NFL: persisted %d team stat sets", written)
        return written

    def _nfl_games_to_rows(self, games, abbr: str) -> list:
        rows = []
        for _, g in games.iterrows():
            is_home = g["home_team"] == abbr
            team_score = g["home_score"] if is_home else g["away_score"]
            opp_score = g["away_score"] if is_home else g["home_score"]
            opp_name = g["away_team"] if is_home else g["home_team"]

            if team_score is None or opp_score is None:
                continue
            try:
                team_score = int(team_score)
                opp_score = int(opp_score)
            except (TypeError, ValueError):
                continue

            result = (
                "W" if team_score > opp_score
                else ("L" if team_score < opp_score else "T")
            )
            rows.append({
                "Rk": len(rows) + 1,
                "Gtm": g.get("week", ""),
                "Date": g.get("gameday", ""),
                "Opp": opp_name,
                "Opp_Score": opp_score,
                "Rslt": result,
                "Tm": team_score,
            })
        return rows

    # ================================================================== #
    # NBA – nba_api
    # ================================================================== #
    def _fetch_nba(self, year: int, db: Session) -> int:
        try:
            from nba_api.stats.endpoints import teamgamelogs
            from nba_api.stats.static import teams as nba_teams
        except ImportError:
            logger.error("nba_api not installed")
            return 0

        season = f"{year - 1}-{str(year)[2:]}"  # 2024-25
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
                rows = self._nba_df_to_rows(df)
                if self._persist("nba", year, team, rows, db):
                    written += 1
            except Exception as e:
                logger.warning("NBA fetch failed for %s: %s", team.abbreviation, e)
        logger.info("NBA: persisted %d team stat sets", written)
        return written

    def _nba_df_to_rows(self, df) -> list:
        rows = []
        for _, g in df.iterrows():
            wl = str(g.get("WL", "")).strip().upper()
            if wl not in ("W", "L", "T"):
                continue
            try:
                team_score = int(g.get("PTS", 0))
            except (TypeError, ValueError):
                continue

            # MATCHUP looks like "DET vs. CHI" or "DET @ CHI"
            matchup = str(g.get("MATCHUP", ""))
            opp = ""
            if " vs. " in matchup:
                opp = matchup.split(" vs. ")[-1]
            elif " @ " in matchup:
                opp = matchup.split(" @ ")[-1]

            rows.append({
                "Rk": len(rows) + 1,
                "Date": str(g.get("GAME_DATE", "")),
                "Opp": opp,
                "Tm": team_score,
                "Opp_Score": 0,
                "Rslt": wl,
                "MIN": g.get("MIN"),
                "FGM": g.get("FGM"),
                "FGA": g.get("FGA"),
                "FG_PCT": g.get("FG_PCT"),
                "FG3M": g.get("FG3M"),
                "FG3A": g.get("FG3A"),
                "FG3_PCT": g.get("FG3_PCT"),
                "FTM": g.get("FTM"),
                "FTA": g.get("FTA"),
                "FT_PCT": g.get("FT_PCT"),
                "OREB": g.get("OREB"),
                "DREB": g.get("DREB"),
                "REB": g.get("REB"),
                "AST": g.get("AST"),
                "STL": g.get("STL"),
                "BLK": g.get("BLK"),
                "TOV": g.get("TOV"),
                "PF": g.get("PF"),
                "PLUS_MINUS": g.get("PLUS_MINUS"),
            })
        return rows

    # ================================================================== #
    # MLB – pybaseball
    # ================================================================== #
    def _fetch_mlb(self, year: int, db: Session) -> int:
        try:
            from pybaseball import schedule_and_record
        except ImportError:
            logger.error("pybaseball not installed – run: pip install pybaseball")
            return 0

        db_teams = db.query(Team).filter(Team.sport == "mlb").all()
        written = 0
        for team in db_teams:
            abbr = team.abbreviation.upper()
            bb_code = PYBASEBALL_ABBR_MAP.get(abbr, abbr)
            try:
                df = schedule_and_record(year, bb_code)
            except Exception as e:
                logger.warning(
                    "MLB fetch failed for %s (code %s): %s", abbr, bb_code, e
                )
                continue
            if df is None or df.empty:
                continue
            rows = self._mlb_df_to_rows(df)
            if self._persist("mlb", year, team, rows, db):
                written += 1
        logger.info("MLB: persisted %d team stat sets", written)
        return written

    def _mlb_df_to_rows(self, df) -> list:
        rows = []
        for _, g in df.iterrows():
            wl = str(g.get("W/L", "")).strip().upper()
            if wl not in ("W", "L", "T"):
                continue
            try:
                team_score = int(g.get("R", 0))
                opp_score = int(g.get("RA", 0))
            except (TypeError, ValueError):
                continue
            rows.append({
                "Rk": len(rows) + 1,
                "Date": str(g.get("Date", "")),
                "Opp": str(g.get("Opp", "")).lstrip("@"),
                "Opp_Score": opp_score,
                "Rslt": wl,
                "Tm": team_score,
                "Home": str(g.get("Home", "")),
                "W-L": str(g.get("W-L", "")),
                "Streak": str(g.get("Streak", "")),
            })
        return rows

    # ================================================================== #
    # NHL – nhl-api-py
    # ================================================================== #
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
                schedule = client.teams.team_schedule(
                    team_abbr=team.abbreviation.upper()
                )
                games = (
                    schedule.get("games", [])
                    if isinstance(schedule, dict)
                    else []
                )
                if not games:
                    continue
                rows = self._nhl_games_to_rows(games, team.abbreviation)
                if self._persist("nhl", year, team, rows, db):
                    written += 1
            except Exception as e:
                logger.warning("NHL fetch failed for %s: %s", team.abbreviation, e)
        logger.info("NHL: persisted %d team stat sets", written)
        return written

    def _nhl_games_to_rows(self, games, team_abbr: str) -> list:
        rows = []
        abbr = team_abbr.upper()
        for g in games:
            home = g.get("homeTeam", {}) or {}
            away = g.get("awayTeam", {}) or {}
            is_home = home.get("abbrev", "").upper() == abbr
            team_score = home.get("score") if is_home else away.get("score")
            opp_score = away.get("score") if is_home else home.get("score")
            opp_name = away.get("abbrev") if is_home else home.get("abbrev")
            if team_score is None or opp_score is None:
                continue
            result = (
                "W" if team_score > opp_score
                else ("L" if team_score < opp_score else "T")
            )
            rows.append({
                "Rk": len(rows) + 1,
                "Date": g.get("gameDate", ""),
                "Opp": opp_name,
                "Opp_Score": opp_score,
                "Rslt": result,
                "Tm": team_score,
            })
        return rows

    # ================================================================== #
    # NCAAF – CFBD via direct HTTP (no SDK, no pydantic conflict)
    # ================================================================== #
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
            rows = self._ncaaf_games_to_rows(team_games, name)
            if self._persist("ncaaf", year, team, rows, db):
                written += 1
        logger.info("NCAAF: persisted %d team stat sets", written)
        return written

    def _ncaaf_games_to_rows(self, team_games, team_name: str) -> list:
        rows = []
        for g in team_games:
            is_home = g.get("homeTeam", "").lower() == team_name
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
                "Opp_Score": op,
                "Rslt": result,
                "Tm": tm,
            })
        return rows

    # ================================================================== #
    # NCAAB – CBBpy (scraper, no pydantic)
    # ================================================================== #
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
                    team=team.name, season=year,
                    info=True, box=True, pbp=False,
                )
                if info is None or info.empty:
                    continue
                rows = info.to_dict(orient="records")
                if self._persist("ncaab", year, team, rows, db):
                    written += 1
            except Exception as e:
                logger.warning("NCAAB fetch failed for %s: %s", team.abbreviation, e)
        logger.info("NCAAB: persisted %d team stat sets", written)
        return written

    # ================================================================== #
    # CSV writer
    # ================================================================== #
    def _write_rows(self, path: Path, rows: list) -> None:
        if not rows:
            return
        keys: list = []
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