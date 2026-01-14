from ..pages.championship import ChampionshipPage
from .controllerinterface import ControllerInterface

class ChampionshipController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: ChampionshipPage):
        self.controller = controller
        self.page = page
        self._bind()

    def initialize(self):
        self.controller.db.check_clubs_file(amount=50)
        clubs = self.controller.db.load_clubs()
        
        # We need to sort or simulate points. For now, we just list them initialized.
        # In a real scenario, this would read from the League class which tracks points.
        # Since we just want "consistency" with Team Selection, we list the clubs.
        # We can randomize points or just show 0 to show they exist.
        
        # Let's create dummy standings based on the clubs loaded
        standings = []
        for i, club in enumerate(clubs, 1):
            # pos, name, played, won, drawn, lost, points
            standings.append((i, club["name"], 0, 0, 0, 0, 0))

        for i in self.page.tree.get_children():
            self.page.tree.delete(i)
            
        for team in standings:
            self.page.tree.insert("", "end", values=team)

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch("debug_home")

    def _bind(self):
        self.page.cancel_btn.config(command=self.go_to_debug_home_page)
