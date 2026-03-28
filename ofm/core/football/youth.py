import random
import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

from .player import PlayerTeam


@dataclass
class YouthProspect:
    player_dict: dict
    scouted_date: datetime.date
    development_score: float
    promoted: bool = False

    @property
    def name(self) -> str:
        return f"{self.player_dict.get('first_name', '')} {self.player_dict.get('last_name', '')}".strip()

    @property
    def age(self) -> int:
        dob = datetime.datetime.strptime(self.player_dict["dob"], "%Y-%m-%d").date()
        today = datetime.date.today()
        age = today.year - dob.year
        if (today.month, today.day) < (dob.month, dob.day):
            age -= 1
        return age

    @property
    def overall(self) -> int:
        attrs = self.player_dict.get("attributes", {})
        all_vals = []
        for group in attrs.values():
            if isinstance(group, dict):
                all_vals.extend(group.values())
        if not all_vals:
            return 0
        return int(sum(all_vals) / len(all_vals))

    @property
    def potential_skill(self) -> int:
        return self.player_dict.get("potential_skill", 0)

    def serialize(self) -> dict:
        return {
            "player_dict": self.player_dict,
            "scouted_date": self.scouted_date.isoformat(),
            "development_score": self.development_score,
            "promoted": self.promoted,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "YouthProspect":
        return cls(
            player_dict=data["player_dict"],
            scouted_date=datetime.date.fromisoformat(data["scouted_date"]),
            development_score=data["development_score"],
            promoted=data.get("promoted", False),
        )


# Attribute group keys matching the PlayerAttributes serialize format
_ATTR_GROUPS = {
    "offensive": ["shot_power", "shot_accuracy", "free_kick", "penalty", "positioning"],
    "defensive": ["tackling", "interception", "positioning"],
    "physical": ["strength", "aggression", "endurance"],
    "intelligence": ["vision", "passing", "crossing", "ball_control", "dribbling", "skills", "team_work"],
    "gk": ["reflexes", "jumping", "positioning", "penalty"],
}


class YouthAcademy:
    def __init__(self, level: int = 1):
        self.level: int = max(1, min(level, 5))
        self.prospects: list[YouthProspect] = []

    @property
    def max_prospects(self) -> int:
        return self.level * 3

    def upgrade(self):
        """Increase academy level, capped at 5."""
        if self.level < 5:
            self.level += 1

    def generate_prospects(
        self,
        settings,
        amount: int = None,
    ) -> list[YouthProspect]:
        """
        Generate young player prospects using PlayerGenerator.
        Amount defaults to 1-3 based on academy level.
        Returns list of newly created YouthProspect objects.
        """
        from ..db.generators import PlayerGenerator

        if amount is None:
            amount = random.randint(1, min(3, self.level))

        # Cap to not exceed max_prospects
        available_slots = self.max_prospects - len(
            [p for p in self.prospects if not p.promoted]
        )
        amount = min(amount, max(0, available_slots))

        if amount <= 0:
            return []

        # Create a PlayerGenerator with youth age range
        player_gen = PlayerGenerator(
            settings,
            today=datetime.date.today(),
            max_age=19,
            min_age=16,
        )

        player_gen.generate(amount)
        player_dicts = player_gen.get_players_dictionaries()

        new_prospects = []
        for pdict in player_dicts:
            # Scale attributes lower for youth (multiply by 0.4-0.7)
            scale = random.uniform(0.4, 0.7)
            attrs = pdict.get("attributes", {})
            for group_name, group_attrs in attrs.items():
                if isinstance(group_attrs, dict):
                    for attr_name in group_attrs:
                        original = group_attrs[attr_name]
                        scaled = max(25, int(original * scale))
                        group_attrs[attr_name] = scaled

            # Set higher potential_skill based on academy level
            potential = 70 + self.level * 5 + random.randint(0, 10)
            potential = min(potential, 99)
            pdict["potential_skill"] = potential

            # Development score starts based on current attributes vs potential
            dev_score = random.uniform(0.3, 0.7)

            prospect = YouthProspect(
                player_dict=pdict,
                scouted_date=datetime.date.today(),
                development_score=round(dev_score, 2),
            )
            self.prospects.append(prospect)
            new_prospects.append(prospect)

        return new_prospects

    def develop_prospects(self):
        """
        Develop all non-promoted prospects. Each gains +1-3 in random attributes.
        Should be called weekly or monthly during the season.
        """
        for prospect in self.prospects:
            if prospect.promoted:
                continue

            attrs = prospect.player_dict.get("attributes", {})
            potential = prospect.player_dict.get("potential_skill", 70)

            # Pick 2-4 random attributes to improve
            all_attrs = []
            for group_name, attr_list in _ATTR_GROUPS.items():
                for attr_name in attr_list:
                    if group_name in attrs and attr_name in attrs[group_name]:
                        all_attrs.append((group_name, attr_name))

            if not all_attrs:
                continue

            count = random.randint(2, 4)
            chosen = random.sample(all_attrs, min(count, len(all_attrs)))

            for group_name, attr_name in chosen:
                current = attrs[group_name][attr_name]
                # Only improve if below a ceiling derived from potential
                ceiling = min(potential, 99)
                if current < ceiling:
                    gain = random.randint(1, 3)
                    attrs[group_name][attr_name] = min(current + gain, ceiling)

            # Update development score based on growth
            prospect.development_score = min(
                1.0,
                round(prospect.development_score + random.uniform(0.01, 0.05), 2),
            )

    def promote_prospect(self, prospect_index: int) -> dict:
        """
        Mark a prospect as promoted and return the player_dict
        for adding to the main squad.
        Raises IndexError if index is out of range.
        """
        if prospect_index < 0 or prospect_index >= len(self.prospects):
            raise IndexError(f"Prospect index {prospect_index} out of range")

        prospect = self.prospects[prospect_index]
        if prospect.promoted:
            raise ValueError(f"Prospect '{prospect.name}' is already promoted")

        prospect.promoted = True
        return prospect.player_dict

    def release_prospect(self, prospect_index: int):
        """Remove a prospect from the academy."""
        if prospect_index < 0 or prospect_index >= len(self.prospects):
            raise IndexError(f"Prospect index {prospect_index} out of range")
        self.prospects.pop(prospect_index)

    def scout_report(self, prospect: YouthProspect) -> str:
        """Generate a text description of a prospect's potential."""
        potential = prospect.potential_skill
        dev = prospect.development_score

        if potential >= 90:
            potential_desc = "Generational talent"
        elif potential >= 85:
            potential_desc = "World-class potential"
        elif potential >= 80:
            potential_desc = "Excellent potential"
        elif potential >= 75:
            potential_desc = "Good potential"
        else:
            potential_desc = "Decent potential"

        if dev >= 0.8:
            dev_desc = "developing rapidly"
        elif dev >= 0.5:
            dev_desc = "progressing well"
        else:
            dev_desc = "still raw, needs time"

        positions = prospect.player_dict.get("positions", [])
        pos_names = {1: "GK", 2: "DF", 3: "MF", 4: "FW"}
        pos_str = "/".join(pos_names.get(p, "?") for p in positions) if positions else "Unknown"

        lines = [
            f"Scout Report: {prospect.name}",
            f"Age: {prospect.age} | Position: {pos_str}",
            f"Current Overall: {prospect.overall} | Potential: {potential}",
            f"Assessment: {potential_desc}, {dev_desc}",
            f"Scouted: {prospect.scouted_date.isoformat()}",
            f"Development Score: {dev:.0%}",
        ]

        # Highlight top attributes
        attrs = prospect.player_dict.get("attributes", {})
        top_attrs = []
        for group_name, group_data in attrs.items():
            if isinstance(group_data, dict):
                for attr_name, val in group_data.items():
                    top_attrs.append((f"{group_name}.{attr_name}", val))
        top_attrs.sort(key=lambda x: x[1], reverse=True)
        if top_attrs:
            top_3 = top_attrs[:3]
            lines.append(
                "Key Strengths: " + ", ".join(f"{n} ({v})" for n, v in top_3)
            )

        return "\n".join(lines)

    def serialize(self) -> dict:
        return {
            "level": self.level,
            "prospects": [p.serialize() for p in self.prospects],
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "YouthAcademy":
        academy = cls(level=data.get("level", 1))
        academy.prospects = [
            YouthProspect.get_from_dict(p) for p in data.get("prospects", [])
        ]
        return academy
