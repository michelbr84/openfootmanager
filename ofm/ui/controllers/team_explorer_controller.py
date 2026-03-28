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
import datetime

from ..pages.team_explorer import TeamExplorerPage
from .controllerinterface import ControllerInterface


class TeamExplorerController(ControllerInterface):
    POSITION_MAP = {1: "GK", 2: "DF", 3: "MF", 4: "FW"}

    def __init__(self, controller: ControllerInterface, page: TeamExplorerPage):
        self.controller = controller
        self.page = page
        self._clubs = []
        self._player_lookup = {}
        self._bind()

    def initialize(self):
        self.controller.db.check_clubs_file(amount=50)
        self._clubs = self.controller.db.load_clubs()
        players = self.controller.db.load_players()

        # Build player_id -> player_dict lookup
        self._player_lookup = {p["id"]: p for p in players}

        # Get unique countries from clubs and populate country combobox
        countries = sorted(set(c["country"] for c in self._clubs if c.get("country")))
        self.page.country_selection["values"] = countries
        if countries:
            self.page.country_selection.set(countries[0])

        # Populate team listbox with all club names initially
        self._update_team_list()

        # Select first team and show its squad
        if self._clubs:
            self.page.team_selection.selection_set(0)
            self._show_selected_team()

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch("debug_home")

    def _bind(self):
        self.page.cancel_btn.config(command=self.go_to_debug_home_page)
        self.page.team_selection.bind("<<ListboxSelect>>", self._on_team_select)
        self.page.country_selection.bind("<<ComboboxSelected>>", self._on_country_change)

    def _on_country_change(self, event=None):
        selected_country = self.page.country_selection.get()
        self._update_team_list(country=selected_country)
        # Select first team in filtered list
        if self.page.team_selection.size() > 0:
            self.page.team_selection.selection_set(0)
            self._show_selected_team()

    def _on_team_select(self, event=None):
        self._show_selected_team()

    def _show_selected_team(self):
        selection = self.page.team_selection.curselection()
        if not selection:
            return
        team_name = self.page.team_selection.get(selection[0])
        club = next((c for c in self._clubs if c["name"] == team_name), None)
        if club:
            self._update_team_table(club)

    def _update_team_list(self, country=None):
        if country:
            filtered = [c for c in self._clubs if c.get("country") == country]
        else:
            filtered = self._clubs
        club_names = sorted(c["name"] for c in filtered)
        self.page.team_selection_items.set(club_names)

    def _update_team_table(self, club_dict):
        today = datetime.date.today()
        rows = []
        for pid in club_dict.get("squad", []):
            player = self._player_lookup.get(pid)
            if not player:
                continue
            name = player.get("short_name", "Unknown")
            nationality = player.get("nationality", "")
            age = self._calculate_age(player.get("dob", "2000-01-01"), today)
            positions = player.get("positions", [])
            primary_pos = positions[0] if positions else 3
            pos_name = self.POSITION_MAP.get(primary_pos, "MF")
            overall = round(self._calculate_overall(player.get("attributes", {}), primary_pos), 1)
            rows.append((name, nationality, age, pos_name, overall))

        self.page.team_table.delete_rows()
        for row_data in rows:
            self.page.team_table.insert_row("end", values=row_data)
        self.page.team_table.load_table_data()

    @staticmethod
    def _calculate_age(dob_str, today=None):
        if today is None:
            today = datetime.date.today()
        try:
            birth = datetime.date.fromisoformat(dob_str)
            return (today - birth).days // 365
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _calculate_overall(attributes, position):
        off_attrs = attributes.get("offensive", {})
        phys_attrs = attributes.get("physical", {})
        def_attrs = attributes.get("defensive", {})
        int_attrs = attributes.get("intelligence", {})
        gk_attrs = attributes.get("gk", {})

        def avg(d):
            vals = list(d.values())
            return sum(vals) / len(vals) if vals else 0.0

        off = avg(off_attrs)
        phys = avg(phys_attrs)
        defn = avg(def_attrs)
        intl = avg(int_attrs)
        gk = avg(gk_attrs)

        if position == 4:  # FW
            return (defn * 1 + phys * 1 + intl * 2 + off * 3) / 7
        elif position == 3:  # MF
            return (defn * 1 + phys * 2 + intl * 3 + off * 1) / 7
        elif position == 2:  # DF
            return (defn * 3 + phys * 2 + intl * 1 + off * 1) / 7
        elif position == 1:  # GK
            return (gk * 3 + defn * 2 + phys * 1 + intl * 1) / 7
        else:
            return (defn + phys + intl + off) / 4
