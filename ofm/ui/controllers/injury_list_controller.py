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

from ..pages.injury_list import InjuryListPage
from .controllerinterface import ControllerInterface
from ...core.football.injury import InjuryManager, PlayerInjury


class InjuryListController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: InjuryListPage):
        self.controller = controller
        self.page = page
        self._injury_manager: InjuryManager = InjuryManager()
        self._current_date: datetime.date = datetime.date.today()
        self._bind()

    def switch(self, page: str):
        self.controller.switch(page)

    def initialize(self):
        career = getattr(self.controller, "career_engine", None)
        if career is not None:
            self._injury_manager = career.injury_manager
            self._current_date = career.current_date
        else:
            # Debug mode: create sample injuries if none exist
            self._injury_manager = InjuryManager()
            self._current_date = datetime.date.today()
            if not self._injury_manager.active_injuries:
                import uuid
                try:
                    self._injury_manager.generate_injury(
                        uuid.uuid4(), PlayerInjury.LIGHT_INJURY, self._current_date
                    )
                    self._injury_manager.generate_injury(
                        uuid.uuid4(), PlayerInjury.MEDIUM_INJURY,
                        self._current_date - datetime.timedelta(days=5)
                    )
                except Exception:
                    pass

        self._refresh_display()

    def _refresh_display(self):
        tree = self.page.injury_tree
        for item in tree.get_children():
            tree.delete(item)

        career = getattr(self.controller, "career_engine", None)

        for injury in self._injury_manager.active_injuries:
            # Try to find the player name
            player_name = str(injury.player_id)[:8] + "..."
            if career is not None:
                player = career._find_player_by_id(injury.player_id)
                if player is not None:
                    player_name = player.details.short_name

            days_elapsed = (self._current_date - injury.date_injured).days
            days_left = max(0, injury.recovery_days - days_elapsed)
            return_date = self._injury_manager.get_return_date(injury)

            severity = injury.injury_type.name.replace("_", " ").title()

            tree.insert(
                "",
                "end",
                values=(
                    player_name,
                    injury.description,
                    severity,
                    days_left,
                    return_date.isoformat(),
                ),
            )

        count = len(self._injury_manager.active_injuries)
        self.page.status_label.config(
            text=f"{count} active injury(ies) as of {self._current_date.isoformat()}"
        )

    def _check_recoveries(self):
        recovered_ids = self._injury_manager.check_recovery(self._current_date)
        if recovered_ids:
            self.page.status_label.config(
                text=f"{len(recovered_ids)} player(s) have recovered!"
            )
        else:
            self.page.status_label.config(text="No recoveries today.")
        self._refresh_display()

    def go_back(self):
        back_page = self.controller.get_back_page()
        self.switch(back_page)

    def _bind(self):
        self.page.check_btn.config(command=self._check_recoveries)
        self.page.cancel_btn.config(command=self.go_back)
