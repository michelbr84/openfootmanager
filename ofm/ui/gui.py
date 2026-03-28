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
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.themes.user import USER_THEMES

from .pages import *

USER_THEMES["football"] = {
    "type": "light",
    "colors": {
        "primary": "#56c2ad",
        "secondary": "#6bc49a",
        "success": "#29cc24",
        "info": "#5968d5",
        "warning": "#666e67",
        "danger": "#007851",
        "light": "#f1fffc",
        "dark": "#514c50",
        "bg": "#ffffff",
        "fg": "#5a5a5a",
        "selectbg": "#56c2ad",
        "selectfg": "#f1ffee",
        "border": "#ced4da",
        "inputfg": "#696969",
        "inputbg": "#ffffff",
        "active": "#e5e5e5",
    },
}

USER_THEMES["darkfootball"] = {
    "type": "dark",
    "colors": {
        "primary": "#00bc8c",
        "secondary": "#0c4444",
        "success": "#00bcd1",
        "info": "#3498db",
        "warning": "#f39c12",
        "danger": "#e74c3c",
        "light": "#ADB5BD",
        "dark": "#303030",
        "bg": "#222222",
        "fg": "#ffffff",
        "selectbg": "#555555",
        "selectfg": "#ffffff",
        "border": "#222222",
        "inputfg": "#ffffff",
        "inputbg": "#2f2f2f",
        "active": "#1F1F1F",
    },
}


class GUI:
    def __init__(self):
        self.window = ttk.Window(title="OpenFoot Manager", themename="darkfootball")

        width = 1360
        height = 968

        self.window.minsize(width, height)
        self.window.geometry("")
        self.window.resizable(True, True)
        self.fix_scaling()

        self.window.rowconfigure(0, weight=1)
        self.window.columnconfigure(0, weight=1)

        # Keyboard shortcut: Escape to go back to home
        self._page_history = []
        self.window.bind("<Escape>", self._on_escape)

        self.style = ttk.Style()

        self.pages = {
            "home": self._add_frame(HomePage),
            "debug_home": self._add_frame(DebugHomePage),
            "debug_match": self._add_frame(DebugMatchPage),
            "team_selection": self._add_frame(TeamSelectionPage),
            "settings": self._add_frame(SettingsPage),
            "player_profile": self._add_frame(PlayerProfilePage),
            "team_explorer": self._add_frame(TeamExplorerPage),
            "finances": self._add_frame(FinancesPage),
            "league": self._add_frame(LeaguePage),
            "market": self._add_frame(MarketPage),
            "training": self._add_frame(TrainingPage),
            "visualizer": self._add_frame(VisualizerPage),
            "team_formation": self._add_frame(TeamFormationPage),
            "championship": self._add_frame(ChampionshipPage),
            "stats_explorer": self._add_frame(StatsExplorerPage),
            "edit": self._add_frame(EditPage),
        }

        # Reverse lookup: frame -> page name
        self._page_names = {v: k for k, v in self.pages.items()}

        self.current_page = self.pages["home"]

        # Status bar at the bottom of the window
        self.status_bar = ttk.Label(self.window, text="Ready", relief="sunken", anchor=W)
        self.status_bar.grid(row=1, column=0, sticky=EW)

    def fix_scaling(self):
        import tkinter.font

        scaling = float(self.window.call("tk", "scaling"))
        if scaling > 1.4:
            for name in tkinter.font.names(self.window):
                font = tkinter.font.Font(root=self.window, name=name, exists=True)
                size = int(font["size"])
                if size < 0:
                    font["size"] = round(-0.75 * size)

    def _add_frame(self, frame) -> ttk.Frame:
        f = frame(self.window)
        return f

    def _on_escape(self, event=None):
        """Handle Escape key: go back to the previous page, or home if no history."""
        if self._page_history:
            previous = self._page_history.pop()
            self.current_page.grid_forget()
            self.current_page = self.pages[previous]
            self.current_page.grid(row=0, column=0)
            self.window.geometry("")
            self.current_page.tkraise()
            self.update_status(f"Navigated back to {previous}")
        elif self._page_names.get(self.current_page) != "home":
            self.switch("home")

    def update_status(self, text: str):
        """Update the status bar text."""
        self.status_bar.config(text=text)

    def switch(self, name: str):
        # Record current page in history for Escape navigation
        current_name = self._page_names.get(self.current_page)
        if current_name and current_name != name:
            self._page_history.append(current_name)

        self.current_page.grid_forget()
        self.current_page = self.pages[name]
        self.current_page.grid(row=0, column=0)
        self.window.geometry("")
        self.current_page.tkraise()
        self.update_status(f"Page: {name}")
