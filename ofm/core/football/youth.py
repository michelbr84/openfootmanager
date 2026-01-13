import random
from .player import PlayerTeam

class YouthAcademy:
    def __init__(self):
        self.level = 1
        self.prospects: list[PlayerTeam] = []

    def upgrade(self):
        self.level += 1

    def generate_prospects(self):
        # Simplified prospect generation
        count = random.randint(1, 3)
        for _ in range(count):
            # Create a placeholder player
            # In real code we would call PlayerGenerator
            pass
