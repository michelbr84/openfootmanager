import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class LoanManagementPage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        # Title
        self.title_label = ttk.Label(self, text="Loan Management", font=("Helvetica", 24))
        self.title_label.grid(row=0, column=0, pady=20)

        # Players Loaned In
        loaned_in_frame = ttk.LabelFrame(self, text="Players Loaned In")
        loaned_in_frame.grid(row=1, column=0, sticky=NSEW, padx=20, pady=(0, 10))
        loaned_in_frame.columnconfigure(0, weight=1)
        loaned_in_frame.rowconfigure(0, weight=1)

        loans_in_cols = ("Player", "From Club", "Fee", "Expires")
        self.loans_in_tree = ttk.Treeview(
            loaned_in_frame, columns=loans_in_cols, show="headings", height=6
        )
        for col in loans_in_cols:
            self.loans_in_tree.heading(col, text=col)
            self.loans_in_tree.column(col, width=140, minwidth=80)
        self.loans_in_tree.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        loans_in_scroll = ttk.Scrollbar(
            loaned_in_frame, orient=VERTICAL, command=self.loans_in_tree.yview
        )
        loans_in_scroll.grid(row=0, column=1, sticky=NS)
        self.loans_in_tree.configure(yscrollcommand=loans_in_scroll.set)

        # Players Loaned Out
        loaned_out_frame = ttk.LabelFrame(self, text="Players Loaned Out")
        loaned_out_frame.grid(row=2, column=0, sticky=NSEW, padx=20, pady=(0, 10))
        loaned_out_frame.columnconfigure(0, weight=1)
        loaned_out_frame.rowconfigure(0, weight=1)

        loans_out_cols = ("Player", "To Club", "Fee", "Expires")
        self.loans_out_tree = ttk.Treeview(
            loaned_out_frame, columns=loans_out_cols, show="headings", height=6
        )
        for col in loans_out_cols:
            self.loans_out_tree.heading(col, text=col)
            self.loans_out_tree.column(col, width=140, minwidth=80)
        self.loans_out_tree.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        loans_out_scroll = ttk.Scrollbar(
            loaned_out_frame, orient=VERTICAL, command=self.loans_out_tree.yview
        )
        loans_out_scroll.grid(row=0, column=1, sticky=NS)
        self.loans_out_tree.configure(yscrollcommand=loans_out_scroll.set)

        # Actions
        action_frame = ttk.Frame(self)
        action_frame.grid(row=3, column=0, sticky=EW, padx=20, pady=10)

        self.loan_out_btn = ttk.Button(action_frame, text="Loan Out Player", bootstyle="warning")
        self.loan_out_btn.pack(side=LEFT, padx=5)

        self.recall_btn = ttk.Button(action_frame, text="Recall Loan", bootstyle="info")
        self.recall_btn.pack(side=LEFT, padx=5)

        self.status_label = ttk.Label(action_frame, text="")
        self.status_label.pack(side=LEFT, padx=20)

        self.back_btn = ttk.Button(action_frame, text="Back")
        self.back_btn.pack(side=RIGHT, padx=5)
