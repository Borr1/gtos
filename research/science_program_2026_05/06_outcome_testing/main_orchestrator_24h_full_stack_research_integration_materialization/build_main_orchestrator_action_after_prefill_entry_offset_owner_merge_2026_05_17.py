"""Merge prefill source rows into the entry-offset proxy owner.

The current action ledger contains prefill rows that correctly reference
ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER as the proxy-R owner, but still carry
standalone IMPLEMENT_DEFAULT_OFF prefill labels with no counted proxy. This
builder removes that duplicate implementation surface: near-miss rows become
entry-offset-owned KEEP/merge rows, far-miss rows become entry-offset-owned
redesign components, and all linked proxy-R remains referenced but not counted
twice.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_COST_DETAIL_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_COST_DETAIL_REPAIR_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_ENTRY_OFFSET_OWNER_MERGE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_ENTRY_OFFSET_OWNER_MERGE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_ENTRY_OFFSET_OWNER_MERGE_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

OWNER = "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"
TARGET_SURFACE = "prefill_delivery_after_entry_offset_repair_decision"
OLD_FAR_BRANCH = "IMPLEMENT_DEFAULT_OFF_PREFILL_FAR_MISS_RETEST_CONTROL_CHALLENGER"
OLD_NEAR_BRANCH = "IMPLEMENT_DEFAULT_OFF_PREFILL_NEAR_MISS_ENTRY_OFFSET_050R_CHALLENGER"
FAR_BRANCH = "REDESIGN_PREFILL_FAR_MISS_RETEST_CONTROL_MERGED_INTO_ENTRY_OFFSET_050R"
NEAR_BRANCH = "MERGE_PREFILL_NEAR_MISS_INTO_ENTRY_OFFSET_050R_IMPLEMENTATION"
PROXY_COUNTING = "PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_NOT_DUPLICATED"
ENTRY_OFFSET_OWNER_SURFACE = "entry_offset_m15_hard_no_fill_repair"
STANDALONE_FVG_NEGATIVE_BRANCH = "REDESIGN_STANDALONE_FVG_POI_SCORER_CURRENT_PROXY_NEGATIVE_SMALL_N"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_no"] = line_no
                rows.append(row)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    total = round(sum(values), 8)
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": total,
        "proxy_r_mean": round(total / len(values), 8) if values else None,
        "positive_rows": sum(value > 0 for value in values),
        "zero_rows": sum(value == 0 for value in values),
        "negative_rows": sum(value < 0 for value in values),
    }


def action_delta(before: Counter[str], after: Counter[str]) -> dict[str, int]:
    keys = sorted(set(before) | set(after))
    return {
        key: int(after.get(key, 0)) - int(before.get(key, 0))
        for key in keys
        if int(after.get(key, 0)) != int(before.get(key, 0))
    }


def target_row(row: dict[str, Any]) -> bool:
    return (
        row.get("source_capture_surface") == TARGET_SURFACE
        and row.get("action_class") == "IMPLEMENT_DEFAULT_OFF"
        and row.get("after_proxy_r") is None
        and row.get("branch_decision") in {OLD_FAR_BRANCH, OLD_NEAR_BRANCH}
        and (
            row.get("linked_entry_offset_proxy_r_owner") == OWNER
            or row.get("linked_prefill_proxy_r_owner") == OWNER
        )
    )


def linked_proxy_r(row: dict[str, Any]) -> float:
    for field in (
        "linked_entry_offset_after_proxy_r",
        "linked_entry_offset_selected_proxy_r",
        "linked_prefill_after_proxy_r",
    ):
        value = safe_float(row.get(field))
        if value is not None:
            return value
    raise ValueError(f"Target row missing linked proxy reference: {row.get('row_id')}")


def owner_rows_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    owners: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("source_capture_surface") != ENTRY_OFFSET_OWNER_SURFACE:
            continue
        cid = str(row.get("candidate_id") or "")
        if cid:
            owners[cid] = row
    return owners


def source_artifact(row: dict[str, Any]) -> str | None:
    artifact = row.get("source_artifact")
    if artifact:
        return str(artifact)
    detail = row.get("source_cost_detail_source")
    if isinstance(detail, dict):
        artifact = detail.get("source_cost_detail_artifact") or detail.get("source_m15_artifact")
        if artifact:
            return str(artifact)
    return None


def row_proxy_reference(row: dict[str, Any]) -> float | None:
    for field in (
        "after_proxy_r",
        "prefill_proxy_reference_r",
        "linked_entry_offset_after_proxy_r",
        "linked_entry_offset_selected_proxy_r",
        "linked_prefill_after_proxy_r",
        "ordering_proxy_midpoint_r",
    ):
        value = safe_float(row.get(field))
        if value is not None:
            return value
    return None


def attach_opportunity_preservation(
    row: dict[str, Any],
    *,
    status: str,
    owner_row_id: str | None,
    owner_source_artifact: str | None,
    proxy_reference: float | None,
    proxy_reference_status: str,
    not_independently_countable_reason: str,
    useful_mechanism: str,
    downstream_paths: list[str],
) -> None:
    row["opportunity_preservation_status"] = status
    row["opportunity_owner_row_id"] = owner_row_id
    row["opportunity_owner_source_artifact"] = owner_source_artifact
    row["opportunity_proxy_r_reference"] = proxy_reference
    row["opportunity_proxy_reference_status"] = proxy_reference_status
    row["opportunity_not_independently_countable_reason"] = not_independently_countable_reason
    row["opportunity_useful_mechanism"] = useful_mechanism
    row["opportunity_downstream_paths"] = downstream_paths
    row["underlying_intelligence_preserved"] = True


def not_killed_audit(row: dict[str, Any], *, preserve_as: str, next_route: str) -> dict[str, Any]:
    return {
        "kill_scope": "NOT_KILLED_MERGED_ENTRY_OFFSET_OWNER",
        "current_claim": str(row.get("branch_decision") or ""),
        "unsupported_reason": "DUPLICATE_PREFILL_IMPLEMENTATION_LABEL_WITH_PROXY_R_OWNED_BY_ENTRY_OFFSET_SCORER",
        "what_was_tried": "LINKED_PREFILL_METADATA_TO_SPREAD_AWARE_ENTRY_OFFSET_050R_PROXY_R",
        "what_could_make_it_work": (
            "STANDALONE_PREFILL_FILL_AND_TERMINAL_PATH_CONTRACT_WITH_OWN_NON_DUPLICATE_R"
        ),
        "preserve_as": preserve_as,
        "next_route": next_route,
        "path_status": {
            "linked_proxy_r_owner": OWNER,
            "proxy_counting_decision": PROXY_COUNTING,
            "linked_proxy_r": linked_proxy_r(row),
        },
    }


def merge_far(row: dict[str, Any], owner: dict[str, Any] | None) -> None:
    reference = linked_proxy_r(row)
    row["action_class"] = "REDESIGN"
    row["branch_decision"] = FAR_BRANCH
    row["current_action"] = FAR_BRANCH
    row["strategy_status"] = FAR_BRANCH
    row["score_status"] = "METADATA_MERGED_TO_ENTRY_OFFSET_SCORER"
    row["outcome_status"] = "LINKED_ENTRY_OFFSET_TP1_AFTER_SHIFT_FILL"
    row["decision_evidence"] = "PREFILL_FAR_MISS_LINKED_ENTRY_OFFSET_050R_TP_PROXY_OWNER_MERGE"
    row["scoring_boundary"] = "PREFILL_METADATA_ONLY_LINKED_ENTRY_OFFSET_PROXY_NO_DUPLICATE_R"
    row["implementation_candidate"] = "MERGE_PREFILL_FAR_MISS_CONTEXT_INTO_ENTRY_OFFSET_050R_RETEST_CONTROL_REDESIGN"
    row["prefill_entry_offset_owner_merge_decision"] = "REDESIGN_COMPONENT_MERGED_INTO_ENTRY_OFFSET_050R"
    attach_opportunity_preservation(
        row,
        status="PREFILL_OPPORTUNITY_PRESERVED_AS_ENTRY_OFFSET_OWNER_MERGE_REDESIGN",
        owner_row_id=str(owner.get("row_id")) if owner else None,
        owner_source_artifact=source_artifact(owner or row),
        proxy_reference=reference,
        proxy_reference_status="REFERENCE_ONLY_NOT_COUNTED_DUPLICATE_ENTRY_OFFSET_OWNER",
        not_independently_countable_reason=(
            "Prefill TP-after-fill evidence reuses the entry-offset 0.50R scorer path; counting it as a "
            "standalone prefill implementation would duplicate the same proxy-R."
        ),
        useful_mechanism=(
            "Far-miss adverse reversal delivery can still inform wider retest offsets, market-control "
            "filters, avoid/inverse conditions, and entry-offset-owned retest-control design."
        ),
        downstream_paths=["entry-offset merge", "redesign", "avoid/inverse", "context feature", "broader system component"],
    )
    row["missed_opportunity_audit"] = not_killed_audit(
        row,
        preserve_as="FAR_MISS_RETEST_CONTROL_COMPONENT_INSIDE_ENTRY_OFFSET_050R_REDESIGN",
        next_route="TEST_WIDER_RETEST_OFFSETS_AND_MARKET_CONTROL_BUCKETS_WITH_ENTRY_OFFSET_PROXY_OWNER",
    )


def merge_near(row: dict[str, Any], owner: dict[str, Any] | None) -> None:
    reference = linked_proxy_r(row)
    row["action_class"] = "KEEP"
    row["branch_decision"] = NEAR_BRANCH
    row["current_action"] = NEAR_BRANCH
    row["strategy_status"] = "MERGED_PREFILL_NEAR_MISS_ENTRY_OFFSET_050R_CHALLENGER"
    row["score_status"] = "METADATA_MERGED_TO_ENTRY_OFFSET_SCORER"
    row["outcome_status"] = "LINKED_ENTRY_OFFSET_TP1_AFTER_SHIFT_FILL"
    row["decision_evidence"] = "PREFILL_NEAR_MISS_LINKED_ENTRY_OFFSET_050R_TP_PROXY_OWNER_MERGE"
    row["scoring_boundary"] = "PREFILL_METADATA_ONLY_LINKED_ENTRY_OFFSET_PROXY_NO_DUPLICATE_R"
    row["implementation_candidate"] = "MERGE_PREFILL_NEAR_MISS_CONTEXT_INTO_ENTRY_OFFSET_050R_SCORER"
    row["prefill_entry_offset_owner_merge_decision"] = "KEEP_AS_ENTRY_OFFSET_050R_IMPLEMENTATION_CONTEXT"
    attach_opportunity_preservation(
        row,
        status="PREFILL_OPPORTUNITY_PRESERVED_AS_ENTRY_OFFSET_OWNER_MERGE_CONTEXT",
        owner_row_id=str(owner.get("row_id")) if owner else None,
        owner_source_artifact=source_artifact(owner or row),
        proxy_reference=reference,
        proxy_reference_status="REFERENCE_ONLY_NOT_COUNTED_DUPLICATE_ENTRY_OFFSET_OWNER",
        not_independently_countable_reason=(
            "Near-miss prefill evidence is source context for the entry-offset 0.50R scorer; it has no "
            "independent fill/terminal contract with non-duplicate R."
        ),
        useful_mechanism=(
            "Near-miss prefill delivery remains useful as a context feature and merge component inside "
            "the entry-offset scorer."
        ),
        downstream_paths=["entry-offset merge", "context feature", "broader system component"],
    )
    row["missed_opportunity_audit"] = not_killed_audit(
        row,
        preserve_as="NEAR_MISS_PREFILL_CONTEXT_INSIDE_ENTRY_OFFSET_050R_IMPLEMENTATION",
        next_route="CONSUME_NEAR_MISS_PREFILL_CONTEXT_IN_ENTRY_OFFSET_050R_SCORER_FEATURES",
    )


def standalone_fvg_negative_audit(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "kill_scope": "NOT_KILLED_CURRENT_STANDALONE_FVG_CLAIM_REDESIGN",
        "current_claim": STANDALONE_FVG_NEGATIVE_BRANCH,
        "unsupported_reason": "CURRENT_STANDALONE_FVG_POI_SHARED_PATH_PROXY_NEGATIVE_SMALL_N",
        "what_was_tried": (
            "Selected FVG POI geometry was repaired and scored with current shared candidate-path proxy evidence."
        ),
        "what_could_make_it_work": (
            "Exact standalone FVG entry-lock/reentry path, source-safe fill ordering, cost/spread accounting, "
            "and condition splits such as tighter target, shorter horizon, session, side, or market regime."
        ),
        "preserve_as": (
            "STANDALONE_FVG_ENTRY_SELECTOR_REDESIGN_CONTEXT_FEATURE_OR_SPECIALIZED_COMPONENT"
        ),
        "next_route": (
            "DESIGN_STANDALONE_FVG_ENTRY_LOCK_REENTRY_SCORER_WITH_TIGHTER_TARGET_SHORTER_HORIZON_AND_CONTEXT_SPLITS"
        ),
        "path_status": {
            "proxy_r_reference": row_proxy_reference(row),
            "score_status": row.get("after_score_status"),
            "strategy_status": row.get("after_strategy_status"),
            "selected_poi_type": row.get("standalone_fvg_poi_type"),
            "fvg_gap_timeframes": row.get("standalone_fvg_matching_gap_timeframes"),
        },
    }


def repair_standalone_fvg_negative(row: dict[str, Any]) -> None:
    proxy_reference = row_proxy_reference(row)
    attach_opportunity_preservation(
        row,
        status="STANDALONE_FVG_NEGATIVE_SMALL_N_OPPORTUNITY_PRESERVED_AS_REDESIGN",
        owner_row_id=str(row.get("row_id") or ""),
        owner_source_artifact=source_artifact(row),
        proxy_reference=proxy_reference,
        proxy_reference_status=(
            "COUNTED_AS_NEGATIVE_REDESIGN_EVIDENCE_NOT_STANDALONE_IMPLEMENTATION"
            if proxy_reference is not None
            else "NO_NUMERIC_PROXY_AVAILABLE_AMBIGUOUS_OR_SOURCE_BOUND_ROW"
        ),
        not_independently_countable_reason=(
            "The current standalone-FVG POI claim has negative small-N shared-path proxy evidence and still lacks "
            "a distinct FVG entry-lock/reentry/fill-cost contract."
        ),
        useful_mechanism=(
            "Selected FVG POI geometry can still become a tighter-entry selector, shorter-horizon path, "
            "context feature, avoid/inverse filter, or component in a broader structural/FVG system."
        ),
        downstream_paths=[
            "redesign",
            "avoid/inverse",
            "context feature",
            "source requirement",
            "tighter target",
            "shorter horizon",
            "broader system component",
        ],
    )
    row["missed_opportunity_audit"] = standalone_fvg_negative_audit(row)


def source_requirement_reason(row: dict[str, Any]) -> tuple[str, str, list[str]]:
    branch = str(row.get("branch_decision") or "")
    if "SWING_PROTECTED" in branch:
        return (
            "Swing-protected stop geometry remains useful but is not independently countable until the protected "
            "swing source/fill path is captured for this row.",
            "Swing-protected stop can become a context feature, source requirement, or structural stop component.",
            ["source requirement", "context feature", "broader system component"],
        )
    if "FVG_OB" in branch:
        return (
            "FVG/OB both-fire bucket lacks exact FVG/OB bounds and entry-lock source, so shared-path R is only a "
            "reference until the exact confluence contract exists.",
            "FVG/OB both-fire remains a confluence component requiring exact bounds before standalone scoring.",
            ["source requirement", "redesign", "broader system component"],
        )
    if "STRUCTURAL_METADATA_LTF" in branch:
        return (
            "Structural metadata is repaired, but same-M1 tick ordering is still unresolved; no stronger R claim is "
            "independent without tighter tick order.",
            "Structural lock/reentry evidence remains useful with a shorter-horizon/tick-order source requirement.",
            ["source requirement", "shorter horizon", "broader system component"],
        )
    if "SOURCE" in branch:
        return (
            "SOURCE branch evidence is interval-bound or no-scalar; it is not independently countable until exact "
            "source/cost/fill ordering is repaired.",
            "SOURCE cost/spread/bar-proxy intelligence remains useful for exact-source repair, avoid/inverse filters, "
            "and market/session-specific redesign.",
            ["source requirement", "redesign", "avoid/inverse", "context feature", "broader system component"],
        )
    return (
        "Current source requirement lacks enough source/cost/fill data for an independent countable scorer claim.",
        "The row remains useful as a source requirement and broader-system component.",
        ["source requirement", "broader system component"],
    )


def repair_source_requirement(row: dict[str, Any]) -> None:
    reason, mechanism, downstream_paths = source_requirement_reason(row)
    proxy_reference = row_proxy_reference(row)
    attach_opportunity_preservation(
        row,
        status="SOURCE_REQUIREMENT_OPPORTUNITY_PRESERVED",
        owner_row_id=str(row.get("row_id") or ""),
        owner_source_artifact=source_artifact(row),
        proxy_reference=proxy_reference,
        proxy_reference_status=(
            "REFERENCE_INTERVAL_OR_PROXY_NOT_IMPLEMENTATION"
            if proxy_reference is not None
            else "NO_NUMERIC_PROXY_AVAILABLE_SOURCE_REQUIREMENT"
        ),
        not_independently_countable_reason=reason,
        useful_mechanism=mechanism,
        downstream_paths=downstream_paths,
    )
    if not isinstance(row.get("missed_opportunity_audit"), dict):
        row["missed_opportunity_audit"] = {
            "kill_scope": "NOT_KILLED_SOURCE_REQUIREMENT_PRESERVED",
            "current_claim": str(row.get("branch_decision") or ""),
            "unsupported_reason": "CURRENT_ROW_REQUIRES_SOURCE_COST_FILL_REPAIR_BEFORE_IMPLEMENTABLE_R",
            "what_was_tried": str(row.get("decision_evidence") or "CURRENT_SOURCE_REPAIR_OR_REQUIREMENT_RECOMPUTE"),
            "what_could_make_it_work": (
                "Exact source/cost/fill/tick-order repair or a redesigned scorer with a non-duplicate source contract."
            ),
            "preserve_as": mechanism,
            "next_route": "REPAIR_EXACT_SOURCE_COST_FILL_ORDER_OR_CONSUME_AS_CONTEXT_AVOID_REDESIGN_FEATURE",
            "path_status": {
                "proxy_r_reference": proxy_reference,
                "proxy_reference_status": row.get("opportunity_proxy_reference_status"),
                "source_artifact": source_artifact(row),
            },
        }


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    source_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    before_counts = Counter(str(row.get("action_class") or "") for row in source_rows)
    before_proxy = proxy_summary(source_rows)
    owner_index = owner_rows_by_candidate(source_rows)

    output_rows: list[dict[str, Any]] = []
    touched_rows: list[dict[str, Any]] = []
    weak_fvg_rows: list[dict[str, Any]] = []
    source_requirement_rows: list[dict[str, Any]] = []
    source_requirement_audit_repairs = 0
    reference_values: list[float] = []

    for row in source_rows:
        new = dict(row)
        new.pop("_source_line_no", None)
        if not target_row(row):
            new["prefill_entry_offset_owner_merge_status"] = "NOT_TARGET_ROW"
            if new.get("branch_decision") == STANDALONE_FVG_NEGATIVE_BRANCH:
                repair_standalone_fvg_negative(new)
                weak_fvg_rows.append(new)
            if new.get("action_class") == "PRESERVE_REQUIREMENT":
                had_audit = isinstance(new.get("missed_opportunity_audit"), dict)
                repair_source_requirement(new)
                if not had_audit:
                    source_requirement_audit_repairs += 1
                source_requirement_rows.append(new)
            output_rows.append(new)
            continue

        reference = linked_proxy_r(row)
        reference_values.append(reference)
        owner = owner_index.get(str(row.get("candidate_id") or ""))
        new["before_prefill_owner_merge_action_class"] = row.get("action_class")
        new["before_prefill_owner_merge_branch_decision"] = row.get("branch_decision")
        new["before_prefill_owner_merge_current_action"] = row.get("current_action")
        new["before_prefill_owner_merge_after_proxy_r"] = row.get("after_proxy_r")
        new["prefill_entry_offset_owner_merge_status"] = "MERGED_TO_ENTRY_OFFSET_PROXY_OWNER"
        new["prefill_proxy_reference_r"] = reference
        new["prefill_proxy_reference_owner"] = OWNER
        new["prefill_proxy_counting_decision"] = PROXY_COUNTING
        new["prefill_owner_merge_generated_utc"] = generated
        new["safe_flags"] = SAFE_FLAGS
        new["no_live_behavior"] = True
        new["no_shadow_log_append"] = True

        if row.get("branch_decision") == OLD_FAR_BRANCH:
            merge_far(new, owner)
        elif row.get("branch_decision") == OLD_NEAR_BRANCH:
            merge_near(new, owner)
        else:
            raise ValueError(f"Unexpected target branch: {row.get('branch_decision')}")

        touched_rows.append(new)
        output_rows.append(new)

    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    after_proxy = proxy_summary(output_rows)
    target_counts = Counter(str(row.get("branch_decision") or "") for row in touched_rows)
    rows_with_audit = sum(isinstance(row.get("missed_opportunity_audit"), dict) for row in output_rows)
    rows_with_opportunity_preserved = sum(
        row.get("underlying_intelligence_preserved") is True for row in output_rows
    )
    source_requirement_values = [
        value for row in source_requirement_rows if (value := row_proxy_reference(row)) is not None
    ]
    weak_fvg_values = [value for row in weak_fvg_rows if (value := row_proxy_reference(row)) is not None]
    summary = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated,
        "input_ledger": str(INPUT_LEDGER),
        "input_summary": str(INPUT_SUMMARY),
        "input_rows": input_summary.get("rows"),
        "rows": len(output_rows),
        "exact_r_rows": 0,
        "safe_flags": SAFE_FLAGS,
        "target_rows": len(touched_rows),
        "rows_owner_merged": len(touched_rows),
        "far_miss_rows_merged_to_redesign": target_counts.get(FAR_BRANCH, 0),
        "near_miss_rows_merged_to_entry_offset": target_counts.get(NEAR_BRANCH, 0),
        "rows_removed_from_standalone_implementation": len(touched_rows),
        "rows_preserved_as_entry_offset_owned": len(touched_rows),
        "reference_proxy_numeric_rows": len(reference_values),
        "reference_proxy_r_sum_not_counted": round(sum(reference_values), 8),
        "reference_proxy_r_mean_not_counted": (
            round(sum(reference_values) / len(reference_values), 8) if reference_values else None
        ),
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "numeric_proxy_row_delta": after_proxy["numeric_proxy_rows"] - before_proxy["numeric_proxy_rows"],
        "action_class_counts_before": dict(sorted(before_counts.items())),
        "action_class_counts_after": dict(sorted(after_counts.items())),
        "action_class_delta_vs_previous": action_delta(before_counts, after_counts),
        "prefill_owner_merge_branch_counts": dict(sorted(target_counts.items())),
        "remaining_prefill_default_off_without_proxy_rows": sum(
            1
            for row in output_rows
            if row.get("source_capture_surface") == TARGET_SURFACE
            and row.get("action_class") == "IMPLEMENT_DEFAULT_OFF"
            and row.get("after_proxy_r") is None
        ),
        "standalone_fvg_negative_small_n_rows_audited": len(weak_fvg_rows),
        "standalone_fvg_negative_small_n_proxy_reference_rows": len(weak_fvg_values),
        "standalone_fvg_negative_small_n_proxy_reference_sum": round(sum(weak_fvg_values), 8),
        "rows_requiring_source_cost_fill_repair_after": int(after_counts.get("PRESERVE_REQUIREMENT", 0)),
        "source_requirement_rows_opportunity_preserved": len(source_requirement_rows),
        "source_requirement_rows_audit_repaired": source_requirement_audit_repairs,
        "source_requirement_proxy_reference_rows": len(source_requirement_values),
        "source_requirement_proxy_reference_sum": round(sum(source_requirement_values), 8),
        "opportunity_preservation_rows_touched": (
            len(touched_rows) + len(weak_fvg_rows) + source_requirement_audit_repairs
        ),
        "rows_with_missed_opportunity_audit_after": rows_with_audit,
        "rows_with_underlying_intelligence_preserved_after": rows_with_opportunity_preserved,
        "redesign_rows_missing_missed_opportunity_audit_after": sum(
            1
            for row in output_rows
            if row.get("action_class") == "REDESIGN"
            and not isinstance(row.get("missed_opportunity_audit"), dict)
        ),
        "preserve_requirement_rows_missing_missed_opportunity_audit_after": sum(
            1
            for row in output_rows
            if row.get("action_class") == "PRESERVE_REQUIREMENT"
            and not isinstance(row.get("missed_opportunity_audit"), dict)
        ),
        "kill_rows_missing_missed_opportunity_audit_after": sum(
            1
            for row in output_rows
            if row.get("action_class") == "KILL"
            and not isinstance(row.get("missed_opportunity_audit"), dict)
        ),
        "kill_count_delta": int(after_counts.get("KILL", 0)) - int(before_counts.get("KILL", 0)),
        "proxy_counting_decision": PROXY_COUNTING,
        "research_safety": {
            "opens_exact_r": False,
            "duplicates_proxy_r": False,
            "changes_live_behavior": False,
            "changes_shadow_log_history": False,
        },
    }
    return output_rows, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": summary["generated_utc"],
        "description": "Action ledger after prefill rows are merged into the entry-offset proxy owner.",
        "inputs": {
            "ledger": {"path": str(INPUT_LEDGER), "sha256": sha256_file(INPUT_LEDGER)},
            "summary": {"path": str(INPUT_SUMMARY), "sha256": sha256_file(INPUT_SUMMARY)},
        },
        "outputs": {
            "ledger": {"path": str(OUTPUT_LEDGER), "sha256": sha256_file(OUTPUT_LEDGER)},
            "summary": {"path": str(OUTPUT_SUMMARY), "sha256": sha256_file(OUTPUT_SUMMARY)},
        },
        "safe_flags": SAFE_FLAGS,
        "key_counts": {
            "rows": summary["rows"],
            "target_rows": summary["target_rows"],
            "rows_owner_merged": summary["rows_owner_merged"],
            "far_miss_rows_merged_to_redesign": summary["far_miss_rows_merged_to_redesign"],
            "near_miss_rows_merged_to_entry_offset": summary["near_miss_rows_merged_to_entry_offset"],
            "rows_removed_from_standalone_implementation": summary["rows_removed_from_standalone_implementation"],
            "rows_preserved_as_entry_offset_owned": summary["rows_preserved_as_entry_offset_owned"],
            "remaining_prefill_default_off_without_proxy_rows": summary[
                "remaining_prefill_default_off_without_proxy_rows"
            ],
            "reference_proxy_numeric_rows": summary["reference_proxy_numeric_rows"],
            "reference_proxy_r_sum_not_counted": summary["reference_proxy_r_sum_not_counted"],
            "standalone_fvg_negative_small_n_rows_audited": summary[
                "standalone_fvg_negative_small_n_rows_audited"
            ],
            "rows_requiring_source_cost_fill_repair_after": summary[
                "rows_requiring_source_cost_fill_repair_after"
            ],
            "source_requirement_rows_audit_repaired": summary["source_requirement_rows_audit_repaired"],
            "rows_with_missed_opportunity_audit_after": summary["rows_with_missed_opportunity_audit_after"],
        },
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    manifest = build_manifest(summary)
    write_json(OUTPUT_MANIFEST, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
