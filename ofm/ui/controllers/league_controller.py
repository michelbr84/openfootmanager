import random

from ...core.ui_systems import FormGuide
from ..pages.league import LeaguePage
from .controllerinterface import ControllerInterface


class LeagueController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: LeaguePage):
        self.controller = controller
        self.page = page
        self._bind()

    @staticmethod
    def _generate_form_string(won: int, drawn: int, lost: int) -> str:
        """Generate a plausible form string from W/D/L counts.

        Builds a pool of results proportional to the team's record,
        then samples the last 5.
        """
        total = won + drawn + lost
        if total == 0:
            return ""
        pool = ["W"] * won + ["D"] * drawn + ["L"] * lost
        random.shuffle(pool)
        guide = FormGuide(pool)
        return guide.get_last_n(5)

    def initialize(self):
        career = getattr(self.controller, "career_engine", None)
        if career and career.season:
            standings = career.get_standings()
            for i in self.page.tree.get_children():
                self.page.tree.delete(i)
            for entry in standings:
                form_str = self._generate_form_string(
                    entry.get("won", 0),
                    entry.get("drawn", 0),
                    entry.get("lost", 0),
                )
                self.page.tree.insert("", "end", values=(
                    entry["position"], entry["club"], entry["played"],
                    entry["won"], entry["drawn"], entry["lost"],
                    entry["goals_for"], entry["goals_against"],
                    entry["goal_difference"], entry["points"],
                    form_str,
                ))
        else:
            # Fallback: debug mode with dummy data
            self.controller.db.check_clubs_file(amount=50)
            clubs = self.controller.db.load_clubs()
            standings = []
            for i, club in enumerate(clubs, 1):
                # Pos, Club, P, W, D, L, GF, GA, GD, Pts, Form
                standings.append((i, club["name"], 0, 0, 0, 0, 0, 0, 0, 0, ""))
            for i in self.page.tree.get_children():
                self.page.tree.delete(i)
            for team in standings:
                self.page.tree.insert("", "end", values=team)

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch(self.controller.get_back_page())

    def _bind(self):
        self.page.back_btn.config(command=self.go_to_debug_home_page)
