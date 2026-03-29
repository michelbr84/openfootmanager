import json
import math

from ..pages.team_formation import TeamFormationPage
from .controllerinterface import ControllerInterface
from ...core.football.formation import Formation, FORMATION_STRINGS

class TeamFormationController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: TeamFormationPage):
        self.controller = controller
        self.page = page
        self.club = None
        self._dragging = None  # Index of player being dragged
        self._dot_positions = []  # List of (cx, cy, player_index) for canvas dots
        self._bind()

    def initialize(self):
        self.page.formation_combobox['values'] = FORMATION_STRINGS
        
        self.page.status_label.config(text="")

        team_data = self.controller.current_user_team
        if not team_data:
             # If no team selected, maybe show empty or error?
             # For now, just return
             return

        # We probably need to load the full team object with players
        # The team_data stored in OFMController might be just the dict from clubs.json
        # We need to construct the team object possibly.
        
        # NOTE: Loading the FULL team object with simulation capabilities might be complex here
        # depending on how 'TeamSelection' stored the data. 
        # In TeamSelectionController we did: self.controller.current_user_team = selected_club (which is a dict)
        
        # So we use the DB to load the full object
        players_dicts = self.controller.db.load_players()
        club_objects = self.controller.db.load_club_objects([team_data], players_dicts)
        if club_objects:
             self.club = club_objects[0]
             # Create a formation object to help us listing players
             self.formation = Formation(self.club.default_formation)
             # Distribute players for initial view
             self.formation.get_best_players(self.club.squad)
             
             self.page.formation_combobox.set(self.formation.formation_string)
             self.update_player_list()
             self._draw_formation_canvas()

    def update_player_list(self):
        for i in self.page.tree.get_children():
            self.page.tree.delete(i)
        
        # Starting 11
        for p in self.formation.players:
             self.page.tree.insert("", "end", values=(p.player.details.short_name, p.player.details.get_best_position().name, p.current_position.name))
        
        # Bench
        for p in self.formation.bench:
             self.page.tree.insert("", "end", values=(p.player.details.short_name, p.player.details.get_best_position().name, "Bench"))

    def on_formation_change(self, event):
        new_formation = self.page.formation_combobox.get()
        if new_formation and self.club:
            try:
                self.formation.change_formation(new_formation)
                self.update_player_list()
                self._draw_formation_canvas()
            except Exception as e:
                print(f"Error changing formation: {e}")

    # ------------------------------------------------------------------
    # Formation Canvas (drag-and-drop)
    # ------------------------------------------------------------------

    def _draw_formation_canvas(self):
        """Draw player dots on the canvas based on current formation positions.

        Layout: GK on the left, FW on the right (same as visualizer convention).
        """
        canvas = self.page.formation_canvas
        canvas.delete("dot")
        canvas.delete("label")
        self._dot_positions = []

        if not hasattr(self, "formation") or self.formation is None:
            return

        cw = 400
        ch = 300
        margin_x = 20
        margin_y = 20
        pitch_w = cw - 2 * margin_x
        pitch_h = ch - 2 * margin_y

        players = list(self.formation.players)
        if not players:
            return

        # Build position groups: GK, then formation lines
        # GK at x=5%, defenders ~20%, midfielders ~50%, forwards ~80%
        groups = []
        # GK
        gk_players = [p for p in players if p.current_position.name == "GK"]
        if gk_players:
            groups.append((0.08, gk_players))

        # Use position categories to group: DF, MF, FW
        df_players = [p for p in players if p.current_position.name in ("CB", "LB", "RB", "LWB", "RWB")]
        mf_players = [p for p in players if p.current_position.name in ("CDM", "CM", "CAM", "LM", "RM", "DM")]
        fw_players = [p for p in players if p.current_position.name in ("CF", "LW", "RW", "ST", "SS")]

        # Fallback: use the formation's own groups
        if not df_players and not mf_players and not fw_players:
            df_players = list(self.formation.df) if hasattr(self.formation, "df") and self.formation.df else []
            mf_players = list(self.formation.mf) if hasattr(self.formation, "mf") and self.formation.mf else []
            fw_players = list(self.formation.fw) if hasattr(self.formation, "fw") and self.formation.fw else []

        if df_players:
            groups.append((0.25, df_players))
        if mf_players:
            groups.append((0.50, mf_players))
        if fw_players:
            groups.append((0.80, fw_players))

        player_index_map = {id(p): i for i, p in enumerate(players)}

        for x_frac, group in groups:
            cx = margin_x + x_frac * pitch_w
            count = len(group)
            for gi, p in enumerate(group):
                if count == 1:
                    cy = margin_y + 0.5 * pitch_h
                else:
                    cy = margin_y + (0.15 + 0.7 * gi / (count - 1)) * pitch_h

                idx = player_index_map.get(id(p), 0)
                self._dot_positions.append((cx, cy, idx))

                canvas.create_oval(
                    cx - 8, cy - 8, cx + 8, cy + 8,
                    fill="white", outline="black", width=2,
                    tags=("dot", f"dot_{idx}")
                )
                short_name = p.player.details.short_name if hasattr(p, "player") else str(p)
                # Truncate name for display
                display_name = short_name[:8] if len(short_name) > 8 else short_name
                canvas.create_text(
                    cx, cy - 14, text=display_name,
                    fill="white", font=("Helvetica", 7),
                    tags=("label", f"label_{idx}")
                )

    def _on_canvas_click(self, event):
        """Find closest player dot and start dragging."""
        self._dragging = None
        if not self._dot_positions:
            return

        best_dist = float("inf")
        best_idx = None
        for cx, cy, idx in self._dot_positions:
            dist = math.hypot(event.x - cx, event.y - cy)
            if dist < best_dist and dist < 25:
                best_dist = dist
                best_idx = idx

        if best_idx is not None:
            self._dragging = best_idx

    def _on_canvas_drag(self, event):
        """Move the dragged dot to mouse position."""
        if self._dragging is None:
            return

        canvas = self.page.formation_canvas
        idx = self._dragging

        # Move the oval and label
        canvas.delete(f"dot_{idx}")
        canvas.delete(f"label_{idx}")

        cx, cy = event.x, event.y
        canvas.create_oval(
            cx - 8, cy - 8, cx + 8, cy + 8,
            fill="yellow", outline="black", width=2,
            tags=("dot", f"dot_{idx}")
        )

        players = list(self.formation.players)
        if idx < len(players):
            p = players[idx]
            short_name = p.player.details.short_name if hasattr(p, "player") else str(p)
            display_name = short_name[:8] if len(short_name) > 8 else short_name
        else:
            display_name = "?"
        canvas.create_text(
            cx, cy - 14, text=display_name,
            fill="white", font=("Helvetica", 7),
            tags=("label", f"label_{idx}")
        )

        # Update stored position
        for i, (dcx, dcy, didx) in enumerate(self._dot_positions):
            if didx == idx:
                self._dot_positions[i] = (cx, cy, idx)
                break

    def _on_canvas_release(self, event):
        """Find the closest position slot to the drop location and swap players if needed."""
        if self._dragging is None:
            return

        dragged_idx = self._dragging
        self._dragging = None

        # Find closest OTHER dot position
        best_dist = float("inf")
        best_swap_idx = None
        drop_x, drop_y = event.x, event.y

        for cx, cy, idx in self._dot_positions:
            if idx == dragged_idx:
                continue
            dist = math.hypot(drop_x - cx, drop_y - cy)
            if dist < best_dist:
                best_dist = dist
                best_swap_idx = idx

        # Only swap if within a reasonable distance
        if best_swap_idx is not None and best_dist < 50:
            players = list(self.formation.players)
            if dragged_idx < len(players) and best_swap_idx < len(players):
                # Swap the two players in the formation
                pa = players[dragged_idx]
                pb = players[best_swap_idx]
                # Swap current positions
                pa.current_position, pb.current_position = pb.current_position, pa.current_position
                # Swap in the list
                self.formation.players[dragged_idx] = pb
                self.formation.players[best_swap_idx] = pa
                self.update_player_list()

        # Redraw canvas to reflect final state
        self._draw_formation_canvas()

    def switch(self, page):
        self.controller.switch(page)

    def go_to_debug_home_page(self):
        self.switch(self.controller.get_back_page())

    def _save_formation(self):
        team_data = self.controller.current_user_team
        if not team_data:
            self.page.status_label.config(text="No team selected. Select a team first.")
            return

        formation_str = self.page.formation_combobox.get()
        if not formation_str:
            return

        # Update the current_user_team dict
        team_data["default_formation"] = formation_str

        # Persist to clubs.json
        clubs = self.controller.db.load_clubs()
        for club in clubs:
            if club["id"] == team_data["id"]:
                club["default_formation"] = formation_str
                break

        with open(self.controller.db.clubs_file, "w", encoding="utf-8") as fp:
            json.dump(clubs, fp)

        self.page.status_label.config(
            text=f"Formation '{formation_str}' saved successfully!"
        )

    def _bind(self):
        self.page.cancel_btn.config(command=self.go_to_debug_home_page)
        self.page.formation_combobox.bind("<<ComboboxSelected>>", self.on_formation_change)
        self.page.save_btn.config(command=self._save_formation)
        self.page.formation_canvas.bind("<Button-1>", self._on_canvas_click)
        self.page.formation_canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.page.formation_canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
