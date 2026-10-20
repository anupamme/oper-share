---
name: skill-installer
description: >-
  Install, update, trust or inspect a skill that comes from outside this
  workspace. Use when the user asks which skills are available, wants a community
  skill installed, or asks whether a downloaded skill can be trusted.
---

# Skill installer

A skill from outside is untrusted material until it has been read: it is
instructions *and* executable files, and both run with your authority.

## Workflow

1. **Identify the source.** A local folder with a `SKILL.md`, a repository, or a
   request to scaffold something new. Write down where it came from before
   copying anything.
2. **Copy, do not run.** Put the folder under `skills/<name>/` and read its
   `SKILL.md` plus every script and reference it carries. A folder that only
   looks like a skill is a folder.
3. **Check the license.** A pack that forbids redistribution stays out of a
   published kit; record the origin and license in `PROVENANCE.md` when it ships.
4. **Check what it reaches for.** Network calls in a setup step, unpinned
   `npx -y` / `uvx`, credential reads, and writes outside the workspace are all
   reasons to stop and ask.
5. **Prefer the host's own mechanism** when it has one — a skill or plugin command
   is safer than hand-copying into a global folder, because it records what was
   enabled. `HOSTS.md` names the mechanism on this client.
6. **Name collisions.** A workspace skill and a host-level skill with the same
   name is a real fork: the workspace copy is the canon here, so either rename the
   incoming one or remove the other deliberately.

Example of the copy itself (the path is the package's, not a client's):

```bash
cp -r /path/to/downloaded-skill skills/<name>
python _scripts/eval_skills.py     # does the new trigger description collide?
```

## Rules

- Never execute a script from a freshly downloaded skill before reading it.
- A skill that needs a credential gets the *name* of the variable, never a value.
- Re-run the trigger benchmark after adding routers: a new description can steal
  another router's queries.

## Related

`skill-meta` (authoring and validating), `security` (reviewing foreign code),
`mcp` (a server is installed under the same rules).
