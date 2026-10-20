---
name: error-memory
description: >
  MUST USE after ANY command error, ANY failure, ANY mistake — auto-logging the
  error as an `incident_lesson` node in the memory tree. Trigger: error, fail,
  crash, broken, 403, 500, timeout, refused, ENOENT, command not found.
  On session start, walk `root/workspace` and read the earlier lessons — know
  what broke before and how it was fixed.
version: 1.2.0
---

# Error Memory — learning from errors

## Trigger

1. **At session start** — walk `root/workspace` and read the `incident_lesson`
   nodes; also read the `promoted` nodes, which are the approaches that worked.
2. **After ANY error** — record it as a node; if you then found a working
   approach for a previously blocked task, record that too, as a promoted node.
3. **Before action** — check whether this error was already met; if a promoted
   node covers the situation, use that approach first.

## Where it goes

The tree is the store; there is no log file to grow forever.

```bash
# read the lessons
python _scripts/memory.py walk --root root/workspace --status promoted

# record one after the error is understood
python _scripts/memory.py branch --root root/workspace \
  --provenance incident_lesson --status active --outcome "fixed: <one line>" \
  --content "Problem: ... Cause: ... Solution: ... Signal: ..."
```

When a fix holds after a second occurrence, promote it:
`verdict --id N --status promoted --outcome "held on repeat"`.

## Node shape

One node per distinct gotcha — not one per occurrence.

```
Problem:  what happened
Cause:    the root cause, not the symptom
Solution: how it was fixed, or how to avoid it
Tool:     which tool NOT to use / which to use instead
Signal:   keywords that make this findable later
```

The `Signal` line is the search key: without it, the node is unfindable and the
mistake repeats.

## Categories

browser (captcha, block, Cloudflare, 404), tool (missing, wrong path), api (key,
403, rate limit, timeout), command (syntax, flag), proxy (proxy, VPN, DNS,
resolver), messaging (platform API, sending, formatting), file (path, encoding,
permissions, size), schedule (job, delivery), local-service (port, connection
reset), reverse-engineering (APK, Android, ADB), install (pip, npm, uv,
dependency), env (interpreter, PATH, shell quirks), search (engine failures,
extraction).

## Checklist

```
1. Error occurred
2. -> Why? (root cause)
3. -> How to fix? (solution)
4. -> How to prevent? (signal)
5. -> Node in the tree, provenance incident_lesson
6. -> Dedup: is there already a node for this gotcha? Update it, do not duplicate
```

## Example lessons

### A datacenter address is blocked by search engines
```
Problem: search engines and some APIs answer with a block page
Cause:   the exit address belongs to a datacenter range, not a residential one
Solution: a local browser with the user's own session, or a residential exit
Signal:  Cloudflare, CAPTCHA, "blocked", 403 from search, "Attention Required"
```

### Unsourced 403 after a key rotation
```
Problem: an API starts answering 403 with a key that worked yesterday
Cause:   the key rotated upstream, or the request goes out through a stale proxy
Solution: probe one endpoint with the plaintext key, then check the egress route
Signal:  403, "invalid key", works from another network
```

### Connection reset on a local proxy
```
Problem: the local proxy dies with ConnectionResetError
Cause:   the upstream behind it is down or restarting
Solution: restart the upstream, then the proxy; confirm the listener afterwards
Signal:  ConnectionResetError, 10054, gateway down
```

## Deduplication and archive

Once per session, keep the branch usable:

1. **One gotcha, one node.** Merge duplicates by meaning; the older node gets a
   `supersedes` edge from the newer one, so lineage still resolves.
2. **Archive, never delete.** A lesson that no longer applies is marked `pruned`
   with the reason, not removed from the tree.
3. **Live gotchas stay.** Age is not irrelevance: an environment quirk that still
   reproduces stays `active` however old it is.
4. **Sanitize before recording.** No addresses, tokens or personal identifiers in
   a node — `user***@domain` at most. A lesson must not become the leak.

## Anti-patterns

- Error occurred, work continued, nothing recorded
- Recorded in reasoning only — the session dies and the lesson with it
- Did not walk the tree at start — the same error repeats
- Node without a `Signal` line — unfindable in a search
- "This tool is broken" instead of the working fix
