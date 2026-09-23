"""Repair full-ledger opportunity preservation fields.

This consumes the latest 3,426-row action ledger and makes opportunity
preservation explicit for every current rejection/redesign/source-repair row.
It does not change action classes, counted proxy R, exact R, or live behavior.
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

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_SCORER_SPLIT_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_SCORER_SPLIT_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

PREFILL_OWNER_STATUS = "MERGED_TO_ENTRY_OFFSET_PROXY_OWNER"
ENTRY_OFFSET_OWNER = "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"
PREFILL_PROXY_COUNTING = "PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_NOT_DUPLICATED"
FVG_NEGATIVE_BRANCH = "REDESIGN_STANDALONE_FVG_POI_SCORER_CURRENT_PROXY_NEGATIVE_SMALL_N"

REQUIRED_ACTION_CLASSES = {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
FULL_PRESERVATION_FIELDS = (
    "opportunity_preservation_status",
    "opportunity_owner_row_id",
    "opportunity_owner_source_artifact",
    "opportunity_proxy_reference_status",
    "opportunity_not_independently_countable_reason",
    "opportunity_useful_mechanism",
    "opportunity_downstream_paths",
)
AUDIT_FIELDS = (
    "kill_scope",
    "current_claim",
    "unsupported_reason",
    "what_was_tried",
    "what_could_make_it_work",
    "preserve_as",
    "next_route",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
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


def proxy_summary(rows: list[dict[str, Any]]) -> tuple[int, float]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return len(values), round(sum(values), 8)


def row_proxy_reference(row: dict[str, Any]) -> float | None:
    for field in (
        "opportunity_proxy_r_reference",
        "prefill_proxy_reference_r",
        "source_proxy_r_reference",
        "after_proxy_r",
        "before_proxy_r",
        "linked_entry_offset_after_proxy_r",
        "linked_entry_offset_selected_proxy_r",
        "linked_prefill_after_proxy_r",
        "linked_entry_offset_050r_proxy_r",
        "selected_shift_proxy_r",
        "ordering_proxy_midpoint_r",
        "strategy_proxy_r",
    ):
        value = safe_float(row.get(field))
        if value is not None:
            return value
    return None


def source_artifact(row: dict[str, Any]) -> str:
    for field in (
        "opportunity_owner_source_artifact",
        "source_artifact",
        "input_source_artifact",
        "owner_source_artifact",
    ):
        value = row.get(field)
        if value not in (None, "", [], {}):
            return str(value)
    detail = row.get("source_cost_detail_source")
    if isinstance(detail, dict):
        for field in ("source_cost_detail_artifact", "source_m15_artifact", "source_artifact"):
            value = detail.get(field)
            if value not in (None, "", [], {}):
                return str(value)
    return str(INPUT_LEDGER)


def opportunity_required(row: dict[str, Any]) -> bool:
    return (
        row.get("action_class") in REQUIRED_ACTION_CLASSES
        or row.get("prefill_entry_offset_owner_merge_status") == PREFILL_OWNER_STATUS
    )


def has_full_preservation(row: dict[str, Any]) -> bool:
    return (
        all(row.get(field) not in (None, "", []) for field in FULL_PRESERVATION_FIELDS)
        and isinstance(row.get("missed_opportunity_audit"), dict)
        and row.get("underlying_intelligence_preserved") is True
    )


def classify(row: dict[str, Any]) -> dict[str, Any]:
    branch = str(row.get("branch_decision") or row.get("current_action") or "")
    action = str(row.get("action_class") or "")
    upper = branch.upper()

    if row.get("prefill_entry_offset_owner_merge_status") == PREFILL_OWNER_STATUS:
        return {
            "status": "PREFILL_OPPORTUNITY_PRESERVED_AS_ENTRY_OFFSET_OWNER_MERGE",
            "reason": (
                "Prefill TP-after-fill evidence is owned by the entry-offset 0.50R scorer; standalone "
                "prefill implementation would duplicate the same proxy-R."
            ),
            "mechanism": (
                "Prefill delivery remains useful as entry-offset-owned retest-control context, avoid/inverse "
                "evidence, and broader entry redesign input."
            ),
            "paths": ["entry-offset merge", "redesign", "avoid/inverse", "context feature", "broader system component"],
            "preserve_as": "ENTRY_OFFSET_OWNED_PREFILL_CONTEXT_OR_RETEST_CONTROL_COMPONENT",
            "next_route": "CONSUME_PREFILL_CONTEXT_INSIDE_ENTRY_OFFSET_RETEST_CONTROL_SCORERS",
            "unsupported": "DUPLICATE_STANDALONE_PREFILL_IMPLEMENTATION_PROXY_OWNER",
            "what_tried": "LINKED_PREFILL_TP_AFTER_FILL_ROW_TO_ENTRY_OFFSET_050R_SPREAD_AWARE_PROXY",
            "proxy_status": "REFERENCE_ONLY_NOT_COUNTED_DUPLICATE_ENTRY_OFFSET_OWNER",
        }
    if FVG_NEGATIVE_BRANCH in branch:
        return {
            "status": "STANDALONE_FVG_NEGATIVE_SMALL_N_OPPORTUNITY_PRESERVED_AS_REDESIGN",
            "reason": (
                "Current standalone-FVG POI proxy evidence is negative and small-N; this rejects only the "
                "current standalone claim, not the FVG mechanism."
            ),
            "mechanism": (
                "Selected FVG POI geometry can still become a tighter-entry selector, shorter-horizon path, "
                "context feature, avoid/inverse filter, or broader structural/FVG component."
            ),
            "paths": [
                "redesign",
                "avoid/inverse",
                "context feature",
                "source requirement",
                "tighter target",
                "shorter horizon",
                "broader system component",
            ],
            "preserve_as": "STANDALONE_FVG_ENTRY_SELECTOR_REDESIGN_CONTEXT_FEATURE_OR_SPECIALIZED_COMPONENT",
            "next_route": "DESIGN_STANDALONE_FVG_ENTRY_LOCK_REENTRY_SCORER_WITH_CONTEXT_SPLITS",
            "unsupported": "CURRENT_STANDALONE_FVG_POI_SHARED_PATH_PROXY_NEGATIVE_SMALL_N",
            "what_tried": "REPAIRED_SELECTED_FVG_POI_GEOMETRY_AND_SCORED_CURRENT_PROXY_ROWS",
            "proxy_status": "NEGATIVE_SMALL_N_REFERENCE_ONLY_NOT_STANDALONE_IMPLEMENTATION",
        }
    if upper.startswith("MERGE_DUPLICATE") or "DUPLICATE" in upper:
        return {
            "status": "DUPLICATE_OPPORTUNITY_PRESERVED_AS_OWNER_MERGE_OR_REDESIGN_COMPONENT",
            "reason": "Current claim duplicates another owner row or shared proxy path and is not independently countable.",
            "mechanism": "Duplicate structure remains useful as a merged component, context contrast, or redesign input.",
            "paths": ["merged component", "redesign", "context feature", "broader system component"],
            "preserve_as": "MERGED_COMPONENT_OR_DISTINCT_SCORER_REDESIGN_INPUT",
            "next_route": "ISOLATE_DISTINCT_SOURCE_FIELDS_BEFORE_RECOUNTING_DUPLICATE_STRUCTURE",
            "unsupported": "DUPLICATE_PROXY_OR_STRUCTURE_WITHOUT_UNIQUE_COUNTABLE_VALUE",
            "what_tried": "DUPLICATE_AWARE_ACTION_LEDGER_MATERIALIZATION",
            "proxy_status": "REFERENCE_ONLY_DUPLICATE_NOT_INDEPENDENTLY_COUNTED",
        }
    if "PREFILL" in upper or "ENTRY_OFFSET" in upper or "FAR_MISS" in upper or "NO_FILL" in upper:
        return {
            "status": "ENTRY_REDESIGN_OPPORTUNITY_PRESERVED",
            "reason": (
                "Current entry/no-fill claim is contradicted or incomplete under the repaired source evidence; "
                "the opportunity remains useful for entry redesign or avoid/inverse routing."
            ),
            "mechanism": "Entry geometry, far-miss/no-fill behavior, and retest distance remain useful entry-redesign signals.",
            "paths": ["entry-offset merge", "redesign", "avoid/inverse", "context feature", "source requirement"],
            "preserve_as": "ENTRY_REDESIGN_AVOID_OR_RETEST_CONTROL_COMPONENT",
            "next_route": "RECOMPUTE_ENTRY_OFFSET_OR_WIDER_RETEST_CONTROL_WITH_SOURCE_SAFE_FILL_COST_FIELDS",
            "unsupported": "CURRENT_ENTRY_FILL_OR_STANDALONE_PREFILL_CLAIM_NOT_SUPPORTED",
            "what_tried": "ENTRY_OFFSET_OR_PREFILL_SOURCE_REPAIR_AND_ACTION_RECOMPUTE",
            "proxy_status": "REFERENCE_ONLY_ENTRY_REDESIGN_OR_NO_FILL_EVIDENCE",
        }
    if "SOURCE" in upper or "REPAIR" in upper or "ORDERING" in upper or "TICK" in upper:
        return {
            "status": "SOURCE_REQUIREMENT_OPPORTUNITY_PRESERVED",
            "reason": (
                "Current row is not independently countable until exact source, cost, fill, tick-order, or "
                "R-outcome evidence is repaired."
            ),
            "mechanism": "Source/cost/fill/order evidence remains useful for exact repair, avoid filters, and context features.",
            "paths": ["source requirement", "redesign", "avoid/inverse", "context feature", "broader system component"],
            "preserve_as": "EXACT_SOURCE_COST_FILL_REPAIR_OR_CONTEXT_FEATURE",
            "next_route": "REPAIR_EXACT_SOURCE_COST_FILL_ORDER_OR_CONSUME_AS_CONTEXT_AVOID_REDESIGN_FEATURE",
            "unsupported": "CURRENT_ROW_REQUIRES_SOURCE_COST_FILL_REPAIR_BEFORE_IMPLEMENTABLE_R",
            "what_tried": "SOURCE_REPAIR_OR_TICK_STRUCTURAL_RECOMPUTE",
            "proxy_status": "SOURCE_OR_INTERVAL_REFERENCE_NOT_IMPLEMENTATION",
        }
    if "ADVERSE" in upper or "AVOID" in upper or "NEGATIVE" in upper:
        return {
            "status": "ADVERSE_OPPORTUNITY_PRESERVED_AS_AVOID_INVERSE_OR_CONTEXT_FEATURE",
            "reason": "Current positive implementation claim is contradicted or weak in this adverse cluster.",
            "mechanism": "Adverse evidence remains useful as avoid/inverse behavior or context conditioning.",
            "paths": ["avoid/inverse", "context feature", "redesign", "broader system component"],
            "preserve_as": "AVOID_INVERSE_OR_CONTEXT_FILTER_CANDIDATE",
            "next_route": "TEST_ADVERSE_CLUSTER_BY_SYMBOL_SESSION_SIDE_REGIME_AND_SOURCE_STATE",
            "unsupported": "CURRENT_POSITIVE_STANDALONE_CLAIM_WEAK_OR_NEGATIVE_IN_CLUSTER",
            "what_tried": "ACTION_LEDGER_BRANCH_SPLIT_AND_PROXY_RECOMPUTE",
            "proxy_status": "REFERENCE_ONLY_ADVERSE_CONTEXT_EVIDENCE",
        }
    if "PENDING" in upper:
        return {
            "status": "PENDING_LIFECYCLE_OPPORTUNITY_PRESERVED_AS_SOURCE_OR_CONTEXT_REDESIGN",
            "reason": "Pending lifecycle current claim is not independently countable without distinct source/R outcome proof.",
            "mechanism": "Pending lifecycle behavior remains useful for source capture, fillability, and entry-quality context.",
            "paths": ["source requirement", "redesign", "context feature", "broader system component"],
            "preserve_as": "PENDING_LIFECYCLE_SOURCE_REPAIR_OR_CONTEXT_FEATURE",
            "next_route": "REPAIR_PENDING_LIFECYCLE_R_OUTCOME_OR_CONSUME_AS_FILLABILITY_CONTEXT",
            "unsupported": "PENDING_LIFECYCLE_CURRENT_CLAIM_NOT_DISTINCT_OR_SOURCE_COMPLETE",
            "what_tried": "PENDING_LIFECYCLE_SOURCE_DECISION_RECOMPUTE",
            "proxy_status": "REFERENCE_ONLY_PENDING_LIFECYCLE_CONTEXT",
        }
    if upper.startswith("KILL_ROW_NOT_"):
        return {
            "status": "CURRENT_BRANCH_DENOMINATOR_EXCLUSION_OPPORTUNITY_PRESERVED",
            "reason": "Row is outside the current branch claim denominator; this excludes only this current claim.",
            "mechanism": "The candidate remains available to the broader action ledger and other branch owners.",
            "paths": ["broader system component", "context feature"],
            "preserve_as": "DENOMINATOR_EXCLUSION_ONLY_CURRENT_BRANCH_NOT_UNDERLYING_CANDIDATE",
            "next_route": "ROUTE_CANDIDATE_TO_APPLICABLE_OWNER_BRANCH_OR_CONTEXT_FEATURE",
            "unsupported": "ROW_NOT_ELIGIBLE_FOR_CURRENT_BRANCH_CLAIM",
            "what_tried": "FULL_LEDGER_ACTION_DENOMINATOR_CLASSIFICATION",
            "proxy_status": "NO_CURRENT_NUMERIC_PROXY_REFERENCE" if row_proxy_reference(row) is None else "REFERENCE_ONLY_DENOMINATOR_EXCLUSION",
        }
    return {
        "status": f"{action}_OPPORTUNITY_PRESERVED_FOR_CURRENT_CLAIM_SCOPE",
        "reason": "Current action decision is not an independently countable standalone implementation claim.",
        "mechanism": "Underlying row intelligence remains useful for redesign, context, source repair, or broader system synthesis.",
        "paths": ["redesign", "context feature", "source requirement", "broader system component"],
        "preserve_as": "CURRENT_CLAIM_SCOPE_ONLY_REDESIGN_OR_CONTEXT_COMPONENT",
        "next_route": "CONSUME_PRESERVED_ROW_INTELLIGENCE_IN_APPLICABLE_BRANCH_OWNER_OR_REDESIGN",
        "unsupported": "CURRENT_CLAIM_NOT_INDEPENDENTLY_COUNTABLE",
        "what_tried": "FULL_LEDGER_ACTION_RECOMPUTE_AND_OPPORTUNITY_PRESERVATION_REPAIR",
        "proxy_status": "REFERENCE_ONLY_NOT_STANDALONE_IMPLEMENTATION" if row_proxy_reference(row) is not None else "NO_CURRENT_NUMERIC_PROXY_REFERENCE",
    }


def repair_row(row: dict[str, Any], generated: str) -> bool:
    missing_before = not has_full_preservation(row)
    info = classify(row)
    proxy_reference = row_proxy_reference(row)
    row.setdefault("opportunity_preservation_status", info["status"])
    row.setdefault("opportunity_owner_row_id", str(row.get("source_row_id") or row.get("row_id") or "UNKNOWN_ROW"))
    row.setdefault("opportunity_owner_source_artifact", source_artifact(row))
    row.setdefault("opportunity_proxy_r_reference", proxy_reference)
    row.setdefault("opportunity_proxy_reference_status", info["proxy_status"])
    row.setdefault("opportunity_not_independently_countable_reason", info["reason"])
    row.setdefault("opportunity_useful_mechanism", info["mechanism"])
    row.setdefault("opportunity_downstream_paths", info["paths"])
    row["underlying_intelligence_preserved"] = True
    row["full_opportunity_preservation_repair_status"] = (
        "REPAIRED_FULL_OPPORTUNITY_PRESERVATION_FIELDS" if missing_before else "ALREADY_COMPLETE"
    )
    row["full_opportunity_preservation_repair_generated_utc"] = generated

    audit = row.get("missed_opportunity_audit")
    if not isinstance(audit, dict):
        audit = {}
    audit.setdefault("kill_scope", "CURRENT_CLAIM_ONLY" if row.get("action_class") == "KILL" else "NOT_KILLED_REDESIGN_OR_REQUIREMENT")
    audit.setdefault("current_claim", str(row.get("branch_decision") or row.get("current_action") or row.get("action_class") or ""))
    audit.setdefault("unsupported_reason", info["unsupported"])
    audit.setdefault("what_was_tried", info["what_tried"])
    audit.setdefault("what_could_make_it_work", info["next_route"])
    audit.setdefault("preserve_as", info["preserve_as"])
    audit.setdefault("next_route", info["next_route"])
    audit.setdefault(
        "path_status",
        {
            "proxy_r_reference": proxy_reference,
            "proxy_reference_status": row.get("opportunity_proxy_reference_status"),
            "source_artifact": row.get("opportunity_owner_source_artifact"),
        },
    )
    row["missed_opportunity_audit"] = audit
    return missing_before


def source_cost_fill_repair_required(row: dict[str, Any]) -> bool:
    branch = str(row.get("branch_decision") or "").upper()
    if row.get("action_class") == "PRESERVE_REQUIREMENT":
        return True
    source_tokens = (
        "SOURCE_REQUIRED",
        "SOURCE_REPAIR",
        "SOURCE_COST",
        "EXACT_SOURCE",
        "TICK_ORDER",
        "ORDERING",
        "R_OUTCOME_SOURCE",
        "PARTIAL_REPAIR",
    )
    return any(token in branch for token in source_tokens)


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    input_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    before_proxy_rows, before_proxy_sum = proxy_summary(input_rows)
    before_counts = Counter(str(row.get("action_class") or "") for row in input_rows)

    output_rows: list[dict[str, Any]] = []
    repaired = 0
    required_before = 0
    for row in input_rows:
        new = dict(row)
        if opportunity_required(new):
            required_before += 1
            if repair_row(new, generated):
                repaired += 1
        else:
            new["full_opportunity_preservation_repair_status"] = "NOT_REQUIRED"
        output_rows.append(new)

    after_proxy_rows, after_proxy_sum = proxy_summary(output_rows)
    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    required_rows = [row for row in output_rows if opportunity_required(row)]
    missing_after = [row for row in required_rows if not has_full_preservation(row)]
    prefill_owner_rows = [
        row for row in output_rows if row.get("prefill_entry_offset_owner_merge_status") == PREFILL_OWNER_STATUS
    ]
    prefill_refs = [
        value for row in prefill_owner_rows if (value := safe_float(row.get("prefill_proxy_reference_r"))) is not None
    ]
    fvg_negative_rows = [row for row in output_rows if row.get("branch_decision") == FVG_NEGATIVE_BRANCH]
    rows_with_audit = [row for row in output_rows if isinstance(row.get("missed_opportunity_audit"), dict)]

    summary = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated,
        "input_ledger": str(INPUT_LEDGER),
        "input_summary": str(INPUT_SUMMARY),
        "input_rows": len(input_rows),
        "input_summary_rows": input_summary.get("rows"),
        "rows": len(output_rows),
        "row_identity_policy": "ROW_ID_AND_ORDER_PRESERVED",
        "action_class_counts_before": dict(sorted(before_counts.items())),
        "action_class_counts_after": dict(sorted(after_counts.items())),
        "action_class_delta": {
            key: int(after_counts.get(key, 0)) - int(before_counts.get(key, 0))
            for key in sorted(set(before_counts) | set(after_counts))
            if int(after_counts.get(key, 0)) != int(before_counts.get(key, 0))
        },
        "exact_r_rows": 0,
        "numeric_proxy_rows_before": before_proxy_rows,
        "numeric_proxy_rows_after": after_proxy_rows,
        "numeric_proxy_row_delta": after_proxy_rows - before_proxy_rows,
        "proxy_r_sum_before": before_proxy_sum,
        "proxy_r_sum_after": after_proxy_sum,
        "proxy_r_sum_delta": round(after_proxy_sum - before_proxy_sum, 8),
        "opportunity_preservation_required_rows": len(required_rows),
        "opportunity_preservation_missing_before": repaired,
        "opportunity_preservation_missing_after": len(missing_after),
        "opportunity_preservation_rows_repaired": repaired,
        "rows_with_full_opportunity_preservation_after": len(required_rows) - len(missing_after),
        "rows_with_missed_opportunity_audit": len(rows_with_audit),
        "rows_with_underlying_intelligence_preserved": sum(
            row.get("underlying_intelligence_preserved") is True for row in output_rows
        ),
        "rows_owner_merged": len(prefill_owner_rows),
        "rows_redesigned": sum(row.get("action_class") == "REDESIGN" for row in prefill_owner_rows),
        "proxy_r_rows_referenced": len(prefill_refs),
        "proxy_r_sum_referenced": round(sum(prefill_refs), 8),
        "rows_removed_from_standalone_implementation": sum(
            row.get("before_prefill_owner_merge_action_class") == "IMPLEMENT_DEFAULT_OFF"
            for row in prefill_owner_rows
        ),
        "rows_preserved_as_entry_offset_owned": sum(
            str(row.get("opportunity_proxy_reference_status") or "").startswith("REFERENCE_ONLY")
            and row.get("prefill_proxy_reference_owner") == ENTRY_OFFSET_OWNER
            for row in prefill_owner_rows
        ),
        "rows_requiring_source_cost_fill_repair": sum(source_cost_fill_repair_required(row) for row in output_rows),
        "source_requirement_action_class_rows": int(after_counts.get("PRESERVE_REQUIREMENT", 0)),
        "standalone_fvg_negative_small_n_rows": len(fvg_negative_rows),
        "standalone_fvg_negative_small_n_rows_with_audit": sum(
            has_full_preservation(row) for row in fvg_negative_rows
        ),
        "standalone_fvg_negative_small_n_proxy_reference_rows": sum(
            row_proxy_reference(row) is not None for row in fvg_negative_rows
        ),
        "standalone_fvg_negative_small_n_proxy_reference_sum": round(
            sum(row_proxy_reference(row) or 0.0 for row in fvg_negative_rows), 8
        ),
        "safe_flags": SAFE_FLAGS,
        "research_safety": {
            "opens_exact_r": False,
            "opens_counted_proxy_r": False,
            "changes_action_classes": False,
            "duplicates_prefill_proxy_r": False,
            "changes_live_behavior": False,
            "changes_prompt_risk_selector_execution": False,
            "changes_shadow_log_history": False,
        },
    }
    return output_rows, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": summary["generated_utc"],
        "description": "Full action-ledger opportunity preservation repair.",
        "input_files": {
            "input_ledger": {
                "path": str(INPUT_LEDGER),
                "rows": summary["input_rows"],
                "size_bytes": INPUT_LEDGER.stat().st_size,
                "sha256": sha256_file(INPUT_LEDGER),
            },
            "input_summary": {
                "path": str(INPUT_SUMMARY),
                "size_bytes": INPUT_SUMMARY.stat().st_size,
                "sha256": sha256_file(INPUT_SUMMARY),
            },
        },
        "output_files": {
            "ledger": {
                "path": str(OUTPUT_LEDGER),
                "rows": summary["rows"],
                "size_bytes": OUTPUT_LEDGER.stat().st_size,
                "sha256": sha256_file(OUTPUT_LEDGER),
            },
            "summary": {
                "path": str(OUTPUT_SUMMARY),
                "size_bytes": OUTPUT_SUMMARY.stat().st_size,
                "sha256": sha256_file(OUTPUT_SUMMARY),
            },
        },
        "key_counts": {
            "rows": summary["rows"],
            "opportunity_preservation_required_rows": summary["opportunity_preservation_required_rows"],
            "opportunity_preservation_rows_repaired": summary["opportunity_preservation_rows_repaired"],
            "opportunity_preservation_missing_after": summary["opportunity_preservation_missing_after"],
            "rows_owner_merged": summary["rows_owner_merged"],
            "rows_redesigned": summary["rows_redesigned"],
            "proxy_r_rows_referenced": summary["proxy_r_rows_referenced"],
            "proxy_r_sum_referenced": summary["proxy_r_sum_referenced"],
            "rows_removed_from_standalone_implementation": summary[
                "rows_removed_from_standalone_implementation"
            ],
            "rows_preserved_as_entry_offset_owned": summary["rows_preserved_as_entry_offset_owned"],
            "rows_requiring_source_cost_fill_repair": summary["rows_requiring_source_cost_fill_repair"],
            "rows_with_missed_opportunity_audit": summary["rows_with_missed_opportunity_audit"],
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary))
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
