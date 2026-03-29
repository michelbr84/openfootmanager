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


class YouthAcademyPage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Row 0 - Title
        self.title_label = ttk.Label(
            self, text="Youth Academy", font="Arial 24 bold"
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky=W)

        # Row 1 - Info frame
        info_frame = ttk.Frame(self)
        info_frame.grid(row=1, column=0, padx=20, pady=5, sticky=EW)

        self.level_label = ttk.Label(
            info_frame, text="Academy Level: 1/5", font="Arial 12"
        )
        self.level_label.pack(side=LEFT, padx=(0, 20))

        self.prospects_label = ttk.Label(
            info_frame, text="Prospects: 0/3", font="Arial 12"
        )
        self.prospects_label.pack(side=LEFT, padx=(0, 20))

        self.upgrade_btn = ttk.Button(
            info_frame, text="Upgrade Academy", bootstyle="warning"
        )
        self.upgrade_btn.pack(side=LEFT, padx=(0, 10))

        # Row 2 - Prospects Treeview
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=2, column=0, padx=20, pady=10, sticky=NSEW)

        columns = ("#", "Name", "Age", "Position", "Overall", "Potential", "Development")
        self.prospects_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=10
        )

        col_widths = {
            "#": 40,
            "Name": 180,
            "Age": 50,
            "Position": 70,
            "Overall": 60,
            "Potential": 60,
            "Development": 80,
        }
        for col in columns:
            self.prospects_tree.heading(col, text=col)
            self.prospects_tree.column(col, width=col_widths[col], minwidth=col_widths[col])

        scrollbar = ttk.Scrollbar(
            tree_frame, orient=VERTICAL, command=self.prospects_tree.yview
        )
        self.prospects_tree.configure(yscrollcommand=scrollbar.set)

        self.prospects_tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Row 3 - Actions frame
        actions_frame = ttk.Frame(self)
        actions_frame.grid(row=3, column=0, padx=20, pady=10, sticky=EW)

        self.generate_btn = ttk.Button(
            actions_frame, text="Generate Prospects", bootstyle="primary"
        )
        self.generate_btn.pack(side=LEFT, padx=(0, 10))

        self.develop_btn = ttk.Button(
            actions_frame, text="Develop All", bootstyle="info"
        )
        self.develop_btn.pack(side=LEFT, padx=(0, 10))

        self.promote_btn = ttk.Button(
            actions_frame, text="Promote to Squad", bootstyle="success"
        )
        self.promote_btn.pack(side=LEFT, padx=(0, 10))

        self.release_btn = ttk.Button(
            actions_frame, text="Release", bootstyle="danger"
        )
        self.release_btn.pack(side=LEFT, padx=(0, 10))

        self.scout_btn = ttk.Button(
            actions_frame, text="Scout Report"
        )
        self.scout_btn.pack(side=LEFT, padx=(0, 10))

        # Row 4 - Scout report text area
        self.report_text = ttk.Text(self, height=6, state=DISABLED)
        self.report_text.grid(row=4, column=0, padx=20, pady=10, sticky=EW)

        # Row 5 - Status label
        self.status_label = ttk.Label(self, text="", font="Arial 11")
        self.status_label.grid(row=5, column=0, padx=20, pady=5, sticky=W)

        # Row 6 - Back button
        self.cancel_btn = ttk.Button(self, text="Back")
        self.cancel_btn.grid(row=6, column=0, padx=20, pady=(5, 20), sticky=W)

        # Make tree row expandable
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
