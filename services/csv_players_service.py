import csv
from pathlib import Path

CSV_PATH = Path("data/nfl_players.csv")

def get_all_players_from_csv():
    with open(CSV_PATH, "r") as f:
    reader = csv.DictReader(f)
    return reader