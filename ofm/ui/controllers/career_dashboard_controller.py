#      Openfoot Manager - A free and open source soccer management simulation
#      Copyright (C) 2020-2025  Pedrenrique G. Guimarães
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
from ..pages.career_dashboard import CareerDashboardPage
from .controllerinterface import ControllerInterface
from ...core.game_state import SaveManager


class CareerDashboardController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: CareerDashboardPage):
        self.controller = controller
        self.page = page
        self._bind()

    def switch(self, page):
        self.controller.switch(page)

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self):
        career = getattr(self.controller, "career_engine", None)
        if career is None:
            self._set_news("No active career. Please start or load a game.")
            return

        # -- Top bar --
        manager_name = "--"
        if career.manager is not None:
            manager_name = f"{career.manager.first_name} {career.manager.last_name}"
        self.page.manager_label.config(text=f"Manager: {manager_name}")

        club_info = career.get_player_club()
        club_name = club_info["name"] if club_info else "--"
        balance = club_info["balance"] if club_info else 0.0
        self.page.club_label.config(text=club_name)
        self.page.date_label.config(
            text=f"Season {career.season_number}  |  {career.current_date.isoformat()}"
        )
        self.page.balance_label.config(text=f"Balance: {balance:,.0f}")

        # -- Standings --
        self._populate_standings(career)

        # -- Upcoming fixtures --
        self._populate_fixtures(career)

        # -- Recent results --
        self._populate_results(career)

        # -- News feed --
        self._populate_news(career)

        # -- Play match button state --
        self._update_play_match_state(career)

    # ------------------------------------------------------------------
    # Widget population helpers
    # ------------------------------------------------------------------

    def _populate_standings(self, career):
        tree = self.page.standings_tree
        for item in tree.get_children():
            tree.delete(item)
        standings = career.get_standings()
        for entry in standings:
            tree.insert(
                "",
                "end",
                values=(
                    entry["position"],
                    entry["club"],
                    entry["played"],
                    entry["won"],
                    entry["drawn"],
                    entry["lost"],
                    entry["points"],
                ),
            )

    def _populate_fixtures(self, career):
        tree = self.page.fixtures_tree
        for item in tree.get_children():
            tree.delete(item)
        fixtures = career.get_upcoming_fixtures(3)
        for fix in fixtures:
            tree.insert("", "end", values=(fix["date"], fix["home"], fix["away"]))

    def _populate_results(self, career):
        tree = self.page.results_tree
        for item in tree.get_children():
            tree.delete(item)
        results = career.get_recent_results(3)
        for res in results:
            score = f"{res['home_goals']} - {res['away_goals']}"
            tree.insert("", "end", values=("", res["home"], score, res["away"]))

    def _populate_news(self, career):
        items = career.news_feed[-10:]
        lines = []
        for item in reversed(items):
            headline = item.get("headline", "")
            body = item.get("body", "")
            date = item.get("date", "")
            lines.append(f"[{date}] {headline}")
            if body:
                lines.append(f"  {body}")
            lines.append("")
        self._set_news("\n".join(lines) if lines else "No news yet.")

    def _set_news(self, text: str):
        self.page.news_text.config(state="normal")
        self.page.news_text.delete("1.0", "end")
        self.page.news_text.insert("1.0", text)
        self.page.news_text.config(state="disabled")

    def _update_play_match_state(self, career):
        """Enable the Play Next Match button only if today has a match."""
        if career.calendar is None:
            self.page.play_match_btn.config(state="disabled")
            return
        events = career.calendar.get_events_for_date(career.current_date)
        has_match = any(e.event_type == "match" for e in events)
        self.page.play_match_btn.config(state="normal" if has_match else "disabled")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _advance_day(self):
        career = getattr(self.controller, "career_engine", None)
        if career is None:
            return
        summary = career.advance_day()

        # Refresh all widgets
        self.initialize()

        # Extra status info
        date_str = summary.get("date", "")
        match_ready = summary.get("match_ready")
        if match_ready:
            self.controller.gui.update_status(
                f"Day advanced to {date_str} - Match day!"
            )
        else:
            self.controller.gui.update_status(f"Day advanced to {date_str}")

    def _play_match(self):
        career = getattr(self.controller, "career_engine", None)
        if career is None:
            return

        # Find today's match event for the player's club
        if career.calendar is None or career.player_club_id is None:
            return

        events = career.calendar.get_events_for_date(career.current_date)
        match_event = None
        for event in events:
            if event.event_type == "match":
                match_event = event
                break

        if match_event is None:
            self.controller.gui.update_status("No match scheduled for today.")
            return

        # Find the player's fixture in this round
        from uuid import UUID

        pid = str(career.player_club_id)
        player_fixture = None
        for fix in match_event.data.get("fixtures", []):
            if fix["home"] == pid or fix["away"] == pid:
                player_fixture = fix
                break

        if player_fixture is None:
            self.controller.gui.update_status("No fixture found for your club today.")
            return

        # Simulate the match via CareerEngine
        home_id = UUID(player_fixture["home"])
        away_id = UUID(player_fixture["away"])
        result = career.play_match(home_id, away_id)

        # Record the result in league table and season history
        round_idx = match_event.data.get("round")
        result["round"] = round_idx
        career.complete_player_match(result)

        # Refresh the dashboard
        self.initialize()

        score_line = (
            f"{result['home_club']} {result['home_goals']} - "
            f"{result['away_goals']} {result['away_club']}"
        )
        self.controller.gui.update_status(f"Match result: {score_line}")

    def _save_game(self):
        career = getattr(self.controller, "career_engine", None)
        if career is None:
            self.controller.gui.update_status("No active career to save.")
            return

        try:
            save_manager = SaveManager(self.controller.settings)
            # Build a GameState from career engine state
            from ...core.game_state import GameState

            club_info = career.get_player_club()
            state = GameState(
                manager_name=(
                    f"{career.manager.first_name} {career.manager.last_name}"
                    if career.manager
                    else "Unknown"
                ),
                club_id=club_info["club_id"] if club_info else 0,
                season=career.season_number,
                current_date=career.current_date,
                league_data={"name": career.league.name if career.league else ""},
                clubs_data=[],
                players_data=[],
                squads_data=[],
                finances_data={"balance": club_info["balance"]} if club_info else {},
                career_data={
                    "news_feed": career.news_feed[-50:],
                },
            )
            save_manager.save_game(state, "career_save")
            self.controller.gui.update_status("Game saved successfully.")
        except Exception as e:
            self.controller.gui.update_status(f"Save failed: {e}")

    def _go_to_training(self):
        self.switch("training")

    def _go_to_transfers(self):
        self.switch("market")

    def _go_to_formation(self):
        self.switch("team_formation")

    def _go_to_youth(self):
        self.switch("debug_home")

    def _go_to_main_menu(self):
        self.switch("home")

    # ------------------------------------------------------------------
    # Binding
    # ------------------------------------------------------------------

    def _bind(self):
        self.page.advance_btn.config(command=self._advance_day)
        self.page.play_match_btn.config(command=self._play_match)
        self.page.training_btn.config(command=self._go_to_training)
        self.page.transfers_btn.config(command=self._go_to_transfers)
        self.page.youth_btn.config(command=self._go_to_youth)
        self.page.formation_btn.config(command=self._go_to_formation)
        self.page.save_btn.config(command=self._save_game)
        self.page.back_btn.config(command=self._go_to_main_menu)
