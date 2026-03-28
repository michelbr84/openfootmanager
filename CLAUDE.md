# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenFoot Manager is a free, open-source football/soccer manager game (GPLv3) built in Python 3.10+. It features an event-driven match simulation engine, comprehensive player/club domain models, and a Tkinter-based GUI. Currently in early development.

## Commands

```bash
# Install dependencies
poetry install

# Run the application
poetry run python run.py

# Run all tests
poetry run pytest

# Run a single test file
poetry run pytest ofm/tests/test_player.py

# Run a specific test
poetry run pytest ofm/tests/test_player.py::test_function_name -v

# Linting
flake8 . --config .flake8

# Formatting
poetry run black .
poetry run isort . --profile black
```

## Code Style

- **Formatter:** Black (line length governed by .flake8: max 89 chars)
- **Import sorting:** isort with Black profile (see `.isort.cfg`)
- **Linting:** flake8 with config in `.flake8` (ignores E203, E266, E501, W503, F403, F401, F405, C901; max complexity 18)
- Pre-commit hooks enforce Black, flake8, and isort automatically
- Type hints are used extensively throughout the codebase
- PEP 8 compliance required

## Architecture

### Entry Point

`run.py` → `OFM` class (`ofm/ofm.py`) which initializes Settings, DB, and OFMController, then starts the GUI mainloop.

### Core Layers

- **`ofm/core/`** — Business logic and domain models
  - **`football/`** — Domain models: `Player`, `Club`, `Formation`, `League`, `PlayerContract`, `FinanceManager`, player attributes (offensive, defensive, intelligence, physical, GK)
  - **`simulation/`** — Event-driven match engine (see below)
  - **`db/`** — JSON-based data loading (`DB` class) and generators (`PlayerGenerator`, `TeamGenerator`)
  - **`settings.py`** — YAML-based configuration, manages paths to resources

- **`ofm/ui/`** — Presentation layer (Tkinter + ttkbootstrap)
  - **`gui.py`** — Window setup with custom themes ("football", "darkfootball")
  - **`controllers/`** — MVC-style controllers; `OFMController` coordinates page navigation
  - **`pages/`** — Individual view classes (home, team selection, formation, championship, debug match, etc.)

- **`ofm/res/`** — Static resources: JSON databases (clubs, players, squads), images, name pools

### Match Simulation Engine

Event-based system in `ofm/core/simulation/`. Key concepts:

- **`LiveGame`** — Manages a single match with fixture, teams, and game state
- **`SimulationEngine`** — Drives match progression through states: `NOT_STARTED → FIRST_HALF → BREAK → SECOND_HALF → [EXTRA_TIME] → [PENALTIES] → FINISHED`
- **`GameState`** — Tracks minutes, possession, ball position, score
- **Events** (`events/` subpackage) — `SimulationEvent` base class with specific implementations: Pass, Shot, Dribble, Cross, Foul, CornerKick, FreeKick, GoalKick, PenaltyKick. Each event calculates outcomes via probability functions based on player attributes, formation, tactics, and fatigue.

### Data Model

- Domain objects use Python dataclasses with UUID-based IDs
- Serialization via `to_dict()`/`from_dict()` methods for JSON persistence
- No SQL database — all data stored as JSON files
- Player attributes are split into typed groups: `OffensiveAttributes`, `DefensiveAttributes`, `IntelligenceAttributes`, `PhysicalAttributes`, `GkAttributes`

### Testing

Tests live in `ofm/tests/` using pytest + Hypothesis (property-based testing). Shared fixtures in `conftest.py` provide pre-built Settings, DB, Player, Club, and simulation objects. CI runs flake8 then pytest on push/PR to master and develop branches.

## ClaudeMaxPower Agent Team

This project uses [ClaudeMaxPower](https://github.com/michelbr84/ClaudeMaxPower) for multi-agent orchestration.

### Hooks (`.claude/hooks/`)
- `session-start.sh` — Git context, session state recovery, auto-dream trigger
- `pre-tool-use.sh` — Audit logging + dangerous command blocking
- `post-tool-use.sh` — Auto-runs pytest after Python file edits
- `stop.sh` — Persists session state to `.estado.md`

### Agents (`.claude/agents/`)
- `team-coordinator` — Orchestrates agent teams (Opus)
- `implementer` — Feature implementation (Sonnet)
- `tester` — Test writing with pytest + Hypothesis (Sonnet)
- `code-reviewer` — Code review specialist (Sonnet)
- `security-auditor` — Security scanning (Sonnet)
- `doc-writer` — Documentation generation (Sonnet)

### Skills (`skills/`)
- `assemble-team` — Analyze project and assemble optimal agent team
- `fix-issue` — Fix a GitHub issue end-to-end
- `review-pr` — Full PR review
- `tdd-loop` — Test-driven development cycle
- `refactor-module` — Safe refactoring with test baseline

### Memory Consolidation
- `scripts/auto-dream.sh` — Runs automatically after 24h + 5 sessions, prunes stale memories, deduplicates, rebuilds index
