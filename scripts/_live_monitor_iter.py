"""GTOS Live Monitor — Iteration script.

Run by the live-monitor agent each M15 candle close (+30s grace).
Reads production state read-only and emits structured findings.

Outputs:
  - shadow_logs/live_monitor.jsonl       (one line per iteration)
  - shadow_logs/live_monitor_alerts.jsonl (one line per CRITICAL/ANOMALY)
  - pipeline_state/_monitor_iteration.json (own state, prefixed _monitor_)

Constraints:
  - READ-ONLY on production state (heartbeats, session_state, dormant_state).
  - No MT5 calls except mt5.positions_get() if MT5 module available.
  - No Anthropic API calls.
  - Iteration must complete in <60 seconds.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
PIPELINE = ROOT / "pipeline_state"
SHADOW = ROOT / "shadow_logs"
EVAL = ROOT / "knowledge_base" / "live_evaluations"
SESSIONS = ROOT / "knowledge_base" / "live_sessions"
NOTRADES = ROOT / "knowledge_base" / "no_trades"
CONFIG_PATH = ROOT / "config" / "agent_config.yaml"

FALLBACK_INSTRUMENTS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]

# Fallback KZ schedules (UTC). Tuples of (start_min, end_min). Crossing
# midnight is handled by in_kz/kz_elapsed_s. Runtime normally derives this
# from agent_config.yaml to keep monitor coverage aligned with production.
FALLBACK_KZ_SCHEDULE: dict[str, dict[str, tuple[int, int]]] = {
    "AUDJPY": {"tokyo": (0, 3 * 60), "london": (7 * 60, 9 * 60 + 30), "ny": (13 * 60, 15 * 60 + 30)},
    "AUDUSD": {"tokyo": (0, 3 * 60), "london": (7 * 60, 12 * 60), "ny": (13 * 60, 15 * 60 + 30)},
    "BTCUSD": {"off_configured_session": (0, 23 * 60 + 59)},
    "CHFJPY": {"tokyo": (0, 3 * 60), "london": (7 * 60, 9 * 60 + 30), "ny": (13 * 60, 15 * 60 + 30)},
    "ETHUSD": {"off_configured_session": (0, 23 * 60 + 59)},
    "EURGBP": {"london": (7 * 60, 12 * 60), "ny": (13 * 60, 15 * 60 + 30)},
    "EURJPY": {"tokyo": (0, 3 * 60), "london": (7 * 60, 9 * 60 + 30), "ny": (13 * 60, 15 * 60 + 30)},
    "EURUSD": {"london": (7 * 60, 12 * 60), "ny": (13 * 60, 15 * 60 + 30)},
    "GBPJPY": {"tokyo": (0, 3 * 60), "london": (7 * 60, 9 * 60 + 30), "ny": (13 * 60, 15 * 60 + 30)},
    "GBPUSD": {"london": (7 * 60, 12 * 60), "ny": (13 * 60, 15 * 60 + 30)},
    "GER40": {"london": (8 * 60, 12 * 60), "ny": (14 * 60, 19 * 60)},
    "JP225": {"tokyo": (0, 3 * 60), "london": (7 * 60, 9 * 60 + 30), "ny": (13 * 60, 15 * 60 + 30)},
    "NAS100": {"ny": (13 * 60, 17 * 60)},
    "NZDUSD": {"tokyo": (0, 3 * 60), "london": (7 * 60, 12 * 60), "ny": (13 * 60, 15 * 60 + 30)},
    "SPX500": {"ny": (13 * 60, 17 * 60)},
    "UK100": {"london": (7 * 60, 10 * 60 + 30), "ny": (13 * 60, 15 * 60 + 30)},
    "UKOIL_cash": {"london": (7 * 60, 12 * 60), "ny": (13 * 60, 17 * 60)},
    "US30_cash": {"london": (8 * 60, 10 * 60 + 30), "ny": (13 * 60 + 30, 16 * 60)},
    "USDCAD": {"london": (7 * 60, 12 * 60), "ny": (13 * 60, 15 * 60 + 30)},
    "USDCHF": {"london": (7 * 60, 12 * 60), "ny": (13 * 60, 15 * 60 + 30)},
    "USDJPY": {"tokyo": (0, 3 * 60), "london": (7 * 60, 9 * 60 + 30), "ny": (13 * 60, 15 * 60 + 30)},
    "USOIL_cash": {"london": (7 * 60, 12 * 60), "ny": (13 * 60, 17 * 60)},
    "XAGUSD": {"london": (7 * 60, 10 * 60 + 30), "ny": (13 * 60, 17 * 60)},
    "XAUUSD": {"london": (7 * 60, 10 * 60 + 30), "ny": (13 * 60, 17 * 60)},
}


def _load_yaml_config(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _hhmm_to_minutes(value: Any) -> int:
    hour_s, minute_s = str(value).split(":", 1)
    return int(hour_s) * 60 + int(minute_s)


def load_monitor_universe(config_path: Path = CONFIG_PATH) -> list[str]:
    config = _load_yaml_config(config_path)
    runtime = config.get("gtos_vnext_runtime") if isinstance(config, dict) else {}
    instruments = config.get("instruments") if isinstance(config, dict) else {}
    if not isinstance(runtime, dict) or not isinstance(instruments, dict):
        return list(FALLBACK_INSTRUMENTS)

    eligible = runtime.get("moonshot_dynamic_execution_router_broker_native_eligible_symbols")
    excluded = set(runtime.get("moonshot_dynamic_execution_router_broker_native_exact_excluded_symbols") or [])
    if not isinstance(eligible, list) or not eligible:
        return list(FALLBACK_INSTRUMENTS)

    out: list[str] = []
    for symbol in eligible:
        symbol_s = str(symbol)
        block = instruments.get(symbol_s)
        if symbol_s in excluded or not isinstance(block, dict):
            continue
        market = block.get("market") if isinstance(block.get("market"), dict) else {}
        if block.get("trading_enabled") is True and isinstance(market.get("kill_zones"), dict):
            out.append(symbol_s)
    return out or list(FALLBACK_INSTRUMENTS)


def load_kz_schedule(
    config_path: Path = CONFIG_PATH,
    instruments: list[str] | None = None,
) -> dict[str, dict[str, tuple[int, int]]]:
    config = _load_yaml_config(config_path)
    blocks = config.get("instruments") if isinstance(config, dict) else {}
    symbols = instruments or load_monitor_universe(config_path)
    if not isinstance(blocks, dict):
        return {symbol: dict(FALLBACK_KZ_SCHEDULE.get(symbol, {})) for symbol in symbols}

    schedule: dict[str, dict[str, tuple[int, int]]] = {}
    for symbol in symbols:
        block = blocks.get(symbol)
        market = block.get("market") if isinstance(block, dict) and isinstance(block.get("market"), dict) else {}
        kill_zones = market.get("kill_zones") if isinstance(market, dict) else None
        if not isinstance(kill_zones, dict):
            schedule[symbol] = dict(FALLBACK_KZ_SCHEDULE.get(symbol, {}))
            continue
        rows: dict[str, tuple[int, int]] = {}
        for name, window in kill_zones.items():
            if not isinstance(window, dict):
                continue
            try:
                rows[str(name)] = (_hhmm_to_minutes(window["start_utc"]), _hhmm_to_minutes(window["end_utc"]))
            except Exception:
                continue
        schedule[symbol] = rows or dict(FALLBACK_KZ_SCHEDULE.get(symbol, {}))
    return schedule


INSTRUMENTS = load_monitor_universe()
TICK_CAPTURE_DAEMONS = [f"tick_capture_{symbol}" for symbol in INSTRUMENTS]
TICK_CAPTURE_PROGRESS_MAX_STALE_S = 600
STRATEGY_FOLLOW_ACTIVE_KZ_MAX_STALE_S = 1800
STRATEGY_FOLLOW_KZ_START_GRACE_S = 1200

KZ_SCHEDULE: dict[str, dict[str, tuple[int, int]]] = load_kz_schedule(instruments=INSTRUMENTS)

STOP_FLAG = PIPELINE / "stop_live_monitor.flag"
MONITOR_STATE = PIPELINE / "_monitor_iteration.json"
MONITOR_LOG = SHADOW / "live_monitor.jsonl"
MONITOR_ALERTS = SHADOW / "live_monitor_alerts.jsonl"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def file_age_s(path: Path) -> float | None:
    try:
        return time.time() - path.stat().st_mtime
    except FileNotFoundError:
        return None


def daemon_progress_age_s(name: str) -> float | None:
    path = PIPELINE / f"daemon_heartbeat_{name}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        stamp = data.get("last_progress_utc") or data.get("utc")
        if not stamp:
            return None
        dt = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (now_utc() - dt.astimezone(timezone.utc)).total_seconds()
    except Exception:
        return None


def candle_close_for_now(now: datetime) -> datetime:
    """Return UTC timestamp of the most recent M15 candle close."""
    minute = (now.minute // 15) * 15
    return now.replace(minute=minute, second=0, microsecond=0)


def in_kz(symbol: str, ts: datetime) -> tuple[bool, str | None]:
    minute_of_day = ts.hour * 60 + ts.minute
    for name, (start, end) in KZ_SCHEDULE.get(symbol, {}).items():
        # Handle midnight crossing (none currently but defensive)
        if start <= end:
            if start <= minute_of_day < end:
                return True, name
        else:  # cross midnight
            if minute_of_day >= start or minute_of_day < end:
                return True, name
    return False, None


def kz_elapsed_s(symbol: str, ts: datetime) -> float | None:
    """Return seconds elapsed since the active KZ start, or None outside KZ."""
    minute_of_day = ts.hour * 60 + ts.minute
    for _name, (start, end) in KZ_SCHEDULE.get(symbol, {}).items():
        if start <= end:
            if start <= minute_of_day < end:
                return float((minute_of_day - start) * 60 + ts.second)
        else:
            if minute_of_day >= start:
                return float((minute_of_day - start) * 60 + ts.second)
            if minute_of_day < end:
                return float(((24 * 60 - start) + minute_of_day) * 60 + ts.second)
    return None


def load_jsonl_tail(path: Path, n: int) -> list[dict]:
    """Return last n parsed JSON lines from a JSONL file. Skip malformed."""
    if not path.exists():
        return []
    try:
        with open(path, "rb") as f:
            try:
                f.seek(-min(8192 * n, path.stat().st_size), os.SEEK_END)
            except OSError:
                f.seek(0)
            data = f.read().decode("utf-8", errors="replace")
    except Exception:
        return []
    lines = [l for l in data.split("\n") if l.strip()]
    out: list[dict] = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def count_jsonl_in_window(path: Path, since_iso: str, predicate) -> int:
    if not path.exists():
        return 0
    cnt = 0
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = entry.get("timestamp_utc") or entry.get("timestamp") or ""
                if ts >= since_iso and predicate(entry):
                    cnt += 1
    except Exception:
        pass
    return cnt


def get_prev_iter() -> int:
    if MONITOR_STATE.exists():
        try:
            return json.load(open(MONITOR_STATE))["iter"]
        except Exception:
            return 0
    return 0


def save_iter_state(n: int, started_at: str) -> None:
    MONITOR_STATE.write_text(json.dumps({
        "iter": n,
        "last_run_utc": now_utc().isoformat(),
        "started_at": started_at,
    }))


def write_record(record: dict) -> None:
    MONITOR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(MONITOR_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def write_alert(alert: dict) -> None:
    MONITOR_ALERTS.parent.mkdir(parents=True, exist_ok=True)
    with open(MONITOR_ALERTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert, default=str) + "\n")


def get_open_positions() -> int | None:
    """Try to query MT5 positions_get(). Return None if MT5 not available."""
    try:
        import MetaTrader5 as mt5  # type: ignore
        if not mt5.initialize():
            return None
        try:
            ps = mt5.positions_get()
            return 0 if ps is None else len(ps)
        finally:
            mt5.shutdown()
    except Exception:
        return None


def main(args: list[str]) -> int:
    if STOP_FLAG.exists():
        # Final summary
        prev_iter = get_prev_iter()
        record = {
            "candle_close_utc": now_utc().isoformat(),
            "monitor_iter": prev_iter,
            "checks_run_at": now_utc().isoformat(),
            "summary": {"stop_flag_observed": True, "exiting": True},
            "per_instrument": {},
            "shadow_logs": {},
            "global_alerts": ["stop_flag_observed"],
        }
        write_record(record)
        print("STOP_FLAG_OBSERVED")
        return 99  # Special exit to signal stop

    started_at_arg = args[1] if len(args) > 1 else now_utc().isoformat()
    iter_n = get_prev_iter() + 1
    save_iter_state(iter_n, started_at_arg)

    now = now_utc()
    candle = candle_close_for_now(now)
    today_str = now.strftime("%Y-%m-%d")

    # Hour-window for L2 reject anomaly
    one_hour_ago = (now - timedelta(hours=1)).isoformat()

    # === Heartbeat checks ===
    per_instrument: dict[str, Any] = {}
    crit = 0
    anom = 0
    alerts_to_emit: list[dict] = []

    for sym in INSTRUMENTS:
        hb_path = PIPELINE / f"heartbeat_{sym}.json"
        age = file_age_s(hb_path)
        in_kz_now, kz_name = in_kz(sym, candle)

        # Eval log
        eval_path = EVAL / sym / f"{today_str}.jsonl"
        eval_tail = load_jsonl_tail(eval_path, 5)
        last_eval_candle = eval_tail[-1].get("candle_time") if eval_tail else None

        # Was the candle evaluated? Look for a row in eval_tail that matches candle hour:min
        candle_hhmm = candle.strftime("%Y-%m-%dT%H:%M")
        evaluated = any(e.get("candle_time", "").startswith(candle_hhmm) for e in eval_tail)
        latest_decision = eval_tail[-1].get("decision") if eval_tail else None
        latest_no_trade_reason = eval_tail[-1].get("no_trade_reason") if eval_tail else None

        # L2 sl_beyond_ob rejections in past hour for this instrument
        l2_path = SHADOW / "sl_beyond_ob_decisions.jsonl"
        rejects_h = count_jsonl_in_window(
            l2_path, one_hour_ago,
            lambda e, s=sym: e.get("symbol") == s and e.get("l2_decision") == "REJECT"
        )

        # Heartbeat status
        issues: list[str] = []
        if age is None and in_kz_now:
            issues.append("hb_missing")
            crit += 1
            alerts_to_emit.append({
                "ts_utc": now.isoformat(),
                "candle": candle.isoformat(),
                "severity": "CRITICAL",
                "instrument": sym,
                "issue": "heartbeat_missing",
                "evidence": str(hb_path),
                "suggested_action": "Verify orchestrator process for symbol is alive",
            })
        elif age is None:
            issues.append("hb_missing_outside_kz")
        else:
            # Threshold: <60s during trading; <300s in inter-KZ; CRITICAL >600s in trading
            if in_kz_now and age > 600:
                issues.append("hb_stale_in_kz_critical")
                crit += 1
                alerts_to_emit.append({
                    "ts_utc": now.isoformat(),
                    "candle": candle.isoformat(),
                    "severity": "CRITICAL",
                    "instrument": sym,
                    "issue": f"heartbeat_stale_in_kz_age_s={age:.0f}",
                    "evidence": str(hb_path),
                    "suggested_action": "Restart orchestrator; check Hypothesis F (computer sleep)",
                })
            elif in_kz_now and age > 60:
                issues.append("hb_stale_in_kz")
                anom += 1
            elif not in_kz_now and age > 300:
                issues.append("hb_stale_inter_kz")

        # L2 reject anomaly per CEO threshold (>3 in 1h per instrument)
        if rejects_h > 3:
            issues.append(f"l2_reject_anomaly_{rejects_h}h")
            anom += 1
            alerts_to_emit.append({
                "ts_utc": now.isoformat(),
                "candle": candle.isoformat(),
                "severity": "ANOMALY",
                "instrument": sym,
                "issue": f"L2_sl_beyond_ob_rejects_in_1h={rejects_h}",
                "evidence": str(l2_path),
                "suggested_action": "Likely AI sl_buffer_applied=0.0 or tight-FX precision; review FA-2 status",
            })

        per_instrument[sym] = {
            "hb_age_s": round(age, 1) if age is not None else None,
            "in_kz": in_kz_now,
            "kz_name": kz_name,
            "eval_today_count": _line_count(eval_path),
            "last_eval_candle": last_eval_candle,
            "evaluated_this_candle": evaluated,
            "latest_decision": latest_decision,
            "latest_no_trade_reason": latest_no_trade_reason,
            "l2_rejects_last_hour": rejects_h,
            "issues": issues,
        }

    # === Shadow log freshness ===
    any_active_kz = any(p.get("in_kz") for p in per_instrument.values())
    active_kz_symbols = [
        sym for sym, payload in per_instrument.items() if payload.get("in_kz")
    ]
    active_kz_elapsed = {
        sym: kz_elapsed_s(sym, candle)
        for sym in active_kz_symbols
    }
    strategy_follow_grace_active = (
        any_active_kz
        and not any(
            elapsed is not None and elapsed >= STRATEGY_FOLLOW_KZ_START_GRACE_S
            for elapsed in active_kz_elapsed.values()
        )
    )
    shadow_status = {}
    for fname, expected_interval_s in [
        ("sl_beyond_ob_decisions.jsonl", 900),
        ("proximity_shadow_log.jsonl", 900),
        ("regime_classifications.jsonl", 900),
        ("displacement_events.jsonl", 900),
        ("candidate_features_log.jsonl", 900),
        ("strategy_follow_evaluations.jsonl", 900),
        ("strategy_follow_candidates.jsonl", 3600),
        ("v2b_forward_pairs.jsonl", 3600),
        ("prefill_delivery_path.jsonl", 3600),
        ("fvg_ob_confluence.jsonl", 3600),
        ("context_control_ledger.jsonl", 3600),
        ("shadow_observer_status.jsonl", 3600),
        ("candidate_path_follow.jsonl", 3600),
        ("live_mechanical_strategy_shadow_outcomes.jsonl", 3600),
        ("pending_limit_lifecycle_join_backfill.jsonl", 3600),
        ("live_structural_strategy_metadata.jsonl", 3600),
        ("v2b_forward_pair_resolutions.jsonl", 3600),
        ("prefill_delivery_path_resolutions.jsonl", 3600),
        ("fvg_ob_confluence_resolutions.jsonl", 3600),
        ("missed_opportunity_shadow.jsonl", 3600),
        ("candidate_ltf_path_order.jsonl", 3600),
        ("databento_live_trigger_decisions.jsonl", 3600),
        ("sierra_confluence_source_status.jsonl", 3600),
        ("live_candidate_strategy_rollups.jsonl", 3600),
        ("account_truth_reconciliation_status.jsonl", 3600),
        ("proxy_blocker_status.jsonl", 3600),
        ("ml_shadow_status.jsonl", 3600),
        ("external_source_blocker_status.jsonl", 3600),
        ("shadow_observer_tick_enrichment.jsonl", 3600),
        ("d1_bias_lag_recovery.jsonl", 86400),
        ("databento_live_confluence.jsonl", 3600),
        ("pending_limit_lifecycle.jsonl", 3600),
        ("heartbeat_flatten_events.jsonl", 60),
    ]:
        p = SHADOW / fname
        age = file_age_s(p)
        # Schema spot-check on last 3
        tail = load_jsonl_tail(p, 3)
        schema_ok = all(isinstance(t, dict) for t in tail) if tail else True
        shadow_status[fname] = {
            "age_s": round(age, 1) if age is not None else None,
            "tail_lines": len(tail),
            "schema_ok": schema_ok,
        }
        if (
            fname == "strategy_follow_evaluations.jsonl"
            and any_active_kz
            and not strategy_follow_grace_active
            and (age is None or age > STRATEGY_FOLLOW_ACTIVE_KZ_MAX_STALE_S)
        ):
            crit += 1
            stale_label = "missing" if age is None else f"age_s={age:.0f}"
            shadow_status[fname]["freshness_issue"] = "stale_during_active_kz"
            alerts_to_emit.append({
                "ts_utc": now.isoformat(),
                "candle": candle.isoformat(),
                "severity": "CRITICAL",
                "instrument": "ALL",
                "issue": f"strategy_follow_evaluations_stale_during_active_kz_{stale_label}",
                "evidence": str(p),
                "suggested_action": (
                    "Production heartbeats may be alive while MSO/evaluation "
                    f"capture is stalled. Active KZ symbols={active_kz_symbols}; "
                    "inspect orchestrator logs for Data incomplete and restart stale processes."
                ),
            })
        elif fname == "strategy_follow_evaluations.jsonl" and strategy_follow_grace_active:
            shadow_status[fname]["freshness_grace"] = {
                "reason": "kz_start_grace_before_first_full_m15_evaluation",
                "active_kz_symbols": active_kz_symbols,
                "active_kz_elapsed_s": active_kz_elapsed,
                "grace_s": STRATEGY_FOLLOW_KZ_START_GRACE_S,
            }

    daemon_status = {}
    for daemon_name in TICK_CAPTURE_DAEMONS:
        age = daemon_progress_age_s(daemon_name)
        status = "OK"
        if age is None:
            status = "MISSING_PROGRESS"
        elif age > TICK_CAPTURE_PROGRESS_MAX_STALE_S:
            status = "STALE_PROGRESS"
        daemon_status[daemon_name] = {
            "progress_age_s": round(age, 1) if age is not None else None,
            "status": status,
        }
        if any_active_kz and status != "OK":
            anom += 1
            alerts_to_emit.append({
                "ts_utc": now.isoformat(),
                "candle": candle.isoformat(),
                "severity": "ANOMALY",
                "instrument": daemon_name.replace("tick_capture_", ""),
                "issue": f"{daemon_name}_{status.lower()}",
                "evidence": str(PIPELINE / f"daemon_heartbeat_{daemon_name}.json"),
                "suggested_action": "Run watchdog; tick-capture PID-only health can miss stale MT5 tick streams.",
            })

    # === Global checks ===
    global_alerts = []
    dormant = PIPELINE / "dormant_state.json"
    dormant_present = dormant.exists()
    dormant_data = None
    if dormant_present:
        try:
            dormant_data = json.load(open(dormant))
        except Exception:
            dormant_data = {"unreadable": True}
        # Bug #25 from CLAUDE.md: equity_at_trigger=0.0 is a transient false positive
        eq = (dormant_data or {}).get("equity_at_trigger") if isinstance(dormant_data, dict) else None
        if eq == 0.0:
            global_alerts.append("dormant_state_present_BUG25_equity_zero_transient_BLOCKING_ALL_TRADING")
            # Any instrument in KZ now means dormant is actively blocking trades
            any_in_kz = any(p.get("in_kz") for p in per_instrument.values())
            if any_in_kz:
                crit += 1
                alerts_to_emit.append({
                    "ts_utc": now.isoformat(),
                    "candle": candle.isoformat(),
                    "severity": "CRITICAL",
                    "instrument": "ALL",
                    "issue": "BUG_25_dormant_state_BLOCKING_active_KZ_trading",
                    "evidence": f"dormant_state.json equity=0.0 triggered={dormant_data.get('triggered_at_utc')}; orchestrators short-circuit at SKIP_DORMANT",
                    "suggested_action": "Verify real equity via MT5; if healthy, delete pipeline_state/dormant_state.json to resume trading",
                })
        else:
            global_alerts.append("dormant_state_present_REAL_daily_loss_stop")
            crit += 1
            alerts_to_emit.append({
                "ts_utc": now.isoformat(),
                "candle": candle.isoformat(),
                "severity": "CRITICAL",
                "instrument": (dormant_data or {}).get("symbol"),
                "issue": "daily_loss_stop_TRIGGERED_REAL",
                "evidence": str(dormant),
                "suggested_action": "Review trades + verify if real loss; if Bug #25 (equity=0), expect transient",
            })

    # Open positions
    open_pos = get_open_positions()

    # Process count check: only count heartbeats with age <120s (alive orchestrators)
    # Heartbeats from ended/dead orchestrators retain stale pid; treat stale as dead.
    pids_alive = set()
    pids_stale = []
    for sym in INSTRUMENTS:
        hb = PIPELINE / f"heartbeat_{sym}.json"
        try:
            d = json.load(open(hb))
            age = file_age_s(hb) or 999999
            if age < 120 and d.get("pid"):
                pids_alive.add(d["pid"])
            elif d.get("pid"):
                pids_stale.append((sym, d["pid"], int(age)))
        except Exception:
            pass
    orchestrator_count = len(pids_alive)
    # Expected alive count is active KZ only. Orchestrators shut down cleanly
    # immediately after processing the end-boundary candle.
    expected_alive = sum(1 for sym in INSTRUMENTS if in_kz(sym, candle)[0])
    if orchestrator_count < expected_alive:
        crit += 1
        alerts_to_emit.append({
            "ts_utc": now.isoformat(),
            "candle": candle.isoformat(),
            "severity": "CRITICAL",
            "instrument": "ALL",
            "issue": f"orchestrator_count_alive={orchestrator_count} (expected_alive={expected_alive}); stale={pids_stale}",
            "evidence": "heartbeat pids + freshness",
            "suggested_action": "Identify which orchestrators died unexpectedly and restart if needed",
        })

    record = {
        "candle_close_utc": candle.isoformat(),
        "monitor_iter": iter_n,
        "checks_run_at": now.isoformat(),
        "summary": {
            "orchestrators_alive": orchestrator_count,
            "anomalies": anom,
            "criticals": crit,
            "open_positions": open_pos,
            "dormant_present": dormant_present,
            "dormant_data": dormant_data,
        },
        "per_instrument": per_instrument,
        "shadow_logs": shadow_status,
        "daemon_progress": daemon_status,
        "global_alerts": global_alerts,
    }
    write_record(record)
    for a in alerts_to_emit:
        write_alert(a)

    # Print summary line
    print(f"iter={iter_n} candle={candle.isoformat()} crit={crit} anom={anom} pids={orchestrator_count} open_pos={open_pos}")
    return 0


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
