# Cutover: from a polling container to Telegram Serverless

Moving a live bot is not a redeploy — it is a handover of one webhook and one database.
Do it in a fixed order, verify both ends, and keep the old host recoverable until the
new one has answered a real client.

## Before touching anything

| Gate | How to check |
|---|---|
| Handlers and `lib/` pushed | `npx tgcloud status` — no pending changes for `tgcloud/` logic |
| Schema applied | `npx tgcloud migrate` reviewed and applied; tables listed |
| External proxy deployed and its secrets set | Probe its endpoints directly with its token and time the answers |
| Local tests green | The suite over the deployed modules with the SDK shim |
| One real turn through `run` | `npx tgcloud run handlers/message '<update>'` for the funnel's main path |

## Order of the switch

1. **Push `lib/` and `schema.js` first, handlers second.** The platform keeps the
   webhook in sync with the handlers you have, so the moment a handler lands you are
   live on it. Cut over with the code you have already smoke-tested, not in two steps
   that leave half the routing deployed.
2. **Seed the owner's data before the webhook moves** — prices, settings, and the
   administrator ids. Use a bootstrap entry point (`/bootstrap <secret> <ids>`) with a
   secret kept in a git-ignored local config, and take the ids from the live system's
   own configuration rather than from memory: read the old host's environment (the
   container's `ADMIN_ID` and friends) so the set of recipients cannot drift from what
   was actually in production. Never infer an administrator from traffic.
3. **Confirm the webhook from both sides**: Telegram's `getWebhookInfo` should name
   `https://cloud.telegram.org/app<id>/webhook` with no `last_error_message` and
   `pending_update_count: 0`; `npx tgcloud status` should report `in sync`.
4. **Stop the old process.** A container that is still long-polling receives nothing —
   Telegram answers `409 Conflict: can't use getUpdates method while webhook is
   active` — and a bot that treats that as fatal will crash-loop instead of idling
   quietly (17 restarts observed on one cutover). Stop it deliberately, check its
   status endpoint, and leave its data directory on a persistent volume.
5. **Verify like a client**: a real message from a real account, a notification card
   arriving at an administrator, and the handler logs for the turn.

## Two databases, one bot

The platform's database starts empty; the container's SQLite holds the client history
you are leaving behind. Decide explicitly which of these you accept:

* **Fresh start.** Simplest: dialog snapshots, past bookings and rate-limit rows are
  not migrated, so a client who was mid-dialog starts the funnel again. Say so.
* **Carry the rows over.** Export the container's tables and insert them through a
  reviewed module (or a `booking`-style import path), keeping the platform's schema
  as the target shape. Worth it when bookings matter — they are the business record.

Either way, do not let the old host keep serving traffic "just in case": two live
databases diverge on the first client message.

## Rollback

Keep it boring and cheap:

* `deleteWebhook` (the Bot API call) plus starting the old process brings polling back;
  its database is untouched if it lives on a persistent volume.
* Rolling back loses whatever the platform recorded while it was live — which is the
  argument for doing the seeding and the smoke turn *before* the webhook moves.
* Deleting the platform project is not part of a rollback. Unpublish or stop serving;
  do not destroy data to take a bot offline.

## Traps seen on a real cutover

* **Scratch modules ship.** Anything under `handlers/` or `endpoints/` is deployed
  code. Delete the probe file *and* `push` the deletion (`✓ ... — deleted`), then
  re-check `status` for `Working directory clean`.
* **A failed `run` loses its logs**, so a probe that exceeds the ceiling reports an
  HTTP 500 with no output. Bracket the budget from below and confirm with a log line.
* **Invalid module names are rejected at push time** (`Invalid module name:
  handlers/probe`): a handler's filename must be a Telegram update type, and modules
  outside `handlers/`/`endpoints/` cannot be run.
* **`push` does not migrate.** A deployed schema change with no `migrate` leaves the
  old tables in place and the new code reading columns that do not exist yet.
* **Secrets cannot be injected into modules.** A token pasted into a module is a token
  in the repository and in the deployed copy — put provider keys behind the proxy and
  keep only a revocable bot-side token in the module.
* **A shared free model pool answers 429 while it is busy**, so a single-provider
  design has silent outages; a keyless backup on the same account is the cheap fix.
* **The old host's keep-alive may not be needed anymore.** Whatever watchdog or
  crontab was keeping a frozen free container alive should be retired with it, or it
  will keep reporting on a process that is intentionally down.

## What to report when it is live

Separate the lines and leave nothing implied: what was deployed, what the measured
ceiling is, which paths were exercised through `run`, which through a real client
message, which host still holds the old data, and the exact rollback steps. Then ask
the owner to read the answers in their own chat — the client-facing wording and
numbers are the one thing no probe can confirm for them.
