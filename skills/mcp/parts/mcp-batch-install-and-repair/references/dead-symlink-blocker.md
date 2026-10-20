# Dead Symlink Blocker — gws-gmail

## Problem
A dead symlink `%LOCALAPPDATA%\hermes\skills\gws-gmail` (target missing) breaks ALL skill operations:
- `skill_view(name)` → FileNotFoundError
- `skill_manage(action='patch'/'create'/'edit')` → FileNotFoundError
- Every call dies before reaching target skill

## Root Cause
Hermes skill indexer scans ALL entries in `%LOCALAPPDATA%\hermes\skills\`. When it hits a broken symlink, YAML parsing aborts before reaching the requested skill.

## Fix
```powershell
Use the approved reversible trash/recycle procedure for `%LOCALAPPDATA%\hermes\skills\gws-gmail` only after ownership and authorization are confirmed; do not run `Remove-Item` directly.
Use the approved reversible trash/recycle procedure for `%LOCALAPPDATA%\hermes\skills\gws-gmail-read` only if it exists and is authorized; do not run `Remove-Item` directly.
Use the approved reversible trash/recycle procedure for `%LOCALAPPDATA%\hermes\skills\gws-gmail-reply` only after authorization; do not run `Remove-Item` directly.
Use the approved reversible trash/recycle procedure for `%LOCALAPPDATA%\hermes\skills\telegram-mcp-setup` only after authorization; do not run `Remove-Item` directly.
```

## Workaround (if cannot delete)
Write skill files directly:
```python
# Direct write to ~/.agents/skills/<name>/SKILL.md
write_file(path="%USERPROFILE%\\.agents\\skills\\<name>\\SKILL.md", content="...")
```

## Detection
```powershell
# List all symlinks and check for dead ones
Get-ChildItem "$env:LOCALAPPDATA\hermes\skills\" -Force | Where-Object {$_.LinkType -ne $null} | ForEach-Object {
    $target = $_.Target
    $exists = Test-Path $target
    [PSCustomObject]@{Name=$_.Name; Target=$target; Exists=$exists}
}
```

## Session Reference
- Reported symptom: the client's connection kept dropping. Diagnosis found proxy
  environment variables left in the user registry from an earlier mitmdump session.
- The same investigation was blocked by the dead symlink above.
- Lesson: always check for dead symlinks before declaring "skill tools broken".
