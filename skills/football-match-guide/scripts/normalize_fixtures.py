#!/usr/bin/env python3
"""Normalize a football fixture payload using only the Python standard library."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


STATUS_VALUES = {
    "confirmed",
    "scheduled",
    "tbd",
    "postponed",
    "cancelled",
    "unconfirmed",
}
BROADCAST_STATUS_VALUES = {"confirmed", "scheduled", "tbd", "changed"}
COMPETITION_TYPES = {
    "domestic-league",
    "domestic-cup",
    "league-cup",
    "continental",
    "super-cup",
    "club-world",
    "friendly",
    "playoff",
    "qualifier",
}


def clean(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def slug(value: str) -> str:
    value = re.sub(r"[^\w\u4e00-\u9fff]+", "-", value.lower()).strip("-")
    return value or "tbd"


def infer_competition_type(name: str) -> str:
    lower = name.lower()
    if any(token in lower for token in ("friendly", "友谊", "热身", "季前")):
        return "friendly"
    if any(token in lower for token in ("champions", "europa", "conference", "欧冠", "欧联", "欧协")):
        return "continental"
    if any(token in lower for token in ("super cup", "supercup", "超级杯")):
        return "super-cup"
    if any(token in lower for token in ("club world", "世俱杯")):
        return "club-world"
    if any(token in lower for token in ("league cup", "carabao", "联赛杯")):
        return "league-cup"
    if any(token in lower for token in ("cup", "杯")):
        return "domestic-cup"
    return "domestic-league"


def normalize_broadcast(raw: Any, parent_updated_at: str) -> dict[str, str]:
    if isinstance(raw, str):
        return {
            "region": "CN-mainland",
            "platform": raw.strip(),
            "channel": "",
            "status": "tbd",
            "source": "",
            "updatedAt": parent_updated_at,
            "note": "未提供官方确认来源",
        }
    raw = raw if isinstance(raw, dict) else {}
    status = clean(raw.get("status")) or "tbd"
    if status not in BROADCAST_STATUS_VALUES:
        status = "tbd"
    return {
        "region": clean(raw.get("region")) or "CN-mainland",
        "platform": clean(raw.get("platform")),
        "channel": clean(raw.get("channel")),
        "status": status,
        "source": clean(raw.get("source")),
        "updatedAt": clean(raw.get("updatedAt")) or parent_updated_at,
        "note": clean(raw.get("note")),
    }


def normalize_fixture(raw: Any, index: int, parent_updated_at: str) -> dict[str, Any]:
    raw = raw if isinstance(raw, dict) else {}
    competition = clean(raw.get("competition")) or "赛事待定"
    date = clean(raw.get("date")) or None
    opponent = clean(raw.get("opponent")) or None
    status = clean(raw.get("status")) or ("confirmed" if date and opponent else "tbd")
    if status not in STATUS_VALUES:
        status = "unconfirmed"
    fixture_id = clean(raw.get("fixtureId"))
    if not fixture_id:
        fixture_id = "-".join(
            [
                date or "tbd",
                slug(competition),
                slug(opponent or "opponent-tbd"),
                str(index + 1),
            ]
        )
    venue = clean(raw.get("venue")) or "unknown"
    if venue not in {"home", "away", "neutral", "unknown"}:
        venue = "unknown"
    broadcasts_raw = raw.get("broadcasts")
    if broadcasts_raw is None and raw.get("broadcast"):
        broadcasts_raw = [raw.get("broadcast")]
    if not isinstance(broadcasts_raw, list):
        broadcasts_raw = []
    normalized = {
        "fixtureId": fixture_id,
        "competition": competition,
        "competitionType": clean(raw.get("competitionType")) or infer_competition_type(competition),
        "stage": clean(raw.get("stage")),
        "date": date,
        "time": clean(raw.get("time")) or None,
        "opponent": opponent,
        "venue": venue,
        "status": status,
        "broadcasts": [normalize_broadcast(item, clean(raw.get("updatedAt")) or parent_updated_at) for item in broadcasts_raw],
        "source": clean(raw.get("source")),
        "updatedAt": clean(raw.get("updatedAt")) or parent_updated_at,
        "note": clean(raw.get("note")),
    }
    if clean(raw.get("location")):
        normalized["location"] = clean(raw.get("location"))
    if clean(raw.get("dateLabel")):
        normalized["dateLabel"] = clean(raw.get("dateLabel"))
    return normalized


def normalize(payload: Any, checked_at: str = "") -> dict[str, Any]:
    if isinstance(payload, list):
        payload = {"fixtures": payload}
    if not isinstance(payload, dict):
        raise ValueError("输入必须是 JSON 对象，或直接提供比赛数组。")
    parent_updated_at = clean(checked_at) or clean(payload.get("lastCheckedAt"))
    fixtures = payload.get("fixtures", [])
    if not isinstance(fixtures, list):
        raise ValueError("fixtures 必须是数组。")
    normalized = dict(payload)
    normalized["season"] = clean(payload.get("season"))
    normalized["region"] = clean(payload.get("region")) or "CN-mainland"
    normalized["lastCheckedAt"] = parent_updated_at
    normalized["fixtures"] = [normalize_fixture(item, index, parent_updated_at) for index, item in enumerate(fixtures)]
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description="规范化足球赛程 JSON")
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--checked-at", default="")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        result = normalize(payload, args.checked_at)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"规范化失败：{exc}", file=sys.stderr)
        return 1
    print(f"已规范化 {len(result['fixtures'])} 场比赛：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
