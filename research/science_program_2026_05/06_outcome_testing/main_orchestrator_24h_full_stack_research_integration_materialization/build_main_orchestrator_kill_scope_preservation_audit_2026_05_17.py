"""Repair kill rows so every kill is current-claim scoped.

The owner clarified that KILL must not mean deleting uncertainty or mechanism
intelligence. This plate preserves all rows and R values while requiring every
KILL action row to carry a missed-opportunity audit that states the unsupported
current claim, what evidence contradicted it, what could make it work, and how
the underlying intelligence should be preserved or redesigned.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_SOURCE_BUCKET_SCORER_DECISION_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_SOURCE_BUCKET_SCORER_DECISION_SUMMARY_{DATE}.json"
SCORER_SOURCE = Path("src/research_infra/live_mechanical_shadow.py")
TEST_SOURCE = Path("tests/test_live_mechanical_shadow.py")

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_KILL_SCOPE_PRESERVATION_AUDIT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_KILL_SCOPE_PRESERVATION_AUDIT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_KILL_SCOPE_PRESERVATION_AUDIT_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(ROUTE_DIR)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
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
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter("" if row.get(field) is None else str(row.get(field)) for row in rows))


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {"numeric_proxy_rows": len(values), "proxy_r_sum": round(sum(values), 8)}


def has_metadata_gap(row: dict[str, Any]) -> bool:
    return (
        row.get("decision_evidence") in (None, "")
        or row.get("scoring_boundary") in (None, "")
        or row.get("implementation_candidate") in (None, "")
        or str(row.get("current_action")) in {"None", "False", ""}
        or str(row.get("next_action")) in {"None", "False", ""}
    )


def kill_audit_present(row: dict[str, Any]) -> bool:
    audit = row.get("missed_opportunity_audit")
    return (
        row.get("claim_decision_scope")
        == "CURRENT_STRATEGY_CLAIM_ONLY_UNDERLYING_INTELLIGENCE_PRESERVED"
        and row.get("underlying_intelligence_preserved") is True
        and isinstance(audit, dict)
        and audit.get("kill_scope") == "CURRENT_CLAIM_ONLY"
        and bool(audit.get("what_was_tried"))
        and bool(audit.get("what_could_make_it_work"))
        and bool(audit.get("preserve_as"))
        and bool(audit.get("next_route"))
    )


def audit_for_branch(row: dict[str, Any]) -> dict[str, Any] | None:
    branch = str(row.get("branch_decision") or "")
    evidence = str(row.get("decision_evidence") or branch)
    strategy = str(row.get("strategy_id") or row.get("source_plate") or "UNKNOWN")
    if branch == "KILL_ROW_NOT_SWING_PROTECTED_STOP":
        return {
            "kill_scope": "CURRENT_CLAIM_ONLY",
            "current_claim": "SWING_PROTECTED_STOP_SCORER",
            "unsupported_reason": evidence,
            "what_was_tried": "CHECKED_CANDIDATE_STOP_AGAINST_CAPTURED_SIDE_COMPATIBLE_PROTECTED_SWING",
            "what_could_make_it_work": "STOP_PROTECTS_SIDE_COMPATIBLE_SWING_OR_REDESIGNED_SWING_LEVEL_BINDING",
            "preserve_as": "SWING_DISTANCE_STOP_PLACEMENT_CONTEXT_OR_AVOID_FILTER",
            "next_route": "ISOLATE_SWING_PROTECTION_FAILURE_BY_SYMBOL_SESSION_SIDE_AND_REDESIGN_STOP_LEVEL_BINDING",
        }
    if branch == "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL":
        return {
            "kill_scope": "CURRENT_CLAIM_ONLY",
            "current_claim": "ENTRY_OFFSET_050R_SPREAD_AWARE_SHIFT_FILL",
            "unsupported_reason": evidence,
            "what_was_tried": "SPREAD_AWARE_OR_M15_REPAIRED_050R_ENTRY_OFFSET_REPLAY",
            "what_could_make_it_work": "WIDER_RETEST_OFFSET_OR_MARKET_CONTROL_STATE_THAT_REACHES_FILL_BEFORE_TARGET_AREA",
            "preserve_as": "FAR_MISS_RETEST_CONTROL_REDESIGN_OR_AVOID_CONTEXT",
            "next_route": "TEST_WIDER_RETEST_OFFSETS_AND_MARKET_CONTROL_BUCKETS_FOR_FAR_MISS_ROWS",
        }
    if branch == "KILL_PREFILL_050R_OFFSET_NO_FILL_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL":
        return {
            "kill_scope": "CURRENT_CLAIM_ONLY",
            "current_claim": "PREFILL_ENTRY_OFFSET_050R_RETEST_CONTROL_FILL",
            "unsupported_reason": evidence,
            "what_was_tried": "LINKED_PREFILL_METADATA_TO_ENTRY_OFFSET_050R_REPLAY_OR_M15_HARD_NO_FILL_PROOF",
            "what_could_make_it_work": "WIDER_RETEST_OFFSET_OR_MARKET_CONTROL_STATE_THAT_REACHES_FILL_BEFORE_TARGET_AREA",
            "preserve_as": "PREFILL_FAR_MISS_RETEST_CONTROL_REDESIGN_OR_AVOID_CONTEXT",
            "next_route": "TEST_PREFILL_FAR_MISS_BY_SYMBOL_SESSION_SPREAD_DISTANCE_AND_OFFSET_GRID",
        }
    if branch == "KILL_OR_AVOID_ACCEPTED_SOURCE_BRANCH_UNTIL_EXACT_SOURCE_REPAIR":
        return {
            "kill_scope": "CURRENT_CLAIM_ONLY",
            "current_claim": f"{strategy}_ACCEPTED_SOURCE_BRANCH",
            "unsupported_reason": evidence,
            "what_was_tried": "SOURCE_BRANCH_RECOMPUTE_WITH_CURRENT_ACCEPTED_SOURCE_EVIDENCE",
            "what_could_make_it_work": "EXACT_SOURCE_REPAIR_OR_PROXY_RECONSTRUCTION_THAT_REMOVES_CURRENT_CONTRADICTION",
            "preserve_as": "SOURCE_REPAIR_REQUIREMENT_AVOID_FILTER_OR_CONTEXT_FEATURE",
            "next_route": "REPAIR_EXACT_SOURCE_OR_TEST_AS_AVOID_INVERSE_CONTEXT_BEFORE_FINAL KILL",
        }
    if branch == "KILL_SOURCE_REPAIR_UPGRADED_CHALLENGER_AFTER_ORDERING_NEGATIVE_PROXY":
        return {
            "kill_scope": "CURRENT_CLAIM_ONLY",
            "current_claim": f"{strategy}_UPGRADED_CHALLENGER",
            "unsupported_reason": evidence,
            "what_was_tried": "SOURCE_REPAIR_UPGRADED_CHALLENGER_RECOMPUTED_WITH_ORDERING_PROXY",
            "what_could_make_it_work": "MARKET_SESSION_TIMEFRAME_OR_SOURCE_CONDITION_WHERE_ORDERING_PROXY_TURNS POSITIVE",
            "preserve_as": "NEGATIVE_PROXY_AVOID_INVERSE_OR_SPECIALIZATION_FEATURE",
            "next_route": "ISOLATE_NEGATIVE_ORDERING_PROXY_BY_MARKET_SESSION_TIMEFRAME_AND_TEST_AVOID_INVERSE",
        }
    return None


def materialize_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    generated = utc_now()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if row.get("action_class") != "KILL":
            row["kill_scope_preservation_audit_status"] = "NOT_KILL_ROW"
            output.append(row)
            continue
        stats["kill_rows"] += 1
        if kill_audit_present(row):
            row["kill_scope_preservation_audit_status"] = "KILL_SCOPE_AUDIT_ALREADY_PRESENT"
            stats["kill_scope_audit_already_present"] += 1
            output.append(row)
            continue
        audit = audit_for_branch(row)
        if audit is None:
            row["kill_scope_preservation_audit_status"] = "KILL_SCOPE_AUDIT_MAPPING_MISSING"
            stats["kill_scope_audit_mapping_missing"] += 1
            output.append(row)
            continue
        row["before_kill_scope_preservation_claim_decision_scope"] = row.get("claim_decision_scope")
        row["before_kill_scope_preservation_missed_opportunity_audit"] = row.get("missed_opportunity_audit")
        row["claim_decision_scope"] = "CURRENT_STRATEGY_CLAIM_ONLY_UNDERLYING_INTELLIGENCE_PRESERVED"
        row["underlying_intelligence_preserved"] = True
        row["current_claim_proxy_counted"] = row.get("after_proxy_r") is not None
        row["preserved_current_claim_proxy_r"] = row.get("after_proxy_r")
        row["missed_opportunity_audit"] = audit
        row["kill_scope_preservation_audit_status"] = "KILL_SCOPE_AUDIT_REPAIRED_FROM_BRANCH_DECISION"
        stats["kill_scope_audit_repaired"] += 1
        output.append(row)
    return output, dict(stats)


def build_manifest(output_paths: list[Path]) -> dict[str, Any]:
    inputs = [
        INPUT_LEDGER,
        INPUT_SUMMARY,
        REPO_ROOT / SCORER_SOURCE,
        REPO_ROOT / TEST_SOURCE,
    ]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            str(path.relative_to(REPO_ROOT)): {
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
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
    output_rows, stats = materialize_rows(input_rows)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    kill_rows = [row for row in output_rows if row.get("action_class") == "KILL"]
    audited_kills = [row for row in kill_rows if kill_audit_present(row)]
    preserved_proxy_values = [
        value
        for row in audited_kills
        for value in (
            safe_float(row.get("preserved_candidate_path_proxy_r")),
            safe_float(row.get("preserved_current_claim_proxy_r")),
        )
        if value is not None
    ]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_KILL_SCOPE_PRESERVATION_AUDIT",
        "claim_boundary": (
            "Row-level repair enforcing the owner correction that kill decisions only kill unsupported "
            "current claims while preserving mechanism intelligence, redesign paths, source requirements, "
            "avoid/inverse routes, and context features. No R values, live behavior, promotion, broker "
            "operation, or AI/API call is opened."
        ),
        "rows": len(output_rows),
        "kill_rows": len(kill_rows),
        "kill_audit_rows_after": len(audited_kills),
        "kill_audit_rows_before": stats.get("kill_scope_audit_already_present", 0),
        "kill_audit_rows_repaired": stats.get("kill_scope_audit_repaired", 0),
        "kill_audit_mapping_missing": stats.get("kill_scope_audit_mapping_missing", 0),
        "kill_scope_preservation_status_counts": counter(output_rows, "kill_scope_preservation_audit_status"),
        "kill_branch_counts": counter(kill_rows, "branch_decision"),
        "preserved_proxy_rows_from_kill_audits": len(preserved_proxy_values),
        "preserved_proxy_r_sum_from_kill_audits": round(sum(preserved_proxy_values), 8),
        "action_class_counts_after": counter(output_rows, "action_class"),
        "all_metadata_gaps_after": sum(1 for row in output_rows if has_metadata_gap(row)),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "ALL_CURRENT_KILL_ROWS_ARE_CLAIM_SCOPED_WITH_MISSED_OPPORTUNITY_AUDITS",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "kill_rows": len(kill_rows),
                "kill_audit_rows_after": len(audited_kills),
                "summary": str(OUTPUT_SUMMARY),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
