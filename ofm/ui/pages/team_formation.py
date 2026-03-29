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

        # Main content frame for treeview and canvas side-by-side
        self.content_frame = ttk.Frame(self)
        self.content_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky=NSEW)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=0)
        self.content_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(self.content_frame, columns=("name", "position", "start_pos"), show="headings")
        self.tree.heading("name", text="Player Name")
        self.tree.heading("position", text="Best Position")
        self.tree.heading("start_pos", text="Current Position")
        self.tree.grid(row=0, column=0, padx=(0, 10), sticky=NSEW)

        # Formation canvas for drag-and-drop
        self.formation_canvas = ttk.Canvas(
            self.content_frame, width=400, height=300, bg="#2a5a2a"
        )
        self.formation_canvas.grid(row=0, column=1, sticky=NSEW)

        # Draw pitch outline on the canvas
        self.formation_canvas.create_rectangle(5, 5, 395, 295, outline="white", width=2)
        self.formation_canvas.create_line(200, 5, 200, 295, fill="white", width=1)
        self.formation_canvas.create_oval(175, 125, 225, 175, outline="white", width=1)

        self.button_frame = ttk.Frame(self)

        self.cancel_btn = ttk.Button(self.button_frame, text="Back")
        self.cancel_btn.pack(side="left", padx=10)

        self.save_btn = ttk.Button(self.button_frame, text="Save Formation", bootstyle="success")
        self.save_btn.pack(side="left", padx=10)

        self.button_frame.grid(
            row=3, column=0, columnspan=2, padx=10, pady=10, sticky=NS
        )

        self.status_label = ttk.Label(self, text="", font=("Helvetica", 11))
        self.status_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky=NS)
