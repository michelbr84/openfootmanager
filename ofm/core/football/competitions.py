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
Competition systems for OpenFoot Manager.

Provides knockout cups, promotion/relegation, continental tournaments,
international competitions, and playoff brackets.
"""

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from .league import League, LeagueTableEntry, Season
from .club import Club


# ---------------------------------------------------------------------------
# Score generation helper (shared by all competition simulations)
# ---------------------------------------------------------------------------

_SCORE_WEIGHTS = [25, 30, 25, 13, 7]


def _random_score() -> int:
    """Return a weighted random score in the 0-4 range."""
    return random.choices(range(len(_SCORE_WEIGHTS)), weights=_SCORE_WEIGHTS, k=1)[0]


# ===================================================================
# 1. CupCompetition — Knockout tournament
# ===================================================================

class CupCompetition:
    """
    Knockout tournament that proceeds round-by-round until a single
    champion remains.  Optionally supports two-legged ties.

    Each round is a list of match dicts::

        {
            "home": UUID,
            "away": UUID,
            "home_goals": int | None,
            "away_goals": int | None,
            "home_goals_leg2": int | None,   # only when two_legs=True
            "away_goals_leg2": int | None,   # only when two_legs=True
            "played": bool,
            "extra_time": bool,
            "penalties": bool,
        }
    """

    def __init__(self, name: str, teams: list[UUID], two_legs: bool = False):
        if len(teams) < 2:
            raise ValueError("A cup competition requires at least 2 teams")
        self.name = name
        self.teams: list[UUID] = list(teams)
        self.two_legs = two_legs
        self.rounds: list[list[dict]] = []
        self.current_round: int = 0
        self._eliminated: set[UUID] = set()

    # ------------------------------------------------------------------
    # Drawing / pairing
    # ------------------------------------------------------------------

    def draw_round(self, seeded: list[UUID] | None = None) -> list[dict]:
        """
        Randomly pair the remaining teams for the current round.

        If *seeded* is provided those teams are placed as the "home" side
        in each match (useful for cross-group pairings in continental
        competitions).  Otherwise teams are shuffled freely.

        If the number of remaining teams is not a power of two the surplus
        teams receive a bye (automatic advance) in round 0 only.
        """
        remaining = [t for t in self.teams if t not in self._eliminated]

        if seeded is not None:
            # Pair seeded[i] vs unseeded[i] (caller controls order)
            unseeded = [t for t in remaining if t not in seeded]
            if len(seeded) != len(unseeded):
                raise ValueError(
                    "Seeded and unseeded lists must be the same length"
                )
            pairs = list(zip(seeded, unseeded))
        else:
            random.shuffle(remaining)

            # Handle byes for non-power-of-two counts in the first round
            if self.current_round == 0 and len(remaining) & (len(remaining) - 1) != 0:
                # Advance surplus teams automatically
                next_pow2 = 1
                while next_pow2 < len(remaining):
                    next_pow2 <<= 1
                target = next_pow2 // 2
                byes = len(remaining) - target * 2  # teams that skip this round
                # The first *byes* teams get a free pass
                bye_teams = remaining[:byes]
                active = remaining[byes:]
                pairs = [(active[i], active[i + 1]) for i in range(0, len(active), 2)]
                # Store byes as already-won matches (home wins walkover)
                bye_matches = [
                    self._make_match(t, t, walkover=True) for t in bye_teams
                ]
            else:
                pairs = [(remaining[i], remaining[i + 1]) for i in range(0, len(remaining), 2)]
                bye_matches = []

        matches = [self._make_match(h, a) for h, a in pairs]

        if seeded is None:
            # Prepend byes (if any)
            try:
                matches = bye_matches + matches
            except NameError:
                pass

        self.rounds.append(matches)
        return matches

    @staticmethod
    def _make_match(home: UUID, away: UUID, walkover: bool = False) -> dict:
        return {
            "home": home,
            "away": away,
            "home_goals": 3 if walkover else None,
            "away_goals": 0 if walkover else None,
            "home_goals_leg2": None,
            "away_goals_leg2": None,
            "played": walkover,
            "extra_time": False,
            "penalties": False,
        }

    # ------------------------------------------------------------------
    # Playing matches
    # ------------------------------------------------------------------

    def play_match(
        self,
        match_index: int,
        home_goals: int,
        away_goals: int,
        home_goals_leg2: int | None = None,
        away_goals_leg2: int | None = None,
    ):
        """Record a result for one match in the current round."""
        match = self.rounds[self.current_round][match_index]
        match["home_goals"] = home_goals
        match["away_goals"] = away_goals
        if self.two_legs:
            match["home_goals_leg2"] = home_goals_leg2
            match["away_goals_leg2"] = away_goals_leg2
        match["played"] = True

        # Determine if extra time / penalties were needed
        if self.two_legs:
            agg_home = home_goals + (home_goals_leg2 or 0)
            agg_away = away_goals + (away_goals_leg2 or 0)
        else:
            agg_home = home_goals
            agg_away = away_goals

        if agg_home == agg_away:
            # In a knockout, a draw triggers extra time / penalties.
            # We simulate a random winner.
            match["extra_time"] = True
            if random.random() < 0.5:
                match["penalties"] = True
            # Add a single extra goal to decide the tie
            if random.random() < 0.5:
                match["home_goals"] = home_goals + 1
            else:
                match["away_goals"] = away_goals + 1

    def simulate_round(self):
        """Auto-generate results for every unplayed match in the current round."""
        if self.current_round >= len(self.rounds):
            self.draw_round()

        for i, match in enumerate(self.rounds[self.current_round]):
            if match["played"]:
                continue
            h = _random_score()
            a = _random_score()
            if self.two_legs:
                h2 = _random_score()
                a2 = _random_score()
                self.play_match(i, h, a, h2, a2)
            else:
                self.play_match(i, h, a)

    # ------------------------------------------------------------------
    # Advancing
    # ------------------------------------------------------------------

    def get_winners(self) -> list[UUID]:
        """Return the list of winners from the current (latest completed) round."""
        if not self.rounds:
            return []

        round_matches = self.rounds[self.current_round]
        winners: list[UUID] = []

        for match in round_matches:
            if not match["played"]:
                continue

            home, away = match["home"], match["away"]

            # Walkover (bye)
            if home == away:
                winners.append(home)
                continue

            if self.two_legs:
                agg_h = (match["home_goals"] or 0) + (match["home_goals_leg2"] or 0)
                agg_a = (match["away_goals"] or 0) + (match["away_goals_leg2"] or 0)
            else:
                agg_h = match["home_goals"] or 0
                agg_a = match["away_goals"] or 0

            if agg_h > agg_a:
                winners.append(home)
                self._eliminated.add(away)
            else:
                winners.append(away)
                self._eliminated.add(home)

        return winners

    def advance_round(self):
        """Move to the next round after all matches are played."""
        # Mark losers as eliminated (get_winners does this as side-effect)
        self.get_winners()
        self.current_round += 1

    def get_champion(self) -> UUID | None:
        """Return the champion if the tournament is finished, else None."""
        remaining = [t for t in self.teams if t not in self._eliminated]
        if len(remaining) == 1:
            return remaining[0]
        return None

    @property
    def is_finished(self) -> bool:
        remaining = [t for t in self.teams if t not in self._eliminated]
        return len(remaining) <= 1

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def serialize(self) -> dict:
        def _ser_match(m: dict) -> dict:
            return {
                "home": str(m["home"]),
                "away": str(m["away"]),
                "home_goals": m["home_goals"],
                "away_goals": m["away_goals"],
                "home_goals_leg2": m["home_goals_leg2"],
                "away_goals_leg2": m["away_goals_leg2"],
                "played": m["played"],
                "extra_time": m["extra_time"],
                "penalties": m["penalties"],
            }

        return {
            "name": self.name,
            "teams": [str(t) for t in self.teams],
            "two_legs": self.two_legs,
            "current_round": self.current_round,
            "eliminated": [str(t) for t in self._eliminated],
            "rounds": [
                [_ser_match(m) for m in rnd] for rnd in self.rounds
            ],
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "CupCompetition":
        cup = cls(
            name=data["name"],
            teams=[UUID(t) for t in data["teams"]],
            two_legs=data.get("two_legs", False),
        )
        cup.current_round = data["current_round"]
        cup._eliminated = {UUID(t) for t in data.get("eliminated", [])}
        cup.rounds = []
        for rnd in data.get("rounds", []):
            matches = []
            for m in rnd:
                matches.append({
                    "home": UUID(m["home"]),
                    "away": UUID(m["away"]),
                    "home_goals": m["home_goals"],
                    "away_goals": m["away_goals"],
                    "home_goals_leg2": m.get("home_goals_leg2"),
                    "away_goals_leg2": m.get("away_goals_leg2"),
                    "played": m["played"],
                    "extra_time": m.get("extra_time", False),
                    "penalties": m.get("penalties", False),
                })
            cup.rounds.append(matches)
        return cup


# ===================================================================
# 2. DivisionSystem — Promotion and relegation
# ===================================================================

class DivisionSystem:
    """
    Manages multiple divisions with promotion and relegation between them.

    *divisions* maps a tier number (1 = top flight) to the list of team
    UUIDs in that tier.

    Default rules (English-style):
      - Top 2 of a lower division are promoted automatically.
      - Bottom 3 of an upper division are relegated.
      - 3rd–6th of the lower division enter a playoff for one extra
        promotion spot.
    """

    PROMOTION_AUTOMATIC = 2
    RELEGATION_SPOTS = 3
    PLAYOFF_POSITIONS = (3, 4, 5, 6)  # 1-indexed standings positions

    def __init__(self, divisions: dict[int, list[UUID]]):
        # Ensure keys are ints and sorted
        self.divisions: dict[int, list[UUID]] = {
            int(k): list(v) for k, v in sorted(divisions.items())
        }
        self._promotions: dict[int, list[UUID]] = {}
        self._relegations: dict[int, list[UUID]] = {}
        self._playoff_winners: dict[int, UUID | None] = {}

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_division(self, team_id: UUID) -> int:
        """Return the division tier a team belongs to, or -1 if not found."""
        for tier, teams in self.divisions.items():
            if team_id in teams:
                return tier
        return -1

    # ------------------------------------------------------------------
    # End-of-season processing
    # ------------------------------------------------------------------

    def get_promoted_teams(self, division: int, standings: list[UUID]) -> list[UUID]:
        """
        Return teams from *division* that earn automatic promotion.

        *standings* is an ordered list of team UUIDs from top to bottom
        in the final table of the given division.
        """
        return standings[: self.PROMOTION_AUTOMATIC]

    def get_relegated_teams(self, division: int, standings: list[UUID]) -> list[UUID]:
        """
        Return teams from *division* that are relegated.

        *standings* is ordered top-to-bottom.
        """
        return standings[-self.RELEGATION_SPOTS :]

    def _get_playoff_teams(self, division: int, standings: list[UUID]) -> list[UUID]:
        """Teams in playoff positions from a lower division."""
        return [
            standings[pos - 1]
            for pos in self.PLAYOFF_POSITIONS
            if pos - 1 < len(standings)
        ]

    def process_end_of_season(
        self, standings_by_division: dict[int, list[UUID]]
    ):
        """
        Determine all promotions and relegations across all tiers.

        *standings_by_division* maps each tier to an ordered list of
        team UUIDs (best to worst).
        """
        tiers = sorted(self.divisions.keys())

        self._promotions = {}
        self._relegations = {}
        self._playoff_winners = {}

        for tier in tiers:
            standings = standings_by_division.get(tier, [])

            # Relegation from this division (not applicable to lowest tier)
            if tier < max(tiers):
                self._relegations[tier] = self.get_relegated_teams(tier, standings)

            # Promotion from this division (not applicable to top tier)
            if tier > min(tiers):
                self._promotions[tier] = self.get_promoted_teams(tier, standings)

                # Playoff for extra spot
                playoff_teams = self._get_playoff_teams(tier, standings)
                if len(playoff_teams) >= 4:
                    bracket = PlayoffBracket(playoff_teams[:4])
                    winner = bracket.simulate()
                    self._playoff_winners[tier] = winner
                else:
                    self._playoff_winners[tier] = None

    def apply_changes(self):
        """
        Swap teams between divisions based on the promotion/relegation
        results computed by ``process_end_of_season``.
        """
        tiers = sorted(self.divisions.keys())

        for i in range(len(tiers) - 1):
            upper = tiers[i]
            lower = tiers[i + 1]

            promoted = list(self._promotions.get(lower, []))
            playoff_winner = self._playoff_winners.get(lower)
            if playoff_winner and playoff_winner not in promoted:
                promoted.append(playoff_winner)

            relegated = list(self._relegations.get(upper, []))

            # Move promoted teams up
            for team in promoted:
                if team in self.divisions[lower]:
                    self.divisions[lower].remove(team)
                    self.divisions[upper].append(team)

            # Move relegated teams down
            for team in relegated:
                if team in self.divisions[upper]:
                    self.divisions[upper].remove(team)
                    self.divisions[lower].append(team)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def serialize(self) -> dict:
        return {
            "divisions": {
                str(k): [str(t) for t in v]
                for k, v in self.divisions.items()
            },
            "promotions": {
                str(k): [str(t) for t in v]
                for k, v in self._promotions.items()
            },
            "relegations": {
                str(k): [str(t) for t in v]
                for k, v in self._relegations.items()
            },
            "playoff_winners": {
                str(k): str(v) if v else None
                for k, v in self._playoff_winners.items()
            },
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "DivisionSystem":
        divisions = {
            int(k): [UUID(t) for t in v]
            for k, v in data["divisions"].items()
        }
        ds = cls(divisions)
        ds._promotions = {
            int(k): [UUID(t) for t in v]
            for k, v in data.get("promotions", {}).items()
        }
        ds._relegations = {
            int(k): [UUID(t) for t in v]
            for k, v in data.get("relegations", {}).items()
        }
        ds._playoff_winners = {
            int(k): UUID(v) if v else None
            for k, v in data.get("playoff_winners", {}).items()
        }
        return ds


# ===================================================================
# 3. ContinentalCompetition — Champions League / Europa League style
# ===================================================================

class ContinentalCompetition:
    """
    A two-phase tournament with a group stage followed by a knockout
    stage, modelled after the UEFA Champions League / Europa League.

    The group stage creates mini-leagues (double round-robin).  The
    top *qualifiers_per_group* teams from each group advance to a
    single-elimination knockout (with optional two-legged ties).
    """

    def __init__(
        self,
        name: str,
        teams: list[UUID],
        group_count: int = 8,
        teams_per_group: int = 4,
        qualifiers_per_group: int = 2,
        knockout_two_legs: bool = True,
    ):
        total_needed = group_count * teams_per_group
        if len(teams) < total_needed:
            raise ValueError(
                f"Need {total_needed} teams for {group_count} groups of "
                f"{teams_per_group}, got {len(teams)}"
            )

        self.name = name
        self.teams: list[UUID] = list(teams[:total_needed])
        self.group_count = group_count
        self.teams_per_group = teams_per_group
        self.qualifiers_per_group = qualifiers_per_group
        self.knockout_two_legs = knockout_two_legs

        self.groups: dict[str, list[UUID]] = {}
        self.group_tables: dict[str, dict[UUID, dict]] = {}
        self.group_results: dict[str, list[dict]] = {}
        self.knockout_stage: CupCompetition | None = None
        self.phase: str = "group"  # "group" | "knockout"

    # ------------------------------------------------------------------
    # Group draw
    # ------------------------------------------------------------------

    def draw_groups(self, pots: list[list[UUID]] | None = None):
        """
        Distribute teams into groups.

        If *pots* are supplied (list of lists, one per pot), one team from
        each pot is placed into each group — standard UEFA-style pot seeding.
        Otherwise teams are shuffled randomly.
        """
        if pots:
            for pot in pots:
                random.shuffle(pot)

            group_labels = [
                chr(ord("A") + i) for i in range(self.group_count)
            ]
            self.groups = {label: [] for label in group_labels}

            for pot in pots:
                for i, team in enumerate(pot[: self.group_count]):
                    self.groups[group_labels[i]].append(team)
        else:
            pool = list(self.teams)
            random.shuffle(pool)
            group_labels = [
                chr(ord("A") + i) for i in range(self.group_count)
            ]
            self.groups = {}
            idx = 0
            for label in group_labels:
                self.groups[label] = pool[idx : idx + self.teams_per_group]
                idx += self.teams_per_group

        # Initialise group tables
        for label, members in self.groups.items():
            self.group_tables[label] = {
                t: {
                    "played": 0,
                    "won": 0,
                    "drawn": 0,
                    "lost": 0,
                    "gf": 0,
                    "ga": 0,
                    "points": 0,
                }
                for t in members
            }
            self.group_results[label] = []

    # ------------------------------------------------------------------
    # Group matches
    # ------------------------------------------------------------------

    def play_group_match(
        self,
        group: str,
        home: UUID,
        away: UUID,
        h_goals: int,
        a_goals: int,
    ):
        """Record the result of a single group-stage match."""
        table = self.group_tables[group]

        for side, opp, gf, ga in [
            (home, away, h_goals, a_goals),
            (away, home, a_goals, h_goals),
        ]:
            entry = table[side]
            entry["played"] += 1
            entry["gf"] += gf
            entry["ga"] += ga
            if gf > ga:
                entry["won"] += 1
                entry["points"] += 3
            elif gf < ga:
                entry["lost"] += 1
            else:
                entry["drawn"] += 1
                entry["points"] += 1

        self.group_results[group].append({
            "home": home,
            "away": away,
            "home_goals": h_goals,
            "away_goals": a_goals,
        })

    def simulate_group_stage(self):
        """Simulate all group-stage matches (double round-robin)."""
        if not self.groups:
            self.draw_groups()

        for label, members in self.groups.items():
            # Generate double round-robin fixtures
            for home in members:
                for away in members:
                    if home != away:
                        self.play_group_match(
                            label, home, away, _random_score(), _random_score()
                        )

    def get_group_standings(self) -> dict[str, list[tuple[UUID, dict]]]:
        """
        Return standings for every group, sorted by points then goal
        difference then goals scored.
        """
        standings: dict[str, list[tuple[UUID, dict]]] = {}
        for label, table in self.group_tables.items():
            ordered = sorted(
                table.items(),
                key=lambda item: (
                    item[1]["points"],
                    item[1]["gf"] - item[1]["ga"],
                    item[1]["gf"],
                ),
                reverse=True,
            )
            standings[label] = ordered
        return standings

    # ------------------------------------------------------------------
    # Transition to knockout
    # ------------------------------------------------------------------

    def advance_to_knockout(self):
        """
        Promote the top teams from each group into a knockout bracket.

        The draw pairs 1st of one group against 2nd of another group
        (no team meets a club from its own group in the round of 16).
        """
        standings = self.get_group_standings()
        group_labels = sorted(standings.keys())

        firsts: list[UUID] = []
        seconds: list[UUID] = []
        for label in group_labels:
            ranked = standings[label]
            firsts.append(ranked[0][0])
            seconds.append(ranked[1][0])

        # Pair 1st of group i with 2nd of group (count - 1 - i) to
        # avoid same-group clashes in the simplest manner.
        random.shuffle(seconds)
        # Make sure no first meets a second from the same group
        for attempt in range(100):
            conflict = False
            for i, first_team in enumerate(firsts):
                own_group = group_labels[i]
                second_team = seconds[i]
                # Check if second_team is from the same group
                if second_team in self.groups[own_group]:
                    conflict = True
                    break
            if not conflict:
                break
            random.shuffle(seconds)

        all_knockout_teams = []
        seeded: list[UUID] = []
        unseeded: list[UUID] = []
        for i in range(len(firsts)):
            seeded.append(firsts[i])
            unseeded.append(seconds[i])
        all_knockout_teams = seeded + unseeded

        self.knockout_stage = CupCompetition(
            name=f"{self.name} Knockout",
            teams=all_knockout_teams,
            two_legs=self.knockout_two_legs,
        )
        self.knockout_stage.draw_round(seeded=seeded)
        self.phase = "knockout"

    def get_champion(self) -> UUID | None:
        """Return the champion if the knockout stage is finished."""
        if self.knockout_stage is not None:
            return self.knockout_stage.get_champion()
        return None

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def serialize(self) -> dict:
        ser_groups = {
            label: [str(t) for t in members]
            for label, members in self.groups.items()
        }
        ser_tables = {}
        for label, table in self.group_tables.items():
            ser_tables[label] = {str(k): v for k, v in table.items()}

        ser_results = {}
        for label, matches in self.group_results.items():
            ser_results[label] = [
                {
                    "home": str(m["home"]),
                    "away": str(m["away"]),
                    "home_goals": m["home_goals"],
                    "away_goals": m["away_goals"],
                }
                for m in matches
            ]

        return {
            "name": self.name,
            "teams": [str(t) for t in self.teams],
            "group_count": self.group_count,
            "teams_per_group": self.teams_per_group,
            "qualifiers_per_group": self.qualifiers_per_group,
            "knockout_two_legs": self.knockout_two_legs,
            "phase": self.phase,
            "groups": ser_groups,
            "group_tables": ser_tables,
            "group_results": ser_results,
            "knockout_stage": (
                self.knockout_stage.serialize()
                if self.knockout_stage
                else None
            ),
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "ContinentalCompetition":
        comp = cls(
            name=data["name"],
            teams=[UUID(t) for t in data["teams"]],
            group_count=data["group_count"],
            teams_per_group=data["teams_per_group"],
            qualifiers_per_group=data.get("qualifiers_per_group", 2),
            knockout_two_legs=data.get("knockout_two_legs", True),
        )
        comp.phase = data.get("phase", "group")

        # Restore groups
        for label, members in data.get("groups", {}).items():
            comp.groups[label] = [UUID(t) for t in members]

        # Restore group tables
        for label, table in data.get("group_tables", {}).items():
            comp.group_tables[label] = {UUID(k): v for k, v in table.items()}

        # Restore group results
        for label, matches in data.get("group_results", {}).items():
            comp.group_results[label] = [
                {
                    "home": UUID(m["home"]),
                    "away": UUID(m["away"]),
                    "home_goals": m["home_goals"],
                    "away_goals": m["away_goals"],
                }
                for m in matches
            ]

        # Restore knockout stage
        if data.get("knockout_stage"):
            comp.knockout_stage = CupCompetition.get_from_dict(
                data["knockout_stage"]
            )

        return comp


# ===================================================================
# 4. InternationalCompetition — World Cup / continental championships
# ===================================================================

class InternationalCompetition:
    """
    International tournament (World Cup, Euro, Copa America, etc.).

    Combines a group stage (via ``ContinentalCompetition``) with a
    knockout stage.  Teams are nations identified by their country
    string, with national squads selected from a pool of available
    players.
    """

    SQUAD_SIZE = 23

    def __init__(self, name: str, nations: list[str]):
        if len(nations) < 2:
            raise ValueError("Need at least 2 nations")
        self.name = name
        self.nations: list[str] = list(nations)
        # Map nation string -> list of player ids
        self.squads: dict[str, list[int]] = {}

        # Internal UUIDs assigned to each nation for the competition engine
        self._nation_ids: dict[str, UUID] = {
            nation: uuid.uuid4() for nation in nations
        }
        self._id_to_nation: dict[UUID, str] = {
            v: k for k, v in self._nation_ids.items()
        }

        # Competition stages (created lazily)
        self.group_stage: ContinentalCompetition | None = None
        self.knockout_stage: CupCompetition | None = None

    # ------------------------------------------------------------------
    # Squad selection
    # ------------------------------------------------------------------

    def select_national_squads(self, all_players: list[dict]):
        """
        Select national squads from the pool of all available players.

        Each player dict is expected to have at least:
          - ``"id"``: int
          - ``"nationality"``: str
          - ``"overall"``: int (or a comparable skill rating)

        The top *SQUAD_SIZE* players per nationality are chosen.
        """
        by_nation: dict[str, list[dict]] = {}
        for p in all_players:
            nat = p.get("nationality", "")
            if nat in self._nation_ids:
                by_nation.setdefault(nat, []).append(p)

        for nation in self.nations:
            pool = by_nation.get(nation, [])
            pool.sort(key=lambda p: p.get("overall", 0), reverse=True)
            self.squads[nation] = [
                p["id"] for p in pool[: self.SQUAD_SIZE]
            ]

    # ------------------------------------------------------------------
    # Tournament flow
    # ------------------------------------------------------------------

    def _setup_group_stage(self):
        """Create the group stage."""
        nation_uuids = [self._nation_ids[n] for n in self.nations]
        # Determine sensible group geometry
        total = len(nation_uuids)
        teams_per_group = 4
        group_count = total // teams_per_group
        if group_count < 1:
            group_count = 1
            teams_per_group = total

        self.group_stage = ContinentalCompetition(
            name=f"{self.name} Group Stage",
            teams=nation_uuids,
            group_count=group_count,
            teams_per_group=teams_per_group,
            knockout_two_legs=False,
        )

    def simulate_tournament(self) -> str:
        """
        Simulate the entire tournament and return the winning nation name.
        """
        self._setup_group_stage()
        assert self.group_stage is not None

        self.group_stage.simulate_group_stage()
        self.group_stage.advance_to_knockout()

        ko = self.group_stage.knockout_stage
        assert ko is not None
        self.knockout_stage = ko

        while not ko.is_finished:
            ko.simulate_round()
            ko.advance_round()
            if not ko.is_finished:
                ko.draw_round()

        champion_id = ko.get_champion()
        if champion_id is not None:
            return self._id_to_nation.get(champion_id, "Unknown")
        return "Unknown"

    def get_results_summary(self) -> dict:
        """Return a summary dictionary of the tournament results."""
        summary: dict = {
            "name": self.name,
            "nations": self.nations,
            "champion": None,
            "group_standings": {},
        }

        if self.group_stage:
            standings = self.group_stage.get_group_standings()
            for label, ranked in standings.items():
                summary["group_standings"][label] = [
                    {
                        "nation": self._id_to_nation.get(tid, "?"),
                        "points": info["points"],
                        "gf": info["gf"],
                        "ga": info["ga"],
                    }
                    for tid, info in ranked
                ]

        champion_id = (
            self.knockout_stage.get_champion()
            if self.knockout_stage
            else None
        )
        if champion_id:
            summary["champion"] = self._id_to_nation.get(champion_id, "?")

        return summary

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def serialize(self) -> dict:
        return {
            "name": self.name,
            "nations": self.nations,
            "squads": self.squads,
            "nation_ids": {
                nation: str(uid) for nation, uid in self._nation_ids.items()
            },
            "group_stage": (
                self.group_stage.serialize() if self.group_stage else None
            ),
            "knockout_stage": (
                self.knockout_stage.serialize() if self.knockout_stage else None
            ),
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "InternationalCompetition":
        comp = cls(name=data["name"], nations=data["nations"])
        comp.squads = data.get("squads", {})

        # Restore nation <-> UUID mapping
        if "nation_ids" in data:
            comp._nation_ids = {
                nation: UUID(uid)
                for nation, uid in data["nation_ids"].items()
            }
            comp._id_to_nation = {
                v: k for k, v in comp._nation_ids.items()
            }

        if data.get("group_stage"):
            comp.group_stage = ContinentalCompetition.get_from_dict(
                data["group_stage"]
            )
        if data.get("knockout_stage"):
            comp.knockout_stage = CupCompetition.get_from_dict(
                data["knockout_stage"]
            )
        return comp


# ===================================================================
# 5. PlayoffBracket — Promotion playoffs (semi-finals + final)
# ===================================================================

class PlayoffBracket:
    """
    A mini knockout bracket for promotion playoffs.

    Expects exactly 4 teams:
      - Two-legged semi-finals: 1st vs 4th, 2nd vs 3rd
      - Single-leg final at a neutral venue

    Seeding follows the English Football League convention where the
    highest-placed team has home advantage in the second leg.
    """

    def __init__(self, teams: list[UUID]):
        if len(teams) != 4:
            raise ValueError("PlayoffBracket requires exactly 4 teams")
        self.teams: list[UUID] = list(teams)  # ordered by league position
        self.semi_finals: list[dict] = []
        self.final: dict | None = None
        self.winner: UUID | None = None

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    def _play_two_leg_tie(self, home: UUID, away: UUID) -> UUID:
        """Simulate a two-legged tie and return the winner."""
        h1, a1 = _random_score(), _random_score()
        h2, a2 = _random_score(), _random_score()
        agg_home = h1 + a2  # home team's total (home leg1 + away leg2)
        agg_away = a1 + h2

        result = {
            "home": home,
            "away": away,
            "leg1_home_goals": h1,
            "leg1_away_goals": a1,
            "leg2_home_goals": h2,
            "leg2_away_goals": a2,
            "agg_home": agg_home,
            "agg_away": agg_away,
        }

        if agg_home > agg_away:
            result["winner"] = home
        elif agg_away > agg_home:
            result["winner"] = away
        else:
            # Decided on away goals, then penalties (random)
            if a1 > a2:
                result["winner"] = home
            elif a2 > a1:
                result["winner"] = away
            else:
                result["winner"] = random.choice([home, away])
            result["decided_by"] = "penalties"

        self.semi_finals.append(result)
        return result["winner"]

    def simulate(self) -> UUID:
        """
        Run the full playoff bracket and return the winning (promoted)
        team's UUID.
        """
        # Semi-finals: 1st vs 4th, 2nd vs 3rd (higher seed gets 2nd leg at home)
        winner1 = self._play_two_leg_tie(self.teams[3], self.teams[0])
        winner2 = self._play_two_leg_tie(self.teams[2], self.teams[1])

        # Final: single leg at neutral venue
        fh, fa = _random_score(), _random_score()
        if fh == fa:
            # Extra time / penalties — random winner
            fh += 1 if random.random() < 0.5 else 0
            fa += 0 if fh > fa else 1

        self.final = {
            "home": winner1,
            "away": winner2,
            "home_goals": fh,
            "away_goals": fa,
        }

        if fh > fa:
            self.winner = winner1
        else:
            self.winner = winner2

        self.final["winner"] = self.winner
        return self.winner

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def serialize(self) -> dict:
        def _ser_uuid(val):
            return str(val) if val else None

        ser_semis = []
        for sf in self.semi_finals:
            ser_semis.append({
                k: _ser_uuid(v) if isinstance(v, UUID) else v
                for k, v in sf.items()
            })

        ser_final = None
        if self.final:
            ser_final = {
                k: _ser_uuid(v) if isinstance(v, UUID) else v
                for k, v in self.final.items()
            }

        return {
            "teams": [str(t) for t in self.teams],
            "semi_finals": ser_semis,
            "final": ser_final,
            "winner": str(self.winner) if self.winner else None,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "PlayoffBracket":
        bracket = cls(teams=[UUID(t) for t in data["teams"]])

        for sf in data.get("semi_finals", []):
            restored = {}
            for k, v in sf.items():
                if k in ("home", "away", "winner") and v is not None:
                    restored[k] = UUID(v)
                else:
                    restored[k] = v
            bracket.semi_finals.append(restored)

        if data.get("final"):
            restored_final = {}
            for k, v in data["final"].items():
                if k in ("home", "away", "winner") and v is not None:
                    restored_final[k] = UUID(v)
                else:
                    restored_final[k] = v
            bracket.final = restored_final

        bracket.winner = UUID(data["winner"]) if data.get("winner") else None
        return bracket
