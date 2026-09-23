"""Repair conservative kill labels in the current action ledger.

This plate consumes the post-pending-tick action ledger and relabels accepted
SOURCE branches that were conservatively marked KILL_OR_AVOID even though the
current evidence preserves an exact-source repair / avoid-redesign requirement.
It does not change proxy R, exact R, live behavior, or shadow logs.
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


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(ROUTE_DIR)

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_KILL_LABEL_SCOPE_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_KILL_LABEL_SCOPE_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_KILL_LABEL_SCOPE_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

SOURCE_BRANCH = "KILL_OR_AVOID_ACCEPTED_SOURCE_BRANCH_UNTIL_EXACT_SOURCE_REPAIR"
REPAIRED_BRANCH = "PRESERVE_ACCEPTED_SOURCE_BRANCH_EXACT_TICK_REPAIR_OR_AVOID_REDESIGN"
TARGET_PRIMITIVE = "source_cost_spread_bar_proxy_implication"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
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
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "") for row in rows))


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "proxy_r_mean": round(sum(values) / len(values), 8) if values else None,
    }


def kill_audit_present(row: dict[str, Any]) -> bool:
    audit = row.get("missed_opportunity_audit")
    return (
        row.get("claim_decision_scope") == "CURRENT_STRATEGY_CLAIM_ONLY_UNDERLYING_INTELLIGENCE_PRESERVED"
        and row.get("underlying_intelligence_preserved") is True
        and isinstance(audit, dict)
        and audit.get("kill_scope") == "CURRENT_CLAIM_ONLY"
        and bool(audit.get("what_was_tried"))
        and bool(audit.get("what_could_make_it_work"))
        and bool(audit.get("preserve_as"))
        and bool(audit.get("next_route"))
    )


def is_target_row(row: dict[str, Any]) -> bool:
    return (
        row.get("primitive_family") == TARGET_PRIMITIVE
        and row.get("action_class") == "KILL"
        and row.get("branch_decision") == SOURCE_BRANCH
    )


def repair_row(source: dict[str, Any], generated_utc: str) -> tuple[dict[str, Any], bool]:
    row = {key: value for key, value in source.items() if key != "_source_line_no"}
    row["generated_utc"] = generated_utc
    if not is_target_row(row):
        row["kill_label_scope_repair_status"] = "NOT_TARGET_ROW"
        return row, False

    row["before_kill_label_scope_repair_action_class"] = row.get("action_class")
    row["before_kill_label_scope_repair_branch_decision"] = row.get("branch_decision")
    row["before_kill_label_scope_repair_current_action"] = row.get("current_action")
    row["before_kill_label_scope_repair_next_action"] = row.get("next_action")
    row["before_kill_label_scope_repair_implementation_decision"] = row.get("implementation_decision")
    row["before_kill_label_scope_repair_coverage_status"] = row.get("coverage_status")
    row["before_kill_label_scope_repair_data_requirement_state"] = row.get("data_requirement_state")

    row["action_class"] = "PRESERVE_REQUIREMENT"
    row["branch_decision"] = REPAIRED_BRANCH
    row["implementation_decision"] = REPAIRED_BRANCH
    row["implementation_candidate"] = (
        "PRESERVE_EXACT_TICK_SOURCE_REPAIR_AND_EVALUATE_AVOID_REDESIGN_FOR_ACCEPTED_SOURCE_BRANCH"
    )
    row["current_action"] = row["implementation_candidate"]
    row["next_action"] = row["implementation_candidate"]
    row["coverage_status"] = "PRESERVED_REQUIREMENT_AFTER_KILL_SCOPE_REPAIR"
    row["data_requirement_state"] = (
        "EXACT_TICK_SOURCE_REPAIR_REQUIRED_AFTER_BAR_SPREAD_PROXY_DEGRADES_ACCEPTED_SOURCE_BRANCH"
    )
    row["decision_evidence"] = (
        "BAR_SPREAD_PROXY_DEGRADED_ACCEPTED_SOURCE_BRANCH_BUT_DOES_NOT_CONTRADICT_UNDERLYING_SOURCE_MECHANISM"
    )
    row["scoring_boundary"] = (
        "NO_KILL_WITHOUT_EXACT_SOURCE_REPAIR_OR_NEGATIVE_ORDERING_PROXY; "
        "PRESERVE_AS_SOURCE_REPAIR_OR_AVOID_REDESIGN"
    )
    row["claim_decision_scope"] = "NOT_KILLED_ACCEPTED_SOURCE_BRANCH_PRESERVED_FOR_REPAIR_OR_AVOID_REDESIGN"
    row["underlying_intelligence_preserved"] = True
    row["current_claim_proxy_counted"] = False
    row["kill_scope_preservation_audit_status"] = (
        "KILL_LABEL_REMOVED_PRESERVED_REQUIREMENT_AFTER_DOCTRINE_CORRECTION"
    )
    row["kill_label_scope_repair_status"] = "RELABELED_KILL_OR_AVOID_AS_PRESERVE_REQUIREMENT"
    row["missed_opportunity_audit"] = {
        "kill_scope": "NOT_KILLED_RELABELED_PRESERVE_REQUIREMENT",
        "what_was_tried": (
            "BAR_SPREAD_PROXY_RECOMPUTE_OF_ACCEPTED_SOURCE_BRANCH_WITH_M15_ORDERING_WHERE_AVAILABLE"
        ),
        "unsupported_current_claim": "DEFAULT_OFF_SOURCE_BRANCH_IMPLEMENTATION_FROM_BAR_SPREAD_PROXY_ALONE",
        "what_could_make_it_work": (
            "EXACT_TICK_OR_QUOTE_ORDERING_SPREAD_REPLAY_FOR_THE_SOURCE_BRANCH_EVENT_WINDOW"
        ),
        "preserve_as": (
            "SOURCE_CAPTURE_REQUIREMENT_OR_AVOID_REDESIGN_CANDIDATE_NOT_CURRENT_STRATEGY_KILL"
        ),
        "next_route": "EXACT_TICK_SOURCE_REPAIR_OR_AVOID_FILTER_REDESIGN_WITH_SOURCE_BRANCH_DENOMINATOR",
    }
    return row, True


def materialize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    generated = utc_now()
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    for source in rows:
        row, changed = repair_row(source, generated)
        if changed:
            stats["kill_or_avoid_source_rows_relabelled_to_preserve_requirement"] += 1
        output.append(row)
    return output, dict(stats)


def branch_count(rows: list[dict[str, Any]], branch: str, action_class: str | None = None) -> int:
    return sum(
        1
        for row in rows
        if row.get("branch_decision") == branch
        and (action_class is None or row.get("action_class") == action_class)
    )


def build_manifest(output_paths: list[Path]) -> dict[str, Any]:
    inputs = [INPUT_LEDGER, INPUT_SUMMARY]
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
    output_rows, stats = materialize(input_rows)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    before_actions = counter(input_rows, "action_class")
    after_actions = counter(output_rows, "action_class")
    kill_rows_after = [row for row in output_rows if row.get("action_class") == "KILL"]
    source_rows_after = [row for row in output_rows if row.get("primitive_family") == TARGET_PRIMITIVE]
    relabelled_rows = [
        row
        for row in output_rows
        if row.get("kill_label_scope_repair_status") == "RELABELED_KILL_OR_AVOID_AS_PRESERVE_REQUIREMENT"
    ]

    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_KILL_LABEL_SCOPE_REPAIR",
        "claim_boundary": (
            "Relabels accepted SOURCE branches that carried a conservative KILL_OR_AVOID label into "
            "preserved exact-source repair / avoid-redesign requirements. Proxy R and exact R are unchanged; "
            "no live behavior, shadow append, validation, promotion, broker operation, or AI/API call is opened."
        ),
        "rows": len(output_rows),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "action_class_counts_before": before_actions,
        "action_class_counts_after": after_actions,
        "action_class_delta_vs_previous": {
            key: after_actions.get(key, 0) - before_actions.get(key, 0)
            for key in sorted(set(before_actions) | set(after_actions))
            if after_actions.get(key, 0) != before_actions.get(key, 0)
        },
        "source_cost_spread_action_counts_after": counter(source_rows_after, "action_class"),
        "repair_stats": stats,
        "remaining_kill_or_avoid_kill_labels": branch_count(output_rows, SOURCE_BRANCH, "KILL"),
        "preserved_source_branch_requirement_rows": branch_count(output_rows, REPAIRED_BRANCH, "PRESERVE_REQUIREMENT"),
        "remaining_kill_rows": len(kill_rows_after),
        "remaining_kill_rows_with_scope_audit": sum(1 for row in kill_rows_after if kill_audit_present(row)),
        "relabelled_rows_have_missed_opportunity_audit": sum(
            1 for row in relabelled_rows if isinstance(row.get("missed_opportunity_audit"), dict)
        ),
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "CONSERVATIVE_KILL_OR_AVOID_SOURCE_LABELS_REPAIRED_TO_PRESERVE_REQUIREMENT",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "relabelled_rows": len(relabelled_rows),
                "proxy_r_sum_after": after_proxy["proxy_r_sum"],
                "summary": str(OUTPUT_SUMMARY),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
