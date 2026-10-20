---
name: telegram-serverless
description: "Telegram Serverless (tgcloud, cloud.telegram.org) bot hosting: project layout, the push/migrate/run CLI loop, what the V8 isolate actually provides, the invocation time ceiling, where module secrets have to live, and the cutover from a polling container. Use when hosting or moving a bot onto Telegram's own platform, when a handler dies at about thirty seconds or answers nothing at all, when a module needs a provider key, when a webhook and a container fight over getUpdates (409), or when deciding whether this platform can host a given bot."
---

# Telegram Serverless — running a bot on Telegram's own infrastructure

Telegram Serverless runs your bot's code on Telegram's machines: there is no VPS, no
container, no cron and no always-on process. The platform owns the webhook, wakes a
module per update, and gives every project a SQLite database next to the Bot API.
Official documentation: <https://core.telegram.org/bots/serverless> (the `.md`
variant is machine-readable and worth fetching directly).

Read this part when the bot is going onto that platform. For *choosing* between
hosting styles read `skills/telegram/parts/telegram-bot-hosting-triage/` first, then come back.

## What the platform is, in one table

| Piece | What you get |
|---|---|
| Runtime | A lightweight V8 isolate per invocation, next to Telegram's own systems |
| Bot API | `api.sendMessage` etc. with no token setup — the platform owns the bot |
| Database | SQLite behind a Drizzle-like DSL, persistent across invocations |
| Outbound HTTP | `fetch` from the SDK (`import { fetch } from 'sdk'`), no other network |
| Webhook | Managed by the platform; it stays in sync with the handlers you have |
| Mini App | Optional: a static build served at `https://app<app_id>.tgcloud.ai/` plus `endpoints/` it calls |
| Secrets | **None.** No way to inject a secret into module code — see below |

## Project layout

```
project/
├─ tgcloud/                     # everything the platform runs
│  ├─ handlers/message.js       # one file per Telegram update type, FLAT
│  ├─ handlers/callback_query.js
│  ├─ endpoints/getProfile.js   # Mini App calls these, FLAT
│  ├─ lib/                      # shared modules; subdirectories allowed
│  └─ schema.js                 # the whole database schema, one file
├─ tgcloud.jsonc                # project config; `static` names the Mini App build folder
├─ docs/tgcloud-sdk.md          # SDK reference the scaffolder writes for you
└─ .tgcloud/                    # CLI state and credentials — git-ignored, never edit
```

* Only `.js` files under `tgcloud/` are deployed. Markdown, configs and `.tgcloud/`
  stay local.
* Relative imports must carry `.js` (`../lib/cart.js`) and cannot escape `tgcloud/`.
  There are **no npm packages at runtime** and no filesystem.
* Module names are paths inside `tgcloud/` without the extension:
  `tgcloud/handlers/message.js` is the module `handlers/message`.
* A handler file's name must be a Telegram update type. `handlers/probe.js` is
  refused at push time (`Invalid module name: handlers/probe`) and a module outside
  `handlers/`/`endpoints/` cannot be run at all.
* An update type is handled only if its handler file exists and is non-empty —
  leave out the ones you would only discard.

The live list of allowed handler names and the directory rules are not only in the
docs: `GET https://cloud.telegram.org/capabilities` is public, needs no token, and
returns them (`result.directories[].allowed_names`). The CLI caches it.

## The CLI loop

Install per project (`npm create @tgcloud/bot <dir>` scaffolds it, `@tgcloud/cli` is
a dev dependency, so `npx tgcloud <cmd>` finds it).

| Command | Use |
|---|---|
| `login` | Paste the CLI access token: BotFather → your bot → Serverless → CLI Access. Shape `app<id>:<secret>`, kept in `.tgcloud/`, never printed |
| `status` / `diff` | What differs between your folder and the deployed copy, and the line-by-line view (offline) |
| `push` | Upload every changed module in one atomic batch. **Never touches the database** |
| `migrate` | Apply schema changes to the database, with confirmation. Separate from `push` on purpose |
| `run <module> '<json5>'` | Execute a handler/endpoint on the platform using your **local** files, print its `console.*` with per-line timings and its return value |
| `pull` / `fetch` / `reset` | Bring local in line with cloud / inspect / discard local changes |
| `webhook` | Inspect and re-sync the webhook |
| `add handlers/<type>` | Scaffold a handler |

`run` is the tightest loop and the only pre-deploy way to exercise the real runtime
(no local emulator exists). Two properties of it are load-bearing:

* **Logs arrive inside the answer envelope.** If the run fails — including by
  exceeding the invocation ceiling — you get an HTTP error and *no log lines at all*.
  Confirm a run early with a log or a return value, or you will be debugging blind.
* The payload is JSON5, so keys may be unquoted and Telegram's own update shape works:
  `run handlers/message '{ chat: { id: 1, type: "private" }, from: { id: 1 }, text: "привет" }'`

## Runtime contract — what the isolate actually provides

Measured on a deployed project, not assumed (`console.log` a `typeof` report from a
throwaway module; see `references/invocation-budget.md` for the recipe):

| Available | Absent |
|---|---|
| `Date.now()`, `JSON`, `Promise`, `Map`, `URL`, `crypto`, `TextEncoder` | `setTimeout`, `setInterval`, `queueMicrotask` |
| `fetch` (SDK), `api` (Bot API), `db` (SQLite DSL), `InputFile` | `AbortSignal`, `AbortController`, `performance` |
| `console.log/warn/error` (collected into the invocation's logs) | `Response`/`Request` as globals, `process`, `require`, any npm package |

Three consequences that shape every deployment:

1. **No timer means no request timeout.** Writing
   `if (typeof AbortSignal !== 'undefined') options.signal = AbortSignal.timeout(ms)`
   produces code that looks careful and never runs — the guard is false. Time limits
   have to live where the timers exist: see "Where the clock lives" below.
2. **No background work.** If the handler returns, the turn is over. There is no
   `waitUntil`: an unawaited promise is not a queue, and a "send later" design has to
   be a second service (or another invocation you trigger yourself).
3. **Everything stateful goes in the database.** Any update may land on a different
   isolate, so an in-memory cache, sliding window or conversation buffer is a lie.
   Persist the dialog snapshot and restore it per update.

### The invocation ceiling

Telegram publishes no execution quota, so measure it:

| Observed | Result |
|---|---|
| A live handler that runs 28 s | returns normally |
| A live handler that runs ~32 s | `HTTP 500`, non-JSON body, **no logs**, no reply sent |

Budget **≈25 s** and keep going down from there. The killer is not the 500 itself —
it is that a client waiting on a killed turn receives *nothing at all*, not even a
fallback message. `references/invocation-budget.md` has the design that survives it.

## Where the clock lives

A module cannot hold a secret, so keys live outside: a small always-on proxy (a
Cloudflare Worker is the cheap standard) holds provider keys, and the bot holds only
a revocable bot-side token. That split also puts the timers in the right place:

* **Bot side** (no timers): keep a turn deadline and refuse to *start* work that
  cannot finish inside it; reserve a couple of seconds for the final send.
* **Worker side** (has timers): accept a `budget_ms` from the bot, cap each provider
  attempt and the whole chain by it, and race a provider that has no timeout of its
  own (`env.AI.run`, for example) against a `setTimeout` guard.
* **Hedge the chain.** A sequential fallback lets a hung first provider eat the turn.
  Start the next provider when the previous one *fails*, or after a short fixed delay,
  and take the first answer — the backup then costs nothing when the primary is healthy.
* **Retry a dropped connection once, immediately.** A thrown `fetch` fails in
  milliseconds and the platform's egress really does drop calls (measured: ~1 in 300).
  Never blind-retry a hang: without timers you cannot tell it from slow work.

## Getting owner data in

There is no secret store for modules, and a fresh bot has no administrator, so
first-run data needs a path of its own:

* Ship a **bootstrap secret** in a git-ignored local config deployed with the modules
  and accept `/bootstrap <secret> <admin ids>` to seed prices and record the
  administrator ids. Never infer an admin from traffic, and never seed prices from a
  guess. Since a deployed module is readable, the secret must be revocable.
* Keep the token out of logs: read it from a file into an environment variable, never
  echo it, and delete scratch files afterwards.
* Writes go through reviewed modules (`push`, then `migrate`) — there is no SQL
  console to poke at.

## What did not work

* A 75 s (or 120 s) "timeout" behind an `AbortSignal` guard, in a runtime with no
  `AbortSignal`. Decoration, not protection.
* Treating webhook and long polling as interchangeable: a container still polling
  gets `409 Conflict: can't use getUpdates method while webhook is active` and, if it
  treats that as fatal, crash-loops (17 restarts observed) while receiving nothing.
* Leaving scratch modules in `tgcloud/`. Anything under `endpoints/` or `handlers/`
  is deployed code — probe with a module, then delete the file *and* `push` the
  deletion, or the diagnostic ships to production.
* Assuming `run` logs survive a failure, or that a successful push means a working
  handler.
* Assuming a free model pool is available: shared concurrency budgets answer `429`
  until the pool frees, so a single-provider design has silent outages.
* Declaring foreign keys (they throw) or expecting `push` to apply a schema.

## Verification contract

Report each line separately, and never let one stand in for another:

1. **Local tests** — the deployed modules run under `node --test` with an SDK shim
   over real SQLite (stub the Bot API and the proxy). Green here means the logic works.
2. **`npx tgcloud run <handler>`** — the real runtime, your local files, the real
   database and the real outbound network. This is where the time ceiling shows up.
3. **The external proxy** — probe its endpoints directly with its token and time the
   answers; a healthy `/health` says nothing about a provider chain that hangs.
4. **A real Telegram message** — send one as a client and read the answer. The
   webhook path, the reply markup and the client's own wording are only proven here.

Anything not run is reported as not run. "Pushed" is not "answers", and "answers" is
not "answers correctly".

## References

* `references/invocation-budget.md` — how to measure the ceiling and the runtime
  primitives, and the two-sided budget that keeps a turn from dying silently.
* `references/container-to-serverless.md` — the cutover playbook: switching the
  webhook away from a polling container, moving owner data, and rolling back.
