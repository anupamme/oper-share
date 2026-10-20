---
name: systematic-debugging
description: >-
  Use for bugs, failing checks, regressions or unexpected behavior. Reproduce
  the symptom, trace the relevant data/control flow, test a specific hypothesis,
  repair the cause and verify the original path. Scale investigation to the
  uncertainty; repeated failures require new evidence, not an automatic
  architecture verdict or a fixed number of permission requests.
---

# Systematic debugging — evidence changes the hypothesis

Understand the failure before prescribing a repair. Keep facts, hypotheses,
containment and confirmed fixes distinct. A simple, well-localized bug may need
one focused read and a reproducer; a distributed incident needs boundary evidence.
Neither requires filling out every phase as a ritual.

## 1. Establish the observed failure

- Capture the owner's exact symptom and expected result, relevant error/stack,
  input, revision and environment. Check current files and recent changes.
- Reproduce through the failing usage path with controlled inputs. If it is
  intermittent or inaccessible, record that and gather discriminating evidence;
  do not invent a reliable reproducer.
- Read the affected implementation, callers, configuration and existing tests.
  Trace the bad value or missing side effect backward to its origin. Compare a
  working case where useful, not every file in the repository.

For multi-component flows, locate the first boundary where actual behavior
separates from expected behavior. Add narrow, temporary diagnostics only where
existing observations cannot answer the question. Record identifiers, types,
counts or redacted metadata, never full credentials, payloads or environment dumps.

For example, this checks presence without printing a credential:

```bash
if [ -n "${IDENTITY:-}" ]; then
  printf 'IDENTITY: set\n'
else
  printf 'IDENTITY: unset or empty\n'
fi
```

Checking presence does not validate a credential. A service probe or runtime
mutation needs task-specific scope; do not start, sign, send or restart merely
because it appears in a diagnostic example.

## Feature-wide repair

When asked to make a whole feature work, start with the broken user journey,
entrypoints and acceptance criteria. Follow the dependencies and consumers needed
to explain and verify that journey. Configuration, migrations, imports, handlers
and UI state may all participate; a folder boundary does not limit root-cause work.

Restore required behavior in coherent slices, prioritizing load-bearing failures.
Explain necessary changes outside the initially named file. Do not turn a repair
into an exhaustive audit of every folder/import or a mandate to fix all TODOs.
Record unrelated findings separately and discuss major scope/architecture changes.

Verify affected consumers and the actual end-to-end journey, including relevant
failure/recovery paths. A feature's unit tests alone may miss broken wiring; a
manual-verification suggestion alone is not a completed UI check when the host
can exercise it. Retain useful evidence in the existing task checkpoint, not
mandatory manifests and per-fix reports.

This includes the useful feature-repair scope of the retired `focused-fix` wrapper.
There is no fixed dependency→types→logic→tests ordering or three-strike gate.

## 2. Form a falsifiable explanation

State the hypothesis and the observation that supports it. Predict what would
confirm **or refute** it. For ambiguous multi-factor incidents compare competing
explanations; for an obvious localized cause do not manufacture alternatives.

Choose the smallest useful experiment. Change one causal variable at a time;
keep any exploratory change identifiable and reversible without losing others'
work. A command error, unavailable tool or empty result must be distinguished.

If a hypothesis fails, retain the observation, undo only your disproved change
when safe, and change the explanation or experiment. Repeating the same attempt
without new information is not investigation.

## 3. Repair the cause within scope

Use the existing architecture and dependencies where they fit. Fix the origin
rather than adding compensating patches in every caller. Add validation where an
actual trust boundary or distinct invariant requires it, not at every layer by
default. Avoid unrelated cleanup and do not weaken tests to make the fix pass.

Preserve a regression reproducer when feasible. A test-first sequence is useful
but not mandatory; tests protecting existing behavior are valid. Follow
`discipline/parts/testing-discipline` for independent expectations and safe
sensitivity checks. If only a manual path is available, record the steps and
limits instead of claiming automated coverage.

Urgent containment may be appropriate when already authorized: explain what it
contains and what root cause remains unresolved. A retry, fallback or timeout is
not a proven permanent fix merely because it hides the symptom; consider
idempotency, side effects and the actual failure mode.

## 4. Verify and reassess

Exercise the original failure and relevant success/boundary cases on the final
files. Run applicable related tests/typechecks and the actual usage interface.
`verification-before-completion` defines the evidence for success claims.

Repeated failed fixes are a signal to reassess, not proof of a wrong architecture.
Inspect whether the problem is a wrong hypothesis, bad reproducer, stale code,
environment, hidden coupling or incomplete observability. Continue ordinary
investigation when it yields new evidence. Bring a major redesign, unresolved
product intent, protected mutation or consequential risk to the owner; do not
infer a universal "fourth attempt requires approval" gate.

When diagnosis remains incomplete, say what is known, what was ruled out and the
next discriminating check. Ask for missing user-only context/access when necessary;
a diagnosis alone does not satisfy an assigned repair unless the blocker is explicit.

## Optional supporting material

Read only when it addresses a concrete gap. These are techniques/examples, not
additional permission or verification laws:

- `root-cause-tracing.md` — backward call/data-flow tracing. Do not run its
  polluter helper before inspecting its cleanup and isolating the target.
- `condition-based-waiting.md` — observe readiness with bounded waiting rather
  than guessing delays; example timings are not universal budgets.
- `references/environment-contamination.md` — check relevant environmental
  assumptions without dumping secret values.

## Checkpoint / result

Give a compact account: symptom and expected result → reproduction/evidence →
localized cause or remaining hypothesis → change and why → original-path and
regression checks → unresolved constraints. Investigation should narrow the
problem and lead to a usable repair, not substitute an elaborate report for it.
