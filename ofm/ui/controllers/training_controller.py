import random

from ..pages.training import TrainingPage
from .controllerinterface import ControllerInterface
from ...core.football.training import TrainingManager, TrainingFocus


class TrainingController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: TrainingPage):
        self.controller = controller
        self.page = page
        self._players = []
        self._training_manager = TrainingManager()
        self._bind()

    def initialize(self):
        self.page.result_label.config(text="")
        if not self.page.focus_var.get():
            self.page.focus_var.set("General")
        self._load_players()

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch("debug_home")

    def _bind(self):
        self.page.back_btn.config(command=self.go_to_debug_home_page)
        self.page.train_btn.config(command=self._run_training)

    def _load_players(self):
        """Load squad as PlayerTeam objects via the DB's club loading."""
        team_data = getattr(self.controller, "current_user_team", None)
        if team_data:
            players_dicts = self.controller.db.load_players()
            try:
                club_objects = self.controller.db.load_club_objects(
                    [team_data], players_dicts
                )
                if club_objects:
                    self._players = list(club_objects[0].squad)
                    return
            except Exception:
                pass

        # Fallback: generate data if needed and load first club
        self.controller.db.check_clubs_file(amount=50)
        clubs = self.controller.db.load_clubs()
        players_dicts = self.controller.db.load_players()
        if clubs:
            try:
                club_objects = self.controller.db.load_club_objects(
                    [clubs[0]], players_dicts
                )
                if club_objects:
                    self._players = list(club_objects[0].squad)
                    return
            except Exception:
                pass
        self._players = []

    def _run_training(self):
        if not self._players:
            self.page.result_label.config(text="No players available for training.")
            return

        # Map combo box value to TrainingFocus enum
        focus_str = self.page.focus_var.get()
        focus_map = {
            "General": TrainingFocus.GENERAL,
            "Attack": TrainingFocus.ATTACK,
            "Defense": TrainingFocus.DEFENSE,
            "Fitness": TrainingFocus.FITNESS,
        }
        focus_enum = focus_map.get(focus_str, TrainingFocus.GENERAL)

        # Pick a sample of players (3-5) or use full squad if small
        if len(self._players) <= 5:
            selected = list(self._players)
        else:
            sample_size = random.randint(3, 5)
            selected = random.sample(self._players, sample_size)

        session = self._training_manager.train_squad(selected, focus_enum, intensity=0.8)
        report = self._training_manager.get_training_report(session)
        self.page.result_label.config(text=report)
