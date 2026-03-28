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
from enum import Enum
from typing import Optional
from uuid import UUID

from .player import PlayerTeam
from ..football.club import Club


class TransferWindow(Enum):
    OPEN = "open"
    CLOSED = "closed"


class OfferStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEGOTIATING = "negotiating"


@dataclass
class TransferListing:
    player_id: UUID
    selling_club_id: Optional[UUID]  # None for free agents
    asking_price: float
    listed_date: datetime.date

    def serialize(self) -> dict:
        return {
            "player_id": self.player_id.int,
            "selling_club_id": self.selling_club_id.int if self.selling_club_id else None,
            "asking_price": self.asking_price,
            "listed_date": self.listed_date.strftime("%Y-%m-%d"),
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "TransferListing":
        return cls(
            player_id=UUID(int=data["player_id"]),
            selling_club_id=UUID(int=data["selling_club_id"]) if data["selling_club_id"] is not None else None,
            asking_price=data["asking_price"],
            listed_date=datetime.datetime.strptime(data["listed_date"], "%Y-%m-%d").date(),
        )


@dataclass
class TransferOffer:
    player_id: UUID
    buying_club_id: UUID
    selling_club_id: Optional[UUID]
    offer_amount: float
    status: OfferStatus = OfferStatus.PENDING
    counter_amount: Optional[float] = None

    def serialize(self) -> dict:
        return {
            "player_id": self.player_id.int,
            "buying_club_id": self.buying_club_id.int,
            "selling_club_id": self.selling_club_id.int if self.selling_club_id else None,
            "offer_amount": self.offer_amount,
            "status": self.status.value,
            "counter_amount": self.counter_amount,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "TransferOffer":
        return cls(
            player_id=UUID(int=data["player_id"]),
            buying_club_id=UUID(int=data["buying_club_id"]),
            selling_club_id=UUID(int=data["selling_club_id"]) if data["selling_club_id"] is not None else None,
            offer_amount=data["offer_amount"],
            status=OfferStatus(data["status"]),
            counter_amount=data.get("counter_amount"),
        )


def calculate_market_value(player_dict: dict) -> float:
    """
    Estimate a player's market value from age, overall, potential, and
    international_reputation.

    Parameters
    ----------
    player_dict : dict
        Must contain keys: "dob" (str YYYY-MM-DD or datetime.date),
        "overall" (int 0-99), "potential_skill" (int 0-99),
        "international_reputation" (int 0-5).

    Returns
    -------
    float
        Estimated market value in currency units.
    """
    # Parse age
    dob = player_dict["dob"]
    if isinstance(dob, str):
        dob = datetime.datetime.strptime(dob, "%Y-%m-%d").date()
    today = datetime.date.today()
    age = (today - dob).days / 365.25

    overall = player_dict.get("overall", 50)
    potential = player_dict.get("potential_skill", overall)
    reputation = player_dict.get("international_reputation", 1)

    # Base value from overall rating (exponential curve)
    base_value = (overall / 99.0) ** 3 * 100_000_000  # max ~100M for 99 rated

    # Age factor: peak at 25-29, drops off sharply after 32
    if age < 21:
        age_factor = 0.6 + (age - 16) * 0.08  # young players gain value
    elif age < 25:
        age_factor = 1.0 + (age - 21) * 0.05
    elif age < 30:
        age_factor = 1.2
    elif age < 33:
        age_factor = 1.2 - (age - 30) * 0.15
    else:
        age_factor = max(0.3, 0.75 - (age - 33) * 0.15)

    # Potential bonus: difference between potential and current adds value
    potential_bonus = max(0, (potential - overall)) / 99.0 * 30_000_000

    # Reputation multiplier: 1-5 scale
    reputation_factor = 0.5 + reputation * 0.3  # ranges from 0.8 to 2.0

    value = (base_value * age_factor + potential_bonus) * reputation_factor
    return round(max(value, 50_000), 2)  # minimum 50k


class TransferMarket:
    def __init__(self, window: TransferWindow = TransferWindow.OPEN):
        self.listings: list[TransferListing] = []
        self.completed_transfers: list[dict] = []
        self.window: TransferWindow = window

    def list_player(self, player_id: UUID, selling_club_id: Optional[UUID], asking_price: float,
                    listed_date: Optional[datetime.date] = None):
        """
        Add a player to the transfer market.
        """
        if self.window == TransferWindow.CLOSED:
            raise ValueError("Transfer window is closed")

        # Don't list the same player twice
        if any(listing.player_id == player_id for listing in self.listings):
            raise ValueError("Player is already listed on the transfer market")

        listing = TransferListing(
            player_id=player_id,
            selling_club_id=selling_club_id,
            asking_price=asking_price,
            listed_date=listed_date or datetime.date.today(),
        )
        self.listings.append(listing)
        return listing

    def remove_listing(self, player_id: UUID):
        """
        Remove a player from the transfer market.
        """
        original_count = len(self.listings)
        self.listings = [l for l in self.listings if l.player_id != player_id]
        if len(self.listings) == original_count:
            raise ValueError("Player not found on the transfer market")

    def _find_listing(self, player_id: UUID) -> TransferListing:
        listing = next((l for l in self.listings if l.player_id == player_id), None)
        if listing is None:
            raise ValueError("Player not found on the transfer market")
        return listing

    def make_offer(self, player_id: UUID, buying_club_id: UUID, offer_amount: float) -> TransferOffer:
        """
        Create a transfer offer for a listed player.

        Auto-accept if offer >= asking_price.
        Reject if offer < 70% of asking_price.
        Negotiate (counter offer) if in between.
        """
        if self.window == TransferWindow.CLOSED:
            raise ValueError("Transfer window is closed")

        listing = self._find_listing(player_id)

        offer = TransferOffer(
            player_id=player_id,
            buying_club_id=buying_club_id,
            selling_club_id=listing.selling_club_id,
            offer_amount=offer_amount,
        )

        if offer_amount >= listing.asking_price:
            offer.status = OfferStatus.ACCEPTED
        elif offer_amount < listing.asking_price * 0.70:
            offer.status = OfferStatus.REJECTED
        else:
            # Negotiate: counter at midpoint between offer and asking price
            offer.status = OfferStatus.NEGOTIATING
            offer.counter_amount = round((offer_amount + listing.asking_price) / 2, 2)

        return offer

    def execute_transfer(self, offer: TransferOffer, selling_club: Optional[Club],
                         buying_club: Club, player: PlayerTeam):
        """
        Execute an accepted transfer: move the player between squads and update finances.

        Parameters
        ----------
        offer : TransferOffer
            Must have status ACCEPTED.
        selling_club : Club or None
            The club selling the player (None for free agents).
        buying_club : Club
            The club buying the player.
        player : PlayerTeam
            The player being transferred.
        """
        if offer.status != OfferStatus.ACCEPTED:
            raise ValueError("Cannot execute a transfer that has not been accepted")

        if self.window == TransferWindow.CLOSED:
            raise ValueError("Transfer window is closed")

        price = offer.offer_amount

        # Check buyer has sufficient funds
        if buying_club.finances.balance < price:
            raise ValueError("Insufficient funds for transfer")

        # Deduct from buyer
        buying_club.finances.add_expense(price, f"Transfer fee: {player.details.short_name}")

        # Credit to seller
        if selling_club is not None:
            selling_club.finances.add_income(price, f"Transfer fee: {player.details.short_name}")
            # Remove player from selling club squad
            selling_club.squad = [p for p in selling_club.squad if
                                  p.details.player_id != player.details.player_id]

        # Add player to buying club squad
        player.team_id = buying_club.club_id
        buying_club.squad.append(player)

        # Remove from market
        self.listings = [l for l in self.listings if l.player_id != player.details.player_id]

        # Record completed transfer
        self.completed_transfers.append({
            "player_id": player.details.player_id.int,
            "player_name": player.details.short_name,
            "from_club_id": selling_club.club_id.int if selling_club else None,
            "from_club_name": selling_club.name if selling_club else "Free Agent",
            "to_club_id": buying_club.club_id.int,
            "to_club_name": buying_club.name,
            "fee": price,
            "date": datetime.date.today().strftime("%Y-%m-%d"),
        })

    def get_available_players(self) -> list[TransferListing]:
        """Return all active listings."""
        return list(self.listings)

    def get_free_agents(self) -> list[TransferListing]:
        """Return listings where selling_club_id is None."""
        return [l for l in self.listings if l.selling_club_id is None]

    def serialize(self) -> dict:
        return {
            "listings": [l.serialize() for l in self.listings],
            "completed_transfers": self.completed_transfers,
            "window": self.window.value,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "TransferMarket":
        window = TransferWindow(data.get("window", "open"))
        market = cls(window=window)
        market.listings = [TransferListing.get_from_dict(l) for l in data.get("listings", [])]
        market.completed_transfers = data.get("completed_transfers", [])
        return market
