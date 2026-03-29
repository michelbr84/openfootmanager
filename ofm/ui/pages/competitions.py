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


class CompetitionsPage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        # Title
        title = ttk.Label(self, text="Competitions", font="Arial 20 bold")
        title.grid(row=0, column=0, padx=10, pady=(10, 5), sticky=W)

        # Notebook with competition tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, padx=10, pady=5, sticky=NSEW)

        # ==============================================================
        # Tab 1: Domestic Cup
        # ==============================================================
        cup_frame = ttk.Frame(self.notebook)
        cup_frame.columnconfigure(0, weight=1)
        cup_frame.rowconfigure(0, weight=1)
        cup_frame.rowconfigure(1, weight=0)
        self.notebook.add(cup_frame, text="Domestic Cup")

        cup_cols = ("Round", "Home", "Score", "Away")
        self.cup_tree = ttk.Treeview(
            cup_frame, columns=cup_cols, show="headings", height=8
        )
        for col in cup_cols:
            w = 60 if col == "Round" else (80 if col == "Score" else 160)
            self.cup_tree.heading(col, text=col)
            self.cup_tree.column(col, width=w, minwidth=40)
        self.cup_tree.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        cup_scroll = ttk.Scrollbar(
            cup_frame, orient=VERTICAL, command=self.cup_tree.yview
        )
        cup_scroll.grid(row=0, column=1, sticky=NS)
        self.cup_tree.configure(yscrollcommand=cup_scroll.set)

        self.sim_cup_btn = ttk.Button(
            cup_frame, text="Simulate Round", bootstyle="primary"
        )
        self.sim_cup_btn.grid(row=1, column=0, padx=5, pady=5, sticky=EW)

        # ==============================================================
        # Tab 2: Continental
        # ==============================================================
        continental_frame = ttk.Frame(self.notebook)
        continental_frame.columnconfigure(0, weight=1)
        continental_frame.rowconfigure(0, weight=1)
        continental_frame.rowconfigure(1, weight=0)
        continental_frame.rowconfigure(2, weight=1)
        self.notebook.add(continental_frame, text="Continental")

        # Group stage standings
        cont_cols = ("Group", "Team", "P", "W", "D", "L", "Pts")
        self.continental_tree = ttk.Treeview(
            continental_frame, columns=cont_cols, show="headings", height=8
        )
        for col in cont_cols:
            w = 50 if col != "Team" else 160
            self.continental_tree.heading(col, text=col)
            self.continental_tree.column(col, width=w, minwidth=30)
        self.continental_tree.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        cont_scroll = ttk.Scrollbar(
            continental_frame, orient=VERTICAL, command=self.continental_tree.yview
        )
        cont_scroll.grid(row=0, column=1, sticky=NS)
        self.continental_tree.configure(yscrollcommand=cont_scroll.set)

        self.sim_continental_btn = ttk.Button(
            continental_frame, text="Simulate Group Stage", bootstyle="primary"
        )
        self.sim_continental_btn.grid(row=1, column=0, padx=5, pady=5, sticky=EW)

        # Knockout bracket
        ko_cols = ("Round", "Home", "Score", "Away")
        self.knockout_tree = ttk.Treeview(
            continental_frame, columns=ko_cols, show="headings", height=6
        )
        for col in ko_cols:
            w = 60 if col == "Round" else (80 if col == "Score" else 160)
            self.knockout_tree.heading(col, text=col)
            self.knockout_tree.column(col, width=w, minwidth=40)
        self.knockout_tree.grid(row=2, column=0, sticky=NSEW, padx=5, pady=5)

        ko_scroll = ttk.Scrollbar(
            continental_frame, orient=VERTICAL, command=self.knockout_tree.yview
        )
        ko_scroll.grid(row=2, column=1, sticky=NS)
        self.knockout_tree.configure(yscrollcommand=ko_scroll.set)

        # ==============================================================
        # Tab 3: Divisions
        # ==============================================================
        div_frame = ttk.Frame(self.notebook)
        div_frame.columnconfigure(0, weight=1)
        div_frame.rowconfigure(0, weight=1)
        div_frame.rowconfigure(1, weight=0)
        self.notebook.add(div_frame, text="Divisions")

        div_cols = ("Div", "Pos", "Team", "P", "W", "D", "L", "Pts")
        self.division_tree = ttk.Treeview(
            div_frame, columns=div_cols, show="headings", height=10
        )
        for col in div_cols:
            w = 40 if col not in ("Team",) else 160
            self.division_tree.heading(col, text=col)
            self.division_tree.column(col, width=w, minwidth=30)
        self.division_tree.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        div_scroll = ttk.Scrollbar(
            div_frame, orient=VERTICAL, command=self.division_tree.yview
        )
        div_scroll.grid(row=0, column=1, sticky=NS)
        self.division_tree.configure(yscrollcommand=div_scroll.set)

        self.promo_label = ttk.Label(
            div_frame, text="Promoted / Relegated: --", font=("Arial", 10)
        )
        self.promo_label.grid(row=1, column=0, padx=5, pady=5, sticky=W)

        # ==============================================================
        # Tab 4: International
        # ==============================================================
        intl_frame = ttk.Frame(self.notebook)
        intl_frame.columnconfigure(0, weight=1)
        intl_frame.rowconfigure(0, weight=1)
        intl_frame.rowconfigure(1, weight=0)
        self.notebook.add(intl_frame, text="International")

        intl_cols = ("Stage", "Team A", "Score", "Team B")
        self.international_tree = ttk.Treeview(
            intl_frame, columns=intl_cols, show="headings", height=8
        )
        for col in intl_cols:
            w = 80 if col in ("Stage", "Score") else 160
            self.international_tree.heading(col, text=col)
            self.international_tree.column(col, width=w, minwidth=40)
        self.international_tree.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        intl_scroll = ttk.Scrollbar(
            intl_frame, orient=VERTICAL, command=self.international_tree.yview
        )
        intl_scroll.grid(row=0, column=1, sticky=NS)
        self.international_tree.configure(yscrollcommand=intl_scroll.set)

        self.sim_intl_btn = ttk.Button(
            intl_frame, text="Simulate Tournament", bootstyle="primary"
        )
        self.sim_intl_btn.grid(row=1, column=0, padx=5, pady=5, sticky=EW)

        # ==============================================================
        # Bottom bar
        # ==============================================================
        bottom = ttk.Frame(self)
        bottom.grid(row=2, column=0, padx=10, pady=(5, 10), sticky=EW)
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=0)

        self.status_label = ttk.Label(bottom, text="Ready")
        self.status_label.grid(row=0, column=0, sticky=W, padx=5)

        self.cancel_btn = ttk.Button(bottom, text="Back")
        self.cancel_btn.grid(row=0, column=1, sticky=E, padx=5)
