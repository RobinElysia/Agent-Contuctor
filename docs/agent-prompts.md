# Agent Prompt Templates

## Purpose
These templates help humans start agent work in a way that respects repository constraints. They are not product requirements. They are execution-entry templates.

## General Implementation Template

```md
Task: `[TASK-ID or goal]`

Read first:
1. `AGENTS.md`
2. `docs/tasks.md`
3. `docs/tech.md`
4. `docs/requirements.md`
5. Any directly relevant file for the task

Priority:
Follow `AGENTS.md` first, then `docs/tasks.md`, then `docs/tech.md`, then `docs/requirements.md`.

Rules:
- stay within the stated task scope
- do not modify unrelated files
- do not add dependencies unless the task requires them
- report document/code drift before implementation

Before editing, output:
1. hard constraints you extracted
2. the task boundary
3. files you plan to change
4. verification you plan to run

After implementation, report:
- what changed
- what you verified
- remaining risks or open questions
```

## Research Template

```md
Read `AGENTS.md`, `docs/requirements.md`, `docs/tech.md`, and any source material relevant to the task.

Do not write code yet.
Produce a structured summary covering:
- hard constraints
- architecture implications
- key unknowns
- likely implementation phases
```

## Bug Fix Template

```md
Issue:
[describe the bug]

Read `AGENTS.md`, `docs/tasks.md`, and the relevant implementation files first.
Do not guess the fix before identifying the likely root cause.
Use the smallest complete change.

Before editing, state:
- likely root cause
- files to change
- behavior that must not regress
- verification plan
```

## Review Template

```md
Review the change against:
- `AGENTS.md`
- `docs/tasks.md`
- `docs/tech.md`

Prioritize findings about:
- incorrect behavior
- architecture violations
- missing tests or verification
- drift from documented constraints

Report findings first, ordered by severity.
```
