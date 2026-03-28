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


class EditPage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title_label = ttk.Label(self, text="Edit", font="Arial 24 bold")
        self.title_label.grid(row=0, column=0, padx=100, pady=10, sticky=NS)

        # Notebook with two tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, padx=10, pady=10, sticky=NSEW)

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # ---- Tab 1: Edit Player ----
        self.player_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.player_tab, text="Edit Player")
        self._build_player_tab()

        # ---- Tab 2: Edit Team ----
        self.team_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.team_tab, text="Edit Team")
        self._build_team_tab()

        # ---- Bottom: Back button ----
        self.cancel_btn = ttk.Button(self, text="Back")
        self.cancel_btn.grid(row=2, column=0, padx=10, pady=10, sticky=EW)

    # ------------------------------------------------------------------
    # Player tab
    # ------------------------------------------------------------------
    def _build_player_tab(self):
        tab = self.player_tab
        tab.columnconfigure(1, weight=1)

        # Player selector
        ttk.Label(tab, text="Select Player:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.player_combo = ttk.Combobox(tab, state="readonly", width=40)
        self.player_combo.grid(row=0, column=1, padx=5, pady=5, sticky=EW)

        # Top-level attributes row
        top_frame = ttk.Frame(tab)
        top_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=EW)

        ttk.Label(top_frame, text="Fitness:").grid(row=0, column=0, padx=5, pady=2, sticky=W)
        self.fitness_entry = ttk.Entry(top_frame, width=8)
        self.fitness_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(top_frame, text="Stamina:").grid(row=0, column=2, padx=5, pady=2, sticky=W)
        self.stamina_entry = ttk.Entry(top_frame, width=8)
        self.stamina_entry.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(top_frame, text="Form:").grid(row=0, column=4, padx=5, pady=2, sticky=W)
        self.form_entry = ttk.Entry(top_frame, width=8)
        self.form_entry.grid(row=0, column=5, padx=5, pady=2)

        # Scrollable area for attribute groups
        attr_frame = ttk.Frame(tab)
        attr_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=NSEW)
        tab.rowconfigure(2, weight=1)

        # Store all attribute entries in dicts for easy access
        self.offensive_entries = {}
        self.defensive_entries = {}
        self.physical_entries = {}
        self.intelligence_entries = {}
        self.gk_entries = {}

        # Offensive
        off_frame = ttk.LabelFrame(attr_frame, text="Offensive")
        off_frame.grid(row=0, column=0, padx=5, pady=5, sticky=NSEW)
        for i, attr in enumerate(["shot_power", "shot_accuracy", "free_kick", "penalty", "positioning"]):
            ttk.Label(off_frame, text=attr.replace("_", " ").title() + ":").grid(row=i, column=0, padx=5, pady=2, sticky=W)
            entry = ttk.Entry(off_frame, width=8)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.offensive_entries[attr] = entry

        # Defensive
        def_frame = ttk.LabelFrame(attr_frame, text="Defensive")
        def_frame.grid(row=0, column=1, padx=5, pady=5, sticky=NSEW)
        for i, attr in enumerate(["tackling", "interception", "positioning"]):
            ttk.Label(def_frame, text=attr.replace("_", " ").title() + ":").grid(row=i, column=0, padx=5, pady=2, sticky=W)
            entry = ttk.Entry(def_frame, width=8)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.defensive_entries[attr] = entry

        # Physical
        phys_frame = ttk.LabelFrame(attr_frame, text="Physical")
        phys_frame.grid(row=0, column=2, padx=5, pady=5, sticky=NSEW)
        for i, attr in enumerate(["strength", "aggression", "endurance"]):
            ttk.Label(phys_frame, text=attr.replace("_", " ").title() + ":").grid(row=i, column=0, padx=5, pady=2, sticky=W)
            entry = ttk.Entry(phys_frame, width=8)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.physical_entries[attr] = entry

        # Intelligence
        int_frame = ttk.LabelFrame(attr_frame, text="Intelligence")
        int_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=NSEW)
        for i, attr in enumerate(["vision", "passing", "crossing", "ball_control", "dribbling", "skills", "team_work"]):
            ttk.Label(int_frame, text=attr.replace("_", " ").title() + ":").grid(row=i, column=0, padx=5, pady=2, sticky=W)
            entry = ttk.Entry(int_frame, width=8)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.intelligence_entries[attr] = entry

        # GK
        gk_frame = ttk.LabelFrame(attr_frame, text="GK")
        gk_frame.grid(row=1, column=2, padx=5, pady=5, sticky=NSEW)
        for i, attr in enumerate(["reflexes", "jumping", "positioning", "penalty"]):
            ttk.Label(gk_frame, text=attr.replace("_", " ").title() + ":").grid(row=i, column=0, padx=5, pady=2, sticky=W)
            entry = ttk.Entry(gk_frame, width=8)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.gk_entries[attr] = entry

        # Save button
        self.save_player_btn = ttk.Button(tab, text="Save Player")
        self.save_player_btn.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky=EW)

    # ------------------------------------------------------------------
    # Team tab
    # ------------------------------------------------------------------
    def _build_team_tab(self):
        tab = self.team_tab
        tab.columnconfigure(1, weight=1)

        # Team selector
        ttk.Label(tab, text="Select Team:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.team_combo = ttk.Combobox(tab, state="readonly", width=40)
        self.team_combo.grid(row=0, column=1, padx=5, pady=5, sticky=EW)

        # Team name
        ttk.Label(tab, text="Team Name:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        self.team_name_entry = ttk.Entry(tab)
        self.team_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky=EW)

        # Stadium name
        ttk.Label(tab, text="Stadium:").grid(row=2, column=0, padx=5, pady=5, sticky=W)
        self.stadium_entry = ttk.Entry(tab)
        self.stadium_entry.grid(row=2, column=1, padx=5, pady=5, sticky=EW)

        # Capacity
        ttk.Label(tab, text="Capacity:").grid(row=3, column=0, padx=5, pady=5, sticky=W)
        self.capacity_entry = ttk.Entry(tab)
        self.capacity_entry.grid(row=3, column=1, padx=5, pady=5, sticky=EW)

        # Formation
        ttk.Label(tab, text="Formation:").grid(row=4, column=0, padx=5, pady=5, sticky=W)
        self.formation_combo = ttk.Combobox(tab, state="readonly", width=20)
        self.formation_combo.grid(row=4, column=1, padx=5, pady=5, sticky=W)

        # Save button
        self.save_team_btn = ttk.Button(tab, text="Save Team")
        self.save_team_btn.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky=EW)
