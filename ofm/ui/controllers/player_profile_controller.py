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

from ..pages import PlayerProfilePage
from .controllerinterface import ControllerInterface

POSITION_MAP = {1: "GK", 2: "DF", 3: "MF", 4: "FW"}


class PlayerProfilePageController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: PlayerProfilePage):
        self.controller = controller
        self.page = page
        self._players = []
        self._bind()

    def switch(self, page):
        self.controller.switch(page)

    def initialize(self):
        self.controller.db.check_clubs_file(amount=50)
        self._players = self.controller.db.load_players()
        player_names = [p["short_name"] for p in self._players]
        self.page.player_list.set(player_names)
        if self._players:
            self.page.player_choice.selection_clear(0, "end")
            self.page.player_choice.selection_set(0)
            self._update_profile(self._players[0])

    def go_to_debug_page(self):
        self.switch(self.controller.get_back_page())

    def _bind(self):
        self.page.cancel_btn.config(command=self.go_to_debug_page)
        self.page.player_choice.bind("<<ListboxSelect>>", self._on_player_select)

    def _on_player_select(self, event=None):
        selection = self.page.player_choice.curselection()
        if not selection:
            return
        index = selection[0]
        if 0 <= index < len(self._players):
            self._update_profile(self._players[index])

    def _update_profile(self, player):
        self.page.player_name_value.set(player["short_name"])
        self.page.player_birth_date_value.set(player["dob"])
        self.page.player_nationality_value.set(player["nationality"])

        positions_str = ", ".join(
            POSITION_MAP.get(p, str(p)) for p in player["positions"]
        )
        self.page.positions_value.set(positions_str)

        # Offensive attributes
        offensive = player["attributes"]["offensive"]
        off_col = self.page.offensive_attributes_column
        off_col.shot_power_value.set(offensive["shot_power"])
        off_col.shot_accuracy_value.set(offensive["shot_accuracy"])
        off_col.free_kick_value.set(offensive["free_kick"])
        off_col.penalty_value.set(offensive["penalty"])
        off_col.positioning_value.set(offensive["positioning"])

        # Defensive attributes
        defensive = player["attributes"]["defensive"]
        def_col = self.page.defensive_attributes_column
        def_col.tackling_value.set(defensive["tackling"])
        def_col.interception_value.set(defensive["interception"])
        def_col.positioning_value.set(defensive["positioning"])

        # Intelligence attributes
        intelligence = player["attributes"]["intelligence"]
        int_col = self.page.intelligence_attributes_column
        int_col.vision_value.set(intelligence["vision"])
        int_col.passing_value.set(intelligence["passing"])
        int_col.dribbling_value.set(intelligence["dribbling"])
        int_col.crossing_value.set(intelligence["crossing"])
        int_col.ball_control_value.set(intelligence["ball_control"])

        # Physical attributes
        physical = player["attributes"]["physical"]
        phys_col = self.page.physical_attributes_column
        phys_col.strength_value.set(physical["strength"])
        phys_col.aggression_value.set(physical["aggression"])
        phys_col.endurance_value.set(physical["endurance"])

        # Goalkeeper attributes
        gk = player["attributes"]["gk"]
        gk_col = self.page.gk_attributes_column
        gk_col.reflexes_value.set(gk["reflexes"])
        gk_col.jumping_value.set(gk["jumping"])
        gk_col.positioning_value.set(gk["positioning"])
        gk_col.penalty_value.set(gk["penalty"])
