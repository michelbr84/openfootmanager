import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class CommunityHubPage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Title
        self.title_label = ttk.Label(self, text="Community Hub", font=("Helvetica", 24))
        self.title_label.grid(row=0, column=0, pady=20)

        # Notebook with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky=NSEW, padx=20, pady=(0, 10))

        # ---- Tab 1: Challenges ----
        challenges_tab = ttk.Frame(self.notebook)
        self.notebook.add(challenges_tab, text="Challenges")
        challenges_tab.columnconfigure(0, weight=1)
        challenges_tab.rowconfigure(0, weight=1)

        challenges_cols = ("Name", "Description", "Difficulty")
        self.challenges_tree = ttk.Treeview(
            challenges_tab, columns=challenges_cols, show="headings", height=6
        )
        self.challenges_tree.heading("Name", text="Name")
        self.challenges_tree.column("Name", width=150, minwidth=100)
        self.challenges_tree.heading("Description", text="Description")
        self.challenges_tree.column("Description", width=350, minwidth=150)
        self.challenges_tree.heading("Difficulty", text="Difficulty")
        self.challenges_tree.column("Difficulty", width=100, minwidth=60)
        self.challenges_tree.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        challenges_action = ttk.Frame(challenges_tab)
        challenges_action.grid(row=1, column=0, sticky=EW, padx=5, pady=5)

        self.start_challenge_btn = ttk.Button(
            challenges_action, text="Start Challenge", bootstyle="success"
        )
        self.start_challenge_btn.pack(side=LEFT, padx=5)

        # ---- Tab 2: Multiplayer ----
        mp_tab = ttk.Frame(self.notebook)
        self.notebook.add(mp_tab, text="Multiplayer")
        mp_tab.columnconfigure(0, weight=1)
        mp_tab.columnconfigure(1, weight=1)

        ttk.Label(mp_tab, text="Player 1 Name:").grid(row=0, column=0, padx=10, pady=(15, 5), sticky=E)
        self.p1_entry = ttk.Entry(mp_tab, width=25)
        self.p1_entry.grid(row=0, column=1, padx=10, pady=(15, 5), sticky=W)

        ttk.Label(mp_tab, text="Player 2 Name:").grid(row=1, column=0, padx=10, pady=5, sticky=E)
        self.p2_entry = ttk.Entry(mp_tab, width=25)
        self.p2_entry.grid(row=1, column=1, padx=10, pady=5, sticky=W)

        self.hotseat_btn = ttk.Button(mp_tab, text="Hot Seat", bootstyle="primary")
        self.hotseat_btn.grid(row=2, column=0, columnspan=2, padx=10, pady=15)

        self.mp_status_label = ttk.Label(mp_tab, text="")
        self.mp_status_label.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

        # ---- Tab 3: Mods ----
        mods_tab = ttk.Frame(self.notebook)
        self.notebook.add(mods_tab, text="Mods")
        mods_tab.columnconfigure(0, weight=1)
        mods_tab.rowconfigure(0, weight=1)

        mods_cols = ("Name", "Type", "Author")
        self.mods_tree = ttk.Treeview(
            mods_tab, columns=mods_cols, show="headings", height=6
        )
        self.mods_tree.heading("Name", text="Name")
        self.mods_tree.column("Name", width=200, minwidth=100)
        self.mods_tree.heading("Type", text="Type")
        self.mods_tree.column("Type", width=100, minwidth=60)
        self.mods_tree.heading("Author", text="Author")
        self.mods_tree.column("Author", width=150, minwidth=80)
        self.mods_tree.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        mods_action = ttk.Frame(mods_tab)
        mods_action.grid(row=1, column=0, sticky=EW, padx=5, pady=5)

        self.load_mod_btn = ttk.Button(mods_action, text="Load Mod", bootstyle="primary")
        self.load_mod_btn.pack(side=LEFT, padx=5)

        self.export_btn = ttk.Button(mods_action, text="Export DB", bootstyle="info")
        self.export_btn.pack(side=LEFT, padx=5)

        self.import_btn = ttk.Button(mods_action, text="Import DB", bootstyle="warning")
        self.import_btn.pack(side=LEFT, padx=5)

        self.mod_status_label = ttk.Label(mods_action, text="")
        self.mod_status_label.pack(side=LEFT, padx=20)

        # ---- Back button ----
        self.back_btn = ttk.Button(self, text="Back")
        self.back_btn.grid(row=2, column=0, padx=20, pady=(0, 20), sticky=EW)
