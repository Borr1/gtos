"""D1-bias-lag shadow logger (T5.24) — observation-only.

Detects the failure mode observed on NAS100 week-14 (2026-04-07 → 2026-04-13):
54/54 M15 candles had ``D1 structure.direction == "bearish"`` while price rallied
+4.20% and both H4 and H1 were bullish. The AI refused to issue any longs because
D1 disagreed with the shorter-timeframe direction, producing 0 CANDIDATEs during
the whole rally.

The pattern is instrument-agnostic — it will bite XAUUSD/US30/etc. at the next
regime inflection where D1 structure lags the turn.

What this logger does
---------------------
For every MSO computed by the orchestrator, checks whether:

    d1_bias != h1_direction  AND  d1_bias != h4_bias

If both shorter timeframes agree against D1, append a JSONL record and
maintain a per-symbol rolling consecutive-count counter. When the counter
crosses the configured threshold (default 20 = ~5h of M15 candles on a live
stream), fire a single Telegram alert per crossing (debounced until the streak
breaks).

If H4 is ``unavailable`` (or missing ``structure.direction`` entirely), the
condition collapses to ``d1_bias != h1_direction`` alone and the record is
tagged ``h4_missing: true``.

Strictly log-only:
    - No trade is gated or modified.
    - Every call is wrapped so failures never propagate into the pipeline.
    - The orchestrator caller should still wrap in try/except as belt-and-suspenders.

Storage
-------
- JSONL: ``shadow_logs/d1_bias_lag.jsonl`` (one line per logged candle)
- State: ``shadow_logs/.d1_bias_lag_state.json`` (per-symbol counters +
  last-alert-threshold, UTC-date tagged so we reset daily)
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # pragma: no cover - exercised on Windows in production
    import msvcrt
except ImportError:  # pragma: no cover - non-Windows test/dev fallback
    msvcrt = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Module-level constants — tests override via module-ref monkeypatch
# (per MEMORY.md `project_pytest_contamination_forensics`).
SHADOW_LOG_PATH = Path("shadow_logs/d1_bias_lag.jsonl")
STATE_PATH = Path("shadow_logs/.d1_bias_lag_state.json")

# Directional structure values. Anything else (transitional, insufficient_data,
# unavailable, None, ...) is treated as non-directional and does not trigger.
_DIRECTIONAL = frozenset({"bullish", "bearish"})


# ── Helpers ─────────────────────────────────────────────────────────────────


def _tf_direction(mso: Any, tf_name: str) -> str | None:
    """Extract ``mso.timeframes[tf_name].structure.direction`` defensively.

    Returns ``None`` when the timeframe is absent, the structure is missing, or
    the direction attribute cannot be fetched.
    """
    try:
        tfs = getattr(mso, "timeframes", None)
        if tfs is None:
            return None
        try:
            tf = tfs.get(tf_name)
        except AttributeError:
            tf = tfs[tf_name] if tf_name in tfs else None  # type: ignore[operator]
        if tf is None:
            return None
        structure = getattr(tf, "structure", None)
        if structure is None:
            return None
        direction = getattr(structure, "direction", None)
        if direction is None:
            return None
        return str(direction)
    except Exception:
        return None


def _load_state(path: Path | None = None) -> dict:
    target = path if path is not None else STATE_PATH
    try:
        if not target.exists():
            return {}
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return data
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _save_state(state: dict, path: Path | None = None) -> None:
    target = path if path is not None else STATE_PATH
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, target)
    except OSError as exc:
        logger.warning("d1_bias_lag: state save failed (%s)", exc)


def _append_jsonl(record: dict, path: Path | None = None) -> None:
    target = path if path is not None else SHADOW_LOG_PATH
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        row = json.dumps(record, separators=(",", ":")) + "\n"
        lock_path = target.with_suffix(target.suffix + ".lock")
        with open(lock_path, "a+b") as lock_f:
            locked = False
            if msvcrt is not None:
                for _ in range(10):
                    try:
                        lock_f.seek(0)
                        msvcrt.locking(lock_f.fileno(), msvcrt.LK_NBLCK, 1)
                        locked = True
                        break
                    except OSError:
                        time.sleep(0.02)
                if not locked:
                    logger.warning("d1_bias_lag: log lock busy; skipped shadow row")
                    return
            try:
                with open(target, "a", encoding="utf-8", newline="") as f:
                    f.write(row)
                    f.flush()
                    os.fsync(f.fileno())
            finally:
                if msvcrt is not None and locked:
                    try:
                        lock_f.seek(0)
                        msvcrt.locking(lock_f.fileno(), msvcrt.LK_UNLCK, 1)
                    except OSError as exc:
                        logger.warning("d1_bias_lag: log unlock failed (%s)", exc)
    except OSError as exc:
        logger.warning("d1_bias_lag: log write failed (%s)", exc)


def _utc_date(iso_timestamp: str | None) -> str:
    """Return the UTC date (YYYY-MM-DD) for an ISO timestamp, or today's.

    Accepts both naive and tz-aware ISO strings. Anything unparseable falls
    back to the process's current UTC date — the counter reset happens at UTC
    midnight regardless of candle ingestion clock skew.
    """
    if iso_timestamp:
        try:
            ts = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts.astimezone(timezone.utc).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _send_threshold_alert(record: dict) -> bool:
    """Fire a Telegram alert via src.notifications.notify_alert.

    Lazy import so a misconfigured Telegram env cannot kill the logger at
    module load. Returns True on success, False on any failure (non-blocking).
    """
    try:
        from src.notifications import notify_alert
    except Exception as exc:  # noqa: BLE001
        logger.warning("d1_bias_lag: notify_alert import failed (%s)", exc)
        return False

    try:
        text = (
            f"GTOS D1-BIAS LAG — {record.get('symbol', '?')}\n"
            f"Consecutive candles with D1 contradicting H1+H4: "
            f"{record.get('rolling_N_consecutive', '?')}\n"
            f"D1={record.get('d1_bias')}  H4={record.get('h4_bias')}  "
            f"H1={record.get('h1_direction')}\n"
            f"Kill zone: {record.get('kill_zone', '-')}  "
            f"H4_missing: {record.get('h4_missing', False)}\n"
            f"Pattern produced 0 CANDIDATEs on NAS100 W14 during +4.20% rally.\n"
            f"Log-only — no position impact."
        )
        notify_alert(text)
        return True
    except Exception as exc:  # noqa: BLE001 — additive monitor must degrade
        logger.warning("d1_bias_lag: notify_alert failed (%s)", exc)
        return False


# ── Public API ──────────────────────────────────────────────────────────────


def log_if_d1_bias_lag(
    mso: Any,
    symbol: str,
    timestamp_utc: str,
    *,
    kill_zone: str = "",
    alert_threshold_consecutive: int = 20,
    log_path: Path | None = None,
    state_path: Path | None = None,
    send_alert: bool = True,
) -> dict | None:
    """Log when D1 bias contradicts both H1 and H4 directional consensus.

    Parameters
    ----------
    mso:
        Market State Object; must expose ``timeframes`` indexed by "D1"/"H4"/"H1"
        with ``.structure.direction`` attributes.
    symbol:
        Instrument symbol (e.g. "XAUUSD", "NAS100"). Counters are per-symbol.
    timestamp_utc:
        ISO-8601 UTC timestamp of the M15 candle. Used for the log record and
        for UTC-date-based counter reset.
    kill_zone:
        Optional kill-zone tag (london/ny/tokyo/-). Included in the record.
    alert_threshold_consecutive:
        Trigger a one-shot Telegram alert when the rolling consecutive count
        crosses this threshold (default 20 ≈ 5h of M15).
    log_path, state_path:
        Test-only overrides for the JSONL/state paths.
    send_alert:
        Set False in tests that don't want the real notifier to fire.

    Returns
    -------
    dict | None
        The logged record when the condition triggers, else None.

    Trigger
    -------
    ``d1 != h1  AND  d1 != h4``  (both shorter TFs agree against D1).
    ``d1``, ``h1``, ``h4`` must be directional ("bullish"/"bearish"). If
    ``h4`` is non-directional/missing, the condition collapses to
    ``d1 != h1`` alone and the record gets ``h4_missing=true``.

    Counter reset
    -------------
    - Reset on any candle where the condition does NOT trigger.
    - Reset on UTC-date rollover (a new UTC day starts the count from zero
      regardless of prior state).

    Debouncing
    ----------
    A new Telegram alert fires the first candle whose rolling count ``>=``
    threshold, and stays silent for subsequent candles in the same streak.
    On reset the debounce clears, so the next crossing will alert again.
    """
    # Defensive wrapping on everything — this function must never raise into
    # the trading pipeline.
    try:
        d1 = _tf_direction(mso, "D1")
        h4 = _tf_direction(mso, "H4")
        h1 = _tf_direction(mso, "H1")

        # D1 and H1 must both be directional for the condition to be meaningful.
        if d1 not in _DIRECTIONAL or h1 not in _DIRECTIONAL:
            _reset_streak(symbol, state_path=state_path)
            return None

        # H4 handling: directional → strict 3-way comparison;
        # non-directional/None → collapse to d1 != h1 with h4_missing=True.
        if h4 in _DIRECTIONAL:
            h4_missing = False
            triggers = (d1 != h1) and (d1 != h4)
        else:
            h4_missing = True
            triggers = d1 != h1

        if not triggers:
            _reset_streak(symbol, state_path=state_path)
            return None

        # Condition holds — increment counter, honour UTC-day reset, build record.
        today = _utc_date(timestamp_utc)
        state = _load_state(path=state_path)
        sym_state = state.get(symbol)
        if not isinstance(sym_state, dict):
            sym_state = {}

        if sym_state.get("date") != today:
            # New UTC day — reset streak + last-alert-threshold.
            consecutive = 1
            last_alert_threshold = 0
        else:
            consecutive = int(sym_state.get("consecutive", 0)) + 1
            last_alert_threshold = int(sym_state.get("last_alert_threshold", 0))

        record = {
            "timestamp": timestamp_utc,
            "symbol": symbol,
            "d1_bias": d1,
            "h4_bias": h4,
            "h1_direction": h1,
            "kill_zone": kill_zone or "-",
            "h4_missing": h4_missing,
            "rolling_N_consecutive": consecutive,
        }

        _append_jsonl(record, path=log_path)

        # Alert crossing logic:
        # - Fire once per streak when count first reaches the threshold.
        # - Fire again if the count crosses a fresh multiple (e.g. 20, 40, 60)
        #   so a very long streak gets periodic escalations without spamming
        #   every candle past threshold.
        new_alert_threshold = last_alert_threshold
        if alert_threshold_consecutive > 0:
            # Largest multiple of the threshold that the count has reached.
            crossed_multiple = (consecutive // alert_threshold_consecutive) * alert_threshold_consecutive
            if crossed_multiple >= alert_threshold_consecutive and crossed_multiple > last_alert_threshold:
                if send_alert:
                    _send_threshold_alert(record)
                new_alert_threshold = crossed_multiple
                logger.info(
                    "d1_bias_lag: threshold crossed — symbol=%s consecutive=%d threshold=%d",
                    symbol, consecutive, alert_threshold_consecutive,
                )

        state[symbol] = {
            "date": today,
            "consecutive": consecutive,
            "last_alert_threshold": new_alert_threshold,
        }
        _save_state(state, path=state_path)

        logger.debug(
            "d1_bias_lag: LOGGED symbol=%s d1=%s h4=%s h1=%s consec=%d",
            symbol, d1, h4, h1, consecutive,
        )
        return record

    except Exception as exc:  # noqa: BLE001 — logger must never break pipeline
        logger.warning("d1_bias_lag: unexpected failure (%s)", exc, exc_info=True)
        return None


def _reset_streak(symbol: str, *, state_path: Path | None = None) -> None:
    """Reset a symbol's streak + alert-threshold state. Called when condition
    fails. Only writes state if the symbol currently has a non-zero streak —
    avoids thrashing the state file on every clean candle.
    """
    try:
        state = _load_state(path=state_path)
        sym_state = state.get(symbol)
        if not isinstance(sym_state, dict):
            return
        if int(sym_state.get("consecutive", 0)) == 0 and int(sym_state.get("last_alert_threshold", 0)) == 0:
            # Already clean — nothing to write.
            return
        state[symbol] = {
            "date": sym_state.get("date", _utc_date(None)),
            "consecutive": 0,
            "last_alert_threshold": 0,
        }
        _save_state(state, path=state_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("d1_bias_lag: streak reset failed (%s)", exc)
