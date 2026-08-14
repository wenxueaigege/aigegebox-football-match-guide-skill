#!/usr/bin/env python3
"""Create a coverage and broadcast summary from normalized fixtures."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def check(payload: dict[str, Any]) -> dict[str, Any]:
    fixtures = payload.get("fixtures", [])
    competitions: dict[str, dict[str, Any]] = defaultdict(lambda: {"type": "", "total": 0, "confirmed": 0, "pending": 0})
    broadcast_confirmed = 0
    broadcast_scheduled = 0
    broadcast_pending = 0
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            continue
        name = fixture.get("competition") or "赛事待定"
        item = competitions[name]
        item["type"] = fixture.get("competitionType", "")
        item["total"] += 1
        if fixture.get("status") in {"confirmed", "scheduled"} and fixture.get("date") and fixture.get("opponent"):
            item["confirmed"] += 1
        else:
            item["pending"] += 1
        cn_broadcasts = [
            broadcast for broadcast in fixture.get("broadcasts", [])
            if isinstance(broadcast, dict) and broadcast.get("region", "CN-mainland") == "CN-mainland"
        ]
        if not cn_broadcasts:
            # No entry is different from a confirmed blank: it still needs a
            # China-mainland broadcast check before publication.
            broadcast_pending += 1
        for broadcast in cn_broadcasts:
            status = broadcast.get("status", "tbd") if isinstance(broadcast, dict) else "tbd"
            if status == "confirmed":
                broadcast_confirmed += 1
            elif status == "scheduled":
                broadcast_scheduled += 1
            else:
                broadcast_pending += 1
    expected = set(payload.get("expectedCompetitions", []) or [])
    found = set(competitions)
    pending_competitions = sorted(expected - found)
    for name, item in competitions.items():
        if item["pending"]:
            pending_competitions.append(name)
    status_counts = Counter(str(f.get("status", "unknown")) for f in fixtures if isinstance(f, dict))
    return {
        "team": payload.get("team", {}),
        "season": payload.get("season", ""),
        "region": payload.get("region", "CN-mainland"),
        "competitionsFound": sorted(found),
        "competitionsPending": sorted(set(pending_competitions)),
        "competitionDetails": dict(sorted(competitions.items())),
        "fixtureCount": len(fixtures),
        "fixtureStatusCounts": dict(sorted(status_counts.items())),
        "broadcastsConfirmed": broadcast_confirmed,
        "broadcastsScheduled": broadcast_scheduled,
        "broadcastsPending": broadcast_pending,
        "lastCheckedAt": payload.get("lastCheckedAt", ""),
        "sourceMode": payload.get("sourceMode", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="生成赛事覆盖和转播统计报告")
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    report = check(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已生成覆盖报告：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
