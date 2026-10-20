---
name: testing-discipline
description: >-
  Use when writing or reviewing tests, reproducing a bug, checking test
  sensitivity, isolating storage or external effects, or deciding what
  verification a change needs. Covers independent expectations, real behavior,
  controlled doubles, boundary cases and the user-facing usage path. No
  mandatory implementation order or per-function test quota. Debugging strategy
  lives in debug-incident-protocol; completion claims in dev's
  verification-before-completion part.
compatibility: any language; use the project's existing test framework
---

# Testing discipline — catch a real break

A test earns its place by detecting a meaningful wrong outcome. Coverage and
process completion are clues, not proof. Order is a technique, not an acceptance criterion:
write a reproducer first when useful; test existing work without discarding it.
Never destroy or blindly roll back code to satisfy a test-writing ritual.

## Derive the test from the contract

1. Identify the behavior and the realistic break this test should catch: a
   wrong branch, missing side effect, boundary error or broken interface.
2. Derive expected results independently of the code under test. Use checked
   literals/fixtures or an independently justified oracle, not the same helper
   on both sides of an assertion.
3. Exercise the actual production path at the smallest useful boundary. A test
   of a fake alone says nothing about the component it replaced.
4. Cover relevant success, failure and boundary cases according to risk. No
   test per getter, no universal three-cases-per-function quota. Multiple
   assertions can describe one coherent outcome.

Name tests after the rule, not `test_works`. A private structure or wording change
is not automatically a bug: pin exact text only when it is an agreed contract
(protocol, required copy, accessibility label). For instructional documents,
bounded contract checks can guard agreed boundaries and routes, but cannot prove
model behavior. Execute runnable entrypoints as well; do not invent a behavioral
benchmark where only a rules audit was authorized.

## Establish sensitivity without damaging the working base

A bug reproducer failing for the original symptom and passing after the repair is
strong evidence. A setup error or failure from the wrong cause is not that proof.
A test passing immediately may correctly protect existing behavior; inspect what
would make it fail instead of weakening it to manufacture RED.

Where meaningful, exercise a known-bad input, baseline or controlled mutation in
an isolated fixture/copy. Observe the expected failure. Never mutate production
storage or temporarily break a shared running checkout merely to demonstrate a
red-green cycle. A mental mutation check finds gaps but is not an executed check;
report when sensitivity could not be demonstrated.

## Isolation and doubles

- Establish test storage/env overrides **before** importing code with connection
  or migration side effects. Use project fixtures, isolated subprocesses or fresh
  imports as appropriate; do not assume `sys.modules.pop` isolates every dependency.
- Keep tests away from production stores, live credentials, payments and real
  sends. Use synthetic data and controlled services. A row count staying unchanged
  does not prove a live store was untouched; isolation must be established first.
- Fake slow/external boundaries, not the business rule being tested. Understand
  side effects before mocking; keep required state transitions real in isolated
  storage. Fixture payloads must match the relevant interface, including error and
  malformed cases, rather than silently accepting any shape.
- Assert call arguments/count/order when they are the boundary contract (for
  example a rejected request must not call a paid API). Do not assert a mock's
  existence as evidence of a real feature.
- Use existing frameworks and cleanup conventions. This workspace's retained
  fixtures may be recycled via the trash helpers; never add permanent deletion
  to satisfy cleanup ceremony. Keep test-only helpers out of production unless
  the product genuinely owns that resource lifecycle.

## Risk-focused cases

| Surface | Useful protection |
|---|---|
| Money / quotas | Duplicate submit is idempotent; provider error preserves balance; rejection has no forbidden side effect |
| Limits / rate limits | Exhausted boundary blocks expensive work; the accepted request reaches the real rule |
| UI / navigation | Visible state, accessible control, correct destination and back behavior through the actual interface |
| Payloads | Malformed/empty input; byte-size limits; serialization consumers |
| Environment / defaults | Explicit fixture values; precedence and empty/missing distinction at the consuming boundary |
| Async behavior | Wait for an observable condition with a bounded timeout; preserve actual timing tests where timing is the contract |

## Verification and hand-back

Use the project's applicable syntax/type/lint checks and focused/related tests.
Inspect output and preserve the tested command's exit status through filters.
Check the final edited version; earlier green runs do not cover later changes.

Exercise the user-facing usage path: library call for a library, CLI invocation for
a CLI, browser interaction for a UI, generated-file inspection for a document.
Do not launch a daemon for an artifact that has no daemon interface. Performance
claims need correctness and representative measured timing, not just a threshold
in a mock test.

Report what behavior was checked, scope and limitations. A passing suite does not
prove all acceptance criteria or external integration; use
`dev/parts/verification-before-completion` for completion claims.
