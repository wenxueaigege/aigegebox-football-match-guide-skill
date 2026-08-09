"""Generic classic-poster panel layout."""

from __future__ import annotations

from typing import Any, Callable

from .registry import CompetitionSpec, fixtures_for_spec, pending_fixture


PanelRenderer = Callable[[list[str], int, int, int, str, list[dict[str, Any]], dict[str, str]], int]


def render_competition_grid(
    parts: list[str],
    y: int,
    specs: list[CompetitionSpec],
    fixtures: list[dict[str, Any]],
    palette: dict[str, str],
    render_panel: PanelRenderer,
) -> int:
    """Render every configured competition without special-casing a team.

    Long competitions such as continental tournaments split their rows into
    two panels. Short competitions occupy one panel and are paired with the
    next short competition.
    """
    panels: list[tuple[str, list[dict[str, Any]]]] = []
    for spec in specs:
        rows = fixtures_for_spec(fixtures, spec)
        if not rows and spec.show_pending:
            rows = [pending_fixture(spec)]
        if not rows:
            continue
        if spec.layout == "split-rows" and len(rows) > 1:
            split = (len(rows) + 1) // 2
            panels.append((spec.name, rows[:split]))
            panels.append((spec.name, rows[split:]))
        else:
            panels.append((spec.name, rows))

    for index in range(0, len(panels), 2):
        left_name, left_rows = panels[index]
        right = panels[index + 1] if index + 1 < len(panels) else None
        left_bottom = render_panel(parts, 32, y, 500, left_name, left_rows, palette)
        right_bottom = y
        if right:
            right_bottom = render_panel(parts, 548, y, 500, right[0], right[1], palette)
        y = max(left_bottom, right_bottom) + 8
    return y
