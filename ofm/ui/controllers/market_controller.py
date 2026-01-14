from ..pages.market import MarketPage
from .controllerinterface import ControllerInterface

class MarketController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: MarketPage):
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
        self.page.back_btn.config(command=self.go_to_debug_home_page)
