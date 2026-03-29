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
from uuid import UUID

from ...core.career_mode import CareerEngine
from ...core.db.expanded_db import ExpandedDatabase
from ..pages.new_game import NewGamePage
from .controllerinterface import ControllerInterface


class NewGameController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: NewGamePage):
        self.controller = controller
        self.page = page
        self.expanded_db = ExpandedDatabase()
        # Maps display name -> club dict for the currently selected league
        self._club_map: dict[str, dict] = {}
        self._bind()

    def initialize(self):
        """Populate the league combo with available leagues."""
        leagues = self.expanded_db.get_available_leagues()
        self.page.league_combo["values"] = leagues
        self.page.league_combo.set("")
        self.page.club_combo["values"] = []
        self.page.club_combo.set("")
        self._clear_club_info()
        self.page.status_label.config(text="")
        self.page.manager_name_entry.delete(0, "end")

    def _on_league_select(self, event=None):
        """When a league is selected, load clubs from the DB filtered by country."""
        league_name = self.page.league_combo.get()
        if not league_name:
            return

        try:
            league_info = self.expanded_db.get_league_info(league_name)
            country = league_info["country"]

            # Load clubs from the core DB and filter by country
            clubs_data = self.controller.db.load_clubs()
            filtered = [c for c in clubs_data if c.get("country") == country]

            if not filtered:
                # If no clubs match the country, show all clubs as fallback
                filtered = clubs_data

            self._club_map = {}
            club_names = []
            for club in filtered:
                name = club["name"]
                self._club_map[name] = club
                club_names.append(name)

            club_names.sort()
            self.page.club_combo["values"] = club_names
            self.page.club_combo.set("")
            self._clear_club_info()
            self.page.status_label.config(
                text=f"Found {len(club_names)} clubs for {league_name}"
            )
        except Exception as e:
            self.page.status_label.config(text=f"Error loading clubs: {e}")

    def _on_club_select(self, event=None):
        """When a club is selected, display its details."""
        club_name = self.page.club_combo.get()
        if not club_name or club_name not in self._club_map:
            self._clear_club_info()
            return

        club = self._club_map[club_name]
        self.page.stadium_label.config(text=club.get("stadium", "Unknown"))
        self.page.capacity_label.config(
            text=f"{club.get('stadium_capacity', 0):,}"
        )
        squad = club.get("squad", [])
        self.page.squad_size_label.config(text=str(len(squad)))

    def _clear_club_info(self):
        """Reset the club info labels."""
        self.page.stadium_label.config(text="--")
        self.page.capacity_label.config(text="--")
        self.page.squad_size_label.config(text="--")

    def _start_career(self):
        """Validate inputs, create a CareerEngine, and start the career."""
        manager_name = self.page.manager_name_entry.get().strip()
        if not manager_name:
            self.page.status_label.config(text="Please enter a manager name.")
            return

        league_name = self.page.league_combo.get()
        if not league_name:
            self.page.status_label.config(text="Please select a league.")
            return

        club_name = self.page.club_combo.get()
        if not club_name or club_name not in self._club_map:
            self.page.status_label.config(text="Please select a club.")
            return

        club_dict = self._club_map[club_name]
        club_id = UUID(int=club_dict["id"])

        try:
            self.page.status_label.config(text="Starting career...")
            self.page.update_idletasks()

            career_engine = CareerEngine(self.controller.settings, self.controller.db)
            career_engine.new_career(manager_name, league_name, club_id)

            # Store on the main controller for other pages to access
            self.controller.career_engine = career_engine
            self.controller.current_user_team = club_dict

            self.page.status_label.config(text="Career started!")
            self.switch("career_dashboard")
        except Exception as e:
            self.page.status_label.config(text=f"Error: {e}")

    def switch(self, page: str):
        self.controller.switch(page)

    def _bind(self):
        self.page.league_combo.bind("<<ComboboxSelected>>", self._on_league_select)
        self.page.club_combo.bind("<<ComboboxSelected>>", self._on_club_select)
        self.page.start_btn.config(command=self._start_career)
        self.page.cancel_btn.config(command=lambda: self.switch("home"))
