"""Materialize far-miss retest-control implementation decisions.

Consumes the repaired prefill/action queue and converts the only remaining
current REDESIGN rows into default-off implementation candidates when current
spread-aware tick replay already scored the 0.50R retest-control surface.
Research/tooling only: no shadow append, live behavior, validation, or
promotion claim.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


ROOT = find_repo_root(Path(__file__).resolve())
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization"

SOURCE_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_FAR_MISS_RETEST_CONTROL_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_FAR_MISS_RETEST_CONTROL_DECISION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_FAR_MISS_RETEST_CONTROL_DECISION_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

PREFILL_STRATEGY_ID = "PREFILL_DELIVERY_REVERSAL_PATH"
ENTRY_BRANCH_BEFORE = "REDESIGN_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL"
PREFILL_BRANCH_BEFORE = "REDESIGN_PREFILL_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL"
ENTRY_BRANCH_AFTER = "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_CHALLENGER"
PREFILL_BRANCH_AFTER = "IMPLEMENT_DEFAULT_OFF_PREFILL_FAR_MISS_RETEST_CONTROL_CHALLENGER"
ENTRY_IMPL_AFTER = "ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_DEFAULT_OFF_CHALLENGER"
PREFILL_IMPL_AFTER = "PREFILL_FAR_MISS_RETEST_CONTROL_DEFAULT_OFF_CHALLENGER_WITH_ENTRY_OFFSET_050R_SOURCE"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_info(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256(path) if path.exists() else None,
    }


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def candidate_date(candidate_id: str | None) -> str:
    if not candidate_id:
        return "UNKNOWN"
    match = re.search(r"\d{4}-\d{2}-\d{2}", candidate_id)
    return match.group(0) if match else "UNKNOWN"


def is_entry_owner_far_miss_positive(row: dict[str, Any]) -> bool:
    return (
        row.get("strategy_id") is None
        and row.get("action_class") == "REDESIGN"
        and row.get("branch_decision") == ENTRY_BRANCH_BEFORE
        and row.get("after_entry_score_status") == "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY"
        and row.get("after_entry_scorer_status") == "SCORED_ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_PROXY"
        and (safe_float(row.get("after_proxy_r")) or 0.0) > 0.0
    )


def is_prefill_far_miss_positive(row: dict[str, Any]) -> bool:
    return (
        row.get("strategy_id") == PREFILL_STRATEGY_ID
        and row.get("action_class") == "REDESIGN"
        and row.get("branch_decision") == PREFILL_BRANCH_BEFORE
        and row.get("linked_entry_offset_score_status") == "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY"
        and row.get("linked_entry_offset_outcome_status") == "TP1_AFTER_SHIFT_FILL"
        and (safe_float(row.get("linked_entry_offset_selected_proxy_r")) or 0.0) > 0.0
    )


def convert_row(row: dict[str, Any], generated: str) -> tuple[dict[str, Any], bool]:
    out = dict(row)
    out["before_far_miss_retest_control_action_class"] = row.get("action_class")
    out["before_far_miss_retest_control_branch_decision"] = row.get("branch_decision")
    out["before_far_miss_retest_control_implementation_candidate"] = row.get("implementation_candidate")
    out["generated_utc"] = generated
    out["safe_flags"] = SAFE_FLAGS
    if is_entry_owner_far_miss_positive(row):
        out.update(
            {
                "action_class": "IMPLEMENT_DEFAULT_OFF",
                "branch_decision": ENTRY_BRANCH_AFTER,
                "implementation_decision": ENTRY_BRANCH_AFTER,
                "implementation_candidate": ENTRY_IMPL_AFTER,
                "coverage_status": "IMPLEMENT_DEFAULT_OFF_WITH_CURRENT_POSITIVE_050R_RETEST_CONTROL_PROXY",
                "current_action": ENTRY_BRANCH_AFTER,
                "next_action": "KEEP_DEFAULT_OFF_FAR_MISS_RETEST_CONTROL_SCORER_WITH_CONCENTRATION_GUARD",
                "data_requirement_state": "SPREAD_AWARE_TICK_REPLAY_COMPLETE_PROXY_ONLY",
                "decision_evidence": (
                    "Current far-miss rows with complete spread-aware tick replay all fill the 0.50R shifted "
                    "entry and reach TP1; promote to default-off retest-control candidate with concentration guard."
                ),
                "scoring_boundary": "FAR_MISS_050R_RETEST_CONTROL_PROXY_DEFAULT_OFF_CONCENTRATION_GUARDED",
                "primitive_family": "entry_geometry_fillability_tick_path_ordering_retest_control",
                "concentration_guard": "N_LT_20_AND_8_OF_10_US30_CASH_SAME_DAY_NO_PROMOTION",
                "no_shadow_log_append": True,
                "no_promotion": True,
                "no_live_behavior": True,
            }
        )
        return out, True
    if is_prefill_far_miss_positive(row):
        out.update(
            {
                "action_class": "IMPLEMENT_DEFAULT_OFF",
                "branch_decision": PREFILL_BRANCH_AFTER,
                "implementation_decision": PREFILL_BRANCH_AFTER,
                "implementation_candidate": PREFILL_IMPL_AFTER,
                "coverage_status": "IMPLEMENT_DEFAULT_OFF_PREFILL_METADATA_LINKED_TO_ENTRY_OFFSET_RETEST_CONTROL",
                "current_action": PREFILL_BRANCH_AFTER,
                "next_action": "KEEP_PREFILL_METADATA_LINKED_TO_DEFAULT_OFF_RETEST_CONTROL_NO_DUPLICATE_R",
                "data_requirement_state": "PREFILL_METADATA_LINKED_TO_ENTRY_OFFSET_050R_RETEST_CONTROL_PROXY_NO_DUPLICATE_R",
                "decision_evidence": (
                    "Prefill far-miss metadata rows link to the entry-offset 0.50R retest-control scorer; proxy R "
                    "is owned by ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER and is not duplicated on prefill rows."
                ),
                "scoring_boundary": "PREFILL_METADATA_ONLY_LINKED_ENTRY_OFFSET_PROXY_NO_DUPLICATE_R",
                "primitive_family": "prefill_delivery_adverse_reversal_path_retest_control",
                "linked_entry_offset_proxy_r_owner": "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER",
                "concentration_guard": "N_LT_20_AND_8_OF_10_US30_CASH_SAME_DAY_NO_PROMOTION",
                "no_shadow_log_append": True,
                "no_promotion": True,
                "no_live_behavior": True,
            }
        )
        return out, True
    return out, False


def proxy_values(rows: list[dict[str, Any]]) -> list[float]:
    return [
        value
        for value in (safe_float(row.get("after_proxy_r")) for row in rows)
        if value is not None
    ]


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=lambda item: str(item))}


def build() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_rows = read_jsonl(SOURCE_LEDGER)
    generated = utc_now()
    out: list[dict[str, Any]] = []
    converted: list[dict[str, Any]] = []
    for row in source_rows:
        new, changed = convert_row(row, generated)
        out.append(new)
        if changed:
            converted.append(new)

    before_actions = Counter(row.get("action_class") for row in source_rows)
    after_actions = Counter(row.get("action_class") for row in out)
    before_branch = Counter(row.get("branch_decision") for row in source_rows)
    after_branch = Counter(row.get("branch_decision") for row in out)
    before_proxy_values = proxy_values(source_rows)
    after_proxy_values = proxy_values(out)
    entry_rows = [row for row in converted if row.get("strategy_id") is None]
    prefill_rows = [row for row in converted if row.get("strategy_id") == PREFILL_STRATEGY_ID]
    entry_proxy_values = proxy_values(entry_rows)
    prefill_target_before = [row for row in source_rows if row.get("strategy_id") == PREFILL_STRATEGY_ID]
    prefill_target_after = [row for row in out if row.get("strategy_id") == PREFILL_STRATEGY_ID]
    candidate_ids = sorted({row.get("candidate_id") for row in converted})
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": generated,
        "evidence_class": "MAIN_ORCH24_PREFILL_FAR_MISS_RETEST_CONTROL_DECISION",
        "claim_boundary": (
            "Versioned action queue that converts remaining far-miss retest-control redesign rows into "
            "default-off implementation candidates from current spread-aware tick replay. Exact R remains absent; "
            "prefill metadata does not duplicate entry-offset proxy R."
        ),
        "rows": len(out),
        "affected_rows": len(converted),
        "affected_candidate_rows": len(candidate_ids),
        "affected_candidate_ids": candidate_ids,
        "entry_offset_owner_rows": len(entry_rows),
        "prefill_metadata_rows": len(prefill_rows),
        "exact_r_rows": 0,
        "action_class_counts_before": counter_dict(before_actions),
        "action_class_counts_after": counter_dict(after_actions),
        "action_class_delta_vs_previous": {
            key: after_actions.get(key, 0) - before_actions.get(key, 0)
            for key in sorted(set(before_actions) | set(after_actions))
            if after_actions.get(key, 0) - before_actions.get(key, 0)
        },
        "branch_decision_counts_before": counter_dict(before_branch),
        "branch_decision_counts_after": counter_dict(after_branch),
        "redesign_rows_before": before_actions.get("REDESIGN", 0),
        "redesign_rows_after": after_actions.get("REDESIGN", 0),
        "prefill_target_action_class_counts_before": dict(
            counter_dict(Counter(row.get("action_class") for row in prefill_target_before))
        ),
        "prefill_target_action_class_counts_after": dict(
            counter_dict(Counter(row.get("action_class") for row in prefill_target_after))
        ),
        "numeric_proxy_rows_before": len(before_proxy_values),
        "numeric_proxy_rows_after": len(after_proxy_values),
        "proxy_r_sum_before": round(sum(before_proxy_values), 8),
        "proxy_r_sum_after": round(sum(after_proxy_values), 8),
        "proxy_r_sum_delta": round(sum(after_proxy_values) - sum(before_proxy_values), 8),
        "affected_entry_offset_proxy_rows": len(entry_proxy_values),
        "affected_entry_offset_proxy_r_sum": round(sum(entry_proxy_values), 8),
        "affected_entry_offset_proxy_r_mean": round(mean(entry_proxy_values), 8) if entry_proxy_values else None,
        "prefill_metadata_proxy_rows": 0,
        "prefill_metadata_proxy_r_sum": 0.0,
        "symbol_counts": dict(sorted(Counter(row.get("symbol") for row in entry_rows).items())),
        "candidate_date_counts": dict(sorted(Counter(candidate_date(row.get("candidate_id")) for row in entry_rows).items())),
        "concentration_guard": "N_LT_20; 8_OF_10_US30_CASH; 8_OF_10_ON_2026_05_08; NO_PROMOTION",
        "safe_flags": SAFE_FLAGS,
        "plate_decision": "REMAINING_FAR_MISS_RETEST_CONTROL_ROWS_CONVERTED_TO_DEFAULT_OFF_CANDIDATES",
    }
    return out, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "evidence_class": summary["evidence_class"],
        "generated_utc": summary["generated_utc"],
        "inputs": {
            "source_ledger": file_info(SOURCE_LEDGER),
            "live_mechanical_shadow": file_info(ROOT / "src/research_infra/live_mechanical_shadow.py"),
            "live_mechanical_shadow_tests": file_info(ROOT / "tests/test_live_mechanical_shadow.py"),
        },
        "outputs": {
            "ledger": file_info(OUTPUT_LEDGER),
            "summary": file_info(OUTPUT_SUMMARY),
        },
        "summary_counts": {
            "rows": summary["rows"],
            "affected_rows": summary["affected_rows"],
            "affected_candidate_rows": summary["affected_candidate_rows"],
            "action_class_delta_vs_previous": summary["action_class_delta_vs_previous"],
            "redesign_rows_after": summary["redesign_rows_after"],
            "affected_entry_offset_proxy_rows": summary["affected_entry_offset_proxy_rows"],
            "affected_entry_offset_proxy_r_sum": summary["affected_entry_offset_proxy_r_sum"],
            "proxy_r_sum_delta": summary["proxy_r_sum_delta"],
            "exact_r_rows": summary["exact_r_rows"],
        },
        "safe_flags": summary["safe_flags"],
    }


def main() -> None:
    rows, summary = build()
    write_jsonl(OUTPUT_LEDGER, rows)
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MANIFEST.write_text(json.dumps(build_manifest(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
