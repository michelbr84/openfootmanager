import datetime

from ..pages.stats_explorer import StatsExplorerPage
from .controllerinterface import ControllerInterface


class StatsExplorerController(ControllerInterface):
    POSITION_MAP = {1: "GK", 2: "DF", 3: "MF", 4: "FW"}

    def __init__(self, controller: ControllerInterface, page: StatsExplorerPage):
        self.controller = controller
        self.page = page
        self._players_data = []
        self._clubs = []
        self._player_club_map = {}
        self._bind()

    def _bind(self):
        self.page.cancel_btn.config(command=self.go_to_debug_home_page)
        self.page.apply_filter_btn.config(command=self._apply_filters)
        self.page.compare_btn.config(command=self._compare_teams)

    def initialize(self):
        self.controller.db.check_clubs_file(amount=50)
        self._clubs = self.controller.db.load_clubs()
        players = self.controller.db.load_players()

        # Build player_id -> club_name lookup
        self._player_club_map = {}
        for club in self._clubs:
            for pid in club.get("squad", []):
                self._player_club_map[pid] = club["name"]

        # Build enriched player data
        today = datetime.date.today()
        self._players_data = []
        for p in players:
            positions = p.get("positions", [])
            primary_pos = positions[0] if positions else 3  # default MF
            overall = self._calculate_overall(p.get("attributes", {}), primary_pos)
            dob = p.get("dob", "2000-01-01")
            try:
                birth = datetime.date.fromisoformat(dob)
                age = (today - birth).days // 365
            except (ValueError, TypeError):
                age = 0

            self._players_data.append({
                "id": p.get("id", 0),
                "name": p.get("short_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
                "club": self._player_club_map.get(p.get("id", 0), "Free Agent"),
                "age": age,
                "position": self._get_position_name(primary_pos),
                "overall": round(overall, 1),
                "fitness": round(p.get("fitness", 0.0), 1),
                "value": p.get("value", 0.0),
            })

        # Populate player rankings with default sort
        self._populate_rankings()

        # Populate team combos
        club_names = sorted([c["name"] for c in self._clubs])
        self.page.team_a_combo["values"] = club_names
        self.page.team_b_combo["values"] = club_names
        if club_names:
            self.page.team_a_combo.set(club_names[0])
            self.page.team_b_combo.set(club_names[min(1, len(club_names) - 1)])

        # Populate top performers
        self._populate_top_performers()

    def _calculate_overall(self, attributes: dict, position: int) -> float:
        off_attrs = attributes.get("offensive", {})
        phys_attrs = attributes.get("physical", {})
        def_attrs = attributes.get("defensive", {})
        int_attrs = attributes.get("intelligence", {})
        gk_attrs = attributes.get("gk", {})

        def avg(d):
            vals = list(d.values())
            return sum(vals) / len(vals) if vals else 0.0

        off = avg(off_attrs)
        phys = avg(phys_attrs)
        defn = avg(def_attrs)
        intl = avg(int_attrs)
        gk = avg(gk_attrs)

        if position == 4:  # FW
            return (defn * 1 + phys * 1 + intl * 2 + off * 3) / 7
        elif position == 3:  # MF
            return (defn * 1 + phys * 2 + intl * 3 + off * 1) / 7
        elif position == 2:  # DF
            return (defn * 3 + phys * 2 + intl * 1 + off * 1) / 7
        elif position == 1:  # GK
            return (gk * 3 + defn * 2 + phys * 1 + intl * 1) / 7
        else:
            return (defn + phys + intl + off) / 4

    @staticmethod
    def _get_position_name(position: int) -> str:
        return StatsExplorerController.POSITION_MAP.get(position, "MF")

    def _populate_rankings(self, data=None):
        tree = self.page.rankings_tree
        for item in tree.get_children():
            tree.delete(item)

        rows = data if data is not None else self._players_data
        for rank, p in enumerate(rows, 1):
            tree.insert("", "end", values=(
                rank,
                p["name"],
                p["club"],
                p["age"],
                p["position"],
                p["overall"],
                f"{p['fitness']}%",
                f"${p['value']:,.0f}",
            ))

    def _apply_filters(self):
        pos_filter = self.page.filter_position.get()
        sort_by = self.page.filter_sort_by.get()
        sort_order = self.page.filter_sort_order.get()

        # Filter by position
        if pos_filter == "All":
            filtered = list(self._players_data)
        else:
            filtered = [p for p in self._players_data if p["position"] == pos_filter]

        # Sort key
        key_map = {
            "Overall": "overall",
            "Age": "age",
            "Fitness": "fitness",
            "Value": "value",
        }
        sort_key = key_map.get(sort_by, "overall")
        reverse = sort_order == "Descending"

        filtered.sort(key=lambda p: p[sort_key], reverse=reverse)
        self._populate_rankings(filtered)

    def _compare_teams(self):
        team_a_name = self.page.team_a_combo.get()
        team_b_name = self.page.team_b_combo.get()

        if not team_a_name or not team_b_name:
            return

        # Update column headings with team names
        self.page.comparison_tree.heading("team_a", text=team_a_name)
        self.page.comparison_tree.heading("team_b", text=team_b_name)

        team_a_players = [p for p in self._players_data if p["club"] == team_a_name]
        team_b_players = [p for p in self._players_data if p["club"] == team_b_name]

        def team_stats(players):
            if not players:
                return {
                    "squad_size": 0,
                    "avg_overall": 0.0,
                    "avg_age": 0.0,
                    "avg_fitness": 0.0,
                    "total_value": 0.0,
                    "best_overall": 0.0,
                    "gk_count": 0,
                    "df_count": 0,
                    "mf_count": 0,
                    "fw_count": 0,
                }
            return {
                "squad_size": len(players),
                "avg_overall": round(sum(p["overall"] for p in players) / len(players), 1),
                "avg_age": round(sum(p["age"] for p in players) / len(players), 1),
                "avg_fitness": round(sum(p["fitness"] for p in players) / len(players), 1),
                "total_value": sum(p["value"] for p in players),
                "best_overall": max(p["overall"] for p in players),
                "gk_count": sum(1 for p in players if p["position"] == "GK"),
                "df_count": sum(1 for p in players if p["position"] == "DF"),
                "mf_count": sum(1 for p in players if p["position"] == "MF"),
                "fw_count": sum(1 for p in players if p["position"] == "FW"),
            }

        sa = team_stats(team_a_players)
        sb = team_stats(team_b_players)

        tree = self.page.comparison_tree
        for item in tree.get_children():
            tree.delete(item)

        rows = [
            ("Squad Size", sa["squad_size"], sb["squad_size"]),
            ("Avg Overall", sa["avg_overall"], sb["avg_overall"]),
            ("Best Overall", sa["best_overall"], sb["best_overall"]),
            ("Avg Age", sa["avg_age"], sb["avg_age"]),
            ("Avg Fitness", f"{sa['avg_fitness']}%", f"{sb['avg_fitness']}%"),
            ("Total Value", f"${sa['total_value']:,.0f}", f"${sb['total_value']:,.0f}"),
            ("Goalkeepers", sa["gk_count"], sb["gk_count"]),
            ("Defenders", sa["df_count"], sb["df_count"]),
            ("Midfielders", sa["mf_count"], sb["mf_count"]),
            ("Forwards", sa["fw_count"], sb["fw_count"]),
        ]

        for row in rows:
            tree.insert("", "end", values=row)

    def _populate_top_performers(self):
        # Top 5 by overall
        by_overall = sorted(self._players_data, key=lambda p: p["overall"], reverse=True)[:5]
        tree = self.page.top_scorers_tree
        for item in tree.get_children():
            tree.delete(item)
        for p in by_overall:
            tree.insert("", "end", values=(p["name"], p["club"], p["overall"]))

        # Top 5 U21 by overall
        young = [p for p in self._players_data if p["age"] <= 21]
        by_young = sorted(young, key=lambda p: p["overall"], reverse=True)[:5]
        tree = self.page.top_youngsters_tree
        for item in tree.get_children():
            tree.delete(item)
        for p in by_young:
            tree.insert("", "end", values=(p["name"], p["club"], p["age"], p["overall"]))

        # Top 5 by value
        by_value = sorted(self._players_data, key=lambda p: p["value"], reverse=True)[:5]
        tree = self.page.top_valuable_tree
        for item in tree.get_children():
            tree.delete(item)
        for p in by_value:
            tree.insert("", "end", values=(p["name"], p["club"], f"${p['value']:,.0f}"))

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch("debug_home")
