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
import datetime
import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ofm.core.settings import Settings
from ofm.core.db.database import DB


@dataclass
class GameState:
    """Holds the entire serializable state of a game session."""

    manager_name: str
    club_id: int
    season: int
    current_date: datetime.date
    league_data: dict = field(default_factory=dict)
    clubs_data: list = field(default_factory=list)
    players_data: list = field(default_factory=list)
    squads_data: list = field(default_factory=list)
    finances_data: dict = field(default_factory=dict)
    career_data: dict = field(default_factory=dict)
    transfer_history: list = field(default_factory=list)
    training_history: list = field(default_factory=list)
    save_timestamp: str = ""

    def to_dict(self) -> dict:
        """Serialize the entire game state to a plain dictionary."""
        return {
            "manager_name": self.manager_name,
            "club_id": self.club_id,
            "season": self.season,
            "current_date": self.current_date.isoformat(),
            "league_data": self.league_data,
            "clubs_data": self.clubs_data,
            "players_data": self.players_data,
            "squads_data": self.squads_data,
            "finances_data": self.finances_data,
            "career_data": self.career_data,
            "transfer_history": self.transfer_history,
            "training_history": self.training_history,
            "save_timestamp": self.save_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        """Deserialize a dictionary into a GameState instance."""
        return cls(
            manager_name=data["manager_name"],
            club_id=data["club_id"],
            season=data["season"],
            current_date=datetime.date.fromisoformat(data["current_date"]),
            league_data=data.get("league_data", {}),
            clubs_data=data.get("clubs_data", []),
            players_data=data.get("players_data", []),
            squads_data=data.get("squads_data", []),
            finances_data=data.get("finances_data", {}),
            career_data=data.get("career_data", {}),
            transfer_history=data.get("transfer_history", []),
            training_history=data.get("training_history", []),
            save_timestamp=data.get("save_timestamp", ""),
        )


class SaveManager:
    """Handles reading and writing save files to disk."""

    def __init__(self, settings: Settings):
        self.save_dir: Path = settings.save

    def _ensure_save_dir(self):
        """Create the save directory if it does not exist."""
        os.makedirs(self.save_dir, exist_ok=True)

    def _save_path(self, slot_name: str) -> Path:
        """Return the full path for a given slot name."""
        return self.save_dir / f"{slot_name}.json"

    def save_game(self, game_state: GameState, slot_name: str = "autosave") -> Path:
        """
        Serialize a GameState to JSON and write it to the save directory.

        Parameters
        ----------
        game_state : GameState
            The game state to persist.
        slot_name : str
            Name of the save slot (becomes the filename without extension).

        Returns
        -------
        Path
            The path to the written save file.
        """
        self._ensure_save_dir()
        game_state.save_timestamp = datetime.datetime.now().isoformat()
        save_path = self._save_path(slot_name)
        with open(save_path, "w", encoding="utf-8") as fp:
            json.dump(game_state.to_dict(), fp, indent=2, ensure_ascii=False)
        return save_path

    def load_game(self, slot_name: str) -> GameState:
        """
        Read a JSON save file and deserialize it into a GameState.

        Parameters
        ----------
        slot_name : str
            Name of the save slot to load.

        Returns
        -------
        GameState
            The restored game state.

        Raises
        ------
        FileNotFoundError
            If the save file does not exist.
        """
        save_path = self._save_path(slot_name)
        if not save_path.exists():
            raise FileNotFoundError(f"Save file not found: {save_path}")
        with open(save_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        return GameState.from_dict(data)

    def list_saves(self) -> list[dict]:
        """
        Return metadata for every save file in the save directory.

        Returns
        -------
        list[dict]
            Each entry contains: name, date (save timestamp), manager, club_id.
        """
        self._ensure_save_dir()
        saves = []
        for entry in sorted(self.save_dir.iterdir()):
            if entry.suffix == ".json" and entry.is_file():
                try:
                    with open(entry, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                    saves.append({
                        "name": entry.stem,
                        "date": data.get("save_timestamp", ""),
                        "manager": data.get("manager_name", ""),
                        "club_id": data.get("club_id"),
                    })
                except (json.JSONDecodeError, KeyError):
                    # Skip corrupted save files
                    continue
        return saves

    def delete_save(self, slot_name: str) -> None:
        """
        Remove a save file from disk.

        Parameters
        ----------
        slot_name : str
            Name of the save slot to delete.

        Raises
        ------
        FileNotFoundError
            If the save file does not exist.
        """
        save_path = self._save_path(slot_name)
        if not save_path.exists():
            raise FileNotFoundError(f"Save file not found: {save_path}")
        os.remove(save_path)

    def autosave(self, game_state: GameState) -> Path:
        """Convenience wrapper that saves to the 'autosave' slot."""
        return self.save_game(game_state, "autosave")

    def has_saves(self) -> bool:
        """Return True if at least one save file exists."""
        if not self.save_dir.exists():
            return False
        return any(
            entry.suffix == ".json" and entry.is_file()
            for entry in self.save_dir.iterdir()
        )


class GameManager:
    """
    Top-level orchestrator for an OpenFoot Manager game session.

    Coordinates the database, save system, and day-to-day game progression.
    """

    def __init__(self, settings: Settings, db: DB):
        self.settings: Settings = settings
        self.db: DB = db
        self.save_manager: SaveManager = SaveManager(settings)
        self.game_state: Optional[GameState] = None
        self.is_game_active: bool = False

    # ------------------------------------------------------------------
    # New game
    # ------------------------------------------------------------------

    def new_game(self, manager_name: str, club_id: int) -> GameState:
        """
        Initialize a fresh game session.

        Loads clubs, players, and squads from the database, sets up the
        initial season state, and creates a new GameState.

        Parameters
        ----------
        manager_name : str
            The player-manager's name.
        club_id : int
            The UUID-int of the club the player will manage.

        Returns
        -------
        GameState
            The newly created game state.
        """
        # Make sure DB files exist
        self.db.check_clubs_file()

        clubs_data = self.db.load_clubs()
        players_data = self.db.load_players()
        squads_data = self.db.load_squads_file()

        # Locate the chosen club and seed its finances
        finances_data: dict = {}
        for club in clubs_data:
            if club["id"] == club_id:
                finances_data = club.get("finances", {"balance": 10_000_000.0})
                break

        # Build initial career data
        career_data: dict = {
            "trophies": [],
            "job_history": [],
            "national_team_job": None,
        }

        # Default season start date: January 1 of the current year
        start_date = datetime.date.today().replace(month=1, day=1)

        self.game_state = GameState(
            manager_name=manager_name,
            club_id=club_id,
            season=1,
            current_date=start_date,
            league_data={},
            clubs_data=clubs_data,
            players_data=players_data,
            squads_data=squads_data,
            finances_data=finances_data,
            career_data=career_data,
            transfer_history=[],
            training_history=[],
        )
        self.is_game_active = True
        return self.game_state

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------

    def save_game(self, slot_name: str = "autosave") -> Path:
        """
        Persist the current game state to disk.

        Parameters
        ----------
        slot_name : str
            Name of the save slot.

        Returns
        -------
        Path
            Path to the saved file.

        Raises
        ------
        RuntimeError
            If there is no active game state to save.
        """
        if self.game_state is None:
            raise RuntimeError("No active game state to save")
        return self.save_manager.save_game(self.game_state, slot_name)

    def load_game(self, slot_name: str) -> bool:
        """
        Load a game state from disk.

        Parameters
        ----------
        slot_name : str
            Name of the save slot to load.

        Returns
        -------
        bool
            True if the load succeeded, False otherwise.
        """
        try:
            self.game_state = self.save_manager.load_game(slot_name)
            self.is_game_active = True
            return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return False

    # ------------------------------------------------------------------
    # Day advancement
    # ------------------------------------------------------------------

    def advance_day(self) -> dict:
        """
        Advance the in-game date by one day and run daily checks.

        Returns
        -------
        dict
            A summary of events that occurred on this day, with keys:
            - ``date``: the new current date (ISO string)
            - ``match_day``: whether fixtures are scheduled
            - ``training_day``: whether it is a training day
            - ``transfer_window_changed``: whether the transfer window status changed
            - ``recovered_players``: list of player IDs that recovered from injury
            - ``expired_loans``: list of expired loan deal dicts
        """
        if self.game_state is None:
            raise RuntimeError("No active game state")

        self.game_state.current_date += datetime.timedelta(days=1)
        current = self.game_state.current_date
        events: dict = {
            "date": current.isoformat(),
            "match_day": False,
            "training_day": False,
            "transfer_window_changed": False,
            "recovered_players": [],
            "expired_loans": [],
        }

        # --- Match day check ---
        # If there is league data with rounds, check whether this date has fixtures
        league = self.game_state.league_data
        if league:
            current_round = league.get("current_round", 0)
            rounds = league.get("rounds", [])
            if current_round < len(rounds):
                # A simple heuristic: match days fall on weekends (Sat/Sun)
                if current.weekday() in (5, 6):
                    events["match_day"] = True

        # --- Training day check ---
        # Training can happen on non-match weekdays
        if current.weekday() < 5 and not events["match_day"]:
            events["training_day"] = True

        # --- Transfer window changes ---
        # Windows typically open Jan 1 and close Jan 31 (winter),
        # or open Jul 1 and close Aug 31 (summer).
        month_day = (current.month, current.day)
        window_boundaries = {
            (1, 1): "open",
            (2, 1): "closed",
            (7, 1): "open",
            (9, 1): "closed",
        }
        if month_day in window_boundaries:
            events["transfer_window_changed"] = True

        # --- Injury recovery checks ---
        # Scan players_data for any injury recovery markers
        for player in self.game_state.players_data:
            injury = player.get("injury")
            if injury and injury.get("date_injured") and injury.get("recovery_days"):
                date_injured = datetime.date.fromisoformat(injury["date_injured"])
                recovery_days = injury["recovery_days"]
                if (current - date_injured).days >= recovery_days:
                    events["recovered_players"].append(player.get("id"))
                    player["injury"] = None
                    player["is_injured"] = False

        # --- Loan expiration checks ---
        # Scan league_data or a top-level loans key for expired loans
        loans = self.game_state.league_data.get("loans", [])
        still_active = []
        for loan in loans:
            end_date = datetime.date.fromisoformat(loan["end_date"])
            if current >= end_date and loan.get("is_active", True):
                loan["is_active"] = False
                events["expired_loans"].append(loan)
            else:
                still_active.append(loan)
        if "loans" in self.game_state.league_data:
            self.game_state.league_data["loans"] = still_active + [
                l for l in loans if not l.get("is_active", True)
            ]

        return events

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    def get_current_date(self) -> datetime.date:
        """Return the current in-game date."""
        if self.game_state is None:
            raise RuntimeError("No active game state")
        return self.game_state.current_date

    def get_player_club(self) -> dict:
        """
        Return the club dict for the player's managed club.

        Returns
        -------
        dict
            The club dictionary from clubs_data whose ``id`` matches the
            game state's ``club_id``.

        Raises
        ------
        RuntimeError
            If there is no active game state.
        ValueError
            If the club cannot be found in clubs_data.
        """
        if self.game_state is None:
            raise RuntimeError("No active game state")
        for club in self.game_state.clubs_data:
            if club["id"] == self.game_state.club_id:
                return club
        raise ValueError(
            f"Club with id {self.game_state.club_id} not found in game state"
        )
