---
name: autonomous-work
description: >-
  Scoped unattended execution for an assigned goal, night shift or heartbeat.
  Finish coherent units, verify results and keep resumable checkpoints. Respect
  task budgets and owner boundaries; stop when complete, blocked or asked, rather
  than inventing endless maintenance. Not an automatic mode for every session.
---

# Autonomous work — finish the assigned goal

> Current contract: `AGENTS.md`, `_memory/USER.md`; the 2026-10-03 charter is
> archived at `_archive/2026-10-15-workspace-rebuild/docs/Autonomy-Charter.md`.
> Older perpetual activity/rejection-counter rituals are retired.

## Start and execute

1. Restore the assigned goal and latest task checkpoint, not another agent's
   latest digest. Check current files and genuinely active overlapping claims.
2. Define delivery evidence and existing task time/resource limits. Do not invent
   a deadline or additional work. Ordinary coding does not require this skill.
3. Choose one coherent unit; inspect code/callers/tests, implement, verify through
   the actual usage interface and review the final files.
4. Persist result, decisions, check output and next unit in the task's own plan.
   Share meaningful progress; a heartbeat log is optional if it adds unique value.
5. Continue agreed units until the goal is complete or a real stop criterion fires.

## Judgment and boundaries

Take ordinary reversible implementation decisions in scope. Consequential new
product intent, architecture, data risk or external actions still require owner
input — a night shift may read, test, edit code in its own branch and prepare the
report, but never deploy, spend money or touch an outside service. If blocked,
record the reason and do another already agreed independent
unit; no authority to pick arbitrary projects, inspect private accounts or enable
cron jobs because the queue looks empty.

Detect contradictions in instructions/tools, explain the cause and propose a
repair. Make small authorized repairs, not hidden blanket permission edits.
Read prior-session work as the base; preserve unrelated changes and coordinate
actual simultaneous edits. Do not stage another agent's changes even if unclaimed.
Git commits follow the active host's authority; pushes/publication need explicit
scope. Data removal remains trash-only. Services need a stop path and verified
cleanup; no unrequested background persistence or system autostart.

## Stop and recovery

Valid stops: verified goal completion, owner stop, agreed budget, dependency or
consequential decision that blocks all agreed work, or unsafe state. State the
reason and preserve a useful checkpoint. Never override a safety stop because it
occurred twice; never force a new pass merely to avoid "nothing to do".

Two attempts with the same failure and no new evidence: change approach or report
what is missing. No infinite retries, invented subagents or compulsory 30-minute
cycles. A checkpoint references evidence rather than duplicating it into several
carriers. No rejection counter is needed to declare a completed goal complete.

Optional repeated bounded iteration: sibling `../loop/`; loop design/discovery:
`../loop-library/`. Canonical queue and coordination: Memora (`root/skill/loops`,
project branches); dependency/service map: `TOOLS.md`.
