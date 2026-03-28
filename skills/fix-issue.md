---
name: fix-issue
description: Fix a GitHub issue end-to-end — reads the issue, reproduces with a test, fixes the code, and verifies
arguments:
  - name: issue
    description: "GitHub issue number"
    required: true
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
---

# Skill: fix-issue

1. Read the issue with `gh issue view $issue`
2. Find the relevant code
3. Write a failing test that reproduces the bug
4. Fix the code
5. Verify all tests pass with `poetry run pytest`
