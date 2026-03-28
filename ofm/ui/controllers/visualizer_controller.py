from ..pages.visualizer import VisualizerPage
from .controllerinterface import ControllerInterface


class VisualizerController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: VisualizerPage):
        self.controller = controller
        self.page = page
        self._bind()

    def initialize(self):
        # Clear previous player drawings without removing pitch lines
        self.page.canvas.delete("player")

        # Get team data
        team_data = self.controller.current_user_team
        if not team_data:
            clubs = self.controller.db.load_clubs()
            if clubs:
                team_data = clubs[0]
            else:
                return

        formation_str = team_data.get("default_formation", "4-4-2")

        # Load player names from the squad
        player_names = []
        players_dicts = self.controller.db.load_players()
        squad_ids = team_data.get("squad", [])
        # Build a lookup of player id -> short_name
        player_lookup = {}
        for p in players_dicts:
            player_lookup[p.get("id")] = p.get("short_name", "")

        for pid in squad_ids:
            name = player_lookup.get(pid, "")
            if name:
                player_names.append(name)

        # Calculate positions and draw
        positions = self._get_formation_positions(formation_str)
        for i, (x, y) in enumerate(positions):
            if i < len(player_names):
                name = player_names[i]
            else:
                name = f"Player {i + 1}"
            self._draw_player(x, y, name)

    def _draw_player(self, x, y, name):
        """Draw a player dot and name label on the canvas."""
        self.page.canvas.create_oval(
            x - 12, y - 12, x + 12, y + 12,
            fill="white", outline="black", width=1, tags="player"
        )
        self.page.canvas.create_text(
            x, y + 20, text=name, fill="white",
            font=("Helvetica", 8), tags="player"
        )

    def _get_formation_positions(self, formation_str):
        """Parse a formation string like '4-4-2' and return (x, y) positions.

        The pitch area is (10, 10) to (790, 590), left = defense, right = attack.
        GK is always included as the first position.
        """
        try:
            parts = [int(n) for n in formation_str.split("-")]
        except (ValueError, AttributeError):
            parts = [4, 4, 2]

        positions = []

        # GK always at far left
        positions.append((60, 300))

        # Distribute remaining lines across the pitch width
        # Available x range for outfield lines: ~180 to ~580
        num_lines = len(parts)
        if num_lines == 0:
            return positions

        x_start = 180
        x_end = 580
        if num_lines == 1:
            x_values = [380]
        else:
            x_step = (x_end - x_start) / (num_lines - 1)
            x_values = [x_start + int(i * x_step) for i in range(num_lines)]

        # Y range for distributing players in each line
        y_min = 120
        y_max = 480

        for line_idx, count in enumerate(parts):
            x = x_values[line_idx]
            if count == 1:
                positions.append((x, 300))
            else:
                y_step = (y_max - y_min) / (count - 1)
                for j in range(count):
                    y = y_min + int(j * y_step)
                    positions.append((x, y))

        return positions

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch("debug_home")

    def _bind(self):
        self.page.back_btn.config(command=self.go_to_debug_home_page)
