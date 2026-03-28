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

        # Fill name fields
        self._set_entry(self.page.first_name_entry, player.get("first_name", ""))
        self._set_entry(self.page.last_name_entry, player.get("last_name", ""))
        self._set_entry(self.page.short_name_entry, player.get("short_name", ""))
        self._set_entry(self.page.nationality_entry, player.get("nationality", ""))
        self._set_entry(self.page.dob_entry, player.get("dob", ""))
        self._set_entry(self.page.value_entry, player.get("value", 0))
        self._set_entry(self.page.potential_entry, player.get("potential_skill", 0))

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

        # Clear status
        self.page.player_status_label.config(text="")

    def _save_player(self):
        idx = self._selected_player_index
        if idx is None or idx < 0 or idx >= len(self._players):
            return

        player = self._players[idx]
        try:
            # Save name fields
            player["first_name"] = self.page.first_name_entry.get()
            player["last_name"] = self.page.last_name_entry.get()
            player["short_name"] = self.page.short_name_entry.get()
            player["nationality"] = self.page.nationality_entry.get()
            player["dob"] = self.page.dob_entry.get()
            player["value"] = float(self.page.value_entry.get())
            player["potential_skill"] = int(self.page.potential_entry.get())

            # Save top-level fields
            player["fitness"] = float(self.page.fitness_entry.get())
            player["stamina"] = float(self.page.stamina_entry.get())
            player["form"] = float(self.page.form_entry.get())

            # Save attribute groups
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

            # Refresh combobox to reflect name changes
            player_names = [p.get("short_name", f"Player {i}") for i, p in enumerate(self._players)]
            self.page.player_combo["values"] = player_names
            self.page.player_combo.current(idx)

            self.page.player_status_label.config(
                text=f"Player '{player['short_name']}' saved!", foreground="green"
            )
        except Exception as e:
            self.page.player_status_label.config(
                text=f"Error saving player: {e}", foreground="red"
            )

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

        self._set_entry(self.page.country_entry, club.get("country", ""))
        self._set_entry(self.page.location_entry, club.get("location", ""))

        # Finances
        finances = club.get("finances", {})
        self._set_entry(self.page.balance_entry, finances.get("balance", 0))
        self._set_entry(self.page.transfer_budget_entry, finances.get("transfer_budget", 0))
        self._set_entry(self.page.wage_budget_entry, finances.get("wage_budget", 0))

        # Clear status
        self.page.team_status_label.config(text="")

    def _save_team(self):
        idx = self._selected_club_index
        if idx is None or idx < 0 or idx >= len(self._clubs):
            return

        club = self._clubs[idx]
        try:
            club["name"] = self.page.team_name_entry.get()
            club["stadium"] = self.page.stadium_entry.get()
            club["stadium_capacity"] = int(self.page.capacity_entry.get())
            club["default_formation"] = self.page.formation_combo.get()
            club["country"] = self.page.country_entry.get()
            club["location"] = self.page.location_entry.get()

            # Finances
            club.setdefault("finances", {})["balance"] = float(self.page.balance_entry.get())
            club["finances"]["transfer_budget"] = float(self.page.transfer_budget_entry.get())
            club["finances"]["wage_budget"] = float(self.page.wage_budget_entry.get())

            with open(self.controller.db.clubs_file, "w", encoding="utf-8") as fp:
                json.dump(self._clubs, fp)

            # Refresh combobox to reflect name changes
            team_names = [c.get("name", f"Club {i}") for i, c in enumerate(self._clubs)]
            self.page.team_combo["values"] = team_names
            self.page.team_combo.current(idx)

            self.page.team_status_label.config(
                text=f"Team '{club['name']}' saved!", foreground="green"
            )
        except Exception as e:
            self.page.team_status_label.config(
                text=f"Error saving team: {e}", foreground="red"
            )

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
