# Skills index

> Generated from the `SKILL.md` frontmatter of every router in `skills/`.
> Edit a skill, not this file. Routing rules: `BOOT.md` § 4.

**31 routers**, 245 parts.

## What a router looks like

Every router is one `SKILL.md` with four blocks, in this order:

1. **Frontmatter trigger** — `name` and a `description` that names the situation
   the user is in, not the topic. It is the only signal for automatic selection.
2. **`Choosing a part`** — a table: situation → part.
3. **`Rules`** — the domain's real forks, the question it raises with the owner,
   and its branch in the memory tree.
4. **`Related`** — the neighbouring routers, so a wrong turn is cheap.

Mechanics live in `parts/<part>/` beside the router and load on demand. A part can
itself be a router, which nests one level deeper; the depth rule lives only in
`BOOT.md` § 4. A domain with one body is a skill, not a router: a router is
justified only where there are real sub-modes.

Skill bodies name actions, not client APIs. Where a body says `ask_questions`, read
"the host's question channel" — `HOSTS.md` names the tool behind that verb on this
client.

## Routers

| Router | Parts | When it fires |
|---|---|---|
| `ai-image-prompts-skill` | 0 | Recommend curated prompts from a 10,000+ real-world image generation prompt library. |
| `ai-prompting` | 0 | Effective communication with the assistant: context-first prompting, phased work from requirements to design to tasks, iterative refinement, examples, explicit constraints, role framing, validation and trade-off exploration. |
| `antislop` | 5 | Anti-slop filter for AI work: rejects technique without purpose and demands liveliness, for UI, copy and code comments. |
| `bro` | 1 | Restate the last message in plain human language with no jargon, or explain a topic simply to a non-technical listener. |
| `browser` | 8 | Browser and device automation: pick the right engine (the host's preview panel first, an anti-detect browser over MCP for hard targets, CDP CLI or Playwright for test suites), test local web apps, capture full-page screenshots, and drive… |
| `decks` | 4 | Presentations and slide decks: HTML decks edited in the browser, markdown-to- slides conversion, Bento decks, themed presets and chart-and-report templates. |
| `design` | 58 | UI, UX and visual design work: direction and brand language, layout and information architecture, components and states, data on screen, flows and accessibility, design systems and craft tooling. |
| `desktop` | 12 | Desktop and workstation environment: Windows dev-env patterns, system optimization and cleanup, console encoding fixes (cp1251/CRLF), Windows 11 theming for Linux tools, Wine and game setup on Linux, Firefox performance and extensions, z… |
| `dev` | 25 | Writing and changing code: Ponytail simplicity, grounded style rules, local and feature-wide systematic debugging, completion verification, architecture improvements, defensive bash, API/database design, money-path safety, hardening and… |
| `documentation-writer` | 1 | Writing a Russian school пояснительная записка (ПЗ) that has to survive a jury: the НИР and проект/сайт structures, title page, format profiles, [N, с. |
| `documents` | 5 | Turning written material into readable documents: markdown to a single-file HTML document, PR reviews and long-form reports, reading Word files, and diagrams. |
| `email` | 3 | Email and inbox work: reading, searching, triaging and drafting replies through the host's mail integration, with triage rules and reply preferences kept in the memory tree under root/skill/email. |
| `grill-me` | 3 | Stress-test a plan or design by interviewing the owner about it: maximize question coverage — every assumption, every edge, every dependency, every implicit decision gets a question. |
| `jupyter-notebook` | 0 | Use when the user asks to create, scaffold, or edit Jupyter notebooks (`.ipynb`) for experiments, explorations, or tutorials; prefer the bundled templates and run the helper script `new_notebook.py` to generate a clean starting notebook. |
| `loops` | 3 | Repeating / autonomous work cycles: bounded loop mode ("loop 10 30m <prompt>"), unattended night-shift or heartbeat work with one-task-at-a- time focus, and a library of proven loop prompts. |
| `mcp` | 5 | Working with MCP (Model Context Protocol) servers in Freebuff Desktop: discovering tools via native search_mcp_tools / call_mcp_tool, bridging stdio servers via _scripts/mcp-call.py, injecting .env secrets via the root `.env` exporter, r… |
| `media` | 11 | Audio, image and video work: text-to-speech through an OpenAI-compatible endpoint (with a Russian fallback), audio/video transcription, image generation and editing, quick ffmpeg screenshot demo videos (while HyperFrames handles motion g… |
| `memory` | 2 | Memory and continuity: the RSI tree in `_memory/memora.db` — walk champions and pruned dead-ends before acting, branch and verdict nodes with provenance and supersedes edges, search report fragments by full text, render the graph on requ… |
| `osint` | 8 | Open-source intelligence: full profiling protocol, breach and leak exposure, image authenticity and reverse image search, entity dossiers, investigator OPSEC, CTF OSINT, and local Google Maps scraping. |
| `planning` | 3 | Plan multi-step or multi-session work with acceptance criteria, coherent units, verification and resumable checkpoints. |
| `prompt-to-exe` | 0 | Turn a natural-language app idea ("an app that...") into a working, double-clickable Windows .exe — with ZERO git, GitHub, terminal, or build knowledge required from the user. |
| `reliable-automation` | 0 | Four proven patterns for reliable automation, extracted from an auto-registration stack and generalized: 1) swappable mailbox pool, 2) OAuth device flow without loopback, 3) anti-detection browser automation techniques, 4) bounded retrie… |
| `research` | 8 | Research on the open web, in feeds and in notebooks: pick the method that fits the question — pulse for what people say right now, deep-research for a high-stakes investigation, research-summarizer for one paper or report, agent-reach fo… |
| `reverse-engineering` | 13 | Understanding how a compiled, obfuscated, packed or virtualized target works: binaries and firmware, Android APKs and iOS IPAs, .NET and JVM assemblies, WASM and custom VMs, browser extensions, network protocols, stripped Go/Rust, anti-d… |
| `review` | 10 | Review and judgement router: evidence-based local code review, self-reflection, idea critique (roast, challenge), human-perspective checks (human-review, think-like-human), learning from outcomes (self-learning), and verification passes… |
| `security` | 26 | Authorized offensive and defensive security assessments, one router over per-surface playbooks: API, cloud/K8s, code audit & SAST review, database, digital forensics, EDR bypass, email, firmware, LLM/AI, malware analysis, OT/ICS, patch-d… |
| `ship` | 15 | Delivering changes safely: release preparation, dependency audits and scoped updates, secrets hygiene, changelog generation, Git conventions and worktrees, GitHub Actions, PR comment handling and CI repair, Cloudflare and Vercel deploys,… |
| `skill-meta` | 6 | Meta-skills about the skills layer itself: creating new skills (scaffold + evals), validating and scoring skill quality, the authoring spec (frontmatter, folder structure, the unified router shape, checklists), installing community skill… |
| `telegram` | 6 | Telegram communications, bot operations, formatted reports, channel/inbox triage, and bot hosting strategies. |
| `triage-route` | 0 | Triage and routing of a reverse-engineering task: by signal (what the target is, what material exists, what result is wanted) choose which reverse-engineering skill to load first. |
| `vpn` | 4 | VPN setup, repair, and verification: GUI client one-button setup (v2RayTun), system-wide stack bootstrap and self-reflection (broken wrappers, RU-zone whitelists, TUN mode, autorun), sing-box TUN tunnel reference on Fedora/Linux, and And… |
