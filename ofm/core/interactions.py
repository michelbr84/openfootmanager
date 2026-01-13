class InteractionType:
    PRESS = "Press"
    PLAYER = "Player"

class InteractionManager:
    def __init__(self):
        pass

    def talk_to_player(self, player_id: str, message: str):
        # Logic to affect morale
        pass

    def talk_to_press(self, topic: str):
        # Logic to affect public opinion
        pass
