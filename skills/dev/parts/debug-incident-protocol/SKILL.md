---
name: debug-incident-protocol
description: >-
  Use for a hung, regressed or silently failing runtime, stale-code suspicion,
  duplicate exclusive consumers, or a process whose restart must be verified.
  Covers discriminating facts, bounded hang localization, process ownership,
  safe recovery and current loaded-code evidence. Testing and refactor methods
  live in their matching discipline parts.
compatibility: any stack; only the active host's available capabilities
---

# Incidents — locate before recovering

Use `dev/parts/systematic-debugging` for hypotheses and root-cause repair. This
part adds operational checks; a failure signal does not expand task authorization.

## Facts that discriminate

- Capture the symptom, expected result, input/revision, relevant timestamps and
  first failing operation. Inspect the config, state, logs or process that can
  distinguish explanations; there is no mandatory flags→DB→logs ordering.
- UI success with a flat metric suggests either a failed side effect **or** a
  measurement problem. Trace both before declaring silent failure.
- Compare served/loaded bytes with edited files. Console mojibake does not prove
  product data is corrupt; inspect encoding at the actual file/client boundary.
- Capture errors before retrying. A repeat should add information or test a
  changed condition; otherwise choose a better probe rather than repeat forever.

## Localize a hang

1. Read the tool's schema/help and expected behavior before guessing parameters.
2. Add narrow start/end progress markers around the suspect operation if logs
   cannot locate it. Redact payloads and credentials.
3. Run the smallest representative stage with a bounded timeout appropriate to
   the operation. Distinguish slow progress from no progress; a 30-second cutoff
   is not correct for every workload. Respect the shared-machine resource gate.
4. Capture output in an owned log when needed, preserve the tested exit status,
   and avoid a pipeline obscuring which stage failed. Inspect the actual failure.
5. Compare a known-working environment/input only where it tests a hypothesis.
   Infrastructure is a possible cause, not automatically guilty before logic.

## Process ownership and recovery

Identify the exact PID, parent/launcher, port, lifetime and safe stop route before
acting. For an exclusive stream/lock, prove duplicate consumers really conflict;
not every multi-process service should have one PID.

Never mass-kill or stop an unknown/user-owned process as a repair shortcut. Stop
only identified task-owned processes or ones whose recovery is explicitly covered
by task authorization. If ownership or consequences are unclear, ask and continue
independent investigation. Do not enable cron/autostart or alter live config as
incidental recovery.

A restart is needed only when the change is not otherwise loaded. With hot reload,
in-process configuration refresh or static-file serving, PID creation time alone
cannot establish freshness. Conversely a new PID does not prove the right source,
profile or config loaded. Use observable behavior, build/revision evidence and
fresh logs through the user's interface.

When an authorized restart is necessary:

- Preserve relevant pre-restart evidence and use the application's graceful stop
  path when available. Start through its known task-required launcher.
- Check readiness and the original operation, not just process existence.
- Filter logs by the new run/session; stale errors are not current failures.
- Verify owned-process cleanup and record any intentionally remaining service.

## Environment/startup races

For simultaneous dependency failures, compare actual paths, transport, working
directory, environment presence and readiness. A disk/mount race is one possible
explanation: verify the dependency was unavailable at startup and works now before
concluding that. Running a server by hand can create another process; inspect its
source/side effects and establish ownership/stop conditions first.

System mount units, service dependencies and autostart changes are not ordinary
application edits. Research the applicable OS mechanism and obtain separately
scoped authority; do not apply a historical host-specific command by analogy.

## Checkpoint / postmortem

Record known cause versus hypothesis, containment versus permanent repair,
observed effects, checks and remaining constraints. For a recurring incident,
keep a short relevant checklist next to the runbook. Promote a lesson only when
supported and useful; do not turn every incident into a new global mandate.
