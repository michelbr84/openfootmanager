---
name: refactor-module
description: Safely refactor a module — captures a test baseline, applies the refactor, verifies tests still pass
arguments:
  - name: file
    description: "File path to refactor"
    required: true
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
---

# Skill: refactor-module

1. Run existing tests to capture baseline: `poetry run pytest -v`
2. Read the target module and plan the refactor
3. Apply changes
4. Run tests again to verify no regressions
