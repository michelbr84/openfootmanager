from ..pages.league import LeaguePage
from .controllerinterface import ControllerInterface

class LeagueController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: LeaguePage):
        self.controller = controller
        self.page = page
        self._bind()

    def initialize(self):
        career = getattr(self.controller, "career_engine", None)
        if career and career.season:
            standings = career.get_standings()
            for i in self.page.tree.get_children():
                self.page.tree.delete(i)
            for entry in standings:
                self.page.tree.insert("", "end", values=(
                    entry["position"], entry["club"], entry["played"],
                    entry["won"], entry["drawn"], entry["lost"],
                    entry["goals_for"], entry["goals_against"],
                    entry["goal_difference"], entry["points"]
                ))
        else:
            # Fallback: debug mode with dummy data
            self.controller.db.check_clubs_file(amount=50)
            clubs = self.controller.db.load_clubs()
            standings = []
            for i, club in enumerate(clubs, 1):
                # Pos, Club, P, W, D, L, GF, GA, GD, Pts
                standings.append((i, club["name"], 0, 0, 0, 0, 0, 0, 0, 0))
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
