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
import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Trophy:
    name: str
    season: str
    club_name: str
    date: datetime.date

    def serialize(self) -> dict:
        return {
            "name": self.name,
            "season": self.season,
            "club_name": self.club_name,
            "date": self.date.strftime("%Y-%m-%d"),
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "Trophy":
        return cls(
            name=data["name"],
            season=data["season"],
            club_name=data["club_name"],
            date=datetime.datetime.strptime(data["date"], "%Y-%m-%d").date(),
        )


@dataclass
class JobRecord:
    club_name: str
    start_date: datetime.date
    end_date: Optional[datetime.date] = None
    matches: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0

    def serialize(self) -> dict:
        return {
            "club_name": self.club_name,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d") if self.end_date else None,
            "matches": self.matches,
            "wins": self.wins,
            "draws": self.draws,
            "losses": self.losses,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "JobRecord":
        end_date = None
        if data.get("end_date"):
            end_date = datetime.datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        return cls(
            club_name=data["club_name"],
            start_date=datetime.datetime.strptime(data["start_date"], "%Y-%m-%d").date(),
            end_date=end_date,
            matches=data.get("matches", 0),
            wins=data.get("wins", 0),
            draws=data.get("draws", 0),
            losses=data.get("losses", 0),
        )


class CareerManager:
    def __init__(self):
        self.trophies: list[Trophy] = []
        self.job_history: list[JobRecord] = []
        self.current_job: Optional[JobRecord] = None
        self.national_team_job: Optional[str] = None
        self.reputation: int = 30

    def add_trophy(
        self, name: str, season: str, club_name: str, date: datetime.date
    ) -> Trophy:
        trophy = Trophy(name=name, season=season, club_name=club_name, date=date)
        self.trophies.append(trophy)
        self.update_reputation(random.randint(5, 15))
        return trophy

    def start_job(self, club_name: str, start_date: datetime.date) -> JobRecord:
        if self.current_job is not None:
            self.end_job(start_date)
        job = JobRecord(club_name=club_name, start_date=start_date)
        self.current_job = job
        return job

    def end_job(self, end_date: datetime.date) -> Optional[JobRecord]:
        if self.current_job is None:
            return None
        self.current_job.end_date = end_date
        self.job_history.append(self.current_job)
        finished_job = self.current_job
        self.current_job = None
        return finished_job

    def record_match_result(self, won: bool, drawn: bool) -> None:
        if self.current_job is None:
            return
        self.current_job.matches += 1
        if won:
            self.current_job.wins += 1
        elif drawn:
            self.current_job.draws += 1
        else:
            self.current_job.losses += 1

    def get_win_rate(self) -> float:
        if self.current_job is None or self.current_job.matches == 0:
            return 0.0
        return (self.current_job.wins / self.current_job.matches) * 100.0

    def update_reputation(self, change: int) -> None:
        self.reputation = max(0, min(100, self.reputation + change))

    def get_career_summary(self) -> dict:
        all_jobs = list(self.job_history)
        if self.current_job is not None:
            all_jobs.append(self.current_job)

        total_matches = sum(j.matches for j in all_jobs)
        total_wins = sum(j.wins for j in all_jobs)
        total_draws = sum(j.draws for j in all_jobs)
        total_losses = sum(j.losses for j in all_jobs)

        return {
            "total_matches": total_matches,
            "total_wins": total_wins,
            "total_draws": total_draws,
            "total_losses": total_losses,
            "total_trophies": len(self.trophies),
            "clubs_managed": len(all_jobs),
            "reputation": self.reputation,
            "win_rate": (total_wins / total_matches * 100.0) if total_matches > 0 else 0.0,
        }

    def serialize(self) -> dict:
        return {
            "trophies": [t.serialize() for t in self.trophies],
            "job_history": [j.serialize() for j in self.job_history],
            "current_job": self.current_job.serialize() if self.current_job else None,
            "national_team_job": self.national_team_job,
            "reputation": self.reputation,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "CareerManager":
        manager = cls()
        manager.trophies = [
            Trophy.get_from_dict(t) for t in data.get("trophies", [])
        ]
        manager.job_history = [
            JobRecord.get_from_dict(j) for j in data.get("job_history", [])
        ]
        if data.get("current_job"):
            manager.current_job = JobRecord.get_from_dict(data["current_job"])
        manager.national_team_job = data.get("national_team_job")
        manager.reputation = data.get("reputation", 30)
        return manager
