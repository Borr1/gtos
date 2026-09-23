from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
INPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_LEDGER_2026-05-17.jsonl"
INPUT_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_SUMMARY_2026-05-17.json"
PROJECTION_ROWS = ROUTE_DIR / "MAIN_ORCH24_LIVE_MECHANICAL_OPPORTUNITY_PRESERVATION_PROJECTION_ROWS_2026-05-17.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_PATH_PROXY_REPAIR_LEDGER_2026-05-17.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_PATH_PROXY_REPAIR_SUMMARY_2026-05-17.json"
OUTPUT_MANIFEST = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_PATH_PROXY_REPAIR_OUTPUT_MANIFEST_2026-05-17.json"

ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
REPAIR_BRANCH = "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_FILLED_PATH_PROXY_REPAIRED"
OLD_BRANCH = "REDESIGN_PENDING_LIFECYCLE_R_OUTCOME_SOURCE_REQUIRED"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

RESEARCH_SAFETY = {
    "changes_action_classes": True,
    "changes_shadow_log_history": False,
    "changes_live_behavior": False,
    "changes_prompt_risk_selector_execution": False,
    "opens_exact_r": False,
    "opens_counted_proxy_r": True,
    "broker_actual_r_claim": False,
}

SOURCE_REPAIR_TOKENS = (
    "SOURCE_REQUIRED",
    "SOURCE_REPAIR",
    "SOURCE_COST",
    "EXACT_SOURCE",
    "TICK_ORDER",
    "ORDERING",
    "R_OUTCOME_SOURCE",
    "PARTIAL_REPAIR",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def proxy_summary(rows: list[dict[str, Any]]) -> tuple[int, float]:
    count = 0
    total = 0.0
    for row in rows:
        value = row.get("after_proxy_r")
        if value is None:
            value = row.get("strategy_proxy_r")
        if value is None or isinstance(value, bool):
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        count += 1
        total += number
    return count, round(total, 8)


def source_cost_fill_repair_required(row: dict[str, Any]) -> bool:
    branch = str(row.get("branch_decision") or "").upper()
    if row.get("action_class") == "PRESERVE_REQUIREMENT":
        return True
    return any(token in branch for token in SOURCE_REPAIR_TOKENS)


def required_preservation(row: dict[str, Any]) -> bool:
    action_class = str(row.get("action_class") or "")
    return action_class in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}


def has_full_preservation(row: dict[str, Any]) -> bool:
    required = (
        "opportunity_preservation_status",
        "opportunity_owner_row_id",
        "opportunity_owner_source_artifact",
        "opportunity_not_independently_countable_reason",
        "opportunity_useful_mechanism",
        "opportunity_downstream_paths",
        "underlying_intelligence_preserved",
        "missed_opportunity_audit",
    )
    return all(row.get(field) not in (None, "", [], {}) for field in required)


def projection_repairs() -> dict[tuple[str, str], dict[str, Any]]:
    repairs: dict[tuple[str, str], dict[str, Any]] = {}
    for row in read_jsonl(PROJECTION_ROWS):
        if row.get("branch_decision") != REPAIR_BRANCH:
            continue
        key = (str(row.get("candidate_id") or ""), str(row.get("strategy_id") or ""))
        repairs[key] = row
    return repairs


def apply_repair(row: dict[str, Any], projection: dict[str, Any], generated_utc: str) -> dict[str, Any]:
    out = dict(row)
    previous_audit = row.get("missed_opportunity_audit")
    proxy_r = projection.get("strategy_proxy_r")

    out.update(
        {
            "action_class": "IMPLEMENT_DEFAULT_OFF",
            "current_action": REPAIR_BRANCH,
            "next_action": "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_FILLED_PATH_PROXY_SCORER_WITH_ACCOUNT_R_REPAIR_FIELD",
            "implementation_decision": REPAIR_BRANCH,
            "implementation_candidate": projection.get("implementation_candidate"),
            "branch_decision": REPAIR_BRANCH,
            "decision_evidence": projection.get("decision_evidence"),
            "scoring_boundary": projection.get("scoring_boundary"),
            "data_requirement_state": "PENDING_LIFECYCLE_FILLED_PATH_PROXY_REPAIRED_NO_BROKER_ACTUAL_R",
            "strategy_proxy_r": proxy_r,
            "after_proxy_r": proxy_r,
            "score_status": projection.get("score_status"),
            "outcome_status": projection.get("outcome_status"),
            "outcome_source": projection.get("outcome_source"),
            "pending_lifecycle_path_proxy_repair_materialized_at_utc": generated_utc,
            "pending_lifecycle_path_proxy_repair_status": "MATERIALIZED_FROM_LIVE_MECHANICAL_SCORER_PROJECTION",
            "pending_lifecycle_original_branch_decision": OLD_BRANCH,
            "pending_lifecycle_r_repair_status": projection.get("pending_lifecycle_r_repair_status"),
            "pending_lifecycle_original_outcome_status": projection.get("pending_lifecycle_original_outcome_status"),
            "pending_lifecycle_proxy_r_source": projection.get("pending_lifecycle_proxy_r_source"),
            "pending_lifecycle_proxy_r_reference": projection.get("pending_lifecycle_proxy_r_reference"),
            "pending_lifecycle_broker_actual_r_status": projection.get("pending_lifecycle_broker_actual_r_status"),
            "pending_lifecycle_path_proxy_outcome_status": projection.get("pending_lifecycle_path_proxy_outcome_status"),
            "pending_lifecycle_source_capture_complete": projection.get("pending_lifecycle_source_capture_complete"),
            "opportunity_preservation_status": "IMPLEMENTED_DEFAULT_OFF_FROM_REPAIRED_PENDING_LIFECYCLE_PATH_PROXY",
            "opportunity_proxy_r_reference": proxy_r,
            "opportunity_proxy_reference_status": "PROXY_R_NOW_COUNTED_BY_PENDING_LIFECYCLE_PATH_PROXY_REPAIR",
            "opportunity_not_independently_countable_reason": (
                "No broker actual-R is claimed; the default-off row is countable only as source-safe path proxy R "
                "until account-history exit truth is repaired."
            ),
            "opportunity_useful_mechanism": (
                "Filled pending-limit lifecycle telemetry plus entry-proven candidate path can score a default-off "
                "pending lifecycle proxy while preserving exact account-R repair as the stronger source path."
            ),
            "opportunity_downstream_paths": [
                "implementation candidate",
                "source requirement",
                "context feature",
                "broader system component",
            ],
            "missed_opportunity_audit": {
                "kill_scope": "NOT_KILLED_IMPLEMENTED_DEFAULT_OFF",
                "current_claim": "PENDING_LIFECYCLE_FILLED_PATH_PROXY_SCORER",
                "unsupported_reason": "BROKER_ACTUAL_R_NOT_CAPTURED_PATH_PROXY_ONLY",
                "what_was_tried": "Consumed pending lifecycle filled broker-ticket state plus candidate path/LTF entry-first terminal order.",
                "what_could_make_it_work": "Account-history close/deal export can upgrade the proxy row to broker actual-R; otherwise keep default-off proxy only.",
                "preserve_as": "DEFAULT_OFF_PENDING_LIFECYCLE_PATH_PROXY_AND_ACCOUNT_R_SOURCE_REQUIREMENT",
                "next_route": "REPAIR_ACCOUNT_HISTORY_EXIT_R_FOR_FILLED_PENDING_LIFECYCLE_ROWS",
                "path_status": {
                    "proxy_r_reference": proxy_r,
                    "proxy_source": projection.get("outcome_source"),
                    "path_proxy_outcome_status": projection.get("pending_lifecycle_path_proxy_outcome_status"),
                    "previous_decision_branch": OLD_BRANCH,
                },
            },
            "previous_missed_opportunity_audit": previous_audit,
            "underlying_intelligence_preserved": True,
        }
    )
    return out


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated_utc = utc_now()
    input_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    before_counts = Counter(str(row.get("action_class") or "") for row in input_rows)
    before_proxy_rows, before_proxy_sum = proxy_summary(input_rows)
    repairs = projection_repairs()

    output_rows: list[dict[str, Any]] = []
    converted: list[dict[str, Any]] = []
    for row in input_rows:
        key = (str(row.get("candidate_id") or ""), str(row.get("strategy_id") or ""))
        projection = repairs.get(key)
        if row.get("branch_decision") == OLD_BRANCH and projection:
            updated = apply_repair(row, projection, generated_utc)
            output_rows.append(updated)
            converted.append(updated)
        else:
            output_rows.append(row)

    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    after_proxy_rows, after_proxy_sum = proxy_summary(output_rows)
    required_rows = [row for row in output_rows if required_preservation(row)]
    missing_preservation = [row for row in required_rows if not has_full_preservation(row)]

    summary = {
        "route_id": ROUTE_ID,
        "date": "2026-05-17",
        "generated_utc": generated_utc,
        "input_ledger": str(INPUT_LEDGER),
        "input_summary": str(INPUT_SUMMARY),
        "projection_rows": str(PROJECTION_ROWS),
        "rows": len(output_rows),
        "input_rows": len(input_rows),
        "input_summary_rows": input_summary.get("rows"),
        "row_identity_policy": "ROW_ID_AND_ORDER_PRESERVED",
        "action_class_counts_before": dict(sorted(before_counts.items())),
        "action_class_counts_after": dict(sorted(after_counts.items())),
        "action_class_delta": {
            key: int(after_counts.get(key, 0) - before_counts.get(key, 0))
            for key in sorted(set(before_counts) | set(after_counts))
            if after_counts.get(key, 0) != before_counts.get(key, 0)
        },
        "exact_r_rows": 0,
        "numeric_proxy_rows_before": before_proxy_rows,
        "numeric_proxy_rows_after": after_proxy_rows,
        "numeric_proxy_row_delta": after_proxy_rows - before_proxy_rows,
        "proxy_r_sum_before": before_proxy_sum,
        "proxy_r_sum_after": after_proxy_sum,
        "proxy_r_sum_delta": round(after_proxy_sum - before_proxy_sum, 8),
        "pending_lifecycle_path_proxy_repaired_rows": len(converted),
        "pending_lifecycle_path_proxy_repaired_proxy_rows": sum(
            1 for row in converted if row.get("strategy_proxy_r") is not None
        ),
        "pending_lifecycle_path_proxy_repaired_proxy_sum": round(
            sum(float(row.get("strategy_proxy_r") or 0.0) for row in converted),
            8,
        ),
        "pending_lifecycle_r_outcome_source_required_rows_after": sum(
            1 for row in output_rows if row.get("branch_decision") == OLD_BRANCH
        ),
        "rows_requiring_source_cost_fill_repair_after": sum(
            source_cost_fill_repair_required(row) for row in output_rows
        ),
        "rows_requiring_source_cost_fill_repair_before": input_summary.get(
            "rows_requiring_source_cost_fill_repair"
        ),
        "opportunity_preservation_required_rows": len(required_rows),
        "opportunity_preservation_missing_after": len(missing_preservation),
        "converted_row_ids": [row.get("row_id") for row in converted],
        "converted_candidate_ids": [row.get("candidate_id") for row in converted],
        "safe_flags": SAFE_FLAGS,
        "research_safety": RESEARCH_SAFETY,
    }
    return output_rows, summary


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "date": "2026-05-17",
        "generated_utc": summary["generated_utc"],
        "artifacts": {
            "ledger": str(OUTPUT_LEDGER),
            "summary": str(OUTPUT_SUMMARY),
            "input_ledger": str(INPUT_LEDGER),
            "projection_rows": str(PROJECTION_ROWS),
        },
        "counts": {
            "rows": summary["rows"],
            "pending_lifecycle_path_proxy_repaired_rows": summary[
                "pending_lifecycle_path_proxy_repaired_rows"
            ],
            "numeric_proxy_row_delta": summary["numeric_proxy_row_delta"],
            "proxy_r_sum_delta": summary["proxy_r_sum_delta"],
            "rows_requiring_source_cost_fill_repair_after": summary[
                "rows_requiring_source_cost_fill_repair_after"
            ],
        },
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_MANIFEST, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
