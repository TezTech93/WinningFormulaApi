import csv, requests
from core.database import SessionLocal
from models.player import Player
from models.team import Team

def import_nfl_players():
    db = SessionLocal()
    # Download from NFLverse
    url = "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv"
    resp = requests.get(url)
    resp.raise_for_status()
    reader = csv.DictReader(resp.text.splitlines())

    count = 0
    for row in reader:
        full_name = row.get('full_name', '').strip()
        if not full_name:
            continue
        # Parse first/last name (simplified)
        parts = full_name.split(',')
        if len(parts) == 2:
            last_name = parts[0].strip()
            first_name = parts[1].strip()
        else:
            first_name = full_name
            last_name = ''
        team_abbr = row.get('team_abbr', '').strip()
        # Find team ID
        team = db.query(Team).filter(Team.sport == 'nfl', Team.abbreviation == team_abbr).first()
        team_id = team.id if team else None

        player = Player(
            sport='nfl',
            team_id=team_id,
            first_name=first_name,
            last_name=last_name,
            position=row.get('position', '').strip(),
            jersey_number=row.get('jersey_number', '').strip(),
            stats={
                'college': row.get('college_name', '').strip(),
                'rookie_season': row.get('rookie_season', ''),
                'years_of_experience': row.get('years_of_experience', '')
            }
        )
        db.add(player)
        count += 1
        if count % 500 == 0:
            db.commit()
    db.commit()
    db.close()
    print(f"✅ Imported {count} NFL players")

if __name__ == "__main__":
    import_nfl_players()