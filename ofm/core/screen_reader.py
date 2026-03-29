"""Screen reader support for key information.

Provides text-based descriptions of game state that can be read
by screen readers or used for text-only output.
"""


class ScreenReader:
    """Generates accessible text descriptions of game state."""

    @staticmethod
    def describe_dashboard(career_engine) -> str:
        """Text summary of career dashboard for screen readers."""
        if not career_engine:
            return "No active career."
        lines = []
        lines.append("Career Dashboard")
        lines.append(f"Date: {career_engine.current_date}")
        lines.append(f"Season: {career_engine.season_number}")
        # Add standings summary
        standings = career_engine.get_standings()
        if standings:
            for i, s in enumerate(standings[:5], 1):
                lines.append(
                    f"{i}. {s.get('name', '?')} - {s.get('points', 0)} pts"
                )
        return "\n".join(lines)

    @staticmethod
    def describe_match(home, away, home_score, away_score, minute) -> str:
        """Text summary of a live match for screen readers."""
        return f"Match: {home} {home_score} - {away_score} {away}, Minute {minute}"

    @staticmethod
    def describe_player(player_dict) -> str:
        """Text summary of a player for screen readers."""
        name = player_dict.get("short_name", "Unknown")
        pos_map = {1: "Goalkeeper", 2: "Defender", 3: "Midfielder", 4: "Forward"}
        positions = player_dict.get("positions", [])
        pos_str = ", ".join(pos_map.get(p, "Unknown") for p in positions)
        nationality = player_dict.get("nationality", "Unknown")
        return f"{name}, {pos_str}, from {nationality}"

    @staticmethod
    def describe_standings(standings) -> str:
        """Text summary of league standings for screen readers."""
        lines = ["League Standings:"]
        for i, s in enumerate(standings, 1):
            lines.append(
                f"Position {i}: {s.get('name', '?')}, "
                f"{s.get('points', 0)} points, "
                f"{s.get('played', 0)} games played"
            )
        return "\n".join(lines)

    @staticmethod
    def describe_formation(formation_str, players) -> str:
        """Text summary of team formation for screen readers."""
        lines = [f"Formation: {formation_str}"]
        for p in players:
            lines.append(f"  {p}")
        return "\n".join(lines)

    @staticmethod
    def describe_finances(balance, transactions) -> str:
        """Text summary of club finances for screen readers."""
        lines = [f"Club Balance: ${balance:,.2f}"]
        if transactions:
            lines.append(f"Recent transactions: {len(transactions)}")
        return "\n".join(lines)
