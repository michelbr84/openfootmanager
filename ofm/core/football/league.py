import random
import uuid
from dataclasses import dataclass, field
from ..football.club import Club
from ..simulation.fixture import Fixture

@dataclass
class LeagueTableEntry:
    club: Club
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    @property
    def goal_difference(self):
        return self.goals_for - self.goals_against

class League:
    def __init__(self, name: str, clubs: list[Club]):
        self.name = name
        self.clubs = clubs
        self.table: dict[str, LeagueTableEntry] = {
            club.name: LeagueTableEntry(club) for club in clubs
        }
        self.fixtures: list[Fixture] = []

    def generate_fixtures(self) -> list[list[tuple]]:
        """
        Round-robin fixture generation. Each team plays every other team twice
        (home and away). Returns fixtures organized by rounds.

        Uses the standard round-robin scheduling algorithm with one team fixed
        and the others rotating. With N teams, produces 2*(N-1) rounds, each
        containing N/2 matches.

        If the number of teams is odd, a dummy entry is added (bye week).
        """
        if not self.clubs or len(self.clubs) < 2:
            return []

        teams = list(self.clubs)

        # If odd number of teams, add a None placeholder for bye rounds
        if len(teams) % 2 != 0:
            teams.append(None)

        n = len(teams)
        num_rounds = n - 1
        half = n // 2

        # First half: single round-robin
        first_half_rounds = []
        rotation = list(range(1, n))  # indices 1..n-1; index 0 is fixed

        for _ in range(num_rounds):
            round_fixtures = []
            # First match: fixed team (index 0) vs first in rotation
            indices = [0] + list(rotation)
            for i in range(half):
                home_idx = indices[i]
                away_idx = indices[n - 1 - i]
                home = teams[home_idx]
                away = teams[away_idx]
                # Skip matches involving the bye placeholder
                if home is not None and away is not None:
                    round_fixtures.append((home.club_id, away.club_id))
            first_half_rounds.append(round_fixtures)
            # Rotate: move last element to front
            rotation = [rotation[-1]] + rotation[:-1]

        # Second half: reverse home/away
        second_half_rounds = []
        for rnd in first_half_rounds:
            reversed_round = [(away, home) for home, away in rnd]
            second_half_rounds.append(reversed_round)

        all_rounds = first_half_rounds + second_half_rounds
        return all_rounds

    def record_result(self, fixture: Fixture, home_score: int, away_score: int):
        home_entry = self.table[fixture.home_team.name] # Assuming team names match club names, careful here
        away_entry = self.table[fixture.away_team.name]

        home_entry.played += 1
        away_entry.played += 1
        home_entry.goals_for += home_score
        home_entry.goals_against += away_score
        away_entry.goals_for += away_score
        away_entry.goals_against += home_score

        if home_score > away_score:
            home_entry.won += 1
            home_entry.points += 3
            away_entry.lost += 1
        elif away_score > home_score:
            away_entry.won += 1
            away_entry.points += 3
            home_entry.lost += 1
        else:
            home_entry.drawn += 1
            home_entry.points += 1
            away_entry.drawn += 1
            away_entry.points += 1

    def _record_result_by_name(self, home_name: str, away_name: str, home_goals: int, away_goals: int):
        """Record a result using club names directly, for use by Season."""
        home_entry = self.table[home_name]
        away_entry = self.table[away_name]

        home_entry.played += 1
        away_entry.played += 1
        home_entry.goals_for += home_goals
        home_entry.goals_against += away_goals
        away_entry.goals_for += away_goals
        away_entry.goals_against += home_goals

        if home_goals > away_goals:
            home_entry.won += 1
            home_entry.points += 3
            away_entry.lost += 1
        elif away_goals > home_goals:
            away_entry.won += 1
            away_entry.points += 3
            home_entry.lost += 1
        else:
            home_entry.drawn += 1
            home_entry.points += 1
            away_entry.drawn += 1
            away_entry.points += 1

    def get_standings(self) -> list[LeagueTableEntry]:
        entries = list(self.table.values())
        # Sort by points, then goal difference, then goals for
        entries.sort(key=lambda x: (x.points, x.goal_difference, x.goals_for), reverse=True)
        return entries


class Season:
    """Manages a complete league season with rounds, results, and standings."""

    # Score weights: index is the score value (0-4), value is relative weight
    _SCORE_WEIGHTS = [25, 30, 25, 13, 7]

    def __init__(self, league: League):
        self.league = league
        self.current_round: int = 0
        self.rounds: list[list[tuple]] = []
        self.results: list[dict] = []
        self._club_map: dict[str, Club] = {
            str(club.club_id): club for club in league.clubs
        }

    @property
    def is_finished(self) -> bool:
        return len(self.rounds) > 0 and self.current_round >= len(self.rounds)

    def setup_season(self):
        """Generate fixtures and organize them into rounds."""
        self.rounds = self.league.generate_fixtures()
        self.current_round = 0
        self.results = []

    def get_current_round_fixtures(self) -> list[tuple]:
        """Returns fixtures for the current round."""
        if self.is_finished or not self.rounds:
            return []
        return self.rounds[self.current_round]

    def play_round(self, results: list[dict]):
        """
        Record results for the current round and advance.

        Each result dict: {"home": club_id, "away": club_id,
                           "home_goals": int, "away_goals": int}
        """
        if self.is_finished:
            return

        for result in results:
            home_id = str(result["home"])
            away_id = str(result["away"])
            home_club = self._club_map[home_id]
            away_club = self._club_map[away_id]
            self.league._record_result_by_name(
                home_club.name, away_club.name,
                result["home_goals"], result["away_goals"]
            )

        self.results.append({
            "round": self.current_round,
            "matches": results,
        })
        self.advance_round()

    def simulate_round(self):
        """
        Auto-generate random results for the current round.
        Scores are weighted toward lower values (0-4 range).
        """
        if self.is_finished:
            return

        fixtures = self.get_current_round_fixtures()
        results = []
        score_range = list(range(len(self._SCORE_WEIGHTS)))

        for home_id, away_id in fixtures:
            home_goals = random.choices(score_range, weights=self._SCORE_WEIGHTS, k=1)[0]
            away_goals = random.choices(score_range, weights=self._SCORE_WEIGHTS, k=1)[0]
            results.append({
                "home": home_id,
                "away": away_id,
                "home_goals": home_goals,
                "away_goals": away_goals,
            })

        self.play_round(results)

    def advance_round(self):
        """Increment the current round counter."""
        self.current_round += 1

    def get_standings(self) -> list[LeagueTableEntry]:
        """Delegate to league standings."""
        return self.league.get_standings()

    def serialize(self) -> dict:
        """Serialize season state for save/load."""
        serialized_results = []
        for round_data in self.results:
            matches = []
            for m in round_data["matches"]:
                matches.append({
                    "home": str(m["home"]),
                    "away": str(m["away"]),
                    "home_goals": m["home_goals"],
                    "away_goals": m["away_goals"],
                })
            serialized_results.append({
                "round": round_data["round"],
                "matches": matches,
            })

        serialized_rounds = []
        for rnd in self.rounds:
            serialized_rounds.append([
                (str(home_id), str(away_id)) for home_id, away_id in rnd
            ])

        return {
            "league_name": self.league.name,
            "current_round": self.current_round,
            "rounds": serialized_rounds,
            "results": serialized_results,
        }

    @classmethod
    def get_from_dict(cls, data: dict, league: League) -> "Season":
        """Restore a Season from serialized data."""
        season = cls(league)
        season.current_round = data["current_round"]

        # Restore rounds with UUID objects
        season.rounds = []
        for rnd in data["rounds"]:
            season.rounds.append([
                (uuid.UUID(home_id), uuid.UUID(away_id))
                for home_id, away_id in rnd
            ])

        # Restore results with UUID objects
        season.results = []
        for round_data in data["results"]:
            matches = []
            for m in round_data["matches"]:
                matches.append({
                    "home": uuid.UUID(m["home"]),
                    "away": uuid.UUID(m["away"]),
                    "home_goals": m["home_goals"],
                    "away_goals": m["away_goals"],
                })
            season.results.append({
                "round": round_data["round"],
                "matches": matches,
            })

        return season
