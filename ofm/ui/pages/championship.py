import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.tableview import Tableview

class ChampionshipPage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title_label = ttk.Label(self, text="Championship", font="Arial 24 bold")
        self.title_label.grid(
            row=0, column=0, padx=10, pady=10, columnspan=2, sticky=NS
        )

        self.tree = ttk.Treeview(self, columns=("pos", "team", "p", "w", "d", "l", "pts"), show="headings")
        self.tree.heading("pos", text="Pos")
        self.tree.heading("team", text="Team")
        self.tree.heading("p", text="P")
        self.tree.heading("w", text="W")
        self.tree.heading("d", text="D")
        self.tree.heading("l", text="L")
        self.tree.heading("pts", text="Pts")
        
        self.tree.column("pos", width=50, anchor="center")
        self.tree.column("team", width=200, anchor="w")
        self.tree.column("p", width=50, anchor="center")
        self.tree.column("w", width=50, anchor="center")
        self.tree.column("d", width=50, anchor="center")
        self.tree.column("l", width=50, anchor="center")
        self.tree.column("pts", width=50, anchor="center")

        self.tree.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky=NSEW)
        
        self.button_frame = ttk.Frame(self)

        self.cancel_btn = ttk.Button(self.button_frame, text="Back")
        self.cancel_btn.pack(side="left", padx=10)

        self.button_frame.grid(
            row=2, column=0, columnspan=2, padx=10, pady=10, sticky=NS
        )
