---
name: review-pr
description: Full PR review — reads the diff, checks for bugs/security/tests/style
arguments:
  - name: pr
    description: "PR number"
    required: true
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# Skill: review-pr

1. Read the PR diff with `gh pr diff $pr`
2. Check for correctness, security, test coverage, and code style
3. Output a structured review with verdict (APPROVED / CHANGES REQUESTED)
