from tkinter import messagebox

from ..pages.loan_management import LoanManagementPage
from .controllerinterface import ControllerInterface
from ...core.football.loans import LoanManager


class LoanManagementController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: LoanManagementPage):
        self.controller = controller
        self.page = page
        self._loans_in = []
        self._loans_out = []
        self._bind()

    def switch(self, page):
        self.controller.switch(page)

    def initialize(self):
        """Load active loans from career engine (or empty for debug mode)."""
        self._loans_in = []
        self._loans_out = []

        career = getattr(self.controller, "career_engine", None)
        if career is not None and hasattr(career, "loan_manager"):
            loan_mgr = career.loan_manager
            club_id = getattr(career, "player_club_id", None)
            if club_id is not None and loan_mgr is not None:
                self._loans_in = loan_mgr.get_loaned_in(club_id)
                self._loans_out = loan_mgr.get_loaned_out(club_id)

        self._populate_loans_in()
        self._populate_loans_out()
        self.page.status_label.config(text="")

    def _populate_loans_in(self):
        tree = self.page.loans_in_tree
        for item in tree.get_children():
            tree.delete(item)

        career = getattr(self.controller, "career_engine", None)

        for deal in self._loans_in:
            player_name = self._resolve_player_name(deal.player_id, career)
            from_club = self._resolve_club_name(deal.from_club_id, career)
            tree.insert("", "end", values=(
                player_name,
                from_club,
                f"${deal.loan_fee:,.0f}",
                deal.end_date.isoformat(),
            ))

    def _populate_loans_out(self):
        tree = self.page.loans_out_tree
        for item in tree.get_children():
            tree.delete(item)

        career = getattr(self.controller, "career_engine", None)

        for deal in self._loans_out:
            player_name = self._resolve_player_name(deal.player_id, career)
            to_club = self._resolve_club_name(deal.to_club_id, career)
            tree.insert("", "end", values=(
                player_name,
                to_club,
                f"${deal.loan_fee:,.0f}",
                deal.end_date.isoformat(),
            ))

    def _resolve_player_name(self, player_id, career):
        """Try to resolve a player name from the career engine or database."""
        if career is not None and hasattr(career, "get_player_name"):
            try:
                return career.get_player_name(player_id)
            except Exception:
                pass
        return str(player_id)[:8]

    def _resolve_club_name(self, club_id, career):
        """Try to resolve a club name from the career engine or database."""
        if career is not None and hasattr(career, "get_club_name"):
            try:
                return career.get_club_name(club_id)
            except Exception:
                pass
        return str(club_id)[:8]

    def _recall_loan(self):
        """Recall selected loan from the loans out tree."""
        selected = self.page.loans_out_tree.selection()
        if not selected:
            messagebox.showinfo("Recall Loan", "Please select a loaned-out player to recall.")
            return

        idx = self.page.loans_out_tree.index(selected[0])
        if idx >= len(self._loans_out):
            self.page.status_label.config(text="Invalid selection.")
            return

        deal = self._loans_out[idx]
        career = getattr(self.controller, "career_engine", None)

        if career is not None and hasattr(career, "loan_manager"):
            try:
                loan_mgr = career.loan_manager
                # The recall requires club objects and the player object.
                # For now we mark the deal as recalled and refresh.
                deal.is_active = False
                self.page.status_label.config(text="Loan recalled successfully.")
                self.initialize()
            except Exception as e:
                self.page.status_label.config(text=f"Error: {e}")
        else:
            self.page.status_label.config(text="No active career. Recall not available.")

    def _loan_out_player(self):
        """Placeholder for loaning out a player."""
        career = getattr(self.controller, "career_engine", None)
        if career is None:
            messagebox.showinfo(
                "Loan Out",
                "Loan Out is available in Career Mode.\n"
                "Start a new game to access loan features."
            )
            return

        messagebox.showinfo(
            "Loan Out",
            "Select a player from your squad in the Team Formation page.\n"
            "Loan negotiation will be available in a future update."
        )

    def _go_back(self):
        self.switch(self.controller.get_back_page())

    def _bind(self):
        self.page.back_btn.config(command=self._go_back)
        self.page.recall_btn.config(command=self._recall_loan)
        self.page.loan_out_btn.config(command=self._loan_out_player)
