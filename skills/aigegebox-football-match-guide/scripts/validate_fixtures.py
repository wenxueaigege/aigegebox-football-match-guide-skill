#!/usr/bin/env python3
"""Validate normalized fixture JSON and emit a Chinese report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


STATUS_VALUES = {"confirmed", "scheduled", "tbd", "postponed", "cancelled", "unconfirmed", "finished", "completed", "played"}
BROADCAST_STATUS_VALUES = {"confirmed", "scheduled", "tbd", "changed"}
TYPE_VALUES = {
    "domestic-league", "domestic-cup", "league-cup", "continental", "super-cup",
    "club-world", "friendly", "playoff", "qualifier",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate(payload: Any) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["顶层数据必须是对象。"], "warnings": []}
    for field in ("team", "season", "fixtures"):
        if field not in payload:
            errors.append(f"缺少顶层字段：{field}")
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list):
        errors.append("fixtures 必须是数组。")
        return {"valid": False, "errors": errors, "warnings": warnings}
    ids: set[str] = set()
    for index, fixture in enumerate(fixtures, start=1):
        prefix = f"第 {index} 场"
        if not isinstance(fixture, dict):
            errors.append(f"{prefix}不是对象。")
            continue
        for field in ("fixtureId", "competition", "competitionType", "status", "source"):
            if field not in fixture:
                errors.append(f"{prefix}缺少字段：{field}")
        fixture_id = str(fixture.get("fixtureId", "")).strip()
        if fixture_id in ids:
            errors.append(f"{prefix}的 fixtureId 重复：{fixture_id}")
        if fixture_id:
            ids.add(fixture_id)
        date = fixture.get("date")
        if date is not None and date != "" and not DATE_RE.fullmatch(str(date)):
            errors.append(f"{prefix}日期格式不正确：{date}")
        status = fixture.get("status")
        if status not in STATUS_VALUES:
            errors.append(f"{prefix}状态不受支持：{status}")
        if fixture.get("competitionType") not in TYPE_VALUES:
            warnings.append(f"{prefix}赛事类型未使用规范枚举：{fixture.get('competitionType')}")
        if status in {"confirmed", "scheduled"}:
            if not fixture.get("date"):
                errors.append(f"{prefix}状态为 {status}，但没有日期。")
            if not fixture.get("opponent"):
                errors.append(f"{prefix}状态为 {status}，但没有对手。")
        elif not fixture.get("date") or not fixture.get("opponent"):
            warnings.append(f"{prefix}包含待定信息，生成海报时应明确显示“待定”。")
        broadcasts = fixture.get("broadcasts", [])
        if not isinstance(broadcasts, list):
            errors.append(f"{prefix}的 broadcasts 必须是数组。")
            continue
        for b_index, broadcast in enumerate(broadcasts, start=1):
            if not isinstance(broadcast, dict):
                errors.append(f"{prefix}第 {b_index} 个转播项不是对象。")
                continue
            b_status = broadcast.get("status", "tbd")
            if b_status not in BROADCAST_STATUS_VALUES:
                errors.append(f"{prefix}转播状态不受支持：{b_status}")
            if b_status in {"confirmed", "changed"} and not broadcast.get("source"):
                errors.append(f"{prefix}的已确认转播缺少来源。")
            if not broadcast.get("platform") and b_status != "tbd":
                warnings.append(f"{prefix}转播项没有平台名称。")
    if not payload.get("lastCheckedAt"):
        warnings.append("没有 lastCheckedAt，海报无法准确显示数据检查时间。")
    if not payload.get("sourceMode"):
        warnings.append("没有 sourceMode，建议标明 official-or-user-provided 或 demo。")
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "fixtureCount": len(fixtures),
        "checkedAt": payload.get("lastCheckedAt", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="校验规范化足球赛程 JSON")
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    try:
        report = validate(json.loads(args.input.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"读取失败：{exc}", file=sys.stderr)
        return 1
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
