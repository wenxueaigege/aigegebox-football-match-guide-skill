#!/usr/bin/env python3
"""Validate the separated aigegebox football data repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

try:
    from validate_fixtures import validate
except ImportError:  # pragma: no cover
    validate = None

SENSITIVE_KEYS = {
    "qrUrl", "footerUrl", "footerLabel", "ip", "email", "phone", "localPath",
    "chat", "chatContext", "account", "username", "userId", "personalNote",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def walk_keys(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield path, key
            yield from walk_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_keys(child, f"{path}[{index}]")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_dataset(data_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    catalog_path = data_root / "catalog.json"
    if not catalog_path.exists():
        return {"valid": False, "errors": ["缺少 catalog.json"], "warnings": []}
    catalog = load_json(catalog_path)
    entries = catalog.get("teams", [])
    if not isinstance(entries, list) or not entries:
        errors.append("catalog.json 的 teams 必须是非空数组")

    seen_teams: set[str] = set()
    for entry in entries:
        team_id = entry.get("teamId") if isinstance(entry, dict) else None
        if not team_id or team_id in seen_teams:
            errors.append(f"球队目录项缺少唯一 teamId: {entry!r}")
            continue
        seen_teams.add(team_id)
        profile_path = data_root / entry.get("profile", f"teams/{team_id}/profile.json")
        if not profile_path.exists():
            errors.append(f"{team_id}: 缺少 {profile_path.relative_to(data_root)}")
            continue
        profile = load_json(profile_path)
        for path, key in walk_keys(profile):
            if key in SENSITIVE_KEYS:
                errors.append(f"{team_id}: 包含敏感字段 {path}.{key}")
        for key in ("teamId", "nameZh", "nameEn", "crest", "crestSource", "crestSourcePage"):
            if not profile.get(key):
                errors.append(f"{team_id}: profile 缺少 {key}")
        crest_path = data_root / profile.get("crest", "")
        if not crest_path.exists():
            errors.append(f"{team_id}: 队徽资源不存在 {profile.get('crest')}")
        seasons = entry.get("seasons", [])
        if not seasons:
            errors.append(f"{team_id}: catalog 没有赛季快照")
        for season_entry in seasons:
            snapshot_rel = season_entry.get("snapshot")
            snapshot_path = data_root / snapshot_rel if snapshot_rel else None
            if not snapshot_path or not snapshot_path.exists():
                errors.append(f"{team_id}: 快照不存在 {snapshot_rel}")
                continue
            snapshot = load_json(snapshot_path)
            for path, key in walk_keys(snapshot):
                if key in SENSITIVE_KEYS:
                    errors.append(f"{team_id}: 快照包含敏感字段 {path}.{key}")
            if snapshot.get("team", {}).get("teamId") not in (None, team_id):
                errors.append(f"{team_id}: 快照 teamId 不一致")
            fixtures = snapshot.get("fixtures")
            if not isinstance(fixtures, list):
                errors.append(f"{team_id}: 快照 fixtures 不是数组")
            elif validate is not None:
                result = validate(snapshot)
                if isinstance(result, dict) and not result.get("valid", True):
                    errors.extend(f"{team_id}: {message}" for message in result.get("errors", []))
            recorded_hash = season_entry.get("sha256")
            if recorded_hash and recorded_hash != sha256(snapshot_path):
                errors.append(f"{team_id}: 快照 sha256 不匹配")

    if not (data_root / "releases/manifest.json").exists():
        warnings.append("缺少 releases/manifest.json")
    return {"valid": not errors, "errors": errors, "warnings": warnings, "teamCount": len(seen_teams)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_root", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = validate_dataset(args.data_root.resolve())
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("资料库校验通过" if report["valid"] else "资料库校验失败")
        for message in report["errors"]:
            print(f"错误：{message}")
        for message in report["warnings"]:
            print(f"提示：{message}")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
