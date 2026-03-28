import random

from ..pages.training import TrainingPage
from .controllerinterface import ControllerInterface


class TrainingController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: TrainingPage):
        self.controller = controller
        self.page = page
        self._players = []
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
        team_data = getattr(self.controller, "current_user_team", None)
        if team_data:
            all_players = self.controller.db.load_players()
            squad_ids = {p["id"] for p in team_data.get("squad", [])}
            if squad_ids:
                self._players = [p for p in all_players if p["id"] in squad_ids]
            else:
                self._players = all_players
        else:
            self.controller.db.check_clubs_file(amount=50)
            self._players = self.controller.db.load_players()

    def _run_training(self):
        if not self._players:
            self.page.result_label.config(text="No players available for training.")
            return

        focus = self.page.focus_var.get()
        sample_size = min(random.randint(3, 5), len(self._players))
        selected = random.sample(self._players, sample_size)

        results = []
        for player in selected:
            name = player.get("short_name", "Unknown")
            attrs = player.get("attributes", {})
            improvements = self._apply_training(focus, attrs)
            if improvements:
                imp_str = ", ".join(f"{attr} +{val}" for attr, val in improvements)
                results.append(f"{name}: {imp_str}")
            else:
                results.append(f"{name}: no improvement")

        result_text = f"Training Session ({focus})\n" + "\n".join(results)
        self.page.result_label.config(text=result_text)

    def _apply_training(self, focus, attributes):
        improvements = []

        if focus == "General":
            improvements = self._train_general(attributes)
        elif focus == "Attack":
            improvements = self._train_attack(attributes)
        elif focus == "Defense":
            improvements = self._train_defense(attributes)
        elif focus == "Fitness":
            improvements = self._train_fitness(attributes)

        return improvements

    def _train_general(self, attributes):
        improvements = []
        all_attrs = []
        for category in ("offensive", "defensive", "intelligence", "physical"):
            cat_dict = attributes.get(category, {})
            for attr_name, value in cat_dict.items():
                all_attrs.append((category, attr_name, value))

        if not all_attrs:
            return improvements

        count = random.randint(1, 2)
        chosen = random.sample(all_attrs, min(count, len(all_attrs)))
        for category, attr_name, value in chosen:
            boost = random.randint(1, 2)
            new_value = min(value + boost, 99)
            attributes[category][attr_name] = new_value
            improvements.append((attr_name, boost))

        return improvements

    def _train_attack(self, attributes):
        improvements = []
        offensive = attributes.get("offensive", {})
        if not offensive:
            return improvements

        attrs = list(offensive.items())
        count = random.randint(1, min(2, len(attrs)))
        chosen = random.sample(attrs, count)
        for attr_name, value in chosen:
            boost = random.randint(1, 3)
            new_value = min(value + boost, 99)
            offensive[attr_name] = new_value
            improvements.append((attr_name, boost))

        return improvements

    def _train_defense(self, attributes):
        improvements = []
        defensive = attributes.get("defensive", {})
        if not defensive:
            return improvements

        attrs = list(defensive.items())
        count = random.randint(1, min(2, len(attrs)))
        chosen = random.sample(attrs, count)
        for attr_name, value in chosen:
            boost = random.randint(1, 3)
            new_value = min(value + boost, 99)
            defensive[attr_name] = new_value
            improvements.append((attr_name, boost))

        return improvements

    def _train_fitness(self, attributes):
        improvements = []
        physical = attributes.get("physical", {})
        fitness_attrs = {}
        for attr_name in ("endurance", "strength"):
            if attr_name in physical:
                fitness_attrs[attr_name] = physical[attr_name]

        if not fitness_attrs:
            return improvements

        for attr_name, value in fitness_attrs.items():
            boost = random.randint(2, 4)
            new_value = min(value + boost, 99)
            physical[attr_name] = new_value
            improvements.append((attr_name, boost))

        return improvements
