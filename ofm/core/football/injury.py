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
from enum import Enum, auto
from uuid import UUID


class PlayerInjury(Enum):
    NO_INJURY = auto()
    LIGHT_INJURY = auto()
    MEDIUM_INJURY = auto()
    SEVERE_INJURY = auto()
    CAREER_ENDING_INJURY = auto()


INJURY_DESCRIPTIONS: dict[PlayerInjury, list[tuple[str, int, int]]] = {
    PlayerInjury.LIGHT_INJURY: [
        ("Minor knock", 3, 7),
        ("Slight muscle strain", 5, 10),
        ("Bruised shin", 2, 5),
    ],
    PlayerInjury.MEDIUM_INJURY: [
        ("Hamstring strain", 14, 28),
        ("Ankle sprain", 10, 21),
        ("Calf injury", 14, 25),
    ],
    PlayerInjury.SEVERE_INJURY: [
        ("ACL tear", 120, 270),
        ("Broken leg", 90, 180),
        ("Torn ligament", 60, 150),
    ],
    PlayerInjury.CAREER_ENDING_INJURY: [
        ("Career-ending knee injury", 999, 999),
    ],
}


@dataclass
class InjuryDetail:
    injury_type: PlayerInjury
    description: str
    recovery_days: int
    date_injured: datetime.date
    player_id: UUID

    def serialize(self) -> dict:
        return {
            "injury_type": self.injury_type.value,
            "description": self.description,
            "recovery_days": self.recovery_days,
            "date_injured": self.date_injured.strftime("%Y-%m-%d"),
            "player_id": self.player_id.int,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "InjuryDetail":
        return cls(
            injury_type=PlayerInjury(data["injury_type"]),
            description=data["description"],
            recovery_days=data["recovery_days"],
            date_injured=datetime.datetime.strptime(data["date_injured"], "%Y-%m-%d").date(),
            player_id=UUID(int=data["player_id"]),
        )


class InjuryManager:
    def __init__(self):
        self.active_injuries: list[InjuryDetail] = []
        self.injury_history: list[InjuryDetail] = []

    def generate_injury(
        self, player_id: UUID, injury_type: PlayerInjury, date: datetime.date
    ) -> InjuryDetail:
        if injury_type == PlayerInjury.NO_INJURY:
            raise ValueError("Cannot generate an injury with NO_INJURY type")

        descriptions = INJURY_DESCRIPTIONS[injury_type]
        description, min_days, max_days = random.choice(descriptions)
        recovery_days = random.randint(min_days, max_days)

        injury = InjuryDetail(
            injury_type=injury_type,
            description=description,
            recovery_days=recovery_days,
            date_injured=date,
            player_id=player_id,
        )
        self.active_injuries.append(injury)
        return injury

    def check_recovery(self, current_date: datetime.date) -> list[UUID]:
        recovered_ids: list[UUID] = []
        still_injured: list[InjuryDetail] = []

        for injury in self.active_injuries:
            days_elapsed = (current_date - injury.date_injured).days
            if days_elapsed >= injury.recovery_days:
                recovered_ids.append(injury.player_id)
                self.injury_history.append(injury)
            else:
                still_injured.append(injury)

        self.active_injuries = still_injured
        return recovered_ids

    def get_player_injury(self, player_id: UUID) -> InjuryDetail | None:
        for injury in self.active_injuries:
            if injury.player_id == player_id:
                return injury
        return None

    def is_player_injured(self, player_id: UUID) -> bool:
        return self.get_player_injury(player_id) is not None

    def get_return_date(self, injury: InjuryDetail) -> datetime.date:
        return injury.date_injured + datetime.timedelta(days=injury.recovery_days)

    def serialize(self) -> dict:
        return {
            "active_injuries": [inj.serialize() for inj in self.active_injuries],
            "injury_history": [inj.serialize() for inj in self.injury_history],
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "InjuryManager":
        manager = cls()
        manager.active_injuries = [
            InjuryDetail.get_from_dict(inj) for inj in data.get("active_injuries", [])
        ]
        manager.injury_history = [
            InjuryDetail.get_from_dict(inj) for inj in data.get("injury_history", [])
        ]
        return manager
