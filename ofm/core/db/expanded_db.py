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
import random
import uuid
from datetime import date
from typing import Optional

from ofm.core.football.club import Club
from ofm.core.settings import Settings

from .generators import TeamGenerator

# ---------------------------------------------------------------------------
# League definitions — each entry describes a top-flight league that can be
# generated for a new game.  "reputation" is a 0-100 score used to calibrate
# the average skill level of generated players for that league.
# ---------------------------------------------------------------------------

LEAGUE_DEFINITIONS: dict[str, dict] = {
    "Premier League": {
        "country": "ENG",
        "confederation": "UEFA",
        "clubs": 20,
        "reputation": 95,
    },
    "La Liga": {
        "country": "ESP",
        "confederation": "UEFA",
        "clubs": 20,
        "reputation": 93,
    },
    "Serie A": {
        "country": "ITA",
        "confederation": "UEFA",
        "clubs": 20,
        "reputation": 90,
    },
    "Bundesliga": {
        "country": "GER",
        "confederation": "UEFA",
        "clubs": 18,
        "reputation": 88,
    },
    "Ligue 1": {
        "country": "FRA",
        "confederation": "UEFA",
        "clubs": 18,
        "reputation": 85,
    },
    "Brasileirao": {
        "country": "BRA",
        "confederation": "CONMEBOL",
        "clubs": 20,
        "reputation": 80,
    },
    "Liga MX": {
        "country": "MEX",
        "confederation": "CONCACAF",
        "clubs": 18,
        "reputation": 70,
    },
    "J-League": {
        "country": "JPN",
        "confederation": "AFC",
        "clubs": 18,
        "reputation": 65,
    },
    "MLS": {
        "country": "USA",
        "confederation": "CONCACAF",
        "clubs": 20,
        "reputation": 60,
    },
    "Eredivisie": {
        "country": "NED",
        "confederation": "UEFA",
        "clubs": 18,
        "reputation": 75,
    },
}

# ---------------------------------------------------------------------------
# Mapping from reputation ranges to player-generation mu/sigma.  Higher
# reputation leagues produce players with higher average skill.
# ---------------------------------------------------------------------------

_REPUTATION_TO_MU_SIGMA: list[tuple[int, int, int]] = [
    # (min_reputation, mu, sigma)
    (90, 68, 15),
    (80, 62, 16),
    (70, 56, 18),
    (60, 50, 20),
    (0, 45, 22),
]


def _mu_sigma_for_reputation(reputation: int) -> tuple[int, int]:
    """Returns (mu, sigma) for player generation given a league reputation."""
    for min_rep, mu, sigma in _REPUTATION_TO_MU_SIGMA:
        if reputation >= min_rep:
            return mu, sigma
    return 50, 20


class ExpandedDatabase:
    """Provides helpers for working with the expanded set of league definitions.

    This does **not** replace the existing ``DB`` class — it sits alongside it
    and adds the ability to generate full leagues on demand using the shared
    ``TeamGenerator`` infrastructure.
    """

    def __init__(
        self,
        league_definitions: Optional[dict[str, dict]] = None,
    ):
        self.league_definitions: dict[str, dict] = (
            league_definitions if league_definitions is not None else dict(LEAGUE_DEFINITIONS)
        )

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_available_leagues(self) -> list[str]:
        """Returns a sorted list of all league names."""
        return sorted(self.league_definitions.keys())

    def get_league_info(self, name: str) -> dict:
        """Returns the detail dict for a single league.

        Raises ``KeyError`` if the league name is not found.
        """
        if name not in self.league_definitions:
            raise KeyError(f"League '{name}' not found in definitions.")
        return dict(self.league_definitions[name])

    def get_leagues_by_confederation(self, confederation: str) -> list[str]:
        """Returns league names belonging to a given FIFA confederation."""
        return sorted(
            name
            for name, info in self.league_definitions.items()
            if info["confederation"] == confederation
        )

    def get_all_countries(self) -> list[str]:
        """Returns a sorted list of unique country codes across all leagues."""
        return sorted({info["country"] for info in self.league_definitions.values()})

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def _build_club_definitions(
        self,
        league_name: str,
        num_clubs: int,
        country: str,
        mu: int,
        sigma: int,
    ) -> list[dict]:
        """Builds a list of synthetic club definition dicts suitable for
        ``TeamGenerator``.

        Each dict mirrors the schema expected by ``Club.get_from_dict`` and by
        ``TeamGenerator.generate()``.
        """
        clubs = []
        for i in range(1, num_clubs + 1):
            club_def = {
                "name": f"{league_name} Club {i}",
                "country": country,
                "location": country,
                "default_formation": random.choice(
                    ["4-4-2", "4-3-3", "3-5-2", "4-5-1"]
                ),
                "stadium": f"Stadium {i}",
                "stadium_capacity": random.randint(15000, 80000),
                "squads_def": {
                    "mu": mu,
                    "sigma": sigma,
                },
            }
            clubs.append(club_def)
        return clubs

    def generate_league(
        self,
        league_name: str,
        settings: Settings,
        season_start: Optional[date] = None,
    ) -> list[Club]:
        """Generates all clubs (with squads) for the named league.

        Parameters
        ----------
        league_name:
            Must be a key in ``self.league_definitions``.
        settings:
            The application ``Settings`` instance — needed by ``TeamGenerator``
            for name files and paths.
        season_start:
            Optional season start date; defaults to today.

        Returns
        -------
        list[Club]
            Fully generated Club objects with squads.
        """
        if league_name not in self.league_definitions:
            raise KeyError(f"League '{league_name}' not found in definitions.")

        info = self.league_definitions[league_name]
        mu, sigma = _mu_sigma_for_reputation(info["reputation"])
        num_clubs = info["clubs"]
        country = info["country"]

        if season_start is None:
            season_start = date.today()

        club_defs = self._build_club_definitions(
            league_name, num_clubs, country, mu, sigma
        )

        # Load FIFA confederations from settings for nationality generation
        try:
            import json

            with open(settings.fifa_conf, "r", encoding="utf-8") as fp:
                fifa_conf = json.load(fp)
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback: minimal confederation list so generation can proceed
            fifa_conf = [
                {
                    "region": info["confederation"],
                    "countries": [country],
                }
            ]

        team_gen = TeamGenerator(club_defs, fifa_conf, settings, season_start)
        return team_gen.generate()
