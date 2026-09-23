"""Consume SOURCE cost-detail proxy bounds into action rows.

This plate repairs the remaining SOURCE M15-ordering rows that were still
default-off labels without scalar evidence. It joins each row to the accepted
moonshot SOURCE cost-cap/acquisition detail ledger, counts accepted proxy
detail as default-off implementation evidence, converts all-negative repair
bounds into redesign/avoid candidates, and preserves straddled repair bounds as
exact-source requirements. It opens no exact R, promotion, or live behavior.
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
MOONSHOT_ROUTE_DIR = (
    Path("C:/tmp/")
    / "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15"
)

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_LTF_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_LTF_REPAIR_SUMMARY_{DATE}.json"
SOURCE_M15_LEDGER = ROUTE_DIR / "MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_LEDGER_2026-05-16.jsonl"
SOURCE_COST_DETAIL_LEDGER = (
    MOONSHOT_ROUTE_DIR
    / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_COST_CAP_ACQUISITION_DETAIL_BRANCH_LEDGER_2026-05-16.jsonl"
)

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_COST_DETAIL_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_COST_DETAIL_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_COST_DETAIL_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

ACCEPTED_PERMISSION = "ACCEPTED_PROXY_DETAIL_ALLOWED"
REPAIR_PERMISSION = "REPAIR_NO_SCALAR"
ALL_NEGATIVE = "SOURCE_COST_INTERVAL_ALL_NEGATIVE"
STRADDLES_ZERO = "SOURCE_COST_INTERVAL_STRADDLES_ZERO"

IMPLEMENT_BRANCH = "IMPLEMENT_DEFAULT_OFF_SOURCE_ACCEPTED_SOURCE_COST_PROXY_REPAIRED"
REDESIGN_BRANCH = "REDESIGN_SOURCE_COST_REPAIR_ALL_NEGATIVE_AVOID_OR_EXACT_SOURCE_REPAIR"
PRESERVE_BRANCH = "PRESERVE_SOURCE_COST_REPAIR_STRADDLE_EXACT_SOURCE_REQUIRED"


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


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "") for row in rows))


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "proxy_r_mean": round(sum(values) / len(values), 8) if values else None,
    }


def action_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    keys = sorted(set(before) | set(after))
    return {
        key: int(after.get(key, 0)) - int(before.get(key, 0))
        for key in keys
        if int(after.get(key, 0)) != int(before.get(key, 0))
    }


def source_m15_by_row_id() -> dict[str, dict[str, Any]]:
    return {row["row_id"]: row for row in read_jsonl(SOURCE_M15_LEDGER)}


def source_cost_by_key() -> dict[tuple[str | None, str | None], dict[str, Any]]:
    return {
        (row.get("branch_queue_id"), row.get("target_stop_contract_id")): row
        for row in read_jsonl(SOURCE_COST_DETAIL_LEDGER)
    }


def target_row(row: dict[str, Any]) -> bool:
    return (
        row.get("source_capture_surface") == "source_m15_ordering_repair"
        and row.get("action_class") == "IMPLEMENT_DEFAULT_OFF"
        and row.get("after_proxy_r") is None
        and str(row.get("current_action") or "").startswith("IMPLEMENT_DEFAULT_OFF")
    )


def source_cost_source(source_row: dict[str, Any], cost_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_cost_detail_artifact": str(SOURCE_COST_DETAIL_LEDGER),
        "source_cost_detail_line_no": cost_row.get("_source_line_no"),
        "source_m15_artifact": SOURCE_M15_LEDGER.name,
        "source_m15_row_id": source_row.get("row_id"),
        "source_m15_source_branch_queue_id": source_row.get("source_branch_queue_id"),
        "target_stop_contract_id": source_row.get("target_stop_contract_id"),
        "source_manifest_hash": cost_row.get("source_manifest_hash"),
    }


def attach_source_cost_fields(row: dict[str, Any], source_row: dict[str, Any], cost_row: dict[str, Any]) -> float:
    midpoint = safe_float(cost_row.get("rstyle_midpoint_mean"))
    if midpoint is None:
        raise ValueError(f"Missing source-cost midpoint for {row.get('row_id')}")
    row["source_branch_queue_id"] = source_row.get("source_branch_queue_id")
    row["target_stop_contract_id"] = source_row.get("target_stop_contract_id")
    row["entry_variant"] = source_row.get("entry_variant")
    row["route_session"] = source_row.get("route_session")
    row["source_implication_class"] = source_row.get("source_implication_class")
    row["route_candidate_id"] = source_row.get("route_candidate_id")
    row["symbol"] = row.get("symbol") or source_row.get("symbol")
    row["side"] = row.get("side") or source_row.get("side")
    row["before_source_cost_detail_action_class"] = row.get("action_class")
    row["before_source_cost_detail_branch_decision"] = row.get("branch_decision")
    row["before_source_cost_detail_current_action"] = row.get("current_action")
    row["before_source_cost_detail_after_proxy_r"] = row.get("after_proxy_r")
    row["source_cost_detail_source"] = source_cost_source(source_row, cost_row)
    row["source_cost_detail_repair_status"] = "SOURCE_COST_DETAIL_PROXY_JOINED"
    row["source_cost_detail_proxy_source_status"] = cost_row.get("source_scalar_permission")
    row["source_cost_interval_sign_class"] = cost_row.get("source_cost_interval_sign_class")
    row["source_cost_branch_result_binary"] = cost_row.get("branch_result_binary")
    row["source_cost_accepted_for_next_executable_builder"] = cost_row.get(
        "accepted_for_next_executable_builder"
    )
    row["source_cost_target_stop_result"] = cost_row.get("target_stop_result")
    row["source_cost_rstyle_lower_r"] = safe_float(cost_row.get("rstyle_lower_mean"))
    row["source_cost_rstyle_midpoint_r"] = midpoint
    row["source_cost_rstyle_upper_r"] = safe_float(cost_row.get("rstyle_upper_mean"))
    row["source_cost_exact_acquisition_state"] = cost_row.get("exact_acquisition_state")
    row["source_cost_detail_status"] = cost_row.get("source_cost_cap_detail_status")
    row["source_cost_detail_scope"] = cost_row.get("source_detail_scope")
    row["after_proxy_r"] = midpoint
    row["proxy_r_delta"] = midpoint
    row["data_requirement_state"] = cost_row.get("source_cost_cap_detail_status")
    return midpoint


def apply_source_cost_decision(row: dict[str, Any], source_row: dict[str, Any], cost_row: dict[str, Any]) -> dict[str, Any]:
    midpoint = attach_source_cost_fields(row, source_row, cost_row)
    permission = str(cost_row.get("source_scalar_permission") or "")
    sign_class = str(cost_row.get("source_cost_interval_sign_class") or "")

    if permission == ACCEPTED_PERMISSION:
        row["source_cost_detail_repair_status"] = "ACCEPTED_SOURCE_COST_PROXY_SCALAR_REPAIRED"
        row["action_class"] = "IMPLEMENT_DEFAULT_OFF"
        row["coverage_status"] = "OBSERVABLE_CANDIDATE_READY_DEFAULT_OFF_WITH_SOURCE_COST_PROXY"
        row["branch_decision"] = IMPLEMENT_BRANCH
        row["implementation_decision"] = IMPLEMENT_BRANCH
        row["current_action"] = "IMPLEMENT_DEFAULT_OFF_SOURCE_ACCEPTED_CONFIRMED_REPLAY_WITH_SOURCE_COST_PROXY"
        row["implementation_candidate"] = row["current_action"]
        row["next_action"] = row["current_action"]
        row["decision_evidence"] = (
            "SOURCE_COST_DETAIL_ACCEPTED_PROXY_DETAIL_ALLOWED_RSTYLE_PROXY"
        )
        row["scoring_boundary"] = (
            "SOURCE_COST_RSTYLE_PROXY_NO_EXACT_TICK_BROKER_R_OR_PROMOTION_CLAIM"
        )
        return row

    if permission == REPAIR_PERMISSION and sign_class == ALL_NEGATIVE:
        row["source_cost_detail_repair_status"] = "REPAIR_SOURCE_COST_ALL_NEGATIVE_REDESIGN"
        row["action_class"] = "REDESIGN"
        row["coverage_status"] = "REDESIGN_REQUIRED_SOURCE_COST_REPAIR_ALL_NEGATIVE"
        row["branch_decision"] = REDESIGN_BRANCH
        row["implementation_decision"] = REDESIGN_BRANCH
        row["current_action"] = "REDESIGN_SOURCE_COST_NEGATIVE_REPAIR_BRANCH_AS_AVOID_OR_CONTEXT_FILTER"
        row["implementation_candidate"] = row["current_action"]
        row["next_action"] = row["current_action"]
        row["decision_evidence"] = "SOURCE_COST_DETAIL_REPAIR_ALL_BOUNDS_NEGATIVE_RSTYLE_PROXY"
        row["scoring_boundary"] = (
            "CURRENT_SOURCE_REPAIR_CLAIM_NOT_IMPLEMENTED_WHEN_SOURCE_COST_BOUNDS_ARE_ALL_NEGATIVE"
        )
        row["underlying_intelligence_preserved"] = True
        row["missed_opportunity_audit"] = {
            "kill_scope": "NOT_KILLED_REDESIGN_SOURCE_COST_REPAIR_ALL_NEGATIVE",
            "preserve_as": "SOURCE_COST_AVOID_INVERSE_CONTEXT_FILTER_OR_EXACT_SOURCE_REPAIR_REQUIREMENT",
            "unsupported_current_claim": "SOURCE_REPAIR_DEFAULT_OFF_IMPLEMENTATION_WITH_ALL_NEGATIVE_COST_BOUNDS",
            "what_was_tried": "JOINED_SOURCE_M15_ROW_TO_SOURCE_COST_CAP_ACQUISITION_DETAIL_RSTYLE_BOUNDS",
            "what_could_make_it_work": (
                "EXACT_SOURCE_ACQUISITION_OR_CONTEXT_SPLIT_THAT_SEPARATES_NEGATIVE_REPAIR_BRANCHES"
            ),
            "next_route": (
                "TEST_SOURCE_COST_REPAIR_ALL_NEGATIVE_ROWS_AS_AVOID_INVERSE_CONTEXT_FILTER_AND_SOURCE_REPAIR_REQUIREMENT"
            ),
        }
        return row

    row["source_cost_detail_repair_status"] = "REPAIR_SOURCE_COST_STRADDLE_PRESERVED"
    row["action_class"] = "PRESERVE_REQUIREMENT"
    row["coverage_status"] = "PRESERVED_SOURCE_COST_STRADDLE_EXACT_SOURCE_REQUIREMENT"
    row["branch_decision"] = PRESERVE_BRANCH
    row["implementation_decision"] = PRESERVE_BRANCH
    row["current_action"] = "PRESERVE_SOURCE_COST_STRADDLE_EXACT_ACQUISITION_REQUIREMENT"
    row["implementation_candidate"] = row["current_action"]
    row["next_action"] = row["current_action"]
    row["decision_evidence"] = "SOURCE_COST_DETAIL_REPAIR_BOUNDS_STRADDLE_ZERO"
    row["scoring_boundary"] = (
        "SOURCE_COST_STRADDLE_PROXY_MIDPOINT_REPORTED_BUT_IMPLEMENTATION_REQUIRES_EXACT_SOURCE_ACQUISITION"
    )
    row["underlying_intelligence_preserved"] = True
    row["missed_opportunity_audit"] = {
        "kill_scope": "NOT_KILLED_PRESERVE_SOURCE_COST_STRADDLE",
        "preserve_as": "EXACT_SOURCE_ACQUISITION_REQUIREMENT_OR_CONTEXT_SPLIT",
        "unsupported_current_claim": "SOURCE_REPAIR_DEFAULT_OFF_IMPLEMENTATION_WITH_STRADDLED_COST_BOUNDS",
        "what_was_tried": "JOINED_SOURCE_M15_ROW_TO_SOURCE_COST_CAP_ACQUISITION_DETAIL_RSTYLE_BOUNDS",
        "what_could_make_it_work": "EXACT_SOURCE_WINDOW_ACQUISITION_OR_STRONGER_STRESS_BOUNDS",
        "next_route": "ACQUIRE_EXACT_SOURCE_WINDOW_OR_SPLIT_STRADDLED_SOURCE_COST_CONTEXT",
    }
    return row


def materialize(input_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    source_rows = source_m15_by_row_id()
    cost_rows = source_cost_by_key()
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    generated = utc_now()
    for source in input_rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if not target_row(row):
            row["source_cost_detail_repair_status"] = "NOT_TARGET_ROW"
            output.append(row)
            continue
        source_m15 = source_rows.get(str(row.get("source_row_id") or ""))
        if not source_m15:
            row["source_cost_detail_repair_status"] = "SOURCE_M15_ROW_MISSING"
            stats["missing_source_m15_rows"] += 1
            output.append(row)
            continue
        key = (source_m15.get("source_branch_queue_id"), source_m15.get("target_stop_contract_id"))
        source_cost = cost_rows.get(key)
        if not source_cost:
            row["source_cost_detail_repair_status"] = "SOURCE_COST_DETAIL_ROW_MISSING"
            stats["missing_source_cost_rows"] += 1
            output.append(row)
            continue
        row = apply_source_cost_decision(row, source_m15, source_cost)
        stats["target_rows_joined"] += 1
        stats[str(row.get("source_cost_detail_repair_status"))] += 1
        stats[f"action_after_{row.get('action_class')}"] += 1
        midpoint = safe_float(row.get("after_proxy_r"))
        if midpoint is not None:
            stats["new_numeric_proxy_rows"] += 1
            if midpoint > 0:
                stats["positive_proxy_rows"] += 1
            elif midpoint < 0:
                stats["negative_proxy_rows"] += 1
        output.append(row)
    return output, dict(stats)


def build_manifest(output_paths: list[Path]) -> dict[str, Any]:
    inputs = [INPUT_LEDGER, INPUT_SUMMARY, SOURCE_M15_LEDGER, SOURCE_COST_DETAIL_LEDGER]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            str(path): {
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
            for path in inputs
        },
        "output_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in output_paths
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    input_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    output_rows, stats = materialize(input_rows)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    before = proxy_summary(input_rows)
    after = proxy_summary(output_rows)
    touched = [row for row in output_rows if row.get("source_cost_detail_repair_status") != "NOT_TARGET_ROW"]
    touched_values = [value for row in touched if (value := safe_float(row.get("after_proxy_r"))) is not None]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_SOURCE_COST_DETAIL_REPAIR",
        "claim_boundary": (
            "Consumes SOURCE cost-cap/acquisition detail R-style bounds into the action ledger. "
            "Accepted SOURCE rows remain default-off implementation candidates; all-negative repair rows "
            "become redesign/avoid candidates; straddled repair rows become exact-source requirements. "
            "No exact broker R/PnL, realized expectancy, validation, promotion, live-readiness, or live behavior is claimed."
        ),
        "rows": len(output_rows),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "action_class_counts_before": counter(input_rows, "action_class"),
        "action_class_counts_after": counter(output_rows, "action_class"),
        "action_class_delta_vs_previous": action_delta(
            counter(input_rows, "action_class"), counter(output_rows, "action_class")
        ),
        "numeric_proxy_rows_before": before["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after["numeric_proxy_rows"],
        "proxy_r_sum_before": before["proxy_r_sum"],
        "proxy_r_sum_after": after["proxy_r_sum"],
        "proxy_r_sum_delta": round(after["proxy_r_sum"] - before["proxy_r_sum"], 8),
        "touched_rows": len(touched),
        "source_cost_numeric_proxy_rows": len(touched_values),
        "source_cost_proxy_r_sum": round(sum(touched_values), 8),
        "source_cost_positive_proxy_rows": sum(1 for value in touched_values if value > 0),
        "source_cost_negative_proxy_rows": sum(1 for value in touched_values if value < 0),
        "source_cost_detail_repair_status_counts": counter(output_rows, "source_cost_detail_repair_status"),
        "source_cost_branch_counts": counter(touched, "branch_decision"),
        "source_cost_action_class_counts": counter(touched, "action_class"),
        "source_cost_scalar_permission_counts": counter(touched, "source_cost_detail_proxy_source_status"),
        "source_cost_interval_sign_counts": counter(touched, "source_cost_interval_sign_class"),
        "source_cost_target_stop_result_counts": counter(touched, "source_cost_target_stop_result"),
        "source_cost_candidate_counts": counter(touched, "candidate_id"),
        "source_cost_entry_variant_counts": counter(touched, "entry_variant"),
        "source_cost_symbol_session_counts": dict(
            Counter(f"{row.get('symbol')}|{row.get('route_session')}" for row in touched)
        ),
        "repair_stats": stats,
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "SOURCE_COST_DETAIL_PROXY_CONSUMED_INTO_ACTION_LEDGER",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "touched_rows": len(touched),
                "numeric_proxy_rows_after": after["numeric_proxy_rows"],
                "proxy_r_sum_after": after["proxy_r_sum"],
                "action_delta": summary["action_class_delta_vs_previous"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
