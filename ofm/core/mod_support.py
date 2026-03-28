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
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mod template — the canonical structure a modder should ship in mod.json.
# ---------------------------------------------------------------------------

MOD_TEMPLATE: dict = {
    "name": "My Custom Mod",
    "version": "1.0.0",
    "author": "Author Name",
    "description": "Description of the mod",
    "type": "database",
    "data": {
        "clubs": [],
        "players": [],
    },
}

# Valid values for the "type" field inside a mod.json.
_VALID_MOD_TYPE_STRINGS = {"database", "roster", "tactics", "graphics", "custom"}


# ---------------------------------------------------------------------------
# ModType enum
# ---------------------------------------------------------------------------


class ModType(Enum):
    DATABASE = "database"
    ROSTER = "roster"
    TACTICS = "tactics"
    GRAPHICS = "graphics"
    CUSTOM = "custom"

    @classmethod
    def from_string(cls, value: str) -> "ModType":
        """Converts a lowercase type string (e.g. from mod.json) to an enum member."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(
                f"Unknown mod type '{value}'. Valid types: {[t.value for t in cls]}"
            )


# ---------------------------------------------------------------------------
# ModInfo dataclass
# ---------------------------------------------------------------------------


@dataclass
class ModInfo:
    name: str
    version: str
    author: str
    description: str
    mod_type: ModType
    path: Path

    def serialize(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "mod_type": self.mod_type.value,
            "path": str(self.path),
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "ModInfo":
        return cls(
            name=data["name"],
            version=data.get("version", "0.0.0"),
            author=data.get("author", "Unknown"),
            description=data.get("description", ""),
            mod_type=ModType.from_string(data.get("mod_type", data.get("type", "custom"))),
            path=Path(data.get("path", "")),
        )


# ---------------------------------------------------------------------------
# ModLoader — discovers, validates, loads, and applies mods
# ---------------------------------------------------------------------------


class ModLoaderError(Exception):
    pass


class ModLoader:
    """Scans a directory for mod packages, validates them, and applies their
    data to the running game database or roster.

    Each mod is a directory that contains a ``mod.json`` file at its root.
    """

    def __init__(self, mods_dir: Optional[Path] = None):
        if mods_dir is None:
            mods_dir = Path("ofm") / "mods"
        self.mods_dir: Path = mods_dir
        self.loaded_mods: list[ModInfo] = []

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover_mods(self) -> list[ModInfo]:
        """Scans ``self.mods_dir`` for sub-directories containing a ``mod.json``.

        Returns a list of ``ModInfo`` instances for every valid mod found.
        Invalid mod.json files are logged and skipped.
        """
        discovered: list[ModInfo] = []

        if not self.mods_dir.exists():
            logger.warning("Mods directory does not exist: %s", self.mods_dir)
            return discovered

        for child in sorted(self.mods_dir.iterdir()):
            mod_file = child / "mod.json" if child.is_dir() else None
            if mod_file is None or not mod_file.exists():
                continue

            try:
                with open(mod_file, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                mod_type_str = data.get("type", "custom")
                info = ModInfo(
                    name=data.get("name", child.name),
                    version=data.get("version", "0.0.0"),
                    author=data.get("author", "Unknown"),
                    description=data.get("description", ""),
                    mod_type=ModType.from_string(mod_type_str),
                    path=child,
                )
                discovered.append(info)
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                logger.warning("Skipping invalid mod at %s: %s", child, exc)

        return discovered

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_mod(self, mod_info: ModInfo) -> dict:
        """Reads and returns the full mod data dict from ``mod.json``.

        Also appends the mod to ``self.loaded_mods`` if not already present.
        """
        mod_file = mod_info.path / "mod.json"
        if not mod_file.exists():
            raise ModLoaderError(f"mod.json not found at {mod_file}")

        with open(mod_file, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        # Track loaded mods (avoid duplicates by path)
        if not any(m.path == mod_info.path for m in self.loaded_mods):
            self.loaded_mods.append(mod_info)

        return data

    # ------------------------------------------------------------------
    # Applying mods
    # ------------------------------------------------------------------

    def apply_database_mod(self, mod_data: dict, db) -> None:
        """Overlays custom club and player data from *mod_data* onto *db*.

        *db* is expected to be an instance of ``ofm.core.db.database.DB`` (or
        any object exposing ``clubs_file``, ``players_file``, and
        ``squads_file`` paths).

        The mod data dict should have a ``"data"`` key containing optional
        ``"clubs"`` and ``"players"`` lists that follow the same serialization
        format used by the core database.
        """
        payload = mod_data.get("data", {})

        mod_clubs: list[dict] = payload.get("clubs", [])
        mod_players: list[dict] = payload.get("players", [])

        if not mod_clubs and not mod_players:
            logger.info("Database mod contains no club or player overrides.")
            return

        # --- Merge players ---
        if mod_players and db.players_file.exists():
            try:
                with open(db.players_file, "r", encoding="utf-8") as fp:
                    existing_players: list[dict] = json.load(fp)
            except (json.JSONDecodeError, FileNotFoundError):
                existing_players = []

            # Index existing players by id for fast lookup
            player_index = {p["id"]: p for p in existing_players}
            for mp in mod_players:
                player_index[mp["id"]] = mp  # overwrite or add
            merged_players = list(player_index.values())

            with open(db.players_file, "w", encoding="utf-8") as fp:
                json.dump(merged_players, fp)
            logger.info("Applied %d player overrides from mod.", len(mod_players))

        # --- Merge clubs ---
        if mod_clubs and db.clubs_file.exists():
            try:
                with open(db.clubs_file, "r", encoding="utf-8") as fp:
                    existing_clubs: list[dict] = json.load(fp)
            except (json.JSONDecodeError, FileNotFoundError):
                existing_clubs = []

            club_index = {c["id"]: c for c in existing_clubs}
            for mc in mod_clubs:
                club_index[mc["id"]] = mc
            merged_clubs = list(club_index.values())

            with open(db.clubs_file, "w", encoding="utf-8") as fp:
                json.dump(merged_clubs, fp)
            logger.info("Applied %d club overrides from mod.", len(mod_clubs))

    def apply_roster_mod(self, mod_data: dict) -> dict:
        """Applies a custom roster mod and returns the roster dict.

        The mod data should contain a ``"data"`` key with roster information
        following the ``RosterManager.serialize()`` schema.

        Returns the roster data dict so the caller can feed it into
        ``RosterManager.get_from_dict()``.
        """
        payload = mod_data.get("data", {})
        roster_data = payload.get("roster", payload)

        if not roster_data:
            raise ModLoaderError("Roster mod contains no roster data.")

        logger.info("Loaded roster mod: formation=%s", roster_data.get("formation_str"))
        return roster_data

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_mod(mod_data: dict) -> tuple[bool, str]:
        """Checks that *mod_data* has a valid mod structure.

        Returns ``(True, "OK")`` when valid, or ``(False, reason)`` otherwise.
        """
        if not isinstance(mod_data, dict):
            return False, "Mod data must be a dict."

        # Required top-level keys
        for key in ("name", "version", "type"):
            if key not in mod_data:
                return False, f"Missing required key: '{key}'."

        # Type must be recognised
        mod_type = mod_data["type"]
        if mod_type not in _VALID_MOD_TYPE_STRINGS:
            return (
                False,
                f"Invalid mod type '{mod_type}'. Must be one of {sorted(_VALID_MOD_TYPE_STRINGS)}.",
            )

        # "data" key must be present and be a dict
        data = mod_data.get("data")
        if data is not None and not isinstance(data, dict):
            return False, "'data' must be a dict if present."

        # Type-specific checks
        if mod_type == "database" and data is not None:
            clubs = data.get("clubs")
            players = data.get("players")
            if clubs is not None and not isinstance(clubs, list):
                return False, "'data.clubs' must be a list."
            if players is not None and not isinstance(players, list):
                return False, "'data.players' must be a list."

        return True, "OK"

    # ------------------------------------------------------------------
    # Template helper
    # ------------------------------------------------------------------

    @staticmethod
    def get_mod_template() -> dict:
        """Returns a deep copy of the canonical mod.json template for modders."""
        import copy

        return copy.deepcopy(MOD_TEMPLATE)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def serialize(self) -> dict:
        """Serializes the loader state (loaded mods list) for persistence."""
        return {
            "mods_dir": str(self.mods_dir),
            "loaded_mods": [mod.serialize() for mod in self.loaded_mods],
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "ModLoader":
        """Restores a ``ModLoader`` from serialized data."""
        loader = cls(mods_dir=Path(data.get("mods_dir", "ofm/mods")))
        for mod_dict in data.get("loaded_mods", []):
            loader.loaded_mods.append(ModInfo.get_from_dict(mod_dict))
        return loader
