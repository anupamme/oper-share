---
name: self-learning
description: >-
  Capture a hard-won golden path from a completed task into a reusable procedure
  or workspace memory. Use when preserving non-obvious operational workflows,
  debugging lessons, or recurring environment procedures that meet intake criteria.
license: MIT
metadata:
  author: kulaxyz
  version: "2.1.0"
---

# self-learning — harvesting verified procedures

Capture proven, reusable procedures and non-obvious operational facts from completed work
so future sessions can execute them reliably without rediscovering solutions from scratch.

This is a meta-method for preserving operational knowledge in accordance with repository
governance (`AGENTS.md` for the contract, the `root/skill/<name>` node for the skill's own
layer). It records verified workflows rather than speculative guesses.

## When to harvest

- **Recurring workflow**: a multi-step operation likely to recur across multiple tasks or projects
  (e.g., specific deployment, database setup, environment configuration).
- **Hard-won discovery**: non-obvious facts, sequences, or workarounds uncovered through real debugging.
- **Explicit owner request**: "remember this workflow", "document how this was done", "save this procedure".

## Intake triage: skill, memory, or skip?

Follow the intake rule in `skills/skill-meta/parts/skill-authoring/` § 0 before
creating any skill (the old `docs/Skills.md` that carried it was retired 2026-10-15):

| Category | Destination | When to use |
|---|---|---|
| **Memory note** | `_memory/` (or project notes) | Single standalone fact, environment gotcha, credentials location, or one-off discovery. |
| **Existing skill update** | `skills/<router>/parts/<name>/` | New procedure that fits naturally into an established domain router. |
| **New skill part** | `skills/<router>/parts/<new-part>/` | Reusable pattern that meets the skill-authoring intake criteria (repeatability ≥ 2–3 runs, no existing coverage), with an independent trigger and useful procedure. |
| **Skip** | (None) | One-off implementation details unlikely to repeat. |

## Evidence and reuse decision

Do not present an observation, attempted fix, or proposed workflow as established fact.
Record what happened, where it was observed, and whether it was directly verified or
remains tentative. A useful verification may be a focused test, actual interface path,
source-traced invariant, or another check suited to the claim; do not invent a passing
check or force a live test when it is unsafe or irrelevant.

For each candidate, identify the concrete reusable lesson and its scope. Search for an
existing canonical note or skill before adding one; update that source when appropriate.
Do not require every lesson to include a separate failure pattern and a tried-and-rejected
alternative. Record those when they materially explain the lesson, and label untested
ideas as tentative rather than promoting them as verified procedures.

## Authoring requirements

When updating or adding a skill part within the task's scope:

- **Follow router structure**: place parts in `skills/<router>/parts/<name>/SKILL.md`
  and update the router's table in `SKILL.md`.
- **Naming**: lowercase, hyphen-separated, descriptive (e.g. `docker-setup`, `vpn-routing`).
- **Trigger-focused description**: frontmatter `description` must clearly state what it does and when to use it.
- **Secrets safety**: NEVER write raw credentials, tokens, or keys into skill files.
  Record only WHERE they live (env var names, secret stores, configuration paths).
- **Procedures over essays**: provide numbered steps, copy-pasteable commands, verification checks, and known gotchas.
- **Self-sufficiency**: ensure all referenced scripts, templates, and relative links exist in the repository. Reuse existing authoring guidance, including `skills/skill-meta/parts/skill-authoring/SKILL.md`; do not rely on absent per-skill template files.
