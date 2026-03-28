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
"""
Comprehensive tests for the new core modules introduced in the OpenFoot Manager
expansion.  All tests are pure logic -- no tkinter or GUI dependencies.
"""
import datetime
import uuid
from collections import Counter
from itertools import combinations
from pathlib import Path
from unittest.mock import patch

import pytest

from ofm.core.football.career import CareerManager
from ofm.core.football.club import Club
from ofm.core.football.finances import (
    ExpenseType,
    FinanceManager,
    RevenueType,
    SeasonBudget,
    SponsorshipDeal,
)
from ofm.core.football.injury import InjuryDetail, InjuryManager, PlayerInjury
from ofm.core.football.interactions import (
    InteractionManager,
    InteractionType,
    MoraleEffect,
    PressConference,
    PressQuestion,
    PressResponse,
    PlayerInteraction,
    TalkType,
    TeamTalkType,
)
from ofm.core.football.league import League, LeagueTableEntry, Season
from ofm.core.football.manager import Manager
from ofm.core.football.roster import RosterError, RosterManager
from ofm.core.football.training import (
    TrainingFocus,
    TrainingManager,
    TrainingSession,
    _set_sub_attr,
)
from ofm.core.football.transfer_market import (
    OfferStatus,
    TransferListing,
    TransferMarket,
    TransferWindow,
    calculate_market_value,
)
from ofm.core.football.youth import YouthAcademy, YouthProspect
from ofm.core.game_state import GameState, SaveManager
from ofm.core.mod_support import ModLoader, ModType, MOD_TEMPLATE
from ofm.core.simulation.commentary import CommentaryGenerator
from ofm.core.simulation.event import EventOutcome
from ofm.core.simulation.event_type import EventType


# ═══════════════════════════════════════════════════════════════════════════
# Helper factories
# ═══════════════════════════════════════════════════════════════════════════


def _make_club(name: str, club_id: uuid.UUID = None) -> Club:
    """Create a minimal Club for testing purposes."""
    if club_id is None:
        club_id = uuid.uuid4()
    return Club(
        club_id=club_id,
        name=name,
        country="TST",
        location="TestCity",
        default_formation="4-4-2",
        squad=[],
        stadium="Test Stadium",
        stadium_capacity=30000,
    )


def _make_clubs(n: int) -> list[Club]:
    """Create *n* uniquely-named clubs."""
    return [_make_club(f"Club_{i}") for i in range(n)]


def _make_player_dict(
    position: int = 4,
    overall: int = 70,
    idx: int = 0,
    injured: bool = False,
) -> dict:
    """Build a minimal player dict compatible with RosterManager."""
    return {
        "id": idx,
        "short_name": f"Player_{idx}",
        "positions": [position],
        "fitness": 100.0,
        "injury_type": 1 if not injured else 2,  # 1 == NO_INJURY, 2 == LIGHT
        "attributes": {
            "offensive": {
                "shot_power": overall,
                "shot_accuracy": overall,
                "free_kick": overall,
                "penalty": overall,
                "positioning": overall,
            },
            "physical": {
                "strength": overall,
                "aggression": overall,
                "endurance": overall,
            },
            "defensive": {
                "tackling": overall,
                "interception": overall,
                "positioning": overall,
            },
            "intelligence": {
                "vision": overall,
                "passing": overall,
                "crossing": overall,
                "ball_control": overall,
                "dribbling": overall,
                "skills": overall,
                "team_work": overall,
            },
            "gk": {
                "reflexes": overall,
                "jumping": overall,
                "positioning": overall,
                "penalty": overall,
            },
        },
    }


def _make_squad(size: int = 20) -> list[dict]:
    """Build a squad of *size* player dicts with realistic position spread.

    1 GK, 5 DF, 5 MF, 4 FW, rest MF.
    """
    squad = []
    positions = (
        [1]          # 1 GK
        + [2] * 5    # 5 DF
        + [3] * 5    # 5 MF
        + [4] * 4    # 4 FW
        + [3] * (size - 15)  # fill remainder with MF
    )
    for i, pos in enumerate(positions[:size]):
        squad.append(_make_player_dict(position=pos, overall=60 + i, idx=i))
    return squad


def _make_youth_prospect_dict(age_offset: int = 0) -> dict:
    """Build a raw prospect player_dict with youth-appropriate data."""
    year = datetime.date.today().year - 17 - age_offset
    return {
        "first_name": "Youth",
        "last_name": f"Player_{age_offset}",
        "dob": f"{year}-06-15",
        "positions": [4],
        "potential_skill": 85,
        "attributes": {
            "offensive": {"shot_power": 40, "shot_accuracy": 38, "free_kick": 30,
                          "penalty": 35, "positioning": 42},
            "defensive": {"tackling": 30, "interception": 28, "positioning": 32},
            "physical": {"strength": 35, "aggression": 30, "endurance": 40},
            "intelligence": {"vision": 38, "passing": 36, "crossing": 34,
                             "ball_control": 40, "dribbling": 42, "skills": 36,
                             "team_work": 38},
            "gk": {"reflexes": 20, "jumping": 22, "positioning": 18, "penalty": 15},
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# 1. League & Season
# ═══════════════════════════════════════════════════════════════════════════


class TestLeagueFixtures:
    """Tests for League.generate_fixtures() and round-robin properties."""

    def test_generate_fixtures_correct_round_count(self):
        clubs = _make_clubs(4)
        league = League("Test League", clubs)
        rounds = league.generate_fixtures()
        # 4 teams -> 2*(4-1) = 6 rounds
        assert len(rounds) == 6

    def test_generate_fixtures_correct_matches_per_round(self):
        clubs = _make_clubs(6)
        league = League("Test League", clubs)
        rounds = league.generate_fixtures()
        # Each round should have N/2 = 3 matches
        for rnd in rounds:
            assert len(rnd) == 3

    def test_round_robin_every_pair_twice(self):
        clubs = _make_clubs(4)
        league = League("Test League", clubs)
        rounds = league.generate_fixtures()
        # Flatten to list of (home_id, away_id)
        all_matches = [match for rnd in rounds for match in rnd]
        # Each ordered pair (A, B) should appear exactly once; the reverse
        # (B, A) should also appear exactly once.
        pair_counts = Counter()
        for home_id, away_id in all_matches:
            pair_counts[frozenset((home_id, away_id))] += 1
        for pair, count in pair_counts.items():
            assert count == 2, f"Pair {pair} appeared {count} times, expected 2"

    def test_generate_fixtures_empty_league(self):
        league = League("Empty", [])
        assert league.generate_fixtures() == []

    def test_generate_fixtures_single_club(self):
        league = League("Solo", _make_clubs(1))
        assert league.generate_fixtures() == []


class TestSeason:
    """Tests for Season orchestration."""

    def _make_season(self, n_clubs: int = 4) -> Season:
        clubs = _make_clubs(n_clubs)
        league = League("Test League", clubs)
        season = Season(league)
        season.setup_season()
        return season

    def test_setup_season_creates_rounds(self):
        season = self._make_season(4)
        assert len(season.rounds) == 6
        assert season.current_round == 0

    def test_simulate_round_records_results(self):
        season = self._make_season(4)
        season.simulate_round()
        assert season.current_round == 1
        assert len(season.results) == 1

    def test_play_round_updates_standings(self):
        season = self._make_season(4)
        fixtures = season.get_current_round_fixtures()
        results = []
        for home_id, away_id in fixtures:
            results.append({
                "home": home_id,
                "away": away_id,
                "home_goals": 2,
                "away_goals": 1,
            })
        season.play_round(results)
        standings = season.get_standings()
        # All home teams won, so at least some entries should have 3 points
        points = [e.points for e in standings]
        assert max(points) == 3

    def test_get_standings_sorted_correctly(self):
        clubs = _make_clubs(4)
        league = League("Test League", clubs)
        # Manually record some results
        league._record_result_by_name(clubs[0].name, clubs[1].name, 3, 0)
        league._record_result_by_name(clubs[2].name, clubs[3].name, 1, 1)
        standings = league.get_standings()
        # Club 0 has 3 pts, clubs 2 and 3 have 1 pt, club 1 has 0
        assert standings[0].club.name == clubs[0].name
        assert standings[0].points == 3

    def test_season_is_finished_after_all_rounds(self):
        season = self._make_season(4)
        total_rounds = len(season.rounds)
        for _ in range(total_rounds):
            season.simulate_round()
        assert season.is_finished is True


# ═══════════════════════════════════════════════════════════════════════════
# 2. Transfer Market
# ═══════════════════════════════════════════════════════════════════════════


class TestTransferMarket:

    def test_list_player_adds_listing(self):
        market = TransferMarket()
        pid = uuid.uuid4()
        cid = uuid.uuid4()
        listing = market.list_player(pid, cid, 5_000_000.0)
        assert len(market.listings) == 1
        assert listing.player_id == pid

    def test_make_offer_auto_accepts_at_asking_price(self):
        market = TransferMarket()
        pid = uuid.uuid4()
        cid = uuid.uuid4()
        market.list_player(pid, cid, 1_000_000.0)
        offer = market.make_offer(pid, uuid.uuid4(), 1_000_000.0)
        assert offer.status == OfferStatus.ACCEPTED

    def test_make_offer_auto_accepts_above_asking_price(self):
        market = TransferMarket()
        pid = uuid.uuid4()
        market.list_player(pid, uuid.uuid4(), 1_000_000.0)
        offer = market.make_offer(pid, uuid.uuid4(), 2_000_000.0)
        assert offer.status == OfferStatus.ACCEPTED

    def test_make_offer_rejects_below_70_percent(self):
        market = TransferMarket()
        pid = uuid.uuid4()
        market.list_player(pid, uuid.uuid4(), 1_000_000.0)
        offer = market.make_offer(pid, uuid.uuid4(), 500_000.0)
        assert offer.status == OfferStatus.REJECTED

    def test_make_offer_negotiates_between_70_and_99(self):
        market = TransferMarket()
        pid = uuid.uuid4()
        market.list_player(pid, uuid.uuid4(), 1_000_000.0)
        offer = market.make_offer(pid, uuid.uuid4(), 800_000.0)
        assert offer.status == OfferStatus.NEGOTIATING
        assert offer.counter_amount is not None
        # Counter should be midpoint between 800k and 1M = 900k
        assert offer.counter_amount == 900_000.0

    def test_get_free_agents_filters_correctly(self):
        market = TransferMarket()
        p1 = uuid.uuid4()
        p2 = uuid.uuid4()
        market.list_player(p1, None, 0.0)  # free agent
        market.list_player(p2, uuid.uuid4(), 5_000_000.0)  # listed by club
        free = market.get_free_agents()
        assert len(free) == 1
        assert free[0].player_id == p1

    def test_closed_window_prevents_listing(self):
        market = TransferMarket(window=TransferWindow.CLOSED)
        with pytest.raises(ValueError, match="closed"):
            market.list_player(uuid.uuid4(), None, 0.0)


class TestCalculateMarketValue:

    def test_reasonable_value_for_young_star(self):
        pdict = {
            "dob": "2002-01-15",
            "overall": 85,
            "potential_skill": 92,
            "international_reputation": 4,
        }
        val = calculate_market_value(pdict)
        assert val > 1_000_000
        assert val < 200_000_000

    def test_minimum_value_floor(self):
        pdict = {
            "dob": "1985-01-01",
            "overall": 30,
            "potential_skill": 30,
            "international_reputation": 1,
        }
        val = calculate_market_value(pdict)
        assert val >= 50_000

    def test_higher_overall_higher_value(self):
        base = {
            "dob": "1998-06-01",
            "potential_skill": 85,
            "international_reputation": 3,
        }
        low = calculate_market_value({**base, "overall": 60})
        high = calculate_market_value({**base, "overall": 85})
        assert high > low


# ═══════════════════════════════════════════════════════════════════════════
# 3. Training
# ═══════════════════════════════════════════════════════════════════════════


class TestTraining:

    def _make_player_team(self, overall: int = 60, potential: int = 90):
        """Create a minimal PlayerTeam-like object for training tests."""
        from ofm.core.football.player import Player, PreferredFoot
        from ofm.core.football.player_attributes import (
            DefensiveAttributes,
            GkAttributes,
            IntelligenceAttributes,
            OffensiveAttributes,
            PhysicalAttributes,
            PlayerAttributes,
        )
        from ofm.core.football.club import PlayerTeam
        from ofm.core.football.playercontract import PlayerContract
        from ofm.core.football.positions import Positions

        attrs = PlayerAttributes(
            OffensiveAttributes(overall, overall, overall, overall, overall),
            PhysicalAttributes(overall, overall, overall),
            DefensiveAttributes(overall, overall, overall),
            IntelligenceAttributes(overall, overall, overall, overall, overall, overall, overall),
            GkAttributes(overall, overall, overall, overall),
        )
        player = Player(
            player_id=uuid.uuid4(),
            nationality="TST",
            dob=datetime.date(2004, 1, 1),  # young player
            first_name="Test",
            last_name="Player",
            short_name="T. Player",
            positions=[Positions.MF],
            fitness=100.0,
            stamina=100.0,
            form=0.5,
            attributes=attrs,
            potential_skill=potential,
            international_reputation=3,
            preferred_foot=PreferredFoot.RIGHT,
            value=100_000.0,
        )
        contract = PlayerContract(
            wage=1000.0,
            contract_started=datetime.date(2023, 1, 1),
            contract_end=datetime.date(2026, 1, 1),
            bonus_for_goal=500.0,
            bonus_for_def=500.0,
        )
        pt = PlayerTeam(player, uuid.uuid4(), 10, contract)
        return pt

    def test_train_squad_returns_session(self):
        tm = TrainingManager()
        pt = self._make_player_team()
        session = tm.train_squad([pt], focus=TrainingFocus.GENERAL, intensity=1.0)
        assert isinstance(session, TrainingSession)
        assert len(session.results) == 1

    def test_attribute_cap_at_99(self):
        pt = self._make_player_team(overall=98, potential=99)
        _set_sub_attr(pt, "offensive", "shot_power", 100)
        # _set_sub_attr caps at 99
        assert pt.details.attributes.offensive.shot_power == 99

    def test_attack_focus_targets_offensive_attrs(self):
        tm = TrainingManager()
        pt = self._make_player_team(overall=40, potential=90)
        # Run many sessions to ensure at least one improvement
        improved_keys = set()
        for _ in range(50):
            session = tm.train_squad([pt], focus=TrainingFocus.ATTACK, intensity=1.0)
            for result in session.results:
                for key in result.get("changes", {}):
                    improved_keys.add(key)
        # At least some offensive attributes should have been trained
        offensive_trained = [k for k in improved_keys if k.startswith("offensive.")]
        assert len(offensive_trained) > 0

    def test_defense_focus_targets_defensive_attrs(self):
        tm = TrainingManager()
        pt = self._make_player_team(overall=40, potential=90)
        improved_keys = set()
        for _ in range(50):
            session = tm.train_squad([pt], focus=TrainingFocus.DEFENSE, intensity=1.0)
            for result in session.results:
                for key in result.get("changes", {}):
                    improved_keys.add(key)
        defensive_trained = [k for k in improved_keys if k.startswith("defensive.")]
        assert len(defensive_trained) > 0

    def test_injured_player_skipped(self):
        tm = TrainingManager()
        pt = self._make_player_team()
        pt.details.injury_type = PlayerInjury.LIGHT_INJURY
        session = tm.train_squad([pt], focus=TrainingFocus.GENERAL, intensity=1.0)
        assert session.results[0]["skipped"] is True


# ═══════════════════════════════════════════════════════════════════════════
# 4. Youth Academy
# ═══════════════════════════════════════════════════════════════════════════


class TestYouthAcademy:

    def test_generate_prospects_creates_young_players(self, settings):
        academy = YouthAcademy(level=3)
        prospects = academy.generate_prospects(settings, amount=2)
        assert len(prospects) == 2
        for p in prospects:
            assert 16 <= p.age <= 19

    def test_promote_prospect_marks_promoted(self):
        academy = YouthAcademy(level=1)
        prospect = YouthProspect(
            player_dict=_make_youth_prospect_dict(),
            scouted_date=datetime.date.today(),
            development_score=0.5,
        )
        academy.prospects.append(prospect)
        pdict = academy.promote_prospect(0)
        assert academy.prospects[0].promoted is True
        assert pdict is prospect.player_dict

    def test_develop_prospects_improves_attributes(self):
        academy = YouthAcademy(level=2)
        prospect = YouthProspect(
            player_dict=_make_youth_prospect_dict(),
            scouted_date=datetime.date.today(),
            development_score=0.3,
        )
        academy.prospects.append(prospect)
        # Capture original attribute sum
        attrs = prospect.player_dict["attributes"]
        original_sum = sum(
            v for group in attrs.values()
            if isinstance(group, dict)
            for v in group.values()
        )
        # Develop many times to ensure statistical improvement
        for _ in range(50):
            academy.develop_prospects()
        new_sum = sum(
            v for group in attrs.values()
            if isinstance(group, dict)
            for v in group.values()
        )
        assert new_sum > original_sum

    def test_academy_level_caps_at_5(self):
        academy = YouthAcademy(level=4)
        academy.upgrade()
        assert academy.level == 5
        academy.upgrade()
        assert academy.level == 5  # should not exceed 5

    def test_academy_level_minimum_is_1(self):
        academy = YouthAcademy(level=0)
        assert academy.level == 1


# ═══════════════════════════════════════════════════════════════════════════
# 5. Injury
# ═══════════════════════════════════════════════════════════════════════════


class TestInjury:

    def test_generate_injury_creates_detail(self):
        mgr = InjuryManager()
        pid = uuid.uuid4()
        injury = mgr.generate_injury(pid, PlayerInjury.LIGHT_INJURY, datetime.date.today())
        assert isinstance(injury, InjuryDetail)
        assert injury.player_id == pid
        assert injury.injury_type == PlayerInjury.LIGHT_INJURY

    def test_generate_injury_rejects_no_injury(self):
        mgr = InjuryManager()
        with pytest.raises(ValueError):
            mgr.generate_injury(uuid.uuid4(), PlayerInjury.NO_INJURY, datetime.date.today())

    def test_check_recovery_returns_recovered(self):
        mgr = InjuryManager()
        pid = uuid.uuid4()
        mgr.generate_injury(pid, PlayerInjury.LIGHT_INJURY, datetime.date(2025, 1, 1))
        # Force recovery_days to a known value
        mgr.active_injuries[0].recovery_days = 5
        recovered = mgr.check_recovery(datetime.date(2025, 1, 10))
        assert pid in recovered
        assert len(mgr.active_injuries) == 0

    def test_is_player_injured_correct(self):
        mgr = InjuryManager()
        pid = uuid.uuid4()
        assert mgr.is_player_injured(pid) is False
        mgr.generate_injury(pid, PlayerInjury.MEDIUM_INJURY, datetime.date.today())
        assert mgr.is_player_injured(pid) is True


# ═══════════════════════════════════════════════════════════════════════════
# 6. Career & Manager
# ═══════════════════════════════════════════════════════════════════════════


class TestCareerManager:

    def test_add_trophy_increases_reputation(self):
        cm = CareerManager()
        initial_rep = cm.reputation
        cm.add_trophy("League", "2025/26", "TestFC", datetime.date.today())
        assert cm.reputation > initial_rep

    def test_record_match_result_updates_stats(self):
        cm = CareerManager()
        cm.start_job("TestFC", datetime.date.today())
        cm.record_match_result(won=True, drawn=False)
        cm.record_match_result(won=False, drawn=True)
        cm.record_match_result(won=False, drawn=False)
        assert cm.current_job.matches == 3
        assert cm.current_job.wins == 1
        assert cm.current_job.draws == 1
        assert cm.current_job.losses == 1

    def test_get_win_rate(self):
        cm = CareerManager()
        cm.start_job("TestFC", datetime.date.today())
        for _ in range(3):
            cm.record_match_result(won=True, drawn=False)
        cm.record_match_result(won=False, drawn=False)
        # 3 wins / 4 matches = 75%
        assert cm.get_win_rate() == pytest.approx(75.0)

    def test_get_win_rate_no_matches(self):
        cm = CareerManager()
        assert cm.get_win_rate() == 0.0


class TestManagerSerialization:

    def test_manager_round_trip(self):
        mgr = Manager(
            manager_id=uuid.uuid4(),
            first_name="Jose",
            last_name="Test",
            birth_date=datetime.date(1970, 5, 20),
            tactical_ability=15,
            man_management=12,
            youth_development=8,
            discipline=14,
            motivation=16,
        )
        mgr.career.start_job("TestFC", datetime.date(2024, 7, 1))
        data = mgr.serialize()
        restored = Manager.get_from_dict(data)
        assert restored.first_name == "Jose"
        assert restored.last_name == "Test"
        assert restored.tactical_ability == 15
        assert restored.career.current_job.club_name == "TestFC"


# ═══════════════════════════════════════════════════════════════════════════
# 7. Finances
# ═══════════════════════════════════════════════════════════════════════════


class TestFinances:

    def test_season_budget_tracking(self):
        budget = SeasonBudget(transfer_budget=10_000_000, wage_budget=5_000_000)
        budget.spend_transfer(3_000_000)
        assert budget.transfer_remaining == 7_000_000
        assert budget.can_afford_transfer(7_000_000)
        assert not budget.can_afford_transfer(8_000_000)

    def test_matchday_revenue(self):
        fm = FinanceManager(balance=0.0)
        revenue = fm.calculate_matchday_revenue(attendance=20_000, ticket_price=30.0)
        assert revenue == 600_000.0
        assert fm.balance == 600_000.0

    def test_tv_revenue_varies_by_position(self):
        fm1 = FinanceManager(balance=0.0)
        fm2 = FinanceManager(balance=0.0)
        rev_first = fm1.calculate_tv_revenue(league_position=1, total_clubs=20)
        rev_last = fm2.calculate_tv_revenue(league_position=20, total_clubs=20)
        assert rev_first > rev_last

    def test_get_season_report_categorizes(self):
        fm = FinanceManager(balance=1_000_000)
        fm.set_season_budget(5_000_000, 2_000_000)
        fm.calculate_matchday_revenue(10_000)
        fm.pay_weekly_wages(50_000)
        report = fm.get_season_report()
        assert "income_by_type" in report
        assert "expense_by_type" in report
        assert RevenueType.TICKET_SALES.value in report["income_by_type"]
        assert ExpenseType.WAGES.value in report["expense_by_type"]

    def test_sponsorship_deal_adds_income(self):
        fm = FinanceManager(balance=0.0)
        deal = SponsorshipDeal(
            sponsor_name="TestCorp",
            annual_amount=2_000_000,
            start_date=datetime.datetime(2025, 1, 1),
            end_date=datetime.datetime(2026, 12, 31),
        )
        fm.add_sponsorship(deal)
        assert fm.balance == 2_000_000
        assert len(fm.sponsorship_deals) == 1


# ═══════════════════════════════════════════════════════════════════════════
# 8. Roster
# ═══════════════════════════════════════════════════════════════════════════


class TestRoster:

    def test_auto_select_best_picks_11_starters(self):
        squad = _make_squad(20)
        rm = RosterManager(squad=squad, formation_str="4-4-2")
        rm.auto_select_best()
        assert len(rm.starting_eleven) == 11

    def test_auto_select_best_assigns_bench(self):
        squad = _make_squad(20)
        rm = RosterManager(squad=squad, formation_str="4-4-2")
        rm.auto_select_best()
        assert len(rm.bench) > 0
        assert len(rm.bench) <= 7

    def test_swap_players_starter_and_bench(self):
        squad = _make_squad(20)
        rm = RosterManager(squad=squad, formation_str="4-4-2")
        rm.auto_select_best()
        starter = rm.starting_eleven[0]
        benched = rm.bench[0]
        rm.swap_players(starter, benched)
        assert benched in rm.starting_eleven
        assert starter in rm.bench

    def test_validate_lineup_detects_incomplete(self):
        squad = _make_squad(20)
        rm = RosterManager(squad=squad, formation_str="4-4-2")
        # No players assigned yet
        valid, reason = rm.validate_lineup()
        assert valid is False

    def test_validate_lineup_ok_after_auto_select(self):
        squad = _make_squad(20)
        rm = RosterManager(squad=squad, formation_str="4-4-2")
        rm.auto_select_best()
        valid, reason = rm.validate_lineup()
        assert valid is True
        assert reason == "OK"

    def test_validate_lineup_detects_injured_starter(self):
        squad = _make_squad(20)
        rm = RosterManager(squad=squad, formation_str="4-4-2")
        rm.auto_select_best()
        # Injure the first starter
        first_starter_idx = rm.starting_eleven[0]
        squad[first_starter_idx]["injury_type"] = 2  # LIGHT_INJURY
        valid, reason = rm.validate_lineup()
        assert valid is False
        assert "injured" in reason.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 9. Save / Load
# ═══════════════════════════════════════════════════════════════════════════


class TestGameState:

    def test_serialization_round_trip(self):
        gs = GameState(
            manager_name="Test Manager",
            club_id=12345,
            season=1,
            current_date=datetime.date(2025, 8, 1),
            league_data={"name": "Premier"},
            clubs_data=[{"id": 1, "name": "FC Test"}],
            players_data=[{"id": 100}],
        )
        data = gs.to_dict()
        restored = GameState.from_dict(data)
        assert restored.manager_name == "Test Manager"
        assert restored.club_id == 12345
        assert restored.current_date == datetime.date(2025, 8, 1)
        assert restored.league_data["name"] == "Premier"

    def test_save_and_load(self, tmp_path, settings):
        settings.save = tmp_path / "saves"
        sm = SaveManager(settings)
        gs = GameState(
            manager_name="Save Test",
            club_id=999,
            season=2,
            current_date=datetime.date(2025, 9, 15),
        )
        saved_path = sm.save_game(gs, "test_slot")
        assert saved_path.exists()
        loaded = sm.load_game("test_slot")
        assert loaded.manager_name == "Save Test"
        assert loaded.season == 2

    def test_load_nonexistent_raises(self, tmp_path, settings):
        settings.save = tmp_path / "saves"
        sm = SaveManager(settings)
        with pytest.raises(FileNotFoundError):
            sm.load_game("nonexistent")


# ═══════════════════════════════════════════════════════════════════════════
# 10. Commentary
# ═══════════════════════════════════════════════════════════════════════════


class TestCommentary:

    def test_generate_returns_nonempty_for_known_events(self):
        cg = CommentaryGenerator()
        result = cg.generate(
            EventType.SHOT, EventOutcome.GOAL,
            player="Ronaldo", team="Portugal",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_returns_empty_for_unknown_pair(self):
        cg = CommentaryGenerator()
        # DRIBBLE + GOAL is not a defined template pair
        result = cg.generate(EventType.DRIBBLE, EventOutcome.GOAL)
        assert result == ""

    def test_placeholder_replacement(self):
        cg = CommentaryGenerator()
        result = cg.generate(
            EventType.SHOT, EventOutcome.GOAL,
            player="Messi", team="Argentina",
        )
        assert "Messi" in result

    def test_kickoff_commentary(self):
        cg = CommentaryGenerator()
        text = cg.generate_kickoff("Brazil")
        assert "Brazil" in text

    def test_halftime_commentary(self):
        cg = CommentaryGenerator()
        text = cg.generate_halftime("TeamA", "TeamB", 2, 1)
        assert "TeamA" in text
        assert "TeamB" in text

    def test_substitution_commentary(self):
        cg = CommentaryGenerator()
        text = cg.generate_substitution("OldPlayer", "NewPlayer", "TestFC")
        assert "OldPlayer" in text
        assert "NewPlayer" in text


# ═══════════════════════════════════════════════════════════════════════════
# 11. Interactions
# ═══════════════════════════════════════════════════════════════════════════


class TestInteractions:

    def test_press_conference_generates_questions(self):
        im = InteractionManager()
        questions = im.conduct_press_conference("pre_match", num_questions=4)
        assert len(questions) >= 3
        assert len(questions) <= 5
        for q in questions:
            assert isinstance(q, PressQuestion)
            assert len(q.options) > 0

    def test_player_interaction_returns_response(self):
        im = InteractionManager()
        result = im.talk_to_player("John Doe", TalkType.PRAISE, player_form=8.0)
        assert "response_text" in result
        assert "morale_change" in result
        assert "John Doe" in result["response_text"]

    def test_team_talk_returns_response(self):
        im = InteractionManager()
        result = im.give_team_talk(TeamTalkType.MOTIVATE, context="halftime_losing")
        assert "response_text" in result
        assert isinstance(result["morale_change"], int)

    def test_interaction_history_tracked(self):
        im = InteractionManager()
        im.conduct_press_conference("general")
        im.talk_to_player("Test", TalkType.ENCOURAGE)
        im.give_team_talk(TeamTalkType.FOCUS)
        assert len(im.interaction_history) == 3


# ═══════════════════════════════════════════════════════════════════════════
# 12. Mod Support
# ═══════════════════════════════════════════════════════════════════════════


class TestModSupport:

    def test_validate_mod_accepts_valid(self):
        mod = {
            "name": "Test Mod",
            "version": "1.0.0",
            "type": "database",
            "data": {"clubs": [], "players": []},
        }
        valid, msg = ModLoader.validate_mod(mod)
        assert valid is True
        assert msg == "OK"

    def test_validate_mod_rejects_missing_name(self):
        mod = {"version": "1.0.0", "type": "database"}
        valid, msg = ModLoader.validate_mod(mod)
        assert valid is False
        assert "name" in msg

    def test_validate_mod_rejects_invalid_type(self):
        mod = {"name": "Bad", "version": "1.0.0", "type": "invalid_type"}
        valid, msg = ModLoader.validate_mod(mod)
        assert valid is False
        assert "invalid_type" in msg.lower() or "Invalid" in msg

    def test_validate_mod_rejects_non_dict(self):
        valid, msg = ModLoader.validate_mod("not a dict")
        assert valid is False

    def test_get_mod_template_structure(self):
        template = ModLoader.get_mod_template()
        assert "name" in template
        assert "version" in template
        assert "type" in template
        assert "data" in template
        assert isinstance(template["data"], dict)
        # Verify it is a deep copy
        template["name"] = "Modified"
        assert MOD_TEMPLATE["name"] != "Modified"
