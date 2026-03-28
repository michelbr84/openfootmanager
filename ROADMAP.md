# OpenFoot Manager Roadmap

This document outlines the development roadmap for OpenFoot Manager, organized by milestones. Each milestone builds on the previous one and represents a coherent set of features that can be released together.

---

## Milestone 1: Foundation (COMPLETE)

Core infrastructure and debug mode with all pages functional.

- [x] Player system: generation, attributes (22 across 5 groups), positions, contracts, injuries
- [x] Club structure: squad, finances, stadium
- [x] Formation system: 8 formations with auto-select, swap, bench management
- [x] Event-driven match engine: Pass, Shot, Dribble, Cross, Foul, set pieces
- [x] Team strategies: Normal, Keep Possession, Counter Attack with transition matrices
- [x] Rich commentary: varied templates for all event types
- [x] JSON database: fictitious players with persistence
- [x] MVC UI framework: ttkbootstrap with custom themes
- [x] All Debug Mode pages: Home, Team Selection, Player Profile, Team Explorer, Formation, Settings, Finances, Market, Training, League, Championship, Stats Explorer, Visualizer, Match, Edit
- [x] 212+ automated tests (pytest + Hypothesis)
- [x] CI/CD: GitHub Actions with flake8 + pytest

## Milestone 2: Game Systems (COMPLETE)

Backend systems for a complete management simulation.

- [x] League & Season: round-robin fixtures, season progression, standings
- [x] World simulation: auto-simulate other league matches
- [x] Transfer market: offers, negotiation, squad movement, market value calculation
- [x] Loan system: deals, squad movement, expiration, recall
- [x] Training: attribute-specific sessions with age/potential factors
- [x] Youth academy: prospect generation, development, promotion, scout reports
- [x] Injury manager: severity levels, recovery times, history
- [x] Career & Manager: trophies, reputation, job history, manager attributes
- [x] Finances: revenue streams, season budgets, sponsorship deals
- [x] Save/Load: game state persistence with JSON
- [x] Performance: caching, monitoring, batch generation
- [x] Interactions: press conferences, player talks, team talks
- [x] Roster management: auto-select, swap, captain, validation
- [x] Mod support: discover, load, validate, apply mods
- [x] Expanded database: 10 leagues across 4 confederations
- [x] Edit page: edit players (names, attributes), teams (finances, formation)

---

## Milestone 3: Career Mode

The first playable game mode — manage a club through a full season.

### 3.1 New Game Flow
- [ ] "New Game" screen: enter manager name, select league, select club
- [ ] Pre-season setup: initial budget allocation, squad review
- [ ] Calendar system: advance day-by-day through the season
- [ ] Dashboard: upcoming fixtures, recent results, league position, finances summary

### 3.2 Season Loop
- [ ] Weekly schedule: training days (Mon-Fri), match days (Sat/Sun)
- [ ] Pre-match: team selection, formation, tactics, team talk
- [ ] Match day: play or simulate with live commentary
- [ ] Post-match: results, player ratings, press conference
- [ ] Between matches: training, transfers (during windows), youth academy
- [ ] End of season: final standings, awards, contract renewals

### 3.3 Multi-Season Progression
- [ ] Season transition: player aging, contract expirations, free agents
- [ ] Player development: young players grow, veterans decline
- [ ] Manager reputation affects job offers
- [ ] Trophy cabinet and career statistics across seasons

### 3.4 AI Opponents
- [ ] AI manager: makes transfers, sets formations, rotates squad
- [ ] AI transfer logic: offers, accepts/rejects based on player value and club needs
- [ ] AI training priorities based on squad weaknesses

---

## Milestone 4: Competitions

Expanded competition formats beyond a single league.

### 4.1 Cup Competitions
- [ ] Knockout tournament format (single/double leg)
- [ ] Draw system: seeding, pots, regional grouping
- [ ] Cup-specific rules: extra time, penalties, away goals
- [ ] Domestic cup (e.g., FA Cup style with rounds)

### 4.2 Promotion & Relegation
- [ ] Multiple divisions per country (Div 1, Div 2)
- [ ] Promotion (top 2-3) and relegation (bottom 2-3) at season end
- [ ] Playoff system for borderline positions
- [ ] Financial implications: promoted clubs get more TV revenue

### 4.3 International Club Competitions
- [ ] Champions League style: group stage + knockout rounds
- [ ] Europa League style: second-tier continental competition
- [ ] Qualification rounds based on league position
- [ ] Prize money and reputation rewards

### 4.4 International Football
- [ ] National team squads (selected from league players)
- [ ] International friendlies and qualifiers
- [ ] World Cup / Continental championship tournaments
- [ ] Player availability conflicts (club vs country)

---

## Milestone 5: Advanced Simulation

Deeper, more realistic match and world simulation.

### 5.1 Enhanced Match Engine
- [ ] Player fatigue curves within matches (non-linear)
- [ ] Weather effects on gameplay (rain reduces passing accuracy)
- [ ] Crowd effects (home advantage, intimidation)
- [ ] Tactical adjustments mid-match (manager reacts to score)
- [ ] Set piece routines (designed plays for corners, free kicks)

### 5.2 Player Depth
- [ ] Player morale and happiness (affected by playing time, results, talks)
- [ ] Player relationships (chemistry bonuses, rivalries)
- [ ] Agent interactions (contract demands, transfer requests)
- [ ] Retirement and testimonial matches
- [ ] Player awards (league MVP, Golden Boot)

### 5.3 Financial Depth
- [ ] Fair Financial Play (FFP) enforcement
- [ ] Stadium expansion and renovation
- [ ] Merchandise sales linked to success
- [ ] Broadcast revenue distribution
- [ ] Debt management and bankruptcy risk

---

## Milestone 6: Visualization & UI Polish

Improved presentation and user experience.

### 6.1 Match Visualization
- [ ] 2D animated match view (ball and player movement)
- [ ] 3D match visualization (long-term goal)
- [ ] Highlight replay system
- [ ] Match heat maps and pass maps

### 6.2 UI/UX Improvements
- [ ] Dashboard with widgets (calendar, news feed, standings)
- [ ] Drag-and-drop formation editor
- [ ] Player comparison tool (side-by-side attributes)
- [ ] Interactive league table with form guides
- [ ] News feed (transfer rumors, injury reports, match previews)
- [ ] Notification system for important events

### 6.3 Accessibility
- [ ] Scalable UI for different screen sizes
- [ ] Color-blind friendly themes
- [ ] Keyboard-only navigation
- [ ] Screen reader support for key information

---

## Milestone 7: Community & Extensibility

Features for community engagement and modding.

### 7.1 Modding Framework
- [ ] Custom database import/export (CSV, JSON)
- [ ] Custom formation creator
- [ ] Tactical preset sharing
- [ ] Skin/theme system
- [ ] Plugin API for custom logic

### 7.2 Multiplayer
- [ ] Hot-seat multiplayer (same machine, take turns)
- [ ] Network multiplayer (LAN/online)
- [ ] League commissioner mode (manage a shared league)

### 7.3 Community Features
- [ ] Steam Workshop integration (if distributed via Steam)
- [ ] Leaderboards (longest win streak, most trophies)
- [ ] Challenge modes (take a relegated team to the top)
- [ ] Historical scenarios (recreate famous seasons)

---

## Technical Debt & Maintenance

Ongoing improvements not tied to a specific milestone.

- [ ] Increase test coverage to 90%+ for core modules
- [ ] Property-based testing with Hypothesis for all generators
- [ ] Benchmarking suite for simulation performance
- [ ] Database migration system for save file compatibility
- [ ] Localization framework (i18n) for multiple languages
- [ ] Package distribution (PyPI, Windows installer, flatpak)
- [ ] Developer documentation with Sphinx
- [ ] API documentation for modders

---

## Version History

| Version | Milestone | Status |
|---------|-----------|--------|
| 0.1.0 | Foundation | Complete |
| 0.2.0 | Game Systems | Complete |
| 0.3.0 | Career Mode | Planned |
| 0.4.0 | Competitions | Planned |
| 0.5.0 | Advanced Simulation | Planned |
| 0.6.0 | Visualization | Planned |
| 0.7.0 | Community | Planned |
| 1.0.0 | First Stable Release | Planned |
