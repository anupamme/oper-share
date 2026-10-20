---
name: brainstorming
description: >-
  Explore fuzzy intent and product/design choices through natural collaborative
  dialogue. Use when the owner wants a brainstorm, an interview, alternatives,
  or help discovering what they need. Batch easy concrete questions by topic;
  do not apply a mandatory design/approval ceremony to routine implementation.
---

# Brainstorming — discover the need together

> Owner-directed rewrite, 2026-10-03. Root question policy: `AGENTS.md`.
> This skill supports co-design; it is not a gate on every code/config change.

## Explore without taking over

Read task-relevant context before asking what files can answer. Distinguish what
the owner stated, evidence on disk and your hypothesis. A supplied example may
show an interview method without naming the project to change.

Offer several easy points of entry instead of demanding one perfect remembered
incident or an already complete specification. Use short related batches through
`ask_questions` (usually 2–4 questions); allow multi-select and free answers.
If the owner prefers a longer prose questionnaire, organize it by topic. Avoid
repeatedly asking resolved questions under different labels.

Probe concrete situations, desired outcomes, irritations and trade-offs. Do not
force the owner to choose an architecture, persona or operating mode before you
understand the need. Recommendations are useful but remain hypotheses, not a
hidden vote for your first plan. `grill-me` is for explicit maximum coverage.

## Form a design when there is enough evidence

Summarize your understanding and separate confirmed decisions from open branches.
Offer genuinely different approaches with consequences and a reasoned position.
Size detail to the task; a small repair does not need a multi-document spec.
Discuss consequential product/architecture forks before implementation; do not
require a fresh approval for every section, tool, file or reversible detail.

Persist confirmed decisions and useful working checkpoints where they belong.
An unfinished question may be recorded as open rather than lost at interruption.
Use `planning` for multi-session implementation and existing artifacts as the
carrier; do not invent duplicate design files or force commits against host policy.

## Transition

Follow the owner's current request. An explicit instruction to implement agreed
work is a transition, not a reason to restart the interview. Continue with the
appropriate implementation skill and verification path. New consequential forks
are still discussed; local execution choices are owned by the agent.

## Visual companion (optional)

Use visuals when a mockup/layout/diagram clarifies an actual choice, not to add
ceremony to a conceptual question. Follow host preview tools and process ownership;
ask about a separate optional visualization if it materially expands the task.
Detailed legacy visual guide: `visual-companion.md` (read only when needed).
