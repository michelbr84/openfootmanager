from ..pages.championship import ChampionshipPage
from .controllerinterface import ControllerInterface

class ChampionshipController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: ChampionshipPage):
        self.controller = controller
        self.page = page
        self._bind()

    def initialize(self):
        # Mock data for demonstration as we don't have a live simulated league context here yet
        # In a real scenario, we would pull this from self.controller.game_state or similar
        mock_standings = [
            (1, "Team A", 10, 8, 1, 1, 25),
            (2, "Team B", 10, 7, 2, 1, 23),
            (3, "Team C", 10, 6, 2, 2, 20),
            (4, "Team D", 10, 5, 3, 2, 18),
            (5, "Team E", 10, 4, 2, 4, 14),
        ]
        
        for i in self.page.tree.get_children():
            self.page.tree.delete(i)
            
        for team in mock_standings:
            self.page.tree.insert("", "end", values=team)

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch("debug_home")

    def _bind(self):
        self.page.cancel_btn.config(command=self.go_to_debug_home_page)
