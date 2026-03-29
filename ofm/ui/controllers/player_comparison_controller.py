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
from ..pages.player_comparison import PlayerComparisonPage
from .controllerinterface import ControllerInterface
from ...core.ui_systems import PlayerComparison


class PlayerComparisonController(ControllerInterface):
    POSITION_MAP = {1: "GK", 2: "DF", 3: "MF", 4: "FW"}

    def __init__(self, controller: ControllerInterface, page: PlayerComparisonPage):
        self.controller = controller
        self.page = page
        self._comparison = PlayerComparison()
        self._players = []  # list of (display_name, player_dict)
        self._bind()

    def switch(self, page: str):
        self.controller.switch(page)

    def initialize(self):
        self._players = []

        career = getattr(self.controller, "career_engine", None)
        if career is not None:
            # Load all players from career engine clubs
            for club in career.clubs:
                for player in club.squad:
                    p = player.details
                    pos = p.get_best_position()
                    pos_name = self.POSITION_MAP.get(pos.value if hasattr(pos, 'value') else pos, "?")
                    overall = p.attributes.get_overall(pos)
                    display = f"{p.short_name} ({club.name})"
                    player_dict = {
                        "name": p.short_name,
                        "position": pos_name,
                        "overall": overall,
                        "age": self._calculate_age(p.dob, career.current_date),
                        "potential": getattr(p, "potential_skill", 0),
                        "fitness": getattr(p, "fitness", 100),
                        "international_reputation": getattr(p, "international_reputation", 0),
                    }
                    # Add offensive attributes
                    if hasattr(p.attributes, "offensive"):
                        off = p.attributes.offensive
                        player_dict["shot_power"] = getattr(off, "shot_power", 0)
                        player_dict["shot_accuracy"] = getattr(off, "shot_accuracy", 0)
                        player_dict["positioning"] = getattr(off, "positioning", 0)
                        player_dict["dribbling"] = getattr(off, "dribbling", 0)
                    # Add defensive attributes
                    if hasattr(p.attributes, "defensive"):
                        dfn = p.attributes.defensive
                        player_dict["tackling"] = getattr(dfn, "tackling", 0)
                        player_dict["interception"] = getattr(dfn, "interception", 0)
                        player_dict["marking"] = getattr(dfn, "marking", 0)
                    # Add physical attributes
                    if hasattr(p.attributes, "physical"):
                        phy = p.attributes.physical
                        player_dict["speed"] = getattr(phy, "speed", 0)
                        player_dict["stamina"] = getattr(phy, "stamina", 0)
                        player_dict["strength"] = getattr(phy, "strength", 0)

                    self._players.append((display, player_dict))
        else:
            # Debug mode: load from DB
            try:
                db = self.controller.db
                db.check_clubs_file()
                clubs_data = db.load_clubs()
                players_data = db.load_players()
                clubs = db.load_club_objects(clubs_data, players_data)
                for club in clubs:
                    for player in club.squad:
                        p = player.details
                        pos = p.get_best_position()
                        pos_name = self.POSITION_MAP.get(
                            pos.value if hasattr(pos, 'value') else pos, "?"
                        )
                        overall = p.attributes.get_overall(pos)
                        display = f"{p.short_name} ({club.name})"
                        player_dict = {
                            "name": p.short_name,
                            "position": pos_name,
                            "overall": overall,
                            "age": self._calculate_age(p.dob),
                            "potential": getattr(p, "potential_skill", 0),
                        }
                        self._players.append((display, player_dict))
            except Exception:
                pass

        # Populate combo boxes
        names = [name for name, _ in self._players]
        self.page.player_a_combo["values"] = names
        self.page.player_b_combo["values"] = names

        if names:
            self.page.player_a_combo.current(0)
            if len(names) > 1:
                self.page.player_b_combo.current(1)
            else:
                self.page.player_b_combo.current(0)

        # Clear tree
        tree = self.page.compare_tree
        for item in tree.get_children():
            tree.delete(item)

    def _compare(self):
        idx_a = self.page.player_a_combo.current()
        idx_b = self.page.player_b_combo.current()

        if idx_a < 0 or idx_b < 0 or not self._players:
            return

        _, player_a = self._players[idx_a]
        _, player_b = self._players[idx_b]

        result = self._comparison.compare(player_a, player_b)

        # Populate tree
        tree = self.page.compare_tree
        for item in tree.get_children():
            tree.delete(item)

        # Header rows
        tree.insert("", "end", values=(
            "Name", player_a.get("name", "?"), player_b.get("name", "?")
        ))
        tree.insert("", "end", values=(
            "Position", player_a.get("position", "?"), player_b.get("position", "?")
        ))

        # Attribute rows
        for attr, data in result.get("attributes", {}).items():
            val_a = data["a"]
            val_b = data["b"]
            # Format nicely
            if isinstance(val_a, float):
                val_a = f"{val_a:.1f}"
            if isinstance(val_b, float):
                val_b = f"{val_b:.1f}"
            tree.insert("", "end", values=(
                attr.replace("_", " ").title(), val_a, val_b
            ))

    @staticmethod
    def _calculate_age(dob, ref_date=None):
        import datetime
        if ref_date is None:
            ref_date = datetime.date.today()
        if isinstance(dob, str):
            dob = datetime.date.fromisoformat(dob)
        elif hasattr(dob, "date"):
            dob = dob.date()
        age = ref_date.year - dob.year
        if (ref_date.month, ref_date.day) < (dob.month, dob.day):
            age -= 1
        return age

    def go_back(self):
        back_page = self.controller.get_back_page()
        self.switch(back_page)

    def _bind(self):
        self.page.compare_btn.config(command=self._compare)
        self.page.cancel_btn.config(command=self.go_back)
