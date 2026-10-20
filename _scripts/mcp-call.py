#!/usr/bin/env python3
"""mcp-call.py — generic MCP stdio bridge for the current shell session.

Mounts any stdio MCP server declared in an `.agents/mcp.json` into this shell:
every configured server becomes callable from the terminal without restarting
the client or opening a new session.

Config is read in the order {cwd}/.agents -> {cwd}/../.agents -> ~/.agents (later
wins), with per-server env resolution (github token via `gh auth token`,
telegram-userbot creds from the local .env) so a call behaves like the client's
own `<server>__<tool>` tools.

Transport is the official `mcp.client.stdio` SDK client, so Windows pipe quirks
(framing, npx.cmd, encoding) are handled rather than hand-rolled.

Usage:
  python _scripts/mcp-call.py <server> tools [--json]
  python _scripts/mcp-call.py <server> <tool> [json-args] [--timeout N] [--json]

Examples:
  python _scripts/mcp-call.py sqlite-mcp list_tables
  python _scripts/mcp-call.py knowledge-rag search_knowledge '{"query": "MCP bridge"}'
  python _scripts/mcp-call.py filesystem read_file '{"path": "AGENTS.md"}'

Non-destructive by default: it only opens a stdio MCP session and calls the
requested tool; mutating tools are invoked only if you ask for them by name.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MCP_SEARCH_DIRS = [
    Path.cwd() / ".agents",
    Path.cwd().parent / ".agents",
    Path.home() / ".agents",
]
WORKSPACE = Path(__file__).resolve().parent.parent


def load_mcp_config() -> dict:
    merged: dict = {}
    for d in MCP_SEARCH_DIRS:
        f = d / "mcp.json"
        if f.is_file():
            try:
                merged.update(json.loads(f.read_text(encoding="utf-8")).get("mcpServers") or {})
            except (OSError, json.JSONDecodeError) as exc:
                print(f"warning: unreadable {f}: {exc}", file=sys.stderr)
    return merged


def resolve_github_token() -> str | None:
    for bin in ["C:/Program Files/GitHub CLI/gh.exe", "gh"]:
        try:
            out = subprocess.run(
                [bin, "auth", "token"], capture_output=True, text=True, timeout=5
            )
            if out.stdout.strip():
                return out.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            continue
    return None


def resolve_telegram_creds() -> dict:
    env_file = Path(__file__).resolve().parent.parent / ".env"
    try:
        content = env_file.read_text(encoding="utf-8")
    except OSError:
        return {}

    def get(key: str) -> str | None:
        m = re.search(rf"^{key}\s*=\s*(.+)$", content, re.M)
        return m.group(1).strip() if m else None

    return {"id": get("TELEGRAM_API_ID"), "hash": get("TELEGRAM_API_HASH"), "session": get("TELEGRAM_SESSION_STRING")}


def build_env(server_name: str, cfg: dict) -> dict:
    env = {**os.environ, **{k: str(v) for k, v in (cfg.get("env") or {}).items()}}
    if server_name == "github":
        token = resolve_github_token()
        if not token:
            raise RuntimeError("github needs `gh auth token`; not logged in")
        env["GITHUB_PERSONAL_ACCESS_TOKEN"] = token
    if server_name == "telegram-userbot":
        creds = resolve_telegram_creds()
        if not creds.get("id") or not creds.get("hash"):
            raise RuntimeError(
                "telegram-userbot needs TELEGRAM_API_ID/TELEGRAM_API_HASH "
                "in the root .env"
            )
        env["TELEGRAM_API_ID"] = creds["id"]
        env["TELEGRAM_API_HASH"] = creds["hash"]
        if creds.get("session"):
            env["TELEGRAM_SESSION_STRING"] = creds["session"]
    return env


def resolve_command(cmd: str) -> str:
    if os.name == "nt" and cmd.lower() == "npx":
        # npx on Windows is a .cmd shim; spawning it raw fails with ENOENT
        return "npx.cmd"
    return cmd


def render_result(result) -> str:
    """Render a CallToolResult: prefer structuredContent, then text content."""
    if result.structuredContent:
        return json.dumps(result.structuredContent, ensure_ascii=False, indent=2)
    parts: list[str] = []
    for c in result.content:
        text = getattr(c, "text", None)
        if text is not None:
            parts.append(text)
        else:
            parts.append(json.dumps(c.model_dump() if hasattr(c, "model_dump") else str(c), ensure_ascii=False))
    body = "\n".join(parts) if parts else json.dumps(result.model_dump(), ensure_ascii=False, indent=2)
    return f"[isError]\n{body}" if result.isError else body


async def run_call(server_name: str, cfg: dict, tool: str, tool_args: dict, timeout: float) -> str:
    env = build_env(server_name, cfg)
    params = StdioServerParameters(
        command=resolve_command(cfg["command"]),
        args=[str(a) for a in cfg.get("args") or []],
        env=env,
        cwd=str(WORKSPACE) if WORKSPACE.is_dir() else None,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=timeout)
            if tool == "__tools__":
                tools = await asyncio.wait_for(session.list_tools(), timeout=timeout)
                return json.dumps([{"name": t.name, "description": t.description} for t in tools.tools], ensure_ascii=False, indent=2)
            result = await session.call_tool(tool, tool_args, read_timeout_seconds=timedelta(seconds=timeout))
            return render_result(result)


def main() -> int:
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    server_name = argv[0]
    config = load_mcp_config()
    cfg = config.get(server_name)
    if not cfg:
        known = ", ".join(sorted(config)) or "(none)"
        print(f"error: server '{server_name}' not found in MCP config. Known: {known}", file=sys.stderr)
        return 2
    stype = cfg.get("type", "stdio")
    if stype != "stdio":
        print(f"error: '{server_name}' is type '{stype}'; this bridge supports stdio only "
              f"(this bridge speaks stdio only; an http/sse server has to be reached "
              f"through the client's own MCP connector).", file=sys.stderr)
        return 2
    if "command" not in cfg:
        print(f"error: '{server_name}' has no command", file=sys.stderr)
        return 2

    tool: str | None = None
    as_json = False
    timeout = 60.0
    tool_args: dict = {}
    rest = argv[1:]
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--timeout" and i + 1 < len(rest):
            timeout = float(rest[i + 1])
            i += 2
            continue
        if a == "--json":
            as_json = True
            i += 1
            continue
        if a == "tools":
            tool = "__tools__"
            i += 1
            continue
        if tool is None:
            tool = a
            i += 1
            continue
        # remaining non-flag token = JSON args
        try:
            parsed = json.loads(a)
        except json.JSONDecodeError as exc:
            print(f"error: invalid JSON args: {exc}", file=sys.stderr)
            return 2
        if not isinstance(parsed, dict):
            print("error: args must be a JSON object", file=sys.stderr)
            return 2
        tool_args = parsed
        i += 1

    if tool is None:
        print(f"usage: python _scripts/mcp-call.py {server_name} tools | <tool> [json-args] [--timeout N]", file=sys.stderr)
        return 2

    try:
        rendered = asyncio.run(run_call(server_name, cfg, tool, tool_args, timeout))
        print(rendered)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
