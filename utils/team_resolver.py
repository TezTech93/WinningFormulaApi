# utils/team_resolver.py
import unicodedata
from sqlalchemy.orm import Session
from models.team import Team

def normalize_string(s: str) -> str:
    """Remove accents, convert to lowercase, strip extra spaces."""
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    return s.lower().strip()

def get_team_id(sport: str, search_name: str, db: Session, team_list=None) -> int:
    """
    Resolve a team name to its database ID.
    Uses the team_list (list of dicts with city, teamName, abv) to map
    normalized search strings to abbreviations, then looks up by abbreviation.
    """
    if not search_name:
        return None

    norm_search = normalize_string(search_name)
    teams = db.query(Team).filter(Team.sport == sport).all()

    # ---- Build mapping from normalized full name → abbreviation ----
    name_to_abbr = {}
    if team_list:
        for team in team_list:
            city = team.get('city', '').strip()
            tname = team.get('teamName', '').strip()
            abv = team.get('abv', '').upper()
            if city and tname:
                full = normalize_string(f"{city} {tname}")
                name_to_abbr[full] = abv
            # Also map by just teamName (e.g., "Tigers" – but beware duplicates)
            if tname:
                name_to_abbr[normalize_string(tname)] = abv
            # Also map by just city (e.g., "Merrimack")
            if city:
                name_to_abbr[normalize_string(city)] = abv

    # 1. Direct match via mapping → then look up by abbreviation
    if norm_search in name_to_abbr:
        abv = name_to_abbr[norm_search]
        team = db.query(Team).filter(Team.sport == sport, Team.abbreviation == abv).first()
        if team:
            return team.id

    # 2. Partial match: if search contains a known city/name or vice versa
    for key, abv in name_to_abbr.items():
        if norm_search in key or key in norm_search:
            team = db.query(Team).filter(Team.sport == sport, Team.abbreviation == abv).first()
            if team:
                return team.id

    # 3. Exact match on DB name (case‑insensitive)
    team = db.query(Team).filter(Team.sport == sport, Team.name.ilike(search_name)).first()
    if team:
        return team.id

    # 4. Partial match on DB name (substring)
    for t in teams:
        if norm_search in normalize_string(t.name) or normalize_string(t.name) in norm_search:
            return t.id

    # 5. Hardcoded overrides for name variations not caught above
    overrides = {
        # Format: normalized_search: "exact DB name"
        "merrimack warriors": "Merrimack Warriors",
        "tcu horned frogs": "TCU Horned Frogs",
        "uc davis aggies": "UC Davis Aggies",
        "stonehill skyhawks": "Stonehill Skyhawks",
        "hawai'i rainbow warriors": "Hawaii Rainbow Warriors",
        "north alabama lions": "North Alabama Lions",
        "mcneese cowboys": "McNeese Cowboys",
        "east texas a&m lions": "East Texas A&M Lions",
        "utah tech trailblazers": "Utah Tech Trailblazers",
        "massachusetts minutenmen": "UMass Minutemen",
        "arkansas-pine bluff golden lions": "Arkansas-Pine Bluff Golden Lions",
        "utah utes": "Utah Utes",
        "long island university sharks": "Long Island University Sharks",
        "miami hurricanes": "Miami Hurricanes",
        "fresno state bulldogs": "Fresno State Bulldogs",
        "pittsburgh panthers": "Pittsburgh Panthers",
        "ball state cardinals": "Ball State Cardinals",
        "kentucky wildcats": "Kentucky Wildcats",
        "ut rio grande valley vaqueros": "UTRGV Vaqueros",   # if not in DB, will fail
        "app state mountaineers": "Appalachian State Mountaineers",
        "nicholls colonels": "Nicholls State Colonels",
        "utah state aggies": "Utah State Aggies",
        "south florida bulls": "South Florida Bulls",
        "se louisiana lions": "Southeastern Louisiana Lions",
        "lsu tigers": "LSU Tigers",
        "ul monroe warhawks": "UL Monroe Warhawks",
        "mississippi valley state delta devils": "Mississippi Valley State Delta Devils",
        "wisconsin badgers": "Wisconsin Badgers",
        "smu mustangs": "SMU Mustangs",
    }
    if norm_search in overrides:
        target = overrides[norm_search]
        team = db.query(Team).filter(Team.sport == sport, Team.name.ilike(target)).first()
        if team:
            return team.id

    return None