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
from typing import Optional

from .formation import FORMATION_STRINGS
from .positions import Positions


class RosterError(Exception):
    pass


class RosterManager:
    """Manages squad lineup selection, formation assignment, and captain designation.

    Works with player dicts (as serialized by Player.serialize()) rather than
    Player objects so that roster state can be persisted and restored cheaply.
    Each player dict is expected to contain at least:
        - "id": int
        - "short_name": str
        - "positions": list[int]   (Positions enum values)
        - "attributes": nested dict used by PlayerAttributes
        - "fitness": float
        - "injury_type": int
    """

    def __init__(
        self,
        squad: Optional[list[dict]] = None,
        formation_str: str = "4-4-2",
        starting_eleven: Optional[list[int]] = None,
        bench: Optional[list[int]] = None,
        captain_index: Optional[int] = None,
    ):
        self.squad: list[dict] = squad if squad is not None else []
        self.formation_str: str = formation_str
        self.starting_eleven: list[int] = starting_eleven if starting_eleven is not None else []
        self.bench: list[int] = bench if bench is not None else []
        self.captain_index: Optional[int] = captain_index

        # Validate formation on construction if one was given
        if self.formation_str and self.formation_str not in FORMATION_STRINGS:
            raise RosterError(
                f"Invalid formation '{self.formation_str}'. "
                f"Valid formations: {FORMATION_STRINGS}"
            )

    # ------------------------------------------------------------------
    # Formation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_formation(formation_str: str) -> tuple[int, int, int]:
        """Returns (defenders, midfielders, forwards) from a formation string."""
        parts = formation_str.split("-")
        if len(parts) != 3:
            raise RosterError(f"Formation string must have 3 parts: '{formation_str}'")
        return int(parts[0]), int(parts[1]), int(parts[2])

    def _formation_slots(self) -> dict[str, int]:
        """Returns the number of slots per position group for the current formation.

        Always includes exactly 1 GK slot.
        """
        df, mf, fw = self._parse_formation(self.formation_str)
        return {"GK": 1, "DF": df, "MF": mf, "FW": fw}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_formation(self, formation_str: str) -> None:
        """Validates and sets a new formation, clearing the current lineup."""
        if formation_str not in FORMATION_STRINGS:
            raise RosterError(
                f"Invalid formation '{formation_str}'. "
                f"Valid formations: {FORMATION_STRINGS}"
            )
        self.formation_str = formation_str
        # Reset lineup when formation changes so stale slot assignments
        # don't carry over to a formation with different slot counts.
        self.starting_eleven = []
        self.bench = []

    def assign_starter(self, squad_index: int, position_slot: int) -> None:
        """Places a squad player into the starting 11 at the given slot (0-10).

        *squad_index* is an index into ``self.squad``.
        *position_slot* is a 0-based slot in the starting 11 (0 = GK, then
        defenders, midfielders, forwards in order).
        """
        if squad_index < 0 or squad_index >= len(self.squad):
            raise RosterError(f"Invalid squad index {squad_index}")
        if position_slot < 0 or position_slot > 10:
            raise RosterError(f"Position slot must be 0-10, got {position_slot}")

        # Remove the player from bench if already there
        if squad_index in self.bench:
            self.bench.remove(squad_index)

        # Remove any existing player in that slot
        if position_slot < len(self.starting_eleven):
            self.starting_eleven[position_slot] = squad_index
        else:
            # Pad with -1 for any intermediate unfilled slots
            while len(self.starting_eleven) < position_slot:
                self.starting_eleven.append(-1)
            self.starting_eleven.append(squad_index)

    def assign_bench(self, squad_index: int) -> None:
        """Places a squad player on the bench."""
        if squad_index < 0 or squad_index >= len(self.squad):
            raise RosterError(f"Invalid squad index {squad_index}")
        if squad_index in self.bench:
            return  # already on bench
        # Remove from starting 11 if present
        if squad_index in self.starting_eleven:
            idx = self.starting_eleven.index(squad_index)
            self.starting_eleven[idx] = -1
        if squad_index not in self.bench:
            self.bench.append(squad_index)

    def swap_players(self, index_a: int, index_b: int) -> None:
        """Swaps two players by their squad indices.

        Handles starter<->starter, starter<->bench, and bench<->bench swaps.
        """
        if index_a < 0 or index_a >= len(self.squad):
            raise RosterError(f"Invalid squad index {index_a}")
        if index_b < 0 or index_b >= len(self.squad):
            raise RosterError(f"Invalid squad index {index_b}")

        a_in_starting = index_a in self.starting_eleven
        b_in_starting = index_b in self.starting_eleven
        a_in_bench = index_a in self.bench
        b_in_bench = index_b in self.bench

        if a_in_starting and b_in_starting:
            # Swap within starting 11
            pos_a = self.starting_eleven.index(index_a)
            pos_b = self.starting_eleven.index(index_b)
            self.starting_eleven[pos_a] = index_b
            self.starting_eleven[pos_b] = index_a

        elif a_in_starting and b_in_bench:
            pos_a = self.starting_eleven.index(index_a)
            bench_pos = self.bench.index(index_b)
            self.starting_eleven[pos_a] = index_b
            self.bench[bench_pos] = index_a

        elif a_in_bench and b_in_starting:
            pos_b = self.starting_eleven.index(index_b)
            bench_pos = self.bench.index(index_a)
            self.starting_eleven[pos_b] = index_a
            self.bench[bench_pos] = index_b

        elif a_in_bench and b_in_bench:
            pos_a = self.bench.index(index_a)
            pos_b = self.bench.index(index_b)
            self.bench[pos_a] = index_b
            self.bench[pos_b] = index_a

        else:
            raise RosterError(
                "Both players must be in the starting eleven or on the bench to swap."
            )

        # Update captain if one of the swapped players was captain
        if self.captain_index == index_a:
            self.captain_index = index_a  # captain follows the player, not the slot
        elif self.captain_index == index_b:
            self.captain_index = index_b

    def set_captain(self, squad_index: int) -> None:
        """Assigns the captain armband to a squad player."""
        if squad_index < 0 or squad_index >= len(self.squad):
            raise RosterError(f"Invalid squad index {squad_index}")
        self.captain_index = squad_index

    # ------------------------------------------------------------------
    # Auto-selection
    # ------------------------------------------------------------------

    @staticmethod
    def _player_overall(player_dict: dict, position: Positions) -> float:
        """Computes a rough overall rating for a player dict at a given position.

        This mirrors the weighted formula in PlayerAttributes.get_overall but
        operates on the raw dict so we don't need to construct full objects.
        """
        attrs = player_dict.get("attributes", {})

        def _avg(group: dict) -> float:
            vals = list(group.values())
            return sum(vals) / len(vals) if vals else 0.0

        off = _avg(attrs.get("offensive", {}))
        phy = _avg(attrs.get("physical", {}))
        defe = _avg(attrs.get("defensive", {}))
        intel = _avg(attrs.get("intelligence", {}))
        gk = _avg(attrs.get("gk", {}))

        if position == Positions.GK:
            return (gk * 3 + defe * 2 + phy + intel) / 7
        elif position == Positions.DF:
            return (defe * 3 + phy * 2 + intel + off) / 7
        elif position == Positions.MF:
            return (defe + phy * 2 + intel * 3 + off) / 7
        elif position == Positions.FW:
            return (defe + phy + intel * 2 + off * 3) / 7
        return 0.0

    @staticmethod
    def _best_position(player_dict: dict) -> Positions:
        """Returns the player's primary position from the dict."""
        positions = player_dict.get("positions", [])
        if positions:
            return Positions(positions[0])
        return Positions.MF  # fallback

    def _is_available(self, player_dict: dict) -> bool:
        """Check if a player is available (not injured)."""
        from .injury import PlayerInjury

        injury_val = player_dict.get("injury_type", 0)
        return injury_val == PlayerInjury.NO_INJURY.value

    def auto_select_best(self) -> None:
        """Auto-picks the best 11 based on overall ratings for the current formation.

        Remaining available players are placed on the bench (up to 7 subs,
        which is a common modern matchday bench size).
        """
        if not self.squad:
            raise RosterError("Cannot auto-select: squad is empty.")

        df_needed, mf_needed, fw_needed = self._parse_formation(self.formation_str)
        slots_needed = {
            Positions.GK: 1,
            Positions.DF: df_needed,
            Positions.MF: mf_needed,
            Positions.FW: fw_needed,
        }

        # Build list of (squad_index, player_dict) for available players
        available = [
            (i, p)
            for i, p in enumerate(self.squad)
            if self._is_available(p)
        ]

        selected: list[int] = []  # squad indices for starters, ordered by slot
        used: set[int] = set()

        # For each position group, pick the best available players whose
        # primary position matches first, then fill remaining slots with
        # the best remaining players rated at that position.
        for position in [Positions.GK, Positions.DF, Positions.MF, Positions.FW]:
            needed = slots_needed[position]

            # Prefer players whose primary position matches
            candidates = [
                (idx, p) for idx, p in available if idx not in used
            ]
            # Sort: primary-position players first (descending overall), then others
            candidates.sort(
                key=lambda t: (
                    self._best_position(t[1]) == position,
                    self._player_overall(t[1], position),
                ),
                reverse=True,
            )

            picked = 0
            for idx, p in candidates:
                if picked >= needed:
                    break
                selected.append(idx)
                used.add(idx)
                picked += 1

        self.starting_eleven = selected

        # Fill bench with remaining best players (up to 7)
        remaining = [
            (idx, p) for idx, p in available if idx not in used
        ]
        remaining.sort(
            key=lambda t: self._player_overall(
                t[1], self._best_position(t[1])
            ),
            reverse=True,
        )
        max_bench = 7
        self.bench = [idx for idx, _ in remaining[:max_bench]]

        # Auto-assign captain: highest overall among starters
        if self.starting_eleven:
            best_starter = max(
                self.starting_eleven,
                key=lambda idx: self._player_overall(
                    self.squad[idx],
                    self._best_position(self.squad[idx]),
                ),
            )
            self.captain_index = best_starter

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_lineup(self) -> dict:
        """Returns a dict describing the current lineup."""
        starters = []
        for idx in self.starting_eleven:
            if 0 <= idx < len(self.squad):
                starters.append(self.squad[idx])
            else:
                starters.append(None)

        bench_players = []
        for idx in self.bench:
            if 0 <= idx < len(self.squad):
                bench_players.append(self.squad[idx])

        return {
            "starters": starters,
            "bench": bench_players,
            "formation": self.formation_str,
            "captain_index": self.captain_index,
        }

    def validate_lineup(self) -> tuple[bool, str]:
        """Checks whether the current lineup is valid.

        Returns (True, "OK") if valid, or (False, reason) otherwise.
        """
        # Must have exactly 11 starters
        valid_starters = [i for i in self.starting_eleven if i >= 0]
        if len(valid_starters) != 11:
            return (
                False,
                f"Starting eleven has {len(valid_starters)} players, need exactly 11.",
            )

        # No duplicate players across starters and bench
        all_selected = valid_starters + self.bench
        if len(all_selected) != len(set(all_selected)):
            return False, "Duplicate player detected in lineup."

        # Check all indices are within squad bounds
        for idx in all_selected:
            if idx < 0 or idx >= len(self.squad):
                return False, f"Squad index {idx} is out of bounds."

        # Check formation slot counts match
        df_needed, mf_needed, fw_needed = self._parse_formation(self.formation_str)
        total_needed = 1 + df_needed + mf_needed + fw_needed
        if total_needed != 11:
            return (
                False,
                f"Formation '{self.formation_str}' requires {total_needed} outfield slots (expected 11).",
            )

        # Check no injured players in starters
        for idx in valid_starters:
            if not self._is_available(self.squad[idx]):
                name = self.squad[idx].get("short_name", f"Player #{idx}")
                return False, f"{name} is injured and cannot start."

        return True, "OK"

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def serialize(self) -> dict:
        """Serializes roster state to a dict for persistence."""
        return {
            "formation_str": self.formation_str,
            "starting_eleven": list(self.starting_eleven),
            "bench": list(self.bench),
            "captain_index": self.captain_index,
        }

    @classmethod
    def get_from_dict(cls, data: dict, squad: list[dict]) -> "RosterManager":
        """Restores a RosterManager from serialized data and the squad player dicts."""
        return cls(
            squad=squad,
            formation_str=data.get("formation_str", "4-4-2"),
            starting_eleven=data.get("starting_eleven", []),
            bench=data.get("bench", []),
            captain_index=data.get("captain_index"),
        )
