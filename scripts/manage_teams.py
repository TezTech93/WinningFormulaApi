# scripts/manage_teams.py
"""
List and rename teams in the DB.

Usage (run from the repo root on Render shell):

  # List all teams, grouped by sport
  python -m scripts.manage_teams list

  # List only one sport
  python -m scripts.manage_teams list ncaaf

  # Rename a single team (by sport + current abbreviation)
  python -m scripts.manage_teams rename ncaaf OSU "Ohio State"

  # Bulk rename from a CSV file (sport,abbr,new_name)
  python -m scripts.manage_teams rename-from-csv renames.csv

  # Export current teams to CSV for editing
  python -m scripts.manage_teams export teams.csv
"""
import csv
import sys
from pathlib import Path

from core.database import SessionLocal
from models.team import Team


def cmd_list(sport: str | None = None) -> None:
    db = SessionLocal()
    try:
        q = db.query(Team).order_by(Team.sport, Team.abbreviation)
        if sport:
            q = q.filter(Team.sport == sport)
        teams = q.all()

        current_sport = None
        for t in teams:
            if t.sport != current_sport:
                current_sport = t.sport
                print(f"\n=== {current_sport.upper()} ({sum(1 for x in teams if x.sport == current_sport)} teams) ===")
            print(f"  {t.abbreviation:<6} | {t.name}")
        print()
    finally:
        db.close()


def cmd_export(path: str) -> None:
    db = SessionLocal()
    try:
        teams = db.query(Team).order_by(Team.sport, Team.abbreviation).all()
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["sport", "abbreviation", "current_name", "new_name"])
            for t in teams:
                w.writerow([t.sport, t.abbreviation, t.name, ""])
        print(f"Wrote {len(teams)} teams to {path}")
        print("Edit the 'new_name' column, then run:")
        print(f"  python -m scripts.manage_teams rename-from-csv {path}")
    finally:
        db.close()


def cmd_rename(sport: str, abbr: str, new_name: str) -> None:
    db = SessionLocal()
    try:
        t = (
            db.query(Team)
            .filter(Team.sport == sport, Team.abbreviation == abbr.upper())
            .first()
        )
        if not t:
            print(f"❌ No team found: sport={sport}, abbr={abbr}")
            sys.exit(1)
        old = t.name
        t.name = new_name
        db.commit()
        print(f"✅ {sport} {t.abbreviation}: {old!r} → {new_name!r}")
    finally:
        db.close()


def cmd_rename_from_csv(path: str) -> None:
    p = Path(path)
    if not p.exists():
        print(f"❌ File not found: {path}")
        sys.exit(1)

    db = SessionLocal()
    updated = skipped = missing = 0
    try:
        with open(p, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                new_name = (row.get("new_name") or "").strip()
                if not new_name:
                    skipped += 1
                    continue

                sport = row["sport"].strip().lower()
                abbr = row["abbreviation"].strip().upper()
                t = (
                    db.query(Team)
                    .filter(Team.sport == sport, Team.abbreviation == abbr)
                    .first()
                )
                if not t:
                    print(f"⚠️  Not found: {sport} {abbr}")
                    missing += 1
                    continue

                old = t.name
                if old == new_name:
                    skipped += 1
                    continue
                t.name = new_name
                print(f"  {sport} {abbr}: {old!r} → {new_name!r}")
                updated += 1

        db.commit()
        print(f"\n✅ updated={updated}, skipped={skipped}, missing={missing}")
    finally:
        db.close()


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    cmd, *rest = args
    if cmd == "list":
        cmd_list(rest[0] if rest else None)
    elif cmd == "export":
        if not rest:
            print("Usage: export <output.csv>")
            sys.exit(1)
        cmd_export(rest[0])
    elif cmd == "rename":
        if len(rest) < 3:
            print('Usage: rename <sport> <abbr> "New Name"')
            sys.exit(1)
        cmd_rename(rest[0], rest[1], " ".join(rest[2:]))
    elif cmd == "rename-from-csv":
        if not rest:
            print("Usage: rename-from-csv <path.csv>")
            sys.exit(1)
        cmd_rename_from_csv(rest[0])
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()