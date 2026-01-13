from .player import PlayerTeam
from ..football.club import Club

class LoanManager:
    def __init__(self):
        self.loans_in: list[tuple[PlayerTeam, Club]] = [] # Player, Parent Club
        self.loans_out: list[tuple[PlayerTeam, Club]] = [] # Player, Target Club

    def loan_player_out(self, player: PlayerTeam, target_club: Club, duration_weeks: int):
        self.loans_out.append((player, target_club))
        # Logic to move player to target club squad temporarily would go here
    
    def return_loan(self, player: PlayerTeam):
        # Logic to return player
        pass
