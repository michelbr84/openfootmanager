import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class StatsExplorerPage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title_label = ttk.Label(self, text="Stats Explorer", font="Arial 24 bold")
        self.title_label.grid(
            row=0, column=0, padx=10, pady=10, columnspan=2, sticky=NS
        )
        
        self.label = ttk.Label(self, text="Stats Explorer feature is under construction.")
        self.label.grid(row=1, column=0, padx=10, pady=10)

        self.button_frame = ttk.Frame(self)
        self.cancel_btn = ttk.Button(self.button_frame, text="Back")
        self.cancel_btn.pack(side="left", padx=10)

        self.button_frame.grid(
            row=2, column=0, columnspan=2, padx=10, pady=10, sticky=NS
        )
