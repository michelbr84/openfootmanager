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
import datetime
import random
import uuid
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from .football.league import League, Season
from .football.training import TrainingManager, TrainingFocus
from .football.transfer_market import (
    TransferMarket,
    TransferListing,
    calculate_market_value,
    TransferWindow,
)
from .football.youth import YouthAcademy
from .football.loans import LoanManager
from .football.injury import InjuryManager, PlayerInjury
from .football.career import CareerManager
from .football.manager import Manager
from .football.finances import FinanceManager, SeasonBudget
from .football.interactions import InteractionManager
from .football.formation import Formation, FORMATION_STRINGS
from .football.club import Club
from .football.player import PlayerTeam, Positions
from .settings import Settings
from .db.database import DB


# ---------------------------------------------------------------------------
# CalendarEvent
# ---------------------------------------------------------------------------

@dataclass
class CalendarEvent:
    """A single event on the season calendar."""

    date: datetime.date
    event_type: str  # "match", "training", "transfer_window_open",
    #                   "transfer_window_close", "season_end", "youth_intake"
    description: str
    data: dict = field(default_factory=dict)

    def serialize(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "event_type": self.event_type,
            "description": self.description,
            "data": self.data,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "CalendarEvent":
        return cls(
            date=datetime.date.fromisoformat(data["date"]),
            event_type=data["event_type"],
            description=data["description"],
            data=data.get("data", {}),
        )


# ---------------------------------------------------------------------------
# SeasonCalendar
# ---------------------------------------------------------------------------

class SeasonCalendar:
    """Generates and manages all calendar events for a single season.

    The season runs from August 1 to May 31.  Match rounds are assigned to
    Saturdays, training days are Monday-Friday, transfer windows cover
    January 1-31 and July 1 - August 31, youth intake is March 1, and the
    season formally ends on May 31.
    """

    def __init__(self, season_year: int, league: League):
        self.season_year = season_year
        self.league = league
        self.events: list[CalendarEvent] = []

    # -- generation ---------------------------------------------------------

    def generate_calendar(self) -> None:
        """Populate *self.events* with every event in the season."""
        self.events.clear()

        start_date = datetime.date(self.season_year, 8, 1)
        end_date = datetime.date(self.season_year + 1, 5, 31)

        # --- collect all Saturday match slots --------------------------------
        saturdays: list[datetime.date] = []
        current = start_date
        while current <= end_date:
            if current.weekday() == 5:  # Saturday
                saturdays.append(current)
            current += datetime.timedelta(days=1)

        # --- assign league rounds to Saturdays -------------------------------
        season = Season(self.league)
        season.setup_season()
        total_rounds = len(season.rounds)

        # Spread rounds evenly across available Saturdays
        if total_rounds > 0 and saturdays:
            step = max(1, len(saturdays) // total_rounds)
            for round_idx in range(total_rounds):
                sat_idx = min(round_idx * step, len(saturdays) - 1)
                match_date = saturdays[sat_idx]
                fixtures = season.rounds[round_idx]
                self.events.append(
                    CalendarEvent(
                        date=match_date,
                        event_type="match",
                        description=f"Match day - Round {round_idx + 1}",
                        data={
                            "round": round_idx,
                            "fixtures": [
                                {"home": str(h), "away": str(a)}
                                for h, a in fixtures
                            ],
                        },
                    )
                )

        # --- training days (Mon-Fri, excluding match-day Saturdays) ----------
        current = start_date
        match_dates = {e.date for e in self.events if e.event_type == "match"}
        while current <= end_date:
            weekday = current.weekday()
            if weekday < 5 and current not in match_dates:  # Mon-Fri
                self.events.append(
                    CalendarEvent(
                        date=current,
                        event_type="training",
                        description="Training day",
                    )
                )
            current += datetime.timedelta(days=1)

        # --- transfer windows ------------------------------------------------
        # Summer window: Jul 1 - Aug 31 of the starting year
        self.events.append(
            CalendarEvent(
                date=datetime.date(self.season_year, 7, 1),
                event_type="transfer_window_open",
                description="Summer transfer window opens",
                data={"window": "summer"},
            )
        )
        self.events.append(
            CalendarEvent(
                date=datetime.date(self.season_year, 8, 31),
                event_type="transfer_window_close",
                description="Summer transfer window closes",
                data={"window": "summer"},
            )
        )
        # Winter window: Jan 1 - Jan 31 of the following year
        self.events.append(
            CalendarEvent(
                date=datetime.date(self.season_year + 1, 1, 1),
                event_type="transfer_window_open",
                description="Winter transfer window opens",
                data={"window": "winter"},
            )
        )
        self.events.append(
            CalendarEvent(
                date=datetime.date(self.season_year + 1, 1, 31),
                event_type="transfer_window_close",
                description="Winter transfer window closes",
                data={"window": "winter"},
            )
        )

        # --- youth intake ----------------------------------------------------
        self.events.append(
            CalendarEvent(
                date=datetime.date(self.season_year + 1, 3, 1),
                event_type="youth_intake",
                description="Annual youth intake day",
            )
        )

        # --- season end ------------------------------------------------------
        self.events.append(
            CalendarEvent(
                date=end_date,
                event_type="season_end",
                description="End of season",
            )
        )

        # sort chronologically
        self.events.sort(key=lambda e: e.date)

    # -- queries ------------------------------------------------------------

    def get_events_for_date(self, date: datetime.date) -> list[CalendarEvent]:
        """Return every event scheduled for *date*."""
        return [e for e in self.events if e.date == date]

    def get_next_match_date(self, from_date: datetime.date) -> Optional[datetime.date]:
        """Return the date of the next match strictly after *from_date*, or None."""
        for e in self.events:
            if e.event_type == "match" and e.date > from_date:
                return e.date
        return None

    # -- serialization ------------------------------------------------------

    def serialize(self) -> dict:
        return {
            "season_year": self.season_year,
            "events": [e.serialize() for e in self.events],
        }

    @classmethod
    def get_from_dict(cls, data: dict, league: League) -> "SeasonCalendar":
        cal = cls(season_year=data["season_year"], league=league)
        cal.events = [CalendarEvent.get_from_dict(e) for e in data.get("events", [])]
        return cal


# ---------------------------------------------------------------------------
# AIManager
# ---------------------------------------------------------------------------

class AIManager:
    """Controls all automated decisions for a single AI-managed club."""

    def __init__(self, club_id: UUID):
        self.club_id = club_id
        self.preferred_formation: str = random.choice(FORMATION_STRINGS)
        self.training_focus: TrainingFocus = TrainingFocus.GENERAL

    # -- transfers ----------------------------------------------------------

    def make_transfer_decisions(
        self,
        club: Club,
        market: TransferMarket,
        current_date: datetime.date,
    ) -> list[dict]:
        """Decide whether to buy or sell players.

        Returns a list of action dicts for logging / news purposes:
            {"action": "buy"/"sell", "player_name": ..., "fee": ...}
        """
        actions: list[dict] = []
        squad = club.squad
        squad_size = len(squad)

        # --- buy if squad too small ---
        if squad_size < 18 and market.window == TransferWindow.OPEN:
            weak_positions = self._find_weak_positions(squad)
            listings = market.get_available_players()
            for listing in listings:
                if listing.selling_club_id == club.club_id:
                    continue
                if club.finances.balance < listing.asking_price:
                    continue
                # Buy cheapest
                offer = market.make_offer(
                    listing.player_id, club.club_id, listing.asking_price
                )
                if offer.status.value == "accepted":
                    actions.append(
                        {
                            "action": "buy",
                            "player_id": str(listing.player_id),
                            "fee": listing.asking_price,
                        }
                    )
                break  # one transfer per day

        # --- sell if squad too large ---
        if squad_size > 25 and market.window == TransferWindow.OPEN:
            # Find lowest-rated bench-type player
            rated = sorted(
                squad,
                key=lambda p: p.details.attributes.get_overall(
                    p.details.get_best_position()
                ),
            )
            if rated:
                weakest = rated[0]
                value = calculate_market_value(
                    {
                        "dob": weakest.details.dob,
                        "overall": weakest.details.attributes.get_overall(
                            weakest.details.get_best_position()
                        ),
                        "potential_skill": weakest.details.potential_skill,
                        "international_reputation": weakest.details.international_reputation,
                    }
                )
                try:
                    market.list_player(
                        weakest.details.player_id,
                        club.club_id,
                        value,
                        current_date,
                    )
                    actions.append(
                        {
                            "action": "sell_listed",
                            "player_name": weakest.details.short_name,
                            "asking_price": value,
                        }
                    )
                except ValueError:
                    pass  # already listed

        # --- random bid on high-rated player (10% chance) ---
        if random.random() < 0.10 and market.window == TransferWindow.OPEN:
            listings = market.get_available_players()
            affordable = [
                l
                for l in listings
                if l.selling_club_id != club.club_id
                and l.asking_price <= club.finances.balance * 0.5
            ]
            if affordable:
                target = random.choice(affordable)
                offer = market.make_offer(
                    target.player_id, club.club_id, target.asking_price
                )
                if offer.status.value == "accepted":
                    actions.append(
                        {
                            "action": "buy",
                            "player_id": str(target.player_id),
                            "fee": target.asking_price,
                        }
                    )

        return actions

    # -- formation ----------------------------------------------------------

    def set_formation(self, club: Club) -> str:
        """Pick a formation based on squad composition."""
        squad = club.squad
        gk_count = sum(
            1 for p in squad if p.details.get_best_position() == Positions.GK
        )
        df_count = sum(
            1 for p in squad if p.details.get_best_position() == Positions.DF
        )
        mf_count = sum(
            1 for p in squad if p.details.get_best_position() == Positions.MF
        )
        fw_count = sum(
            1 for p in squad if p.details.get_best_position() == Positions.FW
        )

        if df_count >= 6 and fw_count <= 2:
            self.preferred_formation = "5-3-2"
        elif mf_count >= 7:
            self.preferred_formation = "4-5-1"
        elif fw_count >= 5:
            self.preferred_formation = "4-3-3"
        elif df_count >= 5:
            self.preferred_formation = "5-4-1"
        else:
            self.preferred_formation = "4-4-2"

        return self.preferred_formation

    # -- training -----------------------------------------------------------

    def set_training_focus(self, club: Club) -> TrainingFocus:
        """Choose training focus based on squad weaknesses."""
        squad = club.squad
        if not squad:
            self.training_focus = TrainingFocus.GENERAL
            return self.training_focus

        avg_off = 0.0
        avg_def = 0.0
        avg_fit = 0.0
        count = len(squad)

        for p in squad:
            attrs = p.details.attributes
            avg_off += (
                attrs.offensive.shot_power + attrs.offensive.shot_accuracy
            ) / 2
            avg_def += (
                attrs.defensive.tackling + attrs.defensive.interception
            ) / 2
            avg_fit += p.details.fitness

        avg_off /= count
        avg_def /= count
        avg_fit /= count

        if avg_fit < 60:
            self.training_focus = TrainingFocus.FITNESS
        elif avg_def < avg_off - 10:
            self.training_focus = TrainingFocus.DEFENSE
        elif avg_off < avg_def - 10:
            self.training_focus = TrainingFocus.ATTACK
        else:
            self.training_focus = TrainingFocus.GENERAL

        return self.training_focus

    # -- squad rotation -----------------------------------------------------

    def rotate_squad(
        self,
        club: Club,
        injury_manager: InjuryManager,
        match_importance: float = 1.0,
    ) -> None:
        """Rest tired or injured players for less important matches.

        For important matches (*match_importance* >= 0.8) no rotation occurs
        unless a player is injured.  For friendlier fixtures the AI rests
        players whose fitness is below 60.
        """
        for player in club.squad:
            if injury_manager.is_player_injured(player.details.player_id):
                player.details.fitness = max(player.details.fitness, 0)
                continue
            if match_importance < 0.8 and player.details.fitness < 60:
                # "rest" by boosting fitness slightly (simulating bench rest)
                player.details.fitness = min(player.details.fitness + 5, 100.0)

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _find_weak_positions(squad: list[PlayerTeam]) -> list[Positions]:
        """Return positions where the club has fewer than 2 players."""
        counts: dict[Positions, int] = {
            Positions.GK: 0,
            Positions.DF: 0,
            Positions.MF: 0,
            Positions.FW: 0,
        }
        for p in squad:
            pos = p.details.get_best_position()
            if pos in counts:
                counts[pos] += 1
        return [pos for pos, c in counts.items() if c < 2]

    # -- serialization ------------------------------------------------------

    def serialize(self) -> dict:
        return {
            "club_id": str(self.club_id),
            "preferred_formation": self.preferred_formation,
            "training_focus": self.training_focus.value,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "AIManager":
        mgr = cls(club_id=UUID(data["club_id"]))
        mgr.preferred_formation = data.get(
            "preferred_formation", random.choice(FORMATION_STRINGS)
        )
        mgr.training_focus = TrainingFocus(
            data.get("training_focus", TrainingFocus.GENERAL.value)
        )
        return mgr


# ---------------------------------------------------------------------------
# generate_season_awards  (module-level helper)
# ---------------------------------------------------------------------------

def generate_season_awards(
    league: League,
    clubs: list[Club],
) -> list[dict]:
    """Generate end-of-season awards from league standings and player data.

    Awards:
        - League Champion
        - Golden Boot (most goals -- approximated via offensive attributes)
        - Best Player (highest overall in the league)
        - Best Young Player (highest overall among players < 23)
        - Best Goalkeeper (highest GK overall)

    Returns a list of award dicts: {"award", "player_name"/"club_name", ...}
    """
    awards: list[dict] = []

    # --- League Champion ---
    standings = league.get_standings()
    if standings:
        champion = standings[0]
        awards.append(
            {
                "award": "League Champion",
                "club_name": champion.club.name,
                "points": champion.points,
            }
        )

    # Collect every player across all clubs
    all_players: list[tuple[PlayerTeam, Club]] = []
    for club in clubs:
        for player in club.squad:
            all_players.append((player, club))

    if not all_players:
        return awards

    today = datetime.date.today()

    def _age(p: PlayerTeam) -> int:
        dob = p.details.dob
        age = today.year - dob.year
        if (today.month, today.day) < (dob.month, dob.day):
            age -= 1
        return age

    def _overall(p: PlayerTeam) -> int:
        return p.details.attributes.get_overall(p.details.get_best_position())

    # --- Golden Boot (proxy: offensive rating for FW/MF) ---
    strikers = [
        (p, c)
        for p, c in all_players
        if p.details.get_best_position() in (Positions.FW, Positions.MF)
    ]
    if strikers:
        best_scorer = max(
            strikers,
            key=lambda pc: (
                pc[0].details.attributes.offensive.shot_power
                + pc[0].details.attributes.offensive.shot_accuracy
                + pc[0].details.attributes.offensive.positioning
            ),
        )
        awards.append(
            {
                "award": "Golden Boot",
                "player_name": best_scorer[0].details.short_name,
                "club_name": best_scorer[1].name,
            }
        )

    # --- Best Player ---
    best_player = max(all_players, key=lambda pc: _overall(pc[0]))
    awards.append(
        {
            "award": "Best Player",
            "player_name": best_player[0].details.short_name,
            "club_name": best_player[1].name,
            "overall": _overall(best_player[0]),
        }
    )

    # --- Best Young Player (age < 23) ---
    young_players = [(p, c) for p, c in all_players if _age(p) < 23]
    if young_players:
        best_young = max(young_players, key=lambda pc: _overall(pc[0]))
        awards.append(
            {
                "award": "Best Young Player",
                "player_name": best_young[0].details.short_name,
                "club_name": best_young[1].name,
                "overall": _overall(best_young[0]),
                "age": _age(best_young[0]),
            }
        )

    # --- Best Goalkeeper ---
    goalkeepers = [
        (p, c)
        for p, c in all_players
        if p.details.get_best_position() == Positions.GK
    ]
    if goalkeepers:
        best_gk = max(
            goalkeepers,
            key=lambda pc: pc[0].details.attributes.get_overall(Positions.GK),
        )
        awards.append(
            {
                "award": "Best Goalkeeper",
                "player_name": best_gk[0].details.short_name,
                "club_name": best_gk[1].name,
            }
        )

    return awards


# ---------------------------------------------------------------------------
# CareerEngine
# ---------------------------------------------------------------------------

class CareerEngine:
    """Central orchestrator for a full career-mode game.

    Ties together League, Season, TrainingManager, TransferMarket,
    YouthAcademy, LoanManager, InjuryManager, CareerManager,
    FinanceManager, InteractionManager and AIManagers into a single
    day-by-day game loop.
    """

    def __init__(self, settings: Settings, db: DB):
        self.settings = settings
        self.db = db

        # Manager / player identity
        self.manager: Optional[Manager] = None
        self.player_club_id: Optional[UUID] = None

        # League / season state
        self.league: Optional[League] = None
        self.season: Optional[Season] = None
        self.calendar: Optional[SeasonCalendar] = None
        self.current_date: datetime.date = datetime.date.today()
        self.season_number: int = 1
        self.is_season_over: bool = False

        # Subsystem managers
        self.training_manager: TrainingManager = TrainingManager()
        self.transfer_market: TransferMarket = TransferMarket(
            window=TransferWindow.CLOSED
        )
        self.youth_academy: YouthAcademy = YouthAcademy(level=1)
        self.loan_manager: LoanManager = LoanManager()
        self.injury_manager: InjuryManager = InjuryManager()
        self.career_manager: CareerManager = CareerManager()
        self.interaction_manager: InteractionManager = InteractionManager()

        # AI controllers (one per non-player club)
        self.ai_managers: dict[UUID, AIManager] = {}

        # Clubs cache (loaded from DB, mutated during play)
        self.clubs: list[Club] = []
        self._club_map: dict[UUID, Club] = {}

        # News / event feed
        self.news_feed: list[dict] = []

        # Track which rounds have been played (to avoid replays)
        self._played_rounds: set[int] = set()

    # ======================================================================
    # NEW CAREER
    # ======================================================================

    def new_career(
        self,
        manager_name: str,
        league_name: str,
        club_id: UUID,
    ) -> dict:
        """Initialise a brand-new career.

        Parameters
        ----------
        manager_name : str
            Display name for the human manager (split on first space into
            first / last names).
        league_name : str
            Name for the league competition.
        club_id : UUID
            The club the player will manage.

        Returns
        -------
        dict
            Summary of the freshly-created career (club name, budget, etc.).
        """
        # --- create Manager ---
        parts = manager_name.strip().split(" ", 1)
        first = parts[0] if parts else "Manager"
        last = parts[1] if len(parts) > 1 else ""
        self.manager = Manager(
            manager_id=uuid.uuid4(),
            first_name=first,
            last_name=last,
            birth_date=datetime.date(1985, 1, 1),
            tactical_ability=random.randint(8, 15),
            man_management=random.randint(8, 15),
            youth_development=random.randint(8, 15),
            discipline=random.randint(8, 15),
            motivation=random.randint(8, 15),
        )

        # --- load clubs / players from DB ---
        self.db.check_clubs_file()
        clubs_data = self.db.load_clubs()
        players_data = self.db.load_players()
        self.clubs = self.db.load_club_objects(clubs_data, players_data)
        self._club_map = {c.club_id: c for c in self.clubs}

        # --- identify player club ---
        if club_id not in self._club_map:
            raise ValueError(f"Club {club_id} not found in database")
        self.player_club_id = club_id
        player_club = self._club_map[club_id]

        # --- create League + Season ---
        self.league = League(name=league_name, clubs=self.clubs)
        self.season = Season(self.league)
        self.season.setup_season()

        # --- calendar ---
        year = datetime.date.today().year
        self.calendar = SeasonCalendar(year, self.league)
        self.calendar.generate_calendar()

        # --- date ---
        self.current_date = datetime.date(year, 8, 1)
        self.season_number = 1
        self.is_season_over = False
        self._played_rounds = set()

        # --- initial budget (stadium_capacity * 500) ---
        initial_balance = player_club.stadium_capacity * 500
        player_club.finances = FinanceManager(balance=float(initial_balance))
        transfer_budget = initial_balance * 0.6
        wage_budget = initial_balance * 0.4
        player_club.finances.set_season_budget(transfer_budget, wage_budget)

        # Give every AI club a proportional balance too
        for club in self.clubs:
            if club.club_id != club_id:
                balance = club.stadium_capacity * 500
                club.finances = FinanceManager(balance=float(balance))
                club.finances.set_season_budget(balance * 0.6, balance * 0.4)

        # --- career manager job ---
        self.career_manager = self.manager.career
        self.career_manager.start_job(player_club.name, self.current_date)

        # --- AI managers ---
        self.ai_managers = {}
        for club in self.clubs:
            if club.club_id != club_id:
                ai = AIManager(club.club_id)
                ai.set_formation(club)
                ai.set_training_focus(club)
                self.ai_managers[club.club_id] = ai

        # --- initial transfer market (20 % of non-player-club players) ---
        self.transfer_market = TransferMarket(window=TransferWindow.OPEN)
        non_player_club_players: list[tuple[PlayerTeam, Club]] = []
        for club in self.clubs:
            if club.club_id != club_id:
                for player in club.squad:
                    non_player_club_players.append((player, club))
        listing_count = max(1, len(non_player_club_players) // 5)
        if non_player_club_players:
            sampled = random.sample(
                non_player_club_players,
                min(listing_count, len(non_player_club_players)),
            )
            for player, club in sampled:
                value = calculate_market_value(
                    {
                        "dob": player.details.dob,
                        "overall": player.details.attributes.get_overall(
                            player.details.get_best_position()
                        ),
                        "potential_skill": player.details.potential_skill,
                        "international_reputation": player.details.international_reputation,
                    }
                )
                try:
                    self.transfer_market.list_player(
                        player.details.player_id,
                        club.club_id,
                        value,
                        self.current_date,
                    )
                except ValueError:
                    pass

        # --- welcome news ---
        self._add_news(
            f"Welcome to {player_club.name}!",
            (
                f"Manager {manager_name} has been appointed as the new head "
                f"coach of {player_club.name}. The club's board expects a "
                f"strong season. The transfer budget has been set to "
                f"{transfer_budget:,.0f}."
            ),
        )

        return {
            "manager": f"{self.manager.first_name} {self.manager.last_name}",
            "club": player_club.name,
            "league": league_name,
            "balance": player_club.finances.balance,
            "transfer_budget": transfer_budget,
            "wage_budget": wage_budget,
            "squad_size": len(player_club.squad),
            "season_year": year,
        }

    # ======================================================================
    # ADVANCE DAY  (the core game-loop tick)
    # ======================================================================

    def advance_day(self) -> dict:
        """Advance the simulation by one calendar day.

        Returns
        -------
        dict
            A summary of everything that happened:
            ``{"date", "events", "news", "match_ready", "season_over"}``.
        """
        self.current_date += datetime.timedelta(days=1)

        day_events: list[dict] = []
        match_ready: Optional[dict] = None

        events = self.calendar.get_events_for_date(self.current_date)

        for event in events:
            day_events.append(event.serialize())

            if event.event_type == "training":
                self._process_training()

            elif event.event_type == "match":
                match_ready = self._process_match_day(event)

            elif event.event_type == "transfer_window_open":
                self.transfer_market.window = TransferWindow.OPEN
                self._add_news(
                    "Transfer window opens!",
                    f"The {event.data.get('window', '')} transfer window "
                    f"is now open.  Clubs may buy and sell players.",
                )

            elif event.event_type == "transfer_window_close":
                self.transfer_market.window = TransferWindow.CLOSED
                self._add_news(
                    "Transfer window closed",
                    f"The {event.data.get('window', '')} transfer window "
                    f"has closed.  No more transfers until the next window.",
                )

            elif event.event_type == "youth_intake":
                self._process_youth_intake()

            elif event.event_type == "season_end":
                self._process_season_end()

        # --- daily maintenance -----------------------------------------------
        # Injury recoveries
        recovered_ids = self.injury_manager.check_recovery(self.current_date)
        for pid in recovered_ids:
            # Clear the injury flag on the player object
            for club in self.clubs:
                for player in club.squad:
                    if player.details.player_id == pid:
                        player.details.injury_type = PlayerInjury.NO_INJURY
                        self._add_news(
                            f"{player.details.short_name} recovered!",
                            f"{player.details.short_name} has recovered from "
                            f"injury and is available for selection.",
                        )

        # Loan expirations
        expired_loans = self.loan_manager.check_expired_loans(self.current_date)
        for deal in expired_loans:
            from_club = self._club_map.get(deal.from_club_id)
            to_club = self._club_map.get(deal.to_club_id)
            if from_club and to_club:
                player = self._find_player_by_id(deal.player_id)
                if player:
                    self.loan_manager.return_loan(deal, from_club, to_club, player)
                    self._add_news(
                        f"Loan ended: {player.details.short_name}",
                        f"{player.details.short_name} has returned to "
                        f"{from_club.name} after their loan at {to_club.name} ended.",
                    )

        # AI daily decisions (transfers when window is open)
        if self.transfer_market.window == TransferWindow.OPEN:
            for club_id, ai in self.ai_managers.items():
                club = self._club_map.get(club_id)
                if club:
                    actions = ai.make_transfer_decisions(
                        club, self.transfer_market, self.current_date
                    )
                    for action in actions:
                        if action["action"] == "buy":
                            self._add_news(
                                f"{club.name} signs player",
                                f"{club.name} have completed a transfer.",
                            )

        # --- random injury chance (very small per day) -----------------------
        self._random_daily_injury_check()

        return {
            "date": self.current_date.isoformat(),
            "events": day_events,
            "news": list(self.news_feed[-10:]),  # last 10
            "match_ready": match_ready,
            "season_over": self.is_season_over,
        }

    # ======================================================================
    # MATCH SIMULATION
    # ======================================================================

    def play_match(self, home_id: UUID, away_id: UUID) -> dict:
        """Create and run a LiveGame, returning the result.

        This delegates to the simulation engine.  If the simulation module
        is not fully wired up, falls back to *simulate_match*.
        """
        try:
            from .simulation.simulation import LiveGame
            from .simulation.fixture import Fixture
            from .football.team_simulation import TeamSimulation
            from .football.formation import Formation

            home_club = self._club_map[home_id]
            away_club = self._club_map[away_id]

            fixture = Fixture(
                fixture_id=uuid.uuid4(),
                championship_id=uuid.uuid4(),
                home_team=home_id,
                away_team=away_id,
                stadium=home_club.stadium,
            )

            # Build formations
            home_formation = Formation(
                home_club.default_formation
            )
            home_formation.get_best_players(list(home_club.squad))
            away_formation = Formation(
                away_club.default_formation
            )
            away_formation.get_best_players(list(away_club.squad))

            home_sim = TeamSimulation(home_club, home_formation)
            away_sim = TeamSimulation(away_club, away_formation)

            game = LiveGame(
                fixture=fixture,
                home_team=home_sim,
                away_team=away_sim,
                possible_extra_time=False,
                possible_penalties=False,
                no_break=True,
            )
            game.run()

            home_goals = home_sim.score
            away_goals = away_sim.score

            result = {
                "home_club": home_club.name,
                "away_club": away_club.name,
                "home_goals": home_goals,
                "away_goals": away_goals,
                "attendance": game.attendance,
            }

            # Record career stats if the player's club is involved
            if home_id == self.player_club_id or away_id == self.player_club_id:
                is_player_home = home_id == self.player_club_id
                player_goals = home_goals if is_player_home else away_goals
                opponent_goals = away_goals if is_player_home else home_goals
                won = player_goals > opponent_goals
                drawn = player_goals == opponent_goals
                self.career_manager.record_match_result(won, drawn)

                # Matchday revenue for player club
                player_club = self._club_map[self.player_club_id]
                if is_player_home:
                    attendance = min(
                        game.attendance, player_club.stadium_capacity
                    )
                    player_club.finances.calculate_matchday_revenue(attendance)

            return result

        except Exception:
            # Fallback to quick simulation
            return self.simulate_match(home_id, away_id)

    def simulate_match(self, home_id: UUID, away_id: UUID) -> dict:
        """Quick-simulate a match without live play.

        Uses the same weighted random score generation as ``Season.simulate_round``.
        """
        score_weights = [25, 30, 25, 13, 7]
        score_range = list(range(len(score_weights)))

        home_goals = random.choices(score_range, weights=score_weights, k=1)[0]
        away_goals = random.choices(score_range, weights=score_weights, k=1)[0]

        home_club = self._club_map[home_id]
        away_club = self._club_map[away_id]

        # Record career stats if the player's club is involved
        if home_id == self.player_club_id or away_id == self.player_club_id:
            is_player_home = home_id == self.player_club_id
            pg = home_goals if is_player_home else away_goals
            og = away_goals if is_player_home else home_goals
            self.career_manager.record_match_result(pg > og, pg == og)

            # Matchday revenue
            if is_player_home:
                player_club = self._club_map[self.player_club_id]
                attendance = random.randint(
                    int(player_club.stadium_capacity * 0.6),
                    player_club.stadium_capacity,
                )
                player_club.finances.calculate_matchday_revenue(attendance)

        return {
            "home_club": home_club.name,
            "away_club": away_club.name,
            "home_goals": home_goals,
            "away_goals": away_goals,
        }

    # ======================================================================
    # QUERIES
    # ======================================================================

    def get_standings(self) -> list[dict]:
        """Return current league standings as a list of dicts."""
        if self.league is None:
            return []
        entries = self.league.get_standings()
        standings = []
        for i, entry in enumerate(entries, start=1):
            standings.append(
                {
                    "position": i,
                    "club": entry.club.name,
                    "club_id": str(entry.club.club_id),
                    "played": entry.played,
                    "won": entry.won,
                    "drawn": entry.drawn,
                    "lost": entry.lost,
                    "goals_for": entry.goals_for,
                    "goals_against": entry.goals_against,
                    "goal_difference": entry.goal_difference,
                    "points": entry.points,
                }
            )
        return standings

    def get_player_club(self) -> Optional[dict]:
        """Return summary dict for the player's club."""
        if self.player_club_id is None:
            return None
        club = self._club_map.get(self.player_club_id)
        if club is None:
            return None
        return {
            "club_id": str(club.club_id),
            "name": club.name,
            "stadium": club.stadium,
            "stadium_capacity": club.stadium_capacity,
            "squad_size": len(club.squad),
            "balance": club.finances.balance,
            "formation": club.default_formation,
        }

    def get_upcoming_fixtures(self, count: int = 5) -> list[dict]:
        """Return the next *count* fixtures for the player's club."""
        fixtures: list[dict] = []
        if self.calendar is None or self.player_club_id is None:
            return fixtures

        pid = str(self.player_club_id)
        for event in self.calendar.events:
            if event.event_type != "match" or event.date <= self.current_date:
                continue
            for fix in event.data.get("fixtures", []):
                if fix["home"] == pid or fix["away"] == pid:
                    home_club = self._club_map.get(UUID(fix["home"]))
                    away_club = self._club_map.get(UUID(fix["away"]))
                    fixtures.append(
                        {
                            "date": event.date.isoformat(),
                            "round": event.data.get("round"),
                            "home": home_club.name if home_club else fix["home"],
                            "away": away_club.name if away_club else fix["away"],
                            "home_id": fix["home"],
                            "away_id": fix["away"],
                        }
                    )
                    if len(fixtures) >= count:
                        return fixtures
        return fixtures

    def get_recent_results(self, count: int = 5) -> list[dict]:
        """Return the last *count* results from ``season.results``."""
        if self.season is None:
            return []
        results: list[dict] = []
        for round_data in reversed(self.season.results):
            for match in round_data["matches"]:
                home_club = self._club_map.get(
                    match["home"]
                    if isinstance(match["home"], UUID)
                    else UUID(str(match["home"]))
                )
                away_club = self._club_map.get(
                    match["away"]
                    if isinstance(match["away"], UUID)
                    else UUID(str(match["away"]))
                )
                results.append(
                    {
                        "home": home_club.name if home_club else str(match["home"]),
                        "away": away_club.name if away_club else str(match["away"]),
                        "home_goals": match["home_goals"],
                        "away_goals": match["away_goals"],
                        "round": round_data["round"],
                    }
                )
                if len(results) >= count:
                    return results
        return results

    # ======================================================================
    # END OF SEASON
    # ======================================================================

    def end_season(self) -> dict:
        """Process all end-of-season activities.

        Returns a summary dict with trophies, awards, finances, etc.
        """
        summary: dict = {"season_number": self.season_number}

        # --- trophies ---
        standings = self.league.get_standings()
        if standings:
            champion = standings[0]
            season_label = (
                f"{self.calendar.season_year}/{self.calendar.season_year + 1}"
            )
            trophy_name = f"{self.league.name} Champion"

            if champion.club.club_id == self.player_club_id:
                self.career_manager.add_trophy(
                    trophy_name,
                    season_label,
                    champion.club.name,
                    self.current_date,
                )
                self._add_news(
                    "Champions!",
                    f"Congratulations!  {champion.club.name} have won the "
                    f"{self.league.name} with {champion.points} points!",
                )
            else:
                self._add_news(
                    f"{champion.club.name} are champions!",
                    f"{champion.club.name} have won the {self.league.name} "
                    f"with {champion.points} points.",
                )

            summary["champion"] = champion.club.name

        # --- awards ---
        awards = generate_season_awards(self.league, self.clubs)
        summary["awards"] = awards
        for award in awards:
            self._add_news(
                f"Award: {award['award']}",
                f"{award.get('player_name', award.get('club_name', 'N/A'))} "
                f"wins the {award['award']} award.",
            )

        # --- expire contracts ---
        season_end = datetime.date(
            self.calendar.season_year + 1, 6, 30
        )
        expired_players: list[str] = []
        for club in self.clubs:
            to_remove: list[PlayerTeam] = []
            for player in club.squad:
                if player.contract.contract_end <= season_end:
                    to_remove.append(player)
            for player in to_remove:
                club.squad.remove(player)
                expired_players.append(player.details.short_name)
        if expired_players:
            self._add_news(
                "Contract expirations",
                f"{len(expired_players)} players have been released as free "
                f"agents after their contracts expired.",
            )
        summary["expired_contracts"] = len(expired_players)

        # --- develop youth prospects ---
        self.youth_academy.develop_prospects()

        # --- TV revenue (based on final position) ---
        player_club = self._club_map.get(self.player_club_id)
        if player_club and standings:
            position = next(
                (
                    i + 1
                    for i, e in enumerate(standings)
                    if e.club.club_id == self.player_club_id
                ),
                len(standings),
            )
            tv_rev = player_club.finances.calculate_tv_revenue(
                position, len(standings)
            )
            summary["tv_revenue"] = tv_rev
            summary["final_position"] = position

        # --- end-of-season news ---
        self._add_news(
            "Season complete!",
            f"The {self.calendar.season_year}/{self.calendar.season_year + 1} "
            f"season has come to an end.",
        )

        # --- career summary update ---
        summary["career"] = self.career_manager.get_career_summary()
        summary["finances"] = (
            player_club.finances.get_season_report() if player_club else {}
        )

        self.is_season_over = True
        return summary

    # ======================================================================
    # START NEW SEASON
    # ======================================================================

    def start_new_season(self) -> dict:
        """Begin the next season.

        Returns a summary dict for the new season.
        """
        self.season_number += 1
        new_year = self.calendar.season_year + 1

        # --- new League + Season ---
        self.league = League(name=self.league.name, clubs=self.clubs)
        self.season = Season(self.league)
        self.season.setup_season()

        # --- new calendar ---
        self.calendar = SeasonCalendar(new_year, self.league)
        self.calendar.generate_calendar()

        # --- reset date ---
        self.current_date = datetime.date(new_year, 8, 1)
        self.is_season_over = False
        self._played_rounds = set()

        # --- reset injuries ---
        self.injury_manager = InjuryManager()
        for club in self.clubs:
            for player in club.squad:
                player.details.injury_type = PlayerInjury.NO_INJURY
                player.details.fitness = min(player.details.fitness + 20, 100.0)

        # --- new budget ---
        player_club = self._club_map.get(self.player_club_id)
        if player_club:
            season_income = player_club.stadium_capacity * 500
            player_club.finances.set_season_budget(
                season_income * 0.6, season_income * 0.4
            )

        for club_id, ai in self.ai_managers.items():
            club = self._club_map.get(club_id)
            if club:
                season_income = club.stadium_capacity * 500
                club.finances.set_season_budget(
                    season_income * 0.6, season_income * 0.4
                )
                ai.set_formation(club)
                ai.set_training_focus(club)

        # --- refresh transfer market ---
        self.transfer_market = TransferMarket(window=TransferWindow.CLOSED)

        # --- news ---
        self._add_news(
            "New season begins!",
            f"The {new_year}/{new_year + 1} season is about to start.  "
            f"Pre-season preparations are underway.",
        )

        return {
            "season_number": self.season_number,
            "season_year": new_year,
            "squad_size": len(player_club.squad) if player_club else 0,
            "balance": player_club.finances.balance if player_club else 0,
        }

    # ======================================================================
    # SERIALIZATION
    # ======================================================================

    def serialize(self) -> dict:
        """Serialize the entire career state for save/load."""
        # Build club data
        clubs_data = [c.serialize() for c in self.clubs]

        # Build players data (all players across all clubs)
        players_data = []
        squads_data = []
        for club in self.clubs:
            for player in club.squad:
                players_data.append(player.details.serialize())
                squads_data.append(player.serialize())

        return {
            "version": 1,
            "manager": self.manager.serialize() if self.manager else None,
            "player_club_id": str(self.player_club_id) if self.player_club_id else None,
            "current_date": self.current_date.isoformat(),
            "season_number": self.season_number,
            "is_season_over": self.is_season_over,
            "league_name": self.league.name if self.league else "",
            "clubs": clubs_data,
            "players": players_data,
            "squads": squads_data,
            "season": self.season.serialize() if self.season else None,
            "calendar": self.calendar.serialize() if self.calendar else None,
            "training_manager": self.training_manager.serialize(),
            "transfer_market": self.transfer_market.serialize(),
            "youth_academy": self.youth_academy.serialize(),
            "loan_manager": self.loan_manager.serialize(),
            "injury_manager": self.injury_manager.serialize(),
            "interaction_manager": self.interaction_manager.serialize(),
            "ai_managers": {
                str(k): v.serialize() for k, v in self.ai_managers.items()
            },
            "news_feed": self.news_feed,
            "played_rounds": list(self._played_rounds),
        }

    @classmethod
    def get_from_dict(cls, data: dict, settings: Settings, db: DB) -> "CareerEngine":
        """Restore a CareerEngine from a serialized save dict."""
        engine = cls(settings, db)

        # --- manager ---
        if data.get("manager"):
            engine.manager = Manager.get_from_dict(data["manager"])

        # --- clubs ---
        clubs_data = data.get("clubs", [])
        players_data = data.get("players", [])
        if clubs_data and players_data:
            engine.clubs = db.load_club_objects(clubs_data, players_data)
        engine._club_map = {c.club_id: c for c in engine.clubs}

        # Restore finances for each club from the serialized data
        for club_dict, club_obj in zip(clubs_data, engine.clubs):
            if "finances" in club_dict:
                fin = club_dict["finances"]
                club_obj.finances.balance = fin.get("balance", 0.0)

        # --- player club ---
        if data.get("player_club_id"):
            engine.player_club_id = UUID(data["player_club_id"])

        # --- dates ---
        engine.current_date = datetime.date.fromisoformat(data["current_date"])
        engine.season_number = data.get("season_number", 1)
        engine.is_season_over = data.get("is_season_over", False)

        # --- league + season ---
        league_name = data.get("league_name", "League")
        engine.league = League(name=league_name, clubs=engine.clubs)
        if data.get("season"):
            engine.season = Season.get_from_dict(data["season"], engine.league)
        else:
            engine.season = Season(engine.league)

        # --- calendar ---
        if data.get("calendar"):
            engine.calendar = SeasonCalendar.get_from_dict(
                data["calendar"], engine.league
            )

        # --- subsystems ---
        engine.training_manager = TrainingManager.get_from_dict(
            data.get("training_manager", {})
        )
        engine.transfer_market = TransferMarket.get_from_dict(
            data.get("transfer_market", {})
        )
        engine.youth_academy = YouthAcademy.get_from_dict(
            data.get("youth_academy", {})
        )
        engine.loan_manager = LoanManager.get_from_dict(
            data.get("loan_manager", {})
        )
        engine.injury_manager = InjuryManager.get_from_dict(
            data.get("injury_manager", {})
        )
        engine.interaction_manager = InteractionManager.get_from_dict(
            data.get("interaction_manager", {})
        )

        # --- career manager (from the manager object) ---
        if engine.manager:
            engine.career_manager = engine.manager.career

        # --- AI managers ---
        engine.ai_managers = {}
        for k, v in data.get("ai_managers", {}).items():
            engine.ai_managers[UUID(k)] = AIManager.get_from_dict(v)

        # --- news ---
        engine.news_feed = data.get("news_feed", [])
        engine._played_rounds = set(data.get("played_rounds", []))

        return engine

    # ======================================================================
    # PRIVATE HELPERS
    # ======================================================================

    def _add_news(self, headline: str, body: str) -> None:
        """Append a news item to the feed."""
        self.news_feed.append(
            {
                "date": self.current_date.isoformat(),
                "headline": headline,
                "body": body,
            }
        )

    def _process_training(self) -> None:
        """Run training sessions for all AI squads (player trains via UI)."""
        for club_id, ai in self.ai_managers.items():
            club = self._club_map.get(club_id)
            if club and club.squad:
                tm = TrainingManager()
                tm.train_squad(club.squad, ai.training_focus, intensity=0.7)

    def _process_match_day(self, event: CalendarEvent) -> Optional[dict]:
        """Process a match-day event.

        AI-vs-AI games are simulated immediately.  If the player's club has a
        fixture, it is flagged for interactive play.

        Returns a dict describing the player's pending match, or None.
        """
        round_idx = event.data.get("round")
        if round_idx is None or round_idx in self._played_rounds:
            return None

        fixtures = event.data.get("fixtures", [])
        player_fixture = None
        ai_results: list[dict] = []

        pid = str(self.player_club_id) if self.player_club_id else None

        for fix in fixtures:
            home_id_str = fix["home"]
            away_id_str = fix["away"]
            is_player_match = pid and (
                home_id_str == pid or away_id_str == pid
            )

            if is_player_match:
                home_club = self._club_map.get(UUID(home_id_str))
                away_club = self._club_map.get(UUID(away_id_str))
                player_fixture = {
                    "round": round_idx,
                    "home_id": home_id_str,
                    "away_id": away_id_str,
                    "home_name": home_club.name if home_club else home_id_str,
                    "away_name": away_club.name if away_club else away_id_str,
                    "date": event.date.isoformat(),
                }
            else:
                # Simulate AI vs AI
                home_uid = UUID(home_id_str)
                away_uid = UUID(away_id_str)
                result = self.simulate_match(home_uid, away_uid)
                ai_results.append(result)

        # Record AI results into the season table
        for res in ai_results:
            home_club_name = res["home_club"]
            away_club_name = res["away_club"]
            self.league._record_result_by_name(
                home_club_name,
                away_club_name,
                res["home_goals"],
                res["away_goals"],
            )

        # If no player fixture in this round, auto-play all and mark done
        if player_fixture is None:
            self._played_rounds.add(round_idx)

        return player_fixture

    def complete_player_match(self, result: dict) -> None:
        """Called after the player's match is resolved (played or simulated).

        Parameters
        ----------
        result : dict
            Must contain: ``home_club``, ``away_club``, ``home_goals``,
            ``away_goals``, and optionally ``round``.
        """
        round_idx = result.get("round")

        # Record in league table
        self.league._record_result_by_name(
            result["home_club"],
            result["away_club"],
            result["home_goals"],
            result["away_goals"],
        )

        if round_idx is not None:
            self._played_rounds.add(round_idx)

        # Build the full round results list for the Season object
        # (combines AI results that were already simulated with the player match)
        round_results = [
            {
                "home": self._club_id_by_name(result["home_club"]),
                "away": self._club_id_by_name(result["away_club"]),
                "home_goals": result["home_goals"],
                "away_goals": result["away_goals"],
            }
        ]
        self.season.results.append(
            {"round": round_idx, "matches": round_results}
        )

        # News
        self._add_news(
            f"{result['home_club']} {result['home_goals']} - "
            f"{result['away_goals']} {result['away_club']}",
            f"Full time: {result['home_club']} {result['home_goals']} - "
            f"{result['away_goals']} {result['away_club']}.",
        )

    def _process_youth_intake(self) -> None:
        """Generate youth prospects for every club."""
        # Player club
        new_prospects = self.youth_academy.generate_prospects(self.settings)
        if new_prospects:
            self._add_news(
                "Youth intake!",
                f"{len(new_prospects)} new prospect(s) have joined your "
                f"youth academy.",
            )

        # AI clubs (just log, don't track their academies in detail)
        for club_id, ai in self.ai_managers.items():
            club = self._club_map.get(club_id)
            if club:
                ai_academy = YouthAcademy(level=random.randint(1, 3))
                ai_academy.generate_prospects(self.settings)

    def _process_season_end(self) -> None:
        """Trigger end-of-season processing."""
        self.end_season()

    def _random_daily_injury_check(self) -> None:
        """Small daily chance of random injuries (simulates training knocks)."""
        for club in self.clubs:
            for player in club.squad:
                if player.details.is_injured:
                    continue
                # 0.5% chance per player per day
                if random.random() < 0.005:
                    injury_type = random.choices(
                        [PlayerInjury.LIGHT_INJURY, PlayerInjury.MEDIUM_INJURY],
                        weights=[85, 15],
                        k=1,
                    )[0]
                    injury = self.injury_manager.generate_injury(
                        player.details.player_id, injury_type, self.current_date
                    )
                    player.details.injury_type = injury_type
                    self._add_news(
                        f"Injury: {player.details.short_name}",
                        f"{player.details.short_name} ({club.name}) has "
                        f"suffered a {injury.description.lower()}.  "
                        f"Expected recovery: {injury.recovery_days} days.",
                    )

    def _find_player_by_id(self, player_id: UUID) -> Optional[PlayerTeam]:
        """Search all club squads for a player by UUID."""
        for club in self.clubs:
            for player in club.squad:
                if player.details.player_id == player_id:
                    return player
        return None

    def _club_id_by_name(self, name: str) -> Optional[UUID]:
        """Reverse-lookup a club UUID from its name."""
        for club in self.clubs:
            if club.name == name:
                return club.club_id
        return None
