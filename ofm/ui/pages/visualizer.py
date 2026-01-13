import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class VisualizerPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.header = ttk.Label(self, text="Match Visualizer", font=("Helvetica", 24))
        self.header.pack(pady=20)

        self.canvas = ttk.Canvas(self, width=800, height=600, bg="green")
        self.canvas.pack(pady=20)
        
        # Static representation of a pitch
        self.canvas.create_rectangle(10, 10, 790, 590, outline="white", width=4)
        self.canvas.create_line(400, 10, 400, 590, fill="white", width=2)
        self.canvas.create_oval(350, 250, 450, 350, outline="white", width=2)

        self.back_btn = ttk.Button(self, text="Back", command=lambda: parent.master.switch("debug_home"))
        self.back_btn.pack(pady=20)
