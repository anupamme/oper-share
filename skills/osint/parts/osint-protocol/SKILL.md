---
name: osint
description: >-
  OSINT (Open Source Intelligence) — full profiling protocol.
  Level 0 (local data) → Level 1 (free tools) → Level 2 (verification) → Level 3 (API).
  Principles: Confidence Scoring, username decomposition, contradiction search, contact correlation.
  Use when: "profile someone", "OSINT", "find info on", "intel", "investigate".
---

# OSINT — Full profiling protocol

## Tools

### Built-in (always available)
- **researcher-web** — web-search (Brave Search)
- **read_url** — page reading
- **browser_check / preview_*** — screenshots, UI interaction
- **basher** — terminal, CLI-tools
- **code-searcher** — grep across project files

### CLI (via basher)
| Tool | Command | Purpose |
|---|---|---|
| **Sherlock** | `sherlock <username>` | Username across 400+ socials |
| **Maigret** | `maigret <username> --all --json` | Username across 2500+ sites |
| **Holehe** | `holehe <email>` | Email registration check |
| **TheHarvester** | `theharvester -d <domain> -b all` | Email/subdomains/hosts |
| **PhoneInfoga** | `phoneinfoga scan -n <number>` | Phone number analysis |

### MCP
| Server | Purpose |
|---|---|
| **osint-tools** | Sherlock/Holehe/Maigret/TheHarvester via MCP |
| **exa-mcp** | Semantic search |
| **open-websearch** | DuckDuckGo search |

### Messaging tools
| Tool | Access | Purpose |
|---|---|---|
| **Client session (Telethon or equivalent)** | A session file the owner authorized; see `HOSTS.md` before touching any account | Reading public dialogs and profiles, when the owner has agreed |
| **Telegram statistics API** | Its token as an environment variable, never in a file | Public message and group statistics |

Working inside someone's signed-in account is an action on their behalf: read the authorization rule in `AGENTS.md` first, and never dump a mailbox or a dialog list as “intel”.

---

## Profiling protocol

### Level 0: Local Data First (MANDATORY before web)

The project may already have the needed information. Check BEFORE web-search:

```bash
# 1. Existing notes and dossiers in the project
find . -name "*.md" -path "*dossier*" 2>/dev/null | head

# 2. Already-collected exports the owner handed over
ls imports/ exports/ 2>/dev/null

# 3. Which tools are actually installed
for t in sherlock maigret holehe theharvester phoneinfoga; do command -v "$t"; done
```

**Critical rule:** If the project has a dossier or scripts linking the target to someone — that is the primary source, not web-guessing.

### Level 0 Principles

**Username Decomposition:**
Decompose a username into constituent parts:
- `jdoe42` = J + Doe + 42 → a plausible name and a number suffix
- `ivanpetrov2005` = Ivan Petrov, born 2005

Search by parts, not as a whole — and treat a decomposed name as a hypothesis, never as an identification.

**"Fake Name" Rule:**
If the name is fake — do NOT search for the person with that name on the web. LinkedIn/Twitter with that name = different person. Search by what cannot be faked: phone number, ID, intersections, patterns.

**Contradiction Rule:**
Contradictions = evidence, not noise. Record and dig deeper:
- Virtual phone ≠ LinkedIn profile location → something is off
- Fake name ≠ real location → anonymization
- Different numbers → possibly two accounts

**Correlation Rule:**
If the target has two accounts — they will:
- Be in the same chats
- Have similar speech patterns
- Share IRL contacts
- One username may contain part of the other's username

Use the filter "which of the contacts recurs across all known aliases", not "new person".

### Confidence Scoring (per fact)

| Level | Description | Example |
|---|---|---|
| 🟢 A | 2+ independent identities | account id + public statistics agree |
| 🔵 B | One reliable identity | a single platform profile |
| 🟡 C | Found, not confirmed | LinkedIn with same name (no intersections) |
| 🔴 D | Assumption | "Looks like them" |
| ⚫ E | Contradictory data | Canada number ≠ NY LinkedIn |

**Never present C/D as fact.**

### Level 1: Quick Scan (seconds, free)

Launch ALL in parallel, ONLY after Level 0:

```bash
sherlock <username> 2>&1 | grep -E "\[\+\]|\[-\]"
maigret <username> --all --json 2>&1 | head -50
holehe <email> 2>&1
theharvester -d <domain> -b all 2>&1 | head -30
researcher-web "<name> biography OR portfolio OR linkedin"
```

### Level 2: Source Verification (minutes)

Check found URLs via `read_url`. Cross-verification: each fact from at least 2 sources.

### Level 3: Deep Research (API keys)

```bash
researcher-web "<query>"   # deep research via web-search tools
# Perplexity/Exa/Tavily API wrappers are NOT bundled (scripts/ would need them).
# Add your own API keys to the root .env and call the APIs directly if needed.
```

---

## Full protocol (step by step)

```
1. Gather Level 0: existing notes, exports, installed tools
2. Find FACTS (username, public identifier, shared affiliation)
3. Find CONTRADICTIONS (what doesn't fit)
4. Decompose username into parts
5. Check ALL contacts via intersection filter
6. Launch Level 1 in parallel
7. Verify Level 2
8. Build dossier with confidence score per fact
```

---

## API keys (optional)

Optional paid providers (search APIs, crawling, breach data) are names only here:
they live in the root `.env` and each one costs money. `AGENTS.md` forbids spending
or creating an account without the owner's approval, and a key that is absent is a
capability the run simply does not have — plan around it instead of guessing.

---

## Lessons (from real failures)

1. **Start with Level 0**, not with web-search
2. **Do not take LinkedIn as truth** — name match ≠ same person
3. **Try username variants** — `jdoe42` vs `j_doe42` vs `jdoe`
4. **Decompose username**, then verify the derived name against a second source
5. **Search contact intersections**, not "another person"
6. **Contradictions = evidence**, not noise
7. **Do not dig into personal data** as OSINT-result — that is not investigation, that is reading correspondence
