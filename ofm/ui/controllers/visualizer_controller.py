from ..pages.visualizer import VisualizerPage
from .controllerinterface import ControllerInterface
from ...core.football.formation import Formation


class VisualizerController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: VisualizerPage):
        self.controller = controller
        self.page = page
        self._bind()

    def initialize(self):
        # Clear previous player drawings without removing pitch lines
        self.page.canvas.delete("player")

        # Get team data
        team_data = getattr(self.controller, "current_user_team", None)
        if not team_data:
            clubs = self.controller.db.load_clubs()
            if clubs:
                team_data = clubs[0]
            else:
                return

        # Load the full Club object with PlayerTeam squad
        players_dicts = self.controller.db.load_players()
        try:
            club_objects = self.controller.db.load_club_objects(
                [team_data], players_dicts
            )
        except Exception:
            return

        if not club_objects:
            return

        club = club_objects[0]

        # Create a Formation and assign players exactly like TeamFormationController
        formation = Formation(club.default_formation)
        formation.get_best_players(club.squad)

        # Draw players by position using the Formation object
        positions = self._get_formation_positions(formation)

        for (x, y), name in positions:
            self._draw_player(x, y, name)

        # Draw bench players as small dots in a row at the bottom
        if formation.bench:
            bench_y = 560
            bench_count = len(formation.bench)
            if bench_count == 1:
                bench_xs = [400]
            else:
                bench_x_start = 100
                bench_x_end = 700
                bench_step = (bench_x_end - bench_x_start) / (bench_count - 1)
                bench_xs = [
                    bench_x_start + int(i * bench_step)
                    for i in range(bench_count)
                ]
            for i, bench_player in enumerate(formation.bench):
                bx = bench_xs[i]
                name = bench_player.player.details.short_name
                self._draw_player(bx, bench_y, name, radius=7)

    def _draw_player(self, x, y, name, radius=12):
        """Draw a player dot and name label on the canvas."""
        self.page.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill="white", outline="black", width=1, tags="player"
        )
        font_size = 7 if radius < 12 else 8
        self.page.canvas.create_text(
            x, y + radius + 8, text=name, fill="white",
            font=("Helvetica", font_size), tags="player"
        )

    def _get_formation_positions(self, formation):
        """Build (x, y) positions from a Formation object and return
        a list of ((x, y), player_short_name) tuples for the starting 11.

        GK at x=60, DF line at x=180, MF line at x=380, FW line at x=580.
        """
        positions = []
        y_min = 120
        y_max = 480

        # GK
        if formation.gk:
            name = formation.gk.player.details.short_name
            positions.append(((60, 300), name))

        # Defenders
        self._spread_line(formation.df, 180, y_min, y_max, positions)

        # Midfielders
        self._spread_line(formation.mf, 380, y_min, y_max, positions)

        # Forwards
        self._spread_line(formation.fw, 580, y_min, y_max, positions)

        return positions

    @staticmethod
    def _spread_line(player_list, x, y_min, y_max, positions):
        """Evenly space a list of PlayerSimulation objects along a vertical line."""
        count = len(player_list)
        if count == 0:
            return
        if count == 1:
            y_positions = [300]
        else:
            step = (y_max - y_min) / (count - 1)
            y_positions = [y_min + int(i * step) for i in range(count)]

        for i, player_sim in enumerate(player_list):
            name = player_sim.player.details.short_name
            positions.append(((x, y_positions[i]), name))

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch(self.controller.get_back_page())

    def _bind(self):
        self.page.back_btn.config(command=self.go_to_debug_home_page)
