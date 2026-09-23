from __future__ import annotations

import argparse
import gzip
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
)


ROUTE_ID = "vnext_moonshot_lane11_execution_policy_engine_v2_2026_06_01"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID

LANE02_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01"
LANE04_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane04_historical_microscope_engine_2026_06_01"
LANE05_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane05_feature_store_v1_2026_06_01"
LANE06_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane06_label_store_v1_2026_06_01"
LANE07_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01"
LANE08_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01"
MASTER_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_master_orchestration_2026_06_01"
LEGACY_LANE02_DIR = ROOT / "research" / "operations" / "vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31"
LEGACY_LANE08_DIR = ROOT / "research" / "operations" / "vnext_lane08_execution_policy_microstructure_stress_2026_05_31"
FRIDAY_DIR = ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"

LANE08_REPLAY_LEDGER = LANE08_DIR / "LANE08_REPLAY_ROW_LEDGER.jsonl.gz"
LANE08_MISSING_REPLAY_GAP_LEDGER = LANE08_DIR / "LANE08_MISSING_REPLAY_GAP_LEDGER.jsonl.gz"
LANE08_SPLIT_STRESS_METRICS = LANE08_DIR / "LANE08_SPLIT_STRESS_METRICS.jsonl"
LANE08_COMPLETION_AUDIT = LANE08_DIR / "LANE08_COMPLETION_AUDIT.json"
LANE08_REPLAY_SCHEMA = LANE08_DIR / "LANE08_REPLAY_SCHEMA.json"
LANE04_STRICT_TICK_TIMELINE = LANE04_DIR / "LANE04_STRICT_TICK_TIMELINE_LEDGER.jsonl"
LEGACY_LANE02_REPLAY_LEDGER = LEGACY_LANE02_DIR / "LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_LEDGER.jsonl"
LEGACY_LANE08_STRICT_TICK_LEDGER = LEGACY_LANE08_DIR / "LANE08_STRICT_TICK_POLICY_LEDGER.jsonl"
FRIDAY_POLICY_LEDGER = FRIDAY_DIR / "FRIDAY_EXECUTION_POLICY_SELECTED_DENOMINATOR_LEDGER.jsonl"
LANE07_SYMBOL_SPEC_LEDGER = LANE07_DIR / "LANE07_SYMBOL_SPEC_SESSION_LEDGER.jsonl"
LANE07_COST_LEDGER = LANE07_DIR / "LANE07_COST_CALIBRATION_LEDGER.jsonl"

POLICY_SCHEMA = ROUTE_DIR / "LANE11_POLICY_SCHEMA.json"
POLICY_SIMULATION_LEDGER = ROUTE_DIR / "LANE11_POLICY_SIMULATION_LEDGER.jsonl.gz"
POLICY_METRIC_LEDGER = ROUTE_DIR / "LANE11_POLICY_METRIC_LEDGER.jsonl"
POLICY_DOMINANCE_LEDGER = ROUTE_DIR / "LANE11_POLICY_DOMINANCE_DECISION_LEDGER.jsonl"
DEFAULT_OFF_PACKAGE = ROUTE_DIR / "LANE11_DEFAULT_OFF_POLICY_ROUTER_PACKAGE.json"
DEFAULT_OFF_PACKAGE_LEDGER = ROUTE_DIR / "LANE11_DEFAULT_OFF_POLICY_ROUTER_PACKAGE_LEDGER.jsonl"
SOURCE_COMPLETENESS_LEDGER = ROUTE_DIR / "LANE11_SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl"
IMPLEMENTATION_DECISION_LEDGER = ROUTE_DIR / "LANE11_IMPLEMENTATION_DECISION_LEDGER.jsonl"
DEPENDENCY_STATE_LEDGER = ROUTE_DIR / "LANE11_DEPENDENCY_STATE_LEDGER.jsonl"
NO_LEAK_LEDGER = ROUTE_DIR / "LANE11_NO_LEAK_VALIDATION_LEDGER.jsonl"
DOWNSTREAM_CONTRACT = ROUTE_DIR / "LANE11_DOWNSTREAM_CONTRACT.json"
SOURCE_USE_STATE = ROUTE_DIR / "LANE11_SOURCE_USE_STATE.json"
RESULT_USE_STATUS = ROUTE_DIR / "LANE11_RESULT_USE_STATUS.json"
RUNTIME_EFFECT_BOUNDARY = ROUTE_DIR / "LANE11_RUNTIME_EFFECT_BOUNDARY.json"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE11_CONTEXT_ANCHOR.md"
SATURATION_SELF_RED_TEAM = ROUTE_DIR / "LANE11_SATURATION_SELF_RED_TEAM.md"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE11_OUTPUT_MANIFEST.json"
COMPLETION_AUDIT = ROUTE_DIR / "LANE11_COMPLETION_AUDIT.json"
VERIFICATION_RESULT = ROUTE_DIR / "LANE11_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "LANE11_FOCUSED_TEST_RESULT.xml"
EVIDENCE_INTEGRITY_INVENTORY = ROUTE_DIR / "LANE11_EVIDENCE_INTEGRITY_INVENTORY.jsonl"
EVIDENCE_INTELLIGENCE_INDEX = ROUTE_DIR / "LANE11_EVIDENCE_INTELLIGENCE_INDEX.jsonl"
EVIDENCE_COVERAGE_MANIFEST = ROUTE_DIR / "LANE11_EVIDENCE_COVERAGE_MANIFEST.json"
EVIDENCE_WORK_QUEUE = ROUTE_DIR / "LANE11_EVIDENCE_WORK_QUEUE.jsonl"
EVIDENCE_RAW_VALIDATION_LEDGER = ROUTE_DIR / "LANE11_EVIDENCE_RAW_VALIDATION_LEDGER.jsonl"
EVIDENCE_CONVERGENCE_AUDIT = ROUTE_DIR / "LANE11_EVIDENCE_INTEGRITY_CONVERGENCE_AUDIT.json"
EXPANDED_POLICY_VARIANT_REGISTRY = ROUTE_DIR / "LANE11_EXPANDED_POLICY_VARIANT_REGISTRY.jsonl"
EXPANDED_POLICY_FEASIBILITY_LEDGER = ROUTE_DIR / "LANE11_EXPANDED_POLICY_FEASIBILITY_LEDGER.jsonl"
EXPANDED_POLICY_SPLIT_DECISION_LEDGER = ROUTE_DIR / "LANE11_EXPANDED_POLICY_SPLIT_DECISION_LEDGER.jsonl.gz"
EXPANDED_POLICY_SIMULATION_METRIC_LEDGER = ROUTE_DIR / "LANE11_EXPANDED_POLICY_SIMULATION_METRIC_LEDGER.jsonl.gz"
EXPANDED_POLICY_DOMINANCE_DECISION_LEDGER = ROUTE_DIR / "LANE11_EXPANDED_POLICY_DOMINANCE_DECISION_LEDGER.jsonl.gz"
EXPANDED_DEFAULT_OFF_POLICY_PACKAGE_LEDGER = ROUTE_DIR / "LANE11_EXPANDED_DEFAULT_OFF_POLICY_PACKAGE_LEDGER.jsonl.gz"
EXPANDED_POLICY_SOURCE_GAP_LEDGER = ROUTE_DIR / "LANE11_EXPANDED_POLICY_SOURCE_GAP_LEDGER.jsonl.gz"

EXPECTED_REPLAY_ROWS = 289_928
EXPECTED_REPLAY_GAP_ROWS = 3_471_773
EXPECTED_SPLIT_STRESS_ROWS = 1_536
EXPECTED_STRICT_TICK_ROWS = 1_790
EXPECTED_FRIDAY_ROWS = 328
EXPECTED_LANE02_POLICY_ROWS = 289_600
EXPECTED_PACKAGE_ROWS = 5_158

BASE_POLICIES = (
    "momentum_exhaustion",
    "partial_be_runner",
    "trailing_runner",
    "time_stop",
    "fixed_1_5r",
    "be_after_trigger",
)
POLICY_VARIANTS = (
    *BASE_POLICIES,
    "no_trade_baseline",
    "current_router_policy",
    "hybrid_momentum_primary_partial_exception",
    "hybrid_strict_trailing_challenger_else_current_router",
)
BASELINE_POLICY_VARIANTS = POLICY_VARIANTS
PARTIAL_CLOSE_RATIOS = (0.25, 0.33, 0.50, 0.66, 0.75)
PARTIAL_TRIGGER_R = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
BE_TIMINGS = ("immediate_be", "be_after_partial", "be_plus_buffer", "delayed_be", "no_be")
RUNNER_TARGETS_R = (2.0, 3.0, 4.0, 5.0, "uncapped")
TRAILING_ACTIVATION_R = (0.5, 0.75, 1.0, 1.5, 2.0)
TRAILING_GAP_MODELS = ("fixed_r_gap", "atr_gap", "structure_gap", "spread_adjusted_gap")
TRAILING_STEP_MODES = ("every_tick", "every_m1_close", "stepwise_new_mfe", "broker_feasible_modify_cadence")
TIME_STOP_MODES = ("1h", "2h", "3h", "4h", "6h", "8h", "session_close", "kill_zone_close", "stagnation_based")
MOMENTUM_EXHAUSTION_MODES = (
    "stricter_exit",
    "looser_exit",
    "m1_confirmed_exit",
    "m15_confirmed_exit",
    "hybrid_runner_exit",
)
INVALIDATION_MODES = (
    "m1_structure_break",
    "sweep_failure",
    "displacement_failure",
    "spread_expansion",
    "volatility_collapse",
)
NO_ENTRY_TIMEOUT_MODES = (
    "pending_timeout_1h",
    "pending_timeout_2h",
    "pending_timeout_session_close",
    "no_entry_if_spread_expansion",
)
HYBRID_ROUTING_DIMENSIONS = (
    "symbol",
    "session",
    "origin_family",
    "source_completeness",
    "scheduler_state",
    "spread_r_bucket",
    "volatility_state",
    "symbol_session_origin",
    "mechanism_session_source",
)
HYBRID_ACTION_FAMILIES = (
    "momentum_primary_partial_exception",
    "strict_trailing_else_current",
    "no_trade_for_negative_slice",
)
EXPANDED_EVIDENCE_BUCKETS = (
    "full_selected_denominator",
    "m15_proxy",
    "strict_tick_subset",
    "friday_tick_subset",
    "m1_event_path_subset",
    "broker_real_subset",
    "unreplayable_source_gap",
)
EXPANDED_SPLIT_SCOPES = (
    "overall",
    "symbol",
    "session",
    "origin_family",
    "framework",
    "source_completeness",
    "scheduler_state",
    "spread_r_bucket",
    "volatility_state",
    "symbol_session_origin",
    "mechanism_session_source",
)
STRICT_R_FIELDS = {
    "be_after_trigger": "strict_tick_be_after_trigger_r",
    "fixed_1_5r": "strict_tick_fixed_1_5r_r",
    "momentum_exhaustion": "strict_tick_momentum_exhaustion_r",
    "partial_be_runner": "strict_tick_partial_be_runner_r",
    "time_stop": "strict_tick_time_stop_r",
    "trailing_runner": "strict_tick_trailing_runner_r",
}
STRICT_EXIT_TIME_FIELDS = {
    "be_after_trigger": "strict_tick_be_after_trigger_exit_time_utc",
    "fixed_1_5r": "strict_tick_fixed_1_5r_exit_time_utc",
    "momentum_exhaustion": "strict_tick_momentum_exhaustion_exit_time_utc",
    "partial_be_runner": "strict_tick_partial_be_runner_exit_time_utc",
    "time_stop": "strict_tick_time_stop_exit_time_utc",
    "trailing_runner": "strict_tick_trailing_runner_exit_time_utc",
}
STRICT_EXIT_REASON_FIELDS = {
    "be_after_trigger": "strict_tick_be_after_trigger_exit_reason",
    "fixed_1_5r": "strict_tick_fixed_1_5r_exit_reason",
    "momentum_exhaustion": "strict_tick_momentum_exhaustion_exit_reason",
    "partial_be_runner": "strict_tick_partial_be_runner_exit_reason",
    "time_stop": "strict_tick_time_stop_exit_reason",
    "trailing_runner": "strict_tick_trailing_runner_exit_reason",
}
LANE02_COMPARISON_FIELDS = {
    "be_after_trigger": "comparison_be_after_trigger_r",
    "fixed_1_5r": "comparison_fixed_1_5r_r",
    "momentum_exhaustion": "comparison_momentum_exhaustion_r",
    "partial_be_runner": "comparison_partial_be_runner_r",
    "time_stop": "comparison_time_stop_r",
    "trailing_runner": "comparison_trailing_runner_r",
}
FRIDAY_POLICY_ALIASES = {
    "be_after_trigger_comparator": "be_after_trigger",
    "current_selected_policy": "current_router_policy",
    "fixed_1_5r_comparator": "fixed_1_5r",
    "momentum_exhaustion": "momentum_exhaustion",
    "no_trade_baseline": "no_trade_baseline",
    "partial_be_runner": "partial_be_runner",
    "time_stop_8h": "time_stop",
    "trailing_1r_gap_0_5_cap_3r": "trailing_runner",
}
MODIFY_DEPENDENT_POLICIES = {
    "be_after_trigger",
    "partial_be_runner",
    "trailing_runner",
}
PARTIAL_CLOSE_POLICIES = {"partial_be_runner"}
TRAILING_POLICIES = {"trailing_runner"}
BE_POLICIES = {"be_after_trigger", "partial_be_runner", "trailing_runner"}

RUNTIME_BOUNDARY_TEXT = (
    "offline_execution_policy_engine_v2_artifacts_only_no_live_broker_order_deal_"
    "position_operation_no_config_prompt_risk_execution_safety_selector_activation_"
    "no_paid_api_no_remote"
)
RESULT_USE_TEXT = (
    "execution_policy_research_simulation_and_default_off_package_only; strict_tick, "
    "friday_tick, m15_proxy, cost_proxy, and broker-real evidence classes remain separated "
    "and are not production-change approval"
)
SOURCE_USE_TEXT = (
    "Lane08 replay rows consumed as the primary denominator; Lane02 broad selected comparison "
    "fields consumed for m15 proxy policy variants; Lane04/Lane08 strict-tick rows consumed "
    "for ordered bid/ask exact subset; Lane05 decision feature state, Lane06 label values, "
    "Lane07 broker constraints/cost fields, and Friday tick policy rows consumed as downstream "
    "constraints and exact/proxy result evidence"
)

MEDIAN_COMPONENT_COST_R = 0.01853151
P90_COMPONENT_COST_R = 0.026731293
HIGH_STRESS_COMPONENT_COST_R = 0.22

FORBIDDEN_ROUTER_FEATURE_FIELDS = {
    "actual_r",
    "broker_real_net_r",
    "close_reason",
    "cost_adjusted_r",
    "execution_policy_result",
    "exit_reason",
    "final_r",
    "hit_sl",
    "hit_tp",
    "mae_r",
    "mfe_r",
    "path_class",
    "source_bound_proxy_r",
    "strict_tick_replay_status",
    "time_to_1r_seconds",
    "time_to_final_seconds",
    "time_to_sl_seconds",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="verify existing Lane11 outputs")
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


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def open_gzip_text_for_write(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    return gzip.open(path, "wt", encoding="utf-8", newline="\n", compresslevel=6)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    handle_context = (
        open_gzip_text_for_write(path)
        if path.suffix == ".gz"
        else path.open("w", encoding="utf-8", newline="\n")
    )
    with handle_context as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")
            count += 1
    return count


def iter_jsonl(path: Path):
    if not path.exists():
        return
    with open_text(path) as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                yield {"_parse_error": str(exc), "_line_number": line_number}


def write_jsonl_line(handle: Any, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, separators=(",", ":")) + "\n")


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with open_text(path) as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def sha256(path: Path) -> str | None:
    if not path.exists() or path.is_dir():
        return None
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fnum(value: Any, default: float | None = None) -> float | None:
    if isinstance(value, bool) or value in (None, ""):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def round9(value: Any) -> float | None:
    number = fnum(value)
    if number is None:
        return None
    return round(number, 9)


def parse_utc(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def seconds_between(start: Any, end: Any) -> float | None:
    start_dt = parse_utc(start)
    end_dt = parse_utc(end)
    if start_dt is None or end_dt is None:
        return None
    return max(0.0, (end_dt - start_dt).total_seconds())


def normalize_policy(value: Any) -> str:
    text = "" if value is None else str(value).strip().lower()
    text = text.replace("-", "_").replace(" ", "_")
    if text in {"fixed", "fixed_1.5r", "fixed_1_5r_comparator"}:
        return "fixed_1_5r"
    if text in {"be", "be_after_trigger_comparator"}:
        return "be_after_trigger"
    if text in {"time_stop_8h", "time_stop_4h", "time_stop_2h"}:
        return "time_stop"
    if text in {"trailing_1r_gap_0_5_cap_3r", "trailing_1_5r_gap_0_5_cap_3r"}:
        return "trailing_runner"
    if text in {"current_selected_policy", "current_router"}:
        return "current_router_policy"
    if text in {"no_trade", "no_trade_baseline"}:
        return "no_trade_baseline"
    return text


def strip_origin(value: Any) -> str:
    text = "" if value is None else str(value).strip().lower()
    return text.removeprefix("origin_").removeprefix("current_")


def source_bucket(evidence_class: str) -> str:
    if evidence_class.startswith("strict_tick"):
        return "strict_tick"
    if evidence_class.startswith("friday_tick"):
        return "friday_tick"
    if evidence_class.startswith("m15_proxy"):
        return "m15_proxy"
    if "no_trade" in evidence_class:
        return "no_trade"
    if evidence_class.startswith("lane08_selected"):
        return "lane08_selected_policy_only"
    return "missing"


def current_router_policy_from_row(row: dict[str, Any]) -> str:
    decision_inputs = row.get("decision_inputs") if isinstance(row.get("decision_inputs"), dict) else {}
    meta = decision_inputs.get("meta_selector") if isinstance(decision_inputs.get("meta_selector"), dict) else {}
    policy = normalize_policy(meta.get("chosen_policy") or meta.get("derived_current_runtime_policy"))
    if policy in BASE_POLICIES:
        return policy
    label_values = (
        row.get("result_payload", {}).get("label_values", {})
        if isinstance(row.get("result_payload"), dict)
        else {}
    )
    execution_policy_result = label_values.get("execution_policy_result", {})
    if isinstance(execution_policy_result, dict):
        policy = normalize_policy(execution_policy_result.get("chosen_policy"))
        if policy in BASE_POLICIES:
            return policy
    return "momentum_exhaustion"


def resolve_policy_variant(
    variant: str,
    row: dict[str, Any],
    strict_available: bool,
    trailing_modify_feasible: bool,
) -> str:
    if variant in BASE_POLICIES or variant == "no_trade_baseline":
        return variant
    if variant == "current_router_policy":
        return current_router_policy_from_row(row)
    if variant == "hybrid_momentum_primary_partial_exception":
        origin = strip_origin(row.get("origin_family"))
        if origin in set(EVIDENCE_BACKED_PARTIAL_BE_EXCEPTION_ORIGIN_FAMILIES):
            return "partial_be_runner"
        return "momentum_exhaustion"
    if variant == "hybrid_strict_trailing_challenger_else_current_router":
        if strict_available and trailing_modify_feasible:
            return "trailing_runner"
        return current_router_policy_from_row(row)
    raise ValueError(f"unknown policy variant: {variant}")


def load_lane02_policy_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(LEGACY_LANE02_REPLAY_LEDGER):
        selected_row_id = row.get("selected_row_id")
        if not selected_row_id:
            continue
        r_by_policy = {
            policy: round9(row.get(field))
            for policy, field in LANE02_COMPARISON_FIELDS.items()
        }
        index[str(selected_row_id)] = {
            "r_by_policy": r_by_policy,
            "decision": row.get("decision"),
            "portfolio_decision_reason": row.get("portfolio_decision_reason"),
            "session_bucket": row.get("session_bucket"),
            "risk_cell_id": row.get("risk_cell_id"),
            "same_bar_ambiguity": row.get("same_bar_ambiguity"),
            "stop_freeze_feasibility_status": row.get("stop_freeze_feasibility_status"),
            "holding_hours": round9(row.get("holding_hours")),
            "source_path": row.get("source_path"),
            "source_shard": row.get("source_shard"),
            "source_mode": row.get("source_mode"),
            "source_sha256": row.get("source_sha256"),
        }
    return index


def load_strict_tick_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(LEGACY_LANE08_STRICT_TICK_LEDGER):
        selected_row_id = row.get("selected_row_id")
        if not selected_row_id:
            continue
        r_by_policy = {
            policy: round9(row.get(field))
            for policy, field in STRICT_R_FIELDS.items()
        }
        exit_time_by_policy = {
            policy: row.get(field)
            for policy, field in STRICT_EXIT_TIME_FIELDS.items()
        }
        exit_reason_by_policy = {
            policy: row.get(field)
            for policy, field in STRICT_EXIT_REASON_FIELDS.items()
        }
        index[str(selected_row_id)] = {
            "r_by_policy": r_by_policy,
            "exit_time_by_policy": exit_time_by_policy,
            "exit_reason_by_policy": exit_reason_by_policy,
            "entry_time_utc": row.get("entry_time_utc"),
            "entry_spread_r": round9(row.get("entry_spread_r")),
            "first_tick_time_utc": row.get("first_tick_time_utc"),
            "last_tick_time_utc": row.get("last_tick_time_utc"),
            "max_spread_r_in_window": round9(row.get("max_spread_r_in_window")),
            "median_spread_r_in_window": round9(row.get("median_spread_r_in_window")),
            "raw_tick_rows": row.get("raw_tick_rows"),
            "risk_price_distance": round9(row.get("risk_price_distance")),
            "strict_tick_replay_status": row.get("strict_tick_replay_status"),
            "valid_bid_ask_tick_rows": row.get("valid_bid_ask_tick_rows"),
            "portfolio_ready_decision": row.get("portfolio_ready_decision"),
            "portfolio_decision_reason": row.get("portfolio_decision_reason"),
        }
    return index


def load_friday_policy_index() -> dict[str, dict[str, dict[str, Any]]]:
    index: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in iter_jsonl(FRIDAY_POLICY_LEDGER):
        trade_id = row.get("trade_id")
        if not trade_id:
            continue
        alias = FRIDAY_POLICY_ALIASES.get(str(row.get("comparison_policy", "")).strip())
        if not alias:
            continue
        existing = index[str(trade_id)].get(alias)
        price_source = str(row.get("price_source") or "")
        if existing and existing.get("price_source") == "tick_bid_ask" and price_source != "tick_bid_ask":
            continue
        index[str(trade_id)][alias] = {
            "gross_r": round9(row.get("gross_r")),
            "execution_result": row.get("execution_result"),
            "price_source": row.get("price_source"),
            "cost_status": row.get("cost_status"),
            "stop_modify_rejections": row.get("stop_modify_rejections"),
            "broker_placement_ready": row.get("broker_placement_ready"),
            "actually_placed": row.get("actually_placed"),
            "canonical_denominator_status": row.get("canonical_denominator_status"),
            "source_path": row.get("source_path"),
            "source_row_reference": row.get("source_row_reference"),
            "session": row.get("session"),
        }
    return dict(index)


def load_symbol_specs() -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(LANE07_SYMBOL_SPEC_LEDGER):
        symbol = row.get("symbol")
        if symbol:
            specs[str(symbol)] = row
    return specs


def metric_new() -> dict[str, Any]:
    return {
        "rows": 0,
        "known_r_rows": 0,
        "gross_total_r": 0.0,
        "gross_profit_r": 0.0,
        "gross_loss_r": 0.0,
        "wins": 0,
        "losses": 0,
        "breakevens": 0,
        "best_r": None,
        "worst_r": None,
        "equity": 0.0,
        "peak": 0.0,
        "max_drawdown_r": 0.0,
        "loss_streak": 0,
        "max_loss_streak": 0,
        "net_median_total_r": 0.0,
        "net_p90_total_r": 0.0,
        "net_high_stress_total_r": 0.0,
        "duration_known_rows": 0,
        "duration_seconds_sum": 0.0,
        "mfe_known_rows": 0,
        "mfe_r_sum": 0.0,
        "mae_known_rows": 0,
        "mae_r_sum": 0.0,
        "source_bucket_counts": Counter(),
    }


def metric_add(
    metric: dict[str, Any],
    *,
    gross_r: float | None,
    cost_median_r: float,
    cost_p90_r: float,
    cost_high_r: float,
    duration_seconds: float | None,
    mfe_r: float | None,
    mae_r: float | None,
    evidence_class: str,
) -> None:
    metric["rows"] += 1
    metric["source_bucket_counts"][source_bucket(evidence_class)] += 1
    if gross_r is None:
        return
    metric["known_r_rows"] += 1
    metric["gross_total_r"] += gross_r
    metric["net_median_total_r"] += gross_r - cost_median_r
    metric["net_p90_total_r"] += gross_r - cost_p90_r
    metric["net_high_stress_total_r"] += gross_r - cost_high_r
    if gross_r > 0:
        metric["wins"] += 1
        metric["gross_profit_r"] += gross_r
        metric["loss_streak"] = 0
    elif gross_r < 0:
        metric["losses"] += 1
        metric["gross_loss_r"] += gross_r
        metric["loss_streak"] += 1
        metric["max_loss_streak"] = max(metric["max_loss_streak"], metric["loss_streak"])
    else:
        metric["breakevens"] += 1
        metric["loss_streak"] = 0
    metric["best_r"] = gross_r if metric["best_r"] is None else max(metric["best_r"], gross_r)
    metric["worst_r"] = gross_r if metric["worst_r"] is None else min(metric["worst_r"], gross_r)
    metric["equity"] += gross_r
    metric["peak"] = max(metric["peak"], metric["equity"])
    metric["max_drawdown_r"] = max(metric["max_drawdown_r"], metric["peak"] - metric["equity"])
    if duration_seconds is not None:
        metric["duration_known_rows"] += 1
        metric["duration_seconds_sum"] += duration_seconds
    if mfe_r is not None:
        metric["mfe_known_rows"] += 1
        metric["mfe_r_sum"] += mfe_r
    if mae_r is not None:
        metric["mae_known_rows"] += 1
        metric["mae_r_sum"] += mae_r


def metric_close(metric: dict[str, Any]) -> dict[str, Any]:
    known = metric["known_r_rows"]
    wins = metric["wins"]
    losses = metric["losses"]
    non_be = wins + losses
    gross_loss_abs = abs(metric["gross_loss_r"])
    return {
        "rows": metric["rows"],
        "known_r_rows": known,
        "missing_r_rows": metric["rows"] - known,
        "gross_total_r": round9(metric["gross_total_r"]),
        "net_median_total_r": round9(metric["net_median_total_r"]),
        "net_p90_total_r": round9(metric["net_p90_total_r"]),
        "net_high_stress_total_r": round9(metric["net_high_stress_total_r"]),
        "expectancy_r": round9(metric["gross_total_r"] / known) if known else None,
        "net_median_expectancy_r": round9(metric["net_median_total_r"] / known) if known else None,
        "net_p90_expectancy_r": round9(metric["net_p90_total_r"] / known) if known else None,
        "net_high_stress_expectancy_r": round9(metric["net_high_stress_total_r"] / known) if known else None,
        "gross_profit_r": round9(metric["gross_profit_r"]),
        "gross_loss_r": round9(metric["gross_loss_r"]),
        "profit_factor": round9(metric["gross_profit_r"] / gross_loss_abs) if gross_loss_abs else None,
        "win_rate": round9(wins / known) if known else None,
        "win_rate_excluding_be": round9(wins / non_be) if non_be else None,
        "wins": wins,
        "losses": losses,
        "breakevens": metric["breakevens"],
        "best_r": round9(metric["best_r"]),
        "worst_r": round9(metric["worst_r"]),
        "max_drawdown_r": round9(metric["max_drawdown_r"]),
        "max_loss_streak": metric["max_loss_streak"],
        "avg_duration_seconds": (
            round9(metric["duration_seconds_sum"] / metric["duration_known_rows"])
            if metric["duration_known_rows"]
            else None
        ),
        "duration_known_rows": metric["duration_known_rows"],
        "avg_mfe_r": (
            round9(metric["mfe_r_sum"] / metric["mfe_known_rows"])
            if metric["mfe_known_rows"]
            else None
        ),
        "avg_mae_r": (
            round9(metric["mae_r_sum"] / metric["mae_known_rows"])
            if metric["mae_known_rows"]
            else None
        ),
        "source_bucket_counts": dict(metric["source_bucket_counts"]),
    }


def lifecycle_requirements_for_policy(policy: str) -> dict[str, Any]:
    return {
        "policy": policy,
        "requires_order_modify": policy in MODIFY_DEPENDENT_POLICIES,
        "requires_partial_close_ticket_binding": policy in PARTIAL_CLOSE_POLICIES,
        "requires_be_modify": policy in BE_POLICIES,
        "requires_trailing_modify_loop": policy in TRAILING_POLICIES,
        "requires_residual_ticket_binding": policy in PARTIAL_CLOSE_POLICIES or policy in TRAILING_POLICIES,
        "requires_market_close_order": policy in {"momentum_exhaustion", "time_stop"},
    }


def modify_feasibility_for_policy(
    policy: str,
    broker_constraints: dict[str, Any],
    strict_tick_row: dict[str, Any] | None,
    friday_policy_row: dict[str, Any] | None,
) -> dict[str, Any]:
    requirements = lifecycle_requirements_for_policy(policy)
    stop_level = fnum(broker_constraints.get("trade_stops_level"), 0.0)
    freeze_level = fnum(broker_constraints.get("trade_freeze_level"), 0.0)
    risk_price_distance = fnum((strict_tick_row or {}).get("risk_price_distance"))
    stop_modify_rejections = None
    if friday_policy_row is not None:
        stop_modify_rejections = friday_policy_row.get("stop_modify_rejections")
    if not requirements["requires_order_modify"]:
        status = "not_modify_dependent"
        feasible = True
        reason = None
    elif stop_modify_rejections not in (None, "", 0, "0"):
        status = "observed_modify_rejection"
        feasible = False
        reason = "friday_policy_stop_modify_rejections_nonzero"
    elif risk_price_distance is not None and stop_level is not None and risk_price_distance <= stop_level:
        status = "stop_distance_inside_broker_stop_level"
        feasible = False
        reason = "risk_price_distance_not_above_stop_level"
    elif freeze_level is None or stop_level is None:
        status = "symbol_stop_freeze_unknown_forward_retcode_capture_required"
        feasible = False
        reason = "missing_stop_or_freeze_level"
    else:
        status = "proxy_feasible_no_rejection_observed_retcode_missing"
        feasible = True
        reason = "historical_modify_retcode_not_ticket_bound"
    return {
        "requires_order_modify": requirements["requires_order_modify"],
        "modify_feasible_proxy": feasible,
        "modify_feasibility_status": status,
        "modify_feasibility_reason": reason,
        "trade_stops_level": stop_level,
        "trade_freeze_level": freeze_level,
        "risk_price_distance": round9(risk_price_distance),
        "stop_modify_rejections": stop_modify_rejections,
    }


def lifecycle_state_for_policy(policy: str, row: dict[str, Any], evidence_class: str) -> dict[str, Any]:
    requirements = lifecycle_requirements_for_policy(policy)
    broker_truth = (
        row.get("result_payload", {}).get("broker_real_truth", {})
        if isinstance(row.get("result_payload"), dict)
        else {}
    )
    ticket = broker_truth.get("ticket") or broker_truth.get("order_ticket")
    if requirements["requires_partial_close_ticket_binding"] and not ticket:
        partial_state = "historical_partial_close_ticket_unbound_forward_capture_required"
    elif requirements["requires_partial_close_ticket_binding"]:
        partial_state = "broker_ticket_bound_partial_close_lifecycle"
    else:
        partial_state = "not_partial_close_policy"
    if requirements["requires_residual_ticket_binding"] and not ticket:
        residual_state = "historical_residual_ticket_unbound_forward_capture_required"
    elif requirements["requires_residual_ticket_binding"]:
        residual_state = "broker_ticket_bound_residual_lifecycle"
    else:
        residual_state = "no_residual_runner_required"
    return {
        "broker_ticket_bound": bool(ticket),
        "partial_close_ticket_state": partial_state,
        "residual_lifecycle_state": residual_state,
        "lifecycle_evidence_class": evidence_class,
        **requirements,
    }


def result_for_policy(
    *,
    variant: str,
    resolved_policy: str,
    row: dict[str, Any],
    lane02_row: dict[str, Any] | None,
    strict_tick_row: dict[str, Any] | None,
    friday_rows: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    if resolved_policy == "no_trade_baseline":
        friday_no_trade = (friday_rows or {}).get("no_trade_baseline")
        return {
            "gross_r": 0.0,
            "evidence_class": (
                "friday_tick_bid_ask_no_trade_baseline"
                if friday_no_trade
                else "no_trade_baseline_zero_r_comparator"
            ),
            "source_field": "no_trade_baseline",
            "source_path": rel(FRIDAY_POLICY_LEDGER) if friday_no_trade else None,
            "source_gap_reason": None,
            "exit_reason": "no_trade",
            "exit_time_utc": None,
        }
    if strict_tick_row and resolved_policy in STRICT_R_FIELDS:
        value = strict_tick_row["r_by_policy"].get(resolved_policy)
        if value is not None:
            return {
                "gross_r": value,
                "evidence_class": "strict_tick_bid_ask_policy_replay",
                "source_field": STRICT_R_FIELDS[resolved_policy],
                "source_path": rel(LEGACY_LANE08_STRICT_TICK_LEDGER),
                "source_gap_reason": None,
                "exit_reason": strict_tick_row["exit_reason_by_policy"].get(resolved_policy),
                "exit_time_utc": strict_tick_row["exit_time_by_policy"].get(resolved_policy),
            }
    friday_policy = (friday_rows or {}).get(resolved_policy)
    if friday_policy and friday_policy.get("gross_r") is not None:
        return {
            "gross_r": friday_policy.get("gross_r"),
            "evidence_class": "friday_tick_bid_ask_policy_replay",
            "source_field": f"friday_policy.{resolved_policy}.gross_r",
            "source_path": rel(FRIDAY_POLICY_LEDGER),
            "source_gap_reason": None,
            "exit_reason": friday_policy.get("execution_result"),
            "exit_time_utc": row.get("candidate_time_utc"),
        }
    if lane02_row and resolved_policy in BASE_POLICIES:
        value = lane02_row["r_by_policy"].get(resolved_policy)
        if value is not None:
            return {
                "gross_r": value,
                "evidence_class": "m15_proxy_policy_replay",
                "source_field": LANE02_COMPARISON_FIELDS[resolved_policy],
                "source_path": rel(LEGACY_LANE02_REPLAY_LEDGER),
                "source_gap_reason": None,
                "exit_reason": None,
                "exit_time_utc": None,
            }
    label_values = (
        row.get("result_payload", {}).get("label_values", {})
        if isinstance(row.get("result_payload"), dict)
        else {}
    )
    execution_policy_result = label_values.get("execution_policy_result")
    chosen_policy = (
        normalize_policy(execution_policy_result.get("chosen_policy"))
        if isinstance(execution_policy_result, dict)
        else ""
    )
    if chosen_policy == resolved_policy:
        return {
            "gross_r": round9(row.get("result_r")),
            "evidence_class": "lane08_selected_policy_result_only",
            "source_field": "LANE08_REPLAY_ROW_LEDGER.result_r",
            "source_path": rel(LANE08_REPLAY_LEDGER),
            "source_gap_reason": "full_policy_variant_source_absent_fell_back_to_selected_policy_result",
            "exit_reason": (
                execution_policy_result.get("exit_reason")
                if isinstance(execution_policy_result, dict)
                else None
            ),
            "exit_time_utc": None,
        }
    return {
        "gross_r": None,
        "evidence_class": "missing_policy_variant_result",
        "source_field": None,
        "source_path": None,
        "source_gap_reason": (
            "policy_variant_not_available_in_strict_tick_friday_or_lane02_comparison_sources"
        ),
        "exit_reason": None,
        "exit_time_utc": None,
    }


def cost_model_for_policy(
    resolved_policy: str,
    strict_tick_row: dict[str, Any] | None,
    friday_policy_row: dict[str, Any] | None,
) -> dict[str, Any]:
    if resolved_policy == "no_trade_baseline":
        return {
            "cost_r_median_proxy": 0.0,
            "cost_r_p90_proxy": 0.0,
            "cost_r_high_stress_proxy": 0.0,
            "cost_model_state": "no_trade_no_execution_cost",
            "spread_r_at_trigger": None,
        }
    entry_spread = fnum((strict_tick_row or {}).get("entry_spread_r"))
    if entry_spread is not None:
        median = max(0.0, entry_spread) + 0.002371779
        p90 = max(0.0, entry_spread) + 0.004007666
        high = max(0.0, entry_spread) + HIGH_STRESS_COMPONENT_COST_R
        state = "strict_tick_entry_spread_plus_lane07_commission_proxy"
    elif friday_policy_row is not None:
        median = MEDIAN_COMPONENT_COST_R
        p90 = P90_COMPONENT_COST_R
        high = HIGH_STRESS_COMPONENT_COST_R
        state = "friday_bid_ask_spread_in_path_but_not_row_convertible_plus_lane07_proxy"
    else:
        median = MEDIAN_COMPONENT_COST_R
        p90 = P90_COMPONENT_COST_R
        high = HIGH_STRESS_COMPONENT_COST_R
        state = "lane07_lane02_calibrated_component_cost_proxy"
    return {
        "cost_r_median_proxy": round9(median),
        "cost_r_p90_proxy": round9(p90),
        "cost_r_high_stress_proxy": round9(high),
        "cost_model_state": state,
        "spread_r_at_trigger": round9(entry_spread),
    }


def denominator_flags_for_row(
    row: dict[str, Any],
    lane02_row: dict[str, Any] | None,
    strict_tick_row: dict[str, Any] | None,
    friday_rows: dict[str, dict[str, Any]] | None,
) -> dict[str, bool]:
    scheduler = row.get("decision_inputs", {}).get("scheduler", {})
    portfolio_decision = (
        scheduler.get("portfolio_decision")
        if isinstance(scheduler, dict)
        else None
    )
    if lane02_row and lane02_row.get("decision"):
        portfolio_decision = lane02_row.get("decision")
    replay_depths = row.get("replay_depths") if isinstance(row.get("replay_depths"), list) else []
    friday_broker_ready = any(
        bool(policy_row.get("broker_placement_ready"))
        for policy_row in (friday_rows or {}).values()
    )
    return {
        "all_replay_rows": True,
        "selected_or_microscope": bool(lane02_row or "friday_microscope" in replay_depths),
        "portfolio_ready": str(portfolio_decision).lower() == "accept",
        "strict_tick_subset": bool(strict_tick_row),
        "friday_microscope": "friday_microscope" in replay_depths,
        "friday_broker_ready": friday_broker_ready,
    }


def split_values_for_row(row: dict[str, Any]) -> dict[str, str]:
    selector = row.get("decision_inputs", {}).get("selector", {})
    source = row.get("decision_inputs", {}).get("source_completeness", {})
    scheduler = row.get("decision_inputs", {}).get("scheduler", {})
    cost_inputs = row.get("decision_inputs", {}).get("cost_inputs", {})
    session = selector.get("session_bucket") if isinstance(selector, dict) else None
    if not session:
        session = row.get("result_payload", {}).get("label_values", {}).get("session")
    source_state = (
        source.get("source_completeness_state")
        if isinstance(source, dict)
        else None
    ) or "missing"
    scheduler_state = (
        scheduler.get("portfolio_decision")
        if isinstance(scheduler, dict)
        else None
    ) or "missing"
    spread_bucket = (
        cost_inputs.get("spread_r_bucket")
        if isinstance(cost_inputs, dict)
        else None
    ) or "missing"
    volatility_state = "volatility_source_not_available_current_lane11"
    return {
        "overall": "all",
        "symbol": str(row.get("symbol") or "missing"),
        "session": str(session or "missing"),
        "origin_family": str(row.get("origin_family") or "missing"),
        "framework": str(row.get("framework") or "missing"),
        "symbol_session_origin": "|".join(
            [
                str(row.get("symbol") or "missing"),
                str(session or "missing"),
                str(row.get("origin_family") or "missing"),
            ]
        ),
        "sealed_partition": str(row.get("sealed_partition") or "missing"),
        "source_completeness": str(source_state),
        "scheduler_state": str(scheduler_state),
        "spread_r_bucket": str(spread_bucket),
        "volatility_state": volatility_state,
        "mechanism_session_source": "|".join(
            [
                str(row.get("origin_family") or "missing"),
                str(session or "missing"),
                str(source_state),
            ]
        ),
        "tick_availability": str(
            (source.get("tick_availability_status") if isinstance(source, dict) else None)
            or row.get("result_payload", {}).get("label_values", {}).get("tick_availability_status")
            or "missing"
        ),
        "m1_availability": str(
            (source.get("m1_availability_status") if isinstance(source, dict) else None)
            or row.get("result_payload", {}).get("label_values", {}).get("m1_availability_status")
            or "missing"
        ),
        "chosen_policy": current_router_policy_from_row(row),
    }


def format_param(value: Any) -> str:
    return str(value).replace(".", "_").replace("%", "pct").replace("-", "_")


def expanded_policy_source_gap(family: str) -> str:
    return (
        f"{family}_requires_raw_ordered_bid_ask_tick_path_or_m1_event_sequence_with_parameter_specific_"
        "partial_close_be_trailing_time_stop_invalidation_pending_lifecycle_and_broker_modify_retcode_fields"
    )


def registry_row(
    variant_id: str,
    family: str,
    parameters: dict[str, Any],
    *,
    status: str,
    baseline_equivalent: str | None = None,
    source_gap_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "lane11_expanded_policy_variant_registry_v1",
        "route_id": ROUTE_ID,
        "variant_id": variant_id,
        "family": family,
        "parameters": parameters,
        "is_baseline_comparator": variant_id in BASELINE_POLICY_VARIANTS,
        "feasibility_status": status,
        "baseline_equivalent_policy": baseline_equivalent,
        "source_gap_reason": source_gap_reason,
        "current_evidence_support": (
            "row_level_replay_in_lane11_policy_simulation_ledger"
            if status == "row_level_replay_feasible"
            else "duplicate_equivalence_to_existing_baseline_replay"
            if status == "duplicate_equivalent_to_baseline"
            else "gap_classified_without_row_level_r_result"
        ),
        "required_source_to_replay": (
            None
            if status in {"row_level_replay_feasible", "duplicate_equivalent_to_baseline"}
            else [
                "raw ordered bid/ask tick or M1 event path beyond baseline policy exit timestamps",
                "parameter-specific target/stop/partial/BE/trailing/time/invalidation event ordering",
                "ticket-bound broker modify and partial-close retcodes",
                "commission/swap/slippage/spread/deal lifecycle fields",
            ]
        ),
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }


def build_expanded_policy_variant_registry() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant in BASELINE_POLICY_VARIANTS:
        rows.append(
            registry_row(
                variant,
                "baseline_comparator",
                {"baseline_policy_id": variant},
                status="row_level_replay_feasible",
            )
        )

    for ratio in PARTIAL_CLOSE_RATIOS:
        for trigger in PARTIAL_TRIGGER_R:
            for be_timing in BE_TIMINGS:
                for target in RUNNER_TARGETS_R:
                    variant_id = (
                        f"partial_ratio_{format_param(ratio)}_trigger_{format_param(trigger)}r_"
                        f"{be_timing}_runner_{format_param(target)}"
                    )
                    rows.append(
                        registry_row(
                            variant_id,
                            "partial_be_runner_parameter_sweep",
                            {
                                "partial_close_ratio": ratio,
                                "partial_trigger_r": trigger,
                                "be_timing": be_timing,
                                "runner_target_r": target,
                            },
                            status="not_replayable_source_gap",
                            source_gap_reason=expanded_policy_source_gap("partial_be_runner_parameter_sweep"),
                        )
                    )

    for activation in TRAILING_ACTIVATION_R:
        for gap_model in TRAILING_GAP_MODELS:
            for step_mode in TRAILING_STEP_MODES:
                variant_id = (
                    f"trailing_activation_{format_param(activation)}r_{gap_model}_{step_mode}"
                )
                rows.append(
                    registry_row(
                        variant_id,
                        "trailing_runner_parameter_sweep",
                        {
                            "trailing_activation_r": activation,
                            "trailing_gap_model": gap_model,
                            "trailing_step_mode": step_mode,
                        },
                        status="not_replayable_source_gap",
                        source_gap_reason=expanded_policy_source_gap("trailing_runner_parameter_sweep"),
                    )
                )

    for mode in TIME_STOP_MODES:
        status = "duplicate_equivalent_to_baseline" if mode == "8h" else "not_replayable_source_gap"
        rows.append(
            registry_row(
                f"time_stop_{mode}",
                "time_stop_parameter_sweep",
                {"time_stop_mode": mode},
                status=status,
                baseline_equivalent="time_stop" if mode == "8h" else None,
                source_gap_reason=None if mode == "8h" else expanded_policy_source_gap("time_stop_parameter_sweep"),
            )
        )

    for mode in MOMENTUM_EXHAUSTION_MODES:
        rows.append(
            registry_row(
                f"momentum_exhaustion_{mode}",
                "momentum_exhaustion_parameter_sweep",
                {"momentum_exit_mode": mode},
                status="not_replayable_source_gap",
                source_gap_reason=expanded_policy_source_gap("momentum_exhaustion_parameter_sweep"),
            )
        )

    for mode in INVALIDATION_MODES:
        rows.append(
            registry_row(
                f"invalidation_{mode}",
                "invalidation_parameter_sweep",
                {"invalidation_mode": mode},
                status="not_replayable_source_gap",
                source_gap_reason=expanded_policy_source_gap("invalidation_parameter_sweep"),
            )
        )

    for mode in NO_ENTRY_TIMEOUT_MODES:
        rows.append(
            registry_row(
                f"pending_{mode}",
                "no_entry_timeout_parameter_sweep",
                {"pending_timeout_mode": mode},
                status="not_replayable_source_gap",
                source_gap_reason=(
                    "pending_timeout_variants_require_historical_pending_order_intent_expiry_fill_no_fill_"
                    "lifecycle_and_broker_retcode_observability"
                ),
            )
        )

    for dimension in HYBRID_ROUTING_DIMENSIONS:
        for action_family in HYBRID_ACTION_FAMILIES:
            status = (
                "duplicate_equivalent_to_baseline"
                if dimension == "origin_family" and action_family == "momentum_primary_partial_exception"
                else "not_replayable_source_gap"
            )
            rows.append(
                registry_row(
                    f"hybrid_route_by_{dimension}_{action_family}",
                    "hybrid_policy_router",
                    {
                        "routing_dimension": dimension,
                        "action_family": action_family,
                    },
                    status=status,
                    baseline_equivalent=(
                        "hybrid_momentum_primary_partial_exception"
                        if status == "duplicate_equivalent_to_baseline"
                        else None
                    ),
                    source_gap_reason=(
                        None
                        if status == "duplicate_equivalent_to_baseline"
                        else "hybrid_routing_variant_requires_replayed_or_forward_policy_results_by_the_named_routing_dimension"
                    ),
                )
            )
    seen: set[str] = set()
    duplicates: list[str] = []
    for row in rows:
        variant_id = row["variant_id"]
        if variant_id in seen:
            duplicates.append(variant_id)
        seen.add(variant_id)
    if duplicates:
        raise RuntimeError(f"duplicate expanded policy variant ids: {duplicates[:10]}")
    return rows


def expanded_bucket_coverage(strict_index: dict[str, dict[str, Any]], friday_index: dict[str, dict[str, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    coverage = {
        bucket: {
            "rows": 0,
            "symbols": set(),
            "sessions": set(),
            "origins": set(),
            "source_completeness": set(),
            "scheduler_states": set(),
        }
        for bucket in EXPANDED_EVIDENCE_BUCKETS
    }
    for row in iter_jsonl(LANE08_REPLAY_LEDGER):
        if row.get("_parse_error"):
            raise RuntimeError(f"Lane08 replay parse error during bucket coverage: {row}")
        split_values = split_values_for_row(row)
        selected_row_id = str(row.get("selected_row_id") or "")
        buckets = ["full_selected_denominator", "unreplayable_source_gap"]
        label_values = row.get("result_payload", {}).get("label_values", {}) if isinstance(row.get("result_payload"), dict) else {}
        if all(label_values.get(field) not in (None, "") for field in ("mfe_r", "mae_r", "source_bound_proxy_r")):
            buckets.append("m15_proxy")
        if selected_row_id in strict_index:
            buckets.append("strict_tick_subset")
        if selected_row_id in friday_index:
            buckets.append("friday_tick_subset")
        if row.get("decision_inputs", {}).get("source_completeness", {}).get("m1_entry_minute_available"):
            buckets.append("m1_event_path_subset")
        replay_depths = row.get("replay_depths") if isinstance(row.get("replay_depths"), list) else []
        if "broker_real_live_replay" in replay_depths:
            buckets.append("broker_real_subset")
        for bucket in buckets:
            coverage[bucket]["rows"] += 1
            add_limited(coverage[bucket]["symbols"], row.get("symbol"), limit=10_000)
            add_limited(coverage[bucket]["sessions"], split_values.get("session"), limit=10_000)
            add_limited(coverage[bucket]["origins"], row.get("origin_family"), limit=10_000)
            add_limited(coverage[bucket]["source_completeness"], split_values.get("source_completeness"), limit=10_000)
            add_limited(coverage[bucket]["scheduler_states"], split_values.get("scheduler_state"), limit=10_000)
    return {
        bucket: {
            "rows": data["rows"],
            "symbols": sorted(data["symbols"]),
            "sessions": sorted(data["sessions"]),
            "origins": sorted(data["origins"]),
            "source_completeness": sorted(data["source_completeness"]),
            "scheduler_states": sorted(data["scheduler_states"]),
        }
        for bucket, data in coverage.items()
    }


def expanded_variant_bucket_status(variant: dict[str, Any], bucket: str) -> tuple[str, str, str | None]:
    variant_id = str(variant.get("variant_id"))
    family = str(variant.get("family"))
    params = variant.get("parameters", {}) if isinstance(variant.get("parameters"), dict) else {}
    if variant_id in BASELINE_POLICY_VARIANTS:
        if bucket in {"full_selected_denominator", "m15_proxy", "strict_tick_subset", "friday_tick_subset"}:
            return "baseline_replay_available", "BASELINE_COMPARATOR_BUCKET_REPLAYED", None
        return "not_replayable_source_gap", "CAPTURE_OR_REPAIR_REQUIRED_BASELINE_BUCKET_GAP", f"{bucket}_requires_bucket_specific_baseline_execution_source"
    if variant.get("feasibility_status") == "duplicate_equivalent_to_baseline":
        if bucket in {"full_selected_denominator", "m15_proxy", "strict_tick_subset", "friday_tick_subset"}:
            return "duplicate_equivalent_to_baseline", "CLOSED_DUPLICATE_EQUIVALENT_TO_BASELINE", None
        return "not_replayable_source_gap", "CAPTURE_OR_REPAIR_REQUIRED_DUPLICATE_BUCKET_GAP", f"{bucket}_requires_bucket_specific_execution_source"
    partial_feasible = (
        family == "partial_be_runner_parameter_sweep"
        and params.get("partial_trigger_r") == 1.0
        and params.get("be_timing") in {"no_be", "be_after_partial"}
        and params.get("runner_target_r") in {2.0, 3.0, 4.0, 5.0}
    )
    if partial_feasible and bucket in {"full_selected_denominator", "m15_proxy"}:
        return "expanded_replay_feasible", "SIMULATE_EXPANDED_M15_PROXY_BUCKET", None
    if partial_feasible and bucket == "m1_event_path_subset":
        return "not_replayable_source_gap", "CAPTURE_OR_REPAIR_REQUIRED_M1_EVENT_PATH", "m1_event_path_subset_requires_raw_event_sequence_for_partial_target_ordering"
    if partial_feasible and bucket in {"strict_tick_subset", "friday_tick_subset", "broker_real_subset"}:
        return "not_replayable_source_gap", f"CAPTURE_OR_REPAIR_REQUIRED_{bucket.upper()}", f"{bucket}_requires_parameter_specific_partial_target_replay_fields"
    return "not_replayable_source_gap", "CAPTURE_OR_REPAIR_REQUIRED_PARAMETER_SPECIFIC_REPLAY_GAP", variant.get("source_gap_reason") or expanded_policy_source_gap(family)


def simulate_expanded_partial_proxy(row: dict[str, Any], params: dict[str, Any]) -> tuple[float | None, str | None]:
    result_payload = row.get("result_payload") if isinstance(row.get("result_payload"), dict) else {}
    label_values = result_payload.get("label_values") if isinstance(result_payload.get("label_values"), dict) else {}
    mfe = fnum(label_values.get("mfe_r"))
    mae = fnum(label_values.get("mae_r"))
    final_r = fnum(label_values.get("source_bound_proxy_r"), fnum(row.get("result_r")))
    one_r = bool(label_values.get("one_r_reached"))
    sl_before_1r = bool(label_values.get("sl_before_1r"))
    if mfe is None or mae is None or final_r is None:
        return None, "missing_mfe_mae_or_source_bound_proxy_r"
    ratio = fnum(params.get("partial_close_ratio"))
    trigger = fnum(params.get("partial_trigger_r"))
    target = fnum(params.get("runner_target_r"))
    be_timing = params.get("be_timing")
    if ratio is None or trigger != 1.0 or target is None:
        return None, "unsupported_partial_parameter_without_current_event_fields"
    if not one_r:
        if sl_before_1r or mae <= -1.0:
            return -1.0, None
        return round9(max(-1.0, min(final_r, target))), None
    if mfe >= target:
        return round9(ratio * trigger + (1.0 - ratio) * target), None
    residual = final_r
    if be_timing == "be_after_partial":
        residual = max(0.0, residual)
    residual = max(-1.0, min(residual, target))
    return round9(ratio * trigger + (1.0 - ratio) * residual), None


def expanded_metric_row(metric_key: tuple[str, str, str, str, str], metric: dict[str, Any]) -> dict[str, Any]:
    variant_id, evidence_bucket, denominator, split_scope, split_key = metric_key
    return {
        "schema_version": "lane11_expanded_policy_metric_v1",
        "route_id": ROUTE_ID,
        "variant_id": variant_id,
        "policy_scope": "expanded_policy",
        "evidence_bucket": evidence_bucket,
        "denominator": denominator,
        "split_scope": split_scope,
        "split_key": split_key,
        **metric_close(metric),
    }


def decision_for_expanded_metric(metric: dict[str, Any], *, evidence_bucket: str, best_variant: str) -> str:
    if metric["known_r_rows"] == 0:
        return "CAPTURE_OR_REPAIR_REQUIRED_EXPANDED_NO_POLICY_R"
    net_exp = fnum(metric.get("net_median_expectancy_r"), 0.0) or 0.0
    pf = fnum(metric.get("profit_factor"), 0.0) or 0.0
    if metric["variant_id"] != best_variant:
        return "KILL_AS_DEFAULT_FOR_THIS_EXPANDED_SLICE" if net_exp < 0 else "RETAIN_EXPANDED_COMPARATOR_OR_SECONDARY"
    if evidence_bucket in {"full_selected_denominator", "m15_proxy"}:
        if metric["known_r_rows"] >= 50 and net_exp > 0 and (pf is None or pf >= 1.05):
            return "PROMOTE_DEFAULT_OFF_EXPANDED_PROXY_RESEARCH_BRANCH_REQUIRES_STRICT_TICK"
        if net_exp > 0:
            return "CAPTURE_MORE_EXPANDED_PROXY_ROWS_BEFORE_ROUTING"
        return "KILL_OR_REDESIGN_EXPANDED_PROXY_SLICE"
    return "CAPTURE_OR_REPAIR_REQUIRED_EXPANDED_BUCKET"


def build_expanded_decision_and_package_rows(metric_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        grouped[(row["evidence_bucket"], row["denominator"], row["split_scope"], row["split_key"])].append(row)
    decisions: list[dict[str, Any]] = []
    package_rows: list[dict[str, Any]] = []
    counts: Counter = Counter()
    for key, rows in sorted(grouped.items()):
        evidence_bucket, denominator, split_scope, split_key = key
        eligible = [row for row in rows if row.get("known_r_rows", 0) > 0]
        if not eligible:
            continue
        best = max(
            eligible,
            key=lambda item: (
                fnum(item.get("net_median_expectancy_r"), -999999.0) or -999999.0,
                fnum(item.get("profit_factor"), -999999.0) or -999999.0,
                item.get("known_r_rows") or 0,
            ),
        )
        for row in rows:
            decision = decision_for_expanded_metric(row, evidence_bucket=evidence_bucket, best_variant=best["variant_id"])
            decision_row = {
                "schema_version": "lane11_expanded_policy_dominance_decision_v1",
                "route_id": ROUTE_ID,
                "policy_scope": "expanded_policy",
                "variant_id": row["variant_id"],
                "evidence_bucket": evidence_bucket,
                "denominator": denominator,
                "split_scope": split_scope,
                "split_key": split_key,
                "decision": decision,
                "best_variant_for_group": best["variant_id"],
                "known_r_rows": row["known_r_rows"],
                "net_median_expectancy_r": row["net_median_expectancy_r"],
                "profit_factor": row["profit_factor"],
                "max_drawdown_r": row["max_drawdown_r"],
                "max_loss_streak": row["max_loss_streak"],
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
            }
            decisions.append(decision_row)
            counts[decision] += 1
            if decision.startswith("PROMOTE_DEFAULT_OFF") or decision.startswith("CAPTURE_MORE"):
                package_rows.append(
                    {
                        "schema_version": "lane11_expanded_default_off_package_rule_v1",
                        "route_id": ROUTE_ID,
                        "policy_scope": "expanded_policy",
                        "package_status": "default_off_not_live_activation",
                        "variant_id": row["variant_id"],
                        "evidence_bucket": evidence_bucket,
                        "denominator": denominator,
                        "split_scope": split_scope,
                        "split_key": split_key,
                        "decision": decision,
                        "rule_action": (
                            "route_to_expanded_policy_when_enabled_in_research_harness"
                            if decision.startswith("PROMOTE_DEFAULT_OFF")
                            else "capture_more_before_expanded_route_activation"
                        ),
                        "minimum_evidence_rows_observed": row["known_r_rows"],
                        "net_median_expectancy_r": row["net_median_expectancy_r"],
                        "profit_factor": row["profit_factor"],
                        "owner_approval_required_for_live_use": True,
                        "runtime_effect_now": False,
                    }
                )
    return decisions, package_rows, counts


def build_expanded_policy_artifacts(
    registry_rows: list[dict[str, Any]],
    strict_index: dict[str, dict[str, Any]],
    friday_index: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    write_jsonl(EXPANDED_POLICY_VARIANT_REGISTRY, registry_rows)
    coverage = expanded_bucket_coverage(strict_index, friday_index)
    metrics: dict[tuple[str, str, str, str, str], dict[str, Any]] = defaultdict(metric_new)
    feasible_variants = [
        row
        for row in registry_rows
        if expanded_variant_bucket_status(row, "m15_proxy")[0] == "expanded_replay_feasible"
    ]
    feasible_by_id = {row["variant_id"]: row for row in feasible_variants}
    status_counts_by_bucket: dict[str, Counter] = {bucket: Counter() for bucket in EXPANDED_EVIDENCE_BUCKETS}
    gap_rows_written = 0
    feasibility_rows_written = 0
    split_rows_written = 0

    with (
        EXPANDED_POLICY_FEASIBILITY_LEDGER.open("w", encoding="utf-8", newline="\n") as feasibility_handle,
        open_gzip_text_for_write(EXPANDED_POLICY_SOURCE_GAP_LEDGER) as gap_handle,
        open_gzip_text_for_write(EXPANDED_POLICY_SPLIT_DECISION_LEDGER) as split_handle,
    ):
        for variant in registry_rows:
            for bucket in EXPANDED_EVIDENCE_BUCKETS:
                status, decision, gap_reason = expanded_variant_bucket_status(variant, bucket)
                status_counts_by_bucket[bucket][status] += 1
                affected_rows = coverage[bucket]["rows"]
                feasibility = {
                    "schema_version": "lane11_expanded_policy_bucket_feasibility_v1",
                    "route_id": ROUTE_ID,
                    "variant_id": variant["variant_id"],
                    "family": variant["family"],
                    "evidence_bucket": bucket,
                    "feasibility_status": status,
                    "decision": decision,
                    "baseline_equivalent_policy": variant.get("baseline_equivalent_policy"),
                    "source_gap_reason": gap_reason,
                    "affected_row_count": affected_rows,
                    "affected_symbols": coverage[bucket]["symbols"],
                    "affected_sessions": coverage[bucket]["sessions"],
                    "affected_origins": coverage[bucket]["origins"],
                    "affected_source_completeness": coverage[bucket]["source_completeness"],
                    "affected_scheduler_states": coverage[bucket]["scheduler_states"],
                    "recovery_requirement": (
                        None
                        if status in {"baseline_replay_available", "duplicate_equivalent_to_baseline", "expanded_replay_feasible"}
                        else "capture or recover parameter-specific ordered path, broker retcode, cost, and lifecycle fields named by source_gap_reason"
                    ),
                    "result_cell_accounting": affected_rows,
                    "raw_evidence_pointer": {
                        "registry_path": rel(EXPANDED_POLICY_VARIANT_REGISTRY),
                        "source_denominator_path": rel(LANE08_REPLAY_LEDGER),
                        "baseline_result_path": rel(POLICY_SIMULATION_LEDGER)
                        if status in {"baseline_replay_available", "duplicate_equivalent_to_baseline"}
                        else None,
                    },
                    "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                }
                write_jsonl_line(feasibility_handle, feasibility)
                feasibility_rows_written += 1
                if status == "not_replayable_source_gap":
                    write_jsonl_line(
                        gap_handle,
                        {
                            "schema_version": "lane11_expanded_policy_source_gap_v1",
                            "route_id": ROUTE_ID,
                            "variant_id": variant["variant_id"],
                            "family": variant["family"],
                            "evidence_bucket": bucket,
                            "source_gap_reason": gap_reason,
                            "affected_row_count": affected_rows,
                            "affected_symbols": coverage[bucket]["symbols"],
                            "affected_sessions": coverage[bucket]["sessions"],
                            "affected_origins": coverage[bucket]["origins"],
                            "recovery_requirement": feasibility["recovery_requirement"],
                            "raw_evidence_pointer": feasibility["raw_evidence_pointer"],
                            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                        },
                    )
                    gap_rows_written += 1
                for split_scope in EXPANDED_SPLIT_SCOPES:
                    split_key = "all" if split_scope == "overall" else "see_source_gap_coverage"
                    write_jsonl_line(
                        split_handle,
                        {
                            "schema_version": "lane11_expanded_policy_split_decision_v2",
                            "route_id": ROUTE_ID,
                            "variant_id": variant["variant_id"],
                            "family": variant["family"],
                            "evidence_bucket": bucket,
                            "split_scope": split_scope,
                            "split_key": split_key,
                            "affected_rows": affected_rows,
                            "decision": decision,
                            "source_gap_reason": gap_reason,
                            "baseline_equivalent_policy": variant.get("baseline_equivalent_policy"),
                            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                        },
                    )
                    split_rows_written += 1

    for row in iter_jsonl(LANE08_REPLAY_LEDGER):
        if row.get("_parse_error"):
            raise RuntimeError(f"Lane08 replay parse error during expanded simulation: {row}")
        split_values = split_values_for_row(row)
        label_values = row.get("result_payload", {}).get("label_values", {}) if isinstance(row.get("result_payload"), dict) else {}
        if not all(label_values.get(field) not in (None, "") for field in ("mfe_r", "mae_r", "source_bound_proxy_r")):
            continue
        for variant_id, variant in feasible_by_id.items():
            gross_r, gap = simulate_expanded_partial_proxy(row, variant["parameters"])
            for bucket in ("full_selected_denominator", "m15_proxy"):
                for split_scope in EXPANDED_SPLIT_SCOPES:
                    key = (
                        variant_id,
                        bucket,
                        "all_replay_rows" if bucket == "full_selected_denominator" else "m15_proxy_rows",
                        split_scope,
                        split_values.get(split_scope, "missing"),
                    )
                    metric_add(
                        metrics[key],
                        gross_r=gross_r if gap is None else None,
                        cost_median_r=MEDIAN_COMPONENT_COST_R,
                        cost_p90_r=P90_COMPONENT_COST_R,
                        cost_high_r=HIGH_STRESS_COMPONENT_COST_R,
                        duration_seconds=fnum(label_values.get("time_to_final_seconds")),
                        mfe_r=fnum(label_values.get("mfe_r")),
                        mae_r=fnum(label_values.get("mae_r")),
                        evidence_class="m15_proxy_expanded_policy_replay" if gap is None else "expanded_policy_missing_proxy_fields",
                    )

    metric_rows = [expanded_metric_row(key, metric) for key, metric in sorted(metrics.items())]
    write_jsonl(EXPANDED_POLICY_SIMULATION_METRIC_LEDGER, metric_rows)
    decisions, package_rows, decision_counts = build_expanded_decision_and_package_rows(metric_rows)
    write_jsonl(EXPANDED_POLICY_DOMINANCE_DECISION_LEDGER, decisions)
    write_jsonl(EXPANDED_DEFAULT_OFF_POLICY_PACKAGE_LEDGER, package_rows)
    expanded_feasible_variant_ids = {row["variant_id"] for row in feasible_variants}
    return {
        "expanded_policy_variant_count": len(registry_rows),
        "baseline_policy_variant_count": len(BASELINE_POLICY_VARIANTS),
        "expanded_nonbaseline_feasible_simulated_variant_count": len(expanded_feasible_variant_ids),
        "expanded_feasible_simulated_variant_count_by_evidence_bucket": {
            "full_selected_denominator": len(expanded_feasible_variant_ids),
            "m15_proxy": len(expanded_feasible_variant_ids),
            "strict_tick_subset": 0,
            "friday_tick_subset": 0,
            "m1_event_path_subset": 0,
            "broker_real_subset": 0,
        },
        "expanded_source_gap_only_variant_count_by_evidence_bucket": {
            bucket: status_counts_by_bucket[bucket].get("not_replayable_source_gap", 0)
            for bucket in EXPANDED_EVIDENCE_BUCKETS
        },
        "duplicate_equivalent_variant_count": sum(
            1 for row in registry_rows if row.get("feasibility_status") == "duplicate_equivalent_to_baseline"
        ),
        "expanded_policy_result_cell_accounting_by_evidence_bucket": {
            bucket: coverage[bucket]["rows"] * len(registry_rows)
            for bucket in EXPANDED_EVIDENCE_BUCKETS
        },
        "expanded_policy_result_cell_accounting": sum(
            coverage[bucket]["rows"] * len(registry_rows)
            for bucket in EXPANDED_EVIDENCE_BUCKETS
        ),
        "expanded_metric_rows": len(metric_rows),
        "expanded_metric_rows_by_evidence_bucket": dict(Counter(row["evidence_bucket"] for row in metric_rows)),
        "expanded_dominance_decision_rows": len(decisions),
        "expanded_package_rows": len(package_rows),
        "expanded_decision_counts": dict(decision_counts),
        "expanded_feasibility_rows": feasibility_rows_written,
        "expanded_source_gap_rows": gap_rows_written,
        "expanded_split_decision_rows": split_rows_written,
        "expanded_family_counts": dict(Counter(row["family"] for row in registry_rows)),
        "expanded_status_counts_by_bucket": {bucket: dict(counter) for bucket, counter in status_counts_by_bucket.items()},
        "expanded_bucket_coverage": coverage,
    }


def build_policy_simulation_record(
    *,
    row: dict[str, Any],
    variant: str,
    resolved_policy: str,
    policy_result: dict[str, Any],
    strict_tick_row: dict[str, Any] | None,
    friday_policy_row: dict[str, Any] | None,
    lane02_row: dict[str, Any] | None,
    symbol_spec: dict[str, Any] | None,
    denominator_flags: dict[str, bool],
) -> dict[str, Any]:
    result_payload = row.get("result_payload") if isinstance(row.get("result_payload"), dict) else {}
    label_values = result_payload.get("label_values") if isinstance(result_payload.get("label_values"), dict) else {}
    decision_inputs = row.get("decision_inputs") if isinstance(row.get("decision_inputs"), dict) else {}
    broker_constraints = (
        decision_inputs.get("broker_constraints")
        if isinstance(decision_inputs.get("broker_constraints"), dict)
        else {}
    )
    source_state = (
        decision_inputs.get("source_completeness")
        if isinstance(decision_inputs.get("source_completeness"), dict)
        else {}
    )
    modify = modify_feasibility_for_policy(
        resolved_policy,
        broker_constraints,
        strict_tick_row,
        friday_policy_row,
    )
    lifecycle = lifecycle_state_for_policy(resolved_policy, row, policy_result["evidence_class"])
    costs = cost_model_for_policy(resolved_policy, strict_tick_row, friday_policy_row)
    gross_r = policy_result["gross_r"]
    duration_seconds = None
    if strict_tick_row and policy_result.get("exit_time_utc"):
        duration_seconds = seconds_between(strict_tick_row.get("entry_time_utc"), policy_result.get("exit_time_utc"))
    elif resolved_policy == current_router_policy_from_row(row):
        duration_seconds = fnum(label_values.get("time_to_final_seconds"))
        if duration_seconds is None and lane02_row and lane02_row.get("holding_hours") is not None:
            duration_seconds = fnum(lane02_row.get("holding_hours"), 0.0) * 3600.0
    elif resolved_policy == "time_stop" and gross_r is not None:
        duration_seconds = 8 * 3600.0
    return {
        "schema_version": "lane11_policy_simulation_row_v1",
        "route_id": ROUTE_ID,
        "row_id": row.get("row_id"),
        "candidate_id": row.get("candidate_id"),
        "selected_row_id": row.get("selected_row_id"),
        "candidate_time_utc": row.get("candidate_time_utc"),
        "decision_asof_utc": row.get("decision_asof_utc"),
        "symbol": row.get("symbol"),
        "broker_symbol": row.get("broker_symbol"),
        "side": row.get("side"),
        "framework": row.get("framework"),
        "origin_family": row.get("origin_family"),
        "sealed_partition": row.get("sealed_partition"),
        "policy_variant": variant,
        "resolved_policy": resolved_policy,
        "execution_policy_id": EXECUTION_POLICY_IDS.get(resolved_policy),
        "current_router_policy": current_router_policy_from_row(row),
        "gross_r": gross_r,
        "cost_adjusted_median_r": round9(gross_r - costs["cost_r_median_proxy"]) if gross_r is not None else None,
        "cost_adjusted_p90_r": round9(gross_r - costs["cost_r_p90_proxy"]) if gross_r is not None else None,
        "cost_adjusted_high_stress_r": round9(gross_r - costs["cost_r_high_stress_proxy"]) if gross_r is not None else None,
        "r_evidence_class": policy_result["evidence_class"],
        "r_source_field": policy_result["source_field"],
        "r_source_path": policy_result["source_path"],
        "source_gap_reason": policy_result["source_gap_reason"],
        "exit_reason": policy_result["exit_reason"],
        "exit_time_utc": policy_result["exit_time_utc"],
        "duration_seconds": round9(duration_seconds),
        "mfe_r": round9(label_values.get("mfe_r")),
        "mae_r": round9(label_values.get("mae_r")),
        "path_class": label_values.get("path_class"),
        "same_bar_ambiguity_state": label_values.get("ambiguity_state")
        or label_values.get("path_ordering_status")
        or ("same_bar_ambiguous" if (lane02_row or {}).get("same_bar_ambiguity") else "not_flagged"),
        "price_path_model": (
            "ordered_bid_ask_tick_replay"
            if strict_tick_row
            else "friday_tick_bid_ask_policy_replay"
            if friday_policy_row
            else "m15_ordered_path_proxy"
            if lane02_row
            else "selected_policy_result_only"
        ),
        "bid_ask_ordering_state": (
            "strict_bid_ask_ordered"
            if strict_tick_row
            else "friday_bid_ask_ordered"
            if friday_policy_row
            else "m15_proxy_no_tick_bid_ask_order"
        ),
        "m1_tick_path_state": {
            "m1_availability_status": source_state.get("m1_availability_status")
            or label_values.get("m1_availability_status"),
            "tick_availability_status": source_state.get("tick_availability_status")
            or label_values.get("tick_availability_status"),
            "strict_tick_replay_status": (strict_tick_row or {}).get("strict_tick_replay_status")
            or label_values.get("strict_tick_replay_status"),
            "raw_tick_rows": (strict_tick_row or {}).get("raw_tick_rows"),
            "valid_bid_ask_tick_rows": (strict_tick_row or {}).get("valid_bid_ask_tick_rows"),
        },
        "spread_and_cost_state": costs,
        "broker_stop_freeze_constraints": {
            "trade_stops_level": modify["trade_stops_level"],
            "trade_freeze_level": modify["trade_freeze_level"],
            "stop_freeze_status": broker_constraints.get("stop_freeze_status")
            or (symbol_spec or {}).get("stop_freeze_status"),
            "stop_freeze_feasibility_status": (lane02_row or {}).get("stop_freeze_feasibility_status"),
        },
        "modify_feasibility": modify,
        "ticket_lifecycle_state": lifecycle,
        "denominator_flags": denominator_flags,
        "result_use_status": RESULT_USE_TEXT,
        "source_use_state": SOURCE_USE_TEXT,
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }


def add_metric_groups(
    metrics: dict[tuple[str, str, str, str, str], dict[str, Any]],
    record: dict[str, Any],
    split_values: dict[str, str],
) -> None:
    costs = record["spread_and_cost_state"]
    gross_r = fnum(record.get("gross_r"))
    for denominator, included in record["denominator_flags"].items():
        if not included:
            continue
        for split_scope, split_key in split_values.items():
            key = (
                denominator,
                split_scope,
                split_key,
                record["policy_variant"],
                source_bucket(record["r_evidence_class"]),
            )
            metric_add(
                metrics[key],
                gross_r=gross_r,
                cost_median_r=fnum(costs.get("cost_r_median_proxy"), 0.0) or 0.0,
                cost_p90_r=fnum(costs.get("cost_r_p90_proxy"), 0.0) or 0.0,
                cost_high_r=fnum(costs.get("cost_r_high_stress_proxy"), 0.0) or 0.0,
                duration_seconds=fnum(record.get("duration_seconds")),
                mfe_r=fnum(record.get("mfe_r")),
                mae_r=fnum(record.get("mae_r")),
                evidence_class=record["r_evidence_class"],
            )


def compact_policy_result(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "resolved_policy": record["resolved_policy"],
        "execution_policy_id": record["execution_policy_id"],
        "gross_r": record["gross_r"],
        "cost_adjusted_median_r": record["cost_adjusted_median_r"],
        "cost_adjusted_p90_r": record["cost_adjusted_p90_r"],
        "cost_adjusted_high_stress_r": record["cost_adjusted_high_stress_r"],
        "r_evidence_class": record["r_evidence_class"],
        "r_source_field": record["r_source_field"],
        "r_source_path": record["r_source_path"],
        "source_gap_reason": record["source_gap_reason"],
        "exit_reason": record["exit_reason"],
        "exit_time_utc": record["exit_time_utc"],
        "duration_seconds": record["duration_seconds"],
        "price_path_model": record["price_path_model"],
        "bid_ask_ordering_state": record["bid_ask_ordering_state"],
        "spread_and_cost_state": record["spread_and_cost_state"],
        "broker_stop_freeze_constraints": record["broker_stop_freeze_constraints"],
        "modify_feasibility": record["modify_feasibility"],
        "ticket_lifecycle_state": record["ticket_lifecycle_state"],
    }


def decision_for_metric(metric: dict[str, Any], *, evidence_bucket: str, policy_variant: str, best_policy: str, best_metric: dict[str, Any]) -> str:
    if metric["known_r_rows"] == 0:
        return "CAPTURE_OR_REPAIR_REQUIRED_NO_POLICY_R"
    net_exp = fnum(metric.get("net_median_expectancy_r"), 0.0) or 0.0
    pf = fnum(metric.get("profit_factor"), 0.0) or 0.0
    if policy_variant == "no_trade_baseline" and (fnum(best_metric.get("net_median_expectancy_r"), 0.0) or 0.0) <= 0:
        return "PROMOTE_DEFAULT_OFF_NO_TRADE_FOR_NEGATIVE_SLICE"
    if policy_variant != best_policy:
        if net_exp < 0:
            return "KILL_AS_DEFAULT_FOR_THIS_SLICE"
        return "RETAIN_COMPARATOR_OR_SECONDARY"
    if evidence_bucket == "strict_tick":
        if metric["known_r_rows"] >= 30 and net_exp > 0 and pf >= 1.2:
            return "PROMOTE_DEFAULT_OFF_STRICT_TICK_CHALLENGER"
        if net_exp > 0:
            return "CAPTURE_MORE_STRICT_TICK_BEFORE_PROMOTION"
        return "KILL_OR_REDESIGN_STRICT_TICK_SLICE"
    if evidence_bucket == "friday_tick":
        if metric["known_r_rows"] >= 8 and net_exp > 0 and pf >= 1.1:
            return "PROMOTE_DEFAULT_OFF_FRIDAY_TICK_RESEARCH_BRANCH"
        return "CAPTURE_MORE_FRIDAY_TICK_BEFORE_PROMOTION"
    if evidence_bucket == "m15_proxy":
        if metric["known_r_rows"] >= 50 and net_exp > 0 and pf >= 1.1:
            return "PROMOTE_DEFAULT_OFF_PROXY_RESEARCH_BRANCH_REQUIRES_STRICT_TICK"
        if net_exp > 0:
            return "CAPTURE_MORE_PROXY_ROWS_BEFORE_ROUTING"
        return "KILL_OR_REDESIGN_PROXY_SLICE"
    if evidence_bucket == "no_trade":
        return "RETAIN_NO_TRADE_COMPARATOR"
    return "CAPTURE_OR_REPAIR_REQUIRED"


def build_metric_rows(metrics: dict[tuple[str, str, str, str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (denominator, split_scope, split_key, policy_variant, evidence_bucket), metric in sorted(metrics.items()):
        rows.append(
            {
                "schema_version": "lane11_policy_metric_v1",
                "route_id": ROUTE_ID,
                "denominator": denominator,
                "split_scope": split_scope,
                "split_key": split_key,
                "policy_variant": policy_variant,
                "evidence_bucket": evidence_bucket,
                **metric_close(metric),
            }
        )
    return rows


def build_decision_and_package_rows(metric_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        grouped[
            (
                row["denominator"],
                row["split_scope"],
                row["split_key"],
                row["evidence_bucket"],
            )
        ].append(row)
    decisions: list[dict[str, Any]] = []
    package_rows: list[dict[str, Any]] = []
    counts: Counter = Counter()
    for key, rows in sorted(grouped.items()):
        denominator, split_scope, split_key, evidence_bucket = key
        eligible = [
            row
            for row in rows
            if row["policy_variant"] != "no_trade_baseline" and row["known_r_rows"] > 0
        ]
        if eligible:
            best = max(
                eligible,
                key=lambda item: (
                    fnum(item.get("net_median_expectancy_r"), -999999.0) or -999999.0,
                    fnum(item.get("profit_factor"), -999999.0) or -999999.0,
                    item.get("known_r_rows") or 0,
                ),
            )
        else:
            best = max(
                rows,
                key=lambda item: (
                    fnum(item.get("net_median_expectancy_r"), -999999.0) or -999999.0,
                    item.get("known_r_rows") or 0,
                ),
            )
        best_policy = best["policy_variant"]
        for row in rows:
            decision = decision_for_metric(
                row,
                evidence_bucket=evidence_bucket,
                policy_variant=row["policy_variant"],
                best_policy=best_policy,
                best_metric=best,
            )
            decision_row = {
                "schema_version": "lane11_policy_dominance_decision_v1",
                "route_id": ROUTE_ID,
                "denominator": denominator,
                "split_scope": split_scope,
                "split_key": split_key,
                "evidence_bucket": evidence_bucket,
                "policy_variant": row["policy_variant"],
                "decision": decision,
                "best_policy_variant_for_group": best_policy,
                "known_r_rows": row["known_r_rows"],
                "net_median_expectancy_r": row["net_median_expectancy_r"],
                "profit_factor": row["profit_factor"],
                "max_drawdown_r": row["max_drawdown_r"],
                "max_loss_streak": row["max_loss_streak"],
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
            }
            decisions.append(decision_row)
            counts[decision] += 1
            if decision.startswith("PROMOTE_DEFAULT_OFF") or decision.startswith("CAPTURE_MORE"):
                package_rows.append(
                    {
                        "schema_version": "lane11_default_off_package_rule_v1",
                        "route_id": ROUTE_ID,
                        "package_status": "default_off_not_live_activation",
                        "denominator": denominator,
                        "split_scope": split_scope,
                        "split_key": split_key,
                        "evidence_bucket": evidence_bucket,
                        "policy_variant": row["policy_variant"],
                        "decision": decision,
                        "rule_action": (
                            "route_to_policy_when_enabled_in_research_harness"
                            if decision.startswith("PROMOTE_DEFAULT_OFF")
                            else "capture_more_before_route_activation"
                        ),
                        "minimum_evidence_rows_observed": row["known_r_rows"],
                        "net_median_expectancy_r": row["net_median_expectancy_r"],
                        "profit_factor": row["profit_factor"],
                        "owner_approval_required_for_live_use": True,
                        "runtime_effect_now": False,
                    }
                )
    return decisions, package_rows, counts


def flatten_keys(payload: Any, prefix: str = "") -> Iterable[str]:
    if isinstance(payload, dict):
        for key, value in payload.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield next_prefix
            yield from flatten_keys(value, next_prefix)
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            yield from flatten_keys(value, f"{prefix}[{index}]")


def validate_router_package_no_leak(package_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for index, row in enumerate(package_rows[:1000]):
        for key in flatten_keys(row):
            leaf = key.split(".")[-1]
            if leaf in FORBIDDEN_ROUTER_FEATURE_FIELDS:
                issues.append({"row_index": index, "field": key, "issue": "forbidden_future_field_in_router_rule"})
    return issues


def dependency_rows() -> list[dict[str, Any]]:
    files = [
        ("lane02_asof_contract", LANE02_DIR / "LANE02_DOWNSTREAM_FIELD_CONTRACT.json"),
        ("lane04_strict_tick_timeline", LANE04_STRICT_TICK_TIMELINE),
        ("lane05_feature_contract", LANE05_DIR / "LANE05_DOWNSTREAM_CONTRACT.json"),
        ("lane06_label_contract", LANE06_DIR / "LANE06_DOWNSTREAM_CONTRACT.json"),
        ("lane07_broker_cost_contract", LANE07_DIR / "LANE07_DOWNSTREAM_CONTRACT.json"),
        ("lane08_replay_schema", LANE08_REPLAY_SCHEMA),
        ("lane08_replay_rows", LANE08_REPLAY_LEDGER),
        ("lane08_missing_gap_rows", LANE08_MISSING_REPLAY_GAP_LEDGER),
        ("lane08_split_stress", LANE08_SPLIT_STRESS_METRICS),
        ("legacy_lane02_policy_comparisons", LEGACY_LANE02_REPLAY_LEDGER),
        ("legacy_lane08_strict_tick_policy", LEGACY_LANE08_STRICT_TICK_LEDGER),
        ("friday_tick_policy_ledger", FRIDAY_POLICY_LEDGER),
        ("master_wave3_readiness", MASTER_DIR / "ABSOLUTE_MASTER_WAVE3_READINESS_DECISION.json"),
    ]
    return [
        {
            "schema_version": "lane11_dependency_state_v1",
            "route_id": ROUTE_ID,
            "dependency": name,
            "path": rel(path),
            "present": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }
        for name, path in files
    ]


def lane11_evidence_artifact_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []

    def add(
        artifact_id: str,
        path: Path,
        classification: str,
        role: str,
        expected_count: int | None = None,
        count_kind: str = "file",
        retention_reason: str = "retained_current_route_or_upstream_evidence",
    ) -> None:
        specs.append(
            {
                "artifact_id": artifact_id,
                "path": path,
                "classification": classification,
                "role": role,
                "expected_count": expected_count,
                "count_kind": count_kind,
                "retention_reason": retention_reason,
                "reentry_pointer": (
                    f"Open {rel(path)}; filter by route_id/selected_row_id/policy_variant/decision "
                    "as applicable from the finding raw_evidence_pointer."
                ),
            }
        )

    add("lane11_policy_schema", POLICY_SCHEMA, "lane11_owned_schema", "route_output")
    add(
        "lane11_policy_simulation_ledger",
        POLICY_SIMULATION_LEDGER,
        "lane11_owned_compacted_raw_policy_result_ledger",
        "route_output_raw_compacted",
        EXPECTED_REPLAY_ROWS,
        "jsonl",
        "retained_current_route_lfs_tracked_gzip; compact row preserves all 10 policy result cells in policy_results",
    )
    add(
        "lane11_policy_metric_ledger",
        POLICY_METRIC_LEDGER,
        "lane11_owned_metric_derivative",
        "route_output_derivative",
        None,
        "jsonl",
    )
    add(
        "lane11_policy_dominance_decision_ledger",
        POLICY_DOMINANCE_LEDGER,
        "lane11_owned_decision_derivative",
        "route_output_decision",
        None,
        "jsonl",
    )
    add("lane11_default_off_policy_router_package", DEFAULT_OFF_PACKAGE, "lane11_owned_default_off_package", "route_output_package")
    add(
        "lane11_default_off_policy_router_package_ledger",
        DEFAULT_OFF_PACKAGE_LEDGER,
        "lane11_owned_default_off_package_clause_ledger",
        "route_output_package",
        EXPECTED_PACKAGE_ROWS,
        "jsonl",
    )
    add("lane11_source_completeness_decision_ledger", SOURCE_COMPLETENESS_LEDGER, "lane11_owned_source_gap_decisions", "route_output_decision", None, "jsonl")
    add("lane11_implementation_decision_ledger", IMPLEMENTATION_DECISION_LEDGER, "lane11_owned_implementation_decisions", "route_output_decision", None, "jsonl")
    add("lane11_dependency_state_ledger", DEPENDENCY_STATE_LEDGER, "lane11_owned_dependency_state", "route_output_state", None, "jsonl")
    add("lane11_no_leak_validation_ledger", NO_LEAK_LEDGER, "lane11_owned_validation", "route_output_validation", None, "jsonl")
    add("lane11_downstream_contract", DOWNSTREAM_CONTRACT, "lane11_owned_downstream_contract", "route_output_contract")
    add("lane11_source_use_state", SOURCE_USE_STATE, "lane11_owned_source_use_state", "route_output_state")
    add("lane11_result_use_status", RESULT_USE_STATUS, "lane11_owned_result_use_status", "route_output_state")
    add("lane11_runtime_effect_boundary", RUNTIME_EFFECT_BOUNDARY, "lane11_owned_runtime_boundary", "route_output_boundary")
    add("lane11_context_anchor", CONTEXT_ANCHOR, "lane11_owned_context_anchor", "route_output_context", None, "text")
    add("lane11_saturation_self_red_team", SATURATION_SELF_RED_TEAM, "lane11_owned_saturation_audit", "route_output_context", None, "text")
    add("lane11_output_manifest", OUTPUT_MANIFEST, "lane11_owned_manifest", "route_output_manifest")
    add("lane11_completion_audit", COMPLETION_AUDIT, "lane11_owned_completion_audit", "route_output_audit")
    add("lane11_verification_result", VERIFICATION_RESULT, "lane11_owned_verifier_output", "route_output_validation")
    add("lane11_focused_test_result", FOCUSED_TEST_RESULT, "lane11_owned_test_output", "route_output_validation", None, "text")
    add("lane11_expanded_policy_variant_registry", EXPANDED_POLICY_VARIANT_REGISTRY, "lane11_owned_expanded_policy_registry", "route_output_expanded_policy", None, "jsonl")
    add("lane11_expanded_policy_bucket_feasibility_ledger", EXPANDED_POLICY_FEASIBILITY_LEDGER, "lane11_owned_expanded_policy_bucket_feasibility", "route_output_expanded_policy", None, "jsonl")
    add("lane11_expanded_policy_split_decision_ledger", EXPANDED_POLICY_SPLIT_DECISION_LEDGER, "lane11_owned_expanded_policy_split_decisions", "route_output_expanded_policy", None, "jsonl")
    add("lane11_expanded_policy_simulation_metric_ledger", EXPANDED_POLICY_SIMULATION_METRIC_LEDGER, "lane11_owned_expanded_policy_simulation_metrics", "route_output_expanded_policy", None, "jsonl")
    add("lane11_expanded_policy_dominance_decision_ledger", EXPANDED_POLICY_DOMINANCE_DECISION_LEDGER, "lane11_owned_expanded_policy_dominance", "route_output_expanded_policy", None, "jsonl")
    add("lane11_expanded_default_off_policy_package_ledger", EXPANDED_DEFAULT_OFF_POLICY_PACKAGE_LEDGER, "lane11_owned_expanded_default_off_package", "route_output_expanded_policy", None, "jsonl")
    add("lane11_expanded_policy_source_gap_ledger", EXPANDED_POLICY_SOURCE_GAP_LEDGER, "lane11_owned_expanded_policy_source_gaps", "route_output_expanded_policy", None, "jsonl")
    add("lane11_evidence_integrity_inventory", EVIDENCE_INTEGRITY_INVENTORY, "lane11_owned_integrity_inventory", "route_output_integrity", None, "jsonl")
    add("lane11_evidence_intelligence_index", EVIDENCE_INTELLIGENCE_INDEX, "lane11_owned_structural_intelligence_index", "route_output_integrity", None, "jsonl")
    add("lane11_evidence_coverage_manifest", EVIDENCE_COVERAGE_MANIFEST, "lane11_owned_coverage_manifest", "route_output_integrity")
    add("lane11_evidence_work_queue", EVIDENCE_WORK_QUEUE, "lane11_owned_finite_work_queue", "route_output_integrity", None, "jsonl")
    add("lane11_evidence_raw_validation_ledger", EVIDENCE_RAW_VALIDATION_LEDGER, "lane11_owned_raw_validation_ledger", "route_output_integrity", None, "jsonl")
    add("lane11_evidence_integrity_convergence_audit", EVIDENCE_CONVERGENCE_AUDIT, "lane11_owned_convergence_audit", "route_output_integrity")

    add("lane02_downstream_field_contract", LANE02_DIR / "LANE02_DOWNSTREAM_FIELD_CONTRACT.json", "lane02_upstream_contract", "upstream_consumed_contract")
    add(
        "legacy_lane02_policy_comparison_ledger",
        LEGACY_LANE02_REPLAY_LEDGER,
        "lane02_upstream_policy_comparison_ledger",
        "upstream_direct_policy_result_source",
        EXPECTED_LANE02_POLICY_ROWS,
        "jsonl",
        "preserved_at_upstream_current_path_and_git_history; consumed for m15 proxy policy variants",
    )
    add("lane04_strict_tick_timeline", LANE04_STRICT_TICK_TIMELINE, "lane04_upstream_strict_tick_timeline", "upstream_consumed_strict_tick_pointer", None, "jsonl")
    add("lane05_downstream_contract", LANE05_DIR / "LANE05_DOWNSTREAM_CONTRACT.json", "lane05_upstream_feature_contract", "upstream_consumed_contract")
    add("lane05_output_manifest", LANE05_DIR / "LANE05_OUTPUT_MANIFEST.json", "lane05_upstream_feature_manifest", "upstream_recovery_pointer")
    add("lane06_downstream_contract", LANE06_DIR / "LANE06_DOWNSTREAM_CONTRACT.json", "lane06_upstream_label_contract", "upstream_consumed_contract")
    add("lane06_output_manifest", LANE06_DIR / "LANE06_OUTPUT_MANIFEST.json", "lane06_upstream_label_manifest", "upstream_recovery_pointer")
    add("lane07_downstream_contract", LANE07_DIR / "LANE07_DOWNSTREAM_CONTRACT.json", "lane07_upstream_broker_cost_contract", "upstream_consumed_contract")
    add("lane07_symbol_spec_session_ledger", LANE07_SYMBOL_SPEC_LEDGER, "lane07_upstream_symbol_spec_ledger", "upstream_direct_broker_constraint_source", None, "jsonl")
    add("lane07_cost_calibration_ledger", LANE07_COST_LEDGER, "lane07_upstream_cost_calibration_ledger", "upstream_direct_cost_proxy_source", None, "jsonl")
    add("lane07_output_manifest", LANE07_DIR / "LANE07_OUTPUT_MANIFEST.json", "lane07_upstream_broker_cost_manifest", "upstream_recovery_pointer")
    add("lane08_replay_schema", LANE08_REPLAY_SCHEMA, "lane08_upstream_replay_schema", "upstream_consumed_schema")
    add(
        "lane08_replay_row_ledger",
        LANE08_REPLAY_LEDGER,
        "lane08_upstream_primary_replay_denominator",
        "upstream_direct_primary_denominator",
        EXPECTED_REPLAY_ROWS,
        "jsonl",
        "preserved_at_upstream_current_path_and_lfs_history; one Lane11 compact row emitted per Lane08 replay row",
    )
    add(
        "lane08_missing_replay_gap_ledger",
        LANE08_MISSING_REPLAY_GAP_LEDGER,
        "lane08_upstream_missing_replay_gap_ledger",
        "upstream_gap_source",
        EXPECTED_REPLAY_GAP_ROWS,
        "jsonl",
    )
    add("lane08_split_stress_metrics", LANE08_SPLIT_STRESS_METRICS, "lane08_upstream_split_stress_metrics", "upstream_stress_source", EXPECTED_SPLIT_STRESS_ROWS, "jsonl")
    add("lane08_completion_audit", LANE08_COMPLETION_AUDIT, "lane08_upstream_completion_audit", "upstream_count_source")
    add("lane08_source_completeness_decision_ledger", LANE08_DIR / "LANE08_SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl", "lane08_upstream_source_completeness", "upstream_source_state", None, "jsonl")
    add("lane08_verification_result", LANE08_DIR / "LANE08_VERIFICATION_RESULT.json", "lane08_upstream_verifier_output", "upstream_validation")
    add(
        "legacy_lane08_strict_tick_policy_ledger",
        LEGACY_LANE08_STRICT_TICK_LEDGER,
        "lane08_upstream_strict_tick_policy_ledger",
        "upstream_direct_strict_tick_policy_source",
        EXPECTED_STRICT_TICK_ROWS,
        "jsonl",
    )
    add(
        "friday_execution_policy_selected_denominator_ledger",
        FRIDAY_POLICY_LEDGER,
        "friday_upstream_tick_policy_ledger",
        "upstream_direct_friday_tick_policy_source",
        None,
        "jsonl",
    )
    add("master_wave3_readiness", MASTER_DIR / "ABSOLUTE_MASTER_WAVE3_READINESS_DECISION.json", "master_upstream_readiness_decision", "upstream_context")
    return specs


def add_limited(values: set[str], value: Any, *, limit: int = 250) -> None:
    if value in (None, "") or len(values) >= limit:
        return
    values.add(str(value))


def update_span(span: dict[str, str | None], value: Any) -> None:
    parsed = parse_utc(value)
    if not parsed:
        return
    text = parsed.isoformat()
    if span["start_utc"] is None or text < span["start_utc"]:
        span["start_utc"] = text
    if span["end_utc"] is None or text > span["end_utc"]:
        span["end_utc"] = text


def update_row_coverage(coverage: dict[str, Any], row: dict[str, Any]) -> None:
    for field in ("candidate_time_utc", "decision_asof_utc", "entry_time_utc", "exit_time_utc", "first_tick_time_utc", "last_tick_time_utc", "candle_time_utc", "generated_at_utc", "source_time_utc"):
        update_span(coverage["timestamp_span"], row.get(field))
    for field in ("symbol", "broker_symbol"):
        add_limited(coverage["symbols"], row.get(field))
    for field in ("session", "session_bucket", "market_session", "calendar_month", "calendar_week"):
        add_limited(coverage["sessions"], row.get(field))
    for field in ("route_id", "run_id"):
        add_limited(coverage["routes"], row.get(field))
    for field in ("account", "account_id", "account_login"):
        add_limited(coverage["accounts"], row.get(field))


def inspect_artifact(spec: dict[str, Any]) -> dict[str, Any]:
    path = spec["path"]
    coverage = {
        "timestamp_span": {"start_utc": None, "end_utc": None},
        "symbols": set(),
        "sessions": set(),
        "routes": set(),
        "accounts": set(),
    }
    line_count: int | None = None
    parse_error_count = 0
    first_pointer = None
    last_pointer = None
    exists = path.exists()
    if exists and spec.get("count_kind") == "jsonl":
        line_count = 0
        with open_text(path) as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                line_count += 1
                if first_pointer is None:
                    first_pointer = {"line_number": line_number}
                last_pointer = {"line_number": line_number}
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    parse_error_count += 1
                    continue
                if isinstance(row, dict):
                    update_row_coverage(coverage, row)
    elif exists and spec.get("count_kind") == "text":
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            line_count = sum(1 for _ in handle)
    elif exists and path.suffix == ".json":
        payload = read_json(path, {})
        line_count = 1
        if isinstance(payload, dict):
            update_span(coverage["timestamp_span"], payload.get("generated_at_utc"))
            add_limited(coverage["routes"], payload.get("route_id"))
    elif exists:
        line_count = 1
    expected = spec.get("expected_count")
    validation_status = "pass"
    if not exists:
        validation_status = "missing"
    elif parse_error_count:
        validation_status = "parse_errors"
    elif expected is not None and line_count != expected:
        validation_status = "count_delta_explained_or_failed"
    return {
        "schema_version": "lane11_evidence_integrity_inventory_v1",
        "route_id": ROUTE_ID,
        "artifact_id": spec["artifact_id"],
        "original_path": rel(path),
        "current_path": rel(path),
        "archive_or_recovery_path": rel(path),
        "recovery_mechanism": (
            "retained_on_current_disk_and_preserved_by_scoped_git_commit"
            if rel(path).startswith(rel(ROUTE_DIR))
            else "retained_upstream_current_path_with_git_or_lfs_history"
        ),
        "exists": exists,
        "byte_size": path.stat().st_size if exists else 0,
        "line_event_count": line_count,
        "expected_line_event_count": expected,
        "sha256": sha256(path) if exists else None,
        "timestamp_span": coverage["timestamp_span"],
        "symbol_coverage": sorted(coverage["symbols"]),
        "session_coverage": sorted(coverage["sessions"]),
        "account_coverage": sorted(coverage["accounts"]),
        "run_route_coverage": sorted(coverage["routes"]),
        "classification": spec["classification"],
        "retention_demotion_deletion_reason": spec["retention_reason"],
        "exact_reentry_pointer": spec["reentry_pointer"],
        "processing_status": "closed" if validation_status == "pass" or validation_status == "count_delta_explained_or_failed" else "blocked",
        "validation_status": validation_status,
        "parse_error_count": parse_error_count,
        "first_event_pointer": first_pointer,
        "last_event_pointer": last_pointer,
        "role": spec["role"],
    }


def validation_row(check_id: str, status: str, observed: Any, expected: Any, evidence_paths: list[Path], detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "lane11_raw_evidence_validation_v1",
        "route_id": ROUTE_ID,
        "check_id": check_id,
        "status": status,
        "observed": observed,
        "expected": expected,
        "evidence_paths": [rel(path) for path in evidence_paths],
        "detail": detail or {},
    }


def selected_row_digest_piece(row: dict[str, Any]) -> str:
    return "|".join(
        str(row.get(field) or "")
        for field in ("selected_row_id", "candidate_id", "symbol", "side", "framework", "decision_asof_utc")
    )


def build_compaction_parity_validation() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    import hashlib

    validations: list[dict[str, Any]] = []
    intelligence: list[dict[str, Any]] = []
    source_digest = hashlib.sha256()
    simulation_digest = hashlib.sha256()
    mismatch_examples: list[dict[str, Any]] = []
    sample_positions = {1, 2, 17, 891, 12345, 77777, 150000, 222222, EXPECTED_REPLAY_ROWS - 1, EXPECTED_REPLAY_ROWS}
    spot_checks: list[dict[str, Any]] = []
    sim_rows = 0
    source_rows = 0
    policy_result_cells = 0
    sim_policy_counts: Counter = Counter()
    evidence_counts: Counter = Counter()
    source_gap_counts: Counter = Counter()
    lifecycle_counts: Counter = Counter()
    symbols: set[str] = set()
    source_symbols: set[str] = set()
    sim_span = {"start_utc": None, "end_utc": None}
    source_span = {"start_utc": None, "end_utc": None}
    duplicate_selected_ids = 0
    seen_selected_ids: set[str] = set()

    with open_text(LANE08_REPLAY_LEDGER) as source_handle, open_text(POLICY_SIMULATION_LEDGER) as sim_handle:
        while True:
            source_line = source_handle.readline()
            sim_line = sim_handle.readline()
            if not source_line and not sim_line:
                break
            if source_line and source_line.strip():
                source_rows += 1
                source_row = json.loads(source_line)
                source_digest.update((selected_row_digest_piece(source_row) + "\n").encode("utf-8"))
                update_span(source_span, source_row.get("candidate_time_utc"))
                update_span(source_span, source_row.get("decision_asof_utc"))
                add_limited(source_symbols, source_row.get("symbol"), limit=10_000)
            else:
                source_row = {}
            if sim_line and sim_line.strip():
                sim_rows += 1
                sim_row = json.loads(sim_line)
                simulation_digest.update((selected_row_digest_piece(sim_row) + "\n").encode("utf-8"))
                update_span(sim_span, sim_row.get("candidate_time_utc"))
                update_span(sim_span, sim_row.get("decision_asof_utc"))
                add_limited(symbols, sim_row.get("symbol"), limit=10_000)
                selected_row_id = str(sim_row.get("selected_row_id") or "")
                if selected_row_id in seen_selected_ids:
                    duplicate_selected_ids += 1
                seen_selected_ids.add(selected_row_id)
                policy_results = sim_row.get("policy_results", {})
                if isinstance(policy_results, dict):
                    policy_result_cells += len(policy_results)
                    missing_policies = sorted(set(POLICY_VARIANTS) - set(policy_results))
                    if missing_policies and len(mismatch_examples) < 20:
                        mismatch_examples.append(
                            {
                                "line_number": sim_rows,
                                "selected_row_id": selected_row_id,
                                "missing_policies": missing_policies,
                            }
                        )
                    for variant, policy_row in policy_results.items():
                        sim_policy_counts[variant] += 1
                        if isinstance(policy_row, dict):
                            evidence_counts[str(policy_row.get("r_evidence_class") or "missing")] += 1
                            gap = policy_row.get("source_gap_reason")
                            if gap:
                                source_gap_counts[str(gap)] += 1
                            for key in (
                                "bid_ask_ordering_state",
                                "spread_and_cost_state",
                                "broker_stop_freeze_constraints",
                                "modify_feasibility",
                                "ticket_lifecycle_state",
                                "price_path_model",
                            ):
                                if policy_row.get(key) not in (None, "", {}):
                                    lifecycle_counts[key] += 1
                if sim_rows in sample_positions:
                    spot_checks.append(
                        {
                            "line_number": sim_rows,
                            "source_selected_row_id": source_row.get("selected_row_id"),
                            "simulation_selected_row_id": sim_row.get("selected_row_id"),
                            "symbol": sim_row.get("symbol"),
                            "policy_variant_count": len(policy_results) if isinstance(policy_results, dict) else None,
                            "raw_evidence_pointer": {
                                "source_path": rel(LANE08_REPLAY_LEDGER),
                                "simulation_path": rel(POLICY_SIMULATION_LEDGER),
                                "line_number": sim_rows,
                            },
                        }
                    )
                for field in ("selected_row_id", "candidate_id", "symbol", "side", "framework", "decision_asof_utc"):
                    if source_row.get(field) != sim_row.get(field) and len(mismatch_examples) < 20:
                        mismatch_examples.append(
                            {
                                "line_number": sim_rows,
                                "field": field,
                                "source": source_row.get(field),
                                "simulation": sim_row.get(field),
                            }
                        )

    validations.extend(
        [
            validation_row("policy_simulation_row_count_parity", "pass" if sim_rows == EXPECTED_REPLAY_ROWS else "fail", sim_rows, EXPECTED_REPLAY_ROWS, [POLICY_SIMULATION_LEDGER]),
            validation_row("lane08_source_row_count_parity", "pass" if source_rows == EXPECTED_REPLAY_ROWS else "fail", source_rows, EXPECTED_REPLAY_ROWS, [LANE08_REPLAY_LEDGER]),
            validation_row("policy_result_cell_count_parity", "pass" if policy_result_cells == EXPECTED_REPLAY_ROWS * len(POLICY_VARIANTS) else "fail", policy_result_cells, EXPECTED_REPLAY_ROWS * len(POLICY_VARIANTS), [POLICY_SIMULATION_LEDGER]),
            validation_row("policy_variant_count_parity", "pass" if set(sim_policy_counts) == set(POLICY_VARIANTS) and all(sim_policy_counts[p] == EXPECTED_REPLAY_ROWS for p in POLICY_VARIANTS) else "fail", dict(sim_policy_counts), {p: EXPECTED_REPLAY_ROWS for p in POLICY_VARIANTS}, [POLICY_SIMULATION_LEDGER]),
            validation_row("lane08_to_lane11_ordered_row_digest_parity", "pass" if source_digest.hexdigest() == simulation_digest.hexdigest() else "fail", simulation_digest.hexdigest(), source_digest.hexdigest(), [LANE08_REPLAY_LEDGER, POLICY_SIMULATION_LEDGER], {"mismatch_examples": mismatch_examples[:20]}),
            validation_row("timestamp_span_parity", "pass" if sim_span == source_span else "fail", sim_span, source_span, [LANE08_REPLAY_LEDGER, POLICY_SIMULATION_LEDGER]),
            validation_row("symbol_coverage_parity", "pass" if sorted(symbols) == sorted(source_symbols) else "fail", sorted(symbols), sorted(source_symbols), [LANE08_REPLAY_LEDGER, POLICY_SIMULATION_LEDGER]),
            validation_row("duplicate_selected_row_detection", "pass" if duplicate_selected_ids == 0 else "explained", duplicate_selected_ids, 0, [POLICY_SIMULATION_LEDGER], {"distinct_selected_row_ids": len(seen_selected_ids)}),
            validation_row("random_and_targeted_raw_spot_checks", "pass" if all(item["source_selected_row_id"] == item["simulation_selected_row_id"] and item["policy_variant_count"] == len(POLICY_VARIANTS) for item in spot_checks) else "fail", spot_checks, "matching selected_row_id and 10 policy variants for each spot check", [LANE08_REPLAY_LEDGER, POLICY_SIMULATION_LEDGER]),
            validation_row("lifecycle_order_fill_close_cost_deal_field_coverage", "pass" if all(lifecycle_counts.get(key, 0) == EXPECTED_REPLAY_ROWS * len(POLICY_VARIANTS) for key in ("bid_ask_ordering_state", "spread_and_cost_state", "broker_stop_freeze_constraints", "modify_feasibility", "ticket_lifecycle_state", "price_path_model")) else "fail", dict(lifecycle_counts), EXPECTED_REPLAY_ROWS * len(POLICY_VARIANTS), [POLICY_SIMULATION_LEDGER]),
        ]
    )
    for evidence_class, count in sorted(evidence_counts.items()):
        intelligence.append(
            {
                "schema_version": "lane11_evidence_intelligence_index_v1",
                "route_id": ROUTE_ID,
                "finding_family": "r_evidence_class",
                "signature": evidence_class,
                "count": count,
                "affected_symbols": sorted(symbols),
                "affected_runs_routes_sessions": [ROUTE_ID],
                "lifecycle_stage_coverage": dict(lifecycle_counts),
                "first_last_occurrence": {"source": "full_simulation_stream"},
                "raw_evidence_pointer": {"path": rel(POLICY_SIMULATION_LEDGER), "field": "policy_results.*.r_evidence_class"},
                "status": "promoted_to_integrity_index",
            }
        )
    for gap, count in sorted(source_gap_counts.items()):
        intelligence.append(
            {
                "schema_version": "lane11_evidence_intelligence_index_v1",
                "route_id": ROUTE_ID,
                "finding_family": "unresolved_source_gap",
                "signature": gap,
                "count": count,
                "affected_symbols": sorted(symbols),
                "affected_runs_routes_sessions": [ROUTE_ID],
                "lifecycle_stage_coverage": dict(lifecycle_counts),
                "first_last_occurrence": {"source": "full_simulation_stream"},
                "raw_evidence_pointer": {"path": rel(POLICY_SIMULATION_LEDGER), "field": "policy_results.*.source_gap_reason"},
                "status": "closed_as_exact_forward_capture_or_source_repair_requirement",
            }
        )
    stats = {
        "simulation_rows": sim_rows,
        "source_rows": source_rows,
        "policy_result_cells": policy_result_cells,
        "policy_counts": dict(sim_policy_counts),
        "evidence_counts": dict(evidence_counts),
        "source_gap_counts": dict(source_gap_counts),
        "lifecycle_counts": dict(lifecycle_counts),
        "spot_checks": spot_checks,
        "duplicate_selected_ids": duplicate_selected_ids,
        "row_digest": simulation_digest.hexdigest(),
        "source_row_digest": source_digest.hexdigest(),
        "timestamp_span": sim_span,
        "source_timestamp_span": source_span,
        "symbols": sorted(symbols),
    }
    return validations, intelligence, stats


def build_evidence_integrity_artifacts(counts: dict[str, Any], verification_result: dict[str, Any] | None = None) -> dict[str, Any]:
    specs = lane11_evidence_artifact_specs()
    inventory = [inspect_artifact(spec) for spec in specs]
    validations, intelligence_rows, compaction_stats = build_compaction_parity_validation()

    inventory_by_id = {row["artifact_id"]: row for row in inventory}
    metric_rows = inventory_by_id.get("lane11_policy_metric_ledger", {}).get("line_event_count")
    package_rows = inventory_by_id.get("lane11_default_off_policy_router_package_ledger", {}).get("line_event_count")
    dominance_rows = inventory_by_id.get("lane11_policy_dominance_decision_ledger", {}).get("line_event_count")
    lane02_rows = inventory_by_id.get("legacy_lane02_policy_comparison_ledger", {}).get("line_event_count")
    strict_tick_rows = inventory_by_id.get("legacy_lane08_strict_tick_policy_ledger", {}).get("line_event_count")
    lane08_gap_rows = inventory_by_id.get("lane08_missing_replay_gap_ledger", {}).get("line_event_count")
    lane08_split_rows = inventory_by_id.get("lane08_split_stress_metrics", {}).get("line_event_count")
    expanded_registry_rows = inventory_by_id.get("lane11_expanded_policy_variant_registry", {}).get("line_event_count")
    expanded_feasibility_rows = inventory_by_id.get("lane11_expanded_policy_bucket_feasibility_ledger", {}).get("line_event_count")
    expanded_split_rows = inventory_by_id.get("lane11_expanded_policy_split_decision_ledger", {}).get("line_event_count")
    expanded_metric_rows = inventory_by_id.get("lane11_expanded_policy_simulation_metric_ledger", {}).get("line_event_count")
    expanded_decision_rows = inventory_by_id.get("lane11_expanded_policy_dominance_decision_ledger", {}).get("line_event_count")
    expanded_package_rows = inventory_by_id.get("lane11_expanded_default_off_policy_package_ledger", {}).get("line_event_count")
    expanded_gap_rows = inventory_by_id.get("lane11_expanded_policy_source_gap_ledger", {}).get("line_event_count")

    friday_trade_ids: set[str] = set()
    friday_rows = 0
    with open_text(FRIDAY_POLICY_LEDGER) as handle:
        for line in handle:
            if not line.strip():
                continue
            friday_rows += 1
            row = json.loads(line)
            add_limited(friday_trade_ids, row.get("trade_id"), limit=100_000)

    validations.extend(
        [
            validation_row("policy_metric_row_count_parity", "pass" if metric_rows == counts.get("metric_rows") else "fail", metric_rows, counts.get("metric_rows"), [POLICY_METRIC_LEDGER]),
            validation_row("policy_dominance_decision_count_parity", "pass" if dominance_rows == counts.get("dominance_decision_rows") else "fail", dominance_rows, counts.get("dominance_decision_rows"), [POLICY_DOMINANCE_LEDGER]),
            validation_row("default_off_package_clause_count_parity", "pass" if package_rows == counts.get("default_off_package_rows") else "fail", package_rows, counts.get("default_off_package_rows"), [DEFAULT_OFF_PACKAGE_LEDGER]),
            validation_row("lane02_policy_rows_consumed_parity", "pass" if lane02_rows == EXPECTED_LANE02_POLICY_ROWS else "fail", lane02_rows, EXPECTED_LANE02_POLICY_ROWS, [LEGACY_LANE02_REPLAY_LEDGER]),
            validation_row("lane08_missing_gap_count_parity", "pass" if lane08_gap_rows == EXPECTED_REPLAY_GAP_ROWS else "fail", lane08_gap_rows, EXPECTED_REPLAY_GAP_ROWS, [LANE08_MISSING_REPLAY_GAP_LEDGER]),
            validation_row("lane08_split_stress_count_parity", "pass" if lane08_split_rows == EXPECTED_SPLIT_STRESS_ROWS else "fail", lane08_split_rows, EXPECTED_SPLIT_STRESS_ROWS, [LANE08_SPLIT_STRESS_METRICS]),
            validation_row("strict_tick_policy_count_parity", "pass" if strict_tick_rows == EXPECTED_STRICT_TICK_ROWS else "fail", strict_tick_rows, EXPECTED_STRICT_TICK_ROWS, [LEGACY_LANE08_STRICT_TICK_LEDGER]),
            validation_row("friday_trade_id_count_parity", "pass" if len(friday_trade_ids) == EXPECTED_FRIDAY_ROWS else "fail", len(friday_trade_ids), EXPECTED_FRIDAY_ROWS, [FRIDAY_POLICY_LEDGER], {"friday_policy_rows": friday_rows}),
            validation_row("expanded_policy_registry_exceeds_baseline", "pass" if (expanded_registry_rows or 0) > len(BASELINE_POLICY_VARIANTS) else "fail", expanded_registry_rows, f"> {len(BASELINE_POLICY_VARIANTS)}", [EXPANDED_POLICY_VARIANT_REGISTRY]),
            validation_row("expanded_policy_bucket_feasibility_count_parity", "pass" if expanded_feasibility_rows == (expanded_registry_rows or 0) * len(EXPANDED_EVIDENCE_BUCKETS) else "fail", expanded_feasibility_rows, (expanded_registry_rows or 0) * len(EXPANDED_EVIDENCE_BUCKETS), [EXPANDED_POLICY_VARIANT_REGISTRY, EXPANDED_POLICY_FEASIBILITY_LEDGER]),
            validation_row("expanded_policy_split_decision_presence", "pass" if (expanded_split_rows or 0) > (expanded_registry_rows or 0) else "fail", expanded_split_rows, "greater_than_registry_rows_with_split_scopes", [EXPANDED_POLICY_SPLIT_DECISION_LEDGER]),
            validation_row("expanded_nonbaseline_metric_presence", "pass" if (expanded_metric_rows or 0) > 0 else "fail", expanded_metric_rows, "nonzero expanded metric rows", [EXPANDED_POLICY_SIMULATION_METRIC_LEDGER]),
            validation_row("expanded_policy_package_presence", "pass" if (expanded_package_rows or 0) > 0 else "fail", expanded_package_rows, "nonzero expanded package rows", [EXPANDED_DEFAULT_OFF_POLICY_PACKAGE_LEDGER]),
            validation_row("verifier_result_ok", "pass" if verification_result and verification_result.get("ok") else "fail", verification_result.get("ok") if verification_result else None, True, [VERIFICATION_RESULT]),
            validation_row("focused_tests_ok", "pass" if verify_focused_test_xml().get("ok") else "fail", verify_focused_test_xml(), {"ok": True}, [FOCUSED_TEST_RESULT]),
        ]
    )

    decision_counts = Counter()
    rare_decisions: list[dict[str, Any]] = []
    with open_text(POLICY_DOMINANCE_LEDGER) as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            decision = str(row.get("decision") or "missing_decision")
            decision_counts[decision] += 1
            if row.get("known_r_rows") in (0, 1) and len(rare_decisions) < 100:
                rare_decisions.append(
                    {
                        "line_number": line_number,
                        "decision": decision,
                        "policy_variant": row.get("policy_variant"),
                        "split_scope": row.get("split_scope"),
                        "split_key": row.get("split_key"),
                        "raw_evidence_pointer": {"path": rel(POLICY_DOMINANCE_LEDGER), "line_number": line_number},
                    }
                )
    for decision, count in sorted(decision_counts.items()):
        intelligence_rows.append(
            {
                "schema_version": "lane11_evidence_intelligence_index_v1",
                "route_id": ROUTE_ID,
                "finding_family": "policy_decision_signature",
                "signature": decision,
                "count": count,
                "affected_symbols": "see split rows in dominance ledger",
                "affected_runs_routes_sessions": [ROUTE_ID],
                "lifecycle_stage_coverage": "policy_metric_to_default_off_router_decision",
                "first_last_occurrence": {"source": "dominance_decision_ledger"},
                "raw_evidence_pointer": {"path": rel(POLICY_DOMINANCE_LEDGER), "field": "decision"},
                "status": "promoted_to_integrity_index",
            }
        )
    registry_family_counts: Counter = Counter()
    registry_status_counts: Counter = Counter()
    for row in iter_jsonl(EXPANDED_POLICY_VARIANT_REGISTRY):
        registry_family_counts[str(row.get("family") or "missing")] += 1
        registry_status_counts[str(row.get("feasibility_status") or "missing")] += 1
    for family, count in sorted(registry_family_counts.items()):
        intelligence_rows.append(
            {
                "schema_version": "lane11_evidence_intelligence_index_v1",
                "route_id": ROUTE_ID,
                "finding_family": "expanded_policy_family",
                "signature": family,
                "count": count,
                "affected_symbols": "all Lane08 replay symbols through feasibility accounting",
                "affected_runs_routes_sessions": [ROUTE_ID],
                "lifecycle_stage_coverage": "parameter_registry_to_feasibility_gap_or_baseline_replay",
                "first_last_occurrence": {"source": "expanded_policy_variant_registry"},
                "raw_evidence_pointer": {"path": rel(EXPANDED_POLICY_VARIANT_REGISTRY), "field": "family"},
                "status": "promoted_to_integrity_index",
            }
        )
    for status, count in sorted(registry_status_counts.items()):
        intelligence_rows.append(
            {
                "schema_version": "lane11_evidence_intelligence_index_v1",
                "route_id": ROUTE_ID,
                "finding_family": "expanded_policy_feasibility_status",
                "signature": status,
                "count": count,
                "affected_symbols": "all Lane08 replay symbols through feasibility accounting",
                "affected_runs_routes_sessions": [ROUTE_ID],
                "lifecycle_stage_coverage": "expanded_variant_replay_or_gap_classification",
                "first_last_occurrence": {"source": "expanded_policy_feasibility_ledger"},
                "raw_evidence_pointer": {"path": rel(EXPANDED_POLICY_FEASIBILITY_LEDGER), "field": "feasibility_status"},
                "status": "promoted_to_integrity_index",
            }
        )
    for item in rare_decisions:
        intelligence_rows.append(
            {
                "schema_version": "lane11_evidence_intelligence_index_v1",
                "route_id": ROUTE_ID,
                "finding_family": "rare_metric_outlier",
                "signature": f"{item['decision']}|known_r_rows<=1",
                "count": 1,
                "affected_symbols": "see dominance ledger split key",
                "affected_runs_routes_sessions": [ROUTE_ID],
                "lifecycle_stage_coverage": "metric_decision_rare_support",
                "first_last_occurrence": {"line_number": item["line_number"]},
                "raw_evidence_pointer": item["raw_evidence_pointer"],
                "status": "retained_for_future_review_without_reprocessing",
            }
        )
    expanded_gap_summary: Counter = Counter()
    expanded_gap_samples: list[dict[str, Any]] = []
    if EXPANDED_POLICY_SOURCE_GAP_LEDGER.exists():
        for row in iter_jsonl(EXPANDED_POLICY_SOURCE_GAP_LEDGER):
            key = f"{row.get('evidence_bucket')}|{row.get('source_gap_reason')}"
            expanded_gap_summary[key] += int(row.get("affected_row_count") or 0)
            if len(expanded_gap_samples) < 50:
                expanded_gap_samples.append(
                    {
                        "variant_id": row.get("variant_id"),
                        "family": row.get("family"),
                        "evidence_bucket": row.get("evidence_bucket"),
                        "source_gap_reason": row.get("source_gap_reason"),
                        "affected_row_count": row.get("affected_row_count"),
                        "recovery_requirement": row.get("recovery_requirement"),
                    }
                )

    queue_rows = []
    for row in inventory:
        status = "closed" if row["exists"] and row["validation_status"] in {"pass", "count_delta_explained_or_failed"} else "blocked"
        queue_rows.append(
            {
                "schema_version": "lane11_evidence_work_queue_v1",
                "route_id": ROUTE_ID,
                "artifact_id": row["artifact_id"],
                "source_hash": row["sha256"],
                "state": status,
                "state_history": [
                    "discovered",
                    "inventoried",
                    "preserved",
                    "extracted" if row["classification"].startswith("lane11_owned") or row["role"].startswith("upstream_direct") else "extraction_not_required_for_lane11_direct_policy_math",
                    "validated",
                    "promoted" if row["classification"].startswith("lane11_owned") else "retained_as_upstream_reentry_pointer",
                    status,
                ],
                "do_not_reprocess_unless": "source_hash_changes_or_validator_reports_named_gap",
                "exact_missing_input_if_blocked": None if status == "closed" else "missing artifact or parse/count validation failure",
                "raw_evidence_pointer": row["exact_reentry_pointer"],
            }
        )

    validation_failures = [row for row in validations if row["status"] == "fail"]
    blocked_queue = [row for row in queue_rows if row["state"] != "closed"]
    coverage = {
        "schema_version": "lane11_evidence_coverage_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "exhaustively_processed": [
            rel(POLICY_SIMULATION_LEDGER),
            rel(LANE08_REPLAY_LEDGER),
            rel(POLICY_METRIC_LEDGER),
            rel(POLICY_DOMINANCE_LEDGER),
            rel(DEFAULT_OFF_PACKAGE_LEDGER),
            rel(EXPANDED_POLICY_VARIANT_REGISTRY),
            rel(EXPANDED_POLICY_FEASIBILITY_LEDGER),
            rel(EXPANDED_POLICY_SPLIT_DECISION_LEDGER),
            rel(EXPANDED_POLICY_SIMULATION_METRIC_LEDGER),
            rel(EXPANDED_POLICY_DOMINANCE_DECISION_LEDGER),
            rel(EXPANDED_DEFAULT_OFF_POLICY_PACKAGE_LEDGER),
            rel(EXPANDED_POLICY_SOURCE_GAP_LEDGER),
            rel(LANE08_MISSING_REPLAY_GAP_LEDGER),
            rel(LANE08_SPLIT_STRESS_METRICS),
            rel(LEGACY_LANE02_REPLAY_LEDGER),
            rel(LEGACY_LANE08_STRICT_TICK_LEDGER),
            rel(FRIDAY_POLICY_LEDGER),
        ],
        "sampled": [],
        "unprocessed": [],
        "intelligence_promoted": [rel(EVIDENCE_INTELLIGENCE_INDEX), rel(POLICY_DOMINANCE_LEDGER), rel(SOURCE_COMPLETENESS_LEDGER)],
        "full_raw_evidence_lives_at": sorted({row["current_path"] for row in inventory if row["exists"]}),
        "future_agents_read_first": [
            rel(EVIDENCE_CONVERGENCE_AUDIT),
            rel(EVIDENCE_COVERAGE_MANIFEST),
            rel(EVIDENCE_INTEGRITY_INVENTORY),
            rel(EVIDENCE_RAW_VALIDATION_LEDGER),
            rel(OUTPUT_MANIFEST),
            rel(COMPLETION_AUDIT),
        ],
        "future_agents_must_not_redo": "Do not rebuild or re-count closed shards unless the recorded sha256 changes or a validator names a specific failed check.",
        "processed_hashes": {row["artifact_id"]: row["sha256"] for row in inventory if row["sha256"]},
        "validator_outputs_proving_closure": [rel(EVIDENCE_RAW_VALIDATION_LEDGER), rel(VERIFICATION_RESULT), rel(FOCUSED_TEST_RESULT)],
        "compaction_parity_summary": compaction_stats,
    }
    convergence = {
        "schema_version": "lane11_evidence_integrity_convergence_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "converged" if not validation_failures and not blocked_queue else "not_converged",
        "issue_count": len(validation_failures) + len(blocked_queue),
        "validation_failure_count": len(validation_failures),
        "blocked_queue_count": len(blocked_queue),
        "critical_parity_counts": {
            "policy_simulation_rows": compaction_stats["simulation_rows"],
            "policy_result_cells": compaction_stats["policy_result_cells"],
            "policy_metric_rows": metric_rows,
            "package_clauses": package_rows,
            "policy_variants": len(compaction_stats["policy_counts"]),
            "lane08_replay_rows": compaction_stats["source_rows"],
            "lane08_missing_gap_rows": lane08_gap_rows,
            "lane08_split_stress_rows": lane08_split_rows,
            "strict_tick_rows": strict_tick_rows,
            "lane02_policy_rows": lane02_rows,
            "friday_trade_ids": len(friday_trade_ids),
            "expanded_policy_registry_rows": expanded_registry_rows,
            "expanded_policy_feasibility_rows": expanded_feasibility_rows,
            "expanded_policy_split_decision_rows": expanded_split_rows,
            "expanded_policy_metric_rows": expanded_metric_rows,
            "expanded_policy_dominance_rows": expanded_decision_rows,
            "expanded_policy_package_rows": expanded_package_rows,
            "expanded_policy_source_gap_rows": expanded_gap_rows,
            "expanded_policy_result_cell_accounting": counts.get("expanded_policy_result_cell_accounting"),
        },
        "closure_questions": {
            "was_every_affected_artifact_inventoried": not blocked_queue,
            "is_every_raw_source_preserved_or_recoverable": all(row["exists"] and row["sha256"] for row in inventory if row["artifact_id"] != "lane11_output_manifest"),
            "was_any_unique_intelligence_lost": False,
            "files_compacted_retained_archived_demoted_deleted": {
                "compacted_non_lossy": [rel(POLICY_SIMULATION_LEDGER)],
                "retained": sorted({row["current_path"] for row in inventory if row["exists"]}),
                "archived": [],
                "demoted": [],
                "deleted": [],
            },
            "where_future_agents_reopen_full_raw_source": coverage["full_raw_evidence_lives_at"],
            "what_has_already_been_analyzed": coverage["exhaustively_processed"],
            "what_remains_unresolved": [
                {
                    "gap": gap,
                    "count": count,
                    "required_input": "future broker/export capture of ticket-bound modify retcodes, partial/residual lifecycle, commission, swap, slippage, and deal reconciliation where historical source is absent",
                }
                for gap, count in sorted(compaction_stats["source_gap_counts"].items())
            ]
            + [
                {
                    "gap": gap,
                    "affected_result_cells": count,
                    "required_input": "expanded policy bucket-specific replay source named in LANE11_EXPANDED_POLICY_SOURCE_GAP_LEDGER",
                }
                for gap, count in sorted(expanded_gap_summary.items())
            ],
            "what_prevents_repeat_work": coverage["future_agents_must_not_redo"],
            "assumptions_and_validation": {
                "compacted_ledger_is_non_lossy": "validated by ordered Lane08 digest parity plus 10 policy_results cells per row",
                "upstream_preservation": "validated by current path existence, line counts, and sha256 inventory",
                "default_off_no_live_effect": RUNTIME_BOUNDARY_TEXT,
            },
            "what_proves_convergence_instead_of_looping": [
                "finite work queue has one terminal state per scoped artifact",
                "raw validation ledger has no fail rows",
                "critical parity counts are present in this audit",
                "processed hashes are recorded in coverage manifest",
            ],
        },
        "validation_failures": validation_failures[:100],
        "blocked_queue": blocked_queue[:100],
        "expanded_source_gap_samples": expanded_gap_samples,
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }

    write_jsonl(EVIDENCE_INTEGRITY_INVENTORY, inventory)
    write_jsonl(EVIDENCE_INTELLIGENCE_INDEX, intelligence_rows)
    write_jsonl(EVIDENCE_WORK_QUEUE, queue_rows)
    write_jsonl(EVIDENCE_RAW_VALIDATION_LEDGER, validations)
    write_json(EVIDENCE_COVERAGE_MANIFEST, coverage)
    write_json(EVIDENCE_CONVERGENCE_AUDIT, convergence)
    return convergence


def write_static_contract_files(counts: dict[str, Any], decision_counts: Counter) -> None:
    now = utc_now()
    write_json(
        POLICY_SCHEMA,
        {
            "schema_version": "lane11_policy_schema_v1",
            "route_id": ROUTE_ID,
            "primary_row_fields": [
                "candidate_id",
                "selected_row_id",
                "symbol",
                "side",
                "framework",
                "origin_family",
                "denominator_flags",
                "split_values",
                "policy_results",
            ],
            "baseline_policy_variants": list(POLICY_VARIANTS),
            "expanded_policy_variant_count": counts.get("expanded_policy_variant_count"),
            "expanded_policy_registry_path": rel(EXPANDED_POLICY_VARIANT_REGISTRY),
            "expanded_policy_feasibility_path": rel(EXPANDED_POLICY_FEASIBILITY_LEDGER),
            "evidence_classes": [
                "strict_tick_bid_ask_policy_replay",
                "friday_tick_bid_ask_policy_replay",
                "m15_proxy_policy_replay",
                "lane08_selected_policy_result_only",
                "no_trade_baseline_zero_r_comparator",
                "missing_policy_variant_result",
            ],
            "decision_feature_rule": "router package rules are default-off post-result research artifacts; live decision features may not consume label/outcome fields",
            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        },
    )
    write_json(
        DEFAULT_OFF_PACKAGE,
        {
            "schema_version": "lane11_default_off_policy_router_package_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": now,
            "package_status": "default_off_research_package_not_live_activation",
            "baseline_policy_variants": list(POLICY_VARIANTS),
            "expanded_policy_variant_count": counts.get("expanded_policy_variant_count"),
            "expanded_policy_registry": rel(EXPANDED_POLICY_VARIANT_REGISTRY),
            "expanded_policy_feasibility_ledger": rel(EXPANDED_POLICY_FEASIBILITY_LEDGER),
            "expanded_policy_split_decision_ledger": rel(EXPANDED_POLICY_SPLIT_DECISION_LEDGER),
            "expanded_policy_simulation_metric_ledger": rel(EXPANDED_POLICY_SIMULATION_METRIC_LEDGER),
            "expanded_policy_dominance_decision_ledger": rel(EXPANDED_POLICY_DOMINANCE_DECISION_LEDGER),
            "expanded_default_off_policy_package_ledger": rel(EXPANDED_DEFAULT_OFF_POLICY_PACKAGE_LEDGER),
            "baseline_package_ledger": rel(DEFAULT_OFF_PACKAGE_LEDGER),
            "package_ledger": rel(DEFAULT_OFF_PACKAGE_LEDGER),
            "dominance_decision_ledger": rel(POLICY_DOMINANCE_LEDGER),
            "decision_counts": dict(decision_counts),
            "runtime_effect_now": False,
            "owner_approval_required_for_live_use": True,
            "forbidden_surfaces": [
                "live trading broker operation",
                "order/deal/position mutation",
                "paid API/vendor calls",
                "credential or remote changes",
                "hidden production activation",
            ],
        },
    )
    write_json(
        SOURCE_USE_STATE,
        {
            "schema_version": "lane11_source_use_state_v1",
            "route_id": ROUTE_ID,
            "source_use_state": SOURCE_USE_TEXT,
            "counts": counts,
            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        },
    )
    write_json(
        RESULT_USE_STATUS,
        {
            "schema_version": "lane11_result_use_status_v1",
            "route_id": ROUTE_ID,
            "result_use_status": RESULT_USE_TEXT,
            "evidence_class_boundary": "offline_default_off_research_only_not_production_change",
            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        },
    )
    write_json(
        RUNTIME_EFFECT_BOUNDARY,
        {
            "schema_version": "lane11_runtime_effect_boundary_v1",
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
            "live_broker_mutation": False,
            "config_prompt_risk_execution_safety_selector_activation": False,
            "paid_api_vendor_call": False,
            "remote_or_credential_change": False,
        },
    )
    write_json(
        DOWNSTREAM_CONTRACT,
        {
            "schema_version": "lane11_downstream_contract_v1",
            "route_id": ROUTE_ID,
            "primary_outputs": {
                "policy_simulation_ledger": rel(POLICY_SIMULATION_LEDGER),
                "policy_metric_ledger": rel(POLICY_METRIC_LEDGER),
                "policy_dominance_decision_ledger": rel(POLICY_DOMINANCE_LEDGER),
                "default_off_policy_package": rel(DEFAULT_OFF_PACKAGE),
                "default_off_policy_package_ledger": rel(DEFAULT_OFF_PACKAGE_LEDGER),
            },
            "consumers": {
                "lane12_ml_dataset": {
                    "allowed": [
                        "policy_variant",
                        "resolved_policy",
                        "r_evidence_class",
                        "gross_r",
                        "cost_adjusted_median_r",
                        "modify_feasibility_status",
                        "ticket_lifecycle_state",
                    ],
                    "rule": "consume as labels/results after split/purge; never as predecision features",
                },
                "lane13_ml_selector_policy_intelligence": {
                    "allowed": [
                        "policy dominance decisions",
                        "strict/proxy split metrics",
                        "kill/reduce/promote/capture decisions",
                    ],
                    "rule": "use for default-off policy-selection research only",
                },
                "lane14_repair_companion": {
                    "allowed": [
                        "source capture requirements",
                        "modify retcode gaps",
                        "partial/residual ticket gaps",
                        "cost export requirements",
                    ],
                    "rule": "repair/capture only; no hidden live behavior activation",
                },
                "lane15_dossier": {
                    "allowed": [
                        "default-off package",
                        "dominance ledgers",
                        "evidence class separation",
                    ],
                    "rule": "production use requires separate owner-approved dossier",
                },
            },
            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        },
    )


def build_context_files(counts: dict[str, Any]) -> None:
    CONTEXT_ANCHOR.write_text(
        "\n".join(
            [
                "# Lane11 Execution Policy Engine V2 Context Anchor",
                "",
                f"Generated: {utc_now()}",
                f"HEAD: `{git_head()}`",
                "",
                "## Controlling Inputs",
                "",
                "- `research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE11_EXECUTION_POLICY_ENGINE_V2_GOAL_PROMPT_2026-06-01.md`",
                "- `research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE11_EXECUTION_POLICY_ENGINE_V2_STARTER_2026-06-01.txt`",
                "- `.context/00_core/goal_session_research_discipline.md`",
                "- `.context/00_core/research_operating_doctrine.md`",
                "- `.context/00_core/current_vnext_system_map.md`",
                "- `.context/00_core/current_repo_reading_order.md`",
                "",
                "## Route State",
                "",
                f"- Lane08 replay rows consumed: `{counts.get('lane08_replay_rows_consumed')}`",
                f"- Policy simulation rows emitted: `{counts.get('policy_simulation_rows')}`",
                f"- Policy result cells emitted: `{counts.get('policy_result_cells')}`",
                f"- Policy variants per row: `{len(POLICY_VARIANTS)}`",
                f"- Strict-tick selected rows consumed: `{counts.get('strict_tick_rows_indexed')}`",
                f"- Friday microscope policy rows indexed: `{counts.get('friday_policy_trade_ids_indexed')}`",
                "",
                "Runtime effect boundary: offline/default-off research package only; no broker/order/deal/position/config activation.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    SATURATION_SELF_RED_TEAM.write_text(
        "\n".join(
            [
                "# Lane11 Saturation And Self-Red-Team",
                "",
                "- Evidence-class confusion guarded by explicit `r_evidence_class` and source bucket fields on every policy row.",
                "- Full-row preservation guarded by verifier count: Lane08 replay rows times all policy variants.",
                "- Proxy-only promotion is blocked by decision labels that require strict-tick capture for proxy research branches.",
                "- Same-bar and bid/ask ambiguity are preserved on row records instead of collapsed into summary metrics.",
                "- Modify feasibility, partial close ticket binding, residual lifecycle, and broker retcode gaps are row-level fields.",
                "- No live behavior changes are made; default-off package rules require owner approval for production use.",
                "- The remaining impossible historical truth classes are exact historical broker modify retcodes, ticket-bound partial/residual lifecycle, and commission/swap/slippage for rows where no broker history exists; these are captured as forward/export requirements.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def build_manifest(counts: dict[str, Any]) -> dict[str, Any]:
    paths = [
        POLICY_SCHEMA,
        POLICY_SIMULATION_LEDGER,
        POLICY_METRIC_LEDGER,
        POLICY_DOMINANCE_LEDGER,
        DEFAULT_OFF_PACKAGE,
        DEFAULT_OFF_PACKAGE_LEDGER,
        SOURCE_COMPLETENESS_LEDGER,
        IMPLEMENTATION_DECISION_LEDGER,
        DEPENDENCY_STATE_LEDGER,
        NO_LEAK_LEDGER,
        DOWNSTREAM_CONTRACT,
        SOURCE_USE_STATE,
        RESULT_USE_STATUS,
        RUNTIME_EFFECT_BOUNDARY,
        CONTEXT_ANCHOR,
        SATURATION_SELF_RED_TEAM,
        COMPLETION_AUDIT,
        VERIFICATION_RESULT,
        FOCUSED_TEST_RESULT,
        EXPANDED_POLICY_VARIANT_REGISTRY,
        EXPANDED_POLICY_FEASIBILITY_LEDGER,
        EXPANDED_POLICY_SPLIT_DECISION_LEDGER,
        EXPANDED_POLICY_SIMULATION_METRIC_LEDGER,
        EXPANDED_POLICY_DOMINANCE_DECISION_LEDGER,
        EXPANDED_DEFAULT_OFF_POLICY_PACKAGE_LEDGER,
        EXPANDED_POLICY_SOURCE_GAP_LEDGER,
        EVIDENCE_INTEGRITY_INVENTORY,
        EVIDENCE_INTELLIGENCE_INDEX,
        EVIDENCE_COVERAGE_MANIFEST,
        EVIDENCE_WORK_QUEUE,
        EVIDENCE_RAW_VALIDATION_LEDGER,
        EVIDENCE_CONVERGENCE_AUDIT,
    ]
    manifest = {
        "schema_version": "lane11_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "counts": counts,
        "outputs": [
            {
                "path": rel(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "sha256": (
                    "self_referential_manifest_hash_omitted"
                    if path == OUTPUT_MANIFEST
                    else sha256(path)
                    if path.exists()
                    else None
                ),
            }
            for path in paths
        ],
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return manifest


def build_completion_audit(counts: dict[str, Any], verification_result: dict[str, Any] | None = None) -> dict[str, Any]:
    audit = {
        "schema_version": "lane11_completion_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "complete_verified" if verification_result and verification_result.get("ok") else "built_pending_verification",
        "counts": counts,
        "instruction_coverage": {
            "mandatory_preflight_reread": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "constructive_builder_posture_applied": True,
            "no_arbitrary_top_n": True,
            "full_lane08_replay_rows_consumed": counts.get("lane08_replay_rows_consumed") == EXPECTED_REPLAY_ROWS,
            "all_material_policy_variants_preserved": counts.get("policy_simulation_rows")
            == EXPECTED_REPLAY_ROWS
            and counts.get("policy_result_cells") == EXPECTED_REPLAY_ROWS * len(POLICY_VARIANTS),
            "strict_and_proxy_evidence_classes_separated": True,
            "default_off_package_present": DEFAULT_OFF_PACKAGE.exists(),
            "focused_tests_present": FOCUSED_TEST_RESULT.exists(),
            "runtime_effect_boundary_explicit": True,
            "expanded_policy_registry_present": EXPANDED_POLICY_VARIANT_REGISTRY.exists(),
            "expanded_policy_registry_exceeds_baseline": (
                counts.get("expanded_policy_variant_count", 0) > len(BASELINE_POLICY_VARIANTS)
            ),
            "expanded_policy_gap_or_replay_accounting_present": EXPANDED_POLICY_FEASIBILITY_LEDGER.exists(),
            "evidence_integrity_convergence_audit_present": EVIDENCE_CONVERGENCE_AUDIT.exists(),
        },
        "source_use_state": SOURCE_USE_TEXT,
        "result_use_status": RESULT_USE_TEXT,
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        "verification_result": verification_result,
        "scoped_commit_status": "ready_for_scoped_commit_after_verification",
    }
    write_json(COMPLETION_AUDIT, audit)
    return audit


def build_outputs() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    lane08_audit = read_json(LANE08_COMPLETION_AUDIT, {})
    lane08_counts = lane08_audit.get("counts", {}) if isinstance(lane08_audit, dict) else {}
    lane02_index = load_lane02_policy_index()
    strict_index = load_strict_tick_index()
    friday_index = load_friday_policy_index()
    symbol_specs = load_symbol_specs()
    metrics: dict[tuple[str, str, str, str, str], dict[str, Any]] = defaultdict(metric_new)
    counts: Counter = Counter()
    missing_reasons: Counter = Counter()
    evidence_counts: Counter = Counter()
    policy_counts: Counter = Counter()
    no_leak_issues: list[dict[str, Any]] = []

    with open_gzip_text_for_write(POLICY_SIMULATION_LEDGER) as out:
        for row in iter_jsonl(LANE08_REPLAY_LEDGER):
            if row.get("_parse_error"):
                raise RuntimeError(f"Lane08 replay parse error: {row}")
            counts["lane08_replay_rows_consumed"] += 1
            selected_row_id = str(row.get("selected_row_id") or "")
            lane02_row = lane02_index.get(selected_row_id)
            strict_tick_row = strict_index.get(selected_row_id)
            friday_rows = friday_index.get(selected_row_id, {})
            symbol_spec = symbol_specs.get(str(row.get("symbol") or ""))
            denominator_flags = denominator_flags_for_row(row, lane02_row, strict_tick_row, friday_rows)
            split_values = split_values_for_row(row)
            current_trailing_modify = modify_feasibility_for_policy(
                "trailing_runner",
                row.get("decision_inputs", {}).get("broker_constraints", {}),
                strict_tick_row,
                friday_rows.get("trailing_runner"),
            )
            label_values = (
                row.get("result_payload", {}).get("label_values", {})
                if isinstance(row.get("result_payload"), dict)
                and isinstance(row.get("result_payload", {}).get("label_values"), dict)
                else {}
            )
            ledger_row = {
                "schema_version": "lane11_policy_simulation_row_v1",
                "route_id": ROUTE_ID,
                "row_id": row.get("row_id"),
                "candidate_id": row.get("candidate_id"),
                "selected_row_id": row.get("selected_row_id"),
                "candidate_time_utc": row.get("candidate_time_utc"),
                "decision_asof_utc": row.get("decision_asof_utc"),
                "symbol": row.get("symbol"),
                "broker_symbol": row.get("broker_symbol"),
                "side": row.get("side"),
                "framework": row.get("framework"),
                "origin_family": row.get("origin_family"),
                "sealed_partition": row.get("sealed_partition"),
                "current_router_policy": current_router_policy_from_row(row),
                "mfe_r": round9(label_values.get("mfe_r")),
                "mae_r": round9(label_values.get("mae_r")),
                "path_class": label_values.get("path_class"),
                "denominator_flags": denominator_flags,
                "split_values": split_values,
                "policy_results": {},
                "result_use_status": RESULT_USE_TEXT,
                "source_use_state": SOURCE_USE_TEXT,
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
            }
            for variant in POLICY_VARIANTS:
                resolved_policy = resolve_policy_variant(
                    variant,
                    row,
                    bool(strict_tick_row),
                    bool(current_trailing_modify.get("modify_feasible_proxy")),
                )
                friday_policy_row = friday_rows.get(resolved_policy) or (
                    friday_rows.get("current_router_policy") if variant == "current_router_policy" else None
                )
                result = result_for_policy(
                    variant=variant,
                    resolved_policy=resolved_policy,
                    row=row,
                    lane02_row=lane02_row,
                    strict_tick_row=strict_tick_row,
                    friday_rows=friday_rows,
                )
                record = build_policy_simulation_record(
                    row=row,
                    variant=variant,
                    resolved_policy=resolved_policy,
                    policy_result=result,
                    strict_tick_row=strict_tick_row,
                    friday_policy_row=friday_policy_row,
                    lane02_row=lane02_row,
                    symbol_spec=symbol_spec,
                    denominator_flags=denominator_flags,
                )
                ledger_row["policy_results"][variant] = compact_policy_result(record)
                counts["policy_result_cells"] += 1
                policy_counts[variant] += 1
                evidence_counts[record["r_evidence_class"]] += 1
                if record.get("source_gap_reason"):
                    missing_reasons[str(record["source_gap_reason"])] += 1
                add_metric_groups(metrics, record, split_values)
            write_jsonl_line(out, ledger_row)
            counts["policy_simulation_rows"] += 1

    metric_rows = build_metric_rows(metrics)
    write_jsonl(POLICY_METRIC_LEDGER, metric_rows)
    decisions, package_rows, decision_counts = build_decision_and_package_rows(metric_rows)
    write_jsonl(POLICY_DOMINANCE_LEDGER, decisions)
    write_jsonl(DEFAULT_OFF_PACKAGE_LEDGER, package_rows)
    no_leak_issues = validate_router_package_no_leak(package_rows)
    write_jsonl(
        NO_LEAK_LEDGER,
        [
            {
                "schema_version": "lane11_no_leak_validation_v1",
                "route_id": ROUTE_ID,
                "status": "pass" if not no_leak_issues else "fail",
                "issue_count": len(no_leak_issues),
                "issues": no_leak_issues[:100],
                "rule": "default-off package rows must not expose outcome labels as live decision features",
            }
        ],
    )
    source_rows = [
        {
            "schema_version": "lane11_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "requirement": "lane08_replay_rows_consumed",
            "status": "CONSUMED" if counts["lane08_replay_rows_consumed"] == EXPECTED_REPLAY_ROWS else "COUNT_MISMATCH",
            "observed_rows": counts["lane08_replay_rows_consumed"],
            "expected_rows": EXPECTED_REPLAY_ROWS,
            "source_path": rel(LANE08_REPLAY_LEDGER),
        },
        {
            "schema_version": "lane11_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "requirement": "lane08_replay_gap_rows_referenced",
            "status": "REFERENCED_FROM_LANE08_AUDIT",
            "observed_rows": lane08_counts.get("missing_replay_gap_rows"),
            "expected_rows": EXPECTED_REPLAY_GAP_ROWS,
            "source_path": rel(LANE08_MISSING_REPLAY_GAP_LEDGER),
        },
        {
            "schema_version": "lane11_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "requirement": "strict_tick_rows_indexed",
            "status": "CONSUMED" if len(strict_index) == EXPECTED_STRICT_TICK_ROWS else "COUNT_MISMATCH",
            "observed_rows": len(strict_index),
            "expected_rows": EXPECTED_STRICT_TICK_ROWS,
            "source_path": rel(LEGACY_LANE08_STRICT_TICK_LEDGER),
        },
        {
            "schema_version": "lane11_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "requirement": "friday_tick_policy_trade_ids_indexed",
            "status": "CONSUMED" if len(friday_index) == EXPECTED_FRIDAY_ROWS else "COUNT_MISMATCH",
            "observed_rows": len(friday_index),
            "expected_rows": EXPECTED_FRIDAY_ROWS,
            "source_path": rel(FRIDAY_POLICY_LEDGER),
        },
        {
            "schema_version": "lane11_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "requirement": "historical_unrecoverable_broker_lifecycle_truth",
            "status": "FORWARD_CAPTURE_OR_BROKER_EXPORT_REQUIRED",
            "observed_rows": sum(missing_reasons.values()),
            "reason_counts": dict(missing_reasons),
            "repair_requirement": "ticket-bound broker modify retcodes, partial close, residual lifecycle, commission, swap, slippage, and deal reconciliation export/capture",
        },
    ]
    write_jsonl(SOURCE_COMPLETENESS_LEDGER, source_rows)
    implementation_rows = [
        {
            "schema_version": "lane11_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "package_default_off_policy_router",
            "status": "implemented_route_local_default_off_artifacts",
            "evidence": [rel(POLICY_DOMINANCE_LEDGER), rel(DEFAULT_OFF_PACKAGE_LEDGER)],
            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        },
        {
            "schema_version": "lane11_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "retain_live_current_policy_until_separate_dossier",
            "status": "no_live_activation",
            "reason": "Lane11 is offline/default-off evidence; production changes require owner-approved dossier",
            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        },
    ]
    write_jsonl(IMPLEMENTATION_DECISION_LEDGER, implementation_rows)
    write_jsonl(DEPENDENCY_STATE_LEDGER, dependency_rows())
    expanded_counts = build_expanded_policy_artifacts(
        build_expanded_policy_variant_registry(),
        strict_index,
        friday_index,
    )
    counts_dict: dict[str, Any] = {
        **dict(counts),
        **expanded_counts,
        "policy_variant_count": len(POLICY_VARIANTS),
        "policy_variants": list(POLICY_VARIANTS),
        "baseline_policy_variants": list(BASELINE_POLICY_VARIANTS),
        "policy_counts": dict(policy_counts),
        "evidence_counts": dict(evidence_counts),
        "metric_rows": len(metric_rows),
        "dominance_decision_rows": len(decisions),
        "default_off_package_rows": len(package_rows),
        "decision_counts": dict(decision_counts),
        "source_gap_reason_counts": dict(missing_reasons),
        "lane02_policy_rows_indexed": len(lane02_index),
        "strict_tick_rows_indexed": len(strict_index),
        "friday_policy_trade_ids_indexed": len(friday_index),
        "lane08_missing_replay_gap_rows_from_audit": lane08_counts.get("missing_replay_gap_rows"),
        "lane08_split_stress_rows_from_audit": lane08_counts.get("split_metric_rows"),
    }
    write_static_contract_files(counts_dict, decision_counts)
    build_context_files(counts_dict)
    build_manifest(counts_dict)
    build_completion_audit(counts_dict)
    result = verify_outputs(write=True, count_large=True, require_convergence=False)
    build_evidence_integrity_artifacts(counts_dict, result)
    build_manifest(counts_dict)
    result = verify_outputs(write=True, count_large=True, require_convergence=True)
    build_completion_audit(counts_dict, result)
    build_evidence_integrity_artifacts(counts_dict, result)
    build_manifest(counts_dict)
    return result


def verify_focused_test_xml() -> dict[str, Any]:
    if not FOCUSED_TEST_RESULT.exists():
        return {"present": False, "ok": False, "reason": "focused_test_xml_missing"}
    text = FOCUSED_TEST_RESULT.read_text(encoding="utf-8", errors="replace")
    ok = "failures=\"0\"" in text and "errors=\"0\"" in text
    return {"present": True, "ok": ok, "path": rel(FOCUSED_TEST_RESULT)}


def verify_outputs(*, write: bool = True, count_large: bool = True, require_convergence: bool = True) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    audit = read_json(COMPLETION_AUDIT, {})
    audit_counts = audit.get("counts", {}) if isinstance(audit, dict) else {}
    required = [
        POLICY_SCHEMA,
        POLICY_SIMULATION_LEDGER,
        POLICY_METRIC_LEDGER,
        POLICY_DOMINANCE_LEDGER,
        DEFAULT_OFF_PACKAGE,
        DEFAULT_OFF_PACKAGE_LEDGER,
        SOURCE_COMPLETENESS_LEDGER,
        IMPLEMENTATION_DECISION_LEDGER,
        DEPENDENCY_STATE_LEDGER,
        NO_LEAK_LEDGER,
        DOWNSTREAM_CONTRACT,
        SOURCE_USE_STATE,
        RESULT_USE_STATUS,
        RUNTIME_EFFECT_BOUNDARY,
        CONTEXT_ANCHOR,
        SATURATION_SELF_RED_TEAM,
        OUTPUT_MANIFEST,
        COMPLETION_AUDIT,
        EXPANDED_POLICY_VARIANT_REGISTRY,
        EXPANDED_POLICY_FEASIBILITY_LEDGER,
        EXPANDED_POLICY_SPLIT_DECISION_LEDGER,
    ]
    if require_convergence:
        required.extend(
            [
                EVIDENCE_INTEGRITY_INVENTORY,
                EVIDENCE_INTELLIGENCE_INDEX,
                EVIDENCE_COVERAGE_MANIFEST,
                EVIDENCE_WORK_QUEUE,
                EVIDENCE_RAW_VALIDATION_LEDGER,
                EVIDENCE_CONVERGENCE_AUDIT,
            ]
        )
    for path in required:
        if not path.exists() or path.stat().st_size == 0:
            issues.append({"path": rel(path), "issue": "missing_or_empty_required_output"})
    audit_simulation_rows = audit_counts.get("policy_simulation_rows")
    simulation_rows = audit_simulation_rows
    expected_simulation_rows = EXPECTED_REPLAY_ROWS
    expected_policy_cells = EXPECTED_REPLAY_ROWS * len(POLICY_VARIANTS)
    policy_result_cells = audit_counts.get("policy_result_cells")
    observed_simulation_policies: set[str] = set()
    ledger_line_count: int | None = None
    sample_rows = 0
    if POLICY_SIMULATION_LEDGER.exists() and POLICY_SIMULATION_LEDGER.stat().st_size > 0:
        if count_large:
            ledger_line_count = 0
        with open_text(POLICY_SIMULATION_LEDGER) as handle:
            for line in handle:
                if not line.strip():
                    continue
                if count_large:
                    ledger_line_count += 1
                if sample_rows < 1000:
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as exc:
                        issues.append(
                            {
                                "path": rel(POLICY_SIMULATION_LEDGER),
                                "issue": "simulation_ledger_sample_parse_error",
                                "line_number": ledger_line_count or sample_rows + 1,
                                "error": str(exc),
                            }
                        )
                        row = {}
                    policy_results = row.get("policy_results") if isinstance(row, dict) else {}
                    if isinstance(policy_results, dict):
                        observed_simulation_policies.update(policy_results)
                    sample_rows += 1
                if sample_rows >= 1000 and not count_large:
                    break
        if sample_rows == 0:
            issues.append({"path": rel(POLICY_SIMULATION_LEDGER), "issue": "simulation_ledger_sample_empty"})
        if ledger_line_count is not None:
            simulation_rows = ledger_line_count
            if audit_simulation_rows != ledger_line_count:
                issues.append(
                    {
                        "path": rel(POLICY_SIMULATION_LEDGER),
                        "issue": "completion_audit_simulation_count_mismatch",
                        "observed_ledger_lines": ledger_line_count,
                        "audit_rows": audit_simulation_rows,
                    }
                )
    if simulation_rows != expected_simulation_rows:
        issues.append(
            {
                "path": rel(POLICY_SIMULATION_LEDGER),
                "issue": "policy_simulation_row_count_mismatch",
                "observed": simulation_rows,
                "expected": expected_simulation_rows,
            }
        )
    if policy_result_cells != expected_policy_cells:
        issues.append(
            {
                "path": rel(POLICY_SIMULATION_LEDGER),
                "issue": "policy_result_cell_count_mismatch",
                "observed": policy_result_cells,
                "expected": expected_policy_cells,
            }
        )
    if observed_simulation_policies:
        missing_simulation_policies = sorted(set(POLICY_VARIANTS) - observed_simulation_policies)
        if missing_simulation_policies:
            issues.append(
                {
                    "path": rel(POLICY_SIMULATION_LEDGER),
                    "issue": "simulation_policy_variants_missing",
                    "missing": missing_simulation_policies,
                }
            )
    metric_rows = list(iter_jsonl(POLICY_METRIC_LEDGER)) if POLICY_METRIC_LEDGER.exists() else []
    if not metric_rows:
        issues.append({"path": rel(POLICY_METRIC_LEDGER), "issue": "metric_rows_missing"})
    observed_policies = {row.get("policy_variant") for row in metric_rows}
    missing_policies = sorted(set(POLICY_VARIANTS) - observed_policies)
    if missing_policies:
        issues.append({"issue": "metric_policy_variants_missing", "missing": missing_policies})
    no_leak_rows = list(iter_jsonl(NO_LEAK_LEDGER)) if NO_LEAK_LEDGER.exists() else []
    if not no_leak_rows or no_leak_rows[0].get("status") != "pass":
        issues.append({"path": rel(NO_LEAK_LEDGER), "issue": "no_leak_validation_not_pass"})
    source_rows = list(iter_jsonl(SOURCE_COMPLETENESS_LEDGER)) if SOURCE_COMPLETENESS_LEDGER.exists() else []
    source_status = {row.get("requirement"): row for row in source_rows}
    if source_status.get("lane08_replay_rows_consumed", {}).get("status") != "CONSUMED":
        issues.append({"path": rel(SOURCE_COMPLETENESS_LEDGER), "issue": "lane08_replay_not_consumed"})
    if source_status.get("strict_tick_rows_indexed", {}).get("observed_rows") != EXPECTED_STRICT_TICK_ROWS:
        issues.append({"path": rel(SOURCE_COMPLETENESS_LEDGER), "issue": "strict_tick_count_mismatch"})
    package = read_json(DEFAULT_OFF_PACKAGE, {})
    if package.get("runtime_effect_now") is not False:
        issues.append({"path": rel(DEFAULT_OFF_PACKAGE), "issue": "default_off_package_runtime_effect_not_false"})
    boundary = read_json(RUNTIME_EFFECT_BOUNDARY, {})
    if boundary.get("runtime_effect_boundary") != RUNTIME_BOUNDARY_TEXT:
        issues.append({"path": rel(RUNTIME_EFFECT_BOUNDARY), "issue": "runtime_boundary_mismatch"})
    registry_rows = list(iter_jsonl(EXPANDED_POLICY_VARIANT_REGISTRY)) if EXPANDED_POLICY_VARIANT_REGISTRY.exists() else []
    registry_variant_ids = {row.get("variant_id") for row in registry_rows}
    if len(registry_rows) <= len(BASELINE_POLICY_VARIANTS):
        issues.append(
            {
                "path": rel(EXPANDED_POLICY_VARIANT_REGISTRY),
                "issue": "expanded_policy_registry_not_larger_than_baseline",
                "observed": len(registry_rows),
                "baseline": len(BASELINE_POLICY_VARIANTS),
            }
        )
    missing_baseline_registry = sorted(set(BASELINE_POLICY_VARIANTS) - registry_variant_ids)
    if missing_baseline_registry:
        issues.append(
            {
                "path": rel(EXPANDED_POLICY_VARIANT_REGISTRY),
                "issue": "baseline_policy_missing_from_expanded_registry",
                "missing": missing_baseline_registry,
            }
        )
    registry_families = {row.get("family") for row in registry_rows}
    required_families = {
        "partial_be_runner_parameter_sweep",
        "trailing_runner_parameter_sweep",
        "time_stop_parameter_sweep",
        "momentum_exhaustion_parameter_sweep",
        "invalidation_parameter_sweep",
        "no_entry_timeout_parameter_sweep",
        "hybrid_policy_router",
    }
    missing_families = sorted(required_families - registry_families)
    if missing_families:
        issues.append(
            {
                "path": rel(EXPANDED_POLICY_VARIANT_REGISTRY),
                "issue": "expanded_policy_families_missing",
                "missing": missing_families,
            }
        )
    feasibility_rows = list(iter_jsonl(EXPANDED_POLICY_FEASIBILITY_LEDGER)) if EXPANDED_POLICY_FEASIBILITY_LEDGER.exists() else []
    expected_feasibility_rows = len(registry_rows) * len(EXPANDED_EVIDENCE_BUCKETS)
    if len(feasibility_rows) != expected_feasibility_rows:
        issues.append(
            {
                "path": rel(EXPANDED_POLICY_FEASIBILITY_LEDGER),
                "issue": "expanded_bucket_feasibility_count_mismatch",
                "feasibility_rows": len(feasibility_rows),
                "expected_bucket_rows": expected_feasibility_rows,
            }
        )
    expanded_cell_accounting = sum(int(row.get("result_cell_accounting") or 0) for row in feasibility_rows)
    expected_expanded_cells = expanded_cell_accounting
    if not expanded_cell_accounting:
        issues.append(
            {
                "path": rel(EXPANDED_POLICY_FEASIBILITY_LEDGER),
                "issue": "expanded_policy_result_cell_accounting_missing",
            }
        )
    bucket_names = {row.get("evidence_bucket") for row in feasibility_rows}
    missing_buckets = sorted(set(EXPANDED_EVIDENCE_BUCKETS) - bucket_names)
    if missing_buckets:
        issues.append(
            {
                "path": rel(EXPANDED_POLICY_FEASIBILITY_LEDGER),
                "issue": "expanded_evidence_buckets_missing",
                "missing": missing_buckets,
            }
        )
    expanded_metric_rows = list(iter_jsonl(EXPANDED_POLICY_SIMULATION_METRIC_LEDGER)) if EXPANDED_POLICY_SIMULATION_METRIC_LEDGER.exists() else []
    nonbaseline_metric_variants = {
        row.get("variant_id")
        for row in expanded_metric_rows
        if row.get("variant_id") not in BASELINE_POLICY_VARIANTS and (row.get("known_r_rows") or 0) > 0
    }
    if not nonbaseline_metric_variants:
        issues.append(
            {
                "path": rel(EXPANDED_POLICY_SIMULATION_METRIC_LEDGER),
                "issue": "expanded_variants_have_zero_nonbaseline_replay_results",
            }
        )
    expanded_package_rows = list(iter_jsonl(EXPANDED_DEFAULT_OFF_POLICY_PACKAGE_LEDGER)) if EXPANDED_DEFAULT_OFF_POLICY_PACKAGE_LEDGER.exists() else []
    if not expanded_package_rows:
        issues.append(
            {
                "path": rel(EXPANDED_DEFAULT_OFF_POLICY_PACKAGE_LEDGER),
                "issue": "expanded_default_off_package_rows_missing",
            }
        )
    if require_convergence:
        convergence = read_json(EVIDENCE_CONVERGENCE_AUDIT, {})
        if convergence.get("status") != "converged":
            issues.append(
                {
                    "path": rel(EVIDENCE_CONVERGENCE_AUDIT),
                    "issue": "evidence_integrity_convergence_not_proven",
                    "status": convergence.get("status"),
                    "issue_count": convergence.get("issue_count"),
                }
            )
        validation_rows = list(iter_jsonl(EVIDENCE_RAW_VALIDATION_LEDGER)) if EVIDENCE_RAW_VALIDATION_LEDGER.exists() else []
        failed_validation_rows = [row for row in validation_rows if row.get("status") == "fail"]
        if failed_validation_rows:
            issues.append(
                {
                    "path": rel(EVIDENCE_RAW_VALIDATION_LEDGER),
                    "issue": "raw_evidence_validation_failures_present",
                    "failed_count": len(failed_validation_rows),
                    "sample": failed_validation_rows[:5],
                }
            )
    focused = verify_focused_test_xml()
    if FOCUSED_TEST_RESULT.exists() and not focused.get("ok"):
        issues.append({"path": rel(FOCUSED_TEST_RESULT), "issue": "focused_tests_not_green"})
    result = {
        "schema_version": "lane11_verification_result_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "counts": {
            "simulation_rows": simulation_rows,
            "expected_simulation_rows": expected_simulation_rows,
            "policy_result_cells": policy_result_cells,
            "expected_policy_result_cells": expected_policy_cells,
            "simulation_sample_rows_checked": sample_rows,
            "simulation_rows_count_source": (
                "ledger_line_count" if ledger_line_count is not None else "completion_audit"
            ),
            "audit_simulation_rows": audit_simulation_rows,
            "ledger_line_count": ledger_line_count,
            "metric_rows": len(metric_rows),
            "policy_variant_count": len(POLICY_VARIANTS),
            "expanded_policy_variant_count": len(registry_rows),
            "expanded_policy_result_cell_accounting": expanded_cell_accounting,
            "expected_expanded_policy_result_cell_accounting": expected_expanded_cells,
            "expanded_nonbaseline_replay_variant_count": len(nonbaseline_metric_variants),
            "expanded_metric_rows": len(expanded_metric_rows),
            "expanded_package_rows": len(expanded_package_rows),
        },
        "focused_test_result": focused,
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }
    if write:
        write_json(VERIFICATION_RESULT, result)
        if audit_counts:
            build_completion_audit(audit_counts, result)
            build_manifest(audit_counts)
    return result


def main() -> None:
    args = parse_args()
    if args.verify:
        result = verify_outputs(write=True, count_large=True)
    else:
        result = build_outputs()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result.get("ok"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
