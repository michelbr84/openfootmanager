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
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Optional


class DashboardData:
    """Provides aggregated data for the manager dashboard view.

    This class gathers information from the career engine and assembles
    a dictionary suitable for display in the UI layer.
    """

    def get_dashboard(self, career_engine) -> dict:
        """Build a complete dashboard data dictionary.

        Args:
            career_engine: The career/game engine object that exposes the
                player's club, league, finances, and schedule data.

        Returns:
            Dict containing all dashboard sections: fixtures, results,
            league standing, finances, injuries, news, and squad info.
        """
        dashboard = {
            "upcoming_fixtures": self._get_upcoming_fixtures(career_engine, count=3),
            "recent_results": self._get_recent_results(career_engine, count=3),
            "league_position": self._get_league_position(career_engine),
            "points": self._get_points(career_engine),
            "form_guide": self._get_form_guide(career_engine, count=5),
            "finances_summary": self._get_finances_summary(career_engine),
            "injury_list": self._get_injury_list(career_engine),
            "next_match_date": self._get_next_match_date(career_engine),
            "news_feed": self._get_news_feed(career_engine, count=5),
            "squad_size": self._get_squad_size(career_engine),
            "avg_age": self._get_avg_age(career_engine),
            "avg_overall": self._get_avg_overall(career_engine),
        }
        return dashboard

    def _get_upcoming_fixtures(self, career_engine, count: int) -> list[dict]:
        """Get the next N upcoming fixtures for the player's club."""
        fixtures = []
        if hasattr(career_engine, "upcoming_fixtures"):
            raw = career_engine.upcoming_fixtures
            for fixture in raw[:count]:
                fixtures.append(self._serialize_fixture(fixture))
        return fixtures

    def _get_recent_results(self, career_engine, count: int) -> list[dict]:
        """Get the last N match results for the player's club."""
        results = []
        if hasattr(career_engine, "recent_results"):
            raw = career_engine.recent_results
            for result in raw[-count:]:
                results.append(self._serialize_result(result))
        return results

    def _get_league_position(self, career_engine) -> int:
        """Get the current league position."""
        if hasattr(career_engine, "league_position"):
            return career_engine.league_position
        return 0

    def _get_points(self, career_engine) -> int:
        """Get the current league points total."""
        if hasattr(career_engine, "points"):
            return career_engine.points
        return 0

    def _get_form_guide(self, career_engine, count: int) -> str:
        """Get a form string like 'WWDLW' for the last N matches."""
        if hasattr(career_engine, "form_guide"):
            guide = career_engine.form_guide
            if isinstance(guide, FormGuide):
                return guide.get_last_n(count)
            return str(guide)[-count:]
        return ""

    def _get_finances_summary(self, career_engine) -> dict:
        """Get a summary of the club's financial state."""
        summary = {"balance": 0, "weekly_wage": 0}
        if hasattr(career_engine, "finances"):
            fin = career_engine.finances
            if hasattr(fin, "balance"):
                summary["balance"] = fin.balance
            if hasattr(fin, "weekly_wage"):
                summary["weekly_wage"] = fin.weekly_wage
        return summary

    def _get_injury_list(self, career_engine) -> list[dict]:
        """Get a list of currently injured players."""
        injuries = []
        if hasattr(career_engine, "injury_list"):
            for entry in career_engine.injury_list:
                if isinstance(entry, dict):
                    injuries.append(entry)
                else:
                    injuries.append({"player": str(entry), "days_remaining": 0})
        return injuries

    def _get_next_match_date(self, career_engine) -> Optional[str]:
        """Get the date of the next scheduled match."""
        if hasattr(career_engine, "next_match_date"):
            date = career_engine.next_match_date
            if isinstance(date, datetime):
                return date.isoformat()
            return str(date) if date else None
        return None

    def _get_news_feed(self, career_engine, count: int) -> list[dict]:
        """Get the last N news items."""
        if hasattr(career_engine, "news_feed"):
            return list(career_engine.news_feed[-count:])
        return []

    def _get_squad_size(self, career_engine) -> int:
        """Get the total number of players in the squad."""
        if hasattr(career_engine, "squad"):
            return len(career_engine.squad)
        return 0

    def _get_avg_age(self, career_engine) -> float:
        """Get the average age of the squad."""
        if hasattr(career_engine, "squad") and career_engine.squad:
            ages = []
            for player in career_engine.squad:
                age = getattr(player, "age", None)
                if age is not None:
                    ages.append(age)
            if ages:
                return round(sum(ages) / len(ages), 1)
        return 0.0

    def _get_avg_overall(self, career_engine) -> float:
        """Get the average overall rating of the squad."""
        if hasattr(career_engine, "squad") and career_engine.squad:
            overalls = []
            for player in career_engine.squad:
                ovr = getattr(player, "overall", None)
                if ovr is not None:
                    overalls.append(ovr)
            if overalls:
                return round(sum(overalls) / len(overalls), 1)
        return 0.0

    @staticmethod
    def _serialize_fixture(fixture) -> dict:
        """Convert a fixture object to a simple dict."""
        if isinstance(fixture, dict):
            return fixture
        result = {}
        for attr in ("home_team", "away_team", "date", "stadium", "fixture_id"):
            if hasattr(fixture, attr):
                val = getattr(fixture, attr)
                result[attr] = str(val)
        return result

    @staticmethod
    def _serialize_result(result) -> dict:
        """Convert a result object to a simple dict."""
        if isinstance(result, dict):
            return result
        out = {}
        for attr in ("home_team", "away_team", "home_score", "away_score", "date"):
            if hasattr(result, attr):
                val = getattr(result, attr)
                out[attr] = str(val) if not isinstance(val, (int, float)) else val
        return out


class NewsFeedGenerator:
    """Generates news headlines from templates by category.

    Each category has a list of template strings that accept keyword
    arguments via str.format().
    """

    TEMPLATES: dict[str, list[str]] = {
        "transfer": [
            "{player} signs for {club} for ${amount}",
            "{club} complete signing of {player} in ${amount} deal",
            "{player} joins {club} on a permanent transfer worth ${amount}",
            "DONE DEAL: {player} moves to {club} for ${amount}",
        ],
        "injury": [
            "{player} ruled out for {days} days with {injury}",
            "Injury blow: {player} sidelined with {injury} for {days} days",
            "{player} faces {days} days on the sidelines after suffering {injury}",
        ],
        "result": [
            "{home} {h_score}-{a_score} {away}",
            "Full time: {home} {h_score} - {a_score} {away}",
            "{home} beat {away} {h_score}-{a_score}" if True else "",
        ],
        "milestone": [
            "{manager} reaches {count} games in charge",
            "Milestone: {manager} celebrates {count} matches as manager",
            "{manager} marks {count}th game at the helm",
        ],
        "youth": [
            "Promising youngster {player} promoted from academy",
            "{player} earns first-team promotion from the youth academy",
            "Academy graduate {player} joins the senior squad",
        ],
        "contract": [
            "{player} signs new {years}-year deal at {club}",
            "{club} tie down {player} with a new {years}-year contract",
            "{player} extends stay at {club} with {years}-year renewal",
        ],
    }

    def generate(self, category: str, **kwargs) -> dict:
        """Generate a news item from a template.

        Args:
            category: One of the keys in TEMPLATES (e.g., "transfer", "injury").
            **kwargs: Values to fill the template placeholders.

        Returns:
            Dict with keys: date (ISO string), headline (str), category (str).
        """
        import random

        templates = self.TEMPLATES.get(category, [])
        if not templates:
            headline = f"News: {category}"
        else:
            template = random.choice(templates)
            try:
                headline = template.format(**kwargs)
            except KeyError:
                headline = template

        return {
            "date": datetime.now().isoformat(),
            "headline": headline,
            "category": category,
        }

    def generate_transfer_rumor(self, player: str, clubs: list[str]) -> dict:
        """Generate a transfer rumor news item.

        Args:
            player: Name of the player involved.
            clubs: List of club names linked with the player.

        Returns:
            News dict with a transfer rumor headline.
        """
        import random

        rumor_templates = [
            "{player} reportedly on the radar of {clubs}",
            "Transfer rumor: {player} attracting interest from {clubs}",
            "Sources say {clubs} are monitoring {player}'s situation",
            "{player} could be set for a move with {clubs} circling",
        ]

        clubs_str = " and ".join(clubs) if len(clubs) <= 2 else ", ".join(clubs[:-1]) + f", and {clubs[-1]}"
        template = random.choice(rumor_templates)
        headline = template.format(player=player, clubs=clubs_str)

        return {
            "date": datetime.now().isoformat(),
            "headline": headline,
            "category": "transfer_rumor",
        }

    def generate_match_preview(
        self,
        home: str,
        away: str,
        league_pos_h: int,
        league_pos_a: int,
    ) -> dict:
        """Generate a match preview news item.

        Args:
            home: Home team name.
            away: Away team name.
            league_pos_h: Home team's league position.
            league_pos_a: Away team's league position.

        Returns:
            News dict with a match preview headline.
        """
        import random

        preview_templates = [
            "PREVIEW: {home} (#{h_pos}) vs {away} (#{a_pos})",
            "Match day: {home} host {away} in league clash",
            "{home} look to continue form against visiting {away}",
            "All eyes on {home} vs {away} as #{h_pos} meets #{a_pos}",
        ]

        template = random.choice(preview_templates)
        headline = template.format(
            home=home, away=away, h_pos=league_pos_h, a_pos=league_pos_a
        )

        return {
            "date": datetime.now().isoformat(),
            "headline": headline,
            "category": "match_preview",
        }


class PlayerComparison:
    """Compares two players across all attributes and provides a summary."""

    def compare(self, player_a: dict, player_b: dict) -> dict:
        """Perform a side-by-side comparison of two players.

        Args:
            player_a: Dict of player A's attributes (name, age, value,
                potential, overall, position, and individual stats).
            player_b: Dict of player B's attributes in the same format.

        Returns:
            Dict with keys:
                - player_a / player_b: The input dicts echoed back.
                - attributes: Dict of {attr: {a: val, b: val, diff: val}}.
                - overall_comparison: {a: overall_a, b: overall_b, diff: int}.
                - age_comparison: {a: age_a, b: age_b}.
                - value_comparison: {a: val_a, b: val_b}.
                - potential_comparison: {a: pot_a, b: pot_b}.
                - better_at: List of attributes where A exceeds B.
                - worse_at: List of attributes where A is less than B.
        """
        # Collect all numeric attributes for comparison
        skip_keys = {"name", "position"}
        all_keys = set(player_a.keys()) | set(player_b.keys())
        numeric_keys = sorted(
            k for k in all_keys
            if k not in skip_keys
            and (isinstance(player_a.get(k), (int, float)) or isinstance(player_b.get(k), (int, float)))
        )

        attributes = {}
        better_at = []
        worse_at = []

        for key in numeric_keys:
            val_a = player_a.get(key, 0)
            val_b = player_b.get(key, 0)
            if not isinstance(val_a, (int, float)):
                val_a = 0
            if not isinstance(val_b, (int, float)):
                val_b = 0
            diff = val_a - val_b
            attributes[key] = {"a": val_a, "b": val_b, "diff": diff}

            if diff > 0:
                better_at.append(key)
            elif diff < 0:
                worse_at.append(key)

        overall_a = player_a.get("overall", 0)
        overall_b = player_b.get("overall", 0)

        return {
            "player_a": player_a,
            "player_b": player_b,
            "attributes": attributes,
            "overall_comparison": {
                "a": overall_a,
                "b": overall_b,
                "diff": overall_a - overall_b,
            },
            "age_comparison": {
                "a": player_a.get("age", 0),
                "b": player_b.get("age", 0),
            },
            "value_comparison": {
                "a": player_a.get("value", 0),
                "b": player_b.get("value", 0),
            },
            "potential_comparison": {
                "a": player_a.get("potential", 0),
                "b": player_b.get("potential", 0),
            },
            "better_at": better_at,
            "worse_at": worse_at,
        }


class FormGuide:
    """Tracks a sequence of match results (W/D/L) and provides form analysis."""

    def __init__(self, results: Optional[list[str]] = None):
        self.results: list[str] = list(results) if results else []

    def add_result(self, won: bool, drawn: bool) -> None:
        """Record a match result.

        Args:
            won: True if the match was won.
            drawn: True if the match was drawn. Ignored if won is True.
        """
        if won:
            self.results.append("W")
        elif drawn:
            self.results.append("D")
        else:
            self.results.append("L")

    def get_last_n(self, n: int = 5) -> str:
        """Get the last N results as a string.

        Args:
            n: Number of recent results to include.

        Returns:
            String like "WWDLW" (most recent last).
        """
        return "".join(self.results[-n:])

    def get_form_points(self, n: int = 5) -> int:
        """Calculate points from the last N results.

        W = 3 points, D = 1 point, L = 0 points.

        Args:
            n: Number of recent results to evaluate.

        Returns:
            Total points from the last N matches.
        """
        recent = self.results[-n:]
        points = 0
        for r in recent:
            if r == "W":
                points += 3
            elif r == "D":
                points += 1
        return points

    def get_trend(self) -> str:
        """Analyze whether form is improving, stable, or declining.

        Compares the points of the most recent 3 matches against the
        3 matches before those. If fewer than 6 results exist, returns
        "stable".

        Returns:
            One of "improving", "stable", or "declining".
        """
        if len(self.results) < 6:
            return "stable"

        recent_3 = self.results[-3:]
        previous_3 = self.results[-6:-3]

        def _points(seq: list[str]) -> int:
            total = 0
            for r in seq:
                if r == "W":
                    total += 3
                elif r == "D":
                    total += 1
            return total

        recent_pts = _points(recent_3)
        prev_pts = _points(previous_3)

        if recent_pts > prev_pts:
            return "improving"
        elif recent_pts < prev_pts:
            return "declining"
        return "stable"

    def serialize(self) -> dict:
        """Serialize form data to a plain dict.

        Returns:
            Dict with key "results" containing the list of result strings.
        """
        return {"results": list(self.results)}

    @classmethod
    def get_from_dict(cls, data: dict) -> "FormGuide":
        """Deserialize a FormGuide from a dict.

        Args:
            data: Dict previously returned by serialize().

        Returns:
            A new FormGuide instance.
        """
        return cls(results=data.get("results", []))


class NotificationPriority(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    URGENT = auto()


@dataclass
class Notification:
    """A single notification entry."""
    date: str
    title: str
    body: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    read: bool = False

    def serialize(self) -> dict:
        return {
            "date": self.date,
            "title": self.title,
            "body": self.body,
            "priority": self.priority.name,
            "read": self.read,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Notification":
        priority = data.get("priority", "MEDIUM")
        if isinstance(priority, str):
            priority = NotificationPriority[priority]
        return cls(
            date=data["date"],
            title=data["title"],
            body=data["body"],
            priority=priority,
            read=data.get("read", False),
        )


class NotificationSystem:
    """Manages a list of notifications with priority levels and read state."""

    def __init__(self):
        self.notifications: list[Notification] = []

    def add(self, title: str, body: str, priority: NotificationPriority = NotificationPriority.MEDIUM) -> None:
        """Add a new notification.

        Args:
            title: Short title for the notification.
            body: Detailed body text.
            priority: Priority level (LOW, MEDIUM, HIGH, URGENT).
        """
        notification = Notification(
            date=datetime.now().isoformat(),
            title=title,
            body=body,
            priority=priority,
            read=False,
        )
        self.notifications.append(notification)

    def get_unread(self) -> list[Notification]:
        """Get all unread notifications, newest first.

        Returns:
            List of Notification objects where read is False.
        """
        return [n for n in reversed(self.notifications) if not n.read]

    def mark_read(self, index: int) -> None:
        """Mark a notification as read by its index in the notifications list.

        Args:
            index: The index of the notification to mark as read.
        """
        if 0 <= index < len(self.notifications):
            self.notifications[index].read = True

    def get_by_priority(self, priority: NotificationPriority) -> list[Notification]:
        """Get all notifications of a specific priority level.

        Args:
            priority: The priority level to filter by.

        Returns:
            List of matching Notification objects.
        """
        return [n for n in self.notifications if n.priority == priority]

    def clear_old(self, days: int = 30) -> None:
        """Remove notifications older than the specified number of days.

        Args:
            days: Age threshold in days. Notifications older than this
                are removed.
        """
        cutoff = datetime.now() - timedelta(days=days)
        kept = []
        for n in self.notifications:
            try:
                n_date = datetime.fromisoformat(n.date)
                if n_date >= cutoff:
                    kept.append(n)
            except (ValueError, TypeError):
                # Keep notifications with unparseable dates
                kept.append(n)
        self.notifications = kept

    def serialize(self) -> dict:
        """Serialize the notification system to a dict.

        Returns:
            Dict with key "notifications" containing serialized entries.
        """
        return {
            "notifications": [n.serialize() for n in self.notifications],
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "NotificationSystem":
        """Deserialize a NotificationSystem from a dict.

        Args:
            data: Dict previously returned by serialize().

        Returns:
            A new NotificationSystem instance with restored notifications.
        """
        system = cls()
        for entry in data.get("notifications", []):
            system.notifications.append(Notification.from_dict(entry))
        return system
