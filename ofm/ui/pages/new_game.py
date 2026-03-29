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


class NewGamePage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)

        # Title
        self.title_label = ttk.Label(self, text="New Game", font="Arial 24 bold")
        self.title_label.grid(row=0, column=0, columnspan=2, padx=100, pady=30, sticky=NS)

        # Manager Name
        self.manager_name_label = ttk.Label(self, text="Manager Name:")
        self.manager_name_label.grid(row=1, column=0, padx=10, pady=10, sticky=E)
        self.manager_name_entry = ttk.Entry(self)
        self.manager_name_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)

        # Select League
        self.league_label = ttk.Label(self, text="Select League:")
        self.league_label.grid(row=2, column=0, padx=10, pady=10, sticky=E)
        self.league_combo = ttk.Combobox(self, state="readonly")
        self.league_combo.grid(row=2, column=1, padx=10, pady=10, sticky=EW)

        # Select Club
        self.club_label = ttk.Label(self, text="Select Club:")
        self.club_label.grid(row=3, column=0, padx=10, pady=10, sticky=E)
        self.club_combo = ttk.Combobox(self, state="readonly")
        self.club_combo.grid(row=3, column=1, padx=10, pady=10, sticky=EW)

        # Club info frame
        self.club_info_frame = ttk.LabelFrame(self, text="Club Info")
        self.club_info_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky=EW)
        self.club_info_frame.columnconfigure(1, weight=1)

        self.stadium_label_title = ttk.Label(self.club_info_frame, text="Stadium:")
        self.stadium_label_title.grid(row=0, column=0, padx=10, pady=5, sticky=E)
        self.stadium_label = ttk.Label(self.club_info_frame, text="--")
        self.stadium_label.grid(row=0, column=1, padx=10, pady=5, sticky=W)

        self.capacity_label_title = ttk.Label(self.club_info_frame, text="Capacity:")
        self.capacity_label_title.grid(row=1, column=0, padx=10, pady=5, sticky=E)
        self.capacity_label = ttk.Label(self.club_info_frame, text="--")
        self.capacity_label.grid(row=1, column=1, padx=10, pady=5, sticky=W)

        self.squad_size_label_title = ttk.Label(self.club_info_frame, text="Squad Size:")
        self.squad_size_label_title.grid(row=2, column=0, padx=10, pady=5, sticky=E)
        self.squad_size_label = ttk.Label(self.club_info_frame, text="--")
        self.squad_size_label.grid(row=2, column=1, padx=10, pady=5, sticky=W)

        # Buttons frame
        self.buttons_frame = ttk.Frame(self)
        self.buttons_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=20, sticky=EW)
        self.buttons_frame.columnconfigure(0, weight=1)
        self.buttons_frame.columnconfigure(1, weight=1)

        self.start_btn = ttk.Button(self.buttons_frame, text="Start Career", bootstyle="success")
        self.start_btn.grid(row=0, column=0, padx=10, pady=10, sticky=EW)

        self.cancel_btn = ttk.Button(self.buttons_frame, text="Back")
        self.cancel_btn.grid(row=0, column=1, padx=10, pady=10, sticky=EW)

        # Status label
        self.status_label = ttk.Label(self, text="", anchor=CENTER)
        self.status_label.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky=EW)
