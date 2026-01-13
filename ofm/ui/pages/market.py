import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class MarketPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.header = ttk.Label(self, text="Transfer Market", font=("Helvetica", 24))
        self.header.pack(pady=20)

        # Filter section
        self.filter_frame = ttk.Frame(self)
        self.filter_frame.pack(fill=X, padx=20, pady=10)
        self.search_entry = ttk.Entry(self.filter_frame)
        self.search_entry.pack(side=LEFT, padx=5)
        self.search_btn = ttk.Button(self.filter_frame, text="Search")
        self.search_btn.pack(side=LEFT, padx=5)

        # Player List
        self.list_frame = ttk.Frame(self)
        self.list_frame.pack(fill=BOTH, expand=YES, padx=20)

        self.tree = ttk.Treeview(self.list_frame, columns=("Name", "Age", "Pos", "Overall", "Value", "Club"), show='headings')
        self.tree.heading("Name", text="Name")
        self.tree.heading("Age", text="Age")
        self.tree.heading("Pos", text="Position")
        self.tree.heading("Overall", text="Ovr")
        self.tree.heading("Value", text="Value")
        self.tree.heading("Club", text="Club")
        
        self.tree.pack(fill=BOTH, expand=YES)

        # Actions
        self.action_frame = ttk.Frame(self)
        self.action_frame.pack(fill=X, padx=20, pady=20)
        
        self.buy_btn = ttk.Button(self.action_frame, text="Buy Player", bootstyle="success")
        self.buy_btn.pack(side=RIGHT)

        self.back_btn = ttk.Button(self.action_frame, text="Back", command=lambda: parent.master.switch("home"))
        self.back_btn.pack(side=LEFT)
