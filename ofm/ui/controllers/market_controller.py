import datetime
from tkinter import messagebox, simpledialog
from uuid import UUID

from ..pages.market import MarketPage
from .controllerinterface import ControllerInterface
from ...core.football.transfer_market import TransferMarket, TransferListing, OfferStatus


class MarketController(ControllerInterface):
    POSITION_MAP = {1: "GK", 2: "DF", 3: "MF", 4: "FW"}

    def __init__(self, controller: ControllerInterface, page: MarketPage):
        self.controller = controller
        self.page = page
        self._market_data = []
        self._selected_player = None
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

        # Reset offer frame
        self._selected_player = None
        self.page.selected_player_label.config(text="Selected: None")
        self.page.offer_entry.delete(0, "end")
        self.page.offer_result_label.config(text="")

    def _bind(self):
        self.page.back_btn.config(command=self.go_to_debug_home_page)
        self.page.search_btn.config(command=self._search)
        self.page.buy_btn.config(command=self._buy_player)
        self.page.sell_btn.config(command=self._sell_player)
        self.page.submit_offer_btn.config(command=self._submit_offer)
        self.page.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

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

    def _on_tree_select(self, event=None):
        """When a player is selected in the tree, show their name and suggest a price."""
        selected = self.page.tree.selection()
        if not selected:
            return

        values = self.page.tree.item(selected[0], "values")
        name, age, pos, overall, value_str, club = values

        self._selected_player = {
            "name": name,
            "age": age,
            "position": pos,
            "overall": overall,
            "value_str": value_str,
            "club": club,
        }

        self.page.selected_player_label.config(text=f"Selected: {name} ({club})")

        # Suggest the displayed value as starting offer
        self.page.offer_entry.delete(0, "end")
        # Strip $ and commas to get numeric value
        clean_value = value_str.replace("$", "").replace(",", "").strip()
        self.page.offer_entry.insert(0, clean_value)
        self.page.offer_result_label.config(text="")

    def _submit_offer(self):
        """Submit a transfer offer for the selected player."""
        if self._selected_player is None:
            messagebox.showinfo("Transfer Offer", "Please select a player first.")
            return

        offer_text = self.page.offer_entry.get().strip()
        try:
            offer_amount = float(offer_text)
        except (ValueError, TypeError):
            messagebox.showerror("Transfer Offer", "Please enter a valid numeric offer amount.")
            return

        if offer_amount <= 0:
            messagebox.showerror("Transfer Offer", "Offer amount must be positive.")
            return

        name = self._selected_player["name"]

        # Try to use career engine's transfer market if available
        career = getattr(self.controller, "career_engine", None)
        if career is not None and hasattr(career, "transfer_market"):
            try:
                # Find the player in market data by name
                player_data = None
                for p in self._market_data:
                    if p["name"] == name:
                        player_data = p
                        break

                if player_data is None:
                    self.page.offer_result_label.config(text="Player not found in market data.")
                    return

                player_id = player_data["id"]
                if isinstance(player_id, int):
                    player_id = UUID(int=player_id)

                # Ensure the player is listed
                tm = career.transfer_market
                listing = None
                for l in tm.listings:
                    if l.player_id == player_id:
                        listing = l
                        break

                if listing is None:
                    # Auto-list the player with current value as asking price
                    asking = player_data["value"]
                    tm.list_player(player_id, None, asking)

                buying_club_id = getattr(career, "player_club_id", None)
                if buying_club_id is None:
                    self.page.offer_result_label.config(text="No user club set.")
                    return

                offer = tm.make_offer(player_id, buying_club_id, offer_amount)

                if offer.status == OfferStatus.ACCEPTED:
                    self.page.offer_result_label.config(
                        text=f"Offer accepted! {name} joins your squad."
                    )
                elif offer.status == OfferStatus.REJECTED:
                    self.page.offer_result_label.config(
                        text=f"Offer rejected. Try a higher amount."
                    )
                elif offer.status == OfferStatus.NEGOTIATING:
                    counter = offer.counter_amount or 0
                    self.page.offer_result_label.config(
                        text=f"Counter-offer: ${counter:,.0f}"
                    )
                else:
                    self.page.offer_result_label.config(
                        text=f"Offer status: {offer.status.value}"
                    )
                return
            except Exception as e:
                self.page.offer_result_label.config(text=f"Error: {e}")
                return

        # Fallback: simple simulation without career engine
        value_str = self._selected_player["value_str"]
        clean_value = float(value_str.replace("$", "").replace(",", "").strip())

        if offer_amount >= clean_value:
            self.page.offer_result_label.config(
                text=f"Offer accepted! {name} joins your squad."
            )
        elif offer_amount >= clean_value * 0.70:
            counter = round((offer_amount + clean_value) / 2, 0)
            self.page.offer_result_label.config(
                text=f"Counter-offer: ${counter:,.0f}"
            )
        else:
            self.page.offer_result_label.config(
                text="Offer rejected. Too low."
            )

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

    def _sell_player(self):
        """List one of the user's players on the market."""
        career = getattr(self.controller, "career_engine", None)
        if career is not None and hasattr(career, "transfer_market"):
            messagebox.showinfo(
                "Sell Player",
                "Select a player from your squad in the Team Formation page "
                "and list them on the transfer market from there.\n\n"
                "This feature will open the squad view in a future update.",
            )
            return

        # Debug mode fallback
        messagebox.showinfo(
            "Sell Player",
            "Sell Player is available in Career Mode.\n"
            "Start a new game to access full transfer features.",
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
        self.switch(self.controller.get_back_page())
