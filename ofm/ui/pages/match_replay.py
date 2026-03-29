import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class MatchReplayPage(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # Title
        self.title_label = ttk.Label(
            self, text="Match Replay", font="Arial 24 bold"
        )
        self.title_label.grid(
            row=0, column=0, columnspan=2, padx=10, pady=10, sticky=NS
        )

        # ------------------------------------------------------------------
        # Left column: Canvas + Controls
        # ------------------------------------------------------------------
        left_col = ttk.Frame(self)
        left_col.grid(row=1, column=0, sticky=NSEW, padx=(10, 5), pady=5)
        left_col.columnconfigure(0, weight=1)
        left_col.rowconfigure(0, weight=1)

        # Replay canvas (pitch)
        self.replay_canvas = ttk.Canvas(
            left_col, width=800, height=500, bg="green"
        )
        self.replay_canvas.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        # Draw pitch lines
        self.replay_canvas.create_rectangle(
            10, 10, 790, 490, outline="white", width=4
        )
        # Center line
        self.replay_canvas.create_line(
            400, 10, 400, 490, fill="white", width=2
        )
        # Center circle
        self.replay_canvas.create_oval(
            350, 200, 450, 300, outline="white", width=2
        )
        # Left penalty box
        self.replay_canvas.create_rectangle(
            10, 150, 120, 350, outline="white", width=2
        )
        # Right penalty box
        self.replay_canvas.create_rectangle(
            680, 150, 790, 350, outline="white", width=2
        )

        # Controls frame
        controls_frame = ttk.Frame(left_col)
        controls_frame.grid(row=1, column=0, sticky=EW, padx=5, pady=5)

        self.play_btn = ttk.Button(controls_frame, text="Play", bootstyle="success")
        self.play_btn.pack(side="left", padx=5)

        self.pause_btn = ttk.Button(controls_frame, text="Pause", bootstyle="warning")
        self.pause_btn.pack(side="left", padx=5)

        self.prev_btn = ttk.Button(controls_frame, text="Previous Frame")
        self.prev_btn.pack(side="left", padx=5)

        self.next_btn = ttk.Button(controls_frame, text="Next Frame")
        self.next_btn.pack(side="left", padx=5)

        speed_label = ttk.Label(controls_frame, text="Speed:")
        speed_label.pack(side="left", padx=(15, 5))

        self.speed_combo = ttk.Combobox(
            controls_frame,
            values=["0.5x", "1x", "2x", "4x"],
            state="readonly",
            width=6,
        )
        self.speed_combo.set("1x")
        self.speed_combo.pack(side="left", padx=5)

        # Commentary text
        self.commentary_text = ttk.Text(left_col, height=3, state=DISABLED, wrap="word")
        self.commentary_text.grid(row=2, column=0, sticky=EW, padx=5, pady=5)

        # ------------------------------------------------------------------
        # Right column: Highlights + Back
        # ------------------------------------------------------------------
        right_col = ttk.Frame(self)
        right_col.grid(row=1, column=1, sticky=NSEW, padx=(5, 10), pady=5)
        right_col.columnconfigure(0, weight=1)
        right_col.rowconfigure(0, weight=1)

        highlights_frame = ttk.LabelFrame(right_col, text="Highlights")
        highlights_frame.grid(row=0, column=0, sticky=NSEW, pady=(0, 5))
        highlights_frame.columnconfigure(0, weight=1)
        highlights_frame.rowconfigure(0, weight=1)

        highlight_cols = ("Minute", "Event", "Player")
        self.highlights_tree = ttk.Treeview(
            highlights_frame,
            columns=highlight_cols,
            show="headings",
            height=5,
        )
        for col in highlight_cols:
            self.highlights_tree.heading(col, text=col)
            width = 60 if col == "Minute" else 120
            self.highlights_tree.column(col, width=width, minwidth=40)
        self.highlights_tree.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)

        highlights_scroll = ttk.Scrollbar(
            highlights_frame, orient=VERTICAL, command=self.highlights_tree.yview
        )
        highlights_scroll.grid(row=0, column=1, sticky=NS)
        self.highlights_tree.configure(yscrollcommand=highlights_scroll.set)

        # ------------------------------------------------------------------
        # Bottom: Back button
        # ------------------------------------------------------------------
        self.cancel_btn = ttk.Button(self, text="Back")
        self.cancel_btn.grid(
            row=2, column=0, columnspan=2, padx=10, pady=(5, 10), sticky=EW
        )
