"""Materialize pending-lifecycle decision-spread source repair.

This plate consumes the current pending-limit lifecycle rows with the repaired
scorer behavior that reconstructs missing decision-spread fields from legacy
lifecycle spread values when that is the strongest same-evidence-class source.
It preserves all rows and R values; only source-completeness and row-level
implementation decisions can change.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(ROUTE_DIR)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.live_mechanical_shadow import (  # noqa: E402
    PENDING_LIMIT_STRATEGY_ID,
    PENDING_LIFECYCLE_CAPTURE_FIELDS,
    build_strategy_outcome_rows,
    latest_lifecycle_for_candidate_asof,
    latest_ltf_for_candidate_asof,
    latest_structural_metadata_by_candidate,
    merge_structural_metadata_candidate,
    read_jsonl as read_shadow_jsonl,
)


INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_KILL_SCOPE_PRESERVATION_AUDIT_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_KILL_SCOPE_PRESERVATION_AUDIT_SUMMARY_{DATE}.json"
SCORER_SOURCE = REPO_ROOT / "src/research_infra/live_mechanical_shadow.py"
TEST_SOURCE = REPO_ROOT / "tests/test_live_mechanical_shadow.py"

SHADOW_INPUTS = {
    "strategy_follow_candidates": REPO_ROOT / "shadow_logs/strategy_follow_candidates.jsonl",
    "candidate_path_follow": REPO_ROOT / "shadow_logs/candidate_path_follow.jsonl",
    "pending_limit_lifecycle": REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl",
    "candidate_ltf_path_order": REPO_ROOT / "shadow_logs/candidate_ltf_path_order.jsonl",
    "live_structural_strategy_metadata": REPO_ROOT / "shadow_logs/live_structural_strategy_metadata.jsonl",
}

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / (
    f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
)

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

RECONSTRUCTED_BRANCH = "KEEP_PENDING_LIFECYCLE_SCORER_WITH_RECONSTRUCTED_SOURCE_FIELDS_COMPLETE"
LEGACY_SPREAD_DERIVATION = "DERIVED_FROM_PENDING_LIFECYCLE_LEGACY_SPREAD_AS_DECISION_SPREAD_PROXY"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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


def nested_status_counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        statuses = row.get("pending_lifecycle_source_capture_statuses")
        if isinstance(statuses, dict):
            counts[str(statuses.get(field))] += 1
        else:
            counts["NO_PENDING_LIFECYCLE_STATUS_MAP"] += 1
    return dict(counts)


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {"numeric_proxy_rows": len(values), "proxy_r_sum": round(sum(values), 8)}


def pending_proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pending = [row for row in rows if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID]
    values = [value for row in pending if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "pending_rows": len(pending),
        "pending_numeric_proxy_rows": len(values),
        "pending_proxy_r_sum": round(sum(values), 8),
    }


def has_metadata_gap(row: dict[str, Any]) -> bool:
    return (
        row.get("decision_evidence") in (None, "")
        or row.get("scoring_boundary") in (None, "")
        or row.get("implementation_candidate") in (None, "")
        or str(row.get("current_action")) in {"None", "False", ""}
        or str(row.get("next_action")) in {"None", "False", ""}
    )


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, tuple[datetime, int, dict[str, Any]]] = {}
    for idx, row in enumerate(rows):
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        observed = (
            parse_utc(row.get("created_at_utc"))
            or parse_utc(row.get("backfilled_at_utc"))
            or datetime.min.replace(tzinfo=timezone.utc)
        )
        previous = latest.get(cid)
        if previous is None or (observed, idx) >= (previous[0], previous[1]):
            latest[cid] = (observed, idx, row)
    return {cid: item[2] for cid, item in latest.items()}


def latest_path_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, tuple[datetime, datetime, int, dict[str, Any]]] = {}
    for idx, row in enumerate(rows):
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        asof = parse_utc(row.get("asof_latest_candle_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        observed = parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        previous = latest.get(cid)
        if previous is None or (asof, observed, idx) >= (previous[0], previous[1], previous[2]):
            latest[cid] = (asof, observed, idx, row)
    return {cid: item[3] for cid, item in latest.items()}


def build_pending_recompute_map(generated_utc: str) -> dict[str, dict[str, Any]]:
    candidates = latest_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["strategy_follow_candidates"]))
    paths = latest_path_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["candidate_path_follow"]))
    pending_lifecycle_rows = read_shadow_jsonl(SHADOW_INPUTS["pending_limit_lifecycle"])
    ltf_rows = read_shadow_jsonl(SHADOW_INPUTS["candidate_ltf_path_order"])
    structural_metadata = latest_structural_metadata_by_candidate(
        read_shadow_jsonl(SHADOW_INPUTS["live_structural_strategy_metadata"])
    )
    recomputed: dict[str, dict[str, Any]] = {}
    for cid in sorted(candidates):
        candidate = merge_structural_metadata_candidate(candidates[cid], structural_metadata.get(cid))
        path = paths.get(cid)
        if not path:
            continue
        pending = latest_lifecycle_for_candidate_asof(candidate, path, pending_lifecycle_rows)
        ltf = latest_ltf_for_candidate_asof(candidate, path, ltf_rows)
        for row in build_strategy_outcome_rows(
            candidate,
            path,
            pending_lifecycle_row=pending,
            ltf_row=ltf,
            created_at_utc=generated_utc,
        ):
            if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID:
                recomputed[str(row.get("candidate_id") or "")] = row
    return recomputed


def mark_before(row: dict[str, Any]) -> None:
    for field in (
        "action_class",
        "branch_decision",
        "decision_evidence",
        "scoring_boundary",
        "implementation_candidate",
        "implementation_decision",
        "current_action",
        "next_action",
        "after_proxy_r",
        "pending_lifecycle_decision_spread_value_source_safe",
        "pending_lifecycle_decision_spread_unit",
        "pending_lifecycle_source_capture_statuses",
        "pending_lifecycle_source_capture_derivations",
        "pending_lifecycle_source_capture_complete",
    ):
        row[f"before_pending_decision_spread_repair_{field}"] = row.get(field)


def apply_pending_scorer(row: dict[str, Any], scorer_row: dict[str, Any]) -> None:
    row["pending_lifecycle_decision_spread_repair_scorer_source"] = (
        "src/research_infra/live_mechanical_shadow.py"
    )
    row["strategy_status"] = scorer_row.get("strategy_status")
    row["score_status"] = scorer_row.get("score_status")
    row["outcome_status"] = scorer_row.get("outcome_status")
    row["reason"] = scorer_row.get("reason")
    row["after_proxy_r"] = scorer_row.get("strategy_proxy_r")
    for field in (
        "branch_decision",
        "decision_evidence",
        "scoring_boundary",
        "implementation_candidate",
    ):
        row[field] = scorer_row.get(field)
    row["implementation_decision"] = scorer_row.get("branch_decision")
    row["current_action"] = scorer_row.get("implementation_candidate")
    row["next_action"] = scorer_row.get("implementation_candidate")
    for field in (
        "outcome_source",
        "pending_lifecycle_intent_after_check",
        "pending_lifecycle_fill_no_fill_label",
        "pending_lifecycle_source_timestamp_utc",
        "pending_lifecycle_checked_candle_time_utc",
        "pending_lifecycle_trade_id",
        "pending_lifecycle_candidate_id",
        "pending_lifecycle_match_method",
        "pending_lifecycle_source_capture_contract",
        "pending_lifecycle_source_capture_statuses",
        "pending_lifecycle_source_capture_derivations",
        "pending_lifecycle_source_capture_complete",
    ):
        if field in scorer_row:
            row[field] = scorer_row.get(field)
    for field in PENDING_LIFECYCLE_CAPTURE_FIELDS:
        prefixed = f"pending_lifecycle_{field}"
        if prefixed in scorer_row:
            row[prefixed] = scorer_row.get(prefixed)


def repair_status(row: dict[str, Any]) -> str:
    if row.get("strategy_id") != PENDING_LIMIT_STRATEGY_ID:
        return "NOT_PENDING_LIFECYCLE_ROW"
    statuses = row.get("pending_lifecycle_source_capture_statuses")
    if (
        row.get("branch_decision") == RECONSTRUCTED_BRANCH
        and isinstance(statuses, dict)
        and statuses.get("decision_spread_value_source_safe") == LEGACY_SPREAD_DERIVATION
    ):
        return "PENDING_LIFECYCLE_DECISION_SPREAD_REPAIRED_FROM_LEGACY_SPREAD_PROXY"
    return "PENDING_LIFECYCLE_RECOMPUTE_APPLIED_NO_DECISION_SPREAD_REPAIR"


def materialize_rows(
    rows: list[dict[str, Any]],
    recomputed: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    generated = utc_now()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if row.get("strategy_id") != PENDING_LIMIT_STRATEGY_ID:
            row["pending_lifecycle_decision_spread_repair_status"] = "NOT_PENDING_LIFECYCLE_ROW"
            output.append(row)
            continue
        stats["pending_rows"] += 1
        mark_before(row)
        scorer_row = recomputed.get(str(row.get("candidate_id") or ""))
        if scorer_row is None:
            row["pending_lifecycle_decision_spread_repair_status"] = "PENDING_LIFECYCLE_RECOMPUTE_MISSING"
            stats["recompute_missing"] += 1
            output.append(row)
            continue
        apply_pending_scorer(row, scorer_row)
        status = repair_status(row)
        row["pending_lifecycle_decision_spread_repair_status"] = status
        stats[status] += 1
        if row.get("before_pending_decision_spread_repair_branch_decision") != row.get("branch_decision"):
            stats["branch_changed"] += 1
        if row.get("before_pending_decision_spread_repair_after_proxy_r") != row.get("after_proxy_r"):
            stats["proxy_changed"] += 1
        if (
            row.get("before_pending_decision_spread_repair_pending_lifecycle_source_capture_complete")
            != row.get("pending_lifecycle_source_capture_complete")
        ):
            stats["source_capture_complete_changed"] += 1
        output.append(row)
    return output, dict(stats)


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


def build_manifest(output_paths: list[Path]) -> dict[str, Any]:
    inputs = [INPUT_LEDGER, INPUT_SUMMARY, SCORER_SOURCE, TEST_SOURCE, *SHADOW_INPUTS.values()]
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
    recomputed = build_pending_recompute_map(utc_now())
    output_rows, stats = materialize_rows(input_rows, recomputed)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    before_pending = pending_proxy_summary(input_rows)
    after_pending = pending_proxy_summary(output_rows)
    pending_rows = [row for row in output_rows if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID]
    kill_rows = [row for row in output_rows if row.get("action_class") == "KILL"]
    reconstructed_rows = [
        row
        for row in pending_rows
        if row.get("pending_lifecycle_decision_spread_repair_status")
        == "PENDING_LIFECYCLE_DECISION_SPREAD_REPAIRED_FROM_LEGACY_SPREAD_PROXY"
    ]

    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_REPAIR",
        "claim_boundary": (
            "Pending-limit lifecycle scorer source completeness after reconstructing current-row "
            "decision-spread fields from legacy lifecycle spread only where that same-evidence-class "
            "proxy exists. This does not promote exact R, validation safety, live behavior, or broker action."
        ),
        "rows": len(output_rows),
        "pending_rows": len(pending_rows),
        "decision_repair_stats": stats,
        "status_counts": counter(output_rows, "pending_lifecycle_decision_spread_repair_status"),
        "before_pending_branch_counts": counter(
            [row for row in input_rows if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID],
            "branch_decision",
        ),
        "after_pending_branch_counts": counter(pending_rows, "branch_decision"),
        "before_pending_source_complete_counts": counter(
            [row for row in input_rows if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID],
            "pending_lifecycle_source_capture_complete",
        ),
        "after_pending_source_complete_counts": counter(
            pending_rows,
            "pending_lifecycle_source_capture_complete",
        ),
        "before_pending_decision_spread_status_counts": nested_status_counter(
            [row for row in input_rows if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID],
            "decision_spread_value_source_safe",
        ),
        "after_pending_decision_spread_status_counts": nested_status_counter(
            pending_rows,
            "decision_spread_value_source_safe",
        ),
        "reconstructed_decision_spread_rows": len(reconstructed_rows),
        "reconstructed_decision_spread_candidates": sorted(
            str(row.get("candidate_id") or "") for row in reconstructed_rows
        ),
        "before_action_class_counts": input_summary.get("action_class_counts_after"),
        "after_action_class_counts": counter(output_rows, "action_class"),
        "all_metadata_gaps_after": sum(1 for row in output_rows if has_metadata_gap(row)),
        "kill_scope_audited_rows_after": sum(1 for row in kill_rows if kill_audit_present(row)),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "before_pending_proxy_summary": before_pending,
        "after_pending_proxy_summary": after_pending,
        "pending_proxy_r_sum_delta": round(
            after_pending["pending_proxy_r_sum"] - before_pending["pending_proxy_r_sum"], 8
        ),
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "PENDING_LIFECYCLE_DECISION_SPREAD_REPAIR_ACCEPTED_NO_R_CHANGE",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "pending_rows": len(pending_rows),
                "reconstructed_decision_spread_rows": len(reconstructed_rows),
                "pending_branch_counts": summary["after_pending_branch_counts"],
                "pending_decision_spread_status_counts": summary[
                    "after_pending_decision_spread_status_counts"
                ],
                "proxy_r_sum_after": summary["proxy_r_sum_after"],
                "pending_proxy_r_sum": after_pending["pending_proxy_r_sum"],
                "plate_decision": summary["plate_decision"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
