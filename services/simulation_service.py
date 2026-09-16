# services/simulation_service.py
"""
Applies a saved formula to upcoming games using Monte Carlo.
"""
import logging
import random
import re
from typing import Dict, List, Any, Optional

from sqlalchemy.orm import Session

from models.formula import UserFormula
from models.gamelines import Gameline
from services.csv_stats_service import CSVStatsService

logger = logging.getLogger(__name__)


class SimulationService:
    def __init__(self, db: Session):
        self.db = db
        self.csv = CSVStatsService()

    # ------------------------------------------------------------------ #
    def run(
        self,
        formula_id: int,
        game_ids: List[str],
        sport: str,
        randomness: float = 0.2,
        iterations: int = 1000,
    ) -> List[Dict[str, Any]]:
        formula: Optional[UserFormula] = self.db.query(UserFormula).filter(UserFormula.id == formula_id).first()
        if not formula:
            return []

        games = self.db.query(Gameline).filter(Gameline.id.in_(game_ids)).all()
        results = []
        for game in games:
            home_stats = self._team_averages(sport, game.home_abbr)
            away_stats = self._team_averages(sport, game.away_abbr)
            if not home_stats or not away_stats:
                results.append(self._empty_result(game))
                continue
            results.append(
                self._simulate_one(formula, game, home_stats, away_stats, randomness, iterations)
            )
        return results

    # ------------------------------------------------------------------ #
    def _team_averages(self, sport: str, abbr: str) -> Optional[Dict[str, float]]:
        stats = self.csv.get_team_season_stats(sport, 2025, abbr)
        if not stats:
            return None
        return {k: float(v) for k, v in stats["averages"].items() if isinstance(v, (int, float, str)) and str(v).replace('.', '', 1).lstrip('-').isdigit()}

    def _simulate_one(self, formula, game, home_avg, away_avg, randomness, iterations):
        try:
            expr = formula.formula
            # Substitute known stats; unknown stats = 0
            def evaluate(stats):
                env = {**stats}
                # Apply randomness: multiply each stat by (1 ± randomness)
                env = {k: v * (1 + random.uniform(-randomness, randomness)) for k, v in env.items()}
                # Sanitize expression: keep only identifiers, numbers, operators
                safe = re.sub(r'[^A-Za-z0-9_+\-*/().\s]', '', expr)
                try:
                    return float(eval(safe, {"__builtins__": {}}, env))
                except Exception:
                    return 0.0

            home_scores = [evaluate(home_avg) for _ in range(iterations)]
            away_scores = [evaluate(away_avg) for _ in range(iterations)]

            home_win_pct = sum(1 for h, a in zip(home_scores, away_scores) if h > a) / iterations
            avg_margin = sum(h - a for h, a in zip(home_scores, away_scores)) / iterations
            avg_total = sum(h + a for h, a in zip(home_scores, away_scores)) / iterations

            return {
                "game_id": game.id,
                "home_abbr": game.home_abbr,
                "away_abbr": game.away_abbr,
                "home_win_probability": round(home_win_pct, 4),
                "away_win_probability": round(1 - home_win_pct, 4),
                "predicted_spread": round(-avg_margin, 2),  # home - away
                "predicted_total": round(avg_total, 2),
                "formula_id": formula.id,
                "formula_name": formula.formula_name,
            }
        except Exception as e:
            logger.error("Simulation failed for game %s: %s", game.id, e)
            return self._empty_result(game)

    def _empty_result(self, game):
        return {
            "game_id": game.id,
            "home_abbr": game.home_abbr,
            "away_abbr": game.away_abbr,
            "home_win_probability": None,
            "away_win_probability": None,
            "predicted_spread": None,
            "predicted_total": None,
            "error": "Insufficient data",
        }