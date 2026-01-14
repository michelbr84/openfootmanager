import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class TeamFormationPage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title_label = ttk.Label(self, text="Team Formation", font="Arial 24 bold")
        self.title_label.grid(
            row=0, column=0, padx=10, pady=10, columnspan=2, sticky=NS
        )
        
        self.options_frame = ttk.Frame(self)
        self.formation_label = ttk.Label(self.options_frame, text="Formation:")
        self.formation_label.pack(side="left", padx=5)
        
        self.formation_combobox = ttk.Combobox(self.options_frame, state="readonly")
        self.formation_combobox.pack(side="left", padx=5)
        
        self.options_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky=EW)

        self.tree = ttk.Treeview(self, columns=("name", "position", "start_pos"), show="headings")
        self.tree.heading("name", text="Player Name")
        self.tree.heading("position", text="Best Position")
        self.tree.heading("start_pos", text="Current Position")
        self.tree.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky=NSEW)
        
        self.button_frame = ttk.Frame(self)

        self.cancel_btn = ttk.Button(self.button_frame, text="Back")
        self.cancel_btn.pack(side="left", padx=10)

        self.button_frame.grid(
            row=3, column=0, columnspan=2, padx=10, pady=10, sticky=NS
        )
