"""Competition registry and section classification for poster rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CUP_TYPES = {
    "domestic-cup",
    "league-cup",
    "continental",
    "super-cup",
    "club-world",
    "playoff",
    "qualifier",
}
KNOWN_TYPES = {
    "Premier League": "domestic-league",
    "La Liga": "domestic-league",
    "Official Friendlies": "friendly",
    "FA Community Shield": "super-cup",
    "Emirates Cup": "friendly",
    "EFL Cup": "league-cup",
    "FA Cup": "domestic-cup",
    "Copa del Rey": "domestic-cup",
    "Supercopa de España": "super-cup",
    "UEFA Champions League": "continental",
}


@dataclass(frozen=True)
class CompetitionSpec:
    name: str
    competition_type: str
    section: str
    layout: str = "paired"
    show_pending: bool = True


def section_for_type(competition_type: str, name: str = "") -> str:
    if competition_type == "friendly" or name == "FA Community Shield":
        return "opening"
    if competition_type == "domestic-league":
        return "league"
    if competition_type in CUP_TYPES:
        return "cup"
    return "other"


def type_for_name(name: str, fixtures: list[dict[str, Any]]) -> str:
    for fixture in fixtures:
        if fixture.get("competition") == name and fixture.get("competitionType"):
            return str(fixture["competitionType"])
    return KNOWN_TYPES.get(name, "other")


def _spec_from_item(item: Any, fixtures: list[dict[str, Any]]) -> CompetitionSpec | None:
    if isinstance(item, str):
        name = item
        competition_type = type_for_name(name, fixtures)
        layout = "split-rows" if competition_type == "continental" else "paired"
        return CompetitionSpec(name, competition_type, section_for_type(competition_type, name), layout)
    if not isinstance(item, dict) or not item.get("name"):
        return None
    name = str(item["name"])
    competition_type = str(item.get("competitionType") or type_for_name(name, fixtures))
    section = str(item.get("section") or section_for_type(competition_type, name))
    layout = str(item.get("layout") or ("split-rows" if competition_type == "continental" else "paired"))
    return CompetitionSpec(name, competition_type, section, layout, bool(item.get("showPending", True)))


def build_registry(
    fixtures: list[dict[str, Any]],
    team: dict[str, Any],
) -> list[CompetitionSpec]:
    """Build renderable competitions from team configuration and actual fixtures.

    expectedCompetitions is intentionally not read here. It belongs to coverage
    reporting, not layout selection.
    """
    configured = team.get("competitionSpecs")
    if not isinstance(configured, list):
        configured = team.get("competitionOrder") or []

    specs: list[CompetitionSpec] = []
    names: set[str] = set()
    for item in configured:
        spec = _spec_from_item(item, fixtures)
        if spec and spec.name not in names:
            specs.append(spec)
            names.add(spec.name)

    for fixture in fixtures:
        name = fixture.get("competition")
        if not name or name in names:
            continue
        competition_type = str(fixture.get("competitionType") or "other")
        spec = CompetitionSpec(
            str(name),
            competition_type,
            section_for_type(competition_type, str(name)),
            "split-rows" if competition_type == "continental" else "paired",
        )
        if spec.section != "other":
            specs.append(spec)
            names.add(spec.name)

    return specs


def specs_for_section(registry: list[CompetitionSpec], section: str) -> list[CompetitionSpec]:
    return [spec for spec in registry if spec.section == section]


def fixtures_for_spec(fixtures: list[dict[str, Any]], spec: CompetitionSpec) -> list[dict[str, Any]]:
    return [fixture for fixture in fixtures if fixture.get("competition") == spec.name]


def pending_fixture(spec: CompetitionSpec) -> dict[str, Any]:
    return {
        "competition": spec.name,
        "competitionType": spec.competition_type,
        "stage": "赛事待定",
        "opponent": "对手待定",
        "status": "tbd",
        "broadcasts": [],
        "note": "官方赛历或抽签信息待确认",
    }
