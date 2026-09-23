"""Shared plumbing for the F5 judgment desk.

Path derivation, atomic JSON writes, fsync'd JSONL appends, byte-cursor stream
tailing, tiny counters. Everything here is defensive: no function raises on a
missing/corrupt input file — the desk fails open toward the code (absent input =
no action) and loud toward the operator (log + counter).

Directory contract (all under the F5 repo root, namespace ``operator``):

    <repo_root>/judgment/                                  flow sidecars the book
        flow_<day>.json, consume_<day>.json                consumes (judgment_layer
                                                           FLOW_SIDECAR_NAMES)
    <repo_root>/pipeline_state/ultimate_book/<ns>/judgment/
        manage_<day>.json                                  gtos.judgment.manage.v1
        judge_<day>.jsonl                                  desk journal
        JUDGE-MEMORY.md                                    rolling desk memory
        JUDGE-SCOREBOARD.md                                (written by the nightly
                                                           scoreboard job, if any)
        slates/slate_<stamp>_<sha16>.json                  sha-pinned slate archive
        state/                                             cursors, counters, lock
        logs/                                              daemon + adapter logs
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

_log = logging.getLogger("f5_desk")

NAMESPACE = "operator"

# Live stream locations, relative to the F5 repo root (verified against the tree:
# minimal_size.py writes shadow_logs/f5_minimal/<ns>/events.jsonl; launcher.py
# defaults log_path="shadow_logs/ultimate_book_launcher.jsonl").
EVENTS_REL = "shadow_logs/f5_minimal/{ns}/events.jsonl"
LAUNCHER_REL = "shadow_logs/ultimate_book_launcher.jsonl"
CALENDAR_REL = "data/news_calendar.json"


def repo_root_default() -> Path:
    """scripts/f5_desk/common.py -> repo root two levels up."""
    return Path(__file__).resolve().parents[2]


def judgment_state_dir(repo_root: Path, namespace: str = NAMESPACE) -> Path:
    return Path(repo_root) / "pipeline_state" / "ultimate_book" / str(namespace) / "judgment"


def flow_dir(repo_root: Path) -> Path:
    """The dir judgment_layer's flow consume seam reads (book_owner.py:350:
    ``self._judgment_verdict_dir = Path(repo_root) / "judgment"``)."""
    return Path(repo_root) / "judgment"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: Optional[datetime] = None) -> str:
    return (dt or now_utc()).astimezone(timezone.utc).isoformat()


def parse_utc(value: Any) -> Optional[datetime]:
    """ISO-8601 (or datetime) -> aware UTC. None on anything unparseable."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def utc_day(dt: Optional[datetime] = None) -> str:
    return (dt or now_utc()).astimezone(timezone.utc).date().isoformat()


def sha256_hex(data: Any) -> str:
    if isinstance(data, bytes):
        payload = data
    else:
        payload = str(data).encode("utf-8", errors="replace")
    return hashlib.sha256(payload).hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


# ---------------------------------------------------------------------------
# safe file IO
# ---------------------------------------------------------------------------
def read_json(path: Any, default: Any = None) -> Any:
    """Parse a JSON file; ``default`` on missing/corrupt. Never raises."""
    try:
        p = Path(path)
        if not p.is_file():
            return default
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # corrupt state must never kill the desk
        _log.warning("f5_desk: unreadable json %s (%r) -> default", path, exc)
        return default


def write_json_atomic(path: Any, obj: Any, *, indent: int = 1) -> bool:
    """tmp + os.replace in the same dir. False (logged) on failure, never raises."""
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + f".tmp{os.getpid()}")
        tmp.write_text(
            json.dumps(obj, indent=indent, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, target)
        return True
    except Exception as exc:
        _log.warning("f5_desk: atomic write failed %s (%r)", path, exc)
        return False


def append_jsonl(path: Any, row: dict) -> bool:
    """One fsync'd JSON line (same discipline as judgment_layer.append_judgment_row)."""
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(row, sort_keys=True, separators=(",", ":"), default=str)
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return True
    except Exception as exc:
        _log.warning("f5_desk: jsonl append failed %s (%r)", path, exc)
        return False


def append_text(path: Any, text: str) -> bool:
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
        return True
    except Exception as exc:
        _log.warning("f5_desk: text append failed %s (%r)", path, exc)
        return False


def tail_lines(path: Any, n: int) -> list[str]:
    """Last ``n`` lines of a text file; [] on missing/unreadable. Reads at most
    the final 512 KB so a huge memory file cannot balloon the prompt."""
    try:
        p = Path(path)
        if not p.is_file() or n <= 0:
            return []
        size = p.stat().st_size
        with open(p, "rb") as handle:
            if size > 512 * 1024:
                handle.seek(size - 512 * 1024)
                handle.readline()  # drop the partial first line
            data = handle.read()
        lines = data.decode("utf-8", errors="replace").splitlines()
        return lines[-n:]
    except Exception as exc:
        _log.warning("f5_desk: tail failed %s (%r)", path, exc)
        return []


# ---------------------------------------------------------------------------
# byte-cursor stream tailing (rotation/truncation tolerant)
# ---------------------------------------------------------------------------
MAX_TAIL_READ_BYTES = 64 * 1024 * 1024  # hard cap per cycle per stream
HEAD_SIG_BYTES = 1024


def tail_new_lines(path: Any, cursor: Optional[dict]) -> tuple[list[str], dict]:
    """Read complete new lines past ``cursor['offset']``; return (lines, new_cursor).

    Cursor: ``{"offset": int, "head_sig": sha256-of-first-1KB}``. A shrunken file
    or a changed head signature means rotation/rewrite -> restart from 0. A
    trailing partial line (no newline yet) is left for the next cycle. Never
    raises; a missing file returns ([], reset cursor).
    """
    cur = dict(cursor or {})
    try:
        p = Path(path)
        if not p.is_file():
            return [], {"offset": 0, "head_sig": ""}
        size = p.stat().st_size
        with open(p, "rb") as handle:
            head = handle.read(min(HEAD_SIG_BYTES, size))
            head_sig = hashlib.sha256(head).hexdigest()
            offset = int(cur.get("offset") or 0)
            if offset < 0 or offset > size or (cur.get("head_sig") and cur["head_sig"] != head_sig):
                offset = 0  # rotated, truncated, or replaced
            handle.seek(offset)
            data = handle.read(min(size - offset, MAX_TAIL_READ_BYTES))
        end = offset + len(data)
        # keep any trailing partial line for next time
        last_nl = data.rfind(b"\n")
        if last_nl < 0:
            return [], {"offset": offset, "head_sig": head_sig}
        consumed = data[: last_nl + 1]
        new_cursor = {"offset": offset + last_nl + 1, "head_sig": head_sig}
        lines = consumed.decode("utf-8", errors="replace").splitlines()
        return [ln for ln in lines if ln.strip()], new_cursor
    except Exception as exc:
        _log.warning("f5_desk: tail_new_lines failed %s (%r)", path, exc)
        return [], cur or {"offset": 0, "head_sig": ""}


def iter_json_lines(lines: Iterable[str]) -> Iterable[dict]:
    """Parse JSONL lines; silently count-and-skip garbage (caller logs totals)."""
    for line in lines:
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            yield obj


# ---------------------------------------------------------------------------
# tiny day-scoped counters (call cap, breach counter)
# ---------------------------------------------------------------------------
def bump_day_counter(path: Any, *, day: str, key: str = "count", extra: Optional[dict] = None) -> int:
    """Increment a per-UTC-day counter file; returns the new count. Rolls over on
    a new day. Never raises."""
    state = read_json(path, default={}) or {}
    if not isinstance(state, dict) or state.get("day") != day:
        state = {"day": day, key: 0}
    try:
        state[key] = int(state.get(key) or 0) + 1
    except Exception:
        state[key] = 1
    state["updated_at_utc"] = iso_utc()
    if extra:
        state.update(extra)
    write_json_atomic(path, state)
    return int(state[key])


def read_day_counter(path: Any, *, day: str, key: str = "count") -> int:
    state = read_json(path, default={}) or {}
    if not isinstance(state, dict) or state.get("day") != day:
        return 0
    try:
        return int(state.get(key) or 0)
    except Exception:
        return 0


def setup_logging(log_path: Optional[Path] = None, level: int = logging.INFO) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if log_path is not None:
        try:
            Path(log_path).parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
        except Exception:
            pass
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=False,
    )
