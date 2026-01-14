from ..pages.finances import FinancesPage
from .controllerinterface import ControllerInterface

class FinancesController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: FinancesPage):
        self.controller = controller
        self.page = page
        self._bind()

    def initialize(self):
        # In the future, load finances data here
        pass

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch("debug_home")

    def _bind(self):
        # Override the lambda command that might be incorrect or just pointing to 'home'
        # We want to go back to 'debug_home' if we came from there contextually
        self.page.back_btn.config(command=self.go_to_debug_home_page)
