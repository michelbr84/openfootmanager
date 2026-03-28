---
name: tdd-loop
description: TDD loop — writes failing tests from a spec, then iterates on implementation until all tests pass
arguments:
  - name: spec
    description: "Feature specification"
    required: true
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
---

# Skill: tdd-loop

1. Write failing tests based on the spec
2. Run tests: `poetry run pytest -v`
3. Implement the minimum code to make tests pass
4. Run tests again — if failing, iterate (max 10 iterations)
5. Refactor once green
