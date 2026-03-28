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
import uuid
from dataclasses import dataclass, field

from .career import CareerManager


@dataclass
class Manager:
    manager_id: uuid.UUID
    first_name: str
    last_name: str
    birth_date: datetime.date
    tactical_ability: int = 10
    man_management: int = 10
    youth_development: int = 10
    discipline: int = 10
    motivation: int = 10
    career: CareerManager = field(default_factory=CareerManager)

    def get_overall(self) -> int:
        attributes = [
            self.tactical_ability,
            self.man_management,
            self.youth_development,
            self.discipline,
            self.motivation,
        ]
        return round(sum(attributes) / len(attributes))

    def serialize(self) -> dict:
        return {
            "manager_id": self.manager_id.int,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "birth_date": self.birth_date.strftime("%Y-%m-%d"),
            "tactical_ability": self.tactical_ability,
            "man_management": self.man_management,
            "youth_development": self.youth_development,
            "discipline": self.discipline,
            "motivation": self.motivation,
            "career": self.career.serialize(),
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "Manager":
        career = CareerManager.get_from_dict(data["career"]) if "career" in data else CareerManager()
        return cls(
            manager_id=uuid.UUID(int=data["manager_id"]),
            first_name=data["first_name"],
            last_name=data["last_name"],
            birth_date=datetime.datetime.strptime(data["birth_date"], "%Y-%m-%d").date(),
            tactical_ability=data.get("tactical_ability", 10),
            man_management=data.get("man_management", 10),
            youth_development=data.get("youth_development", 10),
            discipline=data.get("discipline", 10),
            motivation=data.get("motivation", 10),
            career=career,
        )
