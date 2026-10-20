"""
youtube_pipeline.py — full-video analysis for Gemini Lab.

Turns any YouTube URL into a structured lore report:

    download → probe → adaptive segment → one-pass ASR → per-segment Gemini chain → synthesis

The FULL audio track is transcribed ONCE (with timestamps); every segment is
then sent to Gemini WHOLE (video + full video transcript, its own lines marked
">>"), together with a rolling summary ("РАНЕЕ") from previous segments and a
few freeze-frames from the previous segment (visual memory). Segments are
NEVER skipped: a failed segment is retried until success (or the job fails).

Design: docs/superpowers/specs/2026-08-06-youtube-pipeline-design.md

The module is self-contained (stdlib + yt-dlp/ffmpeg/ffprobe on PATH). It takes
two callbacks from the host app so there is no circular import:
    chat(openai_body)  -> (parsed_json, http_code)
    transcribe(path)   -> str
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Optional

from lab_settings import get as _settings_get  # dynamic config (control panel)

_DEFAULT_MODEL = os.environ.get("GEMINI_LAB_MODEL", "gemini-2.5-flash")

_NW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _which(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"{name} не найден в PATH")
    return found


# ===========================================================================
# Prompt templates
# ===========================================================================
SEGMENT_SYSTEM = """Ты — ассистент по анализу видео для лор-проекта. Ты смотришь ОДИН сегмент видео.

Тебе даются: видео сегмента целиком, ПОЛНЫЙ транскрипт речи всего видео (строки с пометкой «>>» — речь именно этого сегмента, остальное — контекст всего видео), стоп-кадры прошлого сегмента (визуальная память) и сводка «РАНЕЕ» — что происходило до этого момента.

Твоя задача:
1. Подробно опиши ИМЕННО ЭТОТ сегмент: события, действия, персонажи, окружение, визуальные детали (костюмы, локации, стиль, цвет, атмосфера), диалоги и точные цитаты. Опирайся на видео сегмента; полный транскрипт используй как контекст — лови коллбеки, отсылки и форшоудинг, но НЕ описывай события других сегментов.
2. В конце ответь блоком «ПЕРЕДАЧА ДАЛЬШЕ:» — сжатая сводка этого сегмента (3-5 предложений), которая станет контекстом «РАНЕЕ» для следующего сегмента. Выдели самое важное, что нужно помнить дальше.

Формат ответа:
[ОПИСАНИЕ СЕГМЕНТА]
<подробное описание>

ПЕРЕДАЧА ДАЛЬШЕ:
<сжатая сводка>"""

SEGMENT_USER = """РАНЕЕ (история до этого сегмента):
{prev_summary}

ТРАНСКРИПТ ВСЕГО ВИДЕО (>> — реплики ЭТОГО сегмента, остальное — контекст):
{transcript}

[Ниже: видео сегмента целиком]{frames_note}"""

SYNTH_SYSTEM = """Ты — ассистент по анализу видео для лор-проекта. Перед тобой сводки всех сегментов видео в хронологическом порядке.

Составь итоговый структурный отчёт в Markdown:

# Таймлайн событий
- <MM:SS> — <событие>   (таймкоды по возможности)

# Персонажи
- <имя/описание> — где появляется, что делает

# Визуальные детали
- костюмы, локации, стиль, цветокор, атмосфера (важно для лора)

# Цитаты
- <ключевые реплики>

# Ключевое для лора
- что важно для мира/сеттинга: идеи, мотивы, символизм

Будь конкретен и точен, опирайся только на факты из сводок. Не выдумывай."""


# ===========================================================================
# Small helpers
# ===========================================================================
def _run(args: list[str], timeout: int, **kw: Any) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout, creationflags=_NW, **kw,
    )


def _probe_duration(path: Path) -> float:
    """ffprobe duration in seconds (0 on failure)."""
    ffprobe = _which("ffprobe")
    try:
        r = _run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                  "-of", "default=noprint_wrappers=1:nokey=1", str(path)], 60)
        return float(r.stdout.strip()) if r.stdout.strip() else 0.0
    except Exception:
        return 0.0


def _cut_segment(src: Path, dst: Path, start: float, dur: float) -> bool:
    """Accurate cut: re-encode to 480p h264 so -ss lands on the right frame."""
    ffmpeg = _which("ffmpeg")
    try:
        _run([
            ffmpeg, "-y", "-loglevel", "error",
            "-ss", f"{start:.2f}", "-i", str(src), "-t", f"{dur:.2f}",
            "-vf", "scale=480:-2", "-pix_fmt", "yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
            "-movflags", "+faststart", str(dst),
        ], 600)
        return dst.exists() and dst.stat().st_size > 0
    except Exception:
        return False


def _extract_frames(src: Path, out_dir: Path, n: int, seg_len: float) -> list[Path]:
    """n freeze-frames spread across the segment."""
    ffmpeg = _which("ffmpeg")
    fps = max(0.05, min(float(n) / max(seg_len, 1.0), 2.0))
    out_dir.mkdir(parents=True, exist_ok=True)
    pat = str(out_dir / "f-%02d.jpg")
    try:
        _run([
            ffmpeg, "-y", "-loglevel", "error", "-i", str(src),
            "-vf", f"fps={fps:.3f}", "-frames:v", str(n),
            "-q:v", "4", pat,
        ], 180)
    except Exception:
        pass
    return sorted(out_dir.glob("f-*.jpg"))[:n]


def _data_uri_media(path: Path) -> str:
    """data: URI (base64) for a media file."""
    mime = "video/mp4" if path.suffix.lower() == ".mp4" else "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _extract_next_summary(text: str, fallback: str) -> str:
    """Pull the text after «ПЕРЕДАЧА ДАЛЬШЕ:»; fall back to the whole answer."""
    m = re.search(r"ПЕРЕДАЧА ДАЛЬШЕ\s*[:\-]\s*(.*)", text, re.S | re.I)
    if m and m.group(1).strip():
        return m.group(1).strip()
    return fallback.strip() or (text or "").strip()[:2000]


def _slice_transcript(
    segs: list[tuple[float, float, str]],
    start: float,
    dur: float,
    full: bool,
) -> str:
    """Slice transcribed segments by the time window [start, start + dur).

    full=True  → the WHOLE transcript, lines inside this window marked "»"
    full=False → only lines inside this window (for the chat-chip sidecar)
    """
    end = start + dur
    lines: list[str] = []
    for s, e, t in segs:
        overlap = s < end and e > start
        if full:
            mark = ">>" if overlap else "  "
            ts = f"[{int(s // 60):02d}:{int(s % 60):02d}]"
            lines.append(f"{mark} {ts} {t}")
        elif overlap:
            lines.append(t)
    return "\n".join(lines)


# ===========================================================================
# YouTubePipeline
# ===========================================================================
class YouTubePipeline:
    def __init__(
        self,
        chat: Callable[[dict], tuple[dict, int]],
        transcribe: Callable[..., str],
        media_dir: Path,
        model: str,
        transcribe_segments: Optional[Callable[..., list[tuple[float, float, str]]]] = None,
    ) -> None:
        self.chat = chat
        self.transcribe = transcribe
        self.transcribe_segments = transcribe_segments
        self.media_dir = media_dir
        self.model = model
        self.work_root = media_dir / "jobs"
        self.work_root.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, dict] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------- public API
    def _job_cfg(self) -> dict[str, Any]:
        """Snapshot of the dynamic settings at job start (config is frozen
        per job — mid-run panel edits never corrupt a running analysis)."""
        return {
            k: _settings_get(k)
            for k in (
                "yt_segment_sec", "yt_max_segments", "yt_frames_from_prev",
                "yt_rpm", "yt_video_max_h", "yt_max_retries",
                "yt_preview_sec", "yt_preview_max_h", "yt_vad",
            )
        }

    def start(self, url: str) -> str:
        """Create a job and kick off the background pipeline thread."""
        job_id = uuid.uuid4().hex[:12]
        job: dict = {
            "id": job_id,
            "url": url,
            "status": "queued",
            "step": "очередь",
            "done": 0,
            "total": 0,
            "error": "",
            "result": None,
            "report": "",
            "cancel": threading.Event(),
            "cfg": self._job_cfg(),
            "model": _settings_get("model", self.model or _DEFAULT_MODEL),
        }
        with self._lock:
            self._jobs[job_id] = job
        threading.Thread(target=self._run_job, args=(job,), daemon=True).start()
        return job_id

    def status(self, job_id: str) -> Optional[dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return {
                "id": job["id"],
                "status": job["status"],
                "step": job["step"],
                "done": job["done"],
                "total": job["total"],
                "error": job["error"],
                "result": job["result"],
            }

    def report(self, job_id: str) -> str:
        with self._lock:
            job = self._jobs.get(job_id)
            return (job or {}).get("report") or ""

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job["status"] in ("done", "failed", "cancelled"):
                return False
            job["cancel"].set()
            job["status"] = "cancelled"
            job["step"] = "отменено"
            return True

    # ------------------------------------------------------------- pipeline
    def _set(self, job: dict, **kw: Any) -> None:
        with self._lock:
            # once cancelled, never let the worker overwrite the terminal status
            if job["cancel"].is_set() and kw.get("status") not in (None, "cancelled"):
                return
            job.update(kw)

    def _run_job(self, job: dict) -> None:
        jid = job["id"]
        cfg = job["cfg"]
        work = self.work_root / jid
        try:
            work.mkdir(parents=True, exist_ok=True)
            ytdlp = _which("yt-dlp")

            # 1) metadata
            self._set(job, status="downloading", step="получаю метаданные…")
            info_r = _run([
                ytdlp, "--no-warnings", "--skip-download", "--dump-json",
                "--no-playlist", job["url"],
            ], 120)
            title, dur = "YouTube", 0.0
            for line in info_r.stdout.splitlines():
                try:
                    d = json.loads(line)
                    title = d.get("title") or title
                    dur = float(d.get("duration") or 0)
                    break
                except Exception:
                    continue

            # 2) full download
            self._set(job, status="downloading", step="скачиваю видео целиком…")
            full = work / "full.mp4"
            _run([
                ytdlp, "--no-warnings", "-f", f"mp4/best[height<={cfg['yt_video_max_h']}]/best",
                "-o", str(full), "--no-playlist", job["url"],
            ], 3600)
            if not full.exists() or full.stat().st_size == 0:
                raise RuntimeError("не удалось скачать видео")
            if not dur:
                dur = _probe_duration(full)

            # 3) adaptive segmentation
            seg_sec = cfg["yt_segment_sec"]
            if dur <= seg_sec:
                n = 1
                seg_len = dur if dur > 0 else seg_sec
            else:
                n = min(int((dur + seg_sec - 0.001) // seg_sec), cfg["yt_max_segments"])
                seg_len = dur / n
            self._set(job, status="processing", total=n, done=0, step=f"сегментов: {n}")

            # 4) ONE full-audio ASR pass with timestamps — segments slice the
            #    transcript by time instead of transcribing each one separately.
            full_segs: list[tuple[float, float, str]] = []
            full_text = ""  # complete transcript for the chat-chip sidecar
            if self.transcribe_segments is not None:
                self._set(job, status="processing", step="транскрибирую всё видео (один проход)…")
                try:
                    full_segs = self.transcribe_segments(full, vad_filter=cfg["yt_vad"]) or []
                except Exception:
                    full_segs = []
                if full_segs:
                    full_text = "\n".join(t for _, _, t in full_segs).strip()
                if job["cancel"].is_set():
                    return

            # 5) chain over segments (never skip)
            summaries: list[str] = []
            prev_summary = "Видео только началось — это первый сегмент."
            prev_frames: list[Path] = []
            full_transcript: list[str] = []
            gap = max(60.0 / max(cfg["yt_rpm"], 1), 3.0)  # rate-limit pause between calls

            for i in range(n):
                if job["cancel"].is_set():
                    return
                start_t = i * seg_len
                self._set(job, step=f"сегмент {i + 1}/{n}: нарезка…")
                seg = work / f"seg-{i}.mp4"
                if not _cut_segment(full, seg, start_t, seg_len):
                    raise RuntimeError(f"не удалось вырезать сегмент {i + 1}")

                # transcript: full-video slice by timestamp when the one-pass
                # pass worked; per-segment ASR only as a visible fallback.
                if full_segs:
                    transcript = _slice_transcript(full_segs, start_t, seg_len, full=True)
                else:
                    self._set(job, step=f"сегмент {i + 1}/{n}: транскрипция (фолбэк)…")
                    transcript = self.transcribe(seg, vad_filter=cfg["yt_vad"]) or ""
                    if transcript:
                        # fallback lines belong entirely to this segment → mark them
                        transcript = "\n".join(f">> {ln}" for ln in transcript.splitlines())
                        full_transcript.append(transcript)

                # visual memory: frames from the PREVIOUS segment
                frames_note = ""
                prev_frames = []
                if i > 0:
                    prev_seg = work / f"seg-{i - 1}.mp4"
                    if prev_seg.exists():
                        prev_frames = _extract_frames(prev_seg, work / f"frames-{i - 1}", cfg["yt_frames_from_prev"], seg_len)
                        if prev_frames:
                            frames_note = f"\n\n[Стоп-кадры прошлого сегмента (визуальная память): {len(prev_frames)}]"

                self._set(job, step=f"сегмент {i + 1}/{n}: Gemini смотрит видео…")
                summary = self._process_segment(job, seg, prev_frames, prev_summary, transcript, frames_note)
                summaries.append(summary)
                prev_summary = summary
                self._set(job, done=i + 1)

                if i < n - 1:  # pace requests at 15 RPM
                    time.sleep(gap)

            # 5) synthesis
            self._set(job, status="synthesizing", step="финальный синтез…")
            report = self._synthesize(summaries, title, dur, n, job["model"])
            report = (report or "").strip()
            self._set(job, report=report)

            # 6) chat-friendly artifacts
            mid = jid
            preview = self.media_dir / f"{mid}.mp4"
            _make_preview(work / "seg-0.mp4", preview, cfg["yt_preview_sec"], cfg["yt_preview_max_h"])
            full_txt = full_text or "\n\n".join(full_transcript).strip()
            if full_txt:
                try:
                    (self.media_dir / f"{mid}-tr.txt").write_text(full_txt, encoding="utf-8")
                except OSError:
                    pass
            if report:
                try:
                    (self.media_dir / f"{mid}-report.md").write_text(report, encoding="utf-8")
                except OSError:
                    pass

            result = {
                "id": mid,
                "url": f"/media/{mid}.mp4" if preview.exists() else "",
                "kind": "video",
                "name": title,
                "title": title,
                "duration_s": int(dur),
                "transcript": full_txt,
                "report": True,
                "note": f"полное видео разобрано: {n} сегмент(ов), отчёт готов",
            }
            self._set(job, status="done", step="готово", result=result)
        except Exception as exc:
            # user-initiated cancel must stay "cancelled", never flip to failed
            if job["cancel"].is_set():
                self._set(job, status="cancelled", step="отменено")
            else:
                self._set(job, status="failed", step="ошибка", error=str(exc))
        finally:
            # keep the job record for status polling; drop heavy temp files
            shutil.rmtree(work, ignore_errors=True)

    # ------------------------------------------------------------- Gemini
    def _process_segment(
        self,
        job: dict,
        seg: Path,
        prev_frames: list[Path],
        prev_summary: str,
        transcript: str,
        frames_note: str,
    ) -> str:
        user_text = SEGMENT_USER.format(
            prev_summary=prev_summary,
            transcript=transcript or "Речь не распознана (музыка / без слов).",
            frames_note=frames_note,
        ).strip()
        content: list[dict] = [{"type": "video_url", "video_url": {"url": _data_uri_media(seg)}}]
        for fr in prev_frames:
            content.append({"type": "image_url", "image_url": {"url": _data_uri_media(fr)}})
        content.append({"type": "text", "text": user_text})

        body = {
            "model": job["model"],
            "messages": [
                {"role": "system", "content": SEGMENT_SYSTEM},
                {"role": "user", "content": content},
            ],
            "max_tokens": 2048,
            "temperature": 0.4,
        }
        last_err = ""
        max_retries = int(job.get("cfg", {}).get("yt_max_retries", 5))
        for attempt in range(1, max_retries + 1):
            if job["cancel"].is_set():
                raise RuntimeError("отменено")
            resp, code = self.chat(body)
            if code == 200 and resp.get("content"):
                text = resp["content"]
                return _extract_next_summary(text, text)
            last_err = str(resp.get("error") or resp.get("raw") or resp)
            # 4xx (except 429) is a permanent error — retrying won't help
            if 400 <= code < 500 and code != 429:
                raise RuntimeError(f"провайдер отклонил запрос (HTTP {code}): {last_err}")
            if attempt < max_retries:
                wait = min(30, 2 ** attempt * 5) + 2  # exponential backoff
                time.sleep(wait)
        raise RuntimeError(f"сегмент не обработан после {max_retries} попыток: {last_err}")

    def _synthesize(self, summaries: list[str], title: str, dur: float, n: int, model: str = "") -> str:
        if not summaries:
            return ""
        if n == 1:
            # single segment: the segment summary IS the full report body
            seg_body = summaries[0]
            return (
                f"# {title}\n\n"
                f"*Полное видео ({int(dur)} сек) — разобрано одним сегментом.*\n\n"
                f"---\n\n{seg_body}"
            )
        body = {
            "model": model or self.model,
            "messages": [
                {"role": "system", "content": SYNTH_SYSTEM},
                {
                    "role": "user",
                    "content": "\n\n---\n\n".join(
                        f"## Сегмент {i + 1}\n{s}" for i, s in enumerate(summaries)
                    ),
                },
            ],
            "max_tokens": 4096,
            "temperature": 0.4,
        }
        resp, code = self.chat(body)
        if code == 200 and resp.get("content"):
            return f"# {title}\n\n*Полное видео ({int(dur)} сек, {n} сегментов).*\n\n---\n\n{resp['content'].strip()}"
        return "\n\n".join(f"## Сегмент {i + 1}\n{s}" for i, s in enumerate(summaries))


# ===========================================================================
# Preview clip (for the chat chip — the pipeline itself watched full segments)
# ===========================================================================
def _make_preview(src: Path, dst: Path, sec: int, max_h: int) -> bool:
    """Small h264 mp4 of the first `sec` seconds — only for UI display."""
    ffmpeg = _which("ffmpeg")
    try:
        _run([
            ffmpeg, "-y", "-loglevel", "error", "-i", str(src),
            "-t", str(sec), "-vf", f"scale={max_h}:-2", "-pix_fmt", "yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
            "-movflags", "+faststart", str(dst),
        ], 180)
        return dst.exists() and dst.stat().st_size > 0
    except Exception:
        return False
