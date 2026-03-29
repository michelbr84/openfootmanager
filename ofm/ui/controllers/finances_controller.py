import random

from ..pages.finances import FinancesPage
from .controllerinterface import ControllerInterface


class FinancesController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: FinancesPage):
        self.controller = controller
        self.page = page
        self._bind()

    def initialize(self):
        career = getattr(self.controller, "career_engine", None)
        if career and career.season:
            self._initialize_career_mode(career)
        else:
            self._initialize_debug_mode()

    def _initialize_career_mode(self, career):
        """Show real finance data from the career engine."""
        club_info = career.get_player_club()
        if club_info is None:
            self.page.balance_label.config(text="Balance: $0.00")
            return

        balance = club_info["balance"]
        self.page.balance_label.config(text=f"Balance: ${balance:,.2f}")

        # Clear existing items in the treeview
        for item in self.page.trans_list.get_children():
            self.page.trans_list.delete(item)

        # Get real transactions from the club's FinanceManager
        player_club = career._club_map.get(career.player_club_id)
        if player_club and player_club.finances and player_club.finances.transactions:
            for t in player_club.finances.transactions:
                trans_type = t.type.value  # "Income" or "Expense"
                amount_str = f"${t.amount:,.2f}" if t.amount >= 0 else f"-${abs(t.amount):,.2f}"
                self.page.trans_list.insert("", "end", values=(trans_type, amount_str, t.description))
        else:
            self.page.trans_list.insert("", "end", values=("", "", "No transactions yet"))

    def _initialize_debug_mode(self):
        """Fallback: generate sample transactions for debug mode."""
        club = self._get_club()
        if club is None:
            self.page.balance_label.config(text="Balance: $0.00")
            return

        players = self.controller.db.load_players()
        squad_size = len(players) if players else 22
        stadium_capacity = club.get("stadium_capacity", 30000)

        # Generate sample transactions for debug mode
        transactions = self._generate_transactions(squad_size, stadium_capacity)

        # Calculate balance as sum of all transactions
        balance = sum(amount for _, amount, _ in transactions)

        # Update the balance label
        self.page.balance_label.config(text=f"Balance: ${balance:,.2f}")

        # Clear existing items in the treeview
        for item in self.page.trans_list.get_children():
            self.page.trans_list.delete(item)

        # Populate the treeview with transactions
        for trans_type, amount, description in transactions:
            amount_str = f"${amount:,.2f}" if amount >= 0 else f"-${abs(amount):,.2f}"
            self.page.trans_list.insert("", "end", values=(trans_type, amount_str, description))

    def _get_club(self):
        """Return the current user team or load the first club from DB."""
        if self.controller.current_user_team is not None:
            return self.controller.current_user_team

        self.controller.db.check_clubs_file(amount=50)
        clubs = self.controller.db.load_clubs()
        if clubs:
            return clubs[0]
        return None

    def _generate_transactions(self, squad_size, stadium_capacity):
        """Generate realistic sample financial transactions for debug mode.

        Returns a list of (type, amount, description) tuples where
        income is positive and expenses are negative.
        """
        ticket_price = random.uniform(25.0, 55.0)
        occupancy = random.uniform(0.65, 0.95)
        season_games = 19  # home games in a typical season
        ticket_revenue = stadium_capacity * occupancy * ticket_price * season_games

        avg_weekly_wage = random.uniform(15000.0, 45000.0)
        total_wages = squad_size * avg_weekly_wage * 52  # annual wages

        sponsorship = random.uniform(500000.0, 5000000.0)

        maintenance = stadium_capacity * random.uniform(8.0, 20.0)

        transfer_income = random.uniform(200000.0, 10000000.0)

        youth_cost = random.uniform(300000.0, 1500000.0)

        transactions = [
            ("Income", ticket_revenue, "Season Ticket Revenue"),
            ("Expense", -total_wages, "Player Wages"),
            ("Income", sponsorship, "Sponsorship Deal"),
            ("Expense", -maintenance, "Stadium Maintenance"),
            ("Income", transfer_income, "Transfer Income"),
            ("Expense", -youth_cost, "Youth Academy"),
        ]

        return transactions

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch(self.controller.get_back_page())

    def _bind(self):
        self.page.back_btn.config(command=self.go_to_debug_home_page)
