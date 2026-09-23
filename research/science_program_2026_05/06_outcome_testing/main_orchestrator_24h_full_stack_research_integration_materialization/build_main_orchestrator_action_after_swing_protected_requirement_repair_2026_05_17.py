"""Consume repaired swing-protected source requirements into scorer rows.

The owner-merge ledger still contains swing-protected rows marked as source
requirements even though the row already carries tick-derived decision-time
protected-swing metadata and an M1 path-order terminal event. This builder
converts those rows into default-off swing-protected proxy outputs instead of
leaving source-complete negative evidence uncounted.
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

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_ENTRY_OFFSET_OWNER_MERGE_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_ENTRY_OFFSET_OWNER_MERGE_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

TARGET_BRANCH = "PRESERVE_SWING_PROTECTED_SOURCE_REQUIREMENT_AFTER_STRUCTURAL_METADATA_REPAIR"
REPAIRED_BRANCH = "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_SOURCE_REPAIRED_LTF_PROXY"


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


def proxy_from_ltf(row: dict[str, Any]) -> tuple[str, float | None, str]:
    source = row.get("structural_ltf_repair_source")
    if not isinstance(source, dict):
        return "LTF_SOURCE_MISSING", None, "missing_ltf_source"
    terminal = str(source.get("ltf_terminal_outcome_status") or "")
    if terminal == "ENTRY_THEN_TP1":
        return "ENTRY_TOUCHED_THEN_TP1", 1.5, "candidate_ltf_path_order"
    if terminal == "ENTRY_THEN_SL":
        return "ENTRY_TOUCHED_THEN_SL", -1.0, "candidate_ltf_path_order"
    if "AMBIGUOUS" in terminal:
        return terminal, None, "candidate_ltf_path_order_ambiguous"
    return terminal or "LTF_TERMINAL_STATUS_MISSING", None, "candidate_ltf_path_order_incomplete"


def target_row(row: dict[str, Any]) -> bool:
    outcome, proxy_r, source = proxy_from_ltf(row)
    return (
        row.get("branch_decision") == TARGET_BRANCH
        and row.get("action_class") == "PRESERVE_REQUIREMENT"
        and row.get("swing_protected_stop_status") == "SWING_PROTECTED_STOP_CONFIRMED"
        and row.get("swing_protected_source_status") == "TICK_DERIVED_DECISION_TIME_SOURCE_CAPTURED"
        and source == "candidate_ltf_path_order"
        and proxy_r is not None
        and outcome == "ENTRY_TOUCHED_THEN_SL"
    )


def repair_row(row: dict[str, Any], *, generated: str) -> None:
    outcome, proxy_r, outcome_source = proxy_from_ltf(row)
    if proxy_r is None:
        raise ValueError(f"Target row lacks countable LTF proxy: {row.get('row_id')}")
    row["before_swing_requirement_repair_action_class"] = row.get("action_class")
    row["before_swing_requirement_repair_branch_decision"] = row.get("branch_decision")
    row["before_swing_requirement_repair_after_proxy_r"] = row.get("after_proxy_r")
    row["before_swing_requirement_repair_data_requirement_state"] = row.get("data_requirement_state")
    row["swing_protected_requirement_repair_status"] = "REPAIRED_TO_DEFAULT_OFF_PROXY_FROM_TICK_DERIVED_SWING_AND_LTF"
    row["swing_protected_requirement_repair_generated_utc"] = generated
    row["action_class"] = "IMPLEMENT_DEFAULT_OFF"
    row["branch_decision"] = REPAIRED_BRANCH
    row["implementation_decision"] = REPAIRED_BRANCH
    row["current_action"] = REPAIRED_BRANCH
    row["next_action"] = "KEEP_DEFAULT_OFF_SWING_PROTECTED_STOP_SCORER_WITH_SOURCE_REPAIRED_LTF_PROXY"
    row["after_strategy_status"] = "SCORED_SWING_PROTECTED_STOP_PROXY_SHARED_CANDIDATE_PATH"
    row["after_score_status"] = "COMPUTED_FROM_LTF_PATH_ORDER"
    row["after_outcome_status"] = outcome
    row["outcome_status"] = outcome
    row["outcome_source"] = outcome_source
    row["after_proxy_r"] = proxy_r
    row["proxy_r_delta"] = proxy_r
    row["data_requirement_state"] = "CLOSED_BY_TICK_DERIVED_SWING_SOURCE_AND_LTF_PATH_ORDER"
    row["decision_evidence"] = "SWING_PROTECTED_STOP_CONFIRMED_AND_LTF_ORDER_RESOLVED"
    row["scoring_boundary"] = "SWING_PROTECTED_STOP_SHARED_CANDIDATE_PATH_PROXY_NO_LIVE_ENTRY_CHANGE"
    row["implementation_candidate"] = "KEEP_DEFAULT_OFF_SWING_PROTECTED_STOP_PATH_SCORER_NOW_SOURCE_REPAIRED"
    row["opportunity_preservation_status"] = "SWING_PROTECTED_SOURCE_REQUIREMENT_REPAIRED_TO_DEFAULT_OFF_PROXY"
    row["opportunity_proxy_r_reference"] = proxy_r
    row["opportunity_proxy_reference_status"] = "COUNTED_AS_DEFAULT_OFF_SWING_PROTECTED_PROXY_R"
    row["opportunity_not_independently_countable_reason"] = (
        "Source requirement is closed for this row; the proxy is independently countable as default-off "
        "swing-protected shared-path evidence, but still not validation-safe or live behavior."
    )
    row["opportunity_useful_mechanism"] = (
        "Confirmed swing-protected stop geometry remains useful as a default-off structural stop scorer and "
        "as adverse GBPUSD/NAS100 LONG context evidence."
    )
    row["opportunity_downstream_paths"] = [
        "implementation candidate",
        "context feature",
        "avoid/inverse",
        "broader system component",
    ]
    row["underlying_intelligence_preserved"] = True
    row["missed_opportunity_audit"] = {
        "kill_scope": "NOT_KILLED_SOURCE_REQUIREMENT_REPAIRED_TO_SCORER_OUTPUT",
        "current_claim": TARGET_BRANCH,
        "unsupported_reason": "SOURCE_REQUIREMENT_STATUS_WAS_STALE_AFTER_TICK_DERIVED_SWING_SOURCE_AND_LTF_PATH_ORDER",
        "what_was_tried": "Joined tick-derived swing-protected metadata with M1 LTF terminal path order.",
        "what_could_make_it_work": (
            "Already repaired for this row; future improvement requires broker-realized R, exact cost/slippage, "
            "or condition splits rather than source-requirement status."
        ),
        "preserve_as": "DEFAULT_OFF_SWING_PROTECTED_STOP_PROXY_AND_ADVERSE_CONTEXT_FEATURE",
        "next_route": "RECOMPUTE_SWING_PROTECTED_CONDITION_SPLITS_BY_SYMBOL_SIDE_SESSION_AND_CONTEXT",
        "path_status": {
            "outcome_status": outcome,
            "proxy_r": proxy_r,
            "outcome_source": outcome_source,
            "swing_protected_stop_status": row.get("swing_protected_stop_status"),
        },
    }
    row["safe_flags"] = SAFE_FLAGS
    row["no_live_behavior"] = True
    row["no_shadow_log_append"] = True


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    source_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    before_counts = Counter(str(row.get("action_class") or "") for row in source_rows)
    before_proxy = proxy_summary(source_rows)
    output_rows: list[dict[str, Any]] = []
    touched: list[dict[str, Any]] = []

    for row in source_rows:
        new = dict(row)
        new.pop("_source_line_no", None)
        if target_row(row):
            repair_row(new, generated=generated)
            touched.append(new)
        else:
            new["swing_protected_requirement_repair_status"] = "NOT_TARGET_ROW"
        output_rows.append(new)

    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    after_proxy = proxy_summary(output_rows)
    touched_values = [safe_float(row.get("after_proxy_r")) for row in touched]
    touched_values = [value for value in touched_values if value is not None]
    remaining_target = [
        row for row in output_rows if row.get("branch_decision") == TARGET_BRANCH
    ]
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
        "target_rows_repaired": len(touched),
        "target_proxy_rows_added": len(touched_values),
        "target_proxy_r_sum_added": round(sum(touched_values), 8),
        "remaining_swing_protected_source_requirement_rows": len(remaining_target),
        "rows_requiring_source_cost_fill_repair_before": input_summary.get(
            "rows_requiring_source_cost_fill_repair_after"
        ),
        "rows_requiring_source_cost_fill_repair_after": int(after_counts.get("PRESERVE_REQUIREMENT", 0)),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "numeric_proxy_row_delta": after_proxy["numeric_proxy_rows"] - before_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "action_class_counts_before": dict(sorted(before_counts.items())),
        "action_class_counts_after": dict(sorted(after_counts.items())),
        "action_class_delta_vs_previous": action_delta(before_counts, after_counts),
        "kill_count_delta": int(after_counts.get("KILL", 0)) - int(before_counts.get("KILL", 0)),
        "redesign_preserve_kill_missing_audit_after": sum(
            1
            for row in output_rows
            if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
            and not isinstance(row.get("missed_opportunity_audit"), dict)
        ),
        "research_safety": {
            "opens_exact_r": False,
            "changes_live_behavior": False,
            "changes_shadow_log_history": False,
            "changes_prompt_risk_selector_execution": False,
        },
    }
    return output_rows, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": summary["generated_utc"],
        "description": "Action ledger after swing-protected source requirements are repaired from tick-derived source and LTF order.",
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
            "target_rows_repaired": summary["target_rows_repaired"],
            "target_proxy_rows_added": summary["target_proxy_rows_added"],
            "target_proxy_r_sum_added": summary["target_proxy_r_sum_added"],
            "remaining_swing_protected_source_requirement_rows": summary[
                "remaining_swing_protected_source_requirement_rows"
            ],
            "rows_requiring_source_cost_fill_repair_after": summary[
                "rows_requiring_source_cost_fill_repair_after"
            ],
        },
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary))
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
