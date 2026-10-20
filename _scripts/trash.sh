#!/usr/bin/env bash
# trash.sh — Send files to the Recycle Bin (Windows) or the desktop trash (POSIX).
# Usage: trash.sh <file|dir> [file|dir ...]
#
# Windows: PowerShell moves the target to the Recycle Bin (trash.ps1).
# Elsewhere: `gio trash`, else a dated folder under
# ${XDG_DATA_HOME:-~/.local/share}/OperTrash/ — each prints where the file went.
# Nothing is ever deleted: every branch moves, and the last one never needs a GUI.
#
# Handles spaces, quotes, and shell metacharacters without generated scripts.
# Targets are passed POSITIONALLY (no -LiteralPath name): PowerShell 5.1 -File
# named-array binding is broken (PositionalParameterNotFound with one -LiteralPath,
# ParameterAlreadyBound with repeated ones). Positional + ValueFromRemainingArguments
# in trash.ps1 binds every target reliably, including spaces and Unicode names.
# Paths starting with '-' would be parsed as PS parameters — refuse them here.
# NEVER use rm/del/erase. Use this instead.

set -euo pipefail

if [ $# -eq 0 ]; then
  echo "Usage: trash.sh <file|dir> [file|dir ...]" >&2
  echo "Sends existing files to the Recycle Bin, or to a dated trash folder." >&2
  exit 1
fi

for arg in "$@"; do
  case "$arg" in
    -*) echo "Refusing path starting with '-' (PowerShell would parse it as a parameter): $arg" >&2; exit 1 ;;
  esac
done

trash_posix() {
  # The desktop trash if the host has one, else a dated folder: both move, never delete.
  if command -v gio >/dev/null 2>&1 && gio trash -- "$@" 2>/dev/null; then
    for target in "$@"; do echo "Recycled (gio): $target"; done
    return 0
  fi
  trash_root="${XDG_DATA_HOME:-$HOME/.local/share}/OperTrash/$(date +%Y-%m-%d)"
  mkdir -p -- "$trash_root"
  for target in "$@"; do
    [ -e "$target" ] || { echo "Not found: $target" >&2; return 1; }
    name="$(basename -- "$target")"
    destination="$trash_root/$name"
    if [ -e "$destination" ]; then
      destination="$trash_root/$name.$(date +%H%M%S).$$"
    fi
    mv -- "$target" "$destination"
    echo "Moved to trash: $target -> $destination"
  done
  return 0
}

if command -v powershell.exe >/dev/null 2>&1; then
  powershell_command="powershell.exe"
elif command -v powershell >/dev/null 2>&1; then
  powershell_command="powershell"
elif command -v pwsh.exe >/dev/null 2>&1; then
  powershell_command="pwsh.exe"
elif command -v pwsh >/dev/null 2>&1; then
  powershell_command="pwsh"
else
  trash_posix "$@"
  exit $?
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
helper_path="$script_dir/trash.ps1"
windows_targets=()

# Existence pre-check. The shell itself resolves POSIX paths of any length, so
# test the target as given first. `cygpath -u` is consulted only as a fallback
# (a caller passing a Windows-form path): it mangles RELATIVE paths longer than
# MAX_PATH into "/c/p/..." — an absolute path is converted correctly.
if command -v cygpath >/dev/null 2>&1; then
  windows_helper="$(cygpath -aw -- "$helper_path")"
  for target in "$@"; do
    posix_target="$target"
    if [ ! -e "$posix_target" ]; then
      posix_target="$(cygpath -u -- "$target" 2>/dev/null || printf '%s' "$target")"
    fi
    if [ ! -e "$posix_target" ]; then
      echo "Not found: $target" >&2
      exit 1
    fi
    windows_targets+=("$(cygpath -aw -- "$target")")
  done
elif command -v wslpath >/dev/null 2>&1; then
  windows_helper="$(wslpath -w "$helper_path")"
  for target in "$@"; do
    posix_target="$target"
    if [ ! -e "$posix_target" ]; then
      posix_target="$(wslpath -u -- "$target" 2>/dev/null || printf '%s' "$target")"
    fi
    if [ ! -e "$posix_target" ]; then
      echo "Not found: $target" >&2
      exit 1
    fi
    windows_targets+=("$(wslpath -w "$(realpath -- "$posix_target")")")
  done
else
  # PowerShell without a Windows path converter (a Linux box with pwsh): the
  # Recycle Bin is not reachable from here, so use the POSIX trash instead.
  trash_posix "$@"
  exit $?
fi

"$powershell_command" \
  -NoLogo \
  -NoProfile \
  -NonInteractive \
  -ExecutionPolicy Bypass \
  -File "$windows_helper" \
  "${windows_targets[@]}"
