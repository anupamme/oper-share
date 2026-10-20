#!/usr/bin/env python3
"""memory.py — the RSI memory tree, stdlib only.

One SQLite file (`_memory/memora.db` by default) holding nodes that never
overwrite each other: a changed decision is a new node with a `supersedes` edge,
and both directions of that edge are written, so lineage resolves from either end.

Verbs
-----
  init                          create the store and its indexes
  branch --content TEXT         add a node
  verdict --id N --status S     promote or prune an existing node
  walk [--root ROOT]            read a tree, champion and dead-ends first
  search QUERY                  full-text search over nodes and report fragments
  reindex-reports [--dir DIR]   (re)index `_memory/reports/` by section
  render [--output PATH]        draw the local graph view

Every node carries provenance. The ten types are the ones the workspace agreed
on: owner_decision, owner_preference, owner_manual_edit, external_brief,
verified_observation, measurement, incident_lesson, architecture_choice,
external_source, agent_hypothesis. A node whose type is `agent_hypothesis` and
that names no source is reported as unverified by `walk`.

Store location: `_memory/memora.db`, or `--db PATH`, or `$MEMORY_DB`.
Python 3.9+, no third-party packages.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "_memory" / "memora.db"
REPORTS_DIR = ROOT / "_memory" / "reports"
GRAPH = ROOT / "_memory" / "memora-graph.html"

PROVENANCE = (
    "owner_decision",
    "owner_preference",
    "owner_manual_edit",
    "external_brief",
    "verified_observation",
    "measurement",
    "incident_lesson",
    "architecture_choice",
    "external_source",
    "agent_hypothesis",
)
STATUSES = ("promoted", "pruned", "active")

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    metadata TEXT,
    tags TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,
    importance REAL DEFAULT 1.0,
    last_accessed TEXT,
    access_count INTEGER DEFAULT 0
);
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(content, metadata, tags);
CREATE VIRTUAL TABLE IF NOT EXISTS report_chunks_fts
    USING fts5(report_path, report_date, section_title, content, tokenize='unicode61');
"""


def db_path(arg: str | None) -> Path:
    if arg:
        return Path(arg).expanduser()
    env = os.environ.get("MEMORY_DB")
    return Path(env).expanduser() if env else DEFAULT_DB


def connect(path: Path, create: bool = False) -> sqlite3.Connection:
    if not create and not path.exists():
        raise SystemExit(
            f"no store at {path}\n"
            "Create it with: python _scripts/memory.py init"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def load_meta(row: sqlite3.Row) -> dict:
    try:
        return json.loads(row["metadata"] or "{}")
    except json.JSONDecodeError:
        return {}


# --------------------------------------------------------------------- verbs

def cmd_init(args) -> int:
    path = db_path(args.db)
    conn = connect(path, create=True)
    conn.commit()
    existing = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    print(f"store: {path}")
    print(f"nodes: {existing}")
    print(
        "verbs: branch --content ... | walk [--root ...] | verdict --id ... "
        "| search ... | reindex-reports | render"
    )
    return 0


def cmd_branch(args) -> int:
    if args.provenance not in PROVENANCE:
        raise SystemExit(f"provenance must be one of: {', '.join(PROVENANCE)}")
    if args.status not in STATUSES:
        raise SystemExit(f"status must be one of: {', '.join(STATUSES)}")
    path = db_path(args.db)
    conn = connect(path, create=True)
    meta = {
        "root_path": args.root,
        "rsi_status": args.status,
        "provenance": args.provenance,
        "project": args.project,
        "outcome": args.outcome,
        "score": args.score,
        "writer": os.environ.get("MEMORY_WRITER") or f"{os.uname().nodename}:{os.getpid()}"
        if hasattr(os, "uname") else os.environ.get("MEMORY_WRITER", "local"),
        "valid_from": args.valid_from or dt.date.today().isoformat(),
        "recorded_at": now(),
        "parent_id": args.parent,
        "source": args.source,
        "supersedes": [],
        "superseded_by": [],
    }
    if args.valid_until:
        meta["valid_until"] = args.valid_until

    cur = conn.execute(
        "INSERT INTO memories (content, metadata, tags, created_at) VALUES (?, ?, ?, ?)",
        (args.content, json.dumps(meta, ensure_ascii=False), ",".join(args.tag or []), now()),
    )
    node_id = cur.lastrowid

    if args.supersedes:
        for old_id in args.supersedes:
            old = conn.execute("SELECT metadata FROM memories WHERE id = ?", (old_id,)).fetchone()
            if not old:
                print(f"warning: node {old_id} does not exist; edge skipped", file=sys.stderr)
                continue
            old_meta = load_meta(old)
            meta["supersedes"].append(old_id)
            old_meta.setdefault("superseded_by", []).append(node_id)
            conn.execute(
                "UPDATE memories SET metadata = ?, updated_at = ? WHERE id = ?",
                (json.dumps(old_meta, ensure_ascii=False), now(), old_id),
            )
        conn.execute(
            "UPDATE memories SET metadata = ? WHERE id = ?",
            (json.dumps(meta, ensure_ascii=False), node_id),
        )

    conn.execute(
        "INSERT INTO memories_fts (rowid, content, metadata, tags) VALUES (?, ?, ?, ?)",
        (node_id, args.content, json.dumps(meta, ensure_ascii=False), ",".join(args.tag or [])),
    )
    conn.commit()
    print(f"node {node_id} — {args.status} — {args.root}")
    if meta["supersedes"]:
        print(f"supersedes: {', '.join(str(i) for i in meta['supersedes'])}")
    return 0


def cmd_verdict(args) -> int:
    if args.status not in STATUSES:
        raise SystemExit(f"status must be one of: {', '.join(STATUSES)}")
    path = db_path(args.db)
    conn = connect(path)
    row = conn.execute("SELECT metadata FROM memories WHERE id = ?", (args.id,)).fetchone()
    if not row:
        raise SystemExit(f"no node {args.id}")
    meta = load_meta(row)
    meta["rsi_status"] = args.status
    if args.outcome is not None:
        meta["outcome"] = args.outcome
    if args.score is not None:
        meta["score"] = args.score
    for old_id in args.supersedes or []:
        meta.setdefault("supersedes", []).append(old_id)
        old = conn.execute("SELECT metadata FROM memories WHERE id = ?", (old_id,)).fetchone()
        if old:
            old_meta = load_meta(old)
            old_meta.setdefault("superseded_by", []).append(args.id)
            conn.execute(
                "UPDATE memories SET metadata = ?, updated_at = ? WHERE id = ?",
                (json.dumps(old_meta, ensure_ascii=False), now(), old_id),
            )
    conn.execute(
        "UPDATE memories SET metadata = ?, updated_at = ? WHERE id = ?",
        (json.dumps(meta, ensure_ascii=False), now(), args.id),
    )
    conn.commit()
    print(f"node {args.id} -> {args.status}")
    return 0


def _roots(conn) -> list[str]:
    seen = {}
    for row in conn.execute("SELECT metadata FROM memories"):
        root = load_meta(row).get("root_path") or "(no root)"
        seen[root] = seen.get(root, 0) + 1
    return sorted(seen)


def cmd_walk(args) -> int:
    path = db_path(args.db)
    conn = connect(path)
    query = "SELECT * FROM memories"
    params: list = []
    if args.root:
        query += " WHERE json_extract(metadata, '$.root_path') = ?"
        params.append(args.root)
    if args.status:
        clause = "json_extract(metadata, '$.rsi_status') = ?"
        query += (" AND " if params else " WHERE ") + clause
        params.append(args.status)
    query += " ORDER BY json_extract(metadata, '$.parent_id'), id"
    rows = conn.execute(query, params).fetchall()

    if args.json:
        print(json.dumps([{"id": r["id"], "content": r["content"], "meta": load_meta(r)} for r in rows],
                         ensure_ascii=False, indent=2))
        return 0

    if not rows:
        print("nothing recorded under this filter")
        if args.root:
            print("roots with nodes: " + (", ".join(_roots(conn)) or "none"))
        return 0

    by_parent: dict = {}
    for row in rows:
        meta = load_meta(row)
        by_parent.setdefault(meta.get("parent_id"), []).append((row, meta))

    def render(parent, depth):
        for row, meta in by_parent.get(parent, []):
            status = meta.get("rsi_status", "?")
            mark = {"promoted": "[+]", "pruned": "[-]", "active": "[ ]"}.get(status, "[?]")
            head = "  " * depth + f"{mark} #{row['id']} {meta.get('provenance', '')}"
            flags = []
            if meta.get("outcome"):
                flags.append(meta["outcome"])
            if meta.get("provenance") == "agent_hypothesis" and not meta.get("source"):
                flags.append("unverified")
            if meta.get("supersedes"):
                flags.append("supersedes " + ",".join(str(i) for i in meta["supersedes"]))
            if meta.get("superseded_by"):
                flags.append("replaced by " + ",".join(str(i) for i in meta["superseded_by"]))
            print(head + ((" — " + "; ".join(flags)) if flags else ""))
            body = " ".join(row["content"].split())
            print("  " * depth + "   " + (body[:160] + ("…" if len(body) > 160 else "")))
            render(row["id"], depth + 1)

    render(None, 0)
    orphans = [r for r, m in sum(by_parent.values(), []) if m.get("parent_id") and m["parent_id"] not in {x["id"] for x in rows}]
    for row in orphans:
        meta = load_meta(row)
        print(f"[?] #{row['id']} {meta.get('provenance','')} — parent {meta.get('parent_id')} outside this walk")
    return 0


def cmd_search(args) -> int:
    path = db_path(args.db)
    conn = connect(path)
    rows = conn.execute(
        """
        SELECT rowid AS id, snippet(memories_fts, 0, '[', ']', '…', 12) AS text,
               'node' AS kind, '' AS where_
        FROM memories_fts WHERE memories_fts MATCH ?
        ORDER BY rank LIMIT ?
        """,
        (args.query, args.limit),
    ).fetchall()
    chunks = conn.execute(
        """
        SELECT rowid AS id, snippet(report_chunks_fts, 3, '[', ']', '…', 18) AS text,
               'report' AS kind, report_path || ' § ' || section_title AS where_
        FROM report_chunks_fts WHERE report_chunks_fts MATCH ?
        ORDER BY rank LIMIT ?
        """,
        (args.query, args.limit),
    ).fetchall()
    if not rows and not chunks:
        print("no match")
        return 0
    for row in rows:
        print(f"[node #{row['id']}] {row['text']}")
    for row in chunks:
        print(f"[report] {row['where_']}\n    {row['text']}")
    return 0


def cmd_reindex(args) -> int:
    path = db_path(args.db)
    conn = connect(path)
    directory = Path(args.dir) if args.dir else REPORTS_DIR
    if not directory.is_dir():
        print(f"no reports directory at {directory}")
        return 0
    conn.execute("DELETE FROM report_chunks_fts")
    count = 0
    for md in sorted(directory.rglob("*.md")):
        rel = md.relative_to(ROOT).as_posix() if md.is_relative_to(ROOT) else md.as_posix()
        date = md.name[:10] if md.name[:10].count("-") == 2 else ""
        section, buffer = "(intro)", []
        for line in md.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("## "):
                if buffer:
                    conn.execute(
                        "INSERT INTO report_chunks_fts (report_path, report_date, section_title, content) VALUES (?,?,?,?)",
                        (rel, date, section, "\n".join(buffer)),
                    )
                    count += 1
                section, buffer = line[3:].strip(), []
            else:
                buffer.append(line)
        if buffer:
            conn.execute(
                "INSERT INTO report_chunks_fts (report_path, report_date, section_title, content) VALUES (?,?,?,?)",
                (rel, date, section, "\n".join(buffer)),
            )
            count += 1
    conn.commit()
    print(f"indexed {count} fragments from {directory}")
    return 0


def cmd_render(args) -> int:
    path = db_path(args.db)
    conn = connect(path)
    out = Path(args.output) if args.output else GRAPH
    rows = conn.execute("SELECT * FROM memories ORDER BY json_extract(metadata,'$.root_path'), id").fetchall()
    groups: dict = {}
    edges = []
    for row in rows:
        meta = load_meta(row)
        groups.setdefault(meta.get("root_path") or "(no root)", []).append((row, meta))
        for old in meta.get("supersedes", []):
            edges.append((row["id"], old))

    color = {"promoted": "#1f7a3d", "pruned": "#a33", "active": "#777"}
    parts = [
        "<!doctype html><meta charset='utf-8'><title>Memory tree</title>",
        "<style>body{font:14px/1.5 system-ui,sans-serif;margin:2rem;max-width:60rem}"
        "h2{margin:2rem 0 .5rem;font-size:1rem;letter-spacing:.04em;text-transform:uppercase;color:#555}"
        ".n{border-left:3px solid #ccc;padding:.35rem .7rem;margin:.25rem 0}"
        ".id{color:#888}.p{font-size:.8rem;color:#666}pre{white-space:pre-wrap}</style>",
        f"<h1>Memory tree</h1><p class='p'>{len(rows)} nodes · generated {dt.datetime.now():%Y-%m-%d %H:%M}</p>",
    ]
    for root, items in groups.items():
        parts.append(f"<h2>{html.escape(root)}</h2>")
        for row, meta in items:
            status = meta.get("rsi_status", "?")
            body = " ".join(row["content"].split())
            parts.append(
                f"<div class='n' style='border-color:{color.get(status, '#ccc')}'>"
                f"<span class='id'>#{row['id']}</span> "
                f"<b>{html.escape(status)}</b> "
                f"<span class='p'>{html.escape(meta.get('provenance', ''))}</span>"
                f"<pre>{html.escape(body[:400])}</pre></div>"
            )
    if edges:
        parts.append("<h2>supersedes</h2><pre>")
        for new, old in edges:
            parts.append(f"#{new} → #{old}\n")
        parts.append("</pre>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {out}")
    return 0


# ---------------------------------------------------------------------- main

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="memory.py", description="RSI memory tree (stdlib SQLite)."
    )
    parser.add_argument("--db", help="store path (default _memory/memora.db)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="create the store")

    b = sub.add_parser("branch", help="add a node")
    b.add_argument("--content", required=True)
    b.add_argument("--root", default="root/workspace")
    b.add_argument("--parent", type=int)
    b.add_argument("--provenance", default="agent_hypothesis", choices=PROVENANCE)
    b.add_argument("--status", default="active", choices=STATUSES)
    b.add_argument("--outcome")
    b.add_argument("--score", type=float)
    b.add_argument("--project")
    b.add_argument("--source", help="where a hypothesis or external claim comes from")
    b.add_argument("--supersedes", type=int, action="append")
    b.add_argument("--tag", action="append")
    b.add_argument("--valid-from")
    b.add_argument("--valid-until")

    v = sub.add_parser("verdict", help="promote or prune a node")
    v.add_argument("--id", type=int, required=True)
    v.add_argument("--status", required=True, choices=STATUSES)
    v.add_argument("--outcome")
    v.add_argument("--score", type=float)
    v.add_argument("--supersedes", type=int, action="append")

    w = sub.add_parser("walk", help="read a tree")
    w.add_argument("--root")
    w.add_argument("--status", choices=STATUSES)
    w.add_argument("--json", action="store_true")

    s = sub.add_parser("search", help="full-text search")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=8)

    r = sub.add_parser("reindex-reports", help="index _memory/reports by section")
    r.add_argument("--dir")

    g = sub.add_parser("render", help="write the graph view")
    g.add_argument("--output")

    args = parser.parse_args(argv)
    handlers = {
        "init": cmd_init,
        "branch": cmd_branch,
        "verdict": cmd_verdict,
        "walk": cmd_walk,
        "search": cmd_search,
        "reindex-reports": cmd_reindex,
        "render": cmd_render,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
