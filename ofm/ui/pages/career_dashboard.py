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


class CareerDashboardPage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # ==================================================================
        # Top bar (row 0, columnspan 2)
        # ==================================================================
        top_bar = ttk.Frame(self)
        top_bar.grid(row=0, column=0, columnspan=2, sticky=EW, padx=10, pady=(10, 5))
        top_bar.columnconfigure(0, weight=1)
        top_bar.columnconfigure(1, weight=1)
        top_bar.columnconfigure(2, weight=1)
        top_bar.columnconfigure(3, weight=1)

        self.manager_label = ttk.Label(
            top_bar, text="Manager: --", font=("Arial", 14)
        )
        self.manager_label.grid(row=0, column=0, sticky=W, padx=5)

        self.club_label = ttk.Label(
            top_bar, text="Club: --", font=("Arial", 14, "bold")
        )
        self.club_label.grid(row=0, column=1, sticky=W, padx=5)

        self.date_label = ttk.Label(top_bar, text="Date: --")
        self.date_label.grid(row=0, column=2, sticky=E, padx=5)

        self.balance_label = ttk.Label(top_bar, text="Balance: --")
        self.balance_label.grid(row=0, column=3, sticky=E, padx=5)

        # ==================================================================
        # Left column (row 1, col 0) -- Info panels
        # ==================================================================
        left_col = ttk.Frame(self)
        left_col.grid(row=1, column=0, sticky=NSEW, padx=(10, 5), pady=5)
        left_col.columnconfigure(0, weight=1)
        left_col.rowconfigure(0, weight=3)
        left_col.rowconfigure(1, weight=1)
        left_col.rowconfigure(2, weight=1)

        # -- League Standings --
        standings_frame = ttk.LabelFrame(left_col, text="League Standings")
        standings_frame.grid(row=0, column=0, sticky=NSEW, pady=(0, 5))
        standings_frame.columnconfigure(0, weight=1)
        standings_frame.rowconfigure(0, weight=1)

        standings_cols = ("Pos", "Team", "P", "W", "D", "L", "Pts")
        self.standings_tree = ttk.Treeview(
            standings_frame,
            columns=standings_cols,
            show="headings",
            height=8,
        )
        for col in standings_cols:
            width = 40 if col != "Team" else 160
            self.standings_tree.heading(col, text=col)
            self.standings_tree.column(col, width=width, minwidth=30)
        self.standings_tree.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        standings_scroll = ttk.Scrollbar(
            standings_frame, orient=VERTICAL, command=self.standings_tree.yview
        )
        standings_scroll.grid(row=0, column=1, sticky=NS)
        self.standings_tree.configure(yscrollcommand=standings_scroll.set)

        # -- Upcoming Fixtures --
        fixtures_frame = ttk.LabelFrame(left_col, text="Upcoming Fixtures")
        fixtures_frame.grid(row=1, column=0, sticky=NSEW, pady=(0, 5))
        fixtures_frame.columnconfigure(0, weight=1)
        fixtures_frame.rowconfigure(0, weight=1)

        fixtures_cols = ("Date", "Home", "Away")
        self.fixtures_tree = ttk.Treeview(
            fixtures_frame,
            columns=fixtures_cols,
            show="headings",
            height=3,
        )
        for col in fixtures_cols:
            self.fixtures_tree.heading(col, text=col)
            self.fixtures_tree.column(col, width=120, minwidth=60)
        self.fixtures_tree.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        # -- Recent Results --
        results_frame = ttk.LabelFrame(left_col, text="Recent Results")
        results_frame.grid(row=2, column=0, sticky=NSEW)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        results_cols = ("Date", "Home", "Score", "Away")
        self.results_tree = ttk.Treeview(
            results_frame,
            columns=results_cols,
            show="headings",
            height=3,
        )
        for col in results_cols:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=100, minwidth=50)
        self.results_tree.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        # ==================================================================
        # Right column (row 1, col 1) -- News & Actions
        # ==================================================================
        right_col = ttk.Frame(self)
        right_col.grid(row=1, column=1, sticky=NSEW, padx=(5, 10), pady=5)
        right_col.columnconfigure(0, weight=1)
        right_col.rowconfigure(0, weight=1)
        right_col.rowconfigure(1, weight=0)

        # -- News Feed --
        news_frame = ttk.LabelFrame(right_col, text="News Feed")
        news_frame.grid(row=0, column=0, sticky=NSEW, pady=(0, 5))
        news_frame.columnconfigure(0, weight=1)
        news_frame.rowconfigure(0, weight=1)

        self.news_text = ttk.Text(news_frame, height=12, state=DISABLED, wrap="word")
        self.news_text.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        news_scroll = ttk.Scrollbar(
            news_frame, orient=VERTICAL, command=self.news_text.yview
        )
        news_scroll.grid(row=0, column=1, sticky=NS)
        self.news_text.configure(yscrollcommand=news_scroll.set)

        # -- Quick Actions --
        actions_frame = ttk.LabelFrame(right_col, text="Quick Actions")
        actions_frame.grid(row=1, column=0, sticky=NSEW)
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)

        self.advance_btn = ttk.Button(
            actions_frame, text="Advance Day", bootstyle="primary"
        )
        self.advance_btn.grid(row=0, column=0, padx=5, pady=5, sticky=EW)

        self.play_match_btn = ttk.Button(
            actions_frame, text="Play Next Match", bootstyle="success"
        )
        self.play_match_btn.grid(row=0, column=1, padx=5, pady=5, sticky=EW)

        self.training_btn = ttk.Button(actions_frame, text="Training")
        self.training_btn.grid(row=1, column=0, padx=5, pady=5, sticky=EW)

        self.transfers_btn = ttk.Button(actions_frame, text="Transfers")
        self.transfers_btn.grid(row=1, column=1, padx=5, pady=5, sticky=EW)

        self.youth_btn = ttk.Button(actions_frame, text="Youth Academy")
        self.youth_btn.grid(row=2, column=0, padx=5, pady=5, sticky=EW)

        self.formation_btn = ttk.Button(actions_frame, text="Formation")
        self.formation_btn.grid(row=2, column=1, padx=5, pady=5, sticky=EW)

        self.save_btn = ttk.Button(
            actions_frame, text="Save Game", bootstyle="info"
        )
        self.save_btn.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=EW)

        # ==================================================================
        # Bottom (row 2, columnspan 2)
        # ==================================================================
        self.back_btn = ttk.Button(self, text="Back to Main Menu")
        self.back_btn.grid(
            row=2, column=0, columnspan=2, padx=10, pady=(5, 10), sticky=EW
        )
