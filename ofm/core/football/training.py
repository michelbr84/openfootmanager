import random
import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional

from .player import PlayerTeam


class TrainingFocus(Enum):
    GENERAL = "General"
    ATTACK = "Attack"
    DEFENSE = "Defense"
    FITNESS = "Fitness"


# Attribute groups by training focus
OFFENSIVE_ATTRS = ["shot_power", "shot_accuracy", "free_kick", "penalty", "positioning"]
DEFENSIVE_ATTRS = ["tackling", "interception", "positioning"]
PHYSICAL_ATTRS = ["strength", "aggression", "endurance"]
INTELLIGENCE_ATTRS = ["vision", "passing", "crossing", "ball_control", "dribbling", "skills", "team_work"]
GK_ATTRS = ["reflexes", "jumping", "positioning", "penalty"]

# Map attribute names to their sub-attribute group on PlayerAttributes
ATTR_GROUP_MAP = {}
for attr in OFFENSIVE_ATTRS:
    ATTR_GROUP_MAP.setdefault(("offensive", attr), True)
for attr in DEFENSIVE_ATTRS:
    ATTR_GROUP_MAP.setdefault(("defensive", attr), True)
for attr in PHYSICAL_ATTRS:
    ATTR_GROUP_MAP.setdefault(("physical", attr), True)
for attr in INTELLIGENCE_ATTRS:
    ATTR_GROUP_MAP.setdefault(("intelligence", attr), True)
for attr in GK_ATTRS:
    ATTR_GROUP_MAP.setdefault(("gk", attr), True)

ALL_TRAINABLE = list(ATTR_GROUP_MAP.keys())


def _get_age(player: PlayerTeam) -> int:
    """Calculate player age from date of birth."""
    dob = player.details.dob
    today = datetime.date.today()
    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age


def _get_age_factor(age: int) -> float:
    """Younger players improve faster, older players improve slower."""
    if age < 20:
        return 2.0
    elif age < 24:
        return 1.5
    elif age <= 28:
        return 1.0
    elif age <= 30:
        return 0.5
    else:
        return 0.3


def _get_sub_attr(player: PlayerTeam, group: str, attr_name: str) -> int:
    """Get the value of a specific sub-attribute."""
    group_obj = getattr(player.details.attributes, group)
    return getattr(group_obj, attr_name)


def _set_sub_attr(player: PlayerTeam, group: str, attr_name: str, value: int):
    """Set the value of a specific sub-attribute, capped at 99."""
    group_obj = getattr(player.details.attributes, group)
    setattr(group_obj, attr_name, min(value, 99))


@dataclass
class TrainingSession:
    date: datetime.date
    focus: TrainingFocus
    intensity: float
    results: list = field(default_factory=list)

    def serialize(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "focus": self.focus.value,
            "intensity": self.intensity,
            "results": self.results,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "TrainingSession":
        return cls(
            date=datetime.date.fromisoformat(data["date"]),
            focus=TrainingFocus(data["focus"]),
            intensity=data["intensity"],
            results=data.get("results", []),
        )


class TrainingManager:
    def __init__(self):
        self.sessions_history: list[TrainingSession] = []

    def train_squad(
        self,
        squad: list[PlayerTeam],
        focus: TrainingFocus = TrainingFocus.GENERAL,
        intensity: float = 0.8,
    ) -> TrainingSession:
        """
        Simulate a training session for the entire squad.
        Returns a TrainingSession with per-player results.
        """
        intensity = max(0.5, min(1.0, intensity))
        session = TrainingSession(
            date=datetime.date.today(),
            focus=focus,
            intensity=intensity,
        )

        for player in squad:
            if player.details.is_injured:
                session.results.append({
                    "player_name": f"{player.details.first_name} {player.details.last_name}",
                    "player_id": player.details.player_id.int,
                    "changes": {},
                    "skipped": True,
                    "reason": "injured",
                })
                continue

            changes = self._train_player(player, focus, intensity)
            session.results.append({
                "player_name": f"{player.details.first_name} {player.details.last_name}",
                "player_id": player.details.player_id.int,
                "changes": changes,
                "skipped": False,
                "reason": "",
            })

        self.sessions_history.append(session)
        return session

    def _train_player(
        self,
        player: PlayerTeam,
        focus: TrainingFocus,
        intensity: float,
    ) -> dict:
        """
        Train a single player. Improves attributes based on focus, intensity,
        age, and room to grow (overall vs potential_skill).
        Returns dict of {attribute_name: change_amount}.
        """
        changes = {}

        # Check room to grow
        best_pos = player.details.get_best_position()
        current_overall = player.details.attributes.get_overall(best_pos)
        potential = player.details.potential_skill

        if current_overall >= potential:
            return changes

        age = _get_age(player)
        age_factor = _get_age_factor(age)

        # Base probability of improvement, scaled by intensity and age
        base_prob = 0.3 * intensity * age_factor

        if focus == TrainingFocus.FITNESS:
            self._train_fitness(player, intensity, age_factor, changes)
        elif focus == TrainingFocus.ATTACK:
            self._train_attribute_group(
                player, "offensive", OFFENSIVE_ATTRS, base_prob, 1, 2, changes
            )
        elif focus == TrainingFocus.DEFENSE:
            self._train_attribute_group(
                player, "defensive", DEFENSIVE_ATTRS, base_prob, 1, 2, changes
            )
        elif focus == TrainingFocus.GENERAL:
            self._train_general(player, base_prob, changes)

        return changes

    def _train_attribute_group(
        self,
        player: PlayerTeam,
        group: str,
        attrs: list[str],
        probability: float,
        min_attrs: int,
        max_attrs: int,
        changes: dict,
    ):
        """Train specific attribute group with chance of improving min_attrs to max_attrs."""
        count = random.randint(min_attrs, max_attrs)
        chosen = random.sample(attrs, min(count, len(attrs)))

        for attr_name in chosen:
            if random.random() < probability:
                current = _get_sub_attr(player, group, attr_name)
                if current < 99:
                    gain = 1
                    _set_sub_attr(player, group, attr_name, current + gain)
                    key = f"{group}.{attr_name}"
                    changes[key] = gain

    def _train_fitness(
        self,
        player: PlayerTeam,
        intensity: float,
        age_factor: float,
        changes: dict,
    ):
        """Fitness training: improve physical attributes and fitness value."""
        prob = 0.5 * intensity * age_factor

        # Physical attributes: +2-3 to strength/endurance
        phys_attrs = ["strength", "endurance"]
        for attr_name in phys_attrs:
            if random.random() < prob:
                current = _get_sub_attr(player, "physical", attr_name)
                gain = random.randint(2, 3)
                new_val = min(current + gain, 99)
                actual_gain = new_val - current
                if actual_gain > 0:
                    _set_sub_attr(player, "physical", attr_name, new_val)
                    changes[f"physical.{attr_name}"] = actual_gain

        # Fitness boost: +1 to 5
        if random.random() < prob:
            fitness_gain = random.randint(1, 5) * intensity
            new_fitness = min(player.details.fitness + fitness_gain, 100.0)
            actual_gain = round(new_fitness - player.details.fitness, 2)
            if actual_gain > 0:
                player.details.fitness = round(new_fitness, 2)
                changes["fitness"] = actual_gain

    def _train_general(
        self, player: PlayerTeam, probability: float, changes: dict
    ):
        """General training: pick 1-2 random attributes from any group."""
        count = random.randint(1, 2)
        chosen = random.sample(ALL_TRAINABLE, min(count, len(ALL_TRAINABLE)))

        for group, attr_name in chosen:
            if random.random() < probability:
                current = _get_sub_attr(player, group, attr_name)
                if current < 99:
                    _set_sub_attr(player, group, attr_name, current + 1)
                    changes[f"{group}.{attr_name}"] = 1

    def get_training_report(self, session: TrainingSession) -> str:
        """Generate a formatted summary of a training session."""
        lines = [
            f"Training Report - {session.date.isoformat()}",
            f"Focus: {session.focus.value} | Intensity: {session.intensity:.0%}",
            "-" * 50,
        ]

        improved_count = 0
        skipped_count = 0

        for result in session.results:
            name = result["player_name"]
            if result.get("skipped"):
                lines.append(f"  {name}: Skipped ({result.get('reason', 'N/A')})")
                skipped_count += 1
                continue

            changes = result.get("changes", {})
            if changes:
                improved_count += 1
                change_strs = [f"{k} +{v}" for k, v in changes.items()]
                lines.append(f"  {name}: {', '.join(change_strs)}")
            else:
                lines.append(f"  {name}: No improvement")

        lines.append("-" * 50)
        lines.append(
            f"Summary: {improved_count} improved, "
            f"{skipped_count} skipped, "
            f"{len(session.results) - improved_count - skipped_count} unchanged"
        )
        return "\n".join(lines)

    def serialize(self) -> dict:
        return {
            "sessions_history": [s.serialize() for s in self.sessions_history],
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "TrainingManager":
        manager = cls()
        manager.sessions_history = [
            TrainingSession.get_from_dict(s)
            for s in data.get("sessions_history", [])
        ]
        return manager
