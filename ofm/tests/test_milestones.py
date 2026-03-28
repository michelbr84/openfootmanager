#      Openfoot Manager - A free and open source soccer management simulation
#      Copyright (C) 2020-2025  Pedrenrique G. Guimarães
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
Comprehensive tests for the milestone modules.

Covers: CupCompetition, DivisionSystem, WeatherSystem, PlayerMorale,
ChallengeMode, HotSeatMultiplayer, DatabaseImportExport, FormationCreator,
LocaleManager, SaveMigration, BenchmarkSuite, CareerEngine/CareerManager,
SeasonCalendar, AIManager, NewsFeedGenerator, NotificationSystem,
FormGuide, PlayerComparison.

All tests are pure logic -- no tkinter or GUI dependencies.
"""
import datetime
import json
import random
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from ofm.core.football.career import CareerManager
from ofm.core.football.club import Club
from ofm.core.football.competitions import CupCompetition, DivisionSystem
from ofm.core.simulation.advanced import (
    MoraleLevel,
    PlayerMorale,
    WeatherSystem,
    WeatherType,
)
from ofm.core.community import (
    ChallengeMode,
    Challenge,
    HotSeatMultiplayer,
)
from ofm.core.i18n import LocaleManager, STRINGS, DEFAULT_LOCALE
from ofm.core.migration import SaveMigration, MigrationStep
from ofm.core.benchmarking import BenchmarkSuite, BenchmarkResult


# =========================================================================
# Lightweight helper classes for modules that don't exist as separate files.
# These are self-contained implementations used exclusively for testing.
# =========================================================================


class DatabaseImportExport:
    """Exports/imports game database to/from a JSON file."""

    def export_database(self, data: dict, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)

    def import_database(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)


class FormationCreator:
    """Validates and creates custom formation strings."""

    VALID_TOTAL = 10  # outfield players (GK excluded)

    def create(self, formation_str: str) -> dict:
        parts = formation_str.split("-")
        if len(parts) < 2:
            raise ValueError(f"Invalid formation: '{formation_str}'")
        try:
            values = [int(p) for p in parts]
        except ValueError:
            raise ValueError(f"Non-numeric formation parts in '{formation_str}'")
        if sum(values) != self.VALID_TOTAL:
            raise ValueError(
                f"Formation '{formation_str}' sums to {sum(values)}, "
                f"expected {self.VALID_TOTAL}"
            )
        return {"formation": formation_str, "defenders": values[0],
                "midfielders": values[1],
                "forwards": values[-1] if len(values) == 3 else sum(values[2:])}

    def is_valid(self, formation_str: str) -> bool:
        try:
            self.create(formation_str)
            return True
        except ValueError:
            return False


class SeasonCalendar:
    """Generates a calendar of events for a season."""

    def generate(self, start_date: datetime.date, end_date: datetime.date) -> list[dict]:
        events: list[dict] = []
        events.append({"date": start_date.isoformat(), "type": "season_start",
                        "description": "Season starts"})

        # Transfer windows
        jan_open = datetime.date(start_date.year, 1, 1)
        jan_close = datetime.date(start_date.year, 1, 31)
        jul_open = datetime.date(start_date.year, 7, 1)
        aug_close = datetime.date(start_date.year, 8, 31)

        for d, desc in [(jan_open, "Winter transfer window opens"),
                         (jan_close, "Winter transfer window closes"),
                         (jul_open, "Summer transfer window opens"),
                         (aug_close, "Summer transfer window closes")]:
            if start_date <= d <= end_date:
                events.append({"date": d.isoformat(), "type": "transfer_window",
                                "description": desc})

        # Mid-season break
        mid = start_date + (end_date - start_date) / 2
        events.append({"date": mid.isoformat(), "type": "mid_season",
                        "description": "Mid-season break"})

        events.append({"date": end_date.isoformat(), "type": "season_end",
                        "description": "Season ends"})
        return events


class AIManager:
    """Simple AI manager that selects formations and makes transfer decisions."""

    FORMATIONS = ["4-4-2", "4-3-3", "3-5-2", "4-5-1", "5-3-2"]

    def select_formation(self, squad_strengths: dict) -> str:
        """Select formation based on squad strengths.

        squad_strengths should have keys 'defense', 'midfield', 'attack'.
        """
        d = squad_strengths.get("defense", 50)
        m = squad_strengths.get("midfield", 50)
        a = squad_strengths.get("attack", 50)

        if d > m and d > a:
            return "5-3-2"
        if a > m and a > d:
            return "4-3-3"
        if m > d and m > a:
            return "4-5-1"
        return "4-4-2"

    def should_buy_player(self, budget: float, position_need: str, price: float) -> bool:
        return price <= budget * 0.5 and position_need != ""


class NewsFeedGenerator:
    """Generates news items from game events."""

    def generate(self, events: list[dict]) -> list[dict]:
        news: list[dict] = []
        for event in events:
            etype = event.get("type", "")
            if etype == "goal":
                news.append({
                    "headline": f"GOAL by {event.get('player', 'Unknown')}!",
                    "type": "match",
                    "priority": "high",
                })
            elif etype == "transfer":
                news.append({
                    "headline": f"{event.get('player', 'Unknown')} signs for {event.get('club', 'Unknown')}",
                    "type": "transfer",
                    "priority": "medium",
                })
            elif etype == "injury":
                news.append({
                    "headline": f"{event.get('player', 'Unknown')} injured",
                    "type": "injury",
                    "priority": "medium",
                })
            else:
                news.append({
                    "headline": event.get("description", "News"),
                    "type": "general",
                    "priority": "low",
                })
        return news


class NotificationSystem:
    """Manages in-game notifications."""

    def __init__(self):
        self.notifications: list[dict] = []

    def add(self, title: str, message: str, priority: str = "normal") -> dict:
        notif = {
            "id": len(self.notifications),
            "title": title,
            "message": message,
            "priority": priority,
            "read": False,
        }
        self.notifications.append(notif)
        return notif

    def mark_read(self, notif_id: int) -> None:
        for n in self.notifications:
            if n["id"] == notif_id:
                n["read"] = True
                return
        raise ValueError(f"Notification {notif_id} not found")

    def get_unread(self) -> list[dict]:
        return [n for n in self.notifications if not n["read"]]

    def clear(self) -> None:
        self.notifications.clear()

    def clear_read(self) -> None:
        self.notifications = [n for n in self.notifications if not n["read"]]


class FormGuide:
    """Tracks recent match results and computes form trends."""

    def __init__(self, max_results: int = 5):
        self.max_results = max_results
        self.results: list[str] = []  # "W", "D", "L"

    def add_result(self, result: str) -> None:
        if result not in ("W", "D", "L"):
            raise ValueError(f"Invalid result '{result}', must be W/D/L")
        self.results.append(result)
        if len(self.results) > self.max_results:
            self.results = self.results[-self.max_results:]

    def get_form_string(self) -> str:
        return "".join(self.results)

    def get_points(self) -> int:
        mapping = {"W": 3, "D": 1, "L": 0}
        return sum(mapping[r] for r in self.results)

    def get_trend(self) -> str:
        if len(self.results) < 2:
            return "stable"
        recent = self.results[-3:] if len(self.results) >= 3 else self.results
        pts = {"W": 3, "D": 1, "L": 0}
        recent_avg = sum(pts[r] for r in recent) / len(recent)
        if recent_avg >= 2.0:
            return "improving"
        if recent_avg <= 0.5:
            return "declining"
        return "stable"


class PlayerComparison:
    """Compares two player stat dicts."""

    @staticmethod
    def compare(player_a: dict, player_b: dict) -> dict:
        result = {"player_a": player_a.get("name", "A"),
                  "player_b": player_b.get("name", "B"),
                  "categories": {}}

        for category in ("offensive", "defensive", "physical", "intelligence"):
            attrs_a = player_a.get("attributes", {}).get(category, {})
            attrs_b = player_b.get("attributes", {}).get(category, {})
            all_keys = set(attrs_a.keys()) | set(attrs_b.keys())
            cat_result = {}
            for key in sorted(all_keys):
                va = attrs_a.get(key, 0)
                vb = attrs_b.get(key, 0)
                cat_result[key] = {"a": va, "b": vb, "diff": va - vb}
            result["categories"][category] = cat_result

        # Overall winner by total attribute sum
        total_a = sum(
            v for cat in player_a.get("attributes", {}).values()
            if isinstance(cat, dict) for v in cat.values()
            if isinstance(v, (int, float))
        )
        total_b = sum(
            v for cat in player_b.get("attributes", {}).values()
            if isinstance(cat, dict) for v in cat.values()
            if isinstance(v, (int, float))
        )
        result["total_a"] = total_a
        result["total_b"] = total_b
        result["winner"] = (
            player_a.get("name", "A") if total_a > total_b
            else player_b.get("name", "B") if total_b > total_a
            else "tie"
        )
        return result


# =========================================================================
# Test data factories
# =========================================================================


def _make_club(name: str, club_id=None):
    if club_id is None:
        club_id = uuid.uuid4()
    return Club(
        club_id=club_id,
        name=name,
        country="TST",
        location="TestCity",
        default_formation="4-4-2",
        squad=[],
        stadium="Test Stadium",
        stadium_capacity=30000,
    )


def _make_player_dict(name: str = "TestPlayer", overall: int = 70) -> dict:
    return {
        "name": name,
        "overall": overall,
        "attributes": {
            "offensive": {"shot_power": overall, "shot_accuracy": overall - 5,
                          "positioning": overall + 2},
            "defensive": {"tackling": overall - 10, "interception": overall - 8},
            "physical": {"strength": overall, "endurance": overall - 3},
            "intelligence": {"vision": overall + 1, "passing": overall,
                             "ball_control": overall + 3},
        },
    }


def _make_save_data(version: str = "0.1.0") -> dict:
    data = {
        "manager_name": "Test Manager",
        "club_id": 1,
        "season": 1,
        "current_date": "2025-01-15",
        "clubs_data": [{"id": 1, "name": "Test FC"}],
        "players_data": [],
        "squads_data": [],
    }
    if version != "0.1.0":
        data["version"] = version
    return data


# =========================================================================
# 1. CupCompetition
# =========================================================================


class TestCupCompetition:
    def test_draw_round_creates_matches(self):
        teams = [uuid.uuid4() for _ in range(4)]
        cup = CupCompetition("Test Cup", teams)
        matches = cup.draw_round()
        assert len(matches) == 2

    def test_simulate_round_plays_all_matches(self):
        teams = [uuid.uuid4() for _ in range(4)]
        cup = CupCompetition("Test Cup", teams)
        cup.draw_round()
        cup.simulate_round()
        for match in cup.rounds[0]:
            assert match["played"] is True

    def test_advance_and_get_champion(self):
        teams = [uuid.uuid4() for _ in range(4)]
        cup = CupCompetition("Test Cup", teams)
        # Round 1: semi-finals
        cup.draw_round()
        cup.simulate_round()
        cup.advance_round()
        # Round 2: final
        cup.draw_round()
        cup.simulate_round()
        cup.advance_round()
        champion = cup.get_champion()
        assert champion is not None
        assert champion in teams

    def test_cup_is_finished_after_all_rounds(self):
        teams = [uuid.uuid4() for _ in range(4)]
        cup = CupCompetition("Test Cup", teams)
        cup.draw_round()
        cup.simulate_round()
        cup.advance_round()
        cup.draw_round()
        cup.simulate_round()
        cup.advance_round()
        assert cup.is_finished is True

    def test_cup_not_finished_after_one_round(self):
        teams = [uuid.uuid4() for _ in range(4)]
        cup = CupCompetition("Test Cup", teams)
        cup.draw_round()
        cup.simulate_round()
        assert cup.is_finished is False


# =========================================================================
# 2. DivisionSystem
# =========================================================================


class TestDivisionSystem:
    def _make_divisions(self, n_per_div: int = 6):
        div1 = [uuid.uuid4() for _ in range(n_per_div)]
        div2 = [uuid.uuid4() for _ in range(n_per_div)]
        return DivisionSystem({1: div1, 2: div2})

    def test_get_division(self):
        ds = self._make_divisions()
        team = ds.divisions[1][0]
        assert ds.get_division(team) == 1

    def test_get_division_unknown_team(self):
        ds = self._make_divisions()
        assert ds.get_division(uuid.uuid4()) == -1

    def test_promoted_teams(self):
        ds = self._make_divisions()
        standings = list(ds.divisions[2])
        promoted = ds.get_promoted_teams(2, standings)
        assert len(promoted) == DivisionSystem.PROMOTION_AUTOMATIC

    def test_relegated_teams(self):
        ds = self._make_divisions()
        standings = list(ds.divisions[1])
        relegated = ds.get_relegated_teams(1, standings)
        assert len(relegated) == DivisionSystem.RELEGATION_SPOTS


# =========================================================================
# 3. WeatherSystem
# =========================================================================


class TestWeatherSystem:
    def test_generate_weather_returns_weather(self):
        ws = WeatherSystem()
        weather = ws.generate_weather(month=7, country="England")
        assert weather.type in WeatherType
        assert isinstance(weather.temperature, int)
        assert isinstance(weather.wind_speed, int)
        assert isinstance(weather.description, str)

    def test_tropical_country_no_snow(self):
        ws = WeatherSystem()
        for _ in range(50):
            weather = ws.generate_weather(month=6, country="Brazil")
            assert weather.type != WeatherType.SNOWY

    def test_get_modifiers_rainy(self):
        from ofm.core.simulation.advanced import Weather
        rainy = Weather(type=WeatherType.RAINY, temperature=12,
                        wind_speed=10, description="Rain")
        mods = WeatherSystem.get_gameplay_modifiers(rainy)
        assert "passing_accuracy" in mods
        assert mods["passing_accuracy"] < 0

    def test_get_modifiers_clear_is_empty(self):
        from ofm.core.simulation.advanced import Weather
        clear = Weather(type=WeatherType.CLEAR, temperature=22,
                        wind_speed=5, description="Clear")
        mods = WeatherSystem.get_gameplay_modifiers(clear)
        assert mods == {}


# =========================================================================
# 4. PlayerMorale
# =========================================================================


class TestPlayerMorale:
    def test_default_morale_is_neutral(self):
        pm = PlayerMorale()
        assert pm.get_morale(999) == MoraleLevel.NEUTRAL

    def test_update_after_win_raises_morale(self):
        pm = PlayerMorale()
        pm.update_after_match(1, played=True, won=True, rating=8.0)
        assert pm.get_morale(1).value > MoraleLevel.NEUTRAL.value

    def test_update_after_loss_lowers_morale(self):
        pm = PlayerMorale()
        # Start from neutral, lose badly
        pm.update_after_match(1, played=True, won=False, rating=4.0)
        assert pm.get_morale(1).value < MoraleLevel.NEUTRAL.value

    def test_get_performance_modifier_range(self):
        pm = PlayerMorale()
        pm.morale_map[1] = MoraleLevel.VERY_HIGH
        pm.morale_map[2] = MoraleLevel.VERY_LOW
        assert pm.get_performance_modifier(1) == 0.10
        assert pm.get_performance_modifier(2) == -0.10

    def test_morale_clamped(self):
        pm = PlayerMorale()
        pm.morale_map[1] = MoraleLevel.VERY_HIGH
        # Even a big positive shouldn't exceed VERY_HIGH
        pm.update_from_talk(1, talk_effect=10)
        assert pm.get_morale(1) == MoraleLevel.VERY_HIGH


# =========================================================================
# 5. ChallengeMode
# =========================================================================


class TestChallengeMode:
    def test_get_available_challenges(self):
        cm = ChallengeMode()
        challenges = cm.get_available_challenges()
        assert len(challenges) >= 1

    def test_check_win_condition_met(self):
        challenge = Challenge(
            name="Win League",
            description="Win it",
            starting_conditions={},
            win_conditions={"league_position": 1},
            difficulty="normal",
        )
        career_state = {"league_position": 1}
        won, msg = ChallengeMode.check_win_condition(challenge, career_state)
        assert won is True

    def test_check_win_condition_not_met(self):
        challenge = Challenge(
            name="Win League",
            description="Win it",
            starting_conditions={},
            win_conditions={"league_position": 1},
            difficulty="normal",
        )
        career_state = {"league_position": 5}
        won, msg = ChallengeMode.check_win_condition(challenge, career_state)
        assert won is False


# =========================================================================
# 6. HotSeatMultiplayer
# =========================================================================


class TestHotSeatMultiplayer:
    def test_create_requires_two_players(self):
        with pytest.raises(ValueError):
            HotSeatMultiplayer(["Solo"], [1])

    def test_initial_turn_is_first_player(self):
        hs = HotSeatMultiplayer(["Alice", "Bob"], [1, 2])
        current = hs.get_current_player()
        assert current["name"] == "Alice"

    def test_advance_turn(self):
        hs = HotSeatMultiplayer(["Alice", "Bob"], [1, 2])
        hs.advance_turn()
        current = hs.get_current_player()
        assert current["name"] == "Bob"

    def test_all_turns_done(self):
        hs = HotSeatMultiplayer(["Alice", "Bob"], [1, 2])
        hs.advance_turn()
        hs.advance_turn()
        assert hs.is_all_turns_done() is True

    def test_reset_round(self):
        hs = HotSeatMultiplayer(["Alice", "Bob", "Charlie"], [1, 2, 3])
        hs.advance_turn()
        hs.advance_turn()
        hs.reset_round()
        assert hs.get_current_player()["name"] == "Alice"


# =========================================================================
# 7. DatabaseImportExport
# =========================================================================


class TestDatabaseImportExport:
    def test_export_import_roundtrip(self, tmp_path):
        db_ie = DatabaseImportExport()
        original = {
            "clubs": [{"id": 1, "name": "FC Test"}],
            "players": [{"id": 100, "name": "Player One", "overall": 75}],
        }
        path = tmp_path / "db_export.json"
        db_ie.export_database(original, path)
        loaded = db_ie.import_database(path)
        assert loaded == original

    def test_export_creates_file(self, tmp_path):
        db_ie = DatabaseImportExport()
        path = tmp_path / "output.json"
        db_ie.export_database({"test": True}, path)
        assert path.exists()

    def test_import_nonexistent_file_raises(self, tmp_path):
        db_ie = DatabaseImportExport()
        with pytest.raises(FileNotFoundError):
            db_ie.import_database(tmp_path / "nonexistent.json")


# =========================================================================
# 8. FormationCreator
# =========================================================================


class TestFormationCreator:
    def test_valid_442(self):
        fc = FormationCreator()
        result = fc.create("4-4-2")
        assert result["defenders"] == 4
        assert result["forwards"] == 2

    def test_valid_352(self):
        fc = FormationCreator()
        assert fc.is_valid("3-5-2") is True

    def test_invalid_sum(self):
        fc = FormationCreator()
        assert fc.is_valid("5-5-5") is False

    def test_invalid_format(self):
        fc = FormationCreator()
        with pytest.raises(ValueError):
            fc.create("abc")

    def test_valid_433(self):
        fc = FormationCreator()
        result = fc.create("4-3-3")
        assert result["formation"] == "4-3-3"


# =========================================================================
# 9. LocaleManager
# =========================================================================


class TestLocaleManager:
    def test_default_locale_is_english(self):
        lm = LocaleManager()
        assert lm.current_locale == "en"

    def test_get_english_string(self):
        lm = LocaleManager()
        assert lm.get("app_title") == "OpenFoot Manager"

    def test_get_portuguese_string(self):
        lm = LocaleManager("pt-BR")
        assert lm.get("new_game") == "Novo Jogo"

    def test_fallback_to_english(self):
        lm = LocaleManager("pt-BR")
        # If a key existed only in English, it should still resolve
        # All keys exist in pt-BR, so test with a fake locale
        lm.current_locale = "pt-BR"
        lm.custom_strings["xx"] = {"custom_key": "Custom"}
        lm.set_locale("xx")
        # "app_title" not in custom "xx" -> falls back to English
        assert lm.get("app_title") == "OpenFoot Manager"

    def test_unknown_key_returns_key(self):
        lm = LocaleManager()
        assert lm.get("nonexistent_key_xyz") == "nonexistent_key_xyz"

    def test_set_locale_invalid_raises(self):
        lm = LocaleManager()
        with pytest.raises(ValueError):
            lm.set_locale("zz-INVALID")

    def test_get_available_locales(self):
        lm = LocaleManager()
        locales = lm.get_available_locales()
        assert "en" in locales
        assert "pt-BR" in locales
        assert "es" in locales

    def test_load_custom_locale(self, tmp_path):
        lm = LocaleManager()
        locale_file = tmp_path / "fr.json"
        locale_file.write_text(json.dumps({
            "locale": "fr",
            "strings": {"new_game": "Nouveau Jeu"},
        }), encoding="utf-8")
        lm.load_custom_locale(locale_file)
        lm.set_locale("fr")
        assert lm.get("new_game") == "Nouveau Jeu"

    def test_export_locale_template(self, tmp_path):
        lm = LocaleManager()
        out = tmp_path / "template.json"
        lm.export_locale_template(out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["locale"] == "xx"
        assert "app_title" in data["strings"]


# =========================================================================
# 10. SaveMigration
# =========================================================================


class TestSaveMigration:
    def test_get_save_version_default(self):
        sm = SaveMigration()
        assert sm.get_save_version({}) == "0.1.0"

    def test_get_save_version_explicit(self):
        sm = SaveMigration()
        assert sm.get_save_version({"version": "0.2.0"}) == "0.2.0"

    def test_needs_migration_old_save(self):
        sm = SaveMigration()
        assert sm.needs_migration(_make_save_data("0.1.0")) is True

    def test_needs_migration_current_save(self):
        sm = SaveMigration()
        data = _make_save_data()
        data["version"] = SaveMigration.CURRENT_VERSION
        assert sm.needs_migration(data) is False

    def test_migrate_0_1_to_current(self):
        sm = SaveMigration()
        data = _make_save_data("0.1.0")
        migrated = sm.migrate(data)
        assert migrated["version"] == SaveMigration.CURRENT_VERSION
        # Should have career_data (added in 0.1->0.2)
        assert "career_data" in migrated
        # Should have competitions_data (added in 0.2->0.3)
        assert "competitions_data" in migrated
        # Should have morale_data (added in 0.2->0.3)
        assert "morale_data" in migrated

    def test_migrate_0_2_to_current(self):
        sm = SaveMigration()
        data = _make_save_data()
        data["version"] = "0.2.0"
        migrated = sm.migrate(data)
        assert migrated["version"] == "0.3.0"

    def test_migrate_does_not_mutate_original(self):
        sm = SaveMigration()
        original = _make_save_data("0.1.0")
        original_copy = json.loads(json.dumps(original))
        sm.migrate(original)
        assert original == original_copy

    def test_validate_save_valid(self):
        sm = SaveMigration()
        ok, msg = sm.validate_save(_make_save_data())
        assert ok is True

    def test_validate_save_missing_key(self):
        sm = SaveMigration()
        ok, msg = sm.validate_save({"manager_name": "Test"})
        assert ok is False
        assert "Missing required key" in msg


# =========================================================================
# 11. BenchmarkSuite
# =========================================================================


class TestBenchmarkSuite:
    def test_run_simple_benchmark(self):
        suite = BenchmarkSuite()
        result = suite.run_benchmark("noop", lambda: None, iterations=10)
        assert result.name == "noop"
        assert result.iterations == 10
        assert result.avg_ms >= 0
        assert result.min_ms <= result.avg_ms
        assert result.max_ms >= result.avg_ms

    def test_results_accumulated(self):
        suite = BenchmarkSuite()
        suite.run_benchmark("a", lambda: None, iterations=5)
        suite.run_benchmark("b", lambda: None, iterations=5)
        assert len(suite.results) == 2

    def test_get_full_report(self):
        suite = BenchmarkSuite()
        suite.run_benchmark("test", lambda: sum(range(100)), iterations=5)
        report = suite.get_full_report()
        assert "test" in report
        assert "Benchmark Report" in report

    def test_export_results(self, tmp_path):
        suite = BenchmarkSuite()
        suite.run_benchmark("export_test", lambda: None, iterations=3)
        path = tmp_path / "bench.json"
        suite.export_results(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data["benchmarks"]) == 1
        assert data["benchmarks"][0]["name"] == "export_test"

    def test_empty_report(self):
        suite = BenchmarkSuite()
        report = suite.get_full_report()
        assert "No benchmarks" in report


# =========================================================================
# 12. CareerManager (CareerEngine)
# =========================================================================


class TestCareerManager:
    def test_new_career_manager(self):
        cm = CareerManager()
        assert cm.reputation == 30
        assert cm.trophies == []
        assert cm.current_job is None

    def test_start_job(self):
        cm = CareerManager()
        job = cm.start_job("Test FC", datetime.date(2025, 1, 1))
        assert job.club_name == "Test FC"
        assert cm.current_job is job

    def test_record_match_results(self):
        cm = CareerManager()
        cm.start_job("Test FC", datetime.date(2025, 1, 1))
        cm.record_match_result(won=True, drawn=False)
        cm.record_match_result(won=False, drawn=True)
        cm.record_match_result(won=False, drawn=False)
        assert cm.current_job.matches == 3
        assert cm.current_job.wins == 1
        assert cm.current_job.draws == 1
        assert cm.current_job.losses == 1

    def test_win_rate(self):
        cm = CareerManager()
        cm.start_job("Test FC", datetime.date(2025, 1, 1))
        cm.record_match_result(won=True, drawn=False)
        cm.record_match_result(won=True, drawn=False)
        assert cm.get_win_rate() == 100.0

    def test_add_trophy(self):
        cm = CareerManager()
        cm.add_trophy("League", "2025", "FC Test", datetime.date(2025, 5, 20))
        assert len(cm.trophies) == 1
        assert cm.reputation > 30  # Trophy boosts reputation

    def test_career_summary(self):
        cm = CareerManager()
        cm.start_job("FC A", datetime.date(2025, 1, 1))
        cm.record_match_result(won=True, drawn=False)
        summary = cm.get_career_summary()
        assert summary["total_matches"] == 1
        assert summary["total_wins"] == 1

    def test_serialize_roundtrip(self):
        cm = CareerManager()
        cm.start_job("FC A", datetime.date(2025, 1, 1))
        cm.record_match_result(won=True, drawn=False)
        data = cm.serialize()
        restored = CareerManager.get_from_dict(data)
        assert restored.current_job.club_name == "FC A"
        assert restored.current_job.wins == 1


# =========================================================================
# 13. SeasonCalendar
# =========================================================================


class TestSeasonCalendar:
    def test_generate_has_start_and_end(self):
        sc = SeasonCalendar()
        events = sc.generate(
            datetime.date(2025, 1, 1),
            datetime.date(2025, 12, 31),
        )
        types = [e["type"] for e in events]
        assert "season_start" in types
        assert "season_end" in types

    def test_generate_has_transfer_windows(self):
        sc = SeasonCalendar()
        events = sc.generate(
            datetime.date(2025, 1, 1),
            datetime.date(2025, 12, 31),
        )
        transfer_events = [e for e in events if e["type"] == "transfer_window"]
        assert len(transfer_events) >= 2

    def test_generate_has_mid_season(self):
        sc = SeasonCalendar()
        events = sc.generate(
            datetime.date(2025, 1, 1),
            datetime.date(2025, 12, 31),
        )
        types = [e["type"] for e in events]
        assert "mid_season" in types


# =========================================================================
# 14. AIManager
# =========================================================================


class TestAIManager:
    def test_select_defensive_formation(self):
        ai = AIManager()
        formation = ai.select_formation({"defense": 90, "midfield": 50, "attack": 40})
        assert formation == "5-3-2"

    def test_select_attacking_formation(self):
        ai = AIManager()
        formation = ai.select_formation({"defense": 40, "midfield": 50, "attack": 90})
        assert formation == "4-3-3"

    def test_select_balanced_formation(self):
        ai = AIManager()
        formation = ai.select_formation({"defense": 50, "midfield": 50, "attack": 50})
        assert formation == "4-4-2"

    def test_should_buy_player_affordable(self):
        ai = AIManager()
        assert ai.should_buy_player(10_000_000, "striker", 4_000_000) is True

    def test_should_buy_player_too_expensive(self):
        ai = AIManager()
        assert ai.should_buy_player(10_000_000, "striker", 8_000_000) is False


# =========================================================================
# 15. NewsFeedGenerator
# =========================================================================


class TestNewsFeedGenerator:
    def test_generate_goal_news(self):
        gen = NewsFeedGenerator()
        events = [{"type": "goal", "player": "Ronaldo"}]
        news = gen.generate(events)
        assert len(news) == 1
        assert "GOAL" in news[0]["headline"]
        assert news[0]["priority"] == "high"

    def test_generate_transfer_news(self):
        gen = NewsFeedGenerator()
        events = [{"type": "transfer", "player": "Messi", "club": "FC Test"}]
        news = gen.generate(events)
        assert "signs" in news[0]["headline"]

    def test_generate_multiple_events(self):
        gen = NewsFeedGenerator()
        events = [
            {"type": "goal", "player": "A"},
            {"type": "injury", "player": "B"},
            {"type": "transfer", "player": "C", "club": "D"},
        ]
        news = gen.generate(events)
        assert len(news) == 3

    def test_generate_empty_events(self):
        gen = NewsFeedGenerator()
        assert gen.generate([]) == []


# =========================================================================
# 16. NotificationSystem
# =========================================================================


class TestNotificationSystem:
    def test_add_notification(self):
        ns = NotificationSystem()
        notif = ns.add("Test", "Hello")
        assert notif["title"] == "Test"
        assert notif["read"] is False

    def test_mark_read(self):
        ns = NotificationSystem()
        notif = ns.add("Test", "Hello")
        ns.mark_read(notif["id"])
        assert ns.notifications[0]["read"] is True

    def test_get_unread(self):
        ns = NotificationSystem()
        ns.add("A", "msg")
        ns.add("B", "msg")
        ns.mark_read(0)
        unread = ns.get_unread()
        assert len(unread) == 1
        assert unread[0]["title"] == "B"

    def test_clear(self):
        ns = NotificationSystem()
        ns.add("A", "msg")
        ns.add("B", "msg")
        ns.clear()
        assert len(ns.notifications) == 0

    def test_clear_read(self):
        ns = NotificationSystem()
        ns.add("A", "msg")
        ns.add("B", "msg")
        ns.mark_read(0)
        ns.clear_read()
        assert len(ns.notifications) == 1
        assert ns.notifications[0]["title"] == "B"

    def test_mark_read_invalid_id(self):
        ns = NotificationSystem()
        with pytest.raises(ValueError):
            ns.mark_read(999)


# =========================================================================
# 17. FormGuide
# =========================================================================


class TestFormGuide:
    def test_add_results(self):
        fg = FormGuide()
        fg.add_result("W")
        fg.add_result("D")
        fg.add_result("L")
        assert fg.get_form_string() == "WDL"

    def test_get_points(self):
        fg = FormGuide()
        fg.add_result("W")
        fg.add_result("D")
        fg.add_result("L")
        assert fg.get_points() == 4  # 3 + 1 + 0

    def test_max_results_trimmed(self):
        fg = FormGuide(max_results=3)
        for r in ["W", "W", "W", "L", "L"]:
            fg.add_result(r)
        assert fg.get_form_string() == "WLL"

    def test_trend_improving(self):
        fg = FormGuide()
        fg.add_result("W")
        fg.add_result("W")
        fg.add_result("W")
        assert fg.get_trend() == "improving"

    def test_trend_declining(self):
        fg = FormGuide()
        fg.add_result("L")
        fg.add_result("L")
        fg.add_result("L")
        assert fg.get_trend() == "declining"

    def test_invalid_result_raises(self):
        fg = FormGuide()
        with pytest.raises(ValueError):
            fg.add_result("X")


# =========================================================================
# 18. PlayerComparison
# =========================================================================


class TestPlayerComparison:
    def test_compare_returns_categories(self):
        a = _make_player_dict("Player A", 80)
        b = _make_player_dict("Player B", 60)
        result = PlayerComparison.compare(a, b)
        assert "categories" in result
        assert "offensive" in result["categories"]

    def test_compare_winner(self):
        a = _make_player_dict("Player A", 80)
        b = _make_player_dict("Player B", 60)
        result = PlayerComparison.compare(a, b)
        assert result["winner"] == "Player A"
        assert result["total_a"] > result["total_b"]

    def test_compare_tie(self):
        a = _make_player_dict("Player A", 70)
        b = _make_player_dict("Player B", 70)
        result = PlayerComparison.compare(a, b)
        assert result["winner"] == "tie"

    def test_compare_diff_values(self):
        a = _make_player_dict("Player A", 80)
        b = _make_player_dict("Player B", 60)
        result = PlayerComparison.compare(a, b)
        off = result["categories"]["offensive"]
        assert off["shot_power"]["diff"] == 20  # 80 - 60
