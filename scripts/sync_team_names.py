# scripts/sync_team_names.py
"""
Sync DB team names to the canonical names from each sport's official source.

For each sport:
  1. Fetch source's team list → {abbreviation: canonical_name}
  2. Loop DB teams for that sport
  3. If DB name != canonical name → rename

Usage:
    python -m scripts.sync_team_names                 # dry run, all sports
    python -m scripts.sync_team_names --apply         # actually write
    python -m scripts.sync_team_names ncaaf --apply   # only one sport
"""
import argparse
import logging
import sys

from core.database import SessionLocal
from core.config import settings
from models.team import Team

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("sync-team-names")


# --------------------------------------------------------------------------
# Source fetchers — each returns {ABBR: canonical_name}
# --------------------------------------------------------------------------
def fetch_ncaaf() -> dict[str, str]:
    """CFBD — canonical name is the 'school' field (e.g. 'Ohio State')."""
    import requests
    r = requests.get(
        "https://api.collegefootballdata.com/teams/fbs",
        headers={"Authorization": f"Bearer {settings.CFBD_API_KEY}"},
        params={"year": 2025},
        timeout=30,
    )
    r.raise_for_status()
    out = {}
    for t in r.json():
        abbr = (t.get("abbreviation") or "").upper().strip()
        name = (t.get("school") or "").strip()
        if abbr and name:
            out[abbr] = name
    return out


def fetch_mlb() -> dict[str, str]:
    """statsapi.mlb.com — 'name' is like 'New York Yankees'."""
    import requests
    r = requests.get(
        "https://statsapi.mlb.com/api/v1/teams",
        params={"sportId": 1},
        timeout=30,
    )
    r.raise_for_status()
    return {
        t["abbreviation"].upper(): t["name"]
        for t in r.json()["teams"]
        if t.get("abbreviation") and t.get("name")
    }


def fetch_nfl() -> dict[str, str]:
    """nflreadpy — 'team_name' is like 'Arizona Cardinals'."""
    import nflreadpy as nfl
    df = nfl.load_teams()
    df = df.to_pandas() if hasattr(df, "to_pandas") else df
    return {
        str(row["team_abbr"]).upper(): str(row["team_name"])
        for _, row in df.iterrows()
        if row.get("team_abbr") and row.get("team_name")
    }


def fetch_nba() -> dict[str, str]:
    """nba_api — 'full_name' is like 'Atlanta Hawks'."""
    from nba_api.stats.static import teams
    return {
        t["abbreviation"].upper(): t["full_name"]
        for t in teams.get_teams()
        if t.get("abbreviation") and t.get("full_name")
    }


def fetch_nhl() -> dict[str, str]:
    """nhlpy — API surface varies; try a couple of shapes."""
    from nhlpy import NHLClient
    client = NHLClient()
    out = {}
    for t in client.teams.all_teams():
        abbr = (t.get("abbrev") or t.get("triCode") or "").upper()
        name = t.get("name") or t.get("fullName")
        if abbr and name:
            out[abbr] = name
    return out


# ncaab intentionally omitted — CBBpy has no canonical team-list endpoint.
# The fetcher matches NCAAB by name too, but you'll have to align those by
# hand (or scrape the list from a source you trust).
SOURCES = {
    "ncaaf": fetch_ncaaf,
    "mlb":   fetch_mlb,
    "nfl":   fetch_nfl,
    "nba":   fetch_nba,
    "nhl":   fetch_nhl,
}


# --------------------------------------------------------------------------
# Core loop
# --------------------------------------------------------------------------
def sync_sport(db, sport: str, apply: bool) -> tuple[int, int, int]:
    log.info(f"\n=== {sport.upper()} ===")
    try:
        source = SOURCES[sport]()
    except Exception as e:
        log.error(f"  ❌ Could not fetch source names: {e}")
        return (0, 0, 0)

    log.info(f"  Source returned {len(source)} teams")

    db_teams = db.query(Team).filter(Team.sport == sport).all()
    updated = matched = unmatched = 0

    for team in db_teams:
        abbr = team.abbreviation.upper().strip()
        canonical = source.get(abbr)

        if not canonical:
            log.info(f"  ⚠️  {abbr:<6} no source match      (db: {team.name!r})")
            unmatched += 1
            continue

        if team.name == canonical:
            matched += 1
            continue

        log.info(f"  ✏️  {abbr:<6} {team.name!r} → {canonical!r}")
        if apply:
            team.name = canonical
        updated += 1

    if apply and updated:
        db.commit()

    return (updated, matched, unmatched)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sport", nargs="?", help="Only this sport (default: all)")
    ap.add_argument("--apply", action="store_true", help="Actually write changes")
    args = ap.parse_args()

    sports = [args.sport] if args.sport else list(SOURCES.keys())
    for s in sports:
        if s not in SOURCES:
            log.error(f"Unknown sport: {s!r}. Choices: {', '.join(SOURCES)}")
            sys.exit(1)

    db = SessionLocal()
    try:
        grand_updated = grand_matched = grand_unmatched = 0
        for s in sports:
            u, m, x = sync_sport(db, s, args.apply)
            grand_updated += u
            grand_matched += m
            grand_unmatched += x
            log.info(f"  → updated={u}, already-correct={m}, unmatched={x}")

        log.info(
            f"\nTotal: updated={grand_updated}, already-correct={grand_matched}, "
            f"unmatched={grand_unmatched}"
        )
    finally:
        db.close()

    if not args.apply:
        log.info("\nDRY RUN — pass --apply to actually write.")


if __name__ == "__main__":
    main()