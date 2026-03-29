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


class PlayerComparisonPage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        # Row 0 - Title
        self.title_label = ttk.Label(
            self, text="Player Comparison", font="Arial 24 bold"
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky=W)

        # Row 1 - Player selectors
        selector_frame = ttk.Frame(self)
        selector_frame.grid(row=1, column=0, padx=20, pady=5, sticky=EW)
        selector_frame.columnconfigure(1, weight=1)
        selector_frame.columnconfigure(3, weight=1)

        ttk.Label(selector_frame, text="Player A:").grid(
            row=0, column=0, padx=(0, 5), sticky=W
        )
        self.player_a_combo = ttk.Combobox(selector_frame, state="readonly")
        self.player_a_combo.grid(row=0, column=1, padx=(0, 15), sticky=EW)

        ttk.Label(selector_frame, text="Player B:").grid(
            row=0, column=2, padx=(0, 5), sticky=W
        )
        self.player_b_combo = ttk.Combobox(selector_frame, state="readonly")
        self.player_b_combo.grid(row=0, column=3, padx=(0, 5), sticky=EW)

        # Row 2 - Compare button
        self.compare_btn = ttk.Button(
            self, text="Compare", bootstyle="primary"
        )
        self.compare_btn.grid(row=2, column=0, padx=20, pady=5, sticky=EW)

        # Row 3 - Comparison Treeview
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=3, column=0, padx=20, pady=10, sticky=NSEW)

        columns = ("Attribute", "Player A", "Player B")
        self.compare_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=20
        )

        col_widths = {"Attribute": 200, "Player A": 120, "Player B": 120}
        for col in columns:
            self.compare_tree.heading(col, text=col)
            self.compare_tree.column(col, width=col_widths[col], minwidth=80)

        scrollbar = ttk.Scrollbar(
            tree_frame, orient=VERTICAL, command=self.compare_tree.yview
        )
        self.compare_tree.configure(yscrollcommand=scrollbar.set)

        self.compare_tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Row 4 - Back button
        self.cancel_btn = ttk.Button(self, text="Back")
        self.cancel_btn.grid(row=4, column=0, padx=20, pady=(5, 20), sticky=W)
