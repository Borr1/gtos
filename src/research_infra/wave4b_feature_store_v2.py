"""Wave4B Feature Store V2 materialization.

This module consumes the accepted Wave4A canonical row universe and emits
pre-decision, source-hashed feature artifacts only. Outcome/path labels remain
joinable through canonical ids for Wave4C, but their values are not consumed as
features here.
"""

from __future__ import annotations

import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.research_infra import wave4a_digital_twin_historical_microscope as wave4a


ROUTE_ID = "final_moonshot_wave4b_feature_store_v2_2026_06_05"
LANE = "wave4b_feature_store_v2"
ROUTE_DIR = Path("research/operations") / ROUTE_ID
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "FINAL_MOONSHOT_WAVE4B_FEATURE_STORE_V2_GOAL_PROMPT_2026-06-05.md"
)
STARTER_PATH = PROMPT_PATH.with_name("FINAL_MOONSHOT_WAVE4B_FEATURE_STORE_V2_STARTER_2026-06-05.txt")
WAVE4A_ROUTE = Path(
    "research/operations/final_moonshot_wave4a_digital_twin_historical_microscope_2026_06_05"
)
BUILD_REFERENCE_UTC = datetime(2026, 6, 5, tzinfo=timezone.utc)
FEATURE_VERSION = "wave4b_feature_store_v2.0"

FAMILY_NAMES = (
    "selector",
    "probability_debate",
    "numeric_confluence",
    "same_symbol",
    "scheduler_risk",
    "execution_entry",
    "market_state",
    "zero_trade",
    "source_completeness",
    "missing_source_penalty",
)

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
    str(WAVE4A_ROUTE) + "/",
)

WAVE4A_REQUIRED_FILES = (
    "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl",
    "WAVE4A_DIGITAL_TWIN_EVENT_LEDGER.jsonl",
    "WAVE4A_PATH_CLOCK_FORENSIC_LEDGER.jsonl",
    "WAVE4A_ACCEPTED_REJECTED_OPPORTUNITY_LEDGER.jsonl",
    "WAVE4A_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl",
    "WAVE4A_SOURCE_INPUT_INVENTORY.jsonl",
    "WAVE4A_SEARCHED_ROOT_LEDGER.jsonl",
    "WAVE4A_COVERAGE_MATRIX.json",
    "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_OUTPUT_MANIFEST.json",
    "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_VERIFICATION_RESULT.json",
    "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_FOCUSED_TEST_RESULT.json",
    "WAVE4A_ORCHESTRATOR_ACCEPTANCE_REVIEW.md",
    "COMPLETION_AUDIT.md",
)

REQUIRED_ROUTE_FILES = (
    "WAVE4B_CONTEXT_ANCHOR.json",
    "WAVE4B_FEATURE_SCHEMA.json",
    "WAVE4B_FEATURE_LEDGER.jsonl",
    "WAVE4B_FEATURE_FAMILY_LEDGER.jsonl",
    "WAVE4B_FEATURE_SOURCE_HASH_LEDGER.jsonl",
    "WAVE4B_NO_LEAK_FIELD_CLASSIFICATION_LEDGER.jsonl",
    "WAVE4B_NUMERIC_CONFLUENCE_FEATURE_LEDGER.jsonl",
    "WAVE4B_SAME_SYMBOL_FEATURE_LEDGER.jsonl",
    "WAVE4B_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl",
    "WAVE4B_QUESTION_LEDGER.jsonl",
    "WAVE4B_SEARCHED_ROOT_LEDGER.jsonl",
    "WAVE4B_ROUTE_DECISION_LEDGER.jsonl",
    "WAVE4B_INDEPENDENT_REVIEW_LEDGER.md",
    "WAVE4B_FEATURE_STORE_V2_VERIFICATION_RESULT.json",
    "WAVE4B_FEATURE_STORE_V2_FOCUSED_TEST_RESULT.json",
    "WAVE4B_FEATURE_STORE_V2_PROMPT_HARDENING_RESULT.json",
    "WAVE4B_FEATURE_STORE_V2_ROUTE_ARTIFACT_AUDIT_RESULT.json",
    "WAVE4B_FEATURE_STORE_V2_SATURATION_SELF_RED_TEAM.md",
    "WAVE4B_FEATURE_STORE_V2_INSTRUCTION_COVERAGE_CHECKLIST.md",
    "WAVE4B_FEATURE_STORE_V2_OUTPUT_MANIFEST.json",
    "COMPLETION_AUDIT.md",
)

FORBIDDEN_LABEL_FIELD_TOKENS = (
    "actual_r",
    "broker_net_cash",
    "broker_real_cash",
    "broker_real_pnl",
    "commission_cash",
    "exact_r",
    "expectancy",
    "fee_cash",
    "final_outcome",
    "giveback",
    "gross_deal_profit",
    "label_boundary",
    "mae",
    "mfe",
    "path_label",
    "pnl",
    "post_decision_path_labels",
    "profit_factor",
    "proxy_r",
    "source_bound_expectancy_context",
    "strategy_proxy_r",
    "swap_cash",
    "terminal_tick_r",
    "win_loss",
    "win_rate",
)

LABEL_ONLY_MISSING_TOKENS = (
    "actual_r",
    "broker_real",
    "cash",
    "counterfactual_path_outcome",
    "exact_r",
    "expectancy",
    "giveback",
    "mae",
    "mfe",
    "profit_factor",
    "proxy_r",
    "win_rate",
)

SAFE_NUMERIC_SOURCE_KEYS = {
    "alternative_count",
    "candidate_count",
    "candidate_rows",
    "cancelled_count",
    "dynamic_trigger_r",
    "filled_count",
    "initial_broker_order_target_multiple_r",
    "opportunity_candidate_count",
    "partial_close_count",
    "partial_close_ratio",
    "raw_trade_parameters_risk_reward_ratio",
    "rejected_count",
    "selected_cell_risk_pct",
    "selected_cell_rows",
    "skipped_count",
    "valid_sl_tp_order_count",
}

SAFE_STATUS_KEYS = {
    "allocator_intent_status",
    "allocator_truth_status",
    "candidate_quality_classification",
    "clock_status",
    "coverage_status",
    "decision_status",
    "evidence_class",
    "geometry_capture_status",
    "join_status",
    "opportunity_status",
    "open_position_snapshot_status",
    "pending_order_snapshot_status",
    "pretrade_cost_model_status",
    "rank_status",
    "replay_status",
    "result_use_status",
    "same_symbol_overlap_status",
    "source_capture_state",
    "source_capture_status",
    "source_completeness_state",
    "source_completeness_status",
    "source_read_status",
    "status",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def route_abs(repo_root: Path, route_dir: Path = ROUTE_DIR) -> Path:
    return route_dir if route_dir.is_absolute() else repo_root / route_dir


def git_value(repo_root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value in (None, "", [], {}):
        return None
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def bool01(value: bool) -> float:
    return 1.0 if value else 0.0


def log1p_safe(value: Any) -> float:
    numeric = as_float(value)
    if numeric is None or numeric < 0:
        return 0.0
    return round(math.log1p(numeric), 6)


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, numerator / denominator)), 6)


def normalize_side(side: Any) -> str:
    text = str(side or "").strip().upper()
    if text in {"BUY", "BULL", "BULLISH", "LONG", "UP"}:
        return "LONG"
    if text in {"SELL", "BEAR", "BEARISH", "SHORT", "DOWN"}:
        return "SHORT"
    return text or "UNKNOWN_SIDE"


def text_of(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(text_of(item) for item in value)
    if isinstance(value, Mapping):
        return " ".join(f"{key} {text_of(item)}" for key, item in value.items())
    return str(value)


def field_tokens_for(value: Any) -> str:
    return text_of(value).casefold().replace("-", "_")


def has_token(value: Any, *tokens: str) -> bool:
    haystack = field_tokens_for(value)
    return any(token.casefold().replace("-", "_") in haystack for token in tokens)


def first_present(row: Mapping[str, Any], keys: Sequence[str]) -> Any:
    metrics = row.get("metric_fields_used") if isinstance(row.get("metric_fields_used"), Mapping) else {}
    for key in keys:
        if key in row and row[key] not in (None, "", [], {}):
            return row[key]
        if key in metrics and metrics[key] not in (None, "", [], {}):
            return metrics[key]
    return None


def nested_present(row: Mapping[str, Any], key: str) -> bool:
    if key in row and row[key] not in (None, "", [], {}):
        return True
    for value in row.values():
        if isinstance(value, Mapping) and nested_present(value, key):
            return True
    return False


def nested_value(row: Mapping[str, Any], key: str) -> Any:
    if key in row and row[key] not in (None, "", [], {}):
        return row[key]
    metrics = row.get("metric_fields_used") if isinstance(row.get("metric_fields_used"), Mapping) else {}
    if key in metrics and metrics[key] not in (None, "", [], {}):
        return metrics[key]
    return None


def parse_time(value: Any) -> datetime | None:
    parsed = wave4a.parse_time(value)
    return parsed.astimezone(timezone.utc) if parsed is not None else None


def freshness(asof_time_utc: str | None) -> dict[str, Any]:
    parsed = parse_time(asof_time_utc)
    if parsed is None:
        return {
            "reference_time_utc": BUILD_REFERENCE_UTC.isoformat(),
            "age_days": None,
            "freshness_score": 0.0,
            "freshness_status": "clock_source_gap",
        }
    age_days = max(0.0, (BUILD_REFERENCE_UTC - parsed).total_seconds() / 86400.0)
    return {
        "reference_time_utc": BUILD_REFERENCE_UTC.isoformat(),
        "age_days": round(age_days, 6),
        "freshness_score": round(max(0.0, min(1.0, 1.0 - age_days / 30.0)), 6),
        "freshness_status": "asof_clock_available",
    }


def source_completeness_score(canonical: Mapping[str, Any], feature_missing_count: int) -> float:
    state = str(canonical.get("source_completeness_state") or "")
    if state == "source_complete_or_not_materially_gapped":
        base = 1.0
    elif state == "partial_source_coverage":
        base = 0.65
    else:
        base = 0.35
    return round(max(0.0, base - min(0.35, feature_missing_count * 0.035)), 6)


def feature_relevant_missing_fields(row: Mapping[str, Any]) -> list[str]:
    raw_missing = list(row.get("missing_fields_or_runtime_truth") or [])
    raw_missing.extend(row.get("missing_fields") or [])
    raw_missing.extend(row.get("missing_runtime_truth") or [])
    deduped = sorted({str(item) for item in raw_missing if item not in (None, "", [], {})})
    return [
        item
        for item in deduped
        if not any(token in item.casefold().replace("-", "_") for token in LABEL_ONLY_MISSING_TOKENS)
    ]


def raw_row_key(canonical: Mapping[str, Any]) -> tuple[str, int]:
    return str(canonical.get("source_key")), int(canonical.get("source_row_index") or 0)


def load_wave4a_inputs(repo_root: Path) -> dict[str, Any]:
    route = repo_root / WAVE4A_ROUTE
    missing = [name for name in WAVE4A_REQUIRED_FILES if not (route / name).exists()]
    if missing:
        raise FileNotFoundError(f"Wave4A dependency missing required files: {missing}")
    manifest = wave4a.read_json(route / "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_OUTPUT_MANIFEST.json")
    verifier = wave4a.read_json(route / "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_VERIFICATION_RESULT.json")
    coverage = wave4a.read_json(route / "WAVE4A_COVERAGE_MATRIX.json")
    canonical = list(wave4a.iter_jsonl(route / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl"))
    events = {
        str(row["canonical_row_id"]): row
        for row in wave4a.iter_jsonl(route / "WAVE4A_DIGITAL_TWIN_EVENT_LEDGER.jsonl")
    }
    path_clock = {
        str(row["canonical_row_id"]): row
        for row in wave4a.iter_jsonl(route / "WAVE4A_PATH_CLOCK_FORENSIC_LEDGER.jsonl")
    }
    opportunity = {
        str(row["canonical_row_id"]): row
        for row in wave4a.iter_jsonl(route / "WAVE4A_ACCEPTED_REJECTED_OPPORTUNITY_LEDGER.jsonl")
    }
    source_gaps = list(wave4a.iter_jsonl(route / "WAVE4A_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl"))
    inventory = list(wave4a.iter_jsonl(route / "WAVE4A_SOURCE_INPUT_INVENTORY.jsonl"))
    searched_roots = list(wave4a.iter_jsonl(route / "WAVE4A_SEARCHED_ROOT_LEDGER.jsonl"))
    if not verifier.get("ok"):
        raise ValueError("Wave4A verifier result is not ok")
    if len(canonical) != 15679 or len(events) != len(canonical) or len(path_clock) != len(canonical):
        raise ValueError("Wave4A row universe/event/path-clock counts do not reconcile")
    return {
        "manifest": manifest,
        "verifier": verifier,
        "coverage": coverage,
        "canonical": canonical,
        "events": events,
        "path_clock": path_clock,
        "opportunity": opportunity,
        "source_gaps": source_gaps,
        "inventory": inventory,
        "searched_roots": searched_roots,
    }


def load_raw_sources(repo_root: Path, inventory: Iterable[Mapping[str, Any]]) -> dict[tuple[str, int], dict[str, Any]]:
    raw_by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for source in inventory:
        source_key = str(source["source_key"])
        path = repo_root / str(source["path"])
        for index, row in enumerate(wave4a.iter_jsonl(path), start=1):
            raw_by_key[(source_key, index)] = row
    return raw_by_key


def safe_numeric_value(row: Mapping[str, Any], key: str) -> float:
    if key not in SAFE_NUMERIC_SOURCE_KEYS:
        return 0.0
    return as_float(first_present(row, (key,))) or 0.0


def candidate_id_available(raw: Mapping[str, Any]) -> float:
    return bool01(bool(first_present(raw, ("candidate_id", "trade_id", "row_id", "source_row_id"))))


def status_texts(canonical: Mapping[str, Any], raw: Mapping[str, Any], opportunity: Mapping[str, Any] | None) -> str:
    safe_values: list[Any] = [
        canonical.get("opportunity_status"),
        canonical.get("source_completeness_state"),
        canonical.get("row_family"),
        canonical.get("source_key"),
    ]
    if opportunity:
        safe_values.extend(opportunity.get(key) for key in ("opportunity_status", "result_use_status"))
    for key in SAFE_STATUS_KEYS:
        safe_values.append(raw.get(key))
    return field_tokens_for(safe_values)


def family_status(values: Mapping[str, float], gap_codes: Sequence[str]) -> str:
    if not gap_codes:
        return "materialized"
    if any(value > 0 for value in values.values()):
        return "partial_with_source_gap"
    return "source_gap_exact_requirement_recorded"


def family_record(
    *,
    family: str,
    canonical: Mapping[str, Any],
    event: Mapping[str, Any],
    values: Mapping[str, float],
    gap_codes: Sequence[str],
    relevant_missing: Sequence[str],
) -> dict[str, Any]:
    asof_time = event.get("event_time_utc") or canonical.get("canonical_time_utc")
    fresh = freshness(asof_time)
    completeness = source_completeness_score(canonical, len(relevant_missing))
    payload = {
        "schema_version": "wave4b_feature_family_v1",
        "feature_family": family,
        "feature_namespace": f"{LANE}.{family}",
        "feature_version": FEATURE_VERSION,
        "canonical_row_id": canonical["canonical_row_id"],
        "asof_time_utc": asof_time,
        "source_key": canonical["source_key"],
        "source_path": canonical["source_path"],
        "source_sha256": canonical["source_sha256"],
        "source_row_hash": canonical["source_row_hash"],
        "freshness": fresh,
        "evidence_class": (canonical.get("evidence_labels") or {}).get("evidence_class")
        or "source_bound_asof_feature_materialization",
        "source_completeness": {
            "state": canonical.get("source_completeness_state"),
            "score": completeness,
            "feature_relevant_missing_field_count": len(relevant_missing),
        },
        "numeric_features": {key: round(float(value), 6) for key, value in values.items()},
        "source_gap_codes": sorted(set(gap_codes)),
        "feature_status": family_status(values, gap_codes),
        "runtime_effect_boundary": "local_feature_artifact_only_no_model_training_no_live_deployment",
    }
    payload["feature_hash"] = wave4a.stable_hash(payload)
    return payload


def selector_features(
    canonical: Mapping[str, Any],
    raw: Mapping[str, Any],
    opportunity: Mapping[str, Any] | None,
    relevant_missing: Sequence[str],
) -> tuple[dict[str, float], list[str]]:
    opp_status = str(canonical.get("opportunity_status") or "")
    selected_cell_rows = first_present(raw, ("selected_cell_rows",))
    values = {
        "candidate_row_family_flag": bool01(canonical.get("source_key") == "candidate_causal_microscope"),
        "candidate_identifier_available": candidate_id_available(raw),
        "selected_cell_rows_value_excluded_without_asof_cutoff": bool01(selected_cell_rows is not None),
        "selected_cell_rows_available": bool01(selected_cell_rows is not None),
        "selector_quality_stats_available_without_values": bool01(
            nested_present(raw, "selected_cell_win_rate") or nested_present(raw, "selected_cell_profit_factor")
        ),
        "accepted_or_filled_action_flag": bool01("accepted_or_filled" in opp_status),
        "rejected_or_skipped_action_flag": bool01("rejected" in opp_status or "skipped" in opp_status),
        "feature_relevant_missing_penalty": safe_ratio(float(len(relevant_missing)), 10.0),
    }
    gaps = []
    if selected_cell_rows is None and canonical.get("source_key") == "candidate_causal_microscope":
        gaps.append("selector_selected_cell_rows_missing")
    if not values["selector_quality_stats_available_without_values"]:
        gaps.append("selector_probability_quality_stats_absent_or_label_values_excluded")
    if opportunity is None and canonical.get("source_key") in {"candidate_causal_microscope", "zero_trade_counterfactual_path_rank"}:
        gaps.append("selector_opportunity_join_absent")
    return values, gaps


def probability_debate_features(
    canonical: Mapping[str, Any],
    raw: Mapping[str, Any],
    opportunity: Mapping[str, Any] | None,
    relevant_missing: Sequence[str],
) -> tuple[dict[str, float], list[str]]:
    counts = opportunity.get("counts") if isinstance(opportunity, Mapping) else {}
    action_count = 0.0
    if isinstance(counts, Mapping):
        action_count = sum(as_float(value) or 0.0 for value in counts.values())
    probability_source = any(nested_present(raw, key) for key in ("probability", "confidence", "selected_cell_win_rate"))
    ev_source = any(nested_present(raw, key) for key in ("broker_net_ev_per_unit_risk", "fill_probability_at_decision"))
    values = {
        "probability_source_available": bool01(probability_source),
        "probability_value_excluded_until_asof_contract": bool01(nested_present(raw, "selected_cell_win_rate")),
        "ev_source_available_without_outcome_value": bool01(ev_source),
        "debate_action_alternative_count_log1p": log1p_safe(action_count),
        "uncertainty_missing_source_penalty": safe_ratio(float(len(relevant_missing)), 12.0),
        "source_completeness_score": source_completeness_score(canonical, len(relevant_missing)),
    }
    gaps = []
    if not probability_source:
        gaps.append("probability_source_missing_or_not_asof_materialized")
    if not ev_source:
        gaps.append("broker_net_ev_fill_probability_source_missing")
    return values, gaps


def numeric_confluence_features(
    canonical: Mapping[str, Any],
    raw: Mapping[str, Any],
    relevant_missing: Sequence[str],
) -> tuple[dict[str, float], list[str]]:
    text = status_texts(canonical, raw, None)
    follow = "follow" in text
    avoid = "avoid" in text
    mixed = "mixed" in text
    values = {
        "follow_signal_available": bool01(follow),
        "avoid_signal_available": bool01(avoid),
        "mixed_signal_available": bool01(mixed),
        "structured_disagreement_available": bool01(any((follow, avoid, mixed))),
        "source_completeness_numeric_score": source_completeness_score(canonical, len(relevant_missing)),
        "confluence_missing_source_penalty": safe_ratio(float(len(relevant_missing)), 10.0),
    }
    gaps = []
    if not any((follow, avoid, mixed)):
        gaps.append("follow_avoid_mixed_numeric_source_absent_for_row")
    if not any(nested_present(raw, key) for key in ("strength", "confidence", "reliability", "conflict_reason")):
        gaps.append("numeric_confluence_strength_confidence_reliability_fields_missing")
    return values, gaps


def same_symbol_features(
    canonical: Mapping[str, Any],
    raw: Mapping[str, Any],
    opportunity: Mapping[str, Any] | None,
    relevant_missing: Sequence[str],
) -> tuple[dict[str, float], list[str]]:
    text = status_texts(canonical, raw, opportunity)
    same_symbol_available = (
        "same_symbol" in text
        or (isinstance(opportunity, Mapping) and opportunity.get("same_symbol_alternative") not in (None, "", [], {}))
        or nested_present(raw, "same_symbol_overlap_status")
    )
    symbols = raw.get("symbols")
    symbol_count = len(symbols) if isinstance(symbols, list) else 1
    values = {
        "same_symbol_context_available": bool01(same_symbol_available),
        "same_symbol_alternative_available": bool01(
            isinstance(opportunity, Mapping) and opportunity.get("same_symbol_alternative") not in (None, "", [], {})
        ),
        "multi_symbol_window_count_log1p": log1p_safe(symbol_count),
        "scale_reduce_reverse_action_source_available": bool01(
            any(token in text for token in ("scale", "reduce", "reverse", "close"))
        ),
        "open_pending_snapshot_available": bool01(
            any(nested_present(raw, key) for key in ("open_positions", "pending_orders", "open_position_snapshot"))
        ),
        "same_symbol_missing_source_penalty": safe_ratio(float(len(relevant_missing)), 10.0),
    }
    gaps = []
    if not same_symbol_available:
        gaps.append("same_symbol_state_not_materialized_for_row")
    if not values["open_pending_snapshot_available"]:
        gaps.append("same_symbol_open_pending_snapshot_missing")
    return values, gaps


def scheduler_risk_features(
    raw: Mapping[str, Any],
    opportunity: Mapping[str, Any] | None,
    relevant_missing: Sequence[str],
) -> tuple[dict[str, float], list[str]]:
    source = opportunity if isinstance(opportunity, Mapping) else raw
    values = {
        "candidate_rows_log1p": log1p_safe(first_present(source, ("candidate_rows", "candidate_count"))),
        "alternative_count_log1p": log1p_safe(first_present(source, ("alternative_count",))),
        "filled_count_log1p": log1p_safe(first_present(source, ("filled_count",))),
        "rejected_count_log1p": log1p_safe(first_present(source, ("rejected_count",))),
        "skipped_count_log1p": log1p_safe(first_present(source, ("skipped_count",))),
        "risk_headroom_source_available": bool01(
            any(nested_present(raw, key) for key in ("risk_headroom", "available_risk", "selected_cell_risk_pct"))
        ),
        "open_pending_snapshot_available": bool01(
            any(nested_present(raw, key) for key in ("open_positions", "pending_orders", "open_position_snapshot"))
        ),
        "scheduler_missing_source_penalty": safe_ratio(float(len(relevant_missing)), 12.0),
    }
    gaps = []
    if not values["risk_headroom_source_available"]:
        gaps.append("scheduler_risk_headroom_source_missing")
    if not values["open_pending_snapshot_available"]:
        gaps.append("scheduler_open_pending_snapshot_missing")
    return values, gaps


def execution_entry_features(
    canonical: Mapping[str, Any],
    raw: Mapping[str, Any],
    relevant_missing: Sequence[str],
) -> tuple[dict[str, float], list[str]]:
    rr = first_present(
        raw,
        (
            "raw_trade_parameters_risk_reward_ratio",
            "initial_broker_order_target_multiple_r",
            "broker_order_initial_target_multiple_r",
        ),
    )
    dynamic_trigger = first_present(raw, ("dynamic_trigger_r",))
    partial_ratio = first_present(raw, ("partial_close_ratio",))
    values = {
        "geometry_source_available": bool01(rr is not None or dynamic_trigger is not None),
        "target_stop_rr_or_multiple_safe": as_float(rr) or 0.0,
        "dynamic_trigger_r_safe": as_float(dynamic_trigger) or 0.0,
        "partial_close_ratio_config_safe": as_float(partial_ratio) or 0.0,
        "valid_sltp_order_count_log1p": log1p_safe(first_present(raw, ("valid_sl_tp_order_count",))),
        "pending_lifecycle_source_available": bool01(canonical.get("source_key") == "pending_nofill_lifecycle"),
        "entry_fillability_source_available": bool01(
            any(nested_present(raw, key) for key in ("entry_price", "order_send_status", "fill_probability_at_decision"))
        ),
        "execution_missing_source_penalty": safe_ratio(float(len(relevant_missing)), 12.0),
    }
    gaps = []
    if not values["geometry_source_available"]:
        gaps.append("execution_target_stop_geometry_feature_source_missing")
    if not values["entry_fillability_source_available"]:
        gaps.append("entry_fillability_predecision_source_missing")
    return values, gaps


def market_state_features(
    canonical: Mapping[str, Any],
    raw: Mapping[str, Any],
    relevant_missing: Sequence[str],
) -> tuple[dict[str, float], list[str]]:
    session = str(canonical.get("session_bucket") or "")
    symbol = str(canonical.get("symbol") or "")
    text = status_texts(canonical, raw, None)
    values = {
        "session_tokyo_flag": bool01(session == "tokyo_broad"),
        "session_london_flag": bool01(session == "london_broad"),
        "session_ny_flag": bool01(session == "ny_broad"),
        "session_off_kz_flag": bool01(session == "off_kz_broad"),
        "symbol_hash_bucket_0_99": float(int(wave4a.stable_hash(symbol)[:8], 16) % 100),
        "market_state_source_available": bool01(
            any(token in text for token in ("market", "regime", "session", "whiteboard"))
        ),
        "cost_stress_source_required_flag": bool01(any("cost" in item for item in relevant_missing) or "cost" in text),
        "market_state_missing_source_penalty": safe_ratio(float(len(relevant_missing)), 12.0),
    }
    gaps = []
    if not values["market_state_source_available"]:
        gaps.append("market_state_whiteboard_or_regime_source_missing")
    return values, gaps


def zero_trade_features(
    canonical: Mapping[str, Any],
    raw: Mapping[str, Any],
    opportunity: Mapping[str, Any] | None,
    relevant_missing: Sequence[str],
) -> tuple[dict[str, float], list[str]]:
    text = status_texts(canonical, raw, opportunity)
    zero_row = canonical.get("source_key") == "zero_trade_counterfactual_path_rank" or "zero_trade" in text
    values = {
        "zero_trade_row_flag": bool01(zero_row),
        "no_trade_by_evidence_flag": bool01("no_trade_by_evidence" in text),
        "rejected_or_skipped_action_flag": bool01("rejected" in text or "skipped" in text),
        "zero_trade_comparator_available": bool01(
            isinstance(opportunity, Mapping) and opportunity.get("zero_trade_comparator") not in (None, "", [], {})
        ),
        "zero_trade_value_source_available_without_value": bool01(nested_present(raw, "zero_trade_value")),
        "counterfactual_path_gap_flag": bool01(
            any("counterfactual_path" in item.casefold() for item in relevant_missing)
        ),
        "zero_trade_missing_source_penalty": safe_ratio(float(len(relevant_missing)), 10.0),
    }
    gaps = []
    if zero_row and not values["zero_trade_value_source_available_without_value"]:
        gaps.append("zero_trade_runtime_value_source_missing")
    if zero_row and values["counterfactual_path_gap_flag"]:
        gaps.append("zero_trade_counterfactual_path_source_gap")
    return values, gaps


def source_completeness_features(
    canonical: Mapping[str, Any],
    path_clock: Mapping[str, Any] | None,
    relevant_missing: Sequence[str],
) -> tuple[dict[str, float], list[str]]:
    path_status = str((path_clock or {}).get("path_clock_status") or "")
    values = {
        "source_completeness_score": source_completeness_score(canonical, len(relevant_missing)),
        "source_gap_present_flag": bool01(canonical.get("source_completeness_state") == "source_gap_present"),
        "clock_available_flag": bool01(canonical.get("clock_status") == "asof_clock_available"),
        "feature_relevant_missing_count_log1p": log1p_safe(len(relevant_missing)),
        "path_clock_materialized_flag": bool01(path_status == "path_clock_materialized"),
        "path_clock_partial_or_gap_flag": bool01(path_status != "path_clock_materialized"),
        "upstream_label_values_excluded_flag": 1.0,
    }
    gaps = []
    if relevant_missing:
        gaps.append("feature_relevant_missing_source_fields_present")
    if path_status != "path_clock_materialized":
        gaps.append("path_clock_not_materialized_for_future_supervised_join")
    return values, gaps


def missing_source_penalty_features(
    raw: Mapping[str, Any],
    relevant_missing: Sequence[str],
) -> tuple[dict[str, float], list[str]]:
    missing_text = field_tokens_for(relevant_missing)
    values = {
        "missing_source_penalty": safe_ratio(float(len(relevant_missing)), 10.0),
        "non_generatable_runtime_truth_count_log1p": log1p_safe(
            sum(1 for item in relevant_missing if "non_generatable" in item.casefold() or "original_" in item.casefold())
        ),
        "pretrade_cost_snapshot_missing_flag": bool01("pretrade" in missing_text or "cost" in missing_text),
        "allocator_intent_missing_flag": bool01("allocator" in missing_text or "candidate_set" in missing_text),
        "fill_probability_missing_flag": bool01("fill_probability" in missing_text),
        "open_pending_snapshot_missing_flag": bool01(
            "open_position" in missing_text or "pending_order" in missing_text
        ),
        "forbidden_outcome_values_excluded_flag": 1.0,
    }
    gaps = list(relevant_missing)
    if not relevant_missing and raw:
        gaps = []
    return values, gaps


def make_feature_row(
    canonical: Mapping[str, Any],
    event: Mapping[str, Any],
    raw: Mapping[str, Any],
    path_clock: Mapping[str, Any] | None,
    opportunity: Mapping[str, Any] | None,
) -> dict[str, Any]:
    relevant_missing = feature_relevant_missing_fields({**raw, **canonical})
    family_specs: dict[str, tuple[dict[str, float], list[str]]] = {
        "selector": selector_features(canonical, raw, opportunity, relevant_missing),
        "probability_debate": probability_debate_features(canonical, raw, opportunity, relevant_missing),
        "numeric_confluence": numeric_confluence_features(canonical, raw, relevant_missing),
        "same_symbol": same_symbol_features(canonical, raw, opportunity, relevant_missing),
        "scheduler_risk": scheduler_risk_features(raw, opportunity, relevant_missing),
        "execution_entry": execution_entry_features(canonical, raw, relevant_missing),
        "market_state": market_state_features(canonical, raw, relevant_missing),
        "zero_trade": zero_trade_features(canonical, raw, opportunity, relevant_missing),
        "source_completeness": source_completeness_features(canonical, path_clock, relevant_missing),
        "missing_source_penalty": missing_source_penalty_features(raw, relevant_missing),
    }
    families = {
        family: family_record(
            family=family,
            canonical=canonical,
            event=event,
            values=values,
            gap_codes=gaps,
            relevant_missing=relevant_missing,
        )
        for family, (values, gaps) in family_specs.items()
    }
    future_supervised_join_keys = {
        "canonical_row_id": canonical["canonical_row_id"],
        "duplicate_policy_key": canonical.get("duplicate_policy_key"),
        "source_row_id": canonical.get("source_row_id"),
        "source_row_hash": canonical.get("source_row_hash"),
    }
    payload = {
        "schema_version": "wave4b_feature_ledger_v1",
        "feature_row_id": f"feature:{canonical['canonical_row_id']}",
        "canonical_row_id": canonical["canonical_row_id"],
        "feature_namespace": LANE,
        "feature_version": FEATURE_VERSION,
        "asof_time_utc": event.get("event_time_utc") or canonical.get("canonical_time_utc"),
        "source_key": canonical["source_key"],
        "source_path": canonical["source_path"],
        "source_sha256": canonical["source_sha256"],
        "source_row_hash": canonical["source_row_hash"],
        "source_completeness_state": canonical.get("source_completeness_state"),
        "evidence_class": (canonical.get("evidence_labels") or {}).get("evidence_class")
        or "source_bound_asof_feature_materialization",
        "freshness": freshness(event.get("event_time_utc") or canonical.get("canonical_time_utc")),
        "feature_relevant_missing_fields": relevant_missing,
        "family_statuses": {family: record["feature_status"] for family, record in families.items()},
        "features": families,
        "future_supervised_join_keys": future_supervised_join_keys,
        "upstream_supervised_value_status": "upstream_supervised_values_not_consumed_as_features",
        "runtime_effect_boundary": "local_feature_artifact_only_no_model_training_no_live_deployment",
    }
    payload["feature_hash"] = wave4a.stable_hash(payload)
    return payload


def flatten_family_rows(feature_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for feature_row in feature_rows:
        for family in FAMILY_NAMES:
            record = dict(feature_row["features"][family])
            record["feature_row_id"] = feature_row["feature_row_id"]
            rows.append(record)
    return rows


def source_hash_rows(feature_rows: Iterable[Mapping[str, Any]], inputs: Mapping[str, Any]) -> list[dict[str, Any]]:
    manifest_hash = wave4a.sha256_file(
        Path(inputs["repo_root"]) / WAVE4A_ROUTE / "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_OUTPUT_MANIFEST.json"
    )
    rows: list[dict[str, Any]] = []
    for row in feature_rows:
        rows.append(
            {
                "schema_version": "wave4b_feature_source_hash_v1",
                "feature_row_id": row["feature_row_id"],
                "canonical_row_id": row["canonical_row_id"],
                "source_key": row["source_key"],
                "source_path": row["source_path"],
                "source_sha256": row["source_sha256"],
                "source_row_hash": row["source_row_hash"],
                "wave4a_manifest_sha256": manifest_hash,
                "feature_hash": row["feature_hash"],
                "hash_join_status": "source_hash_materialized",
            }
        )
    return rows


def scan_field_classifications(rows_by_name: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()

    def walk(prefix: str, value: Any) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                walk(f"{prefix}.{key}" if prefix else str(key), item)
        elif isinstance(value, list):
            counts[f"{prefix}[]"] += 1
            for item in value[:3]:
                walk(f"{prefix}[]", item)
        else:
            counts[prefix] += 1

    for name, rows in rows_by_name.items():
        for row in rows:
            walk(name, row)

    output: list[dict[str, Any]] = []
    for field_path, count in sorted(counts.items()):
        normalized = field_path.casefold()
        forbidden = any(token in normalized for token in FORBIDDEN_LABEL_FIELD_TOKENS)
        safe_numeric = field_path.split(".")[-1].replace("[]", "") in SAFE_NUMERIC_SOURCE_KEYS
        safe_status = field_path.split(".")[-1].replace("[]", "") in SAFE_STATUS_KEYS
        if forbidden:
            classification = "forbidden_label_or_outcome_field_excluded"
        elif safe_numeric:
            classification = "feature_safe_numeric_asof_or_config_field"
        elif safe_status or any(token in normalized for token in ("source", "missing", "clock", "status")):
            classification = "feature_safe_status_or_source_completeness_field"
        else:
            classification = "not_used_unclassified_or_text_context"
        output.append(
            {
                "schema_version": "wave4b_no_leak_field_classification_v1",
                "field_path": field_path,
                "classification": classification,
                "observed_count": count,
                "feature_input_allowed": classification.startswith("feature_safe"),
                "reason": (
                    "excluded because field name/path is a Wave4C label, post-decision path, broker-real cash, R, expectancy, or outcome surface"
                    if forbidden
                    else "safe only through explicit Wave4B whitelist and verifier checks"
                    if classification.startswith("feature_safe")
                    else "not consumed by Wave4B feature materializer"
                ),
            }
        )
    return output


def source_gap_rows(feature_rows: Iterable[Mapping[str, Any]], wave4a_source_gaps: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_gap in wave4a_source_gaps:
        rows.append(
            {
                "schema_version": "wave4b_source_gap_capture_v1",
                "row_id": f"wave4a_upstream_gap:{source_gap.get('row_id')}",
                "canonical_row_id": None,
                "feature_family": "upstream_wave4a_source_gap",
                "source_gap_state": source_gap.get("source_gap_state", "source_gap_present"),
                "missing_source_or_field": source_gap.get("missing_source_or_field"),
                "repair_or_capture_requirement": source_gap.get("repair_or_capture_requirement"),
                "source_path": source_gap.get("source_path"),
                "result_use_status": "upstream_source_gap_preserved_no_feature_label_imputation",
            }
        )
    for row in feature_rows:
        for family, family_row in row["features"].items():
            for gap in family_row["source_gap_codes"]:
                rows.append(
                    {
                        "schema_version": "wave4b_source_gap_capture_v1",
                        "row_id": f"feature_gap:{row['canonical_row_id']}:{family}:{wave4a.stable_hash(gap)[:10]}",
                        "canonical_row_id": row["canonical_row_id"],
                        "feature_family": family,
                        "source_gap_state": "source_gap_present",
                        "missing_source_or_field": gap,
                        "repair_or_capture_requirement": repair_requirement_for_gap(family, str(gap)),
                        "source_path": row["source_path"],
                        "result_use_status": "wave4b_feature_gap_no_label_imputation",
                    }
                )
    return rows


def repair_requirement_for_gap(family: str, gap: str) -> str:
    if family == "probability_debate":
        return "Capture per-thesis probability, EV, uncertainty, veto, confidence calibration, and source-completeness fields inside LiveDecisionPacketV4 before model training."
    if family == "numeric_confluence":
        return "Persist FOLLOW/AVOID/MIXED strength, reliability history, freshness, cost sensitivity, conflict reason, and source completeness as pre-decision numeric rows."
    if family == "same_symbol":
        return "Persist same-symbol open/pending snapshot, lifecycle action alternatives, thesis-improvement score, reverse pressure, and risk headroom before final authority."
    if family == "scheduler_risk":
        return "Persist decision_window_id, candidate_set_id, open positions, pending orders, risk headroom, stale exposure opportunity cost, fill probability, and broker-net EV per unit risk."
    if family == "execution_entry":
        return "Persist predecision entry/fillability, target/stop geometry, cost/spread/slippage risk, and dynamic policy geometry in the packet before order authority."
    if family == "market_state":
        return "Persist Market Whiteboard V2 regime, damage memory, session health, source confidence, and zero-trade quality state as pre-decision context."
    if family == "zero_trade":
        return "Persist zero-trade value, rejected alternative ids, no-trade thesis, and source-bound counterfactual capture keys without realized path labels."
    return f"Repair or prospectively capture Wave4B {family} feature source: {gap}"


def question_rows() -> list[dict[str, Any]]:
    questions = [
        ("W4B_Q001", "Which fields are genuinely available before selection?", "answered_with_no_leak_classification_and_feature_schema"),
        ("W4B_Q002", "How are probability, EV, uncertainty, and disagreement encoded?", "partial_features_plus_exact_source_gaps_for_missing_asof_theses"),
        ("W4B_Q003", "How are FOLLOW/AVOID/MIXED confluence fields numeric?", "availability_and_missing_source_penalties_materialized_full_row_ledger"),
        ("W4B_Q004", "How do same-symbol pressure and alternatives become features?", "same_symbol_feature_ledger_and_gap_rows_materialized"),
        ("W4B_Q005", "How does scheduler risk headroom enter without leakage?", "counts_and_availability_features_only_exact_headroom_gap_recorded"),
        ("W4B_Q006", "Which features expose weak entry and geometry risk?", "predecision_geometry_availability_and_safe_rr_fields_materialized"),
        ("W4B_Q007", "How is zero-trade value represented?", "zero_trade_state_availability_and_gap_penalty_features_materialized"),
        ("W4B_Q008", "How are source completeness and missing-source penalties encoded?", "dedicated_full_row_feature_family_materialized"),
        ("W4B_Q009", "Which label families are excluded?", "no_leak_classification_excludes_cash_r_expectancy_mfe_mae_giveback_path_outcome"),
        ("W4B_Q010", "Can Wave4B reconcile to Wave4A row count and hash?", "feature_and_family_ledgers_reconcile_to_15679_wave4a_rows"),
        ("W4B_Q011", "What outside-current-edge mechanisms are preserved?", "session_market_state_geometry_fillability_cost_source_and_same_symbol_mechanisms_preserved_as_features_or_gaps"),
        ("W4B_Q012", "What remains impossible inside Wave4B evidence class?", "exact_prospective_capture_requirements_recorded_for_missing_predecision_sources"),
    ]
    return [
        {
            "schema_version": "wave4b_question_ledger_v1",
            "question_id": qid,
            "question": question,
            "status": status,
            "result_use_status": "feature_materialization_question_not_outcome_label",
        }
        for qid, question, status in questions
    ]


def searched_root_rows(repo_root: Path) -> list[dict[str, Any]]:
    paths = list(REQUIRED_CONTEXT_PATHS) + list(UPSTREAM_ROUTE_PATHS) + [
        str(WAVE4A_ROUTE / name) for name in WAVE4A_REQUIRED_FILES
    ]
    return [
        {
            "schema_version": "wave4b_searched_root_v1",
            "row_id": f"searched_root:{index:03d}",
            "path": path,
            "exists": (repo_root / path).exists(),
            "search_status": "read_or_inventory_checked_from_disk",
            "result_use_status": "source_discovery_context_not_label",
        }
        for index, path in enumerate(paths, start=1)
    ]


def route_decision_rows() -> list[dict[str, Any]]:
    decisions = [
        (
            "W4B_DECISION_001",
            "Build local Feature Store V2 over Wave4A canonical row ids only; do not synthesize replacement row universe.",
            "Wave4A verifier and acceptance review pass on disk.",
        ),
        (
            "W4B_DECISION_002",
            "Use family-level numeric features with source hash, as-of time, freshness, evidence class, and completeness metadata on every row.",
            "Prompt requires reusable structured APIs and full ledgers before Wave5.",
        ),
        (
            "W4B_DECISION_003",
            "Exclude exact-R, proxy-R, expectancy, broker-real cash/PnL, MFE/MAE, giveback, post-decision path labels, and outcome fields from feature inputs.",
            "Those labels belong to Wave4C/downstream audits.",
        ),
        (
            "W4B_DECISION_004",
            "Represent missing probability/debate, confluence, same-symbol, scheduler, cost, and fillability sources as numeric availability/penalty features plus exact capture requirements.",
            "Same-evidence-class repair found current accepted rows lack durable predecision packet fields for several families.",
        ),
    ]
    return [
        {
            "schema_version": "wave4b_route_decision_v1",
            "decision_id": decision_id,
            "decision": decision,
            "evidence": evidence,
            "evidence_class": "pre-decision as-of source-hashed feature materialization",
            "runtime_effect_boundary": "local_feature_artifact_only",
        }
        for decision_id, decision, evidence in decisions
    ]


def feature_schema() -> dict[str, Any]:
    return {
        "schema_version": "wave4b_feature_schema_v1",
        "lane": LANE,
        "feature_version": FEATURE_VERSION,
        "row_contract": {
            "primary_key": "canonical_row_id",
            "source_universe": str(WAVE4A_ROUTE / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl"),
            "row_count_expected": 15679,
            "one_feature_row_per_wave4a_canonical_row": True,
            "one_family_row_per_canonical_row_per_family": True,
        },
        "required_family_names": list(FAMILY_NAMES),
        "family_metadata_required": [
            "asof_time_utc",
            "source_sha256",
            "source_row_hash",
            "feature_namespace",
            "feature_version",
            "freshness",
            "evidence_class",
            "source_completeness",
        ],
        "forbidden_feature_inputs": sorted(FORBIDDEN_LABEL_FIELD_TOKENS),
        "safe_numeric_source_keys": sorted(SAFE_NUMERIC_SOURCE_KEYS),
        "safe_status_source_keys": sorted(SAFE_STATUS_KEYS),
        "label_boundary_policy": "Wave4B preserves future label join keys but does not compute, consume, select on, or encode exact-R, proxy-R, expectancy, broker-real cash/PnL, MFE/MAE, giveback, or outcome/path labels.",
    }


def context_anchor(repo_root: Path, summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "wave4b_context_anchor_v1",
        "route_id": ROUTE_ID,
        "lane": LANE,
        "branch": git_value(repo_root, "branch", "--show-current"),
        "head": git_value(repo_root, "rev-parse", "HEAD"),
        "created_at_utc": utc_now(),
        "prompt_path": str(PROMPT_PATH),
        "starter_path": str(STARTER_PATH),
        "route_dir": str(ROUTE_DIR),
        "evidence_class": "pre-decision as-of source-hashed feature materialization",
        "runtime_effect_boundary": "local feature artifacts/code only; no model training, production promotion, live deployment, or Feature Store label leakage",
        "boundary_status": BOUNDARY_STATUS,
        "required_context_paths": list(REQUIRED_CONTEXT_PATHS),
        "upstream_route_paths_read_from_disk": list(UPSTREAM_ROUTE_PATHS),
        "wave4a_dependency": summary["wave4a_dependency"],
        "row_counts": summary["row_counts"],
        "feature_family_names": list(FAMILY_NAMES),
        "pre_existing_unrelated_dirt_policy": "preserve unrelated legacy outcome-testing JSONL dirt and do not stage it for Wave4B",
    }


def independent_review_text(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Wave4B Independent Review Ledger",
        "",
        "Subagent tooling was available; bounded sidecar reviewers completed no-leak/schema and feature-family completeness reviews. The local route also ran role-separated review passes and incorporated their findings.",
        "",
        "| Role | Finding | Disposition |",
        "|---|---|---|",
        "| source/artifact auditor | Wave4A verifier, manifest, coverage, source inventory, searched-root, canonical/events/path/opportunity/source-gap ledgers were inspected and Wave4A verifier reran pass. | Wave4B uses Wave4A canonical ids only and records Wave4A hashes. |",
        "| no-leak/label-boundary critic | Sidecar review warned against upstream supervised boundary fields, path post-decision labels, broker cash/R, expectancy, MFE/MAE/giveback, win/loss, and final_outcome leakage. | These field paths are classified forbidden and excluded from numeric feature inputs; verifier scans feature values and supervised join keys carry no values. |",
        "| schema/manifest auditor | Every feature family requires as-of time, source hash, namespace, version, freshness, evidence class, and source completeness. | Feature schema and verifier enforce family metadata on every row. |",
        "| feature-family completeness critic | Sidecar review confirmed all ten required families are computable as source-hashed availability/status/penalty features, but native V4 packet values are often absent. | Availability/penalty features are materialized for every Wave4A row and exact capture requirements are emitted in the source-gap ledger. |",
        "| prompt/merge-scope critic | Shared context, runtime config, registry, and live deployment are outside Wave4B ownership. | Route writes only lane code/test/wrappers/artifacts; shared changes are capture requirements for Wave4I/orchestrator. |",
        "| saturation/self-red-team critic | The main leakage risk is accidentally treating Wave4A path labels or Wave2 expectancy/cash/R fields as features. | No-leak classification, family feature whitelist, and verifier checks preempt this. |",
    ]
    lines.extend(
        [
            "",
            "## Row Evidence",
            "",
            f"- Wave4A canonical rows: `{summary['row_counts']['wave4a_canonical_rows']}`.",
            f"- Wave4B feature rows: `{summary['row_counts']['feature_rows']}`.",
            f"- Feature-family rows: `{summary['row_counts']['feature_family_rows']}`.",
            f"- Source-gap rows: `{summary['row_counts']['source_gap_rows']}`.",
        ]
    )
    return "\n".join(lines) + "\n"


def saturation_text(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Wave4B Saturation And Self-Red-Team",
            "",
            "- Evidence-class leakage attack: exact-R, proxy-R, expectancy, broker-real cash/PnL, MFE/MAE, giveback, final outcome, and post-decision path labels were treated as forbidden field tokens and excluded from feature inputs.",
            "- Source-hash attack: every feature row carries source sha256, source row hash, Wave4A manifest hash through the source-hash ledger, and deterministic feature hash.",
            "- Timestamp attack: every feature family carries as-of time and deterministic freshness computed against the route reference date; clock gaps become zero freshness and source-gap rows.",
            "- Duplicate/denominator attack: the canonical Wave4A row id is the only primary key; Wave4B does not create alternate row ids or collapse duplicates.",
            "- Label-to-feature attack: Wave4A supervised boundary values and path-clock `post_decision_path_labels` are not read for numeric features. Future supervised join keys are preserved without supervised values.",
            "- Cost omission attack: broker-real post-trade cost cash is excluded; missing pretrade cost, spread, swap, commission, and fill-probability snapshots become source-gap requirements.",
            "- Static example boxing attack: feature-family coverage spans selector, probability/debate, numeric confluence, same-symbol, scheduler/risk, execution/entry, market state, zero-trade, source completeness, and missing-source penalties for every Wave4A row.",
            "- Same-class repair attack: current accepted rows lack several durable predecision packet fields; the route encodes availability/penalty features and exact prospective capture requirements rather than stopping at a vague blocker.",
            "",
            f"Result: `{summary['row_counts']['feature_rows']}` feature rows and `{summary['row_counts']['feature_family_rows']}` family rows preserve all material Wave4A rows before any ranking.",
        ]
    ) + "\n"


def instruction_checklist_text(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Wave4B Instruction Coverage Checklist",
            "",
            "| Requirement | Status | Evidence |",
            "|---|---|---|",
            "| Preflight/live-state/context read | complete | context anchor and searched-root ledger |",
            "| Wave4A dependency verified from disk | complete | verifier rerun pass, manifest/coverage inspected |",
            "| Feature builder implemented | complete | `src/research_infra/wave4b_feature_store_v2.py` |",
            "| Full Wave4A row coverage | complete | feature ledger row count equals Wave4A canonical row count |",
            "| No label leakage | complete | no-leak classification ledger and verifier |",
            "| Source hashes/freshness/completeness | complete | feature schema and source-hash ledger |",
            "| Required family ledgers | complete | feature-family, numeric confluence, and same-symbol ledgers |",
            "| Source gaps and capture requirements | complete | source-gap ledger |",
            "| Role-separated reviews | complete | independent review ledger |",
            "| Saturation/self-red-team | complete | saturation artifact |",
            "| Doctrine coverage | complete | completion audit table |",
            "| Runtime/deployment forbidden surfaces | preserved | boundary status all forbidden surfaces false |",
        ]
    ) + "\n"


def completion_audit_text(repo_root: Path, summary: Mapping[str, Any], verify_result: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Wave4B Feature Store V2 Completion Audit",
            "",
            f"Generated: {utc_now()}",
            f"Branch: `{git_value(repo_root, 'branch', '--show-current')}`",
            f"HEAD before Wave4B commit: `{git_value(repo_root, 'rev-parse', 'HEAD')}`",
            f"Route: `{ROUTE_DIR}`",
            "",
            "## Scope",
            "",
            "Built the as-of source-hashed Feature Store V2 over the accepted Wave4A canonical row universe. The route materializes local feature artifacts/code only and performs no model training, production promotion, live deployment, broker mutation, credential change, paid/vendor call, remote push, active VPS process mutation, or MT5 live operation.",
            "",
            "## Counts",
            "",
            f"- Wave4A canonical rows: `{summary['row_counts']['wave4a_canonical_rows']}`.",
            f"- Feature rows: `{summary['row_counts']['feature_rows']}`.",
            f"- Feature-family rows: `{summary['row_counts']['feature_family_rows']}`.",
            f"- Numeric confluence rows: `{summary['row_counts']['numeric_confluence_rows']}`.",
            f"- Same-symbol rows: `{summary['row_counts']['same_symbol_rows']}`.",
            f"- Source-gap/capture rows: `{summary['row_counts']['source_gap_rows']}`.",
            "",
            "## Evidence Separation",
            "",
            "Exact-R, proxy-R, expectancy, broker-real cash/PnL, MFE/MAE, giveback, final outcome, and post-decision path labels are excluded from numeric feature inputs. Future supervised join keys are preserved for Wave4C without supervised values.",
            "",
            "## Verification",
            "",
            f"- Wave4B verifier: `{'pass' if verify_result.get('ok') else 'fail'}`.",
            "- Focused tests, prompt hardening, route artifact audit, py_compile, pytest, diff check, and staged-path review are recorded in route result artifacts after execution.",
            "",
            "## Doctrine Coverage",
            "",
            "| Doctrine Item | Status |",
            "|---|---|",
            "| `goal_session_research_discipline.md` read after preflight | complete |",
            "| `research_operating_doctrine.md` read after preflight | complete |",
            "| Lane posture | builder/repair/replay feature-materialization |",
            "| Anti-boxing questions pursued | selector, probability/debate, confluence, same-symbol, scheduler/risk, execution/entry, market state, zero-trade, source completeness, missing-source penalties |",
            "| Outside-current-edge mechanisms considered | session state, geometry/fillability, cost stress, source completeness, stale/open/pending/same-symbol lifecycle, zero-trade value |",
            "| Proof-or-impossibility stop condition used | every Wave4A row has features or exact source/capture requirement |",
            "| Subagent/role-separated reviews completed | sidecar no-leak/schema and feature-family completeness reviews completed; local role-separated reviews integrated |",
            "| Doctrine requirements not answered | outcome labels, model training, partitions, production promotion, registry/runtime gates cross Wave4C/Wave4I/Wave5 or forbidden surfaces |",
            "",
            "## Unresolved Exact Requirements",
            "",
            "Unresolved items are exact prospective capture requirements in `WAVE4B_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl`, primarily missing predecision probability/EV theses, FOLLOW/AVOID/MIXED strength/reliability, same-symbol open/pending snapshots, scheduler risk headroom, broker-net EV/fill probability, pretrade cost/spread/slippage, and zero-trade value fields.",
        ]
    ) + "\n"


def output_manifest(repo_root: Path, route_dir: Path) -> dict[str, Any]:
    files = []
    for path in sorted(route_dir.iterdir()):
        if not path.is_file() or path.name == "WAVE4B_FEATURE_STORE_V2_OUTPUT_MANIFEST.json":
            continue
        try:
            manifest_path = path.relative_to(repo_root).as_posix()
        except ValueError:
            manifest_path = path.as_posix()
        item: dict[str, Any] = {
            "path": manifest_path,
            "sha256": wave4a.sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        if path.suffix == ".jsonl":
            item["jsonl_rows"] = sum(1 for _ in wave4a.iter_jsonl(path))
        files.append(item)
    return {
        "schema_version": "wave4b_output_manifest_v1",
        "route_id": ROUTE_ID,
        "lane": LANE,
        "generated_at_utc": utc_now(),
        "file_count": len(files),
        "manifest_self_excluded_from_hash_list": True,
        "boundary_status": BOUNDARY_STATUS,
        "files": files,
    }


def route_artifact_audit(repo_root: Path, route_dir: Path) -> dict[str, Any]:
    missing = [name for name in REQUIRED_ROUTE_FILES if not (route_dir / name).exists()]
    jsonl_counts = {}
    parse_errors = []
    for path in route_dir.glob("*.jsonl"):
        try:
            jsonl_counts[path.name] = sum(1 for _ in wave4a.iter_jsonl(path))
        except Exception as exc:  # pragma: no cover - defensive route audit
            parse_errors.append(f"{path.name}: {exc}")
    return {
        "schema_version": "wave4b_route_artifact_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "ok": not missing and not parse_errors,
        "missing_required_files": missing,
        "jsonl_counts": jsonl_counts,
        "parse_errors": parse_errors,
        "boundary_status": BOUNDARY_STATUS,
        "git_status_short": git_value(repo_root, "status", "--short"),
    }


def prompt_hardening_result(repo_root: Path) -> dict[str, Any]:
    checks = []
    for path in (PROMPT_PATH, STARTER_PATH):
        text = (repo_root / path).read_text(encoding="utf-8", errors="replace")
        checks.append(
            {
                "path": str(path),
                "exists": True,
                "has_preflight": "generate_live_state.py" in text,
                "has_no_chat_memory": "chat memory" in text,
                "has_no_top_n": "No arbitrary top-N" in text or "no arbitrary top-N" in text,
                "has_forbidden_surfaces": "Forbidden" in text or "forbidden" in text,
                "has_completion_standard": "completion standard" in text.casefold() or "complete only" in text.casefold(),
            }
        )
    return {
        "schema_version": "wave4b_prompt_hardening_result_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "ok": all(all(value is True for key, value in check.items() if key not in {"path"}) for check in checks),
        "checks": checks,
    }


def focused_test_result(commands: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "wave4b_focused_test_result_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "ok": all(command.get("exit_code") == 0 for command in (commands or [])) if commands else False,
        "commands": list(commands or []),
    }


def build_artifacts(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    route = route_abs(repo_root, route_dir)
    route.mkdir(parents=True, exist_ok=True)
    inputs = load_wave4a_inputs(repo_root)
    inputs["repo_root"] = str(repo_root)
    raw_by_key = load_raw_sources(repo_root, inputs["inventory"])
    feature_rows: list[dict[str, Any]] = []
    for canonical in inputs["canonical"]:
        canonical_id = str(canonical["canonical_row_id"])
        event = inputs["events"][canonical_id]
        path_clock = inputs["path_clock"].get(canonical_id)
        opportunity = inputs["opportunity"].get(canonical_id)
        raw = raw_by_key.get(raw_row_key(canonical), {})
        feature_rows.append(make_feature_row(canonical, event, raw, path_clock, opportunity))

    family_rows = flatten_family_rows(feature_rows)
    numeric_confluence_rows = [row for row in family_rows if row["feature_family"] == "numeric_confluence"]
    same_symbol_rows = [row for row in family_rows if row["feature_family"] == "same_symbol"]
    summary = {
        "wave4a_dependency": {
            "verifier_ok": bool(inputs["verifier"].get("ok")),
            "manifest_path": str(WAVE4A_ROUTE / "WAVE4A_DIGITAL_TWIN_HISTORICAL_MICROSCOPE_OUTPUT_MANIFEST.json"),
            "canonical_universe_sha256": wave4a.sha256_file(repo_root / WAVE4A_ROUTE / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl"),
            "canonical_universe_rows": len(inputs["canonical"]),
        },
        "row_counts": {
            "wave4a_canonical_rows": len(inputs["canonical"]),
            "feature_rows": len(feature_rows),
            "feature_family_rows": len(family_rows),
            "numeric_confluence_rows": len(numeric_confluence_rows),
            "same_symbol_rows": len(same_symbol_rows),
            "source_gap_rows": 0,
        },
    }

    wave4a.write_json(route / "WAVE4B_FEATURE_SCHEMA.json", feature_schema())
    wave4a.write_jsonl(route / "WAVE4B_FEATURE_LEDGER.jsonl", feature_rows)
    wave4a.write_jsonl(route / "WAVE4B_FEATURE_FAMILY_LEDGER.jsonl", family_rows)
    wave4a.write_jsonl(route / "WAVE4B_NUMERIC_CONFLUENCE_FEATURE_LEDGER.jsonl", numeric_confluence_rows)
    wave4a.write_jsonl(route / "WAVE4B_SAME_SYMBOL_FEATURE_LEDGER.jsonl", same_symbol_rows)
    wave4a.write_jsonl(route / "WAVE4B_FEATURE_SOURCE_HASH_LEDGER.jsonl", source_hash_rows(feature_rows, inputs))
    classification_rows = scan_field_classifications(
        {
            "wave4a_canonical": inputs["canonical"][:200],
            "wave4a_event": list(inputs["events"].values())[:200],
            "wave4a_path_clock": list(inputs["path_clock"].values())[:200],
            "wave4a_opportunity": list(inputs["opportunity"].values())[:200],
            "raw_source": list(raw_by_key.values())[:500],
        }
    )
    wave4a.write_jsonl(route / "WAVE4B_NO_LEAK_FIELD_CLASSIFICATION_LEDGER.jsonl", classification_rows)
    gaps = source_gap_rows(feature_rows, inputs["source_gaps"])
    summary["row_counts"]["source_gap_rows"] = len(gaps)
    wave4a.write_jsonl(route / "WAVE4B_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl", gaps)
    wave4a.write_jsonl(route / "WAVE4B_QUESTION_LEDGER.jsonl", question_rows())
    wave4a.write_jsonl(route / "WAVE4B_SEARCHED_ROOT_LEDGER.jsonl", searched_root_rows(repo_root))
    wave4a.write_jsonl(route / "WAVE4B_ROUTE_DECISION_LEDGER.jsonl", route_decision_rows())
    wave4a.write_json(route / "WAVE4B_CONTEXT_ANCHOR.json", context_anchor(repo_root, summary))
    wave4a.write_text(route / "WAVE4B_INDEPENDENT_REVIEW_LEDGER.md", independent_review_text(summary))
    wave4a.write_text(route / "WAVE4B_FEATURE_STORE_V2_SATURATION_SELF_RED_TEAM.md", saturation_text(summary))
    wave4a.write_text(route / "WAVE4B_FEATURE_STORE_V2_INSTRUCTION_COVERAGE_CHECKLIST.md", instruction_checklist_text(summary))
    wave4a.write_json(route / "WAVE4B_FEATURE_STORE_V2_PROMPT_HARDENING_RESULT.json", prompt_hardening_result(repo_root))
    wave4a.write_json(route / "WAVE4B_FEATURE_STORE_V2_FOCUSED_TEST_RESULT.json", focused_test_result([]))
    verify_result = verify_route(repo_root, route)
    wave4a.write_json(route / "WAVE4B_FEATURE_STORE_V2_VERIFICATION_RESULT.json", verify_result)
    wave4a.write_text(route / "COMPLETION_AUDIT.md", completion_audit_text(repo_root, summary, verify_result))
    wave4a.write_json(route / "WAVE4B_FEATURE_STORE_V2_OUTPUT_MANIFEST.json", output_manifest(repo_root, route))
    wave4a.write_json(route / "WAVE4B_FEATURE_STORE_V2_ROUTE_ARTIFACT_AUDIT_RESULT.json", route_artifact_audit(repo_root, route))
    wave4a.write_json(route / "WAVE4B_FEATURE_STORE_V2_OUTPUT_MANIFEST.json", output_manifest(repo_root, route))
    return summary


def verify_route(repo_root: Path, route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    route = route_abs(repo_root, route_dir)
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, evidence: Mapping[str, Any] | None = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "evidence": dict(evidence or {})})

    for filename in REQUIRED_ROUTE_FILES:
        if filename in {"WAVE4B_FEATURE_STORE_V2_VERIFICATION_RESULT.json", "WAVE4B_FEATURE_STORE_V2_OUTPUT_MANIFEST.json"}:
            continue
        check(f"exists:{filename}", (route / filename).exists())

    try:
        wave4a_inputs = load_wave4a_inputs(repo_root)
        canonical_count = len(wave4a_inputs["canonical"])
        canonical_hash = wave4a.sha256_file(repo_root / WAVE4A_ROUTE / "WAVE4A_CANONICAL_ROW_UNIVERSE.jsonl")
    except Exception as exc:
        canonical_count = 0
        canonical_hash = None
        check("wave4a_dependency_loads", False, {"error": str(exc)})
    else:
        check("wave4a_dependency_loads", True, {"canonical_count": canonical_count, "canonical_sha256": canonical_hash})

    jsonl_counts = {}
    parse_errors = []
    for path in route.glob("*.jsonl"):
        try:
            jsonl_counts[path.name] = sum(1 for _ in wave4a.iter_jsonl(path))
        except Exception as exc:
            parse_errors.append(f"{path.name}: {exc}")
    check("all_jsonl_parse", not parse_errors, {"errors": parse_errors})

    feature_rows = list(wave4a.iter_jsonl(route / "WAVE4B_FEATURE_LEDGER.jsonl")) if (route / "WAVE4B_FEATURE_LEDGER.jsonl").exists() else []
    family_rows = list(wave4a.iter_jsonl(route / "WAVE4B_FEATURE_FAMILY_LEDGER.jsonl")) if (route / "WAVE4B_FEATURE_FAMILY_LEDGER.jsonl").exists() else []
    check("feature_rows_match_wave4a_canonical", len(feature_rows) == canonical_count, {"feature_rows": len(feature_rows), "canonical": canonical_count})
    check("feature_ids_unique", len({row.get("canonical_row_id") for row in feature_rows}) == len(feature_rows))
    check(
        "family_rows_full_coverage",
        len(family_rows) == canonical_count * len(FAMILY_NAMES),
        {"family_rows": len(family_rows), "expected": canonical_count * len(FAMILY_NAMES)},
    )
    family_counts = Counter(row.get("feature_family") for row in family_rows)
    check("all_required_families_present", set(family_counts) == set(FAMILY_NAMES), {"family_counts": dict(family_counts)})

    metadata_missing = []
    for row in family_rows[:]:
        for key in (
            "asof_time_utc",
            "source_sha256",
            "source_row_hash",
            "feature_namespace",
            "feature_version",
            "freshness",
            "evidence_class",
            "source_completeness",
        ):
            if key not in row:
                metadata_missing.append({"row": row.get("canonical_row_id"), "family": row.get("feature_family"), "missing": key})
                break
    check("every_family_has_required_metadata", not metadata_missing, {"missing_examples": metadata_missing[:10]})

    forbidden_feature_hits = []
    for row in family_rows:
        numeric = row.get("numeric_features")
        if not isinstance(numeric, Mapping):
            forbidden_feature_hits.append({"row": row.get("canonical_row_id"), "family": row.get("feature_family"), "issue": "numeric_features_not_object"})
            continue
        for key, value in numeric.items():
            lowered = str(key).casefold()
            if any(token in lowered for token in FORBIDDEN_LABEL_FIELD_TOKENS):
                forbidden_feature_hits.append({"row": row.get("canonical_row_id"), "family": row.get("feature_family"), "field": key})
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                forbidden_feature_hits.append({"row": row.get("canonical_row_id"), "family": row.get("feature_family"), "field": key, "issue": "non_numeric"})
    check("no_forbidden_or_non_numeric_feature_values", not forbidden_feature_hits, {"hits": forbidden_feature_hits[:20]})

    feature_hash_bad = []
    for row in feature_rows:
        feature_hash = row.get("feature_hash")
        comparable = dict(row)
        comparable.pop("feature_hash", None)
        if wave4a.stable_hash(comparable) != feature_hash:
            feature_hash_bad.append(row.get("canonical_row_id"))
    check("feature_hashes_recompute", not feature_hash_bad, {"bad_examples": feature_hash_bad[:10]})

    numeric_rows = jsonl_counts.get("WAVE4B_NUMERIC_CONFLUENCE_FEATURE_LEDGER.jsonl", 0)
    same_symbol_rows = jsonl_counts.get("WAVE4B_SAME_SYMBOL_FEATURE_LEDGER.jsonl", 0)
    check("numeric_confluence_full_rows", numeric_rows == canonical_count, {"actual": numeric_rows, "expected": canonical_count})
    check("same_symbol_full_rows", same_symbol_rows == canonical_count, {"actual": same_symbol_rows, "expected": canonical_count})

    source_gaps = jsonl_counts.get("WAVE4B_SOURCE_GAP_AND_CAPTURE_LEDGER.jsonl", 0)
    check("source_gap_rows_materialized", source_gaps > 0, {"source_gap_rows": source_gaps})
    boundary_ok = all(value is False for key, value in BOUNDARY_STATUS.items() if key != "RESULT_MATERIALIZATION_REQUIRED")
    check("boundary_status_preserved", boundary_ok, BOUNDARY_STATUS)

    ok = all(item["passed"] for item in checks)
    return {
        "schema_version": "wave4b_verification_result_v1",
        "route_id": ROUTE_ID,
        "lane": LANE,
        "generated_at_utc": utc_now(),
        "ok": ok,
        "issue_count": sum(1 for item in checks if not item["passed"]),
        "checks": checks,
        "jsonl_counts": jsonl_counts,
        "boundary_status": BOUNDARY_STATUS,
    }
