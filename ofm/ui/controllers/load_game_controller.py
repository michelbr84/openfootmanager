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
import tkinter.messagebox as messagebox

from ...core.career_mode import CareerEngine
from ...core.game_state import SaveManager
from ...core.migration import SaveMigration
from ..pages.load_game import LoadGamePage
from .controllerinterface import ControllerInterface


class LoadGameController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: LoadGamePage):
        self.controller = controller
        self.page = page
        self.save_manager = SaveManager(self.controller.settings)
        self._bind()

    def initialize(self):
        """List all saves and populate the treeview."""
        self._refresh_tree()
        self.page.status_label.config(text="")

    def _refresh_tree(self):
        """Clear and repopulate the saves treeview."""
        for item in self.page.saves_tree.get_children():
            self.page.saves_tree.delete(item)

        try:
            saves = self.save_manager.list_saves()
            for save in saves:
                self.page.saves_tree.insert(
                    "",
                    "end",
                    iid=save["name"],
                    values=(
                        save["name"],
                        save.get("date", ""),
                        save.get("manager", ""),
                        save.get("club_id", ""),
                    ),
                )
            if not saves:
                self.page.status_label.config(text="No save files found.")
        except Exception as e:
            self.page.status_label.config(text=f"Error listing saves: {e}")

    def _load_save(self):
        """Load the selected save file and switch to career dashboard."""
        selection = self.page.saves_tree.selection()
        if not selection:
            self.page.status_label.config(text="Please select a save to load.")
            return

        save_name = selection[0]

        try:
            self.page.status_label.config(text=f"Loading '{save_name}'...")
            self.page.update_idletasks()

            game_state = self.save_manager.load_game(save_name)

            # Migrate save data if needed
            migration = SaveMigration()
            save_dict = game_state.__dict__ if hasattr(game_state, '__dict__') else {}
            if isinstance(save_dict, dict) and migration.needs_migration(save_dict):
                migrated = migration.migrate(save_dict)
                for key, value in migrated.items():
                    if hasattr(game_state, key):
                        setattr(game_state, key, value)
                self.page.status_label.config(
                    text=f"Save migrated from older version to {SaveMigration.CURRENT_VERSION}."
                )
                self.page.update_idletasks()

            # Create a CareerEngine and attach the loaded state
            career_engine = CareerEngine(self.controller.settings, self.controller.db)
            career_engine.game_state = game_state
            career_engine.is_game_active = True

            # Store on the main controller
            self.controller.career_engine = career_engine

            # Try to set current_user_team from clubs_data
            club_id = game_state.club_id
            for club in game_state.clubs_data:
                if club.get("id") == club_id:
                    self.controller.current_user_team = club
                    break

            self.page.status_label.config(text="Game loaded!")
            self.switch("career_dashboard")
        except FileNotFoundError:
            self.page.status_label.config(text=f"Save '{save_name}' not found.")
        except Exception as e:
            self.page.status_label.config(text=f"Error loading save: {e}")

    def _delete_save(self):
        """Confirm and delete the selected save file."""
        selection = self.page.saves_tree.selection()
        if not selection:
            self.page.status_label.config(text="Please select a save to delete.")
            return

        save_name = selection[0]

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete save '{save_name}'?",
        )
        if not confirm:
            return

        try:
            self.save_manager.delete_save(save_name)
            self.page.status_label.config(text=f"Save '{save_name}' deleted.")
            self._refresh_tree()
        except FileNotFoundError:
            self.page.status_label.config(text=f"Save '{save_name}' not found.")
        except Exception as e:
            self.page.status_label.config(text=f"Error deleting save: {e}")

    def switch(self, page: str):
        self.controller.switch(page)

    def _bind(self):
        self.page.load_btn.config(command=self._load_save)
        self.page.delete_btn.config(command=self._delete_save)
        self.page.cancel_btn.config(command=lambda: self.switch("home"))
