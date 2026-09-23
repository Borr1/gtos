"""Heartbeat-flatten kill switch — T1.1 (session 28 approval).

Detects silent orchestrator crashes (Apr 16 sleep-TOCTOU pattern) and, when
enabled, flattens orphan MT5 positions so the watchdog-restart cycle doesn't
leave a live position sitting untrailed.

Design
------
Two processes cooperate:

1. **Producer** — every orchestrator writes a UTC timestamp to its own
   per-symbol file ``pipeline_state/heartbeat_{SYMBOL}.json`` every
   ``heartbeat.write_interval_seconds`` (default 30s). See
   ``src/components/orchestrator.py::_write_heartbeat``.

2. **Consumer** — this module runs as a standalone, watchdog-launched process.
   It polls **every** per-symbol heartbeat file every ``write_interval_seconds``
   and treats the **oldest** observed age as the staleness signal. This means
   any single orchestrator going silent triggers detection — fixing the prior
   shared-file failure mode where one healthy writer masked silent crashes in
   the other six processes (last-writer-wins). Per-symbol files also enable
   per-symbol staleness reporting in the cascade event log for triage.

   Per iteration the monitor:

   - Counts consecutive *misses* (oldest age >= 3x write_interval, or no
     readable heartbeat files, or every file is malformed / future-dated).
   - After ``miss_threshold`` (default 3) consecutive misses, emits a
     TRIGGER_CANDIDATE event.
   - After 3 consecutive TRIGGER_CANDIDATE events (so ~180s total of
     continuous silence), enters the flatten sequence.
   - A single fresh heartbeat mid-sequence resets *both* counters to 0 — the
     monitor is sticky to real silence only.

   When ``heartbeat.flatten_enabled`` is False OR the current UTC time is
   outside every instrument's kill zone, the monitor only logs events and
   never touches MT5 or Telegram.

   When enabled *and* in-KZ, the monitor:

   - Sends a Telegram pre-flatten alert with a ``telegram_countdown_seconds``
     countdown (default 30s).
   - Listens for a "CANCEL" reply during the countdown. If received, aborts
     the flatten and logs a CANCELLED event.
   - On countdown expiry, enumerates open positions and closes each with
     comment ``heartbeat_flatten``. Each close is retried 3x with 5s backoff
     on MT5 failure.
   - After a completed sequence (FLATTENED or CANCELLED), no new alert fires
     for ``telegram_throttle_minutes`` (default 60).

Per-symbol architecture intent
------------------------------
The cascade is intentionally biased toward over-detection: ANY one of the
configured production orchestrators going silent for long enough fires the alarm. This is
the desired property — a silent partial fleet is the exact hypothesis-B
silent-degradation pattern that the shared-file design hid in production.
Telegram + flatten still gate on ``flatten_enabled`` + ``in_KZ`` + throttle,
so over-detection translates into observability noise (event log entries),
not action — which is the safe direction.

Events
------
All events append to ``shadow_logs/heartbeat_flatten_events.jsonl`` as one
JSON object per line. Event types:

- FEATURE_DISABLED — trigger reached but ``flatten_enabled=false``.
- OUTSIDE_KZ       — trigger reached but no instrument KZ active.
- TRIGGER_CANDIDATE — 3 misses reached; countdown toward full trigger.
- ARMED            — 3 trigger candidates reached (flatten sequence begins).
- COUNTDOWN_START  — Telegram countdown initiated.
- CANCELLED        — CANCEL reply received during countdown.
- FLATTENED        — all open positions successfully closed.
- FLATTEN_FAILED   — at least one close failed after all retries.
- RETRY_N          — individual close attempt failed, retry N pending.
- THROTTLED        — within 60-min throttle window; suppressed.

Constants marked ``MODULE-LEVEL`` below are deliberately module-level so
tests can ``monkeypatch.setattr(_mod, "HEARTBEAT_PATH", tmp_path/...)`` per
the session 21 canon (see ``tests/conftest.py`` write-guard notes).

Ship disabled. CEO enables after live validation.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from src.safety.runtime_halt import append_runtime_halt_audit, read_runtime_halt_state

logger = logging.getLogger(__name__)


# ── MODULE-LEVEL paths (monkeypatch in tests) ─────────────────────────────
# Absolute paths derived from this file's location so the module works
# regardless of the caller's CWD. Tests override via module-ref monkeypatch.

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
HEARTBEAT_DIR: Path = PROJECT_ROOT / "pipeline_state"
HEARTBEAT_PATH: Path = HEARTBEAT_DIR / "heartbeat.json"  # Legacy single-file fallback
PER_SYMBOL_HEARTBEAT_GLOB: str = "heartbeat_*.json"      # discovery pattern for per-symbol files
EVENTS_LOG_PATH: Path = PROJECT_ROOT / "shadow_logs" / "heartbeat_flatten_events.jsonl"
THROTTLE_STATE_PATH: Path = PROJECT_ROOT / "shadow_logs" / "heartbeat_throttle_state.json"
CONFIG_PATH: Path = PROJECT_ROOT / "config" / "agent_config.yaml"
RUNTIME_HALT_CONFIG: dict[str, dict[str, object]] = {
    "runtime_control": {
        "enabled": True,
        "audit_log_path": "pipeline_state/runtime_control_atomic_halt_audit.jsonl",
    }
}

# Default tuning knobs (mirrored in config/agent_config.yaml heartbeat: block).
DEFAULT_WRITE_INTERVAL_SECONDS: int = 30
DEFAULT_MISS_THRESHOLD: int = 3
DEFAULT_TRIGGER_CANDIDATE_THRESHOLD: int = 3
DEFAULT_TELEGRAM_COUNTDOWN_SECONDS: int = 30
DEFAULT_TELEGRAM_THROTTLE_MINUTES: int = 60
DEFAULT_RETRY_ATTEMPTS: int = 3
DEFAULT_RETRY_BACKOFF_SECONDS: float = 5.0
DEFAULT_FLATTEN_ENABLED: bool = False

# Per-instrument kill zones (UTC). Mirrors CLAUDE.md §KILL ZONE SCHEDULE.
# Each entry is (symbol, (start_h, start_m), (end_h, end_m)).
KILL_ZONES_UTC: tuple[tuple[str, tuple[int, int], tuple[int, int]], ...] = (
    ("AUDJPY", (0, 0), (3, 0)),
    ("AUDJPY", (7, 0), (9, 30)),
    ("AUDJPY", (13, 0), (15, 30)),
    ("AUDUSD", (0, 0), (3, 0)),
    ("AUDUSD", (7, 0), (12, 0)),
    ("AUDUSD", (13, 0), (15, 30)),
    ("BTCUSD", (0, 0), (23, 59)),
    ("CHFJPY", (0, 0), (3, 0)),
    ("CHFJPY", (7, 0), (9, 30)),
    ("CHFJPY", (13, 0), (15, 30)),
    ("ETHUSD", (0, 0), (23, 59)),
    ("EURGBP", (7, 0), (12, 0)),
    ("EURGBP", (13, 0), (15, 30)),
    ("EURJPY", (0, 0), (3, 0)),
    ("EURJPY", (7, 0), (9, 30)),
    ("EURJPY", (13, 0), (15, 30)),
    ("EURUSD", (7, 0), (12, 0)),
    ("EURUSD", (13, 0), (15, 30)),
    ("GBPJPY", (0, 0), (3, 0)),
    ("GBPJPY", (7, 0), (9, 30)),
    ("GBPJPY", (13, 0), (15, 30)),
    ("GBPUSD", (7, 0), (12, 0)),
    ("GBPUSD", (13, 0), (15, 30)),
    ("GER40", (8, 0), (12, 0)),
    ("GER40", (14, 0), (19, 0)),
    ("JP225", (0, 0), (3, 0)),
    ("JP225", (7, 0), (9, 30)),
    ("JP225", (13, 0), (15, 30)),
    ("NAS100", (13, 0), (17, 0)),
    ("NZDUSD", (0, 0), (3, 0)),
    ("NZDUSD", (7, 0), (12, 0)),
    ("NZDUSD", (13, 0), (15, 30)),
    ("SPX500", (13, 0), (17, 0)),
    ("UK100", (7, 0), (10, 30)),
    ("UK100", (13, 0), (15, 30)),
    ("UKOIL_cash", (7, 0), (12, 0)),
    ("UKOIL_cash", (13, 0), (17, 0)),
    ("US30_cash", (8, 0), (10, 30)),
    ("US30_cash", (13, 30), (16, 0)),
    ("USDCAD", (7, 0), (12, 0)),
    ("USDCAD", (13, 0), (15, 30)),
    ("USDCHF", (7, 0), (12, 0)),
    ("USDCHF", (13, 0), (15, 30)),
    ("USDJPY", (0, 0), (3, 0)),
    ("USDJPY", (7, 0), (9, 30)),
    ("USDJPY", (13, 0), (15, 30)),
    ("USOIL_cash", (7, 0), (12, 0)),
    ("USOIL_cash", (13, 0), (17, 0)),
    ("XAGUSD", (7, 0), (10, 30)),
    ("XAGUSD", (13, 0), (17, 0)),
    ("XAUUSD", (7, 0), (10, 30)),
    ("XAUUSD", (13, 0), (17, 0)),
)


# ── Heartbeat producer (called from orchestrator) ────────────────────────


def _sanitize_symbol_for_path(symbol: str) -> str:
    """Strip everything except [A-Za-z0-9_-] from ``symbol``.

    Defensive scrub so a bad ``extra["symbol"]`` value cannot escape the
    heartbeat dir via path traversal (``../``) or hit illegal Windows
    filename chars (``:``, ``\\``, ``/``, etc.). Mirrors the shadow-logger
    sanitization pattern in ``src/components/touch_count_gate_logger.py``.
    """
    import re
    if not symbol:
        return ""
    cleaned = re.sub(r"[^0-9A-Za-z_\-]", "_", str(symbol))
    return cleaned


def per_symbol_heartbeat_path(symbol: str, *, heartbeat_dir: Optional[Path] = None) -> Path:
    """Derive ``heartbeat_{SANITIZED_SYMBOL}.json`` under the heartbeat dir.

    The dir defaults to the module-level ``HEARTBEAT_DIR`` so tests that
    monkeypatch ``HEARTBEAT_DIR`` get redirected automatically. The
    sanitization step prevents a malformed ``extra["symbol"]`` from writing
    outside the directory.
    """
    base = Path(heartbeat_dir) if heartbeat_dir is not None else HEARTBEAT_DIR
    safe = _sanitize_symbol_for_path(symbol)
    return base / f"heartbeat_{safe}.json"


def write_heartbeat(
    *,
    heartbeat_path: Optional[Path] = None,
    extra: Optional[dict] = None,
) -> bool:
    """Best-effort heartbeat write. Never raises.

    Returns True on successful write, False if the IO failed (caller logs
    at WARNING via the wrapping try/except, but MUST NOT crash).

    Path resolution (in priority order):
      1. ``heartbeat_path`` — if explicitly provided, written as-is. Used
         only by tests and migration scripts.
      2. ``extra["symbol"]`` — if provided, write to
         ``HEARTBEAT_DIR / heartbeat_{SYMBOL}.json``. This is the canonical
         per-symbol path used by the orchestrator (every live process
         supplies ``extra={"symbol": self._symbol}``).
      3. Fallback — write to the legacy ``HEARTBEAT_PATH`` (single shared
         file) AND emit a WARNING. This branch fires only when an orchestrator
         (or test) calls without a symbol; in production it indicates a
         caller bug because every orchestrator instance is symbol-bound.

    The file contains a minimal envelope::

        {"utc": "2026-04-19T07:00:00+00:00", "pid": 1234, "symbol": "XAUUSD"}

    Atomic-rename via ``os.replace(tmp, target)`` is preserved for crash
    safety — readers will never observe a half-written file.
    """
    payload: dict[str, Any] = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
    }
    if extra:
        payload.update(extra)

    # Resolve target path.
    target: Path
    if heartbeat_path is not None:
        target = Path(heartbeat_path)
    else:
        sym = (extra or {}).get("symbol") if isinstance(extra, dict) else None
        if sym:
            target = per_symbol_heartbeat_path(str(sym))
        else:
            # No symbol → fall back to legacy single-file path. This path is
            # an architectural smell in production (every orchestrator is
            # symbol-bound), so we surface it loudly.
            logger.warning(
                "heartbeat write missing symbol — falling back to legacy "
                "shared file %s. Cascade detection will be blind to silent "
                "crashes when other orchestrators keep this file fresh.",
                HEARTBEAT_PATH,
            )
            target = HEARTBEAT_PATH

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(tmp, target)
        return True
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "heartbeat write failed (non-fatal) target=%s: %s", target, e,
        )
        return False


def _now_utc() -> datetime:
    """Indirection so tests can monkeypatch time."""
    return datetime.now(timezone.utc)


def read_heartbeat_age_seconds(
    heartbeat_path: Optional[Path] = None,
    *,
    now: Optional[datetime] = None,
) -> Optional[float]:
    """Return heartbeat age in seconds for a single file.

    Returns ``None`` if the file is missing, unreadable, malformed, has no
    ``utc`` key, or its timestamp lies in the future (clock drift). The
    caller treats ``None`` identically to ``age >= miss_threshold_seconds``,
    i.e. a miss.

    A future-dated heartbeat (now - ts < 0) is treated as malformed and
    returns None — this prevents an attacker or broken clock from
    suppressing the monitor by writing a future timestamp.

    NOTE: This is the per-file primitive. The fleet-wide monitor reads
    EVERY per-symbol file via ``read_oldest_heartbeat_age_seconds`` to defeat
    the silent-degradation pattern. Direct callers of this single-file
    function are tests, the legacy fallback path, and any tool that explicitly
    wants one symbol.
    """
    target = Path(heartbeat_path) if heartbeat_path is not None else HEARTBEAT_PATH
    if not target.exists():
        return None
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    ts_str = data.get("utc") if isinstance(data, dict) else None
    if not ts_str or not isinstance(ts_str, str):
        return None
    try:
        ts = datetime.fromisoformat(ts_str)
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    now_dt = now if now is not None else _now_utc()
    age = (now_dt - ts).total_seconds()
    if age < 0:
        # Future-dated → treat as malformed
        return None
    return age


def discover_heartbeat_paths(
    *,
    heartbeat_dir: Optional[Path] = None,
    legacy_fallback_path: Optional[Path] = None,
) -> list[Path]:
    """Enumerate per-symbol heartbeat files.

    Behavior:
      - Returns every file matching ``HEARTBEAT_DIR / heartbeat_*.json``
        whose name is NOT exactly ``heartbeat.json`` (the legacy single-file
        sentinel). Files are returned in stable alphabetical order so per-
        symbol breakdowns in the event log are reproducible.
      - If zero per-symbol files are found AND the legacy fallback path
        exists, returns ``[legacy_fallback_path]`` for backward compat
        during migration. This makes a half-deployed state safe: while
        only some orchestrators have rolled to the per-symbol writer, the
        monitor still observes the legacy file produced by the rest.
      - If neither is present, returns the empty list — the caller treats
        this as "no readable heartbeat" (a miss).

    The caller is responsible for treating an empty list as a miss and for
    logging which files were observed.
    """
    base = Path(heartbeat_dir) if heartbeat_dir is not None else HEARTBEAT_DIR
    legacy = Path(legacy_fallback_path) if legacy_fallback_path is not None else HEARTBEAT_PATH

    per_symbol: list[Path] = []
    try:
        if base.exists() and base.is_dir():
            for entry in sorted(base.glob(PER_SYMBOL_HEARTBEAT_GLOB)):
                if entry.is_file() and entry.name != legacy.name:
                    per_symbol.append(entry)
    except OSError as e:
        # Filesystem hiccup (perm denied, transient I/O). Surface but don't
        # raise — we'll fall through to the legacy path or empty list.
        logger.warning("heartbeat dir scan failed (non-fatal) dir=%s: %s", base, e)

    if per_symbol:
        return per_symbol

    # Fallback to legacy single file if it exists.
    if legacy.exists():
        return [legacy]

    return []


def read_oldest_heartbeat_age_seconds(
    *,
    heartbeat_dir: Optional[Path] = None,
    legacy_fallback_path: Optional[Path] = None,
    now: Optional[datetime] = None,
    write_interval_seconds: int = DEFAULT_WRITE_INTERVAL_SECONDS,
    miss_threshold: int = DEFAULT_MISS_THRESHOLD,
) -> tuple[Optional[float], dict[str, Optional[float]]]:
    """Return (oldest_age_seconds, per_file_breakdown).

    The fleet-wide staleness signal: across every per-symbol heartbeat file
    (or the legacy fallback during migration), return the OLDEST observed
    age. Any single orchestrator going silent → its file ages → the oldest
    age climbs → the cascade fires.

    Failure isolation: corrupt / future-dated / missing-utc-key files map
    to ``None`` in the per-file breakdown. The aggregate ``oldest_age``
    treats ANY ``None`` entry as a miss (it dominates over fresh entries —
    the safe direction). If every entry is fresh, the aggregate is the max
    fresh age.

    Returns:
      ``(None, {})``  — no heartbeat files exist (treat as miss)
      ``(None, {f: None, ...})`` — at least one file is unreadable / future
      ``(max_age, {f: age, ...})`` — all files readable; max_age is the
                                     largest observed age (oldest writer)
    """
    paths = discover_heartbeat_paths(
        heartbeat_dir=heartbeat_dir,
        legacy_fallback_path=legacy_fallback_path,
    )
    if not paths:
        return (None, {})

    breakdown: dict[str, Optional[float]] = {}
    saw_none = False
    max_age: Optional[float] = None
    for path in paths:
        # Read each file in isolation — a corrupt file MUST NOT poison the
        # monitor's read of the others.
        try:
            age = read_heartbeat_age_seconds(path, now=now)
        except Exception as e:  # noqa: BLE001 — defensive belt-and-braces
            logger.warning(
                "heartbeat read raised unexpectedly (treating as miss) "
                "path=%s: %s", path, e,
            )
            age = None

        breakdown[path.name] = age
        if age is None:
            saw_none = True
        else:
            if max_age is None or age > max_age:
                max_age = age

    if saw_none:
        # At least one file is missing/malformed → fleet is in a bad state.
        # Returning None forces a miss regardless of how fresh the others are.
        return (None, breakdown)

    return (max_age, breakdown)


def is_miss(
    age: Optional[float],
    *,
    write_interval_seconds: int = DEFAULT_WRITE_INTERVAL_SECONDS,
    miss_threshold: int = DEFAULT_MISS_THRESHOLD,
) -> bool:
    """A miss is: no readable age, OR age >= write_interval * miss_threshold.

    Default: 30s * 3 = 90s.
    """
    threshold_seconds = float(write_interval_seconds) * float(miss_threshold)
    if age is None:
        return True
    return age >= threshold_seconds


def any_kill_zone_active(now: Optional[datetime] = None) -> bool:
    """Return True if current UTC time falls inside ANY instrument's KZ.

    Each KZ is a half-open interval ``[start, end)`` in UTC. Any overlap is
    sufficient — the monitor is not symbol-aware, just market-hours aware.
    """
    now_dt = now if now is not None else _now_utc()
    h, m = now_dt.hour, now_dt.minute
    minutes_of_day = h * 60 + m
    for _sym, (sh, sm), (eh, em) in KILL_ZONES_UTC:
        start = sh * 60 + sm
        end = eh * 60 + em
        if start <= minutes_of_day < end:
            return True
    return False


# ── Event logging ────────────────────────────────────────────────────────


def log_event(
    event_type: str,
    *,
    events_path: Optional[Path] = None,
    details: Optional[dict] = None,
) -> None:
    """Append a JSON-line event. Best-effort — never raises."""
    target = Path(events_path) if events_path is not None else EVENTS_LOG_PATH
    payload: dict[str, Any] = {
        "timestamp": _now_utc().isoformat(),
        "event_type": event_type,
    }
    if details:
        payload.update(details)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception as e:  # noqa: BLE001
        logger.warning("event log failed (non-fatal) path=%s: %s", target, e)


# ── Throttle state ───────────────────────────────────────────────────────


def _load_throttle_state(path: Optional[Path] = None) -> dict:
    target = Path(path) if path is not None else THROTTLE_STATE_PATH
    if not target.exists():
        return {}
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _save_throttle_state(state: dict, path: Optional[Path] = None) -> None:
    target = Path(path) if path is not None else THROTTLE_STATE_PATH
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(state), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "throttle state save failed (non-fatal) path=%s: %s", target, e,
        )


def in_throttle_window(
    *,
    throttle_minutes: int = DEFAULT_TELEGRAM_THROTTLE_MINUTES,
    state_path: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> bool:
    """Return True if we're still within the post-alert throttle window."""
    state = _load_throttle_state(state_path)
    last = state.get("last_alert_utc")
    if not last or not isinstance(last, str):
        return False
    try:
        ts = datetime.fromisoformat(last)
    except ValueError:
        return False
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    now_dt = now if now is not None else _now_utc()
    return (now_dt - ts) < timedelta(minutes=throttle_minutes)


def mark_alert_fired(
    *,
    state_path: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> None:
    now_dt = now if now is not None else _now_utc()
    _save_throttle_state({"last_alert_utc": now_dt.isoformat()}, state_path)


# ── Telegram ─────────────────────────────────────────────────────────────


def send_telegram_alert(text: str) -> bool:
    """Fire a synchronous Telegram message + enqueue a CRITICAL retry copy.

    Returns True if the synchronous send succeeded, False otherwise. The
    countdown logic needs the synchronous result to decide whether to wait
    for a CANCEL reply.

    H7 (2026-04-26): in addition to the synchronous attempt this function
    enqueues the same message at CRITICAL priority via the persistent
    notification queue. If the synchronous send fails (network blip, broker
    cert issue), the queue's daemon retries indefinitely until delivery
    succeeds OR the message ages out at 24h. The CEO must always see
    flatten-cascade alerts; the queue is the safety net behind the
    synchronous fast path.

    The enqueue is deliberately non-blocking and best-effort — if the
    queue subsystem is unavailable the synchronous attempt remains the
    primary delivery channel and we don't want a queue failure to mask
    the True/False return.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    # Persistent retry copy (best-effort; never raises into caller).
    try:
        from src.utils.notification_queue import Level, send as _q_send
        _q_send(text, level=Level.CRITICAL)
    except Exception as e:  # pragma: no cover — defensive
        logger.debug("heartbeat_monitor: queue enqueue failed: %s", e)

    # Direct POST path — bypasses the queue transport, so it carries its own
    # authorization gate (F30 / Q7). Credential presence is not authorization;
    # see src/safety/notification_authorization.py.
    from src.safety.notification_authorization import delivery_authorization

    _auth = delivery_authorization()
    if not _auth.allowed:
        logger.error(
            "heartbeat_monitor: Telegram send REFUSED (unauthorized process): %s", _auth.detail,
        )
        return False

    if not token or not chat_id:
        logger.warning("Telegram creds missing — alert not sent: %s", text[:60])
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
            return resp.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        logger.warning("Telegram send failed: %s", e)
        return False


def poll_telegram_for_cancel(
    *,
    since_update_id: int = 0,
    bot_token: Optional[str] = None,
    timeout_seconds: int = 5,
) -> tuple[bool, int]:
    """Poll Telegram getUpdates once. Return (cancel_seen, max_update_id).

    ``cancel_seen`` is True if any message text since ``since_update_id``
    equals 'CANCEL' (case-insensitive, trimmed). ``max_update_id`` is the
    largest update_id observed — the caller passes it back as
    ``since_update_id + 1`` on the next poll to avoid re-reading old updates.

    On any error (missing creds, HTTP failure, bad JSON) returns
    ``(False, since_update_id)`` — we never trigger a cancel on error.
    """
    token = bot_token if bot_token is not None else os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return (False, since_update_id)
    url = (
        f"https://api.telegram.org/bot{token}/getUpdates"
        f"?offset={max(since_update_id, 0)}&timeout={max(timeout_seconds, 0)}"
    )
    try:
        with urllib.request.urlopen(url, timeout=timeout_seconds + 5) as resp:  # nosec B310
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.debug("telegram getUpdates failed: %s", e)
        return (False, since_update_id)
    if not isinstance(data, dict) or not data.get("ok"):
        return (False, since_update_id)
    max_id = since_update_id
    cancel_seen = False
    for upd in data.get("result", []) or []:
        upd_id = upd.get("update_id", 0) if isinstance(upd, dict) else 0
        if upd_id > max_id:
            max_id = upd_id
        msg = upd.get("message") if isinstance(upd, dict) else None
        if not isinstance(msg, dict):
            continue
        text = (msg.get("text") or "").strip().upper()
        if text == "CANCEL":
            cancel_seen = True
    return (cancel_seen, max_id)


# ── MT5 flatten ──────────────────────────────────────────────────────────


FLATTEN_COMMENT: str = "heartbeat_flatten"
# MT5 retcode for TRADE_RETCODE_DONE (successful deal placement)
TRADE_RETCODE_DONE: int = 10009
TRADE_ACTION_DEAL: int = 1
DEAL_TYPE_SELL: int = 1  # to close a long
DEAL_TYPE_BUY: int = 0   # to close a short


def _close_one_position_via_mt5(
    mt5_module: Any,
    position: Any,
    *,
    deviation: int = 20,
) -> tuple[bool, dict]:
    """Issue a single close order for ``position``.

    Returns ``(success, detail)``. ``detail`` carries the raw retcode / reason
    so callers can log it.
    """
    # Position.type: 0=BUY (long), 1=SELL (short). To close a long we SELL, to
    # close a short we BUY.
    pos_type = getattr(position, "type", None)
    if pos_type == 0:
        close_type = DEAL_TYPE_SELL
    elif pos_type == 1:
        close_type = DEAL_TYPE_BUY
    else:
        return (False, {"reason": "unknown_position_type", "pos_type": pos_type})

    request = {
        "action": TRADE_ACTION_DEAL,
        "symbol": getattr(position, "symbol", ""),
        "volume": getattr(position, "volume", 0.0),
        "type": close_type,
        "position": getattr(position, "ticket", 0),
        "deviation": deviation,
        "magic": getattr(position, "magic", 0),
        "comment": FLATTEN_COMMENT,
    }
    halt_snapshot = read_runtime_halt_state(
        RUNTIME_HALT_CONFIG,
        repo_root=PROJECT_ROOT,
    )
    if halt_snapshot.active:
        append_runtime_halt_audit(
            action="heartbeat_flatten_order_send",
            snapshot=halt_snapshot,
            context={
                "component": "heartbeat_monitor",
                "symbol": request.get("symbol"),
                "position": request.get("position"),
            },
            config=RUNTIME_HALT_CONFIG,
            repo_root=PROJECT_ROOT,
        )
        return (
            False,
            {
                "reason": "runtime_halt_active_no_order_send",
                "status": halt_snapshot.status,
                "ticket": getattr(position, "ticket", 0),
            },
        )
    try:
        result = mt5_module.order_send(request)
    except Exception as e:  # noqa: BLE001
        return (False, {"reason": "exception", "error": str(e)})
    if result is None:
        return (False, {"reason": "order_send_returned_none"})
    retcode = getattr(result, "retcode", None)
    if retcode == TRADE_RETCODE_DONE:
        return (True, {"retcode": retcode, "ticket": getattr(position, "ticket", 0)})
    return (False, {
        "retcode": retcode,
        "comment": getattr(result, "comment", ""),
        "ticket": getattr(position, "ticket", 0),
    })


def flatten_open_positions(
    mt5_module: Any,
    *,
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
    retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
    sleep_fn: Callable[[float], None] = time.sleep,
    events_path: Optional[Path] = None,
) -> dict:
    """Flatten every open position reachable via ``mt5_module.positions_get``.

    Retries each per-position close up to ``retry_attempts`` times with
    ``retry_backoff_seconds`` between attempts. Logs one RETRY_N event per
    failed attempt and a terminal FLATTENED or FLATTEN_FAILED summary event.

    Returns a summary dict::

        {"closed": [...], "failed": [...], "attempted": N}
    """
    try:
        positions = mt5_module.positions_get() or []
    except Exception as e:  # noqa: BLE001
        log_event(
            "FLATTEN_FAILED",
            events_path=events_path,
            details={"reason": "positions_get_failed", "error": str(e)},
        )
        return {"closed": [], "failed": [], "attempted": 0, "error": str(e)}

    closed: list[dict] = []
    failed: list[dict] = []

    for position in positions:
        attempt = 0
        succeeded = False
        last_detail: dict = {}
        while attempt < retry_attempts and not succeeded:
            attempt += 1
            succeeded, last_detail = _close_one_position_via_mt5(mt5_module, position)
            if not succeeded:
                log_event(
                    f"RETRY_{attempt}",
                    events_path=events_path,
                    details={
                        "ticket": getattr(position, "ticket", 0),
                        "symbol": getattr(position, "symbol", ""),
                        **last_detail,
                    },
                )
                if attempt < retry_attempts:
                    sleep_fn(retry_backoff_seconds)
        record = {
            "ticket": getattr(position, "ticket", 0),
            "symbol": getattr(position, "symbol", ""),
            "attempts": attempt,
            **last_detail,
        }
        if succeeded:
            closed.append(record)
        else:
            failed.append(record)

    summary = {"closed": closed, "failed": failed, "attempted": len(positions)}
    if failed:
        log_event("FLATTEN_FAILED", events_path=events_path, details=summary)
    else:
        log_event("FLATTENED", events_path=events_path, details=summary)
    return summary


# ── Countdown orchestration ──────────────────────────────────────────────


def run_countdown_with_cancel_listener(
    *,
    countdown_seconds: int,
    poll_interval_seconds: float = 2.0,
    sleep_fn: Callable[[float], None] = time.sleep,
    cancel_poller: Callable[[int], tuple[bool, int]] = poll_telegram_for_cancel,
    initial_update_id: int = 0,
) -> bool:
    """Run the pre-flatten countdown. Return True if CANCEL observed.

    Polls ``cancel_poller`` every ``poll_interval_seconds`` seconds for
    ``countdown_seconds`` total. On the first CANCEL, returns True early.
    Otherwise sleeps until expiry and returns False.

    The poller signature ``(since_update_id: int) -> (bool, int)`` matches
    ``poll_telegram_for_cancel`` so tests can substitute a deterministic
    mock without monkeypatching urllib.
    """
    elapsed = 0.0
    since = initial_update_id
    while elapsed < countdown_seconds:
        cancelled, since = cancel_poller(since)
        if cancelled:
            return True
        step = min(poll_interval_seconds, countdown_seconds - elapsed)
        if step <= 0:
            break
        sleep_fn(step)
        elapsed += step
    # Final poll after the loop to catch messages that arrived right at the end
    cancelled, _ = cancel_poller(since)
    return bool(cancelled)


# ── Single-iteration tick (easy to unit-test) ────────────────────────────


class MonitorState:
    """Mutable counters for the monitor state machine."""

    __slots__ = ("miss_count", "trigger_candidate_count", "last_telegram_update_id")

    def __init__(self) -> None:
        self.miss_count: int = 0
        self.trigger_candidate_count: int = 0
        self.last_telegram_update_id: int = 0

    def reset(self) -> None:
        self.miss_count = 0
        self.trigger_candidate_count = 0

    def __repr__(self) -> str:  # pragma: no cover — debug helper
        return (
            f"MonitorState(miss={self.miss_count}, "
            f"trigger_candidate={self.trigger_candidate_count})"
        )


def _stalest_symbol_label(breakdown: dict[str, Optional[float]]) -> Optional[str]:
    """Return the filename whose age is None (missing/malformed) or maximum.

    The label surfaces in the cascade event log so an operator scanning
    TRIGGER_CANDIDATE / ARMED rows can immediately see WHICH orchestrator
    is silent. ``None``-aged entries always win over fresh entries because
    a missing/malformed file is worse than a stale-but-readable one.
    """
    if not breakdown:
        return None
    none_entries = [name for name, age in breakdown.items() if age is None]
    if none_entries:
        return sorted(none_entries)[0]
    # All readable → pick the oldest.
    items = [(name, age) for name, age in breakdown.items() if age is not None]
    if not items:
        return None
    items.sort(key=lambda kv: kv[1], reverse=True)
    return items[0][0]


def tick(
    state: MonitorState,
    *,
    config: Optional[dict] = None,
    heartbeat_path: Optional[Path] = None,
    heartbeat_dir: Optional[Path] = None,
    legacy_fallback_path: Optional[Path] = None,
    events_path: Optional[Path] = None,
    throttle_state_path: Optional[Path] = None,
    mt5_module: Optional[Any] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    cancel_poller: Optional[Callable[[int], tuple[bool, int]]] = None,
    telegram_sender: Callable[[str], bool] = send_telegram_alert,
    now: Optional[datetime] = None,
) -> dict:
    """One iteration of the monitor loop. Returns a small summary dict.

    Extracted as a pure-ish function so tests don't need to manage an
    infinite loop. The ``main()`` loop just calls this in a while-True.

    Read mode:
      - If ``heartbeat_path`` is supplied, the legacy single-file path is
        read (preserved for older tests + diagnostic tools).
      - Otherwise, the fleet-wide reader is used:
        ``read_oldest_heartbeat_age_seconds(heartbeat_dir, legacy_fallback_path)``
        — the oldest age across every per-symbol file becomes the staleness
        signal. Per-file breakdown is included in event details for triage.

    Summary dict fields::

        {"event": str, "miss": int, "trigger_candidate": int,
         "action": "none"|"alert"|"flatten"|"cancelled",
         "age_seconds": float | None,
         "stalest_file": str | None,
         "per_file_ages": {filename: age_or_null, ...}}
    """
    cfg = (config or {}).get("heartbeat", {}) if config else {}
    write_interval = int(cfg.get("write_interval_seconds", DEFAULT_WRITE_INTERVAL_SECONDS))
    miss_threshold = int(cfg.get("miss_threshold", DEFAULT_MISS_THRESHOLD))
    flatten_enabled = bool(cfg.get("flatten_enabled", DEFAULT_FLATTEN_ENABLED))
    countdown_s = int(cfg.get("telegram_countdown_seconds", DEFAULT_TELEGRAM_COUNTDOWN_SECONDS))
    throttle_min = int(cfg.get("telegram_throttle_minutes", DEFAULT_TELEGRAM_THROTTLE_MINUTES))
    breakdown: dict[str, Optional[float]] = {}
    if heartbeat_path is not None:
        # Legacy single-file path — preserved for older tests + diagnostic
        # tools. Production code paths leave heartbeat_path=None to engage
        # the fleet-wide reader.
        age = read_heartbeat_age_seconds(heartbeat_path, now=now)
    else:
        age, breakdown = read_oldest_heartbeat_age_seconds(
            heartbeat_dir=heartbeat_dir,
            legacy_fallback_path=legacy_fallback_path,
            now=now,
            write_interval_seconds=write_interval,
            miss_threshold=miss_threshold,
        )

    stalest = _stalest_symbol_label(breakdown) if breakdown else None
    miss = is_miss(
        age,
        write_interval_seconds=write_interval,
        miss_threshold=miss_threshold,
    )

    def _result(event: str, action: str, **extra) -> dict:
        out = {
            "event": event,
            "miss": state.miss_count,
            "trigger_candidate": state.trigger_candidate_count,
            "action": action,
            "age_seconds": age,
            "stalest_file": stalest,
            "per_file_ages": dict(breakdown),
        }
        out.update(extra)
        return out

    if not miss:
        # Fresh heartbeat — reset both counters (counter-reset semantics).
        had_progress = state.miss_count > 0 or state.trigger_candidate_count > 0
        state.reset()
        return _result("FRESH" if not had_progress else "RESET", "none")

    # Miss observed
    state.miss_count += 1
    if state.miss_count < miss_threshold:
        return _result("MISS", "none")

    # Reached miss_threshold → emit a TRIGGER_CANDIDATE and reset miss_count.
    state.trigger_candidate_count += 1
    state.miss_count = 0
    log_event(
        "TRIGGER_CANDIDATE",
        events_path=events_path,
        details={
            "trigger_candidate_count": state.trigger_candidate_count,
            "age_seconds": age,
            "stalest_file": stalest,
            "per_file_ages": dict(breakdown),
        },
    )

    if state.trigger_candidate_count < DEFAULT_TRIGGER_CANDIDATE_THRESHOLD:
        return _result("TRIGGER_CANDIDATE", "none")

    # 3 trigger candidates reached → full alarm. Decide action based on gates.
    # After this point we always reset trigger_candidate_count so the next
    # silence cycle starts from 0 even if we early-return.
    state.trigger_candidate_count = 0

    # Gate 1: feature flag.
    if not flatten_enabled:
        log_event(
            "FEATURE_DISABLED",
            events_path=events_path,
            details={
                "age_seconds": age,
                "stalest_file": stalest,
                "per_file_ages": dict(breakdown),
            },
        )
        return _result("FEATURE_DISABLED", "none")

    # Gate 2: market-hours.
    if not any_kill_zone_active(now=now):
        log_event(
            "OUTSIDE_KZ",
            events_path=events_path,
            details={
                "age_seconds": age,
                "stalest_file": stalest,
                "per_file_ages": dict(breakdown),
            },
        )
        return _result("OUTSIDE_KZ", "none")

    # Gate 3: throttle.
    if in_throttle_window(
        throttle_minutes=throttle_min,
        state_path=throttle_state_path,
        now=now,
    ):
        log_event(
            "THROTTLED",
            events_path=events_path,
            details={
                "age_seconds": age,
                "throttle_minutes": throttle_min,
                "stalest_file": stalest,
            },
        )
        return _result("THROTTLED", "none")

    # All gates open — arm + run countdown + flatten.
    log_event(
        "ARMED",
        events_path=events_path,
        details={
            "age_seconds": age,
            "stalest_file": stalest,
            "per_file_ages": dict(breakdown),
        },
    )
    log_event(
        "COUNTDOWN_START",
        events_path=events_path,
        details={"countdown_seconds": countdown_s, "stalest_file": stalest},
    )
    telegram_sender(
        f"GTOS HEARTBEAT ALERT\nOrchestrator silent for {int(age or 0)}s "
        f"(stalest: {stalest or 'none'}).\n"
        f"Flatten in {countdown_s}s. Reply CANCEL to abort."
    )

    poller: Callable[[int], tuple[bool, int]]
    if cancel_poller is not None:
        poller = cancel_poller
    else:
        # Wrapped so the stored update-id state is threaded through.
        captured_since = state.last_telegram_update_id

        def _default_poller(since: int) -> tuple[bool, int]:
            return poll_telegram_for_cancel(since_update_id=since)

        poller = _default_poller
        _ = captured_since  # silence flake — used implicitly via initial_update_id below

    cancelled = run_countdown_with_cancel_listener(
        countdown_seconds=countdown_s,
        sleep_fn=sleep_fn,
        cancel_poller=poller,
        initial_update_id=state.last_telegram_update_id,
    )

    if cancelled:
        log_event(
            "CANCELLED",
            events_path=events_path,
            details={"age_seconds": age, "stalest_file": stalest},
        )
        mark_alert_fired(state_path=throttle_state_path, now=now)
        telegram_sender("GTOS HEARTBEAT: flatten CANCELLED by operator.")
        return _result("CANCELLED", "cancelled")

    # Execute flatten.
    if mt5_module is None:
        log_event(
            "FLATTEN_FAILED",
            events_path=events_path,
            details={
                "reason": "no_mt5_module_available",
                "stalest_file": stalest,
            },
        )
        mark_alert_fired(state_path=throttle_state_path, now=now)
        return _result("FLATTEN_FAILED", "flatten_failed")

    summary = flatten_open_positions(
        mt5_module,
        sleep_fn=sleep_fn,
        events_path=events_path,
    )
    mark_alert_fired(state_path=throttle_state_path, now=now)
    final_event = "FLATTENED" if not summary.get("failed") else "FLATTEN_FAILED"
    return _result(final_event, "flatten", details=summary)


# ── Config loader ────────────────────────────────────────────────────────


def load_config(path: Optional[Path] = None) -> dict:
    """Best-effort config load. Returns empty dict on any failure.

    We intentionally don't import ``src.utils.config`` here — the monitor
    runs as a standalone process and should not depend on the orchestrator
    bootstrap machinery.
    """
    target = Path(path) if path is not None else CONFIG_PATH
    if not target.exists():
        return {}
    try:
        import yaml  # Local import — lazy so tests can skip.
    except ImportError:
        return {}
    try:
        with open(target, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as e:  # type: ignore[attr-defined]
        logger.debug("config load failed: %s", e)
        return {}
    return data or {}


# ── Main loop (watchdog-launched) ────────────────────────────────────────


def main(argv: Optional[list[str]] = None) -> int:
    """Standalone monitor entry point.

    Runs forever (or until SIGTERM), calling ``tick`` every
    ``write_interval_seconds`` seconds. ``argv`` is accepted for test
    compatibility but unused — all config comes from ``agent_config.yaml``.

    2026-04-28 sibling-daemon-stability fix: this entry now claims a
    single-instance lock via ``mt5_daemon_runtime.acquire_single_instance_lock``
    so duplicate watchdog restarts don't pile up multiple monitors. The
    legacy lock-file scheme (``.heartbeat_monitor.lock`` written by the
    PowerShell watchdog) is replaced with own-PID semantics: if a previous
    monitor exited cleanly, the lock is gone; if it crashed leaving a
    stale lock, the new instance reclaims it (PID dead). If a real second
    monitor is already running, this instance exits 0 cleanly so the
    watchdog does not enter a hot restart loop.
    """
    _ = argv  # reserved

    # Operator notification delivery is default-deny per process (F30 / Q7).
    # The standalone monitor daemon exists to page the operator on
    # flatten-cascade and heartbeat-stall events, so it takes the grant at its
    # entrypoint. Importing this module elsewhere (tests, tooling) stays
    # refused — the grant is per-process, not per-module.
    from src.safety.notification_authorization import authorize_operator_delivery
    authorize_operator_delivery(reason="src/safety/heartbeat_monitor.py standalone monitor daemon")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s heartbeat_monitor: %(message)s",
    )

    halt_snapshot = read_runtime_halt_state(RUNTIME_HALT_CONFIG, repo_root=PROJECT_ROOT)
    if halt_snapshot.active:
        append_runtime_halt_audit(
            action="heartbeat_monitor_start",
            snapshot=halt_snapshot,
            context={"component": "heartbeat_monitor"},
            config=RUNTIME_HALT_CONFIG,
            repo_root=PROJECT_ROOT,
        )
        logger.info(
            "%s active; heartbeat monitor exiting before lock/MT5 interaction.",
            halt_snapshot.status,
        )
        return 0

    # Single-instance enforcement.
    from src.components import mt5_daemon_runtime as _runtime
    lock_name = "heartbeat_monitor"
    argv_marker = "src.safety.heartbeat_monitor"
    acquired, conflicting = _runtime.acquire_single_instance_lock(
        lock_name, argv_marker=argv_marker,
    )
    if not acquired:
        logger.warning(
            "heartbeat_monitor already running (pid=%s) -- exiting cleanly",
            conflicting,
        )
        return 0

    cfg = load_config()
    heartbeat_cfg = cfg.get("heartbeat", {}) if isinstance(cfg, dict) else {}
    write_interval = int(heartbeat_cfg.get("write_interval_seconds", DEFAULT_WRITE_INTERVAL_SECONDS))

    logger.info(
        "heartbeat_monitor starting: enabled=%s write_interval=%ds miss_threshold=%s",
        heartbeat_cfg.get("flatten_enabled", DEFAULT_FLATTEN_ENABLED),
        write_interval,
        heartbeat_cfg.get("miss_threshold", DEFAULT_MISS_THRESHOLD),
    )

    # Lazy-import MT5 — skip entirely when flatten disabled (we can run the
    # log-only path on machines without MetaTrader5 installed).
    mt5_module: Optional[Any] = None
    if heartbeat_cfg.get("flatten_enabled", DEFAULT_FLATTEN_ENABLED):
        try:
            import MetaTrader5 as mt5_module  # type: ignore[import-not-found]
        except ImportError:
            logger.warning("MetaTrader5 import failed — flatten will log FLATTEN_FAILED on trigger")
            mt5_module = None

    # Initial daemon heartbeat so the very first watchdog cycle sees the
    # monitor as healthy + producing.
    _runtime.write_daemon_heartbeat(
        lock_name, last_progress_at=datetime.now(timezone.utc),
    )

    state = MonitorState()
    try:
        while True:
            try:
                tick(
                    state,
                    config=cfg,
                    mt5_module=mt5_module,
                )
                # Daemon heartbeat after every successful tick. Allows
                # an out-of-band monitor to distinguish "PID alive AND
                # making progress" from "PID alive but stuck".
                _runtime.write_daemon_heartbeat(
                    lock_name, last_progress_at=datetime.now(timezone.utc),
                )
            except Exception as e:  # noqa: BLE001 — never crash the monitor
                logger.error("tick raised (non-fatal): %s", e, exc_info=True)
            time.sleep(max(1, write_interval))
    except KeyboardInterrupt:
        logger.info("heartbeat_monitor shutting down on SIGINT")
        return 0
    finally:
        _runtime.release_single_instance_lock(lock_name)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
