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
from ..pages.press_conference import PressConferencePage
from .controllerinterface import ControllerInterface
from ...core.football.interactions import InteractionManager


class PressConferenceController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: PressConferencePage):
        self.controller = controller
        self.page = page
        self._questions = []
        self._current_index = 0
        self._total_morale = 0
        self._total_reputation = 0
        self._bind()

    def switch(self, page: str):
        self.controller.switch(page)

    def initialize(self):
        career = getattr(self.controller, "career_engine", None)
        if career is not None and hasattr(career, "interaction_manager"):
            self._interaction = career.interaction_manager
        else:
            self._interaction = InteractionManager()

        self._total_morale = 0
        self._total_reputation = 0
        self._current_index = 0

        # Generate press conference questions
        self._questions = self._interaction.conduct_press_conference(
            "general", num_questions=4
        )

        if self._questions:
            self._show_question()
        else:
            self.page.question_label.config(text="No questions available.")
            self._disable_responses()

        self._set_result("")
        self.page.status_label.config(text="")

    def _show_question(self):
        if self._current_index >= len(self._questions):
            self.page.question_label.config(text="Press conference is over.")
            self._disable_responses()
            self.page.next_btn.config(state="disabled")
            self.page.status_label.config(
                text=f"Final: Morale {self._total_morale:+d}, "
                     f"Reputation {self._total_reputation:+d}"
            )
            return

        q = self._questions[self._current_index]
        self.page.question_label.config(
            text=f"Q{self._current_index + 1}/{len(self._questions)}: {q.question}"
        )

        # Set up response buttons
        options = q.options
        if len(options) >= 1:
            self.page.response_a_btn.config(
                text=options[0].text, state="normal",
                command=lambda: self._select_response(0)
            )
        if len(options) >= 2:
            self.page.response_b_btn.config(
                text=options[1].text, state="normal",
                command=lambda: self._select_response(1)
            )
        if len(options) >= 3:
            self.page.response_c_btn.config(
                text=options[2].text, state="normal",
                command=lambda: self._select_response(2)
            )

        self.page.next_btn.config(state="disabled")
        self._set_result("")

    def _select_response(self, index):
        if self._current_index >= len(self._questions):
            return

        q = self._questions[self._current_index]
        if index >= len(q.options):
            return

        response = q.options[index]
        result = self._interaction.submit_press_response(response)

        morale_change = result.get("morale_change", 0)
        rep_change = result.get("reputation_change", 0)
        self._total_morale += morale_change
        self._total_reputation += rep_change

        result_text = (
            f"Response: {response.text}\n"
            f"Morale effect: {morale_change:+d}  |  "
            f"Reputation change: {rep_change:+d}"
        )
        self._set_result(result_text)

        # Disable response buttons, enable next
        self._disable_responses()
        self.page.next_btn.config(state="normal")

        self.page.status_label.config(
            text=f"Running total: Morale {self._total_morale:+d}, "
                 f"Reputation {self._total_reputation:+d}"
        )

    def _next_question(self):
        self._current_index += 1
        self._show_question()

    def _disable_responses(self):
        self.page.response_a_btn.config(state="disabled")
        self.page.response_b_btn.config(state="disabled")
        self.page.response_c_btn.config(state="disabled")

    def _set_result(self, text: str):
        self.page.result_text.config(state="normal")
        self.page.result_text.delete("1.0", "end")
        self.page.result_text.insert("1.0", text)
        self.page.result_text.config(state="disabled")

    def go_back(self):
        back_page = self.controller.get_back_page()
        self.switch(back_page)

    def _bind(self):
        self.page.next_btn.config(command=self._next_question)
        self.page.cancel_btn.config(command=self.go_back)
