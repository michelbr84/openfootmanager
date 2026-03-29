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
        self.action_frame.pack(fill=X, padx=20, pady=10)

        self.buy_btn = ttk.Button(self.action_frame, text="Buy Player", bootstyle="success")
        self.buy_btn.pack(side=RIGHT, padx=5)

        self.sell_btn = ttk.Button(self.action_frame, text="Sell Player", bootstyle="warning")
        self.sell_btn.pack(side=RIGHT, padx=5)

        self.back_btn = ttk.Button(self.action_frame, text="Back", command=lambda: parent.master.switch("home"))
        self.back_btn.pack(side=LEFT, padx=5)

        # Transfer Offer frame
        self.offer_frame = ttk.LabelFrame(self, text="Transfer Offer")
        self.offer_frame.pack(fill=X, padx=20, pady=(0, 20))

        self.selected_player_label = ttk.Label(self.offer_frame, text="Selected: None")
        self.selected_player_label.pack(anchor=W, padx=10, pady=(10, 5))

        offer_row = ttk.Frame(self.offer_frame)
        offer_row.pack(fill=X, padx=10, pady=5)

        ttk.Label(offer_row, text="Offer Amount:").pack(side=LEFT, padx=(0, 5))
        self.offer_entry = ttk.Entry(offer_row, width=20)
        self.offer_entry.pack(side=LEFT, padx=5)

        self.submit_offer_btn = ttk.Button(offer_row, text="Submit Offer", bootstyle="primary")
        self.submit_offer_btn.pack(side=LEFT, padx=5)

        self.offer_result_label = ttk.Label(self.offer_frame, text="")
        self.offer_result_label.pack(anchor=W, padx=10, pady=(0, 10))
