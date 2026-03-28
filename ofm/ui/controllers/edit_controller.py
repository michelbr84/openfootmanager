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
import json

from ..pages.edit import EditPage
from .controllerinterface import ControllerInterface
from ...core.football.formation import FORMATION_STRINGS


class EditController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: EditPage):
        self.controller = controller
        self.page = page
        self._players = []
        self._clubs = []
        self._selected_player_index = None
        self._selected_club_index = None
        self._bind()

    def switch(self, page: str):
        self.controller.switch(page)

    def initialize(self):
        db = self.controller.db
        try:
            self._players = db.load_players()
            self._clubs = db.load_clubs()
        except Exception:
            self._players = []
            self._clubs = []

        # Populate player combobox
        player_names = [p.get("short_name", f"Player {i}") for i, p in enumerate(self._players)]
        self.page.player_combo["values"] = player_names
        if player_names:
            self.page.player_combo.current(0)
            self._on_player_select(None)

        # Populate team combobox
        team_names = [c.get("name", f"Club {i}") for i, c in enumerate(self._clubs)]
        self.page.team_combo["values"] = team_names
        if team_names:
            self.page.team_combo.current(0)
            self._on_team_select(None)

        # Populate formation combobox
        self.page.formation_combo["values"] = FORMATION_STRINGS

    def _on_player_select(self, event):
        idx = self.page.player_combo.current()
        if idx < 0 or idx >= len(self._players):
            return
        self._selected_player_index = idx
        player = self._players[idx]

        # Fill top-level fields
        self._set_entry(self.page.fitness_entry, player.get("fitness", 0))
        self._set_entry(self.page.stamina_entry, player.get("stamina", 0))
        self._set_entry(self.page.form_entry, player.get("form", 0))

        # Fill attribute groups
        attrs = player.get("attributes", {})
        for attr, entry in self.page.offensive_entries.items():
            self._set_entry(entry, attrs.get("offensive", {}).get(attr, 0))
        for attr, entry in self.page.defensive_entries.items():
            self._set_entry(entry, attrs.get("defensive", {}).get(attr, 0))
        for attr, entry in self.page.physical_entries.items():
            self._set_entry(entry, attrs.get("physical", {}).get(attr, 0))
        for attr, entry in self.page.intelligence_entries.items():
            self._set_entry(entry, attrs.get("intelligence", {}).get(attr, 0))
        for attr, entry in self.page.gk_entries.items():
            self._set_entry(entry, attrs.get("gk", {}).get(attr, 0))

    def _save_player(self):
        idx = self._selected_player_index
        if idx is None or idx < 0 or idx >= len(self._players):
            return

        player = self._players[idx]
        player["fitness"] = float(self.page.fitness_entry.get())
        player["stamina"] = float(self.page.stamina_entry.get())
        player["form"] = float(self.page.form_entry.get())

        attrs = player.setdefault("attributes", {})
        for attr, entry in self.page.offensive_entries.items():
            attrs.setdefault("offensive", {})[attr] = int(entry.get())
        for attr, entry in self.page.defensive_entries.items():
            attrs.setdefault("defensive", {})[attr] = int(entry.get())
        for attr, entry in self.page.physical_entries.items():
            attrs.setdefault("physical", {})[attr] = int(entry.get())
        for attr, entry in self.page.intelligence_entries.items():
            attrs.setdefault("intelligence", {})[attr] = int(entry.get())
        for attr, entry in self.page.gk_entries.items():
            attrs.setdefault("gk", {})[attr] = int(entry.get())

        with open(self.controller.db.players_file, "w", encoding="utf-8") as fp:
            json.dump(self._players, fp)

    def _on_team_select(self, event):
        idx = self.page.team_combo.current()
        if idx < 0 or idx >= len(self._clubs):
            return
        self._selected_club_index = idx
        club = self._clubs[idx]

        self._set_entry(self.page.team_name_entry, club.get("name", ""))
        self._set_entry(self.page.stadium_entry, club.get("stadium", ""))
        self._set_entry(self.page.capacity_entry, club.get("stadium_capacity", 0))

        formation = club.get("default_formation", "")
        if formation in FORMATION_STRINGS:
            self.page.formation_combo.current(FORMATION_STRINGS.index(formation))
        else:
            self.page.formation_combo.set(formation)

    def _save_team(self):
        idx = self._selected_club_index
        if idx is None or idx < 0 or idx >= len(self._clubs):
            return

        club = self._clubs[idx]
        club["name"] = self.page.team_name_entry.get()
        club["stadium"] = self.page.stadium_entry.get()
        club["stadium_capacity"] = int(self.page.capacity_entry.get())
        club["default_formation"] = self.page.formation_combo.get()

        with open(self.controller.db.clubs_file, "w", encoding="utf-8") as fp:
            json.dump(self._clubs, fp)

    def _bind(self):
        self.page.player_combo.bind("<<ComboboxSelected>>", self._on_player_select)
        self.page.team_combo.bind("<<ComboboxSelected>>", self._on_team_select)
        self.page.save_player_btn.config(command=self._save_player)
        self.page.save_team_btn.config(command=self._save_team)
        self.page.cancel_btn.config(command=lambda: self.switch("debug_home"))

    @staticmethod
    def _set_entry(entry, value):
        entry.delete(0, "end")
        entry.insert(0, str(value))
