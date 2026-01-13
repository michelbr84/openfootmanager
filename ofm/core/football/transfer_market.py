from .player import PlayerTeam
from ..football.club import Club

class TransferMarket:
    def __init__(self):
        self.listed_players: list[tuple[PlayerTeam, float]] = [] # Player, Price

    def list_player(self, player: PlayerTeam, price: float):
        if not any(p[0] == player for p in self.listed_players):
            self.listed_players.append((player, price))

    def remove_player(self, player: PlayerTeam):
        self.listed_players = [p for p in self.listed_players if p[0] != player]

    def buy_player(self, buyer_club: Club, player: PlayerTeam, price: float):
        """
        Execute transfer: Move player to buyer club, deduct money.
        """
        # Ensure player is actually for sale
        listing = next((p for p in self.listed_players if p[0] == player), None)
        if not listing:
            raise ValueError("Player not for sale")
        
        # Check funds
        if buyer_club.finances.balance < price:
            raise ValueError("Insufficient funds")

        # Execute
        buyer_club.finances.add_expense(price, f"Bought {player.details.name}")
        buyer_club.squad.append(player)
        self.remove_player(player)
        
        # Note: In a full simulation, we'd remove from old club and give them money.
        # But PlayerTeam object might not have a back-reference to the old club easily accessible here 
        # without further changes. For now, assuming free agents or simplified view.
