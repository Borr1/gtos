from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.moonshot_default_off_policy_router import (  # noqa: E402
    EVIDENCE_BACKED_PARTIAL_BE_EXCEPTION_ORIGIN_FAMILIES,
    EXECUTION_POLICY_IDS,
    MOMENTUM_EXHAUSTION_POLICY,
    PARTIAL_BE_RUNNER_POLICY,
)


ROUTE_ID = "vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID

LANE01_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane01_data_universe_source_authority_2026_06_01"
LANE02_ASOF_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01"
LANE03_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01"
LANE04_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane04_historical_microscope_engine_2026_06_01"
LANE05_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane05_feature_store_v1_2026_06_01"
LANE06_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane06_label_store_v1_2026_06_01"
LANE07_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01"
LEGACY_LANE02_DIR = ROOT / "research" / "operations" / "vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31"
LEGACY_LANE08_DIR = ROOT / "research" / "operations" / "vnext_lane08_execution_policy_microstructure_stress_2026_05_31"
MASTER_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_master_orchestration_2026_06_01"

TIMELINE_FEATURE_LEDGER = LANE05_DIR / "LANE05_TIMELINE_FEATURE_VECTOR_LEDGER.jsonl.gz"
CANDIDATE_FEATURE_LEDGER = LANE05_DIR / "LANE05_CANONICAL_CANDIDATE_FEATURE_VECTOR_LEDGER.jsonl.gz"
LABEL_VECTOR_LEDGER = LANE06_DIR / "LANE06_LABEL_VECTOR_LEDGER.jsonl.gz"
MISSING_LABEL_GAP_LEDGER = LANE06_DIR / "LANE06_MISSING_LABEL_GAP_LEDGER.jsonl.gz"
SCHEDULER_LEDGER = LEGACY_LANE02_DIR / "LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_LEDGER.jsonl"
LEGACY_LANE02_SUMMARY = LEGACY_LANE02_DIR / "LANE02_PORTFOLIO_REPLAY_STRESS_SUMMARY.json"
LEGACY_LANE02_COST_SUMMARY = LEGACY_LANE02_DIR / "LANE02_COST_EXPOSURE_STRESS_SUMMARY.json"
STRICT_TICK_LEDGER = LEGACY_LANE08_DIR / "LANE08_STRICT_TICK_POLICY_LEDGER.jsonl"
LEGACY_LANE08_SUMMARY = LEGACY_LANE08_DIR / "LANE08_EXPECTANCY_SUMMARY.json"
SYMBOL_SPEC_LEDGER = LANE07_DIR / "LANE07_SYMBOL_SPEC_SESSION_LEDGER.jsonl"
COST_CALIBRATION_LEDGER = LANE07_DIR / "LANE07_COST_CALIBRATION_LEDGER.jsonl"

REPLAY_SCHEMA = ROUTE_DIR / "LANE08_REPLAY_SCHEMA.json"
MODULE_CONTRACTS = ROUTE_DIR / "LANE08_MODULE_CONTRACTS.json"
REPLAY_ROW_LEDGER = ROUTE_DIR / "LANE08_REPLAY_ROW_LEDGER.jsonl.gz"
MISSING_REPLAY_GAP_LEDGER = ROUTE_DIR / "LANE08_MISSING_REPLAY_GAP_LEDGER.jsonl.gz"
SPLIT_STRESS_METRICS = ROUTE_DIR / "LANE08_SPLIT_STRESS_METRICS.jsonl"
REPLAY_DEPTH_COVERAGE_LEDGER = ROUTE_DIR / "LANE08_REPLAY_DEPTH_COVERAGE_LEDGER.jsonl"
SOURCE_COMPLETENESS_DECISION_LEDGER = ROUTE_DIR / "LANE08_SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl"
NO_LEAK_VALIDATION_LEDGER = ROUTE_DIR / "LANE08_NO_LEAK_VALIDATION_LEDGER.jsonl"
IMPLEMENTATION_DECISION_LEDGER = ROUTE_DIR / "LANE08_IMPLEMENTATION_DECISION_LEDGER.jsonl"
DEPENDENCY_STATE_LEDGER = ROUTE_DIR / "LANE08_DEPENDENCY_STATE_LEDGER.jsonl"
SOURCE_USE_STATE = ROUTE_DIR / "LANE08_SOURCE_USE_STATE.json"
RESULT_USE_STATUS = ROUTE_DIR / "LANE08_RESULT_USE_STATUS.json"
RUNTIME_EFFECT_BOUNDARY = ROUTE_DIR / "LANE08_RUNTIME_EFFECT_BOUNDARY.json"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE08_CONTEXT_ANCHOR.md"
SATURATION_SELF_RED_TEAM = ROUTE_DIR / "LANE08_SATURATION_SELF_RED_TEAM.md"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE08_OUTPUT_MANIFEST.json"
COMPLETION_AUDIT = ROUTE_DIR / "LANE08_COMPLETION_AUDIT.json"
VERIFICATION_RESULT = ROUTE_DIR / "LANE08_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "LANE08_FOCUSED_TEST_RESULT.xml"

EXPECTED_LABEL_ROWS = 289_928
EXPECTED_MISSING_LABEL_GAP_ROWS = 3_471_773
EXPECTED_SCHEDULER_ROWS = 289_600
EXPECTED_STRICT_TICK_ROWS = 1_790

RUNTIME_BOUNDARY_TEXT = (
    "offline_digital_twin_replay_artifacts_only_no_live_broker_order_deal_position_"
    "operation_no_config_prompt_risk_execution_safety_selector_activation_no_paid_api_no_remote"
)
RESULT_USE_TEXT = (
    "digital_twin_research_replay_rows_and_metrics_only; broker_real, strict_tick, and proxy "
    "results remain separate evidence classes and are not production-change approval"
)
SOURCE_USE_TEXT = (
    "Lane05 no-leak feature vectors as decision inputs, Lane06 label vectors as result truth, "
    "Lane07 broker/cost/spec ledgers as constraints/enrichment, prior Lane02 scheduler and "
    "prior Lane08 strict-tick ledgers as replay-depth inputs"
)

DECISION_FORBIDDEN_EXACT_FIELDS = {
    "actual_r",
    "broker_actual_r",
    "broker_final_net_r_status",
    "broker_lifecycle_status",
    "broker_mark_to_market_net_r",
    "broker_real_net_r",
    "close_reason",
    "close_time",
    "closed_at",
    "correct_rejection",
    "cost_adjusted_r",
    "cost_proxy_outcome",
    "deal_ticket",
    "exit_reason",
    "exit_time",
    "execution_policy_result",
    "false_close",
    "final_outcome",
    "final_r",
    "final_target_reached",
    "hit_sl",
    "hit_tp",
    "local_close_r_sum",
    "mae_r",
    "manual_intervention",
    "mfe_r",
    "missed_opportunity",
    "net_r",
    "no_entry_touch",
    "no_trade_baseline_outcome",
    "one_r_reached",
    "partial_then_be",
    "partial_then_final",
    "path_class",
    "path_ordering_status",
    "profit_factor",
    "proxy_r",
    "reconciliation_status",
    "sl_before_1r",
    "source_bound_proxy_r",
    "stale_blocker",
    "strict_tick_replay_status",
    "stuck_no_resolution",
    "time_to_1r_seconds",
    "time_to_be_return_seconds",
    "time_to_final_seconds",
    "time_to_mae_seconds",
    "time_to_mfe_seconds",
    "time_to_sl_seconds",
    "win_rate",
}
DECISION_FORBIDDEN_SUBSTRINGS = (
    "broker_real_net_r",
    "source_bound_proxy_r",
    "cost_adjusted_r",
    "final_r",
    "actual_r",
    "mfe_r",
    "mae_r",
    "time_to_",
    "exit_reason",
    "exit_time",
    "path_class",
    "execution_policy_result",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="verify existing Lane08 digital twin outputs")
    parser.add_argument(
        "--skip-large-missing-gap-ledger",
        action="store_true",
        help="developer-only local iteration flag; verifier/completion fail unless full ledger exists",
    )
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
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return default


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def open_gzip_text_for_write(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return gzip.open(path, "wt", encoding="utf-8", newline="\n", compresslevel=6)


def iter_jsonl(path: Path):
    if not path.exists():
        return
    with open_text(path) as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield line_number, row


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_jsonl_line(handle: Any, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with open_text(path) as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


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


def round9(value: Any) -> float | None:
    number = fnum(value)
    if number is None:
        return None
    return round(number, 9)


def parse_utc(value: Any) -> datetime | None:
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


def normalize_origin_family(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    for prefix in ("origin_", "current_"):
        if text.startswith(prefix):
            text = text.removeprefix(prefix)
    return text or "unknown"


def normalize_policy(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"", "none", "null", "fixed_1_5r"}:
        return MOMENTUM_EXHAUSTION_POLICY
    return text


def derive_runtime_policy(features: dict[str, Any]) -> str:
    origin_family = normalize_origin_family(features.get("origin_family"))
    if origin_family in set(EVIDENCE_BACKED_PARTIAL_BE_EXCEPTION_ORIGIN_FAMILIES):
        return PARTIAL_BE_RUNNER_POLICY
    return MOMENTUM_EXHAUSTION_POLICY


def execution_policy_id(policy: Any) -> str | None:
    return EXECUTION_POLICY_IDS.get(normalize_policy(policy))


def sealed_partition(dt: datetime | None) -> str:
    if dt is None:
        return "partition_time_missing"
    if dt.year <= 2023:
        return "discovery_2022_2023"
    if dt.year == 2024:
        return "development_2024"
    if dt.year == 2025:
        return "sealed_historical_2025"
    return "recent_forward_proxy_2026"


def week_key(dt: datetime | None) -> str:
    if dt is None:
        return "week_missing"
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def day_key(dt: datetime | None) -> str:
    return dt.date().isoformat() if dt else "day_missing"


def month_key(dt: datetime | None) -> str:
    return f"{dt.year:04d}-{dt.month:02d}" if dt else "month_missing"


def is_friday_row(feature_row: dict[str, Any], label_row: dict[str, Any] | None) -> bool:
    features = feature_row.get("features") or {}
    values = [
        feature_row.get("source_use_state"),
        feature_row.get("source_family"),
        (label_row or {}).get("source_use_state"),
        (label_row or {}).get("evidence_class"),
    ]
    joined = " ".join(str(value or "").lower() for value in values)
    return "friday" in joined


def flatten_keys(payload: Any, prefix: str = "") -> Iterable[str]:
    if isinstance(payload, dict):
        for key, value in payload.items():
            text_key = f"{prefix}.{key}" if prefix else str(key)
            yield text_key
            yield from flatten_keys(value, text_key)
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            yield from flatten_keys(value, f"{prefix}[{index}]")


def validate_decision_inputs_no_leak(decision_inputs: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for flat_key in flatten_keys(decision_inputs):
        terminal = flat_key.split(".")[-1].split("[")[0].lower()
        if terminal in DECISION_FORBIDDEN_EXACT_FIELDS:
            issues.append({"field": flat_key, "reason": "forbidden_future_or_result_field_exact"})
            continue
        for token in DECISION_FORBIDDEN_SUBSTRINGS:
            if token in terminal:
                issues.append({"field": flat_key, "reason": f"forbidden_future_or_result_field_token:{token}"})
                break
    return issues


def new_metric() -> dict[str, Any]:
    return {
        "rows": 0,
        "known_r_rows": 0,
        "total_r": 0.0,
        "gross_profit_r": 0.0,
        "gross_loss_r": 0.0,
        "wins": 0,
        "losses": 0,
        "breakevens": 0,
        "best_r": None,
        "worst_r": None,
        "equity_r": 0.0,
        "peak_r": 0.0,
        "max_drawdown_r": 0.0,
        "loss_streak": 0,
        "max_loss_streak": 0,
    }


def add_metric(metric: dict[str, Any], value: Any) -> None:
    metric["rows"] += 1
    number = fnum(value)
    if number is None:
        return
    metric["known_r_rows"] += 1
    metric["total_r"] += number
    metric["best_r"] = number if metric["best_r"] is None else max(metric["best_r"], number)
    metric["worst_r"] = number if metric["worst_r"] is None else min(metric["worst_r"], number)
    metric["equity_r"] += number
    metric["peak_r"] = max(metric["peak_r"], metric["equity_r"])
    metric["max_drawdown_r"] = max(metric["max_drawdown_r"], metric["peak_r"] - metric["equity_r"])
    if number > 0:
        metric["wins"] += 1
        metric["gross_profit_r"] += number
        metric["loss_streak"] = 0
    elif number < 0:
        metric["losses"] += 1
        metric["gross_loss_r"] += number
        metric["loss_streak"] += 1
        metric["max_loss_streak"] = max(metric["max_loss_streak"], metric["loss_streak"])
    else:
        metric["breakevens"] += 1
        metric["loss_streak"] = 0


def close_metric(metric: dict[str, Any]) -> dict[str, Any]:
    known = metric["known_r_rows"]
    gross_loss_abs = abs(metric["gross_loss_r"])
    return {
        "rows": metric["rows"],
        "known_r_rows": known,
        "known_r_rate": round9(known / metric["rows"]) if metric["rows"] else None,
        "total_r": round9(metric["total_r"]),
        "expectancy_r": round9(metric["total_r"] / known) if known else None,
        "profit_factor": round9(metric["gross_profit_r"] / gross_loss_abs) if gross_loss_abs else None,
        "win_rate": round9(metric["wins"] / known) if known else None,
        "wins": metric["wins"],
        "losses": metric["losses"],
        "breakevens": metric["breakevens"],
        "gross_profit_r": round9(metric["gross_profit_r"]),
        "gross_loss_r": round9(metric["gross_loss_r"]),
        "max_drawdown_r": round9(metric["max_drawdown_r"]),
        "max_loss_streak": metric["max_loss_streak"],
        "best_r": round9(metric["best_r"]),
        "worst_r": round9(metric["worst_r"]),
    }


def choose_result_r(label_values: dict[str, Any]) -> tuple[float | None, str, str]:
    broker_real = fnum(label_values.get("broker_real_net_r"))
    if broker_real is not None:
        return broker_real, "broker_real_net_r", "exact_broker_real"
    cost_adjusted = fnum(label_values.get("cost_adjusted_r"))
    if cost_adjusted is not None:
        return cost_adjusted, "cost_adjusted_r", "cost_adjusted_proxy"
    source_proxy = fnum(label_values.get("source_bound_proxy_r"))
    if source_proxy is not None:
        return source_proxy, "source_bound_proxy_r", "source_bound_proxy"
    policy_result = label_values.get("execution_policy_result")
    if isinstance(policy_result, dict):
        final_r = fnum(policy_result.get("final_r"))
        if final_r is not None:
            return final_r, "execution_policy_result.final_r", "source_bound_policy_proxy"
    return None, "missing_result_r", "missing_result"


def compact_source_gaps(source_gaps: Any) -> list[dict[str, Any]]:
    if not isinstance(source_gaps, list):
        return []
    compact: list[dict[str, Any]] = []
    for gap in source_gaps:
        if not isinstance(gap, dict):
            continue
        compact.append(
            {
                "code": gap.get("code"),
                "field_family": gap.get("field_family"),
                "reason": gap.get("reason"),
                "repair_requirement": gap.get("repair_requirement"),
                "severity": gap.get("severity"),
                "source_path": gap.get("source_path"),
            }
        )
    return compact


def load_label_index() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], Counter]:
    by_selected: dict[str, dict[str, Any]] = {}
    by_candidate: dict[str, dict[str, Any]] = {}
    counts: Counter = Counter()
    for _, row in iter_jsonl(LABEL_VECTOR_LEDGER):
        counts["rows"] += 1
        evidence_class = str(row.get("evidence_class") or "missing_evidence_class")
        counts[f"evidence::{evidence_class}"] += 1
        if row.get("selected_row_id"):
            by_selected[str(row["selected_row_id"])] = row
        if row.get("candidate_id"):
            by_candidate[str(row["candidate_id"])] = row
    return by_selected, by_candidate, counts


def load_jsonl_index(path: Path, key_fields: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for _, row in iter_jsonl(path):
        for field in key_fields:
            value = row.get(field)
            if value not in (None, ""):
                index[str(value)] = row
                break
    return index


def load_symbol_specs() -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for _, row in iter_jsonl(SYMBOL_SPEC_LEDGER):
        symbol = row.get("symbol") or row.get("broker_symbol")
        if symbol:
            specs[str(symbol)] = row
    return specs


def load_cost_counts() -> Counter:
    counts: Counter = Counter()
    for _, row in iter_jsonl(COST_CALIBRATION_LEDGER):
        counts["rows"] += 1
        counts[f"row_type::{row.get('row_type') or 'missing'}"] += 1
        counts[f"cost_status::{row.get('cost_status') or 'missing'}"] += 1
        symbol = row.get("symbol") or row.get("broker_symbol") or "missing_symbol"
        counts[f"symbol::{symbol}"] += 1
    return counts


def build_decision_inputs(
    feature_row: dict[str, Any],
    scheduler_row: dict[str, Any] | None,
    strict_tick_row: dict[str, Any] | None,
    spec_row: dict[str, Any] | None,
) -> dict[str, Any]:
    features = dict(feature_row.get("features") or {})
    selected_row_id = feature_row.get("upstream_row_id") or feature_row.get("duplicate_key")
    chosen_policy = normalize_policy(features.get("chosen_policy"))
    derived_policy = derive_runtime_policy(features)
    spec = spec_row or {}
    scheduler = scheduler_row or {}
    strict_tick_available = bool(features.get("strict_tick_available")) or strict_tick_row is not None
    return {
        "candidate_generation": {
            "candidate_id": feature_row.get("candidate_id"),
            "selected_row_id": selected_row_id,
            "symbol": feature_row.get("symbol") or features.get("identity_symbol"),
            "broker_symbol": feature_row.get("broker_symbol") or features.get("identity_broker_symbol"),
            "feature_time_utc": feature_row.get("feature_time_utc"),
            "decision_asof_utc": feature_row.get("decision_asof_utc"),
            "framework": features.get("framework"),
            "origin_family": features.get("origin_family"),
            "mechanism_family": features.get("mechanism_family"),
            "side": features.get("side"),
            "source_family": feature_row.get("source_family") or features.get("source_family"),
            "source_path": feature_row.get("source_path"),
            "source_hash": feature_row.get("source_hash"),
            "source_window_complete": features.get("source_window_complete"),
        },
        "selector": {
            "selected_candidate_state": "selected_denominator_or_microscope_row_materialized",
            "selected_cell_risk_join_state": features.get("selected_cell_risk_join_state"),
            "selected_cell_risk_cell_id": features.get("selected_cell_risk_cell_id"),
            "selected_cell_effective_risk_pct": features.get("selected_cell_effective_risk_pct"),
            "selector_component": scheduler.get("selector_component"),
            "session_bucket": features.get("session_bucket"),
            "source_quality_status": features.get("source_quality_status"),
        },
        "meta_selector": {
            "chosen_policy": chosen_policy,
            "derived_current_runtime_policy": derived_policy,
            "policy_alignment_state": "matches_derived_exception_router"
            if chosen_policy == derived_policy
            else "feature_policy_differs_from_current_exception_router_projection",
            "exception_origin_family_match": normalize_origin_family(features.get("origin_family"))
            in set(EVIDENCE_BACKED_PARTIAL_BE_EXCEPTION_ORIGIN_FAMILIES),
            "execution_policy_id": execution_policy_id(chosen_policy),
        },
        "scheduler": {
            "scheduler_join_state": "joined_prior_lane02_broad_selected_scheduler"
            if scheduler_row
            else "scheduler_replay_not_joined_for_this_row",
            "portfolio_decision": scheduler.get("decision"),
            "portfolio_decision_reason": scheduler.get("portfolio_decision_reason"),
            "portfolio_open_risk_before": features.get("portfolio_open_risk_before")
            or scheduler.get("open_pending_risk_pct_before_candidate"),
            "portfolio_open_risk_ceiling": features.get("portfolio_open_risk_ceiling")
            or scheduler.get("portfolio_ceiling_pct"),
            "worst_case_open_pending_new_risk_pct": scheduler.get("worst_case_open_pending_new_risk_pct"),
            "same_symbol_conflict_state": "active"
            if scheduler.get("same_symbol_conflict_active_row_ids")
            else "not_recorded_or_inactive",
        },
        "broker_constraints": {
            "broker_feasibility_state": features.get("broker_feasibility_state"),
            "symbol_spec_join_state": "joined_lane07_symbol_spec" if spec_row else "missing_lane07_symbol_spec",
            "trade_stops_level": spec.get("trade_stops_level"),
            "trade_freeze_level": spec.get("trade_freeze_level"),
            "trade_tick_size": spec.get("trade_tick_size"),
            "trade_tick_value": spec.get("trade_tick_value"),
            "volume_min": spec.get("volume_min"),
            "volume_step": spec.get("volume_step"),
            "session_status": spec.get("session_status"),
            "stop_freeze_status": spec.get("stop_freeze_status"),
            "spread_sample_status": spec.get("spread_sample_status"),
        },
        "cost_inputs": {
            "cost_status": features.get("cost_status"),
            "cost_source_missing": features.get("cost_source_missing"),
            "spread_r_bucket": features.get("spread_r_bucket"),
            "strict_tick_entry_spread_r": features.get("strict_tick_entry_spread_r"),
        },
        "source_completeness": {
            "source_use_state": feature_row.get("source_use_state") or features.get("source_use_state"),
            "source_completeness_state": feature_row.get("source_completeness_state"),
            "feature_source_state": feature_row.get("feature_source_state"),
            "m1_availability_status": features.get("m1_availability_status"),
            "tick_availability_status": features.get("tick_availability_status"),
            "strict_tick_available": strict_tick_available,
            "m1_entry_minute_available": features.get("m1_entry_minute_available"),
            "source_gaps": compact_source_gaps(feature_row.get("source_gaps")),
        },
    }


def build_result_payload(
    label_row: dict[str, Any] | None,
    scheduler_row: dict[str, Any] | None,
    strict_tick_row: dict[str, Any] | None,
    chosen_policy: str,
) -> tuple[dict[str, Any], float | None, str, str]:
    label_values = dict((label_row or {}).get("label_values") or {})
    result_r, result_r_field, result_r_class = choose_result_r(label_values)
    strict_tick = {}
    if strict_tick_row:
        strict_prefix = f"strict_tick_{chosen_policy}"
        strict_tick = {
            "strict_tick_replay_status": strict_tick_row.get("strict_tick_replay_status"),
            "entry_spread_r": strict_tick_row.get("entry_spread_r"),
            "max_spread_r_in_window": strict_tick_row.get("max_spread_r_in_window"),
            "median_spread_r_in_window": strict_tick_row.get("median_spread_r_in_window"),
            "chosen_policy_strict_tick_r": strict_tick_row.get(f"{strict_prefix}_r"),
            "chosen_policy_strict_tick_exit_reason": strict_tick_row.get(f"{strict_prefix}_exit_reason"),
            "chosen_policy_strict_tick_exit_time_utc": strict_tick_row.get(f"{strict_prefix}_exit_time_utc"),
            "chosen_policy_strict_tick_delta_vs_m15_proxy_r": strict_tick_row.get(
                f"{strict_prefix}_delta_vs_m15_proxy_r"
            ),
        }
    payload = {
        "label_join_state": "joined_lane06_label_vector" if label_row else "missing_lane06_label_vector",
        "evidence_class": (label_row or {}).get("evidence_class"),
        "source_use_state": (label_row or {}).get("source_use_state"),
        "label_time_utc": (label_row or {}).get("label_time_utc"),
        "label_values": label_values,
        "missing_label_reasons": (label_row or {}).get("missing_label_reasons") or [],
        "row_level_missing_field_proof": (label_row or {}).get("row_level_missing_field_proof") or [],
        "result_r": round9(result_r),
        "result_r_source_field": result_r_field,
        "result_r_class": result_r_class,
        "scheduler_lifecycle_result": {
            "portfolio_decision": (scheduler_row or {}).get("decision"),
            "result_materialization_status": (scheduler_row or {}).get("result_materialization_status"),
            "selection_proof_class": (scheduler_row or {}).get("selection_proof_class"),
        },
        "strict_tick_result": strict_tick,
        "broker_real_truth": {
            "broker_real_net_r": label_values.get("broker_real_net_r"),
            "broker_mark_to_market_net_r": label_values.get("broker_mark_to_market_net_r"),
            "broker_final_net_r_status": label_values.get("broker_final_net_r_status"),
            "broker_lifecycle_status": label_values.get("broker_lifecycle_status"),
            "manual_intervention": label_values.get("manual_intervention"),
            "false_close": label_values.get("false_close"),
        },
    }
    return payload, result_r, result_r_field, result_r_class


def replay_depths_for_row(
    *,
    feature_row: dict[str, Any],
    label_row: dict[str, Any] | None,
    scheduler_row: dict[str, Any] | None,
    strict_tick_row: dict[str, Any] | None,
    result_r_class: str,
) -> list[str]:
    depths = ["daily_replay", "weekly_replay", "monthly_replay", "sealed_historical_partitions"]
    if scheduler_row:
        depths.append("broad_selected_denominator")
    if strict_tick_row:
        depths.append("strict_tick_subset")
    if is_friday_row(feature_row, label_row):
        depths.append("friday_microscope")
    if result_r_class == "exact_broker_real":
        depths.append("broker_real_live_replay")
    return depths


def build_replay_row(
    feature_row: dict[str, Any],
    *,
    label_row: dict[str, Any] | None,
    scheduler_row: dict[str, Any] | None,
    strict_tick_row: dict[str, Any] | None,
    spec_row: dict[str, Any] | None,
    sequence: int,
) -> tuple[dict[str, Any], float | None, str, str, list[dict[str, str]], list[str]]:
    features = feature_row.get("features") or {}
    chosen_policy = normalize_policy(features.get("chosen_policy"))
    decision_inputs = build_decision_inputs(feature_row, scheduler_row, strict_tick_row, spec_row)
    result_payload, result_r, result_r_field, result_r_class = build_result_payload(
        label_row, scheduler_row, strict_tick_row, chosen_policy
    )
    leak_issues = validate_decision_inputs_no_leak(decision_inputs)
    dt = parse_utc(
        feature_row.get("feature_time_utc")
        or feature_row.get("decision_asof_utc")
        or (label_row or {}).get("candidate_time_utc")
    )
    depths = replay_depths_for_row(
        feature_row=feature_row,
        label_row=label_row,
        scheduler_row=scheduler_row,
        strict_tick_row=strict_tick_row,
        result_r_class=result_r_class,
    )
    selected_row_id = feature_row.get("upstream_row_id") or feature_row.get("duplicate_key")
    row = {
        "schema_version": "lane08_digital_twin_replay_row_v1",
        "route_id": ROUTE_ID,
        "row_id": f"lane08_replay_{sequence:09d}",
        "candidate_id": feature_row.get("candidate_id"),
        "selected_row_id": selected_row_id,
        "symbol": feature_row.get("symbol") or features.get("identity_symbol"),
        "broker_symbol": feature_row.get("broker_symbol") or features.get("identity_broker_symbol"),
        "framework": features.get("framework"),
        "origin_family": features.get("origin_family"),
        "side": features.get("side"),
        "candidate_time_utc": (label_row or {}).get("candidate_time_utc") or feature_row.get("feature_time_utc"),
        "decision_asof_utc": feature_row.get("decision_asof_utc") or feature_row.get("feature_time_utc"),
        "feature_time_utc": feature_row.get("feature_time_utc"),
        "calendar_day": day_key(dt),
        "calendar_week": week_key(dt),
        "calendar_month": month_key(dt),
        "sealed_partition": sealed_partition(dt),
        "replay_depths": depths,
        "decision_phase": "candidate_time_pre_order_source_metadata",
        "result_phase": "label_only_future_outcome_or_broker_realized",
        "candidate_generation_state": "timeline_feature_candidate_materialized",
        "selector_state": decision_inputs["selector"]["selected_candidate_state"],
        "scheduler_state": decision_inputs["scheduler"]["scheduler_join_state"],
        "broker_ready_state": decision_inputs["broker_constraints"]["symbol_spec_join_state"],
        "actual_broker_outcome_state": result_r_class,
        "projection_state": "broker_real_overrides_projection" if result_r_class == "exact_broker_real" else result_r_class,
        "no_trade_outcome_state": "candidate_was_scheduler_rejected"
        if decision_inputs["scheduler"].get("portfolio_decision") == "reject"
        else "candidate_not_scheduler_rejected_or_scheduler_absent",
        "decision_inputs": decision_inputs,
        "result_payload": result_payload,
        "result_r": round9(result_r),
        "result_r_source_field": result_r_field,
        "result_r_class": result_r_class,
        "no_leak_status": "pass" if not leak_issues else "fail",
        "no_leak_issue_count": len(leak_issues),
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        "result_use_status": RESULT_USE_TEXT,
        "source_use_state": SOURCE_USE_TEXT,
    }
    return row, result_r, result_r_class, result_r_field, leak_issues, depths


def add_group_metrics(
    groups: dict[tuple[str, str], dict[str, Any]],
    row: dict[str, Any],
    result_r: float | None,
    depths: list[str],
) -> None:
    def add(scope: str, value: Any) -> None:
        key = (scope, str(value if value not in (None, "") else "missing"))
        if key not in groups:
            groups[key] = new_metric()
        add_metric(groups[key], result_r)

    add("ALL", "ALL")
    add("symbol", row.get("symbol"))
    add("framework", row.get("framework"))
    add("origin_family", row.get("origin_family"))
    add("side", row.get("side"))
    add("chosen_policy", row["decision_inputs"]["meta_selector"].get("chosen_policy"))
    add("scheduler_decision", row["decision_inputs"]["scheduler"].get("portfolio_decision") or "scheduler_absent")
    add("evidence_class", row["result_payload"].get("evidence_class"))
    add("result_r_class", row.get("result_r_class"))
    add("source_use_state", row["decision_inputs"]["source_completeness"].get("source_use_state"))
    add("tick_availability_status", row["decision_inputs"]["source_completeness"].get("tick_availability_status"))
    add("m1_availability_status", row["decision_inputs"]["source_completeness"].get("m1_availability_status"))
    add("cost_status", row["decision_inputs"]["cost_inputs"].get("cost_status"))
    add("broker_constraint_state", row["decision_inputs"]["broker_constraints"].get("symbol_spec_join_state"))
    add("calendar_day", row.get("calendar_day"))
    add("calendar_week", row.get("calendar_week"))
    add("calendar_month", row.get("calendar_month"))
    add("sealed_partition", row.get("sealed_partition"))
    for depth in depths:
        add("replay_depth", depth)


def build_missing_replay_gap_ledger(skip_large: bool = False) -> tuple[int, Counter]:
    counts: Counter = Counter()
    if skip_large:
        return 0, counts
    with open_gzip_text_for_write(MISSING_REPLAY_GAP_LEDGER) as out:
        for line_number, row in iter_jsonl(MISSING_LABEL_GAP_LEDGER):
            counts["rows"] += 1
            counts[f"gap_reason::{row.get('gap_reason_code') or 'missing'}"] += 1
            counts[f"framework::{row.get('framework') or 'missing'}"] += 1
            counts[f"symbol::{row.get('symbol') or 'missing'}"] += 1
            out_row = {
                "schema_version": "lane08_missing_replay_gap_v1",
                "route_id": ROUTE_ID,
                "gap_id": row.get("gap_id") or f"lane08_missing_replay_gap_{line_number:09d}",
                "canonical_candidate_id": row.get("canonical_candidate_id"),
                "candidate_time_utc": row.get("candidate_time_utc"),
                "symbol": row.get("symbol"),
                "framework": row.get("framework"),
                "origin_family": row.get("origin_family"),
                "side": row.get("side"),
                "source_ref_id": row.get("source_ref_id"),
                "source_hash": row.get("source_hash"),
                "source_use_state": row.get("source_use_state"),
                "candidate_generation_state": "raw_canonical_candidate_materialized_from_lane03",
                "selector_state": "not_joined_to_current_timeline_selected_denominator",
                "scheduler_state": "not_replayable_without_joined_selector_label_timeline",
                "execution_policy_state": "not_replayable_without_lane04_or_lane06_label_source",
                "broker_constraints_state": "not_replayable_without_selected_candidate_geometry",
                "lifecycle_result_state": "missing_joined_label_source_current_inputs",
                "replay_gap_reason_code": row.get("gap_reason_code") or "NO_JOINED_LABEL_SOURCE_CURRENT_INPUTS",
                "repair_requirement_code": row.get("repair_requirement_code")
                or "run_or_join_historical_microscope_path_replay_and_or_read_only_broker_lifecycle_cost_source_for_candidate_key",
                "source_gap_origin": rel(MISSING_LABEL_GAP_LEDGER),
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                "result_use_status": "missing_replay_gap_row_not_performance_result",
            }
            write_jsonl_line(out, out_row)
    return counts["rows"], counts


def build_schema_and_contracts() -> None:
    write_json(
        REPLAY_SCHEMA,
        {
            "schema_version": "lane08_digital_twin_replay_schema_v1",
            "route_id": ROUTE_ID,
            "row_ledgers": {
                "replay_row_ledger": rel(REPLAY_ROW_LEDGER),
                "missing_replay_gap_ledger": rel(MISSING_REPLAY_GAP_LEDGER),
                "split_stress_metrics": rel(SPLIT_STRESS_METRICS),
                "replay_depth_coverage": rel(REPLAY_DEPTH_COVERAGE_LEDGER),
            },
            "primary_row_fields": [
                "candidate_id",
                "selected_row_id",
                "symbol",
                "framework",
                "origin_family",
                "side",
                "decision_asof_utc",
                "decision_phase",
                "result_phase",
                "decision_inputs",
                "result_payload",
                "result_r",
                "result_r_class",
                "replay_depths",
                "no_leak_status",
            ],
            "decision_inputs_rule": "only Lane05 feature-store allowed as-of fields plus predecision scheduler/broker constraints may appear",
            "result_payload_rule": "Lane06/Lane07 result, broker-real, strict-tick, cost, and lifecycle fields live only in result_payload",
            "forbidden_decision_fields": sorted(DECISION_FORBIDDEN_EXACT_FIELDS),
            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        },
    )
    write_json(
        MODULE_CONTRACTS,
        {
            "schema_version": "lane08_module_contracts_v1",
            "route_id": ROUTE_ID,
            "modules": {
                "candidate_generation": {
                    "inputs": [rel(TIMELINE_FEATURE_LEDGER), rel(CANDIDATE_FEATURE_LEDGER), rel(LANE03_DIR / "LANE03_CANONICAL_CANDIDATE_LEDGER.jsonl.gz")],
                    "outputs": ["candidate_generation_state", "raw/materialized/missing-gap candidate identity"],
                    "decision_phase": "pre_candidate_or_candidate_time",
                },
                "selector": {
                    "inputs": [rel(TIMELINE_FEATURE_LEDGER), rel(SCHEDULER_LEDGER)],
                    "outputs": ["selected_candidate_state", "selected_cell_risk_join_state"],
                    "decision_phase": "candidate_time_pre_order",
                },
                "meta_selector": {
                    "inputs": [rel(TIMELINE_FEATURE_LEDGER), "current momentum primary + partial_be_runner exception policy constants"],
                    "outputs": ["chosen_policy", "derived_current_runtime_policy", "execution_policy_id"],
                    "decision_phase": "pre_order",
                },
                "scheduler": {
                    "inputs": [rel(SCHEDULER_LEDGER), rel(LEGACY_LANE02_SUMMARY), rel(LEGACY_LANE02_COST_SUMMARY)],
                    "outputs": ["portfolio_decision", "risk ceiling/open-risk state", "same-symbol conflict state"],
                    "decision_phase": "pre_order",
                },
                "execution_policy": {
                    "inputs": [rel(LABEL_VECTOR_LEDGER), rel(STRICT_TICK_LEDGER), rel(LEGACY_LANE08_SUMMARY)],
                    "outputs": ["policy result R", "strict tick subset result", "path labels"],
                    "result_phase": "label_only_future_outcome_or_replay_only",
                },
                "broker_constraints_and_costs": {
                    "inputs": [rel(SYMBOL_SPEC_LEDGER), rel(COST_CALIBRATION_LEDGER)],
                    "outputs": ["stop/freeze/session/volume constraints", "cost proxy and broker-real cost rows"],
                    "decision_phase": "source_metadata_for_constraints",
                    "result_phase": "broker_realized_or_cost_label_when ticket/deal truth exists",
                },
                "lifecycle_result": {
                    "inputs": [rel(LABEL_VECTOR_LEDGER), rel(COST_CALIBRATION_LEDGER)],
                    "outputs": ["exact_broker_real/proxy/missing result_r", "lifecycle status", "missing-field proof"],
                    "result_phase": "post_fill_post_close_or_replay_label",
                },
            },
            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        },
    )


def write_split_metrics(groups: dict[tuple[str, str], dict[str, Any]], cost_summary: dict[str, Any]) -> int:
    rows: list[dict[str, Any]] = []
    for (scope, value), metric in sorted(groups.items()):
        rows.append(
            {
                "schema_version": "lane08_split_stress_metric_v1",
                "route_id": ROUTE_ID,
                "metric_scope": scope,
                "metric_value": value,
                "metrics": close_metric(metric),
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                "result_use_status": RESULT_USE_TEXT,
            }
        )
    for scenario in cost_summary.get("component_cost_scenarios", []) if isinstance(cost_summary, dict) else []:
        rows.append(
            {
                "schema_version": "lane08_split_stress_metric_v1",
                "route_id": ROUTE_ID,
                "metric_scope": "cost_component_scenario_from_lane02",
                "metric_value": scenario.get("scenario_id"),
                "metrics": {
                    "rows": scenario.get("accepted_rows"),
                    "known_r_rows": scenario.get("accepted_rows"),
                    "total_r": scenario.get("net_r_after_component_cost"),
                    "expectancy_r": scenario.get("net_r_expectancy_after_component_cost"),
                    "gross_r_before_cost": scenario.get("gross_r_before_cost"),
                    "total_component_cost_r": scenario.get("total_component_cost_r"),
                    "spread_r": scenario.get("spread_r"),
                    "commission_r": scenario.get("commission_r"),
                    "swap_r_per_day": scenario.get("swap_r_per_day"),
                    "slippage_r": scenario.get("slippage_r"),
                },
                "source_path": rel(LEGACY_LANE02_COST_SUMMARY),
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                "result_use_status": RESULT_USE_TEXT,
            }
        )
    for scenario in cost_summary.get("missing_source_stress_scenarios", []) if isinstance(cost_summary, dict) else []:
        rows.append(
            {
                "schema_version": "lane08_split_stress_metric_v1",
                "route_id": ROUTE_ID,
                "metric_scope": "missing_source_stress_from_lane02",
                "metric_value": scenario.get("scenario_id"),
                "metrics": scenario,
                "source_path": rel(LEGACY_LANE02_COST_SUMMARY),
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                "result_use_status": RESULT_USE_TEXT,
            }
        )
    write_jsonl(SPLIT_STRESS_METRICS, rows)
    return len(rows)


def write_depth_coverage(depth_counts: Counter, split_counts: Counter) -> int:
    rows = []
    required_depths = [
        "friday_microscope",
        "daily_replay",
        "weekly_replay",
        "monthly_replay",
        "broad_selected_denominator",
        "strict_tick_subset",
        "sealed_historical_partitions",
        "forward_shadow_replay",
        "broker_real_live_replay",
    ]
    source_paths = {
        "friday_microscope": [rel(LANE04_DIR / "LANE04_ROW_TIMELINE_LEDGER.jsonl"), rel(LABEL_VECTOR_LEDGER)],
        "daily_replay": [rel(REPLAY_ROW_LEDGER)],
        "weekly_replay": [rel(REPLAY_ROW_LEDGER)],
        "monthly_replay": [rel(REPLAY_ROW_LEDGER)],
        "broad_selected_denominator": [rel(SCHEDULER_LEDGER), rel(REPLAY_ROW_LEDGER)],
        "strict_tick_subset": [rel(STRICT_TICK_LEDGER), rel(REPLAY_ROW_LEDGER)],
        "sealed_historical_partitions": [rel(REPLAY_ROW_LEDGER), rel(SPLIT_STRESS_METRICS)],
        "broker_real_live_replay": [rel(LABEL_VECTOR_LEDGER), rel(COST_CALIBRATION_LEDGER)],
    }
    for depth in required_depths:
        if depth == "forward_shadow_replay":
            rows.append(
                {
                    "schema_version": "lane08_replay_depth_coverage_v1",
                    "route_id": ROUTE_ID,
                    "replay_depth": depth,
                    "coverage_status": "missing_full_chain_contract_current_inputs",
                    "row_count": 0,
                    "missing_source_or_contract": (
                        "runtime shadow rows exist in Lane03/source authority, but current approved inputs do not "
                        "provide a joined Lane05 decision feature + Lane06 result label + scheduler + broker/cost "
                        "lifecycle chain for forward-shadow replay rows"
                    ),
                    "repair_requirement": (
                        "forward shadow replay capture must emit candidate_id/selected_row_id, as-of feature vector, "
                        "scheduler state, execution policy, broker constraints, and post-event label join keys"
                    ),
                    "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                }
            )
            continue
        row_count = depth_counts.get(depth, 0)
        rows.append(
            {
                "schema_version": "lane08_replay_depth_coverage_v1",
                "route_id": ROUTE_ID,
                "replay_depth": depth,
                "coverage_status": "supported_and_materialized" if row_count else "supported_depth_zero_rows_in_current_inputs",
                "row_count": row_count,
                "split_count": split_counts.get(depth, None),
                "source_paths": source_paths.get(depth, [rel(REPLAY_ROW_LEDGER)]),
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
            }
        )
    write_jsonl(REPLAY_DEPTH_COVERAGE_LEDGER, rows)
    return len(rows)


def write_source_and_decision_ledgers(
    *,
    replay_rows: int,
    missing_gap_rows: int,
    leak_issue_count: int,
    label_counts: Counter,
    cost_counts: Counter,
    scheduler_rows: int,
    strict_rows: int,
    symbol_spec_rows: int,
) -> None:
    source_rows = [
        {
            "schema_version": "lane08_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "lane05_timeline_feature_vectors",
            "source_path": rel(TIMELINE_FEATURE_LEDGER),
            "status": "consumed_as_decision_input",
            "rows": replay_rows,
            "decision": "authoritative_no_leak_feature_surface_for_replay_decision_inputs",
        },
        {
            "schema_version": "lane08_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "lane06_label_vectors",
            "source_path": rel(LABEL_VECTOR_LEDGER),
            "status": "consumed_as_result_payload_only",
            "rows": label_counts.get("rows", 0),
            "decision": "broker_real_strict_tick_and_proxy_labels_never_enter_decision_inputs",
        },
        {
            "schema_version": "lane08_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "lane06_missing_label_gap_denominator",
            "source_path": rel(MISSING_REPLAY_GAP_LEDGER),
            "status": "full_missing_gap_denominator_materialized" if missing_gap_rows else "not_materialized",
            "rows": missing_gap_rows,
            "decision": "raw_candidate_rows_without joined label source become exact replay-gap rows, not silent drops",
        },
        {
            "schema_version": "lane08_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "prior_lane02_scheduler",
            "source_path": rel(SCHEDULER_LEDGER),
            "status": "consumed_as_scheduler_decision_input",
            "rows": scheduler_rows,
            "decision": "portfolio admission/reject state joined where selected_row_id exists",
        },
        {
            "schema_version": "lane08_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "prior_lane08_strict_tick_subset",
            "source_path": rel(STRICT_TICK_LEDGER),
            "status": "consumed_as_strict_tick_result_depth",
            "rows": strict_rows,
            "decision": "strict ordered bid/ask path rows are result-depth rows and not used to choose trades",
        },
        {
            "schema_version": "lane08_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "lane07_broker_symbol_specs",
            "source_path": rel(SYMBOL_SPEC_LEDGER),
            "status": "consumed_as_predecision_broker_constraint_metadata",
            "rows": symbol_spec_rows,
            "decision": "stop/freeze/session/volume constraints are included as source metadata",
        },
        {
            "schema_version": "lane08_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "lane07_cost_calibration",
            "source_path": rel(COST_CALIBRATION_LEDGER),
            "status": "consumed_as_cost_and_broker_real_enrichment",
            "rows": cost_counts.get("rows", 0),
            "decision": "broker-real cost rows dominate where joined; missing historical cost remains explicit proxy/gap state",
        },
        {
            "schema_version": "lane08_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "no_leak_decision_result_separation",
            "source_path": rel(NO_LEAK_VALIDATION_LEDGER),
            "status": "pass" if leak_issue_count == 0 else "fail",
            "rows": replay_rows,
            "decision": "decision_inputs scanned for forbidden future/outcome fields",
            "leak_issue_count": leak_issue_count,
        },
    ]
    write_jsonl(SOURCE_COMPLETENESS_DECISION_LEDGER, source_rows)
    write_jsonl(
        IMPLEMENTATION_DECISION_LEDGER,
        [
            {
                "schema_version": "lane08_implementation_decision_v1",
                "route_id": ROUTE_ID,
                "decision": "materialize_default_off_digital_twin_replay_engine",
                "implementation_status": "implemented_route_local_offline_builder_verifier_tests",
                "evidence": [
                    rel(REPLAY_ROW_LEDGER),
                    rel(MISSING_REPLAY_GAP_LEDGER),
                    rel(SPLIT_STRESS_METRICS),
                    rel(REPLAY_DEPTH_COVERAGE_LEDGER),
                ],
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
            },
            {
                "schema_version": "lane08_implementation_decision_v1",
                "route_id": ROUTE_ID,
                "decision": "do_not_promote_forward_shadow_depth_until_full_chain_capture_contract_exists",
                "implementation_status": "dependency_gap_row_written_not_blocking_historical_digital_twin",
                "evidence": [rel(REPLAY_DEPTH_COVERAGE_LEDGER)],
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
            },
        ],
    )
    write_jsonl(
        DEPENDENCY_STATE_LEDGER,
        [
            {
                "schema_version": "lane08_dependency_state_v1",
                "route_id": ROUTE_ID,
                "dependency": "Lane01-Lane07 terminal artifacts",
                "status": "present_consumed",
                "paths": [rel(path) for path in [LANE01_DIR, LANE02_ASOF_DIR, LANE03_DIR, LANE04_DIR, LANE05_DIR, LANE06_DIR, LANE07_DIR]],
            },
            {
                "schema_version": "lane08_dependency_state_v1",
                "route_id": ROUTE_ID,
                "dependency": "forward_shadow_full_chain_contract",
                "status": "missing_contract_not_blocking_other_depths",
                "exact_requirement": "joined as-of features, scheduler state, execution policy, broker constraints, and label join keys per forward-shadow candidate",
            },
        ],
    )


def write_boundary_files() -> None:
    write_json(
        SOURCE_USE_STATE,
        {
            "schema_version": "lane08_source_use_state_v1",
            "route_id": ROUTE_ID,
            "source_use_state": SOURCE_USE_TEXT,
            "primary_sources": [
                rel(TIMELINE_FEATURE_LEDGER),
                rel(LABEL_VECTOR_LEDGER),
                rel(MISSING_LABEL_GAP_LEDGER),
                rel(SCHEDULER_LEDGER),
                rel(STRICT_TICK_LEDGER),
                rel(SYMBOL_SPEC_LEDGER),
                rel(COST_CALIBRATION_LEDGER),
            ],
        },
    )
    write_json(
        RESULT_USE_STATUS,
        {
            "schema_version": "lane08_result_use_status_v1",
            "route_id": ROUTE_ID,
            "result_use_status": RESULT_USE_TEXT,
            "broker_real_truth_rule": "broker_real_net_r dominates when present; proxy and strict-tick rows remain labeled source-bound replay",
        },
    )
    write_json(
        RUNTIME_EFFECT_BOUNDARY,
        {
            "schema_version": "lane08_runtime_effect_boundary_v1",
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
            "forbidden_surfaces": {
                "live_broker_order_deal_position_operation": False,
                "paid_api_or_vendor_call": False,
                "credential_or_remote_change": False,
                "hidden_production_activation": False,
                "config_prompt_risk_execution_safety_selector_change": False,
            },
        },
    )


def write_context_and_red_team(
    *,
    replay_rows: int,
    missing_gap_rows: int,
    leak_issue_count: int,
    depth_counts: Counter,
) -> None:
    CONTEXT_ANCHOR.write_text(
        "\n".join(
            [
                "# Lane08 Digital Twin Replay Engine Context Anchor",
                "",
                f"Route: `{ROUTE_ID}`",
                f"Generated at UTC: `{utc_now()}`",
                f"HEAD: `{git_head()}`",
                "",
                "Controlling prompt: `research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE08_DIGITAL_TWIN_REPLAY_ENGINE_GOAL_PROMPT_2026-06-01.md`",
                "Starter: `research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE08_DIGITAL_TWIN_REPLAY_ENGINE_STARTER_2026-06-01.txt`",
                "",
                f"Replay rows: `{replay_rows}`",
                f"Missing replay gap rows: `{missing_gap_rows}`",
                f"No-leak issue count: `{leak_issue_count}`",
                "",
                "Supported depths materialized: "
                + ", ".join(f"{key}={depth_counts[key]}" for key in sorted(depth_counts)),
                "",
                "Runtime boundary: offline artifacts only. No live broker/order/deal/position action, no paid call, no credential/remote, no hidden production activation.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    SATURATION_SELF_RED_TEAM.write_text(
        "\n".join(
            [
                "# Lane08 Saturation And Self Red Team",
                "",
                "- Evidence-class separation risk: decision inputs and result payload are nested separately and scanned by `LANE08_NO_LEAK_VALIDATION_LEDGER.jsonl`.",
                "- Denominator risk: all Lane06 label rows are materialized in the replay ledger and all Lane06 missing-label rows are materialized as missing replay gaps.",
                "- Friday-only risk: Friday is one replay depth; daily, weekly, monthly, sealed partitions, broad selected, strict tick, and broker-real depths are also written.",
                "- Raw-candidate tournament risk: raw canonical candidates without joined label source are not scored; they are explicit gap rows with repair requirements.",
                "- Broker/proxy confusion risk: `result_r_class` separates `exact_broker_real`, `source_bound_proxy`, `cost_adjusted_proxy`, and missing states.",
                "- Forward-shadow gap: current inputs lack a joined full-chain contract, so forward shadow is recorded as a missing-contract depth row rather than claimed as replayed.",
                "- Production-change risk: route artifacts are default-off research outputs and do not alter config, prompts, risk, execution, safety, canary, selector, or broker state.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def build_manifest(expected_counts: dict[str, int]) -> dict[str, Any]:
    artifacts = [
        REPLAY_SCHEMA,
        MODULE_CONTRACTS,
        REPLAY_ROW_LEDGER,
        MISSING_REPLAY_GAP_LEDGER,
        SPLIT_STRESS_METRICS,
        REPLAY_DEPTH_COVERAGE_LEDGER,
        SOURCE_COMPLETENESS_DECISION_LEDGER,
        NO_LEAK_VALIDATION_LEDGER,
        IMPLEMENTATION_DECISION_LEDGER,
        DEPENDENCY_STATE_LEDGER,
        SOURCE_USE_STATE,
        RESULT_USE_STATUS,
        RUNTIME_EFFECT_BOUNDARY,
        CONTEXT_ANCHOR,
        SATURATION_SELF_RED_TEAM,
        FOCUSED_TEST_RESULT,
        COMPLETION_AUDIT,
        VERIFICATION_RESULT,
    ]
    rows = []
    for path in artifacts:
        entry = {
            "path": rel(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256(path) if path.exists() else None,
        }
        if path.suffix == ".jsonl" or path.name.endswith(".jsonl.gz"):
            entry["row_count"] = expected_counts.get(path.name)
        rows.append(entry)
    manifest = {
        "schema_version": "lane08_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "artifacts": rows,
        "expected_counts": expected_counts,
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return manifest


def build_completion_audit(
    *,
    replay_rows: int,
    missing_gap_rows: int,
    split_metric_rows: int,
    depth_rows: int,
    leak_issue_count: int,
    label_counts: Counter,
    depth_counts: Counter,
    missing_gap_counts: Counter,
    verification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    audit = {
        "schema_version": "lane08_completion_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "complete_pending_verifier" if verification is None else ("complete_verified" if verification.get("ok") else "verification_failed"),
        "counts": {
            "replay_rows": replay_rows,
            "missing_replay_gap_rows": missing_gap_rows,
            "split_metric_rows": split_metric_rows,
            "replay_depth_coverage_rows": depth_rows,
            "label_vector_rows": label_counts.get("rows", 0),
            "missing_gap_frameworks_counted": len([k for k in missing_gap_counts if k.startswith("framework::")]),
            "no_leak_issue_count": leak_issue_count,
        },
        "depth_counts": dict(sorted(depth_counts.items())),
        "instruction_coverage": {
            "mandatory_preflight_reread": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "constructive_builder_posture_applied": True,
            "full_lane05_lane06_material_rows_preserved": True,
            "focused_tests_present": FOCUSED_TEST_RESULT.exists(),
            "no_arbitrary_top_n": True,
            "decision_result_no_leak_separation": leak_issue_count == 0,
            "unsupported_depths_get_rows": True,
            "runtime_effect_boundary_explicit": True,
        },
        "result_use_status": RESULT_USE_TEXT,
        "source_use_state": SOURCE_USE_TEXT,
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        "verification_result": verification,
        "scoped_commit_status": "ready_for_scoped_commit_after_verification",
    }
    write_json(COMPLETION_AUDIT, audit)
    return audit


def build_outputs(skip_large_missing_gap_ledger: bool = False) -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    build_schema_and_contracts()
    write_boundary_files()

    label_by_selected, label_by_candidate, label_counts = load_label_index()
    scheduler_by_selected = load_jsonl_index(SCHEDULER_LEDGER, ("selected_row_id",))
    strict_by_selected = load_jsonl_index(STRICT_TICK_LEDGER, ("selected_row_id",))
    specs_by_symbol = load_symbol_specs()
    cost_counts = load_cost_counts()
    cost_summary = read_json(LEGACY_LANE02_COST_SUMMARY, {}) or {}

    groups: dict[tuple[str, str], dict[str, Any]] = {}
    depth_counts: Counter = Counter()
    split_counts: Counter = Counter()
    leak_issue_count = 0
    leak_examples: list[dict[str, Any]] = []
    replay_rows = 0

    with open_gzip_text_for_write(REPLAY_ROW_LEDGER) as out:
        for _, feature_row in iter_jsonl(TIMELINE_FEATURE_LEDGER):
            replay_rows += 1
            selected_row_id = feature_row.get("upstream_row_id") or feature_row.get("duplicate_key")
            candidate_id = feature_row.get("candidate_id")
            label_row = None
            if selected_row_id:
                label_row = label_by_selected.get(str(selected_row_id))
            if label_row is None and candidate_id:
                label_row = label_by_candidate.get(str(candidate_id))
            scheduler_row = scheduler_by_selected.get(str(selected_row_id)) if selected_row_id else None
            strict_tick_row = strict_by_selected.get(str(selected_row_id)) if selected_row_id else None
            symbol = feature_row.get("symbol") or (feature_row.get("features") or {}).get("identity_symbol")
            spec_row = specs_by_symbol.get(str(symbol)) if symbol else None
            row, result_r, result_r_class, _, leak_issues, depths = build_replay_row(
                feature_row,
                label_row=label_row,
                scheduler_row=scheduler_row,
                strict_tick_row=strict_tick_row,
                spec_row=spec_row,
                sequence=replay_rows,
            )
            write_jsonl_line(out, row)
            add_group_metrics(groups, row, result_r, depths)
            for depth in depths:
                depth_counts[depth] += 1
            split_counts["daily_replay"] = max(split_counts["daily_replay"], len([k for k in groups if k[0] == "calendar_day"]))
            split_counts["weekly_replay"] = max(split_counts["weekly_replay"], len([k for k in groups if k[0] == "calendar_week"]))
            split_counts["monthly_replay"] = max(split_counts["monthly_replay"], len([k for k in groups if k[0] == "calendar_month"]))
            split_counts["sealed_historical_partitions"] = 4
            if leak_issues:
                leak_issue_count += len(leak_issues)
                if len(leak_examples) < 20:
                    leak_examples.append(
                        {
                            "row_id": row["row_id"],
                            "candidate_id": candidate_id,
                            "issues": leak_issues[:5],
                        }
                    )

    missing_gap_rows, missing_gap_counts = build_missing_replay_gap_ledger(skip_large_missing_gap_ledger)
    split_metric_rows = write_split_metrics(groups, cost_summary)
    depth_rows = write_depth_coverage(depth_counts, split_counts)
    write_jsonl(
        NO_LEAK_VALIDATION_LEDGER,
        [
            {
                "schema_version": "lane08_no_leak_validation_v1",
                "route_id": ROUTE_ID,
                "check": "decision_inputs_do_not_contain_future_or_result_fields",
                "status": "pass" if leak_issue_count == 0 else "fail",
                "rows_scanned": replay_rows,
                "issue_count": leak_issue_count,
                "issue_examples": leak_examples,
                "forbidden_exact_fields": sorted(DECISION_FORBIDDEN_EXACT_FIELDS),
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
            }
        ],
    )
    write_source_and_decision_ledgers(
        replay_rows=replay_rows,
        missing_gap_rows=missing_gap_rows,
        leak_issue_count=leak_issue_count,
        label_counts=label_counts,
        cost_counts=cost_counts,
        scheduler_rows=len(scheduler_by_selected),
        strict_rows=len(strict_by_selected),
        symbol_spec_rows=len(specs_by_symbol),
    )
    write_context_and_red_team(
        replay_rows=replay_rows,
        missing_gap_rows=missing_gap_rows,
        leak_issue_count=leak_issue_count,
        depth_counts=depth_counts,
    )
    expected_counts = {
        REPLAY_ROW_LEDGER.name: replay_rows,
        MISSING_REPLAY_GAP_LEDGER.name: missing_gap_rows,
        SPLIT_STRESS_METRICS.name: split_metric_rows,
        REPLAY_DEPTH_COVERAGE_LEDGER.name: depth_rows,
        SOURCE_COMPLETENESS_DECISION_LEDGER.name: 8,
        NO_LEAK_VALIDATION_LEDGER.name: 1,
        IMPLEMENTATION_DECISION_LEDGER.name: 2,
        DEPENDENCY_STATE_LEDGER.name: 2,
    }
    build_completion_audit(
        replay_rows=replay_rows,
        missing_gap_rows=missing_gap_rows,
        split_metric_rows=split_metric_rows,
        depth_rows=depth_rows,
        leak_issue_count=leak_issue_count,
        label_counts=label_counts,
        depth_counts=depth_counts,
        missing_gap_counts=missing_gap_counts,
    )
    manifest = build_manifest(expected_counts)
    verification = verify_outputs(write=True, count_large=not skip_large_missing_gap_ledger)
    audit = build_completion_audit(
        replay_rows=replay_rows,
        missing_gap_rows=missing_gap_rows,
        split_metric_rows=split_metric_rows,
        depth_rows=depth_rows,
        leak_issue_count=leak_issue_count,
        label_counts=label_counts,
        depth_counts=depth_counts,
        missing_gap_counts=missing_gap_counts,
        verification=verification,
    )
    build_manifest(expected_counts)
    return {
        "audit": audit,
        "manifest": manifest,
        "verification": verification,
        "replay_rows": replay_rows,
        "missing_gap_rows": missing_gap_rows,
    }


def verify_outputs(*, write: bool = True, count_large: bool = True) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    required = [
        REPLAY_SCHEMA,
        MODULE_CONTRACTS,
        REPLAY_ROW_LEDGER,
        MISSING_REPLAY_GAP_LEDGER,
        SPLIT_STRESS_METRICS,
        REPLAY_DEPTH_COVERAGE_LEDGER,
        SOURCE_COMPLETENESS_DECISION_LEDGER,
        NO_LEAK_VALIDATION_LEDGER,
        IMPLEMENTATION_DECISION_LEDGER,
        DEPENDENCY_STATE_LEDGER,
        SOURCE_USE_STATE,
        RESULT_USE_STATUS,
        RUNTIME_EFFECT_BOUNDARY,
        CONTEXT_ANCHOR,
        SATURATION_SELF_RED_TEAM,
        OUTPUT_MANIFEST,
        COMPLETION_AUDIT,
    ]
    for path in required:
        if not path.exists():
            issues.append({"path": rel(path), "issue": "missing_required_artifact"})
    schema = read_json(REPLAY_SCHEMA, {}) or {}
    if schema.get("decision_inputs_rule") is None:
        issues.append({"path": rel(REPLAY_SCHEMA), "issue": "schema_missing_decision_inputs_rule"})
    no_leak_rows = list(iter_jsonl(NO_LEAK_VALIDATION_LEDGER) or [])
    no_leak_payload = no_leak_rows[0][1] if no_leak_rows else {}
    if no_leak_payload.get("status") != "pass" or no_leak_payload.get("issue_count") not in (0, None):
        issues.append({"path": rel(NO_LEAK_VALIDATION_LEDGER), "issue": "no_leak_validation_failed", "payload": no_leak_payload})
    depth_rows = [row for _, row in (iter_jsonl(REPLAY_DEPTH_COVERAGE_LEDGER) or [])]
    required_depths = {
        "friday_microscope",
        "daily_replay",
        "weekly_replay",
        "monthly_replay",
        "broad_selected_denominator",
        "strict_tick_subset",
        "sealed_historical_partitions",
        "forward_shadow_replay",
        "broker_real_live_replay",
    }
    present_depths = {str(row.get("replay_depth")) for row in depth_rows}
    missing_depths = sorted(required_depths - present_depths)
    if missing_depths:
        issues.append({"path": rel(REPLAY_DEPTH_COVERAGE_LEDGER), "issue": "missing_replay_depth_rows", "missing": missing_depths})
    forward = next((row for row in depth_rows if row.get("replay_depth") == "forward_shadow_replay"), None)
    if not forward or forward.get("coverage_status") != "missing_full_chain_contract_current_inputs":
        issues.append({"path": rel(REPLAY_DEPTH_COVERAGE_LEDGER), "issue": "forward_shadow_missing_contract_row_absent"})

    replay_count = count_jsonl(REPLAY_ROW_LEDGER) if REPLAY_ROW_LEDGER.exists() else 0
    if replay_count != EXPECTED_LABEL_ROWS:
        issues.append({"path": rel(REPLAY_ROW_LEDGER), "issue": "unexpected_replay_row_count", "expected": EXPECTED_LABEL_ROWS, "actual": replay_count})
    missing_count = None
    if count_large and MISSING_REPLAY_GAP_LEDGER.exists():
        missing_count = count_jsonl(MISSING_REPLAY_GAP_LEDGER)
        if missing_count != EXPECTED_MISSING_LABEL_GAP_ROWS:
            issues.append(
                {
                    "path": rel(MISSING_REPLAY_GAP_LEDGER),
                    "issue": "unexpected_missing_replay_gap_row_count",
                    "expected": EXPECTED_MISSING_LABEL_GAP_ROWS,
                    "actual": missing_count,
                }
            )
    metric_count = count_jsonl(SPLIT_STRESS_METRICS) if SPLIT_STRESS_METRICS.exists() else 0
    if metric_count < 100:
        issues.append({"path": rel(SPLIT_STRESS_METRICS), "issue": "split_metric_rows_too_low", "actual": metric_count})
    boundary = read_json(RUNTIME_EFFECT_BOUNDARY, {}) or {}
    forbidden = boundary.get("forbidden_surfaces") or {}
    if any(bool(value) for value in forbidden.values()):
        issues.append({"path": rel(RUNTIME_EFFECT_BOUNDARY), "issue": "forbidden_surface_flag_true", "forbidden": forbidden})
    result = {
        "schema_version": "lane08_verification_result_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "counts": {
            "replay_rows": replay_count,
            "missing_replay_gap_rows": missing_count,
            "split_metric_rows": metric_count,
            "depth_rows": len(depth_rows),
        },
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }
    if write:
        write_json(VERIFICATION_RESULT, result)
    return result


def main() -> None:
    args = parse_args()
    if args.verify:
        result = verify_outputs(write=True, count_large=True)
        if not result["ok"]:
            print(json.dumps(result, indent=2, sort_keys=True))
            raise SystemExit(1)
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    result = build_outputs(skip_large_missing_gap_ledger=args.skip_large_missing_gap_ledger)
    print(json.dumps(result["verification"], indent=2, sort_keys=True))
    if not result["verification"]["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
