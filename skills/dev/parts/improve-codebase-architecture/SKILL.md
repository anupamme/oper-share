---
name: improve-codebase-architecture
description: >-
  Use to investigate demonstrated architectural friction, compare coherent
  boundary/interface changes and discuss the best improvement. Follow current
  project decisions and actual consumers; use a visual report when requested
  or useful for comparison. No mandatory new glossary, external CDN or
  unexposed skill/subagent dependency.
disable-model-invocation: true
---

# Improve architecture — solve demonstrated friction

Read the actual code, consumers, tests and relevant project decisions. A domain
glossary or ADR is useful when one exists; do not require a file named CONTEXT.md
or create one merely to run this method. Use vocabulary that explains this project,
not a compulsory imported glossary.

## Find a worthwhile change

Look for concrete friction: duplicated invariants, changes scattered across
unrelated locations, circular dependencies, unclear state ownership, interfaces
that expose internals, or bugs the current testing boundary cannot catch.

Trace the relevant paths and show the consequence. File length, wrapper count,
a metric or one awkward name alone is not evidence for a redesign. A deep module
can improve locality; splitting or combining modules can also move complexity
without reducing it. Compare preserving the current design, a small local repair
and a structural change where viable. Ponytail checks necessity and fitting reuse.

## Discuss the candidate

For the strongest useful candidate(s), explain:

- Observed problem and affected code/consumers.
- Proposed responsibility/interface boundary and behavior that must survive.
- Expected gain, migration/wiring risks and meaningful alternatives.
- What check would confirm the improvement, including correctness and measured
  performance when relevant. Do not claim a gain before measuring it.
- Any relevant past decision and why changed evidence warrants revisiting it.

Give a recommendation rather than a pile of theoretical refactors. Ask through
`ask_questions` for material architecture/product forks; do not ask the owner to
choose every helper name or approve ordinary steps of an already assigned redesign.
Use existing `brainstorming`/`planning`/`grill-me` only where their methods help.
No `/codebase-design`, `/grilling`, `/domain-modeling` or worker spawning is assumed.

## Visual explanation

The owner wants visual reports more often when they clarify a substantial redesign.
Use before/after diagrams, decision cards and visible evidence/remaining-work labels
when comparison is hard to follow in prose, and whenever explicitly requested.
Offer the useful visual at a real checkpoint; do not make it a mandatory gate for
all coding work or silently substitute it for implementation.

Follow `HTML-REPORT.md` for an offline, responsive artifact. Keep it inside this
workspace's owning work folder, open it using the host's local preview and inspect
its actual rendering/links. No external scripts/fonts/CDNs, publishing or unrelated
browser/server launch is required. Respect an explicit output path or no-report
constraint; a visual review is not a directory-map deliverable.

## Implement and verify when assigned

Once the meaningful direction is agreed, work in coherent slices with existing
project conventions. Record durable rationale in the existing plan/ADR only when
it matters; do not mutate domain documents as an automatic side effect of naming.
Follow agent-refactor-safety for compatibility/state and verification-before-
completion for final evidence. Report open risks and continue agreed work.
