from dataclasses import dataclass
from .game_state import GameState

@dataclass
class VisualizerState:
    ball_position: tuple[float, float]
    player_positions: dict[str, tuple[float, float]]

class MatchVisualizer:
    def __init__(self):
        # This would interface with a 3D engine or canvas
        pass

    def get_frame_for_state(self, game_state: GameState) -> VisualizerState:
        # returns dummy positions
        return VisualizerState((50.0, 30.0), {})
