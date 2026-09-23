"""Convert accepted SOURCE degraded rows into redesign/avoid decisions.

These rows were preserved as exact-source requirements after the owner corrected
kill semantics. The latest action ledger already states that the accepted SOURCE
branch is degraded by the current bar/spread proxy; the useful mechanism is not
erased, but the current standalone implementation claim should not remain a
terminal blocker row. This plate moves the rows to redesign/avoid-or-exact-repair
decisions with no proxy-R counting.
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

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_OUTPUT_MANIFEST_{DATE}.json"

TARGET_BRANCH = "PRESERVE_ACCEPTED_SOURCE_BRANCH_EXACT_TICK_REPAIR_OR_AVOID_REDESIGN"
REPAIRED_BRANCH = "REDESIGN_ACCEPTED_SOURCE_BRANCH_DEGRADED_PROXY_AVOID_OR_EXACT_REPAIR"

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


def target_row(row: dict[str, Any]) -> bool:
    return row.get("action_class") == "PRESERVE_REQUIREMENT" and row.get("branch_decision") == TARGET_BRANCH


def redesign_row(row: dict[str, Any], *, generated: str) -> None:
    row["before_source_accepted_degraded_redesign_action_class"] = row.get("action_class")
    row["before_source_accepted_degraded_redesign_branch_decision"] = row.get("branch_decision")
    row["before_source_accepted_degraded_redesign_after_proxy_r"] = row.get("after_proxy_r")
    row["source_accepted_degraded_redesign_status"] = "CONVERTED_TO_REDESIGN_AVOID_OR_EXACT_REPAIR_DECISION"
    row["source_accepted_degraded_redesign_generated_utc"] = generated
    row["action_class"] = "REDESIGN"
    row["branch_decision"] = REPAIRED_BRANCH
    row["implementation_decision"] = REPAIRED_BRANCH
    row["current_action"] = REPAIRED_BRANCH
    row["next_action"] = "REDESIGN_ACCEPTED_SOURCE_BRANCH_AS_AVOID_CONTEXT_OR_REPAIR_EXACT_TICK_SOURCE"
    row["after_strategy_status"] = "REDESIGN_ACCEPTED_SOURCE_BRANCH_DEGRADED_BY_CURRENT_PROXY"
    row["after_score_status"] = "NOT_COUNTED_ACCEPTED_SOURCE_DEGRADED_PROXY_REQUIRES_REDESIGN_OR_EXACT_REPAIR"
    row["after_proxy_r"] = None
    row["proxy_r_delta"] = None
    row["data_requirement_state"] = "CURRENT_IMPLEMENTATION_UNSUPPORTED_REDESIGN_PATH_OPEN_EXACT_REPAIR_RETAINED"
    row["decision_evidence"] = "BAR_SPREAD_PROXY_DEGRADED_ACCEPTED_SOURCE_BRANCH_CURRENT_CLAIM"
    row["scoring_boundary"] = "NO_IMPLEMENTATION_R_WITHOUT_EXACT_TICK_SOURCE_OR_REDESIGNED_AVOID_RULE"
    row["implementation_candidate"] = "REDESIGN_AS_AVOID_INVERSE_CONTEXT_OR_EXACT_SOURCE_REPAIR_CANDIDATE"
    row["source_requirement_preserved"] = True
    row["source_requirement_next_action"] = "EXACT_TICK_SOURCE_REPAIR_BEFORE_ANY_POSITIVE_IMPLEMENTATION_CLAIM"
    row["opportunity_preservation_status"] = "ACCEPTED_SOURCE_INTELLIGENCE_PRESERVED_AS_REDESIGN_AVOID_OR_EXACT_REPAIR"
    row["opportunity_proxy_r_reference"] = None
    row["opportunity_proxy_reference_status"] = "NO_NUMERIC_PROXY_AVAILABLE_DEGRADED_ACCEPTED_SOURCE_BRANCH"
    row["opportunity_not_independently_countable_reason"] = (
        "The current accepted SOURCE implementation claim is degraded by available bar/spread proxy evidence and "
        "lacks an exact tick/source scalar; it is not independently countable until exact repair or an avoid-rule "
        "redesign is specified."
    )
    row["opportunity_useful_mechanism"] = (
        "Accepted SOURCE branch intelligence remains useful as an avoid/inverse candidate, context feature, "
        "source/cost stress control, or exact-source repair input."
    )
    row["opportunity_downstream_paths"] = [
        "redesign",
        "avoid/inverse",
        "context feature",
        "source requirement",
        "broader system component",
    ]
    row["underlying_intelligence_preserved"] = True
    row["missed_opportunity_audit"] = {
        "kill_scope": "NOT_KILLED_ACCEPTED_SOURCE_CURRENT_IMPLEMENTATION_CLAIM_REDESIGNED_ONLY",
        "current_claim": TARGET_BRANCH,
        "unsupported_reason": "ACCEPTED_SOURCE_BRANCH_DEGRADED_BY_CURRENT_BAR_SPREAD_PROXY_AND_NO_EXACT_SCALAR",
        "what_was_tried": (
            "Accepted SOURCE implication, M15 ordering repair, source-cost detail repair, and opportunity-preserving "
            "kill-label repair were consumed before this redesign decision."
        ),
        "what_could_make_it_work": (
            "Exact tick/source/cost acquisition with a non-degraded scalar, or a redesigned avoid/inverse/context "
            "rule that treats the degraded accepted-source condition as useful negative selection intelligence."
        ),
        "preserve_as": "ACCEPTED_SOURCE_AVOID_OR_EXACT_REPAIR_REDESIGN_CANDIDATE",
        "next_route": "EXACT_TICK_SOURCE_REPAIR_OR_AVOID_INVERSE_CONTEXT_FEATURE_REDESIGN",
        "path_status": {
            "proxy_r_reference": None,
            "proxy_reference_status": "NO_NUMERIC_PROXY_AVAILABLE_DEGRADED_ACCEPTED_SOURCE_BRANCH",
            "source_artifact": row.get("source_artifact"),
            "source_row_id": row.get("source_row_id"),
            "decision_evidence": row.get("decision_evidence"),
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
        if target_row(new):
            redesign_row(new, generated=generated)
            touched.append(new)
        else:
            new["source_accepted_degraded_redesign_status"] = "NOT_TARGET_ROW"
        output_rows.append(new)

    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    after_proxy = proxy_summary(output_rows)
    missing_audit = sum(
        1
        for row in output_rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and not row.get("missed_opportunity_audit")
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
        "accepted_source_rows_redesigned": len(touched),
        "accepted_source_rows_by_symbol": dict(sorted(Counter(str(row.get("symbol")) for row in touched).items())),
        "accepted_source_rows_requiring_exact_repair_preserved": sum(
            1 for row in touched if row.get("source_requirement_preserved") is True
        ),
        "remaining_preserve_requirement_rows": after_counts.get("PRESERVE_REQUIREMENT", 0),
        "remaining_accepted_source_preserve_rows": sum(
            1 for row in output_rows if row.get("branch_decision") == TARGET_BRANCH
        ),
        "redesign_preserve_kill_missing_audit_after": missing_audit,
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
        "generated_utc": summary["generated_utc"],
        "inputs": {
            str(INPUT_LEDGER): sha256_file(INPUT_LEDGER),
            str(INPUT_SUMMARY): sha256_file(INPUT_SUMMARY),
        },
        "outputs": {str(path): sha256_file(path) for path in outputs if path.exists()},
        "safe_flags": SAFE_FLAGS,
        "summary": summary,
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
