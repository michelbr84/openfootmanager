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
Tests for Stats Explorer pure logic functions.

These functions mirror the controller logic for calculating player stats,
tested without any tkinter dependency so they run in headless CI.
"""
import datetime
from statistics import mean

import pytest


# ---------------------------------------------------------------------------
# Pure helper functions (extracted logic that the controller would use)
# ---------------------------------------------------------------------------

def _attr_avg(attrs: dict) -> float:
    """Average of all values in an attribute group dict."""
    values = list(attrs.values())
    return mean(values) if values else 0.0


def calculate_overall(player: dict, position: int) -> float:
    """
    Calculate weighted overall for a player at a given position.

    Position codes (from Positions IntEnum with auto()):
        1 = GK, 2 = DF, 3 = MF, 4 = FW

    Formulae (each sub-overall is the mean of that attribute group):
        FW:  (def*1 + phys*1 + int*2 + off*3) / 7
        MF:  (def*1 + phys*2 + int*3 + off*1) / 7
        DF:  (def*3 + phys*2 + int*1 + off*1) / 7
        GK:  (gk*3  + def*2  + phys*1 + int*1) / 7
    """
    attrs = player["attributes"]
    off = _attr_avg(attrs["offensive"])
    phys = _attr_avg(attrs["physical"])
    defs = _attr_avg(attrs["defensive"])
    intel = _attr_avg(attrs["intelligence"])
    gk = _attr_avg(attrs["gk"])

    if position == 4:  # FW
        return (defs * 1 + phys * 1 + intel * 2 + off * 3) / 7
    elif position == 3:  # MF
        return (defs * 1 + phys * 2 + intel * 3 + off * 1) / 7
    elif position == 2:  # DF
        return (defs * 3 + phys * 2 + intel * 1 + off * 1) / 7
    elif position == 1:  # GK
        return (gk * 3 + defs * 2 + phys * 1 + intel * 1) / 7
    else:
        raise ValueError(f"Unknown position code: {position}")


def get_position_name(position_code: int) -> str:
    """Map position integer code to a human-readable abbreviation."""
    mapping = {1: "GK", 2: "DF", 3: "MF", 4: "FW"}
    return mapping.get(position_code, "Unknown")


def calculate_age(dob_str: str, reference_date: datetime.date | None = None) -> int:
    """Calculate age in whole years from a 'YYYY-MM-DD' date-of-birth string."""
    dob = datetime.date.fromisoformat(dob_str)
    today = reference_date or datetime.date.today()
    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age


def sort_players(
    players: list[dict],
    key: str,
    descending: bool = True,
    position_for_overall: int | None = None,
) -> list[dict]:
    """
    Sort a list of player dicts by *key*.

    Supported keys: "overall", "age", "fitness", "value".
    For "overall" the caller must supply *position_for_overall*.
    """
    if key == "overall":
        if position_for_overall is None:
            raise ValueError("position_for_overall is required when sorting by overall")
        return sorted(
            players,
            key=lambda p: calculate_overall(p, position_for_overall),
            reverse=descending,
        )
    elif key == "age":
        return sorted(
            players,
            key=lambda p: calculate_age(p["dob"]),
            reverse=descending,
        )
    elif key == "fitness":
        return sorted(players, key=lambda p: p["fitness"], reverse=descending)
    elif key == "value":
        return sorted(players, key=lambda p: p["value"], reverse=descending)
    else:
        raise ValueError(f"Unsupported sort key: {key}")


def filter_by_position(players: list[dict], position_code: int) -> list[dict]:
    """Return only those players whose positions list contains *position_code*."""
    return [p for p in players if position_code in p["positions"]]


def calculate_team_stats(players: list[dict]) -> dict:
    """
    Aggregate team-level statistics from a list of player dicts.

    Returns dict with keys:
        avg_overall  - average overall (using each player's first position)
        avg_age      - average age
        total_value  - sum of player values
        position_counts - dict mapping position name to count
    """
    if not players:
        return {
            "avg_overall": 0.0,
            "avg_age": 0.0,
            "total_value": 0.0,
            "position_counts": {},
        }

    overalls = [
        calculate_overall(p, p["positions"][0]) for p in players
    ]
    ages = [calculate_age(p["dob"]) for p in players]

    position_counts: dict[str, int] = {}
    for p in players:
        for pos in p["positions"]:
            name = get_position_name(pos)
            position_counts[name] = position_counts.get(name, 0) + 1

    return {
        "avg_overall": mean(overalls),
        "avg_age": mean(ages),
        "total_value": sum(p["value"] for p in players),
        "position_counts": position_counts,
    }


# ---------------------------------------------------------------------------
# Test data fixtures
# ---------------------------------------------------------------------------

def _make_player(
    player_id: int = 1,
    dob: str = "1996-12-14",
    positions: list[int] | None = None,
    fitness: float = 85.0,
    value: float = 50_000_000.0,
    off_attrs: dict | None = None,
    phys_attrs: dict | None = None,
    def_attrs: dict | None = None,
    int_attrs: dict | None = None,
    gk_attrs: dict | None = None,
) -> dict:
    """Factory for player dicts with sensible defaults."""
    return {
        "id": player_id,
        "nationality": "Brazil",
        "dob": dob,
        "first_name": "John",
        "last_name": "Doe",
        "short_name": "J. Doe",
        "positions": positions or [4],
        "fitness": fitness,
        "stamina": 90.0,
        "form": 0.7,
        "attributes": {
            "offensive": off_attrs or {
                "shot_power": 85, "shot_accuracy": 80,
                "free_kick": 75, "penalty": 88, "positioning": 90,
            },
            "physical": phys_attrs or {
                "strength": 80, "aggression": 75, "endurance": 40,
            },
            "defensive": def_attrs or {
                "tackling": 54, "interception": 65, "positioning": 50,
            },
            "intelligence": int_attrs or {
                "vision": 60, "passing": 88, "crossing": 82,
                "ball_control": 87, "dribbling": 80, "skills": 83, "team_work": 75,
            },
            "gk": gk_attrs or {
                "reflexes": 20, "jumping": 20, "positioning": 10, "penalty": 10,
            },
        },
        "potential_skill": 90,
        "international_reputation": 5,
        "preferred_foot": 1,
        "value": value,
        "injury_type": 0,
    }


@pytest.fixture
def fw_player():
    return _make_player(player_id=1, positions=[4], dob="1996-12-14")


@pytest.fixture
def mf_player():
    return _make_player(player_id=2, positions=[3], dob="1994-06-20", value=40_000_000.0)


@pytest.fixture
def df_player():
    return _make_player(
        player_id=3,
        positions=[2],
        dob="1992-03-10",
        value=30_000_000.0,
        def_attrs={"tackling": 85, "interception": 80, "positioning": 78},
        phys_attrs={"strength": 88, "aggression": 82, "endurance": 75},
    )


@pytest.fixture
def gk_player():
    return _make_player(
        player_id=4,
        positions=[1],
        dob="1990-01-05",
        fitness=92.0,
        value=20_000_000.0,
        gk_attrs={"reflexes": 88, "jumping": 85, "positioning": 90, "penalty": 80},
        def_attrs={"tackling": 60, "interception": 55, "positioning": 65},
    )


@pytest.fixture
def sample_squad(fw_player, mf_player, df_player, gk_player):
    return [fw_player, mf_player, df_player, gk_player]


# ---------------------------------------------------------------------------
# Tests: Overall calculation
# ---------------------------------------------------------------------------

class TestCalculateOverall:
    def test_fw_overall(self, fw_player):
        """FW formula: (def*1 + phys*1 + int*2 + off*3) / 7"""
        attrs = fw_player["attributes"]
        off = mean(attrs["offensive"].values())
        phys = mean(attrs["physical"].values())
        defs = mean(attrs["defensive"].values())
        intel = mean(attrs["intelligence"].values())

        expected = (defs * 1 + phys * 1 + intel * 2 + off * 3) / 7
        result = calculate_overall(fw_player, 4)
        assert result == pytest.approx(expected)

    def test_mf_overall(self, mf_player):
        """MF formula: (def*1 + phys*2 + int*3 + off*1) / 7"""
        attrs = mf_player["attributes"]
        off = mean(attrs["offensive"].values())
        phys = mean(attrs["physical"].values())
        defs = mean(attrs["defensive"].values())
        intel = mean(attrs["intelligence"].values())

        expected = (defs * 1 + phys * 2 + intel * 3 + off * 1) / 7
        result = calculate_overall(mf_player, 3)
        assert result == pytest.approx(expected)

    def test_df_overall(self, df_player):
        """DF formula: (def*3 + phys*2 + int*1 + off*1) / 7"""
        attrs = df_player["attributes"]
        off = mean(attrs["offensive"].values())
        phys = mean(attrs["physical"].values())
        defs = mean(attrs["defensive"].values())
        intel = mean(attrs["intelligence"].values())

        expected = (defs * 3 + phys * 2 + intel * 1 + off * 1) / 7
        result = calculate_overall(df_player, 2)
        assert result == pytest.approx(expected)

    def test_gk_overall(self, gk_player):
        """GK formula: (gk*3 + def*2 + phys*1 + int*1) / 7"""
        attrs = gk_player["attributes"]
        phys = mean(attrs["physical"].values())
        defs = mean(attrs["defensive"].values())
        intel = mean(attrs["intelligence"].values())
        gk = mean(attrs["gk"].values())

        expected = (gk * 3 + defs * 2 + phys * 1 + intel * 1) / 7
        result = calculate_overall(gk_player, 1)
        assert result == pytest.approx(expected)

    def test_fw_overall_values(self):
        """Verify a concrete numeric result for FW overall."""
        player = _make_player(
            off_attrs={"a": 80, "b": 80, "c": 80, "d": 80, "e": 80},  # avg 80
            phys_attrs={"a": 70, "b": 70, "c": 70},                    # avg 70
            def_attrs={"a": 50, "b": 50, "c": 50},                      # avg 50
            int_attrs={"a": 60, "b": 60, "c": 60, "d": 60, "e": 60, "f": 60, "g": 60},  # avg 60
        )
        # FW: (50*1 + 70*1 + 60*2 + 80*3) / 7 = (50+70+120+240)/7 = 480/7
        expected = 480 / 7
        assert calculate_overall(player, 4) == pytest.approx(expected)

    def test_unknown_position_raises(self, fw_player):
        with pytest.raises(ValueError, match="Unknown position code"):
            calculate_overall(fw_player, 99)


# ---------------------------------------------------------------------------
# Tests: Position name mapping
# ---------------------------------------------------------------------------

class TestGetPositionName:
    @pytest.mark.parametrize("code, expected", [
        (1, "GK"),
        (2, "DF"),
        (3, "MF"),
        (4, "FW"),
    ])
    def test_known_positions(self, code, expected):
        assert get_position_name(code) == expected

    def test_unknown_position(self):
        assert get_position_name(0) == "Unknown"
        assert get_position_name(99) == "Unknown"


# ---------------------------------------------------------------------------
# Tests: Age calculation
# ---------------------------------------------------------------------------

class TestCalculateAge:
    def test_age_birthday_passed(self):
        # Reference date is after birthday in the year
        age = calculate_age("2000-01-15", reference_date=datetime.date(2026, 3, 28))
        assert age == 26

    def test_age_birthday_not_yet(self):
        # Reference date is before birthday in the year
        age = calculate_age("2000-06-15", reference_date=datetime.date(2026, 3, 28))
        assert age == 25

    def test_age_on_birthday(self):
        age = calculate_age("2000-03-28", reference_date=datetime.date(2026, 3, 28))
        assert age == 26

    def test_age_newborn(self):
        age = calculate_age("2026-03-28", reference_date=datetime.date(2026, 3, 28))
        assert age == 0

    def test_age_leap_year_dob(self):
        # Born Feb 29 - on March 1 they should be considered to have had their birthday
        age = calculate_age("2000-02-29", reference_date=datetime.date(2026, 3, 1))
        assert age == 26


# ---------------------------------------------------------------------------
# Tests: Sorting players
# ---------------------------------------------------------------------------

class TestSortPlayers:
    def test_sort_by_value_descending(self, sample_squad):
        result = sort_players(sample_squad, "value", descending=True)
        values = [p["value"] for p in result]
        assert values == sorted(values, reverse=True)

    def test_sort_by_value_ascending(self, sample_squad):
        result = sort_players(sample_squad, "value", descending=False)
        values = [p["value"] for p in result]
        assert values == sorted(values)

    def test_sort_by_fitness_descending(self, sample_squad):
        result = sort_players(sample_squad, "fitness", descending=True)
        fitnesses = [p["fitness"] for p in result]
        assert fitnesses == sorted(fitnesses, reverse=True)

    def test_sort_by_age_descending(self, sample_squad):
        result = sort_players(sample_squad, "age", descending=True)
        ages = [calculate_age(p["dob"]) for p in result]
        assert ages == sorted(ages, reverse=True)

    def test_sort_by_overall_requires_position(self, sample_squad):
        with pytest.raises(ValueError, match="position_for_overall is required"):
            sort_players(sample_squad, "overall")

    def test_sort_by_overall_fw(self, sample_squad):
        result = sort_players(sample_squad, "overall", descending=True, position_for_overall=4)
        overalls = [calculate_overall(p, 4) for p in result]
        assert overalls == sorted(overalls, reverse=True)

    def test_sort_invalid_key(self, sample_squad):
        with pytest.raises(ValueError, match="Unsupported sort key"):
            sort_players(sample_squad, "hair_color")


# ---------------------------------------------------------------------------
# Tests: Position filtering
# ---------------------------------------------------------------------------

class TestFilterByPosition:
    def test_filter_fw(self, sample_squad):
        result = filter_by_position(sample_squad, 4)
        assert len(result) == 1
        assert result[0]["positions"] == [4]

    def test_filter_gk(self, sample_squad):
        result = filter_by_position(sample_squad, 1)
        assert len(result) == 1
        assert result[0]["id"] == 4  # gk_player has id=4

    def test_filter_no_match(self, sample_squad):
        # No player has position code 99
        result = filter_by_position(sample_squad, 99)
        assert result == []

    def test_filter_multi_position_player(self):
        """A player with multiple positions should appear in filters for each."""
        player = _make_player(positions=[3, 4])
        squad = [player]
        assert len(filter_by_position(squad, 3)) == 1
        assert len(filter_by_position(squad, 4)) == 1
        assert len(filter_by_position(squad, 2)) == 0


# ---------------------------------------------------------------------------
# Tests: Team stats
# ---------------------------------------------------------------------------

class TestCalculateTeamStats:
    def test_empty_squad(self):
        stats = calculate_team_stats([])
        assert stats["avg_overall"] == 0.0
        assert stats["avg_age"] == 0.0
        assert stats["total_value"] == 0.0
        assert stats["position_counts"] == {}

    def test_total_value(self, sample_squad):
        stats = calculate_team_stats(sample_squad)
        expected_total = sum(p["value"] for p in sample_squad)
        assert stats["total_value"] == pytest.approx(expected_total)

    def test_position_counts(self, sample_squad):
        stats = calculate_team_stats(sample_squad)
        counts = stats["position_counts"]
        assert counts["FW"] == 1
        assert counts["MF"] == 1
        assert counts["DF"] == 1
        assert counts["GK"] == 1

    def test_position_counts_multi_position(self):
        players = [
            _make_player(player_id=1, positions=[3, 4]),
            _make_player(player_id=2, positions=[3]),
        ]
        stats = calculate_team_stats(players)
        assert stats["position_counts"]["MF"] == 2
        assert stats["position_counts"]["FW"] == 1

    def test_avg_age(self, sample_squad):
        stats = calculate_team_stats(sample_squad)
        expected_ages = [calculate_age(p["dob"]) for p in sample_squad]
        assert stats["avg_age"] == pytest.approx(mean(expected_ages))

    def test_avg_overall(self, sample_squad):
        stats = calculate_team_stats(sample_squad)
        expected_overalls = [
            calculate_overall(p, p["positions"][0]) for p in sample_squad
        ]
        assert stats["avg_overall"] == pytest.approx(mean(expected_overalls))
