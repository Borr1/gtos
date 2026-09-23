"""
Per-symbol No-Data Alert Monitor — T1.7.

Called periodically by watchdog.ps1 (e.g. every 5 min during trading hours).
For each supervised orchestrator symbol, checks whether the per-symbol heartbeat or
live log file has been written to recently. If both are silent longer than
``NO_DATA_THRESHOLD_MINUTES`` **during that symbol's kill-zone hours**,
a Telegram alert is sent. Outside a symbol's kill zones, silence is
expected and the check is skipped.

Gap closed
----------
Canary cache (handoff 23) catches Anthropic API drift.
Between-KZ pending-limit fix (handoff 17) catches pending-order gaps.
Heartbeat-flatten monitor (T1.1, ships DISABLED) catches SILENT orchestrator
crashes on ONE shared ``pipeline_state/heartbeat.json`` — last-writer-wins
across symbols, so a single-symbol crash where the other processes
keep writing the heartbeat file is invisible to it.

This monitor closes the per-symbol branch: if XAUUSD's process wedges
mid-KZ but US30/USDJPY/etc. keep running, the shared heartbeat file is
still being refreshed and the T1.1 monitor never fires, yet the XAUUSD
log file sits stale for the entire kill zone.

Liveness signal — design rationale
----------------------------------
We cannot add a new per-symbol heartbeat file today because that would
require editing ``src/components/orchestrator.py`` (forbidden without
CEO approval — trading-logic file). Candidates considered:

* ``pipeline_state/heartbeat.json``     — shared, last-writer-wins, not
                                          per-symbol. REJECTED.
* ``knowledge_base/meta/.orchestrator_<symbol>.lock`` — written once at
                                          startup; mtime does not refresh.
                                          REJECTED.
* ``knowledge_base/live_sessions/<symbol>/*`` — only written at KZ
                                          transitions. Too infrequent.
                                          REJECTED.
* ``logs/<symbol>.log``                 — stdout/stderr redirect from
                                          ``start_all.bat`` and
                                          ``scripts/watchdog.ps1``; also
                                          receives Python logging via the
                                          orchestrator's StreamHandler.
                                          Refreshed every M15 candle
                                          close, every HTTP request to
                                          Anthropic, every
                                          ``_monitored_sleep`` chunk
                                          boundary (\u2264 60 s during
                                          active KZ processing).
                                          SELECTED.

The orchestrator logs at least once per M15 candle close (\"Processing
candle — <kz> KZ\"), plus the HTTP request line emitted by ``httpx`` on
every Anthropic call. Inside a healthy KZ the log is written every
15 min (natural cadence) or more often.

Threshold
---------
The task specification asks for a 5-minute threshold. The natural M15
cadence during a calm kill-zone is already ~15 minutes between log
writes (no trades triggered → no HTTP requests → only the
\"Processing candle\" line fires at each M15 close), so a 5-minute
threshold would alert on every healthy kill zone.

We therefore use ``NO_DATA_THRESHOLD_MINUTES = 20`` (1.33 \u00d7 M15) as a
documented deviation from the spec's \"5 minutes\". This is larger than
the natural candle cadence but smaller than two missed candles, so the
monitor still flags real feed outages within 20 minutes while avoiding
false positives on normal operation.

Symbol to log-file map
----------------------
Mirrors ``scripts/watchdog.ps1 $SymbolMap`` for the full Stage08
broker-native vNext surface, not the old live launcher.

Kill-zone gating
----------------
Kill-zone windows are imported directly from
``src.safety.heartbeat_monitor.KILL_ZONES_UTC`` to avoid duplication.
Each ``(symbol, (start_h, start_m), (end_h, end_m))`` tuple is a
half-open UTC interval. Outside every KZ window for a given symbol,
this monitor is a no-op for that symbol.

De-dup
------
State file ``knowledge_base/meta/no_data_alert_state.json`` stores
``{symbol: last_alert_utc}``. A fresh alert for a given symbol fires
only if the previous alert for that symbol is older than
``COOLDOWN_MINUTES`` (default 60). When a symbol's log resumes
writing (age < threshold), its entry is cleared so the next outage
alerts immediately.

Exit codes
----------
    0  — all symbols OK, or outside KZ for every symbol, or alert sent
         successfully, or skipped by cooldown.
    1  — alert needed but ``TELEGRAM_BOT_TOKEN``/``TELEGRAM_CHAT_ID``
         not configured.
    2  — Telegram HTTP call failed for at least one symbol.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Import the KZ definitions from the existing heartbeat-flatten monitor so
# kill-zone boundaries remain the single source of truth. Both files are
# read-only consumers of this tuple.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from src.safety.heartbeat_monitor import KILL_ZONES_UTC  # noqa: E402


# ── MODULE-LEVEL paths (monkeypatch in tests, session 21 canon) ──────────

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
LOGS_DIR: Path = PROJECT_ROOT / "logs"
HEARTBEAT_DIR: Path = PROJECT_ROOT / "pipeline_state"
STATE_FILE: Path = PROJECT_ROOT / "knowledge_base" / "meta" / "no_data_alert_state.json"

# Symbol → log filename. Mirrors watchdog.ps1:$SymbolMap.
SYMBOL_LOG_MAP: dict[str, str] = {
    "AUDJPY": "audjpy.log",
    "AUDUSD": "audusd.log",
    "BTCUSD": "btcusd.log",
    "CHFJPY": "chfjpy.log",
    "ETHUSD": "ethusd.log",
    "EURGBP": "eurgbp.log",
    "EURJPY": "eurjpy.log",
    "EURUSD": "eurusd.log",
    "GBPJPY": "gbpjpy.log",
    "GBPUSD": "gbpusd.log",
    "GER40": "ger40.log",
    "JP225": "jp225.log",
    "NAS100": "nas100.log",
    "NZDUSD": "nzdusd.log",
    "SPX500": "spx500.log",
    "UK100": "uk100.log",
    "UKOIL_cash": "ukoil.log",
    "US30_cash": "us30.log",
    "USDCAD": "usdcad.log",
    "USDCHF": "usdchf.log",
    "USDJPY": "usdjpy.log",
    "USOIL_cash": "usoil.log",
    "XAGUSD": "xagusd.log",
    "XAUUSD": "xauusd.log",
}

SYMBOL_HEARTBEAT_MAP: dict[str, str] = {
    "AUDJPY": "heartbeat_AUDJPY.json",
    "AUDUSD": "heartbeat_AUDUSD.json",
    "BTCUSD": "heartbeat_BTCUSD.json",
    "CHFJPY": "heartbeat_CHFJPY.json",
    "ETHUSD": "heartbeat_ETHUSD.json",
    "EURGBP": "heartbeat_EURGBP.json",
    "EURJPY": "heartbeat_EURJPY.json",
    "EURUSD": "heartbeat_EURUSD.json",
    "GBPJPY": "heartbeat_GBPJPY.json",
    "GBPUSD": "heartbeat_GBPUSD.json",
    "GER40": "heartbeat_GER40.json",
    "JP225": "heartbeat_JP225.json",
    "NAS100": "heartbeat_NAS100.json",
    "NZDUSD": "heartbeat_NZDUSD.json",
    "SPX500": "heartbeat_SPX500.json",
    "UK100": "heartbeat_UK100.json",
    "UKOIL_cash": "heartbeat_UKOIL_cash.json",
    "US30_cash": "heartbeat_US30_cash.json",
    "USDCAD": "heartbeat_USDCAD.json",
    "USDCHF": "heartbeat_USDCHF.json",
    "USDJPY": "heartbeat_USDJPY.json",
    "USOIL_cash": "heartbeat_USOIL_cash.json",
    "XAGUSD": "heartbeat_XAGUSD.json",
    "XAUUSD": "heartbeat_XAUUSD.json",
}

# Per-symbol heartbeats are the current primary liveness source. Logs remain a
# fallback for older deployments and for tests without heartbeat fixtures.

# Symbols are keyed to the production orchestrator names used by
# ``KILL_ZONES_UTC`` and ``start_all.bat``.
KZ_SYMBOL_ALIAS: dict[str, str] = {}

NO_DATA_THRESHOLD_MINUTES: int = 20
HEARTBEAT_FRESH_THRESHOLD_MINUTES: int = 5
COOLDOWN_MINUTES: int = 60


# ── Liveness + KZ gating ─────────────────────────────────────────────────


def _now_utc() -> datetime:
    """Indirection so tests can monkeypatch time."""
    return datetime.now(timezone.utc)


def log_age_minutes(log_path: Path, now: Optional[datetime] = None) -> Optional[float]:
    """Return the age of ``log_path`` in minutes, or ``None`` if missing.

    The age is ``now - mtime`` where mtime is the last filesystem write
    time converted to a UTC-aware datetime. We never trust raw MT5
    timestamps here — the file mtime is the OS clock, and ``now`` is
    UTC-aware.
    """
    if not log_path.exists():
        return None
    try:
        mtime_ts = log_path.stat().st_mtime
    except OSError:
        return None
    mtime_dt = datetime.fromtimestamp(mtime_ts, tz=timezone.utc)
    now_dt = now if now is not None else _now_utc()
    age_seconds = (now_dt - mtime_dt).total_seconds()
    # A future-dated file (clock skew after restore, etc.) is treated as
    # fresh — we never want to alert on a future mtime.
    if age_seconds < 0:
        return 0.0
    return age_seconds / 60.0


def heartbeat_age_minutes(
    symbol: str,
    now: Optional[datetime] = None,
) -> Optional[float]:
    """Return per-symbol heartbeat age in minutes, or ``None`` if absent."""
    heartbeat_filename = SYMBOL_HEARTBEAT_MAP.get(symbol)
    if not heartbeat_filename:
        return None
    return log_age_minutes(HEARTBEAT_DIR / heartbeat_filename, now=now)


def kz_active_for_symbol(symbol: str, now: Optional[datetime] = None) -> bool:
    """Return True iff the given symbol has an active kill zone at ``now``.

    Kill zones are imported from ``src.safety.heartbeat_monitor`` and are
    half-open UTC intervals ``[start, end)``. Unknown symbols (those not
    in ``KILL_ZONES_UTC`` after alias resolution) return False — no alert
    fires for instruments that have no configured KZ.
    """
    kz_symbol = KZ_SYMBOL_ALIAS.get(symbol, symbol)
    now_dt = now if now is not None else _now_utc()
    minutes_of_day = now_dt.hour * 60 + now_dt.minute
    for sym, (sh, sm), (eh, em) in KILL_ZONES_UTC:
        if sym != kz_symbol:
            continue
        start = sh * 60 + sm
        end = eh * 60 + em
        if start <= minutes_of_day < end:
            return True
    return False


# ── State / cooldown ─────────────────────────────────────────────────────


def _load_state(path: Optional[Path] = None) -> dict:
    """Load the per-symbol alert-state dict. Returns ``{}`` on any error.

    Shape::

        {"XAUUSD": "2026-04-19T08:12:00+00:00", ...}
    """
    target = path if path is not None else STATE_FILE
    if not target.exists():
        return {}
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _save_state(state: dict, path: Optional[Path] = None) -> None:
    """Persist ``state`` atomically. Best-effort — never raises."""
    target = path if path is not None else STATE_FILE
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        os.replace(tmp, target)
    except OSError:
        pass


def _in_cooldown(
    state: dict,
    symbol: str,
    now: Optional[datetime] = None,
    cooldown_minutes: int = COOLDOWN_MINUTES,
) -> bool:
    """True iff ``symbol`` already alerted within ``cooldown_minutes``."""
    last = state.get(symbol)
    if not last or not isinstance(last, str):
        return False
    try:
        last_ts = datetime.fromisoformat(last)
    except ValueError:
        return False
    if last_ts.tzinfo is None:
        last_ts = last_ts.replace(tzinfo=timezone.utc)
    now_dt = now if now is not None else _now_utc()
    return (now_dt - last_ts) < timedelta(minutes=cooldown_minutes)


# ── Telegram ─────────────────────────────────────────────────────────────


def build_alert_message(symbol: str, age_minutes: float, log_path: Path) -> str:
    return (
        f"GTOS NO-DATA ALERT — {symbol}\n"
        f"No log activity for {age_minutes:.1f} min "
        f"(threshold {NO_DATA_THRESHOLD_MINUTES} min)\n"
        f"Log: {log_path.name}\n"
        f"Symbol is in KZ — check MT5 feed + process liveness."
    )


def send_telegram(token: str, chat_id: str, text: str) -> bool:
    """Send a Telegram message using urllib (stdlib). Returns True on 200.

    Refuses unless this process is authorized to page the operator (F30 / Q7).
    This monitor POSTs directly rather than through the notification queue, so
    it needs its own gate — credential presence is not authorization. See
    ``src/safety/notification_authorization.py``.
    """
    from src.safety.notification_authorization import delivery_authorization

    _auth = delivery_authorization()
    if not _auth.allowed:
        print(
            f"[no_data_alert_monitor] Telegram send REFUSED (unauthorized process): "
            f"{_auth.detail}",
            file=sys.stderr,
        )
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        print(
            f"[no_data_alert_monitor] Telegram HTTP error: {e.code} {e.reason}",
            file=sys.stderr,
        )
        return False
    except Exception as e:  # noqa: BLE001 — monitor must degrade gracefully
        print(f"[no_data_alert_monitor] Telegram send failed: {e}", file=sys.stderr)
        return False


# ── Per-symbol check ─────────────────────────────────────────────────────


def check_symbol(
    symbol: str,
    log_filename: str,
    state: dict,
    now: Optional[datetime] = None,
    threshold_minutes: int = NO_DATA_THRESHOLD_MINUTES,
) -> dict:
    """Evaluate one symbol. Returns a decision dict with keys:

    ``symbol``           — str
    ``status``           — "ok" | "outside_kz" | "no_log" | "stale" |
                           "stale_cooldown"
    ``age_minutes``      — float | None
    ``should_alert``     — bool
    ``should_clear``     — bool
    ``message``          — str | None   (populated iff should_alert)

    This function is pure w.r.t. ``state``: it reads ``state`` but does
    NOT mutate it. The caller decides when to record a fired alert.
    """
    log_path = LOGS_DIR / log_filename
    in_kz = kz_active_for_symbol(symbol, now=now)

    # Outside KZ: silence is expected. If the symbol had a prior alert we
    # still want to clear it once fresh data returns, but only if a log
    # exists and is fresh relative to the threshold (the outage is over).
    age = log_age_minutes(log_path, now=now)
    hb_age = heartbeat_age_minutes(symbol, now=now)
    log_fresh = age is not None and age < threshold_minutes
    heartbeat_fresh = (
        hb_age is not None and hb_age < HEARTBEAT_FRESH_THRESHOLD_MINUTES
    )

    if not in_kz:
        # Clear stale alert state only if data has clearly returned.
        should_clear = symbol in state and (log_fresh or heartbeat_fresh)
        return {
            "symbol": symbol,
            "status": "outside_kz",
            "age_minutes": age,
            "heartbeat_age_minutes": hb_age,
            "liveness_source": "heartbeat" if heartbeat_fresh else "log",
            "should_alert": False,
            "should_clear": should_clear,
            "message": None,
        }

    if heartbeat_fresh:
        return {
            "symbol": symbol,
            "status": "ok",
            "age_minutes": hb_age,
            "log_age_minutes": age,
            "heartbeat_age_minutes": hb_age,
            "liveness_source": "heartbeat",
            "should_alert": False,
            "should_clear": symbol in state,
            "message": None,
        }

    # Inside KZ ───────────────────────────────────────────────────────
    if age is None:
        # Log file does not exist (e.g. process never started). This IS
        # an outage by the monitor's definition — alert unless in
        # cooldown.
        if _in_cooldown(state, symbol, now=now):
            return {
                "symbol": symbol,
                "status": "stale_cooldown",
                "age_minutes": None,
                "heartbeat_age_minutes": hb_age,
                "liveness_source": "none",
                "should_alert": False,
                "should_clear": False,
                "message": None,
            }
        msg = (
            f"GTOS NO-DATA ALERT — {symbol}\n"
            f"Log file missing: {log_filename}\n"
            f"Symbol is in KZ — process may not be running."
        )
        return {
            "symbol": symbol,
            "status": "no_log",
            "age_minutes": None,
            "heartbeat_age_minutes": hb_age,
            "liveness_source": "none",
            "should_alert": True,
            "should_clear": False,
            "message": msg,
        }

    if age < threshold_minutes:
        return {
            "symbol": symbol,
            "status": "ok",
            "age_minutes": age,
            "heartbeat_age_minutes": hb_age,
            "liveness_source": "log",
            "should_alert": False,
            "should_clear": symbol in state,
            "message": None,
        }

    # Stale ───────────────────────────────────────────────────────────
    if _in_cooldown(state, symbol, now=now):
        return {
            "symbol": symbol,
            "status": "stale_cooldown",
            "age_minutes": age,
            "heartbeat_age_minutes": hb_age,
            "liveness_source": "none",
            "should_alert": False,
            "should_clear": False,
            "message": None,
        }

    return {
        "symbol": symbol,
        "status": "stale",
        "age_minutes": age,
        "heartbeat_age_minutes": hb_age,
        "liveness_source": "none",
        "should_alert": True,
        "should_clear": False,
        "message": build_alert_message(symbol, age, log_path),
    }


# ── Main ─────────────────────────────────────────────────────────────────


def main() -> int:
    # Operator notification delivery is default-deny per process (F30 / Q7).
    # This monitor is an operator-facing cron alerter launched by
    # scripts/watchdog.ps1; it takes the grant explicitly at its entrypoint so
    # send_telegram() below can deliver, while an import of this module from a
    # test or another tool stays refused.
    from src.safety.notification_authorization import authorize_operator_delivery
    authorize_operator_delivery(reason="scripts/no_data_alert_monitor.py cron entrypoint")

    now = _now_utc()
    state = _load_state()

    decisions = [
        check_symbol(sym, log_name, state, now=now)
        for sym, log_name in SYMBOL_LOG_MAP.items()
    ]

    alerts_needed = [d for d in decisions if d["should_alert"]]
    clears_needed = [d for d in decisions if d["should_clear"]]

    # Clear returned-to-normal entries first (no side effects on alerts).
    state_mutated = False
    for d in clears_needed:
        if state.pop(d["symbol"], None) is not None:
            state_mutated = True
            print(
                f"[no_data_alert_monitor] {d['symbol']} recovered — "
                f"clearing alert state"
            )

    # Early-exit if nothing to alert on.
    if not alerts_needed:
        if state_mutated:
            _save_state(state)
        return 0

    # We have alerts. Check Telegram credentials.
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        print(
            f"[no_data_alert_monitor] ALERT NEEDED for "
            f"{[d['symbol'] for d in alerts_needed]} but "
            f"TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set — configure in .env",
            file=sys.stderr,
        )
        if state_mutated:
            _save_state(state)
        return 1

    any_telegram_failure = False
    for d in alerts_needed:
        ok = send_telegram(token, chat_id, d["message"])
        if ok:
            state[d["symbol"]] = now.isoformat()
            state_mutated = True
            print(
                f"[no_data_alert_monitor] Alert sent: {d['symbol']} "
                f"age={d['age_minutes']}"
            )
        else:
            any_telegram_failure = True

    if state_mutated:
        _save_state(state)

    return 2 if any_telegram_failure else 0


if __name__ == "__main__":
    sys.exit(main())
