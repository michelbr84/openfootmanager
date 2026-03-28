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
Distribution and packaging helpers for OpenFoot Manager.

Provides utilities for reading package metadata, checking dependencies,
gathering system information, and generating install instructions.
"""
import importlib.metadata
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PackageInfo:
    """Metadata about the OpenFoot Manager package."""

    name: str = "openfootmanager"
    version: str = "0.1.0"
    description: str = "A free and open source football manager game."
    author: str = "sturdy-robot"
    license: str = "GPL-3.0"
    python_requires: str = "^3.10"
    dependencies: list[str] = field(default_factory=list)


class PackageManager:
    """Utilities for inspecting the installed package and its environment."""

    # Fallback metadata when pyproject.toml cannot be read at runtime.
    _FALLBACK = PackageInfo(
        dependencies=["ttkbootstrap", "pyyaml"],
    )

    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            # Default: two levels up from this file (ofm/core -> ofm -> project)
            project_root = Path(__file__).resolve().parent.parent.parent
        self.project_root = project_root

    # ------------------------------------------------------------------
    # Package info
    # ------------------------------------------------------------------

    def get_package_info(self) -> PackageInfo:
        """Read package metadata from ``pyproject.toml``.

        Falls back to hard-coded defaults if the file is missing or the
        format is unexpected.
        """
        toml_path = self.project_root / "pyproject.toml"
        if not toml_path.exists():
            return PackageInfo(**self._FALLBACK.__dict__)

        try:
            # Python 3.11+ has tomllib; older versions need fallback
            try:
                import tomllib  # type: ignore[import-not-found]
            except ModuleNotFoundError:
                import tomli as tomllib  # type: ignore[import-not-found,no-redef]

            with open(toml_path, "rb") as fp:
                data = tomllib.load(fp)

            poetry = data.get("tool", {}).get("poetry", {})
            deps_raw = poetry.get("dependencies", {})
            # Filter out python itself from the dependency list
            deps = [k for k in deps_raw if k.lower() != "python"]

            return PackageInfo(
                name=poetry.get("name", self._FALLBACK.name),
                version=poetry.get("version", self._FALLBACK.version),
                description=poetry.get("description", self._FALLBACK.description),
                author=(
                    poetry.get("authors", [self._FALLBACK.author])[0]
                    if poetry.get("authors")
                    else self._FALLBACK.author
                ),
                license=poetry.get("license", self._FALLBACK.license),
                python_requires=deps_raw.get("python", self._FALLBACK.python_requires),
                dependencies=deps,
            )
        except Exception:
            return PackageInfo(**self._FALLBACK.__dict__)

    # ------------------------------------------------------------------
    # Dependency checking
    # ------------------------------------------------------------------

    def check_dependencies(self) -> list[tuple[str, bool]]:
        """Check whether each declared dependency is importable.

        Returns a list of ``(package_name, is_installed)`` tuples.
        """
        info = self.get_package_info()
        results: list[tuple[str, bool]] = []

        for dep in info.dependencies:
            # Normalize: pyproject names may use hyphens; Python uses underscores
            module_name = dep.replace("-", "_").lower()
            try:
                importlib.metadata.distribution(dep)
                results.append((dep, True))
            except importlib.metadata.PackageNotFoundError:
                # Try import as a secondary check
                try:
                    __import__(module_name)
                    results.append((dep, True))
                except ImportError:
                    results.append((dep, False))

        return results

    # ------------------------------------------------------------------
    # System info
    # ------------------------------------------------------------------

    def get_system_info(self) -> dict:
        """Gather system information useful for bug reports and diagnostics."""
        info: dict = {
            "python_version": sys.version,
            "python_implementation": platform.python_implementation(),
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "platform": platform.platform(),
        }

        # Try to get screen resolution (best-effort, no hard dependency)
        try:
            import tkinter as tk

            root = tk.Tk()
            root.withdraw()
            info["screen_resolution"] = f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}"
            root.destroy()
        except Exception:
            info["screen_resolution"] = "unknown"

        return info

    # ------------------------------------------------------------------
    # Update checking (placeholder)
    # ------------------------------------------------------------------

    def check_for_updates(self, current_version: str) -> Optional[dict]:
        """Check whether a newer version is available.

        This is a placeholder that always returns ``None``.  A real
        implementation would query a release API (e.g. GitHub Releases).

        Parameters
        ----------
        current_version:
            The currently installed version string (e.g. ``"0.1.0"``).

        Returns
        -------
        dict or None
            ``None`` when no update is available (or the check cannot be
            performed).  A future implementation would return a dict with
            keys ``latest_version``, ``download_url``, and ``changelog``.
        """
        # Placeholder — no network call.
        return None

    # ------------------------------------------------------------------
    # Install instructions
    # ------------------------------------------------------------------

    @staticmethod
    def get_install_instructions(platform_name: str) -> str:
        """Return platform-specific install instructions.

        Parameters
        ----------
        platform_name:
            One of ``"windows"``, ``"macos"``, ``"linux"``, or ``"source"``.

        Returns
        -------
        str
            Human-readable installation instructions.
        """
        platform_name = platform_name.lower()

        if platform_name == "windows":
            return (
                "Windows Installation\n"
                "====================\n"
                "1. Install Python 3.10+ from https://python.org\n"
                "2. Open a terminal and run:\n"
                "   pip install openfootmanager\n"
                "3. Launch with:\n"
                "   python -m ofm\n"
            )
        elif platform_name == "macos":
            return (
                "macOS Installation\n"
                "==================\n"
                "1. Install Python 3.10+ via Homebrew:\n"
                "   brew install python@3.12\n"
                "2. Install the package:\n"
                "   pip3 install openfootmanager\n"
                "3. Launch with:\n"
                "   python3 -m ofm\n"
            )
        elif platform_name == "linux":
            return (
                "Linux Installation\n"
                "==================\n"
                "1. Ensure Python 3.10+ is installed:\n"
                "   sudo apt install python3 python3-pip  # Debian/Ubuntu\n"
                "2. Install the package:\n"
                "   pip3 install openfootmanager\n"
                "3. Launch with:\n"
                "   python3 -m ofm\n"
            )
        elif platform_name == "source":
            return (
                "Install from Source\n"
                "===================\n"
                "1. Clone the repository:\n"
                "   git clone https://github.com/sturdy-robot/openfootmanager.git\n"
                "2. Install Poetry:\n"
                "   pip install poetry\n"
                "3. Install dependencies:\n"
                "   cd openfootmanager && poetry install\n"
                "4. Run:\n"
                "   poetry run python -m ofm\n"
            )
        else:
            return (
                f"No specific instructions for platform '{platform_name}'.\n"
                "Please install Python 3.10+ and run: pip install openfootmanager\n"
            )
