---
name: assemble-team
description: Analyze the OpenFoot Manager project and assemble an optimal agent team tailored to the user's goals
arguments:
  - name: mode
    description: "new-feature or fix-issue"
    required: true
  - name: goals
    description: "Goals or pending items to accomplish"
    required: true
  - name: team-size
    description: "Max number of teammates (default: 5)"
    required: false
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Agent
---

# Skill: assemble-team

Assemble an agent team optimized for OpenFoot Manager development tasks.

## Workflow

1. Analyze the project context: read CLAUDE.md, check pending TODOs, scan the target area
2. Design team composition from: Architect, Implementer, Tester, Reviewer, Doc Writer, Analyst
3. Create tasks with dependencies using TaskCreate
4. Spawn agents in dependency order using the Agent tool
5. Coordinate results and synthesize a summary report
