Architecture
============

Project Structure
-----------------

The project follows an MVC pattern with clear separation of concerns:

- ``ofm/core/`` — Business logic and domain models
- ``ofm/ui/`` — Presentation layer (Tkinter + ttkbootstrap)
- ``ofm/res/`` — Static resources (JSON databases, images)

Core Modules
------------

Football Domain (``ofm/core/football/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``player.py`` — Player dataclass with 22 attributes across 5 groups
- ``club.py`` — Club with squad, finances, stadium
- ``formation.py`` — 8 formations with auto-select and bench management
- ``league.py`` — League standings and Season round-robin fixtures
- ``competitions.py`` — Cups, divisions, continental, international
- ``transfer_market.py`` — Offers, negotiation, squad movement
- ``training.py`` — Attribute-specific sessions with age factors
- ``youth.py`` — Academy with prospect generation and development
- ``finances.py`` — Revenue streams, budgets, sponsorships
- ``injury.py`` — Severity levels, recovery tracking
- ``career.py`` — Trophy tracking, reputation, job history
- ``manager.py`` — Manager attributes
- ``interactions.py`` — Press conferences, player/team talks

Match Simulation (``ofm/core/simulation/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``simulation.py`` — SimulationEngine and LiveGame state machine
- ``event.py`` — Event-driven system with outcomes and commentary
- ``team_strategy.py`` — Transition matrices for 3 strategies
- ``advanced.py`` — Weather, crowd, morale, relationships, FFP
- ``match_visuals.py`` — Animation frames, heat maps, highlights
- ``commentary.py`` — Rich template-based commentary generation

Career Mode (``ofm/core/career_mode.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The CareerEngine orchestrates a full season with day-by-day calendar,
match simulation, AI opponents, training, transfers, and youth intake.
