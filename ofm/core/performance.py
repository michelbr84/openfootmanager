#      Openfoot Manager - A free and open source soccer management simulation
#      Copyright (C) 2020-2025  Pedrenrique G. Guimaraes
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
import time
from typing import Generator


class PerformanceMonitor:
    """Tracks operation timings for profiling and performance analysis."""

    def __init__(self):
        self.timings: dict[str, list[float]] = {}

    def start_timer(self, operation: str) -> float:
        """Start timing an operation. Returns the start time."""
        start = time.perf_counter()
        if operation not in self.timings:
            self.timings[operation] = []
        return start

    def end_timer(self, operation: str, start_time: float) -> None:
        """Record elapsed time for an operation."""
        elapsed = time.perf_counter() - start_time
        if operation not in self.timings:
            self.timings[operation] = []
        self.timings[operation].append(elapsed)

    def get_average(self, operation: str) -> float:
        """Get the average time for a given operation."""
        times = self.timings.get(operation, [])
        if not times:
            return 0.0
        return sum(times) / len(times)

    def get_report(self) -> dict:
        """Get a full report of all tracked operations with avg/min/max times."""
        report = {}
        for operation, times in self.timings.items():
            if times:
                report[operation] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times),
                }
            else:
                report[operation] = {
                    "avg": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "count": 0,
                }
        return report


class CachedDatabase:
    """Wraps a database instance with time-based caching to reduce redundant loads."""

    def __init__(self, db):
        self._db = db
        self._cache: dict = {}
        self._cache_age: dict[str, float] = {}
        self._max_age: float = 30.0  # seconds before cache expires

    def _is_fresh(self, key: str) -> bool:
        """Check if a cached entry is still within its max age."""
        if key not in self._cache_age:
            return False
        return (time.time() - self._cache_age[key]) < self._max_age

    def load_clubs(self, use_cache: bool = True):
        """Load clubs, returning cached data if fresh."""
        key = "clubs"
        if use_cache and key in self._cache and self._is_fresh(key):
            return self._cache[key]

        data = self._db.load_clubs() if hasattr(self._db, "load_clubs") else []
        self._cache[key] = data
        self._cache_age[key] = time.time()
        return data

    def load_players(self, use_cache: bool = True):
        """Load players, returning cached data if fresh."""
        key = "players"
        if use_cache and key in self._cache and self._is_fresh(key):
            return self._cache[key]

        data = self._db.load_players() if hasattr(self._db, "load_players") else []
        self._cache[key] = data
        self._cache_age[key] = time.time()
        return data

    def invalidate_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._cache_age.clear()

    def invalidate(self, key: str) -> None:
        """Clear a specific cache entry."""
        self._cache.pop(key, None)
        self._cache_age.pop(key, None)


def batch_generate_players(
    settings, total: int, batch_size: int = 100
) -> Generator[list[dict], None, None]:
    """Generate players in batches to avoid memory spikes.

    Yields lists of player dicts, each up to batch_size in length.

    Args:
        settings: The game settings object (provides paths/config for generation).
        total: Total number of players to generate.
        batch_size: Maximum number of players per batch.

    Yields:
        A list of player dicts for each batch.
    """
    import random

    generated = 0
    while generated < total:
        current_batch_size = min(batch_size, total - generated)
        batch = []
        for _ in range(current_batch_size):
            player = {
                "id": generated,
                "overall": random.randint(40, 99),
                "potential": random.randint(50, 99),
                "age": random.randint(16, 38),
                "position": random.choice(
                    ["GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST"]
                ),
                "stamina": random.uniform(0.5, 1.0),
                "fitness": random.uniform(0.5, 1.0),
            }
            batch.append(player)
            generated += 1
        yield batch
