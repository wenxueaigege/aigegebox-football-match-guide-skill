#!/usr/bin/env python3
"""Read public football data into a local, disposable cache."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

DEFAULT_BASE = "https://raw.githubusercontent.com/wenxueaigege/aigegebox-football-match-data/main"


def parse_day(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def freshness(last_checked: str | None, days: int, today: date | None = None) -> bool:
    checked = parse_day(last_checked)
    if not checked:
        return False
    return (today or date.today()) - checked <= timedelta(days=days)


def fetch_json(url: str) -> object:
    request = urllib.request.Request(url, headers={"User-Agent": "aigegebox-football-match-guide/1.1"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict:
    cache_dir = Path(args.cache_dir or os.environ.get("AIGEGEBOX_FOOTBALL_CACHE_DIR", ".aigegebox-football-cache"))
    team_dir = cache_dir / "teams" / args.team_id
    season_path = team_dir / "seasons" / f"{args.season.replace('/', '-')}.json"
    profile_path = team_dir / "profile.json"
    catalog_path = cache_dir / "catalog.json"
    result = {"teamId": args.team_id, "season": args.season, "cacheDir": str(cache_dir), "source": "local-cache"}

    if args.offline:
        result["available"] = profile_path.exists() and season_path.exists()
        result["fresh"] = False
        return result

    base = args.base_url.rstrip("/")
    try:
        catalog = fetch_json(f"{base}/catalog.json")
        write_json(catalog_path, catalog)
        entry = next(item for item in catalog.get("teams", []) if item.get("teamId") == args.team_id)
        profile_rel = entry.get("profile", f"teams/{args.team_id}/profile.json")
        season_entry = next(item for item in entry.get("seasons", []) if item.get("season") == args.season)
        snapshot_rel = season_entry["snapshot"]
        write_json(profile_path, fetch_json(f"{base}/{quote(profile_rel)}"))
        write_json(season_path, fetch_json(f"{base}/{quote(snapshot_rel)}"))
        result.update({"source": "public-data-repo", "available": True, "lastCheckedAt": season_entry.get("lastCheckedAt")})
        result["fixtureFresh"] = freshness(season_entry.get("lastCheckedAt"), 7)
        result["broadcastFresh"] = freshness(season_entry.get("broadcastCheckedAt", season_entry.get("lastCheckedAt")), 1)
        result["crestFresh"] = freshness(entry.get("crestCheckedAt", season_entry.get("lastCheckedAt")), 90)
        result["needsRecheck"] = not (result["fixtureFresh"] and result["broadcastFresh"] and result["crestFresh"])
    except (urllib.error.URLError, TimeoutError, KeyError, StopIteration, json.JSONDecodeError) as exc:
        result.update({"available": profile_path.exists() and season_path.exists(), "source": "local-cache-fallback", "error": str(exc), "needsRecheck": True})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team-id", required=True)
    parser.add_argument("--season", required=True)
    parser.add_argument("--cache-dir")
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
