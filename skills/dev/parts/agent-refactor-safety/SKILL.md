---
name: agent-refactor-safety
description: >-
  Use when extracting modules, splitting a monolith, merging versions, moving
  symbols or repairing behavior lost after an edit. Trace affected callers,
  preserve public contracts and shared-state identity, change coherent slices
  and verify after the last edit. Stack-specific techniques are examples,
  not a required Python workflow for every language.
compatibility: any language; use the project's own tools and conventions
---

# Refactor safety — preserve behavior across the seam

## Understand what must survive

Read the current code, actual callers, tests and relevant local contract. Check
active overlap and preserve unrelated changes. Find imports/exports, side effects,
initialization order, state owners and public interfaces that the move affects.
Use search, language tooling or AST inspection where useful; there is no required
number of reads or universal parser before an edit.

Distinguish behavior-preserving refactor from redesign. If the request changes a
public contract, update agreed consumers/tests explicitly; do not hide that change
inside a cleanup. Characterize important current behavior when coverage is weak.

## Change coherent slices

- Extract by real dependency boundaries, not a fixed runtime→money→UX sequence.
  Avoid circular imports and import-time side effects; test the resulting wiring.
- Keep compatibility facades/re-exports when required by existing consumers.
  Do not add them speculatively if the contract can be changed in scope.
- Preserve shared-state identity and lifecycle. Copying a mutable object can
  diverge state; importing the same name does not prove the same instance.
- Prefer explicit wiring over unrestricted namespace mutation. Python `bind()` /
  `_LOCAL_NAMES` patterns are specialized legacy techniques, not the default
  architecture. Use them only when the existing project genuinely needs them.
- Remove proven-dead code in scope; no speculative abstraction or drive-by cleanup.
  Removal and file moves retain this workspace's trash/data-preservation boundaries.
- If a slice fails, diagnose the cause; undo only your disproved changes with a
  narrow edit, never discard a whole dirty file or reset the working base.

## Merging versions

Compare both versions and their consumers before copying. Identify desired
behavior, local edits, generated files and ownership; resolve meaningful conflicts
rather than choosing the newer timestamp. Preserve inputs/checkpoints before
consequential replacement. Ask when intended behavior or material data risk remains
unclear; do not silently overwrite a version with another.

## Verify the last edit

Use the project's own syntax/type/lint checks and relevant tests, then exercise
consumer interfaces affected by the move. Python import/compile checks may help a
Python extraction; Ruff/pytest are not universal requirements and tools must not be
installed simply to satisfy this skill's examples.

Check the final diff for dropped neighboring lines, missing exports and unrelated
edits. Rerun affected checks after a repair; earlier results do not cover later
changes. Report behavior preserved, any intentional interface changes, the actual
checks and limitations. For proof of completion use
`dev/parts/verification-before-completion`.
