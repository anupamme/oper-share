---
name: human-review
description: Present rendered HTML, Markdown, or a task-relevant local application view in the supported workspace Preview route for owner inspection. Use when seeing the rendered appearance or interaction materially helps review a user-facing artifact or UI; feedback and decisions remain in conversation or ask_questions.
---

# human-review — interactive preview and human feedback

Show rendered visual artifacts or a task-relevant local application view through the
workspace's supported Preview route when that view helps the owner assess appearance or
interaction. The Preview is for inspection; ordinary conversation and `ask_questions`
carry feedback and decisions. Do not promise in-page editing, anchored comments, saved
feedback batches, or automatic source updates unless the active interface explicitly
provides and verifies that capability.

## When to use

- When the owner asks to see a visual artifact or when a rendered view materially improves review of a user-facing document, report, plan, dashboard, or app.
- When checking a locally running UI through a supported Preview path.
- Do not open every text edit or every task in Preview; use it when the visual result is relevant.

## Verification & review loop

1. **Choose the actual Preview route**:
   - For a complete local `.html`/`.htm` artifact, use `register_preview` with its workspace-relative `htmlPath`.
   - For a running owned dev server, confirm it answers HTTP on loopback and register its URL with the server PID.
   - For a public website or an existing browser page, use `preview_open` only when browser access is needed. A browser tab is not the same as the Preview pane.
   - Do not start a new server merely to satisfy this skill; if the needed preview capability is unavailable, state the limitation and offer a suitable alternative.

2. **Inspect the rendered result**:
   - Read the current page/Preview state; check the relevant viewport and content for clipping, overflow, missing assets and obvious rendering errors.
   - Check console/network evidence when a live app's behavior matters. Do not require a desktop+mobile matrix when only one viewport is relevant.

3. **Ask for feedback only where useful**:
   - Briefly identify what is shown and which decision, if any, needs the owner's taste.
   - Use `ask_questions` for real product/design forks with clear consequences; otherwise the owner can respond in conversation.
   - Do not require a response when the task is simply to present or verify the artifact.

4. **Apply confirmed changes within scope**:
   - Treat the owner's comments as input; edit the authoritative source only when the request authorizes the change.
   - Re-render and rerun affected checks after edits. Never assume the Preview itself changed the source.
   - Keep communication direct and concise.
