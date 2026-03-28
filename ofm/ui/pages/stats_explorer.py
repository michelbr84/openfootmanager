import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class StatsExplorerPage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Title
        self.title_label = ttk.Label(self, text="Stats Explorer", font="Arial 24 bold")
        self.title_label.grid(
            row=0, column=0, padx=10, pady=10, columnspan=2, sticky=NS
        )

        # Notebook with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(
            row=1, column=0, columnspan=2, padx=10, pady=5, sticky=NSEW
        )

        # Configure grid weights so notebook expands
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # =====================================================================
        # Tab 1: Player Rankings
        # =====================================================================
        self.tab_rankings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_rankings, text="Player Rankings")

        # Filter frame
        self.filter_frame = ttk.Labelframe(self.tab_rankings, text="Filters")
        self.filter_frame.pack(fill=X, padx=10, pady=(10, 5))

        ttk.Label(self.filter_frame, text="Position:").pack(side=LEFT, padx=(10, 2), pady=5)
        self.filter_position = ttk.Combobox(
            self.filter_frame,
            values=["All", "GK", "DF", "MF", "FW"],
            state="readonly",
            width=8,
        )
        self.filter_position.set("All")
        self.filter_position.pack(side=LEFT, padx=(0, 10), pady=5)

        ttk.Label(self.filter_frame, text="Sort by:").pack(side=LEFT, padx=(10, 2), pady=5)
        self.filter_sort_by = ttk.Combobox(
            self.filter_frame,
            values=["Overall", "Age", "Fitness", "Value"],
            state="readonly",
            width=10,
        )
        self.filter_sort_by.set("Overall")
        self.filter_sort_by.pack(side=LEFT, padx=(0, 10), pady=5)

        ttk.Label(self.filter_frame, text="Sort order:").pack(side=LEFT, padx=(10, 2), pady=5)
        self.filter_sort_order = ttk.Combobox(
            self.filter_frame,
            values=["Descending", "Ascending"],
            state="readonly",
            width=12,
        )
        self.filter_sort_order.set("Descending")
        self.filter_sort_order.pack(side=LEFT, padx=(0, 10), pady=5)

        self.apply_filter_btn = ttk.Button(self.filter_frame, text="Apply", bootstyle=PRIMARY)
        self.apply_filter_btn.pack(side=LEFT, padx=10, pady=5)

        # Treeview frame with scrollbar
        self.rankings_tree_frame = ttk.Frame(self.tab_rankings)
        self.rankings_tree_frame.pack(fill=BOTH, expand=True, padx=10, pady=(5, 10))

        self.rankings_tree = ttk.Treeview(
            self.rankings_tree_frame,
            columns=("rank", "name", "club", "age", "position", "overall", "fitness", "value"),
            show="headings",
        )

        self.rankings_tree.heading("rank", text="#")
        self.rankings_tree.heading("name", text="Name")
        self.rankings_tree.heading("club", text="Club")
        self.rankings_tree.heading("age", text="Age")
        self.rankings_tree.heading("position", text="Position")
        self.rankings_tree.heading("overall", text="Overall")
        self.rankings_tree.heading("fitness", text="Fitness")
        self.rankings_tree.heading("value", text="Value")

        self.rankings_tree.column("rank", width=40, anchor=CENTER)
        self.rankings_tree.column("name", width=180, anchor=W)
        self.rankings_tree.column("club", width=150, anchor=W)
        self.rankings_tree.column("age", width=50, anchor=CENTER)
        self.rankings_tree.column("position", width=60, anchor=CENTER)
        self.rankings_tree.column("overall", width=60, anchor=CENTER)
        self.rankings_tree.column("fitness", width=60, anchor=CENTER)
        self.rankings_tree.column("value", width=100, anchor=E)

        self.rankings_scrollbar = ttk.Scrollbar(
            self.rankings_tree_frame, orient=VERTICAL, command=self.rankings_tree.yview
        )
        self.rankings_tree.configure(yscrollcommand=self.rankings_scrollbar.set)

        self.rankings_tree.pack(side=LEFT, fill=BOTH, expand=True)
        self.rankings_scrollbar.pack(side=RIGHT, fill=Y)

        # =====================================================================
        # Tab 2: Team Comparison
        # =====================================================================
        self.tab_comparison = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_comparison, text="Team Comparison")

        # Selection frame
        self.comparison_select_frame = ttk.Frame(self.tab_comparison)
        self.comparison_select_frame.pack(fill=X, padx=10, pady=10)

        ttk.Label(self.comparison_select_frame, text="Team A:").pack(side=LEFT, padx=(10, 2), pady=5)
        self.team_a_combo = ttk.Combobox(
            self.comparison_select_frame, state="readonly", width=20
        )
        self.team_a_combo.pack(side=LEFT, padx=(0, 10), pady=5)

        ttk.Label(self.comparison_select_frame, text="Team B:").pack(side=LEFT, padx=(10, 2), pady=5)
        self.team_b_combo = ttk.Combobox(
            self.comparison_select_frame, state="readonly", width=20
        )
        self.team_b_combo.pack(side=LEFT, padx=(0, 10), pady=5)

        self.compare_btn = ttk.Button(
            self.comparison_select_frame, text="Compare", bootstyle=PRIMARY
        )
        self.compare_btn.pack(side=LEFT, padx=10, pady=5)

        # Comparison results treeview
        self.comparison_result_frame = ttk.Labelframe(self.tab_comparison, text="Comparison Results")
        self.comparison_result_frame.pack(fill=BOTH, expand=True, padx=10, pady=(5, 10))

        self.comparison_tree = ttk.Treeview(
            self.comparison_result_frame,
            columns=("stat", "team_a", "team_b"),
            show="headings",
        )

        self.comparison_tree.heading("stat", text="Stat")
        self.comparison_tree.heading("team_a", text="Team A")
        self.comparison_tree.heading("team_b", text="Team B")

        self.comparison_tree.column("stat", width=200, anchor=W)
        self.comparison_tree.column("team_a", width=150, anchor=CENTER)
        self.comparison_tree.column("team_b", width=150, anchor=CENTER)

        self.comparison_tree.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # =====================================================================
        # Tab 3: Top Performers
        # =====================================================================
        self.tab_top = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_top, text="Top Performers")

        # Top Scorers (by Overall)
        self.top_scorers_frame = ttk.Labelframe(self.tab_top, text="Top Scorers (by Overall)")
        self.top_scorers_frame.pack(fill=BOTH, expand=True, padx=10, pady=(10, 5))

        self.top_scorers_tree = ttk.Treeview(
            self.top_scorers_frame,
            columns=("name", "club", "overall"),
            show="headings",
            height=5,
        )
        self.top_scorers_tree.heading("name", text="Name")
        self.top_scorers_tree.heading("club", text="Club")
        self.top_scorers_tree.heading("overall", text="Overall")
        self.top_scorers_tree.column("name", width=180, anchor=W)
        self.top_scorers_tree.column("club", width=150, anchor=W)
        self.top_scorers_tree.column("overall", width=80, anchor=CENTER)
        self.top_scorers_tree.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Best Youngsters (U21)
        self.top_youngsters_frame = ttk.Labelframe(self.tab_top, text="Best Youngsters (U21)")
        self.top_youngsters_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        self.top_youngsters_tree = ttk.Treeview(
            self.top_youngsters_frame,
            columns=("name", "club", "age", "overall"),
            show="headings",
            height=5,
        )
        self.top_youngsters_tree.heading("name", text="Name")
        self.top_youngsters_tree.heading("club", text="Club")
        self.top_youngsters_tree.heading("age", text="Age")
        self.top_youngsters_tree.heading("overall", text="Overall")
        self.top_youngsters_tree.column("name", width=180, anchor=W)
        self.top_youngsters_tree.column("club", width=150, anchor=W)
        self.top_youngsters_tree.column("age", width=50, anchor=CENTER)
        self.top_youngsters_tree.column("overall", width=80, anchor=CENTER)
        self.top_youngsters_tree.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Most Valuable
        self.top_valuable_frame = ttk.Labelframe(self.tab_top, text="Most Valuable")
        self.top_valuable_frame.pack(fill=BOTH, expand=True, padx=10, pady=(5, 10))

        self.top_valuable_tree = ttk.Treeview(
            self.top_valuable_frame,
            columns=("name", "club", "value"),
            show="headings",
            height=5,
        )
        self.top_valuable_tree.heading("name", text="Name")
        self.top_valuable_tree.heading("club", text="Club")
        self.top_valuable_tree.heading("value", text="Value")
        self.top_valuable_tree.column("name", width=180, anchor=W)
        self.top_valuable_tree.column("club", width=150, anchor=W)
        self.top_valuable_tree.column("value", width=100, anchor=E)
        self.top_valuable_tree.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # =====================================================================
        # Bottom: Back button
        # =====================================================================
        self.button_frame = ttk.Frame(self)
        self.cancel_btn = ttk.Button(self.button_frame, text="Back")
        self.cancel_btn.pack(side=LEFT, padx=10)

        self.button_frame.grid(
            row=2, column=0, columnspan=2, padx=10, pady=10, sticky=NS
        )
