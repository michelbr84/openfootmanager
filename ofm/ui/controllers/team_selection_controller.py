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
from ..pages.team_selection import TeamSelectionPage
from .controllerinterface import ControllerInterface


class TeamSelectionController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: TeamSelectionPage):
        self.controller = controller
        self.page = page
        self._bind()

    def initialize(self):
        self.controller.db.check_clubs_file(amount=50)
        clubs = self.controller.db.load_clubs()
        for i in self.page.tree.get_children():
            self.page.tree.delete(i)
        
        for club in clubs:
            self.page.tree.insert("", "end", iid=club["id"], values=(club["name"], club["country"]))

    def switch(self, page):
        self.controller.switch(page)

    def select_team(self):
        selected = self.page.tree.selection()
        if not selected:
            return
        
        team_id = selected[0]
        # Find the full club object or just store ID
        clubs = self.controller.db.load_clubs()
        selected_club = next((c for c in clubs if str(c["id"]) == str(team_id)), None)
        
        if selected_club:
            self.controller.current_user_team = selected_club
            self.go_to_debug_home_page()

    def go_to_debug_home_page(self):
        self.switch("debug_home")

    def _bind(self):
        self.page.cancel_btn.config(command=self.go_to_debug_home_page)
        self.page.select_team_btn.config(command=self.select_team)
