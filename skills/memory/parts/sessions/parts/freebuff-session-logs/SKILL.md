---
name: freebuff-session-logs
description: >-
  Recover interrupted Freebuff work from an authorized thread or an explicitly
  selected workspace SQLite source. Verify project mapping and schema, search
  visible history within scope, recover bounded decisions, exclude hidden
  reasoning and sanitize private content. Never select by newest DB alone. Ships
  a read-only helper (`scripts/fbsess.py`) and a dated description of one store
  layout.
---

# Freebuff session recovery — scoped continuity

> Use for a concrete continuity gap, not automatic session mining. The `sessions`
> router and `AGENTS.md` govern authority and privacy; `HOSTS.md` names the
> host's own thread-access tool when it has one.

## Choose the source before reading history

1. Read the current task checkpoint and files. Recover only the gap that can
   change the work; do not replay a whole conversation by default.
2. Prefer host-supported thread access when authorized. `read_thread_context`
   requires the owner's explicit thread mention and resolved ID; never invent a
   mention or use local SQLite as a workaround around a host refusal.
3. For authorized local recovery, match the candidate's project metadata to the
   workspace in scope before opening its conversation tables. Do not search
   unrelated projects. A workspace the user keeps aside from the current one is
   excluded by policy; auditing the current workspace does not authorize its
   history.
4. Source paths and schemas below are dated evidence, not live guarantees. Run
   `python scripts/fbsess.py doctor` for the current mapping, sizes and schema of
   every store before reading one, and keep the scope filters on
   (`--project`, `--exclude`). Highest mtime or last message time is not authority.
5. Select an explicit thread by ID or scoped metadata/topic evidence; do not
   assume the most recently active thread is the intended task. If several real
   candidates leave consequential intent unclear, ask; otherwise recover locally.

## Layout as observed (dated evidence)

Read-only helper (stdlib only):
`python scripts/fbsess.py doctor|list|find|brief|dump|answers|cli`, with
`--project SUBSTR` / `--exclude SUBSTR` limiting which stores are opened. The
helper excludes a workspace named in `EXCLUDE_DEFAULT` unless the user asks
otherwise. What one machine showed:

- Live stores are `~/.config/freebuff-desktop/projects/<slug>/desktop-v2.db` with
  the `project.json` sibling carrying `projectPath`. Several exist per machine —
  local workspaces, cloud-backed ones and per-project stores. `<project>/.freebuff/`
  held no DB at all on that machine — do not rely on it as a fallback source.
- `threads.sidebar_archived_at` is the archive marker. The legacy `archived_at`
  still exists but is partial — never filter on it.
- `messages` has no text column; `parts_json` kinds observed: `text`, `compaction`
  (`receipt.summary`), `reasoning`, `tool` (`toolName`, `input`,
  `output`/`result`, `exitCode`), `notice`, `changes`, `agent`, `ad`,
  `sponsored_*`, `*_setup_invitation`.
- The store carries an FTS index `freebuff_conversation_search(text, thread_id)`: a
  `MATCH` is one to two orders of magnitude faster than a `parts_json` `LIKE` scan
  over a large store, and it does not sweep hidden reasoning or tool payloads.
  Prefer it; fall back to a scoped `LIKE` only when the index is missing.
- CLI: `~/.config/manicode/projects/<project>/chats/<ISO-time>/` holds only
  `log.jsonl` (no `chat-messages.json`); recorded prompts live in
  `~/.config/manicode/message-history.json`. `FREEBUFF_CONFIG_DIR` replaces the
  `~/.config/manicode` root when set.
- Crash log: `%APPDATA%/Freebuff/logs/orchestrator-stderr.log`.

`doctor`, `list`, `find`, `brief`, `dump`, `answers` and `cli` were exercised
against one large live store; `.db`, `-wal` and `-shm` sizes and mtimes were
unchanged before and after. The lock-fallback (temporary copy) path was not
triggered.

## A metadata-only probe

The following v2-compatible probe requires **DB path, workspace path and thread
ID**. Optional fourth argument is an exclusive message-sequence cursor. It prints
only the selected window's visible-part lengths and completed-question markers:
no titles, text, tool payloads, patches, attachments, hidden reasoning or secrets.
It writes no dump and fails on unsupported schema/mapping. Inspect source metadata
and adapt a different schema deliberately; do not guess or fall back to all DBs.

```bash
python - "$DB_PATH" "$WORKSPACE_PATH" "$THREAD_ID" <<'PY'
import json, os, sqlite3, sys
from pathlib import Path

if len(sys.argv) not in (4, 5):
    raise SystemExit('usage: DB_PATH WORKSPACE_PATH THREAD_ID [BEFORE_SEQ]')
db, workspace = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
thread_id = sys.argv[3]
if any(part.casefold() in EXCLUDED for part in workspace.parts):
    raise SystemExit('workspace excluded by policy')
before = int(sys.argv[4]) if len(sys.argv) == 5 else None
with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True, timeout=5) as con:
    con.execute('PRAGMA query_only=ON')
    required = {'threads': {'id', 'project_path'},
                'messages': {'seq', 'thread_id', 'role', 'parts_json'}}
    for table, columns in required.items():
        present = {r[1] for r in con.execute(f'PRAGMA table_info({table})')}
        if not columns <= present:
            raise SystemExit('unsupported schema; inspect this selected source')
    mapped = con.execute('SELECT project_path FROM threads WHERE id=?',
                         (thread_id,)).fetchone()
    if not mapped or not isinstance(mapped[0], str) or not mapped[0]:
        raise SystemExit('selected thread has no workspace mapping')
    if os.path.normcase(str(Path(mapped[0]).resolve())) != os.path.normcase(str(workspace)):
        raise SystemExit('selected thread belongs to a different workspace')
    rows = con.execute('''
        WITH window AS (
            SELECT seq, role, parts_json FROM messages
            WHERE thread_id=? AND (? IS NULL OR seq < ?)
            ORDER BY seq DESC LIMIT 20
        )
        SELECT w.seq, w.role, json_extract(j.value, '$.kind'),
               CASE WHEN json_extract(j.value, '$.kind')='text'
                    THEN length(json_extract(j.value, '$.text')) ELSE NULL END,
               CASE WHEN json_extract(j.value, '$.kind')='tool'
                    THEN json_extract(j.value, '$.output') IS NOT NULL ELSE NULL END
        FROM window w, json_each(w.parts_json) j
        WHERE j.type='object' AND (
            json_extract(j.value, '$.kind')='text' OR (
                json_extract(j.value, '$.kind')='tool' AND
                json_extract(j.value, '$.toolName')='ask_questions'))
        ORDER BY w.seq, CAST(j.key AS INTEGER)
    ''', (thread_id, before, before)).fetchall()
    print(json.dumps([{'seq': seq, 'role': role, 'kind': kind,
                       'text_chars': size, 'answered': answered}
                      for seq, role, kind, size, answered in rows]))
PY
```

## Search and recover the necessary excerpt

- Search visible `text` parts within the selected source/thread and bounded
  windows — `fbsess.py find` on a scoped store, then `fbsess.py brief <thread_id>`
  for the bounded window. Do not search raw `parts_json` as a substitute: that
  also matches hidden reasoning, tool payloads and unrelated attachments. Extend
  windows when a concrete earlier decision is missing; report retrieval limits
  honestly.
- Recover only the relevant visible turns or a specific completed `ask_questions`
  result. An unanswered question is not an owner decision. Tool output schemas
  and retention differ by client/build; not every answer is guaranteed recoverable.
- Sanitize before any excerpt reaches tool output, chat, logs or a saved file.
  Never print raw request dumps, headers, environment, credential/config writes,
  token-bearing URLs, command/file-edit payloads or hidden reasoning. Prefer a
  minimal factual paraphrase. If a credential-bearing block cannot be reliably
  separated, withhold the block and report the omission without the value.
- A regex redaction is not proof an excerpt is safe. Inspect the extraction and
  selected fields first, then review the sanitized result. Do not claim complete
  recovery when parts were omitted or the evidence is ambiguous.
- Check source, task scope, changed circumstances and supersession before applying
  a recovered rule. Persist useful decisions/checkpoints where the work belongs;
  no automatic transcript dump, overwrite or sync into external Hermes memory.

## Aggregate behaviour (not recovery)

To measure how sessions behave in aggregate — turn shape, invocation sources,
context size, what sessions read, read-before-edit rate — write one read-only
scanner over the same stores (`mode=ro`, `query_only`), emitting counts and no
message text, and keep its output as a dated report under `_memory/reports/`.
Do not use it to recover a conversation; use the sections above for that.

## Crash diagnosis and safety

For a client crash, select relevant error entries from the dated candidate
`%APPDATA%/Freebuff/logs/orchestrator-stderr.log`; sanitize before output, never
cat the whole log. Installed bundle/schema inspection is read-only and separate
from permission to patch or restart the owner-facing app.

Open SQLite with `mode=ro` and `query_only`; do not alter, move or remove the live
DB, WAL or SHM. `fbsess.py dump` writes only the path you name and refuses to
replace an existing file without `--force`; keep dumps out of version control.
Check DB stability/schema first; no unrequested writes, repair, checkpoint or
vacuum against the conversation store. Credential-bearing tool output inside a
recovered turn is never echoed: withhold the block and report the omission
without the value.

## Verification

- The selected source belongs to the authorized workspace/thread; unsupported or
  mismatched sources fail rather than widening scope. The metadata probe is still
  verified on synthetic SQLite data, and the scoped helper on the live store
  (2026-10-12, read-only: store bytes unchanged).
- The layout above is dated evidence. If `doctor` reports a schema that differs
  from it — a missing `sidebar_archived_at`, no `parts_json`, a new store root —
  record the difference instead of guessing, and do not silently fall back to an
  older store.
- Content recovery remains verified only for the sanitized excerpts actually
  exercised. This procedure is neither a client-loader check nor a behavioural
  benchmark.
