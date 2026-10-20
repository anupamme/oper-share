# HOSTS.md — the tool surface this client provides

`AGENTS.md` is written host-neutral on purpose: rules outlive clients, tool names
do not. This file is where the verb-to-tool mapping lives — the one place to look
to learn what *ask*, *publish* or *elevate* mean on this client. Two profiles ship
— **Freebuff Desktop** as the reference implementation, and a **generic** profile
for any other client.

If a verb below has no tool on the current host, say so plainly and degrade. Never
simulate a question, an approval or a preview that did not happen.

## 1. The verbs the law relies on

| Verb | What the tool must do | If the host has no such tool |
|---|---|---|
| **Ask** | Pose one fork with concrete options and wait for an answer before continuing | Stop the mutating call and state the fork in one line; a channel that cannot block is not a question channel |
| **Propose** | Offer follow-up actions as clickable cards | End with a short list of next steps in prose |
| **Delegate** | Run independent sub-tasks in parallel | Batch the lookups into one round and do them in sequence |
| **Show file** | Open an artifact in the user's panel | Give a clickable path |
| **Show app** | Render a running local server in the panel | Print the URL and confirm it answers HTTP |
| **Offload** | Move long or overnight work off this machine | Keep the work local and say so |
| **Elevate** | Request administrator rights through the client | Stop and hand the exact command to the user |
| **Read mail** | Read the user's mail, calendar and drive | Ask for the material instead |
| **Publish** | Preview first, then publish on command | Produce the artifact and stop before publication |

Memory, skills, scripts and Git need no host tool: they are local files and local
processes. That is why the package can be moved between clients at all.

## 2. Freebuff Desktop — reference profile

| Verb | Tool | How it behaves |
|---|---|---|
| Ask | `ask_questions` | The only question channel. Two to four concrete options, best first, each with a one-line consequence. The user can always type a free answer, so never add an "Other" option. |
| Propose | `suggest_prompts` | Two to four cards at the end of a substantive turn, introduced in prose, one of them a bold direction. Rendering a card does not run it. |
| Delegate | `spawn_agents` | Independent slices in one call: reconnaissance, mechanical per-file work, verbatim extraction. The main session reconciles and verifies the whole change. |
| Show file | `reveal_file` | Opens a file or folder in the right panel. |
| Show app | `register_preview` | Takes a loopback URL and the PID of the server you started. Show it before any deploy; a dev-server preview is not a deployment. |
| Offload | `move_to_cloud` | Long or overnight jobs only, never work that must run on this machine. |
| Elevate | `request_elevation` | The exact command without a privilege wrapper; the app asks the user. |
| Read mail | Gmail, Calendar and Drive integrations | Read freely; write and send after confirmation. |
| Publish | Sites tools | Preview first, production on the user's command; unpublishing stops serving and keeps the data. |
| New service | `gravity_index` | Search before adopting a third-party service; creating an account needs explicit consent. |
| Research | `researcher_web`, `web_search` | Several questions to the first, one quick lookup to the second. |
| Terminal | Shared terminal and shell tools | Long jobs run in the background with a log and a known PID. |
| Browser | `preview_*` tools | A shared panel; read a fresh snapshot before acting. |

Behaviour that belongs to the platform rather than to any tool: the workspace's
skill folder stays the canon, and the client's account copy is a derivative that
is regenerated, never edited in place.

## 3. Generic profile

Any client with a shell, file tools and a blocking question tool can run this
package unchanged. Map the verbs in section 1 to that client's names, then keep
this section as that client's profile: one row per verb, the tool that implements
it, and a note on how it behaves — the same shape as section 2.

Hosts without a deployment target, a cloud offload or an elevation request simply
do not list those verbs. Their absence is a fact to report, not a gap to paper
over: produce the artifact, verify it locally, and leave publication to the user.

## 4. Wiring a new host

1. Read `AGENTS.md` and list every capability it leans on.
2. Fill section 1 with real tool names, verifying each with one real call — a name
   read from documentation is not a working tool.
3. Record the gaps in the same table. A missing capability is a line in this file,
   not a rewrite of the law.
4. Never edit `AGENTS.md` to fit a client. If the law needs a capability that no
   host provides, that is a fork for the owner, not a silent local rule.

## 5. What this file never contains — and what it does not own

Credentials, account handles, machine names, ports of someone's private services:
none of these appear here, and none appear in the law either.

It also does not claim to be the only place a client is ever named. What carries a
name is tied to one client by what it does, not by a rule, and says so in its own
file:

| Where | Why it is not host-neutral |
|---|---|
| `_scripts/sync_skills.py` | It publishes into that client's `account-skills/<account>/<scope>/` layout, with `--target` to point at any other folder |
| `skills/memory/parts/sessions/parts/freebuff-*` | Two parts named after the client whose session logs they read |

The promise kept here is narrower and checkable: the law names no tool, and every
verb in section 1 resolves here or is reported absent.
