"""Convert source-provenance preserve rows into context/avoid decisions.

The previous plate joined the last nine no-scalar SOURCE rows to moonshot
source-provenance evidence, but left them as PRESERVE_REQUIREMENT rows. This
plate consumes that evidence into concrete action decisions: positive R-style
references become default-off context-feature candidates, while negative
R-style references become avoid/inverse redesign candidates. The R-style values
remain reference-only and are not added to the counted proxy-R denominator.
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

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_OUTPUT_MANIFEST_{DATE}.json"

POSITIVE_REFERENCE_BRANCH = "PRESERVE_SOURCE_PROVENANCE_EXCLUDE_SCALAR_POSITIVE_RSTYLE_REFERENCE"
NEGATIVE_REFERENCE_BRANCH = "PRESERVE_SOURCE_PROVENANCE_EXCLUDE_SCALAR_NEGATIVE_RSTYLE_REFERENCE_AVOID_CONTEXT"
POSITIVE_DECISION_BRANCH = "IMPLEMENT_DEFAULT_OFF_SOURCE_PROVENANCE_CONTEXT_FEATURE_REFERENCE"
NEGATIVE_DECISION_BRANCH = "REDESIGN_SOURCE_PROVENANCE_AVOID_CONTEXT_FEATURE_REFERENCE"

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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_no"] = line_no
                rows.append(row)
    return rows


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


def target_row(row: dict[str, Any]) -> bool:
    return (
        row.get("action_class") == "PRESERVE_REQUIREMENT"
        and row.get("branch_decision") in {POSITIVE_REFERENCE_BRANCH, NEGATIVE_REFERENCE_BRANCH}
    )


def audit_payload(row: dict[str, Any], *, decision_branch: str, positive: bool) -> dict[str, Any]:
    reference_payload = row.get("source_provenance_reference_payload")
    if not isinstance(reference_payload, dict):
        reference_payload = {}
    return {
        "kill_scope": "NOT_KILLED_SOURCE_PROVENANCE_CONTEXT_DECISION",
        "current_claim": row.get("branch_decision"),
        "decision_branch": decision_branch,
        "unsupported_reason": (
            "SOURCE_PROVENANCE_REFERENCE_IS_EXCLUDED_FROM_STANDALONE_SCALAR_RANKING_NOT_FROM_SYSTEM_USE"
        ),
        "what_was_tried": (
            "Consumed the moonshot source-provenance R-style interval, candidate-score proxy, target/stop result, "
            "fillability friction, source-confidence status, and unified exclude-from-scalar decision."
        ),
        "what_could_make_it_work": (
            "A distinct non-duplicated context-feature scorer with source-confidence, target/stop, fillability, "
            "cost-stress, and exact source-acquisition controls; exact broker/account execution remains separate."
        ),
        "preserve_as": (
            "DEFAULT_OFF_SOURCE_PROVENANCE_CONTEXT_FEATURE"
            if positive
            else "SOURCE_PROVENANCE_AVOID_OR_INVERSE_CONTEXT_FEATURE"
        ),
        "next_route": (
            "BUILD_DEFAULT_OFF_SOURCE_PROVENANCE_CONTEXT_FEATURE_SCORER_WITH_NON_DUPLICATED_DENOMINATOR"
            if positive
            else "BUILD_SOURCE_PROVENANCE_AVOID_INVERSE_CONTEXT_FEATURE_AND_FAILURE_FILTER"
        ),
        "path_status": {
            "opportunity_proxy_r_reference": row.get("opportunity_proxy_r_reference"),
            "source_provenance_candidate_score_proxy_reference": row.get(
                "source_provenance_candidate_score_proxy_reference"
            ),
            "source_provenance_target_stop_result": reference_payload.get("target_stop_result"),
            "source_provenance_entry_variant": reference_payload.get("entry_variant"),
            "source_provenance_exact_failure_cause": reference_payload.get("exact_failure_cause"),
            "source_provenance_reference_status": row.get("source_provenance_reference_status"),
        },
    }


def convert_target(row: dict[str, Any], *, generated_utc: str) -> None:
    reference = safe_float(row.get("opportunity_proxy_r_reference"))
    if reference is None:
        raise ValueError(f"target row lacks opportunity proxy reference: {row.get('row_id')}")
    positive = reference >= 0
    decision_branch = POSITIVE_DECISION_BRANCH if positive else NEGATIVE_DECISION_BRANCH
    row["before_source_provenance_context_action_class"] = row.get("action_class")
    row["before_source_provenance_context_branch_decision"] = row.get("branch_decision")
    row["action_class"] = "IMPLEMENT_DEFAULT_OFF" if positive else "REDESIGN"
    row["branch_decision"] = decision_branch
    row["current_action"] = decision_branch
    row["strategy_status"] = decision_branch
    row["score_status"] = "REFERENCE_ONLY_CONTEXT_FEATURE_DECISION_NOT_R_COUNTED"
    row["outcome_status"] = "SOURCE_PROVENANCE_CONTEXT_DECISION_MATERIALIZED"
    row["implementation_decision"] = decision_branch
    row["implementation_candidate"] = (
        "IMPLEMENT_DEFAULT_OFF_SOURCE_PROVENANCE_CONTEXT_FEATURE_SCORER"
        if positive
        else "REDESIGN_SOURCE_PROVENANCE_AVOID_INVERSE_CONTEXT_FEATURE"
    )
    row["decision_evidence"] = "SOURCE_PROVENANCE_RSTYLE_REFERENCE_CONSUMED_AS_CONTEXT_OR_AVOID_DECISION"
    row["scoring_boundary"] = "SOURCE_PROVENANCE_PROXY_REFERENCE_NOT_COUNTED_NO_STANDALONE_SCALAR_R"
    row["source_provenance_context_decision_status"] = (
        "POSITIVE_RSTYLE_REFERENCE_MATERIALIZED_AS_DEFAULT_OFF_CONTEXT_FEATURE"
        if positive
        else "NEGATIVE_RSTYLE_REFERENCE_MATERIALIZED_AS_AVOID_INVERSE_REDESIGN"
    )
    row["source_provenance_context_decision_generated_utc"] = generated_utc
    row["source_provenance_removed_from_preserve_requirement"] = True
    row["source_provenance_proxy_reference_counted_as_r"] = False
    row["source_provenance_reference_only_not_counted_reason"] = (
        "Moonshot source-provenance rows explicitly exclude this branch from standalone scalar implementation "
        "ranking; use as context/avoid/source-quality intelligence until a non-duplicated scorer denominator exists."
    )
    row["opportunity_preservation_status"] = (
        "SOURCE_PROVENANCE_POSITIVE_REFERENCE_PRESERVED_AS_DEFAULT_OFF_CONTEXT_FEATURE"
        if positive
        else "SOURCE_PROVENANCE_NEGATIVE_REFERENCE_PRESERVED_AS_AVOID_INVERSE_CONTEXT_FEATURE"
    )
    row["opportunity_proxy_reference_status"] = "REFERENCE_ONLY_NOT_COUNTED_SOURCE_PROVENANCE_CONTEXT_DECISION"
    row["opportunity_not_independently_countable_reason"] = (
        "The R-style reference is branch-level source-provenance evidence excluded from scalar ranking and lacks "
        "a distinct current-candidate scorer denominator, broker execution, slippage, and account-history truth."
    )
    row["opportunity_useful_mechanism"] = (
        "Source provenance, target/stop result, fillability friction, and source-confidence status can improve "
        "context scoring, avoid/inverse behavior, source-quality controls, and broader system routing."
    )
    paths = ["context feature", "source requirement", "broader system component"]
    if positive:
        paths.insert(0, "default-off scorer input")
    else:
        paths.insert(0, "avoid/inverse")
        paths.insert(1, "redesign")
    row["opportunity_downstream_paths"] = paths
    row["underlying_intelligence_preserved"] = True
    row["missed_opportunity_audit"] = audit_payload(row, decision_branch=decision_branch, positive=positive)
    row["safe_flags"] = SAFE_FLAGS
    row["no_live_behavior"] = True
    row["no_shadow_log_append"] = True


def build() -> dict[str, Any]:
    generated_utc = utc_now()
    input_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    before_counts = Counter(str(row.get("action_class") or "") for row in input_rows)
    before_proxy = proxy_summary(input_rows)
    output_rows: list[dict[str, Any]] = []
    converted: list[dict[str, Any]] = []

    for source_row in input_rows:
        row = {key: value for key, value in source_row.items() if key != "_source_line_no"}
        if target_row(row):
            convert_target(row, generated_utc=generated_utc)
            converted.append(row)
        else:
            row["source_provenance_context_decision_status"] = "NOT_TARGET_ROW"
        output_rows.append(row)

    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    after_proxy = proxy_summary(output_rows)
    refs = [safe_float(row.get("opportunity_proxy_r_reference")) for row in converted]
    refs = [value for value in refs if value is not None]
    candidate_scores = [
        safe_float(row.get("source_provenance_candidate_score_proxy_reference"))
        for row in converted
    ]
    candidate_scores = [value for value in candidate_scores if value is not None]
    positive_refs = [value for value in refs if value >= 0]
    negative_refs = [value for value in refs if value < 0]

    write_jsonl(OUTPUT_LEDGER, output_rows)
    summary = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "input_ledger": str(INPUT_LEDGER),
        "input_summary": str(INPUT_SUMMARY),
        "input_rows": len(input_rows),
        "rows": len(output_rows),
        "exact_r_rows": 0,
        "action_class_counts_before": dict(sorted(before_counts.items())),
        "action_class_counts_after": dict(sorted(after_counts.items())),
        "action_class_delta_vs_previous": action_delta(before_counts, after_counts),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "source_provenance_context_decision_rows": len(converted),
        "rows_removed_from_preserve_requirement": sum(
            row.get("source_provenance_removed_from_preserve_requirement") is True
            for row in converted
        ),
        "context_feature_implement_rows": sum(row.get("action_class") == "IMPLEMENT_DEFAULT_OFF" for row in converted),
        "avoid_inverse_redesign_rows": sum(row.get("action_class") == "REDESIGN" for row in converted),
        "reference_proxy_r_rows": len(refs),
        "reference_proxy_r_sum_not_counted": round(sum(refs), 8),
        "positive_reference_proxy_rows": len(positive_refs),
        "positive_reference_proxy_sum": round(sum(positive_refs), 8),
        "negative_reference_proxy_rows": len(negative_refs),
        "negative_reference_proxy_sum": round(sum(negative_refs), 8),
        "candidate_score_proxy_reference_rows": len(candidate_scores),
        "candidate_score_proxy_reference_sum": round(sum(candidate_scores), 8),
        "remaining_preserve_requirement_rows": sum(
            row.get("action_class") == "PRESERVE_REQUIREMENT" for row in output_rows
        ),
        "remaining_numeric_preserve_requirement_rows": sum(
            row.get("action_class") == "PRESERVE_REQUIREMENT"
            and safe_float(row.get("after_proxy_r")) is not None
            for row in output_rows
        ),
        "source_provenance_reference_branches_remaining": {
            POSITIVE_REFERENCE_BRANCH: sum(row.get("branch_decision") == POSITIVE_REFERENCE_BRANCH for row in output_rows),
            NEGATIVE_REFERENCE_BRANCH: sum(row.get("branch_decision") == NEGATIVE_REFERENCE_BRANCH for row in output_rows),
        },
        "source_provenance_decision_branch_counts": dict(
            sorted(
                Counter(
                    row.get("branch_decision")
                    for row in converted
                ).items()
            )
        ),
        "rows_with_missed_opportunity_audit_after": sum(
            isinstance(row.get("missed_opportunity_audit"), dict) for row in output_rows
        ),
        "redesign_preserve_kill_missing_audit_after": sum(
            row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
            and not isinstance(row.get("missed_opportunity_audit"), dict)
            for row in output_rows
        ),
        "redesign_preserve_kill_missing_underlying_intel_after": sum(
            row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
            and row.get("underlying_intelligence_preserved") is not True
            for row in output_rows
        ),
        "research_safety": {
            "opens_exact_r": False,
            "opens_counted_proxy_r": False,
            "changes_shadow_log_history": False,
            "changes_live_behavior": False,
            "changes_prompt_risk_selector_execution": False,
        },
        "input_snapshot": {
            "input_ledger_sha256": sha256_file(INPUT_LEDGER),
            "input_ledger_size_bytes": INPUT_LEDGER.stat().st_size,
            "input_summary_sha256": sha256_file(INPUT_SUMMARY),
            "input_summary_captured_proxy_rows": input_summary.get("numeric_proxy_rows_after"),
            "input_summary_captured_proxy_sum": input_summary.get("proxy_r_sum_after"),
        },
    }
    write_json(OUTPUT_SUMMARY, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated_utc,
        "description": "Source-provenance context/avoid decision materialization from remaining preserve rows.",
        "safe_flags": SAFE_FLAGS,
        "input_files": {
            "input_ledger": {
                "path": str(INPUT_LEDGER),
                "sha256": sha256_file(INPUT_LEDGER),
                "size_bytes": INPUT_LEDGER.stat().st_size,
                "rows": len(input_rows),
            },
            "input_summary": {
                "path": str(INPUT_SUMMARY),
                "sha256": sha256_file(INPUT_SUMMARY),
                "size_bytes": INPUT_SUMMARY.stat().st_size,
            },
        },
        "output_files": {
            "ledger": {
                "path": str(OUTPUT_LEDGER),
                "sha256": sha256_file(OUTPUT_LEDGER),
                "size_bytes": OUTPUT_LEDGER.stat().st_size,
                "rows": len(output_rows),
            },
            "summary": {
                "path": str(OUTPUT_SUMMARY),
                "sha256": sha256_file(OUTPUT_SUMMARY),
                "size_bytes": OUTPUT_SUMMARY.stat().st_size,
            },
        },
        "counts": {
            "rows": len(output_rows),
            "source_provenance_context_decision_rows": len(converted),
            "context_feature_implement_rows": summary["context_feature_implement_rows"],
            "avoid_inverse_redesign_rows": summary["avoid_inverse_redesign_rows"],
            "remaining_preserve_requirement_rows": summary["remaining_preserve_requirement_rows"],
            "reference_proxy_r_rows": summary["reference_proxy_r_rows"],
            "reference_proxy_r_sum_not_counted": summary["reference_proxy_r_sum_not_counted"],
        },
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
