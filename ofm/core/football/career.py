class CareerManager:
    def __init__(self):
        self.trophies: list[str] = []
        self.job_history: list[str] = []
        self.national_team_job = None

    def add_trophy(self, trophy_name: str):
        self.trophies.append(trophy_name)

    def hire_national_team(self, team_name: str):
        self.national_team_job = team_name
