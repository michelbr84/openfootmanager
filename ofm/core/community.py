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
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HotSeatMultiplayer
# ---------------------------------------------------------------------------


class HotSeatMultiplayer:
    """Manages local hot-seat multiplayer where multiple human players take
    turns on the same machine."""

    def __init__(self, player_names: list[str], club_ids: list[int]):
        if len(player_names) != len(club_ids):
            raise ValueError("player_names and club_ids must have the same length.")
        if len(player_names) < 2:
            raise ValueError("Hot-seat multiplayer requires at least 2 players.")

        self.players: list[dict] = []
        for i, (name, club_id) in enumerate(zip(player_names, club_ids)):
            self.players.append(
                {
                    "name": name,
                    "club_id": club_id,
                    "is_current_turn": i == 0,
                }
            )

        self.current_player_index: int = 0
        self.turn_order: list[int] = list(range(len(player_names)))

    def advance_turn(self) -> None:
        """Moves to the next player in the turn order."""
        self.players[self.current_player_index]["is_current_turn"] = False
        self.current_player_index += 1
        if self.current_player_index < len(self.turn_order):
            actual_index = self.turn_order[self.current_player_index]
            self.players[actual_index]["is_current_turn"] = True

    def get_current_player(self) -> dict:
        """Returns the dict of the player whose turn it currently is."""
        if self.current_player_index >= len(self.turn_order):
            return self.players[self.turn_order[-1]]
        actual_index = self.turn_order[self.current_player_index]
        return self.players[actual_index]

    def is_all_turns_done(self) -> bool:
        """Returns True if every player has had their turn this round."""
        return self.current_player_index >= len(self.turn_order)

    def reset_round(self) -> None:
        """Starts a new round of turns."""
        self.current_player_index = 0
        for player in self.players:
            player["is_current_turn"] = False
        actual_index = self.turn_order[0]
        self.players[actual_index]["is_current_turn"] = True

    def serialize(self) -> dict:
        return {
            "players": self.players,
            "current_player_index": self.current_player_index,
            "turn_order": self.turn_order,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "HotSeatMultiplayer":
        players = data["players"]
        names = [p["name"] for p in players]
        club_ids = [p["club_id"] for p in players]
        obj = cls(names, club_ids)
        obj.players = players
        obj.current_player_index = data.get("current_player_index", 0)
        obj.turn_order = data.get("turn_order", list(range(len(players))))
        return obj


# ---------------------------------------------------------------------------
# NetworkMultiplayer (stub/framework for future implementation)
# ---------------------------------------------------------------------------


class MultiplayerState(Enum):
    DISCONNECTED = "disconnected"
    LOBBY = "lobby"
    IN_GAME = "in_game"
    PAUSED = "paused"


class NetworkMultiplayer:
    """Framework stub for future network multiplayer support.

    All network operations are placeholders that log their intent and return
    sensible defaults so the rest of the codebase can reference this API
    without crashing.
    """

    def __init__(self):
        self.state: MultiplayerState = MultiplayerState.DISCONNECTED
        self.host: str = ""
        self.port: int = 0
        self.players: list[dict] = []

    def create_lobby(self, host: str, port: int) -> dict:
        """Creates a multiplayer lobby. Returns lobby info dict."""
        logger.info("NetworkMultiplayer.create_lobby: stub called (host=%s, port=%d)", host, port)
        self.host = host
        self.port = port
        self.state = MultiplayerState.LOBBY
        return {
            "host": self.host,
            "port": self.port,
            "state": self.state.value,
            "players": self.players,
        }

    def join_lobby(self, host: str, port: int, player_name: str) -> bool:
        """Joins an existing lobby. Returns True on success."""
        logger.info(
            "NetworkMultiplayer.join_lobby: stub called (host=%s, port=%d, player=%s)",
            host,
            port,
            player_name,
        )
        self.host = host
        self.port = port
        self.state = MultiplayerState.LOBBY
        self.players.append({"name": player_name, "ready": False})
        return True

    def start_game(self) -> bool:
        """Transitions the lobby to in-game state. Returns True on success."""
        if self.state != MultiplayerState.LOBBY:
            logger.warning("Cannot start game: not in LOBBY state (current=%s)", self.state.value)
            return False
        self.state = MultiplayerState.IN_GAME
        logger.info("NetworkMultiplayer.start_game: stub — game started.")
        return True

    def send_action(self, action_dict: dict) -> None:
        """Sends a game action over the network. Placeholder."""
        logger.info("NetworkMultiplayer.send_action: stub — action=%s", action_dict)

    def receive_actions(self) -> list[dict]:
        """Receives pending game actions from the network. Placeholder."""
        logger.info("NetworkMultiplayer.receive_actions: stub — returning empty list.")
        return []

    def serialize(self) -> dict:
        return {
            "state": self.state.value,
            "host": self.host,
            "port": self.port,
            "players": self.players,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "NetworkMultiplayer":
        obj = cls()
        obj.state = MultiplayerState(data.get("state", "disconnected"))
        obj.host = data.get("host", "")
        obj.port = data.get("port", 0)
        obj.players = data.get("players", [])
        return obj


# ---------------------------------------------------------------------------
# LeagueCommissioner
# ---------------------------------------------------------------------------


class LeagueCommissioner:
    """Allows a human commissioner to manage a custom league with enforced
    rules (salary caps, transfer limits, etc.)."""

    DEFAULT_RULES: dict = {
        "max_transfers_per_window": 5,
        "salary_cap": 1_000_000,
        "min_squad_size": 18,
        "max_squad_size": 30,
        "allow_loan_deals": True,
    }

    def __init__(self, commissioner_name: str, league_name: str, rules: Optional[dict] = None):
        self.commissioner_name: str = commissioner_name
        self.league_name: str = league_name
        self.rules: dict = {**self.DEFAULT_RULES, **(rules or {})}
        self.players: list[dict] = []

    def register_player(self, name: str, club_id: int) -> bool:
        """Registers a human player into the commissioner league.

        Returns False if a player with the same name is already registered.
        """
        if any(p["name"] == name for p in self.players):
            logger.warning("Player '%s' is already registered.", name)
            return False
        self.players.append({"name": name, "club_id": club_id})
        return True

    def validate_transfer(
        self, buyer: str, seller: str, player: str, amount: float
    ) -> tuple[bool, str]:
        """Validates a transfer against the league rules.

        Returns (True, "OK") when valid, or (False, reason) otherwise.
        """
        salary_cap = self.rules.get("salary_cap", float("inf"))
        if amount > salary_cap:
            return False, f"Transfer amount {amount} exceeds salary cap {salary_cap}."

        max_transfers = self.rules.get("max_transfers_per_window", float("inf"))
        # NOTE: Actual per-player transfer counting would require career state
        # integration. For now we only validate amount-based rules.
        if max_transfers <= 0:
            return False, "No transfers allowed by league rules."

        return True, "OK"

    def get_league_rules(self) -> dict:
        """Returns a copy of the current rule set."""
        return dict(self.rules)

    def modify_rule(self, key: str, value) -> None:
        """Commissioner power: changes a single rule value."""
        self.rules[key] = value
        logger.info("Commissioner '%s' changed rule '%s' to %s.", self.commissioner_name, key, value)

    def serialize(self) -> dict:
        return {
            "commissioner_name": self.commissioner_name,
            "league_name": self.league_name,
            "rules": self.rules,
            "players": self.players,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "LeagueCommissioner":
        obj = cls(
            commissioner_name=data["commissioner_name"],
            league_name=data["league_name"],
            rules=data.get("rules"),
        )
        obj.players = data.get("players", [])
        return obj


# ---------------------------------------------------------------------------
# ChallengeMode
# ---------------------------------------------------------------------------


@dataclass
class Challenge:
    name: str
    description: str
    starting_conditions: dict
    win_conditions: dict
    difficulty: str

    def serialize(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "starting_conditions": self.starting_conditions,
            "win_conditions": self.win_conditions,
            "difficulty": self.difficulty,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "Challenge":
        return cls(
            name=data["name"],
            description=data["description"],
            starting_conditions=data.get("starting_conditions", {}),
            win_conditions=data.get("win_conditions", {}),
            difficulty=data.get("difficulty", "normal"),
        )


CHALLENGES: list[Challenge] = [
    Challenge(
        name="Rags to Riches",
        description="Start with the worst team and win the league in 5 seasons.",
        starting_conditions={"club_rank": "last"},
        win_conditions={"league_position": 1, "max_seasons": 5},
        difficulty="hard",
    ),
    Challenge(
        name="Youth Revolution",
        description="Win the league using only U23 players.",
        starting_conditions={},
        win_conditions={"league_position": 1, "max_avg_age": 23},
        difficulty="hard",
    ),
    Challenge(
        name="No Money, No Problem",
        description="Win the league without buying any players.",
        starting_conditions={"transfer_budget": 0},
        win_conditions={"league_position": 1},
        difficulty="hard",
    ),
    Challenge(
        name="The Great Escape",
        description="Save a team from relegation after joining mid-season.",
        starting_conditions={"club_rank": "last", "season_progress": 0.5},
        win_conditions={"league_position": ">relegation_zone"},
        difficulty="medium",
    ),
    Challenge(
        name="Dynasty",
        description="Win 3 consecutive league titles.",
        starting_conditions={},
        win_conditions={"consecutive_titles": 3},
        difficulty="very_hard",
    ),
    Challenge(
        name="Invincibles",
        description="Go unbeaten for an entire season.",
        starting_conditions={},
        win_conditions={"losses": 0},
        difficulty="legendary",
    ),
]


class ChallengeMode:
    """Manages predefined and custom challenge scenarios."""

    def __init__(self, challenges: Optional[list[Challenge]] = None):
        self.challenges: list[Challenge] = list(challenges or CHALLENGES)

    @staticmethod
    def check_win_condition(challenge: Challenge, career_state: dict) -> tuple[bool, str]:
        """Evaluates whether the win conditions for *challenge* are met based
        on the supplied *career_state* dict.

        Returns (True, congratulations_message) or (False, progress_message).
        """
        wc = challenge.win_conditions

        # --- league_position ---
        if "league_position" in wc:
            current_pos = career_state.get("league_position")
            target = wc["league_position"]

            if isinstance(target, str) and target.startswith(">"):
                # e.g. ">relegation_zone" — player must finish above relegation
                relegation_line = career_state.get("relegation_zone", 18)
                if current_pos is None or current_pos >= relegation_line:
                    return False, f"Currently in relegation zone (position {current_pos})."
            elif current_pos != target:
                return False, f"League position is {current_pos}, target is {target}."

        # --- max_seasons ---
        if "max_seasons" in wc:
            seasons_played = career_state.get("seasons_played", 0)
            if seasons_played > wc["max_seasons"]:
                return False, f"Exceeded maximum seasons ({wc['max_seasons']})."

        # --- max_avg_age ---
        if "max_avg_age" in wc:
            avg_age = career_state.get("squad_avg_age", 30)
            if avg_age > wc["max_avg_age"]:
                return False, f"Squad average age {avg_age} exceeds limit {wc['max_avg_age']}."

        # --- consecutive_titles ---
        if "consecutive_titles" in wc:
            titles = career_state.get("consecutive_titles", 0)
            if titles < wc["consecutive_titles"]:
                return False, f"Consecutive titles: {titles}/{wc['consecutive_titles']}."

        # --- losses ---
        if "losses" in wc:
            losses = career_state.get("season_losses", 0)
            if losses > wc["losses"]:
                return False, f"Season losses: {losses} (target: {wc['losses']})."

        return True, f"Challenge '{challenge.name}' completed!"

    def get_available_challenges(self) -> list[Challenge]:
        """Returns all available challenges."""
        return list(self.challenges)

    def serialize(self) -> dict:
        return {
            "challenges": [c.serialize() for c in self.challenges],
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "ChallengeMode":
        challenges = [Challenge.get_from_dict(c) for c in data.get("challenges", [])]
        return cls(challenges=challenges if challenges else None)


# ---------------------------------------------------------------------------
# HistoricalScenario
# ---------------------------------------------------------------------------


@dataclass
class Scenario:
    name: str
    year: int
    description: str
    league_setup: dict
    special_rules: dict

    def serialize(self) -> dict:
        return {
            "name": self.name,
            "year": self.year,
            "description": self.description,
            "league_setup": self.league_setup,
            "special_rules": self.special_rules,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "Scenario":
        return cls(
            name=data["name"],
            year=data["year"],
            description=data["description"],
            league_setup=data.get("league_setup", {}),
            special_rules=data.get("special_rules", {}),
        )


SCENARIOS: list[Scenario] = [
    Scenario(
        name="The Miracle of Istanbul 2005",
        year=2005,
        description=(
            "Recreate the legendary Champions League final comeback. "
            "Take control of a mid-table team trailing 3-0 at half-time and "
            "turn the match around."
        ),
        league_setup={
            "league": "Champions League",
            "stage": "final",
            "opponent_strength": "elite",
            "starting_score": {"home": 0, "away": 3},
        },
        special_rules={
            "half": 2,
            "morale_boost": True,
        },
    ),
    Scenario(
        name="Leicester 2016",
        year=2016,
        description=(
            "Take a 5000-1 outsider to the league title. Your squad is modest, "
            "your budget tiny, but team spirit is sky-high."
        ),
        league_setup={
            "league": "Premier League",
            "club_rank": "last",
            "budget_multiplier": 0.1,
            "team_spirit": 100,
        },
        special_rules={
            "transfer_ban": False,
            "underdog_bonus": True,
        },
    ),
    Scenario(
        name="Ajax Youth Revolution",
        year=2019,
        description=(
            "Build a team entirely from academy graduates and challenge "
            "for European glory."
        ),
        league_setup={
            "league": "Eredivisie",
            "academy_quality": "world_class",
            "squad_source": "academy_only",
        },
        special_rules={
            "no_transfers_in": True,
            "youth_development_boost": 2.0,
        },
    ),
]


class HistoricalScenario:
    """Manages historical scenario setups for special game modes."""

    def __init__(self, scenarios: Optional[list[Scenario]] = None):
        self.scenarios: list[Scenario] = list(scenarios or SCENARIOS)

    def setup_scenario(self, scenario: Scenario, settings: dict, db) -> dict:
        """Modifies *db* to match the historical scenario setup.

        *settings* is a user-provided dict that can override parts of the
        scenario (e.g. difficulty adjustments).

        Returns a summary dict describing what was configured.
        """
        setup_summary: dict = {
            "scenario_name": scenario.name,
            "year": scenario.year,
            "applied_league_setup": {},
            "applied_special_rules": {},
        }

        # Merge user settings with scenario defaults
        league_setup = {**scenario.league_setup, **settings.get("league_setup", {})}
        special_rules = {**scenario.special_rules, **settings.get("special_rules", {})}

        setup_summary["applied_league_setup"] = league_setup
        setup_summary["applied_special_rules"] = special_rules

        logger.info(
            "HistoricalScenario.setup_scenario: configured '%s' (%d) with league_setup=%s, special_rules=%s",
            scenario.name,
            scenario.year,
            league_setup,
            special_rules,
        )

        return setup_summary

    def serialize(self) -> dict:
        return {
            "scenarios": [s.serialize() for s in self.scenarios],
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "HistoricalScenario":
        scenarios = [Scenario.get_from_dict(s) for s in data.get("scenarios", [])]
        return cls(scenarios=scenarios if scenarios else None)
