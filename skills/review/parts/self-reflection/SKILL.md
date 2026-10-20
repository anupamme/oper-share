---
name: self-reflection
description: >-
  Post-task reflection: extract proven lessons, record failure patterns and root causes,
  evaluate whether changes represent genuine utility or unnecessary complexity, and route
  findings to memory or existing skill updates.
invocation: model+user
---

# self-reflection — post-task analysis and lesson extraction

Review outcomes honestly at the conclusion of a milestone, complex repair, or phase.
Distinguish genuine, repeatable patterns from accidental complexity, and document
lessons in workspace memory rather than creating unapproved files or modifying external agent configurations.

## When to use

- At the end of a non-trivial task, debugging session, or architectural milestone.
- When evaluating whether a newly introduced feature or change is necessary and durable.
- To analyze root causes of unexpected bugs, workarounds, or surprising failures.

## Core cycle: intent → evidence → disposition

1. **Intended goal**: what was the specific outcome expected?
2. **Minimal action**: what was changed, and was anything extraneous added?
3. **Observable check**: what concrete test, command output, or measurement proves the result?
4. **Assessment**:
   - Did the solution solve the underlying cause, or merely mask a symptom?
   - Is the complexity justified, or can it be simplified without losing capability?
   - Does the interface tell the truth (no deceptive indicators or silent fallbacks)?
5. **Disposition**:
   - Keep or record supported, reusable findings in the appropriate canonical source.
   - A proposed rollback is a separate change: check task authority, current state,
     concurrent edits and the identified recovery point (a version control
     checkpoint, a file in `_archive/`) before touching anything.
     Repair only an understood task-local mistake narrowly; ask if intent is unclear
     or the affected work cannot be separated safely.
   - Distinguish finding an issue from being authorized to modify or revert it.
     Leave useful work in place when the evidence or scope does not support removal.

## Where lessons go

Follow repository intake and authority rules:

| Finding type | Destination |
|---|---|
| Single fact, tool trap, or environment quirk | A node in the memory tree under the matching root |
| Error pattern, diagnostic trap, or root cause | A node with provenance `incident_lesson` |
| Verified procedure extending an existing domain | Update the relevant router part under `skills/` |
| Architectural or policy decision | A node with provenance `architecture_choice`, confirmed with the owner |

## Hard boundaries

- Never invent external CLI calls or attempt to sync prompts to foreign client directories.
- Do not delete or roll back working project features merely because reflection labels them unnecessary; follow task authority.
- Never store secrets, passwords, or personal credentials in reflections or notes.
- Focus on observable evidence and root causes, not vague aspirations ("be more careful").
