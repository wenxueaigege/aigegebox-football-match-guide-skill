import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "aigegebox-football-match-guide"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from poster.classic_layout import render_competition_grid  # noqa: E402
from poster.registry import build_registry, specs_for_section  # noqa: E402
from render_poster import footer_site_text  # noqa: E402


class PosterModuleTests(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads((SKILL_ROOT / "teams" / "real-madrid.json").read_text(encoding="utf-8"))

    def test_expected_competitions_never_leak_into_cup_section(self):
        fixtures = [
            {"competition": "La Liga", "competitionType": "domestic-league"},
            {"competition": "Copa del Rey", "competitionType": "domestic-cup"},
        ]
        registry = build_registry(fixtures, {**self.profile, "competitionSpecs": []})
        cup_names = {spec.name for spec in specs_for_section(registry, "cup")}
        league_names = {spec.name for spec in specs_for_section(registry, "league")}
        self.assertNotIn("La Liga", cup_names)
        self.assertIn("La Liga", league_names)
        self.assertIn("Copa del Rey", cup_names)

    def test_configured_pending_competitions_are_kept(self):
        registry = build_registry([], self.profile)
        cup_names = [spec.name for spec in specs_for_section(registry, "cup")]
        self.assertEqual(cup_names, ["Copa del Rey", "Supercopa de España", "UEFA Champions League"])

    def test_long_competition_renders_every_row(self):
        fixtures = [
            {"competition": "UEFA Champions League", "competitionType": "continental", "stage": f"第{i}轮"}
            for i in range(1, 9)
        ]
        registry = build_registry(fixtures, self.profile)
        rendered = []

        def fake_panel(parts, x, y, width, name, rows, palette):
            rendered.append((name, len(rows)))
            return y + len(rows)

        render_competition_grid([], 0, specs_for_section(registry, "cup"), fixtures, {}, fake_panel)
        self.assertEqual(sum(count for name, count in rendered if name == "UEFA Champions League"), 8)
        self.assertEqual(len([name for name, count in rendered if name == "UEFA Champions League"]), 2)

    def test_custom_footer_url_is_shortened_without_query(self):
        self.assertEqual(footer_site_text("https://example.com/guide?from=test"), "example.com/guide")


if __name__ == "__main__":
    unittest.main()
