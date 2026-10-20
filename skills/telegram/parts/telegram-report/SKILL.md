---
name: telegram-report
description: >
  Telegram reporting protocol, kept as a historical reference: how a task report
  to the owner was shaped — success, error, question — with threading on the
  message being answered. Inactive by default: do not send automatic reports.
  Use when the user asks how such reporting worked or wants it revived.
---

> ⚠️ **Historical reference.** Automatic Telegram reports are off by default.
> Do not send a report after a task unless the owner asks for it.

# Telegram report — the shape of a task report

> ⚠️ **Automation is frequently banned.** A user-session client is a reserve, not a
> primary route: prefer the official Bot API or a manual send. Minimum automated
> messages, no mass mailings.

> The agent reports to the owner. One report per task, not a stream.

## How it worked

```
owner (Telegram)                 agent
      │                               │
      │  "do X"                       │
      │──────────────────────────────►│
      │                               │  Execute task
      │                               │
      │  "✅ Done: X"                 │
      │◄──────────────────────────────│
      │     (via the sender script)   │
```

## Intended behavior

**After each action:**

- ✅ Task done → what was done, which files
- ❌ Error → what went wrong, what was tried
- ❓ Need info → question, context, what is needed

## Templates

### Success

```
✅ Done: [task]
What: [what was done]
Files: [modified files]
Time: [duration]
```

### Error

```
❌ Failed: [task]
Error: [what went wrong]
Attempted: [what was tried]
Next: [proposed path]
```

### Question

```
❓ Question: [topic]
Context: [known info]
Need: [what is needed to proceed]
```

## How to send

Use a small sender script of your own that reads the bot token and the target chat
id from the root `.env`, and pass the message as its argument. Where the host has a
native messaging integration, use that instead of a script.

- Plain message: the sender script with one argument.
- Reply to a specific message: the sender script with the original `message_id`,
  taken from the message being answered.
- If the send fails, check that the chat id in `.env` is the owner's chat: send one
  test message and ask the owner to confirm it arrived before relying on it.

## Rules

- **Reply to the same message** — thread the answer onto the request.
- **Don't spam** — one report per task.
- **Be concrete** — what was done, which files, the result.
- **Error → immediately** — do not wait for the end of the session.
- **Long report → split** into several messages.
