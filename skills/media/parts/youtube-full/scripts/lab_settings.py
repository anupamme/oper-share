"""
lab_settings.py — server-side settings store for Gemini Lab.

Everything the control panel can change lives here: chat, YouTube pipeline,
media caps and the proxy timeout. Persisted to a `settings.json` file under the
lab's own `tmp/` directory, so the same instance behaves identically from any
device (desktop / tablet).

Env vars remain the fallback defaults (GEMINI_LAB_* / YT_*), matching the
behaviour before the store existed. Settings file wins over env once saved.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Defaults — env vars are the fallback, matching the pre-store behaviour
# ---------------------------------------------------------------------------
_DEFAULTS: dict[str, Any] = {
    # chat
    "model": os.environ.get("GEMINI_LAB_MODEL", "gemini-2.5-flash"),
    "temperature": float(os.environ.get("GEMINI_LAB_TEMP", "0.7")),
    "max_tokens": int(os.environ.get("GEMINI_LAB_MAX_TOKENS", "1024")),
    "system_prompt": os.environ.get("GEMINI_LAB_SYS", ""),
    "proxy_timeout": int(os.environ.get("GEMINI_LAB_PROXY_TIMEOUT", "180")),
    # youtube pipeline
    "yt_segment_sec": int(os.environ.get("YT_SEGMENT_SEC", "60")),
    "yt_max_segments": int(os.environ.get("YT_MAX_SEGMENTS", "30")),
    "yt_frames_from_prev": int(os.environ.get("YT_FRAMES_FROM_PREV", "3")),
    "yt_rpm": int(os.environ.get("YT_RPM", "15")),
    "yt_video_max_h": int(os.environ.get("YT_VIDEO_MAX_H", "720")),
    "yt_max_retries": int(os.environ.get("YT_MAX_RETRIES", "5")),
    "yt_preview_sec": int(os.environ.get("YT_PREVIEW_SEC", "10")),
    "yt_preview_max_h": int(os.environ.get("YT_PREVIEW_MAX_H", "480")),
    # False = VAD on (default); True = vad_filter off — whisper captures singing/background
    "yt_vad": os.environ.get("YT_VAD", "0").strip().lower() in ("1", "true", "yes", "on", "да"),
    # media caps
    "max_video_bytes": int(os.environ.get("GEMINI_LAB_MAX_VIDEO_MB", "3")) * 1024 * 1024,
    "max_video_raw_bytes": int(os.environ.get("GEMINI_LAB_MAX_RAW_MB", "50")) * 1024 * 1024,
    "max_note_chars": int(os.environ.get("GEMINI_LAB_MAX_NOTE_CHARS", "12000")),
    "max_attachments_per_msg": int(os.environ.get("GEMINI_LAB_MAX_ATTACH", "8")),
    "max_img_mb": int(os.environ.get("GEMINI_LAB_MAX_IMG_MB", "12")),
    # server (informational — changing these needs a restart)
    "port": int(os.environ.get("GEMINI_LAB_PORT", "4010")),
}

# validation: key -> (min, max)
_LIMITS: dict[str, tuple[float, float]] = {
    "temperature": (0.0, 2.0),
    "max_tokens": (256, 8192),
    "proxy_timeout": (30, 3600),          # up to 60 minutes
    "yt_segment_sec": (10, 3600),
    "yt_max_segments": (1, 200),
    "yt_frames_from_prev": (0, 12),
    "yt_rpm": (1, 120),
    "yt_video_max_h": (240, 2160),
    "yt_max_retries": (0, 20),
    "yt_preview_sec": (3, 300),
    "yt_preview_max_h": (240, 1080),
    "max_video_bytes": (1 * 1024 * 1024, 200 * 1024 * 1024),
    "max_video_raw_bytes": (10 * 1024 * 1024, 1024 * 1024 * 1024),
    "max_note_chars": (1000, 100000),
    "max_attachments_per_msg": (1, 20),
    "max_img_mb": (1, 100),
    "port": (1, 65535),
}

# yt_vad is a bool — no numeric clamping, but keep it in _LIMITS shape for sanity
_LIMITS["yt_vad"] = (0.0, 1.0)

# keys saved by the panel (chat + youtube + media + timeout); port/PIN are read-only
_SAVE_KEYS = [
    "model", "temperature", "max_tokens", "system_prompt", "proxy_timeout",
    "yt_segment_sec", "yt_max_segments", "yt_frames_from_prev", "yt_rpm",
    "yt_video_max_h", "yt_max_retries", "yt_preview_sec", "yt_preview_max_h",
    "yt_vad",
    "max_video_bytes", "max_video_raw_bytes", "max_note_chars",
    "max_attachments_per_msg", "max_img_mb",
]

_PATH: Path | None = None
_cfg: dict[str, Any] | None = None
# RLock: update() holds the lock while calling load() — must be reentrant.
_lock = threading.RLock()


def _path() -> Path:
    global _PATH
    if _PATH is None:
        root = Path(__file__).resolve().parent.parent  # workspace/
        _PATH = root / "tmp" / "gemini-lab" / "settings.json"
    return _PATH


def _sanitize(k: str, v: Any) -> Any:
    """Coerce to the right type and clamp to limits."""
    if k not in _DEFAULTS:
        return v
    try:
        # bool FIRST — in Python bool is a subclass of int
        if isinstance(_DEFAULTS[k], bool):
            if isinstance(v, str):
                return v.strip().lower() in ("1", "true", "yes", "on", "да")
            return bool(v)
        if isinstance(_DEFAULTS[k], float):
            v = float(v)
            lo, hi = _LIMITS.get(k, (float("-inf"), float("inf")))
            return max(lo, min(hi, v))
        if isinstance(_DEFAULTS[k], int):
            v = int(v)
            lo, hi = _LIMITS.get(k, (float("-inf"), float("inf")))
            return max(int(lo), min(int(hi), v))
    except (TypeError, ValueError, OverflowError):  # int(inf)/int(nan) etc.
        return _DEFAULTS[k]
    return v


def load() -> dict[str, Any]:
    """Read settings from disk once; merge over defaults. Thread-safe."""
    global _cfg
    with _lock:
        if _cfg is not None:
            return dict(_cfg)
        merged = dict(_DEFAULTS)
        p = _path()
        if p.exists():
            try:
                saved = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(saved, dict):
                    for k in _SAVE_KEYS:
                        if k in saved:
                            merged[k] = _sanitize(k, saved[k])
            except Exception:
                pass  # corrupt file → fall back to defaults
        _cfg = merged
        return dict(_cfg)


def get(key: str, default: Any = None) -> Any:
    return load().get(key, _DEFAULTS.get(key, default))


def all() -> dict[str, Any]:
    """Full view for the control panel (clamped, ready to render)."""
    return load()


def update(patch: dict[str, Any]) -> dict[str, Any]:
    """Merge a partial patch (only _SAVE_KEYS), persist atomically, return merged."""
    global _cfg
    with _lock:
        cur = load()  # loads into _cfg
        for k, v in patch.items():
            if k in _SAVE_KEYS:
                if k == "model" and not str(v).strip():
                    continue  # never persist an empty model
                cur[k] = _sanitize(k, v)
        _persist(cur)
        _cfg = cur
        return dict(cur)


def reset() -> dict[str, Any]:
    """Drop the settings file and return pure defaults."""
    global _cfg
    with _lock:
        p = _path()
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
        _cfg = None
        return load()


def _persist(cfg: dict[str, Any]) -> None:
    p = _path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        tmp.replace(p)  # atomic on Windows (same volume)
    except OSError:
        pass  # never crash the server because settings can't be written
