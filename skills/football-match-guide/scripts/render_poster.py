#!/usr/bin/env python3
"""Render deterministic SVG/HTML football match posters without third-party packages."""

from __future__ import annotations

import argparse
import base64
import html
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from qr_code import qr_matrix
from poster.classic_layout import render_competition_grid
from poster.output import (
    rasterizer_install_hint,
    rasterizer_name,
    write_html,
    write_scaled_png,
)
from poster.registry import build_registry, specs_for_section


FONT = "Arial, PingFang SC, Microsoft YaHei, sans-serif"
DEFAULT_QR_URL = "http://www.wenxueaigege.com?from=football-match-guide"
TYPE_LABELS = {
    "domestic-league": "联赛",
    "domestic-cup": "国内杯赛",
    "league-cup": "联赛杯",
    "continental": "欧战",
    "super-cup": "超级杯",
    "club-world": "世俱杯",
    "friendly": "友谊赛",
    "playoff": "附加赛",
    "qualifier": "资格赛",
}
COMPETITION_LABELS = {
    "Premier League": "英超 Premier League",
    "Official Friendlies": "友谊赛 Official Friendlies",
    "Emirates Cup": "酋长杯 Emirates Cup",
    "FA Community Shield": "社区盾 FA Community Shield",
    "EFL Cup": "联赛杯 Carabao Cup",
    "FA Cup": "足总杯 FA Cup",
    "UEFA Champions League": "欧冠 UEFA Champions League",
    "La Liga": "西甲 La Liga",
    "Copa del Rey": "国王杯 Copa del Rey",
    "Supercopa de España": "西超杯 Supercopa de España",
    "Bundesliga": "德甲 Bundesliga",
    "DFB-Pokal": "德国杯 DFB-Pokal",
    "Franz Beckenbauer Supercup": "弗朗茨·贝肯鲍尔超级杯 Franz Beckenbauer Supercup",
    "Telekom Cup": "电信杯 Telekom Cup",
}
CUP_STAGE_ORDER = {
    "EFL Cup": {
        "第三轮": 10, "第四轮": 20, "第五轮": 30,
        "半决赛首回合": 40, "半决赛次回合": 50, "决赛": 60,
    },
    "FA Cup": {
        "第三轮": 10, "第四轮": 20, "第五轮": 30,
        "八强": 40, "半决赛": 50, "决赛": 60,
    },
    "UEFA Champions League": {
        **{f"Matchday {index}": index for index in range(1, 9)},
        "附加赛首回合": 20, "附加赛次回合": 21,
        "1/8决赛首回合": 30, "1/8决赛次回合": 31,
        "1/4决赛首回合": 40, "1/4决赛次回合": 41,
        "半决赛首回合": 50, "半决赛次回合": 51, "决赛": 60,
    },
}
WEEKDAY_LABELS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def color(value: str, fallback: str) -> str:
    return value if re.fullmatch(r"#[0-9a-fA-F]{6}", value or "") else fallback


def team_profile(payload: dict[str, Any], profile_path: Path | None) -> dict[str, Any]:
    team = payload.get("team") if isinstance(payload.get("team"), dict) else {}
    if profile_path:
        team = {**team, **json.loads(profile_path.read_text(encoding="utf-8"))}
    colors = team.get("colors") if isinstance(team.get("colors"), dict) else {}
    team["colors"] = {
        "primary": color(colors.get("primary", ""), "#b42318"),
        "secondary": color(colors.get("secondary", ""), "#ffffff"),
        "accent": color(colors.get("accent", ""), "#f4c542"),
        "text": color(colors.get("text", ""), "#241b19"),
    }
    return team


def text(parts: list[str], x: int, y: int, value: Any, size: int, fill: str, weight: str = "400", anchor: str = "start") -> None:
    parts.append(
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}px" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(value)}</text>'
    )


def rect(parts: list[str], x: int, y: int, width: int, height: int, fill: str, radius: int = 0, stroke: str = "none") -> None:
    parts.append(
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" '
        f'fill="{fill}" stroke="{stroke}"/>'
    )


def qr_svg(parts: list[str], url: str, x: int, y: int, size: int, label: str) -> bool:
    """Draw a real QR matrix; return False only when the URL is too long."""
    try:
        matrix = qr_matrix(url)
    except ValueError:
        return False
    quiet = 4
    module = size / (len(matrix) + quiet * 2)
    rect(parts, x, y, size, size, "#ffffff", 6)
    for row, values in enumerate(matrix):
        for col, dark in enumerate(values):
            if dark:
                parts.append(
                    f'<rect x="{x + (col + quiet) * module:.3f}" y="{y + (row + quiet) * module:.3f}" '
                    f'width="{module + 0.12:.3f}" height="{module + 0.12:.3f}" fill="#111111"/>'
                )
    text(parts, x + size / 2, y + size + 20, label, 13, "#786d66", "600", "middle")
    return True


def crest_href(team: dict[str, Any]) -> str:
    """Embed a local crest asset so standalone SVG/HTML outputs keep the badge."""
    value = team.get("crest")
    if not value:
        return ""
    path = Path(value)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    if not path.is_file():
        return ""
    mime_types = {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    mime = mime_types.get(path.suffix.lower(), "application/octet-stream")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def crest_path(team: dict[str, Any]) -> Path | None:
    value = str(team.get("crest") or "").strip()
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    return path if path.is_file() else None


def require_official_crest(team: dict[str, Any], allow_text_crest: bool = False) -> None:
    """Block formal posters when the team badge is missing or lacks an official source."""
    if allow_text_crest:
        return
    missing = []
    if crest_path(team) is None:
        missing.append("本地队徽文件")
    if not str(team.get("crestSource") or "").strip():
        missing.append("crestSource 官网资源地址")
    if not str(team.get("crestSourcePage") or team.get("crestSource") or "").strip():
        missing.append("crestSourcePage 官网页面")
    if missing:
        raise ValueError(
            "正式海报缺少已核验的官网队徽：" + "、".join(missing)
            + "。请先检查 assets/；库中没有时从俱乐部官网下载并补齐球队配置。"
            + "内部排版草稿如确需文字占位，可显式使用 --allow-text-crest。"
        )


def fixture_date(fixture: dict[str, Any]) -> str:
    value = fixture.get("date")
    return format_short_date(value) if isinstance(value, str) and len(value) >= 10 else "待定"


def fixture_broadcast(fixture: dict[str, Any]) -> str:
    items = []
    for item in fixture.get("broadcasts", []):
        if not isinstance(item, dict) or item.get("region", "CN-mainland") != "CN-mainland":
            continue
        if item.get("status") == "tbd":
            continue
        label = item.get("platform", "")
        if item.get("channel"):
            label = f"{label} · {item['channel']}" if label else item["channel"]
        if label:
            items.append(label)
    return " / ".join(items) if items else "转播待定"


def reference_date(payload: dict[str, Any], override: str = "") -> str:
    return override or payload.get("asOfDate") or payload.get("lastCheckedAt") or date.today().isoformat()


def fixture_is_visible(fixture: dict[str, Any], as_of: str) -> bool:
    """Keep only matches that have not ended as of the poster check date."""
    status = str(fixture.get("status") or "").lower()
    if status in {"cancelled", "finished", "completed", "played"}:
        return False
    match_date = fixture.get("date")
    if isinstance(match_date, str) and len(match_date) >= 10 and match_date[:10] < as_of:
        return status in {"postponed", "rescheduled"}
    return True


def visible_fixtures(fixtures: list[dict[str, Any]], as_of: str) -> list[dict[str, Any]]:
    return [fixture for fixture in fixtures if fixture_is_visible(fixture, as_of)]


def fixture_card(parts: list[str], fixture: dict[str, Any], x: int, y: int, width: int, height: int, primary: str, text_color: str) -> None:
    rect(parts, x, y, width, height, "#ffffff", 10, "#eadfd1")
    date = fixture_date(fixture)
    time = fixture.get("time") or "时间待定"
    opponent = fixture.get("opponent") or "对手待定"
    venue = {"home": "主", "away": "客", "neutral": "中立"}.get(fixture.get("venue"), "")
    status = fixture.get("status")
    if status in {"postponed", "cancelled"}:
        date = "延期" if status == "postponed" else "取消"
    text(parts, x + 18, y + 27, date, 20, primary, "700")
    text(parts, x + 18, y + 53, f"{time} · {venue}" if venue else time, 15, "#786d66")
    text(parts, x + 158, y + 32, opponent, 24, text_color, "700")
    text(parts, x + 158, y + 59, fixture.get("competition", "赛事待定"), 14, "#786d66")
    text(parts, x + width - 18, y + 30, fixture_broadcast(fixture), 13, "#7c5d16", "600", "end")
    if fixture.get("note"):
        text(parts, x + 18, y + height - 11, fixture["note"], 12, "#9a6b3b")


def classic_palette(team: dict[str, Any]) -> dict[str, str]:
    primary = team["colors"]["primary"]
    accent = team["colors"]["accent"]
    is_arsenal_red = primary.lower() in {"#d71920", "#e21b18", "#e02218"}
    return {
        "red": "#d82819" if is_arsenal_red else primary,
        "dark": "#8b110c" if is_arsenal_red else "#092452",
        "deep": "#650a09" if is_arsenal_red else "#061735",
        "gold": "#f7d501" if is_arsenal_red else accent,
        "cream": "#f5f5f5",
        "cream_alt": "#ebebeb",
        "ink": "#231616",
        "muted": "#755d58",
        "line": "#f7d501" if is_arsenal_red else accent,
        "home": "#8b110c" if is_arsenal_red else "#092452",
        "away": "#1e4f8d" if is_arsenal_red else accent,
        "neutral": "#8a741f",
    }


def classic_section_title(parts: list[str], y: int, title: str, subtitle: str, palette: dict[str, str]) -> int:
    line_y = y + 22
    parts.append(f'<line x1="48" y1="{line_y}" x2="390" y2="{line_y}" stroke="{palette["line"]}" stroke-width="3"/>')
    parts.append(f'<line x1="690" y1="{line_y}" x2="1032" y2="{line_y}" stroke="{palette["line"]}" stroke-width="3"/>')
    parts.append(f'<circle cx="390" cy="{line_y}" r="5" fill="{palette["line"]}"/><circle cx="690" cy="{line_y}" r="5" fill="{palette["line"]}"/>')
    text(parts, 540, y + 29, title, 28, palette["gold"], "700", "middle")
    text(parts, 540, y + 54, subtitle, 15, "#ffd98b", "400", "middle")
    return y + 72


def classic_month_bar(parts: list[str], y: int, month: str, count: int, palette: dict[str, str]) -> int:
    rect(parts, 32, y, 1016, 32, palette["cream"], 3)
    text(parts, 44, y + 22, month, 18, palette["dark"], "700")
    text(parts, 1032, y + 22, f"{count} 场", 13, palette["muted"], "400", "end")
    return y + 39


def display_date(fixture: dict[str, Any]) -> str:
    if fixture.get("dateLabel"):
        return str(fixture["dateLabel"])
    value = fixture.get("date")
    if isinstance(value, str) and len(value) >= 10:
        return format_short_date(value)
    return "日期待定"


def display_card_date(fixture: dict[str, Any]) -> str:
    if fixture.get("dateLabel"):
        return str(fixture["dateLabel"])
    value = fixture.get("date")
    if isinstance(value, str) and len(value) >= 10:
        return format_short_date(value)
    return str(fixture.get("dateLabel") or "日期待定")


def format_short_date(value: str) -> str:
    """Format a valid ISO date as a compact Chinese date with weekday."""
    try:
        parsed = date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return "日期待定"
    return f"{parsed.month}月{parsed.day}日 {WEEKDAY_LABELS[parsed.weekday()]}"


def display_month(value: str) -> str:
    if value == "待定":
        return "日期待定"
    year, month = value.split("-")
    return f"{year}年{int(month)}月"


def display_venue(fixture: dict[str, Any]) -> str:
    label = {"home": "主场", "away": "客场", "neutral": "中立"}.get(fixture.get("venue"), "主客待定")
    location = fixture.get("location")
    return f"{label} · {location}" if location else label


def display_home_away(fixture: dict[str, Any]) -> str:
    return {"home": "主场", "away": "客场", "neutral": "中立"}.get(fixture.get("venue"), "待定")


def display_location(fixture: dict[str, Any]) -> str:
    return str(fixture.get("location") or "场地待定")


def display_short_location(fixture: dict[str, Any]) -> str:
    value = display_location(fixture)
    return re.split(r"[（(]", value, maxsplit=1)[0].strip()


def competition_label(name: str) -> str:
    return COMPETITION_LABELS.get(name, name or "赛事待定")


def fixture_sort_key(name: str, fixture: dict[str, Any], index: int) -> tuple[int, str, int]:
    stage_rank = CUP_STAGE_ORDER.get(name, {}).get(str(fixture.get("stage") or ""), 900)
    return stage_rank, str(fixture.get("date") or "9999-99-99"), index


def display_broadcast(fixture: dict[str, Any]) -> str:
    labels = []
    for item in fixture.get("broadcasts", []):
        if not isinstance(item, dict) or item.get("region", "CN-mainland") != "CN-mainland":
            continue
        if item.get("status") == "tbd":
            continue
        label = item.get("platform") or ""
        if item.get("channel"):
            label = f"{label}/{item['channel']}" if label else item["channel"]
        if label:
            labels.append(label)
    return " / ".join(labels) if labels else "转播待定"


def display_card_tag(fixture: dict[str, Any]) -> str:
    tags = {
        "Premier League": "联赛",
        "FA Community Shield": "社区盾",
        "EFL Cup": "联赛杯",
        "FA Cup": "足总杯",
        "UEFA Champions League": "欧冠",
        "Emirates Cup": "酋长杯",
        "Official Friendlies": "友谊赛",
        "La Liga": "西甲",
        "Copa del Rey": "国王杯",
        "Supercopa de España": "西超杯",
        "Bundesliga": "德甲",
        "DFB-Pokal": "德国杯",
        "Franz Beckenbauer Supercup": "超级杯",
        "Telekom Cup": "电信杯",
    }
    return tags.get(fixture.get("competition"), TYPE_LABELS.get(fixture.get("competitionType"), "赛事"))


def venue_color(fixture: dict[str, Any], palette: dict[str, str]) -> str:
    return {
        "home": palette["home"],
        "away": palette["away"],
        "neutral": palette["neutral"],
    }.get(fixture.get("venue"), palette["dark"])


def classic_match_card(parts: list[str], fixture: dict[str, Any], x: int, y: int, width: int, palette: dict[str, str]) -> None:
    height = 68
    rect(parts, x, y, width, height, palette["cream"], 5, palette["red"])
    rect(parts, x, y, 112, height, palette["dark"], 5)
    text(parts, x + 12, y + 25, display_card_date(fixture), 15, "#ffffff", "700")
    text(parts, x + 12, y + 48, fixture.get("time") or "时间待定", 12, "#ffd98b")
    text(parts, x + 132, y + 23, str(fixture.get("opponent") or "对手待定")[:16], 19, palette["ink"], "700")
    broadcast = display_broadcast(fixture)
    text(parts, x + 132, y + 55, broadcast[:23], 11, palette["muted"])
    venue = display_home_away(fixture)
    if fixture.get("competitionType") == "domestic-league":
        pill_width = 54 if venue in {"主场", "客场"} else 54
        pill_color = palette["home"] if venue == "主场" else palette["gold"]
        rect(parts, x + width - pill_width - 12, y + 8, pill_width, 20, pill_color, 10)
        text(parts, x + width - pill_width / 2 - 12, y + 22, venue, 10, "#ffffff", "700", "middle")
    else:
        tag = display_card_tag(fixture)
        pill_width = min(98, max(72, len(tag) * 13 + 18))
        rect(parts, x + width - pill_width - 10, y + 9, pill_width, 21, palette["gold"], 10)
        text(parts, x + width - pill_width / 2 - 10, y + 24, tag, 11, palette["dark"], "700", "middle")
    text(parts, x + width - 14, y + 55, display_short_location(fixture)[:16], 11, palette["muted"], "400", "end")


def classic_fixture_groups(fixtures: list[dict[str, Any]], competition_type: str | None = None, competition: str | None = None) -> list[tuple[str, list[dict[str, Any]]]]:
    selected = [
        fixture for fixture in fixtures
        if isinstance(fixture, dict)
        and (competition_type is None or fixture.get("competitionType") == competition_type)
        and (competition is None or fixture.get("competition") == competition)
        and fixture.get("status") != "cancelled"
    ]
    months: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fixture in selected:
        months[(fixture.get("date") or "待定")[:7]].append(fixture)
    return sorted(months.items(), key=lambda item: item[0])


def classic_opening_section(parts: list[str], y: int, fixtures: list[dict[str, Any]], palette: dict[str, str]) -> int:
    opening = [
        fixture for fixture in fixtures
        if fixture.get("competitionType") == "friendly" or fixture.get("competition") == "FA Community Shield"
    ]
    if not opening:
        opening = [{
            "competition": "Official Friendlies",
            "competitionType": "friendly",
            "date": None,
            "time": None,
            "opponent": "官方季前赛待定",
            "venue": None,
            "status": "tbd",
            "broadcasts": [],
            "note": "本次检查未找到可核验的完整季前赛清单",
        }]
    has_community_shield = any(fixture.get("competition") == "FA Community Shield" for fixture in opening)
    has_super_cup = any(fixture.get("competitionType") == "super-cup" for fixture in opening)
    if has_community_shield:
        opening_title, opening_subtitle = "季前赛 & 社区盾", "Pre-season & Community Shield · 北京时间"
    elif has_super_cup:
        opening_title, opening_subtitle = "季前赛 & 超级杯", "Pre-season & Super Cup · 北京时间"
    else:
        opening_title, opening_subtitle = "季前赛", "Pre-season · 北京时间"
    y = classic_section_title(parts, y, opening_title, opening_subtitle, palette)
    for month, month_items in classic_fixture_groups(opening):
        y = classic_month_bar(parts, y, display_month(month), len(month_items), palette)
        for index in range(0, len(month_items), 2):
            row = month_items[index:index + 2]
            for column, fixture in enumerate(row):
                classic_match_card(parts, fixture, 32 + column * 508, y, 492, palette)
            y += 76
    return y + 10


def classic_league_section(parts: list[str], y: int, fixtures: list[dict[str, Any]], palette: dict[str, str], team: dict[str, Any]) -> int:
    league_items = [fixture for fixture in fixtures if fixture.get("competitionType") == "domestic-league"]
    league_name = league_items[0].get("competition") if league_items else team.get("leagueNameEn", "联赛")
    league_title = team.get("leagueTitle") or ("英超联赛" if league_name == "Premier League" else competition_label(league_name).split(" ", 1)[0] + "联赛")
    league_english = team.get("leagueNameEn") or league_name
    known_league_items = [
        fixture for fixture in league_items
        if fixture.get("date") and fixture.get("opponent")
        and fixture.get("status") in {"confirmed", "scheduled"}
    ]
    if known_league_items and len(known_league_items) == len(league_items):
        league_heading = f"{league_title} {len(known_league_items)} 轮"
        league_subtitle = f"{league_english} · 北京时间"
    elif known_league_items:
        league_heading = f"{league_title} {len(known_league_items)} 轮 · 其余待定"
        league_subtitle = f"{league_english} · 其余赛程待定 · 北京时间"
    else:
        league_heading = league_title
        league_subtitle = f"{league_english} · 赛程待定 · 北京时间"
    y = classic_section_title(parts, y, league_heading, league_subtitle, palette)
    for month, month_items in classic_fixture_groups(fixtures, competition_type="domestic-league"):
        y = classic_month_bar(parts, y, display_month(month), len(month_items), palette)
        for index in range(0, len(month_items), 2):
            row = month_items[index:index + 2]
            for column, fixture in enumerate(row):
                classic_match_card(parts, fixture, 32 + column * 508, y, 492, palette)
            y += 76
    return y + 12


def classic_table_panel(parts: list[str], x: int, y: int, width: int, name: str, fixtures: list[dict[str, Any]], palette: dict[str, str]) -> int:
    """Render a mobile-readable two-line cup panel and return its bottom position."""
    title = competition_label(name)
    rect(parts, x, y, width, 30, palette["dark"], 4)
    text(parts, x + 12, y + 21, title, 14, "#ffffff", "700")
    y += 33
    rect(parts, x, y, width, 26, palette["cream_alt"], 0)
    text(parts, x + 10, y + 17, "日期 / 时间", 10, palette["dark"], "700")
    text(parts, x + 150, y + 17, "对手 / 转播渠道", 10, palette["dark"], "700")
    text(parts, x + width - 10, y + 17, "主客 / 比赛场地", 10, palette["dark"], "700", "end")
    parts.append(f'<line x1="{x}" y1="{y + 26}" x2="{x + width}" y2="{y + 26}" stroke="{palette["gold"]}" stroke-width="2"/>')
    y += 27
    ordered = [item for _, item in sorted(enumerate(fixtures), key=lambda pair: fixture_sort_key(name, pair[1], pair[0]))]
    for index, fixture in enumerate(ordered):
        fill = palette["cream"] if index % 2 == 0 else palette["cream_alt"]
        rect(parts, x, y, width, 46, fill, 0)
        first = display_date(fixture) if fixture.get("date") or fixture.get("dateLabel") else fixture.get("stage") or "待定"
        text(parts, x + 10, y + 17, str(first)[:14], 11, palette["ink"], "700")
        text(parts, x + 150, y + 17, str(fixture.get("opponent") or "对手待定")[:15], 11, palette["ink"], "700")
        text(parts, x + width - 10, y + 17, display_home_away(fixture), 11, palette["ink"], "400", "end")
        text(parts, x + 10, y + 37, str(fixture.get("time") or "待定")[:10], 11, palette["muted"], "400")
        text(parts, x + 150, y + 37, display_broadcast(fixture)[:17], 11, palette["muted"], "400")
        text(parts, x + width - 10, y + 37, display_short_location(fixture)[:13], 11, palette["muted"], "400", "end")
        y += 47
    return y + 8


def classic_cup_section(parts: list[str], y: int, fixtures: list[dict[str, Any]], palette: dict[str, str], team: dict[str, Any]) -> int:
    y = classic_section_title(parts, y, "杯赛 · 欧冠", "Cups · Champions League", palette)
    registry = build_registry(fixtures, team)
    cup_specs = specs_for_section(registry, "cup")
    return render_competition_grid(parts, y, cup_specs, fixtures, palette, classic_table_panel) + 10


def classic_broadcast_section(parts: list[str], y: int, fixtures: list[dict[str, Any]], palette: dict[str, str], team: dict[str, Any]) -> int:
    y = classic_section_title(parts, y, "直播渠道汇总", "Broadcast Channels Overview", palette)
    registry = build_registry(fixtures, team)
    names = [spec.name for spec in registry]
    for fixture in fixtures:
        if fixture.get("competition") not in names and fixture.get("competition"):
            names.append(fixture.get("competition"))
    for index in range(0, len(names), 2):
        row_names = names[index:index + 2]
        row_bottom = y
        for column, name in enumerate(row_names):
            x = 32 + column * 516
            rows = [fixture for fixture in fixtures if fixture.get("competition") == name]
            channels = sorted({display_broadcast(fixture) for fixture in rows if display_broadcast(fixture) != "转播待定"})
            label = " / ".join(channels) if channels else "转播待定"
            rect(parts, x, y, 500, 43, palette["cream"], 4, palette["red"])
            text(parts, x + 16, y + 19, competition_label(name), 13, palette["dark"], "700")
            text(parts, x + 16, y + 36, label[:50], 11, palette["muted"])
            row_bottom = max(row_bottom, y + 43)
        y = row_bottom + 6
    return y


def source_summary(payload: dict[str, Any]) -> str:
    sources = payload.get("sources", [])
    organizations = []
    for item in sources:
        if not isinstance(item, dict):
            continue
        organization = str(item.get("organization") or "").strip()
        if organization and organization not in organizations:
            organizations.append(organization)
    return " / ".join(organizations[:4]) or "官方赛事来源"


def make_classic_svg(payload: dict[str, Any], team: dict[str, Any], qr_url: str = "", as_of: str = "") -> str:
    palette = classic_palette(team)
    checked_date = reference_date(payload, as_of)
    all_fixtures = [fixture for fixture in payload.get("fixtures", []) if isinstance(fixture, dict)]
    fixtures = visible_fixtures(all_fixtures, checked_date)
    height = 260
    probe: list[str] = []
    y = 265
    y = classic_opening_section(probe, y, fixtures, palette)
    y = classic_league_section(probe, y, fixtures, palette, team)
    y = classic_cup_section(probe, y, fixtures, palette, team)
    y = classic_broadcast_section(probe, y, fixtures, palette, team)
    height = y + 160
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="{height}" viewBox="0 0 1080 {height}">']
    rect(parts, 0, 0, 1080, height, palette["red"])
    rect(parts, 0, 0, 1080, 58, palette["deep"])
    rect(parts, 0, 58, 1080, 160, palette["dark"])
    parts.append(f'<line x1="0" y1="58" x2="1080" y2="58" stroke="{palette["gold"]}" stroke-width="5"/>')
    parts.append(f'<line x1="0" y1="218" x2="1080" y2="218" stroke="{palette["gold"]}" stroke-width="4"/>')
    crest = crest_href(team)
    if crest:
        parts.append(f'<image href="{crest}" x="50" y="74" width="100" height="130" preserveAspectRatio="xMidYMid meet"/>')
    else:
        parts.append(f'<path d="M72 92 L128 92 L144 110 L136 168 Q100 206 64 168 L56 110 Z" fill="{palette["cream"]}" stroke="{palette["gold"]}" stroke-width="3"/>')
        text(parts, 100, 141, (team.get("nameEn") or "TEAM")[:8].upper(), 11, palette["dark"], "700", "middle")
    text(parts, 174, 105, payload.get("season", "赛季"), 28, palette["gold"], "700")
    text(parts, 174, 158, team.get("nameZh") or team.get("nameEn") or "球队", 48, "#ffffff", "700")
    text(parts, 560, 139, "完整赛程 & 直播渠道", 23, "#ffffff", "700", "middle")
    text(parts, 560, 169, "Fixtures & Broadcast Guide", 15, "#ffd98b", "400", "middle")
    if qr_url:
        qr_svg(parts, qr_url, 900, 78, 112, "")
        text(parts, 956, 205, "格格的工具箱", 11, "#ffffff", "600", "middle")
    else:
        text(parts, 956, 130, team.get("nameEn") or "TEAM", 20, "#ffffff", "700", "middle")
    y = 225
    y = classic_opening_section(parts, y, fixtures, palette)
    y = classic_league_section(parts, y, fixtures, palette, team)
    y = classic_cup_section(parts, y, fixtures, palette, team)
    y = classic_broadcast_section(parts, y, fixtures, palette, team)
    text(parts, 540, y + 30, f"数据来源：{source_summary(payload)}", 13, "#ffd98b", "400", "middle")
    text(parts, 540, y + 52, f"转播安排以中国大陆当地实际播出为准 · 数据检查时间：{payload.get('lastCheckedAt') or '待补充'}", 12, "#ffd98b", "400", "middle")
    text(parts, 540, y + 72, "详细来源与待确认项目见覆盖检查报告", 12, "#ffd98b", "400", "middle")
    footer_y = y + 90
    rect(parts, 0, footer_y, 1080, 70, palette["deep"], 0)
    parts.append(f'<line x1="30" y1="{footer_y + 13}" x2="1050" y2="{footer_y + 13}" stroke="{palette["gold"]}" stroke-width="3"/>')
    text(parts, 540, footer_y + 48, "格格的工具箱 · http://www.wenxueaigege.com", 20, "#ffffff", "700", "middle")
    text(parts, 1028, footer_y + 58, "Skill生成", 10, "#ffd98b", "400", "end")
    parts.append("</svg>")
    return "".join(parts)


def make_classic_share_svg(payload: dict[str, Any], team: dict[str, Any], qr_url: str = "", as_of: str = "") -> str:
    palette = classic_palette(team)
    checked_date = reference_date(payload, as_of)
    fixtures = [fixture for fixture in visible_fixtures(payload.get("fixtures", []), checked_date) if fixture.get("date")]
    fixtures.sort(key=lambda item: (item.get("date") or "9999-99-99", item.get("time") or "99:99"))
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440" viewBox="0 0 1080 1440">']
    rect(parts, 0, 0, 1080, 1440, palette["red"])
    rect(parts, 0, 0, 1080, 250, palette["dark"])
    text(parts, 60, 70, payload.get("season", "赛季"), 28, palette["gold"], "700")
    text(parts, 60, 125, team.get("nameZh") or "球队", 50, "#ffffff", "700")
    text(parts, 60, 170, "近期看球赛程", 22, "#ffffff", "700")
    text(parts, 60, 205, f"数据检查时间：{payload.get('lastCheckedAt') or checked_date}", 14, "#ffd98b")
    if qr_url:
        qr_svg(parts, qr_url, 900, 58, 108, "")
    y = 290
    y = classic_section_title(parts, y, "接下来要看", "Next Matches · 北京时间", palette)
    for fixture in fixtures[:5]:
        classic_match_card(parts, fixture, 32, y, 1016, palette)
        y += 76
    y += 15
    rect(parts, 32, y, 1016, 175, palette["cream"], 5)
    text(parts, 52, y + 32, "直播渠道", 20, palette["dark"], "700")
    text(parts, 52, y + 62, "中国大陆逐场官方排期未确认时显示“转播待定”", 15, palette["muted"])
    text(parts, 52, y + 92, "数据来源：PremierLeague.com / UEFA.com / TheFA.com / EFL.com", 12, palette["muted"])
    text(parts, 52, y + 122, "更多看球工具：wenxueaigege.com", 12, palette["muted"])
    text(parts, 52, y + 152, "保存这张卡片，赛程更新后重新生成", 13, palette["dark"], "700")
    parts.append("</svg>")
    return "".join(parts)


def make_svg(payload: dict[str, Any], team: dict[str, Any], qr_url: str = "", as_of: str = "") -> str:
    primary = team["colors"]["primary"]
    secondary = team["colors"]["secondary"]
    accent = team["colors"]["accent"]
    text_color = team["colors"]["text"]
    fixtures = payload.get("fixtures", [])
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for fixture in fixtures:
        if not isinstance(fixture, dict) or fixture.get("status") == "cancelled":
            continue
        groups[(fixture.get("competition", "赛事待定"), fixture.get("competitionType", ""))].append(fixture)
    for items in groups.values():
        items.sort(key=lambda item: (item.get("date") or "9999-99-99", item.get("time") or "99:99"))
    checked_date = reference_date(payload, as_of)
    upcoming = [f for f in fixtures if isinstance(f, dict) and f.get("date") and f.get("date") >= checked_date and f.get("status") not in {"cancelled", "postponed"}]
    upcoming.sort(key=lambda item: (item.get("date") or "9999", item.get("time") or "99:99"))
    height = 310 + 58 + min(len(upcoming), 5) * 82 + 10
    for items in groups.values():
        months: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            months[(item.get("date") or "待定")[:7]].append(item)
        height += 68
        for month_items in months.values():
            rows = (len(month_items) + 1) // 2 if len(month_items) >= 4 else len(month_items)
            height += 40 + rows * 86
    height += 210
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="{height}" viewBox="0 0 1080 {height}">']
    rect(parts, 0, 0, 1080, height, "#f7f2e9")
    rect(parts, 24, 24, 1032, 250, primary, 18)
    text(parts, 62, 76, "SEASON MATCH GUIDE", 25, accent, "700")
    text(parts, 62, 142, f"{team.get('nameZh') or team.get('nameEn') or '球队'} · {payload.get('season', '赛季待定')}", 48, secondary, "700")
    text(parts, 62, 184, "中国大陆看球赛程", 24, secondary)
    text(parts, 62, 224, f"生成时间：{payload.get('lastCheckedAt') or '待补充'} · 近期起算：{checked_date}", 16, secondary)
    if qr_url:
        if not qr_svg(parts, qr_url, 900, 42, 116, "格格的工具箱"):
            text(parts, 1018, 78, "二维码链接过长", 14, secondary, "600", "end")
            text(parts, 1018, 104, qr_url[:34], 11, secondary, "400", "end")
    else:
        text(parts, 1005, 78, "队徽 /", 15, secondary, "600", "end")
        text(parts, 1005, 104, team.get("nameZh") or team.get("nameEn") or "球队", 18, secondary, "700", "end")
    y = 306
    rect(parts, 40, y, 1000, 44, accent, 8)
    text(parts, 62, y + 29, "接下来要看", 19, text_color, "700")
    text(parts, 1018, y + 29, f"{min(len(upcoming), 5)} 场", 15, text_color, "600", "end")
    y += 58
    for fixture in upcoming[:5]:
        fixture_card(parts, fixture, 40, y, 1000, 72, primary, text_color)
        y += 82
    y += 10
    for (competition, competition_type), items in sorted(groups.items(), key=lambda group: (group[0][1], group[0][0])):
        rect(parts, 40, y, 1000, 48, primary, 8)
        text(parts, 62, y + 31, competition, 21, secondary, "700")
        text(parts, 1018, y + 30, TYPE_LABELS.get(competition_type, "赛事"), 14, accent, "700", "end")
        y += 62
        months: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            months[(item.get("date") or "待定")[:7]].append(item)
        for month, month_items in sorted(months.items()):
            month_label = month if month != "待定" else "日期待定"
            text(parts, 48, y + 26, month_label, 18, text_color, "700")
            y += 40
            if len(month_items) >= 4:
                for index in range(0, len(month_items), 2):
                    row_items = month_items[index:index + 2]
                    for col, fixture in enumerate(row_items):
                        fixture_card(parts, fixture, 40 + col * 510, y, 490, 72, primary, text_color)
                    y += 86
            else:
                for fixture in month_items:
                    fixture_card(parts, fixture, 40, y, 1000, 72, primary, text_color)
                    y += 86
    rect(parts, 40, y + 10, 1000, 170, "#fffdf9", 12, "#eadfd1")
    text(parts, 62, y + 44, "看球提示", 20, primary, "700")
    text(parts, 62, y + 78, "转播信息以中国大陆当地实际播出安排为准。", 16, "#786d66")
    text(parts, 62, y + 108, f"数据检查时间：{payload.get('lastCheckedAt') or '待补充'}", 15, "#786d66")
    if qr_url:
        text(parts, 1018, y + 80, "扫码进入格格的工具箱", 14, "#786d66", "600", "end")
        readable_qr_url = qr_url.replace("https://", "").replace("http://", "")
        if "?" in readable_qr_url:
            domain, query = readable_qr_url.split("?", 1)
            text(parts, 1018, y + 108, domain, 11, "#786d66", "400", "end")
            text(parts, 1018, y + 126, "?" + query[:48], 11, "#786d66", "400", "end")
        else:
            text(parts, 1018, y + 108, readable_qr_url[:44], 11, "#786d66", "400", "end")
    parts.append("</svg>")
    return "".join(parts)


def make_share_svg(payload: dict[str, Any], team: dict[str, Any], qr_url: str = "", as_of: str = "") -> str:
    primary = team["colors"]["primary"]
    secondary = team["colors"]["secondary"]
    accent = team["colors"]["accent"]
    text_color = team["colors"]["text"]
    checked_date = reference_date(payload, as_of)
    fixtures = [f for f in payload.get("fixtures", []) if isinstance(f, dict) and f.get("date") and f.get("date") >= checked_date and f.get("status") not in {"cancelled", "postponed"}]
    fixtures.sort(key=lambda item: (item.get("date") or "9999-99-99", item.get("time") or "99:99"))
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440" viewBox="0 0 1080 1440">']
    rect(parts, 0, 0, 1080, 1440, "#f7f2e9")
    rect(parts, 0, 0, 1080, 300, primary)
    text(parts, 60, 92, "NEXT MATCHES", 27, accent, "700")
    text(parts, 60, 175, team.get("nameZh") or team.get("nameEn") or "球队", 55, secondary, "700")
    text(parts, 60, 225, f"{payload.get('season', '赛季待定')} · 中国大陆看球指南 · {checked_date} 起", 22, secondary)
    y = 360
    for fixture in fixtures[:5]:
        fixture_card(parts, fixture, 50, y, 980, 104, primary, text_color)
        y += 128
    rect(parts, 50, 1030, 980, 270, "#fffdf9", 14, "#eadfd1")
    text(parts, 80, 1080, "转播信息", 24, primary, "700")
    text(parts, 80, 1125, "以中国大陆当地实际播出安排为准", 17, "#786d66")
    text(parts, 80, 1170, f"数据检查时间：{payload.get('lastCheckedAt') or '待补充'}", 15, "#786d66")
    if qr_url:
        qr_ok = qr_svg(parts, qr_url, 820, 1140, 150, "格格的工具箱")
        text(parts, 80, 1220, "更多看球工具与实用小工具", 14, "#786d66", "600")
        if not qr_ok:
            text(parts, 80, 1252, "二维码链接过长：" + qr_url[:64], 12, "#9a6b3b")
        else:
            text(parts, 80, 1252, qr_url[:64], 11, "#786d66")
    parts.append("</svg>")
    return "".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成足球看球赛程 SVG/HTML 海报")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--team-profile", type=Path)
    parser.add_argument("--qr-url", default=DEFAULT_QR_URL, help="二维码目标链接，默认带来源标记的格格工具箱主页")
    parser.add_argument("--no-qr", action="store_true", help="不在输出中绘制二维码")
    parser.add_argument("--as-of", default="", help="近期比赛起算日期，默认使用 asOfDate 或 lastCheckedAt")
    parser.add_argument("--png-scale", type=int, default=4, choices=range(1, 9), metavar="1-8", help="PNG 输出倍率，默认 4")
    parser.add_argument("--no-png", action="store_true", help="只生成 SVG/HTML，不生成 PNG")
    parser.add_argument("--allow-text-crest", action="store_true", help="仅内部排版草稿允许文字队徽占位；正式海报不要使用")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    profile = team_profile(payload, args.team_profile)
    try:
        require_official_crest(profile, args.allow_text_crest)
    except ValueError as exc:
        parser.error(str(exc))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    qr_url = "" if args.no_qr else args.qr_url
    try:
        if qr_url:
            qr_matrix(qr_url)
        qr_rendered = bool(qr_url)
    except ValueError:
        qr_rendered = False
    poster = make_classic_svg(payload, profile, qr_url, args.as_of)
    poster_svg_path = args.output_dir / "season-poster.svg"
    poster_svg_path.write_text(poster, encoding="utf-8")
    write_html(args.output_dir / "season-poster.html", "赛季看球赛程", poster, esc)
    outputs = ["season-poster.svg", "season-poster.html"]
    rasterizer = "disabled" if args.no_png else rasterizer_name()
    png_outputs: list[dict[str, Any]] = []
    png_error = ""
    if not args.no_png and rasterizer:
        for stem, svg_path, svg_content in (("season-poster", poster_svg_path, poster),):
            png_name = f"{stem}-{args.png_scale}x.png"
            png_path = args.output_dir / png_name
            width, height = write_scaled_png(svg_path, png_path, svg_content, args.png_scale, rasterizer)
            outputs.append(png_name)
            png_outputs.append({"file": png_name, "width": width, "height": height, "scale": args.png_scale})
    elif not args.no_png:
        png_error = rasterizer_install_hint()
        print(f"未生成 PNG：{png_error}")
    manifest = {
        "outputs": outputs,
        "svgMaster": True,
        "pngRasterizer": rasterizer or "unavailable",
        "pngOutputs": png_outputs,
        "pngError": png_error,
        "team": profile,
        "season": payload.get("season", ""),
        "lastCheckedAt": payload.get("lastCheckedAt", ""),
        "asOfDate": reference_date(payload, args.as_of),
        "qrUrl": qr_url,
        "qrUrlProvided": bool(qr_url),
        "qrRendered": qr_rendered,
        "qrPlacement": {"seasonPoster": "header-top-right"},
        "crest": {
            "asset": profile.get("crest", ""),
            "source": profile.get("crestSource", ""),
            "preserveAspectRatio": True,
            "rightsNote": profile.get("crestRightsNote", ""),
        },
        "note": "本 Skill 只生成完整赛季长图；SVG 为矢量母版，默认同时生成 4 倍 PNG。二维码由 Skill 自带的标准库编码器生成。",
    }
    (args.output_dir / "render-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已生成海报：{args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
