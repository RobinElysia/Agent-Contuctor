# Claude Code Execution Constraints

## Purpose
This document defines how Claude Code should work in AgentConductor. Claude Code should follow repository constraints first and use general coding intuition only as a fallback.

## Reading Order

Claude Code should usually read in this order before substantial implementation:

1. current user instruction
2. `AGENTS.md`
3. `docs/tasks.md`
4. `docs/tech.md`
5. `docs/requirements.md`
6. relevant code, tests, and source material

## Operating Discipline

Claude Code should:

- stay grounded in local repository context
- use incremental changes instead of speculative rewrites
- separate facts, inferences, and open questions
- preserve any user-authored changes outside the active scope

## Pre-Implementation Summary

Before editing, Claude Code should be able to summarize:

- the hard constraints that govern the task
- the task boundary and out-of-scope areas
- the files it plans to touch
- the checks it plans to run

If repository drift is found, Claude Code should surface it before implementation.

## Backend Architecture Rules

- Keep the reusable method boundary independent from CLI or future HTTP adapters.
- Keep configuration explicit and reproducible.
- Favor typed interfaces, validated inputs, and narrow dependencies.
- Keep modules cohesive enough to test directly.
- Avoid hiding orchestration state in global variables or side effects.

## Entropy Management

Claude Code should resist drift by:

- not duplicating guidance without need
- not expanding dependencies casually
- not storing important assumptions only in chat output
- documenting unresolved ambiguity instead of inventing behavior silently

## Editing and Verification

- Make the smallest complete change that solves the task.
- Preserve repository style unless there is a concrete reason to improve it.
- Run targeted verification where available.
- State clearly when verification could not be performed.

## Communication

Claude Code should provide concise progress updates during longer work and end with:

- completed work
- verification status
- remaining risks or next steps
