#!/usr/bin/env python3
"""sync_skills.py — publish this package's skills into the host's skill folder.

The rule this script enforces is single-writer: `skills/` here is the canon, the
host's copy is a derivative. Sync runs one way only. A skill edited in the host
folder is treated as a proposal to bring back here by hand, never as the new
truth — otherwise two copies diverge and nobody can say which one answered.

Usage
-----
  python _scripts/sync_skills.py                 # plan only
  python _scripts/sync_skills.py --apply         # copy changed skills
  python _scripts/sync_skills.py --target PATH   # explicit host folder

Target discovery, first hit wins:
  1. `--target PATH`
  2. `$SKILLS_TARGET`
  3. Freebuff Desktop: ~/.config/freebuff-desktop/account-skills/<account>/<scope>/

With no target, the script prints where it looked and exits 0: a host without a
skill folder is not an error, it simply has nothing to sync into.

Nothing is ever deleted. A skill that exists in the host folder but not here is
reported as stale and left alone; removing it is the owner's call, and removal
goes through `_scripts/trash.sh`.
"""
from __future__ import annotations

import argparse
import filecmp
import os
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "skills"
IGNORE_DIRS = frozenset({"node_modules", "__pycache__", ".git", ".venv", ".pytest_cache"})


def local_skills() -> dict[str, pathlib.Path]:
    return {
        d.name: d
        for d in sorted(SOURCE.iterdir())
        if d.is_dir() and (d / "SKILL.md").is_file()
    }


def discover_target() -> pathlib.Path | None:
    env = os.environ.get("SKILLS_TARGET")
    if env:
        return pathlib.Path(env).expanduser()
    account_root = pathlib.Path.home() / ".config" / "freebuff-desktop" / "account-skills"
    counts: dict[pathlib.Path, int] = {}
    for skill_md in account_root.glob("*/*/*/SKILL.md"):
        scope = skill_md.parent.parent
        counts[scope] = counts.get(scope, 0) + 1
    return max(counts, key=counts.get) if counts else None


def differs(src: pathlib.Path, dst: pathlib.Path) -> bool:
    if not dst.exists():
        return True
    cmp = filecmp.dircmp(src, dst)
    kept = lambda names: [n for n in names if n not in IGNORE_DIRS]  # noqa: E731
    if kept(cmp.left_only) or kept(cmp.right_only) or cmp.diff_files or cmp.funny_files:
        return True
    return any(differs(src / sub, dst / sub) for sub in kept(cmp.common_dirs))


def copy_skill(src: pathlib.Path, dst: pathlib.Path) -> None:
    ignore = shutil.ignore_patterns(*IGNORE_DIRS, "*.pyc", ".DS_Store")
    if dst.exists():
        staging = dst.with_name(dst.name + ".incoming")
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(src, staging, ignore=ignore)
        shutil.rmtree(dst)
        staging.rename(dst)
    else:
        shutil.copytree(src, dst, ignore=ignore)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish skills/ into the host skill folder (one writer: this tree)."
    )
    parser.add_argument("--apply", action="store_true", help="write files (default: plan only)")
    parser.add_argument("--target", type=pathlib.Path, help="host skill folder")
    args = parser.parse_args()

    skills = local_skills()
    if not skills:
        print(f"no skills under {SOURCE}", file=sys.stderr)
        return 1

    target = args.target or discover_target()
    if target is None or not target.is_dir():
        print("no host skill folder found; nothing to sync.")
        print("looked for: --target, $SKILLS_TARGET,")
        print("            ~/.config/freebuff-desktop/account-skills/<account>/<scope>/")
        print(f"canon: {SOURCE} ({len(skills)} routers)")
        return 0

    changed = [name for name, src in skills.items() if differs(src, target / name)]
    stale = sorted(
        d.name
        for d in target.iterdir()
        if d.is_dir() and (d / "SKILL.md").is_file() and d.name not in skills
    )

    print(f"target:  {target}")
    print(f"canon:   {len(skills)} routers")
    print(f"changed: {len(changed)}" + (": " + ", ".join(changed) if changed else ""))
    if stale:
        print(f"stale:   {len(stale)} not in this tree (left alone): {', '.join(stale)}")

    if not args.apply:
        if changed:
            print("dry run: pass --apply to copy")
        return 0

    for name in changed:
        copy_skill(skills[name], target / name)
        print(f"copied {name}")
    print(f"done: {len(changed)} skill folders updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
