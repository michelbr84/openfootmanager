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


class HomePage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Center the layout by configuring column weight
        self.columnconfigure(0, weight=1)

        self.logo = ttk.PhotoImage(file="ofm/res/images/openfoot.png")

        self.logo_label = ttk.Label(self, image=self.logo, anchor=CENTER)
        self.logo_label.grid(row=0, column=0, padx=20, pady=75, sticky=NSEW)

        self.debug_mode_btn = ttk.Button(self, text="Start Debug Mode")
        self.debug_mode_btn.grid(row=1, column=0, padx=120, pady=15, sticky=NSEW)

        self.new_game_btn = ttk.Button(self, text="New Game")
        self.new_game_btn.grid(row=2, column=0, padx=120, pady=15, sticky=NSEW)

        self.load_game_btn = ttk.Button(self, text="Load Game")
        self.load_game_btn.grid(row=3, column=0, padx=120, pady=15, sticky=NSEW)

        self.settings_btn = ttk.Button(self, text="Settings")
        self.settings_btn.grid(row=4, column=0, padx=120, pady=15, sticky=NSEW)

        self.version_label = ttk.Label(
            self, text="v0.2.0 - Debug Mode", font=("TkDefaultFont", 9),
            anchor=CENTER, foreground="gray"
        )
        self.version_label.grid(row=5, column=0, padx=20, pady=(30, 10), sticky=EW)
