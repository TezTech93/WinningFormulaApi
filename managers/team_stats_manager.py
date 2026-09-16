# managers/team_stats_manager.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from models.team import Team, TeamStats

logger = logging.getLogger(__name__)


class TeamStatsManager:
    def __init__(self, db: Session):
        self.db = db

    def upsert_stats(
        self,
        team_id: int,
        year: int,
        payload: Dict[str, Any],
        season_type: str = "regular",
    ) -> TeamStats:
        """Insert or update TeamStats for (team_id, year, season_type)."""
        existing = (
            self.db.query(TeamStats)
            .filter(
                TeamStats.team_id == team_id,
                TeamStats.year == year,
                TeamStats.season_type == season_type,
            )
            .first()
        )
        if existing:
            existing.stats = payload
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        row = TeamStats(
            team_id=team_id,
            year=year,
            season_type=season_type,
            stats=payload,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_stats(
        self,
        team_id: int,
        year: int,
        season_type: str = "regular",
    ) -> Optional[Dict[str, Any]]:
        row = (
            self.db.query(TeamStats)
            .filter(
                TeamStats.team_id == team_id,
                TeamStats.year == year,
                TeamStats.season_type == season_type,
            )
            .first()
        )
        return row.stats if row else None

    def get_stats_by_abbr(
        self,
        sport: str,
        abbr: str,
        year: int,
        season_type: str = "regular",
    ) -> Optional[Dict[str, Any]]:
        team = (
            self.db.query(Team)
            .filter(Team.sport == sport, Team.abbreviation == abbr.upper())
            .first()
        )
        if not team:
            return None
        return self.get_stats(team.id, year, season_type)

        @staticmethod
    def compute_aggregates(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Given raw game rows (each with keys like Tm, Opp_Score, Rslt, ...),
        return {record, totals, averages, games_played}.
        """
        record = {"W": 0, "L": 0, "T": 0}
        totals: Dict[str, float] = {}
        counts: Dict[str, int] = {}
        SKIP = {"Opp", "Opponent", "Date", "Gtm", "Week", "Day",
                "Rslt", "Result", "Location", "Home", "W-L", "Streak"}

        for row in rows:
            tm = row.get("Tm")
            opp = row.get("Opp_Score")
            try:
                tm_f = float(tm)
                opp_f = float(opp)
                if tm_f > opp_f:
                    record["W"] += 1
                elif tm_f < opp_f:
                    record["L"] += 1
                else:
                    record["T"] += 1
            except (TypeError, ValueError):
                pass

            for col, val in row.items():
                if col in SKIP:
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
            for col in totals if counts[col] > 0
        }
        return {
            "record": record,
            "totals": totals,
            "averages": averages,
            "games_played": len(rows),
        }