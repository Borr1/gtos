"""Convert residual SOURCE proxy preserve rows into redesign decisions.

The prior action ledger still had residual SOURCE rows in PRESERVE_REQUIREMENT
despite carrying numeric negative or straddled proxy evidence. Those proxy
values are useful intelligence, but they are not independently implementable R:
the current claim needs exact source/cost/fill or tick-order repair. This plate
therefore moves the numeric residual SOURCE preserve rows to redesign/context
decisions, keeps the proxy as reference-only evidence, and preserves the exact
repair path instead of killing the mechanism.
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

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_SOURCE_PROXY_REDESIGN_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_SOURCE_PROXY_REDESIGN_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_SOURCE_PROXY_REDESIGN_OUTPUT_MANIFEST_{DATE}.json"

TARGET_BRANCH_MAP = {
    "PRESERVE_SOURCE_COST_REPAIR_STRADDLE_EXACT_SOURCE_REQUIRED": (
        "REDESIGN_SOURCE_COST_STRADDLE_PROXY_AS_AVOID_CONTEXT_EXACT_SOURCE_REQUIRED"
    ),
    "PRESERVE_SOURCE_REPAIR_INTERVAL_BOUND_EXACT_ORDERING_REQUIRED": (
        "REDESIGN_SOURCE_INTERVAL_BOUND_PROXY_AS_AVOID_CONTEXT_EXACT_ORDERING_REQUIRED"
    ),
    "PRESERVE_SOURCE_REPAIR_UPGRADED_INTERVAL_BOUND_NO_CHALLENGER": (
        "REDESIGN_SOURCE_UPGRADED_INTERVAL_BOUND_PROXY_AS_CONTEXT_NO_CHALLENGER_EXACT_ORDERING_REQUIRED"
    ),
}

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


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
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
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


def is_target_row(row: dict[str, Any]) -> bool:
    return (
        row.get("action_class") == "PRESERVE_REQUIREMENT"
        and row.get("branch_decision") in TARGET_BRANCH_MAP
        and safe_float(row.get("after_proxy_r")) is not None
    )


def proxy_reference_payload(row: dict[str, Any], proxy_reference: float) -> dict[str, Any]:
    return {
        "proxy_r_reference": proxy_reference,
        "proxy_reference_status": "REFERENCE_ONLY_NOT_COUNTED_CURRENT_CLAIM_UNSUPPORTED",
        "source_artifact": row.get("source_artifact"),
        "source_row_id": row.get("source_row_id"),
        "source_line_no": row.get("source_line_no"),
        "source_cost_rstyle_lower_r": row.get("source_cost_rstyle_lower_r"),
        "source_cost_rstyle_midpoint_r": row.get("source_cost_rstyle_midpoint_r"),
        "source_cost_rstyle_upper_r": row.get("source_cost_rstyle_upper_r"),
        "ordering_proxy_lower_r": row.get("ordering_proxy_lower_r"),
        "ordering_proxy_midpoint_r": row.get("ordering_proxy_midpoint_r"),
        "ordering_proxy_upper_r": row.get("ordering_proxy_upper_r"),
        "decision_evidence": row.get("decision_evidence"),
    }


def redesign_target_row(row: dict[str, Any], *, generated: str) -> None:
    original_branch = str(row.get("branch_decision"))
    repaired_branch = TARGET_BRANCH_MAP[original_branch]
    proxy_reference = safe_float(row.get("after_proxy_r"))
    if proxy_reference is None:
        raise ValueError(f"target row lacks numeric after_proxy_r: {row.get('row_id')}")

    row["before_residual_source_proxy_redesign_action_class"] = row.get("action_class")
    row["before_residual_source_proxy_redesign_branch_decision"] = original_branch
    row["before_residual_source_proxy_redesign_after_proxy_r"] = proxy_reference
    row["residual_source_proxy_redesign_status"] = "CONVERTED_TO_REDESIGN_REFERENCE_ONLY"
    row["residual_source_proxy_redesign_generated_utc"] = generated
    row["action_class"] = "REDESIGN"
    row["branch_decision"] = repaired_branch
    row["implementation_decision"] = repaired_branch
    row["current_action"] = repaired_branch
    row["next_action"] = "REDESIGN_AS_AVOID_INVERSE_CONTEXT_FEATURE_OR_EXACT_SOURCE_REPAIR"
    row["after_strategy_status"] = "REDESIGN_RESIDUAL_SOURCE_PROXY_NOT_STANDALONE_IMPLEMENTABLE"
    row["after_score_status"] = "REFERENCE_ONLY_SOURCE_PROXY_REQUIRES_EXACT_REPAIR_OR_CONTEXT_REDESIGN"
    row["after_proxy_r"] = None
    row["proxy_r_delta"] = None
    row["current_claim_proxy_counted"] = False
    row["source_proxy_r_reference"] = proxy_reference
    row["source_proxy_reference_status"] = "REFERENCE_ONLY_NOT_COUNTED_CURRENT_CLAIM_UNSUPPORTED"
    row["source_proxy_reference_owner_row_id"] = row.get("source_row_id")
    row["source_proxy_reference_owner_artifact"] = row.get("source_artifact")
    row["source_proxy_reference_payload"] = proxy_reference_payload(row, proxy_reference)
    row["data_requirement_state"] = "CURRENT_SOURCE_PROXY_REFERENCE_ONLY_EXACT_SOURCE_COST_FILL_REQUIRED"
    row["decision_evidence"] = "NEGATIVE_OR_STRADDLED_SOURCE_PROXY_CURRENT_CLAIM_NOT_IMPLEMENTABLE"
    row["scoring_boundary"] = "NO_IMPLEMENTATION_R_WITHOUT_EXACT_SOURCE_COST_FILL_OR_REDESIGNED_AVOID_CONTEXT_RULE"
    row["implementation_candidate"] = "REDESIGN_SOURCE_PROXY_AS_AVOID_INVERSE_CONTEXT_OR_EXACT_SOURCE_REPAIR"
    row["source_requirement_preserved"] = True
    row["source_requirement_next_action"] = (
        "EXACT_SOURCE_COST_FILL_ACQUISITION_OR_AVOID_CONTEXT_BACKTEST_WITH_SOURCE_PROXY_REFERENCE"
    )
    row["opportunity_preservation_status"] = (
        "RESIDUAL_SOURCE_PROXY_INTELLIGENCE_PRESERVED_AS_REDESIGN_CONTEXT_OR_EXACT_REPAIR"
    )
    row["opportunity_proxy_r_reference"] = proxy_reference
    row["opportunity_proxy_reference_status"] = "REFERENCE_ONLY_NOT_COUNTED_CURRENT_CLAIM_UNSUPPORTED"
    row["opportunity_owner_row_id"] = row.get("source_row_id")
    row["opportunity_owner_source_artifact"] = row.get("source_artifact")
    row["opportunity_not_independently_countable_reason"] = (
        "The residual SOURCE proxy is negative or straddles zero under current bar/spread/order bounds; "
        "it is useful evidence but not an independently countable implementation until exact source/cost/fill "
        "or a redesigned avoid/context rule is materialized."
    )
    row["opportunity_useful_mechanism"] = (
        "Source-cost/order ambiguity remains useful as an avoid/inverse signal, context feature, tighter target "
        "or shorter-horizon redesign constraint, exact-source acquisition requirement, and broader source-quality "
        "component."
    )
    row["opportunity_downstream_paths"] = [
        "redesign",
        "avoid/inverse",
        "context feature",
        "source requirement",
        "tighter target",
        "shorter horizon",
        "broader system component",
    ]
    row["underlying_intelligence_preserved"] = True
    row["missed_opportunity_audit"] = {
        "kill_scope": "NOT_KILLED_RESIDUAL_SOURCE_CURRENT_IMPLEMENTATION_CLAIM_REDESIGNED_ONLY",
        "current_claim": original_branch,
        "unsupported_reason": "NEGATIVE_OR_STRADDLED_PROXY_REQUIRES_EXACT_SOURCE_COST_FILL_OR_CONTEXT_REDESIGN",
        "what_was_tried": (
            "SOURCE M15 ordering repair, source-cost detail repair, accepted-source degraded redesign, and "
            "opportunity-preserving audit fields were consumed before this branch decision."
        ),
        "what_could_make_it_work": (
            "Exact source/cost/fill/tick-order acquisition that resolves the interval, or a redesigned avoid, "
            "inverse, context-feature, tighter-target, shorter-horizon, or broader source-quality component."
        ),
        "preserve_as": "RESIDUAL_SOURCE_PROXY_AVOID_CONTEXT_OR_EXACT_REPAIR_REDESIGN_CANDIDATE",
        "next_route": "EXACT_SOURCE_REPAIR_OR_AVOID_INVERSE_CONTEXT_FEATURE_REDESIGN",
        "path_status": proxy_reference_payload(row, proxy_reference),
    }
    row["safe_flags"] = SAFE_FLAGS
    row["no_live_behavior"] = True
    row["no_shadow_log_append"] = True


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    source_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    before_counts = Counter(str(row.get("action_class") or "") for row in source_rows)
    before_branch_counts = Counter(str(row.get("branch_decision") or "") for row in source_rows)
    before_proxy = proxy_summary(source_rows)
    output_rows: list[dict[str, Any]] = []
    touched: list[dict[str, Any]] = []

    for row in source_rows:
        new = dict(row)
        new.pop("_source_line_no", None)
        if is_target_row(new):
            redesign_target_row(new, generated=generated)
            touched.append(new)
        else:
            new["residual_source_proxy_redesign_status"] = "NOT_TARGET_ROW"
        output_rows.append(new)

    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    after_branch_counts = Counter(str(row.get("branch_decision") or "") for row in output_rows)
    after_proxy = proxy_summary(output_rows)
    touched_reference_sum = round(
        sum(float(row["opportunity_proxy_r_reference"]) for row in touched),
        8,
    )
    missing_audit = sum(
        1
        for row in output_rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and not row.get("missed_opportunity_audit")
    )
    missing_intel = sum(
        1
        for row in output_rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and row.get("underlying_intelligence_preserved") is not True
    )

    summary = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated,
        "input_ledger": str(INPUT_LEDGER),
        "input_summary": str(INPUT_SUMMARY),
        "input_rows": input_summary.get("rows"),
        "rows": len(output_rows),
        "exact_r_rows": sum(1 for row in output_rows if safe_float(row.get("exact_r")) is not None),
        "action_class_counts_before": dict(sorted(before_counts.items())),
        "action_class_counts_after": dict(sorted(after_counts.items())),
        "action_class_delta_vs_previous": action_delta(before_counts, after_counts),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "residual_source_proxy_rows_redesigned": len(touched),
        "residual_source_proxy_reference_rows": len(touched),
        "residual_source_proxy_r_sum_referenced_not_counted": touched_reference_sum,
        "residual_source_proxy_rows_removed_from_counted_denominator": len(touched),
        "residual_source_rows_exact_repair_preserved": sum(
            1 for row in touched if row.get("source_requirement_preserved") is True
        ),
        "residual_source_rows_by_original_branch": dict(
            sorted(Counter(str(row.get("before_residual_source_proxy_redesign_branch_decision")) for row in touched).items())
        ),
        "residual_source_rows_by_new_branch": dict(
            sorted(Counter(str(row.get("branch_decision")) for row in touched).items())
        ),
        "residual_source_rows_by_symbol": dict(sorted(Counter(str(row.get("symbol")) for row in touched).items())),
        "residual_source_rows_by_side": dict(sorted(Counter(str(row.get("side")) for row in touched).items())),
        "remaining_preserve_requirement_rows": after_counts.get("PRESERVE_REQUIREMENT", 0),
        "remaining_no_scalar_preserve_rows": after_branch_counts.get("PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR", 0),
        "remaining_tick_order_preserve_rows": after_branch_counts.get(
            "PRESERVE_STRUCTURAL_METADATA_LTF_SAME_M1_TICK_ORDER_REQUIRED",
            0,
        ),
        "remaining_numeric_preserve_requirement_rows": sum(
            1
            for row in output_rows
            if row.get("action_class") == "PRESERVE_REQUIREMENT" and safe_float(row.get("after_proxy_r")) is not None
        ),
        "redesign_preserve_kill_missing_audit_after": missing_audit,
        "redesign_preserve_kill_missing_underlying_intel_after": missing_intel,
        "rows_with_missed_opportunity_audit_after": sum(1 for row in output_rows if row.get("missed_opportunity_audit")),
        "rows_with_underlying_intelligence_preserved_after": sum(
            1 for row in output_rows if row.get("underlying_intelligence_preserved") is True
        ),
        "safe_flags": SAFE_FLAGS,
        "research_safety": {
            "changes_live_behavior": False,
            "changes_shadow_log_history": False,
            "changes_prompt_risk_selector_execution": False,
            "opens_exact_r": False,
        },
    }
    return output_rows, summary


def build_manifest(summary: dict[str, Any], outputs: list[Path]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "date": DATE,
        "description": "Residual SOURCE proxy preserve rows redesigned as reference-only avoid/context/exact-repair candidates.",
        "generated_utc": summary["generated_utc"],
        "inputs": {
            "ledger": {"path": str(INPUT_LEDGER), "sha256": sha256_file(INPUT_LEDGER)},
            "summary": {"path": str(INPUT_SUMMARY), "sha256": sha256_file(INPUT_SUMMARY)},
        },
        "outputs": {
            path.name: {"path": str(path), "sha256": sha256_file(path)}
            for path in outputs
            if path.exists()
        },
        "key_counts": {
            "rows": summary["rows"],
            "residual_source_proxy_rows_redesigned": summary["residual_source_proxy_rows_redesigned"],
            "residual_source_proxy_reference_rows": summary["residual_source_proxy_reference_rows"],
            "residual_source_proxy_r_sum_referenced_not_counted": summary[
                "residual_source_proxy_r_sum_referenced_not_counted"
            ],
            "numeric_proxy_rows_after": summary["numeric_proxy_rows_after"],
            "proxy_r_sum_after": summary["proxy_r_sum_after"],
            "remaining_preserve_requirement_rows": summary["remaining_preserve_requirement_rows"],
            "remaining_numeric_preserve_requirement_rows": summary["remaining_numeric_preserve_requirement_rows"],
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary, [OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    write_json(OUTPUT_MANIFEST, build_manifest(summary, [OUTPUT_LEDGER, OUTPUT_SUMMARY, OUTPUT_MANIFEST]))
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
