#!/usr/bin/env python3
"""Create a sanitized, reviewable football data contribution bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SENSITIVE_KEYS = {
    "qrUrl", "footerUrl", "footerLabel", "ip", "email", "phone", "localPath",
    "chat", "chatContext", "account", "username", "userId", "personalNote",
}


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: sanitize(child) for key, child in value.items() if key not in SENSITIVE_KEYS}
    if isinstance(value, list):
        return [sanitize(child) for child in value]
    return value


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_sources(snapshot: dict, profile: dict) -> list[dict[str, str]]:
    values: set[str] = set()
    for fixture in snapshot.get("fixtures", []):
        if fixture.get("source"):
            values.add(fixture["source"])
        for broadcast in fixture.get("broadcasts", []):
            if broadcast.get("source"):
                values.add(broadcast["source"])
    for key in ("crestSource", "crestSourcePage"):
        if profile.get(key):
            values.add(profile[key])
    return [{"url": url, "status": "to-review"} for url in sorted(values)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--team-profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--consent", action="store_true", help="用户已明确同意生成候选提交包")
    parser.add_argument("--endpoint")
    args = parser.parse_args()
    if not args.consent:
        parser.error("必须使用 --consent 明确确认后才会生成候选包")

    snapshot = sanitize(load(args.snapshot))
    profile = sanitize(load(args.team_profile))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    dump(output / "snapshot.json", snapshot)
    dump(output / "team-profile.json", profile)
    dump(output / "sources.json", unique_sources(snapshot, profile))
    manifest = {
        "schemaVersion": "1.1",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "teamId": snapshot.get("team", {}).get("teamId") or profile.get("teamId"),
        "season": snapshot.get("season"),
        "region": snapshot.get("region", "CN-mainland"),
        "consent": True,
        "files": {},
    }
    for name in ("snapshot.json", "sources.json", "team-profile.json"):
        manifest["files"][name] = {"sha256": digest(output / name)}
    dump(output / "submission-manifest.json", manifest)

    if args.endpoint:
        payload = {
            "schemaVersion": manifest["schemaVersion"],
            "teamId": manifest["teamId"],
            "season": manifest["season"],
            "region": manifest["region"],
            "snapshot": snapshot,
            "sources": load(output / "sources.json"),
            "crestMetadata": {key: profile[key] for key in ("crest", "crestSource", "crestSourcePage") if key in profile},
            "consent": True,
        }
        request = urllib.request.Request(
            args.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "aigegebox-football-match-guide/1.1"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                print(json.dumps({"bundle": str(output), "server": json.loads(response.read().decode("utf-8"))}, ensure_ascii=False, indent=2))
        except Exception as exc:  # network failure must keep local bundle
            print(json.dumps({"bundle": str(output), "serverError": str(exc)}, ensure_ascii=False, indent=2))
            return 2
    else:
        print(json.dumps({"bundle": str(output), "submitted": False, "message": "候选包已生成，等待人工审核或稍后提交"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
