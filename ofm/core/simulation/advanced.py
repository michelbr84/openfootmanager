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
Advanced simulation systems for match and world simulation.

Provides weather, crowd, morale, relationships, career events,
financial fair play, and stadium management systems.
"""
import random
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum, IntEnum, auto
from itertools import combinations
from typing import Optional


# =============================================================================
# 1. WeatherSystem
# =============================================================================

class WeatherType(Enum):
    CLEAR = "Clear"
    CLOUDY = "Cloudy"
    RAINY = "Rainy"
    SNOWY = "Snowy"
    WINDY = "Windy"
    HOT = "Hot"


@dataclass
class Weather:
    type: WeatherType
    temperature: int
    wind_speed: int
    description: str


# Countries considered tropical for weather generation.
TROPICAL_COUNTRIES = {
    "Brazil", "Colombia", "Nigeria", "Ghana", "Cameroon", "Ivory Coast",
    "Senegal", "Mexico", "Ecuador", "Costa Rica", "Thailand", "Indonesia",
    "Malaysia", "India", "Egypt", "Saudi Arabia", "Qatar", "UAE",
    "Venezuela", "Peru", "Paraguay",
}

# Northern-hemisphere summer months and winter months.
_SUMMER_MONTHS = {6, 7, 8}
_WINTER_MONTHS = {11, 12, 1, 2}


class WeatherSystem:
    """Generates match-day weather and computes gameplay modifiers."""

    def generate_weather(self, month: int, country: str) -> Weather:
        """Return a randomised ``Weather`` appropriate for *month* and *country*."""
        is_tropical = country in TROPICAL_COUNTRIES
        is_summer = month in _SUMMER_MONTHS
        is_winter = month in _WINTER_MONTHS

        if is_tropical:
            weights = {
                WeatherType.CLEAR: 20,
                WeatherType.CLOUDY: 10,
                WeatherType.RAINY: 35,
                WeatherType.SNOWY: 0,
                WeatherType.WINDY: 5,
                WeatherType.HOT: 30,
            }
        elif is_summer:
            weights = {
                WeatherType.CLEAR: 35,
                WeatherType.CLOUDY: 20,
                WeatherType.RAINY: 10,
                WeatherType.SNOWY: 0,
                WeatherType.WINDY: 5,
                WeatherType.HOT: 30,
            }
        elif is_winter:
            weights = {
                WeatherType.CLEAR: 5,
                WeatherType.CLOUDY: 15,
                WeatherType.RAINY: 30,
                WeatherType.SNOWY: 25,
                WeatherType.WINDY: 20,
                WeatherType.HOT: 0,
            }
        else:
            # Spring / autumn – mild mix.
            weights = {
                WeatherType.CLEAR: 25,
                WeatherType.CLOUDY: 25,
                WeatherType.RAINY: 20,
                WeatherType.SNOWY: 5,
                WeatherType.WINDY: 15,
                WeatherType.HOT: 10,
            }

        # Filter out zero-weight entries before choosing.
        types = [t for t, w in weights.items() if w > 0]
        type_weights = [weights[t] for t in types]
        weather_type = random.choices(types, weights=type_weights, k=1)[0]

        temperature = self._random_temperature(weather_type, is_tropical, is_summer, is_winter)
        wind_speed = self._random_wind_speed(weather_type)
        description = self._describe(weather_type, temperature, wind_speed)

        return Weather(
            type=weather_type,
            temperature=temperature,
            wind_speed=wind_speed,
            description=description,
        )

    # ------------------------------------------------------------------
    # Gameplay modifiers
    # ------------------------------------------------------------------

    @staticmethod
    def get_gameplay_modifiers(weather: Weather) -> dict[str, float]:
        """Return a dict of modifier name to signed float value."""
        modifiers: dict[str, float] = {
            WeatherType.RAINY: {
                "passing_accuracy": -0.05,
                "dribble_success": -0.03,
                "injury_risk": 0.02,
            },
            WeatherType.SNOWY: {
                "passing_accuracy": -0.08,
                "shot_accuracy": -0.05,
                "speed": -0.1,
            },
            WeatherType.WINDY: {
                "crossing_accuracy": -0.1,
                "long_pass": -0.07,
            },
            WeatherType.HOT: {
                "stamina_drain": 0.15,
                "fatigue": 0.1,
            },
        }.get(weather.type, {})
        return modifiers

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _random_temperature(
        wtype: WeatherType, tropical: bool, summer: bool, winter: bool
    ) -> int:
        if wtype == WeatherType.HOT:
            return random.randint(30, 42)
        if wtype == WeatherType.SNOWY:
            return random.randint(-5, 2)
        if tropical:
            return random.randint(24, 36)
        if summer:
            return random.randint(18, 32)
        if winter:
            return random.randint(-3, 10)
        return random.randint(8, 22)

    @staticmethod
    def _random_wind_speed(wtype: WeatherType) -> int:
        if wtype == WeatherType.WINDY:
            return random.randint(30, 65)
        return random.randint(0, 25)

    @staticmethod
    def _describe(wtype: WeatherType, temp: int, wind: int) -> str:
        base = {
            WeatherType.CLEAR: "Clear skies",
            WeatherType.CLOUDY: "Overcast",
            WeatherType.RAINY: "Rain expected",
            WeatherType.SNOWY: "Snowfall",
            WeatherType.WINDY: "Strong winds",
            WeatherType.HOT: "Hot conditions",
        }[wtype]
        return f"{base}, {temp}°C, wind {wind} km/h"


# =============================================================================
# 2. CrowdSystem
# =============================================================================

class CrowdSystem:
    """Models attendance, home advantage, and crowd mood."""

    def calculate_attendance(
        self,
        home_club,
        away_club,
        match_importance: float = 1.0,
        weather: Optional[Weather] = None,
        is_weekday: bool = False,
    ) -> int:
        """Return estimated attendance as an integer.

        Parameters
        ----------
        home_club:
            Must expose ``stadium_capacity`` (int).
        away_club:
            Opponent club (used for derby detection via ``country``).
        match_importance:
            Multiplier – 1.0 normal, 1.5 cup final, etc.
        weather:
            Optional ``Weather`` instance; bad weather reduces attendance.
        is_weekday:
            Weekday matches draw fewer fans.
        """
        capacity: int = home_club.stadium_capacity
        base_ratio = random.uniform(0.50, 0.95)

        # Importance boost (derbies, cup finals, top-of-table).
        importance_factor = min(match_importance, 2.0)
        base_ratio *= importance_factor

        # Same-country rival boost (simple derby heuristic).
        if home_club.country == away_club.country:
            base_ratio += random.uniform(0.0, 0.05)

        # Bad weather penalty.
        if weather is not None and weather.type in (
            WeatherType.RAINY,
            WeatherType.SNOWY,
            WeatherType.WINDY,
        ):
            base_ratio -= random.uniform(0.05, 0.15)

        # Weekday penalty.
        if is_weekday:
            base_ratio -= random.uniform(0.05, 0.10)

        base_ratio = max(0.15, min(base_ratio, 1.0))
        return int(capacity * base_ratio)

    @staticmethod
    def get_home_advantage(attendance: int, capacity: int) -> float:
        """Return home advantage factor in [0.0, 0.15]."""
        if capacity <= 0:
            return 0.0
        ratio = min(attendance / capacity, 1.0)
        return round(ratio * 0.15, 4)

    @staticmethod
    def get_crowd_mood(home_score: int, away_score: int, minute: int) -> str:
        """Return a mood string based on the current match state."""
        diff = home_score - away_score
        if diff >= 2:
            return "ecstatic"
        if diff == 1:
            return "excited" if minute > 70 else "excited"
        if diff == 0:
            return "tense" if minute > 60 else "quiet"
        if diff == -1:
            return "frustrated" if minute > 45 else "tense"
        # diff <= -2
        return "frustrated"


# =============================================================================
# 3. PlayerMorale
# =============================================================================

class MoraleLevel(IntEnum):
    VERY_LOW = 1
    LOW = 2
    NEUTRAL = 3
    HIGH = 4
    VERY_HIGH = 5


class PlayerMorale:
    """Tracks and updates morale for every player by id."""

    def __init__(self, morale_map: Optional[dict[int, MoraleLevel]] = None):
        self.morale_map: dict[int, MoraleLevel] = morale_map or {}

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------

    def update_after_match(
        self, player_id: int, played: bool, won: bool, rating: float
    ) -> None:
        """Adjust morale after a match result.

        * Playing and winning boosts morale.
        * High match rating (>= 7.5) boosts further.
        * Not playing or losing lowers morale.
        """
        current = self._ensure(player_id)
        delta = 0
        if played:
            delta += 1 if won else -1
            if rating >= 7.5:
                delta += 1
            elif rating < 5.5:
                delta -= 1
        else:
            # Unused – slight morale dip.
            delta -= 1

        self._apply_delta(player_id, current, delta)

    def update_from_talk(self, player_id: int, talk_effect: int) -> None:
        """Apply effect from a manager–player interaction.

        ``talk_effect`` is an integer (positive = encouraging, negative = bad talk).
        """
        current = self._ensure(player_id)
        self._apply_delta(player_id, current, talk_effect)

    def update_from_playing_time(
        self, player_id: int, minutes_this_month: int, expected_minutes: int
    ) -> None:
        """Lower morale if the player is being benched below expectations."""
        current = self._ensure(player_id)
        if expected_minutes <= 0:
            return
        ratio = minutes_this_month / expected_minutes
        if ratio < 0.3:
            self._apply_delta(player_id, current, -2)
        elif ratio < 0.6:
            self._apply_delta(player_id, current, -1)
        elif ratio > 1.0:
            self._apply_delta(player_id, current, 1)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_performance_modifier(self, player_id: int) -> float:
        """Return a modifier in [-0.1, +0.1] based on morale."""
        level = self.get_morale(player_id)
        mapping = {
            MoraleLevel.VERY_LOW: -0.10,
            MoraleLevel.LOW: -0.05,
            MoraleLevel.NEUTRAL: 0.0,
            MoraleLevel.HIGH: 0.05,
            MoraleLevel.VERY_HIGH: 0.10,
        }
        return mapping[level]

    def get_morale(self, player_id: int) -> MoraleLevel:
        return self.morale_map.get(player_id, MoraleLevel.NEUTRAL)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def serialize(self) -> dict:
        return {"morale_map": {str(k): v.value for k, v in self.morale_map.items()}}

    @classmethod
    def get_from_dict(cls, data: dict) -> "PlayerMorale":
        morale_map = {
            int(k): MoraleLevel(v)
            for k, v in data.get("morale_map", {}).items()
        }
        return cls(morale_map=morale_map)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _ensure(self, player_id: int) -> MoraleLevel:
        if player_id not in self.morale_map:
            self.morale_map[player_id] = MoraleLevel.NEUTRAL
        return self.morale_map[player_id]

    def _apply_delta(self, player_id: int, current: MoraleLevel, delta: int) -> None:
        new_value = max(MoraleLevel.VERY_LOW, min(current.value + delta, MoraleLevel.VERY_HIGH))
        self.morale_map[player_id] = MoraleLevel(new_value)


# =============================================================================
# 4. PlayerRelationships
# =============================================================================

class RelationshipType(Enum):
    NEUTRAL = "Neutral"
    FRIENDS = "Friends"
    RIVALS = "Rivals"
    MENTOR_PROTEGE = "Mentor-Protege"


class PlayerRelationships:
    """Tracks pairwise relationships between players and computes chemistry."""

    def __init__(
        self,
        relationships: Optional[dict[tuple[int, int], RelationshipType]] = None,
    ):
        self.relationships: dict[tuple[int, int], RelationshipType] = relationships or {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_relationship(
        self, p1: int, p2: int, rel_type: RelationshipType
    ) -> None:
        key = self._key(p1, p2)
        self.relationships[key] = rel_type

    def generate_initial_relationships(self, squad: list) -> None:
        """Auto-generate relationships for a squad.

        Players sharing the same nationality have a chance of becoming friends.
        A large age gap may create a mentor-protege bond.
        Each ``player`` in *squad* must expose ``player_id`` (int-like),
        ``nationality`` (str), and ``dob`` (date/datetime).
        """
        for i, p1 in enumerate(squad):
            for p2 in squad[i + 1:]:
                pid1 = int(p1.player_id) if hasattr(p1.player_id, "int") else p1.player_id
                pid2 = int(p2.player_id) if hasattr(p2.player_id, "int") else p2.player_id

                # Same nationality → chance of friendship.
                if getattr(p1, "nationality", None) == getattr(p2, "nationality", None):
                    if random.random() < 0.35:
                        self.add_relationship(pid1, pid2, RelationshipType.FRIENDS)
                        continue

                # Large age gap → possible mentor-protege.
                dob1 = getattr(p1, "dob", None)
                dob2 = getattr(p2, "dob", None)
                if dob1 is not None and dob2 is not None:
                    age_diff = abs((dob1 - dob2).days) / 365.25
                    if age_diff >= 8 and random.random() < 0.20:
                        self.add_relationship(pid1, pid2, RelationshipType.MENTOR_PROTEGE)
                        continue

                # Small chance of rivalry.
                if random.random() < 0.05:
                    self.add_relationship(pid1, pid2, RelationshipType.RIVALS)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_chemistry_bonus(self, p1: int, p2: int) -> float:
        """Return chemistry bonus for a pair of players."""
        key = self._key(p1, p2)
        rel = self.relationships.get(key, RelationshipType.NEUTRAL)
        return {
            RelationshipType.NEUTRAL: 0.0,
            RelationshipType.FRIENDS: 0.05,
            RelationshipType.RIVALS: -0.03,
            RelationshipType.MENTOR_PROTEGE: 0.08,
        }[rel]

    def get_team_chemistry(self, squad_ids: list[int]) -> float:
        """Return the average pair chemistry bonus for the given squad."""
        if len(squad_ids) < 2:
            return 0.0
        total = 0.0
        count = 0
        for p1, p2 in combinations(squad_ids, 2):
            total += self.get_chemistry_bonus(p1, p2)
            count += 1
        return round(total / count, 6) if count else 0.0

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def serialize(self) -> dict:
        entries = []
        for (p1, p2), rel in self.relationships.items():
            entries.append({"p1": p1, "p2": p2, "type": rel.value})
        return {"relationships": entries}

    @classmethod
    def get_from_dict(cls, data: dict) -> "PlayerRelationships":
        rels: dict[tuple[int, int], RelationshipType] = {}
        for entry in data.get("relationships", []):
            key = (entry["p1"], entry["p2"])
            rels[key] = RelationshipType(entry["type"])
        return cls(relationships=rels)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _key(p1: int, p2: int) -> tuple[int, int]:
        """Canonical key so (a, b) and (b, a) map to the same pair."""
        return (min(p1, p2), max(p1, p2))


# =============================================================================
# 5. PlayerCareerEvents
# =============================================================================

@dataclass
class AgentDemand:
    player_id: int
    demand_type: str  # "wage_increase", "transfer_request", "more_playing_time"
    urgency: int  # 1 (low) to 5 (critical)


@dataclass
class PlayerAward:
    name: str
    season: str
    player_id: int
    value: str


class PlayerCareerEvents:
    """Handles retirement checks, agent demands, and season awards."""

    # ------------------------------------------------------------------
    # Retirement
    # ------------------------------------------------------------------

    @staticmethod
    def check_retirement(player_dict: dict, current_date: date) -> bool:
        """Return ``True`` if the player should retire.

        The player dict must contain ``dob`` (ISO str or date) and
        ``overall`` (int, 0-100).  Players older than 34 with declining
        attributes face an increasing chance of retirement.
        """
        dob = player_dict.get("dob")
        if dob is None:
            return False
        if isinstance(dob, str):
            dob = date.fromisoformat(dob)
        elif isinstance(dob, datetime):
            dob = dob.date()

        age = (current_date - dob).days / 365.25
        if age <= 34:
            return False

        overall = player_dict.get("overall", 70)
        # Base retirement chance rises sharply with age and falling ability.
        base_chance = 0.05 * (age - 34)
        if overall < 60:
            base_chance += 0.15
        elif overall < 70:
            base_chance += 0.05

        return random.random() < min(base_chance, 0.90)

    # ------------------------------------------------------------------
    # Agent demands
    # ------------------------------------------------------------------

    @staticmethod
    def generate_agent_demands(
        player_dict: dict,
        morale: MoraleLevel,
        contract: dict,
    ) -> Optional[AgentDemand]:
        """Possibly generate an agent demand based on morale/contract state.

        ``contract`` should contain ``wage`` (float) and optionally
        ``years_remaining`` (int).
        """
        player_id = player_dict.get("id", 0)
        years_remaining = contract.get("years_remaining", 2)
        wage = contract.get("wage", 0.0)

        # Unhappy player with expiring contract → transfer request.
        if morale.value <= MoraleLevel.LOW.value and years_remaining <= 1:
            return AgentDemand(
                player_id=player_id,
                demand_type="transfer_request",
                urgency=min(5, 4 + (MoraleLevel.LOW.value - morale.value)),
            )

        # Low morale → more playing time demand.
        if morale.value <= MoraleLevel.LOW.value:
            return AgentDemand(
                player_id=player_id,
                demand_type="more_playing_time",
                urgency=3,
            )

        # Good player on low wage → wage increase.
        overall = player_dict.get("overall", 70)
        if overall >= 78 and wage < overall * 500:
            return AgentDemand(
                player_id=player_id,
                demand_type="wage_increase",
                urgency=2,
            )

        return None

    # ------------------------------------------------------------------
    # Awards
    # ------------------------------------------------------------------

    @staticmethod
    def award_golden_boot(players_stats: list[dict]) -> Optional[PlayerAward]:
        """Return the Golden Boot for the top scorer.

        Each entry in *players_stats* should have ``player_id``, ``goals``,
        and ``season``.
        """
        if not players_stats:
            return None
        top = max(players_stats, key=lambda p: p.get("goals", 0))
        if top.get("goals", 0) == 0:
            return None
        return PlayerAward(
            name="Golden Boot",
            season=top.get("season", ""),
            player_id=top["player_id"],
            value=f"{top['goals']} goals",
        )

    @staticmethod
    def award_league_mvp(players_stats: list[dict]) -> Optional[PlayerAward]:
        """Return League MVP – highest average rating."""
        if not players_stats:
            return None
        top = max(players_stats, key=lambda p: p.get("avg_rating", 0.0))
        if top.get("avg_rating", 0.0) == 0.0:
            return None
        return PlayerAward(
            name="League MVP",
            season=top.get("season", ""),
            player_id=top["player_id"],
            value=f"{top['avg_rating']:.2f} avg rating",
        )

    @staticmethod
    def award_best_young_player(
        players: list[dict], current_date: date
    ) -> Optional[PlayerAward]:
        """Return Best Young Player – best U21 by overall rating.

        Each dict needs ``player_id``, ``dob`` (ISO str or date),
        ``overall``, and ``season``.
        """
        young: list[dict] = []
        for p in players:
            dob = p.get("dob")
            if dob is None:
                continue
            if isinstance(dob, str):
                dob = date.fromisoformat(dob)
            elif isinstance(dob, datetime):
                dob = dob.date()
            age = (current_date - dob).days / 365.25
            if age < 21:
                young.append(p)

        if not young:
            return None
        best = max(young, key=lambda p: p.get("overall", 0))
        return PlayerAward(
            name="Best Young Player",
            season=best.get("season", ""),
            player_id=best["player_id"],
            value=f"Overall {best.get('overall', 0)}",
        )

    def generate_all_season_awards(
        self,
        players_stats: list[dict],
        players: list[dict],
        current_date: date,
    ) -> list[PlayerAward]:
        """Return all end-of-season awards that can be determined."""
        awards: list[PlayerAward] = []
        gb = self.award_golden_boot(players_stats)
        if gb is not None:
            awards.append(gb)
        mvp = self.award_league_mvp(players_stats)
        if mvp is not None:
            awards.append(mvp)
        byp = self.award_best_young_player(players, current_date)
        if byp is not None:
            awards.append(byp)
        return awards

    # ------------------------------------------------------------------
    # Testimonial
    # ------------------------------------------------------------------

    @staticmethod
    def check_testimonial(player_dict: dict, club_years: int) -> bool:
        """Return ``True`` if the player qualifies for a testimonial match."""
        return club_years >= 10

    # ------------------------------------------------------------------
    # Serialisation (stateless – included for interface consistency)
    # ------------------------------------------------------------------

    def serialize(self) -> dict:
        return {}

    @classmethod
    def get_from_dict(cls, data: dict) -> "PlayerCareerEvents":
        return cls()


# =============================================================================
# 6. FinancialFairPlay
# =============================================================================

class FFPChecker:
    """Financial Fair Play compliance checks."""

    # Maximum overspend allowed over a 3-season window.
    _OVERSPEND_LIMIT: float = 10_000_000.0
    # Maximum wage-to-revenue ratio.
    _WAGE_RATIO_LIMIT: float = 0.70

    def check_compliance(
        self, club_finances: dict, seasons_data: list[dict]
    ) -> tuple[bool, str]:
        """Check FFP compliance over the last 3 seasons.

        ``club_finances`` is informational.  ``seasons_data`` is a list of
        dicts each containing ``revenue`` and ``spending`` floats.

        Returns (is_compliant, message).
        """
        if not seasons_data:
            return True, "No season data to evaluate."

        # Use last 3 seasons (or fewer if not available).
        recent = seasons_data[-3:]
        total_revenue = sum(s.get("revenue", 0.0) for s in recent)
        total_spending = sum(s.get("spending", 0.0) for s in recent)
        overspend = total_spending - total_revenue

        if overspend > self._OVERSPEND_LIMIT:
            return (
                False,
                f"FFP violation: overspend of {overspend:,.0f} exceeds "
                f"the {self._OVERSPEND_LIMIT:,.0f} limit over {len(recent)} season(s).",
            )
        return True, "Club is FFP compliant."

    def get_transfer_cap(self, club_finances: dict) -> float:
        """Return the maximum transfer spending allowed this window.

        A simple heuristic: 60 % of current balance plus any declared
        transfer budget.
        """
        balance = club_finances.get("balance", 0.0)
        budget = club_finances.get("transfer_budget", 0.0)
        return max(0.0, balance * 0.6 + budget)

    def check_wage_ratio(self, wages: float, revenue: float) -> bool:
        """Return ``True`` if the wage-to-revenue ratio is healthy."""
        if revenue <= 0:
            return wages == 0
        return (wages / revenue) < self._WAGE_RATIO_LIMIT

    @staticmethod
    def apply_sanctions(club, violation_level: int) -> dict:
        """Return a dict describing sanctions for the given *violation_level*.

        Levels: 1 = warning, 2 = fine, 3 = transfer ban, 4+ = points deduction.

        The caller is responsible for actually applying the sanctions to the
        club object; this method only describes them.
        """
        sanctions: dict = {"violation_level": violation_level}

        if violation_level <= 0:
            sanctions["action"] = "none"
            return sanctions

        if violation_level == 1:
            sanctions["action"] = "warning"
            sanctions["description"] = "Official FFP warning issued."
        elif violation_level == 2:
            sanctions["action"] = "fine"
            sanctions["fine_amount"] = 5_000_000.0
            sanctions["description"] = "Financial fine of 5,000,000."
        elif violation_level == 3:
            sanctions["action"] = "transfer_ban"
            sanctions["ban_windows"] = 1
            sanctions["description"] = "Transfer ban for 1 window."
        else:
            sanctions["action"] = "points_deduction"
            sanctions["points"] = min(violation_level * 3, 15)
            sanctions["description"] = (
                f"Points deduction of {sanctions['points']} and transfer restrictions."
            )
            sanctions["transfer_ban"] = True
            sanctions["ban_windows"] = 2

        return sanctions


# =============================================================================
# 7. StadiumManager
# =============================================================================

@dataclass
class StadiumUpgrade:
    name: str
    cost: float
    capacity_increase: int
    duration_weeks: int


# Pre-defined catalogue of available upgrades.
UPGRADES: list[StadiumUpgrade] = [
    StadiumUpgrade("New Stand", 15_000_000, 5_000, 26),
    StadiumUpgrade("Expand East Wing", 8_000_000, 2_500, 16),
    StadiumUpgrade("Expand West Wing", 8_000_000, 2_500, 16),
    StadiumUpgrade("Executive Boxes", 12_000_000, 1_000, 20),
    StadiumUpgrade("Corner Infill", 4_000_000, 1_500, 10),
    StadiumUpgrade("Second Tier", 25_000_000, 10_000, 40),
    StadiumUpgrade("Roof Installation", 6_000_000, 0, 12),
    StadiumUpgrade("Pitch Renovation", 2_000_000, 0, 4),
]


class StadiumManager:
    """Manages stadium capacity and ongoing upgrade projects."""

    def __init__(
        self,
        current_capacity: int = 20_000,
        upgrades_in_progress: Optional[list[dict]] = None,
    ):
        self.current_capacity = current_capacity
        self.upgrades_in_progress: list[dict] = upgrades_in_progress or []

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def start_upgrade(self, upgrade: StadiumUpgrade, finances) -> bool:
        """Begin an upgrade if the club can afford it.

        ``finances`` must expose ``balance`` (float) and
        ``add_expense(amount, description)`` or act as a ``FinanceManager``.
        Returns ``True`` on success, ``False`` if insufficient funds.
        """
        if finances.balance < upgrade.cost:
            return False

        finances.add_expense(upgrade.cost, f"Stadium upgrade: {upgrade.name}")
        start_date = datetime.now()
        completion_date = start_date + timedelta(weeks=upgrade.duration_weeks)
        self.upgrades_in_progress.append({
            "name": upgrade.name,
            "capacity_increase": upgrade.capacity_increase,
            "start_date": start_date.isoformat(),
            "completion_date": completion_date.isoformat(),
        })
        return True

    def check_completion(self, current_date: date) -> list[dict]:
        """Check for completed upgrades and apply capacity increases.

        Returns a list of upgrade dicts that were completed this check.
        """
        if isinstance(current_date, datetime):
            current_date = current_date.date()

        completed: list[dict] = []
        still_in_progress: list[dict] = []

        for upgrade in self.upgrades_in_progress:
            comp_date = date.fromisoformat(upgrade["completion_date"][:10])
            if current_date >= comp_date:
                self.current_capacity += upgrade["capacity_increase"]
                completed.append(upgrade)
            else:
                still_in_progress.append(upgrade)

        self.upgrades_in_progress = still_in_progress
        return completed

    def get_available_upgrades(self, current_capacity: Optional[int] = None) -> list[StadiumUpgrade]:
        """Return upgrades from the catalogue applicable at the given capacity."""
        cap = current_capacity if current_capacity is not None else self.current_capacity
        available: list[StadiumUpgrade] = []
        for u in UPGRADES:
            # Second Tier only available for larger stadiums.
            if u.name == "Second Tier" and cap < 20_000:
                continue
            # Don't offer upgrades already in progress.
            in_progress_names = {up["name"] for up in self.upgrades_in_progress}
            if u.name in in_progress_names:
                continue
            available.append(u)
        return available

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def serialize(self) -> dict:
        return {
            "current_capacity": self.current_capacity,
            "upgrades_in_progress": self.upgrades_in_progress,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "StadiumManager":
        return cls(
            current_capacity=data.get("current_capacity", 20_000),
            upgrades_in_progress=data.get("upgrades_in_progress", []),
        )
