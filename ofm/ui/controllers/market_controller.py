import datetime
from tkinter import messagebox

from ..pages.market import MarketPage
from .controllerinterface import ControllerInterface


class MarketController(ControllerInterface):
    POSITION_MAP = {1: "GK", 2: "DF", 3: "MF", 4: "FW"}

    def __init__(self, controller: ControllerInterface, page: MarketPage):
        self.controller = controller
        self.page = page
        self._market_data = []
        self._bind()

    def initialize(self):
        self.controller.db.check_clubs_file(amount=50)
        clubs = self.controller.db.load_clubs()
        players = self.controller.db.load_players()

        # Build player_id -> club_name lookup
        player_club_map = {}
        for club in clubs:
            for pid in club.get("squad", []):
                player_club_map[pid] = club["name"]

        # Build enriched player data
        today = datetime.date.today()
        self._market_data = []
        for p in players:
            positions = p.get("positions", [])
            primary_pos = positions[0] if positions else 3
            overall = self._calculate_overall(p.get("attributes", {}), primary_pos)
            age = self._calculate_age(p.get("dob", "2000-01-01"), today)

            self._market_data.append({
                "id": p.get("id", 0),
                "name": p.get("short_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
                "age": age,
                "position": self._get_position_name(primary_pos),
                "overall": round(overall, 1),
                "value": p.get("value", 0.0),
                "club": player_club_map.get(p.get("id", 0), "Free Agent"),
            })

        # Sort by value descending and populate
        self._market_data.sort(key=lambda p: p["value"], reverse=True)
        self._populate_tree(self._market_data)

    def _bind(self):
        self.page.back_btn.config(command=self.go_to_debug_home_page)
        self.page.search_btn.config(command=self._search)
        self.page.buy_btn.config(command=self._buy_player)

    def _search(self):
        query = self.page.search_entry.get().strip().lower()
        if not query:
            self._populate_tree(self._market_data)
            return

        filtered = [p for p in self._market_data if query in p["name"].lower()]
        self._populate_tree(filtered)

    def _populate_tree(self, data):
        tree = self.page.tree
        for item in tree.get_children():
            tree.delete(item)

        for p in data:
            tree.insert("", "end", values=(
                p["name"],
                p["age"],
                p["position"],
                p["overall"],
                f"${p['value']:,.0f}",
                p["club"],
            ))

    def _buy_player(self):
        selected = self.page.tree.selection()
        if not selected:
            messagebox.showinfo("Transfer Market", "Please select a player first.")
            return

        values = self.page.tree.item(selected[0], "values")
        name, age, pos, overall, value, club = values
        messagebox.showinfo(
            "Player Info",
            f"Name: {name}\nAge: {age}\nPosition: {pos}\n"
            f"Overall: {overall}\nValue: {value}\nClub: {club}",
        )

    @staticmethod
    def _calculate_age(dob: str, today: datetime.date) -> int:
        try:
            birth = datetime.date.fromisoformat(dob)
            return (today - birth).days // 365
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _calculate_overall(attributes: dict, position: int) -> float:
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
        return MarketController.POSITION_MAP.get(position, "MF")

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch("debug_home")
