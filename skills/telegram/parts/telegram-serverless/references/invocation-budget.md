# The invocation budget

Telegram publishes no execution quota for Serverless, and the failure mode is the
nastiest one available: a killed invocation sends the client **nothing** — no answer,
no fallback, just a typing indicator that stops. So the budget is measured, then
enforced on both sides of the Worker boundary.

## 1. Measure the ceiling

`endpoints/` is the safe place for a probe: endpoints are not routed from Telegram, so
adding one cannot touch the webhook, and with no Mini App configured they are
unreachable from outside. Loop real outbound HTTP (waiting on I/O burns no CPU, so
this measures wall clock, not CPU) and return the numbers.

```js
// tgcloud/endpoints/probe.js  — temporary, delete the file and push the deletion
import { fetch } from 'sdk';

const URL = 'https://your-proxy.example/health';

export default async function (args) {
  const budgetMs = Number(args && args.ms) > 0 ? Number(args.ms) : 15000;
  const t0 = Date.now();
  let calls = 0;
  let firstError = null;
  while (Date.now() - t0 < budgetMs) {
    try {
      const res = await fetch(URL);
      await res.text();
      calls += 1;
    } catch (error) {
      firstError = `${(error && error.name) || 'error'} ${String(error && error.message).slice(0, 120)}`;
      break;
    }
  }
  const ms = Date.now() - t0;
  console.log(`budget ${budgetMs} ms: ${calls} calls in ${ms} ms`);
  return { budgetMs, calls, ms, perCall: calls ? Math.round(ms / calls) : null, firstError };
}
```

```bash
npx tgcloud push
npx tgcloud run endpoints/probe '{ms: 20000}'   # -> 268 calls in 20043 ms (75 ms per call)
npx tgcloud run endpoints/probe '{ms: 28000}'   # -> 372 calls in 28024 ms (75 ms per call)
npx tgcloud run endpoints/probe '{ms: 32000}'   # -> HTTP 500, non-JSON, and the logs above are lost
```

Results worth keeping in mind (a Cloudflare Worker as the upstream, 2026-10):

| Fact | Value |
|---|---|
| Wall-clock ceiling | 28 s completes, ~32 s is killed (HTTP 500, no envelope, no logs) |
| Outbound call to an external Worker | ~75 ms round trip |
| Transient egress failures | ~1 call in 300 (`Error fetch: request failed`) |

Two traps while measuring: a failed run loses its own logs, so bracket the budget from
below (a run that *completes* tells you something; a killed run tells you only that it
was too long), and a single failed call inside the loop is not the ceiling — rerun
before concluding anything.

## 2. Measure the runtime primitives

Timers or their absence decide the whole design, so ask the runtime directly:

```js
// tgcloud/endpoints/env.js — temporary
export default async function () {
  const type = (v) => (v === undefined ? 'undefined' : typeof v);
  const report = {
    setTimeout: type(typeof setTimeout === 'undefined' ? undefined : setTimeout),
    AbortSignal: type(typeof AbortSignal === 'undefined' ? undefined : AbortSignal),
    AbortController: type(typeof AbortController === 'undefined' ? undefined : AbortController),
    queueMicrotask: type(typeof queueMicrotask === 'undefined' ? undefined : queueMicrotask),
    Date_now: type(Date.now),
  };
  try { report.AbortSignal_timeout = type(AbortSignal.timeout); }
  catch (error) { report.AbortSignal_timeout = `throws ${(error && error.name) || 'error'}`; }
  console.log('runtime primitives: ' + JSON.stringify(report));
  return report;
}
```

Observed: `setTimeout`, `setInterval`, `queueMicrotask`, `AbortSignal`,
`AbortController` and `performance` are all **absent**; `Date.now` is a function.
`AbortSignal.timeout` throws `ReferenceError`.

That is why the bot side cannot enforce a per-request timeout, and why an
`if (typeof AbortSignal !== 'undefined') options.signal = ...` guard is dead code that
reads like protection.

## 3. The two-sided budget

Split the work by who owns a clock.

**Bot side — a deadline, and the discipline not to start doomed work.**

```js
export const INVOCATION_BUDGET_MS = 22000;  // the measured ceiling, minus margin
export const REPLY_RESERVE_MS = 3500;       // sending the reply is part of the turn
export const MIN_ROUND_MS = 6000;           // below this a model round cannot finish

export class Deadline {
  constructor(budgetMs = INVOCATION_BUDGET_MS) { this.endsAt = Date.now() + Math.max(0, budgetMs); }
  remainingMs() { return this.endsAt - Date.now(); }
  callBudget(capMs) { return Math.min(capMs, this.remainingMs() - REPLY_RESERVE_MS); }
  canStart(ms = MIN_ROUND_MS) { return this.remainingMs() >= ms; }
}
```

Rules that make it hold:

* Create **one** deadline per update, in the handler, and pass it to everything that
  can spend time (the agent loop, the media calls).
* Before every model round: `if (!deadline.canStart()) return deterministicReply();`
  The deterministic layer knows the next question to ask and invents no prices, so a
  turn cut short by the clock still moves the funnel and says nothing false.
* Send a reply on **every** path, including the refused-because-late one. A refusal
  inside the budget is an answer; a killed invocation is silence.
* Do not sweat the exact number: anywhere from ~15 s to ~22 s is defensible. Being
  under the ceiling and always answering is the property that matters.

**Worker side — the only place with timers.**

```js
const TURN_ATTEMPT_MS = 8000;    // one provider attempt
const TURN_CHAIN_MS = 14000;     // the whole chain
const HEDGE_AFTER_MS = 2000;     // when the next provider joins a slow one

function budgetDeadline(body, cap) {
  const asked = Number(body && body.budget_ms);
  return Date.now() + (Number.isFinite(asked) && asked > 0 ? Math.min(cap, asked) : cap);
}
function attemptBudget(deadline, perAttempt) {
  const left = deadline - Date.now();
  return left > 500 ? Math.min(perAttempt, left) : 0;   // 0 means: do not start
}
function withDeadline(promise, ms) {                     // for calls with no signal
  let timer;
  const guard = new Promise((resolve, reject) => {
    timer = setTimeout(() => reject(new Error(`no answer within ${ms} ms`)), ms);
  });
  return Promise.race([promise, guard]).finally(() => clearTimeout(timer));
}
```

* The bot sends `budget_ms` on every call; the worker shrinks its own ceiling to it, so
  a nearly-expired turn gets a fast failure instead of a kill.
* Race anything with no cancellation of its own (Workers AI `env.AI.run`).
* **Hedge, do not merely sequence.** Provider #1 starts at once; each later one starts
  when an earlier one *fails*, or after `index * HEDGE_AFTER_MS`, and the first
  fulfilled answer wins (`Promise.any` over attempts that reject on failure). Measured
  reason: with a plain sequence and both Dahl keys hanging, the chain reported
  `workersai: skipped, the turn ran out of time` — the emergency fallback would have
  been sent to the client while a perfectly good free model sat untried. After the
  hedge the same call answered `200` from the backup in 4.9 s.

## 4. Tests worth writing

Local tests cannot see the ceiling, so pin the properties that make it survivable:

* a deadline with no time left starts no model round and still returns a reply;
* a call is refused **before it is sent** when the budget is gone (assert zero outbound
  calls recorded, not just a thrown error);
* `budget_ms` reaches the worker, minus the reply reserve;
* one dropped connection is retried, two in a row surface as a real failure (never as
  an answer);
* the worker abandons an attempt that outlives its budget and says so (stub the
  upstream to hang and to honour `AbortSignal`, otherwise the stub tests nothing);
* a hung first choice still gets an answer from the backup, in well under the window;
* the first answer wins, so a slow backup cannot displace a healthy primary.

Keep time assertions loose (a 12 s window with an 8 s expectation, not a 5 s window
with a 4 s expectation) — a tight margin passes locally and flakes on a loaded machine.
