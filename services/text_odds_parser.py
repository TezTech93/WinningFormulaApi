import re
import json
from datetime import datetime

def parse_team_block(lines, start_idx):
    """
    Expects 9 lines starting at start_idx:
    [team_name, record, spread1, odds1, spread2, odds2, total, total_odds, ml]
    Returns dict and the next index (start_idx + 9).
    """
    if start_idx + 8 >= len(lines):
        return None, start_idx

    team_name = lines[start_idx].strip()
    # record = lines[start_idx + 1].strip()  # not used
    spread_str = lines[start_idx + 2].strip()
    odds1_str = lines[start_idx + 3].strip()
    # spread2 and odds2 are ignored (alternate spread)
    total_str = lines[start_idx + 6].strip()
    total_odds_str = lines[start_idx + 7].strip()
    ml_str = lines[start_idx + 8].strip()

    def to_float(v):
        if v == '--' or not v:
            return None
        try:
            return float(v)
        except ValueError:
            return None

    def to_int(v):
        if v == '--' or not v:
            return None
        try:
            return int(v)
        except ValueError:
            return None

    spread = to_float(spread_str)
    spread_odds = to_int(odds1_str)
    total = None
    total_odds = None
    if total_str.startswith(('o', 'u')):
        total = to_float(total_str[1:])
        total_odds = to_int(total_odds_str)
    ml = to_int(ml_str)

    return {
        'team_name': team_name,
        'spread': spread,
        'spread_odds': spread_odds,
        'total': total,
        'total_odds': total_odds,
        'moneyline': ml
    }, start_idx + 9

def parse_games_from_text(content):
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    games = []
    i = 0
    current_date = None

    while i < len(lines):
        line = lines[i]

        # Check for date line (e.g., "Friday, August 28")
        date_match = re.match(r'^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),', line)
        if date_match:
            current_date = line
            i += 1
            continue

        # Check for time line (e.g., "5:00 PM", "11:00 AM")
        time_match = re.match(r'^(\d{1,2}:\d{2}\s*(AM|PM))', line, re.I)
        if time_match and current_date is not None:
            time_str = line
            i += 1

            # Skip the four header lines: Open, Spread, Total, ML
            # They may appear as separate lines; skip exactly those words
            for _ in range(4):
                if i < len(lines) and lines[i] in ('Open', 'Spread', 'Total', 'ML'):
                    i += 1
                else:
                    # If not found, break to avoid infinite loop
                    break

            # Parse home team (9 lines)
            home_data, i = parse_team_block(lines, i)
            if not home_data:
                break

            # Parse away team (9 lines)
            away_data, i = parse_team_block(lines, i)
            if not away_data:
                break

            # Convert date to YYYY-MM-DD
            try:
                date_part = re.sub(r'^[A-Za-z]+, ', '', current_date)  # "August 28"
                dt = datetime.strptime(f"{date_part} {datetime.now().year}", "%B %d %Y")
                game_date = dt.strftime("%Y-%m-%d")
            except:
                game_date = datetime.now().strftime("%Y-%m-%d")

            game = {
                "game_date": game_date,
                "start_time": time_str,
                "home_team_id": home_data['team_name'],
                "away_team_id": away_data['team_name'],
                "home_abbr": None,
                "away_abbr": None,
                "home_ml": home_data['moneyline'],
                "away_ml": away_data['moneyline'],
                "home_spread": home_data['spread'],
                "away_spread": away_data['spread'],
                "home_spread_odds": home_data['spread_odds'],
                "away_spread_odds": away_data['spread_odds'],
                "total": home_data['total'] or away_data['total'],
                "over_odds": home_data['total_odds'] if home_data['total'] is not None else None,
                "under_odds": away_data['total_odds'] if away_data['total'] is not None else None,
                "is_completed": False
            }
            games.append(game)
        else:
            # If line doesn't match date or time, skip it (shouldn't happen)
            i += 1

    return games

if __name__ == "__main__":
    import sys
    filename = sys.argv[1] if len(sys.argv) > 1 else "odds.txt"
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    games = parse_games_from_text(content)
    print(json.dumps(games, indent=2))
    with open('ncaaf_odds_import.json', 'w', encoding='utf-8') as out:
        json.dump(games, out, indent=2)
    print(f"\n✅ Exported {len(games)} games to ncaaf_odds_import.json")