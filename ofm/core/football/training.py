import random
from .player import PlayerTeam

class TrainingFocus:
    GENERAL = "General"
    ATTACK = "Attack"
    DEFENSE = "Defense"
    FITNESS = "Fitness"

class TrainingManager:
    def __init__(self):
        pass

    def train_squad(self, squad: list[PlayerTeam], focus: str = TrainingFocus.GENERAL):
        """
        Simulate a training session for the squad.
        """
        for player in squad:
            self._train_player(player, focus)

    def _train_player(self, player: PlayerTeam, focus: str):
        # improvement_chance depends on age, potential, etc.
        # This is a simplified logic.
        curr_ability = player.details.overall
        potential = player.details.potential
        
        if curr_ability >= potential:
            return

        improvement = 0
        dice = random.random()

        if focus == TrainingFocus.FITNESS:
            # Recover stamina or improve physicals
            pass
        elif focus == TrainingFocus.ATTACK:
            if dice < 0.1: # 10% chance to improve
                improvement = 1
        elif focus == TrainingFocus.DEFENSE:
            if dice < 0.1:
                improvement = 1
        else: # General
            if dice < 0.05:
                improvement = 1
        
        # In a real implementation, we would increase specific attributes.
        # For now, we might just boost 'overall' artificially or pick a random attribute if we had access to modify them directly easily.
        # Since 'overall' is calculated, we should increase attributes.
        
        if improvement > 0:
            # Pick a random attribute to improve
            attr_name = random.choice(list(player.attributes.__dict__.keys()))
            if not attr_name.startswith('_'):
                current_val = getattr(player.attributes, attr_name)
                if isinstance(current_val, int) and current_val < 99:
                     setattr(player.attributes, attr_name, current_val + 1)
