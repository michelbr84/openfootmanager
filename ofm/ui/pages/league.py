import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class LeaguePage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.header = ttk.Label(self, text="League Table", font=("Helvetica", 24))
        self.header.pack(pady=20)

        self.table_frame = ttk.Frame(self)
        self.table_frame.pack(fill=BOTH, expand=YES, padx=20)

        self.tree = ttk.Treeview(self.table_frame, columns=("Pos", "Club", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"), show='headings')
        self.tree.heading("Pos", text="#")
        self.tree.heading("Club", text="Club")
        self.tree.heading("P", text="P")
        self.tree.heading("W", text="W")
        self.tree.heading("D", text="D")
        self.tree.heading("L", text="L")
        self.tree.heading("GF", text="GF")
        self.tree.heading("GA", text="GA")
        self.tree.heading("GD", text="GD")
        self.tree.heading("Pts", text="Pts")
        
        self.tree.column("Pos", width=30)
        self.tree.column("Club", width=200)
        self.tree.column("P", width=30)
        
        self.tree.pack(fill=BOTH, expand=YES)

        self.back_btn = ttk.Button(self, text="Back", command=lambda: parent.master.switch("home"))
        self.back_btn.pack(pady=20)
