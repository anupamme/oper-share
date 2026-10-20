---
name: tech-debt-tracker
description: >-
  Scan a codebase for technical debt, score and prioritize it, and keep the
  backlog as Memora nodes with dated snapshots. Use when the owner mentions tech
  debt, code quality, refactoring priority, cleanup sprints, code health or
  modernization planning.
---

# Tech debt tracker

> Part of the `ship` router. The scanner measures; the tree remembers. A debt
> backlog kept in a local file drifts away from the graph within a week.

## The loop

1. **Scan** — the bundled scanner emits a dated inventory:

   ```bash
   python3 scripts/debt_scanner.py <project> --format json --output snapshots/debt_$(date +%F).json
   ```

   Report the `summary` counts, not the file. `assets/sample_codebase` is the dry run.
2. **Prioritize** — cost of delay is the default frame; `wsjf` and `rice` are available:

   ```bash
   python3 scripts/debt_prioritizer.py snapshots/debt_<date>.json --framework cost_of_delay --format json
   ```

3. **Record** — the backlog becomes nodes under `root/project/<name>`, one node
   per remediation item, with `--status active`, the cost-of-delay reason in
   `outcome` and a `debt` tag. A whole scan is one node holding the dated counts;
   its items are children.
4. **Verify** — after a cleanup, re-scan into a new dated snapshot and compare the
   targeted categories. A cleanup that does not move the numbers is rework.
5. **Close** — the item's node goes `promoted` with the snapshot pair that proves
   the drop, or `pruned` with why it was not worth paying.

## Rules

- Severity follows consequences: a debt item that costs nobody anything is not a
  priority because a score says so.
- Do not create a second backlog file, dashboard or tracker next to the tree;
  `scripts/debt_dashboard.py` reads the snapshots and reports trends, it does not
  own the list.
- A cleanup sprint is ordinary work: verify it like any change, through the real
  usage path.
