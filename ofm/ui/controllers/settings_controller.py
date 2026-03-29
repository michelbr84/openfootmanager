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
import tkinter.messagebox as messagebox

from ...core.benchmarking import BenchmarkSuite
from ...core.i18n import LocaleManager
from ..pages.settings import SettingsPage
from .controllerinterface import ControllerInterface


class SettingsController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: SettingsPage):
        self.controller = controller
        self.page = page
        self._locale_manager = LocaleManager()
        self._bind()

    def initialize(self):
        # Populate language combo with available locales
        locales = self._locale_manager.get_available_locales()
        self.page.language_combo.config(values=locales)
        current = getattr(self.controller, "locale", "en")
        if current in locales:
            self.page.language_combo.current(locales.index(current))
        elif locales:
            self.page.language_combo.current(0)

    def switch(self, page):
        self.controller.switch(page)

    def select_theme(self, e):
        theme = self.page.theme_combo_box.get()
        self.controller.gui.style.theme_use(theme)
        self.page.theme_combo_box.selection_clear()

    def _on_language_change(self, e=None):
        selected = self.page.language_combo.get()
        try:
            self._locale_manager.set_locale(selected)
            self.controller.locale = selected
            self.page.language_combo.selection_clear()
        except ValueError:
            pass

    def _run_benchmark(self):
        suite = BenchmarkSuite()
        db = getattr(self.controller, "db", None)
        if db is not None:
            result = suite.benchmark_database_load(db)
            messagebox.showinfo("Benchmark Results", str(result))
        else:
            messagebox.showinfo("Benchmark Results", "No database available to benchmark.")

    def go_to_debug_home_page(self):
        self.switch("home")

    def _bind(self):
        self.page.cancel_btn.config(command=self.go_to_debug_home_page)
        self.page.theme_combo_box.bind("<<ComboboxSelected>>", self.select_theme)
        self.page.language_combo.bind("<<ComboboxSelected>>", self._on_language_change)
        self.page.benchmark_btn.config(command=self._run_benchmark)
