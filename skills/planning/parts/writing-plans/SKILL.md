---
name: writing-plans
description: Optional implementation-plan decomposition and handoff templates for multi-step work with known requirements. Use when a detailed plan helps delivery; preserve decisions during planning and ask only about consequential changes.
---

# Writing Plans

## Workspace adaptation (owner decisions 2026-10-03)

This is optional decomposition guidance under the `planning` router, not a
second task cycle. The current root contract governs authority and questions.

- Plan placement: next to the work it plans (project folder) or the workspace
  root for workspace-level rebuilds. The vendor default below (`docs/superpowers/plans/`)
  does not apply here.
- Persist agreed decisions, open branches and useful checkpoints during planning.
  Refine them into an implementation plan as the requirements become clear.
- Ask about material goal/architecture changes, taste, risk or external effects;
  ordinary newly discovered files and technical fixes are execution work.
- Templates below are examples, not a mandatory header or exact-code script.
  Use enough detail for a handoff; do not duplicate implementation in the plan.
- Local commits follow active host authorization; an uncommitted but verified
  checkpoint is valid when this host requires an explicit commit request.
- The "REQUIRED SUB-SKILL: superpowers:executing-plans" header line is void —
  that part is archived here (duplicate); execution follows the AGENTS.md cycle
  and the planning router contract.

## Overview

Write enough context for another engineer to resume: the outcome, constraints,
files/interfaces, coherent units and how each is checked. Choose detail for the
recipient and task, not a blanket assumption of poor taste or zero competence.
Avoid duplicate implementation text; retain useful test-first steps and authorized
checkpoints.

**Announce at start:** not required in this workspace — no ceremony.

**Context:** Worktree skills referenced below are from the vendor stack
(superpowers) and are not installed here; skip worktree steps unless the task
explicitly calls for one.

**Save plans to:** next to the work (project folder) or workspace root for
workspace-level rebuilds — see the adaptation note above.
- (The vendor default `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
  is not used in this workspace.)

## Scope Check

If independent subsystems benefit from separate delivery, propose coherent units
or work-owned plans. Do not require an earlier brainstorming pass. Each unit
should produce something independently checkable.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Task Right-Sizing

A task is the smallest unit that carries its own test cycle and is worth a
fresh reviewer's gate. When drawing task boundaries: fold setup,
configuration, scaffolding, and documentation steps into the task whose
deliverable needs them; split only where a reviewer could meaningfully
reject one task while approving its neighbor. Each task ends with an
independently testable deliverable.

## Facts vs Hypotheses (field lesson 2026-09-18)

When a plan arrives from a conversation, tag every claim at Level A (verified by a live probe: token works, endpoint responds, price list scraped) or Level B (stakeholder belief: sales scripts, assumed capacities). Level-B rules must be isolated in one marked block of the artifact they affect (`# HYPOTHESIS — confirm with X` ... `# END HYPOTHESIS`) so they can be replaced with one edit; never bake them into architecture. Also record an explicit **LLM/deterministic boundary decision** when agents are involved: what the model may decide versus what plain code enforces (stages, validation, identity injection).

## Bite-Sized Task Granularity

**Example test-first steps (size them to the actual unit):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Save a verified checkpoint; commit only when authorized" - step

## Plan Document Header

**Optional header for a self-contained handoff:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** implement task-by-task per the AGENTS.md cycle (steps use checkbox (`- [ ]`) syntax for tracking; per-task verify before moving on).

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

## Global Constraints

[The spec's project-wide requirements — version floors, dependency limits,
naming and copy rules, platform requirements — one line each, with exact
values copied verbatim from the spec. Every task's requirements implicitly
include this section.]

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Interfaces:**
- Consumes: [what this task uses from earlier tasks — exact signatures]
- Produces: [what later tasks rely on — exact function names, parameter
  and return types. A task's implementer sees only their own task; this
  block is how they learn the names and types neighboring tasks use.]

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Save checkpoint (commit only when the host permits it)**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## No Placeholders

Make the next unit actionable: name its files, interfaces, constraints and real
verification. The following are gaps when they hide an essential decision; full
implementation code is optional and ordinary technical details may evolve:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" without observable behavior and the check to run
- Cross-task references that omit an essential interface or constraint
- Steps with no independently checkable outcome
- References to types, functions, or methods not defined in any task

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Placeholder scan:** Search your plan for red flags — any of the patterns from the "No Placeholders" section above. Fix them.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

If you find issues, repair the plan and recheck affected requirements and
interfaces. Add missing tasks in scope; discuss material scope changes.

## Execution Handoff

After saving the plan, report its state. Continue when implementation is already
assigned; stop at the plan when that was the requested deliverable.

**"Plan complete and saved to <the agreed plan file path>".**

**Execution:** Execute coherent units per AGENTS.md with verification and
checkpoints. Update ordinary technical details yourself; consequential changes
follow the planning router's question boundary.

## Gate before planning (merged from plan)

- Investigate unknowns and ask about unresolved product choices; an exploratory
  plan may retain clearly labeled open branches. No universal interview gate.
- Reuse the owning plan and `planning` router. `executing-plans` is archived;
  execution follows AGENTS.md rather than an absent companion skill.
