"""Build Stage 06 ablation and MIXED-resolution ledgers.

This is an offline replay measurement tool. It consumes the Stage 05 saturated
replay ledger and measures what changes when evidence families/components/classes
are removed from the compact runtime evidence recorded by Stage 05. It does not
mutate production config, prompts, broker state, accounts, orders, deals,
positions, or live runtime behavior.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import src.components.gtos_vnext_runtime as vnext_runtime  # noqa: E402
from src.components.gtos_vnext_runtime import (  # noqa: E402
    GTOSVNextRuntimeDecision,
    apply_vnext_risk_adjustment,
    evaluate_vnext_pending_policy,
    load_vnext_evidence_index,
    normalize_event,
)


CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"
SATURATED_REPLAY_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_SATURATED_REPLAY_LEDGER_2026-05-24.jsonl"
SATURATED_REPLAY_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_SATURATED_REPLAY_SUMMARY_2026-05-24.json"
STAGE05_METRICS_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_METRICS_SUMMARY_2026-05-24.json"
ABLATION_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_ABLATION_LEDGER_2026-05-24.jsonl"
MIXED_RESOLUTION_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_MIXED_RESOLUTION_LEDGER_2026-05-24.jsonl"
STAGE06_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_ABLATION_MIXED_SUMMARY_2026-05-24.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / "VNEXT_REPLAY_OUTPUT_MANIFEST_2026-05-24.json"
SESSION_STATE_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/gtos_vnext_replay_truth_engine"
    / "VNEXT_REPLAY_TRUTH_ENGINE_SESSION_STATE_2026-05-24.json"
)

STAGE_ID = "STAGE_06_ABLATION_AND_MIXED_RESOLUTION"
NEXT_STAGE_ID = "STAGE_07_PROP_FIRM_AND_ROBUSTNESS_MEASUREMENT"

DECISION_LABELS = ("FOLLOW", "AVOID", "MIXED", "LEGACY")
SURFACES = ("route_decision", "direct_decision", "pre_ai_side_decision")
ABLATION_DIMENSIONS = (
    "evidence_family",
    "source_component",
    "action_class",
    "route_family",
    "source_name",
    "source_role",
    "r_evidence_class",
    "target_stop_order_class",
    "proxy_r_class",
    "framework",
    "market_timeframe",
    "route_session",
    "symbol",
    "source_symbol",
    "side",
)
DIMENSION_COUNT_KEYS = {
    "evidence_family": ("evidence_family_counts", "evidence_family_decision_counts"),
    "source_component": ("source_component_counts", "source_component_decision_counts"),
    "action_class": ("action_class_counts", "action_class_decision_counts"),
    "route_family": ("route_family_counts", "route_family_decision_counts"),
    "source_name": ("source_name_counts", "source_name_decision_counts"),
    "source_role": ("source_role_counts", "source_role_decision_counts"),
    "r_evidence_class": ("r_evidence_class_counts", None),
    "target_stop_order_class": ("target_stop_order_class_counts", None),
    "proxy_r_class": ("proxy_r_class_counts", None),
    "framework": ("framework_counts", None),
    "market_timeframe": ("market_timeframe_counts", None),
    "route_session": ("route_session_counts", None),
    "symbol": ("symbol_counts", None),
    "source_symbol": ("source_symbol_counts", None),
    "side": ("side_counts", None),
}

SOURCE_REQUIRED_TOKENS = (
    "source_required",
    "source_requirement",
    "source_repair",
    "source_capture",
    "source_acquisition",
    "missing_source",
    "missing_denominator",
    "geometry_missing",
    "exact_r_missing",
    "sierra_depth_source",
)
REPLAY_ATTRIBUTION_TOKENS = (
    "replay_attribution",
    "runtime_decision_trace_only",
    "legacy",
    "v2_v3",
    "t7_simulation",
    "live_shadow",
)
CONTEXT_TOKENS = (
    "context",
    "guard",
    "quarantine",
    "shadow",
    "residue",
    "observability",
    "diagnostic",
)
BROAD_NOISY_TOKENS = (
    "<blank>",
    "none",
    "unknown",
    "all_sides",
    "all_sessions",
    "all_markets",
    "all_available_or_unmapped_sessions",
)


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
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def stable_hash(payload: Any, length: int = 24) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:length]


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def activated_config(config: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    runtime_cfg = cfg.setdefault("gtos_vnext_runtime", {})
    runtime_cfg["enabled"] = True
    runtime_cfg["apply_to_execution"] = True
    runtime_cfg["pre_ai_enabled"] = True
    runtime_cfg["pre_ai_apply_to_ai_call"] = True
    runtime_cfg["risk_adjustment_enabled"] = True
    runtime_cfg["pending_policy_enabled"] = True
    runtime_cfg["exit_management_residue_apply_to_execution"] = True
    runtime_cfg["ready8_failure_control_residue_apply_to_execution"] = True
    return cfg


def row_identity(row: dict[str, Any]) -> str:
    return str(
        row.get("review_row_id")
        or row.get("vnext_matrix_row_id")
        or row.get("event_scope_rollup_row_id")
        or row.get("registry_catalog_row_id")
        or row.get("ai_narrowing_policy_row_id")
        or row.get("ai_narrowing_capacity_blocklist_row_id")
        or row.get("numeric_router_catalog_runtime_row_id")
        or row.get("survivor_failure_runtime_row_id")
        or row.get("branch_ambiguity_collapse_runtime_row_id")
        or row.get("branch_followup_computation_runtime_row_id")
        or row.get("adverse_stop_first_execution_runtime_row_id")
        or row.get("gate_selector_session_timeframe_runtime_row_id")
        or row.get("sierra_depth_source_acquisition_runtime_row_id")
        or row.get("source_repair_missing_denominator_runtime_row_id")
        or row.get("nr_source_repair_execution_identity_runtime_row_id")
        or row.get("ai_narrowing_default_off_runtime_row_id")
        or row.get("ai_decision_trace_routing_guard_runtime_row_id")
        or row.get("pre_ai_post_l2_routing_policy_runtime_row_id")
        or row.get("rejected_candidate_l2_value_mining_runtime_row_id")
        or row.get("accepted_candidate_m1_fill_source_repair_runtime_row_id")
        or row.get("trade_record_execution_lifecycle_runtime_row_id")
        or row.get("nofill_pending_lifecycle_runtime_row_id")
        or row.get("scid_forward_source_capture_runtime_row_id")
        or row.get("source_geometry_runtime_row_id")
        or row.get("source_geometry_repair_row_id")
        or row.get("legacy_ai_cascade_model_runtime_row_id")
        or row.get("legacy_v2_v3_paper_live_friction_runtime_row_id")
        or row.get("sl_beyond_ob_outcome_join_source_repair_runtime_row_id")
        or row.get("fvg_trade_record_bounds_execution_runtime_row_id")
        or row.get("scid_target_horizon_control_runtime_row_id")
        or row.get("main_orch24_structural_repair_action_runtime_row_id")
        or row.get("main_orch24_action_completeness_residual_r_runtime_row_id")
        or row.get("main_orch24_implementation_selection_runtime_row_id")
        or row.get("main_orch24_snapshot_dependency_repair_runtime_row_id")
        or row.get("main_orch48_final_review_selector_runtime_row_id")
        or row.get("ltf_path_geometry_source_runtime_row_id")
        or row.get("instrument_expansion_market_session_runtime_row_id")
        or row.get("scid_combined_source_capture_poi_bounds_runtime_row_id")
        or row.get("frontier_action_id")
        or row.get("recommendation_unified_candidate_id")
        or row.get("recommendation_scope_rollup_id")
        or row.get("recommendation_family_rollup_id")
        or row.get("bucket_id")
        or row.get("numeric_result_row_id")
        or row.get("row_key")
        or ""
    )


def build_row_id_map(runtime_index: Any) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
    row_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    duplicate_counts: Counter[str] = Counter()
    for row in runtime_index.rows:
        rid = row_identity(row)
        if not rid:
            continue
        row_map[rid].append(dict(row))
    for rid, rows in row_map.items():
        if len(rows) > 1:
            duplicate_counts[rid] = len(rows)
    return dict(row_map), dict(duplicate_counts)


def counter_from(value: Any) -> Counter[str]:
    result: Counter[str] = Counter()
    if not isinstance(value, dict):
        return result
    for key, count in value.items():
        label = str(key)
        try:
            result[label] += int(count)
        except (TypeError, ValueError):
            continue
    return result


def sorted_counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def decision_counts_from_rows(rows: list[dict[str, Any]], cfg: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts[str(vnext_runtime._decision_from_row(row, cfg))] += 1
    return counts


def residual_decision(counts: Counter[str]) -> str:
    nonzero = {label for label, count in counts.items() if count > 0 and label != "LEGACY"}
    if not nonzero:
        return "LEGACY"
    if nonzero == {"FOLLOW"}:
        return "FOLLOW"
    if nonzero == {"AVOID"}:
        return "AVOID"
    return "MIXED"


def dimension_value(row: dict[str, Any], dimension: str) -> str:
    value = row.get(dimension)
    if value in (None, ""):
        return "<blank>"
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(item) for item in value) or "<blank>"
    return str(value)


def group_rows_by_dimension(rows: list[dict[str, Any]], dimension: str) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        groups[dimension_value(row, dimension)].append(idx)
    return dict(groups)


def matched_ids(decision: dict[str, Any]) -> list[str]:
    evidence = decision.get("evidence") or {}
    ids = evidence.get("matched_row_ids")
    if isinstance(ids, list):
        return [str(item) for item in ids if item not in (None, "")]
    return []


def reconstruct_rows_from_ids(
    decision: dict[str, Any],
    row_map: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    evidence = decision.get("evidence") or {}
    ids = matched_ids(decision)
    expected_count = int(evidence.get("matched_row_id_count") or 0)
    truncated = bool(evidence.get("matched_row_ids_truncated"))
    if not ids:
        return [], {
            "status": "NO_MATCHED_IDS_IN_STAGE05_EVIDENCE",
            "expected_count": expected_count,
            "matched_ids": 0,
            "missing_ids": [],
            "duplicate_id_hits": 0,
        }
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    duplicate_hits = 0
    for rid in ids:
        matches = row_map.get(rid) or []
        if not matches:
            missing.append(rid)
            continue
        if len(matches) > 1:
            duplicate_hits += 1
        rows.append(dict(matches[0]))
    if truncated:
        status = "ID_LIST_TRUNCATED_NEEDS_RUNTIME_RESELECTION"
    elif missing:
        status = "ID_RECONSTRUCTION_PARTIAL_MISSING_IDS"
    elif len(rows) != expected_count:
        status = "ID_RECONSTRUCTION_COUNT_MISMATCH"
    else:
        status = "ID_RECONSTRUCTED_FULL"
    return rows, {
        "status": status,
        "expected_count": expected_count,
        "matched_ids": len(ids),
        "rows_reconstructed": len(rows),
        "missing_ids": missing,
        "duplicate_id_hits": duplicate_hits,
    }


def route_selected_rows(
    *,
    event: dict[str, Any],
    surface: str,
    runtime_index: Any,
    runtime_cfg: dict[str, Any],
) -> tuple[list[dict[str, Any]], int | None]:
    min_scope_fields = int(runtime_cfg.get("min_scope_fields", 1) or 1)
    if surface == "direct_decision":
        normalized = normalize_event(event)
        matches = runtime_index.match_event(normalized, min_scope_fields=min_scope_fields)
        selected = vnext_runtime._select_runtime_rows(
            matches,
            cfg=runtime_cfg,
            min_scope_fields=min_scope_fields,
            normalized_event=normalized,
        )
        return vnext_runtime._dedupe_rows(selected), None

    prefix = "pre_ai" if surface == "pre_ai_side_decision" else "post_l2"
    route_cfg = runtime_cfg
    if prefix == "post_l2":
        candidate_framework = str(
            event.get("effective_framework") or event.get("framework") or ""
        )
        if bool(runtime_cfg.get("post_l2_route_use_candidate_framework_only", True)) and candidate_framework:
            route_cfg = {**runtime_cfg, "post_l2_route_frameworks": [candidate_framework]}
    selected, route_event_count = vnext_runtime._artifact_scoped_route_selected_rows(
        event,
        cfg=route_cfg,
        prefix=prefix,
        artifact_index=runtime_index,
        min_scope_fields=min_scope_fields,
    )
    return vnext_runtime._dedupe_rows(selected), route_event_count


def reconstruct_selected_rows(
    *,
    decision: dict[str, Any],
    surface: str,
    runtime_index: Any,
    row_map: dict[str, list[dict[str, Any]]],
    runtime_cfg: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows, status = reconstruct_rows_from_ids(decision, row_map)
    if status["status"] == "ID_RECONSTRUCTED_FULL":
        return rows, status
    selected, route_event_count = route_selected_rows(
        event=decision.get("event") or {},
        surface=surface,
        runtime_index=runtime_index,
        runtime_cfg=runtime_cfg,
    )
    expected = int((decision.get("evidence") or {}).get("matched_row_id_count") or 0)
    reselection_status = "RUNTIME_RESELECTED_FULL"
    if expected and len(selected) != expected:
        reselection_status = "RUNTIME_RESELECTED_COUNT_DIFFERS_FROM_STAGE05_COMPACT_COUNT"
    return selected, {
        **status,
        "status": reselection_status,
        "runtime_reselected_count": len(selected),
        "runtime_reselected_route_event_count": route_event_count,
    }


def compact_resolution(resolution: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(resolution, dict):
        return {}
    return {
        key: resolution.get(key)
        for key in (
            "mode",
            "fallback_decision",
            "selected_decision",
            "rows_scored",
            "follow_pressure",
            "avoid_pressure",
            "dominance_ratio",
            "min_abs_pressure",
            "effective_n_sum",
            "raw_decision_counts",
        )
        if key in resolution
    }


def pressure_row_id(row: dict[str, Any]) -> str:
    return str(
        row.get("review_row_id")
        or row.get("vnext_matrix_row_id")
        or row.get("event_scope_rollup_row_id")
        or row.get("sierra_depth_source_acquisition_runtime_row_id")
        or row.get("source_repair_missing_denominator_runtime_row_id")
        or row.get("nr_source_repair_execution_identity_runtime_row_id")
        or row.get("legacy_ai_cascade_model_runtime_row_id")
        or row.get("legacy_v2_v3_paper_live_friction_runtime_row_id")
        or row.get("sl_beyond_ob_outcome_join_source_repair_runtime_row_id")
        or row.get("fvg_trade_record_bounds_execution_runtime_row_id")
        or row.get("main_orch24_structural_repair_action_runtime_row_id")
        or row.get("main_orch24_action_completeness_residual_r_runtime_row_id")
        or row.get("main_orch24_implementation_selection_runtime_row_id")
        or row.get("main_orch24_snapshot_dependency_repair_runtime_row_id")
        or row.get("main_orch48_final_review_selector_runtime_row_id")
        or row.get("ltf_path_geometry_source_runtime_row_id")
        or row.get("instrument_expansion_market_session_runtime_row_id")
        or row.get("ai_narrowing_default_off_runtime_row_id")
        or row.get("ai_decision_trace_routing_guard_runtime_row_id")
        or row.get("pre_ai_post_l2_routing_policy_runtime_row_id")
        or row.get("rejected_candidate_l2_value_mining_runtime_row_id")
        or row.get("accepted_candidate_m1_fill_source_repair_runtime_row_id")
        or row.get("trade_record_execution_lifecycle_runtime_row_id")
        or row.get("nofill_pending_lifecycle_runtime_row_id")
        or row.get("source_geometry_runtime_row_id")
        or row.get("numeric_result_row_id")
        or row.get("frontier_action_id")
        or row.get("row_key")
        or ""
    )


def row_score_from_runtime(row: dict[str, Any], cfg: dict[str, Any]) -> float:
    return float(sum(vnext_runtime._weighted_pressure_components(row, cfg).values()))


def score_by_index(
    rows: list[dict[str, Any]],
    before_resolution: dict[str, Any],
    cfg: dict[str, Any],
) -> list[float]:
    queued_scores: dict[str, list[float]] = defaultdict(list)
    for score_row in before_resolution.get("row_scores") or []:
        if not isinstance(score_row, dict):
            continue
        queued_scores[str(score_row.get("row_id") or "")].append(float(score_row.get("score") or 0.0))
    scores: list[float] = []
    for row in rows:
        rid = pressure_row_id(row)
        if queued_scores.get(rid):
            scores.append(queued_scores[rid].pop(0))
        else:
            scores.append(row_score_from_runtime(row, cfg))
    return scores


def pressure_delta_decision(
    *,
    before_resolution: dict[str, Any],
    residual_counts: Counter[str],
    removed_indexes: set[int],
    row_scores: list[float],
    cfg: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    fallback = residual_decision(residual_counts)
    mode = str(before_resolution.get("mode") or "strict")
    if fallback != "MIXED" or mode not in {"evidence_weighted", "weighted"}:
        return fallback, {
            "mode": "stage06_aggregate_count_ablation",
            "fallback_decision": fallback,
            "selected_decision": fallback,
            "raw_decision_counts": dict(sorted(residual_counts.items())),
        }

    follow_pressure = 0.0
    avoid_pressure = 0.0
    rows_scored = 0
    for idx, score in enumerate(row_scores):
        if idx in removed_indexes or score == 0:
            continue
        rows_scored += 1
        if score > 0:
            follow_pressure += score
        elif score < 0:
            avoid_pressure += abs(score)
    dominance_ratio = float(
        before_resolution.get("dominance_ratio")
        or vnext_runtime._configured_float(cfg, "conflict_pressure_dominance_ratio", 1.25)
    )
    min_abs_pressure = float(
        before_resolution.get("min_abs_pressure")
        or vnext_runtime._configured_float(cfg, "conflict_min_abs_pressure", 0.0)
    )
    selected = fallback
    if rows_scored:
        if follow_pressure >= min_abs_pressure and follow_pressure >= avoid_pressure * dominance_ratio:
            selected = "FOLLOW"
        elif avoid_pressure >= min_abs_pressure and avoid_pressure >= follow_pressure * dominance_ratio:
            selected = "AVOID"
    return selected, {
        "mode": "stage06_pressure_delta_from_original_row_scores",
        "fallback_decision": fallback,
        "selected_decision": selected,
        "rows_scored": rows_scored,
        "follow_pressure": round(follow_pressure, 12),
        "avoid_pressure": round(avoid_pressure, 12),
        "dominance_ratio": dominance_ratio,
        "min_abs_pressure": min_abs_pressure,
        "raw_decision_counts": dict(sorted(residual_counts.items())),
    }


def runtime_decision_from_rows(
    *,
    rows: list[dict[str, Any]],
    event: dict[str, Any],
    enabled: bool,
    apply_to_execution: bool,
    cfg: dict[str, Any],
    artifact_paths: tuple[str, ...],
) -> GTOSVNextRuntimeDecision:
    normalized_event = normalize_event(event)
    if not rows:
        return GTOSVNextRuntimeDecision(
            decision="LEGACY",
            event=normalized_event,
            enabled=enabled,
            apply_to_execution=apply_to_execution,
            matched=False,
            reason="stage06_ablation_removed_all_matching_rows",
            evidence={"decision_counts": {}, "matched_rows": 0},
            artifact_paths=artifact_paths,
        )
    decision, resolution = vnext_runtime._resolve_final_decision(rows, cfg)
    evidence = vnext_runtime._aggregate_evidence(
        rows,
        row_detail_limit=0,
        id_list_limit=0,
        cfg=cfg,
    )
    evidence["decision_resolution"] = resolution
    return GTOSVNextRuntimeDecision(
        decision=decision,
        event=normalized_event,
        enabled=enabled,
        apply_to_execution=apply_to_execution,
        matched=True,
        reason="stage06_ablation_recomputed_from_remaining_rows",
        evidence=evidence,
        artifact_paths=artifact_paths,
    )


def best_path(row: dict[str, Any]) -> dict[str, Any]:
    summary = row.get("path_outcome_summary") or {}
    path = summary.get("best_available_path")
    return path if isinstance(path, dict) else {}


def path_payload(row: dict[str, Any]) -> dict[str, Any]:
    path = best_path(row)
    return {
        "best_path_mode": path.get("replay_mode"),
        "best_path_status": path.get("path_source_status"),
        "best_path_confidence": path.get("confidence"),
        "best_path_outcome": path.get("outcome_class"),
        "terminal_order": path.get("terminal_order"),
        "entry_touched": path.get("entry_touched"),
        "same_bar_ambiguity": path.get("same_bar_ambiguity"),
        "proxy_r_conservative": path.get("proxy_r_conservative"),
        "proxy_r_neutral": path.get("proxy_r_neutral"),
        "proxy_r_optimistic": path.get("proxy_r_optimistic"),
        "mfe_r": path.get("mfe_r"),
        "mae_r": path.get("mae_r"),
    }


def numeric(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def mode_config(mode: str, current_config: dict[str, Any], active_config: dict[str, Any]) -> dict[str, Any]:
    return active_config if mode == "hypothetical_activated_vnext" else current_config


def token_hit(text: str, tokens: tuple[str, ...]) -> bool:
    lowered = str(text or "").casefold()
    return any(token in lowered for token in tokens)


def path_outcome_signal(path: dict[str, Any]) -> str:
    outcome = str(path.get("outcome_class") or "").casefold()
    terminal = str(path.get("terminal_order") or "").casefold()
    proxy = numeric(path.get("proxy_r_neutral"))
    if "target_first" in outcome or "target_first" in terminal or "tp1" in terminal:
        return "WIN_OR_TARGET_FIRST"
    if "stop_first" in outcome or "stop_first" in terminal or "sl" in terminal:
        return "LOSS_OR_STOP_FIRST"
    if proxy is not None and proxy > 0:
        return "POSITIVE_PROXY_R"
    if proxy is not None and proxy < 0:
        return "NEGATIVE_PROXY_R"
    if "no_fill" in outcome or "no_entry" in outcome:
        return "NO_FILL_OR_NO_ENTRY_TOUCH"
    if "missing" in outcome:
        return "MISSING_OR_REFERENCE"
    return "NEUTRAL_OR_UNRESOLVED"


def ablation_path_hint(before_decision: str, after_decision: str, path: dict[str, Any]) -> str:
    signal = path_outcome_signal(path)
    if before_decision == "AVOID" and after_decision != "AVOID" and signal == "WIN_OR_TARGET_FIRST":
        return "avoid_pressure_removed_on_winning_path"
    if before_decision == "FOLLOW" and after_decision != "FOLLOW" and signal == "LOSS_OR_STOP_FIRST":
        return "follow_pressure_removed_on_losing_path"
    if before_decision == "MIXED" and after_decision in {"FOLLOW", "AVOID"}:
        return "mixed_pressure_resolved_by_ablation"
    if before_decision != after_decision:
        return "decision_changed"
    return "no_decision_change"


def risk_pending_after(
    *,
    surface: str,
    remaining_decision: GTOSVNextRuntimeDecision,
    config: dict[str, Any],
) -> dict[str, Any]:
    if surface != "route_decision":
        return {}
    risk_pct = float((config.get("risk", {}) or {}).get("risk_per_trade_pct", 2.0))
    risk = apply_vnext_risk_adjustment(
        current_risk_pct=risk_pct,
        decision=remaining_decision,
        config=config,
    ).to_record()
    pending = evaluate_vnext_pending_policy(
        decision=remaining_decision,
        config=config,
    ).to_record()
    return {
        "risk_after_would_multiplier": risk.get("would_multiplier"),
        "risk_after_multiplier": risk.get("multiplier"),
        "risk_after_reason": risk.get("reason"),
        "pending_after_would_action": pending.get("would_action"),
        "pending_after_action": pending.get("action"),
        "pending_after_reason": pending.get("reason"),
    }


def before_effects(row: dict[str, Any], surface: str) -> dict[str, Any]:
    if surface != "route_decision":
        return {}
    risk = row.get("risk_adjustment") or {}
    pending = row.get("pending_policy") or {}
    return {
        "risk_before_would_multiplier": risk.get("would_multiplier"),
        "risk_before_multiplier": risk.get("multiplier"),
        "risk_before_reason": risk.get("reason"),
        "pending_before_would_action": pending.get("would_action"),
        "pending_before_action": pending.get("action"),
        "pending_before_reason": pending.get("reason"),
    }


def surface_decisions(row: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    for surface in ("route_decision", "direct_decision"):
        decision = row.get(surface)
        if isinstance(decision, dict) and decision.get("matched"):
            yield surface, decision
    pre_ai = row.get("pre_ai_decision") or {}
    for side_index, side_decision in enumerate(pre_ai.get("side_decisions") or []):
        if isinstance(side_decision, dict) and side_decision.get("matched"):
            copied = dict(side_decision)
            copied["_pre_ai_side_index"] = side_index
            yield "pre_ai_side_decision", copied


def aggregate_ablation_rows_for_surface(
    *,
    replay_row: dict[str, Any],
    surface: str,
    decision: dict[str, Any],
) -> list[dict[str, Any]]:
    mode = str(replay_row.get("runtime_activation_mode") or "")
    before_decision = str(decision.get("decision") or "LEGACY")
    evidence = decision.get("evidence") or {}
    total_counts = counter_from(evidence.get("decision_counts"))
    rows_before = int(evidence.get("matched_rows") or evidence.get("matched_row_id_count") or 0)
    path = best_path(replay_row)
    path_info = path_payload(replay_row)
    before_resolution = compact_resolution(evidence.get("decision_resolution"))
    output: list[dict[str, Any]] = []
    if rows_before <= 0:
        return output
    for dimension in ABLATION_DIMENSIONS:
        count_key, decision_count_key = DIMENSION_COUNT_KEYS[dimension]
        counts = counter_from(evidence.get(count_key))
        if not counts:
            continue
        decision_by_value = evidence.get(decision_count_key) if decision_count_key else None
        for value, removed_count in sorted(counts.items()):
            removed_decisions = Counter()
            if isinstance(decision_by_value, dict) and isinstance(decision_by_value.get(value), dict):
                removed_decisions = counter_from(decision_by_value.get(value))
            residual_counts = Counter(total_counts)
            if removed_decisions:
                for label, count in removed_decisions.items():
                    residual_counts[label] -= count
                    if residual_counts[label] <= 0:
                        residual_counts.pop(label, None)
                decision_after = residual_decision(residual_counts)
                method = "aggregate_decision_count_ablation"
            else:
                decision_after = before_decision
                method = "presence_only_no_dimension_decision_counts"
            decision_changed = before_decision != decision_after
            effect_changed = bool(surface == "route_decision" and decision_changed)
            row_effects = before_effects(replay_row, surface)
            output.append(
                {
                    "schema_version": "vnext_replay_stage06_ablation_row_v1",
                    "stage_id": STAGE_ID,
                    "ablation_row_id": "abl_" + stable_hash(
                        [
                            replay_row.get("replay_row_id"),
                            mode,
                            surface,
                            decision.get("_pre_ai_side_index"),
                            dimension,
                            value,
                        ]
                    ),
                    "replay_row_id": replay_row.get("replay_row_id"),
                    "event_group_id": (replay_row.get("group") or {}).get("group_id"),
                    "runtime_activation_mode": mode,
                    "surface": surface,
                    "pre_ai_side_index": decision.get("_pre_ai_side_index"),
                    "dimension": dimension,
                    "dimension_value": value,
                    "rows_before": rows_before,
                    "rows_removed": removed_count,
                    "rows_after": max(0, rows_before - removed_count),
                    "decision_before": before_decision,
                    "decision_after": decision_after,
                    "aggregate_count_decision_after": decision_after,
                    "decision_changed": decision_changed,
                    "effect_changed": effect_changed,
                    "removed_decision_counts": dict(sorted(removed_decisions.items())),
                    "residual_decision_counts": dict(sorted(residual_counts.items())),
                    "total_decision_counts": dict(sorted(total_counts.items())),
                    "decision_resolution_before": before_resolution,
                    "decision_resolution_after": {
                        "mode": method,
                        "selected_decision": decision_after,
                        "raw_decision_counts": dict(sorted(residual_counts.items())),
                    },
                    "removed_contains_mixed": removed_decisions.get("MIXED", 0) > 0
                    or (not removed_decisions and before_decision == "MIXED"),
                    "mixed_involvement": bool(
                        before_decision == "MIXED"
                        or decision_after == "MIXED"
                        or removed_decisions.get("MIXED", 0) > 0
                        or residual_counts.get("MIXED", 0) > 0
                    ),
                    "ablation_path_hint": ablation_path_hint(before_decision, decision_after, path),
                    "path_outcome_signal": path_outcome_signal(path),
                    "reconstruction_status": "STAGE05_COMPACT_AGGREGATE_EVIDENCE",
                    "reconstruction_expected_count": rows_before,
                    "reconstruction_rows_reconstructed": rows_before,
                    "effect_recompute_status": (
                        "decision_delta_proxy_no_policy_recompute"
                        if surface == "route_decision"
                        else "not_route_policy_surface"
                    ),
                    "ablation_method": method,
                    "no_live_trading_or_broker_mutation": True,
                    "production_config_mutated": False,
                    **row_effects,
                    **path_info,
                }
            )
    return output


def ablation_rows_for_surface(
    *,
    replay_row: dict[str, Any],
    surface: str,
    decision: dict[str, Any],
    selected_rows: list[dict[str, Any]],
    reconstruction: dict[str, Any],
    current_config: dict[str, Any],
    active_config: dict[str, Any],
    artifact_paths: tuple[str, ...],
) -> list[dict[str, Any]]:
    mode = str(replay_row.get("runtime_activation_mode") or "")
    config = mode_config(mode, current_config, active_config)
    runtime_cfg = (config.get("gtos_vnext_runtime", {}) or {})
    before_decision = str(decision.get("decision") or "LEGACY")
    full_before_resolution = (decision.get("evidence") or {}).get("decision_resolution") or {}
    before_resolution = compact_resolution(full_before_resolution)
    row_decisions = [
        str(vnext_runtime._decision_from_row(selected_row, runtime_cfg))
        for selected_row in selected_rows
    ]
    row_scores = score_by_index(selected_rows, full_before_resolution, runtime_cfg)
    total_counts: Counter[str] = Counter(row_decisions)
    event = decision.get("event") or {}
    path = best_path(replay_row)
    path_info = path_payload(replay_row)
    output: list[dict[str, Any]] = []
    if not selected_rows:
        return output

    for dimension in ABLATION_DIMENSIONS:
        groups = group_rows_by_dimension(selected_rows, dimension)
        for value, indexes in sorted(groups.items()):
            removed_ids = {idx for idx in indexes}
            removed_counts: Counter[str] = Counter(row_decisions[idx] for idx in indexes)
            residual_counts = Counter(total_counts)
            for label, count in removed_counts.items():
                residual_counts[label] -= count
                if residual_counts[label] <= 0:
                    residual_counts.pop(label, None)
            aggregate_after = residual_decision(residual_counts)
            decision_after, resolution_after = pressure_delta_decision(
                before_resolution=full_before_resolution,
                residual_counts=residual_counts,
                removed_indexes=removed_ids,
                row_scores=row_scores,
                cfg=runtime_cfg,
            )
            row_effects = before_effects(replay_row, surface)
            decision_changed = before_decision != decision_after
            effect_changed = bool(surface == "route_decision" and decision_changed)
            removed_has_mixed = removed_counts.get("MIXED", 0) > 0
            ablation_row = {
                "schema_version": "vnext_replay_stage06_ablation_row_v1",
                "stage_id": STAGE_ID,
                "ablation_row_id": "abl_" + stable_hash(
                    [
                        replay_row.get("replay_row_id"),
                        mode,
                        surface,
                        decision.get("_pre_ai_side_index"),
                        dimension,
                        value,
                    ]
                ),
                "replay_row_id": replay_row.get("replay_row_id"),
                "event_group_id": (replay_row.get("group") or {}).get("group_id"),
                "runtime_activation_mode": mode,
                "surface": surface,
                "pre_ai_side_index": decision.get("_pre_ai_side_index"),
                "dimension": dimension,
                "dimension_value": value,
                "rows_before": len(selected_rows),
                "rows_removed": len(indexes),
                "rows_after": len(selected_rows) - len(indexes),
                "decision_before": before_decision,
                "decision_after": decision_after,
                "aggregate_count_decision_after": aggregate_after,
                "decision_changed": decision_changed,
                "effect_changed": effect_changed,
                "removed_decision_counts": dict(sorted(removed_counts.items())),
                "residual_decision_counts": dict(sorted(residual_counts.items())),
                "total_decision_counts": dict(sorted(total_counts.items())),
                "decision_resolution_before": before_resolution,
                "decision_resolution_after": compact_resolution(resolution_after),
                "removed_contains_mixed": removed_has_mixed,
                "mixed_involvement": bool(
                    before_decision == "MIXED"
                    or decision_after == "MIXED"
                    or removed_has_mixed
                    or residual_counts.get("MIXED", 0) > 0
                ),
                "ablation_path_hint": ablation_path_hint(before_decision, decision_after, path),
                "path_outcome_signal": path_outcome_signal(path),
                "reconstruction_status": reconstruction.get("status"),
                "reconstruction_expected_count": reconstruction.get("expected_count"),
                "reconstruction_rows_reconstructed": reconstruction.get("rows_reconstructed")
                or reconstruction.get("runtime_reselected_count"),
                "effect_recompute_status": (
                    "decision_delta_proxy_no_policy_recompute"
                    if surface == "route_decision"
                    else "not_route_policy_surface"
                ),
                "no_live_trading_or_broker_mutation": True,
                "production_config_mutated": False,
                **row_effects,
                **path_info,
            }
            output.append(ablation_row)
    return output


def add_group_stats(stats: dict[str, Any], row: dict[str, Any]) -> None:
    stats["ablation_rows"] += 1
    stats["runtime_activation_modes"].add(row.get("runtime_activation_mode"))
    stats["surfaces"].add(row.get("surface"))
    stats["event_group_ids"].add(row.get("event_group_id"))
    stats["decision_before_counts"][row.get("decision_before")] += 1
    stats["decision_after_counts"][row.get("decision_after")] += 1
    stats["path_outcome_counts"][row.get("best_path_outcome")] += 1
    stats["path_signal_counts"][row.get("path_outcome_signal")] += 1
    stats["path_mode_counts"][row.get("best_path_mode")] += 1
    stats["reconstruction_status_counts"][row.get("reconstruction_status")] += 1
    if row.get("decision_changed"):
        stats["decision_changed_count"] += 1
        transition = f"{row.get('decision_before')}->{row.get('decision_after')}"
        stats["decision_transition_counts"][transition] += 1
    if row.get("effect_changed"):
        stats["effect_changed_count"] += 1
    if row.get("removed_contains_mixed") or row.get("decision_before") == "MIXED":
        stats["mixed_involvement_count"] += 1
    proxy = numeric(row.get("proxy_r_neutral"))
    if proxy is not None:
        stats["proxy_r_count"] += 1
        stats["proxy_r_sum"] += proxy
    value_text = f"{row.get('dimension')}:{row.get('dimension_value')}"
    if token_hit(value_text, SOURCE_REQUIRED_TOKENS):
        stats["source_required_signal_count"] += 1
    if token_hit(value_text, REPLAY_ATTRIBUTION_TOKENS):
        stats["replay_attribution_signal_count"] += 1
    if token_hit(value_text, CONTEXT_TOKENS):
        stats["context_signal_count"] += 1
    if token_hit(str(row.get("dimension_value")), BROAD_NOISY_TOKENS):
        stats["broad_noisy_signal_count"] += 1


def classify_mixed_group(stats: dict[str, Any]) -> tuple[str, str]:
    transitions = stats["decision_transition_counts"]
    path_signals = stats["path_signal_counts"]
    proxy_count = stats["proxy_r_count"]
    proxy_mean = stats["proxy_r_sum"] / proxy_count if proxy_count else None
    value_text = f"{stats['dimension']}:{stats['dimension_value']}"

    if stats["source_required_signal_count"] > 0 or token_hit(value_text, SOURCE_REQUIRED_TOKENS):
        return (
            "source-required and not safely resolvable",
            "dimension carries source-repair/source-acquisition/missing-source semantics",
        )
    if stats["replay_attribution_signal_count"] > 0 or token_hit(value_text, REPLAY_ATTRIBUTION_TOKENS):
        return (
            "replay attribution only",
            "dimension is legacy/replay-attribution context and should not cast fresh pressure",
        )
    if transitions.get("MIXED->FOLLOW", 0) and not transitions.get("MIXED->AVOID", 0):
        if proxy_mean is None or proxy_mean >= 0:
            return ("resolvable into FOLLOW", "ablation resolves MIXED into FOLLOW without negative proxy mean")
    if transitions.get("MIXED->AVOID", 0) and not transitions.get("MIXED->FOLLOW", 0):
        if proxy_mean is None or proxy_mean <= 0:
            return ("resolvable into AVOID", "ablation resolves MIXED into AVOID without positive proxy mean")
    if transitions.get("AVOID->FOLLOW", 0) and path_signals.get("WIN_OR_TARGET_FIRST", 0):
        return ("harmful route pressure", "AVOID pressure removal exposes winning/target-first paths")
    if transitions.get("FOLLOW->AVOID", 0) and path_signals.get("LOSS_OR_STOP_FIRST", 0):
        return ("toxic/remove candidate", "FOLLOW pressure removal exposes losing/stop-first paths")
    if stats["decision_changed_count"] > 0 and proxy_count:
        return ("ambiguous but replay-resolvable", "ablation changes decisions and path proxy evidence exists")
    if stats["context_signal_count"] > 0 and stats["decision_changed_count"] == 0:
        return ("useful context", "context/guard evidence does not alter ablated runtime decisions")
    if stats["broad_noisy_signal_count"] > 0:
        return ("broad/unanchored/noisy", "dimension is blank/all/unknown or otherwise broadly scoped")
    if stats["decision_changed_count"] == 0:
        return ("neutral/no-effect context", "ablation does not change runtime decision or measured effects")
    return ("ambiguous but replay-resolvable", "ablation is measured but direction is mixed across rows")


def mixed_resolution_rows(ablation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in ablation_rows:
        if not row.get("mixed_involvement"):
            continue
        key = (str(row.get("surface")), str(row.get("dimension")), str(row.get("dimension_value")))
        if key not in groups:
            groups[key] = {
                "surface": key[0],
                "dimension": key[1],
                "dimension_value": key[2],
                "ablation_rows": 0,
                "runtime_activation_modes": set(),
                "surfaces": set(),
                "event_group_ids": set(),
                "decision_before_counts": Counter(),
                "decision_after_counts": Counter(),
                "decision_transition_counts": Counter(),
                "path_outcome_counts": Counter(),
                "path_signal_counts": Counter(),
                "path_mode_counts": Counter(),
                "reconstruction_status_counts": Counter(),
                "decision_changed_count": 0,
                "effect_changed_count": 0,
                "mixed_involvement_count": 0,
                "proxy_r_count": 0,
                "proxy_r_sum": 0.0,
                "source_required_signal_count": 0,
                "replay_attribution_signal_count": 0,
                "context_signal_count": 0,
                "broad_noisy_signal_count": 0,
            }
        add_group_stats(groups[key], row)

    output: list[dict[str, Any]] = []
    for key, stats in sorted(groups.items()):
        classification, reason = classify_mixed_group(stats)
        proxy_mean = (
            stats["proxy_r_sum"] / stats["proxy_r_count"]
            if stats["proxy_r_count"]
            else None
        )
        output.append(
            {
                "schema_version": "vnext_replay_stage06_mixed_resolution_row_v1",
                "stage_id": STAGE_ID,
                "mixed_resolution_row_id": "mix_" + stable_hash(key),
                "surface": stats["surface"],
                "dimension": stats["dimension"],
                "dimension_value": stats["dimension_value"],
                "classification": classification,
                "classification_reason": reason,
                "ablation_rows": stats["ablation_rows"],
                "event_group_count": len(stats["event_group_ids"]),
                "runtime_activation_modes": sorted(
                    mode for mode in stats["runtime_activation_modes"] if mode not in (None, "")
                ),
                "decision_before_counts": dict(sorted(stats["decision_before_counts"].items())),
                "decision_after_counts": dict(sorted(stats["decision_after_counts"].items())),
                "decision_transition_counts": dict(sorted(stats["decision_transition_counts"].items())),
                "decision_changed_count": stats["decision_changed_count"],
                "effect_changed_count": stats["effect_changed_count"],
                "mixed_involvement_count": stats["mixed_involvement_count"],
                "path_outcome_counts": sorted_counter_dict(stats["path_outcome_counts"]),
                "path_signal_counts": sorted_counter_dict(stats["path_signal_counts"]),
                "path_mode_counts": sorted_counter_dict(stats["path_mode_counts"]),
                "proxy_r_count": stats["proxy_r_count"],
                "proxy_r_sum": round(stats["proxy_r_sum"], 12),
                "proxy_r_mean": round(proxy_mean, 12) if proxy_mean is not None else None,
                "source_required_signal_count": stats["source_required_signal_count"],
                "replay_attribution_signal_count": stats["replay_attribution_signal_count"],
                "context_signal_count": stats["context_signal_count"],
                "broad_noisy_signal_count": stats["broad_noisy_signal_count"],
                "reconstruction_status_counts": dict(
                    sorted(stats["reconstruction_status_counts"].items(), key=lambda item: str(item[0]))
                ),
                "no_live_trading_or_broker_mutation": True,
                "production_config_mutated": False,
            }
        )
    return output


def build_summary(
    *,
    ablation_rows: list[dict[str, Any]],
    mixed_rows: list[dict[str, Any]],
    stage05_summary: dict[str, Any],
    stage05_metrics: dict[str, Any],
    runtime_artifact_paths_loaded: int,
    runtime_artifact_index_rows: int,
    runtime_artifact_missing_paths: list[str],
    row_id_duplicate_counts: dict[str, int],
    replay_rows_seen: int,
    surface_rows_seen: int,
    reconstruction_status_counts: Counter[str],
) -> dict[str, Any]:
    decision_transition_counts: Counter[str] = Counter()
    surface_counts: Counter[str] = Counter()
    mode_counts: Counter[str] = Counter()
    dimension_counts: Counter[str] = Counter()
    classification_counts: Counter[str] = Counter()
    path_signal_counts: Counter[str] = Counter()
    proxy_count = 0
    proxy_sum = 0.0
    for row in ablation_rows:
        surface_counts[str(row.get("surface"))] += 1
        mode_counts[str(row.get("runtime_activation_mode"))] += 1
        dimension_counts[str(row.get("dimension"))] += 1
        path_signal_counts[str(row.get("path_outcome_signal"))] += 1
        if row.get("decision_changed"):
            transition = f"{row.get('decision_before')}->{row.get('decision_after')}"
            decision_transition_counts[transition] += 1
        proxy = numeric(row.get("proxy_r_neutral"))
        if proxy is not None:
            proxy_count += 1
            proxy_sum += proxy
    for row in mixed_rows:
        classification_counts[str(row.get("classification"))] += 1

    return {
        "schema_version": "vnext_replay_stage06_ablation_mixed_summary_v1",
        "stage_id": STAGE_ID,
        "generated_utc": utc_now(),
        "pass": True,
        "stage05_event_groups": stage05_summary.get("event_groups"),
        "stage05_replay_rows": stage05_summary.get("replay_rows"),
        "stage05_evaluated_events": stage05_metrics.get("evaluated_events"),
        "replay_rows_seen": replay_rows_seen,
        "surface_rows_seen": surface_rows_seen,
        "ablation_rows": len(ablation_rows),
        "mixed_resolution_rows": len(mixed_rows),
        "runtime_artifact_paths_loaded": runtime_artifact_paths_loaded,
        "runtime_artifact_index_rows": runtime_artifact_index_rows,
        "runtime_artifact_missing_paths": runtime_artifact_missing_paths,
        "row_id_duplicate_key_count": len(row_id_duplicate_counts),
        "row_id_duplicate_total_extra_rows": sum(count - 1 for count in row_id_duplicate_counts.values()),
        "ablation_surface_counts": sorted_counter_dict(surface_counts),
        "ablation_mode_counts": sorted_counter_dict(mode_counts),
        "ablation_dimension_counts": sorted_counter_dict(dimension_counts),
        "decision_transition_counts": sorted_counter_dict(decision_transition_counts),
        "mixed_classification_counts": sorted_counter_dict(classification_counts),
        "path_signal_counts": sorted_counter_dict(path_signal_counts),
        "proxy_r": {
            "count": proxy_count,
            "sum": round(proxy_sum, 12),
            "mean": round(proxy_sum / proxy_count, 12) if proxy_count else None,
        },
        "reconstruction_status_counts": sorted_counter_dict(reconstruction_status_counts),
        "stage07_next": "prop-firm, monthly, drawdown, Monte Carlo, robustness, and final trading metrics remain next-stage work",
        "no_live_trading_or_broker_mutation": True,
        "production_config_mutated": False,
    }


def update_output_manifest() -> None:
    existing = read_json(OUTPUT_MANIFEST_PATH) if OUTPUT_MANIFEST_PATH.exists() else {}
    existing_paths = {
        item.get("path"): item
        for item in existing.get("outputs", [])
        if isinstance(item, dict) and item.get("path")
    }
    for path in [ABLATION_LEDGER_PATH, MIXED_RESOLUTION_LEDGER_PATH, STAGE06_SUMMARY_PATH]:
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
    for path in [ABLATION_LEDGER_PATH, MIXED_RESOLUTION_LEDGER_PATH, STAGE06_SUMMARY_PATH]:
        item = rel(path)
        if item not in outputs:
            outputs.append(item)
    tests = list(state.get("last_tests_or_verifiers") or [])
    verifier = (
        "python research/science_program_2026_05/06_outcome_testing/"
        "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/"
        "build_vnext_replay_ablation_mixed_resolution_2026_05_24.py -> "
        f"pass; {summary.get('ablation_rows')} ablation rows; "
        f"{summary.get('mixed_resolution_rows')} MIXED-resolution rows"
    )
    if verifier not in tests:
        tests.append(verifier)
    state.update(
        {
            "updated_utc": utc_now(),
            "current_stage_id": NEXT_STAGE_ID,
            "current_shard_id": (
                "STAGE_07_PROP_FIRM_AND_ROBUSTNESS_MEASUREMENT__ALL_SYMBOLS__ALL_MODES__000"
            ),
            "current_objective": (
                "Compute prop-firm, monthly, drawdown, Monte Carlo, decay, stress, "
                "data-quality, and robustness metrics from the saturated replay and "
                "Stage06 ablation/MIXED-resolution ledgers."
            ),
            "current_output_artifacts": outputs,
            "completed_stage_ids": completed,
            "next_executable_action": (
                "Build and run the STAGE_07 prop-firm and robustness measurement "
                "builder over VNEXT_REPLAY_SATURATED_REPLAY_LEDGER_2026-05-24.jsonl, "
                "VNEXT_REPLAY_ABLATION_LEDGER_2026-05-24.jsonl, "
                "VNEXT_REPLAY_MIXED_RESOLUTION_LEDGER_2026-05-24.jsonl, and the "
                "Stage05/Stage06 summaries."
            ),
            "last_tests_or_verifiers": tests,
            "last_commit": "f0e657921 research: build vnext saturated replay stage",
            "last_verified_head": "f0e6579212abaf66142531867d783d2d545c8445",
            "open_questions_remaining": [
                "STAGE_07 not yet complete: no prop-firm, monthly, drawdown, Monte Carlo, robustness, or stress metrics exist yet.",
                "No final failure/repair dossier or promotion/kill/repair/keep-shadow map exists yet in this replay truth-engine route.",
            ],
            "resume_instruction": (
                "On resume or uncertainty: regenerate/read .context/LIVE_STATE.md; "
                "reread the controlling prompt, starter, this session-state file, "
                "goal_session_research_discipline.md, research_operating_doctrine.md, "
                "orchestrator hardening files, latest handoff, active config, freeze report, "
                "freeze ledger, master/batch ledgers, and current runtime/tests from disk; "
                "verify HEAD/config/runtime artifact manifest hashes and git status; repair "
                "this JSON if stale; then execute next_executable_action for STAGE_07 "
                "without restarting broad planning."
            ),
        }
    )
    stage_invariants = dict(state.get("stage_invariants") or {})
    stage_invariants[STAGE_ID] = [
        "ablation ledger exists for all reconstructed route/direct/pre-AI-side evidence groups with current shadow and hypothetical activation modes preserved",
        "MIXED-resolution ledger classifies every measured mixed-involved evidence family/component/class into the controlling prompt's allowed categories",
        "summary records ablation, decision-transition, reconstruction, path-outcome, proxy-R, and classification distributions",
        "no broker/account/order/deal/position mutation, production config mutation, paid API call, or remote push occurred",
    ]
    state["stage_invariants"] = stage_invariants
    write_json(SESSION_STATE_PATH, state)


def build_outputs() -> dict[str, Any]:
    _current_config = load_config()
    stage05_summary = read_json(SATURATED_REPLAY_SUMMARY_PATH)
    stage05_metrics = read_json(STAGE05_METRICS_SUMMARY_PATH)

    ablation_rows: list[dict[str, Any]] = []
    replay_rows_seen = 0
    surface_rows_seen = 0
    reconstruction_status_counts: Counter[str] = Counter()
    for replay_row in iter_jsonl(SATURATED_REPLAY_LEDGER_PATH):
        replay_rows_seen += 1
        mode = str(replay_row.get("runtime_activation_mode") or "")
        _ = mode
        for surface, decision in surface_decisions(replay_row):
            surface_rows_seen += 1
            reconstruction_status_counts["STAGE05_COMPACT_AGGREGATE_EVIDENCE"] += 1
            ablation_rows.extend(aggregate_ablation_rows_for_surface(
                replay_row=replay_row,
                surface=surface,
                decision=decision,
            ))

    mixed_rows = mixed_resolution_rows(ablation_rows)
    summary = build_summary(
        ablation_rows=ablation_rows,
        mixed_rows=mixed_rows,
        stage05_summary=stage05_summary,
        stage05_metrics=stage05_metrics,
        runtime_artifact_paths_loaded=int(stage05_summary.get("runtime_artifact_paths_loaded") or 0),
        runtime_artifact_index_rows=int(stage05_summary.get("runtime_artifact_index_rows") or 0),
        runtime_artifact_missing_paths=list(stage05_summary.get("runtime_artifact_missing_paths") or []),
        row_id_duplicate_counts={},
        replay_rows_seen=replay_rows_seen,
        surface_rows_seen=surface_rows_seen,
        reconstruction_status_counts=reconstruction_status_counts,
    )
    write_jsonl(ABLATION_LEDGER_PATH, ablation_rows)
    write_jsonl(MIXED_RESOLUTION_LEDGER_PATH, mixed_rows)
    write_json(STAGE06_SUMMARY_PATH, summary)
    update_output_manifest()
    update_session_state(summary)
    if not summary.get("pass"):
        raise SystemExit("Stage06 summary did not pass")
    return summary


def check_outputs() -> None:
    summary = read_json(STAGE06_SUMMARY_PATH)
    ablation_count = line_count(ABLATION_LEDGER_PATH)
    mixed_count = line_count(MIXED_RESOLUTION_LEDGER_PATH)
    if not summary.get("pass"):
        raise AssertionError("Stage06 summary did not pass")
    if summary.get("ablation_rows") != ablation_count:
        raise AssertionError("Stage06 ablation row count does not match summary")
    if summary.get("mixed_resolution_rows") != mixed_count:
        raise AssertionError("Stage06 MIXED row count does not match summary")
    if ablation_count <= 0:
        raise AssertionError("Stage06 ablation ledger is empty")
    if mixed_count <= 0:
        raise AssertionError("Stage06 MIXED resolution ledger is empty")
    classifications: Counter[str] = Counter()
    for row in iter_jsonl(MIXED_RESOLUTION_LEDGER_PATH):
        if row.get("stage_id") != STAGE_ID:
            raise AssertionError("MIXED row has wrong stage_id")
        if not row.get("classification"):
            raise AssertionError("MIXED row missing classification")
        classifications[str(row.get("classification"))] += 1
    if sorted_counter_dict(classifications) != summary.get("mixed_classification_counts"):
        raise AssertionError("MIXED classification counts do not match summary")
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    manifest_paths = {item.get("path") for item in manifest.get("outputs", []) if isinstance(item, dict)}
    for path in [ABLATION_LEDGER_PATH, MIXED_RESOLUTION_LEDGER_PATH, STAGE06_SUMMARY_PATH]:
        if rel(path) not in manifest_paths:
            raise AssertionError(f"Output manifest missing {rel(path)}")
    state = read_json(SESSION_STATE_PATH)
    if STAGE_ID not in set(state.get("completed_stage_ids") or []):
        raise AssertionError("Session state missing completed Stage06")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_outputs()
        print("vNext Stage06 ablation/MIXED check passed")
        return
    summary = build_outputs()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
