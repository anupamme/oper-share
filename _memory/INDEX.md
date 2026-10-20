# Memory index

> `_memory/` holds the tree and the files generated from it. Nothing here is a
> place to keep prose that should be a node. Law: `AGENTS.md` § Memory; rule and
> verbs: `BOOT.md` § 3.

## What lives here

| Path | What it is | Where it comes from |
|---|---|---|
| `memora.db` | The RSI tree: decisions, lessons, findings, tasks, with provenance and `supersedes` chains | Created by `_scripts/memory.py init` during birth, written by the agent |
| `memora-graph.html` | Rendered view of the tree | Generated locally by the `render` verb; never committed |
| `USER.md` | Who the user is: name, language, autonomy level, working profile, person | Written once at birth, updated when it changes |
| `OWNER-CANON.md` | Flattened read-only view of the canon root | Rendered by the agent from `walk --json` at the end of a round; never hand-edited |
| `parity/` | Claims on shared paths while more than one session edits them | Created at birth; a closed claim becomes a node |
| `reports/` | Dated evidence too large for a node, indexed by fragments | Written during the work, archived when superseded |

## Where facts belong

- A decision, a lesson, a pruned approach, a task → a node in the tree. How a node
  is written is `BOOT.md` § 3 and is not restated here.
- An owner fact or preference → a node under the canon root, and a line in
  `USER.md` when it changes how the agent should behave.
- A long measurement, a survey, an acceptance record → `reports/<date>-<CODE>-*.md`,
  and one node that points at it. The report is the exhibit, the node is the claim.
- A question that has no answer yet → the project's `STATUS.md`, not a node: a
  node records what was decided, never what is still open.

## Tools

`python _scripts/memory.py` — `init`, `walk`, `branch`, `verdict`, `search`,
`reindex-reports`, `render`. Stdlib only, no service to start; the store is one
file you can copy. `_scripts/parity_claim.py` issues a coordination record under
`parity/` when two sessions edit the same paths.

## Retrieval

How to walk is `BOOT.md` § 3. Two cautions belong to this file: a retrieval miss
does not prove absence — check the report index and the source file before
concluding that something was never written down — and a hit is verified at its
source before acting on it. A node states a claim; the artifact states the fact.
