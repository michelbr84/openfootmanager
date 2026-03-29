from ..pages.match_replay import MatchReplayPage
from .controllerinterface import ControllerInterface
from ...core.simulation.match_visuals import MatchAnimator, MatchFrame, HighlightGenerator


class MatchReplayController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: MatchReplayPage):
        self.controller = controller
        self.page = page
        self._frames: list = []
        self._current_frame: int = 0
        self._playing: bool = False
        self._timer_id = None
        self._highlights: list[dict] = []
        self._bind()

    def switch(self, page: str):
        self.controller.switch(page)

    def initialize(self):
        self._pause()
        self._current_frame = 0
        self._frames = []
        self._highlights = []

        # Generate sample frames since we may not have real match data
        self._generate_sample_frames()

        # Populate highlights tree
        self._populate_highlights()

        # Draw first frame
        if self._frames:
            self._draw_frame(self._frames[0])

        # Clear commentary
        self._set_commentary("")

    def _generate_sample_frames(self):
        """Generate sample animation frames for demonstration."""
        import random

        # Create sample player names
        home_players = [f"Home_{i}" for i in range(1, 12)]
        away_players = [f"Away_{i}" for i in range(1, 12)]

        # Generate base positions (4-4-2 layout)
        home_positions = {}
        # GK
        home_positions[home_players[0]] = (5.0, 50.0)
        # Defenders
        for i, idx in enumerate([1, 2, 3, 4]):
            home_positions[home_players[idx]] = (15.0, 15.0 + i * 23.0)
        # Midfielders
        for i, idx in enumerate([5, 6, 7, 8]):
            home_positions[home_players[idx]] = (35.0, 15.0 + i * 23.0)
        # Forwards
        for i, idx in enumerate([9, 10]):
            home_positions[home_players[idx]] = (45.0, 30.0 + i * 40.0)

        away_positions = {}
        # GK
        away_positions[away_players[0]] = (95.0, 50.0)
        # Defenders
        for i, idx in enumerate([1, 2, 3, 4]):
            away_positions[away_players[idx]] = (85.0, 15.0 + i * 23.0)
        # Midfielders
        for i, idx in enumerate([5, 6, 7, 8]):
            away_positions[away_players[idx]] = (65.0, 15.0 + i * 23.0)
        # Forwards
        for i, idx in enumerate([9, 10]):
            away_positions[away_players[idx]] = (55.0, 30.0 + i * 40.0)

        all_positions = {**home_positions, **away_positions}

        # Generate 90 frames (one per "minute")
        random.seed(42)
        ball_x, ball_y = 50.0, 50.0

        for minute in range(90):
            # Move ball randomly
            ball_x += random.uniform(-5, 5)
            ball_y += random.uniform(-3, 3)
            ball_x = max(2, min(98, ball_x))
            ball_y = max(5, min(95, ball_y))

            # Slightly jitter player positions
            frame_positions = {}
            for name, (px, py) in all_positions.items():
                jx = px + random.uniform(-2, 2)
                jy = py + random.uniform(-2, 2)
                frame_positions[name] = (max(0, min(100, jx)), max(0, min(100, jy)))

            event_text = None
            if minute in (23, 45, 67, 78):
                event_text = f"GOAL at minute {minute}!"
            elif minute in (12, 34, 55, 80):
                event_text = f"Shot on target at minute {minute}"

            self._frames.append(
                MatchFrame(
                    timestamp=float(minute),
                    ball_x=ball_x,
                    ball_y=ball_y,
                    player_positions=frame_positions,
                    event_text=event_text,
                )
            )

        # Generate sample highlights
        self._highlights = [
            {"minute": 12, "event_type": "SHOT", "player": "Home_10"},
            {"minute": 23, "event_type": "GOAL", "player": "Home_9"},
            {"minute": 34, "event_type": "SHOT", "player": "Away_10"},
            {"minute": 45, "event_type": "GOAL", "player": "Away_9"},
            {"minute": 55, "event_type": "SHOT", "player": "Home_7"},
            {"minute": 67, "event_type": "GOAL", "player": "Home_10"},
            {"minute": 78, "event_type": "GOAL", "player": "Away_7"},
            {"minute": 80, "event_type": "SHOT", "player": "Home_9"},
        ]

    def _populate_highlights(self):
        tree = self.page.highlights_tree
        for item in tree.get_children():
            tree.delete(item)

        for h in self._highlights:
            tree.insert(
                "",
                "end",
                values=(
                    f"{h.get('minute', 0):.0f}'",
                    h.get("event_type", ""),
                    h.get("player", h.get("attacker", "")),
                ),
            )

    def _draw_frame(self, frame: MatchFrame):
        """Draw a single frame on the canvas."""
        canvas = self.page.replay_canvas
        canvas_w = 800
        canvas_h = 500
        margin_x = 10
        margin_y = 10
        pitch_w = canvas_w - 2 * margin_x
        pitch_h = canvas_h - 2 * margin_y

        # Clear previous player/ball items
        canvas.delete("player")
        canvas.delete("ball")

        # Draw ball as yellow dot
        bx = margin_x + frame.ball_x / 100.0 * pitch_w
        by = margin_y + frame.ball_y / 100.0 * pitch_h
        canvas.create_oval(
            bx - 5, by - 5, bx + 5, by + 5,
            fill="yellow", outline="black", tags="ball"
        )

        # Draw player positions
        for name, (px, py) in frame.player_positions.items():
            x = margin_x + px / 100.0 * pitch_w
            y = margin_y + py / 100.0 * pitch_h

            # Home players white, away players red
            color = "white" if name.startswith("Home") else "red"

            canvas.create_oval(
                x - 6, y - 6, x + 6, y + 6,
                fill=color, outline="black", tags="player"
            )
            canvas.create_text(
                x, y - 12, text=name.split("_")[-1],
                fill="white", font=("Helvetica", 7), tags="player"
            )

        # Update commentary if there is event text
        if frame.event_text:
            self._set_commentary(frame.event_text)

    def _set_commentary(self, text: str):
        self.page.commentary_text.config(state="normal")
        self.page.commentary_text.delete("1.0", "end")
        self.page.commentary_text.insert("1.0", text)
        self.page.commentary_text.config(state="disabled")

    def _get_delay(self) -> int:
        """Return delay in ms based on selected speed."""
        speed_str = self.page.speed_combo.get()
        speed_map = {"0.5x": 400, "1x": 200, "2x": 100, "4x": 50}
        return speed_map.get(speed_str, 200)

    def _play(self):
        if not self._frames:
            return
        self._playing = True
        self._advance_frame()

    def _pause(self):
        self._playing = False
        if self._timer_id is not None:
            try:
                self.page.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None

    def _next_frame(self):
        if not self._frames:
            return
        self._current_frame = min(self._current_frame + 1, len(self._frames) - 1)
        self._draw_frame(self._frames[self._current_frame])

    def _prev_frame(self):
        if not self._frames:
            return
        self._current_frame = max(self._current_frame - 1, 0)
        self._draw_frame(self._frames[self._current_frame])

    def _advance_frame(self):
        if not self._playing or not self._frames:
            return
        if self._current_frame < len(self._frames) - 1:
            self._current_frame += 1
            self._draw_frame(self._frames[self._current_frame])
            self._timer_id = self.page.after(self._get_delay(), self._advance_frame)
        else:
            self._playing = False

    def _on_highlight_select(self, event=None):
        """Jump to the frame corresponding to the selected highlight."""
        selection = self.page.highlights_tree.selection()
        if not selection:
            return
        item = self.page.highlights_tree.item(selection[0])
        minute_str = item["values"][0] if item["values"] else ""
        # Parse minute from e.g. "23'"
        try:
            minute = int(str(minute_str).replace("'", "").strip())
        except (ValueError, TypeError):
            return

        # Find closest frame
        if not self._frames:
            return
        best_idx = 0
        best_diff = abs(self._frames[0].timestamp - minute)
        for i, f in enumerate(self._frames):
            diff = abs(f.timestamp - minute)
            if diff < best_diff:
                best_diff = diff
                best_idx = i

        self._current_frame = best_idx
        self._draw_frame(self._frames[self._current_frame])

    def _go_back(self):
        self._pause()
        self.switch(self.controller.get_back_page())

    def _bind(self):
        self.page.play_btn.config(command=self._play)
        self.page.pause_btn.config(command=self._pause)
        self.page.next_btn.config(command=self._next_frame)
        self.page.prev_btn.config(command=self._prev_frame)
        self.page.cancel_btn.config(command=self._go_back)
        self.page.highlights_tree.bind("<<TreeviewSelect>>", self._on_highlight_select)
