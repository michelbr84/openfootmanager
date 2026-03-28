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
import csv
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DatabaseImportExport
# ---------------------------------------------------------------------------


class DatabaseImportExport:
    """Handles importing and exporting game data to/from CSV and JSON formats
    for modding and data-sharing purposes."""

    @staticmethod
    def export_to_csv(players: list[dict], output_path: Path) -> None:
        """Exports a list of player dicts to a CSV file.

        The CSV columns are derived from the keys of the first player dict.
        Nested dicts are serialized as JSON strings.
        """
        if not players:
            logger.warning("export_to_csv: empty player list, nothing to export.")
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Flatten: nested dicts become JSON strings for CSV compatibility.
        fieldnames = list(players[0].keys())

        with open(output_path, "w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for player in players:
                row = {}
                for key in fieldnames:
                    value = player.get(key)
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value)
                    else:
                        row[key] = value
                writer.writerow(row)

        logger.info("Exported %d players to %s", len(players), output_path)

    @staticmethod
    def export_to_json(data: dict, output_path: Path) -> None:
        """Exports a full database dict to a JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
        logger.info("Exported database to %s", output_path)

    @staticmethod
    def import_from_csv(csv_path: Path) -> list[dict]:
        """Imports player data from a CSV file.

        Values that look like JSON objects or arrays are automatically parsed
        back into Python dicts/lists.
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        players: list[dict] = []
        with open(csv_path, "r", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                parsed_row: dict = {}
                for key, value in row.items():
                    if value and isinstance(value, str):
                        stripped = value.strip()
                        if (stripped.startswith("{") and stripped.endswith("}")) or (
                            stripped.startswith("[") and stripped.endswith("]")
                        ):
                            try:
                                parsed_row[key] = json.loads(stripped)
                                continue
                            except json.JSONDecodeError:
                                pass
                    parsed_row[key] = value
                players.append(parsed_row)

        logger.info("Imported %d players from %s", len(players), csv_path)
        return players

    @staticmethod
    def import_from_json(json_path: Path) -> dict:
        """Imports a full database dict from a JSON file."""
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        logger.info("Imported database from %s", json_path)
        return data

    @staticmethod
    def validate_import(data) -> tuple[bool, list[str]]:
        """Checks data integrity of imported data.

        Returns (True, []) when valid, or (False, [list of issues]) otherwise.
        """
        issues: list[str] = []

        if isinstance(data, list):
            # Validate a player list
            for i, entry in enumerate(data):
                if not isinstance(entry, dict):
                    issues.append(f"Entry at index {i} is not a dict.")
                    continue
                if "id" not in entry:
                    issues.append(f"Entry at index {i} is missing 'id' field.")
        elif isinstance(data, dict):
            # Validate a full DB export
            if "players" in data and not isinstance(data["players"], list):
                issues.append("'players' field must be a list.")
            if "clubs" in data and not isinstance(data["clubs"], list):
                issues.append("'clubs' field must be a list.")
        else:
            issues.append(f"Unexpected data type: {type(data).__name__}. Expected dict or list.")

        return (len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# FormationCreator
# ---------------------------------------------------------------------------


class FormationCreator:
    """Creates and persists custom formation definitions."""

    @staticmethod
    def create_custom_formation(name: str, defenders: int, midfielders: int, forwards: int) -> str:
        """Validates and returns a formation string like '3-5-2'.

        The total outfield players must equal 10 (goalkeeper is implicit).
        """
        total = defenders + midfielders + forwards
        if total != 10:
            raise ValueError(
                f"Formation '{name}' has {total} outfield players (must be exactly 10)."
            )
        if defenders < 1:
            raise ValueError("Formation must have at least 1 defender.")
        if midfielders < 1:
            raise ValueError("Formation must have at least 1 midfielder.")
        if forwards < 1:
            raise ValueError("Formation must have at least 1 forward.")

        formation_str = f"{defenders}-{midfielders}-{forwards}"
        logger.info("Created custom formation '%s': %s", name, formation_str)
        return formation_str

    @staticmethod
    def save_custom_formation(name: str, formation_str: str, presets_file: Path) -> None:
        """Persists a named custom formation to a JSON presets file."""
        existing: list[dict] = []
        if presets_file.exists():
            with open(presets_file, "r", encoding="utf-8") as fp:
                existing = json.load(fp)

        # Update existing entry or append new one
        for entry in existing:
            if entry.get("name") == name:
                entry["formation_str"] = formation_str
                break
        else:
            existing.append({"name": name, "formation_str": formation_str})

        presets_file.parent.mkdir(parents=True, exist_ok=True)
        with open(presets_file, "w", encoding="utf-8") as fp:
            json.dump(existing, fp, indent=2)

        logger.info("Saved custom formation '%s' (%s) to %s", name, formation_str, presets_file)

    @staticmethod
    def load_custom_formations(presets_file: Path) -> list[dict]:
        """Loads all custom formations from a JSON presets file."""
        if not presets_file.exists():
            return []

        with open(presets_file, "r", encoding="utf-8") as fp:
            formations = json.load(fp)

        return formations


# ---------------------------------------------------------------------------
# TacticalPreset / TacticalPresetManager
# ---------------------------------------------------------------------------


@dataclass
class TacticalPreset:
    name: str
    formation: str
    strategy: str
    instructions: dict

    def serialize(self) -> dict:
        return {
            "name": self.name,
            "formation": self.formation,
            "strategy": self.strategy,
            "instructions": self.instructions,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "TacticalPreset":
        return cls(
            name=data["name"],
            formation=data["formation"],
            strategy=data.get("strategy", "balanced"),
            instructions=data.get("instructions", {}),
        )


class TacticalPresetManager:
    """Manages tactical presets that can be saved, loaded, and shared."""

    def __init__(self):
        self.presets: list[TacticalPreset] = []

    def save_preset(self, preset: TacticalPreset) -> None:
        """Adds a preset to the in-memory list, replacing any with the same name."""
        self.presets = [p for p in self.presets if p.name != preset.name]
        self.presets.append(preset)

    def load_preset(self, name: str) -> TacticalPreset:
        """Returns the preset matching *name*.

        Raises KeyError if not found.
        """
        for preset in self.presets:
            if preset.name == name:
                return preset
        raise KeyError(f"Tactical preset '{name}' not found.")

    def export_presets(self, path: Path) -> None:
        """Saves all presets to a JSON file for sharing."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump([p.serialize() for p in self.presets], fp, indent=2)
        logger.info("Exported %d tactical presets to %s", len(self.presets), path)

    def import_presets(self, path: Path) -> None:
        """Loads presets from a JSON file, merging with existing ones."""
        if not path.exists():
            raise FileNotFoundError(f"Presets file not found: {path}")

        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        for entry in data:
            preset = TacticalPreset.get_from_dict(entry)
            self.save_preset(preset)

        logger.info("Imported %d tactical presets from %s", len(data), path)

    def get_all_presets(self) -> list[TacticalPreset]:
        """Returns all loaded presets."""
        return list(self.presets)

    def serialize(self) -> dict:
        return {
            "presets": [p.serialize() for p in self.presets],
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "TacticalPresetManager":
        manager = cls()
        for p in data.get("presets", []):
            manager.presets.append(TacticalPreset.get_from_dict(p))
        return manager


# ---------------------------------------------------------------------------
# ThemeManager
# ---------------------------------------------------------------------------


class ThemeManager:
    """Discovers and manages UI themes, including custom user-created themes."""

    BUILT_IN_THEMES: list[str] = ["football", "darkfootball"]

    def __init__(self, custom_themes_dir: Optional[Path] = None):
        if custom_themes_dir is None:
            custom_themes_dir = Path("ofm") / "themes"
        self.custom_themes_dir: Path = custom_themes_dir

    def discover_custom_themes(self) -> list[dict]:
        """Scans the custom themes directory for theme.json files.

        Each theme directory should contain a ``theme.json`` with at least
        a ``"name"`` and ``"colors"`` dict.
        """
        discovered: list[dict] = []

        if not self.custom_themes_dir.exists():
            return discovered

        for child in sorted(self.custom_themes_dir.iterdir()):
            theme_file = child / "theme.json" if child.is_dir() else None
            if theme_file is None or not theme_file.exists():
                continue

            try:
                with open(theme_file, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                discovered.append(
                    {
                        "name": data.get("name", child.name),
                        "path": str(child),
                        "colors": data.get("colors", {}),
                    }
                )
            except (json.JSONDecodeError, KeyError) as exc:
                logger.warning("Skipping invalid theme at %s: %s", child, exc)

        return discovered

    def load_theme(self, theme_name: str) -> dict:
        """Returns the ttkbootstrap color dict for the given theme.

        Looks in custom themes first, then falls back to built-in theme names.
        """
        # Check custom themes
        for theme in self.discover_custom_themes():
            if theme["name"] == theme_name:
                return theme["colors"]

        # Built-in themes return a sentinel dict so callers know to use the
        # ttkbootstrap built-in style.
        if theme_name in self.BUILT_IN_THEMES:
            return {"builtin": True, "name": theme_name}

        raise KeyError(f"Theme '{theme_name}' not found.")

    def save_custom_theme(self, name: str, colors: dict) -> None:
        """Saves a custom theme to the themes directory."""
        theme_dir = self.custom_themes_dir / name
        theme_dir.mkdir(parents=True, exist_ok=True)

        theme_data = {"name": name, "colors": colors}
        theme_file = theme_dir / "theme.json"
        with open(theme_file, "w", encoding="utf-8") as fp:
            json.dump(theme_data, fp, indent=2)

        logger.info("Saved custom theme '%s' to %s", name, theme_file)

    def get_all_themes(self) -> list[str]:
        """Returns a combined list of built-in and custom theme names."""
        custom_names = [t["name"] for t in self.discover_custom_themes()]
        return self.BUILT_IN_THEMES + custom_names


# ---------------------------------------------------------------------------
# PluginAPI (framework for future plugins)
# ---------------------------------------------------------------------------


@dataclass
class Plugin:
    name: str
    version: str
    author: str
    hooks: dict[str, Callable] = field(default_factory=dict)

    def serialize(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "hooks": list(self.hooks.keys()),
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "Plugin":
        """Restores metadata only; callables cannot be serialized."""
        return cls(
            name=data["name"],
            version=data.get("version", "0.0.0"),
            author=data.get("author", "Unknown"),
            hooks={},
        )


class PluginAPI:
    """Lightweight plugin registry that allows mods to hook into game events.

    Plugins register named hooks (e.g. ``"on_match_end"``, ``"on_transfer"``)
    and the engine triggers them at the appropriate time.
    """

    def __init__(self):
        self.plugins: list[Plugin] = []

    def register_plugin(self, plugin: Plugin) -> None:
        """Registers a plugin. Replaces an existing plugin with the same name."""
        self.plugins = [p for p in self.plugins if p.name != plugin.name]
        self.plugins.append(plugin)
        logger.info(
            "Registered plugin '%s' v%s by %s (hooks: %s)",
            plugin.name,
            plugin.version,
            plugin.author,
            list(plugin.hooks.keys()),
        )

    def trigger_hook(self, hook_name: str, *args, **kwargs) -> None:
        """Calls every plugin callback registered under *hook_name*."""
        for plugin in self.plugins:
            callback = plugin.hooks.get(hook_name)
            if callback is not None:
                try:
                    callback(*args, **kwargs)
                except Exception as exc:
                    logger.error(
                        "Plugin '%s' hook '%s' raised: %s",
                        plugin.name,
                        hook_name,
                        exc,
                    )

    def get_loaded_plugins(self) -> list[str]:
        """Returns a list of loaded plugin names."""
        return [p.name for p in self.plugins]
