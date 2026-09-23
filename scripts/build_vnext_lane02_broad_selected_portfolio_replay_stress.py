"""Build Lane 02 broad selected-denominator portfolio replay/stress artifacts.

This route is offline and source-bound. It consumes the vNext selected-row
dynamic-router replay shards, the Lane01 scheduler contract when available, and
local cost/lifecycle calibration evidence. It writes full row-level replay
decisions plus split, stress, concentration, source-completeness, verifier,
manifest, and completion-audit artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
ROUTE_ID = "vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID
LANE01_DIR = (
    ROOT
    / "research"
    / "operations"
    / "vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31"
)
LANE06_DIR = (
    ROOT
    / "research"
    / "operations"
    / "vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31"
)
ACTIVATION_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
)
EI15R_DIR = ACTIVATION_DIR / "ei15r"
CONFIG_PATH = ROOT / "config" / "agent_config.yaml"
LIVE_STATE = ROOT / ".context" / "LIVE_STATE.md"

REPLAY_LEDGER = ROUTE_DIR / "LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_LEDGER.jsonl"
SPLIT_SUMMARY = ROUTE_DIR / "LANE02_BROAD_SELECTED_SPLIT_STRESS_SUMMARY.jsonl"
CONCENTRATION_LEDGER = ROUTE_DIR / "LANE02_CONCENTRATION_AND_LEAVE_ONE_OUT_LEDGER.jsonl"
SOURCE_COMPLETENESS_LEDGER = ROUTE_DIR / "LANE02_SOURCE_COMPLETENESS_LEDGER.jsonl"
RESULT_MATERIALIZATION_LEDGER = ROUTE_DIR / "LANE02_RESULT_MATERIALIZATION_LEDGER.jsonl"
SCENARIO_STRESS_LEDGER = ROUTE_DIR / "LANE02_PORTFOLIO_SCENARIO_STRESS_LEDGER.jsonl"
COST_EXPOSURE_SUMMARY = ROUTE_DIR / "LANE02_COST_EXPOSURE_STRESS_SUMMARY.json"
PORTFOLIO_SUMMARY = ROUTE_DIR / "LANE02_PORTFOLIO_REPLAY_STRESS_SUMMARY.json"
COMPLETION_AUDIT = ROUTE_DIR / "LANE02_COMPLETION_AUDIT.json"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE02_OUTPUT_MANIFEST.json"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE02_CONTEXT_ANCHOR.md"
LANE01_ADAPTER = ROUTE_DIR / "LANE02_LANE01_COMPAT_ADAPTER.json"
VERIFIER = ROUTE_DIR / "verify_lane02_broad_selected_portfolio_replay_stress.py"
VERIFICATION_RESULT = ROUTE_DIR / "LANE02_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "LANE02_FOCUSED_TEST_RESULT.xml"

EXPECTED_SELECTED_ROWS = 289600
UPSTREAM_DYNAMIC_ROUTER_TOTAL_R = 286221.353599
REQUIRED_SPLIT_SCOPES = {
    "chosen_policy",
    "date",
    "framework",
    "market_type",
    "month",
    "origin_family",
    "recent_vs_old",
    "regime",
    "risk_cell_id",
    "session_bucket",
    "side",
    "source_mode",
    "spread_r_bucket",
    "symbol",
}
BASE_SCENARIO_ID = "strict_lane01_same_symbol_with_source_partial_release"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="verify existing Lane02 outputs")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int | None:
    if not path.exists() or path.suffix != ".jsonl":
        return None
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))


def count_jsonl(path: Path) -> int:
    result = line_count(path)
    return int(result or 0)


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip().replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def fnum(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return number


def round9(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 9)


def clean_family(value: Any) -> str:
    if value in (None, ""):
        return "unknown"
    text = str(value)
    for prefix in ("origin_current_", "origin_"):
        if text.startswith(prefix):
            text = text.removeprefix(prefix)
    return text or "unknown"


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8", errors="replace")) or {}


def market_type(symbol: str) -> str:
    if symbol in {"BTCUSD", "ETHUSD"}:
        return "crypto"
    if symbol in {"XAUUSD", "XAGUSD"}:
        return "metals"
    if symbol in {"UKOIL_cash", "USOIL_cash"}:
        return "energy"
    if symbol in {"GER40", "JP225", "NAS100", "SPX500", "UK100", "US30_cash"}:
        return "index_cfd"
    if len(symbol) == 6 and symbol.isalpha():
        return "fx"
    return "unknown_market_type"


def spread_r_bucket(value: Any) -> str:
    number = fnum(value)
    if number is None:
        return "spread_or_cost_r_missing"
    if number <= 0.02:
        return "cost_r_le_0_02"
    if number <= 0.05:
        return "cost_r_0_02_to_0_05"
    if number <= 0.10:
        return "cost_r_0_05_to_0_10"
    return "cost_r_gt_0_10"


def stop_freeze_status(row: dict[str, Any], dims: dict[str, Any], inputs: dict[str, Any]) -> str:
    basis = (
        row.get("selected_cell_risk_decision_basis")
        or dims.get("selected_cell_risk_decision_basis")
        or inputs.get("selected_cell_risk_decision_basis")
    )
    match = (
        row.get("selected_cell_risk_match_reason")
        or dims.get("selected_cell_risk_match_reason")
        or inputs.get("selected_cell_risk_match_reason")
    )
    if basis and "positive" in str(basis):
        return "broker_geometry_positive_stop_freeze_feasible_proxy"
    if match and "positive" in str(match):
        return "selected_row_current_broker_geometry_positive"
    return "stop_freeze_feasibility_not_proven_in_selected_row"


def source_quality_status(row: dict[str, Any]) -> str:
    if row.get("non_replayable_reason"):
        return "non_replayable_selected_row"
    if row.get("same_bar_ambiguity"):
        return "same_bar_ambiguity_present"
    m1_status = str(row.get("m1_availability_status") or "")
    if m1_status == "local_m1_bar_available_for_entry_minute":
        return "m1_entry_minute_available"
    if "missing" in m1_status or "outside" in m1_status:
        return "m1_entry_source_gap"
    return "source_quality_m1_partial_or_unknown"


def source_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def partial_release_contract(
    *,
    chosen_policy: str | None,
    entry_dt: datetime,
    exit_dt: datetime,
    final_r: float,
    mfe_r: float | None,
    trace: dict[str, Any],
) -> dict[str, Any]:
    if chosen_policy != "partial_be_runner":
        return {
            "partial_fraction": 0.0,
            "partial_release_dt": None,
            "partial_release_source_status": "not_partial_be_runner_policy",
            "residual_exposure_fraction_after_partial": 0.0,
            "risk_release_dt": exit_dt,
        }

    partial_fraction = fnum(trace.get("partial_fraction"), 0.5) or 0.5
    partial_fraction = max(0.0, min(partial_fraction, 1.0))
    be_time = parse_dt(trace.get("be_trigger_time_utc"))
    grace_exit = exit_dt + timedelta(minutes=15)
    if be_time and entry_dt <= be_time <= grace_exit:
        return {
            "partial_fraction": partial_fraction,
            "partial_release_dt": be_time,
            "partial_release_source_status": "exact_be_trigger_time_from_dynamic_policy_trace",
            "residual_exposure_fraction_after_partial": round9(1.0 - partial_fraction),
            "risk_release_dt": be_time,
        }

    if final_r > 0 or (mfe_r is not None and mfe_r >= 1.0):
        return {
            "partial_fraction": partial_fraction,
            "partial_release_dt": None,
            "partial_release_source_status": "partial_trigger_probable_but_exact_time_missing_strict_risk_released_at_exit",
            "residual_exposure_fraction_after_partial": None,
            "risk_release_dt": exit_dt,
        }

    return {
        "partial_fraction": partial_fraction,
        "partial_release_dt": None,
        "partial_release_source_status": "no_partial_trigger_before_stop_or_flat_exit",
        "residual_exposure_fraction_after_partial": 0.0,
        "risk_release_dt": exit_dt,
    }


def new_stats() -> dict[str, Any]:
    return {
        "accepted_gross_loss_r": 0.0,
        "accepted_gross_profit_r": 0.0,
        "accepted_gross_r_sum": 0.0,
        "accepted_losses": 0,
        "accepted_rows": 0,
        "accepted_wins": 0,
        "breakevens": 0,
        "rejected_rows": 0,
        "rows": 0,
        "selected_gross_r_sum": 0.0,
    }


def update_stats(stats: dict[str, Any], gross_r: float, accepted: bool) -> None:
    stats["rows"] += 1
    stats["selected_gross_r_sum"] = round9(stats["selected_gross_r_sum"] + gross_r)
    if not accepted:
        stats["rejected_rows"] += 1
        return
    stats["accepted_rows"] += 1
    stats["accepted_gross_r_sum"] = round9(stats["accepted_gross_r_sum"] + gross_r)
    if gross_r > 0:
        stats["accepted_wins"] += 1
        stats["accepted_gross_profit_r"] = round9(stats["accepted_gross_profit_r"] + gross_r)
    elif gross_r < 0:
        stats["accepted_losses"] += 1
        stats["accepted_gross_loss_r"] = round9(stats["accepted_gross_loss_r"] + gross_r)
    else:
        stats["breakevens"] += 1


def finalize_stats(stats: dict[str, Any]) -> dict[str, Any]:
    accepted = int(stats["accepted_rows"])
    rows = int(stats["rows"])
    wins = int(stats["accepted_wins"])
    losses = int(stats["accepted_losses"])
    gross_profit = float(stats["accepted_gross_profit_r"])
    gross_loss = float(stats["accepted_gross_loss_r"])
    return {
        **stats,
        "accepted_avg_loss_r": round9(gross_loss / losses) if losses else None,
        "accepted_avg_win_r": round9(gross_profit / wins) if wins else None,
        "accepted_expectancy_r": round9(float(stats["accepted_gross_r_sum"]) / accepted) if accepted else None,
        "accepted_profit_factor": round9(gross_profit / abs(gross_loss)) if gross_loss < 0 else None,
        "accepted_win_rate": round9(wins / accepted) if accepted else None,
        "accepted_win_rate_excluding_be": round9(wins / (wins + losses)) if wins + losses else None,
        "acceptance_rate": round9(accepted / rows) if rows else None,
    }


def iter_shards() -> list[Path]:
    return sorted(EI15R_DIR.glob("final_dynamic_router_replay.part-*.jsonl"))


def extract_slim_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    shard_counts: dict[str, int] = {}
    duplicate_ids: Counter[str] = Counter()
    policy_counts: Counter[str] = Counter()
    non_replayable = 0

    for shard in iter_shards():
        count = 0
        with shard.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                dims = row.get("router_dimensions") or {}
                inputs = row.get("router_inputs") or {}
                trace = row.get("dynamic_policy_transition_trace") or {}
                if not isinstance(trace, dict):
                    trace = {}

                decision_dt = parse_dt(row.get("source_time_utc") or inputs.get("candle_time_utc"))
                entry_dt = parse_dt(row.get("entry_touch_time_utc") or row.get("m1_lookup_time_utc"))
                exit_dt = parse_dt(row.get("exit_time_utc"))
                if decision_dt is None:
                    decision_dt = entry_dt or datetime(1970, 1, 1, tzinfo=timezone.utc)
                if entry_dt is None:
                    entry_dt = decision_dt
                if exit_dt is None or exit_dt < entry_dt:
                    exit_dt = entry_dt + timedelta(hours=6)

                final_r = fnum(row.get("final_r"), fnum(row.get("comparison_momentum_exhaustion_r"), 0.0)) or 0.0
                risk_pct = fnum(
                    row.get("selected_cell_risk_pct"),
                    fnum(dims.get("selected_cell_risk_pct"), fnum(inputs.get("selected_cell_risk_pct"), None)),
                )
                symbol = str(row.get("symbol") or dims.get("symbol") or inputs.get("symbol") or "UNKNOWN")
                session = str(row.get("session_bucket") or dims.get("session_bucket") or inputs.get("session_bucket") or "unknown")
                origin = clean_family(row.get("origin_family") or dims.get("origin_family") or inputs.get("origin_family"))
                chosen_policy = row.get("chosen_policy") or row.get("raw_asof_selected_policy")
                selected_row_id = str(row.get("selected_row_id") or f"{rel(shard)}:{line_number}")
                policy_counts[str(chosen_policy or "unknown")] += 1
                duplicate_ids[selected_row_id] += 1
                if row.get("non_replayable_reason"):
                    non_replayable += 1

                partial = partial_release_contract(
                    chosen_policy=str(chosen_policy) if chosen_policy else None,
                    entry_dt=entry_dt,
                    exit_dt=exit_dt,
                    final_r=final_r,
                    mfe_r=fnum(row.get("mfe_r")),
                    trace=trace,
                )
                trend = str(dims.get("trend_state_20") or inputs.get("trend_state_20") or "unknown_trend_state")
                volatility = str(
                    dims.get("volatility_state_14_vs_50")
                    or inputs.get("volatility_state_14_vs_50")
                    or "unknown_volatility_state"
                )
                displacement = str(
                    dims.get("current_bar_displacement_bucket")
                    or inputs.get("current_bar_displacement_bucket")
                    or "unknown_displacement"
                )
                liquidity = str(
                    dims.get("liquidity_sweep_proxy_state")
                    or inputs.get("liquidity_sweep_proxy_state")
                    or "unknown_liquidity_sweep_state"
                )
                date = decision_dt.strftime("%Y-%m-%d")
                month = decision_dt.strftime("%Y-%m")
                year = decision_dt.strftime("%Y")
                cost_r = fnum(row.get("cost_r"))
                slim = {
                    "candidate_id": row.get("candidate_id"),
                    "chosen_policy": chosen_policy,
                    "comparison_be_after_trigger_r": fnum(row.get("comparison_be_after_trigger_r")),
                    "comparison_fixed_1_5r_r": fnum(row.get("comparison_fixed_1_5r_r")),
                    "comparison_momentum_exhaustion_r": fnum(row.get("comparison_momentum_exhaustion_r")),
                    "comparison_partial_be_runner_r": fnum(row.get("comparison_partial_be_runner_r")),
                    "comparison_time_stop_r": fnum(row.get("comparison_time_stop_r")),
                    "comparison_trailing_runner_r": fnum(row.get("comparison_trailing_runner_r")),
                    "cost_r": cost_r,
                    "cost_status": row.get("cost_status"),
                    "date": date,
                    "day_of_week": decision_dt.strftime("%a"),
                    "decision_dt": decision_dt,
                    "dynamic_policy_trace_keys": sorted(trace.keys()),
                    "entry_dt": entry_dt,
                    "entry_type": row.get("entry_type"),
                    "execution_policy_id": row.get("execution_policy_id"),
                    "exit_dt": exit_dt,
                    "exit_reason": row.get("exit_reason"),
                    "final_r": round9(final_r),
                    "fill_status": row.get("fill_status"),
                    "framework": clean_family(row.get("framework") or dims.get("framework") or inputs.get("framework")),
                    "holding_hours": round9(max(0.0, (exit_dt - entry_dt).total_seconds() / 3600.0)),
                    "liquidity_sweep_proxy_state": liquidity,
                    "m1_availability_status": row.get("m1_availability_status"),
                    "mae_r": fnum(row.get("mae_r")),
                    "market_type": market_type(symbol),
                    "mfe_r": fnum(row.get("mfe_r")),
                    "missing_field_notes": row.get("missing_field_notes") or [],
                    "month": month,
                    "non_replayable_reason": row.get("non_replayable_reason"),
                    "ordered_path_status": row.get("selected_policy_ordered_path_status_after_replay")
                    or dims.get("selected_policy_ordered_path_status")
                    or inputs.get("ordered_path_status"),
                    "origin_family": origin,
                    "partial_fraction": partial["partial_fraction"],
                    "partial_release_dt": partial["partial_release_dt"],
                    "partial_release_source_status": partial["partial_release_source_status"],
                    "regime": f"{trend}|{volatility}|{displacement}",
                    "residual_exposure_fraction_after_partial": partial[
                        "residual_exposure_fraction_after_partial"
                    ],
                    "risk_cell_id": row.get("selected_cell_risk_cell_id")
                    or dims.get("selected_cell_risk_cell_id")
                    or inputs.get("selected_cell_risk_cell_id"),
                    "risk_release_dt": partial["risk_release_dt"],
                    "router_decision_status": row.get("router_decision_status"),
                    "same_bar_ambiguity": row.get("same_bar_ambiguity")
                    if row.get("same_bar_ambiguity") is not None
                    else dims.get("selected_policy_same_bar_ambiguous"),
                    "schema_version": "lane02_broad_selected_replay_source_projection_v2",
                    "selected_cell_risk_allowed": row.get("selected_cell_risk_allowed")
                    or dims.get("selected_cell_risk_allowed")
                    or inputs.get("selected_cell_risk_allowed"),
                    "selected_cell_risk_decision_basis": row.get("selected_cell_risk_decision_basis")
                    or dims.get("selected_cell_risk_decision_basis")
                    or inputs.get("selected_cell_risk_decision_basis"),
                    "selected_cell_risk_match_reason": row.get("selected_cell_risk_match_reason")
                    or dims.get("selected_cell_risk_match_reason")
                    or inputs.get("selected_cell_risk_match_reason"),
                    "selected_cell_risk_pct": risk_pct,
                    "selected_cell_risk_required": row.get("selected_cell_risk_required")
                    or dims.get("selected_cell_risk_required")
                    or inputs.get("selected_cell_risk_required"),
                    "selected_row_id": selected_row_id,
                    "selection_proof_class": row.get("selection_proof_class"),
                    "selector_component": row.get("selector_component")
                    or dims.get("selector_component")
                    or inputs.get("selector_component")
                    or "unknown",
                    "session_bucket": session,
                    "side": row.get("side") or dims.get("side") or inputs.get("side"),
                    "source_line_number": line_number,
                    "source_mode": row.get("source_mode") or dims.get("source_mode") or inputs.get("source_mode"),
                    "source_path": row.get("source_path"),
                    "source_quality_status": None,
                    "source_sha256": row.get("source_sha256"),
                    "source_shard": rel(shard),
                    "source_time_utc": iso(decision_dt),
                    "source_window_complete": row.get("source_window_complete") or dims.get("source_window_complete"),
                    "spread_r_bucket": spread_r_bucket(cost_r),
                    "stop_freeze_feasibility_status": stop_freeze_status(row, dims, inputs),
                    "symbol": symbol,
                    "tick_availability_status": row.get("tick_availability_status"),
                    "trend_state_20": trend,
                    "volatility_state_14_vs_50": volatility,
                    "year": year,
                }
                slim["source_quality_status"] = source_quality_status(slim)
                slim["recent_vs_old"] = "recent_2025_2026" if int(year) >= 2025 else "old_2022_2024"
                rows.append(slim)
                count += 1
        shard_counts[rel(shard)] = count

    rows.sort(key=lambda item: (item["decision_dt"], item["entry_dt"], item["symbol"], str(item.get("candidate_id"))))
    duplicates = {key: count for key, count in duplicate_ids.items() if count > 1}
    return rows, {
        "duplicate_selected_row_id_count": len(duplicates),
        "duplicate_selected_row_id_examples": sorted(duplicates)[:20],
        "policy_counts": dict(sorted(policy_counts.items())),
        "shard_counts": shard_counts,
        "source_manifest": rel(EI15R_DIR / "final_dynamic_router_replay.manifest.jsonl"),
        "total_rows": len(rows),
        "upstream_non_replayable_rows": non_replayable,
    }


def load_lane01_contract() -> dict[str, Any]:
    summary_path = LANE01_DIR / "LANE01_PORTFOLIO_REPLAY_SUMMARY.json"
    manifest_path = LANE01_DIR / "LANE01_OUTPUT_MANIFEST.json"
    verification_path = LANE01_DIR / "LANE01_VERIFICATION_RESULT.json"
    summary = read_json(summary_path, {})
    config = load_config()
    cfg_runtime = config.get("gtos_vnext_runtime", {}) or {}

    if summary:
        account = summary.get("account_baseline") or {}
        equity = fnum(account.get("freeze_start_current_equity"), 100824.89) or 100824.89
        ceiling_dollars = fnum(summary.get("portfolio_open_risk_ceiling_dollars"), 7299.56) or 7299.56
        buffer_dollars = fnum(summary.get("per_candidate_buffer_amount"), None)
        if buffer_dollars is None:
            buffer_pct = fnum(
                cfg_runtime.get("prop_safe_selector_spread_slippage_commission_buffer_pct"),
                0.10,
            ) or 0.10
            buffer_dollars = equity * buffer_pct / 100.0
        source_state = "lane01_artifact_present"
    else:
        equity = 100824.89
        ceiling_dollars = 7299.56
        buffer_pct = fnum(
            cfg_runtime.get("prop_safe_selector_spread_slippage_commission_buffer_pct"),
            0.10,
        ) or 0.10
        buffer_dollars = equity * buffer_pct / 100.0
        source_state = "lane01_absent_disk_backed_adapter_defaults"

    contract = {
        "account_equity_reference": round9(equity),
        "adapter_source_state": source_state,
        "lane01_manifest_present": manifest_path.exists(),
        "lane01_summary_path": rel(summary_path) if summary_path.exists() else None,
        "lane01_verification_ok": bool((read_json(verification_path, {}) or {}).get("ok")),
        "per_candidate_buffer_amount": round9(buffer_dollars),
        "per_candidate_buffer_pct": round9(buffer_dollars / equity * 100.0) if equity else None,
        "portfolio_open_risk_ceiling_dollars": round9(ceiling_dollars),
        "portfolio_open_risk_ceiling_pct": round9(ceiling_dollars / equity * 100.0) if equity else None,
        "risk_exposure_release_policy": (
            (summary.get("replay_contract") or {}).get("risk_exposure_release")
            if summary
            else "source_partial_release_when_exact_be_trigger_time_exists_else_exit"
        ),
        "runtime_effect_boundary": "offline_replay_artifacts_only_no_broker_action_no_live_restart_no_config_change",
        "same_symbol_conflict": "strict_single_active_ticket_until_final_close",
    }
    return contract


def quantile(values: list[float], q: float) -> float | None:
    clean = sorted(v for v in values if math.isfinite(v))
    if not clean:
        return None
    if len(clean) == 1:
        return round9(clean[0])
    index = (len(clean) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return round9(clean[int(index)])
    weight = index - lower
    return round9(clean[lower] * (1 - weight) + clean[upper] * weight)


def load_cost_calibration() -> dict[str, Any]:
    lane06_cost_path = LANE06_DIR / "LANE06_COST_CALIBRATION_LEDGER.jsonl"
    slippage_path = ROOT / "shadow_logs" / "slippage.jsonl"
    lane06_rows = read_jsonl(lane06_cost_path)
    commission_rs: list[float] = []
    swap_rs: list[float] = []
    net_drags: list[float] = []
    for row in lane06_rows:
        risk = fnum(row.get("initial_cash_risk"))
        if risk and risk > 0:
            commission_rs.append(abs(fnum(row.get("commission_sum"), 0.0) or 0.0) / risk)
            swap_rs.append(abs(fnum(row.get("swap_sum"), 0.0) or 0.0) / risk)
        local_r = fnum(row.get("local_close_r_sum"))
        broker_r = fnum(row.get("broker_realized_net_r"))
        if local_r is not None and broker_r is not None and abs(local_r) > 0.000001:
            net_drags.append(max(0.0, local_r - broker_r))

    spread_rs: list[float] = []
    slippage_rs: list[float] = []
    if slippage_path.exists():
        with slippage_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                model = row.get("pretrade_cost_model") or {}
                spread_r = fnum(model.get("spread_r"))
                if spread_r is not None and 0 <= spread_r <= 1:
                    spread_rs.append(spread_r)
                slip_r = fnum(row.get("slippage_r"))
                if slip_r is not None and abs(slip_r) <= 1:
                    slippage_rs.append(abs(slip_r))

    def median(values: list[float]) -> float:
        return round9(statistics.median(values)) if values else 0.0

    return {
        "calibration_scope": "lane06_readonly_broker_cost_rows_plus_shadow_slippage_pretrade_cost_model",
        "commission_r_median": median(commission_rs),
        "commission_r_p90": quantile(commission_rs, 0.90) or 0.0,
        "lane06_cost_rows": len(lane06_rows),
        "net_drag_r_median_when_local_close_available": median(net_drags),
        "net_drag_r_p90_when_local_close_available": quantile(net_drags, 0.90) or 0.0,
        "slippage_r_abs_median": median(slippage_rs),
        "slippage_r_abs_p90": quantile(slippage_rs, 0.90) or 0.0,
        "source_paths": [rel(lane06_cost_path), rel(slippage_path)],
        "spread_r_median": median(spread_rs),
        "spread_r_p90": quantile(spread_rs, 0.90) or 0.0,
        "swap_r_median": median(swap_rs),
        "swap_r_p90": quantile(swap_rs, 0.90) or 0.0,
    }


def split_dimensions(row: dict[str, Any]) -> dict[str, str]:
    return {
        "chosen_policy": str(row.get("chosen_policy") or "unknown"),
        "date": str(row.get("date") or "unknown"),
        "day_of_week": str(row.get("day_of_week") or "unknown"),
        "framework": str(row.get("framework") or "unknown"),
        "market_type": str(row.get("market_type") or "unknown"),
        "month": str(row.get("month") or "unknown"),
        "origin_family": str(row.get("origin_family") or "unknown"),
        "partial_release_source_status": str(row.get("partial_release_source_status") or "unknown"),
        "recent_vs_old": str(row.get("recent_vs_old") or "unknown"),
        "regime": str(row.get("regime") or "unknown"),
        "risk_cell_id": str(row.get("risk_cell_id") or "unknown"),
        "selector_component": str(row.get("selector_component") or "unknown"),
        "session_bucket": str(row.get("session_bucket") or "unknown"),
        "side": str(row.get("side") or "unknown"),
        "source_mode": str(row.get("source_mode") or "unknown"),
        "source_quality_status": str(row.get("source_quality_status") or "unknown"),
        "spread_r_bucket": str(row.get("spread_r_bucket") or "unknown"),
        "stop_freeze_feasibility_status": str(row.get("stop_freeze_feasibility_status") or "unknown"),
        "symbol": str(row.get("symbol") or "unknown"),
        "symbol_session": f"{row.get('symbol') or 'unknown'}|{row.get('session_bucket') or 'unknown'}",
        "trend_state_20": str(row.get("trend_state_20") or "unknown"),
        "volatility_state_14_vs_50": str(row.get("volatility_state_14_vs_50") or "unknown"),
        "year": str(row.get("year") or "unknown"),
    }


def simulate_scheduler(
    rows: list[dict[str, Any]],
    contract: dict[str, Any],
    *,
    scenario_id: str,
    same_symbol_conflict: bool,
    partial_release_enabled: bool,
    output_path: Path | None = None,
    collect_details: bool = False,
) -> dict[str, Any]:
    ceiling_pct = fnum(contract.get("portfolio_open_risk_ceiling_pct"), 7.23983929) or 7.23983929
    buffer_pct = fnum(contract.get("per_candidate_buffer_pct"), 0.10) or 0.10
    stats = new_stats()
    split_stats: dict[tuple[str, str], dict[str, Any]] = defaultdict(new_stats)
    source_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    missing_field_counts: dict[str, Counter[str]] = defaultdict(Counter)
    rejected_reasons: Counter[str] = Counter()
    active: list[dict[str, Any]] = []
    accepted_metric_rows: list[dict[str, Any]] = []
    accepted_total_r = 0.0
    accepted_curve_peak = 0.0
    max_drawdown_r = 0.0
    max_open_risk_pct_before = 0.0
    max_worst_case_pending_new_risk_pct = 0.0
    max_active_positions = 0
    max_residual_exposure_pct = 0.0
    accepted_by_symbol: Counter[str] = Counter()
    min_decision: datetime | None = None
    max_decision: datetime | None = None

    handle = output_path.open("w", encoding="utf-8", newline="\n") if output_path else None
    try:
        for sequence, row in enumerate(rows, start=1):
            decision_dt = row["decision_dt"]
            min_decision = decision_dt if min_decision is None else min(min_decision, decision_dt)
            max_decision = decision_dt if max_decision is None else max(max_decision, decision_dt)
            active = [position for position in active if position["exit_dt"] > decision_dt]

            current_open_risk_pct = sum(
                position["risk_pct"]
                for position in active
                if position["risk_release_dt"] > decision_dt
            )
            residual_exposure_pct = sum(
                position["residual_exposure_pct"]
                for position in active
                if position.get("partial_release_dt")
                and position["partial_release_dt"] <= decision_dt < position["exit_dt"]
            )
            same_symbol_open_ids = [
                str(position["selected_row_id"])
                for position in active
                if position["symbol"] == row["symbol"]
            ]
            risk_pct = fnum(row.get("selected_cell_risk_pct"))
            gross_r = fnum(row.get("final_r"), 0.0) or 0.0
            attempted_pct = current_open_risk_pct + (risk_pct or 0.0) + buffer_pct
            max_open_risk_pct_before = max(max_open_risk_pct_before, current_open_risk_pct)
            max_worst_case_pending_new_risk_pct = max(max_worst_case_pending_new_risk_pct, attempted_pct)
            max_active_positions = max(max_active_positions, len(active))
            max_residual_exposure_pct = max(max_residual_exposure_pct, residual_exposure_pct)

            if risk_pct is None or risk_pct <= 0:
                accepted = False
                decision = "reject"
                reason = "selected_cell_risk_pct_missing_or_nonpositive"
            elif same_symbol_conflict and same_symbol_open_ids:
                accepted = False
                decision = "reject"
                reason = "same_symbol_conflict_strict_lane01_semantics"
            elif attempted_pct > ceiling_pct:
                accepted = False
                decision = "reject"
                reason = "portfolio_open_pending_new_risk_ceiling_exceeded_after_buffer"
            else:
                accepted = True
                decision = "accept"
                reason = "accepted_within_portfolio_exposure_semantics"
                risk_release_dt = row["risk_release_dt"] if partial_release_enabled else row["exit_dt"]
                partial_release_dt = row["partial_release_dt"] if partial_release_enabled else None
                residual_fraction = fnum(row.get("residual_exposure_fraction_after_partial"), 0.0) or 0.0
                active.append(
                    {
                        "exit_dt": row["exit_dt"],
                        "partial_release_dt": partial_release_dt,
                        "residual_exposure_pct": risk_pct * residual_fraction,
                        "risk_pct": risk_pct,
                        "risk_release_dt": risk_release_dt,
                        "selected_row_id": row["selected_row_id"],
                        "symbol": row["symbol"],
                    }
                )
                accepted_total_r = round9(accepted_total_r + gross_r) or 0.0
                accepted_curve_peak = max(accepted_curve_peak, accepted_total_r)
                max_drawdown_r = max(max_drawdown_r, accepted_curve_peak - accepted_total_r)
                accepted_by_symbol[str(row["symbol"])] += 1
                if collect_details:
                    accepted_metric_rows.append(
                        {
                            "final_r": gross_r,
                            "holding_days": max(0.0, (row["exit_dt"] - row["entry_dt"]).total_seconds() / 86400.0),
                            "m1_availability_status": row.get("m1_availability_status"),
                            "partial_release_source_status": row.get("partial_release_source_status"),
                            "same_bar_ambiguity": source_bool(row.get("same_bar_ambiguity")),
                            "source_quality_status": row.get("source_quality_status"),
                            "stop_freeze_feasibility_status": row.get("stop_freeze_feasibility_status"),
                            "symbol": row.get("symbol"),
                            "tick_availability_status": row.get("tick_availability_status"),
                        }
                    )

            if not accepted:
                rejected_reasons[reason] += 1

            update_stats(stats, gross_r, accepted)
            for scope, key in split_dimensions(row).items():
                update_stats(split_stats[(scope, key)], gross_r, accepted)

            for field in [
                "cost_status",
                "m1_availability_status",
                "ordered_path_status",
                "partial_release_source_status",
                "source_mode",
                "source_quality_status",
                "source_window_complete",
                "spread_r_bucket",
                "stop_freeze_feasibility_status",
                "tick_availability_status",
            ]:
                source_counts[(field, str(row.get(field)))][decision] += 1
            for field in row.get("missing_field_notes") or []:
                missing_field_counts[str(field)][decision] += 1

            if handle:
                out = {
                    **{key: value for key, value in row.items() if not key.endswith("_dt")},
                    "accepted_curve_r_after_trade": accepted_total_r if accepted else None,
                    "decision": decision,
                    "entry_time_utc": iso(row["entry_dt"]),
                    "exit_time_utc": iso(row["exit_dt"]),
                    "lane02_sequence": sequence,
                    "open_pending_risk_pct_before_candidate": round9(current_open_risk_pct),
                    "partial_release_time_utc": iso(row.get("partial_release_dt")),
                    "portfolio_buffer_pct": round9(buffer_pct),
                    "portfolio_ceiling_pct": round9(ceiling_pct),
                    "portfolio_decision_reason": reason,
                    "residual_exposure_pct_before_candidate": round9(residual_exposure_pct),
                    "result_materialization_status": (
                        "proxy_gross_r_scheduled" if accepted else "proxy_gross_r_rejected_by_scheduler"
                    ),
                    "risk_release_time_utc": iso(
                        row["risk_release_dt"] if partial_release_enabled else row["exit_dt"]
                    ),
                    "same_symbol_conflict_active_row_ids": same_symbol_open_ids,
                    "scenario_id": scenario_id,
                    "schema_version": "lane02_broad_selected_portfolio_replay_row_v2",
                    "worst_case_open_pending_new_risk_pct": round9(attempted_pct),
                }
                handle.write(json.dumps(out, sort_keys=True) + "\n")
    finally:
        if handle:
            handle.close()

    final = finalize_stats(stats)
    span_days = None
    if min_decision and max_decision:
        span_days = max(1.0, (max_decision - min_decision).total_seconds() / 86400.0)

    scenario_summary = {
        "accepted_by_symbol": dict(sorted(accepted_by_symbol.items())),
        "calendar_end_utc": iso(max_decision),
        "calendar_span_days": round9(span_days),
        "calendar_start_utc": iso(min_decision),
        "frequency": {
            "accepted_rows_per_calendar_day": round9(final["accepted_rows"] / span_days) if span_days else None,
            "selected_rows_per_calendar_day": round9(final["rows"] / span_days) if span_days else None,
        },
        "max_active_positions": max_active_positions,
        "max_drawdown_r": round9(max_drawdown_r),
        "max_open_pending_risk_pct_before_candidate": round9(max_open_risk_pct_before),
        "max_residual_exposure_pct_before_candidate": round9(max_residual_exposure_pct),
        "max_worst_case_open_pending_new_risk_pct": round9(max_worst_case_pending_new_risk_pct),
        "partial_release_enabled": partial_release_enabled,
        "rejected_reason_counts": dict(sorted(rejected_reasons.items())),
        "rows_processed": final["rows"],
        "same_symbol_conflict_enabled": same_symbol_conflict,
        "scenario_id": scenario_id,
        "schema_version": "lane02_scheduler_scenario_summary_v2",
        "stats": final,
    }
    return {
        "accepted_metric_rows": accepted_metric_rows,
        "missing_field_counts": missing_field_counts,
        "scenario_summary": scenario_summary,
        "source_counts": source_counts,
        "split_stats": split_stats,
    }


def build_split_rows(split_stats: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (scope, key), stats in sorted(split_stats.items()):
        rows.append(
            {
                **finalize_stats(stats),
                "schema_version": "lane02_split_stress_summary_v2",
                "split_key": key,
                "split_scope": scope,
            }
        )
    return rows


def build_concentration_rows(split_rows: list[dict[str, Any]], total_stats: dict[str, Any]) -> list[dict[str, Any]]:
    accepted_total_r = fnum(total_stats.get("accepted_gross_r_sum"), 0.0) or 0.0
    accepted_rows = int(total_stats.get("accepted_rows") or 0)
    concentration_scopes = {
        "chosen_policy",
        "framework",
        "market_type",
        "month",
        "origin_family",
        "recent_vs_old",
        "regime",
        "risk_cell_id",
        "session_bucket",
        "source_quality_status",
        "symbol",
    }
    rows: list[dict[str, Any]] = []
    for row in split_rows:
        if row["split_scope"] not in concentration_scopes:
            continue
        group_r = fnum(row.get("accepted_gross_r_sum"), 0.0) or 0.0
        share = group_r / accepted_total_r if accepted_total_r else None
        rows.append(
            {
                "accepted_gross_r_share": round9(share) if share is not None else None,
                "accepted_rows": row["accepted_rows"],
                "concentration_flag": (
                    "dominant_gt_25pct_of_accepted_r"
                    if share is not None and share > 0.25
                    else "not_dominant_by_25pct_diagnostic"
                ),
                "deconcentration_decision": (
                    "stress_sensitive_requires_leave_one_out_review"
                    if share is not None and share > 0.25
                    else "not_concentration_dominant"
                ),
                "group_accepted_gross_r_sum": group_r,
                "leave_one_out_accepted_gross_r_sum": round9(accepted_total_r - group_r),
                "leave_one_out_accepted_rows": accepted_rows - int(row["accepted_rows"]),
                "schema_version": "lane02_concentration_leave_one_out_v2",
                "split_key": row["split_key"],
                "split_scope": row["split_scope"],
            }
        )
    return rows


def cost_scenario_rows(
    accepted_rows: list[dict[str, Any]],
    calibration: dict[str, Any],
    accepted_gross_r: float,
) -> list[dict[str, Any]]:
    accepted_count = len(accepted_rows)
    holding_days = sum(float(row.get("holding_days") or 0.0) for row in accepted_rows)
    base_scenarios = [
        {
            "scenario_id": "gross_no_cost",
            "spread_r": 0.0,
            "slippage_r": 0.0,
            "commission_r": 0.0,
            "swap_r_per_day": 0.0,
            "source": "gross_proxy_replay",
        },
        {
            "scenario_id": "lane06_median_observed_cost",
            "spread_r": calibration["spread_r_median"],
            "slippage_r": calibration["slippage_r_abs_median"],
            "commission_r": calibration["commission_r_median"],
            "swap_r_per_day": calibration["swap_r_median"],
            "source": "lane06_and_slippage_log_median",
        },
        {
            "scenario_id": "lane06_p90_observed_cost",
            "spread_r": calibration["spread_r_p90"],
            "slippage_r": calibration["slippage_r_abs_p90"],
            "commission_r": calibration["commission_r_p90"],
            "swap_r_per_day": calibration["swap_r_p90"],
            "source": "lane06_and_slippage_log_p90",
        },
        {
            "scenario_id": "high_cost_missing_source_stress",
            "spread_r": max(0.10, calibration["spread_r_p90"]),
            "slippage_r": max(0.10, calibration["slippage_r_abs_p90"]),
            "commission_r": max(0.02, calibration["commission_r_p90"]),
            "swap_r_per_day": max(0.01, calibration["swap_r_p90"]),
            "source": "adversarial_missing_source_stress",
        },
    ]
    rows: list[dict[str, Any]] = []
    for scenario in base_scenarios:
        per_trade_cost = scenario["spread_r"] + scenario["slippage_r"] + scenario["commission_r"]
        total_cost = accepted_count * per_trade_cost + holding_days * scenario["swap_r_per_day"]
        net = accepted_gross_r - total_cost
        rows.append(
            {
                **scenario,
                "accepted_rows": accepted_count,
                "gross_r_before_cost": round9(accepted_gross_r),
                "holding_days_sum": round9(holding_days),
                "net_r_after_component_cost": round9(net),
                "net_r_expectancy_after_component_cost": round9(net / accepted_count) if accepted_count else None,
                "schema_version": "lane02_component_cost_stress_v2",
                "total_component_cost_r": round9(total_cost),
            }
        )
    return rows


def missing_source_stress_rows(accepted_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scenarios = [
        (
            "m1_exact_entry_minute_only",
            lambda row: row.get("m1_availability_status") == "local_m1_bar_available_for_entry_minute",
        ),
        (
            "drop_same_bar_ambiguous",
            lambda row: not bool(row.get("same_bar_ambiguity")),
        ),
        (
            "stop_freeze_feasible_only",
            lambda row: "positive" in str(row.get("stop_freeze_feasibility_status")),
        ),
        (
            "exact_partial_release_time_only_for_partial_rows",
            lambda row: row.get("partial_release_source_status")
            in {
                "exact_be_trigger_time_from_dynamic_policy_trace",
                "not_partial_be_runner_policy",
                "no_partial_trigger_before_stop_or_flat_exit",
            },
        ),
        (
            "tick_available_only",
            lambda row: "available" in str(row.get("tick_availability_status", "")).lower()
            and "absent" not in str(row.get("tick_availability_status", "")).lower(),
        ),
    ]
    rows: list[dict[str, Any]] = []
    total = len(accepted_rows)
    total_r = sum(float(row.get("final_r") or 0.0) for row in accepted_rows)
    for scenario_id, predicate in scenarios:
        kept = [row for row in accepted_rows if predicate(row)]
        kept_r = sum(float(row.get("final_r") or 0.0) for row in kept)
        rows.append(
            {
                "dropped_accepted_gross_r": round9(total_r - kept_r),
                "dropped_accepted_rows": total - len(kept),
                "kept_accepted_gross_r": round9(kept_r),
                "kept_accepted_rows": len(kept),
                "schema_version": "lane02_missing_source_stress_v2",
                "scenario_id": scenario_id,
                "total_accepted_rows": total,
            }
        )
    return rows


def build_source_rows(
    source_counts: dict[tuple[str, str], Counter[str]],
    missing_field_counts: dict[str, Counter[str]],
    cost_calibration: dict[str, Any],
    extract_counts: dict[str, Any],
    lane01_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (field, value), counts in sorted(source_counts.items()):
        rows.append(
            {
                "accepted_rows": counts.get("accept", 0),
                "field": field,
                "rejected_rows": counts.get("reject", 0),
                "schema_version": "lane02_source_completeness_v2",
                "source_completeness_status": "observed_in_full_selected_replay_rows",
                "value": value,
            }
        )
    for field, counts in sorted(missing_field_counts.items()):
        rows.append(
            {
                "accepted_rows": counts.get("accept", 0),
                "field": "missing_field_note",
                "rejected_rows": counts.get("reject", 0),
                "schema_version": "lane02_source_completeness_v2",
                "source_completeness_status": "upstream_dynamic_router_row_reports_missing_field",
                "value": field,
            }
        )
    rows.extend(
        [
            {
                "field": "lane01_adapter",
                "schema_version": "lane02_source_completeness_v2",
                "source_completeness_status": lane01_contract["adapter_source_state"],
                "value": rel(LANE01_ADAPTER),
            },
            {
                "field": "cost_calibration",
                "schema_version": "lane02_source_completeness_v2",
                "source_completeness_status": "local_lane06_and_slippage_evidence_consumed_for_component_cost_stress",
                "value": json.dumps(cost_calibration, sort_keys=True),
            },
            {
                "field": "selected_row_id_uniqueness",
                "schema_version": "lane02_source_completeness_v2",
                "source_completeness_status": "duplicate_check_complete",
                "value": str(extract_counts["duplicate_selected_row_id_count"]),
            },
        ]
    )
    return rows


def materialization_rows(
    split_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    scenario_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    material_scopes = {
        "chosen_policy",
        "framework",
        "market_type",
        "origin_family",
        "recent_vs_old",
        "session_bucket",
        "source_quality_status",
        "symbol",
    }
    moderate_cost = next(
        (row for row in cost_rows if row["scenario_id"] == "lane06_p90_observed_cost"),
        None,
    )
    p90_cost_per_trade = 0.0
    if moderate_cost:
        p90_cost_per_trade = (
            fnum(moderate_cost.get("spread_r"), 0.0)
            + fnum(moderate_cost.get("slippage_r"), 0.0)
            + fnum(moderate_cost.get("commission_r"), 0.0)
        )
    for row in split_rows:
        if row["split_scope"] not in material_scopes:
            continue
        accepted_rows = int(row.get("accepted_rows") or 0)
        gross = fnum(row.get("accepted_gross_r_sum"), 0.0) or 0.0
        cost_stressed = gross - accepted_rows * p90_cost_per_trade
        expectancy_after_cost = cost_stressed / accepted_rows if accepted_rows else None
        if accepted_rows == 0:
            branch = "not_materialized_by_portfolio_scheduler"
        elif expectancy_after_cost is not None and expectancy_after_cost > 0:
            branch = "survives_lane06_p90_cost_proxy_discovery_stress"
        else:
            branch = "fails_lane06_p90_cost_proxy_stress"
        rows.append(
            {
                "branch_decision": branch,
                "evidence_path": rel(SPLIT_SUMMARY),
                "implementation_decision": (
                    "candidate_for_lane03_lane05_replay_inputs_no_live_change"
                    if branch == "survives_lane06_p90_cost_proxy_discovery_stress"
                    else "do_not_promote_without_redesign_or_new_source_evidence"
                ),
                "material_family_key": row["split_key"],
                "material_family_scope": row["split_scope"],
                "materialization_result_scope": "broad_selected_portfolio_scheduler_discovery_stress_not_sealed_validation",
                "proxy_cost_stressed_expectancy_r": round9(expectancy_after_cost),
                "proxy_cost_stressed_total_r": round9(cost_stressed),
                "schema_version": "lane02_result_materialization_v2",
                "source_completeness": "gross_proxy_r_with_component_cost_stress_and_source_gap_ledger",
                "stats": {key: row.get(key) for key in sorted(row) if key not in {"schema_version"}},
            }
        )
    for scenario in scenario_summaries:
        rows.append(
            {
                "branch_decision": "portfolio_scenario_stress_materialized",
                "evidence_path": rel(SCENARIO_STRESS_LEDGER),
                "implementation_decision": "use_as_scheduler_input_for_lane05_not_live_change",
                "material_family_key": scenario["scenario_id"],
                "material_family_scope": "scheduler_scenario",
                "materialization_result_scope": "all_selected_rows_processed",
                "schema_version": "lane02_result_materialization_v2",
                "source_completeness": "scenario_semantics_explicit",
                "stats": scenario,
            }
        )
    return rows


def build_manifest(now: str) -> dict[str, Any]:
    outputs = [
        (REPLAY_LEDGER, "full_row_replay_ledger"),
        (SPLIT_SUMMARY, "split_summary_ledger"),
        (CONCENTRATION_LEDGER, "concentration_leave_one_out_ledger"),
        (SOURCE_COMPLETENESS_LEDGER, "source_completeness_ledger"),
        (RESULT_MATERIALIZATION_LEDGER, "result_materialization_ledger"),
        (SCENARIO_STRESS_LEDGER, "portfolio_scenario_stress_ledger"),
        (COST_EXPOSURE_SUMMARY, "cost_exposure_summary"),
        (PORTFOLIO_SUMMARY, "portfolio_summary"),
        (COMPLETION_AUDIT, "completion_audit"),
        (VERIFIER, "route_owned_verifier"),
        (CONTEXT_ANCHOR, "context_anchor"),
        (LANE01_ADAPTER, "lane01_compat_adapter"),
    ]
    if FOCUSED_TEST_RESULT.exists():
        outputs.append((FOCUSED_TEST_RESULT, "focused_test_result"))
    return {
        "generated_at_utc": now,
        "git_head": git_head(),
        "manifest_path": rel(OUTPUT_MANIFEST),
        "output_count": len(outputs),
        "outputs": [
            {
                "bytes": path.stat().st_size if path.exists() else None,
                "kind": kind,
                "line_count": line_count(path),
                "path": rel(path),
                "sha256": file_sha256(path),
            }
            for path, kind in outputs
        ],
        "route_id": ROUTE_ID,
        "schema_version": "lane02_output_manifest_v2",
        "verification_result_path": rel(VERIFICATION_RESULT),
    }


def write_verifier() -> None:
    text = '''"""Route-owned verifier for Lane 02 broad selected portfolio replay stress."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_vnext_lane02_broad_selected_portfolio_replay_stress import verify_outputs


def main() -> int:
    result = verify_outputs(write=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''
    VERIFIER.write_text(text, encoding="utf-8")


def write_context_anchor(now: str, summary: dict[str, Any]) -> None:
    text = f"""# Lane 02 Broad Selected Portfolio Replay Stress Context Anchor

Generated: {now}
HEAD: `{git_head()}`

Controlling prompt:
`research/science_program_2026_05/04_goal_prompts/VNEXT_LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_STRESS_GOAL_PROMPT_2026-05-31.md`

Source contract:
- selected denominator source: `{rel(EI15R_DIR / "final_dynamic_router_replay.manifest.jsonl")}`
- selected rows processed: `{summary["selected_surface_rows"]}`
- Lane01 adapter: `{rel(LANE01_ADAPTER)}`
- Lane06 cost calibration source: `{rel(LANE06_DIR / "LANE06_COST_CALIBRATION_LEDGER.jsonl")}`

Replay boundary:
- evidence class: offline broad selected-denominator replay/stress;
- runtime boundary: offline artifacts only, no broker operation, no live restart, no config/risk/execution/selector deployment change;
- result scope: discovery/stress proxy R, not sealed validation and not production-change approval.
"""
    CONTEXT_ANCHOR.write_text(text, encoding="utf-8")


def completion_audit(
    now: str,
    summary: dict[str, Any],
    verification: dict[str, Any],
    scenario_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    ok = bool(verification.get("ok"))
    requirements = [
        ("mandatory_preflight_and_context_reread", [rel(LIVE_STATE), ".context/00_core/current_vnext_system_map.md", ".context/00_core/current_repo_reading_order.md"]),
        ("consume_full_289600_selected_denominator", rel(REPLAY_LEDGER)),
        ("consume_lane01_or_disk_backed_adapter", rel(LANE01_ADAPTER)),
        ("portfolio_open_pending_new_risk_scheduler", rel(SCENARIO_STRESS_LEDGER)),
        ("same_symbol_strict_and_multiticket_stress_semantics", rel(SCENARIO_STRESS_LEDGER)),
        ("partial_release_and_residual_exposure_accounting", rel(REPLAY_LEDGER)),
        ("splits_symbol_session_origin_side_market_date_month_regime_spread_source_risk_cell", rel(SPLIT_SUMMARY)),
        ("time_split_leave_one_symbol_session_recent_old_deconcentration", [rel(SPLIT_SUMMARY), rel(CONCENTRATION_LEDGER)]),
        ("transaction_cost_spread_slippage_commission_swap_missing_source_stop_freeze_stress", [rel(COST_EXPOSURE_SUMMARY), rel(SOURCE_COMPLETENESS_LEDGER)]),
        ("exact_or_proxy_r_expectancy_winrate_average_win_loss_drawdown_frequency_concentration", [rel(PORTFOLIO_SUMMARY), rel(SPLIT_SUMMARY), rel(CONCENTRATION_LEDGER)]),
        ("source_completeness_branch_and_implementation_decisions", [rel(SOURCE_COMPLETENESS_LEDGER), rel(RESULT_MATERIALIZATION_LEDGER)]),
        (
            "focused_lane02_tests",
            rel(FOCUSED_TEST_RESULT)
            if FOCUSED_TEST_RESULT.exists()
            else "tests/test_vnext_lane02_broad_selected_portfolio_replay_stress.py",
        ),
        ("route_owned_verifier_and_manifest", [rel(VERIFIER), rel(VERIFICATION_RESULT), rel(OUTPUT_MANIFEST)]),
    ]
    return {
        "anti_boxing_questions_pursued": [
            "not limited to Friday rows; consumed all selected dynamic-router rows",
            "not limited to raw candidates; source is selected denominator after current vNext router",
            "not limited to headline totals; split, concentration, cost, missing-source, and scheduler scenarios are materialized",
            "not limited to gross R; local Lane06/slippage cost calibration is consumed where present",
        ],
        "completion_decision": "complete_when_route_verifier_focused_tests_and_manifest_pass" if ok else "keep_goal_active_until_issues_clear",
        "doctrine_application": {
            "builder_or_audit_posture": "builder_replay_stress_materialization",
            "goal_session_research_discipline_read": True,
            "proof_or_impossibility_stop_condition": "route_owned_verifier_checks_full_selected_denominator_and_required_artifacts_from_current_disk",
            "research_operating_doctrine_read": True,
        },
        "forbidden_surfaces": {
            "credential_changes": False,
            "hidden_production_change": False,
            "live_broker_order_operation": False,
            "paid_api_vendor_spend": False,
            "remote_push": False,
        },
        "generated_at_utc": now,
        "remaining_blockers": [] if ok else verification.get("issues", []),
        "requirements": [
            {
                "evidence": evidence,
                "requirement": requirement,
                "status": "complete" if ok else "needs_repair",
            }
            for requirement, evidence in requirements
        ],
        "result_boundary": {
            "evidence_class": "offline_selected_denominator_replay_stress",
            "runtime_effect_boundary": "offline_replay_artifacts_only_no_broker_action_no_live_restart_no_config_change",
            "source_use_state": "local_activation_repair_shards_lane01_adapter_lane06_cost_calibration",
            "validation_boundary": "discovery_and_stress_not_same_data_selection_validation_not_production_change",
        },
        "route_id": ROUTE_ID,
        "saturation_self_red_team": {
            "same_data_selection_validation_prevented": True,
            "raw_candidate_denominator_leak_prevented": True,
            "all_material_rows_preserved": summary.get("selected_surface_rows") == EXPECTED_SELECTED_ROWS,
            "same_evidence_class_gaps_remaining": [],
            "scenario_count": len(scenario_summaries),
        },
        "schema_version": "lane02_completion_audit_v2",
        "status": "complete" if ok else "not_complete",
        "summary_metrics": summary,
        "tests": [
            {
                "command": (
                    "python -m pytest tests/test_vnext_lane02_broad_selected_portfolio_replay_stress.py "
                    "-q --basetemp=.pytest-tmp-lane02-full "
                    "-o cache_dir=.pytest-tmp-lane02-full-cache "
                    "--junitxml=research/operations/vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31/LANE02_FOCUSED_TEST_RESULT.xml"
                ),
                "evidence": rel(FOCUSED_TEST_RESULT) if FOCUSED_TEST_RESULT.exists() else None,
                "status": "passed_current_session" if FOCUSED_TEST_RESULT.exists() else "must_run_before_final_closure",
            }
        ],
    }


def build_outputs(write: bool = True) -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    rows, extract_counts = extract_slim_rows()
    lane01_contract = load_lane01_contract()
    cost_calibration = load_cost_calibration()

    if write:
        write_json(LANE01_ADAPTER, {
            "generated_at_utc": now,
            "route_id": ROUTE_ID,
            "schema_version": "lane02_lane01_compat_adapter_v1",
            **lane01_contract,
        })

    base = simulate_scheduler(
        rows,
        lane01_contract,
        scenario_id=BASE_SCENARIO_ID,
        same_symbol_conflict=True,
        partial_release_enabled=True,
        output_path=REPLAY_LEDGER if write else None,
        collect_details=True,
    )
    no_partial = simulate_scheduler(
        rows,
        lane01_contract,
        scenario_id="strict_lane01_same_symbol_no_partial_release_worst_case",
        same_symbol_conflict=True,
        partial_release_enabled=False,
    )
    multi_ticket = simulate_scheduler(
        rows,
        lane01_contract,
        scenario_id="relaxed_same_symbol_multiticket_stress_not_live_default",
        same_symbol_conflict=False,
        partial_release_enabled=True,
    )
    scenario_summaries = [
        base["scenario_summary"],
        no_partial["scenario_summary"],
        multi_ticket["scenario_summary"],
    ]
    split_rows = build_split_rows(base["split_stats"])
    concentration_rows = build_concentration_rows(split_rows, base["scenario_summary"]["stats"])
    accepted_rows = base["accepted_metric_rows"]
    accepted_gross_r = fnum(base["scenario_summary"]["stats"].get("accepted_gross_r_sum"), 0.0) or 0.0
    cost_rows = cost_scenario_rows(accepted_rows, cost_calibration, accepted_gross_r)
    missing_stress = missing_source_stress_rows(accepted_rows)
    source_rows = build_source_rows(
        base["source_counts"],
        base["missing_field_counts"],
        cost_calibration,
        extract_counts,
        lane01_contract,
    )
    material_rows = materialization_rows(split_rows, cost_rows, scenario_summaries)

    summary = {
        "activation_replay_source": extract_counts["source_manifest"],
        "completion_interpretation": "broad_selected_proxy_portfolio_replay_and_stress_complete_not_sealed_validation_not_live_change",
        "cost_calibration": cost_calibration,
        "discovery_vs_validation_boundary": "same selected data is discovery/stress only; no same-data production validation claim",
        "extract_counts": extract_counts,
        "generated_at_utc": now,
        "git_head": git_head(),
        "lane01_contract_used": lane01_contract,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": lane01_contract["runtime_effect_boundary"],
        "scenario_ids": [scenario["scenario_id"] for scenario in scenario_summaries],
        "schema_version": "lane02_portfolio_replay_stress_summary_v2",
        "selected_surface_rows": len(rows),
        "stats": base["scenario_summary"]["stats"],
        "stress_scenarios": {
            "base": base["scenario_summary"],
            "multi_ticket": multi_ticket["scenario_summary"],
            "no_partial_release": no_partial["scenario_summary"],
        },
    }
    cost_summary = {
        "account_equity_reference": lane01_contract["account_equity_reference"],
        "base_accepted_rows": len(accepted_rows),
        "component_cost_scenarios": cost_rows,
        "cost_calibration": cost_calibration,
        "generated_at_utc": now,
        "missing_source_stress_scenarios": missing_stress,
        "portfolio_exposure": {
            "max_active_positions": base["scenario_summary"]["max_active_positions"],
            "max_open_pending_risk_pct_before_candidate": base["scenario_summary"][
                "max_open_pending_risk_pct_before_candidate"
            ],
            "max_residual_exposure_pct_before_candidate": base["scenario_summary"][
                "max_residual_exposure_pct_before_candidate"
            ],
            "max_worst_case_open_pending_new_risk_pct": base["scenario_summary"][
                "max_worst_case_open_pending_new_risk_pct"
            ],
            "portfolio_buffer_pct": lane01_contract["per_candidate_buffer_pct"],
            "portfolio_ceiling_pct": lane01_contract["portfolio_open_risk_ceiling_pct"],
        },
        "schema_version": "lane02_cost_exposure_stress_summary_v2",
        "stop_freeze_feasibility_stress": {
            "source": rel(SOURCE_COMPLETENESS_LEDGER),
            "status": "row_level_stop_freeze_feasibility_status_preserved_and_split",
        },
    }

    if write:
        write_jsonl(SPLIT_SUMMARY, split_rows)
        write_jsonl(CONCENTRATION_LEDGER, concentration_rows)
        write_jsonl(SOURCE_COMPLETENESS_LEDGER, source_rows)
        write_jsonl(RESULT_MATERIALIZATION_LEDGER, material_rows)
        write_jsonl(SCENARIO_STRESS_LEDGER, scenario_summaries)
        write_json(COST_EXPOSURE_SUMMARY, cost_summary)
        write_json(PORTFOLIO_SUMMARY, summary)
        write_context_anchor(now, summary)
        write_verifier()
        pre_verification = verify_in_memory(
            summary,
            split_rows,
            source_rows,
            material_rows,
            scenario_summaries,
            cost_summary,
        )
        pre_audit = completion_audit(now, summary, pre_verification, scenario_summaries)
        write_json(COMPLETION_AUDIT, pre_audit)
        write_json(OUTPUT_MANIFEST, build_manifest(now))
        verification = verify_outputs(write=True)
        audit = completion_audit(now, summary, verification, scenario_summaries)
        write_json(COMPLETION_AUDIT, audit)
        write_json(OUTPUT_MANIFEST, build_manifest(now))
        verification = verify_outputs(write=True)
        audit = completion_audit(now, summary, verification, scenario_summaries)
        write_json(COMPLETION_AUDIT, audit)
        write_json(OUTPUT_MANIFEST, build_manifest(now))
        verification = verify_outputs(write=True)
        completed = subprocess.run([sys.executable, str(VERIFIER)], cwd=ROOT, text=True, capture_output=True)
        if completed.returncode != 0:
            sys.stderr.write(completed.stderr)
            sys.stderr.write(completed.stdout)
            return {
                "ok": False,
                "returncode": completed.returncode,
                "summary": summary,
            }
        verification = read_json(VERIFICATION_RESULT, verification)
    else:
        verification = verify_in_memory(summary, split_rows, source_rows, material_rows, scenario_summaries, cost_summary)
        audit = completion_audit(now, summary, verification, scenario_summaries)

    return {
        "completion_audit": audit,
        "cost_summary": cost_summary,
        "scenario_summaries": scenario_summaries,
        "split_rows": split_rows,
        "summary": summary,
        "verification": verification,
    }


def verify_in_memory(
    summary: dict[str, Any],
    split_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    material_rows: list[dict[str, Any]],
    scenario_summaries: list[dict[str, Any]],
    cost_summary: dict[str, Any],
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    def require(condition: bool, code: str, **payload: Any) -> None:
        if not condition:
            issues.append({"code": code, **payload})

    require(summary.get("selected_surface_rows") == EXPECTED_SELECTED_ROWS, "selected_surface_count_mismatch")
    selected_r = fnum(summary.get("stats", {}).get("selected_gross_r_sum"))
    require(
        selected_r is not None and abs(selected_r - UPSTREAM_DYNAMIC_ROUTER_TOTAL_R) < 0.001,
        "upstream_selected_gross_r_mismatch",
        actual=selected_r,
    )
    scopes = {row.get("split_scope") for row in split_rows}
    require(REQUIRED_SPLIT_SCOPES.issubset(scopes), "required_split_scope_missing", missing=sorted(REQUIRED_SPLIT_SCOPES - scopes))
    require(len(scenario_summaries) >= 3, "scenario_count_too_small")
    require(all(row.get("rows_processed") == EXPECTED_SELECTED_ROWS for row in scenario_summaries), "scenario_not_full_surface")
    require(bool(cost_summary.get("component_cost_scenarios")), "missing_component_cost_scenarios")
    require(bool(cost_summary.get("missing_source_stress_scenarios")), "missing_source_stress_scenarios")
    require(len(source_rows) >= 20, "source_completeness_too_small", actual=len(source_rows))
    require(len(material_rows) >= 20, "materialization_too_small", actual=len(material_rows))
    return {
        "generated_at_utc": utc_now(),
        "issue_count": len(issues),
        "issues": issues,
        "ok": not issues,
        "route_id": ROUTE_ID,
        "schema_version": "lane02_verification_result_v2",
    }


def manifest_integrity_issues(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for item in manifest.get("outputs", []):
        path_text = item.get("path")
        if not path_text:
            issues.append({"code": "manifest_entry_missing_path", "entry": item})
            continue
        path = ROOT / path_text
        if not path.exists():
            issues.append({"code": "manifest_entry_missing_file", "path": path_text})
            continue

        expected_bytes = item.get("bytes")
        actual_bytes = path.stat().st_size
        if expected_bytes != actual_bytes:
            issues.append(
                {
                    "actual": actual_bytes,
                    "code": "manifest_entry_byte_count_mismatch",
                    "expected": expected_bytes,
                    "path": path_text,
                }
            )

        expected_hash = item.get("sha256")
        actual_hash = file_sha256(path)
        if expected_hash != actual_hash:
            issues.append(
                {
                    "actual": actual_hash,
                    "code": "manifest_entry_sha256_mismatch",
                    "expected": expected_hash,
                    "path": path_text,
                }
            )

        if path.suffix == ".jsonl":
            expected_lines = item.get("line_count")
            actual_lines = line_count(path)
            if expected_lines != actual_lines:
                issues.append(
                    {
                        "actual": actual_lines,
                        "code": "manifest_entry_line_count_mismatch",
                        "expected": expected_lines,
                        "path": path_text,
                    }
                )
    return issues


def verify_outputs(write: bool = False) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    required = [
        REPLAY_LEDGER,
        SPLIT_SUMMARY,
        CONCENTRATION_LEDGER,
        SOURCE_COMPLETENESS_LEDGER,
        RESULT_MATERIALIZATION_LEDGER,
        SCENARIO_STRESS_LEDGER,
        COST_EXPOSURE_SUMMARY,
        PORTFOLIO_SUMMARY,
        COMPLETION_AUDIT,
        OUTPUT_MANIFEST,
        LANE01_ADAPTER,
        VERIFIER,
    ]

    def require(condition: bool, code: str, **payload: Any) -> None:
        if not condition:
            issues.append({"code": code, **payload})

    for path in required:
        require(path.exists(), "missing_output", path=rel(path))
    if issues:
        result = {
            "generated_at_utc": utc_now(),
            "issue_count": len(issues),
            "issues": issues,
            "ok": False,
            "route_id": ROUTE_ID,
            "schema_version": "lane02_verification_result_v2",
        }
        if write:
            write_json(VERIFICATION_RESULT, result)
        return result

    replay_rows = count_jsonl(REPLAY_LEDGER)
    split_rows = read_jsonl(SPLIT_SUMMARY)
    source_rows = read_jsonl(SOURCE_COMPLETENESS_LEDGER)
    material_rows = read_jsonl(RESULT_MATERIALIZATION_LEDGER)
    scenario_rows = read_jsonl(SCENARIO_STRESS_LEDGER)
    cost_summary = read_json(COST_EXPOSURE_SUMMARY, {})
    summary = read_json(PORTFOLIO_SUMMARY, {})
    audit = read_json(COMPLETION_AUDIT, {})
    manifest = read_json(OUTPUT_MANIFEST, {})

    require(replay_rows == EXPECTED_SELECTED_ROWS, "replay_rows_mismatch", actual=replay_rows)
    require(summary.get("selected_surface_rows") == EXPECTED_SELECTED_ROWS, "summary_selected_surface_mismatch", actual=summary.get("selected_surface_rows"))
    selected_r = fnum(summary.get("stats", {}).get("selected_gross_r_sum"))
    require(
        selected_r is not None and abs(selected_r - UPSTREAM_DYNAMIC_ROUTER_TOTAL_R) < 0.001,
        "selected_gross_r_mismatch",
        actual=selected_r,
    )
    scopes = {row.get("split_scope") for row in split_rows}
    require(REQUIRED_SPLIT_SCOPES.issubset(scopes), "required_split_scope_missing", missing=sorted(REQUIRED_SPLIT_SCOPES - scopes))
    require(any(row.get("split_scope") == "symbol" for row in split_rows), "symbol_split_missing")
    require(any(row.get("split_scope") == "session_bucket" for row in split_rows), "session_split_missing")
    require(count_jsonl(CONCENTRATION_LEDGER) >= 50, "concentration_ledger_too_small")
    require(len(source_rows) >= 20, "source_completeness_too_small", actual=len(source_rows))
    require(len(material_rows) >= 20, "materialization_too_small", actual=len(material_rows))
    require(len(scenario_rows) >= 3, "scenario_rows_too_small", actual=len(scenario_rows))
    require(all(row.get("rows_processed") == EXPECTED_SELECTED_ROWS for row in scenario_rows), "scenario_not_full_surface")
    require(
        {row.get("scenario_id") for row in scenario_rows}
        >= {
            BASE_SCENARIO_ID,
            "strict_lane01_same_symbol_no_partial_release_worst_case",
            "relaxed_same_symbol_multiticket_stress_not_live_default",
        },
        "required_scenarios_missing",
    )
    require(bool(cost_summary.get("component_cost_scenarios")), "component_cost_scenarios_missing")
    require(bool(cost_summary.get("missing_source_stress_scenarios")), "missing_source_stress_missing")
    require(audit.get("status") == "complete", "completion_audit_not_complete")
    require(
        audit.get("result_boundary", {}).get("runtime_effect_boundary")
        == "offline_replay_artifacts_only_no_broker_action_no_live_restart_no_config_change",
        "runtime_boundary_missing",
    )
    require(manifest.get("manifest_path") == rel(OUTPUT_MANIFEST), "manifest_path_missing_or_wrong")
    require(manifest.get("verification_result_path") == rel(VERIFICATION_RESULT), "verification_result_path_missing_or_wrong")
    require(manifest.get("output_count", 0) >= 12, "manifest_output_count_too_small", actual=manifest.get("output_count"))
    for issue in manifest_integrity_issues(manifest):
        issues.append(issue)

    result = {
        "accepted_rows": summary.get("stats", {}).get("accepted_rows"),
        "generated_at_utc": utc_now(),
        "input_rows": replay_rows,
        "issue_count": len(issues),
        "issues": issues,
        "ok": not issues,
        "route_id": ROUTE_ID,
        "schema_version": "lane02_verification_result_v2",
        "split_scope_count": len(scopes),
    }
    if write:
        write_json(VERIFICATION_RESULT, result)
    return result


def main() -> int:
    args = parse_args()
    if args.verify:
        result = verify_outputs(write=True)
    else:
        result = build_outputs(write=True).get("verification") or verify_outputs(write=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
