# utils/seed_teams.py
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import SessionLocal
from models.team import Team

# Import team lists from the sports modules
# These files should exist at: sports/{sport}/{sport}_teams.py
# Each file must define a variable named exactly as the sport (e.g., nfl_teams)
try:
    from sports.nfl.nfl_teams import nfl_teams
except ImportError:
    nfl_teams = []
    logging.warning("Could not import nfl_teams from sports.nfl.nfl_teams")

try:
    from sports.nba.nba_teams import nba_teams
except ImportError:
    nba_teams = []
    logging.warning("Could not import nba_teams from sports.nba.nba_teams")

try:
    from sports.mlb.mlb_teams import mlb_teams
except ImportError:
    mlb_teams = []
    logging.warning("Could not import mlb_teams from sports.mlb.mlb_teams")

try:
    from sports.nhl.nhl_teams import nhl_teams
except ImportError:
    nhl_teams = []
    logging.warning("Could not import nhl_teams from sports.nhl.nhl_teams")

try:
    from sports.ncaab.ncaab_teams import ncaab_teams
except ImportError:
    ncaab_teams = []
    logging.warning("Could not import ncaab_teams from sports.ncaab.ncaab_teams")

try:
    from sports.ncaaf.ncaaf_teams import ncaaf_teams
except ImportError:
    ncaaf_teams = []
    logging.warning("Could not import ncaaf_teams from sports.ncaaf.ncaaf_teams")


logger = logging.getLogger(__name__)

# Map sport names to their team lists
ALL_TEAMS = {
    'nfl': nfl_teams,
    'nba': nba_teams,
    'mlb': mlb_teams,
    'nhl': nhl_teams,
    'ncaab': ncaab_teams,
    'ncaaf': ncaaf_teams,
}


def seed_teams(db: Session, sport: str = None):
    """
    Seed teams for a specific sport or all sports.

    Args:
        db: SQLAlchemy session
        sport: Optional sport name ('nfl', 'nba', 'mlb', 'nhl', 'ncaab', 'ncaaf')

    Returns:
        dict: Summary of seeded teams
    """
    results = {}

    sports_to_seed = [sport] if sport else ALL_TEAMS.keys()

    for sport_name in sports_to_seed:
        if sport_name not in ALL_TEAMS:
            logger.warning(f"Sport '{sport_name}' not found in team data")
            continue

        team_data = ALL_TEAMS[sport_name]
        if not team_data:
            logger.warning(f"No team data found for {sport_name}, skipping.")
            results[sport_name] = {'added': 0, 'skipped': 0, 'total': 0}
            continue

        added = 0
        skipped = 0

        for team_info in team_data:
            # Handle both 'abbreviation' and 'abv' keys
            abbr = team_info.get('abbreviation') or team_info.get('abv')
            if not abbr:
                logger.warning(f"Skipping team with no abbreviation: {team_info}")
                continue

            # Handle both 'name' and 'teamName' keys
            name = team_info.get('name') or team_info.get('teamName')
            if not name:
                logger.warning(f"Skipping team with no name: {team_info}")
                continue

            # Check if team already exists
            existing = db.query(Team).filter(
                Team.sport == sport_name,
                Team.abbreviation == abbr.upper()
            ).first()

            if existing:
                skipped += 1
                continue

            # Create new team
            team = Team(
                sport=sport_name,
                name=name,
                abbreviation=abbr.upper(),
                conference=team_info.get('conference'),
                division=team_info.get('division'),
                city=team_info.get('city'),
                state=team_info.get('state'),
                stadium=team_info.get('stadium'),
            )
            db.add(team)
            added += 1

        db.commit()
        results[sport_name] = {
            'added': added,
            'skipped': skipped,
            'total': len(team_data)
        }
        logger.info(f"Seeded {sport_name.upper()}: {added} added, {skipped} skipped")

    return results


def seed_nfl_teams(db: Session):
    """Seed only NFL teams"""
    return seed_teams(db, 'nfl')


def seed_all_teams(db: Session):
    """Seed all teams"""
    return seed_teams(db)


def get_team_id(db: Session, sport: str, abbreviation: str) -> int:
    """Get team ID by sport and abbreviation"""
    team = db.query(Team).filter(
        Team.sport == sport,
        Team.abbreviation == abbreviation.upper()
    ).first()
    return team.id if team else None


def get_team_mapping(db: Session, sport: str) -> dict:
    """Get mapping of abbreviation -> ID for a sport"""
    teams = db.query(Team).filter(Team.sport == sport).all()
    return {team.abbreviation: team.id for team in teams}


if __name__ == "__main__":
    # Run directly to seed all teams
    db = SessionLocal()
    try:
        print("Seeding teams...")
        results = seed_all_teams(db)
        print("\nSeeding Results:")
        for sport, data in results.items():
            print(f"  {sport.upper()}: {data['added']} added, {data['skipped']} skipped, {data['total']} total")
        print("\n✅ Teams seeded successfully!")
    except Exception as e:
        print(f"❌ Error seeding teams: {e}")
        db.rollback()
    finally:
        db.close()