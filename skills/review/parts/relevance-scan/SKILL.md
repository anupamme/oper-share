---
name: relevance-scan
description: >-
  Targeted prior-art and workspace-context lookup when an answer, decision,
  artifact or skill may already exist. Use for explicit "what already exists?"
  questions and before creating reusable workspace guidance, a skill or script;
  locate the owning source, check its scope and currentness, and avoid broad
  scans when the task has a clear direct route. Check `skills/` for unclear skill discovery.
license: MIT
metadata:
  category: process
  version: "1.0.0"
  created: "2026-09-13"
---



# relevance-scan — targeted prior-art and workspace context

> This method helps answer a concrete workspace-context question or avoid
> duplicating reusable work. It is not a mandatory step before ordinary tasks:
> when the task and source are already clear, follow the direct route in
> `AGENTS.md`, `BOOT.md` or the relevant project map.

## When to use it

- The owner asks what already exists, where prior work lives, or what decision
  applies to a specific question.
- Before creating a reusable workspace contract, a skill or a script, when
  locating existing coverage is part of the decision. Skill creation also
  follows the intake requirements in the `skill-meta` router.
- A continuation request has a concrete gap in its current checkpoint that
  targeted history or workspace context could resolve.

Do not invoke it as a preflight for every non-trivial task, a trivial edit, or
an answer fully supported by the current conversation and files already in view.

## Choose the smallest relevant set of sources

The layers below are routes, not a sequence to exhaust. Pick sources based on
the specific question; one relevant canonical source may be enough, while a
conflict or a cross-layer question may require more.

| # | Layer | What it holds | How to check |
|---|-------|---------------|--------------|
| 1 | **Root contract** | Authority, questions and safety boundaries | `AGENTS.md`; operations and file rules in `BOOT.md` |
| 2 | **Canon and infrastructure** | Owner decisions, keys, MCP, published surfaces | Memora `root/canon-2026-10` first; `TOOLS.md` for keys and services (`OWNER-CANON.md` is superseded history) |
| 3 | **Session entry** | Task-local context and dependency routes | `BOOT.md`; `_memory/INDEX.md` — no compulsory full dump or health sweep |
| 4 | **Findings** | Dated investigation results, one topic per file | `_memory/reports/INDEX.md` first, then `investigations/` and `surveys/`; retired `knowledge/` material sits in `_archive/2026-10-15-knowledge-retired/` with its own `INDEX.md` |
| 5 | **RSI tree** | Learned lessons, promoted/pruned branches, closed work | `python _scripts/memory.py walk` from the domain root; read node provenance and `supersedes` |
| 6 | **File-backed memory** | Owner facts, live layouts, canonical decisions | `_memory/USER.md`, `_memory/INDEX.md`, `_memory/parity/`; retired flat logs became tree nodes |
| 7 | **Memory MCP** | Cross-session retrieval when prior decisions or project history could change the work | Search a suitable source early; route KB-RAG/Memora/Obsidian by scope in `TOOLS.md`. Follow distinct hits to close concrete gaps; no fixed per-task cap or duplicate fan-out. Verify snapshot claims at canonical files. |
| 8 | **Skills** | Executable contracts for repeated work | `skills/` router by name — read the router, not a raw directory dump |
| 9 | **Scripts** | Working automation, validators, checkers | `_scripts/` — `grep` by purpose keyword before writing a new one |
| 10 | **Projects** | Per-project code and archives | `projects/<name>/` — check the specific project tree |
| 11 | **Plans** | Work-owned plans and checkpoints | The target project's plan and README; workspace work records live in `_memory/reports/`; confirmed policy decisions became `root/canon-2026-10` nodes |

## How to investigate

1. State the concrete gap: existing artifact, owner decision, implementation,
   or prior task history.
2. Start at the relevant route: root contract and `BOOT.md` for workspace-wide
   policy/navigation; the project README and current files for project work;
   `skills/` routers for skill discovery.
3. Search only plausible canonical sources with an available, task-fit search
   tool. Read relevant hits rather than dumping folders or loading every layer.
4. Check source, scope and supersession, not recency alone. A retrieved snapshot
   or index is a lead; verify consequential/current claims at the owning file or
   active interface. A newer plan is not automatically authority over the
   owner's current task.
5. If familiar work has no trace after a targeted lookup, ask whether similar
   work existed. An explicitly new task needs no continuity interview.
6. Stop when the concrete question is answered or state what remains unknown;
   do not keep scanning for its own sake.

## Boundaries

- No fixed keyword, source-count, search-tool or report-line quota. Prefer the
  narrowest route that answers the question; widen only to resolve a real gap.
- Searching does not replace judgment or owner questions about consequential
  unresolved choices. Ordinary context recovery is part of the assigned work.
- Use the semantic skill catalog for skill discovery rather than raw directory
  listings. Use grep/rg or another available index only when it fits the source
  and question; no search tool is a universal prerequisite.
- For cross-session decisions or prior project work, use a task-routed memory
  source from `TOOLS.md` when that history could affect the work. Choose by
  scope, follow distinct hits that close concrete gaps, and avoid duplicate
  fan-out. Verify imported snapshots against their canonical source.

## Reporting

When prior-art findings materially affect a creation/reuse decision, report the
relevant sources and whether the artifact will be reused, extended or created.
There is no mandatory scan verdict before ordinary work or for tasks with a
clear direct route.
