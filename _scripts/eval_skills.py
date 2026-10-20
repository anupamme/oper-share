#!/usr/bin/env python3
"""eval_skills.py — what this package costs at startup, and whether its routers are findable.

1. Startup cost: `AGENTS.md` plus the trigger description of every router in
   `skills/`, in estimated tokens. Documents read on demand and the full skill
   bodies are measured apart and never added to that budget.
2. Trigger benchmark: every query in `BENCHMARK_QUERIES` scored against the router
   descriptions with TF-IDF + BM25, reporting Hit@1 and Hit@3; `NEGATIVE_QUERIES`
   gives the near-miss control score.

Usage:
  python _scripts/eval_skills.py            # report
  python _scripts/eval_skills.py --json     # machine-readable
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

WORKSPACE = Path(__file__).resolve().parents[1]
SKILLS_DIR = WORKSPACE / "skills"


def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def parse_skill(skill_dir: Path) -> Dict[str, str]:
    md_path = skill_dir / "SKILL.md"
    raw = md_path.read_text(encoding="utf-8", errors="ignore")
    desc = ""
    body = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            fm, body = parts[1], parts[2]
            m = re.search(r"description:\s*>?-?\s*\n((?:  .+\n)+)", fm)
            if m:
                desc = " ".join(line.strip() for line in m.group(1).splitlines())
            else:
                m2 = re.search(r"description:\s*(.+)", fm)
                if m2:
                    desc = m2.group(1).strip().strip("\"'")
    return {
        "name": skill_dir.name,
        "description": desc,
        "body": body.strip(),
        "raw": raw,
    }


def audit_context_layers() -> Dict[str, Any]:
    def read(name: str) -> str:
        path = WORKSPACE / name
        return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""

    agents_md = read("AGENTS.md")
    boot_md = read("BOOT.md")
    hosts_md = read("HOSTS.md")
    index_md = read("SKILLS.md") + read("MANIFEST.md") + read("README.md")

    skills = [
        parse_skill(d)
        for d in sorted(SKILLS_DIR.iterdir())
        if d.is_dir() and (d / "SKILL.md").is_file()
    ]
    fm_total_chars = sum(len(s["name"]) + len(s["description"]) + 20 for s in skills)
    body_total_chars = sum(len(s["raw"]) for s in skills)

    # The start-up cost is what ships here: the law plus the trigger descriptions.
    # A host's MCP schemas belong to the host and are not this script's subject.
    return {
        "package": {
            "AGENTS.md_lines": len(agents_md.splitlines()),
            "AGENTS.md_tokens": est_tokens(agents_md),
            "skill_catalog_count": len(skills),
            "skill_descriptions_tokens": fm_total_chars // 4,
            "startup_tokens": est_tokens(agents_md) + (fm_total_chars // 4),
        },
        "on_demand_reference": {
            "BOOT.md_tokens": est_tokens(boot_md),
            "HOSTS.md_tokens": est_tokens(hosts_md),
            "SKILLS_MANIFEST_README_tokens": est_tokens(index_md),
            "all_skill_bodies_tokens": body_total_chars // 4,
        },
    }


BENCHMARK_QUERIES: List[Tuple[str, str]] = [
    ("ai-image-prompts-skill", "give me proven image generation prompts with lighting, lens and composition detail"),
    ("ai-prompting", "structure a prompt with few-shot examples and output schema constraints"),
    ("antislop", "strip the AI slop phrases and rewrite this landing page copy so it sounds human"),
    ("bro", "explain that again in plain language, no jargon, like one person talking to another"),
    ("browser", "open the local web app, click through the login and capture a full-page screenshot"),
    ("decks", "build a ten-slide pptx deck from this outline and export it"),
    ("design", "redesign the dashboard typography, palette and component hierarchy"),
    ("desktop", "fix the Windows console encoding mojibake and set up a Wine game"),
    ("dev", "debug this failing endpoint, add tests and refactor the module"),
    ("documentation-writer", "write a structured technical report with a title page and numbered sources"),
    ("documents", "extract tables from a PDF and produce a formatted docx and xlsx"),
    ("email", "triage my inbox and draft replies in my own tone"),
    ("grill-me", "interview me until every architectural fork in this plan is closed"),
    ("jupyter-notebook", "create a clean reproducible notebook with pandas charts"),
    ("loops", "run an autonomous loop with a stop condition until the tests pass"),
    ("mcp", "repair a broken MCP server connection and call one of its tools"),
    ("media", "synthesize speech, transcribe a recording and stitch a quick demo video"),
    ("memory", "walk the memory tree, record a decision node and search past reports"),
    ("osint", "build a due-diligence dossier on a company and check breach exposure"),
    ("planning", "break this multi-session feature into a plan with acceptance criteria"),
    ("prompt-to-exe", "package this Python GUI script into a standalone Windows executable"),
    ("reliable-automation", "make this multi-step automation survive OAuth and flaky pages"),
    ("research", "run a multi-source research pass and verify every claim at its source"),
    ("reverse-engineering", "decompile this APK and turn its traffic into a typed API client"),
    ("review", "review this diff like a hostile critic before it ships"),
    ("security", "run an authorized API security assessment and a code audit"),
    ("ship", "prepare a release, bump dependencies and deploy the site"),
    ("skill-meta", "author a new router skill and check what it costs in the context window"),
    ("telegram", "format a rich report for Telegram and check the channel feed"),
    ("triage-route", "the target is a packed binary with no symbols, which reverse-engineering path first"),
    ("vpn", "fix a leaking tunnel and verify the exit address"),
]

NEGATIVE_QUERIES: List[str] = [
    "what is 2 + 2 in Python",
    "print current working directory",
    "rename variable x to count in main.py",
]


def tokenize(text: str) -> List[str]:
    return [t.lower() for t in re.findall(r"[A-Za-zА-Яа-я0-9_]{2,}", text)]


def run_trigger_eval() -> Dict[str, Any]:
    skills = [
        parse_skill(d)
        for d in sorted(SKILLS_DIR.iterdir())
        if d.is_dir() and (d / "SKILL.md").is_file()
    ]
    docs: Dict[str, Counter] = {}
    df: Counter = Counter()
    for s in skills:
        # Weight name + description 3x and body 1x
        toks = tokenize((s["name"].replace("-", " ") + " " + s["description"] + " ") * 3 + s["body"])
        c = Counter(toks)
        docs[s["name"]] = c
        for term in c:
            df[term] += 1

    N = max(1, len(skills))
    avgdl = sum(sum(c.values()) for c in docs.values()) / N

    def score_query(q: str) -> List[Tuple[str, float]]:
        q_toks = tokenize(q)
        scores: List[Tuple[str, float]] = []
        for name, tf_map in docs.items():
            dl = sum(tf_map.values()) or 1
            sc = 0.0
            for t in q_toks:
                tf = tf_map.get(t, 0)
                if tf == 0:
                    continue
                idf = math.log(1.0 + (N - df[t] + 0.5) / (df[t] + 0.5))
                sc += idf * (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * (dl / avgdl)))
            scores.append((name, round(sc, 3)))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    hit1 = 0
    hit3 = 0
    misses: List[Dict[str, Any]] = []
    for expected, query in BENCHMARK_QUERIES:
        ranked = score_query(query)
        top1 = ranked[0][0] if ranked else ""
        top3 = [r[0] for r in ranked[:3]]
        if top1 == expected:
            hit1 += 1
        if expected in top3:
            hit3 += 1
        else:
            misses.append({"expected": expected, "query": query, "top3": ranked[:3]})

    neg_scores = [score_query(nq)[0] for nq in NEGATIVE_QUERIES]
    total = len(BENCHMARK_QUERIES)
    return {
        "queries_tested": total,
        "hit_at_1": hit1,
        "hit_at_1_pct": round(100.0 * hit1 / total, 1),
        "hit_at_3": hit3,
        "hit_at_3_pct": round(100.0 * hit3 / total, 1),
        "misses_outside_top3": misses,
        "negative_baseline_top_scores": neg_scores,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    report = {
        "context_layers": audit_context_layers(),
        "trigger_eval": run_trigger_eval(),
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    pkg = report["context_layers"]["package"]
    on_demand = report["context_layers"]["on_demand_reference"]
    te = report["trigger_eval"]
    print(f"=== Package startup cost (IND §2) ===")
    print(f"  AGENTS.md:                {pkg['AGENTS.md_lines']} lines (~{pkg['AGENTS.md_tokens']} tokens)")
    print(f"  Skill catalog ({pkg['skill_catalog_count']} routers): ~{pkg['skill_descriptions_tokens']} tokens (descriptions only)")
    print(f"  Package startup total:    ~{pkg['startup_tokens']} tokens")
    print(f"  Read on demand:           BOOT/HOSTS/SKILLS/MANIFEST/README ~{on_demand['SKILLS_MANIFEST_README_tokens'] + on_demand['BOOT.md_tokens'] + on_demand['HOSTS.md_tokens']} tokens; all skill bodies ~{on_demand['all_skill_bodies_tokens']} tokens")
    print()
    print(f"=== Skill Trigger Benchmark (IND §1) ===")
    print(f"  Queries: {te['queries_tested']} | Hit@1: {te['hit_at_1']}/{te['queries_tested']} ({te['hit_at_1_pct']}%) | Hit@3: {te['hit_at_3']}/{te['queries_tested']} ({te['hit_at_3_pct']}%)")
    if te["misses_outside_top3"]:
        print("  Misses outside Top-3:", te["misses_outside_top3"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
