# services/csv_stats_service.py
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

class CSVStatsService:
    """
    Reads per‑team per‑season game‑by‑game CSV files.
    Caches files locally and downloads from GitHub on demand.
    """

    GITHUB_RAW_URL = "https://raw.githubusercontent.com/TezTech93/Sports-Stats/main/{sport}/{year}/{file_base}_{year}_stats.csv"
    SUPPORTED_SPORTS = ["nfl", "nba", "nhl", "mlb", "ncaaf", "ncaab"]

    # Map frontend abbreviations (what the API receives) to actual file base names.
    # Example: the frontend sends 'GB' but the file is 'GNB_2025_stats.csv'
    ABBR_MAPPING = {
        'nfl': {
            'GB': 'GNB',      # Green Bay Packers
            # Add other NFL overrides if needed
        },
        'nba': {
            # Add NBA overrides if needed (e.g., if file names differ)
        },
        'nhl': {},
        'mlb': {},
        'ncaaf': {},
        'ncaab': {}
    }

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        for sport in self.SUPPORTED_SPORTS:
            (self.data_dir / sport).mkdir(exist_ok=True)

    # ---------- File Management ----------

    def _get_file_base(self, sport: str, abbr: str) -> str:
        """Return the actual file base name (without '_year_stats') after applying the mapping."""
        sport_mapping = self.ABBR_MAPPING.get(sport, {})
        return sport_mapping.get(abbr.upper(), abbr.upper())

    def get_csv_path(self, sport: str, year: int, abbr: str) -> Path:
        """Local path: data/{sport}/{year}/{file_base}_{year}_stats.csv"""
        file_base = self._get_file_base(sport, abbr)
        path = self.data_dir / sport / str(year) / f"{file_base}_{year}_stats.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def ensure_csv_exists(self, sport: str, year: int, abbr: str) -> bool:
        """Download from GitHub if not present locally."""
        path = self.get_csv_path(sport, year, abbr)
        if path.exists():
            return True
        return self.download_csv(sport, year, abbr)

    def download_csv(self, sport: str, year: int, abbr: str) -> bool:
        file_base = self._get_file_base(sport, abbr)
        url = f"https://raw.githubusercontent.com/TezTech93/Sports-Stats/main/{sport}/{year}/{file_base}_{year}_stats.csv"
        path = self.get_csv_path(sport, year, abbr)

        headers = {}
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        try:
            logger.info(f"Downloading {url} ...")
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            with open(path, 'w', encoding='utf-8') as f:
                f.write(resp.text)
            logger.info(f"Cached to {path}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
            """Download a CSV from GitHub to the local cache."""
            file_base = self._get_file_base(sport, abbr)
            url = self.GITHUB_RAW_URL.format(
                sport=sport,
                year=year,
                file_base=file_base
            )
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

    def _find_header_row(self, rows) -> tuple:
        """
        Find the row that contains a known header column.
        Known header columns: Rk, Gtm, Date, Opp, Rslt, Tm, Week, Day, etc.
        Returns (header_row, header_index) or (None, -1).
        """
        known_headers = ['Rk', 'Gtm', 'Date', 'Opp', 'Rslt', 'Tm', 'FG', 'FGA', '3P', 'Week', 'Day', 'Location']
        for idx, row in enumerate(rows):
            if not row:
                continue
            # Check if any column in this row matches a known header (case-insensitive)
            for cell in row:
                cell_clean = cell.strip()
                if cell_clean in known_headers or cell_clean.lower() in [h.lower() for h in known_headers]:
                    return row, idx
        return None, -1

    def _read_game_rows(self, sport: str, year: int, abbr: str) -> List[Dict[str, str]]:
        """
        Read the CSV file.
        - Auto‑detects the header row using a list of known column names.
        - Skips any rows above the header (description).
        - Skips any row where the first column is not a number (e.g. totals row).
        Returns a list of dicts (column name -> value).
        """
        path = self.get_csv_path(sport, year, abbr)
        if not path.exists():
            return []

        rows = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            all_rows = list(reader)

        # Find the header row
        header, header_idx = self._find_header_row(all_rows)
        if header is None:
            logger.error(f"Could not find header row in {path}")
            return []

        # Clean header: strip whitespace, keep non‑empty columns
        header = [col.strip() for col in header]
        non_empty_indices = [i for i, h in enumerate(header) if h != '']

        # Process data rows (skip the header row itself)
        for row in all_rows[header_idx + 1:]:
            if not row:
                continue
            # Skip rows where the first column is not a number (totals row)
            try:
                float(row[0].strip())  # Try to convert to float; int works too
            except (ValueError, IndexError):
                continue  # this is likely a totals row or description

            # Build dict using only non‑empty header columns
            row_dict = {}
            for idx in non_empty_indices:
                if idx < len(row):
                    col_name = header[idx]
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
            # Determine result if 'Tm' and 'Opp' exist (NFL, NBA, etc.)
            # For NBA, the columns are 'Tm' and 'Opp' as well (from the sample)
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
            'game_rows': game_rows
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
                        files = []
                        for f in year_dir.glob("*.csv"):
                            stem = f.stem  # e.g., 'LAL_2025_stats'
                            parts = stem.rsplit('_', 2)
                            if len(parts) == 3 and parts[1] == str(year) and parts[2] == 'stats':
                                base = parts[0]
                            else:
                                base = stem
                            files.append(base)
                        if files:
                            years[year] = sorted(files)
                    except ValueError:
                        continue
            result[s] = years

        return result