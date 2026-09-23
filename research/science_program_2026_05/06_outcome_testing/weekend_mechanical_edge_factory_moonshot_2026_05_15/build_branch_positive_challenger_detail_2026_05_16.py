#!/usr/bin/env python3
"""Build accepted positive challenger detail from branch-local positive ledgers."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

NEXT_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_RESULT_2026-05-16.json"
NEXT_ACCEPTED = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_ACCEPTED_LEDGER_2026-05-16.jsonl"
NEXT_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_POSITIVE_LEDGER_2026-05-16.jsonl"
ACCEPTED_BUILDER_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_POSITIVE_RESULT_LEDGER_2026-05-16.jsonl"
SELECTOR_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_POSITIVE_REPLAY_REPAIR_LEDGER_2026-05-16.jsonl"
PARAM_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_POSITIVE_LEDGER_2026-05-16.jsonl"
ROUTER_SPEC_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_POSITIVE_LEDGER_2026-05-16.jsonl"
FOLLOWUP_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_POSITIVE_LEDGER_2026-05-16.jsonl"
SCORE_EXPORT_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_POSITIVE_REPLAY_LEDGER_2026-05-16.jsonl"
NEXT_COMPUTE_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_POSITIVE_REPLAY_LEDGER_2026-05-16.jsonl"
DEEP_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_DEEP_BRANCH_LEDGER_2026-05-16.jsonl"
SCOPE_COMPARISON = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_SCOPE_COMPARISON_LEDGER_2026-05-16.jsonl"
MODIFIER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CONTROL_CONCENTRATION_MODIFIER_LEDGER_2026-05-16.jsonl"
IMPLEMENTATION_CANDIDATE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-16.jsonl"
REPLAY_SPEC = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_REPLAY_SPEC_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_DETAIL"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_LEDGER_2026-05-16.jsonl"
ACCEPTED_LEDGER = ROUTE_DIR / f"{PREFIX}_ACCEPTED_DETAIL_LEDGER_2026-05-16.jsonl"
REPLAY_PROXY_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_NOW_PROXY_LEDGER_2026-05-16.jsonl"
EXACT_REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_REPAIR_LEDGER_2026-05-16.jsonl"
REPAIR_STRESS_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_STRESS_FIRST_LEDGER_2026-05-16.jsonl"
SIDECAR_LEDGER = ROUTE_DIR / f"{PREFIX}_SIDECAR_CONTEXT_LEDGER_2026-05-16.jsonl"
REJECTED_LEDGER = ROUTE_DIR / f"{PREFIX}_REJECTED_NONPOSITIVE_LEDGER_2026-05-16.jsonl"
MODIFIER_DETAIL_LEDGER = ROUTE_DIR / f"{PREFIX}_MODIFIER_DETAIL_LEDGER_2026-05-16.jsonl"
DEEP_CONTEXT_LEDGER = ROUTE_DIR / f"{PREFIX}_DEEP_CONTEXT_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Positive challenger detail packet only. It consumes accepted POSITIVE rows and "
    "full positive/deep context, computes replay-now proxy/exact-repair detail with "
    "control and concentration modifiers preserved, and keeps repair/sidecar/rejected "
    "rows in separate ledgers. It does not change live behavior and does not claim "
    "broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-POSITIVE-DETAIL-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": sha256_file(path),
                "status": "HASHED" if path.exists() else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def avg(values: list[float]) -> float | None:
    return round(mean(values), 6) if values else None


def by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["branch_queue_id"]: row for row in rows if row.get("branch_queue_id")}


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    row.update(
        {
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
    )
    return row


def positive_status_scope(status: str | None) -> str:
    if status == "POSITIVE_REPLAY_ACCEPTED_AFTER_MODIFIERS":
        return "ACCEPTED_PRIMARY_POSITIVE_EXECUTION_SCOPE"
    if status == "POSITIVE_REPAIR_OR_STRESS_REQUIRED_BEFORE_REPLAY":
        return "POSITIVE_REPAIR_STRESS_FIRST_SCOPE"
    if status == "POSITIVE_SIDE_CAR_CONTEXT_PRESERVED":
        return "POSITIVE_SIDECAR_CONTEXT_SCOPE"
    if status == "POSITIVE_REJECTED_OR_NONPOSITIVE":
        return "POSITIVE_REJECTED_NONPOSITIVE_SCOPE"
    return "POSITIVE_UNKNOWN_SCOPE"


def main() -> int:
    generated_at = now_utc()
    next_result = read_json(NEXT_RESULT)
    next_accepted_rows = read_jsonl(NEXT_ACCEPTED)
    next_positive_rows = read_jsonl(NEXT_POSITIVE)
    positive_result_rows = read_jsonl(ACCEPTED_BUILDER_POSITIVE)
    selector_rows = read_jsonl(SELECTOR_POSITIVE)
    param_rows = read_jsonl(PARAM_POSITIVE)
    router_spec_rows = read_jsonl(ROUTER_SPEC_POSITIVE)
    followup_rows = read_jsonl(FOLLOWUP_POSITIVE)
    score_export_rows = read_jsonl(SCORE_EXPORT_POSITIVE)
    next_compute_rows = read_jsonl(NEXT_COMPUTE_POSITIVE)
    deep_rows = read_jsonl(DEEP_POSITIVE)
    scope_rows_input = read_jsonl(SCOPE_COMPARISON)
    modifier_rows_input = read_jsonl(MODIFIER)
    implementation_rows = read_jsonl(IMPLEMENTATION_CANDIDATE)
    replay_spec_rows = read_jsonl(REPLAY_SPEC)
    accepted_positive_rows = [
        row
        for row in next_accepted_rows
        if row.get("primary_export_family") == "POSITIVE"
        and row.get("integrated_evidence_action") == "EXECUTE_POSITIVE_CHALLENGER_DETAIL_BUILDER"
    ]
    accepted_ids = {row["branch_queue_id"] for row in accepted_positive_rows}
    next_accepted_by_branch = by_id(accepted_positive_rows)
    next_positive_by_branch = by_id(next_positive_rows)
    positive_result_by_branch = by_id(positive_result_rows)
    selector_by_branch = by_id(selector_rows)
    param_by_branch = by_id(param_rows)
    router_by_branch = by_id(router_spec_rows)
    followup_by_branch = by_id(followup_rows)
    score_export_by_branch = by_id(score_export_rows)
    next_compute_by_branch = by_id(next_compute_rows)
    deep_by_branch = by_id(deep_rows)
    scope_by_branch = by_id(scope_rows_input)
    modifier_by_branch = by_id(modifier_rows_input)
    implementation_by_branch = by_id(implementation_rows)
    replay_spec_by_branch = by_id(replay_spec_rows)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            NEXT_RESULT,
            NEXT_ACCEPTED,
            NEXT_POSITIVE,
            ACCEPTED_BUILDER_POSITIVE,
            SELECTOR_POSITIVE,
            PARAM_POSITIVE,
            ROUTER_SPEC_POSITIVE,
            FOLLOWUP_POSITIVE,
            SCORE_EXPORT_POSITIVE,
            NEXT_COMPUTE_POSITIVE,
            DEEP_POSITIVE,
            SCOPE_COMPARISON,
            MODIFIER,
            IMPLEMENTATION_CANDIDATE,
            REPLAY_SPEC,
        ],
        generated_at,
    )

    scope_rows: list[dict[str, Any]] = []
    repair_stress_rows: list[dict[str, Any]] = []
    sidecar_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    modifier_detail_rows: list[dict[str, Any]] = []
    for row in positive_result_rows:
        branch_id = row.get("branch_queue_id")
        deep = deep_by_branch.get(branch_id, {})
        replay_spec = replay_spec_by_branch.get(branch_id, {})
        status = row.get("positive_builder_result_status")
        scope_class = positive_status_scope(status)
        out = {
            "positive_challenger_detail_scope_id": f"OHLC-GTOS-POSITIVE-DETAIL-SCOPE-{len(scope_rows) + 1:05d}",
            "branch_queue_id": branch_id,
            "scope_class": scope_class,
            "accepted_primary_positive": branch_id in accepted_ids,
            "route_candidate_id": row.get("route_candidate_id"),
            "route_session": row.get("route_session"),
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "entry_variant": row.get("entry_variant"),
            "target_stop_contract_id": row.get("target_stop_contract_id"),
            "positive_builder_result_status": status,
            "positive_selector_execution_status": row.get("positive_selector_execution_status"),
            "positive_replayable_now": row.get("positive_replayable_now"),
            "positive_deep_action_class": deep.get("positive_deep_action_class"),
            "positive_challenger_class": deep.get("positive_challenger_class"),
            "positive_replay_status": replay_spec.get("positive_replay_status"),
            "positive_adjusted_lower": row.get("positive_adjusted_lower"),
            "positive_adjusted_midpoint": row.get("positive_adjusted_midpoint"),
            "positive_modifier_penalty": row.get("positive_modifier_penalty"),
            "positive_control_delta_modifier_class": row.get("positive_control_delta_modifier_class"),
            "positive_concentration_modifier_class": row.get("positive_concentration_modifier_class"),
        }
        with_common(out, generated_at, manifest_hash)
        scope_rows.append(out)
        target_list: list[dict[str, Any]] | None = None
        id_field = None
        if status == "POSITIVE_REPAIR_OR_STRESS_REQUIRED_BEFORE_REPLAY":
            target_list = repair_stress_rows
            id_field = "positive_challenger_detail_repair_stress_id"
        elif status == "POSITIVE_SIDE_CAR_CONTEXT_PRESERVED":
            target_list = sidecar_rows
            id_field = "positive_challenger_detail_sidecar_id"
        elif status == "POSITIVE_REJECTED_OR_NONPOSITIVE":
            target_list = rejected_rows
            id_field = "positive_challenger_detail_rejected_id"
        if target_list is not None and id_field:
            side = dict(out)
            side[id_field] = f"OHLC-GTOS-POSITIVE-DETAIL-{id_field.rsplit('_', 1)[0].split('_')[-1].upper()}-{len(target_list) + 1:05d}"
            side.pop("positive_challenger_detail_scope_id", None)
            target_list.append(side)
        mod = modifier_by_branch.get(branch_id, {})
        modifier_detail = {
            "positive_challenger_detail_modifier_id": f"OHLC-GTOS-POSITIVE-DETAIL-MOD-{len(modifier_detail_rows) + 1:05d}",
            "branch_queue_id": branch_id,
            "scope_class": scope_class,
            "accepted_primary_positive": branch_id in accepted_ids,
            "route_candidate_id": row.get("route_candidate_id"),
            "route_session": row.get("route_session"),
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "entry_variant": row.get("entry_variant"),
            "target_stop_contract_id": row.get("target_stop_contract_id"),
            "positive_builder_result_status": status,
            "positive_replay_status": replay_spec.get("positive_replay_status"),
            "rstyle_lower_mean": deep.get("rstyle_lower_mean"),
            "rstyle_midpoint_mean": deep.get("rstyle_midpoint_mean"),
            "rstyle_upper_mean": deep.get("rstyle_upper_mean"),
            "positive_adjusted_lower": row.get("positive_adjusted_lower"),
            "positive_adjusted_midpoint": row.get("positive_adjusted_midpoint"),
            "positive_modifier_penalty": row.get("positive_modifier_penalty"),
            "positive_control_delta_modifier_class": row.get("positive_control_delta_modifier_class"),
            "positive_concentration_modifier_class": row.get("positive_concentration_modifier_class"),
            "positive_combined_modifier_class": deep.get("positive_combined_modifier_class") or mod.get("positive_combined_modifier_class"),
            "same_route_peer_count": deep.get("same_route_peer_count"),
            "same_route_peer_delta": deep.get("same_route_peer_delta"),
            "source_deep_action_class": next_positive_by_branch.get(branch_id, {}).get("source_deep_action_class"),
            "ordering_deep_action_class": next_positive_by_branch.get(branch_id, {}).get("ordering_deep_action_class"),
            "target_stop_result": deep.get("target_stop_result"),
        }
        with_common(modifier_detail, generated_at, manifest_hash)
        modifier_detail_rows.append(modifier_detail)

    accepted_detail_rows: list[dict[str, Any]] = []
    for accepted in accepted_positive_rows:
        branch_id = accepted["branch_queue_id"]
        positive_result = positive_result_by_branch.get(branch_id, {})
        selector = selector_by_branch.get(branch_id, {})
        param = param_by_branch.get(branch_id, {})
        router = router_by_branch.get(branch_id, {})
        followup = followup_by_branch.get(branch_id, {})
        score_export = score_export_by_branch.get(branch_id, {})
        next_compute = next_compute_by_branch.get(branch_id, {})
        deep = deep_by_branch.get(branch_id, {})
        scope = scope_by_branch.get(branch_id, {})
        mod = modifier_by_branch.get(branch_id, {})
        impl = implementation_by_branch.get(branch_id, {})
        replay_spec = replay_spec_by_branch.get(branch_id, {})
        replay_status = replay_spec.get("positive_replay_status")
        if replay_status == "REPLAYABLE_WITH_EXACT_REPAIR":
            detail_status = "POSITIVE_ACCEPTED_EXACT_REPAIR_DETAIL"
            next_action = "PRESERVE_EXACT_REPAIR_POSITIVE_CHALLENGER_WITH_MODIFIER_PENALTY"
        else:
            detail_status = "POSITIVE_ACCEPTED_M1_SPREAD_PROXY_DETAIL"
            next_action = "PRESERVE_M1_SPREAD_PROXY_POSITIVE_CHALLENGER_WITH_MODIFIER_PENALTY"
        out = {
            "positive_challenger_detail_id": f"OHLC-GTOS-POSITIVE-DETAIL-BRANCH-{len(accepted_detail_rows) + 1:05d}",
            "branch_queue_id": branch_id,
            "next_layer_evidence_branch_id": accepted.get("next_layer_evidence_branch_id"),
            "accepted_builder_branch_result_id": accepted.get("accepted_builder_branch_result_id"),
            "selector_execution_branch_id": accepted.get("selector_execution_branch_id"),
            "matrix_branch_id": accepted.get("matrix_branch_id") or positive_result.get("matrix_branch_id"),
            "positive_builder_result_id": positive_result.get("positive_builder_result_id"),
            "positive_selector_execution_id": selector.get("positive_selector_execution_id") or positive_result.get("positive_selector_execution_id"),
            "positive_parameter_id": param.get("positive_parameter_id") or positive_result.get("positive_parameter_id"),
            "positive_decision_id": positive_result.get("positive_decision_id") or selector.get("positive_decision_id"),
            "positive_challenger_replay_spec_id": replay_spec.get("positive_challenger_replay_spec_id"),
            "positive_challenger_deep_branch_id": deep.get("positive_challenger_deep_branch_id"),
            "route_candidate_id": accepted.get("route_candidate_id") or positive_result.get("route_candidate_id"),
            "route_session": accepted.get("route_session") or positive_result.get("route_session"),
            "symbol": accepted.get("symbol") or positive_result.get("symbol"),
            "side": accepted.get("side") or positive_result.get("side"),
            "entry_variant": accepted.get("entry_variant") or positive_result.get("entry_variant"),
            "target_stop_contract_id": accepted.get("target_stop_contract_id") or positive_result.get("target_stop_contract_id"),
            "primary_export_family": "POSITIVE",
            "branch_result_binary": accepted.get("branch_result_binary"),
            "branch_decision_class": accepted.get("branch_decision_class"),
            "accepted_for_next_executable_builder": accepted.get("accepted_for_next_executable_builder"),
            "integrated_evidence_action": accepted.get("integrated_evidence_action"),
            "integrated_evidence_state": accepted.get("integrated_evidence_state"),
            "integrated_evidence_score": accepted.get("integrated_evidence_score"),
            "positive_detail_status": detail_status,
            "next_same_resource_action": next_action,
            "positive_builder_result_status": positive_result.get("positive_builder_result_status"),
            "positive_builder_next_action": positive_result.get("positive_builder_next_action"),
            "positive_selector_execution_status": selector.get("positive_selector_execution_status") or positive_result.get("positive_selector_execution_status"),
            "positive_selector_policy": selector.get("positive_selector_policy"),
            "positive_selector_action": selector.get("positive_selector_action"),
            "positive_builder_policy": param.get("positive_builder_policy"),
            "positive_replay_status": replay_status,
            "positive_replay_note": replay_spec.get("positive_replay_note"),
            "positive_replayable_now": positive_result.get("positive_replayable_now"),
            "positive_challenger_class": deep.get("positive_challenger_class"),
            "positive_deep_action_class": deep.get("positive_deep_action_class"),
            "source_deep_action_class": accepted.get("source_deep_action_class"),
            "ordering_deep_action_class": accepted.get("ordering_deep_action_class"),
            "positive_control_delta_modifier_class": positive_result.get("positive_control_delta_modifier_class"),
            "positive_concentration_modifier_class": positive_result.get("positive_concentration_modifier_class"),
            "positive_combined_modifier_class": deep.get("positive_combined_modifier_class") or mod.get("positive_combined_modifier_class"),
            "positive_modifier_penalty": positive_result.get("positive_modifier_penalty"),
            "rstyle_lower_mean": deep.get("rstyle_lower_mean"),
            "rstyle_midpoint_mean": deep.get("rstyle_midpoint_mean"),
            "rstyle_upper_mean": deep.get("rstyle_upper_mean"),
            "positive_adjusted_lower": positive_result.get("positive_adjusted_lower"),
            "positive_adjusted_midpoint": positive_result.get("positive_adjusted_midpoint"),
            "positive_builder_score": positive_result.get("positive_builder_score"),
            "positive_builder_score_class": positive_result.get("positive_builder_score_class"),
            "positive_selector_score": selector.get("positive_selector_score"),
            "positive_selector_score_class": selector.get("positive_selector_score_class"),
            "same_route_peer_count": deep.get("same_route_peer_count"),
            "same_route_peer_delta": deep.get("same_route_peer_delta"),
            "implementation_prerequisite": deep.get("implementation_prerequisite"),
            "surface_mode": replay_spec.get("surface_mode") or impl.get("surface_mode"),
            "proposed_branch_local_code_surface": replay_spec.get("proposed_branch_local_code_surface") or impl.get("proposed_branch_local_code_surface"),
            "target_stop_result": accepted.get("target_stop_result") or deep.get("target_stop_result"),
            "sealed_proxy_class": accepted.get("sealed_proxy_class"),
            "exact_success_cause": accepted.get("exact_success_cause"),
            "exact_failure_cause": accepted.get("exact_failure_cause"),
            "exact_missing_geometry_or_source_reason": accepted.get("exact_missing_geometry_or_source_reason"),
            "scope_comparison_status": scope.get("positive_scope_comparison_status"),
            "followup_positive_status": followup.get("positive_followup_status"),
            "score_export_positive_status": score_export.get("positive_score_export_status"),
            "next_compute_positive_status": next_compute.get("positive_next_compute_status"),
            "router_spec_score": router.get("positive_spec_score"),
            "m15_exact_chronology_claim": False,
            "m1_exact_chronology_claim": False,
            "m1_tick_ordering_exact": False,
        }
        with_common(out, generated_at, manifest_hash)
        accepted_detail_rows.append(out)

    replay_proxy_rows = [
        row for row in accepted_detail_rows if row.get("positive_replay_status") == "REPLAYABLE_WITH_M1_SPREAD_ADJUSTED_PROXY"
    ]
    exact_repair_rows = [
        row for row in accepted_detail_rows if row.get("positive_replay_status") == "REPLAYABLE_WITH_EXACT_REPAIR"
    ]
    deep_context_rows = []
    for row in deep_rows:
        out = {
            "positive_challenger_detail_deep_context_id": f"OHLC-GTOS-POSITIVE-DETAIL-DEEP-{len(deep_context_rows) + 1:05d}",
            "branch_queue_id": row.get("branch_queue_id"),
            "route_candidate_id": row.get("route_candidate_id"),
            "route_session": row.get("route_session"),
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "entry_variant": row.get("entry_variant"),
            "target_stop_contract_id": row.get("target_stop_contract_id"),
            "positive_challenger_class": row.get("positive_challenger_class"),
            "positive_deep_action_class": row.get("positive_deep_action_class"),
            "positive_control_delta_modifier_class": row.get("positive_control_delta_modifier_class"),
            "positive_concentration_modifier_class": row.get("positive_concentration_modifier_class"),
            "same_route_peer_count": row.get("same_route_peer_count"),
            "same_route_peer_delta": row.get("same_route_peer_delta"),
            "target_stop_result": row.get("target_stop_result"),
            "scope_class": (
                "DEEP_CONTEXT_ACCEPTED_POSITIVE_SCOPE"
                if row.get("branch_queue_id") in accepted_ids
                else "DEEP_CONTEXT_NON_ACCEPTED_OR_CONTROL_SCOPE"
            ),
        }
        with_common(out, generated_at, manifest_hash)
        deep_context_rows.append(out)

    accepted_lowers = [as_float(row.get("positive_adjusted_lower")) for row in accepted_detail_rows]
    accepted_mids = [as_float(row.get("positive_adjusted_midpoint")) for row in accepted_detail_rows]
    accepted_lowers = [value for value in accepted_lowers if value is not None]
    accepted_mids = [value for value in accepted_mids if value is not None]
    bucket_sources = {
        "scope_class": Counter(row.get("scope_class") for row in scope_rows),
        "accepted_symbol": Counter(row.get("symbol") for row in accepted_detail_rows),
        "accepted_route_session": Counter(row.get("route_session") for row in accepted_detail_rows),
        "accepted_side": Counter(row.get("side") for row in accepted_detail_rows),
        "accepted_entry_variant": Counter(row.get("entry_variant") for row in accepted_detail_rows),
        "accepted_target_stop_result": Counter(row.get("target_stop_result") for row in accepted_detail_rows),
        "accepted_positive_deep_action_class": Counter(row.get("positive_deep_action_class") for row in accepted_detail_rows),
        "accepted_positive_challenger_class": Counter(row.get("positive_challenger_class") for row in accepted_detail_rows),
        "accepted_positive_replay_status": Counter(row.get("positive_replay_status") for row in accepted_detail_rows),
        "accepted_source_deep_action_class": Counter(row.get("source_deep_action_class") for row in accepted_detail_rows),
        "accepted_ordering_deep_action_class": Counter(row.get("ordering_deep_action_class") for row in accepted_detail_rows),
        "accepted_positive_control_delta_modifier_class": Counter(row.get("positive_control_delta_modifier_class") for row in accepted_detail_rows),
        "accepted_positive_concentration_modifier_class": Counter(row.get("positive_concentration_modifier_class") for row in accepted_detail_rows),
        "accepted_positive_modifier_penalty": Counter(row.get("positive_modifier_penalty") for row in accepted_detail_rows),
        "positive_builder_result_status": Counter(row.get("positive_builder_result_status") for row in positive_result_rows),
        "positive_selector_execution_status": Counter(row.get("positive_selector_execution_status") for row in selector_rows),
        "positive_builder_policy": Counter(row.get("positive_builder_policy") for row in param_rows),
        "deep_positive_challenger_class": Counter(row.get("positive_challenger_class") for row in deep_rows),
    }
    bucket_rows = []
    for category, counter in sorted(bucket_sources.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-POSITIVE-DETAIL-BUCKET-{len(bucket_rows) + 1:05d}",
                        "bucket_category": category,
                        "bucket": str(bucket),
                        "row_count": int(count),
                        "share": round(count / total, 9) if total else None,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    question_rows = [
        {
            "question_id": "OHLC-GTOS-POSITIVE-DETAIL-QUESTION-001",
            "question": "Which accepted POSITIVE rows are M1 spread proxy versus exact-repair replay candidates?",
            "answer_route": "Use accepted detail positive_replay_status and replay/exact ledgers.",
        },
        {
            "question_id": "OHLC-GTOS-POSITIVE-DETAIL-QUESTION-002",
            "question": "Which modifier penalties remain attached to accepted positive challengers?",
            "answer_route": "Use modifier detail rows and accepted modifier buckets.",
        },
        {
            "question_id": "OHLC-GTOS-POSITIVE-DETAIL-QUESTION-003",
            "question": "Which full positive rows are not accepted and why are they preserved?",
            "answer_route": "Use repair/stress-first, sidecar, and rejected/nonpositive ledgers.",
        },
        {
            "question_id": "OHLC-GTOS-POSITIVE-DETAIL-QUESTION-004",
            "question": "What is the next executable queue after positive detail?",
            "answer_route": "Continue entry/adverse redesign detail and SOURCE upgraded/degraded implication split builders.",
        },
    ]
    for row in question_rows:
        with_common(row, generated_at, manifest_hash)

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_DETAIL",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_next_accepted_rows": len(next_accepted_rows),
            "input_next_accepted_positive_rows": len(accepted_positive_rows),
            "input_next_positive_rows": len(next_positive_rows),
            "input_positive_result_rows": len(positive_result_rows),
            "input_selector_positive_rows": len(selector_rows),
            "input_parameter_positive_rows": len(param_rows),
            "input_router_spec_positive_rows": len(router_spec_rows),
            "input_followup_positive_rows": len(followup_rows),
            "input_score_export_positive_rows": len(score_export_rows),
            "input_next_compute_positive_rows": len(next_compute_rows),
            "input_deep_positive_rows": len(deep_rows),
            "input_scope_comparison_rows": len(scope_rows_input),
            "input_modifier_rows": len(modifier_rows_input),
            "input_implementation_candidate_rows": len(implementation_rows),
            "input_replay_spec_rows": len(replay_spec_rows),
            "scope_rows": len(scope_rows),
            "accepted_detail_rows": len(accepted_detail_rows),
            "replay_now_proxy_rows": len(replay_proxy_rows),
            "exact_repair_rows": len(exact_repair_rows),
            "repair_stress_first_rows": len(repair_stress_rows),
            "sidecar_context_rows": len(sidecar_rows),
            "rejected_nonpositive_rows": len(rejected_rows),
            "modifier_detail_rows": len(modifier_detail_rows),
            "deep_context_rows": len(deep_context_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_next_counts": next_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_sources.items())},
        "accepted_score_stats": {
            "positive_adjusted_lower_min": round(min(accepted_lowers), 6) if accepted_lowers else None,
            "positive_adjusted_lower_max": round(max(accepted_lowers), 6) if accepted_lowers else None,
            "positive_adjusted_lower_mean": avg(accepted_lowers),
            "positive_adjusted_midpoint_min": round(min(accepted_mids), 6) if accepted_mids else None,
            "positive_adjusted_midpoint_max": round(max(accepted_mids), 6) if accepted_mids else None,
            "positive_adjusted_midpoint_mean": avg(accepted_mids),
        },
        "system_decision": {
            "system_recommendation": (
                "POSITIVE_CHALLENGER_DETAIL_RESULT: preserve 43 accepted modifier-penalized "
                "positive challengers, split M1-spread-proxy and exact-repair replay rows, "
                "keep repair/stress-first, sidecar, and nonpositive rows separate, and "
                "continue entry/adverse plus SOURCE implication detail builders."
            ),
            "accepted_primary_positive_rows": len(accepted_detail_rows),
            "replay_now_proxy_rows": len(replay_proxy_rows),
            "exact_repair_rows": len(exact_repair_rows),
            "repair_stress_first_rows": len(repair_stress_rows),
            "sidecar_context_rows": len(sidecar_rows),
            "rejected_nonpositive_rows": len(rejected_rows),
            "deep_context_rows": len(deep_context_rows),
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (SCOPE_LEDGER, scope_rows),
        (ACCEPTED_LEDGER, accepted_detail_rows),
        (REPLAY_PROXY_LEDGER, replay_proxy_rows),
        (EXACT_REPAIR_LEDGER, exact_repair_rows),
        (REPAIR_STRESS_LEDGER, repair_stress_rows),
        (SIDECAR_LEDGER, sidecar_rows),
        (REJECTED_LEDGER, rejected_rows),
        (MODIFIER_DETAIL_LEDGER, modifier_detail_rows),
        (DEEP_CONTEXT_LEDGER, deep_context_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]
    for path, rows in outputs:
        write_jsonl(path, rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch Positive Challenger Detail",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Full positive scope rows: `{len(scope_rows)}`",
                f"- Accepted positive rows: `{len(accepted_detail_rows)}`",
                f"- M1 spread proxy replay rows: `{len(replay_proxy_rows)}`",
                f"- Exact repair replay rows: `{len(exact_repair_rows)}`",
                f"- Repair/stress-first rows: `{len(repair_stress_rows)}`",
            ]
        ),
        encoding="utf-8",
    )
    manifest = read_json(OUTPUT_MANIFEST) if OUTPUT_MANIFEST.exists() else {"schema": "weekend_mechanical_edge_factory_output_manifest_v1", "artifacts": []}
    output_paths = [RESULT_PATH, SUMMARY_PATH] + [path for path, _rows in outputs]
    path_strings = {path.relative_to(REPO).as_posix() for path in output_paths}
    manifest["artifacts"] = [item for item in manifest.get("artifacts", []) if item.get("path") not in path_strings]
    for path in output_paths:
        manifest["artifacts"].append(
            {
                "path": path.relative_to(REPO).as_posix(),
                "status": "created",
                "type": "branch_positive_challenger_detail",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["safe_flags"] = SAFE_FLAGS
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "branch_positive_challenger_detail_built",
                    "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
                    "artifact": RESULT_PATH.relative_to(REPO).as_posix(),
                    "counts": result["counts"],
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "not_completion": True,
                },
                sort_keys=True,
            )
            + "\n"
        )
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
