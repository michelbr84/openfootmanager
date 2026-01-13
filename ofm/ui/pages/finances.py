import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class FinancesPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.header = ttk.Label(self, text="Finances", font=("Helvetica", 24))
        self.header.pack(pady=20)

        self.balance_label = ttk.Label(self, text="Balance: $0.00", font=("Helvetica", 18))
        self.balance_label.pack(pady=10)

        self.transactions_frame = ttk.Labelframe(self, text="Recent Transactions")
        self.transactions_frame.pack(fill=BOTH, expand=YES, padx=20, pady=20)
        
        # Placeholder for transaction list
        self.trans_list = ttk.Treeview(self.transactions_frame, columns=("Type", "Amount", "Desc"), show='headings')
        self.trans_list.heading("Type", text="Type")
        self.trans_list.heading("Amount", text="Amount")
        self.trans_list.heading("Desc", text="Description")
        self.trans_list.pack(fill=BOTH, expand=YES)

        self.back_btn = ttk.Button(self, text="Back", command=lambda: parent.master.switch("home"))
        self.back_btn.pack(pady=20)
    
    def tkraise(self, aboveThis=None):
        super().tkraise(aboveThis)
        # Refresh logic here would assume we have access to the current club
        # For now, just static or need a way to pass App context.
        # Assuming parent.master has 'app' or logic.
        pass
