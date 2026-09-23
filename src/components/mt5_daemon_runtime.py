"""Shared runtime helpers for sibling MT5 daemons (tick capture, heartbeat
monitor, displacement logger).

Why this module exists
----------------------
On 2026-04-28 the watchdog cron was observed restarting NINE sibling daemons
(7 tick capture + heartbeat + displacement) every 15-min cycle. Diagnosis:

1. **Lock-PID identity confusion (Windows-specific).** The watchdog launched
   each daemon via ``cmd.exe /c "... && python ..."`` and wrote the
   ``cmd.exe`` PID into the lock file. ``cmd.exe /c`` blocks on its chained
   command, so the PID stays valid for the lifetime of the python child --
   *most of the time*. But Windows occasionally separates them (job-object
   inheritance edge cases, broken redirections, fast cmd.exe early-exit on
   environment race), leaving an orphan python whose PPID points to a dead
   cmd.exe. Next watchdog cycle then reads the dead cmd.exe PID, declares
   the daemon "DEAD", and spawns ANOTHER python. Repeat for hours: 7+ live
   python orphans for one symbol, all racing on the same parquet write.
   Live evidence: ``logs/watchdog.log`` shows 76 ``[TICK_CAP_XAUUSD] STARTED``
   events between 2026-04-27 00:00 and 2026-04-28 09:00, while
   ``data/ticks/XAUUSD/`` directory was never created (the orphans cannot
   subscribe to the symbol — see #2 — so they never write).

2. **Symbol subscription not enforced on every reconnect.** The original
   ``tick_capture.main`` called ``mt5.symbol_select(sym, True)`` only when
   ``info.visible`` was False. Empirically (redacted_account broker, FX/metals on
   reconnect) ``info.visible`` reads True even when the tick stream is not
   actually subscribed -- ``copy_ticks_from`` returns ``None`` / empty list
   forever, ``symbol_info_tick`` returns the same stale tick from 32+ hours
   ago. Live evidence: ``logs/tick_capture_XAUUSD.log`` showed
   ``no ticks for 117500+ s`` warnings every 2 seconds with the same daemon
   process. The fix is to always call ``symbol_select(sym, True)`` then
   verify a fresh tick arrives before declaring the symbol healthy, with
   exponential backoff + reconnect on failure.

3. **No "alive but stalled" detection.** The watchdog only checked PID
   liveness, not whether the daemon was making progress. A python process
   stuck in a ``no ticks`` warning loop counts as "healthy" -- yet the
   tick-feature pipeline is functionally dead. The shared helper writes a
   per-daemon heartbeat file with a "last successful operation" timestamp
   so an out-of-band monitor (or future watchdog upgrade) can detect this.

This module fixes all three pathologies in ONE place so the four sibling
daemons (tick capture, heartbeat monitor, displacement logger, and any
future addition) inherit the fix.

Public API
----------

- ``acquire_single_instance_lock(name, lock_dir)`` — atomic single-instance
  enforcement. Writes own PID to lock file. If the lock holder is dead OR
  the lock holder PID does not correspond to a python process running with
  matching argv, the lock is reclaimed. Prevents both orphan-python-pile-up
  AND legitimate concurrent runs.
- ``release_single_instance_lock(name, lock_dir)`` — best-effort cleanup
  on shutdown.
- ``ensure_mt5_symbol_ready(mt5_module, symbol, ...)`` — call
  ``mt5.symbol_select`` unconditionally, verify ``symbol_info_tick`` returns
  a fresh tick, retry with backoff on stale/None. Returns True on healthy
  subscription.
- ``write_daemon_heartbeat(name, ...)`` — write own-PID + last-progress
  timestamp + custom payload to ``pipeline_state/daemon_heartbeat_{NAME}.json``.
- ``install_signal_handlers(stop_callback)`` — uniform SIGINT / SIGTERM
  handling that flips a stop flag without raising.

The module is dependency-light (no MT5 import at module level — the helpers
take an mt5 module as a parameter so tests can substitute a mock).
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

logger = logging.getLogger(__name__)


# ── MODULE-LEVEL paths (monkeypatch in tests) ─────────────────────────────
# Absolute paths derived from this file's location so the helpers work
# regardless of the caller's CWD. Tests override via module-ref monkeypatch
# (``monkeypatch.setattr(_mod, "LOCK_DIR", tmp_path)``).

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
LOCK_DIR: Path = PROJECT_ROOT / "knowledge_base" / "meta"
HEARTBEAT_DIR: Path = PROJECT_ROOT / "pipeline_state"

# Stale-tick threshold used by ``ensure_mt5_symbol_ready`` to verify the
# subscription actually delivered a tick. Default 5 seconds is generous
# enough for any open kill zone and tight enough that a truly subscribed
# symbol passes immediately.
DEFAULT_STARTUP_TICK_FRESH_SECONDS: float = 5.0

# Subscription retry budget on the daemon's first attempt. Exponential
# backoff 1s -> 2s -> 4s -> 8s -> ~16s, total ~31s before declaring failure.
DEFAULT_SUBSCRIPTION_RETRY_ATTEMPTS: int = 5
DEFAULT_SUBSCRIPTION_INITIAL_BACKOFF: float = 1.0
DEFAULT_SUBSCRIPTION_BACKOFF_FACTOR: float = 2.0

# Default symbols to probe when detecting broker offset. The first one that
# returns a populated tick wins. Order: most-likely-visible (FN/FTMO) first.
DEFAULT_OFFSET_PROBE_SYMBOLS: tuple[str, ...] = (
    "EURUSD", "USDJPY", "GBPUSD", "XAUUSD", "GBPJPY", "XAGUSD",
)

# Brokers in practice run whole-hour offsets, but a few run 30-minute offsets
# (Iran, India, parts of Australia for some retail brokers). We round to the
# nearest 1800s so a probe with a few seconds of network jitter still maps
# to the canonical offset.
BROKER_OFFSET_ROUND_SECONDS: int = 1800

# When |computed_offset| < this, treat broker as UTC (offset = 0). This
# prevents tiny network-jitter offsets (< ~60s) from accidentally bumping the
# tick into a "GMT+0.5" bucket when the broker is actually GMT+0.
BROKER_OFFSET_ZERO_THRESHOLD_SECONDS: float = 60.0

# Broker server clocks are real-world timezone offsets, not market-data age.
# A closed CFD/index can return its last Friday quote on Monday startup; using
# that stale tick as a timezone probe produced impossible -48h/-49h offsets and
# would corrupt tick parquet timestamps when the market reopened.
BROKER_OFFSET_MAX_ABS_SECONDS: int = 14 * 3600

# Tolerance for sub-second broker-vs-system clock skew when checking tick
# freshness. The detected offset is rounded to whole seconds (or to the
# nearest BROKER_OFFSET_ROUND_SECONDS bucket), so the broker's true clock
# can sit fractionally ahead of the system clock and produce ticks that
# evaluate to slightly-future ages. Without tolerance, every such tick is
# rejected as stale and the daemon never reaches the capture loop. Live
# fail seen 2026-04-30: NDX100 ticks consistently age=-0.17s on FN UTC+3.
TICK_FRESHNESS_NEG_AGE_TOLERANCE_SECONDS: float = 2.0


# =============================================================================
# Single-instance lock with argv-aware reclaim
# =============================================================================


def _read_lock_pid(lock_path: Path) -> Optional[int]:
    """Return the PID stored in ``lock_path`` or None if missing/malformed.

    Tolerates UTF-8 BOM (PowerShell ``Set-Content -Encoding UTF8`` on Windows
    writes a BOM by default, which historic watchdog runs left in lock files).
    """
    if not lock_path.exists():
        return None
    try:
        raw = lock_path.read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeDecodeError):
        return None
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _is_process_alive(pid: int) -> bool:
    """Return True if a process with ``pid`` is currently running.

    Implementation note: we avoid taking a hard dependency on ``psutil``.
    On POSIX, ``os.kill(pid, 0)`` is idiomatic. On Windows, ``OpenProcess``
    via ctypes is the standard approach. Both paths return False on errors
    (treat as dead — the safe direction for lock reclaim).
    """
    if pid <= 0:
        return False
    if os.name == "nt":
        # Windows path: use OpenProcess via ctypes. PROCESS_QUERY_LIMITED_INFORMATION
        # (0x1000) works for any current process the user can see.
        try:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            handle = kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not handle:
                return False
            # Check if the process has exited via GetExitCodeProcess.
            STILL_ACTIVE = 259
            exit_code = ctypes.c_ulong(0)
            ok = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            kernel32.CloseHandle(handle)
            if not ok:
                return False
            return exit_code.value == STILL_ACTIVE
        except Exception:  # noqa: BLE001 — defensive
            return False
    # POSIX path
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def _find_python_process_by_argv_marker(marker: str) -> Optional[int]:
    """Best-effort scan for a running python process whose command line
    contains ``marker``. Returns the PID or None.

    Used as the second-line check during lock reclaim: if the recorded PID
    is dead but a python process running with our argv is alive, we adopt
    that PID into the lock instead of spawning a duplicate.

    Implementation: prefers ``psutil`` when available; falls back to
    Windows ``wmic`` and POSIX ``ps``. All paths are best-effort -- any
    exception returns None and the caller proceeds as if no match exists
    (which leads to a clean re-launch — safe direction).
    """
    if not marker:
        return None
    try:
        import psutil  # type: ignore[import-not-found]
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if "python" not in name:
                    continue
                cmdline = proc.info.get("cmdline") or []
                joined = " ".join(cmdline)
                if marker in joined:
                    return int(proc.info["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):  # type: ignore[attr-defined]
                continue
        return None
    except ImportError:
        pass

    # Fallback path. We avoid spawning subprocesses on the hot path of every
    # daemon startup; this is reached only when psutil is missing.
    try:
        import subprocess
        if os.name == "nt":
            # wmic is deprecated but ships with Windows 10 + 11 + Server.
            out = subprocess.check_output(
                ["wmic", "process", "where", "name='python.exe'",
                 "get", "processid,commandline", "/format:csv"],
                stderr=subprocess.DEVNULL, timeout=10,
            ).decode("utf-8", errors="replace")
            for line in out.splitlines():
                if marker in line:
                    parts = [p for p in line.strip().split(",") if p]
                    # csv format: Node,CommandLine,ProcessId
                    if len(parts) >= 3:
                        try:
                            return int(parts[-1])
                        except ValueError:
                            continue
            return None
        else:
            out = subprocess.check_output(
                ["ps", "-eo", "pid,command"],
                stderr=subprocess.DEVNULL, timeout=10,
            ).decode("utf-8", errors="replace")
            for line in out.splitlines():
                if marker in line and "python" in line.lower():
                    parts = line.strip().split(None, 1)
                    if parts:
                        try:
                            return int(parts[0])
                        except ValueError:
                            continue
            return None
    except Exception:  # noqa: BLE001
        return None


def _pid_cmdline_contains_marker(pid: int, marker: str) -> Optional[bool]:
    """Return whether ``pid`` has ``marker`` in its command line.

    ``None`` means the command line could not be inspected. Callers should
    treat that as unknown, not as a negative match, so we do not accidentally
    reclaim a lock from a process we could not inspect.
    """
    if pid <= 0 or not marker:
        return None
    try:
        import psutil  # type: ignore[import-not-found]
        proc = psutil.Process(pid)
        cmdline = proc.cmdline()
        return marker in " ".join(cmdline)
    except ImportError:
        pass
    except Exception:  # noqa: BLE001 - best-effort process inspection
        return None

    try:
        import subprocess
        if os.name == "nt":
            out = subprocess.check_output(
                [
                    "wmic", "process", "where", f"ProcessId={pid}",
                    "get", "commandline", "/format:list",
                ],
                stderr=subprocess.DEVNULL, timeout=10,
            ).decode("utf-8", errors="replace")
            return marker in out

        out = subprocess.check_output(
            ["ps", "-p", str(pid), "-o", "command="],
            stderr=subprocess.DEVNULL, timeout=10,
        ).decode("utf-8", errors="replace")
        return marker in out
    except Exception:  # noqa: BLE001
        return None


def acquire_single_instance_lock(
    name: str,
    *,
    lock_dir: Optional[Path] = None,
    own_pid: Optional[int] = None,
    argv_marker: Optional[str] = None,
    is_alive_fn: Callable[[int], bool] = _is_process_alive,
    process_lookup_fn: Callable[[str], Optional[int]] = _find_python_process_by_argv_marker,
    pid_marker_fn: Callable[[int, str], Optional[bool]] = _pid_cmdline_contains_marker,
) -> tuple[bool, Optional[int]]:
    """Atomically acquire a lock named ``name``.

    Returns ``(acquired, conflicting_pid)``.

    - ``acquired=True, conflicting_pid=None`` -- caller may proceed.
    - ``acquired=False, conflicting_pid=N`` -- another live instance owns
      the lock at PID N; caller should exit.

    Behavior:
      1. Read the existing lock-file PID (if any).
      2. If lock-PID == own_pid: idempotent re-acquisition, returns acquired.
      3. If lock-PID is a live process and either no argv marker is provided
         or the command line cannot be inspected: NOT acquired (conservative
         conflict). If the command line can be inspected and does not match
         ``argv_marker``, treat the lock as stale/mis-owned and continue.
      4. If lock-PID is dead AND ``argv_marker`` is provided AND
         ``process_lookup_fn(argv_marker)`` finds a live python process,
         we treat THAT pid as the conflict (the daemon is alive but the
         lock got out of sync — common under the cmd.exe wrapper bug).
         The function rewrites the lock to point at the live PID and
         returns NOT acquired so the caller exits cleanly without
         double-spawning.
      5. Otherwise (dead lock + no live argv match): acquire by writing
         own_pid atomically.

    The atomic write uses ``write+rename`` so a partial write can never
    confuse the next reader.

    Notes on Windows BOM tolerance: ``_read_lock_pid`` strips UTF-8 BOMs
    so legacy locks written by PowerShell's ``Set-Content -Encoding UTF8``
    are still readable.
    """
    base = Path(lock_dir) if lock_dir is not None else LOCK_DIR
    base.mkdir(parents=True, exist_ok=True)
    lock_path = base / f".{name}.lock"

    pid = own_pid if own_pid is not None else os.getpid()

    existing = _read_lock_pid(lock_path)
    if existing is not None:
        if existing == pid:
            # Same process re-entering. Idempotent.
            _atomic_write_pid(lock_path, pid)
            return (True, None)
        if is_alive_fn(existing):
            if argv_marker:
                marker_match = pid_marker_fn(existing, argv_marker)
                if marker_match is False:
                    logger.warning(
                        "Lock %s pointed at live PID %s, but its argv did not "
                        "match marker %r; reclaiming stale/mis-owned lock",
                        name, existing, argv_marker,
                    )
                else:
                    return (False, existing)
            else:
                return (False, existing)
        # Lock-PID is dead or was positively identified as a live but unrelated
        # process. Before reclaiming, check if a sibling is actually alive
        # under a different PID (cmd.exe-wrapper bug).
        if argv_marker:
            adopted = process_lookup_fn(argv_marker)
            if adopted and adopted != pid and is_alive_fn(adopted):
                # Re-sync the lock to the live PID and report conflict.
                _atomic_write_pid(lock_path, adopted)
                return (False, adopted)

    # Either no lock, or lock-PID is dead with no live argv match.
    _atomic_write_pid(lock_path, pid)
    return (True, None)


def _atomic_write_pid(lock_path: Path, pid: int) -> None:
    """Write ``pid`` to ``lock_path`` atomically (write-then-rename).

    On Windows, ``os.replace`` is atomic across the same volume, so a
    partial-write will not be observable by another process.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = lock_path.with_suffix(lock_path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(str(pid) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(lock_path))


def release_single_instance_lock(
    name: str,
    *,
    lock_dir: Optional[Path] = None,
    own_pid: Optional[int] = None,
) -> bool:
    """Best-effort release. Removes the lock file IFF it currently points
    at ``own_pid`` (default: current process). Returns True on removal.

    Never raises. Safe to call from a signal handler / atexit.
    """
    base = Path(lock_dir) if lock_dir is not None else LOCK_DIR
    lock_path = base / f".{name}.lock"
    pid = own_pid if own_pid is not None else os.getpid()
    existing = _read_lock_pid(lock_path)
    if existing != pid:
        # Either missing, or owned by someone else (in which case we MUST
        # NOT delete -- that would unlock another live process's lock).
        return False
    try:
        lock_path.unlink()
        return True
    except OSError:
        return False


# =============================================================================
# MT5 symbol-subscription readiness
# =============================================================================


def _extract_tick_msc(tick_obj: Any) -> Optional[int]:
    """Return the broker-localized millisecond timestamp from ``tick_obj``.

    The tick objects returned by ``mt5.symbol_info_tick()`` expose ``time``
    (seconds) and ``time_msc`` (milliseconds). The mock fixtures used in
    tests can be a dict/namedtuple/custom object; we duck-type all three.

    Returns ``None`` for missing / malformed timestamps. The returned value
    is **broker server time**, not UTC — see ``detect_broker_offset_seconds``.
    """
    if tick_obj is None:
        return None
    ts_msc: Optional[int] = None
    try:
        if hasattr(tick_obj, "__getitem__"):
            try:
                ts_msc = int(tick_obj["time_msc"])
            except (KeyError, IndexError, ValueError, TypeError):
                ts_msc = None
        if ts_msc is None and hasattr(tick_obj, "time_msc"):
            ts_msc = int(getattr(tick_obj, "time_msc"))
        if ts_msc is None and hasattr(tick_obj, "time"):
            ts_msc = int(getattr(tick_obj, "time")) * 1000
        if ts_msc is None and isinstance(tick_obj, dict):
            if "time_msc" in tick_obj:
                ts_msc = int(tick_obj["time_msc"])
            elif "time" in tick_obj:
                ts_msc = int(tick_obj["time"]) * 1000
    except (TypeError, ValueError):
        return None
    if not ts_msc or ts_msc <= 0:
        return None
    return ts_msc


def detect_broker_offset_seconds(
    mt5_module: Any,
    *,
    symbols: Optional[Iterable[str]] = None,
    now_fn: Callable[[], datetime] = lambda: datetime.now(tz=timezone.utc),
    round_seconds: int = BROKER_OFFSET_ROUND_SECONDS,
    zero_threshold_seconds: float = BROKER_OFFSET_ZERO_THRESHOLD_SECONDS,
) -> int:
    """Detect the broker server-time offset relative to true UTC, in seconds.

    Returns the integer **seconds-ahead-of-UTC** the broker reports its tick
    timestamps. Examples:

      - redacted_account-Server 2 (UTC+3): returns ``+10800``.
      - FTMO-Server 3 (UTC+2): returns ``+7200``.
      - GMT broker: returns ``0``.
      - Negative offsets (broker reports timestamps in the past) are
        supported but vanishingly rare in practice.

    Detection algorithm
    -------------------
    1. For each symbol in ``symbols`` (default: a curated list of the most
       commonly-visible FX + metals + indices on FN/FTMO), call
       ``mt5.symbol_info_tick(sym)``.
    2. The first symbol that returns a non-None tick with a valid
       ``time_msc`` wins. Compute ``raw_offset = tick.time - utc_now``.
    3. Round to nearest ``round_seconds`` (default 1800s) so half-hour and
       whole-hour brokers both bucket correctly. Tiny offsets within
       ``zero_threshold_seconds`` (default 60s) are reported as 0.

    Returns 0 (treat as UTC broker) when:
      - No symbol returns a usable tick.
      - The MT5 module lacks ``symbol_info_tick``.
      - The computed offset is within ``zero_threshold_seconds``.

    The function is **detection-only** — it does NOT subscribe symbols or
    mutate state. Safe to call once at daemon startup.

    Cache
    -----
    This helper is intended to be called ONCE per daemon process startup
    (not per tick). The caller stores the returned int and passes it into
    ``_tick_is_fresh`` / ``ensure_mt5_symbol_ready`` for the lifetime of
    the daemon. Brokers do NOT change their server timezone mid-session;
    the only legitimate jump is daylight-saving on a broker that observes
    DST (some FN servers do; FTMO does not). DST-related drift is at most
    3600s and only happens twice a year — re-running on reconnect or every
    24h is acceptable but not required.
    """
    if not hasattr(mt5_module, "symbol_info_tick"):
        return 0

    probe_list: tuple[str, ...]
    if symbols is None:
        probe_list = DEFAULT_OFFSET_PROBE_SYMBOLS
    else:
        probe_list = tuple(symbols) or DEFAULT_OFFSET_PROBE_SYMBOLS

    utc_now = now_fn()
    utc_epoch = utc_now.timestamp()

    last_failure: Optional[str] = None
    for sym in probe_list:
        try:
            tick = mt5_module.symbol_info_tick(sym)
        except Exception as e:  # noqa: BLE001 — defensive
            last_failure = f"{sym}: raised {e!r}"
            continue
        ts_msc = _extract_tick_msc(tick)
        if ts_msc is None:
            last_failure = f"{sym}: no usable timestamp"
            continue
        broker_epoch = ts_msc / 1000.0
        raw_offset = broker_epoch - utc_epoch
        # Round to nearest ``round_seconds`` so 30-min brokers bucket cleanly.
        if round_seconds > 0:
            rounded = round(raw_offset / round_seconds) * round_seconds
        else:
            rounded = int(round(raw_offset))
        if abs(rounded) > BROKER_OFFSET_MAX_ABS_SECONDS:
            last_failure = (
                f"{sym}: implausible broker offset raw={raw_offset:.1f}s "
                f"rounded={int(rounded):+d}s"
            )
            logger.warning(
                "broker offset detection: probe=%s raw=%.1fs rounded=%+ds "
                "exceeds plausible timezone bound (+/-%ds) -- skipping stale "
                "or closed-market quote",
                sym, raw_offset, int(rounded), BROKER_OFFSET_MAX_ABS_SECONDS,
            )
            continue
        if abs(rounded) < zero_threshold_seconds:
            logger.info(
                "broker offset detection: probe=%s raw=%.1fs rounded=0s "
                "(within zero-threshold %.0fs — treating as UTC)",
                sym, raw_offset, zero_threshold_seconds,
            )
            return 0
        logger.info(
            "broker offset detection: probe=%s raw=%.1fs rounded=%+ds "
            "(broker is %+.1fh ahead of UTC)",
            sym, raw_offset, int(rounded), rounded / 3600.0,
        )
        return int(rounded)

    logger.warning(
        "broker offset detection: no probe symbol yielded a usable tick "
        "(last_failure=%s) — defaulting to offset=0 (UTC). The freshness "
        "check may incorrectly reject ticks if the broker is offset.",
        last_failure,
    )
    return 0


def _tick_is_fresh(
    tick_obj: Any,
    *,
    max_age_seconds: float,
    now: Optional[datetime] = None,
    broker_offset_seconds: float = 0.0,
) -> bool:
    """Return True if ``tick_obj`` has a ``time_msc`` (or ``time``) field
    within ``max_age_seconds`` of ``now`` (true UTC).

    ``broker_offset_seconds`` is the broker server-time offset relative to
    UTC (e.g. ``+10800`` for a UTC+3 broker). The tick's broker-localized
    timestamp has this offset SUBTRACTED before comparison so the age math
    is performed in true UTC.

    Live failure mode this fix addresses (2026-04-28 redacted_account)
    -----------------------------------------------------------
    FN runs UTC+3. A live tick at true-UTC ``02:18:04`` arrives with
    ``tick.time_msc`` corresponding to broker-local ``05:18:04``. Without
    offset adjustment, ``age = utc_now - tick_dt = -10800s`` and the check
    rejects every live tick as future-dated. The daemon retries 5x with
    backoff, exits ``stale_tick``, the watchdog respawns it 15min later,
    and the loop never produces a ready signal.

    The tick objects returned by ``mt5.symbol_info_tick()`` expose ``time``
    (seconds) and ``time_msc`` (milliseconds). The mock fixtures used in
    tests can be a dict/namedtuple/custom object; we duck-type all three.
    """
    if tick_obj is None:
        return False
    now_dt = now if now is not None else datetime.now(tz=timezone.utc)
    ts_msc = _extract_tick_msc(tick_obj)
    if ts_msc is None:
        return False
    broker_dt = datetime.fromtimestamp(ts_msc / 1000.0, tz=timezone.utc)
    # Convert broker-localized epoch to true-UTC by subtracting the offset.
    # E.g. broker GMT+3 ts=05:18:04 minus +10800s = UTC 02:18:04.
    tick_dt = broker_dt - _seconds_as_timedelta(broker_offset_seconds)
    age = (now_dt - tick_dt).total_seconds()
    if age < -TICK_FRESHNESS_NEG_AGE_TOLERANCE_SECONDS:
        # Future-dated tick beyond the clock-skew tolerance = malformed
        # (broker clock skew exceeds the known offset, or detection drift).
        # Treat as stale.
        return False
    return age <= max_age_seconds


def _seconds_as_timedelta(seconds: float) -> "timedelta":
    """Helper: float seconds -> timedelta. Module-private convenience.

    Keeps the call site of ``_tick_is_fresh`` readable while still allowing
    sub-second offset values (rare — but possible if a future caller skips
    the rounding step in ``detect_broker_offset_seconds``).
    """
    return timedelta(seconds=seconds)


def ensure_mt5_symbol_ready(
    mt5_module: Any,
    symbol: str,
    *,
    fresh_seconds: float = DEFAULT_STARTUP_TICK_FRESH_SECONDS,
    retry_attempts: int = DEFAULT_SUBSCRIPTION_RETRY_ATTEMPTS,
    initial_backoff: float = DEFAULT_SUBSCRIPTION_INITIAL_BACKOFF,
    backoff_factor: float = DEFAULT_SUBSCRIPTION_BACKOFF_FACTOR,
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], datetime] = lambda: datetime.now(tz=timezone.utc),
    require_fresh_tick: bool = True,
    broker_offset_seconds: float = 0.0,
) -> tuple[bool, str]:
    """Ensure ``symbol`` is subscribed in MT5 Market Watch and the tick
    stream is delivering fresh ticks.

    Returns ``(ready, reason)``. ``reason`` is a short identifier suitable
    for logs / events:

      - ``"ready"``           — symbol is subscribed and a fresh tick arrived.
      - ``"unknown_symbol"``  — ``symbol_info`` returned None (broker doesn't
        expose this name; daemon should exit non-zero).
      - ``"select_failed"``   — ``symbol_select(sym, True)`` returned False
        on every retry (transient broker rejection or bad symbol).
      - ``"stale_tick"``      — symbol is subscribed but ``symbol_info_tick``
        keeps returning stale data (>fresh_seconds old) on every retry. This
        was the live failure mode for FX/metals on 2026-04-28: the daemon
        thought the symbol was OK but the feed never advanced.
      - ``"weekend_or_closed"`` — ``require_fresh_tick=False`` but otherwise
        same as stale; caller decides whether to proceed (e.g., write the
        heartbeat anyway to detect daemon-vs-feed-down separately).

    Why we ALWAYS call ``symbol_select(sym, True)``: empirically (redacted_account
    broker, FX/metals on reconnect) ``symbol_info(sym).visible`` reads True
    even when the tick stream is silent. The original ``tick_capture.main``
    only re-selected when ``visible`` was False, missing this case. Always
    re-selecting is idempotent for already-visible symbols, so this is a
    safe blanket fix.

    ``broker_offset_seconds`` MUST match the broker's server-time offset
    relative to UTC (e.g. ``+10800`` for redacted_account UTC+3). When the offset
    is wrong (e.g. defaulted to 0 against a UTC+3 broker), ``_tick_is_fresh``
    will treat every live tick as 3 hours future-dated and reject it; the
    daemon will exhaust its retry budget and exit ``stale_tick``. Detect the
    offset ONCE per daemon process via ``detect_broker_offset_seconds`` and
    pass the resulting int through here (and through the heartbeat / tick
    capture loop).
    """
    # Defensive: ``mt5_module`` MUST expose the methods we depend on.
    for attr in ("symbol_info", "symbol_select", "symbol_info_tick"):
        if not hasattr(mt5_module, attr):
            return (False, f"missing_mt5_method:{attr}")

    info = mt5_module.symbol_info(symbol)
    if info is None:
        return (False, "unknown_symbol")

    backoff = initial_backoff
    last_reason = "select_failed"
    for attempt in range(1, max(1, retry_attempts) + 1):
        # 1. Force-select the symbol (idempotent if already visible).
        try:
            select_ok = bool(mt5_module.symbol_select(symbol, True))
        except Exception as e:  # noqa: BLE001
            logger.warning("symbol_select(%s) raised: %s", symbol, e)
            select_ok = False

        if not select_ok:
            last_reason = "select_failed"
            logger.warning(
                "[%s] symbol_select failed (attempt %d/%d) -- backing off %.1fs",
                symbol, attempt, retry_attempts, backoff,
            )
            sleep_fn(backoff)
            backoff *= backoff_factor
            continue

        if not require_fresh_tick:
            return (True, "ready")

        # 2. Verify a fresh tick arrives.
        try:
            tick = mt5_module.symbol_info_tick(symbol)
        except Exception as e:  # noqa: BLE001
            logger.warning("symbol_info_tick(%s) raised: %s", symbol, e)
            tick = None

        if _tick_is_fresh(
            tick,
            max_age_seconds=fresh_seconds,
            now=now_fn(),
            broker_offset_seconds=broker_offset_seconds,
        ):
            return (True, "ready")

        last_reason = "stale_tick"
        logger.warning(
            "[%s] subscription appears stuck (no fresh tick within %.1fs) "
            "-- attempt %d/%d, backing off %.1fs",
            symbol, fresh_seconds, attempt, retry_attempts, backoff,
        )
        sleep_fn(backoff)
        backoff *= backoff_factor

    return (False, last_reason)


# =============================================================================
# Daemon heartbeat (own-PID + last-progress timestamp)
# =============================================================================


def write_daemon_heartbeat(
    name: str,
    *,
    heartbeat_dir: Optional[Path] = None,
    last_progress_at: Optional[datetime] = None,
    extra: Optional[dict] = None,
) -> bool:
    """Write a per-daemon heartbeat envelope.

    Path: ``HEARTBEAT_DIR / daemon_heartbeat_{NAME}.json``

    Payload::

        {"utc": "2026-04-28T...", "pid": 1234, "name": "tick_capture_XAUUSD",
         "last_progress_utc": "2026-04-28T..." | null,
         ...extra}

    The ``last_progress_utc`` field is the key signal: even if the daemon
    process is alive (PID-check passes), if ``last_progress_utc`` is older
    than the per-daemon staleness threshold we know the daemon is stuck.

    Best-effort. Never raises. Returns True on successful write.
    """
    base = Path(heartbeat_dir) if heartbeat_dir is not None else HEARTBEAT_DIR
    target = base / f"daemon_heartbeat_{name}.json"
    payload: dict[str, Any] = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        "name": name,
        "last_progress_utc": last_progress_at.isoformat() if last_progress_at else None,
    }
    if extra:
        payload.update(extra)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(str(tmp), str(target))
        return True
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "daemon heartbeat write failed (non-fatal) name=%s target=%s: %s",
            name, target, e,
        )
        return False


# =============================================================================
# Signal handler
# =============================================================================


def install_signal_handlers(stop_callback: Callable[[], None]) -> None:
    """Wire SIGINT and (where present) SIGTERM to ``stop_callback``.

    The callback is responsible for flipping a stop flag the daemon's main
    loop reads. The signal handler MUST NOT raise; if the callback raises
    we swallow and log so the process still exits via the natural shutdown
    path.
    """
    def _handler(signum, frame):  # noqa: ARG001
        try:
            stop_callback()
        except Exception as e:  # noqa: BLE001
            logger.error("stop_callback raised on signal %s: %s", signum, e)

    signal.signal(signal.SIGINT, _handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handler)


# =============================================================================
# CLI helper for ad-hoc lock inspection (operator tool)
# =============================================================================


def _main(argv: Optional[list[str]] = None) -> int:  # pragma: no cover
    """Inspect lock files. Used by operators for triage; not part of the
    core daemon flow."""
    import argparse
    parser = argparse.ArgumentParser(description="MT5 daemon lock inspector")
    parser.add_argument("--list", action="store_true",
                         help="List all daemon lock files and PIDs")
    args = parser.parse_args(argv)
    if args.list:
        for path in sorted(LOCK_DIR.glob(".*.lock")):
            pid = _read_lock_pid(path)
            alive = _is_process_alive(pid) if pid else False
            print(f"{path.name}: pid={pid} alive={alive}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_main())
