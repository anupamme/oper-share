#!/usr/bin/env python3
"""Issue a numbered parity claim record (owner, 2026-10-09).

Usage:
  python _scripts/parity_claim.py new <slug> [--dir DIR]
  python _scripts/parity_claim.py list [--dir DIR]

`new` picks the next free number 001, 002, ... among existing records named
<digits>-*.md, creates the record from the format in _memory/parity/README.md
and prints its path. Fill the claims and paths immediately after creation.
`list` prints records whose self-reported `alive:` is yes.
Records are coordination notes, not locks (see README).
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parent.parent / "_memory" / "parity"
NUMBERED = re.compile(r"^(\d+)-.+\.md$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,50}$")


def next_number(directory: Path) -> int:
    numbers = [int(m.group(1)) for p in directory.glob("*-*.md")
               if (m := NUMBERED.match(p.name))]
    return max(numbers, default=0) + 1


def new_record(directory: Path, slug: str) -> Path:
    if not SLUG.match(slug):
        raise SystemExit("slug must be lowercase letters, digits and hyphens")
    directory.mkdir(parents=True, exist_ok=True)
    number = next_number(directory)
    path = directory / f"{number:03d}-{slug}.md"
    if path.exists():
        raise SystemExit(f"record already exists: {path}")
    now = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z")
    path.write_text(
        f"# {number:03d} {slug} — coordination\n"
        f"updated: {now}\n"
        "alive: yes\n"
        "claims:\n"
        "- [task] <current goal — fill now>\n"
        "- [file] <paths to be edited — fill now>\n"
        "notes:\n"
        "- created by _scripts/parity_claim.py\n",
        encoding="utf-8",
    )
    return path


def list_alive(directory: Path) -> list[str]:
    rows = []
    for p in sorted(directory.glob("*-*.md")):
        if not NUMBERED.match(p.name):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if re.search(r"^alive:\s*yes\b", text, re.MULTILINE):
            rows.append(p.name)
    return rows


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_new = sub.add_parser("new")
    p_new.add_argument("slug")
    p_list = sub.add_parser("list")
    for p in (p_new, p_list):
        p.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args(argv)
    if args.cmd == "new":
        print(new_record(args.dir, args.slug))
    else:
        for name in list_alive(args.dir):
            print(name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
