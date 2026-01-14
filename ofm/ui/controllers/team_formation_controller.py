from ..pages.team_formation import TeamFormationPage
from .controllerinterface import ControllerInterface
from ...core.football.formation import Formation, FORMATION_STRINGS

class TeamFormationController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: TeamFormationPage):
        self.controller = controller
        self.page = page
        self.club = None
        self._bind()

    def initialize(self):
        self.page.formation_combobox['values'] = FORMATION_STRINGS
        
        team_data = self.controller.current_user_team
        if not team_data:
             # If no team selected, maybe show empty or error?
             # For now, just return
             return

        # We probably need to load the full team object with players
        # The team_data stored in OFMController might be just the dict from clubs.json
        # We need to construct the team object possibly.
        
        # NOTE: Loading the FULL team object with simulation capabilities might be complex here
        # depending on how 'TeamSelection' stored the data. 
        # In TeamSelectionController we did: self.controller.current_user_team = selected_club (which is a dict)
        
        # So we use the DB to load the full object
        players_dicts = self.controller.db.load_players()
        club_objects = self.controller.db.load_club_objects([team_data], players_dicts)
        if club_objects:
             self.club = club_objects[0]
             # Create a formation object to help us listing players
             self.formation = Formation(self.club.default_formation)
             # Distribute players for initial view
             self.formation.get_best_players(self.club.squad)
             
             self.page.formation_combobox.set(self.formation.formation_string)
             self.update_player_list()

    def update_player_list(self):
        for i in self.page.tree.get_children():
            self.page.tree.delete(i)
        
        # Starting 11
        for p in self.formation.players:
             self.page.tree.insert("", "end", values=(p.player.details.short_name, p.player.details.get_best_position().name, p.current_position.name))
        
        # Bench
        for p in self.formation.bench:
             self.page.tree.insert("", "end", values=(p.player.details.short_name, p.player.details.get_best_position().name, "Bench"))

    def on_formation_change(self, event):
        new_formation = self.page.formation_combobox.get()
        if new_formation and self.club:
            try:
                self.formation.change_formation(new_formation)
                self.update_player_list()
            except Exception as e:
                print(f"Error changing formation: {e}")

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch("debug_home")

    def _bind(self):
        self.page.cancel_btn.config(command=self.go_to_debug_home_page)
        self.page.formation_combobox.bind("<<ComboboxSelected>>", self.on_formation_change)
