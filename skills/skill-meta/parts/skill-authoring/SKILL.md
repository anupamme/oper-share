---
name: skill-authoring
description: Use when creating or editing any skill in `skills/` — frontmatter rules, folder structure, the unified router shape, script bundling, and the quality checklist.
compatibility: operative for `skills/` in this workspace, synced to Freebuff account-skills by `_scripts/sync_skills.py`
---

# How to properly create skills and plugins

Rules per the Agent Skills specification (agentskills.io) plus what this
workspace has verified in practice.

## 0. Intake rule (workspace, before creating anything)

1. **Repeatability** — the pattern already repeated, or will clearly repeat,
   ≥ 2–3 times. One-off findings go to `_memory/`, not into a skill.
2. **No coverage** — scan `skills/` (routers and their `parts/`) and
   confirm nothing already covers it. The directory is the catalog. Update an
   existing part before adding a sibling.
3. **A place, not a pile** — a new procedure belongs in the router whose theme
   it serves, as `parts/<name>/`; a new top-level skill only when no theme fits.

Archive never deletes: retiring a skill means moving it out of `skills/`
(through `_scripts/trash.sh`), not rewriting history. Layer decisions live in
Memora under `root/skill/<name>`.

## 1. Frontmatter (mandatory fields — hard rules)

```markdown
---
name: my-skill
description: Use when [triggers/symptoms/contexts]. [what it does + when to apply]
---
```

| Field | Rule (spec) |
|-------|------------|
| `name` | MANDATORY. 1–64 characters, only `a-z0-9` + hyphens: `^[a-z0-9]+(-[a-z0-9]+)*$`. No `--`, no hyphen at start/end. **Must match the skill folder name** |
| `description` | MANDATORY. 1–1024 characters, non-empty. "What it does + when to use"; include keywords the agent searches by. NOT a workflow summary (agent follows description and skips the body) |
| `license` | optional |
| `compatibility` | 1–500 characters, only if environment requirements exist |
| `metadata` | optional, string→string map |
| `allowed-tools` | experimental |

- No vendor attribution, no chat-channel links, no third-party product names in
  frontmatter or body. A skill that advertises someone's channel is not a skill.
- Validate against the spec by reading the file; `skills-ref` and the retired
  `_scripts/audit_skills_format.py` are not part of this workspace's loop.

## 2. Directory structure

```
skill-name/
├── SKILL.md            # mandatory
├── scripts/            # optional: executable scripts
├── references/         # optional: details, "read when X"
├── assets/             # optional
└── any other files/folders — allowed
```

Discovery: `skills/<name>/SKILL.md` in the workspace, mirrored into
Freebuff account-skills by `_scripts/sync_skills.py`.

## 3. Unified router shape (all top-level routers)

Every router is four blocks in this order — no more, no less:

1. **Frontmatter trigger** — `name` matching the folder, `description` naming
   the situations and the words the owner actually says.
2. **`Choosing a part`** — a table `Situation | Part`, one line per part, so the
   agent loads one method instead of the whole router.
3. **`Rules`** — the contract: which forks go to `ask_questions`, the skill's
   Memora branch (`root/skill/<name>`) to read and append to, the tool or script
   the method actually uses, and the hard limits (`Never Destroy`, no external
   validation, no deploy without the owner).
4. **`Related`** — sibling routers and parts worth opening next.

Brevity over ceremony: a router that fits on one screen beats a manual. Detail
belongs in `parts/`, and a part is opened only when its situation matches.
