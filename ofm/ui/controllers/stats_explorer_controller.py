from ..pages.stats_explorer import StatsExplorerPage
from .controllerinterface import ControllerInterface

class StatsExplorerController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: StatsExplorerPage):
        self.controller = controller
        self.page = page
        self._bind()

    def initialize(self):
        pass

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch("debug_home")

    def _bind(self):
        self.page.cancel_btn.config(command=self.go_to_debug_home_page)
