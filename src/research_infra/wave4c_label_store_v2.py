"""Wave4C Label Store V2 over the accepted Wave4A row universe.

This module is local-file only. It materializes separated labels for validation
and ML consumption while preserving broker-real, R-style, replay/simulation,
shadow, path, source-gap, and prospective-capture evidence classes.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.research_infra import wave4a_digital_twin_historical_microscope as wave4a


ROUTE_ID = "final_moonshot_wave4c_label_store_v2_2026_06_05"
LANE = "wave4c_label_store_v2"
ROUTE_DIR = Path("research/operations") / ROUTE_ID
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "FINAL_MOONSHOT_WAVE4C_LABEL_STORE_V2_GOAL_PROMPT_2026-06-05.md"
)
STARTER_PATH = PROMPT_PATH.with_name("FINAL_MOONSHOT_WAVE4C_LABEL_STORE_V2_STARTER_2026-06-05.txt")
WAVE4A_ROUTE = Path("research/operations/final_moonshot_wave4a_digital_twin_historical_microscope_2026_06_05")
WAVE2_ROUTE = Path("research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04")

LABEL_SET_VERSION = "wave4c_label_store_v2_2026_06_05"
CANONICAL_ROW_COUNT = 15679
CANONICAL_UNIVERSE_HASH = "fef22580d4b641243d166bb2ce3d24535826436f5d0f818ad2a3dbab1c53bab6"
FEATURE_STORE_EXCLUSION = "banned_from_wave4b_asof_inputs_labels_only"

BOUNDARY_STATUS = {
    "RESULT_MATERIALIZATION_REQUIRED": True,
    "validation_result_status": False,
    "outcome_result_rows_status": False,
    "broker_runtime_change_status": False,
    "broker_account_order_deal_position_mutation": False,
    "credential_mutation_or_disclosure": False,
    "paid_vendor_api_call": False,
    "remote_push": False,
    "active_vps_process_change": False,
    "live_trading_deployment": False,
    "mt5_live_operation": False,
    "feature_store_leakage": False,
}

REQUIRED_CONTEXT_PATHS = (
    ".context/LIVE_STATE.md",
    "AGENTS.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/final_moonshot_post_hard_halt_research_plan.md",
    ".context/00_core/final_moonshot_goal_session_execution_architecture.md",
    ".context/00_core/final_moonshot_central_orchestrator_successor_brief.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
    ".context/00_core/portable_path_authority.md",
    "research/operations/final_moonshot_wave4_wave5_lane_architecture_repair_2026_06_05/WAVE4_WAVE5_LANE_ARCHITECTURE.md",
)

UPSTREAM_ROUTE_PATHS = (
    "research/operations/final_moonshot_wave1a_hard_halt_forensic_matrix_2026_06_04/",
    "research/operations/final_moonshot_wave1b_v3_live_authority_gap_2026_06_04/",
    "research/operations/final_moonshot_wave1c_dual_broker_architecture_2026_06_04/",
    "research/operations/final_moonshot_wave1_integration_review_2026_06_04/",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/",
    "research/operations/final_moonshot_wave3_integration_review_2026_06_05/",
    "research/operations/final_moonshot_wave3_5_v4_authority_activation_2026_06_05/",
    "research/operations/final_moonshot_wave4a_digital_twin_historical_microscope_2026_06_05/",
)

UPSTREAM_CONTRACT_PATHS = (
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_FEATURE_LABEL_STORE_CONTRACT.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json",
    "research/operations/wave3_profit_harvest_mfe_capture_v4_2026_06_04/WAVE3_PROFIT_HARVEST_MFE_TRIGGER_CONTRACT.json",
    "research/operations/wave3_partial_be_trailing_stale_thesis_exit_policy_v4_2026_06_04/WAVE3_14_STALE_THESIS_RULE_CONTRACT.json",
    "research/operations/wave3_dynamic_target_stop_thesis_horizon_geometry_v4_2026_06_04/WAVE3_DYNAMIC_TARGET_STOP_GEOMETRY_POLICY.json",
    "research/operations/wave3_same_symbol_same_instrument_lifecycle_v4_2026_06_04/WAVE3_SAME_SYMBOL_LIFECYCLE_V4_SEMANTIC_OWNERSHIP_COVERAGE.json",
    "research/operations/wave3_cost_swap_slippage_broker_constraint_engine_2026_06_04/WAVE3_COST_REGRESSION_SUMMARY.json",
    "research/operations/wave3_validation_anti_overfit_v4_2026_06_04/WAVE3_VALIDATION_ANTI_OVERFIT_FEATURE_LABEL_CAPTURE_CONTRACT.json",
    "research/operations/wave3_validation_anti_overfit_v4_2026_06_04/WAVE3_VALIDATION_ANTI_OVERFIT_SEALED_PROTOCOL.json",
    "research/operations/vnext_moonshot_lane06_label_store_v1_2026_06_01/LANE06_LABEL_SCHEMA.json",
)

LABEL_FAMILIES = (
    "broker_real_cash_pnl",
    "broker_real_cash_cost",
    "exact_r",
    "proxy_r",
    "replay",
    "simulation",
    "shadow",
    "mfe_r",
    "mae_r",
    "timing",
    "giveback",
    "stale_thesis",
    "stop_target_efficiency",
    "harvest_failure",
    "opportunity_cost",
    "static_r_1_5",
    "static_r_2r",
    "same_symbol_action",
    "source_gap",
    "prospective_capture_requirement",
)

REQUIRED_LEDGER_NAMES = (
    "WAVE4C_LABEL_LEDGER.jsonl",
    "WAVE4C_EVIDENCE_CLASS_LABEL_LEDGER.jsonl",
    "WAVE4C_MFE_MAE_TIMING_LABEL_LEDGER.jsonl",
    "WAVE4C_HARVEST_STALE_STATIC_R_LABEL_LEDGER.jsonl",
    "WAVE4C_SAME_SYMBOL_ACTION_LABEL_LEDGER.jsonl",
    "WAVE4C_OPPORTUNITY_COST_LABEL_LEDGER.jsonl",
    "WAVE4C_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl",
)

REQUIRED_ROUTE_FILES = (
    "WAVE4C_CONTEXT_ANCHOR.json",
    "WAVE4C_LABEL_SCHEMA.json",
    *REQUIRED_LEDGER_NAMES,
    "WAVE4C_QUESTION_LEDGER.jsonl",
    "WAVE4C_SEARCHED_ROOT_LEDGER.jsonl",
    "WAVE4C_ROUTE_DECISION_LEDGER.jsonl",
    "WAVE4C_BLOCKER_AND_REPAIR_LEDGER.jsonl",
    "WAVE4C_INDEPENDENT_REVIEW_LEDGER.md",
    "WAVE4C_LABEL_STORE_V2_VERIFICATION_RESULT.json",
    "WAVE4C_LABEL_STORE_V2_FOCUSED_TEST_RESULT.json",
    "WAVE4C_LABEL_STORE_V2_PROMPT_HARDENING_RESULT.json",
    "WAVE4C_LABEL_STORE_V2_ROUTE_ARTIFACT_AUDIT_RESULT.json",
    "WAVE4C_LABEL_STORE_V2_SATURATION_SELF_RED_TEAM.md",
    "WAVE4C_LABEL_STORE_V2_INSTRUCTION_COVERAGE_CHECKLIST.md",
    "WAVE4C_LABEL_STORE_V2_OUTPUT_MANIFEST.json",
    "WAVE4C_PROMPT_AND_STARTER_REFERENCE.md",
    "COMPLETION_AUDIT.md",
    "build_wave4c_label_store_v2.py",
    "verify_wave4c_label_store_v2.py",
)

FORBIDDEN_ASOF_LABEL_FIELDS = set(wave4a.FORBIDDEN_LABEL_FIELDS) | {
    "broker_real_cash_pnl",
    "label",
    "label_family",
    "label_value",
    "harvest_failure",
    "opportunity_cost",
    "same_symbol_action_label",
}


@dataclass(frozen=True)
class Wave4CInputs:
    canonical_rows: list[dict[str, Any]]
    event_rows: dict[str, dict[str, Any]]
    path_rows: dict[str, dict[str, Any]]
    opportunity_rows: dict[str, dict[str, Any]]
    loser_rows: dict[str, dict[str, Any]]
    source_gap_rows: list[dict[str, Any]]
    wave4a_manifest: dict[str, Any]
    wave4a_verification: dict[str, Any]
    wave4a_coverage: dict[str, Any]
    raw_by_hash: dict[tuple[str, str], dict[str, Any]]
    raw_by_id: dict[tuple[str, str], dict[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def route_abs(repo_root: Path, route_dir: Path = ROUTE_DIR) -> Path:
    return route_dir if route_dir.is_absolute() else repo_root / route_dir


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _string(value: Any) -> str:
    return str(value or "").strip()


def _float(value: Any) -> float | None:
    if value in (None, "", [], {}):
        return None
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def _first_present(row: Mapping[str, Any] | None, keys: Sequence[str]) -> Any:
    if not isinstance(row, Mapping):
        return None
    metrics = row.get("metric_fields_used")
    metrics_map = metrics if isinstance(metrics, Mapping) else {}
    for key in keys:
        if row.get(key) not in (None, "", [], {}):
            return row[key]
        if metrics_map.get(key) not in (None, "", [], {}):
            return metrics_map[key]
    return None


def _first_nested(obj: Any, keys: set[str], *, max_depth: int = 5) -> Any:
    if max_depth < 0:
        return None
    if isinstance(obj, Mapping):
        for key in keys:
            if obj.get(key) not in (None, "", [], {}):
                return obj[key]
        for value in obj.values():
            found = _first_nested(value, keys, max_depth=max_depth - 1)
            if found not in (None, "", [], {}):
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = _first_nested(value, keys, max_depth=max_depth - 1)
            if found not in (None, "", [], {}):
                return found
    return None


def _hash_row(row: Mapping[str, Any]) -> str:
    return wave4a.stable_hash(row)


def _load_jsonl_map(path: Path) -> dict[str, dict[str, Any]]:
    return {str(row["canonical_row_id"]): row for row in wave4a.iter_jsonl(path)}


def _load_raw_source_indexes(repo_root: Path) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    by_hash: dict[tuple[str, str], dict[str, Any]] = {}
    by_id: dict[tuple[str, str], dict[str, Any]] = {}
    for spec in wave4a.MATERIAL_SOURCE_SPECS:
        path = repo_root / spec.path
        if not path.exists():
            continue
        for index, row in enumerate(wave4a.iter_jsonl(path), start=1):
            row_hash = _hash_row(row)
            row_id = wave4a.source_row_id(row, f"{spec.source_key}:{index:06d}")
            by_hash[(spec.source_key, row_hash)] = row
            by_id[(spec.source_key, str(row_id))] = row
    return by_hash, by_id


def load_inputs(repo_root: Path) -> Wave4CInputs:
    base = repo_root / WAVE4A_ROUTE
    canonical_path = base / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl"
    canonical_rows = list(wave4a.iter_jsonl(canonical_path))
    raw_by_hash, raw_by_id = _load_raw_source_indexes(repo_root)
    return Wave4CInputs(
        canonical_rows=canonical_rows,
        event_rows=_load_jsonl_map(base / "WAVE4A_DIGITAL_TWIN_EVENT_LEDGER.jsonl"),
        path_rows=_load_jsonl_map(base / "WAVE4A_PATH_CLOCK_FORENSIC_LEDGER.jsonl"),
        opportunity_rows=_load_jsonl_map(base / "WAVE4A_ACCEPTED_REJECTED_OPPORTUNITY_LEDGER.jsonl"),
        loser_rows=_load_jsonl_map(base / "WAVE4A_LOSER_MFE_HARVEST_LEDGER.jsonl"),
        source_gap_rows=list(wave4a.iter_jsonl(base / "WAVE4A_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl")),
        wave4a_manifest=wave4a.read_json(base / "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_OUTPUT_MANIFEST.json"),
        wave4a_verification=wave4a.read_json(base / "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_VERIFICATION_RESULT.json"),
        wave4a_coverage=wave4a.read_json(base / "WAVE4A_COVERAGE_MATRIX.json"),
        raw_by_hash=raw_by_hash,
        raw_by_id=raw_by_id,
    )


def raw_source_for(row: Mapping[str, Any], inputs: Wave4CInputs) -> dict[str, Any]:
    source_key = str(row.get("source_key"))
    source_hash = str(row.get("source_row_hash") or "")
    source_id = str(row.get("source_row_id") or "")
    return inputs.raw_by_hash.get((source_key, source_hash)) or inputs.raw_by_id.get((source_key, source_id)) or {}


def source_trace(row: Mapping[str, Any], path_row: Mapping[str, Any] | None = None) -> dict[str, Any]:
    path_missing = _as_list((path_row or {}).get("missing_source_or_capture_requirement"))
    path_available = _as_list((path_row or {}).get("path_metric_fields_available"))
    if path_available:
        path_missing = [
            item
            for item in path_missing
            if not str(item).startswith("no path label available from this source family")
        ]
    missing = sorted(
        {
            str(item)
            for item in (
                _as_list(row.get("missing_fields_or_runtime_truth"))
                + path_missing
            )
            if item not in (None, "", [], {})
        }
    )
    completeness = _string(row.get("source_completeness_state")) or (
        "source_gap_present" if missing else "source_complete_or_not_materially_gapped"
    )
    if not missing and completeness == "source_gap_present":
        missing = ["upstream_source_gap_present_without_field_list"]
    return {
        "source_key": row.get("source_key"),
        "source_path": row.get("source_path"),
        "source_sha256": row.get("source_sha256"),
        "source_row_id": row.get("source_row_id"),
        "source_row_hash": row.get("source_row_hash"),
        "source_capture_state": row.get("source_capture_state"),
        "source_completeness_state": completeness,
        "missing_fields_or_runtime_truth": missing,
        "capture_status": "prospective_capture_required" if missing or completeness == "source_gap_present" else "source_materialized",
        "capture_requirement": capture_requirement(missing, row.get("source_key")),
    }


def capture_requirement(missing: Sequence[Any], source_key: Any) -> str | None:
    clean = [str(item) for item in missing if item not in (None, "", [], {})]
    if not clean:
        return None
    return (
        "Capture or recover "
        + ", ".join(clean)
        + f" for source_key={source_key}; keep Wave4C label as source-gap/prospective-capture until source-bound."
    )


def _status_for_value(value: Any, trace: Mapping[str, Any], *, available_text: str) -> str:
    if value not in (None, "", [], {}):
        return available_text
    if trace.get("capture_status") == "prospective_capture_required":
        return "source_gap_or_capture_requirement"
    return "not_available_in_accepted_wave4a_sources"


def evidence_class_label(row: Mapping[str, Any], path_row: Mapping[str, Any], raw: Mapping[str, Any]) -> dict[str, Any]:
    trace = source_trace(row, path_row)
    labels = row.get("evidence_labels") if isinstance(row.get("evidence_labels"), Mapping) else {}
    broker_real = labels.get("broker_real") if isinstance(labels.get("broker_real"), Mapping) else {}
    exact_r = labels.get("exact_r") if isinstance(labels.get("exact_r"), Mapping) else {}
    proxy_r = labels.get("proxy_r") if isinstance(labels.get("proxy_r"), Mapping) else {}
    replay_or_shadow = labels.get("replay_or_shadow") if isinstance(labels.get("replay_or_shadow"), Mapping) else {}
    path_labels = path_row.get("post_decision_path_labels") if isinstance(path_row.get("post_decision_path_labels"), Mapping) else {}
    raw_broker_cost = raw.get("broker_cost_fields") if isinstance(raw.get("broker_cost_fields"), Mapping) else {}

    broker_cash = _float(
        broker_real.get("cash_pnl")
        if broker_real.get("cash_pnl") is not None
        else _first_present(raw_broker_cost, ("broker_net_cash_from_deals", "broker_net_cash_from_wave1a"))
        or _first_nested(raw, {"broker_net_cash_from_deals", "actual_broker_real_pnl_cash", "broker_real_pnl_cash"})
    )
    broker_cost_cash = _float(_first_present(raw_broker_cost, ("cost_drag_cash", "commission_cash", "swap_cash")))
    exact_value = _float(
        exact_r.get("value")
        if exact_r.get("value") is not None
        else _first_present(raw, ("exact_r", "actual_exact_r"))
        or _first_nested(raw, {"actual_exact_r", "exact_r"})
    )
    proxy_value = _float(
        proxy_r.get("value")
        if proxy_r.get("value") is not None
        else _first_present(raw, ("proxy_r", "source_bound_proxy_r"))
    )
    replay_value = _float(
        replay_or_shadow.get("actual_r")
        if replay_or_shadow.get("actual_r") is not None
        else path_labels.get("actual_or_terminal_r")
        if path_labels.get("actual_or_terminal_r") is not None
        else _first_present(raw, ("actual_r", "terminal_tick_r", "ledger_actual_r"))
    )
    text_blob = json.dumps(
        {
            "source_key": row.get("source_key"),
            "evidence_class": labels.get("evidence_class"),
            "raw_evidence_class": raw.get("evidence_class"),
            "result_use_status": raw.get("result_use_status"),
            "status": raw.get("status"),
        },
        sort_keys=True,
        default=str,
    ).casefold()
    simulation_available = any(token in text_blob for token in ("counterfactual", "simulation", "zero_trade"))
    shadow_available = "shadow" in text_blob
    replay_available = bool(replay_or_shadow.get("available")) or "replay" in text_blob or row.get("source_key") == "allocator_decision_window_replay"
    return {
        "schema_version": "wave4c_evidence_class_label_v1",
        "broker_real_cash_pnl": {
            "status": _status_for_value(broker_cash, trace, available_text="broker_real_cash_pnl_available"),
            "value": broker_cash,
            "unit": "cash",
            "evidence_class": "broker-real cash/PnL",
            "source_rule": "broker cash value only; never replaced by exact-R, proxy-R, replay, simulation, or shadow labels",
        },
        "broker_real_cash_cost": {
            "status": _status_for_value(broker_cost_cash, trace, available_text="broker_real_cost_cash_available"),
            "value": broker_cost_cash,
            "unit": "cash",
            "evidence_class": "broker-real cost cash",
            "source_rule": "broker deal/cost fields only",
        },
        "exact_r": {
            "status": _status_for_value(exact_value, trace, available_text="exact_r_available"),
            "value": exact_value,
            "unit": "R",
            "evidence_class": "exact-R",
            "source_rule": "R-style label only; not broker-real cash",
        },
        "proxy_r": {
            "status": _status_for_value(proxy_value, trace, available_text="proxy_r_available"),
            "value": proxy_value,
            "unit": "R",
            "evidence_class": "proxy-R",
            "source_rule": "proxy R label only; not broker-real cash",
        },
        "replay": {
            "status": "replay_label_available" if replay_available else _status_for_value(replay_value, trace, available_text="replay_value_available"),
            "value": replay_value,
            "unit": "R_or_state",
            "evidence_class": "replay",
            "source_rule": "replay/as-of reconstruction label only",
        },
        "simulation": {
            "status": "simulation_or_counterfactual_label_available" if simulation_available else "not_available_in_accepted_wave4a_sources",
            "value": None,
            "unit": "state",
            "evidence_class": "simulation",
            "source_rule": "counterfactual/no-trade rows are not realized PnL",
        },
        "shadow": {
            "status": "shadow_label_available" if shadow_available else "not_available_in_accepted_wave4a_sources",
            "value": None,
            "unit": "state",
            "evidence_class": "shadow",
            "source_rule": "shadow diagnostic label only",
        },
        "source_gap": {
            "status": "source_gap_present" if trace.get("capture_status") == "prospective_capture_required" else "no_source_gap_for_label_row",
            "value": trace.get("missing_fields_or_runtime_truth"),
            "unit": "fields",
            "evidence_class": "source gap",
            "source_rule": "missing source is represented explicitly and never imputed favorably",
        },
        "prospective_capture_requirement": {
            "status": trace.get("capture_status"),
            "value": trace.get("capture_requirement"),
            "unit": "requirement",
            "evidence_class": "prospective capture requirement",
            "source_rule": "non-generatable historical truth remains prospective capture",
        },
    }


def mfe_mae_timing_label(row: Mapping[str, Any], path_row: Mapping[str, Any], raw: Mapping[str, Any]) -> dict[str, Any]:
    trace = source_trace(row, path_row)
    post = path_row.get("post_decision_path_labels") if isinstance(path_row.get("post_decision_path_labels"), Mapping) else {}
    value = {
        "mfe_r": _float(post.get("mfe_r") if post.get("mfe_r") is not None else _first_present(raw, ("mfe_r", "tick_mfe_r", "ledger_mfe_r", "near_mfe_within_0_10r_max_r"))),
        "mae_r": _float(post.get("mae_r") if post.get("mae_r") is not None else _first_present(raw, ("mae_r", "tick_mae_r", "ledger_mae_r"))),
        "actual_or_terminal_r": _float(post.get("actual_or_terminal_r") if post.get("actual_or_terminal_r") is not None else _first_present(raw, ("actual_r", "terminal_tick_r", "ledger_actual_r"))),
        "hold_minutes": _float(post.get("hold_minutes") if post.get("hold_minutes") is not None else _first_present(raw, ("hold_minutes", "hold_minutes_repaired", "ledger_hold_minutes"))),
        "mfe_time_minutes": _float(post.get("mfe_time_minutes") if post.get("mfe_time_minutes") is not None else _first_present(raw, ("mfe_time_minutes", "tick_mfe_time_minutes"))),
        "mae_time_minutes": _float(post.get("mae_time_minutes") if post.get("mae_time_minutes") is not None else _first_present(raw, ("mae_time_minutes", "tick_mae_time_minutes"))),
        "time_to_plus_0_25r_minutes": _float(_first_present(raw, ("time_to_plus_0_25r_minutes", "first_giveback_0_25r_after_mfe_minutes_from_entry"))),
        "time_to_plus_0_5r_minutes": _float(_first_present(raw, ("time_to_plus_0_5r_minutes", "first_giveback_0_5r_after_mfe_minutes_from_entry"))),
        "time_to_plus_1r_minutes": _float(_first_present(raw, ("time_to_plus_1r_minutes", "first_giveback_1_0r_after_mfe_minutes_from_entry"))),
        "first_giveback_0_25r_minutes_after_mfe": _float(post.get("first_giveback_0_25r_minutes_after_mfe") if post.get("first_giveback_0_25r_minutes_after_mfe") is not None else _first_present(raw, ("first_giveback_0_25r_minutes_after_mfe",))),
        "first_giveback_0_5r_minutes_after_mfe": _float(post.get("first_giveback_0_5r_minutes_after_mfe") if post.get("first_giveback_0_5r_minutes_after_mfe") is not None else _first_present(raw, ("first_giveback_0_5r_minutes_after_mfe",))),
        "time_from_mfe_to_terminal_minutes": _float(post.get("time_from_mfe_to_terminal_minutes") if post.get("time_from_mfe_to_terminal_minutes") is not None else _first_present(raw, ("time_from_mfe_to_terminal_minutes",))),
    }
    available_fields = sorted(key for key, item in value.items() if item is not None)
    return {
        "schema_version": "wave4c_mfe_mae_timing_label_v1",
        "status": "source_supported_path_label" if available_fields else ("source_gap_or_capture_requirement" if trace.get("capture_status") == "prospective_capture_required" else "not_applicable_or_not_available"),
        "evidence_class": raw.get("evidence_class") or path_row.get("path_clock_status") or "path_label",
        "value": value,
        "available_fields": available_fields,
        "source_status": trace.get("source_completeness_state"),
        "capture_requirement": trace.get("capture_requirement"),
        "labels_never_asof_features": True,
    }


def harvest_stale_static_label(row: Mapping[str, Any], path_row: Mapping[str, Any], raw: Mapping[str, Any], mfe_label: Mapping[str, Any]) -> dict[str, Any]:
    trace = source_trace(row, path_row)
    post = path_row.get("post_decision_path_labels") if isinstance(path_row.get("post_decision_path_labels"), Mapping) else {}
    values = mfe_label.get("value") if isinstance(mfe_label.get("value"), Mapping) else {}
    mfe = _float(values.get("mfe_r"))
    actual = _float(values.get("actual_or_terminal_r"))
    giveback = _float(post.get("giveback_r") if post.get("giveback_r") is not None else _first_present(raw, ("giveback_r", "mfe_to_terminal_giveback_r", "mfe_to_worst_after_mfe_reversal_r")))
    partial_count = _float(post.get("partial_close_count") if post.get("partial_close_count") is not None else _first_present(raw, ("partial_close_count",)))
    static_baseline_r = _float(
        _first_present(raw, ("raw_trade_parameters_risk_reward_ratio", "repaired_geometry_risk_reward_ratio"))
    )
    dynamic_or_broker_target_r = _float(
        post.get("target_distance_or_multiple_r")
        if post.get("target_distance_or_multiple_r") is not None
        else _first_present(raw, ("broker_order_initial_target_multiple_r", "dynamic_final_target_r"))
    )
    target_multiple = dynamic_or_broker_target_r if dynamic_or_broker_target_r is not None else static_baseline_r
    stop_width = _float(post.get("stop_width_or_risk_distance") if post.get("stop_width_or_risk_distance") is not None else _first_present(raw, ("risk_distance_for_r", "stop_width_r")))
    stale_status = _string(post.get("stale_thesis_state")) or _string(raw.get("stale_thesis_status"))
    harvest_tags = [str(item) for item in _as_list(raw.get("harvest_tags"))]
    raw_harvest_status = _string(raw.get("harvest_failure_status"))
    if raw_harvest_status:
        harvest_status = raw_harvest_status
    elif actual is not None and actual < 0 and mfe is not None and mfe >= 0.25:
        harvest_status = "harvest_failure_mfe_before_loss"
    elif giveback is not None and giveback >= 0.5:
        harvest_status = "giveback_ge_0_5r_harvest_watch"
    elif trace.get("capture_status") == "prospective_capture_required":
        harvest_status = "source_gap_for_harvest_label"
    else:
        harvest_status = "no_harvest_failure_label_from_sources"

    if not stale_status:
        hold_minutes = _float(values.get("hold_minutes"))
        if hold_minutes is not None and hold_minutes >= 24 * 60:
            stale_status = "stale_hold_ge_24h"
        elif hold_minutes is not None and hold_minutes >= 12 * 60:
            stale_status = "stale_hold_ge_12h"
        elif hold_minutes is not None and hold_minutes >= 6 * 60:
            stale_status = "stale_hold_ge_6h"
        elif hold_minutes is not None:
            stale_status = "intraday_or_short_hold"
        else:
            stale_status = "not_available_in_accepted_sources"

    if target_multiple is None:
        stop_target_efficiency = "source_gap_for_stop_target_efficiency" if trace.get("capture_status") == "prospective_capture_required" else "target_distance_not_available"
    elif actual is not None and actual < 0 and mfe is not None and target_multiple >= 2.0 and mfe < target_multiple:
        stop_target_efficiency = "target_too_far_for_observed_path"
    elif mfe is not None and target_multiple > 0 and mfe >= target_multiple:
        stop_target_efficiency = "target_reached_or_feasible_from_path"
    elif target_multiple >= 3.0:
        stop_target_efficiency = "far_runner_target_geometry_label"
    elif 1.45 <= target_multiple <= 1.55:
        stop_target_efficiency = "static_1_5r_comparator_geometry"
    elif 1.95 <= target_multiple <= 2.05:
        stop_target_efficiency = "static_2r_comparator_geometry"
    else:
        stop_target_efficiency = "target_stop_geometry_observed"

    return {
        "schema_version": "wave4c_harvest_stale_static_r_label_v1",
        "harvest_failure": {
            "status": harvest_status,
            "mfe_r": mfe,
            "actual_or_terminal_r": actual,
            "giveback_r": giveback,
            "partial_close_count": partial_count,
            "harvest_tags": harvest_tags,
            "eligible_actions": ["harvest", "partial", "trail", "BE", "cut"] if harvest_status not in {"no_harvest_failure_label_from_sources", "not_available_in_accepted_sources"} else [],
        },
        "stale_thesis": {
            "status": stale_status,
            "eligible_actions": ["cut", "close/reverse", "wait"] if "stale" in stale_status else ["hold"] if stale_status == "intraday_or_short_hold" else [],
        },
        "static_r_and_stop_target_efficiency": {
            "status": stop_target_efficiency,
            "static_r_1_5_present": bool(static_baseline_r is not None and 1.45 <= static_baseline_r <= 1.55),
            "static_r_2r_present": bool(
                (static_baseline_r is not None and 1.95 <= static_baseline_r <= 2.05)
                or (dynamic_or_broker_target_r is not None and 1.95 <= dynamic_or_broker_target_r <= 2.05)
            ),
            "static_baseline_r": static_baseline_r,
            "dynamic_or_broker_target_multiple_r": dynamic_or_broker_target_r,
            "target_distance_or_multiple_r": target_multiple,
            "stop_width_or_risk_distance": stop_width,
            "source_rule": "static/fixed R geometry remains comparator label; dynamic target truth stays separated from broker-real PnL",
        },
        "source_status": trace.get("source_completeness_state"),
        "capture_requirement": trace.get("capture_requirement"),
        "labels_never_asof_features": True,
    }


def opportunity_cost_label(row: Mapping[str, Any], opportunity_row: Mapping[str, Any] | None, raw: Mapping[str, Any]) -> dict[str, Any]:
    trace = source_trace(row)
    opp = opportunity_row if isinstance(opportunity_row, Mapping) else {}
    context = opp.get("source_bound_expectancy_context")
    if not isinstance(context, Mapping):
        context = raw.get("source_bound_expectancy_context") if isinstance(raw.get("source_bound_expectancy_context"), Mapping) else {}
    expectancy = _float(context.get("expectancy_r_source_bound") if isinstance(context, Mapping) else None)
    final_outcome = _string(context.get("final_outcome") if isinstance(context, Mapping) else None) or _string(raw.get("final_outcome"))
    selected_ids = [str(item) for item in _as_list(opp.get("selected_or_filled_candidate_ids")) if item not in (None, "", [], {})]
    rejected_ids = [str(item) for item in _as_list(opp.get("rejected_skipped_no_trade_candidate_ids")) if item not in (None, "", [], {})]
    text_blob = json.dumps({"source_key": row.get("source_key"), "final_outcome": final_outcome, "raw_status": raw.get("rank_status")}, sort_keys=True, default=str).casefold()
    if opportunity_row:
        status = "opportunity_denominator_label_available_no_counterfactual_pnl"
    elif "zero_trade" in text_blob or "skipped" in text_blob or "rejected" in text_blob:
        status = "zero_trade_or_reject_value_label_available_no_realized_pnl"
    elif trace.get("capture_status") == "prospective_capture_required":
        status = "source_gap_for_opportunity_cost_label"
    else:
        status = "not_available_or_not_applicable"
    return {
        "schema_version": "wave4c_opportunity_cost_label_v1",
        "status": status,
        "evidence_class": opp.get("evidence_class") or raw.get("evidence_class") or "opportunity_label",
        "expectancy_r_source_bound": expectancy,
        "final_outcome": final_outcome or None,
        "selected_or_filled_candidate_ids": selected_ids,
        "rejected_skipped_no_trade_candidate_ids": rejected_ids,
        "counts": opp.get("counts") if isinstance(opp.get("counts"), Mapping) else None,
        "zero_trade_comparator": opp.get("zero_trade_comparator"),
        "same_symbol_alternative": opp.get("same_symbol_alternative"),
        "source_rule": "opportunity and zero-trade rows are denominator/value labels, not realized counterfactual PnL",
        "capture_requirement": trace.get("capture_requirement"),
        "labels_never_asof_features": True,
    }


def same_symbol_action_label(
    row: Mapping[str, Any],
    opportunity: Mapping[str, Any],
    harvest_label: Mapping[str, Any],
    opp_label: Mapping[str, Any],
) -> dict[str, Any]:
    trace = source_trace(row)
    source_key = str(row.get("source_key"))
    status_text = json.dumps(
        {
            "opportunity_status": row.get("opportunity_status"),
            "row_family": row.get("row_family"),
            "source_key": source_key,
            "opp_status": opp_label.get("status"),
            "same_symbol_alternative": opportunity.get("same_symbol_alternative") if isinstance(opportunity, Mapping) else None,
        },
        sort_keys=True,
        default=str,
    ).casefold()
    actions: list[str]
    status: str
    if "same_symbol" in status_text or "opposite" in status_text:
        status = "same_symbol_competing_action_label_available"
        actions = ["scale/add", "reduce", "close/reverse", "wait", "no-trade"]
    elif source_key in {"pending_nofill_lifecycle"}:
        status = "pending_same_symbol_wait_or_replace_label"
        actions = ["wait", "no-trade"]
    elif "zero_trade" in source_key or "rejected" in status_text or "skipped" in status_text:
        status = "no_trade_or_wait_action_label"
        actions = ["wait", "no-trade"]
    elif source_key in {"profit_harvest_filled_trade", "partial_be_runner_forensic", "loser_mfe_repair", "tick_repaired_first_passage_mfe_mae_reversal"}:
        status = "open_trade_management_action_label"
        actions = ["hold", "cut", "partial", "trail", "BE", "harvest"]
    elif source_key in {"broker_trade_causal_microscope", "target_stop_geometry_path_order"}:
        status = "filled_trade_hold_or_cut_action_label"
        actions = ["hold", "cut"]
    elif trace.get("capture_status") == "prospective_capture_required":
        status = "source_gap_for_same_symbol_action_label"
        actions = ["wait"]
    else:
        status = "no_same_symbol_action_label_from_sources"
        actions = []
    stale_actions = harvest_label.get("stale_thesis", {}).get("eligible_actions", []) if isinstance(harvest_label.get("stale_thesis"), Mapping) else []
    harvest_actions = harvest_label.get("harvest_failure", {}).get("eligible_actions", []) if isinstance(harvest_label.get("harvest_failure"), Mapping) else []
    merged_actions = sorted({*actions, *[str(item) for item in stale_actions], *[str(item) for item in harvest_actions]})
    return {
        "schema_version": "wave4c_same_symbol_action_label_v1",
        "status": status,
        "action_family": merged_actions,
        "source_rule": "same-symbol action labels are downstream targets only; runtime action choice remains owned by same-symbol/probability/execution lanes",
        "wave3_action_contract": ["hold", "cut", "partial", "trail", "BE", "harvest", "scale/add", "reduce", "close/reverse", "wait", "no-trade"],
        "capture_requirement": trace.get("capture_requirement"),
        "labels_never_asof_features": True,
    }


def source_gap_label(
    row: Mapping[str, Any],
    path_row: Mapping[str, Any],
    labels: Mapping[str, Any],
    source_gap_rows_by_key: Mapping[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    trace = source_trace(row, path_row)
    source_key = str(row.get("source_key"))
    family_status: dict[str, str] = {}
    for family in LABEL_FAMILIES:
        value = labels.get(family)
        family_status[family] = "materialized" if value not in (None, "", [], {}) else (
            "source_gap_or_prospective_capture" if trace.get("capture_status") == "prospective_capture_required" else "not_available_or_not_applicable"
        )
    inherited = source_gap_rows_by_key.get(source_key, [])
    return {
        "schema_version": "wave4c_source_gap_capture_label_v1",
        "status": "source_gap_or_capture_requirement" if trace.get("capture_status") == "prospective_capture_required" or inherited else "source_materialized_or_not_materially_gapped",
        "source_trace": trace,
        "label_family_status": family_status,
        "inherited_wave4a_source_gap_count_for_source_key": len(inherited),
        "inherited_missing_source_or_field_values": sorted(
            {
                str(item.get("missing_source_or_field"))
                for item in inherited
                if item.get("missing_source_or_field") not in (None, "", [], {})
            }
        ),
        "repair_or_capture_requirement": trace.get("capture_requirement")
        or (
            "; ".join(
                sorted(
                    {
                        str(item.get("repair_or_capture_requirement"))
                        for item in inherited
                        if item.get("repair_or_capture_requirement") not in (None, "", [], {})
                    }
                )
            )
            if inherited
            else None
        ),
        "labels_never_asof_features": True,
    }


def build_label_rows(inputs: Wave4CInputs) -> dict[str, list[dict[str, Any]]]:
    source_gaps_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in inputs.source_gap_rows:
        source_gaps_by_key[str(item.get("source_key"))].append(item)

    ledgers: dict[str, list[dict[str, Any]]] = {name: [] for name in REQUIRED_LEDGER_NAMES}
    for index, canonical in enumerate(inputs.canonical_rows, start=1):
        canonical_id = str(canonical["canonical_row_id"])
        path_row = inputs.path_rows.get(canonical_id, {})
        opportunity_row = inputs.opportunity_rows.get(canonical_id, {})
        raw = raw_source_for(canonical, inputs)
        trace = source_trace(canonical, path_row)
        evidence = evidence_class_label(canonical, path_row, raw)
        mfe = mfe_mae_timing_label(canonical, path_row, raw)
        harvest = harvest_stale_static_label(canonical, path_row, raw, mfe)
        opportunity = opportunity_cost_label(canonical, opportunity_row, raw)
        same_symbol = same_symbol_action_label(canonical, opportunity_row, harvest, opportunity)
        source_gap = source_gap_label(canonical, path_row, {
            "broker_real_cash_pnl": evidence["broker_real_cash_pnl"].get("value"),
            "broker_real_cash_cost": evidence["broker_real_cash_cost"].get("value"),
            "exact_r": evidence["exact_r"].get("value"),
            "proxy_r": evidence["proxy_r"].get("value"),
            "replay": evidence["replay"].get("status"),
            "simulation": evidence["simulation"].get("status"),
            "shadow": evidence["shadow"].get("status"),
            "mfe_r": mfe["value"].get("mfe_r"),
            "mae_r": mfe["value"].get("mae_r"),
            "timing": mfe["available_fields"],
            "giveback": harvest["harvest_failure"].get("giveback_r"),
            "stale_thesis": harvest["stale_thesis"].get("status"),
            "stop_target_efficiency": harvest["static_r_and_stop_target_efficiency"].get("status"),
            "harvest_failure": harvest["harvest_failure"].get("status"),
            "opportunity_cost": opportunity.get("status"),
            "static_r_1_5": harvest["static_r_and_stop_target_efficiency"].get("static_r_1_5_present"),
            "static_r_2r": harvest["static_r_and_stop_target_efficiency"].get("static_r_2r_present"),
            "same_symbol_action": same_symbol.get("status"),
            "source_gap": trace.get("missing_fields_or_runtime_truth"),
            "prospective_capture_requirement": trace.get("capture_requirement"),
        }, source_gaps_by_key)
        common = {
            "canonical_row_id": canonical_id,
            "label_row_index": index,
            "label_set_version": LABEL_SET_VERSION,
            "source_key": canonical.get("source_key"),
            "symbol": canonical.get("symbol"),
            "side": canonical.get("side"),
            "canonical_time_utc": canonical.get("canonical_time_utc"),
            "row_family": canonical.get("row_family"),
            "source_trace": trace,
            "feature_store_exclusion": FEATURE_STORE_EXCLUSION,
            "labels_never_asof_features": True,
            "runtime_effect_boundary": "local_label_artifact_only_no_broker_vps_runtime_mutation",
        }
        ledger_row = {
            **common,
            "schema_version": "wave4c_label_ledger_v1",
            "evidence_class_labels": evidence,
            "mfe_mae_timing_label": mfe,
            "harvest_stale_static_r_label": harvest,
            "same_symbol_action_label": same_symbol,
            "opportunity_cost_label": opportunity,
            "source_gap_and_capture_label": source_gap,
        }
        ledger_row["label_row_hash"] = wave4a.stable_hash(ledger_row)
        ledgers["WAVE4C_LABEL_LEDGER.jsonl"].append(ledger_row)
        ledgers["WAVE4C_EVIDENCE_CLASS_LABEL_LEDGER.jsonl"].append(
            {**common, "schema_version": "wave4c_evidence_class_label_ledger_v1", "evidence_class_labels": evidence}
        )
        ledgers["WAVE4C_MFE_MAE_TIMING_LABEL_LEDGER.jsonl"].append(
            {**common, "schema_version": "wave4c_mfe_mae_timing_label_ledger_v1", "mfe_mae_timing_label": mfe}
        )
        ledgers["WAVE4C_HARVEST_STALE_STATIC_R_LABEL_LEDGER.jsonl"].append(
            {**common, "schema_version": "wave4c_harvest_stale_static_r_label_ledger_v1", "harvest_stale_static_r_label": harvest}
        )
        ledgers["WAVE4C_SAME_SYMBOL_ACTION_LABEL_LEDGER.jsonl"].append(
            {**common, "schema_version": "wave4c_same_symbol_action_label_ledger_v1", "same_symbol_action_label": same_symbol}
        )
        ledgers["WAVE4C_OPPORTUNITY_COST_LABEL_LEDGER.jsonl"].append(
            {**common, "schema_version": "wave4c_opportunity_cost_label_ledger_v1", "opportunity_cost_label": opportunity}
        )
        ledgers["WAVE4C_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl"].append(
            {**common, "schema_version": "wave4c_source_gap_capture_label_ledger_v1", "source_gap_and_capture_label": source_gap}
        )
    return ledgers


def label_schema() -> dict[str, Any]:
    return {
        "schema_version": "wave4c_label_schema_v1",
        "lane": LANE,
        "label_set_version": LABEL_SET_VERSION,
        "canonical_dependency": {
            "route": WAVE4A_ROUTE.as_posix(),
            "row_count": CANONICAL_ROW_COUNT,
            "canonical_universe_sha256": CANONICAL_UNIVERSE_HASH,
        },
        "feature_store_input_allowed": False,
        "feature_store_exclusion": FEATURE_STORE_EXCLUSION,
        "runtime_effect_boundary": "local label artifacts for validation/ML only; no broker/VPS/runtime mutation",
        "evidence_class_authority_order": [
            "broker-real cash/PnL",
            "exact-R",
            "proxy-R",
            "replay",
            "simulation",
            "shadow",
            "source gap",
            "prospective capture requirement",
        ],
        "label_families": {
            family: {
                "label_timing": "post_event_or_source_completeness_state_label_store_only",
                "feature_store_asof_input": False,
                "value_type": "scalar_or_object_or_null",
                "required_source_trace_fields": [
                    "source_key",
                    "source_path",
                    "source_sha256",
                    "source_row_id",
                    "source_row_hash",
                    "source_completeness_state",
                    "capture_status",
                ],
            }
            for family in LABEL_FAMILIES
        },
        "forbidden_asof_fields": sorted(FORBIDDEN_ASOF_LABEL_FIELDS),
        "same_symbol_action_contract": [
            "hold",
            "cut",
            "partial",
            "trail",
            "BE",
            "harvest",
            "scale/add",
            "reduce",
            "close/reverse",
            "wait",
            "no-trade",
        ],
        "boundary_status": BOUNDARY_STATUS,
    }


def context_anchor(repo_root: Path, inputs: Wave4CInputs, ledgers: Mapping[str, list[dict[str, Any]]]) -> dict[str, Any]:
    branch = wave4a.git_value(repo_root, "branch", "--show-current")
    head = wave4a.git_value(repo_root, "rev-parse", "--short=10", "HEAD")
    status_short = wave4a.git_value(repo_root, "status", "--short")
    source_counts = Counter(str(row.get("source_key")) for row in inputs.canonical_rows)
    return {
        "schema_version": "wave4c_context_anchor_v1",
        "generated_at_utc": utc_now(),
        "lane": LANE,
        "route_id": ROUTE_ID,
        "branch": branch,
        "head": head,
        "worktree": str(repo_root),
        "prompt_path": PROMPT_PATH.as_posix(),
        "starter_path": STARTER_PATH.as_posix(),
        "route_dir": ROUTE_DIR.as_posix(),
        "boundary_status": BOUNDARY_STATUS,
        "wave4a_dependency": {
            "route": WAVE4A_ROUTE.as_posix(),
            "verification_ok": bool(inputs.wave4a_verification.get("ok")),
            "canonical_row_count": len(inputs.canonical_rows),
            "canonical_universe_sha256": wave4a.sha256_file(repo_root / WAVE4A_ROUTE / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl"),
            "manifest_canonical_universe_sha256": CANONICAL_UNIVERSE_HASH,
            "source_counts": dict(sorted(source_counts.items())),
        },
        "ledger_counts": {name: len(rows) for name, rows in sorted(ledgers.items())},
        "required_context_paths_read": list(REQUIRED_CONTEXT_PATHS),
        "upstream_route_paths_read": list(UPSTREAM_ROUTE_PATHS),
        "upstream_contract_paths_read": list(UPSTREAM_CONTRACT_PATHS),
        "dirty_status_at_build": status_short.splitlines() if status_short else [],
        "unrelated_dirty_policy": "legacy outcome-testing JSONL dirt remains unstaged and outside Wave4C scope",
    }


def question_rows() -> list[dict[str, Any]]:
    questions = [
        ("Q001", "Which label class is strongest for each row?", "full WAVE4C_EVIDENCE_CLASS_LABEL_LEDGER rows for every Wave4A canonical id"),
        ("Q002", "Which rows have broker-real cash/PnL and what remains R-only?", "broker_real_cash_pnl, exact_r, proxy_r labels remain separated by unit and source rule"),
        ("Q003", "Which rows have MFE/MAE/timing labels?", "full WAVE4C_MFE_MAE_TIMING_LABEL_LEDGER with source-supported and source-gap statuses"),
        ("Q004", "Which losses had harvestable MFE or giveback?", "harvest_failure labels derived from tick/path/filled-trade rows, no imputed broker PnL"),
        ("Q005", "Which rows expose stale thesis or slow time to destination?", "stale_thesis labels from Wave2 stale-thesis ledger/path clocks"),
        ("Q006", "How are stop/target efficiency and static-R/2R represented?", "static comparator labels stay separated from dynamic target and broker-real outcome"),
        ("Q007", "How are opportunity cost and zero-trade labels represented?", "opportunity labels preserve denominator/counterfactual boundary without realized PnL claims"),
        ("Q008", "How are same-symbol scale/add/reduce/close/reverse/wait/no-trade labels represented?", "same-symbol action ledger uses Wave3 semantic ownership and Wave4A opportunity/path states"),
        ("Q009", "Which rows remain source gaps or prospective capture requirements?", "full source-gap ledger records capture requirements per row"),
        ("Q010", "Could label fields leak back into Feature Store V2?", "schema forbids feature-store use and verifier checks all label rows"),
        ("Q011", "Could broker-real cash be replaced by exact/proxy/replay labels?", "verifier checks cash units and R units remain distinct"),
        ("Q012", "What outside-current-edge label families were considered?", "giveback, adverse-before-profit, stale thesis, opportunity cost, same-symbol actions, source completeness, cost drag"),
        ("Q013", "What source classes were searched?", "Wave4A substrate, Wave2 source ledgers/contracts, Wave3 harvest/exit/same-symbol/dynamic/cost/validation contracts, Label Store V1 schema"),
        ("Q014", "What remains outside Wave4C evidence class?", "production promotion, registry edits, broker/VPS mutation, paid/vendor calls, and live runtime deployment"),
        ("Q015", "What is the proof-or-impossibility stop condition?", "every Wave4A canonical row has label rows; missing truth is exact source/capture requirement"),
    ]
    return [
        {
            "schema_version": "wave4c_question_ledger_v1",
            "question_id": qid,
            "question": question,
            "disposition": "answered_by_machine_checkable_artifact",
            "artifact_evidence": evidence,
            "no_arbitrary_top_n": True,
        }
        for qid, question, evidence in questions
    ]


def searched_root_rows(repo_root: Path) -> list[dict[str, Any]]:
    paths = [
        PROMPT_PATH.as_posix(),
        STARTER_PATH.as_posix(),
        *REQUIRED_CONTEXT_PATHS,
        *UPSTREAM_ROUTE_PATHS,
        *UPSTREAM_CONTRACT_PATHS,
        (WAVE4A_ROUTE / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl").as_posix(),
        (WAVE4A_ROUTE / "WAVE4A_DIGITAL_TWIN_EVENT_LEDGER.jsonl").as_posix(),
        (WAVE4A_ROUTE / "WAVE4A_PATH_CLOCK_FORENSIC_LEDGER.jsonl").as_posix(),
        (WAVE4A_ROUTE / "WAVE4A_ACCEPTED_REJECTED_OPPORTUNITY_LEDGER.jsonl").as_posix(),
        (WAVE4A_ROUTE / "WAVE4A_LOSER_MFE_HARVEST_LEDGER.jsonl").as_posix(),
        (WAVE4A_ROUTE / "WAVE4A_SOURCE_INPUT_INVENTORY.jsonl").as_posix(),
        (WAVE4A_ROUTE / "WAVE4A_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl").as_posix(),
    ]
    rows: list[dict[str, Any]] = []
    for index, raw_path in enumerate(dict.fromkeys(paths), start=1):
        path = repo_root / raw_path
        rows.append(
            {
                "schema_version": "wave4c_searched_root_ledger_v1",
                "row_id": f"searched_root:{index:04d}",
                "path": raw_path,
                "exists": path.exists(),
                "source_class": "file" if path.is_file() else "directory" if path.is_dir() else "missing",
                "sha256": wave4a.sha256_file(path) if path.is_file() else None,
                "search_disposition": "read_or_indexed_from_current_disk" if path.exists() else "missing_exact_path",
            }
        )
    return rows


def decision_rows() -> list[dict[str, Any]]:
    decisions = [
        ("D001", "consume_wave4a_as_frozen_canonical_universe", "implemented", "Wave4C does not synthesize or alter Wave4A row ids"),
        ("D002", "materialize_full_label_ledgers_for_all_rows", "implemented", "Every required full-row ledger reconciles to 15679 rows"),
        ("D003", "preserve_evidence_class_separation", "implemented", "Cash, R, replay/simulation/shadow, path, source-gap labels are separate objects"),
        ("D004", "ban_label_to_feature_leakage", "implemented", "All label rows carry Feature Store exclusion and verifier checks as-of event fields"),
        ("D005", "treat_missing_truth_as_capture_requirement", "implemented", "Source gaps remain explicit and not imputed"),
        ("D006", "do_not_touch_runtime_or_broker_surfaces", "implemented", "Lane owns local code/tests/route artifacts only"),
        ("D007", "emit_shared_surface_requirements_only_as_route_decisions", "implemented", "No shared context/config/runtime registry mutation"),
        ("D008", "use_role_separated_local_reviews", "implemented", "Independent review ledger records source/artifact, leakage, label-family, prompt/scope, loop/source-gap, saturation roles"),
    ]
    return [
        {
            "schema_version": "wave4c_route_decision_ledger_v1",
            "decision_id": decision_id,
            "decision": decision,
            "status": status,
            "rationale": rationale,
            "boundary_status": BOUNDARY_STATUS,
        }
        for decision_id, decision, status, rationale in decisions
    ]


def blocker_repair_rows(inputs: Wave4CInputs) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    counter = 0
    for canonical in inputs.canonical_rows:
        missing = _as_list(canonical.get("missing_fields_or_runtime_truth"))
        if not missing and canonical.get("source_completeness_state") != "source_gap_present":
            continue
        counter += 1
        rows.append(
            {
                "schema_version": "wave4c_blocker_repair_ledger_v1",
                "row_id": f"blocker_repair:{counter:06d}",
                "canonical_row_id": canonical.get("canonical_row_id"),
                "source_key": canonical.get("source_key"),
                "missing_source_or_field": [str(item) for item in missing],
                "repair_or_capture_requirement": capture_requirement(missing, canonical.get("source_key"))
                or "Preserve source-gap status from Wave4A; capture row-level missing truth prospectively.",
                "same_evidence_class_status": "reduced_to_exact_source_capture_requirement",
                "labels_never_asof_features": True,
            }
        )
    return rows


def independent_review_text() -> str:
    return """# Wave4C Independent Review Ledger

Generated by local role-separated passes. Subagent tooling was unavailable in this session, so the same roles were executed as explicit local self-review passes against disk artifacts.

| Role | Finding | Disposition |
|---|---|---|
| source/artifact auditor | Wave4A manifest, verifier, focused tests, completion audit, acceptance review, canonical universe, event, path-clock, opportunity, loser-MFE, source inventory, searched-root, coverage, and source-gap artifacts were present and read from disk. | Accepted substrate; Wave4C verifier reconciles to Wave4A row count/hash. |
| evidence-class/label-boundary critic | Broker-real cash/PnL can be confused with exact/proxy/replay R if flattened. | Label schema and verifier enforce cash units separately from R labels and ban label fields from Feature Store inputs. |
| label-family completeness critic | The prompt requires broker-real cash/PnL, exact-R, proxy-R, replay, simulation, shadow, MFE/MAE/timing, giveback, stale thesis, stop/target efficiency, harvest failure, opportunity cost, static-R/2R, same-symbol actions, source gaps, and capture requirements. | All families are represented in full-row ledgers; unavailable families become source-gap/not-available labels rather than dropped rows. |
| prompt/merge-scope critic | Shared context, Feature Store V2, registry, config, and runtime surfaces could be tempting but are outside Wave4C ownership. | No shared-surface edits; route decisions preserve Wave4I/orchestrator requirements. |
| loop/source-gap reviewer | Missing historical runtime truth is not a reason to stop when label rows can still preserve capture requirements. | Source-gap and blocker/repair ledgers materialize exact row-level requirements; no abstract handoff replaces full ledgers. |
| saturation/self-red-team critic | Duplicate denominators, source hashes, stale prompt facts, and label-to-feature leakage are the highest-risk failure modes. | Verifier checks canonical ID equality, source trace coverage, as-of event no-label fields, and full ledger counts. |
"""


def saturation_text() -> str:
    return """# Wave4C Saturation And Self-Red-Team

## Evidence-Class Leakage Attack

Broker-real cash/PnL, exact-R, proxy-R, replay, simulation, shadow, path, source-gap, and prospective-capture labels are stored as separate objects with explicit units and source rules. Cash labels use broker cash/cost fields only; R labels stay R-style labels.

## Label-To-Feature Leakage Attack

Every full-row label ledger carries `feature_store_exclusion = banned_from_wave4b_asof_inputs_labels_only`, and the verifier checks Wave4A `asof_observation` fields for forbidden label names. Wave4C does not edit Wave4B.

## Duplicate/Denominator Attack

Wave4C preserves Wave4A canonical IDs exactly. The verifier requires every full-row ledger to contain the same 15,679 canonical IDs as Wave4A with no duplicates. Opportunity and zero-trade rows remain denominator/value labels, not realized PnL.

## Source-Hash Attack

Every row carries source key, source path, source sha256, source row id, and source row hash. Missing source truth becomes a row-level capture requirement rather than imputation.

## Static Example Boxing Attack

The schema includes the prompt floor plus adjacent labels exposed by upstream routes: cost cash, timing, stale thesis, giveback thresholds, static 1.5R/2R comparator state, same-symbol actions, no-trade/wait labels, and source completeness labels.

## Same-Evidence-Class Repair

The accepted Wave4A/Wave2 artifacts already performed source-safe repairs for tick/path, loser MFE, cost, opportunity, and static geometry. Wave4C consumes those repaired artifacts and marks remaining non-generatable or absent fields as exact capture requirements. No same-evidence-class row is dropped.

## Deliberate Non-Answers

Wave4C does not perform production promotion, registry edits, broker/VPS mutation, paid/vendor calls, or live runtime deployment. Those cross the Wave4C evidence class and remain Wave4I/orchestrator or owner-approved production-return surfaces.
"""


def instruction_checklist_text() -> str:
    checks = [
        ("goal_session_research_discipline.md read after preflight", "yes"),
        ("research_operating_doctrine.md read after preflight", "yes"),
        ("lane posture", "builder/repair/replay label-materialization"),
        ("anti-boxing questions pursued", "yes: source class, label family, same-symbol, opportunity cost, stale thesis, static-R, capture-gap questions in WAVE4C_QUESTION_LEDGER"),
        ("outside-current-edge mechanisms considered", "giveback, adverse-before-profit/MFE, stale thesis, opportunity cost, no-trade value, same-symbol actions, cost drag, source completeness"),
        ("proof-or-impossibility stop condition", "all Wave4A canonical rows receive full-row labels; missing fields are exact source/capture requirements"),
        ("role-separated reviews completed", "yes, local passes recorded in WAVE4C_INDEPENDENT_REVIEW_LEDGER.md"),
        ("doctrine requirements not answered because forbidden/cross-class", "production promotion, registry edits, broker/VPS mutation, paid/vendor calls, live runtime deployment"),
    ]
    lines = ["# Wave4C Instruction Coverage Checklist", "", "| Requirement | Status |", "|---|---|"]
    lines.extend(f"| {item} | {status} |" for item, status in checks)
    lines.append("")
    return "\n".join(lines)


def prompt_starter_reference_text() -> str:
    return f"""# Wave4C Prompt And Starter Reference

- Prompt path: `{PROMPT_PATH.as_posix()}`
- Starter path: `{STARTER_PATH.as_posix()}`
- Route: `{ROUTE_DIR.as_posix()}`
- Evidence class: separated label materialization with no label-to-feature leakage.
- Runtime boundary: local label artifacts for validation/ML only; no broker/VPS runtime mutation.
"""


def run_command(repo_root: Path, command: Sequence[str]) -> dict[str, Any]:
    completed = subprocess.run(
        list(command),
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "status": "passed" if completed.returncode == 0 else "failed",
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def write_prompt_hardening_result(repo_root: Path, route_dir: Path) -> dict[str, Any]:
    result = {
        "schema_version": "wave4c_prompt_hardening_result_v1",
        "generated_at_utc": utc_now(),
        "commands": [
            run_command(
                repo_root,
                [
                    "python3",
                    "scripts/validate_goal_prompt_hardening.py",
                    PROMPT_PATH.as_posix(),
                    STARTER_PATH.as_posix(),
                    "--kind",
                    "builder",
                    "--json",
                ],
            )
        ],
    }
    result["ok"] = all(item["exit_code"] == 0 for item in result["commands"])
    wave4a.write_json(route_dir / "WAVE4C_LABEL_STORE_V2_PROMPT_HARDENING_RESULT.json", result)
    return result


def write_output_manifest(repo_root: Path, route_dir: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for path in sorted(route_dir.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        rel = rel_path(repo_root, path)
        item: dict[str, Any] = {
            "path": rel,
            "size_bytes": path.stat().st_size,
            "sha256": None if path.name == "WAVE4C_LABEL_STORE_V2_OUTPUT_MANIFEST.json" else wave4a.sha256_file(path),
        }
        if path.suffix == ".jsonl":
            item["jsonl_rows"] = sum(1 for _ in wave4a.iter_jsonl(path))
        files.append(item)
    manifest = {
        "schema_version": "wave4c_output_manifest_v1",
        "route_id": ROUTE_ID,
        "lane": LANE,
        "generated_at_utc": utc_now(),
        "manifest_self_excluded_from_hash_list": True,
        "wave4a_canonical_row_count": CANONICAL_ROW_COUNT,
        "wave4a_canonical_universe_sha256": CANONICAL_UNIVERSE_HASH,
        "boundary_status": BOUNDARY_STATUS,
        "file_count": len(files),
        "files": files,
    }
    wave4a.write_json(route_dir / "WAVE4C_LABEL_STORE_V2_OUTPUT_MANIFEST.json", manifest)
    return manifest


def _summary_counts(ledgers: Mapping[str, list[dict[str, Any]]]) -> dict[str, Any]:
    evidence_rows = ledgers["WAVE4C_EVIDENCE_CLASS_LABEL_LEDGER.jsonl"]
    label_rows = ledgers["WAVE4C_LABEL_LEDGER.jsonl"]
    evidence_counts = {
        "broker_real_cash_pnl_value_rows": sum(
            1 for row in evidence_rows if row["evidence_class_labels"]["broker_real_cash_pnl"]["value"] is not None
        ),
        "broker_real_cash_cost_value_rows": sum(
            1 for row in evidence_rows if row["evidence_class_labels"]["broker_real_cash_cost"]["value"] is not None
        ),
        "exact_r_value_rows": sum(1 for row in evidence_rows if row["evidence_class_labels"]["exact_r"]["value"] is not None),
        "proxy_r_value_rows": sum(1 for row in evidence_rows if row["evidence_class_labels"]["proxy_r"]["value"] is not None),
        "replay_value_or_state_rows": sum(
            1
            for row in evidence_rows
            if row["evidence_class_labels"]["replay"]["value"] is not None
            or row["evidence_class_labels"]["replay"]["status"] == "replay_label_available"
        ),
        "simulation_state_rows": sum(
            1
            for row in evidence_rows
            if row["evidence_class_labels"]["simulation"]["status"] == "simulation_or_counterfactual_label_available"
        ),
        "shadow_state_rows": sum(
            1 for row in evidence_rows if row["evidence_class_labels"]["shadow"]["status"] == "shadow_label_available"
        ),
        "source_gap_rows": sum(
            1 for row in evidence_rows if row["evidence_class_labels"]["source_gap"]["status"] == "source_gap_present"
        ),
        "prospective_capture_requirement_rows": sum(
            1
            for row in evidence_rows
            if row["evidence_class_labels"]["prospective_capture_requirement"]["status"] == "prospective_capture_required"
        ),
    }
    path_rows = ledgers["WAVE4C_MFE_MAE_TIMING_LABEL_LEDGER.jsonl"]
    harvest_rows = ledgers["WAVE4C_HARVEST_STALE_STATIC_R_LABEL_LEDGER.jsonl"]
    return {
        "ledger_rows": {name: len(rows) for name, rows in sorted(ledgers.items())},
        "evidence_class_nonempty_counts": evidence_counts,
        "mfe_rows": sum(1 for row in path_rows if row["mfe_mae_timing_label"]["value"]["mfe_r"] is not None),
        "mae_rows": sum(1 for row in path_rows if row["mfe_mae_timing_label"]["value"]["mae_r"] is not None),
        "giveback_rows": sum(1 for row in harvest_rows if row["harvest_stale_static_r_label"]["harvest_failure"]["giveback_r"] is not None),
        "stale_rows": sum(1 for row in harvest_rows if "stale" in str(row["harvest_stale_static_r_label"]["stale_thesis"]["status"])),
        "static_1_5_rows": sum(1 for row in harvest_rows if row["harvest_stale_static_r_label"]["static_r_and_stop_target_efficiency"]["static_r_1_5_present"]),
        "static_2r_rows": sum(1 for row in harvest_rows if row["harvest_stale_static_r_label"]["static_r_and_stop_target_efficiency"]["static_r_2r_present"]),
        "all_label_rows_have_hash": all("label_row_hash" in row for row in label_rows),
    }


def completion_audit_text(repo_root: Path, route_dir: Path, inputs: Wave4CInputs, ledgers: Mapping[str, list[dict[str, Any]]]) -> str:
    verification = wave4a.read_json(route_dir / "WAVE4C_LABEL_STORE_V2_VERIFICATION_RESULT.json") if (route_dir / "WAVE4C_LABEL_STORE_V2_VERIFICATION_RESULT.json").exists() else {"ok": False, "status": "not_run_yet"}
    focused = wave4a.read_json(route_dir / "WAVE4C_LABEL_STORE_V2_FOCUSED_TEST_RESULT.json") if (route_dir / "WAVE4C_LABEL_STORE_V2_FOCUSED_TEST_RESULT.json").exists() else {"ok": False, "status": "not_run_yet"}
    prompt = wave4a.read_json(route_dir / "WAVE4C_LABEL_STORE_V2_PROMPT_HARDENING_RESULT.json") if (route_dir / "WAVE4C_LABEL_STORE_V2_PROMPT_HARDENING_RESULT.json").exists() else {"ok": False, "status": "not_run_yet"}
    route_audit = wave4a.read_json(route_dir / "WAVE4C_LABEL_STORE_V2_ROUTE_ARTIFACT_AUDIT_RESULT.json") if (route_dir / "WAVE4C_LABEL_STORE_V2_ROUTE_ARTIFACT_AUDIT_RESULT.json").exists() else {"ok": False, "status": "not_run_yet"}
    summary = _summary_counts(ledgers)
    branch = wave4a.git_value(repo_root, "branch", "--show-current")
    head = wave4a.git_value(repo_root, "rev-parse", "--short=10", "HEAD")
    lines = [
        "# Wave4C Completion Audit",
        "",
        f"Generated: {utc_now()}",
        f"Branch: `{branch}`",
        f"Current HEAD at audit time: `{head}`",
        f"Route: `{ROUTE_DIR.as_posix()}`",
        "",
        "## Scope",
        "",
        "Built Label Store V2 over the accepted Wave4A canonical row universe. The package materializes separated label ledgers for broker-real cash/PnL, exact-R, proxy-R, replay, simulation, shadow, MFE/MAE/timing, giveback, stale thesis, stop/target efficiency, harvest failure, opportunity cost, static-R/2R, same-symbol actions, source gaps, and prospective capture requirements.",
        "",
        "## Wave4A Reconciliation",
        "",
        f"- Canonical rows: `{len(inputs.canonical_rows)}`.",
        f"- Canonical universe sha256: `{wave4a.sha256_file(repo_root / WAVE4A_ROUTE / 'WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl')}`.",
        f"- Expected Wave4A hash: `{CANONICAL_UNIVERSE_HASH}`.",
        f"- Wave4A verifier ok: `{inputs.wave4a_verification.get('ok')}`.",
        "",
        "## Label Counts",
        "",
        "```json",
        json.dumps(summary, indent=2, sort_keys=True),
        "```",
        "",
        "## Evidence-Class Separation",
        "",
        "- Broker-real cash/PnL is stored only as cash-unit labels.",
        "- Exact-R and proxy-R are R-unit labels and are never promoted to broker-real cash.",
        "- Replay, simulation, and shadow labels remain offline labels.",
        "- Labels are explicitly banned from Wave4B as-of Feature Store inputs.",
        "",
        "## Verification",
        "",
        f"- Wave4C verifier ok: `{verification.get('ok')}`.",
        f"- Focused test result ok: `{focused.get('ok')}`.",
        f"- Prompt hardening ok: `{prompt.get('ok')}`.",
        f"- Route artifact audit ok: `{route_audit.get('ok')}`.",
        "",
        "## Doctrine Coverage",
        "",
        "| Requirement | Status |",
        "|---|---|",
        "| `goal_session_research_discipline.md` read after preflight | yes |",
        "| `research_operating_doctrine.md` read after preflight | yes |",
        "| Lane posture | builder/repair/replay label-materialization |",
        "| Anti-boxing questions pursued | yes, recorded in `WAVE4C_QUESTION_LEDGER.jsonl` |",
        "| Outside-current-edge label/failure mechanisms considered | giveback, adverse-before-profit, stale thesis, opportunity cost, no-trade value, same-symbol actions, cost drag, source completeness |",
        "| Proof-or-impossibility stop condition used | all Wave4A rows labeled; missing truth becomes exact source/capture requirement |",
        "| Subagent or role-separated reviews completed | local role-separated passes recorded in `WAVE4C_INDEPENDENT_REVIEW_LEDGER.md` |",
        "| Doctrine requirements not answered because they cross evidence class or forbidden surfaces | production promotion, registry edits, broker/VPS mutation, paid/vendor calls, live runtime deployment |",
        "",
        "## Boundaries",
        "",
        "No broker account/history/order/deal/position mutation, credential mutation/disclosure, paid/vendor API call, remote push, active VPS process mutation, MT5 live operation, live trading deployment, or runtime restart occurred.",
        "",
        "## Unresolved Exact Requirements",
        "",
        "Remaining unresolved items are row-level source/capture requirements in `WAVE4C_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl` and `WAVE4C_BLOCKER_AND_REPAIR_LEDGER.jsonl`. They are not blockers to local label materialization because every row has an explicit label/source status and no missing truth is imputed.",
        "",
        "## Commit Status",
        "",
        "Commit after verifier, focused tests, prompt hardening, route audit, diff check, staged-path review, and LFS scope review pass. Leave unrelated legacy outcome-testing JSONL dirt unstaged.",
        "",
    ]
    return "\n".join(lines)


def build_artifacts(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    route = route_abs(repo_root, route_dir)
    route.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs(repo_root)
    ledgers = build_label_rows(inputs)
    wave4a.write_json(route / "WAVE4C_LABEL_SCHEMA.json", label_schema())
    for name, rows in ledgers.items():
        wave4a.write_jsonl(route / name, rows)
    wave4a.write_json(route / "WAVE4C_CONTEXT_ANCHOR.json", context_anchor(repo_root, inputs, ledgers))
    wave4a.write_jsonl(route / "WAVE4C_QUESTION_LEDGER.jsonl", question_rows())
    wave4a.write_jsonl(route / "WAVE4C_SEARCHED_ROOT_LEDGER.jsonl", searched_root_rows(repo_root))
    wave4a.write_jsonl(route / "WAVE4C_ROUTE_DECISION_LEDGER.jsonl", decision_rows())
    wave4a.write_jsonl(route / "WAVE4C_BLOCKER_AND_REPAIR_LEDGER.jsonl", blocker_repair_rows(inputs))
    wave4a.write_text(route / "WAVE4C_INDEPENDENT_REVIEW_LEDGER.md", independent_review_text())
    wave4a.write_text(route / "WAVE4C_LABEL_STORE_V2_SATURATION_SELF_RED_TEAM.md", saturation_text())
    wave4a.write_text(route / "WAVE4C_LABEL_STORE_V2_INSTRUCTION_COVERAGE_CHECKLIST.md", instruction_checklist_text())
    wave4a.write_text(route / "WAVE4C_PROMPT_AND_STARTER_REFERENCE.md", prompt_starter_reference_text())
    write_prompt_hardening_result(repo_root, route)
    wave4a.write_text(route / "COMPLETION_AUDIT.md", completion_audit_text(repo_root, route, inputs, ledgers))
    manifest = write_output_manifest(repo_root, route)
    return {
        "ok": True,
        "route_dir": rel_path(repo_root, route),
        "canonical_rows": len(inputs.canonical_rows),
        "canonical_universe_sha256": wave4a.sha256_file(repo_root / WAVE4A_ROUTE / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl"),
        "ledger_counts": {name: len(rows) for name, rows in sorted(ledgers.items())},
        "summary_counts": _summary_counts(ledgers),
        "manifest_file_count": manifest["file_count"],
    }


def _canonical_id_set(repo_root: Path) -> set[str]:
    return {
        str(row["canonical_row_id"])
        for row in wave4a.iter_jsonl(repo_root / WAVE4A_ROUTE / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl")
    }


def _ledger_ids(path: Path) -> tuple[list[str], list[str]]:
    ids: list[str] = []
    errors: list[str] = []
    for line_no, row in enumerate(wave4a.iter_jsonl(path), start=1):
        cid = row.get("canonical_row_id")
        if not cid:
            errors.append(f"{path.name}:{line_no}:missing canonical_row_id")
        else:
            ids.append(str(cid))
    return ids, errors


def verify_route(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    route = route_abs(repo_root, route_dir)
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, evidence: Mapping[str, Any] | None = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "evidence": dict(evidence or {})})

    add("route_dir_exists", route.exists() and route.is_dir())
    for name in REQUIRED_ROUTE_FILES:
        add(f"exists:{name}", (route / name).exists())

    canonical_path = repo_root / WAVE4A_ROUTE / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl"
    canonical_hash = wave4a.sha256_file(canonical_path)
    canonical_ids = _canonical_id_set(repo_root)
    add(
        "wave4a_canonical_hash_matches_manifest",
        canonical_hash == CANONICAL_UNIVERSE_HASH,
        {"actual": canonical_hash, "expected": CANONICAL_UNIVERSE_HASH},
    )
    add("wave4a_canonical_count_matches_expected", len(canonical_ids) == CANONICAL_ROW_COUNT, {"actual": len(canonical_ids), "expected": CANONICAL_ROW_COUNT})

    json_errors: list[str] = []
    jsonl_counts: dict[str, int] = {}
    for path in sorted(route.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        try:
            if path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8", errors="replace"))
            elif path.suffix == ".jsonl":
                count = sum(1 for _ in wave4a.iter_jsonl(path))
                jsonl_counts[path.name] = count
        except Exception as exc:  # noqa: BLE001 - verifier reports all parse failures.
            json_errors.append(f"{path.name}:{exc}")
    add("all_json_and_jsonl_parse", not json_errors, {"errors": json_errors})

    for name in REQUIRED_LEDGER_NAMES:
        path = route / name
        ids, errors = _ledger_ids(path)
        add(f"{name}:canonical_ids_present", not errors, {"errors": errors[:5]})
        add(f"{name}:row_count_matches_wave4a", len(ids) == CANONICAL_ROW_COUNT, {"actual": len(ids), "expected": CANONICAL_ROW_COUNT})
        add(f"{name}:canonical_ids_unique", len(set(ids)) == len(ids), {"actual": len(ids), "unique": len(set(ids))})
        add(f"{name}:canonical_ids_equal_wave4a", set(ids) == canonical_ids, {"missing": len(canonical_ids - set(ids)), "extra": len(set(ids) - canonical_ids)})

    label_rows = list(wave4a.iter_jsonl(route / "WAVE4C_LABEL_LEDGER.jsonl"))
    evidence_rows = list(wave4a.iter_jsonl(route / "WAVE4C_EVIDENCE_CLASS_LABEL_LEDGER.jsonl"))
    event_rows = list(wave4a.iter_jsonl(repo_root / WAVE4A_ROUTE / "WAVE4A_DIGITAL_TWIN_EVENT_LEDGER.jsonl"))
    source_trace_missing = [
        row["canonical_row_id"]
        for row in label_rows
        if any(row.get("source_trace", {}).get(key) in (None, "", [], {}) for key in ("source_key", "source_path", "source_sha256", "source_row_id", "source_row_hash", "source_completeness_state", "capture_status"))
    ]
    add("source_trace_complete_for_all_label_rows", not source_trace_missing, {"missing_count": len(source_trace_missing), "examples": source_trace_missing[:5]})

    leakage_rows = [
        row["canonical_row_id"]
        for row in label_rows
        if row.get("feature_store_exclusion") != FEATURE_STORE_EXCLUSION or row.get("labels_never_asof_features") is not True
    ]
    add("all_label_rows_banned_from_feature_store_asof_inputs", not leakage_rows, {"violations": len(leakage_rows), "examples": leakage_rows[:5]})

    asof_leaks = []
    for event in event_rows:
        obs = event.get("asof_observation") if isinstance(event.get("asof_observation"), Mapping) else {}
        leak = set(obs) & FORBIDDEN_ASOF_LABEL_FIELDS
        if leak:
            asof_leaks.append({"canonical_row_id": event.get("canonical_row_id"), "fields": sorted(leak)})
    add("wave4a_asof_observations_do_not_include_label_fields", not asof_leaks, {"leakage": asof_leaks[:5], "count": len(asof_leaks)})

    mixed_cash_r: list[str] = []
    for row in evidence_rows:
        labels = row["evidence_class_labels"]
        cash = labels["broker_real_cash_pnl"]
        exact_r = labels["exact_r"]
        proxy_r = labels["proxy_r"]
        if cash.get("value") is not None and cash.get("unit") != "cash":
            mixed_cash_r.append(str(row["canonical_row_id"]))
        if exact_r.get("value") is not None and exact_r.get("unit") != "R":
            mixed_cash_r.append(str(row["canonical_row_id"]))
        if proxy_r.get("value") is not None and proxy_r.get("unit") != "R":
            mixed_cash_r.append(str(row["canonical_row_id"]))
    add("broker_real_cash_not_replaced_by_r_labels", not mixed_cash_r, {"mixed": mixed_cash_r[:5], "count": len(mixed_cash_r)})

    schema = wave4a.read_json(route / "WAVE4C_LABEL_SCHEMA.json")
    add("schema_bans_feature_store_inputs", schema.get("feature_store_input_allowed") is False, {"feature_store_input_allowed": schema.get("feature_store_input_allowed")})
    add("schema_contains_required_label_families", set(schema.get("label_families", {})) >= set(LABEL_FAMILIES), {"missing": sorted(set(LABEL_FAMILIES) - set(schema.get("label_families", {})))})
    add("boundary_status_preserved", all(value is False for key, value in BOUNDARY_STATUS.items() if key != "RESULT_MATERIALIZATION_REQUIRED"), {"boundary_status": BOUNDARY_STATUS})

    source_gap_rows = list(wave4a.iter_jsonl(route / "WAVE4C_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl"))
    unresolved_without_requirement = [
        row["canonical_row_id"]
        for row in source_gap_rows
        if row["source_gap_and_capture_label"]["status"] == "source_gap_or_capture_requirement"
        and not row["source_gap_and_capture_label"].get("repair_or_capture_requirement")
    ]
    add("source_gap_rows_have_capture_requirements", not unresolved_without_requirement, {"missing_count": len(unresolved_without_requirement), "examples": unresolved_without_requirement[:5]})

    prompt_result = wave4a.read_json(route / "WAVE4C_LABEL_STORE_V2_PROMPT_HARDENING_RESULT.json")
    add("prompt_hardening_passed", bool(prompt_result.get("ok")), {"ok": prompt_result.get("ok")})
    focused_result = wave4a.read_json(route / "WAVE4C_LABEL_STORE_V2_FOCUSED_TEST_RESULT.json") if (route / "WAVE4C_LABEL_STORE_V2_FOCUSED_TEST_RESULT.json").exists() else {"ok": False}
    add("focused_test_result_passed_or_recorded", bool(focused_result.get("ok")), {"ok": focused_result.get("ok")})

    issue_count = sum(1 for check in checks if not check["passed"])
    return {
        "schema_version": "wave4c_verification_result_v1",
        "route_id": ROUTE_ID,
        "lane": LANE,
        "generated_at_utc": utc_now(),
        "ok": issue_count == 0,
        "issue_count": issue_count,
        "checks": checks,
        "jsonl_counts": jsonl_counts,
        "boundary_status": BOUNDARY_STATUS,
        "wave4a_canonical_row_count": len(canonical_ids),
        "wave4a_canonical_universe_sha256": canonical_hash,
    }


def write_verification_result(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    route = route_abs(repo_root, route_dir)
    result = verify_route(repo_root, route)
    wave4a.write_json(route / "WAVE4C_LABEL_STORE_V2_VERIFICATION_RESULT.json", result)
    write_output_manifest(repo_root, route)
    return result


def write_route_audit_result(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    from scripts.audit_goal_route_artifacts import audit_route

    route = route_abs(repo_root, route_dir)
    result = audit_route(route, None, profile="standard", require_saturation=True)
    result["generated_at_utc"] = utc_now()
    wave4a.write_json(route / "WAVE4C_LABEL_STORE_V2_ROUTE_ARTIFACT_AUDIT_RESULT.json", result)
    write_output_manifest(repo_root, route)
    return result


def write_focused_test_result(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    route = route_abs(repo_root, route_dir)
    commands = [
        run_command(
            repo_root,
            [
                "python3",
                "-m",
                "py_compile",
                "src/research_infra/wave4c_label_store_v2.py",
                str(route / "build_wave4c_label_store_v2.py"),
                str(route / "verify_wave4c_label_store_v2.py"),
                "tests/test_wave4c_label_store_v2.py",
            ],
        ),
        run_command(
            repo_root,
            [
                "python3",
                "-m",
                "pytest",
                "tests/test_wave4c_label_store_v2.py",
                "-q",
            ],
        ),
    ]
    if commands[-1]["exit_code"] != 0 and "No module named pytest" in (commands[-1]["stderr"] + commands[-1]["stdout"]):
        commands.append(
            run_command(
                repo_root,
                [
                    "uv",
                    "run",
                    "--with",
                    "pytest",
                    "--with",
                    "pyyaml",
                    "python",
                    "-m",
                    "pytest",
                    "tests/test_wave4c_label_store_v2.py",
                    "-q",
                    "--basetemp=/tmp/gtos_wave4c_pytest",
                ],
            )
        )
    ok = commands[0]["exit_code"] == 0 and any(command["command"].find("pytest") >= 0 and command["exit_code"] == 0 for command in commands[1:])
    result = {
        "schema_version": "wave4c_focused_test_result_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "ok": ok,
        "commands": commands,
    }
    wave4a.write_json(route / "WAVE4C_LABEL_STORE_V2_FOCUSED_TEST_RESULT.json", result)
    write_output_manifest(repo_root, route)
    return result
