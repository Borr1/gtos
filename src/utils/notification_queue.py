"""Persistent, retry-safe Telegram notification queue.

Background
----------
The legacy ``src/notifications.py`` fire-and-forget pattern (daemon thread,
no retry, no persistence) silently loses CRITICAL alerts when the producer
process crashes mid-send or transient HTTPS failure occurs. The two
highest-stakes alert types — SPRT halt verdicts and heartbeat-flatten
cascade messages — are exactly the ones lost during MT5 disconnect, watchdog
kill, or live-host network blips.

The audit verdict: file-backed queue, priority-routed, exponential-backoff
retry, crash-safe restart. This module implements that policy.

Process model (2026-04-28)
--------------------------
The queue is consumed by a **dedicated long-lived worker process**, started
from ``start_all.bat`` and supervised by ``scripts/watchdog.ps1`` under the
lock ``knowledge_base/meta/.notification_queue_worker{_namespace}.lock``. Producers
(orchestrators, cron scripts like ``correlation_shock_monitor.py``,
``api_refusal_monitor.py``, ``no_data_alert_monitor.py``) only need to
*append* enqueue rows to the JSONL file and exit; they never need to start
or own a daemon thread.

Why: short-lived cron scripts that started the in-process daemon thread
lazily (via ``send`` → ``get_default_queue().start()``) would tear the
thread down when the process exited a fraction of a second later, leaving
the row on disk forever with ``retry_count: 0``. This was observed live on
2026-04-28 00:02 UTC — two correlation_shock alerts sat undelivered for
34+ minutes because no orchestrator process had triggered the lazy
singleton.

The in-process lazy daemon is **kept** as a defense-in-depth fallback for
long-lived processes (orchestrators) that emit alerts during their own
lifetime — but it is no longer the primary drain path. The worker process
is authoritative.

CLI
---
``python -m src.utils.notification_queue`` exposes::

    --worker         Run the long-lived poller (used by start_all.bat /
                     watchdog.ps1). Acquires a PID lock + drains forever.

    --drain-once     Process every entry whose ``ready_at()`` is in the
                     past + exit. Used by operators to flush stuck queues
                     without the worker, or by smoke tests.

    --queue-path P   Override the queue file (default is
                     ``GTOS_NOTIFICATION_QUEUE_PATH`` when set, else
                     ``pipeline_state/notification_queue.jsonl``).
    --runtime-namespace N
                     Scope the worker PID lock for dual-account runtimes.

Priority levels
---------------
* ``CRITICAL``  — SPRT halt, heartbeat-flatten, kill-switch. Persisted;
  retried indefinitely until delivery succeeds OR the alert ages out at
  ``CRITICAL_AGE_OUT_SECONDS`` (default 24 h, after which it is marked
  ``EXPIRED`` so the queue does not pile up dead messages).
* ``HIGH``      — Trade closes, errors, daily-loss-stop, drawdown alerts.
  Persisted; retried with exponential backoff up to ``HIGH_MAX_RETRIES``
  (default 5), backoff ladder 5s → 30s → 2 min → 10 min → 1 h.
* ``LOW``       — Trade fills, BE updates, daily summaries. Fire-and-forget;
  not persisted; one synchronous attempt and discard on failure.

Disk format
-----------
Append-only JSONL at the configured queue path. In dual-broker live mode this
is account-scoped by profile, for example
``pipeline_state/redacted_account_live_bee34003/notification_queue.jsonl``. Each
line is one of:

* **Enqueue row** (full schema)::

      {"alert_id": "<sha256-hex>", "ts_utc": "2026-04-26T...", "level": "CRITICAL",
       "message": "...", "retry_count": 0, "last_attempt_utc": null}

* **Marker row** (terminal state)::

      {"alert_id": "<sha256-hex>", "marker": "DELIVERED" | "EXPIRED" | "FAILED"}

  Markers carry only ``alert_id`` + ``marker`` so the on-disk overhead per
  delivery is small. A pending entry is "still pending" iff the queue file
  contains an enqueue row with that ``alert_id`` and no marker row for the
  same ``alert_id``.

Compaction
----------
After 100 marker rows accumulate (or daily on the first ``flush`` call after
UTC midnight crossing), the queue file is compacted: pending rows are
re-emitted into a temp file + ``os.replace``-ed over the live file. The old
markers are dropped from disk; the in-memory ``alert_id`` set retains them so
subsequent ``send`` calls still deduplicate.

Atomicity
---------
* Enqueue: append-mode write to JSONL (POSIX-atomic per row for typical
  payload sizes; Windows append is consistent in practice).
* Compaction: write temp + ``os.replace`` is atomic at the filesystem layer.
* Marker writes: append-mode (same atomicity guarantees as enqueue).
* Recovery: on startup, parse the queue file, separate enqueue rows from
  marker rows by ``alert_id``, retry pending rows.

Retry policy
------------
A daemon thread polls the configured queue file every ``POLL_INTERVAL_SECONDS``
(default 30s). For each pending row whose
``last_attempt_utc + backoff_for(retry_count)`` is in the past, it attempts
delivery via the configured ``transport`` callable. On success, it appends
a ``DELIVERED`` marker. On failure, it bumps ``retry_count`` (in memory) and
defers; the disk row is rewritten on compaction or new app start.

Out of scope
------------
* In-process clustering / leader election. One worker owns each account-scoped
  queue file. Dual-broker live mode relies on distinct queue paths and
  namespace-scoped worker locks rather than multiple workers draining one file.
* Strict ordering. Retry ladder is per-alert; alerts are not strictly
  FIFO (a HIGH that succeeds first delivers before a CRITICAL stuck in
  retry).
* Encryption / secret redaction. Messages go through unmodified.

Wire format (2026-04-28)
------------------------
Messages are sent to Telegram as **plain text** — ``parse_mode`` is NOT set
on the POST. Alert templates may contain unicode emoji glyphs but MUST NOT
contain HTML tags (``<b>``, ``<i>``, ``<code>``, etc.) or rely on Telegram
parsing the body. This prevents the entire HTML-injection bug class
(literal ``&``, ``<``, ``>`` in interpolated runtime values) that caused
the 2026-04-27 GBPJPY daily-loss-stop 400 storm. See
``src/notifications.py`` module docstring for the root-cause write-up.

References
----------
* Audit triage 2026-04-26 (H7): "critical alerts (SPRT halt, flatten,
  emergency stop): MUST be persistent; routine alerts (BE update, daily
  summary): can stay fire-and-forget".
* CEO directive 2026-04-26: "do things the right way dont just patch".
* HTML-ESCAPE BUG fix 2026-04-28: dropped ``parse_mode=HTML`` from
  ``_default_transport`` after literal ``P&L:`` + ``<= -4.00%`` in the
  daily-loss-stop alert produced 100+ HTTP 400s.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants (overridable via class kwargs)
# ---------------------------------------------------------------------------


class Level(str, Enum):
    """Priority levels. ``str`` mixin so values JSON-serialize as strings."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    LOW = "LOW"


# Default queue file path. Broker profiles can override this with
# notification_queue.queue_path; launcher/watchdog paths can also set
# GTOS_NOTIFICATION_QUEUE_PATH before the profile-aware runtime is loaded.
_DEFAULT_QUEUE_PATH: str = "pipeline_state/notification_queue.jsonl"
_DEFAULT_QUEUE_PATH_CONFIGURED: bool = False

# Retry ladder for HIGH alerts (seconds). 5s → 30s → 2 min → 10 min → 1 hr.
# Index = retry_count (already-attempted count); 0 = "first retry after the
# initial attempt failed".
_HIGH_BACKOFF_LADDER: tuple[int, ...] = (5, 30, 120, 600, 3600)

# CRITICAL alerts use the same ladder, but retry_count saturates at the
# top (1 h) and keeps trying — it never expires by retry count.
_CRITICAL_BACKOFF_LADDER: tuple[int, ...] = (5, 30, 120, 600, 3600)

# CRITICAL alerts age out after 24h to avoid a forever-pile of stale messages
# if Telegram is permanently broken on the host.
_CRITICAL_AGE_OUT_SECONDS: int = 24 * 60 * 60

# HIGH alerts give up after `len(_HIGH_BACKOFF_LADDER)` retries (5 retries).
_HIGH_MAX_RETRIES: int = len(_HIGH_BACKOFF_LADDER)

# Daemon polling cadence.
_POLL_INTERVAL_SECONDS: int = 30

# Compaction trigger: rewrite the queue file after this many DELIVERED /
# EXPIRED / FAILED markers accumulate.
_COMPACT_AFTER_MARKERS: int = 100


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _alert_id_for(message: str, ts_utc: str) -> str:
    """Deterministic 16-hex-char alert_id derived from (message, ts).

    Same (message, ts) → same alert_id → automatic dedup if a caller
    re-enqueues the same content in the same second.
    """
    h = hashlib.sha256()
    h.update(ts_utc.encode("utf-8"))
    h.update(b"\x00")
    h.update(message.encode("utf-8"))
    return h.hexdigest()[:16]


def _challenge() -> bool:
    """True only on the Challenge writer. Friends and tests keep the ladders."""
    try:
        from src.judgment.state_choices import on_challenge

        return bool(on_challenge())
    except Exception:
        return False


def _side(spot: str, facts: dict, positive: str, negative: str, instructions: str):
    """Choice on the Challenge writer. None off-challenge, and on empty, tie, or error."""
    if not _challenge():
        return None
    try:
        from src.judgment.state_choices import side

        return side(spot, facts, positive, negative, instructions)
    except Exception:
        return None


def _stored_wait() -> Optional[float]:
    """Seconds already stored for jev_call_timeout. Does not post a new ask."""
    if not _challenge():
        return None
    try:
        from src.judgment.jev_client import _stored_score

        score = _stored_score("jev_call_timeout")
    except Exception:
        return None
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return None
    if score > 0:
        return float(score)
    return None


def _whole_minutes(seconds: float) -> int:
    if seconds != seconds or seconds < 0:
        return 0
    return int(seconds // 60)


def _critical_expired(entry: "_Entry", now: datetime, critical_age_out_seconds: int) -> bool:
    """True only when a CRITICAL alert is expired and must be marked EXPIRED.

    Off the Challenge writer the 24h comparison stands. On it, only the
    answer ``expired`` expires the alert. ``keep``, empty, tie, and error
    leave it pending and do not restore that comparison.
    """
    if entry.level is not Level.CRITICAL:
        return False
    if not _challenge():
        return entry.age_seconds(now) >= critical_age_out_seconds
    chosen = _side(
        "notification.critical_age",
        {
            "level": entry.level.value,
            "age_minutes": _whole_minutes(entry.age_seconds(now)),
            "retry_count": int(entry.retry_count),
        },
        "expired",
        "keep",
        "Has this critical alert aged out of the queue?",
    )
    return chosen == "expired"


def _high_stopped(entry: "_Entry", high_max_retries: int) -> bool:
    """True only when a HIGH alert must be marked FAILED.

    Off the Challenge writer the retry cap stands. On it, only ``stop``
    stops the alert. ``continue``, empty, tie, and error leave it pending.
    CRITICAL is never stopped by retry count.
    """
    if entry.level is not Level.HIGH:
        return False
    if not _challenge():
        return entry.retry_count >= high_max_retries
    chosen = _side(
        "notification.high_retries",
        {"level": entry.level.value, "retry_count": int(entry.retry_count)},
        "stop",
        "continue",
        "Has this high alert been attempted enough times to stop?",
    )
    return chosen == "stop"


def _retry_due(entry: "_Entry", now: datetime) -> bool:
    """True when this cycle should attempt delivery.

    The first attempt (no last attempt) is due immediately, with no ask.
    Off the Challenge writer the backoff ladder stands. On it, only ``due``
    sends. ``wait``, empty, tie, and error are not a send and do not
    restore the ladder.
    """
    if _parse_iso(entry.last_attempt_utc) is None:
        return True
    if not _challenge():
        return entry.ready_at() <= now
    last = _parse_iso(entry.last_attempt_utc)
    elapsed = 0.0 if last is None else (now - last).total_seconds()
    chosen = _side(
        "notification.retry_due",
        {
            "level": entry.level.value,
            "retry_count": int(entry.retry_count),
            "minutes_since_attempt": _whole_minutes(elapsed),
        },
        "due",
        "wait",
        "Is another delivery attempt due now?",
    )
    return chosen == "due"


def _ask_expired(entries: list["_Entry"], now: datetime) -> set[str]:
    """Concurrent age-out asks for CRITICAL rows only. Other levels are not asked."""
    critical = [entry for entry in entries if entry.level is Level.CRITICAL]
    if not critical:
        return set()

    def _work(entry: "_Entry") -> tuple[str, bool]:
        return entry.alert_id, _critical_expired(entry, now, _CRITICAL_AGE_OUT_SECONDS)

    from concurrent.futures import ThreadPoolExecutor

    expired: set[str] = set()
    with ThreadPoolExecutor(max_workers=len(critical)) as pool:
        for aid, flag in pool.map(_work, critical):
            if flag:
                expired.add(aid)
    return expired


def _ask_drain(entries: list["_Entry"], now: datetime) -> dict[str, dict[str, bool]]:
    """Ask age-out, retry-stop, and due together. One state, one post, shared by cache."""
    out: dict[str, dict[str, bool]] = {}
    jobs: list[tuple[str, str, _Entry]] = []
    for entry in entries:
        out[entry.alert_id] = {"expired": False, "stopped": False, "due": False}
        if entry.level is Level.CRITICAL:
            jobs.append((entry.alert_id, "expired", entry))
        if entry.level is Level.HIGH:
            jobs.append((entry.alert_id, "stopped", entry))
        if _parse_iso(entry.last_attempt_utc) is None:
            out[entry.alert_id]["due"] = True
        else:
            jobs.append((entry.alert_id, "due", entry))
    if not jobs:
        return out

    def _work(item: tuple[str, str, _Entry]) -> tuple[str, str, bool]:
        aid, kind, entry = item
        if kind == "expired":
            return aid, kind, _critical_expired(entry, now, _CRITICAL_AGE_OUT_SECONDS)
        if kind == "stopped":
            return aid, kind, _high_stopped(entry, _HIGH_MAX_RETRIES)
        return aid, kind, _retry_due(entry, now)

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        for aid, kind, value in pool.map(_work, jobs):
            out[aid][kind] = bool(value)
    return out


def _transport_timeout() -> Optional[float]:
    """HTTP wait. Off-challenge the existing 10s stands. On-challenge a stored
    jev_call_timeout if one was already returned, otherwise no planted wait.
    """
    if not _challenge():
        return 10
    return _stored_wait()


def _seconds_until_next_minute(now: datetime) -> float:
    """Clock remainder to the next UTC minute. 60 is the length of a minute."""
    second = int(now.second)
    if second <= 0:
        return 60.0
    return float(60 - second)


# ---------------------------------------------------------------------------
# In-memory entry
# ---------------------------------------------------------------------------


@dataclass
class _Entry:
    """One pending alert in the in-memory queue."""

    alert_id: str
    level: Level
    message: str
    ts_utc: str                              # ISO-8601 UTC enqueue timestamp
    retry_count: int = 0                     # attempts so far (0 = none yet)
    last_attempt_utc: Optional[str] = None   # ISO-8601 UTC of last attempt

    def to_row(self) -> dict:
        """Disk schema for an enqueue row."""
        return {
            "alert_id": self.alert_id,
            "level": self.level.value,
            "message": self.message,
            "ts_utc": self.ts_utc,
            "retry_count": self.retry_count,
            "last_attempt_utc": self.last_attempt_utc,
        }

    def age_seconds(self, now: Optional[datetime] = None) -> float:
        now = now or _now_utc()
        enqueued = _parse_iso(self.ts_utc) or now
        return (now - enqueued).total_seconds()

    def ready_at(self) -> datetime:
        """When the next retry is allowed (now if never attempted)."""
        last = _parse_iso(self.last_attempt_utc)
        if last is None:
            return _parse_iso(self.ts_utc) or _now_utc()
        if self.level is Level.CRITICAL:
            ladder = _CRITICAL_BACKOFF_LADDER
        else:
            ladder = _HIGH_BACKOFF_LADDER
        idx = min(max(0, self.retry_count - 1), len(ladder) - 1)
        return last + timedelta(seconds=ladder[idx])


# ---------------------------------------------------------------------------
# PersistentNotificationQueue
# ---------------------------------------------------------------------------


# Default transport: stdlib HTTPS POST to Telegram. Importing
# notifications._send would create a cycle (notifications imports this
# module), so we re-implement the minimal POST here.

def _default_transport(text: str) -> bool:
    """Synchronous Telegram POST. Return True iff HTTP 200.

    Sends as **plain text** — ``parse_mode`` is intentionally NOT set. Alert
    bodies routinely contain runtime-interpolated values with ``<``, ``>``,
    or ``&`` (e.g. ``MTM P&L: -4.07% <= -4.00% cap``). Under
    ``parse_mode=HTML`` Telegram returns HTTP 400 on those messages, the
    CRITICAL queue retries indefinitely, and the CEO never sees the alert.
    See ``src/notifications.py`` module docstring for the full root-cause
    write-up (HTML-ESCAPE BUG, 2026-04-28).
    """
    import json as _json
    import ssl
    import urllib.request

    # ---- Authorization gate (F30 / Q7) ---------------------------------
    # Everything below this point is operator-facing: an HTTPS POST to
    # Borhen's Telegram, or a durable trade-shaped record in
    # pipeline_state/UNDELIVERED_CRITICAL_ALERTS.jsonl that monitor_books
    # watches. Neither may happen in a process that was never authorized to
    # page the operator. Credential presence is NOT authorization — F30
    # measured pytest producing "[FTMO] 🟢 LONG BTCUSD ... risk 0.40%
    # (~$397)" here, stopped only by the creds happening to be unset.
    #
    # Fail-closed: absence of a grant is a refusal. See
    # src/safety/notification_authorization.py for why this is a
    # presence-of-authorization check and not an "are we testing?" check.
    from src.safety.notification_authorization import delivery_authorization

    _auth = delivery_authorization()
    if not _auth.allowed:
        logger.error(
            "notification_queue: delivery REFUSED (unauthorized process); "
            "alert not sent and not persisted: %s | preview=%r",
            _auth.detail, text[:120],
        )
        # False = "not delivered", so a CRITICAL stays pending and is never
        # falsely marked DELIVERED. An unauthorized live process is a
        # misconfiguration and must stay loud rather than silently succeed.
        return False

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        # No credentials → non-retryable (return True so the CRITICAL queue does not pile up forever),
        # BUT do NOT let the alert vanish silently: PERSIST it to a durable, inspectable marker file so
        # a dropped CRITICAL is recoverable (the operator's only push channel must not fail OPEN —
        # live-ops intel cycle-2). A separate watcher (monitor_books) can detect the marker's presence.
        logger.error(
            "notification_queue: TELEGRAM_* creds missing; CRITICAL alert NOT delivered, persisting to "
            "pipeline_state/UNDELIVERED_CRITICAL_ALERTS.jsonl: %s", text[:120],
        )
        try:
            import json as _json2
            import time as _time2
            from pathlib import Path as _Path2
            _mk = _Path2("pipeline_state")
            _mk.mkdir(parents=True, exist_ok=True)
            with open(_mk / "UNDELIVERED_CRITICAL_ALERTS.jsonl", "a", encoding="utf-8") as _fh:
                _fh.write(_json2.dumps({"ts_epoch": _time2.time(), "reason": "telegram_creds_missing",
                                        "text": text}) + "\n")
        except Exception:
            pass
        return True
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = _json.dumps(
        {"chat_id": chat_id, "text": text}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=_transport_timeout(), context=ctx) as resp:
            return resp.status == 200
    except Exception as e:
        logger.info("notification_queue: transport failed: %s", e)
        return False


class PersistentNotificationQueue:
    """File-backed retry queue for prioritized Telegram alerts.

    Usage::

        q = PersistentNotificationQueue()
        q.start()                                     # spawn daemon poller
        q.send("FLATTEN: positions closed", level=Level.CRITICAL)
        q.send("Trade closed: +1.5R", level=Level.HIGH)
        q.send("BE moved", level=Level.LOW)           # fire-and-forget
        # ... process exits ...
        # On next process start:
        q = PersistentNotificationQueue()
        q.start()                                     # recovery loads pending rows

    Thread-safety
    -------------
    Public methods acquire ``self._lock``. The daemon thread holds the lock
    while iterating + draining the in-memory queue, releasing for each
    transport call (so a slow transport doesn't block enqueue).
    """

    def __init__(
        self,
        queue_path: str | os.PathLike = _DEFAULT_QUEUE_PATH,
        *,
        transport: Optional[Callable[[str], bool]] = None,
        poll_interval_seconds: int = _POLL_INTERVAL_SECONDS,
        critical_age_out_seconds: int = _CRITICAL_AGE_OUT_SECONDS,
        high_max_retries: int = _HIGH_MAX_RETRIES,
        compact_after_markers: int = _COMPACT_AFTER_MARKERS,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self.queue_path: Path = Path(queue_path)
        self.transport: Callable[[str], bool] = transport or _default_transport
        self.poll_interval_seconds: int = int(poll_interval_seconds)
        self.critical_age_out_seconds: int = int(critical_age_out_seconds)
        self.high_max_retries: int = int(high_max_retries)
        self.compact_after_markers: int = int(compact_after_markers)
        self._clock = clock or _now_utc

        self._lock = threading.RLock()
        # Pending entries by alert_id. Insertion order = enqueue order.
        self._pending: dict[str, _Entry] = {}
        # Marker counts for compaction trigger.
        self._marker_count: int = 0
        # Last UTC date we ran the daily-compaction check.
        self._last_compact_date: str = ""

        # Daemon thread machinery.
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._loaded: bool = False

    # ----- public API --------------------------------------------------------

    def start(self) -> None:
        """Load queue from disk + spawn the daemon poller. Idempotent."""
        with self._lock:
            if not self._loaded:
                self._recover_from_disk()
                self._loaded = True
            if self._thread is None or not self._thread.is_alive():
                self._stop_event.clear()
                self._thread = threading.Thread(
                    target=self._poll_loop,
                    daemon=True,
                    name="notif-queue-poller",
                )
                self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the daemon to stop + join. Idempotent."""
        self._stop_event.set()
        t = self._thread
        if t is not None and t.is_alive():
            t.join(timeout)

    def send(
        self,
        message: str,
        *,
        level: Level = Level.HIGH,
        alert_id: Optional[str] = None,
    ) -> str:
        """Enqueue an alert.

        Returns the alert_id (auto-generated if not provided). The queue
        ensures dedup: re-sending the same alert_id is a no-op while it is
        still pending or has a terminal marker.
        """
        if level is Level.LOW:
            # Fire-and-forget — single synchronous attempt, no persistence.
            try:
                self.transport(message)
            except Exception as e:  # pragma: no cover — defensive
                logger.info("notification_queue: LOW transport failed: %s", e)
            return ""

        ts_utc = _iso(self._clock())
        if alert_id is None:
            alert_id = _alert_id_for(message, ts_utc)

        with self._lock:
            if alert_id in self._pending:
                # Already queued — dedup.
                return alert_id
            entry = _Entry(
                alert_id=alert_id,
                level=level,
                message=message,
                ts_utc=ts_utc,
            )
            self._pending[alert_id] = entry
            self._append_row(entry.to_row())
        return alert_id

    def flush(self) -> int:
        """Synchronously drain the queue once. Returns # alerts dispatched.

        Used by tests + by the daemon's polling loop. Honors retry timing —
        an entry whose ``ready_at()`` is in the future is left pending.
        """
        return self._drain_once()

    def pending_count(self) -> int:
        """Return the # of pending alerts (not yet DELIVERED/EXPIRED/FAILED)."""
        with self._lock:
            return len(self._pending)

    # ----- internals: recovery ----------------------------------------------

    def _recover_from_disk(self) -> None:
        """Read queue file + re-load pending alerts.

        Pending = enqueue rows whose ``alert_id`` has no DELIVERED/EXPIRED/
        FAILED marker. Older-than-age-out CRITICAL rows are dropped at load
        time (they would expire on first poll anyway).
        """
        self._pending = {}
        self._marker_count = 0
        if not self.queue_path.exists():
            return

        # Pass 1: collect markers.
        terminal: set[str] = set()
        try:
            with open(self.queue_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    marker = obj.get("marker")
                    aid = obj.get("alert_id")
                    if marker and aid:
                        terminal.add(aid)
                        self._marker_count += 1
        except OSError as e:
            logger.warning("notification_queue: recovery pass-1 failed: %s", e)
            return

        # Pass 2: load pending enqueue rows that aren't terminal.
        # If the same alert_id has multiple enqueue rows, keep the latest
        # (overwrite by alert_id ensures most-recent retry_count/last_attempt
        # state from the last compaction wins).
        try:
            with open(self.queue_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if "marker" in obj:
                        continue
                    aid = obj.get("alert_id")
                    if not aid or aid in terminal:
                        continue
                    try:
                        level = Level(obj["level"])
                    except (KeyError, ValueError):
                        continue
                    entry = _Entry(
                        alert_id=aid,
                        level=level,
                        message=obj.get("message", ""),
                        ts_utc=obj.get("ts_utc") or _iso(self._clock()),
                        retry_count=int(obj.get("retry_count", 0) or 0),
                        last_attempt_utc=obj.get("last_attempt_utc"),
                    )
                    self._pending[aid] = entry
        except OSError as e:
            logger.warning("notification_queue: recovery pass-2 failed: %s", e)
            return

        # Drop CRITICAL rows that have aged out — they're going to expire
        # on first poll anyway; trim them now so the in-memory set stays
        # bounded across long downtime. On the Challenge writer the age-out
        # is the hop, and an empty answer does not drop the row.
        now = self._clock()
        pending = list(self._pending.values())
        if _challenge() and pending:
            expired_ids = _ask_expired(pending, now)
            for aid in list(self._pending):
                if aid in expired_ids:
                    self._mark(aid, "EXPIRED")
                    self._pending.pop(aid, None)
        else:
            for aid, entry in list(self._pending.items()):
                if _critical_expired(entry, now, self.critical_age_out_seconds):
                    self._mark(aid, "EXPIRED")
                    self._pending.pop(aid, None)

    # ----- internals: poll loop ---------------------------------------------

    def _poll_loop(self) -> None:
        """Daemon thread: drain queue, sleep, repeat."""
        while not self._stop_event.is_set():
            try:
                self._drain_once()
                self._maybe_compact()
            except Exception as e:  # pragma: no cover — defensive
                logger.warning("notification_queue: poll iteration failed: %s", e)
            # Sleep with the stop event so stop() can interrupt early.
            # Off the Challenge writer the configured poll interval stands.
            # On it, a stored jev_call_timeout if one exists, otherwise the
            # seconds left until the next UTC minute. No new ask, and an
            # empty queue does not post.
            if _challenge():
                wait = _stored_wait()
                if wait is None:
                    wait = _seconds_until_next_minute(self._clock())
            else:
                wait = float(self.poll_interval_seconds)
            self._stop_event.wait(wait)

    # ----- internals: drain --------------------------------------------------

    def _drain_once(self) -> int:
        """Attempt delivery of every entry that is due this cycle.

        ``ready_at()`` stays the ladder so an external comparison can still
        read it. The drain itself uses the hop on the Challenge writer.
        """
        now = self._clock()
        delivered = 0
        with self._lock:
            ids = list(self._pending)
            snapshot = [self._pending[aid] for aid in ids if aid in self._pending]
        challenge = _challenge() and bool(snapshot)
        flags = _ask_drain(snapshot, now) if challenge else {}
        for aid in ids:
            with self._lock:
                entry = self._pending.get(aid)
                if entry is None:
                    continue
                if challenge:
                    row = flags.get(aid) or {}
                    expired = bool(row.get("expired"))
                    stopped = bool(row.get("stopped"))
                    due = bool(row.get("due"))
                else:
                    expired = _critical_expired(entry, now, self.critical_age_out_seconds)
                    stopped = _high_stopped(entry, self.high_max_retries)
                    due = _retry_due(entry, now)
                # Age-out CRITICAL alerts before any transport attempt.
                if expired:
                    self._mark(aid, "EXPIRED")
                    self._pending.pop(aid, None)
                    continue
                # Retry-count cap for HIGH alerts.
                if stopped:
                    self._mark(aid, "FAILED")
                    self._pending.pop(aid, None)
                    continue
                # Skip if not yet ready. Empty is not a send.
                if not due:
                    continue
                # Snapshot for the transport call. We release the lock
                # around the transport so a slow HTTP doesn't block enqueue.
                msg = entry.message
            ok = False
            try:
                ok = bool(self.transport(msg))
            except Exception as e:  # pragma: no cover — defensive
                logger.info("notification_queue: transport raised: %s", e)
                ok = False
            with self._lock:
                # Re-fetch — entry may have been removed by another path.
                entry = self._pending.get(aid)
                if entry is None:
                    continue
                if ok:
                    self._mark(aid, "DELIVERED")
                    self._pending.pop(aid, None)
                    delivered += 1
                else:
                    entry.retry_count += 1
                    entry.last_attempt_utc = _iso(now)
                    # Persist the updated retry state (compaction will dedup).
                    self._append_row(entry.to_row())
        return delivered

    # ----- internals: disk writes -------------------------------------------

    def _ensure_parent(self) -> None:
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)

    def _append_row(self, row: dict) -> None:
        """Append a single row to the queue file (atomic per-row)."""
        self._ensure_parent()
        try:
            with open(self.queue_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
        except OSError as e:
            logger.warning("notification_queue: append failed: %s", e)

    def _mark(self, alert_id: str, marker: str) -> None:
        """Append a terminal marker row + bump compaction counter."""
        self._append_row({"alert_id": alert_id, "marker": marker})
        self._marker_count += 1

    def _maybe_compact(self) -> None:
        """Compact the queue file if marker count or daily timer triggers."""
        with self._lock:
            today = self._clock().strftime("%Y-%m-%d")
            should_compact = False
            if self._marker_count >= self.compact_after_markers:
                should_compact = True
            if today != self._last_compact_date and self._marker_count > 0:
                should_compact = True
            self._last_compact_date = today
            if not should_compact:
                return
            self._compact_locked()

    def _compact_locked(self) -> None:
        """Rewrite queue file with only pending rows. Caller holds the lock.

        Strategy: write to ``{queue_path}.tmp`` then ``os.replace`` over the
        live path. Atomic at the filesystem layer.
        """
        if not self.queue_path.exists():
            self._marker_count = 0
            return
        tmp = self.queue_path.with_suffix(self.queue_path.suffix + ".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                for entry in self._pending.values():
                    f.write(json.dumps(entry.to_row()) + "\n")
            os.replace(str(tmp), str(self.queue_path))
            self._marker_count = 0
        except OSError as e:
            logger.warning("notification_queue: compaction failed: %s", e)
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Module-level singleton (for callers that don't want to manage a queue obj)
# ---------------------------------------------------------------------------


_SINGLETON: Optional[PersistentNotificationQueue] = None
_SINGLETON_LOCK = threading.Lock()


def get_default_queue() -> PersistentNotificationQueue:
    """Return the lazily-constructed module-wide singleton.

    Called from ``src.notifications.notify_alert`` for CRITICAL/HIGH levels
    + from ``src.components.sprt_halt_alert_template.format_telegram_alert``
    callers (the orchestrator's SPRT-halt branch). The singleton's daemon
    thread is started lazily on first ``send`` to avoid creating a thread
    in test contexts that never use the queue.
    """
    global _SINGLETON
    with _SINGLETON_LOCK:
        if _SINGLETON is None:
            _SINGLETON = PersistentNotificationQueue(
                queue_path=_effective_default_queue_path(),
                poll_interval_seconds=_POLL_INTERVAL_SECONDS,
                critical_age_out_seconds=_CRITICAL_AGE_OUT_SECONDS,
                high_max_retries=_HIGH_MAX_RETRIES,
                compact_after_markers=_COMPACT_AFTER_MARKERS,
            )
        return _SINGLETON


def _reset_singleton_for_tests() -> None:
    """Clear the module singleton so a test fixture can install its own."""
    global _SINGLETON
    with _SINGLETON_LOCK:
        if _SINGLETON is not None:
            _SINGLETON.stop()
        _SINGLETON = None


def configure_from_config(config: dict | None) -> None:
    """Apply ``notification_queue.*`` config overrides to module defaults.

    Reads the optional config block::

        notification_queue:
          queue_path: pipeline_state/redacted_account_live_bee34003/notification_queue.jsonl
          poll_interval_seconds: 30
          critical_age_out_seconds: 86400
          high_max_retries: 5
          compact_after_markers: 100

    Must be called BEFORE the first ``send`` call to take effect — typically
    once at orchestrator startup. Missing / partial blocks fall back to
    module defaults; an entirely missing block is a no-op.

    Drops the singleton so the next ``get_default_queue`` picks up the new
    defaults.
    """
    global _POLL_INTERVAL_SECONDS, _CRITICAL_AGE_OUT_SECONDS
    global _HIGH_MAX_RETRIES, _COMPACT_AFTER_MARKERS
    global _DEFAULT_QUEUE_PATH, _DEFAULT_QUEUE_PATH_CONFIGURED
    if not isinstance(config, dict):
        return
    nq_cfg = config.get("notification_queue")
    if not isinstance(nq_cfg, dict):
        return
    queue_path = nq_cfg.get("queue_path")
    if queue_path is not None:
        path_text = str(queue_path).strip()
        if path_text:
            _DEFAULT_QUEUE_PATH = path_text
            _DEFAULT_QUEUE_PATH_CONFIGURED = True
        else:
            logger.warning(
                "notification_queue: invalid queue_path=%r; keeping default",
                queue_path,
            )
    for key, target in (
        ("poll_interval_seconds", "_POLL_INTERVAL_SECONDS"),
        ("critical_age_out_seconds", "_CRITICAL_AGE_OUT_SECONDS"),
        ("high_max_retries", "_HIGH_MAX_RETRIES"),
        ("compact_after_markers", "_COMPACT_AFTER_MARKERS"),
    ):
        if key not in nq_cfg:
            continue
        try:
            value = int(nq_cfg[key])
        except (TypeError, ValueError):
            logger.warning(
                "notification_queue: invalid %s=%r; keeping default",
                key, nq_cfg[key],
            )
            continue
        globals()[target] = value
    _reset_singleton_for_tests()


def _effective_default_queue_path() -> str:
    """Return the configured or environment-derived default queue path."""
    if _DEFAULT_QUEUE_PATH_CONFIGURED:
        return _DEFAULT_QUEUE_PATH
    env_path = os.environ.get("GTOS_NOTIFICATION_QUEUE_PATH")
    if env_path and env_path.strip():
        return env_path.strip()
    return _DEFAULT_QUEUE_PATH


def send(
    message: str,
    *,
    level: Level = Level.HIGH,
    alert_id: Optional[str] = None,
) -> str:
    """Convenience wrapper: enqueue via the module-wide singleton.

    Starts the singleton's daemon poller on first use as a defense-in-depth
    fallback for long-lived processes. The authoritative drain path is the
    external worker process started by ``start_all.bat`` / supervised by
    ``scripts/watchdog.ps1`` (see ``main()`` below). Short-lived cron
    scripts that exit after enqueueing rely on the worker — the lazy
    in-process daemon dies with them.
    """
    q = get_default_queue()
    q.start()
    return q.send(message, level=level, alert_id=alert_id)


# ---------------------------------------------------------------------------
# CLI: worker + drain-once entry points
# ---------------------------------------------------------------------------


def _drain_once_cli(queue_path: str) -> int:
    """One-shot drain. Returns # alerts dispatched. Exit-code wrapper for CLI.

    Loads pending rows from ``queue_path``, attempts every entry whose
    ``ready_at()`` is in the past, and exits. Intended for operator use
    when the worker is offline (or before deployment) and the queue has
    accumulated stuck entries.
    """
    q = PersistentNotificationQueue(queue_path=queue_path)
    # Load disk state explicitly without starting the daemon thread.
    with q._lock:
        if not q._loaded:
            q._recover_from_disk()
            q._loaded = True
    pending = q.pending_count()
    delivered = q.flush()
    print(
        f"notification_queue: drain-once on {queue_path}: "
        f"pending_loaded={pending} delivered={delivered} "
        f"still_pending={q.pending_count()}",
        flush=True,
    )
    return delivered


def _worker_lock_path(runtime_namespace: str | None = None) -> Path:
    namespace = (runtime_namespace or "").strip()
    suffix = f"_{namespace}" if namespace else ""
    return (
        Path(__file__).resolve().parent.parent.parent
        / "knowledge_base" / "meta" / f".notification_queue_worker{suffix}.lock"
    )


def _run_worker_cli(queue_path: str, runtime_namespace: str | None = None) -> int:
    """Long-lived worker loop. Acquires PID lock, polls forever, returns 0 on graceful stop.

    Lock convention matches the rest of the watchdog-supervised siblings:
    ``knowledge_base/meta/.notification_queue_worker{_namespace}.lock``
    containing the PID as text. Watchdog reads the file, checks the PID,
    restarts on death.

    Signal handling: SIGINT / SIGTERM trigger a graceful stop (worker
    finishes the in-flight drain pass, then exits). On Windows there is
    no SIGTERM — Ctrl-C / taskkill /F deliver as KeyboardInterrupt or a
    hard kill respectively; the lock file is best-effort cleaned up on
    exit but a hard kill leaves it — the watchdog's ``Test-ProcessAlive``
    check correctly treats a stale-PID lock as "process dead, restart".
    """
    import signal

    # Lock file lives next to the orchestrator + heartbeat locks.
    lock_path = _worker_lock_path(runtime_namespace)
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # If a previous worker died unexpectedly, the lock may persist with a
    # stale PID. We check + clean up, matching the watchdog's behavior.
    if lock_path.exists():
        try:
            stale_pid_text = lock_path.read_text(encoding="utf-8").strip()
            if stale_pid_text:
                stale_pid = int(stale_pid_text)
                # Check if the PID is still alive by sending signal 0
                # (no-op probe; raises if the PID is gone).
                try:
                    os.kill(stale_pid, 0)
                    logger.error(
                        "notification_queue worker: another worker is alive "
                        "(PID=%d via %s). Refusing to start a duplicate.",
                        stale_pid, lock_path,
                    )
                    return 2
                except (OSError, ProcessLookupError):
                    logger.info(
                        "notification_queue worker: stale lock from PID=%d, cleaning up",
                        stale_pid,
                    )
        except (OSError, ValueError):
            pass

    try:
        lock_path.write_text(str(os.getpid()), encoding="utf-8")
    except OSError as e:
        logger.error("notification_queue worker: lock write failed: %s", e)
        return 2

    logger.info(
        "notification_queue worker: started PID=%d queue=%s namespace=%s lock=%s",
        os.getpid(), queue_path, runtime_namespace or "", lock_path,
    )

    q = PersistentNotificationQueue(queue_path=queue_path)
    q.start()  # spawns the polling thread; worker process keeps it alive.

    stop_flag = threading.Event()

    def _on_signal(signum, frame):  # noqa: ARG001 — frame unused
        logger.info(
            "notification_queue worker: received signal %d, draining + stopping",
            signum,
        )
        stop_flag.set()

    # On Windows, SIGTERM is not delivered for taskkill /F — KeyboardInterrupt
    # is the realistic graceful path; fall through to KeyboardInterrupt below.
    try:
        signal.signal(signal.SIGINT, _on_signal)
    except (ValueError, OSError):  # pragma: no cover — non-main thread
        pass
    if hasattr(signal, "SIGTERM"):
        try:
            signal.signal(signal.SIGTERM, _on_signal)
        except (ValueError, OSError):  # pragma: no cover
            pass

    try:
        # Block in main thread until signaled. The PersistentNotificationQueue's
        # own daemon thread does the polling work; we just keep the process
        # alive so daemon threads survive.
        while not stop_flag.is_set():
            stop_flag.wait(timeout=5.0)
    except KeyboardInterrupt:
        logger.info("notification_queue worker: KeyboardInterrupt, draining + stopping")
    finally:
        try:
            q.stop(timeout=10.0)
        except Exception as e:  # pragma: no cover — defensive
            logger.warning("notification_queue worker: stop() raised %s", e)
        try:
            if lock_path.exists():
                lock_path.unlink()
        except OSError:
            pass
        logger.info("notification_queue worker: stopped")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    """CLI dispatcher: ``--worker`` runs forever; ``--drain-once`` does one pass.

    See module docstring for usage. Returns process exit code.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)
    except Exception:
        pass

    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m src.utils.notification_queue",
        description="GTOS notification queue: worker daemon or one-shot drain.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--worker", action="store_true",
        help="Run the long-lived poller daemon (used by start_all.bat).",
    )
    mode.add_argument(
        "--drain-once", action="store_true",
        help="Process every entry whose ready_at() is in the past + exit.",
    )
    parser.add_argument(
        "--queue-path", default=_effective_default_queue_path(),
        help=(
            "Path to the JSONL queue file (default: GTOS_NOTIFICATION_QUEUE_PATH "
            f"when set, else {_DEFAULT_QUEUE_PATH})."
        ),
    )
    parser.add_argument(
        "--runtime-namespace",
        default=os.environ.get("GTOS_RUNTIME_NAMESPACE", ""),
        help="Runtime namespace used to scope the worker PID lock.",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        help="Python logging level (default: INFO).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # This CLI *is* the live delivery path (watchdog.ps1:1516 launches it as
    # `python -m src.utils.notification_queue --worker`), so it takes explicit
    # responsibility for paging the operator. Delivery is default-deny
    # process-wide; without this grant the worker would drain nothing.
    from src.safety.notification_authorization import authorize_operator_delivery

    authorize_operator_delivery(
        reason=(
            "notification_queue CLI "
            + ("--worker" if args.worker else "--drain-once")
            + f" queue={args.queue_path}"
        )
    )

    halt_flag = Path("pipeline_state/RESEARCH_RUNTIME_HALT.flag")
    if halt_flag.exists():
        logging.getLogger(__name__).info(
            "RESEARCH_RUNTIME_HALT active at %s; notification queue CLI exiting.",
            halt_flag,
        )
        return 0

    if args.drain_once:
        _drain_once_cli(args.queue_path)
        return 0
    return _run_worker_cli(args.queue_path, runtime_namespace=args.runtime_namespace)


if __name__ == "__main__":
    raise SystemExit(main())
