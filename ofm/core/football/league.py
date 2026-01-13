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

    def generate_fixtures(self):
        """
        Simple round-robin fixture generation.
        """
        if not self.clubs:
            return

        # Simplified algorithm
        # In a real game, this is complex.
        pass

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

    def get_standings(self) -> list[LeagueTableEntry]:
        entries = list(self.table.values())
        # Sort by points, then goal difference, then goals for
        entries.sort(key=lambda x: (x.points, x.goal_difference, x.goals_for), reverse=True)
        return entries
