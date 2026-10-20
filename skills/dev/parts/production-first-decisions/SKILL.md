---
name: production-first-decisions
description: >-
  Use when a consequential tool, dependency or design choice has unresolved
  evidence: compare existing solutions and project conventions, research the
  specific uncertainty, and test the load-bearing claim before adopting it.
  Includes reuse versus build, small spikes and durable decision rationale.
  Not a web-search requirement for ordinary implementation details.
compatibility: any project; respect its stack, constraints and authorization
---

# Engineering decisions — fit before fashion

Start from the problem, not a tool or an "industry standard". A maintained
solution may eliminate work, but popularity alone does not establish fit.
Existing code, current documentation and representative experiments answer
different questions; none grants permission or replaces engineering judgment.

## Frame the actual choice

- Name the outcome, constraints and specific uncertainty that could change the
  decision: API behavior, maintenance, deployment fit, correctness, performance,
  cost or operational burden.
- Read the relevant project implementation, dependencies and prior decisions.
  Reuse or extend a maintained solution when it meets the acceptance criteria.
  Compare with doing nothing or a smaller local solution where viable.
- Distinguish product/architecture choices from reversible local details. Discuss
  major scope changes and user taste; own ordinary implementation decisions.

## Research enough to answer the gap

Use primary documentation/source for unfamiliar or volatile APIs, installation,
compatibility and support claims. Use the host's developer-service discovery
route when selecting a third-party service. Existing maintained project commands
and installed dependency behavior can answer routine questions without a web tour.

There is no search quota or minimum number of sources. Deepen research when
sources conflict, evidence is weak or consequences justify it. Stop when the
load-bearing uncertainty is resolved, not after five queries or because "everyone
uses it". Label estimates and source claims; do not present them as measurements.

## Test before depending on a risky claim

For a novel integration or load-bearing assumption, choose a small isolated spike:

1. State what would make the option succeed or fail for this project.
2. Exercise a representative real interface/input under controlled conditions.
3. Check correctness and resources; measure representative timing/cost before
   claiming an optimization. Compare viable alternatives, not every product.
4. Adopt, reject or narrow the choice based on the result. A spike does not
   authorize production mutation, publishing, paid calls or system-wide changes.

Not every small local choice needs installation, a benchmark or an ADR. Use
existing tests and evidence when they already answer the question.

## Keep the reason, not a ceremony

Record consequential decisions as a Memora node under the project branch (or
`root/skill/dev` for workspace-wide work): choice, reason, rejected alternative,
evidence and limitations, with `--supersedes` when it replaces an earlier one.
Dated research that needs tables goes to `_memory/reports/`; conclusions go to the
tree. Do not create another store or duplicate an existing canonical record to
prove research occurred.

DRY/KISS/YAGNI are trade-off checks, not algorithms: similar code can represent
different concepts; an abstraction may pay for a real boundary; a simple option
must still satisfy correctness, safety and the requested outcome.

## Verification

Can the next worker see what claim was checked, through which interface, under
what conditions, and why the chosen option fits? If only a recommendation is
supported, say so. If implementation was assigned, continue to integrate and
verify the actual result rather than ending at a research verdict.
