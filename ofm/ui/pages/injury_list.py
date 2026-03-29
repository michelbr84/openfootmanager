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


class InjuryListPage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Row 0 - Title
        self.title_label = ttk.Label(
            self, text="Medical Center", font="Arial 24 bold"
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky=W)

        # Row 1 - Check recoveries button
        actions_frame = ttk.Frame(self)
        actions_frame.grid(row=1, column=0, padx=20, pady=5, sticky=EW)

        self.check_btn = ttk.Button(
            actions_frame, text="Check Recoveries", bootstyle="primary"
        )
        self.check_btn.pack(side=LEFT, padx=(0, 10))

        # Row 2 - Injury Treeview
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=2, column=0, padx=20, pady=10, sticky=NSEW)

        columns = ("Player", "Injury", "Severity", "Days Left", "Return Date")
        self.injury_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=10
        )

        col_widths = {
            "Player": 180,
            "Injury": 180,
            "Severity": 100,
            "Days Left": 80,
            "Return Date": 120,
        }
        for col in columns:
            self.injury_tree.heading(col, text=col)
            self.injury_tree.column(col, width=col_widths[col], minwidth=60)

        scrollbar = ttk.Scrollbar(
            tree_frame, orient=VERTICAL, command=self.injury_tree.yview
        )
        self.injury_tree.configure(yscrollcommand=scrollbar.set)

        self.injury_tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Row 3 - Status label
        self.status_label = ttk.Label(self, text="", font="Arial 11")
        self.status_label.grid(row=3, column=0, padx=20, pady=5, sticky=W)

        # Row 4 - Back button
        self.cancel_btn = ttk.Button(self, text="Back")
        self.cancel_btn.grid(row=4, column=0, padx=20, pady=(5, 20), sticky=W)
