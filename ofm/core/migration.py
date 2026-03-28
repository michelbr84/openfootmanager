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
Save file migration system for OpenFoot Manager.

When the game evolves between releases the save-file schema changes.
``SaveMigration`` applies a chain of versioned migration steps so that
older saves can be loaded by newer game versions.
"""
import copy
import logging
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass
class MigrationStep:
    """Describes a single schema migration between two consecutive versions."""

    from_version: str
    to_version: str
    description: str
    migration_func: Callable[[dict], dict]


# =========================================================================
# Built-in migration functions
# =========================================================================


def _migrate_0_1_to_0_2(save_data: dict) -> dict:
    """0.1.0 -> 0.2.0: add finances to clubs and career_data to top level."""
    data = copy.deepcopy(save_data)

    # Ensure every club in clubs_data has a finances dict
    for club in data.get("clubs_data", []):
        if "finances" not in club:
            club["finances"] = {"balance": 10_000_000.0}

    # Ensure top-level career_data exists
    if "career_data" not in data:
        data["career_data"] = {
            "trophies": [],
            "job_history": [],
            "national_team_job": None,
        }

    # Ensure finances_data exists at top level
    if "finances_data" not in data:
        data["finances_data"] = {"balance": 10_000_000.0}

    data["version"] = "0.2.0"
    return data


def _migrate_0_2_to_0_3(save_data: dict) -> dict:
    """0.2.0 -> 0.3.0: add competitions field and morale data."""
    data = copy.deepcopy(save_data)

    # Add competitions data
    if "competitions_data" not in data:
        data["competitions_data"] = {
            "cups": [],
            "continental": [],
            "international": [],
        }

    # Add morale data
    if "morale_data" not in data:
        data["morale_data"] = {"morale_map": {}}

    # Ensure league_data has a season field
    league = data.get("league_data", {})
    if "season_number" not in league:
        league["season_number"] = data.get("season", 1)
    data["league_data"] = league

    data["version"] = "0.3.0"
    return data


# =========================================================================
# SaveMigration
# =========================================================================


class SaveMigration:
    """Applies a chain of migrations to bring a save file up to date."""

    CURRENT_VERSION = "0.3.0"

    def __init__(self):
        self.migrations: list[MigrationStep] = [
            MigrationStep(
                from_version="0.1.0",
                to_version="0.2.0",
                description="Add finances to clubs and career_data",
                migration_func=_migrate_0_1_to_0_2,
            ),
            MigrationStep(
                from_version="0.2.0",
                to_version="0.3.0",
                description="Add competitions field and morale data",
                migration_func=_migrate_0_2_to_0_3,
            ),
        ]

    # ------------------------------------------------------------------
    # Version detection
    # ------------------------------------------------------------------

    @staticmethod
    def get_save_version(save_data: dict) -> str:
        """Return the version string stored in the save data.

        If no version field is present the save is assumed to be ``"0.1.0"``
        (the earliest supported format).
        """
        return save_data.get("version", "0.1.0")

    def needs_migration(self, save_data: dict) -> bool:
        """Return ``True`` if the save is older than ``CURRENT_VERSION``."""
        return self.get_save_version(save_data) != self.CURRENT_VERSION

    # ------------------------------------------------------------------
    # Migration
    # ------------------------------------------------------------------

    def migrate(self, save_data: dict) -> dict:
        """Apply all necessary migration steps in order.

        Returns a **new** dict (the original is not mutated).

        Raises
        ------
        ValueError
            If the save version is unrecognised or a migration chain
            cannot reach ``CURRENT_VERSION``.
        """
        data = copy.deepcopy(save_data)
        current = self.get_save_version(data)

        if current == self.CURRENT_VERSION:
            return data

        # Build an index: from_version -> MigrationStep
        step_map: dict[str, MigrationStep] = {
            step.from_version: step for step in self.migrations
        }

        visited: set[str] = set()
        while current != self.CURRENT_VERSION:
            if current in visited:
                raise ValueError(
                    f"Migration loop detected at version '{current}'."
                )
            visited.add(current)

            step = step_map.get(current)
            if step is None:
                raise ValueError(
                    f"No migration path from version '{current}' to "
                    f"'{self.CURRENT_VERSION}'. Available migrations start "
                    f"from: {sorted(step_map.keys())}"
                )

            logger.info(
                "Migrating save from %s to %s: %s",
                step.from_version,
                step.to_version,
                step.description,
            )
            data = step.migration_func(data)
            current = self.get_save_version(data)

        return data

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_save(self, save_data: dict) -> tuple[bool, str]:
        """Perform basic structural validation on a save dict.

        Returns ``(True, "OK")`` if the structure looks valid, or
        ``(False, reason)`` describing the first problem found.
        """
        if not isinstance(save_data, dict):
            return False, "Save data must be a dictionary."

        # Required top-level keys (present in all versions)
        required_keys = ["manager_name", "club_id", "season", "current_date"]
        for key in required_keys:
            if key not in save_data:
                return False, f"Missing required key: '{key}'."

        # Type checks
        if not isinstance(save_data.get("manager_name"), str):
            return False, "'manager_name' must be a string."

        if not isinstance(save_data.get("season"), int):
            return False, "'season' must be an integer."

        # Check that clubs_data is a list (if present)
        clubs = save_data.get("clubs_data")
        if clubs is not None and not isinstance(clubs, list):
            return False, "'clubs_data' must be a list."

        # Check that players_data is a list (if present)
        players = save_data.get("players_data")
        if players is not None and not isinstance(players, list):
            return False, "'players_data' must be a list."

        return True, "OK"
