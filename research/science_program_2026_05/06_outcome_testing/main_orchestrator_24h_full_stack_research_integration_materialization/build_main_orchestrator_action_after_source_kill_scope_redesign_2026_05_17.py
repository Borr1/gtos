from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
INPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_PATH_PROXY_REPAIR_LEDGER_2026-05-17.jsonl"
INPUT_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_PATH_PROXY_REPAIR_SUMMARY_2026-05-17.json"
OUTPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_SOURCE_KILL_SCOPE_REDESIGN_LEDGER_2026-05-17.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_SOURCE_KILL_SCOPE_REDESIGN_SUMMARY_2026-05-17.json"
OUTPUT_MANIFEST = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_SOURCE_KILL_SCOPE_REDESIGN_OUTPUT_MANIFEST_2026-05-17.json"

ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
OLD_BRANCH = "KILL_SOURCE_REPAIR_UPGRADED_CHALLENGER_AFTER_ORDERING_NEGATIVE_PROXY"
NEW_BRANCH = "REDESIGN_SOURCE_REPAIR_UPGRADED_CHALLENGER_NEGATIVE_PROXY_AVOID_OR_EXACT_ORDERING"

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
    "opens_counted_proxy_r": False,
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
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
    return str(row.get("action_class") or "") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}


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


def redesign_row(row: dict[str, Any], generated_utc: str) -> dict[str, Any]:
    out = dict(row)
    previous_audit = row.get("missed_opportunity_audit") or {}
    proxy_reference = row.get("after_proxy_r")
    audit = dict(previous_audit)
    audit.update(
        {
            "kill_scope": "CURRENT_CLAIM_REDESIGNED_NOT_KILLED",
            "current_claim": "SOURCE_REPAIR_UPGRADED_CHALLENGER_AFTER_ORDERING_NEGATIVE_PROXY",
            "unsupported_reason": "NEGATIVE_BAR_SPREAD_PROXY_REJECTS_ONLY_CURRENT_IMPLEMENTATION_CLAIM",
            "what_was_tried": "M15 ordering/source-cost proxy recompute with accepted source evidence.",
            "what_could_make_it_work": (
                "Exact tick/order/source repair that reverses the negative proxy, or use the negative proxy "
                "as avoid/inverse/context evidence in a broader system."
            ),
            "preserve_as": "SOURCE_REPAIR_AVOID_INVERSE_CONTEXT_OR_EXACT_ORDERING_REQUIREMENT",
            "next_route": "TEST_AS_AVOID_INVERSE_CONTEXT_OR_REPAIR_EXACT_ORDERING_SOURCE",
            "path_status": {
                "proxy_r_reference": proxy_reference,
                "proxy_reference_status": "NEGATIVE_SOURCE_PROXY_NOT_STANDALONE_IMPLEMENTATION",
                "source_artifact": row.get("opportunity_owner_source_artifact"),
                "previous_decision_branch": OLD_BRANCH,
            },
        }
    )
    out.update(
        {
            "action_class": "REDESIGN",
            "current_action": NEW_BRANCH,
            "next_action": "REDESIGN_AS_AVOID_INVERSE_CONTEXT_OR_EXACT_SOURCE_ORDERING_REQUIREMENT",
            "implementation_decision": NEW_BRANCH,
            "implementation_candidate": (
                "REDESIGN_SOURCE_REPAIR_CHALLENGER_AS_AVOID_INVERSE_CONTEXT_FEATURE_OR_EXACT_ORDERING_REPAIR"
            ),
            "branch_decision": NEW_BRANCH,
            "decision_evidence": "NEGATIVE_M15_ORDERING_PROXY_REDESIGNED_NOT_KILLED",
            "scoring_boundary": (
                "NEGATIVE_SOURCE_PROXY_CAN_INFORM_AVOID_CONTEXT_BUT_NOT_STANDALONE_IMPLEMENTATION"
            ),
            "source_kill_scope_redesign_materialized_at_utc": generated_utc,
            "source_kill_scope_redesign_status": "KILL_LABEL_REPLACED_WITH_REDESIGN_UNDER_CURRENT_CLAIM_SCOPE_RULE",
            "opportunity_preservation_status": "CURRENT_CLAIM_REDESIGNED_UNDERLYING_SOURCE_INTELLIGENCE_PRESERVED",
            "opportunity_not_independently_countable_reason": (
                "The current source-repair challenger proxy is negative, so it is not a standalone implementation; "
                "the source mechanism remains usable as exact repair, avoid/inverse, context, or broader-system evidence."
            ),
            "opportunity_useful_mechanism": (
                "Negative source/cost/order proxy identifies adverse source conditions that can become avoid/inverse "
                "or context features instead of deleting the source intelligence."
            ),
            "opportunity_downstream_paths": [
                "redesign",
                "avoid/inverse",
                "context feature",
                "source requirement",
                "broader system component",
            ],
            "missed_opportunity_audit": audit,
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

    output_rows: list[dict[str, Any]] = []
    converted: list[dict[str, Any]] = []
    for row in input_rows:
        if row.get("branch_decision") == OLD_BRANCH and row.get("action_class") == "KILL":
            updated = redesign_row(row, generated_utc)
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
        "source_kill_scope_rows_redesigned": len(converted),
        "source_kill_scope_redesigned_proxy_reference_rows": sum(
            1 for row in converted if row.get("after_proxy_r") is not None
        ),
        "source_kill_scope_redesigned_proxy_reference_sum": round(
            sum(float(row.get("after_proxy_r") or 0.0) for row in converted),
            8,
        ),
        "old_source_kill_branch_rows_after": sum(
            1 for row in output_rows if row.get("branch_decision") == OLD_BRANCH
        ),
        "rows_requiring_source_cost_fill_repair_after": sum(
            source_cost_fill_repair_required(row) for row in output_rows
        ),
        "rows_requiring_source_cost_fill_repair_before": input_summary.get(
            "rows_requiring_source_cost_fill_repair_after"
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
    write_json(
        OUTPUT_MANIFEST,
        {
            "route_id": ROUTE_ID,
            "date": "2026-05-17",
            "generated_utc": summary["generated_utc"],
            "artifacts": {
                "ledger": str(OUTPUT_LEDGER),
                "summary": str(OUTPUT_SUMMARY),
                "input_ledger": str(INPUT_LEDGER),
            },
            "counts": {
                "rows": summary["rows"],
                "source_kill_scope_rows_redesigned": summary["source_kill_scope_rows_redesigned"],
                "proxy_r_sum_delta": summary["proxy_r_sum_delta"],
                "opportunity_preservation_missing_after": summary[
                    "opportunity_preservation_missing_after"
                ],
            },
            "safe_flags": SAFE_FLAGS,
        },
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
