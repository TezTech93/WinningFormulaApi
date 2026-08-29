# utils/team_resolver.py
import unicodedata
from sqlalchemy.orm import Session
from models.team import Team
from Sports.ncaaf.ncaaf_teams import ncaaf_teams  # for abbreviation mapping

def normalize_string(s: str) -> str:
    """Remove accents, convert to lowercase, strip extra spaces."""
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    return s.lower().strip()

def get_team_id(sport: str, name: str, db: Session, team_list=None) -> int:
    """
    Resolve a team name to its database ID using multiple strategies.
    team_list is optional – if provided, it's a list of dicts with 'abv' (abbreviation) and 'teamName'/'city'.
    """
    if not name:
        return None

    # 1. Exact match (case-insensitive)
    team = db.query(Team).filter(
        Team.sport == sport,
        Team.name.ilike(name)
    ).first()
    if team:
        return team.id

    # 2. Normalize (remove accents, lower)
    norm_name = normalize_string(name)
    teams = db.query(Team).filter(Team.sport == sport).all()
    for t in teams:
        if normalize_string(t.name) == norm_name:
            return t.id

    # 3. Partial match (if one contains the other)
    for t in teams:
        if norm_name in normalize_string(t.name) or normalize_string(t.name) in norm_name:
            # Prefer the shorter if it's a substring, but we'll take the first match
            return t.id

    # 4. Abbreviation lookup (from the team list)
    if team_list:
        for team_info in team_list:
            abv = team_info.get('abv', '').lower()
            if abv and (abv == norm_name or abv in norm_name or norm_name in abv):
                # Find the team in DB by abbreviation
                team = db.query(Team).filter(Team.sport == sport, Team.abbreviation == abv.upper()).first()
                if team:
                    return team.id

    # 5. Manual override for common mismatches
    overrides = {
        "san jose state spartans": "San Jose State Spartans",
        "san josé state spartans": "San Jose State Spartans",
        "albany great danes": "UAlbany Great Danes",
        "ualbany great danes": "UAlbany Great Danes",
        "app state mountaineers": "Appalachian State Mountaineers",
        "ul monroe warhawks": "Louisiana-Monroe Warhawks",
        "louisiana-monroe warhawks": "UL Monroe Warhawks",  # both directions
        "lsu tigers": "LSU Tigers",
        "smu mustangs": "SMU Mustangs",
        "uc davis aggies": "UC Davis Aggies",
        "ut rio grande valley vaqueros": "UTRGV Vaqueros",  # adjust if needed
        "se louisiana lions": "Southeastern Louisiana Lions",
        "mcneese cowboys": "McNeese State Cowboys",
        "nicholls colonels": "Nicholls State Colonels",
        "tennessee tech golden eagles": "Tennessee Tech Golden Eagles",
        "arkansas-pine bluff golden lions": "Arkansas-Pine Bluff Golden Lions",
        "massachusetts minutenmen": "UMass Minutemen",
        "minutemen": "UMass Minutemen",
        "merrimack warriors": "Merrimack Warriors",  # should match
        "stonehill skyhawks": "Stonehill Skyhawks",
        "idaho state bengals": "Idaho State Bengals",
        "north alabama lions": "North Alabama Lions",
        "tarleton state texans": "Tarleton State Texans",
        "utah tech trailblazers": "Utah Tech Trailblazers",
        "hawai'i rainbow warriors": "Hawaii Rainbow Warriors",
        "pittsburgh panthers": "Pittsburgh Panthers",
        "penn state nittany lions": "Penn State Nittany Lions",
        "kentucky wildcats": "Kentucky Wildcats",
        "wisonsin badgers": "Wisconsin Badgers",
        "florida state seminoles": "Florida State Seminoles",
        "east texas a&m lions": "East Texas A&M Lions",
        # Add more as you discover
        "nc state wolfpack": "North Carolina State Wolfpack",
        "tarleton state texans": "Tarleton State Texans",
        "ball state cardinals": "Ball State Cardinals",
        "kansas state wildcats": "Kansas State Wildcats",
        "lsu tigers": "LSU Tigers",
        "san diego state aztecs": "San Diego State Aztecs",
        "ualbany great danes": "UAlbany Great Danes",
        "new haven chargers": "New Haven Chargers",
        "west georgia wolves": "West Georgia Wolves",
    }

    # Check override using normalized name
    key = normalize_string(name)
    if key in overrides:
        override_name = overrides[key]
        team = db.query(Team).filter(Team.sport == sport, Team.name.ilike(override_name)).first()
        if team:
            return team.id

    # 6. Try to find by abbreviation directly from DB
    abbr_team = db.query(Team).filter(Team.sport == sport, Team.abbreviation.ilike(name)).first()
    if abbr_team:
        return abbr_team.id

    return None  # Not found