import argparse
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import models  # noqa: F401

from core.database import SessionLocal
from managers.gameline_manager import GamelineManager
from services.odds_api_service import OddsAPIService
from services.sports_stats_fetcher import SportsStatsFetcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SPORTS = ["nfl", "nba", "mlb", "nhl", "ncaaf", "ncaab"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sport", choices=SPORTS)
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--gamelines", action="store_true")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--cleanup-only", action="store_true",
                        help="Only purge/dedupe gamelines, no fetching")
    args = parser.parse_args()

    if not any([args.gamelines, args.stats, args.all, args.cleanup_only]):
        parser.error("Specify --gamelines, --stats, --all, or --cleanup-only")

    sports = [args.sport] if args.sport else SPORTS
    db = SessionLocal()

    try:
        # ---- Cleanup first, always ----
        gm = GamelineManager(db)
        removed_a = gm.dedupe_gamelines()          # by (game_id, source)
        removed_b = gm.dedupe_by_matchup()          # by (sport, date, home, away)
        removed_old = gm.purge_past_games(buffer_hours=3)
        logger.info(
            "Cleanup: %d id-dupes, %d matchup-dupes, %d past games",
            removed_a, removed_b, removed_old,
        )

        if args.cleanup_only:
            return

        if args.gamelines or args.all:
            svc = OddsAPIService()
            for sp in sports:
                count = svc.store_gamelines(sp, db)
                logger.info("[gamelines] %s: %d stored", sp, count)

        if args.stats or args.all:
            fetcher = SportsStatsFetcher()
            from datetime import datetime

            current_year = datetime.now().year   # e.g. 2026

            for sp in sports:
                # Try the current year first (in case the season has started)
                written = 0
                used_year = None

                if current_year != args.year:
                    try:
                        written = fetcher.fetch_and_save(sp, current_year, db)
                        used_year = current_year
                    except Exception as e:
                        logger.info("[stats] %s %d not available yet (%s); falling back to %d",
                                    sp, current_year, e, args.year)

                # Fall back to the user-provided year
                if not used_year:
                    try:
                        written = fetcher.fetch_and_save(sp, args.year, db)
                        used_year = args.year
                    except Exception as e:
                        logger.error("[stats] %s %d failed: %s", sp, args.year, e)
                        continue

                logger.info("[stats] %s %s: %d files", sp, used_year, written)

    finally:
        db.close()


if __name__ == "__main__":
    main()