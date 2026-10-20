---
name: reverse-api-engineer
description: >-
  Reverse-engineer a website into a clean, typed API client by capturing real
  network traffic (HAR) and generating client code in Python, JS/TS, Go, Java,
  C#, PHP, Ruby, or C. Use when the user wants programmatic access to a site's
  internal API, says "reverse engineer this API", "make a client for this
  website", or needs data from a site with no official API. Not for sites with
  official APIs — use those instead.
license: MIT
metadata:
  source: https://github.com/nottelabs/reverse-api-engineer
  runtimeClone: tools/reverse-api-engineer
  referencesCopiedAt: 2026-10-17
---

# reverse-api-engineer

The runtime is a real tool, not a prompt: the Python package lives in
`tools/reverse-api-engineer/` (also on PyPI as `reverse-api-engineer`) and the
upstream README, design notes and worked examples are copied into
`references/` so this skill answers without opening the clone.

## What is here

| Path | What it holds |
|---|---|
| `references/README.md` | The authoritative usage: install, capture, generated output, language targets, CLI flags |
| `references/design/PROMPT.md` | The generator prompt: how a captured HAR becomes a typed client |
| `references/design/design-system.md` | How generated clients are structured (types, errors, pagination, auth) |
| `references/design/examples.md` | Design-level worked examples |
| `references/examples/<site>/` | Six real captures — `apple`, `ashby`, `autoscout24`, `ikea`, `mintlify`, `uber` — with the analysis that produced each client |

Read `references/README.md` before running anything: CLI flags change between
releases and memory of them is not evidence.

## Two modes

- **Manual mode** — the user browses the target site in a captured session;
  traffic lands in a HAR file; the generator writes the client.
- **Agent mode** — an agent drives the browser to fulfil a stated goal, traffic
  is captured, and the configured model reads the HAR and writes the typed
  client.

## Workflow

1. First use: `pip install -e tools/reverse-api-engineer` (or
   `pip install reverse-api-engineer`).
2. Fix a concrete goal: "list all open job postings from site X" — one page
   type per pass beats "get everything".
3. Capture per `references/README.md`.
4. Feed the HAR to the model; request the client in the language the user's
   project uses. `references/design/design-system.md` is the shape to aim at,
   and `references/examples/<site>/` shows a finished analysis.
5. Smoke-test the generated client against the live site. Deliver the client
   into the user's project directory — never leave it inside this skill.

## Boundaries

- Only for APIs the user is entitled to use; respect site ToS and robots.
- Unofficial endpoints break silently — every generated client ships with a
  smoke test or does not ship.
- Never capture traffic from accounts other than the user's own logged-in
  session; never capture credential fields.
- Browser-driving backends already exist in `tools/` (Camoufox, Playwright);
  reuse them instead of adding another stack.
