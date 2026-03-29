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
from uuid import UUID

from ..pages.competitions import CompetitionsPage
from .controllerinterface import ControllerInterface
from ...core.football.competitions import (
    CupCompetition,
    DivisionSystem,
    ContinentalCompetition,
    InternationalCompetition,
)


class CompetitionsController(ControllerInterface):
    def __init__(self, controller: ControllerInterface, page: CompetitionsPage):
        self.controller = controller
        self.page = page

        # Competition instances (created during initialize)
        self.cup: CupCompetition | None = None
        self.division_system: DivisionSystem | None = None
        self.continental: ContinentalCompetition | None = None
        self.international: InternationalCompetition | None = None

        # Lookup: UUID -> club name
        self._club_names: dict[UUID, str] = {}

        self._bind()

    def switch(self, page: str):
        self.controller.switch(page)

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self):
        career = getattr(self.controller, "career_engine", None)

        if career is not None:
            clubs = self._clubs_from_career(career)
        else:
            clubs = self._clubs_from_db()

        if not clubs:
            self.page.status_label.config(text="No clubs available.")
            return

        # Build name lookup
        self._club_names = {c["uuid"]: c["name"] for c in clubs}
        club_ids = list(self._club_names.keys())

        # --- Domestic Cup ---
        self.cup = CupCompetition("Domestic Cup", club_ids)
        self.cup.draw_round()
        self._refresh_cup_tree()

        # --- Division System (2 divisions, split clubs in half) ---
        half = max(len(club_ids) // 2, 1)
        divisions = {1: club_ids[:half], 2: club_ids[half:]}
        self.division_system = DivisionSystem(divisions)
        self._refresh_division_tree()

        # --- Continental Competition (top 8 clubs, needs 8 for 2 groups of 4) ---
        if len(club_ids) >= 8:
            top8 = club_ids[:8]
            self.continental = ContinentalCompetition(
                "Continental Cup",
                top8,
                group_count=2,
                teams_per_group=4,
                knockout_two_legs=False,
            )
            self.continental.draw_groups()
            self._refresh_continental_tree()
        else:
            self.continental = None
            self._clear_tree(self.page.continental_tree)
            self._clear_tree(self.page.knockout_tree)

        # --- International Competition (unique nationalities from players) ---
        nations = self._collect_nations(career)
        if len(nations) >= 8:
            # Need a multiple of 4 for group geometry
            usable = (len(nations) // 4) * 4
            nations = nations[:usable]
            self.international = InternationalCompetition(
                "International Cup", nations
            )
        elif len(nations) >= 2:
            self.international = InternationalCompetition(
                "International Cup", nations
            )
        else:
            self.international = None
        self._refresh_international_tree()

        self.page.status_label.config(text="Competitions initialized.")

    # ------------------------------------------------------------------
    # Data loaders
    # ------------------------------------------------------------------

    def _clubs_from_career(self, career) -> list[dict]:
        """Extract club dicts from the career engine."""
        clubs = []
        if hasattr(career, "clubs") and career.clubs:
            for club in career.clubs:
                if hasattr(club, "club_id") and hasattr(club, "name"):
                    clubs.append({"uuid": club.club_id, "name": club.name})
        # Fallback: use league entries
        if not clubs and hasattr(career, "league") and career.league:
            league = career.league
            if hasattr(league, "table") and league.table:
                for entry in league.table:
                    if hasattr(entry, "club"):
                        c = entry.club
                        clubs.append({"uuid": c.club_id, "name": c.name})
        return clubs

    def _clubs_from_db(self) -> list[dict]:
        """Load clubs from the database (debug mode)."""
        try:
            self.controller.db.check_clubs_file(amount=50)
            raw = self.controller.db.load_clubs()
            clubs = []
            for c in raw:
                uid = UUID(int=c["id"]) if isinstance(c["id"], int) else UUID(c["id"])
                clubs.append({"uuid": uid, "name": c["name"]})
            return clubs
        except Exception:
            return []

    def _collect_nations(self, career) -> list[str]:
        """Gather unique nationality strings for the international tournament."""
        nations_set: set[str] = set()
        try:
            if career is not None:
                if hasattr(career, "players") and career.players:
                    for p in career.players:
                        nat = getattr(p, "nationality", None)
                        if nat:
                            nations_set.add(str(nat))
            else:
                raw_players = self.controller.db.load_players()
                for p in raw_players:
                    nat = p.get("nationality", "")
                    if nat:
                        nations_set.add(str(nat))
        except Exception:
            pass

        if not nations_set:
            # Provide sensible defaults so the tab is not empty
            nations_set = {
                "Brazil", "Germany", "France", "Argentina",
                "Spain", "Italy", "England", "Netherlands",
            }
        return sorted(nations_set)

    # ------------------------------------------------------------------
    # Name helper
    # ------------------------------------------------------------------

    def _name(self, team_id: UUID) -> str:
        return self._club_names.get(team_id, str(team_id)[:8])

    # ------------------------------------------------------------------
    # Cup
    # ------------------------------------------------------------------

    def _sim_cup_round(self):
        if self.cup is None:
            return
        if self.cup.is_finished:
            champ = self.cup.get_champion()
            self.page.status_label.config(
                text=f"Cup finished! Champion: {self._name(champ)}"
            )
            return
        self.cup.simulate_round()
        self._refresh_cup_tree()
        self.cup.advance_round()
        if not self.cup.is_finished:
            self.cup.draw_round()
            self._refresh_cup_tree()
            self.page.status_label.config(
                text=f"Cup round {self.cup.current_round} drawn."
            )
        else:
            champ = self.cup.get_champion()
            self._refresh_cup_tree()
            self.page.status_label.config(
                text=f"Cup finished! Champion: {self._name(champ)}"
            )

    def _refresh_cup_tree(self):
        tree = self.page.cup_tree
        self._clear_tree(tree)
        if self.cup is None:
            return
        for r_idx, rnd in enumerate(self.cup.rounds):
            round_label = self._round_label(r_idx)
            for match in rnd:
                home = self._name(match["home"])
                away = self._name(match["away"])
                if match["played"]:
                    score = f"{match['home_goals']} - {match['away_goals']}"
                    extra = ""
                    if match.get("penalties"):
                        extra = " (pen)"
                    elif match.get("extra_time"):
                        extra = " (aet)"
                    score += extra
                else:
                    score = "vs"
                tree.insert("", "end", values=(round_label, home, score, away))

    def _round_label(self, r_idx: int) -> str:
        labels = {0: "R1", 1: "R2", 2: "QF", 3: "SF", 4: "Final"}
        return labels.get(r_idx, f"R{r_idx + 1}")

    # ------------------------------------------------------------------
    # Continental
    # ------------------------------------------------------------------

    def _sim_continental(self):
        if self.continental is None:
            return
        if self.continental.phase == "group":
            self.continental.simulate_group_stage()
            self._refresh_continental_tree()
            self.continental.advance_to_knockout()
            self._refresh_knockout_tree()
            self.page.sim_continental_btn.config(text="Simulate Knockout")
            self.page.status_label.config(text="Group stage complete. Knockout drawn.")
        elif self.continental.phase == "knockout":
            ko = self.continental.knockout_stage
            if ko is None:
                return
            if ko.is_finished:
                champ = ko.get_champion()
                self.page.status_label.config(
                    text=f"Continental champion: {self._name(champ)}"
                )
                return
            ko.simulate_round()
            ko.advance_round()
            if not ko.is_finished:
                ko.draw_round()
            self._refresh_knockout_tree()
            if ko.is_finished:
                champ = ko.get_champion()
                self.page.status_label.config(
                    text=f"Continental champion: {self._name(champ)}"
                )
            else:
                self.page.status_label.config(
                    text=f"Knockout round {ko.current_round} complete."
                )

    def _refresh_continental_tree(self):
        tree = self.page.continental_tree
        self._clear_tree(tree)
        if self.continental is None:
            return
        standings = self.continental.get_group_standings()
        for label in sorted(standings.keys()):
            for team_id, info in standings[label]:
                tree.insert("", "end", values=(
                    label,
                    self._name(team_id),
                    info["played"],
                    info["won"],
                    info["drawn"],
                    info["lost"],
                    info["points"],
                ))

    def _refresh_knockout_tree(self):
        tree = self.page.knockout_tree
        self._clear_tree(tree)
        ko = self.continental.knockout_stage if self.continental else None
        if ko is None:
            return
        for r_idx, rnd in enumerate(ko.rounds):
            round_label = self._round_label(r_idx)
            for match in rnd:
                home = self._name(match["home"])
                away = self._name(match["away"])
                if match["played"]:
                    score = f"{match['home_goals']} - {match['away_goals']}"
                else:
                    score = "vs"
                tree.insert("", "end", values=(round_label, home, score, away))

    # ------------------------------------------------------------------
    # Divisions
    # ------------------------------------------------------------------

    def _refresh_division_tree(self):
        tree = self.page.division_tree
        self._clear_tree(tree)
        if self.division_system is None:
            return
        for tier in sorted(self.division_system.divisions.keys()):
            teams = self.division_system.divisions[tier]
            for pos, tid in enumerate(teams, 1):
                tree.insert("", "end", values=(
                    tier, pos, self._name(tid), 0, 0, 0, 0, 0
                ))

        # Promotion / relegation info
        promo_parts = []
        for tier, promoted in self.division_system._promotions.items():
            for tid in promoted:
                promo_parts.append(f"{self._name(tid)} (promoted from Div {tier})")
        for tier, relegated in self.division_system._relegations.items():
            for tid in relegated:
                promo_parts.append(f"{self._name(tid)} (relegated from Div {tier})")

        if promo_parts:
            self.page.promo_label.config(text=" | ".join(promo_parts))
        else:
            self.page.promo_label.config(text="Promoted / Relegated: --")

    # ------------------------------------------------------------------
    # International
    # ------------------------------------------------------------------

    def _sim_international(self):
        if self.international is None:
            self.page.status_label.config(text="No international competition.")
            return
        winner = self.international.simulate_tournament()
        self._refresh_international_tree()
        self.page.status_label.config(text=f"International champion: {winner}")

    def _refresh_international_tree(self):
        tree = self.page.international_tree
        self._clear_tree(tree)
        if self.international is None:
            return

        # Show group stage results if available
        if self.international.group_stage:
            standings = self.international.group_stage.get_group_standings()
            for label in sorted(standings.keys()):
                for team_id, info in standings[label]:
                    nation = self.international._id_to_nation.get(team_id, "?")
                    tree.insert("", "end", values=(
                        f"Group {label}",
                        nation,
                        f"Pts: {info['points']}",
                        f"GD: {info['gf']}-{info['ga']}",
                    ))

        # Show knockout results if available
        ko = self.international.knockout_stage
        if ko:
            for r_idx, rnd in enumerate(ko.rounds):
                round_label = self._round_label(r_idx)
                for match in rnd:
                    home_n = self.international._id_to_nation.get(match["home"], "?")
                    away_n = self.international._id_to_nation.get(match["away"], "?")
                    if match["played"]:
                        score = f"{match['home_goals']} - {match['away_goals']}"
                    else:
                        score = "vs"
                    tree.insert("", "end", values=(
                        f"KO {round_label}", home_n, score, away_n
                    ))

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _clear_tree(tree):
        for item in tree.get_children():
            tree.delete(item)

    def _go_back(self):
        self.switch(self.controller.get_back_page())

    # ------------------------------------------------------------------
    # Binding
    # ------------------------------------------------------------------

    def _bind(self):
        self.page.sim_cup_btn.config(command=self._sim_cup_round)
        self.page.sim_continental_btn.config(command=self._sim_continental)
        self.page.sim_intl_btn.config(command=self._sim_international)
        self.page.cancel_btn.config(command=self._go_back)
