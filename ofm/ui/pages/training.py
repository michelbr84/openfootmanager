import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class TrainingPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.header = ttk.Label(self, text="Training Ground", font=("Helvetica", 24))
        self.header.pack(pady=20)

        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill=BOTH, expand=YES, padx=50)

        # Focus Selection
        self.focus_label = ttk.Label(self.content_frame, text="Select Training Focus:", font=("Helvetica", 14))
        self.focus_label.pack(pady=10)

        self.focus_var = ttk.StringVar(value="General")
        self.focus_combo = ttk.Combobox(self.content_frame, textvariable=self.focus_var, values=["General", "Attack", "Defense", "Fitness"])
        self.focus_combo.pack(pady=10)

        self.train_btn = ttk.Button(self.content_frame, text="Run Session", bootstyle="primary", command=self.run_training)
        self.train_btn.pack(pady=20)

        self.result_label = ttk.Label(self.content_frame, text="", font=("Helvetica", 12))
        self.result_label.pack(pady=20)

        self.back_btn = ttk.Button(self, text="Back", command=lambda: parent.master.switch("home"))
        self.back_btn.pack(pady=20)

    def run_training(self):
        # Trigger training logic here
        self.result_label.config(text="Training Completed! (Simulation placeholder)")
