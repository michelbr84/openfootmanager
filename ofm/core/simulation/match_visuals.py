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
from dataclasses import dataclass, field
from typing import Optional

from .event_type import EventType
from .event import EventOutcome


@dataclass
class MatchFrame:
    """A single frame of match visualization data.

    Positions are normalized to a 0-100 coordinate system for flexible rendering.
    """
    timestamp: float
    ball_x: float
    ball_y: float
    player_positions: dict[str, tuple[float, float]]
    event_text: Optional[str] = None


class MatchAnimator:
    """Generates animation frames from simulation events.

    This class produces visualization data (MatchFrame sequences) from
    match simulation events. It does not handle rendering -- that is the
    responsibility of the UI layer (tkinter).
    """

    # Mapping from PitchPosition-like zones to (x, y) center coordinates
    # on a 0-100 normalized pitch. Home attacks left-to-right.
    PITCH_ZONE_COORDS: dict[str, tuple[float, float]] = {
        "DEF_BOX": (8, 50),
        "DEF_LEFT": (15, 20),
        "DEF_RIGHT": (15, 80),
        "DEF_MIDFIELD_CENTER": (25, 50),
        "DEF_MIDFIELD_LEFT": (25, 20),
        "DEF_MIDFIELD_RIGHT": (25, 80),
        "MIDFIELD_LEFT": (45, 20),
        "MIDFIELD_CENTER": (50, 50),
        "MIDFIELD_RIGHT": (45, 80),
        "OFF_MIDFIELD_CENTER": (70, 50),
        "OFF_MIDFIELD_LEFT": (70, 20),
        "OFF_MIDFIELD_RIGHT": (70, 80),
        "OFF_LEFT": (85, 20),
        "OFF_RIGHT": (85, 80),
        "OFF_BOX": (92, 50),
    }

    # Formation line x-positions for home (left half) and away (right half)
    # Each formation string maps to a list of (line_x, count) tuples
    FORMATION_LINE_POSITIONS: dict[str, list[tuple[float, int]]] = {
        "3-4-3": [(15, 3), (35, 4), (45, 3)],
        "3-5-2": [(15, 3), (35, 5), (45, 2)],
        "3-6-1": [(15, 3), (35, 6), (45, 1)],
        "4-4-2": [(15, 4), (35, 4), (45, 2)],
        "4-3-3": [(15, 4), (35, 3), (45, 3)],
        "4-5-1": [(15, 4), (35, 5), (45, 1)],
        "5-4-1": [(15, 5), (35, 4), (45, 1)],
        "5-3-2": [(15, 5), (35, 3), (45, 2)],
    }

    def generate_frames(
        self,
        events: list,
        formation_home,
        formation_away,
    ) -> list[MatchFrame]:
        """Generate a list of MatchFrames from simulation events.

        For each event, 3-5 frames are produced showing smooth transitions
        (ball movement, player runs, etc.). The number of frames depends on
        the event type.

        Args:
            events: List of SimulationEvent objects from the match simulation.
            formation_home: Formation object for the home team.
            formation_away: Formation object for the away team.

        Returns:
            Ordered list of MatchFrame objects representing the match animation.
        """
        frames: list[MatchFrame] = []
        home_positions = self.get_player_base_positions(formation_home, is_home=True)
        away_positions = self.get_player_base_positions(formation_away, is_home=False)

        base_timestamp = 0.0

        for event in events:
            event_frames = self._generate_event_frames(
                event, home_positions, away_positions, base_timestamp
            )
            frames.extend(event_frames)
            if event_frames:
                base_timestamp = event_frames[-1].timestamp + 0.1

        return frames

    def get_player_base_positions(
        self,
        formation,
        is_home: bool,
    ) -> dict[str, tuple[float, float]]:
        """Calculate base positions for all players in a formation.

        Home team occupies the left half (x: 10-50), away team the right
        half (x: 50-90). The goalkeeper is placed at the edge, and formation
        lines are evenly distributed within the team's half.

        Args:
            formation: A Formation object with gk, df, mf, fw lists.
            is_home: True for home team (left half), False for away (right half).

        Returns:
            Dict mapping player name (str) to (x, y) position in 0-100 coords.
        """
        positions: dict[str, tuple[float, float]] = {}
        formation_str = formation.formation_string

        lines = self.FORMATION_LINE_POSITIONS.get(formation_str, [(15, 4), (35, 4), (45, 2)])

        # Place goalkeeper
        if formation.gk is not None:
            gk_name = str(formation.gk)
            if is_home:
                positions[gk_name] = (5.0, 50.0)
            else:
                positions[gk_name] = (95.0, 50.0)

        # Place outfield players by line
        player_groups = [formation.df, formation.mf, formation.fw]

        for line_idx, (line_x, _expected_count) in enumerate(lines):
            if line_idx >= len(player_groups):
                break

            group = player_groups[line_idx]
            if not group:
                continue

            if is_home:
                x = line_x
            else:
                x = 100.0 - line_x

            count = len(group)
            for i, player in enumerate(group):
                player_name = str(player)
                # Spread players evenly across y-axis (10-90 range)
                if count == 1:
                    y = 50.0
                else:
                    y = 15.0 + (70.0 * i / (count - 1))
                positions[player_name] = (x, y)

        return positions

    def _generate_event_frames(
        self,
        event,
        home_positions: dict[str, tuple[float, float]],
        away_positions: dict[str, tuple[float, float]],
        base_timestamp: float,
    ) -> list[MatchFrame]:
        """Generate frames for a single simulation event."""
        all_positions = {**home_positions, **away_positions}

        event_type = event.event_type
        attacker_name = str(event.attacking_player) if event.attacking_player else None
        defender_name = str(event.defending_player) if event.defending_player else None

        # Determine ball start and end positions from event context
        pitch_pos = event.state.position.name if event.state else "MIDFIELD_CENTER"
        zone_coords = self.PITCH_ZONE_COORDS.get(pitch_pos, (50.0, 50.0))

        if attacker_name and attacker_name in all_positions:
            start_pos = all_positions[attacker_name]
        else:
            start_pos = zone_coords

        if event_type == EventType.PASS:
            return self._generate_pass_frames(
                event, start_pos, all_positions, base_timestamp, attacker_name, defender_name
            )
        elif event_type == EventType.SHOT:
            return self._generate_shot_frames(
                event, start_pos, all_positions, base_timestamp, attacker_name
            )
        elif event_type == EventType.DRIBBLE:
            return self._generate_dribble_frames(
                event, start_pos, zone_coords, all_positions, base_timestamp, attacker_name
            )
        elif event_type == EventType.CROSS:
            return self._generate_cross_frames(
                event, start_pos, all_positions, base_timestamp, attacker_name
            )
        else:
            # Generic frames for other event types (fouls, free kicks, etc.)
            return self._generate_generic_frames(
                event, zone_coords, all_positions, base_timestamp
            )

    def _generate_pass_frames(
        self,
        event,
        start_pos: tuple[float, float],
        all_positions: dict[str, tuple[float, float]],
        base_timestamp: float,
        attacker_name: Optional[str],
        defender_name: Optional[str],
    ) -> list[MatchFrame]:
        """Generate 4 frames for a pass event: wind-up, ball in flight (x2), arrival."""
        frames: list[MatchFrame] = []
        num_frames = 4

        # Target is the defending player position (receiver in a pass) or a zone offset
        if defender_name and defender_name in all_positions:
            end_pos = all_positions[defender_name]
        else:
            end_pos = (start_pos[0] + 10, start_pos[1])

        event_text = self._build_event_text(event)

        for i in range(num_frames):
            t = i / (num_frames - 1)
            ball_x = self._lerp(start_pos[0], end_pos[0], t)
            ball_y = self._lerp(start_pos[1], end_pos[1], t)

            frame = MatchFrame(
                timestamp=base_timestamp + i * 0.25,
                ball_x=self._clamp(ball_x),
                ball_y=self._clamp(ball_y),
                player_positions=dict(all_positions),
                event_text=event_text if i == 0 else None,
            )
            frames.append(frame)

        return frames

    def _generate_shot_frames(
        self,
        event,
        start_pos: tuple[float, float],
        all_positions: dict[str, tuple[float, float]],
        base_timestamp: float,
        attacker_name: Optional[str],
    ) -> list[MatchFrame]:
        """Generate 5 frames for a shot event: wind-up, ball accelerating toward goal."""
        frames: list[MatchFrame] = []
        num_frames = 5

        # Determine which goal to shoot at based on attacker position
        if start_pos[0] < 50:
            goal_pos = (98.0, 50.0)
        else:
            goal_pos = (2.0, 50.0)

        event_text = self._build_event_text(event)

        for i in range(num_frames):
            t = i / (num_frames - 1)
            # Ease-in for acceleration effect
            t_eased = t * t
            ball_x = self._lerp(start_pos[0], goal_pos[0], t_eased)
            ball_y = self._lerp(start_pos[1], goal_pos[1], t_eased)

            frame = MatchFrame(
                timestamp=base_timestamp + i * 0.2,
                ball_x=self._clamp(ball_x),
                ball_y=self._clamp(ball_y),
                player_positions=dict(all_positions),
                event_text=event_text if i == 0 else None,
            )
            frames.append(frame)

        return frames

    def _generate_dribble_frames(
        self,
        event,
        start_pos: tuple[float, float],
        zone_coords: tuple[float, float],
        all_positions: dict[str, tuple[float, float]],
        base_timestamp: float,
        attacker_name: Optional[str],
    ) -> list[MatchFrame]:
        """Generate 3 frames for a dribble: player moving with the ball."""
        frames: list[MatchFrame] = []
        num_frames = 3

        # Dribble moves forward in the attacking direction
        dx = 8.0 if start_pos[0] < 50 else -8.0
        end_pos = (start_pos[0] + dx, start_pos[1])

        event_text = self._build_event_text(event)

        for i in range(num_frames):
            t = i / (num_frames - 1)
            ball_x = self._lerp(start_pos[0], end_pos[0], t)
            ball_y = self._lerp(start_pos[1], end_pos[1], t)

            # Move the attacker along with the ball
            positions = dict(all_positions)
            if attacker_name and attacker_name in positions:
                positions[attacker_name] = (self._clamp(ball_x), self._clamp(ball_y))

            frame = MatchFrame(
                timestamp=base_timestamp + i * 0.3,
                ball_x=self._clamp(ball_x),
                ball_y=self._clamp(ball_y),
                player_positions=positions,
                event_text=event_text if i == 0 else None,
            )
            frames.append(frame)

        return frames

    def _generate_cross_frames(
        self,
        event,
        start_pos: tuple[float, float],
        all_positions: dict[str, tuple[float, float]],
        base_timestamp: float,
        attacker_name: Optional[str],
    ) -> list[MatchFrame]:
        """Generate 5 frames for a cross: ball arcing from the wing toward the box."""
        frames: list[MatchFrame] = []
        num_frames = 5

        # Cross goes from wide position toward the center of the box
        if start_pos[0] < 50:
            end_pos = (88.0, 50.0)
        else:
            end_pos = (12.0, 50.0)

        event_text = self._build_event_text(event)

        for i in range(num_frames):
            t = i / (num_frames - 1)
            ball_x = self._lerp(start_pos[0], end_pos[0], t)
            ball_y = self._lerp(start_pos[1], end_pos[1], t)

            # Add an arc to the y-coordinate to simulate the ball curving
            arc_height = 10.0 * (4 * t * (1 - t))  # Parabolic arc peaking at t=0.5
            ball_y = ball_y - arc_height  # Shift upward for arc

            frame = MatchFrame(
                timestamp=base_timestamp + i * 0.2,
                ball_x=self._clamp(ball_x),
                ball_y=self._clamp(ball_y),
                player_positions=dict(all_positions),
                event_text=event_text if i == 0 else None,
            )
            frames.append(frame)

        return frames

    def _generate_generic_frames(
        self,
        event,
        zone_coords: tuple[float, float],
        all_positions: dict[str, tuple[float, float]],
        base_timestamp: float,
    ) -> list[MatchFrame]:
        """Generate 3 generic frames for events like fouls or set pieces."""
        event_text = self._build_event_text(event)
        frames = []
        for i in range(3):
            frame = MatchFrame(
                timestamp=base_timestamp + i * 0.3,
                ball_x=self._clamp(zone_coords[0]),
                ball_y=self._clamp(zone_coords[1]),
                player_positions=dict(all_positions),
                event_text=event_text if i == 0 else None,
            )
            frames.append(frame)
        return frames

    def _build_event_text(self, event) -> str:
        """Build descriptive text for an event."""
        parts = []
        if hasattr(event, "event_type"):
            parts.append(event.event_type.name)
        if event.attacking_player:
            parts.append(str(event.attacking_player))
        if event.outcome:
            parts.append(event.outcome.name)
        return " - ".join(parts) if parts else "Play"

    @staticmethod
    def _lerp(a: float, b: float, t: float) -> float:
        """Linear interpolation between a and b by factor t."""
        return a + (b - a) * t

    @staticmethod
    def _clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
        """Clamp a value to the given range."""
        return max(min_val, min(max_val, value))


class HeatMapGenerator:
    """Accumulates player position data during a match and produces heat map grids.

    The pitch is divided into a 10x10 grid. Each cell records how many times
    a player was recorded in that zone.
    """

    GRID_SIZE = 10

    def __init__(self):
        self._positions: dict[str, list[tuple[float, float]]] = {}

    def record_position(self, player_name: str, x: float, y: float) -> None:
        """Record a player's position during the match.

        Args:
            player_name: Identifier for the player.
            x: X coordinate (0-100).
            y: Y coordinate (0-100).
        """
        if player_name not in self._positions:
            self._positions[player_name] = []
        self._positions[player_name].append((x, y))

    def get_heat_map(self, player_name: str) -> list[list[int]]:
        """Get a 10x10 heat map grid for a single player.

        Args:
            player_name: The player to generate the heat map for.

        Returns:
            10x10 grid where each cell is an integer intensity count.
        """
        grid = [[0] * self.GRID_SIZE for _ in range(self.GRID_SIZE)]
        positions = self._positions.get(player_name, [])

        for x, y in positions:
            col = min(int(x / (100.0 / self.GRID_SIZE)), self.GRID_SIZE - 1)
            row = min(int(y / (100.0 / self.GRID_SIZE)), self.GRID_SIZE - 1)
            grid[row][col] += 1

        return grid

    def get_team_heat_map(self, team_players: list[str]) -> list[list[int]]:
        """Get a combined 10x10 heat map for an entire team.

        Args:
            team_players: List of player names belonging to the team.

        Returns:
            10x10 grid with combined intensity values from all specified players.
        """
        combined = [[0] * self.GRID_SIZE for _ in range(self.GRID_SIZE)]

        for player_name in team_players:
            player_grid = self.get_heat_map(player_name)
            for row in range(self.GRID_SIZE):
                for col in range(self.GRID_SIZE):
                    combined[row][col] += player_grid[row][col]

        return combined

    def get_pass_map(self, passes: list[dict]) -> list[dict]:
        """Aggregate pass data into a pass map with counts.

        Args:
            passes: List of dicts with keys 'from_x', 'from_y', 'to_x', 'to_y'.

        Returns:
            List of dicts with from_x, from_y, to_x, to_y, count -- grouped
            by rounded grid zones to aggregate similar passes.
        """
        cell_size = 100.0 / self.GRID_SIZE
        aggregated: dict[tuple[int, int, int, int], int] = {}

        for p in passes:
            from_col = min(int(p["from_x"] / cell_size), self.GRID_SIZE - 1)
            from_row = min(int(p["from_y"] / cell_size), self.GRID_SIZE - 1)
            to_col = min(int(p["to_x"] / cell_size), self.GRID_SIZE - 1)
            to_row = min(int(p["to_y"] / cell_size), self.GRID_SIZE - 1)

            key = (from_col, from_row, to_col, to_row)
            aggregated[key] = aggregated.get(key, 0) + 1

        result = []
        for (fc, fr, tc, tr), count in aggregated.items():
            result.append(
                {
                    "from_x": (fc + 0.5) * cell_size,
                    "from_y": (fr + 0.5) * cell_size,
                    "to_x": (tc + 0.5) * cell_size,
                    "to_y": (tr + 0.5) * cell_size,
                    "count": count,
                }
            )

        return result


class HighlightGenerator:
    """Extracts highlight-worthy moments from match events and generates
    detailed replay data for them.
    """

    # Event outcomes that qualify as highlights
    HIGHLIGHT_OUTCOMES = {
        EventOutcome.GOAL,
        EventOutcome.OWN_GOAL,
        EventOutcome.SHOT_ON_GOAL,
        EventOutcome.SHOT_HIT_POST,
        EventOutcome.SHOT_SAVED,
        EventOutcome.FOUL_YELLOW_CARD,
        EventOutcome.FOUL_RED_CARD,
    }

    def extract_highlights(self, events: list) -> list[dict]:
        """Filter events down to highlight-worthy moments.

        Highlights include goals, cards, spectacular saves, near-misses
        (post hits), and shots on target.

        Args:
            events: List of SimulationEvent objects.

        Returns:
            List of dicts with keys: minute, event_type, outcome, attacker,
            defender, commentary.
        """
        highlights = []

        for event in events:
            outcome = getattr(event, "outcome", None)
            if outcome is None:
                continue

            if outcome not in self.HIGHLIGHT_OUTCOMES:
                continue

            minute = 0.0
            if hasattr(event, "state") and event.state:
                minutes_td = event.state.minutes
                if minutes_td is not None:
                    minute = minutes_td.total_seconds() / 60.0

            highlights.append(
                {
                    "minute": minute,
                    "event_type": event.event_type.name if hasattr(event, "event_type") else "UNKNOWN",
                    "outcome": outcome.name,
                    "attacker": str(event.attacking_player) if event.attacking_player else None,
                    "defender": str(event.defending_player) if event.defending_player else None,
                    "commentary": list(event.commentary) if hasattr(event, "commentary") else [],
                }
            )

        return highlights

    def generate_replay_data(self, highlight_event) -> list[MatchFrame]:
        """Generate 10 detailed frames for replaying a highlight event.

        The replay zooms in on the action area, providing a slower, more
        detailed view of the key moment.

        Args:
            highlight_event: A SimulationEvent representing a highlight moment.

        Returns:
            List of 10 MatchFrame objects for the replay sequence.
        """
        frames: list[MatchFrame] = []
        num_frames = 10

        # Determine the action zone
        pitch_pos = "MIDFIELD_CENTER"
        if hasattr(highlight_event, "state") and highlight_event.state:
            pitch_pos = highlight_event.state.position.name

        center = MatchAnimator.PITCH_ZONE_COORDS.get(pitch_pos, (50.0, 50.0))

        attacker_name = (
            str(highlight_event.attacking_player)
            if highlight_event.attacking_player
            else None
        )
        defender_name = (
            str(highlight_event.defending_player)
            if highlight_event.defending_player
            else None
        )

        # Create a zoomed view: players cluster near the action
        for i in range(num_frames):
            t = i / (num_frames - 1)
            positions: dict[str, tuple[float, float]] = {}

            if attacker_name:
                # Attacker moves toward goal
                ax = center[0] + 5 * t
                ay = center[1] + 2 * (0.5 - abs(t - 0.5))
                positions[attacker_name] = (
                    MatchAnimator._clamp(ax),
                    MatchAnimator._clamp(ay),
                )

            if defender_name:
                # Defender converges on attacker
                dx = center[0] + 3 * t
                dy = center[1] - 3 * (0.5 - abs(t - 0.5))
                positions[defender_name] = (
                    MatchAnimator._clamp(dx),
                    MatchAnimator._clamp(dy),
                )

            # Ball follows the attacker then diverges toward goal
            ball_x = center[0] + 8 * t
            ball_y = center[1] + 5 * (0.5 - abs(t - 0.5))

            outcome_name = ""
            if hasattr(highlight_event, "outcome") and highlight_event.outcome:
                outcome_name = highlight_event.outcome.name

            event_text = None
            if i == 0:
                event_text = f"REPLAY: {outcome_name}"
            elif i == num_frames - 1:
                event_text = outcome_name

            frames.append(
                MatchFrame(
                    timestamp=i * 0.15,
                    ball_x=MatchAnimator._clamp(ball_x),
                    ball_y=MatchAnimator._clamp(ball_y),
                    player_positions=positions,
                    event_text=event_text,
                )
            )

        return frames
