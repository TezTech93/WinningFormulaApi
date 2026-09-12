# utils/sync_sports_data.py
"""
CLI to sync gamelines and stats.

Usage:
  python -m utils.sync_sports_data --gamelines --sport nfl
  python -m utils.sync_sports_data --stats --sport nba --year 2025
  python -m utils.sync_sports_data --all --year 2025
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

# ---- IMPORTANT: import all models so SQLAlchemy registers every class ----
import models  # noqa: F401  (this triggers models/__init__.py which imports every model)

from core.database import SessionLocal
from services.odds_api_service import OddsAPIService
from services.sports_stats_fetcher import SportsStatsFetcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SPORTS = ["nfl", "nba", "mlb", "nhl", "ncaaf", "ncaab"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sport", choices=SPORTS, help="Single sport")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--gamelines", action="store_true")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--all", action="store_true", help="Both gamelines and stats for all sports")
    args = parser.parse_args()

    if not any([args.gamelines, args.stats, args.all]):
        parser.error("Specify --gamelines, --stats, or --all")

    sports = [args.sport] if args.sport else SPORTS
    db = SessionLocal()

    try:
        if args.gamelines or args.all:
            svc = OddsAPIService()
            for sp in sports:
                count = svc.store_gamelines(sp, db)
                logger.info("[gamelines] %s: %d stored", sp, count)

        if args.stats or args.all:
            fetcher = SportsStatsFetcher()
            for sp in sports:
                written = fetcher.fetch_and_save(sp, args.year, db)
                logger.info("[stats] %s %s: %d files", sp, args.year, written)
    finally:
        db.close()


if __name__ == "__main__":
    main()