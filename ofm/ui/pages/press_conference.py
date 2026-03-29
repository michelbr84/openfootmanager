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
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class PressConferencePage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        # Row 0 - Title
        self.title_label = ttk.Label(
            self, text="Press Conference", font="Arial 24 bold"
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky=W)

        # Row 1 - Question label
        self.question_label = ttk.Label(
            self,
            text="No questions yet.",
            font="Arial 13",
            wraplength=600,
        )
        self.question_label.grid(row=1, column=0, padx=20, pady=10, sticky=W)

        # Row 2 - Response buttons frame
        response_frame = ttk.Frame(self)
        response_frame.grid(row=2, column=0, padx=20, pady=5, sticky=EW)
        response_frame.columnconfigure(0, weight=1)

        self.response_a_btn = ttk.Button(
            response_frame, text="Response A", bootstyle="primary"
        )
        self.response_a_btn.grid(row=0, column=0, padx=5, pady=3, sticky=EW)

        self.response_b_btn = ttk.Button(
            response_frame, text="Response B", bootstyle="secondary"
        )
        self.response_b_btn.grid(row=1, column=0, padx=5, pady=3, sticky=EW)

        self.response_c_btn = ttk.Button(
            response_frame, text="Response C", bootstyle="info"
        )
        self.response_c_btn.grid(row=2, column=0, padx=5, pady=3, sticky=EW)

        # Row 3 - Result text
        self.result_text = ttk.Text(self, height=4, state=DISABLED, wrap="word")
        self.result_text.grid(row=3, column=0, padx=20, pady=10, sticky=NSEW)

        # Row 4 - Next question button
        self.next_btn = ttk.Button(
            self, text="Next Question", bootstyle="success"
        )
        self.next_btn.grid(row=4, column=0, padx=20, pady=5, sticky=EW)

        # Row 5 - Status label
        self.status_label = ttk.Label(self, text="", font="Arial 11")
        self.status_label.grid(row=5, column=0, padx=20, pady=5, sticky=W)

        # Row 6 - Back button
        self.cancel_btn = ttk.Button(self, text="Back")
        self.cancel_btn.grid(row=6, column=0, padx=20, pady=(5, 20), sticky=W)
