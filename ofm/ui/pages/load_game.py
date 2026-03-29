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


class LoadGamePage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.columnconfigure(0, weight=1)

        # Title
        self.title_label = ttk.Label(self, text="Load Game", font="Arial 24 bold")
        self.title_label.grid(row=0, column=0, padx=100, pady=30, sticky=NS)

        # Treeview for save files
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky=NSEW)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        columns = ("Name", "Date", "Manager", "Season")
        self.saves_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse"
        )
        for col in columns:
            self.saves_tree.heading(col, text=col)
            self.saves_tree.column(col, width=150, anchor=W)
        self.saves_tree.grid(row=0, column=0, sticky=NSEW)

        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.saves_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=NS)
        self.saves_tree.configure(yscrollcommand=scrollbar.set)

        # Buttons frame
        self.buttons_frame = ttk.Frame(self)
        self.buttons_frame.grid(row=2, column=0, padx=10, pady=10, sticky=EW)
        self.buttons_frame.columnconfigure(0, weight=1)
        self.buttons_frame.columnconfigure(1, weight=1)
        self.buttons_frame.columnconfigure(2, weight=1)

        self.load_btn = ttk.Button(self.buttons_frame, text="Load", bootstyle="success")
        self.load_btn.grid(row=0, column=0, padx=10, pady=10, sticky=EW)

        self.delete_btn = ttk.Button(self.buttons_frame, text="Delete", bootstyle="danger")
        self.delete_btn.grid(row=0, column=1, padx=10, pady=10, sticky=EW)

        self.cancel_btn = ttk.Button(self.buttons_frame, text="Back")
        self.cancel_btn.grid(row=0, column=2, padx=10, pady=10, sticky=EW)

        # Status label
        self.status_label = ttk.Label(self, text="", anchor=CENTER)
        self.status_label.grid(row=3, column=0, padx=10, pady=5, sticky=EW)
