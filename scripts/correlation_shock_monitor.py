#!/usr/bin/env python3
"""Correlation-shock Telegram alert (T1.6).

Daily sentinel that watches the rolling-50 Pearson correlation between every
pair of instruments inside each ``portfolio_risk.DEFAULT_CORRELATION_GROUPS``
group on M15 returns. When the current rolling-50 rho deviates from its own
recent baseline (mean of the prior ``BASELINE_WINDOW`` rolling-50 windows)
by more than ``SIGMA_THRESHOLD`` baseline-standard-deviations, a Telegram
alert fires. Alert-only — never touches trade decisions or sizing.

Source: Quantlabs Q004a (cold-review split from full DCC-GARCH; alert-only
half). Mechanism per master-backlog spec:
  "Rolling Pearson >2σ move vs 50-candle baseline across JPY_CROSSES /
   USD_BLOC. Telegram-only alert, NO position impact."

Group-list deviation
--------------------
Spec says "JPY_CROSSES / USD_BLOC". The ``portfolio_risk.py`` defaults have
no group called ``USD_BLOC``; the closest is ``EUR_GBP`` (EURUSD + GBPUSD).
We therefore iterate over EVERY group in
``portfolio_risk.DEFAULT_CORRELATION_GROUPS`` rather than hard-coding two
group names — this satisfies the spec's "reuse existing
``portfolio_risk.py`` correlation groups" requirement and degrades
gracefully on instruments the broker does not serve (skipped silently).

Cadence
-------
Run once per UTC day from ``scripts/watchdog.ps1`` (same shape as the OB
continuation and CUSUM monitors). Per-pair cooldown stored in
``knowledge_base/meta/correlation_shock_state.json`` suppresses repeat
alerts for ``COOLDOWN_HOURS`` after a fired alarm on the same pair.

Exit codes
----------
    0 — all pairs OK (or no usable data, or skipped by cooldown)
    1 — one or more pairs alarmed (Telegram dispatched best-effort)
    2 — unexpected error (caller can retry next watchdog tick)
"""

from __future__ import annotations

import json
import logging
import math
import os
import statistics
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Optional

# Project root on sys.path so we can import portfolio_risk + notifications.
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(PROJECT_ROOT / ".env", override=True)

from src.components.portfolio_risk import DEFAULT_CORRELATION_GROUPS  # noqa: E402

logger = logging.getLogger(__name__)


# ── MODULE-LEVEL paths / knobs (monkeypatch in tests, session 21 canon) ──

STATE_FILE: Path = PROJECT_ROOT / "knowledge_base" / "meta" / "correlation_shock_state.json"

# Rolling-50 Pearson + baseline of prior windows. Total candles needed per
# instrument = ROLLING_WINDOW + BASELINE_WINDOW + 1 returns + 1 close.
ROLLING_WINDOW: int = 50
BASELINE_WINDOW: int = 200
SIGMA_THRESHOLD: float = 2.0
MIN_BASELINE_SAMPLES: int = 30  # require at least N rolling windows for σ
COOLDOWN_HOURS: float = 24.0

# Bars to request from MT5. Need ROLLING_WINDOW closes for the current rho,
# plus BASELINE_WINDOW additional closes shifted back to populate the
# baseline series. Add a small head-room for skipped/aligned bars.
M15_LOOKBACK_CANDLES: int = ROLLING_WINDOW + BASELINE_WINDOW + 50

# Broker symbol overrides — the keys in DEFAULT_CORRELATION_GROUPS are the
# canonical names used by ``permissions.py``; FTMO-style brokers serve a
# different alias for one of them. Mirrors the mapping in
# ``scripts/sweep_divergence_monitor.py:MT5_SYMBOLS``.
BROKER_SYMBOL_ALIAS: dict[str, str] = {
    "NAS100": "NDX100",
    "US30_cash": "US30.cash",
    "US30": "US30.cash",
    "US500": "US500.cash",
    "US500_cash": "US500.cash",
    "SPX500": "US500.cash",
}

# MT5 M15 timeframe constant (mirrors src/components/data_ingestion.py).
TF_M15: int = 15


# ── Math ─────────────────────────────────────────────────────────────────


def _log_returns(closes: list[float]) -> list[float]:
    """Convert a close series to a log-return series of length len(closes) - 1."""
    out: list[float] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        cur = closes[i]
        if prev <= 0 or cur <= 0:
            return []
        out.append(math.log(cur / prev))
    return out


def pearson(xs: list[float], ys: list[float]) -> Optional[float]:
    """Population Pearson correlation. Returns None on degenerate input."""
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = sum((x - mean_x) ** 2 for x in xs)
    den_y = sum((y - mean_y) ** 2 for y in ys)
    den = (den_x * den_y) ** 0.5
    if den == 0.0:
        return None
    return num / den


def rolling_pearson_series(
    rx: list[float],
    ry: list[float],
    window: int = ROLLING_WINDOW,
) -> list[float]:
    """Return a list of rolling Pearson values, length ``len(rx) - window + 1``.

    Degenerate windows (zero variance on either side) contribute NaN-equivalent
    skips: we drop them. Caller treats the survivors as the time series.
    """
    n = min(len(rx), len(ry))
    if n < window:
        return []
    out: list[float] = []
    for end in range(window, n + 1):
        start = end - window
        rho = pearson(rx[start:end], ry[start:end])
        if rho is None:
            continue
        out.append(rho)
    return out


def evaluate_pair(
    rx: list[float],
    ry: list[float],
    *,
    rolling_window: int = ROLLING_WINDOW,
    baseline_window: int = BASELINE_WINDOW,
    sigma_threshold: float = SIGMA_THRESHOLD,
    min_baseline_samples: int = MIN_BASELINE_SAMPLES,
) -> dict:
    """Evaluate a single (rx, ry) return pair. Pure function, no IO.

    Returns::

        {
          "status": "alarm" | "ok" | "insufficient",
          "rho_now": float | None,
          "baseline_mean": float | None,
          "baseline_std": float | None,
          "z": float | None,
          "n_baseline": int,
          "reason": str,
        }
    """
    rho_series = rolling_pearson_series(rx, ry, window=rolling_window)
    if len(rho_series) < (min_baseline_samples + 1):
        return {
            "status": "insufficient",
            "rho_now": None,
            "baseline_mean": None,
            "baseline_std": None,
            "z": None,
            "n_baseline": max(0, len(rho_series) - 1),
            "reason": (
                f"only {len(rho_series)} rolling windows; need "
                f"{min_baseline_samples + 1}"
            ),
        }

    rho_now = rho_series[-1]
    baseline = rho_series[-(baseline_window + 1):-1] if len(rho_series) > baseline_window \
        else rho_series[:-1]
    if len(baseline) < min_baseline_samples:
        return {
            "status": "insufficient",
            "rho_now": rho_now,
            "baseline_mean": None,
            "baseline_std": None,
            "z": None,
            "n_baseline": len(baseline),
            "reason": f"baseline {len(baseline)} < {min_baseline_samples}",
        }

    mu = statistics.fmean(baseline)
    sigma = statistics.pstdev(baseline)
    if sigma == 0.0:
        return {
            "status": "insufficient",
            "rho_now": rho_now,
            "baseline_mean": mu,
            "baseline_std": 0.0,
            "z": None,
            "n_baseline": len(baseline),
            "reason": "baseline_std=0 (constant correlation)",
        }

    z = (rho_now - mu) / sigma
    status = "alarm" if abs(z) > sigma_threshold else "ok"
    return {
        "status": status,
        "rho_now": rho_now,
        "baseline_mean": mu,
        "baseline_std": sigma,
        "z": z,
        "n_baseline": len(baseline),
        "reason": "" if status == "ok" else f"|z|={abs(z):.2f} > {sigma_threshold}",
    }


# ── Pair enumeration ─────────────────────────────────────────────────────


def enumerate_pairs(groups: dict | None = None) -> list[tuple[str, str, str]]:
    """Yield ``(group_name, sym_a, sym_b)`` for every unordered pair in every
    group. Stable order so the test suite can assert on it.
    """
    src = groups if groups is not None else DEFAULT_CORRELATION_GROUPS
    out: list[tuple[str, str, str]] = []
    for group_name in sorted(src.keys()):
        instruments = src[group_name].get("instruments", [])
        for a, b in combinations(instruments, 2):
            out.append((group_name, a, b))
    return out


def broker_symbol(canonical: str) -> str:
    """Translate a permissions/portfolio_risk symbol to the broker alias."""
    return BROKER_SYMBOL_ALIAS.get(canonical, canonical)


# ── State / cooldown ─────────────────────────────────────────────────────


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _pair_key(group: str, a: str, b: str) -> str:
    """Stable key for the per-pair cooldown map (a/b alphabetical)."""
    lo, hi = sorted((a, b))
    return f"{group}|{lo}|{hi}"


def _load_state(path: Optional[Path] = None) -> dict:
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
    target = path if path is not None else STATE_FILE
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, target)
    except OSError as exc:
        logger.warning("correlation_shock: state save failed (%s)", exc)


def _in_cooldown(
    state: dict,
    pair_key: str,
    *,
    now: Optional[datetime] = None,
    cooldown_hours: float = COOLDOWN_HOURS,
) -> bool:
    last = state.get(pair_key)
    if not last or not isinstance(last, str):
        return False
    try:
        last_ts = datetime.fromisoformat(last)
    except ValueError:
        return False
    if last_ts.tzinfo is None:
        last_ts = last_ts.replace(tzinfo=timezone.utc)
    now_dt = now if now is not None else _now_utc()
    elapsed_hours = (now_dt - last_ts).total_seconds() / 3600.0
    return elapsed_hours < cooldown_hours


# ── Telegram ─────────────────────────────────────────────────────────────


def build_alert_message(group: str, sym_a: str, sym_b: str, eval_dict: dict) -> str:
    rho_now = eval_dict.get("rho_now")
    mu = eval_dict.get("baseline_mean")
    sigma = eval_dict.get("baseline_std")
    z = eval_dict.get("z")
    n = eval_dict.get("n_baseline")
    return (
        f"GTOS CORRELATION SHOCK — {group}\n"
        f"Pair: {sym_a} \u2194 {sym_b}\n"
        f"Rolling-50 \u03c1: {rho_now:+.3f}\n"
        f"Baseline (n={n}): \u03bc={mu:+.3f}  \u03c3={sigma:.3f}\n"
        f"z-score: {z:+.2f}  (threshold |z|>{SIGMA_THRESHOLD})\n"
        f"Alert-only — no position impact."
    )


def _emit_alert(text: str) -> bool:
    """Send via src.notifications.notify_alert. Returns False on any error.

    Lazy import keeps a misconfigured notifier from killing the monitor at
    module load (matches the model_pin._emit_drift_alert pattern).
    """
    try:
        from src.notifications import notify_alert
        notify_alert(text)
        return True
    except Exception as exc:  # noqa: BLE001 — additive monitor must degrade
        logger.warning("correlation_shock: notify_alert failed (%s)", exc)
        return False


# ── MT5 fetch (real entry point — overridable in tests) ──────────────────


def ensure_symbols_subscribed(mt5_facade, symbols: list[str]) -> dict[str, bool]:
    """Force-subscribe the given symbols in MT5 Market Watch (Issue #17).

    EURJPY is in ``JPY_CROSSES`` but is not directly traded by any
    orchestrator, so it may be absent from MT5 Market Watch on the live
    terminal. ``mt5.copy_rates_from_pos`` returns an empty/short series for
    unsubscribed symbols on some broker terminals — the symptom that
    triggered Issue #17 (EURJPY M15 bars only up to 00:30 UTC at 14:30 UTC).

    Calls ``mt5.symbol_select(broker_symbol(s), True)`` for each requested
    symbol via the raw MT5 module exposed by the wrapper. Failures are
    logged + skipped silently — out-of-our-control if the broker doesn't
    serve the symbol at all.

    Returns a dict ``{symbol: ok}`` for diagnostics; the caller does NOT
    have to fail on a False result (we still attempt the candle fetch and
    log no_data downstream).
    """
    out: dict[str, bool] = {}
    raw = getattr(mt5_facade, "_mt5", None)
    if raw is None:
        # Wrapper without raw access (mock/test path) — treat as no-op
        # success so tests that monkeypatch ``fetch_closes`` don't need to
        # also stub this out.
        for sym in symbols:
            out[sym] = True
        return out
    for sym in symbols:
        broker_sym = broker_symbol(sym)
        try:
            ok = bool(raw.symbol_select(broker_sym, True))
        except Exception as exc:  # noqa: BLE001 — sentinel must not crash
            logger.warning(
                "correlation_shock: symbol_select(%s) raised %s — skipping",
                broker_sym, exc,
            )
            ok = False
        out[sym] = ok
        if not ok:
            logger.warning(
                "correlation_shock: symbol_select(%s) returned False — "
                "feed may be unavailable on this broker terminal", broker_sym,
            )
    return out


def fetch_closes(symbol: str, count: int = M15_LOOKBACK_CANDLES) -> list[float]:
    """Fetch the most recent M15 closes for ``symbol``. Returns [] on failure.

    Wraps the project's MT5 facade so tests can monkeypatch this at module
    level without spinning up MetaTrader5.
    """
    try:
        from src.mt5 import create_mt5  # local import: heavy, optional dep
    except Exception as exc:  # noqa: BLE001
        logger.warning("correlation_shock: cannot import MT5 (%s)", exc)
        return []
    try:
        mt5 = create_mt5(mode="live")
        if not mt5.connect():
            logger.warning("correlation_shock: MT5 connect failed")
            return []
        candles = mt5.get_candles(broker_symbol(symbol), TF_M15, count)
    except Exception as exc:  # noqa: BLE001
        logger.warning("correlation_shock: get_candles(%s) raised %s", symbol, exc)
        return []
    if not candles:
        return []
    out: list[float] = []
    for c in candles:
        try:
            out.append(float(c["close"]))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _all_group_symbols() -> list[str]:
    """Return the deduplicated, sorted list of symbols across all groups."""
    found: set[str] = set()
    for group_cfg in DEFAULT_CORRELATION_GROUPS.values():
        for sym in group_cfg.get("instruments", []):
            found.add(sym)
    return sorted(found)


def _subscribe_all_group_symbols() -> dict[str, bool]:
    """Open the MT5 facade once on startup and force-subscribe every symbol
    listed in ``DEFAULT_CORRELATION_GROUPS``. Returns the subscription map for
    diagnostics + tests. Errors degrade silently so monitor still runs.
    """
    try:
        from src.mt5 import create_mt5  # local import — heavy
    except Exception as exc:  # noqa: BLE001
        logger.warning("correlation_shock: cannot import MT5 for subscribe (%s)", exc)
        return {}
    try:
        mt5 = create_mt5(mode="live")
        if not mt5.connect():
            logger.warning(
                "correlation_shock: MT5 connect failed during symbol-subscribe"
            )
            return {}
        return ensure_symbols_subscribed(mt5, _all_group_symbols())
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "correlation_shock: unexpected error during symbol-subscribe (%s)",
            exc,
        )
        return {}


# ── Per-pair check ───────────────────────────────────────────────────────


def check_pair(
    group: str,
    sym_a: str,
    sym_b: str,
    state: dict,
    *,
    now: Optional[datetime] = None,
    fetch=fetch_closes,
) -> dict:
    """Evaluate one (group, sym_a, sym_b). Pure w.r.t. ``state`` (read-only).

    Returns::

        {
          "group": str, "a": str, "b": str,
          "status": "alarm" | "ok" | "insufficient" | "no_data" |
                    "alarm_cooldown",
          "evaluation": dict | None,
          "should_alert": bool,
          "message": str | None,
        }
    """
    closes_a = fetch(sym_a)
    closes_b = fetch(sym_b)
    if not closes_a or not closes_b:
        return {
            "group": group, "a": sym_a, "b": sym_b,
            "status": "no_data", "evaluation": None,
            "should_alert": False, "message": None,
        }

    # Align lengths from the right (most recent candles).
    n = min(len(closes_a), len(closes_b))
    rx = _log_returns(closes_a[-n:])
    ry = _log_returns(closes_b[-n:])
    if not rx or not ry:
        return {
            "group": group, "a": sym_a, "b": sym_b,
            "status": "no_data", "evaluation": None,
            "should_alert": False, "message": None,
        }

    ev = evaluate_pair(rx, ry)
    if ev["status"] != "alarm":
        return {
            "group": group, "a": sym_a, "b": sym_b,
            "status": ev["status"], "evaluation": ev,
            "should_alert": False, "message": None,
        }

    pair_key = _pair_key(group, sym_a, sym_b)
    if _in_cooldown(state, pair_key, now=now):
        return {
            "group": group, "a": sym_a, "b": sym_b,
            "status": "alarm_cooldown", "evaluation": ev,
            "should_alert": False, "message": None,
        }

    return {
        "group": group, "a": sym_a, "b": sym_b,
        "status": "alarm", "evaluation": ev,
        "should_alert": True,
        "message": build_alert_message(group, sym_a, sym_b, ev),
    }


# ── Main ─────────────────────────────────────────────────────────────────


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    try:
        now = _now_utc()
        state = _load_state()
        # Issue #17 (2026-04-28): force-subscribe every symbol in the
        # correlation groups before the first fetch. EURJPY (in JPY_CROSSES)
        # is not directly traded by any orchestrator and may be absent from
        # MT5 Market Watch; without symbol_select(EURJPY, True) the
        # ``copy_rates_*`` queries return short/empty series. Lookup table
        # is sourced from DEFAULT_CORRELATION_GROUPS; a bypass for tests
        # is wired via the module-dict lookup pattern (matches fetch_closes).
        subscribe = globals().get(
            "_subscribe_all_group_symbols", _subscribe_all_group_symbols,
        )
        try:
            sub_map = subscribe()
            if sub_map:
                ok_count = sum(1 for v in sub_map.values() if v)
                logger.info(
                    "correlation_shock: subscribed %d/%d symbols via "
                    "symbol_select",
                    ok_count, len(sub_map),
                )
        except Exception as exc:  # noqa: BLE001 — additive, never blocks
            logger.warning(
                "correlation_shock: symbol-subscribe step failed (%s) — "
                "continuing with default Market Watch state", exc,
            )
        # Look up the fetch callable from the module dict at call time so
        # tests can monkeypatch ``mod.fetch_closes`` and have main() see
        # the patched value (default-arg binding would freeze the original).
        fetch = globals().get("fetch_closes", fetch_closes)
        decisions = [
            check_pair(grp, a, b, state, now=now, fetch=fetch)
            for grp, a, b in enumerate_pairs()
        ]

        alarms = [d for d in decisions if d["should_alert"]]
        for d in decisions:
            ev = d.get("evaluation") or {}
            logger.info(
                "[%s] %s\u2194%s status=%s rho=%s z=%s",
                d["group"], d["a"], d["b"], d["status"],
                None if ev.get("rho_now") is None else f"{ev['rho_now']:+.3f}",
                None if ev.get("z") is None else f"{ev['z']:+.2f}",
            )

        if not alarms:
            return 0

        any_dispatched = False
        for d in alarms:
            ok = _emit_alert(d["message"])
            if ok:
                any_dispatched = True
                state[_pair_key(d["group"], d["a"], d["b"])] = now.isoformat()
                logger.warning(
                    "correlation_shock: alarm %s %s\u2194%s z=%+.2f",
                    d["group"], d["a"], d["b"], d["evaluation"]["z"],
                )
        if any_dispatched:
            _save_state(state)
        return 1
    except Exception as exc:  # noqa: BLE001
        logger.exception("correlation_shock: unexpected error: %s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
