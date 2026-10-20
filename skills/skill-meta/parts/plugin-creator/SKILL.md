---
name: plugin-creator
description: >-
  Package several skills, and optionally an MCP server, as one versioned bundle
  with a manifest and an explicit trust review. Use when a set of skills is meant
  to travel together, or when a client needs a single installable unit instead of
  loose folders.
---

# Plugin and bundle creator

A bundle is a distribution unit, not a new kind of skill: the same `SKILL.md`
rules apply inside it, plus a manifest that says what the bundle is and what it is
allowed to touch.

## Workflow

1. **Decide that it should be a bundle.** One skill that travels alone is a
   folder. A bundle is for several skills that share setup, or a skill plus the MCP
   server it talks to.
2. **Name it in lower hyphen-case**, and keep every skill inside named the same way.
3. **Write the manifest** — a small declarative file next to the skills:

   ```toml
   schema_version = 1

   [plugin]
   name = "my-bundle"
   version = "0.1.0"
   description = "What this bundle provides"

   [skills]
   path = "skills"
   ```

4. **Keep skills under `skills/<name>/SKILL.md`.** A client that namespaces a
   bundle will expose them as `<bundle>:<skill>`, never as an unqualified command
   that can collide with the workspace router of the same name.
5. **Declare an MCP server only when needed.** Keep the command and its paths
   inside the bundle, map environment values as references (`${NAME}`, never a
   literal), use HTTPS or loopback HTTP, and list the exact hosts it may reach.
   Credentials never go in the manifest.
6. **Everything else is inventory.** Hooks, native extensions, filesystem roots and
   lifecycle mutation are declarations a reviewer can see, not behaviour to switch
   on quietly.
7. **Review before enabling.** Show the manifest and the file list, read the
   scripts, and only then let the client activate anything. Verify afterwards that
   the skills appear and report the bundle as their origin.

## Rules

- A bundle starts untrusted. Trust is a decision the user makes after reading, not
  a flag the bundle sets for itself.
- No downloader, updater or marketplace inside the bundle.
- The interface a client exposes (validate / inspect / enable / trust) is a host
  detail: `HOSTS.md` names it for this client.

## Related

`skill-meta` (authoring), `skill-installer` (taking one skill in),
`mcp` (the server side).
