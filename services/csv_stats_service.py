# services/csv_stats_service.py
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)

class CSVStatsService:
    """
    Reads per‑team per‑season game‑by‑game CSV files.
    Caches files locally and downloads from GitHub on demand.
    """

    GITHUB_RAW_URL = "https://raw.githubusercontent.com/TezTech93/Sports-Stats/main/{sport}/{year}/{abbr}.csv"
    SUPPORTED_SPORTS = ["nfl", "nba", "nhl", "mlb", "ncaaf", "ncaab"]

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        for sport in self.SUPPORTED_SPORTS:
            (self.data_dir / sport).mkdir(exist_ok=True)

    # ---------- File Management ----------

    def get_csv_path(self, sport: str, year: int, abbr: str) -> Path:
        """Local path: data/{sport}/{year}/{abbr}.csv"""
        path = self.data_dir / sport / str(year) / f"{abbr.upper()}.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def ensure_csv_exists(self, sport: str, year: int, abbr: str) -> bool:
        """Download from GitHub if not present locally."""
        path = self.get_csv_path(sport, year, abbr)
        if path.exists():
            return True
        return self.download_csv(sport, year, abbr)

    def download_csv(self, sport: str, year: int, abbr: str) -> bool:
        """Download a CSV from GitHub to the local cache."""
        url = self.GITHUB_RAW_URL.format(sport=sport, year=year, abbr=abbr.upper())
        path = self.get_csv_path(sport, year, abbr)

        try:
            logger.info(f"Downloading {url} ...")
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            with open(path, 'w', encoding='utf-8') as f:
                f.write(resp.text)
            logger.info(f"Cached to {path}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {url}: {e}")
            return False

    # ---------- CSV Parsing ----------

    def _read_game_rows(self, sport: str, year: int, abbr: str) -> List[Dict[str, str]]:
        """
        Read the CSV file.
        - Auto‑detects the header row (contains 'Week').
        - Skips any rows above the header (description).
        - Skips any row where 'Week' is not an integer (e.g. totals row).
        Returns a list of dicts (column name -> value).
        """
        path = self.get_csv_path(sport, year, abbr)
        if not path.exists():
            return []

        rows = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = None
            non_empty_indices = []

            for row in reader:
                if not row or len(row) == 0:
                    continue

                # Detect the header: look for a column containing 'week' (case-insensitive)
                if header is None:
                    for i, col in enumerate(row):
                        if 'week' in col.lower():
                            # This row is the header
                            header = [col.strip() for col in row]
                            non_empty_indices = [i for i, h in enumerate(header) if h.strip() != '']
                            # Clean header (keep only non-empty)
                            header_clean = [h for h in header if h.strip() != '']
                            # We'll use the original header list and non_empty_indices for data rows
                            break
                    if header is not None:
                        continue  # skip processing the header row as data

                # Process data rows after header is set
                if header is not None:
                    # Skip rows where the first column (Week) is not a number
                    try:
                        int(row[0].strip())
                    except (ValueError, IndexError):
                        # This is likely a "Totals" row or a description row
                        continue

                    # Build dict using only non‑empty header columns
                    row_dict = {}
                    for idx in non_empty_indices:
                        if idx < len(row):
                            col_name = header[idx].strip()
                            row_dict[col_name] = row[idx].strip()
                    rows.append(row_dict)

        return rows

    # ---------- Aggregation ----------

    def get_team_season_stats(self, sport: str, year: int, abbr: str) -> Optional[Dict[str, Any]]:
        """
        Compute season totals, averages, and record from all games.
        Returns a dict with:
            - team_abbr, sport, year
            - games_played
            - record: {'W': wins, 'L': losses, 'T': ties}
            - totals: sum of all numeric columns
            - averages: per‑game average of those numeric columns
            - game_rows: the raw list of game dicts (for table display)
        """
        if not self.ensure_csv_exists(sport, year, abbr):
            return None

        game_rows = self._read_game_rows(sport, year, abbr)
        if not game_rows:
            return None

        totals = {}
        counts = {}
        record = {'W': 0, 'L': 0, 'T': 0}

        for row in game_rows:
            # Determine result (if 'Tm' and 'Opp' exist)
            try:
                tm = float(row.get('Tm', 0))
                opp = float(row.get('Opp', 0))
                if tm > opp:
                    record['W'] += 1
                elif tm < opp:
                    record['L'] += 1
                else:
                    record['T'] += 1
            except (ValueError, TypeError):
                pass  # ignore if these columns are missing or non‑numeric

            # Sum all columns that can be parsed as float
            for col, val in row.items():
                val = val.strip()
                if val == '':
                    continue
                try:
                    num = float(val)
                    if col not in totals:
                        totals[col] = 0.0
                        counts[col] = 0
                    totals[col] += num
                    counts[col] += 1
                except ValueError:
                    # Not numeric, skip
                    pass

        # Compute averages
        averages = {}
        for col, total in totals.items():
            averages[col] = round(total / counts[col], 2) if counts[col] > 0 else 0.0

        return {
            'team_abbr': abbr.upper(),
            'sport': sport,
            'year': year,
            'games_played': len(game_rows),
            'record': record,
            'totals': totals,
            'averages': averages,
            'game_rows': game_rows   # <-- added for raw data
        }

    def list_available_files(self, sport: Optional[str] = None) -> Dict[str, Dict[int, List[str]]]:
        """List all cached files: {sport: {year: [abbr1, abbr2, ...]}}"""
        result = {}
        sports = [sport] if sport else self.SUPPORTED_SPORTS

        for s in sports:
            sport_dir = self.data_dir / s
            if not sport_dir.exists():
                result[s] = {}
                continue

            years = {}
            for year_dir in sport_dir.iterdir():
                if year_dir.is_dir():
                    try:
                        year = int(year_dir.name)
                        files = [f.stem.upper() for f in year_dir.glob("*.csv")]
                        if files:
                            years[year] = sorted(files)
                    except ValueError:
                        continue
            result[s] = years

        return result