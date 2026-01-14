from ..pages.league import LeaguePage
from .controllerinterface import ControllerInterface

class LeagueController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: LeaguePage):
        self.controller = controller
        self.page = page
        self._bind()

    def initialize(self):
         # Similar logic to Championship, load real clubs
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
        self.switch("debug_home")

    def _bind(self):
        self.page.back_btn.config(command=self.go_to_debug_home_page)
