"""Fail CI when active repository files contain new plaintext secrets.

The scanner is stdlib-only and deliberately prints metadata, never matched
values or fingerprints. Historical/raw collections are handled by the
documented quarantine policy instead of being silently normalized.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASELINE = Path(__file__).with_name("secret_gate_baseline.txt")

PROHIBITED_PARTS = frozenset({"unfiltered", "jailbreak", "jb-archive"})
QUARANTINE_PREFIXES = (
    "_archive/",     # cold storage: never active code
    "_backups/",     # backup snapshots, never the live tree
    "experiments/",
    "inbox/",        # imported external material
    "logs/",
    "tmp/",
)
QUARANTINE_PARTS = frozenset()  # add a name here when a folder is known junk

PLACEHOLDER_MARKERS = (
    "changeme",
    "dummy",
    "example",
    "fake",
    "placeholder",
    "redacted",
    "sample",
    "test",
    "xxxxx",
    "your_",
)
ENV_REFERENCE_PATTERN = re.compile(
    r"""(?ix)^
    (?:
        os[.]environ/
        | process[.]env[.]
        | secret_key_ref[:=/]
        | valuefrom[:=/]
    )
    [A-Z_][A-Z0-9_]*
    $"""
)
# Module-attribute references (e.g. config.LLM_API_KEY, settings.api_key):
# structurally a Python identifier chain, not a literal secret value.
# Attribute part allows NO digits: real key constants don't contain digits,
# and digit-bearing attrs are how substring-bypass values (e.g.
# `opaqueprocess.envCredential123456789`) try to smuggle past the gate.
MODULE_REFERENCE_PATTERN = re.compile(
    r"""(?ix)^
    [a-z_][a-z0-9_]*
    [.]
    [A-Za-z_]+  
    $"""
)

SECRET_PATTERNS = (
    (
        "openai-style-token",
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
        0,
    ),
    (
        "github-token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
        0,
    ),
    (
        "slack-token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
        0,
    ),
    (
        "telegram-bot-token",
        re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b"),
        0,
    ),
    (
        "google-api-key",
        re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
        0,
    ),
    (
        "aws-access-key",
        re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
        0,
    ),
    (
        "private-key-material",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
        0,
    ),
    (
        "literal-secret-assignment",
        re.compile(
            r"""(?ix)
            \b(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret(?:[_-]?key)?
            |password|passwd|telegram_bot_token|litellm_master_key)\b
            \s*[:=]\s*["']?([A-Za-z0-9_./+=:-]{16,})
            """
        ),
        1,
    ),
)


@dataclass(frozen=True)
class Finding:
    """A redacted secret candidate."""

    path: str
    line: int
    detector: str
    digest: str

    @property
    def baseline_key(self) -> tuple[str, str, str]:
        """Return the stable, non-secret baseline identity."""
        return self.path, self.detector, self.digest


def normalize_repo_path(path: str) -> str:
    """Normalize a Git path without resolving or opening it.

    Never use ``str.lstrip("./")`` here: lstrip strips *any* leading ``.``/``/``
    character, which turned ``.agents/skills/x.py`` into ``agents/skills/x.py``
    and made the gate silently skip every file inside a dot-directory
    (``.agents/``, ``.github/``, ``.githooks/``, ``.claude/``).
    ``PurePosixPath`` already drops a leading ``./``, so no manual strip is needed.
    """
    return PurePosixPath(path.replace("\\", "/")).as_posix()


def is_prohibited(path: str) -> bool:
    """Return True for paths that must never be opened by this scanner."""
    parts = {part.lower() for part in PurePosixPath(normalize_repo_path(path)).parts}
    return bool(parts & PROHIBITED_PARTS)


def is_quarantined(path: str) -> bool:
    """Return True for documented historical/raw corpus paths."""
    normalized = normalize_repo_path(path)
    lowered = normalized.lower()
    if any(lowered.startswith(prefix) for prefix in QUARANTINE_PREFIXES):
        return True
    parts = {part.lower() for part in PurePosixPath(normalized).parts}
    return bool(parts & QUARANTINE_PARTS)


def _looks_like_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    if ENV_REFERENCE_PATTERN.fullmatch(value.strip()):
        return True
    if MODULE_REFERENCE_PATTERN.fullmatch(value.strip()):
        return True

    for marker in PLACEHOLDER_MARKERS:
        if lowered == marker:
            return True
        if not lowered.startswith(marker):
            continue
        suffix = lowered[len(marker) :].lstrip("-_./:")
        if suffix and len(set(suffix)) <= 2:
            return True
    return False


def _resolved_path_policy(resolved_root: Path, absolute: Path) -> str:
    """Classify a resolved path before any content I/O."""
    try:
        relative = absolute.relative_to(resolved_root).as_posix()
    except ValueError:
        return "prohibited"
    if is_prohibited(relative):
        return "prohibited"
    if is_quarantined(relative):
        return "quarantined"
    return "active"


def scan_text(text: str, path: str) -> list[Finding]:
    """Scan text and return findings without retaining or exposing values."""
    findings: list[Finding] = []
    normalized = normalize_repo_path(path)
    for line_number, line in enumerate(text.splitlines(), 1):
        for detector, pattern, value_group in SECRET_PATTERNS:
            for match in pattern.finditer(line):
                value = match.group(value_group)
                if _looks_like_placeholder(value):
                    continue
                digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
                findings.append(Finding(normalized, line_number, detector, digest))
    return findings


def _decode_git_paths(stdout: bytes) -> list[str]:
    """Decode a NUL-separated git path list."""
    return [
        item.decode("utf-8", errors="surrogateescape")
        for item in stdout.split(b"\0")
        if item
    ]


def _git_candidate_paths(root: Path) -> list[str]:
    """List tracked and non-ignored untracked files using NUL delimiters."""
    process = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode:
        error = process.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git ls-files failed: {error}")
    return _decode_git_paths(process.stdout)


def _staged_candidate_paths(root: Path) -> list[str]:
    """List added/copied/modified/renamed files in the index (pre-commit mode).

    Scanning only staged paths keeps one agent's untracked scratch files from
    blocking an unrelated commit; the whole-tree scan stays the CI behaviour.
    """
    process = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMR",
            "-z",
        ],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode:
        error = process.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git diff --cached failed: {error}")
    return _decode_git_paths(process.stdout)


def _is_binary(path: Path) -> bool:
    with path.open("rb") as stream:
        return b"\0" in stream.read(4096)


def scan_paths(root: Path, paths: Iterable[str]) -> tuple[list[Finding], int, int]:
    """Scan allowed files and return findings plus quarantine/prohibited counts."""
    findings: list[Finding] = []
    quarantined = 0
    prohibited = 0
    resolved_root = root.resolve()

    for raw_path in paths:
        path = normalize_repo_path(raw_path)
        if is_prohibited(path):
            prohibited += 1
            continue
        if is_quarantined(path):
            quarantined += 1
            continue

        absolute = (root / Path(path)).resolve()
        resolved_policy = _resolved_path_policy(resolved_root, absolute)
        if resolved_policy == "prohibited":
            prohibited += 1
            continue
        if resolved_policy == "quarantined":
            quarantined += 1
            continue
        if not absolute.is_file() or _is_binary(absolute):
            continue
        text = absolute.read_text(encoding="utf-8", errors="replace")
        findings.extend(scan_text(text, path))

    return findings, quarantined, prohibited


def load_baseline(path: Path) -> set[tuple[str, str, str]]:
    """Load path/detector/SHA-256 entries from the baseline."""
    entries: set[tuple[str, str, str]] = set()
    if not path.exists():
        return entries
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3 or not re.fullmatch(r"[0-9a-f]{64}", parts[2]):
            raise ValueError(f"{path}:{line_number}: invalid redacted baseline entry")
        entries.add((normalize_repo_path(parts[0]), parts[1], parts[2]))
    return entries


def render_findings(findings: Iterable[Finding]) -> str:
    """Render only locations and detector names; values stay redacted."""
    return "\n".join(
        f"- {finding.path}:{finding.line} [{finding.detector}] value=[REDACTED]"
        for finding in findings
    )


def main(argv: list[str] | None = None) -> int:
    """Run the repository secret prevention gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument(
        "--staged",
        action="store_true",
        help="scan only staged added/copied/modified/renamed paths (pre-commit mode)",
    )
    args = parser.parse_args(argv)

    try:
        baseline = load_baseline(args.baseline)
        candidates = (
            _staged_candidate_paths(args.root)
            if args.staged
            else _git_candidate_paths(args.root)
        )
        findings, quarantined, prohibited = scan_paths(args.root, candidates)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"SECRET_GATE_ERROR: {exc}", file=sys.stderr)
        return 2

    new_findings = [
        finding for finding in findings if finding.baseline_key not in baseline
    ]
    if new_findings:
        print(
            f"SECRET_GATE_FAIL: {len(new_findings)} new secret candidate(s); "
            "matched values are always redacted.",
            file=sys.stderr,
        )
        print(render_findings(new_findings), file=sys.stderr)
        return 1

    print(
        "SECRET_GATE_PASS: no new active-code secrets; "
        f"quarantined_paths={quarantined}, prohibited_paths_skipped={prohibited}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
