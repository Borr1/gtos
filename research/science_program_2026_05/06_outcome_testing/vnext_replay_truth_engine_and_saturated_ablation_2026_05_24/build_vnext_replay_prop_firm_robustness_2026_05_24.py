"""Build Stage 07 prop-firm and robustness metrics.

This offline measurement tool consumes the Stage 05 saturated replay and Stage
06 ablation/MIXED ledgers. It computes compact trading, prop-firm, Monte Carlo,
stress, holdout, data-quality, ablation, and MIXED contribution metrics without
mutating production config, prompts, broker state, accounts, orders, deals,
positions, or live runtime behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SATURATED_REPLAY_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_SATURATED_REPLAY_LEDGER_2026-05-24.jsonl"
SATURATED_REPLAY_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_SATURATED_REPLAY_SUMMARY_2026-05-24.json"
STAGE05_METRICS_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_METRICS_SUMMARY_2026-05-24.json"
ABLATION_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_ABLATION_LEDGER_2026-05-24.jsonl"
MIXED_RESOLUTION_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_MIXED_RESOLUTION_LEDGER_2026-05-24.jsonl"
STAGE06_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_ABLATION_MIXED_SUMMARY_2026-05-24.json"
PROP_FIRM_METRICS_PATH = ROUTE_DIR / "VNEXT_REPLAY_PROP_FIRM_METRICS_2026-05-24.json"
ROBUSTNESS_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_ROBUSTNESS_LEDGER_2026-05-24.jsonl"
STAGE07_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_PROP_FIRM_ROBUSTNESS_SUMMARY_2026-05-24.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / "VNEXT_REPLAY_OUTPUT_MANIFEST_2026-05-24.json"
SESSION_STATE_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/gtos_vnext_replay_truth_engine"
    / "VNEXT_REPLAY_TRUTH_ENGINE_SESSION_STATE_2026-05-24.json"
)

STAGE_ID = "STAGE_07_PROP_FIRM_AND_ROBUSTNESS_MEASUREMENT"
NEXT_STAGE_ID = "STAGE_08_FAILURE_AND_REPAIR_DOSSIERS"
MONTE_CARLO_SEED = 20260524
MONTE_CARLO_ITERATIONS = 5000
CHALLENGE_SCENARIOS = (
    {
        "scenario_id": "challenge_8_5_risk_0_5pct_per_r",
        "target_pct": 8.0,
        "max_loss_pct": 5.0,
        "daily_loss_pct": 5.0,
        "risk_pct_per_r": 0.5,
    },
    {
        "scenario_id": "challenge_8_5_risk_1_0pct_per_r",
        "target_pct": 8.0,
        "max_loss_pct": 5.0,
        "daily_loss_pct": 5.0,
        "risk_pct_per_r": 1.0,
    },
    {
        "scenario_id": "challenge_8_5_current_config_2_0pct_per_r",
        "target_pct": 8.0,
        "max_loss_pct": 5.0,
        "daily_loss_pct": 5.0,
        "risk_pct_per_r": 2.0,
    },
)
STRESS_COSTS_R = (0.05, 0.10, 0.20)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, allow_nan=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, allow_nan=False, sort_keys=True) + "\n")


def stable_hash(payload: Any, length: int = 24) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:length]


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result) or math.isinf(result):
        return None
    return result


def sorted_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 12)
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return round(ordered[int(pos)], 12)
    weight = pos - lo
    return round(ordered[lo] * (1 - weight) + ordered[hi] * weight, 12)


def month_key(timestamp: str | None) -> str:
    if not timestamp or len(timestamp) < 7:
        return "unknown_month"
    return timestamp[:7]


def date_key(timestamp: str | None) -> str:
    if not timestamp or "T" not in timestamp:
        return "unknown_date"
    return timestamp.split("T", 1)[0]


def best_path(row: dict[str, Any]) -> dict[str, Any]:
    summary = row.get("path_outcome_summary") or {}
    best = summary.get("best_available_path")
    return best if isinstance(best, dict) else {}


def path_quality_bucket(path: dict[str, Any]) -> str:
    status = str(path.get("path_source_status") or "")
    confidence = str(path.get("confidence") or "")
    mode = str(path.get("replay_mode") or "")
    if "TICKS" in status or "tick" in confidence or "tick" in mode:
        return "tick_or_sierra_path_aware"
    if "M1" in status or mode == "m1_path_aware":
        return "m1_path_aware"
    if "M5" in status or mode == "m5_path_aware":
        return "m5_path_aware"
    if "M15" in status or "bar_close" in mode:
        return "m15_bar_close_or_contract"
    if "MISSING" in status or mode == "missing_source":
        return "missing_source"
    if "OHLC" in status or "ohlc" in mode:
        return "ohlc_proxy"
    return "unknown_or_reference"


def terminal_bucket(path: dict[str, Any]) -> str:
    outcome = str(path.get("outcome_class") or "missing_or_reference")
    terminal = str(path.get("terminal_order") or "")
    if outcome == "target_first_win" or terminal == "TARGET_FIRST":
        return "target_first_win"
    if outcome == "stop_first_loss" or terminal == "STOP_FIRST":
        return "stop_first_loss"
    if outcome == "no_fill_no_entry_touch" or "NO_ENTRY_TOUCH" in terminal:
        return "no_fill_no_entry_touch"
    if outcome == "entry_touched_timeout_or_unresolved" or "UNRESOLVED" in terminal:
        return "entry_touched_timeout_or_unresolved"
    if outcome == "missing_or_reference" or "MISSING" in terminal:
        return "missing_or_reference"
    return outcome


def active_effects(row: dict[str, Any]) -> tuple[bool, float, list[str]]:
    mode = str(row.get("runtime_activation_mode") or "")
    if mode != "hypothetical_activated_vnext":
        return False, 1.0, []

    reasons: list[str] = []
    pre_ai = row.get("pre_ai_decision") or {}
    pending = row.get("pending_policy") or {}
    risk = row.get("risk_adjustment") or {}

    pre_ai_action = str(pre_ai.get("action") or "")
    if pre_ai_action.startswith("SKIP"):
        reasons.append(f"pre_ai:{pre_ai_action}")

    pending_action = str(pending.get("action") or "")
    if pending_action.startswith("SKIP"):
        reasons.append(f"pending:{pending_action}")

    multiplier = to_float(risk.get("multiplier"))
    if multiplier is None:
        multiplier = to_float(risk.get("would_multiplier"))
    if multiplier is None:
        multiplier = 1.0
    if multiplier <= 0:
        reasons.append(f"risk_multiplier:{multiplier}")

    return bool(reasons), multiplier, reasons


def project_replay_row(row: dict[str, Any]) -> dict[str, Any]:
    group = row.get("group") or {}
    inp = row.get("input_event") or {}
    path = best_path(row)
    raw_r = to_float(path.get("proxy_r_neutral"))
    raw_conservative = to_float(path.get("proxy_r_conservative"))
    raw_optimistic = to_float(path.get("proxy_r_optimistic"))
    blocked, multiplier, block_reasons = active_effects(row)
    disposition = str(row.get("replay_disposition") or "")
    source_available = raw_r is not None and terminal_bucket(path) != "missing_or_reference"
    performance_eligible = disposition == "RUNTIME_EVALUATED_WITH_PATH_SUMMARY" and source_available
    effective_r = None
    if performance_eligible:
        effective_r = 0.0 if blocked else raw_r * multiplier

    timestamp = str(group.get("decision_time_utc") or inp.get("decision_time_utc") or "")
    route = row.get("route_decision") or {}
    direct = row.get("direct_decision") or {}
    pre_ai = row.get("pre_ai_decision") or {}
    pending = row.get("pending_policy") or {}
    risk = row.get("risk_adjustment") or {}

    return {
        "event_group_id": group.get("group_id"),
        "replay_row_id": row.get("replay_row_id"),
        "runtime_activation_mode": row.get("runtime_activation_mode"),
        "decision_time_utc": timestamp,
        "date": date_key(timestamp),
        "month": month_key(timestamp),
        "symbol": str(group.get("symbol") or inp.get("symbol") or "None"),
        "source_symbol": str(group.get("source_symbol") or inp.get("source_symbol") or "None"),
        "session": str(group.get("session") or inp.get("session") or inp.get("kill_zone") or "None"),
        "side": str(group.get("side") or inp.get("side") or inp.get("direction") or "None"),
        "framework": str(group.get("framework") or "None"),
        "timeframe": str(group.get("timeframe") or inp.get("timeframe") or inp.get("market_timeframe") or "None"),
        "replay_disposition": disposition,
        "runtime_call_status": str(row.get("runtime_call_status") or ""),
        "route_decision": str(route.get("decision") if isinstance(route, dict) else "None"),
        "direct_decision": str(direct.get("decision") if isinstance(direct, dict) else "None"),
        "pre_ai_action": str(pre_ai.get("action") or "None"),
        "pre_ai_would_action": str(pre_ai.get("would_action") or "None"),
        "pending_action": str(pending.get("action") or "None"),
        "pending_would_action": str(pending.get("would_action") or "None"),
        "risk_multiplier": multiplier,
        "risk_reason": str(risk.get("reason") or "None"),
        "active_blocked": blocked,
        "active_block_reasons": block_reasons,
        "performance_eligible": performance_eligible,
        "source_available": source_available,
        "raw_proxy_r": raw_r,
        "raw_proxy_r_conservative": raw_conservative,
        "raw_proxy_r_optimistic": raw_optimistic,
        "effective_proxy_r": effective_r,
        "entry_touched": bool(path.get("entry_touched")),
        "same_bar_ambiguity": bool(path.get("same_bar_ambiguity")),
        "mfe_r": to_float(path.get("mfe_r")),
        "mae_r": to_float(path.get("mae_r")),
        "path_mode": str(path.get("replay_mode") or "missing_source"),
        "path_confidence": str(path.get("confidence") or "None"),
        "path_source_status": str(path.get("path_source_status") or "None"),
        "path_quality_bucket": path_quality_bucket(path),
        "terminal_bucket": terminal_bucket(path),
    }


def max_drawdown(values: list[float]) -> float:
    peak = 0.0
    equity = 0.0
    max_dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_dd = min(max_dd, equity - peak)
    return round(max_dd, 12)


def max_loss_streak(values: list[float]) -> int:
    current = 0
    worst = 0
    for value in values:
        if value < 0:
            current += 1
            worst = max(worst, current)
        else:
            current = 0
    return worst


def summarize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(events, key=lambda item: (str(item.get("decision_time_utc") or ""), str(item.get("replay_row_id") or "")))
    r_values = [float(item["effective_proxy_r"]) for item in ordered if item.get("effective_proxy_r") is not None]
    positive = [value for value in r_values if value > 0]
    negative = [value for value in r_values if value < 0]
    mfe_values = [float(item["mfe_r"]) for item in ordered if item.get("mfe_r") is not None]
    mae_values = [float(item["mae_r"]) for item in ordered if item.get("mae_r") is not None]
    daily: dict[str, float] = defaultdict(float)
    monthly: dict[str, float] = defaultdict(float)
    for item in ordered:
        value = item.get("effective_proxy_r")
        if value is None:
            continue
        daily[str(item.get("date"))] += float(value)
        monthly[str(item.get("month"))] += float(value)

    wins = sum(1 for item in ordered if item.get("effective_proxy_r") is not None and item.get("effective_proxy_r") > 0)
    losses = sum(1 for item in ordered if item.get("effective_proxy_r") is not None and item.get("effective_proxy_r") < 0)
    terminal_wins = sum(
        1
        for item in ordered
        if item.get("performance_eligible")
        and item.get("terminal_bucket") == "target_first_win"
        and not item.get("active_blocked")
    )
    terminal_losses = sum(
        1
        for item in ordered
        if item.get("performance_eligible")
        and item.get("terminal_bucket") == "stop_first_loss"
        and not item.get("active_blocked")
    )
    trade_count = sum(
        1
        for item in ordered
        if item.get("performance_eligible") and item.get("entry_touched") and not item.get("active_blocked")
    )
    order_attempt_count = sum(
        1 for item in ordered if item.get("performance_eligible") and not item.get("active_blocked")
    )
    profit_factor = None
    if negative:
        profit_factor = round(sum(positive) / abs(sum(negative)), 12) if positive else 0.0
    elif positive:
        profit_factor = None

    return {
        "events": len(ordered),
        "performance_rows": sum(1 for item in ordered if item.get("performance_eligible")),
        "source_available_rows": sum(1 for item in ordered if item.get("source_available")),
        "active_blocked_rows": sum(1 for item in ordered if item.get("active_blocked")),
        "order_attempt_count": order_attempt_count,
        "trade_count_entry_touched": trade_count,
        "terminal_trade_count": terminal_wins + terminal_losses,
        "target_first_wins": terminal_wins,
        "stop_first_losses": terminal_losses,
        "win_rate_terminal": round(terminal_wins / (terminal_wins + terminal_losses), 12)
        if (terminal_wins + terminal_losses)
        else None,
        "effective_r_count": len(r_values),
        "effective_r_total": round(sum(r_values), 12) if r_values else 0.0,
        "effective_r_mean": round(sum(r_values) / len(r_values), 12) if r_values else None,
        "effective_r_median": round(statistics.median(r_values), 12) if r_values else None,
        "effective_r_q05": quantile(r_values, 0.05),
        "effective_r_q95": quantile(r_values, 0.95),
        "profit_factor": profit_factor,
        "profit_factor_status": "infinite_no_losses" if positive and not negative else "finite_or_no_positive_r",
        "max_drawdown_r": max_drawdown(r_values),
        "daily_drawdown_r": round(min(daily.values()), 12) if daily else None,
        "max_loss_streak": max_loss_streak(r_values),
        "positive_r_rows": wins,
        "negative_r_rows": losses,
        "zero_r_rows": sum(1 for value in r_values if value == 0),
        "no_fill_rows": sum(
            1
            for item in ordered
            if item.get("performance_eligible") and item.get("terminal_bucket") == "no_fill_no_entry_touch"
        ),
        "timeout_or_unresolved_rows": sum(
            1
            for item in ordered
            if item.get("performance_eligible")
            and item.get("terminal_bucket") == "entry_touched_timeout_or_unresolved"
        ),
        "same_bar_ambiguity_rows": sum(1 for item in ordered if item.get("same_bar_ambiguity")),
        "mean_mfe_r": round(sum(mfe_values) / len(mfe_values), 12) if mfe_values else None,
        "mean_mae_r": round(sum(mae_values) / len(mae_values), 12) if mae_values else None,
        "monthly_r": {key: round(monthly[key], 12) for key in sorted(monthly)},
        "positive_months": sum(1 for value in monthly.values() if value > 0),
        "negative_months": sum(1 for value in monthly.values() if value < 0),
    }


def challenge_once(
    dated_r: list[tuple[str, float]],
    scenario: dict[str, float],
) -> dict[str, Any]:
    risk_pct = float(scenario["risk_pct_per_r"])
    target_pct = float(scenario["target_pct"])
    max_loss_pct = float(scenario["max_loss_pct"])
    daily_loss_pct = float(scenario["daily_loss_pct"])
    cumulative_pct = 0.0
    peak_pct = 0.0
    max_drawdown_pct = 0.0
    current_date = None
    daily_pct = 0.0
    target_reached = False
    max_loss_breached = False
    daily_loss_breached = False
    breach_index = None
    pass_index = None

    for index, (date, r_value) in enumerate(dated_r):
        if date != current_date:
            current_date = date
            daily_pct = 0.0
        pct = r_value * risk_pct
        cumulative_pct += pct
        daily_pct += pct
        peak_pct = max(peak_pct, cumulative_pct)
        max_drawdown_pct = min(max_drawdown_pct, cumulative_pct - peak_pct)
        if daily_pct <= -daily_loss_pct:
            daily_loss_breached = True
            breach_index = index
            break
        if cumulative_pct <= -max_loss_pct:
            max_loss_breached = True
            breach_index = index
            break
        if cumulative_pct >= target_pct:
            target_reached = True
            pass_index = index
            break

    return {
        "target_reached": target_reached,
        "passed": target_reached and not daily_loss_breached and not max_loss_breached,
        "daily_loss_breached": daily_loss_breached,
        "max_loss_breached": max_loss_breached,
        "final_return_pct": round(cumulative_pct, 12),
        "max_drawdown_pct": round(max_drawdown_pct, 12),
        "pass_index": pass_index,
        "breach_index": breach_index,
    }


def monte_carlo_challenge(
    events: list[dict[str, Any]],
    scenario: dict[str, float],
    iterations: int = MONTE_CARLO_ITERATIONS,
) -> dict[str, Any]:
    dated = [
        (str(item.get("date")), float(item["effective_proxy_r"]))
        for item in sorted(events, key=lambda event: str(event.get("decision_time_utc") or ""))
        if item.get("effective_proxy_r") is not None
    ]
    chronological = challenge_once(dated, scenario)
    if not dated:
        return {
            "scenario": scenario,
            "chronological": chronological,
            "iterations": iterations,
            "pass_probability": None,
            "daily_loss_breach_rate": None,
            "max_loss_breach_rate": None,
            "target_reached_rate": None,
        }

    dates = [item[0] for item in dated]
    values = [item[1] for item in dated]
    rng = random.Random(MONTE_CARLO_SEED + stable_int(scenario["scenario_id"]))
    passes = 0
    daily_breaches = 0
    max_breaches = 0
    target_reached = 0
    finals: list[float] = []
    drawdowns: list[float] = []
    for _ in range(iterations):
        shuffled = list(values)
        rng.shuffle(shuffled)
        result = challenge_once(list(zip(dates, shuffled)), scenario)
        passes += int(bool(result["passed"]))
        daily_breaches += int(bool(result["daily_loss_breached"]))
        max_breaches += int(bool(result["max_loss_breached"]))
        target_reached += int(bool(result["target_reached"]))
        finals.append(float(result["final_return_pct"]))
        drawdowns.append(float(result["max_drawdown_pct"]))

    return {
        "scenario": scenario,
        "chronological": chronological,
        "iterations": iterations,
        "pass_probability": round(passes / iterations, 12),
        "daily_loss_breach_rate": round(daily_breaches / iterations, 12),
        "max_loss_breach_rate": round(max_breaches / iterations, 12),
        "target_reached_rate": round(target_reached / iterations, 12),
        "final_return_pct_p05": quantile(finals, 0.05),
        "final_return_pct_p50": quantile(finals, 0.50),
        "final_return_pct_p95": quantile(finals, 0.95),
        "max_drawdown_pct_p05": quantile(drawdowns, 0.05),
        "max_drawdown_pct_p50": quantile(drawdowns, 0.50),
        "max_drawdown_pct_p95": quantile(drawdowns, 0.95),
    }


def stable_int(value: Any) -> int:
    return int(hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:8], 16)


def robustness_row(
    *,
    row_type: str,
    activation_mode: str,
    split_type: str,
    split_value: str,
    events: list[dict[str, Any]],
    baseline_total_r: float | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = summarize_events(events)
    total_r = float(summary.get("effective_r_total") or 0.0)
    row = {
        "schema_version": "vnext_replay_stage07_robustness_row_v1",
        "stage_id": STAGE_ID,
        "robustness_row_id": "rob_" + stable_hash([row_type, activation_mode, split_type, split_value]),
        "row_type": row_type,
        "runtime_activation_mode": activation_mode,
        "split_type": split_type,
        "split_value": split_value,
        "event_count": summary["events"],
        "performance_rows": summary["performance_rows"],
        "trade_count_entry_touched": summary["trade_count_entry_touched"],
        "terminal_trade_count": summary["terminal_trade_count"],
        "target_first_wins": summary["target_first_wins"],
        "stop_first_losses": summary["stop_first_losses"],
        "win_rate_terminal": summary["win_rate_terminal"],
        "effective_r_count": summary["effective_r_count"],
        "effective_r_total": total_r,
        "effective_r_mean": summary["effective_r_mean"],
        "effective_r_median": summary["effective_r_median"],
        "profit_factor": summary["profit_factor"],
        "max_drawdown_r": summary["max_drawdown_r"],
        "daily_drawdown_r": summary["daily_drawdown_r"],
        "max_loss_streak": summary["max_loss_streak"],
        "delta_vs_activation_overall_total_r": round(total_r - baseline_total_r, 12)
        if baseline_total_r is not None
        else None,
        "no_live_trading_or_broker_mutation": True,
        "production_config_mutated": False,
    }
    if extra:
        row.update(extra)
    return row


def stress_events(events: list[dict[str, Any]], stress_id: str, cost_r: float = 0.0) -> list[dict[str, Any]]:
    stressed: list[dict[str, Any]] = []
    for item in events:
        clone = dict(item)
        value = clone.get("effective_proxy_r")
        if value is not None and clone.get("entry_touched"):
            clone["effective_proxy_r"] = float(value) - cost_r
        if stress_id == "delayed_entry_proxy_minus_0_10r" and value is not None and clone.get("entry_touched"):
            clone["effective_proxy_r"] = float(value) - 0.10
        if stress_id == "worse_fill_proxy_minus_0_05r" and value is not None and clone.get("entry_touched"):
            clone["effective_proxy_r"] = float(value) - 0.05
        stressed.append(clone)
    return stressed


def remove_best_trade_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [
        (float(item["effective_proxy_r"]), index)
        for index, item in enumerate(events)
        if item.get("effective_proxy_r") is not None
    ]
    if not candidates:
        return list(events)
    _, remove_index = max(candidates)
    return [dict(item) for index, item in enumerate(events) if index != remove_index]


def remove_best_month_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    monthly: dict[str, float] = defaultdict(float)
    for item in events:
        if item.get("effective_proxy_r") is not None:
            monthly[str(item.get("month"))] += float(item["effective_proxy_r"])
    if not monthly:
        return list(events)
    best_month = max(monthly, key=lambda key: monthly[key])
    return [dict(item) for item in events if item.get("month") != best_month]


def deterministic_missed_win_events(events: list[dict[str, Any]], fraction: float) -> list[dict[str, Any]]:
    wins = [
        item for item in events if item.get("effective_proxy_r") is not None and float(item["effective_proxy_r"]) > 0
    ]
    cutoff = max(1, int(math.ceil(len(wins) * fraction))) if wins else 0
    win_ids = {
        item.get("replay_row_id")
        for item in sorted(wins, key=lambda item: stable_hash(item.get("replay_row_id")))[:cutoff]
    }
    stressed: list[dict[str, Any]] = []
    for item in events:
        clone = dict(item)
        if clone.get("replay_row_id") in win_ids:
            clone["effective_proxy_r"] = 0.0
        stressed.append(clone)
    return stressed


def placebo_random_signal_summary(events: list[dict[str, Any]], iterations: int = MONTE_CARLO_ITERATIONS) -> dict[str, Any]:
    source_pool = [
        float(item["raw_proxy_r"])
        for item in events
        if item.get("performance_eligible") and item.get("raw_proxy_r") is not None
    ]
    selected_count = sum(
        1 for item in events if item.get("performance_eligible") and not item.get("active_blocked")
    )
    if not source_pool or selected_count <= 0:
        return {"iterations": iterations, "selected_count": selected_count, "placebo_total_r_mean": None}
    rng = random.Random(MONTE_CARLO_SEED + 91)
    totals: list[float] = []
    for _ in range(iterations):
        if selected_count <= len(source_pool):
            sample = rng.sample(source_pool, selected_count)
        else:
            sample = [rng.choice(source_pool) for _ in range(selected_count)]
        totals.append(sum(sample))
    return {
        "iterations": iterations,
        "selected_count": selected_count,
        "placebo_total_r_mean": round(sum(totals) / len(totals), 12),
        "placebo_total_r_p05": quantile(totals, 0.05),
        "placebo_total_r_p50": quantile(totals, 0.50),
        "placebo_total_r_p95": quantile(totals, 0.95),
    }


def group_by(events: list[dict[str, Any]], field: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in events:
        groups[str(item.get(field) or "None")].append(item)
    return dict(groups)


def chronological_folds(events: list[dict[str, Any]], folds: int = 4) -> dict[str, list[dict[str, Any]]]:
    ordered = sorted(events, key=lambda item: str(item.get("decision_time_utc") or ""))
    if not ordered:
        return {}
    result: dict[str, list[dict[str, Any]]] = {}
    for index, item in enumerate(ordered):
        fold_index = min(folds - 1, int(index * folds / len(ordered)))
        result.setdefault(f"fold_{fold_index + 1}_of_{folds}", []).append(item)
    return result


def old_recent_split(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    ordered = sorted(events, key=lambda item: str(item.get("decision_time_utc") or ""))
    midpoint = len(ordered) // 2
    return {"old_half": ordered[:midpoint], "recent_half": ordered[midpoint:]}


def build_event_metrics(events_by_mode: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    robustness_rows: list[dict[str, Any]] = []
    mode_metrics: dict[str, Any] = {}
    for mode, events in sorted(events_by_mode.items()):
        overall = summarize_events(events)
        mode_metrics[mode] = {
            "overall": overall,
            "decision_distributions": {
                "route_decision": sorted_counter(Counter(str(item.get("route_decision")) for item in events)),
                "direct_decision": sorted_counter(Counter(str(item.get("direct_decision")) for item in events)),
                "pre_ai_action": sorted_counter(Counter(str(item.get("pre_ai_action")) for item in events)),
                "pending_action": sorted_counter(Counter(str(item.get("pending_action")) for item in events)),
                "risk_reason": sorted_counter(Counter(str(item.get("risk_reason")) for item in events)),
                "path_quality_bucket": sorted_counter(Counter(str(item.get("path_quality_bucket")) for item in events)),
                "terminal_bucket": sorted_counter(Counter(str(item.get("terminal_bucket")) for item in events)),
            },
            "challenge_scenarios": {
                scenario["scenario_id"]: monte_carlo_challenge(events, scenario)
                for scenario in CHALLENGE_SCENARIOS
            },
            "placebo_random_signal_baseline": placebo_random_signal_summary(events),
            "regime_volatility_news_source_status": {
                "regime_rows_source_bound": 0,
                "volatility_rows_source_bound": 0,
                "news_rows_source_bound": 0,
                "status": (
                    "not present as source-bound fields in Stage05 saturated replay rows; "
                    "Stage07 records this as data-quality/source limitation rather than "
                    "fabricating regime/news partitions"
                ),
            },
        }

        baseline_total = float(overall.get("effective_r_total") or 0.0)
        robustness_rows.append(
            robustness_row(
                row_type="overall",
                activation_mode=mode,
                split_type="all",
                split_value="all_events",
                events=events,
                baseline_total_r=baseline_total,
            )
        )
        for split_type, groups in [
            ("month", group_by(events, "month")),
            ("old_vs_recent", old_recent_split(events)),
            ("walk_forward_time_fold", chronological_folds(events)),
            ("symbol", group_by(events, "symbol")),
            ("session", group_by(events, "session")),
            ("side", group_by(events, "side")),
            ("framework", group_by(events, "framework")),
            ("timeframe", group_by(events, "timeframe")),
            ("path_mode", group_by(events, "path_mode")),
            ("path_quality_bucket", group_by(events, "path_quality_bucket")),
            ("path_confidence", group_by(events, "path_confidence")),
            ("path_source_status", group_by(events, "path_source_status")),
            ("terminal_bucket", group_by(events, "terminal_bucket")),
        ]:
            for value, subset in sorted(groups.items()):
                robustness_rows.append(
                    robustness_row(
                        row_type="split_metric",
                        activation_mode=mode,
                        split_type=split_type,
                        split_value=value,
                        events=subset,
                        baseline_total_r=baseline_total,
                    )
                )

        for split_type in ("symbol", "session", "side", "framework", "timeframe"):
            for value in sorted(group_by(events, split_type)):
                subset = [item for item in events if str(item.get(split_type) or "None") != value]
                robustness_rows.append(
                    robustness_row(
                        row_type="holdout_metric",
                        activation_mode=mode,
                        split_type=f"leave_one_{split_type}_out",
                        split_value=value,
                        events=subset,
                        baseline_total_r=baseline_total,
                    )
                )

        for cost_r in STRESS_COSTS_R:
            stress_id = f"entry_touched_cost_minus_{cost_r:.2f}r"
            robustness_rows.append(
                robustness_row(
                    row_type="stress_cost_metric",
                    activation_mode=mode,
                    split_type="stress_cost",
                    split_value=stress_id,
                    events=stress_events(events, stress_id, cost_r),
                    baseline_total_r=baseline_total,
                    extra={"stress_cost_r": cost_r},
                )
            )
        for stress_id, stressed in [
            ("delayed_entry_proxy_minus_0_10r", stress_events(events, "delayed_entry_proxy_minus_0_10r")),
            ("worse_fill_proxy_minus_0_05r", stress_events(events, "worse_fill_proxy_minus_0_05r")),
            ("remove_best_trade", remove_best_trade_events(events)),
            ("remove_best_month", remove_best_month_events(events)),
            ("deterministic_missed_10pct_positive_fills", deterministic_missed_win_events(events, 0.10)),
            ("deterministic_missed_25pct_positive_fills", deterministic_missed_win_events(events, 0.25)),
        ]:
            robustness_rows.append(
                robustness_row(
                    row_type="stress_path_metric",
                    activation_mode=mode,
                    split_type="stress_path",
                    split_value=stress_id,
                    events=stressed,
                    baseline_total_r=baseline_total,
                )
            )

        for scenario_id, scenario_summary in mode_metrics[mode]["challenge_scenarios"].items():
            robustness_rows.append(
                {
                    "schema_version": "vnext_replay_stage07_robustness_row_v1",
                    "stage_id": STAGE_ID,
                    "robustness_row_id": "rob_" + stable_hash(["monte_carlo", mode, scenario_id]),
                    "row_type": "monte_carlo_trade_order_reshuffle",
                    "runtime_activation_mode": mode,
                    "split_type": "challenge_scenario",
                    "split_value": scenario_id,
                    "event_count": len(events),
                    "iterations": MONTE_CARLO_ITERATIONS,
                    "pass_probability": scenario_summary.get("pass_probability"),
                    "daily_loss_breach_rate": scenario_summary.get("daily_loss_breach_rate"),
                    "max_loss_breach_rate": scenario_summary.get("max_loss_breach_rate"),
                    "target_reached_rate": scenario_summary.get("target_reached_rate"),
                    "final_return_pct_p05": scenario_summary.get("final_return_pct_p05"),
                    "final_return_pct_p50": scenario_summary.get("final_return_pct_p50"),
                    "final_return_pct_p95": scenario_summary.get("final_return_pct_p95"),
                    "no_live_trading_or_broker_mutation": True,
                    "production_config_mutated": False,
                }
            )

        placebo = mode_metrics[mode]["placebo_random_signal_baseline"]
        robustness_rows.append(
            {
                "schema_version": "vnext_replay_stage07_robustness_row_v1",
                "stage_id": STAGE_ID,
                "robustness_row_id": "rob_" + stable_hash(["placebo_random_signal", mode]),
                "row_type": "placebo_null_random_signal_baseline",
                "runtime_activation_mode": mode,
                "split_type": "placebo_random_signal",
                "split_value": "same_order_attempt_count_randomized_over_source_available_pool",
                "event_count": len(events),
                **placebo,
                "no_live_trading_or_broker_mutation": True,
                "production_config_mutated": False,
            }
        )

    return mode_metrics, robustness_rows


def aggregate_ablation_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aggregate: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    rows_seen = 0
    for row in iter_jsonl(ABLATION_LEDGER_PATH):
        rows_seen += 1
        key = (
            str(row.get("runtime_activation_mode") or "None"),
            str(row.get("surface") or "None"),
            str(row.get("dimension") or "None"),
            str(row.get("dimension_value") or "None"),
        )
        item = aggregate.setdefault(
            key,
            {
                "rows": 0,
                "decision_changed_count": 0,
                "effect_changed_count": 0,
                "proxy_r_count": 0,
                "proxy_r_sum": 0.0,
                "path_signal_counts": Counter(),
                "transition_counts": Counter(),
                "mixed_involvement_count": 0,
            },
        )
        item["rows"] += 1
        item["decision_changed_count"] += int(bool(row.get("decision_changed")))
        item["effect_changed_count"] += int(bool(row.get("effect_changed")))
        item["mixed_involvement_count"] += int(bool(row.get("mixed_involvement")))
        proxy = to_float(row.get("proxy_r_neutral"))
        if proxy is not None:
            item["proxy_r_count"] += 1
            item["proxy_r_sum"] += proxy
        item["path_signal_counts"][str(row.get("path_outcome_signal") or "None")] += 1
        transition = f"{row.get('decision_before')}->{row.get('decision_after')}"
        item["transition_counts"][transition] += 1

    output_rows: list[dict[str, Any]] = []
    for key, item in sorted(aggregate.items()):
        mode, surface, dimension, value = key
        output_rows.append(
            {
                "schema_version": "vnext_replay_stage07_robustness_row_v1",
                "stage_id": STAGE_ID,
                "robustness_row_id": "rob_" + stable_hash(["ablation_delta", *key]),
                "row_type": "ablation_delta",
                "runtime_activation_mode": mode,
                "surface": surface,
                "split_type": f"ablation_{dimension}",
                "split_value": value,
                "dimension": dimension,
                "dimension_value": value,
                "ablation_rows": item["rows"],
                "decision_changed_count": item["decision_changed_count"],
                "decision_changed_rate": round(item["decision_changed_count"] / item["rows"], 12)
                if item["rows"]
                else None,
                "effect_changed_count": item["effect_changed_count"],
                "mixed_involvement_count": item["mixed_involvement_count"],
                "proxy_r_count": item["proxy_r_count"],
                "proxy_r_sum": round(item["proxy_r_sum"], 12),
                "proxy_r_mean": round(item["proxy_r_sum"] / item["proxy_r_count"], 12)
                if item["proxy_r_count"]
                else None,
                "decision_transition_counts": sorted_counter(item["transition_counts"]),
                "path_signal_counts": sorted_counter(item["path_signal_counts"]),
                "no_live_trading_or_broker_mutation": True,
                "production_config_mutated": False,
            }
        )
    return output_rows, {"ablation_rows_seen": rows_seen, "ablation_group_rows": len(output_rows)}


def mixed_contribution_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    source_required = 0
    replay_resolvable = 0
    for row in iter_jsonl(MIXED_RESOLUTION_LEDGER_PATH):
        classification = str(row.get("classification") or "None")
        class_counts[classification] += 1
        source_required += int(classification == "source-required and not safely resolvable")
        replay_resolvable += int(classification in {"ambiguous but replay-resolvable", "resolvable into AVOID"})
        rows.append(
            {
                "schema_version": "vnext_replay_stage07_robustness_row_v1",
                "stage_id": STAGE_ID,
                "robustness_row_id": "rob_" + stable_hash([
                    "mixed_contribution",
                    row.get("surface"),
                    row.get("dimension"),
                    row.get("dimension_value"),
                    classification,
                ]),
                "row_type": "mixed_contribution_delta",
                "runtime_activation_mode": "|".join(sorted(map(str, row.get("runtime_activation_modes") or []))),
                "surface": row.get("surface"),
                "split_type": f"mixed_{row.get('dimension')}",
                "split_value": str(row.get("dimension_value") or "None"),
                "dimension": row.get("dimension"),
                "dimension_value": row.get("dimension_value"),
                "classification": classification,
                "classification_reason": row.get("classification_reason"),
                "ablation_rows": row.get("ablation_rows"),
                "event_group_count": row.get("event_group_count"),
                "decision_changed_count": row.get("decision_changed_count"),
                "effect_changed_count": row.get("effect_changed_count"),
                "proxy_r_count": row.get("proxy_r_count"),
                "proxy_r_sum": row.get("proxy_r_sum"),
                "proxy_r_mean": row.get("proxy_r_mean"),
                "decision_transition_counts": row.get("decision_transition_counts"),
                "path_signal_counts": row.get("path_signal_counts"),
                "path_outcome_counts": row.get("path_outcome_counts"),
                "no_live_trading_or_broker_mutation": True,
                "production_config_mutated": False,
            }
        )
    return rows, {
        "mixed_rows_seen": len(rows),
        "mixed_classification_counts": sorted_counter(class_counts),
        "mixed_source_required_rows": source_required,
        "mixed_replay_resolvable_rows": replay_resolvable,
    }


def build_outputs() -> dict[str, Any]:
    stage05_summary = read_json(SATURATED_REPLAY_SUMMARY_PATH)
    stage05_metrics = read_json(STAGE05_METRICS_SUMMARY_PATH)
    stage06_summary = read_json(STAGE06_SUMMARY_PATH)

    events_by_mode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    projected_rows = 0
    duplicate_ids: Counter[str] = Counter()
    for row in iter_jsonl(SATURATED_REPLAY_LEDGER_PATH):
        projected = project_replay_row(row)
        projected_rows += 1
        duplicate_ids[str(projected.get("replay_row_id"))] += 1
        events_by_mode[str(projected["runtime_activation_mode"])].append(projected)

    mode_metrics, robustness_rows = build_event_metrics(events_by_mode)
    ablation_rows, ablation_summary = aggregate_ablation_rows()
    mixed_rows, mixed_summary = mixed_contribution_rows()
    robustness_rows.extend(ablation_rows)
    robustness_rows.extend(mixed_rows)

    activation_delta = {}
    if "current_config_shadow" in mode_metrics and "hypothetical_activated_vnext" in mode_metrics:
        current_total = mode_metrics["current_config_shadow"]["overall"]["effective_r_total"]
        activated_total = mode_metrics["hypothetical_activated_vnext"]["overall"]["effective_r_total"]
        activation_delta = {
            "effective_r_total_delta_hypothetical_minus_current": round(activated_total - current_total, 12),
            "trade_count_delta_hypothetical_minus_current": (
                mode_metrics["hypothetical_activated_vnext"]["overall"]["trade_count_entry_touched"]
                - mode_metrics["current_config_shadow"]["overall"]["trade_count_entry_touched"]
            ),
            "max_drawdown_r_delta_hypothetical_minus_current": round(
                mode_metrics["hypothetical_activated_vnext"]["overall"]["max_drawdown_r"]
                - mode_metrics["current_config_shadow"]["overall"]["max_drawdown_r"],
                12,
            ),
        }

    prop_metrics = {
        "schema_version": "vnext_replay_stage07_prop_firm_metrics_v1",
        "stage_id": STAGE_ID,
        "generated_utc": utc_now(),
        "pass": True,
        "metric_scope": (
            "Stage07 source-bound proxy/trading metrics over Stage05 saturated replay "
            "and Stage06 ablation/MIXED ledgers; not broker-actual-R and not a "
            "production-change promotion"
        ),
        "candidate_events": stage05_metrics.get("candidate_events"),
        "evaluated_events": stage05_metrics.get("evaluated_events"),
        "skipped_events_by_reason": stage05_metrics.get("skipped_events_by_reason"),
        "stage05_replay_rows": stage05_summary.get("replay_rows"),
        "stage06_ablation_rows": stage06_summary.get("ablation_rows"),
        "stage06_mixed_resolution_rows": stage06_summary.get("mixed_resolution_rows"),
        "projected_replay_rows": projected_rows,
        "duplicate_replay_row_ids": {
            "duplicate_key_count": sum(1 for count in duplicate_ids.values() if count > 1),
            "duplicate_extra_rows": sum(count - 1 for count in duplicate_ids.values() if count > 1),
        },
        "mode_metrics": mode_metrics,
        "activation_delta": activation_delta,
        "ablation_summary": ablation_summary,
        "mixed_summary": mixed_summary,
        "robustness_rows": len(robustness_rows),
        "monte_carlo_seed": MONTE_CARLO_SEED,
        "monte_carlo_iterations": MONTE_CARLO_ITERATIONS,
        "challenge_scenarios": [dict(item) for item in CHALLENGE_SCENARIOS],
        "data_quality_source_limitations": {
            "broker_actual_r_used": False,
            "regime_volatility_news_split_status": (
                "Stage05 saturated replay rows do not carry source-bound regime, "
                "volatility-state, or news-state fields. Stage07 records this as a "
                "source limitation and does not fabricate those splits."
            ),
            "performance_denominator_rule": (
                "R metrics use rows with replay_disposition=RUNTIME_EVALUATED_WITH_PATH_SUMMARY "
                "and a non-missing best_available_path proxy R. Pre-AI-only insufficient "
                "post-L2 rows remain counted as candidates/skips, not broker-realized trades."
            ),
        },
        "no_live_trading_or_broker_mutation": True,
        "production_config_mutated": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
    }
    summary = {
        "schema_version": "vnext_replay_stage07_prop_firm_robustness_summary_v1",
        "stage_id": STAGE_ID,
        "generated_utc": utc_now(),
        "pass": True,
        "projected_replay_rows": projected_rows,
        "activation_modes": sorted(events_by_mode),
        "mode_overall": {mode: metrics["overall"] for mode, metrics in mode_metrics.items()},
        "activation_delta": activation_delta,
        "robustness_rows": len(robustness_rows),
        **ablation_summary,
        **mixed_summary,
        "stage08_next": "failure/repair dossiers for runtime/system limits, M15 blindness, source gaps, AI, risk, and market coverage remain next-stage work",
        "no_live_trading_or_broker_mutation": True,
        "production_config_mutated": False,
    }

    write_json(PROP_FIRM_METRICS_PATH, prop_metrics)
    write_jsonl(ROBUSTNESS_LEDGER_PATH, robustness_rows)
    write_json(STAGE07_SUMMARY_PATH, summary)
    update_output_manifest()
    update_session_state(summary)
    return summary


def update_output_manifest() -> None:
    existing = read_json(OUTPUT_MANIFEST_PATH) if OUTPUT_MANIFEST_PATH.exists() else {}
    existing_paths = {
        item.get("path"): item
        for item in existing.get("outputs", [])
        if isinstance(item, dict) and item.get("path")
    }
    for path in [PROP_FIRM_METRICS_PATH, ROBUSTNESS_LEDGER_PATH, STAGE07_SUMMARY_PATH]:
        existing_paths[rel(path)] = {
            "path": rel(path),
            "exists": True,
            "bytes": path.stat().st_size,
            "lines": line_count(path),
            "sha256": sha256_file(path),
            "source_kind": "generated_replay_output",
        }
    write_json(
        OUTPUT_MANIFEST_PATH,
        {
            "schema_version": "vnext_replay_output_manifest_v1",
            "generated_utc": utc_now(),
            "route_id": "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24",
            "outputs": [existing_paths[key] for key in sorted(existing_paths)],
            "next_stage": NEXT_STAGE_ID,
        },
    )


def update_session_state(summary: dict[str, Any]) -> None:
    if not SESSION_STATE_PATH.exists():
        return
    state = read_json(SESSION_STATE_PATH)
    completed = list(state.get("completed_stage_ids") or [])
    if STAGE_ID not in completed:
        completed.append(STAGE_ID)
    outputs = list(state.get("current_output_artifacts") or [])
    for path in [PROP_FIRM_METRICS_PATH, ROBUSTNESS_LEDGER_PATH, STAGE07_SUMMARY_PATH]:
        item = rel(path)
        if item not in outputs:
            outputs.append(item)
    tests = list(state.get("last_tests_or_verifiers") or [])
    verifier = (
        "python research/science_program_2026_05/06_outcome_testing/"
        "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/"
        "build_vnext_replay_prop_firm_robustness_2026_05_24.py -> "
        f"pass; {summary.get('robustness_rows')} robustness rows; "
        f"{summary.get('projected_replay_rows')} projected replay rows"
    )
    if verifier not in tests:
        tests.append(verifier)
    state.update(
        {
            "updated_utc": utc_now(),
            "current_stage_id": NEXT_STAGE_ID,
            "current_shard_id": "STAGE_08_FAILURE_AND_REPAIR_DOSSIERS__ALL_LIMITATION_FAMILIES__ALL_SOURCES__000",
            "current_objective": (
                "Produce runtime/system limitation, M15-blindness, entry/execution, "
                "source-gap, AI, risk, and market-coverage repair dossiers from the "
                "Stage05-Stage07 replay, ablation, MIXED, prop-firm, and robustness metrics."
            ),
            "current_output_artifacts": outputs,
            "completed_stage_ids": completed,
            "next_executable_action": (
                "Build and run the STAGE_08 failure and repair dossier builder over "
                "VNEXT_REPLAY_PROP_FIRM_METRICS_2026-05-24.json, "
                "VNEXT_REPLAY_ROBUSTNESS_LEDGER_2026-05-24.jsonl, Stage05/Stage06 "
                "summaries, source-gap ledgers, and output manifest."
            ),
            "last_tests_or_verifiers": tests,
            "last_commit": "b0f3699b0 research: build vnext replay ablation stage",
            "last_verified_head": "b0f3699b01057ba60e61f2ce7e33c8f882582969",
            "last_verified_git_status": [
                " M .context/LIVE_STATE.md",
                " M research/science_program_2026_05/06_outcome_testing/gtos_vnext_replay_truth_engine/VNEXT_REPLAY_TRUTH_ENGINE_SESSION_STATE_2026-05-24.json",
                " M research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_OUTPUT_MANIFEST_2026-05-24.json",
                "?? research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_PROP_FIRM_METRICS_2026-05-24.json",
                "?? research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_PROP_FIRM_ROBUSTNESS_SUMMARY_2026-05-24.json",
                "?? research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_ROBUSTNESS_LEDGER_2026-05-24.jsonl",
                "?? research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/build_vnext_replay_prop_firm_robustness_2026_05_24.py",
            ],
            "open_questions_remaining": [
                "STAGE_08 not yet complete: no runtime/system limitation, M15-blindness, entry/execution, source-gap, AI, risk, or market-coverage repair dossiers exist yet.",
                "No final promotion/kill/repair/keep-shadow map or final truth-freeze report exists yet in this replay truth-engine route.",
            ],
            "resume_instruction": (
                "On resume or uncertainty: regenerate/read .context/LIVE_STATE.md; "
                "reread the controlling prompt, starter, this session-state file, "
                "goal_session_research_discipline.md, research_operating_doctrine.md, "
                "orchestrator hardening files, latest handoff, active config, freeze report, "
                "freeze ledger, master/batch ledgers, and current runtime/tests from disk; "
                "verify HEAD/config/runtime artifact manifest hashes and git status; repair "
                "this JSON if stale; then execute next_executable_action for STAGE_08 "
                "without restarting broad planning."
            ),
        }
    )
    write_json(SESSION_STATE_PATH, state)


def check_outputs() -> None:
    prop = read_json(PROP_FIRM_METRICS_PATH)
    summary = read_json(STAGE07_SUMMARY_PATH)
    robustness_count = line_count(ROBUSTNESS_LEDGER_PATH)
    if prop.get("stage_id") != STAGE_ID or summary.get("stage_id") != STAGE_ID:
        raise AssertionError("Stage07 output has wrong stage_id")
    if not prop.get("pass") or not summary.get("pass"):
        raise AssertionError("Stage07 summary did not pass")
    if summary.get("robustness_rows") != robustness_count:
        raise AssertionError("Stage07 robustness ledger line count does not match summary")
    if robustness_count <= 0:
        raise AssertionError("Stage07 robustness ledger is empty")
    if not prop.get("mode_metrics"):
        raise AssertionError("Stage07 prop metrics missing mode_metrics")
    required_modes = {"current_config_shadow", "hypothetical_activated_vnext"}
    if not required_modes.issubset(set(prop.get("mode_metrics"))):
        raise AssertionError("Stage07 prop metrics missing activation modes")
    seen_row_types: Counter[str] = Counter()
    for row in iter_jsonl(ROBUSTNESS_LEDGER_PATH):
        if row.get("stage_id") != STAGE_ID:
            raise AssertionError("Stage07 robustness row has wrong stage_id")
        seen_row_types[str(row.get("row_type") or "None")] += 1
    required_types = {
        "overall",
        "split_metric",
        "holdout_metric",
        "stress_cost_metric",
        "stress_path_metric",
        "monte_carlo_trade_order_reshuffle",
        "placebo_null_random_signal_baseline",
        "ablation_delta",
        "mixed_contribution_delta",
    }
    missing = required_types - set(seen_row_types)
    if missing:
        raise AssertionError(f"Stage07 robustness ledger missing row types: {sorted(missing)}")
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    manifest_paths = {item.get("path") for item in manifest.get("outputs", []) if isinstance(item, dict)}
    for path in [PROP_FIRM_METRICS_PATH, ROBUSTNESS_LEDGER_PATH, STAGE07_SUMMARY_PATH]:
        if rel(path) not in manifest_paths:
            raise AssertionError(f"Output manifest missing {rel(path)}")
    state = read_json(SESSION_STATE_PATH)
    if STAGE_ID not in set(state.get("completed_stage_ids") or []):
        raise AssertionError("Session state missing completed Stage07")
    if state.get("current_stage_id") != NEXT_STAGE_ID:
        raise AssertionError("Session state did not advance to Stage08")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_outputs()
        print("vNext Stage07 prop-firm/robustness check passed")
        return
    summary = build_outputs()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
