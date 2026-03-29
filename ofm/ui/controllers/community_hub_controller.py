from pathlib import Path
from tkinter import messagebox, filedialog

from ..pages.community_hub import CommunityHubPage
from .controllerinterface import ControllerInterface
from ...core.community import ChallengeMode
from ...core.mod_support import ModLoader
from ...core.modding_extended import DatabaseImportExport


class CommunityHubController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: CommunityHubPage):
        self.controller = controller
        self.page = page
        self._challenge_mode = ChallengeMode()
        self._mod_loader = ModLoader()
        self._discovered_mods = []
        self._bind()

    def switch(self, page):
        self.controller.switch(page)

    def initialize(self):
        """Load challenges and discover mods."""
        self._populate_challenges()
        self._discover_mods()

    def _populate_challenges(self):
        tree = self.page.challenges_tree
        for item in tree.get_children():
            tree.delete(item)

        challenges = self._challenge_mode.get_available_challenges()
        for ch in challenges:
            tree.insert("", "end", values=(
                ch.name,
                ch.description,
                ch.difficulty,
            ))

    def _discover_mods(self):
        tree = self.page.mods_tree
        for item in tree.get_children():
            tree.delete(item)

        try:
            self._discovered_mods = self._mod_loader.discover_mods()
        except Exception:
            self._discovered_mods = []

        for mod in self._discovered_mods:
            tree.insert("", "end", values=(
                mod.name,
                mod.mod_type.value,
                mod.author,
            ))

        if not self._discovered_mods:
            self.page.mod_status_label.config(text="No mods found in mods directory.")
        else:
            self.page.mod_status_label.config(
                text=f"{len(self._discovered_mods)} mod(s) discovered."
            )

    def _start_challenge(self):
        """Set up challenge conditions and start new career with them."""
        selected = self.page.challenges_tree.selection()
        if not selected:
            messagebox.showinfo("Challenges", "Please select a challenge first.")
            return

        values = self.page.challenges_tree.item(selected[0], "values")
        challenge_name = values[0]

        # Find the challenge object
        challenges = self._challenge_mode.get_available_challenges()
        challenge = None
        for ch in challenges:
            if ch.name == challenge_name:
                challenge = ch
                break

        if challenge is None:
            messagebox.showerror("Challenges", "Challenge not found.")
            return

        result = messagebox.askyesno(
            "Start Challenge",
            f"Start challenge: {challenge.name}?\n\n"
            f"{challenge.description}\n"
            f"Difficulty: {challenge.difficulty}",
        )
        if result:
            # Navigate to new game page where the challenge conditions can be applied
            messagebox.showinfo(
                "Challenge Started",
                f"Challenge '{challenge.name}' selected.\n"
                "Proceed with New Game setup to apply challenge conditions.",
            )
            self.switch("new_game")

    def _hotseat(self):
        """Set up hot-seat multiplayer."""
        p1 = self.page.p1_entry.get().strip()
        p2 = self.page.p2_entry.get().strip()

        if not p1 or not p2:
            self.page.mp_status_label.config(text="Please enter both player names.")
            return

        if p1 == p2:
            self.page.mp_status_label.config(text="Player names must be different.")
            return

        self.page.mp_status_label.config(
            text=f"Hot Seat mode: {p1} vs {p2}. Starting new game..."
        )

        # Navigate to new game to set up hot-seat
        messagebox.showinfo(
            "Hot Seat",
            f"Hot-seat multiplayer with {p1} and {p2}.\n"
            "Proceed to New Game to select clubs for each player.",
        )
        self.switch("new_game")

    def _load_mod(self):
        """Load the selected mod."""
        selected = self.page.mods_tree.selection()
        if not selected:
            messagebox.showinfo("Mods", "Please select a mod to load.")
            return

        idx = self.page.mods_tree.index(selected[0])
        if idx >= len(self._discovered_mods):
            self.page.mod_status_label.config(text="Invalid selection.")
            return

        mod_info = self._discovered_mods[idx]

        try:
            mod_data = self._mod_loader.load_mod(mod_info)

            # Validate
            valid, reason = ModLoader.validate_mod(mod_data)
            if not valid:
                self.page.mod_status_label.config(text=f"Invalid mod: {reason}")
                return

            # Apply based on type
            if mod_info.mod_type.value == "database":
                self._mod_loader.apply_database_mod(mod_data, self.controller.db)
                self.page.mod_status_label.config(
                    text=f"Database mod '{mod_info.name}' applied successfully."
                )
            elif mod_info.mod_type.value == "roster":
                self._mod_loader.apply_roster_mod(mod_data)
                self.page.mod_status_label.config(
                    text=f"Roster mod '{mod_info.name}' applied successfully."
                )
            else:
                self.page.mod_status_label.config(
                    text=f"Mod '{mod_info.name}' loaded ({mod_info.mod_type.value} type)."
                )

        except Exception as e:
            self.page.mod_status_label.config(text=f"Error loading mod: {e}")

    def _export_db(self):
        """Export database to JSON file."""
        file_path = filedialog.asksaveasfilename(
            title="Export Database",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            # Gather data from the database
            clubs = self.controller.db.load_clubs()
            players = self.controller.db.load_players()

            data = {
                "clubs": clubs,
                "players": players,
            }

            DatabaseImportExport.export_to_json(data, Path(file_path))
            self.page.mod_status_label.config(text=f"Database exported to {file_path}")
        except Exception as e:
            self.page.mod_status_label.config(text=f"Export failed: {e}")

    def _import_db(self):
        """Import database from JSON file."""
        file_path = filedialog.askopenfilename(
            title="Import Database",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return

        result = messagebox.askyesno(
            "Import Database",
            "This will overwrite existing database data.\nAre you sure?",
        )
        if not result:
            return

        try:
            import json
            with open(file_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)

            # The imported data should have "clubs" and "players" keys
            if "clubs" in data or "players" in data:
                # Apply as a database mod
                mod_data = {"data": data}
                self._mod_loader.apply_database_mod(mod_data, self.controller.db)
                self.page.mod_status_label.config(text=f"Database imported from {file_path}")
            else:
                self.page.mod_status_label.config(text="Invalid database format.")
        except Exception as e:
            self.page.mod_status_label.config(text=f"Import failed: {e}")

    def _go_back(self):
        self.switch(self.controller.get_back_page())

    def _bind(self):
        self.page.back_btn.config(command=self._go_back)
        self.page.start_challenge_btn.config(command=self._start_challenge)
        self.page.hotseat_btn.config(command=self._hotseat)
        self.page.load_mod_btn.config(command=self._load_mod)
        self.page.export_btn.config(command=self._export_db)
        self.page.import_btn.config(command=self._import_db)
