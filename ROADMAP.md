# OpenFoot Manager — Project Status & Roadmap

This document provides an **honest assessment** of what's built, what's wired end-to-end, and what remains. Items are marked with their true integration status:

- **E2E** = Backend + UI + Controller all connected, user can actually use it
- **Backend** = Core module exists and tested, but not yet wired to a UI page
- **Framework** = Class/structure exists as a foundation for future work

---

## What Works End-to-End (User Can Do This)

### Game Flow
- [x] **New Game** (E2E): Enter manager name, select league, select club, start career
- [x] **Load Game** (E2E): Browse saved games, load, delete
- [x] **Save Game** (E2E): Save from career dashboard
- [x] **Career Dashboard** (E2E): View standings, fixtures, results, news; advance days; play matches

### Debug Mode (All E2E)
- [x] Match Simulation: live event-driven match with commentary, stats, working substitutions
- [x] Team Selection: browse and select clubs from DB
- [x] Team Formation: change formation, view starting 11 + bench, **save to DB**
- [x] Player Profile: browse all players, view all 22 attributes
- [x] Team Explorer: filter by country, view squad rosters with overalls
- [x] Stats Explorer: player rankings (filter/sort), team comparison, top performers
- [x] Match Visualizer: 2D pitch with formation-correct player positions
- [x] Edit Page: edit player names/attributes/value, team name/stadium/finances/formation
- [x] Training: run sessions via core TrainingManager with age/potential factors
- [x] Transfer Market: browse and search players with stats
- [x] Finances: real data in career mode, sample data in debug mode
- [x] League Table: real standings in career mode, placeholder in debug mode
- [x] Championship: real standings in career mode, placeholder in debug mode
- [x] Settings: theme selection (darkfootball, football, + system themes)
- [x] Keyboard navigation: Escape key back, status bar

### Core Engine (All E2E via Career Dashboard)
- [x] Season calendar: day-by-day progression (Aug-May), match days on Saturdays
- [x] League system: round-robin fixture generation, standings with points/GD/GF
- [x] World simulation: AI clubs play their matches automatically
- [x] AI managers: make transfers, set formations, rotate squads, choose training focus

---

## Backend Complete, Partially Wired

These systems are fully implemented and tested but only accessible through the career engine's `advance_day()` loop — not through dedicated UI pages:

- [x] **Transfer Market engine** (Backend): offers, negotiation, counter-offers, squad movement, market value — *UI shows browse only, no buy/sell flow yet*
- [x] **Loan system** (Backend): loan deals, squad movement, expiration — *no dedicated UI*
- [x] **Youth Academy** (Backend): prospect generation, development, promotion — *no dedicated UI page*
- [x] **Injury Manager** (Backend): severity levels, recovery tracking — *injuries happen in career loop but no injury list UI*
- [x] **Press Conferences** (Backend): questions, responses, morale effects — *no dedicated UI trigger*
- [x] **Player/Team Talks** (Backend): praise, criticize, encourage — *no dedicated UI trigger*
- [x] **Training sessions** (Backend + E2E in debug): core TrainingManager used by both career AI and debug page

---

## Backend Complete, Not Yet Wired to UI

These systems are fully implemented with tests but have **no UI access point**:

### Competitions (ofm/core/football/competitions.py)
- [ ] Cup competitions: knockout brackets, seeded draws, extra time/penalties
- [ ] Promotion/relegation: division system with playoff brackets
- [ ] Continental competitions: Champions League style group + knockout
- [ ] International football: World Cup with national squad selection

### Advanced Simulation (ofm/core/simulation/advanced.py)
- [ ] Weather effects: rain/snow/wind/heat modifiers on gameplay
- [ ] Crowd system: attendance calculation, home advantage, crowd mood
- [ ] Player morale: affects performance based on playing time, results, talks
- [ ] Player relationships: chemistry bonuses between teammates
- [ ] Agent demands: transfer requests, wage increases
- [ ] FFP checker: financial fair play compliance
- [ ] Stadium upgrades: expansion catalog with costs and duration

### Visualization (ofm/core/simulation/match_visuals.py)
- [ ] Animated match frames: ball/player movement data for 2D/3D rendering
- [ ] Heat maps: 10x10 position intensity grids
- [ ] Pass maps: aggregated passing patterns
- [ ] Highlight replay: extracted key moments with zoom frames

### UI Systems (ofm/core/ui_systems.py)
- [ ] Dashboard widgets: comprehensive data aggregation (partially used by career dashboard)
- [ ] News feed generator: template-based news (partially used by career engine)
- [ ] Player comparison tool: side-by-side attribute analysis
- [ ] Form guide: W/D/L tracking with trend analysis
- [ ] Notification system: prioritized notifications with read state

### Community (ofm/core/community.py)
- [ ] Hot-seat multiplayer: turn-based local multiplayer
- [ ] Network multiplayer: lobby/game framework (stub)
- [ ] League commissioner: custom league rules
- [ ] Challenge modes: 6 predefined challenges (Rags to Riches, Invincibles, etc.)
- [ ] Historical scenarios: 3 scenarios (Istanbul 2005, Leicester 2016, Ajax Youth)

### Modding (ofm/core/modding_extended.py)
- [ ] Database import/export: CSV and JSON with validation
- [ ] Custom formation creator with persistence
- [ ] Tactical preset sharing (export/import)
- [ ] Custom theme system: discover, load, save themes
- [ ] Plugin API: hook-based plugin system

### Infrastructure
- [ ] i18n: 3 languages defined (EN, PT-BR, ES) but UI strings still hardcoded
- [ ] Benchmarking suite: performance measurement tools built but not integrated
- [ ] Save migration: version chain defined but not triggered on load

---

## Not Yet Built

These items have no implementation at all:

- [ ] Dedicated Youth Academy UI page
- [ ] Dedicated Press Conference UI page
- [ ] Transfer negotiation UI (bid/counter-offer flow)
- [ ] Loan management UI
- [ ] Injury list/medical center UI
- [ ] Dedicated Player Comparison UI page
- [ ] Match replay viewer (using MatchAnimator frame data)
- [ ] 3D match visualization renderer
- [ ] Drag-and-drop formation editor (current is combobox-based)
- [ ] Screen reader accessibility
- [ ] Package distribution (PyPI, installer)
- [ ] Sphinx documentation build

---

## Test Coverage

| Area | Tests | Status |
|------|-------|--------|
| Match simulation (events, shots, passes, etc.) | 96 | Passing |
| Stats Explorer logic | 33 | Passing |
| Core systems (DB, settings, players, teams) | 27 | Passing |
| New systems (competitions, career, morale, etc.) | 92 | Passing |
| Substitutions | 11 | Passing |
| Formations | 11 | Passing |
| **Total** | **304** | **All passing** |

---

## Architecture Summary

```
User clicks "New Game" → NewGamePage → NewGameController
  → CareerEngine.new_career() → creates League, Season, Calendar, AI managers
  → switches to CareerDashboardPage

CareerDashboardController:
  "Advance Day" → CareerEngine.advance_day()
    → processes calendar events (training, matches, transfers, injuries)
    → AI managers make decisions
    → refreshes dashboard widgets

  "Play Match" → CareerEngine.play_match()
    → creates LiveGame with TeamSimulation
    → runs SimulationEngine with events
    → records result in League standings

  "Save Game" → SaveManager.save_game()
    → serializes GameState to JSON

User clicks "Load Game" → LoadGamePage → LoadGameController
  → SaveManager.load_game() → restores GameState
  → switches to CareerDashboardPage
```

---

## Version History

| Version | What was delivered |
|---------|-------------------|
| 0.1.0 | Foundation: match engine, player system, debug UI |
| 0.2.0 | Game systems: training, transfers, youth, finances, save/load |
| 0.3.0 | Career mode: new game flow, dashboard, season loop, AI opponents |
| 0.4.0-0.7.0 | Backend systems: competitions, advanced sim, visualization, community, modding, i18n |
| **Current** | **v0.7.0 — Career mode playable, rich backend, UI integration ongoing** |
| 1.0.0 | Target: all backend systems wired to UI, full game loop polished |
