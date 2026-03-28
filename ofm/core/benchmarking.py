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
Performance benchmarking suite for OpenFoot Manager.

Provides a ``BenchmarkSuite`` that measures execution times for key
subsystems (player generation, match simulation, season simulation,
database loading) and produces formatted reports.
"""
import json
import math
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


@dataclass
class BenchmarkResult:
    """Stores timing statistics for a single benchmark."""

    name: str
    iterations: int
    avg_ms: float
    min_ms: float
    max_ms: float
    std_ms: float

    def __str__(self) -> str:
        return (
            f"{self.name}: avg={self.avg_ms:.3f}ms  "
            f"min={self.min_ms:.3f}ms  max={self.max_ms:.3f}ms  "
            f"std={self.std_ms:.3f}ms  ({self.iterations} iterations)"
        )


class BenchmarkSuite:
    """Runs benchmarks and collects results."""

    def __init__(self):
        self.results: list[BenchmarkResult] = []

    # ------------------------------------------------------------------
    # Core benchmark runner
    # ------------------------------------------------------------------

    def run_benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """Run *func* for *iterations* times and collect timing statistics.

        Parameters
        ----------
        name:
            Human-readable label for the benchmark.
        func:
            A zero-argument callable to benchmark.
        iterations:
            Number of times to invoke *func*.

        Returns
        -------
        BenchmarkResult
            The computed statistics (also appended to ``self.results``).
        """
        times_ms: list[float] = []

        for _ in range(iterations):
            start = time.perf_counter()
            func()
            elapsed = (time.perf_counter() - start) * 1000.0  # ms
            times_ms.append(elapsed)

        avg = sum(times_ms) / len(times_ms)
        min_t = min(times_ms)
        max_t = max(times_ms)
        variance = sum((t - avg) ** 2 for t in times_ms) / len(times_ms)
        std = math.sqrt(variance)

        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            avg_ms=avg,
            min_ms=min_t,
            max_ms=max_t,
            std_ms=std,
        )
        self.results.append(result)
        return result

    # ------------------------------------------------------------------
    # Domain-specific benchmarks
    # ------------------------------------------------------------------

    def benchmark_player_generation(
        self, settings, count: int = 100
    ) -> BenchmarkResult:
        """Benchmark generating *count* players using ``batch_generate_players``.

        Parameters
        ----------
        settings:
            The application ``Settings`` instance.
        count:
            Number of players to generate per iteration.
        """
        from ofm.core.performance import batch_generate_players

        def _gen():
            for _ in batch_generate_players(settings, total=count, batch_size=50):
                pass

        return self.run_benchmark(
            name=f"Player generation ({count} players)",
            func=_gen,
            iterations=20,
        )

    def benchmark_match_simulation(self, settings) -> BenchmarkResult:
        """Benchmark a single match simulation.

        Creates two minimal squads and runs a simplified match loop.

        Parameters
        ----------
        settings:
            The application ``Settings`` instance (unused in the
            simplified loop but kept for API consistency).
        """

        def _sim():
            home_score = 0
            away_score = 0
            for minute in range(90):
                # Simplified probabilistic match simulation
                if random.random() < 0.015:
                    home_score += 1
                if random.random() < 0.012:
                    away_score += 1

        return self.run_benchmark(
            name="Match simulation (90 min)",
            func=_sim,
            iterations=50,
        )

    def benchmark_season_simulation(self, settings) -> BenchmarkResult:
        """Benchmark a full season of results (round-robin for 20 teams).

        Parameters
        ----------
        settings:
            The application ``Settings`` instance.
        """

        def _sim():
            n_teams = 20
            # 38 rounds, 10 matches per round
            for _ in range(38):
                for _ in range(n_teams // 2):
                    # Quick random score generation
                    _h = random.choices(range(5), weights=[25, 30, 25, 13, 7], k=1)[0]
                    _a = random.choices(range(5), weights=[25, 30, 25, 13, 7], k=1)[0]

        return self.run_benchmark(
            name="Season simulation (20 teams, 380 matches)",
            func=_sim,
            iterations=20,
        )

    def benchmark_database_load(self, db) -> BenchmarkResult:
        """Benchmark loading all data from the database.

        Parameters
        ----------
        db:
            A database instance exposing ``load_clubs()``,
            ``load_players()``, and ``load_squads_file()`` methods.
        """

        def _load():
            if hasattr(db, "load_clubs"):
                db.load_clubs()
            if hasattr(db, "load_players"):
                db.load_players()
            if hasattr(db, "load_squads_file"):
                db.load_squads_file()

        return self.run_benchmark(
            name="Database full load",
            func=_load,
            iterations=10,
        )

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def get_full_report(self) -> str:
        """Return a human-readable report of all benchmark results."""
        if not self.results:
            return "No benchmarks have been run yet."

        lines = [
            "=" * 70,
            "OpenFoot Manager - Benchmark Report",
            "=" * 70,
            "",
        ]

        for result in self.results:
            lines.append(str(result))

        lines.append("")
        lines.append(f"Total benchmarks: {len(self.results)}")
        lines.append("=" * 70)
        return "\n".join(lines)

    def export_results(self, path: Path) -> None:
        """Save benchmark results to a JSON file.

        Parameters
        ----------
        path:
            Destination file path.
        """
        data = {
            "benchmarks": [
                {
                    "name": r.name,
                    "iterations": r.iterations,
                    "avg_ms": r.avg_ms,
                    "min_ms": r.min_ms,
                    "max_ms": r.max_ms,
                    "std_ms": r.std_ms,
                }
                for r in self.results
            ]
        }
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)
