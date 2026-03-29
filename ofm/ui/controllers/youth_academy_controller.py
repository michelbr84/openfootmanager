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
from ..pages.youth_academy import YouthAcademyPage
from .controllerinterface import ControllerInterface
from ...core.football.youth import YouthAcademy


class YouthAcademyController(ControllerInterface):
    POSITION_MAP = {1: "GK", 2: "DF", 3: "MF", 4: "FW"}

    def __init__(self, controller: ControllerInterface, page: YouthAcademyPage):
        self.controller = controller
        self.page = page
        self._academy: YouthAcademy = YouthAcademy(level=1)
        self._bind()

    def switch(self, page: str):
        self.controller.switch(page)

    def initialize(self):
        career = getattr(self.controller, "career_engine", None)
        if career is not None and hasattr(career, "youth_academy"):
            self._academy = career.youth_academy
        else:
            if not self._academy.prospects:
                self._academy = YouthAcademy(level=1)

        # Auto-generate if no prospects yet
        active = [p for p in self._academy.prospects if not p.promoted]
        if not active:
            self._academy.generate_prospects(self.controller.settings)

        self._refresh_display()

    def _refresh_display(self):
        # Update info labels
        active = [p for p in self._academy.prospects if not p.promoted]
        self.page.level_label.config(
            text=f"Academy Level: {self._academy.level}/5"
        )
        self.page.prospects_label.config(
            text=f"Prospects: {len(active)}/{self._academy.max_prospects}"
        )

        # Update upgrade button state
        if self._academy.level >= 5:
            self.page.upgrade_btn.config(state="disabled")
        else:
            self.page.upgrade_btn.config(state="normal")

        # Clear and repopulate tree
        tree = self.page.prospects_tree
        for item in tree.get_children():
            tree.delete(item)

        for idx, prospect in enumerate(active, start=1):
            positions = prospect.player_dict.get("positions", [])
            pos_str = "/".join(
                self.POSITION_MAP.get(p, "?") for p in positions
            ) if positions else "?"

            tree.insert(
                "",
                "end",
                values=(
                    idx,
                    prospect.name,
                    prospect.age,
                    pos_str,
                    prospect.overall,
                    prospect.potential_skill,
                    f"{prospect.development_score:.0%}",
                ),
            )

        # Clear status
        self.page.status_label.config(text="")

    def _get_active_prospects(self):
        """Return list of non-promoted prospects."""
        return [p for p in self._academy.prospects if not p.promoted]

    def _get_selected_index(self):
        """Get the real index into self._academy.prospects for the selected tree item."""
        selection = self.page.prospects_tree.selection()
        if not selection:
            return None, None
        item = selection[0]
        values = self.page.prospects_tree.item(item, "values")
        display_num = int(values[0])  # 1-based display number

        # Map display number to actual index in self._academy.prospects
        active_indices = [
            i for i, p in enumerate(self._academy.prospects) if not p.promoted
        ]
        if display_num < 1 or display_num > len(active_indices):
            return None, None
        real_index = active_indices[display_num - 1]
        return real_index, self._academy.prospects[real_index]

    def _generate_prospects(self):
        new_prospects = self._academy.generate_prospects(self.controller.settings)
        self._refresh_display()
        self.page.status_label.config(
            text=f"Generated {len(new_prospects)} new prospects!"
        )

    def _develop_all(self):
        self._academy.develop_prospects()
        self._refresh_display()
        self.page.status_label.config(text="All prospects trained!")

    def _promote_prospect(self):
        real_index, prospect = self._get_selected_index()
        if real_index is None:
            self.page.status_label.config(text="Select a prospect first.")
            return
        name = prospect.name
        try:
            self._academy.promote_prospect(real_index)
            self.page.status_label.config(
                text=f"Promoted {name} to first team!"
            )
            self._refresh_display()
        except (IndexError, ValueError) as e:
            self.page.status_label.config(text=str(e))

    def _release_prospect(self):
        real_index, prospect = self._get_selected_index()
        if real_index is None:
            self.page.status_label.config(text="Select a prospect first.")
            return
        name = prospect.name
        try:
            self._academy.release_prospect(real_index)
            self.page.status_label.config(text=f"Released {name}")
            self._refresh_display()
        except IndexError as e:
            self.page.status_label.config(text=str(e))

    def _show_scout_report(self):
        real_index, prospect = self._get_selected_index()
        if real_index is None:
            self.page.status_label.config(text="Select a prospect first.")
            return
        report = self._academy.scout_report(prospect)
        self.page.report_text.config(state="normal")
        self.page.report_text.delete("1.0", "end")
        self.page.report_text.insert("1.0", report)
        self.page.report_text.config(state="disabled")

    def _upgrade_academy(self):
        if self._academy.level >= 5:
            self.page.status_label.config(text="Academy is already at max level!")
            return
        self._academy.upgrade()
        self._refresh_display()
        self.page.status_label.config(
            text=f"Academy upgraded to level {self._academy.level}!"
        )

    def go_back(self):
        back_page = self.controller.get_back_page()
        self.switch(back_page)

    def _bind(self):
        self.page.generate_btn.config(command=self._generate_prospects)
        self.page.develop_btn.config(command=self._develop_all)
        self.page.promote_btn.config(command=self._promote_prospect)
        self.page.release_btn.config(command=self._release_prospect)
        self.page.scout_btn.config(command=self._show_scout_report)
        self.page.upgrade_btn.config(command=self._upgrade_academy)
        self.page.cancel_btn.config(command=self.go_back)
