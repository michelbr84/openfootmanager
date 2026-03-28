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
import datetime
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from .player import PlayerTeam
from ..football.club import Club


@dataclass
class LoanDeal:
    player_id: UUID
    from_club_id: UUID
    to_club_id: UUID
    start_date: datetime.date
    end_date: datetime.date
    loan_fee: float
    wage_percentage: float  # 0.0 to 1.0: fraction of wages paid by the borrowing club
    is_active: bool = True

    def serialize(self) -> dict:
        return {
            "player_id": self.player_id.int,
            "from_club_id": self.from_club_id.int,
            "to_club_id": self.to_club_id.int,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "loan_fee": self.loan_fee,
            "wage_percentage": self.wage_percentage,
            "is_active": self.is_active,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "LoanDeal":
        return cls(
            player_id=UUID(int=data["player_id"]),
            from_club_id=UUID(int=data["from_club_id"]),
            to_club_id=UUID(int=data["to_club_id"]),
            start_date=datetime.datetime.strptime(data["start_date"], "%Y-%m-%d").date(),
            end_date=datetime.datetime.strptime(data["end_date"], "%Y-%m-%d").date(),
            loan_fee=data["loan_fee"],
            wage_percentage=data["wage_percentage"],
            is_active=data.get("is_active", True),
        )


class LoanManager:
    def __init__(self):
        self.active_loans: list[LoanDeal] = []

    def loan_player_out(self, deal: LoanDeal, from_club: Club, to_club: Club, player: PlayerTeam):
        """
        Move a player from one club to another on loan.

        Parameters
        ----------
        deal : LoanDeal
            The loan deal details.
        from_club : Club
            The parent club lending the player.
        to_club : Club
            The club borrowing the player.
        player : PlayerTeam
            The player being loaned.
        """
        # Validate the player is in the from_club squad
        if not any(p.details.player_id == player.details.player_id for p in from_club.squad):
            raise ValueError("Player is not in the lending club's squad")

        # Validate deal dates
        if deal.end_date <= deal.start_date:
            raise ValueError("Loan end date must be after start date")

        if not (0.0 <= deal.wage_percentage <= 1.0):
            raise ValueError("Wage percentage must be between 0.0 and 1.0")

        # Process loan fee: borrowing club pays the lending club
        if deal.loan_fee > 0:
            to_club.finances.add_expense(deal.loan_fee, f"Loan fee: {player.details.short_name}")
            from_club.finances.add_income(deal.loan_fee, f"Loan fee: {player.details.short_name}")

        # Move player from parent club to borrowing club
        from_club.squad = [p for p in from_club.squad if
                           p.details.player_id != player.details.player_id]
        to_club.squad.append(player)

        # Record the loan
        deal.is_active = True
        self.active_loans.append(deal)

    def return_loan(self, deal: LoanDeal, from_club: Club, to_club: Club, player: PlayerTeam):
        """
        Return a loaned player to their parent club.

        Parameters
        ----------
        deal : LoanDeal
            The loan deal to terminate.
        from_club : Club
            The parent club (player returns here).
        to_club : Club
            The borrowing club (player leaves here).
        player : PlayerTeam
            The player being returned.
        """
        if not deal.is_active:
            raise ValueError("Loan deal is not active")

        # Move player back: remove from borrowing club, add to parent club
        to_club.squad = [p for p in to_club.squad if
                         p.details.player_id != player.details.player_id]
        player.team_id = from_club.club_id
        from_club.squad.append(player)

        # Mark deal as inactive
        deal.is_active = False

    def recall_loan(self, deal: LoanDeal, from_club: Club, to_club: Club, player: PlayerTeam):
        """
        Early return of a loaned player to the parent club.
        Same mechanics as return_loan but can be called before the end_date.

        Parameters
        ----------
        deal : LoanDeal
            The loan deal to terminate early.
        from_club : Club
            The parent club recalling the player.
        to_club : Club
            The borrowing club.
        player : PlayerTeam
            The player being recalled.
        """
        self.return_loan(deal, from_club, to_club, player)

    def check_expired_loans(self, current_date: datetime.date) -> list[LoanDeal]:
        """
        Return all active loans that have passed their end_date.

        Parameters
        ----------
        current_date : datetime.date
            The current simulation date.

        Returns
        -------
        list[LoanDeal]
            Loans that are past their end date and still active.
        """
        return [deal for deal in self.active_loans if deal.is_active and current_date >= deal.end_date]

    def get_loaned_in(self, club_id: UUID) -> list[LoanDeal]:
        """Return active loans where the given club is the borrowing club."""
        return [deal for deal in self.active_loans if deal.is_active and deal.to_club_id == club_id]

    def get_loaned_out(self, club_id: UUID) -> list[LoanDeal]:
        """Return active loans where the given club is the lending club."""
        return [deal for deal in self.active_loans if deal.is_active and deal.from_club_id == club_id]

    def serialize(self) -> dict:
        return {
            "active_loans": [deal.serialize() for deal in self.active_loans],
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "LoanManager":
        manager = cls()
        manager.active_loans = [LoanDeal.get_from_dict(d) for d in data.get("active_loans", [])]
        return manager
