"""Materialize bucketed prefill delivery scorer/action decisions.

This is a research-only action-queue refresh. It consumes the latest committed
action ledger and replaces the generic prefill delivery no-scorer rows with
current bucketed scorer output from ``live_mechanical_shadow``. It deliberately
does not duplicate entry-offset proxy R on the prefill rows.
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


REPO_ROOT = find_repo_root(Path(__file__).resolve())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.live_mechanical_shadow import (
    PREFILL_DELIVERY_STRATEGY_ID,
    build_strategy_outcome_rows,
    latest_path_rows_by_candidate,
    read_jsonl,
)


DATE = "2026-05-17"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

INPUT_ACTION_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR_LEDGER_2026-05-17.jsonl"
)
INPUT_STRATEGY_FOLLOW = Path("shadow_logs/strategy_follow_candidates.jsonl")
INPUT_PATH_FOLLOW = Path("shadow_logs/candidate_path_follow.jsonl")
INPUT_LIVE_MECHANICAL_SOURCE = Path("src/research_infra/live_mechanical_shadow.py")
INPUT_LIVE_MECHANICAL_TESTS = Path("tests/test_live_mechanical_shadow.py")
INPUT_LINKED_ENTRY_OFFSET_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_PREFILL_DELIVERY_ADVERSE_REDESIGN_INTEGRATION_LEDGER_2026-05-16.jsonl"
)
INPUT_LINKED_ENTRY_OFFSET_SUMMARY = (
    ROUTE_DIR / "MAIN_ORCH24_PREFILL_DELIVERY_ADVERSE_REDESIGN_INTEGRATION_SUMMARY_2026-05-16.json"
)

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_BUCKETED_SCORER_OUTPUT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_BUCKETED_SCORER_OUTPUT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = (
    ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_BUCKETED_SCORER_OUTPUT_OUTPUT_MANIFEST_{DATE}.json"
)

GENERIC_IMPL = "REDESIGN_PREFILL_DELIVERY_REVERSAL_PATH_SCORER"
GENERIC_BRANCH = "REDESIGN_REQUIRED_NO_SCORER"
GENERIC_BOUNDARY = "NO_SHARED_ENTRY_PROXY_FOR_PREFILL_DELIVERY_REVERSAL_PATH"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value: Any) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current = parse_utc(row.get("created_at_utc"))
        previous = parse_utc(latest.get(cid, {}).get("created_at_utc"))
        if current >= previous:
            latest[cid] = row
    return latest


def latest_path_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("candidate_id") or ""): row
        for row in latest_path_rows_by_candidate(rows)
        if row.get("candidate_id")
    }


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def proxy_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [safe_float(row.get("after_proxy_r")) for row in rows]
    numeric = [value for value in values if value is not None]
    total = round(sum(numeric), 8)
    return {
        "numeric_proxy_rows": len(numeric),
        "proxy_r_sum": total,
        "proxy_r_mean": round(total / len(numeric), 8) if numeric else None,
    }


def linked_entry_offset_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = read_jsonl(INPUT_LINKED_ENTRY_OFFSET_LEDGER)
    summary = read_json(INPUT_LINKED_ENTRY_OFFSET_SUMMARY)
    return rows, summary


def scorer_row_for(
    *,
    source_row: dict[str, Any],
    candidates: dict[str, dict[str, Any]],
    paths: dict[str, dict[str, Any]],
    generated: str,
) -> dict[str, Any] | None:
    cid = str(source_row.get("candidate_id") or "")
    candidate = candidates.get(cid)
    path = paths.get(cid)
    if not candidate or not path:
        return None
    for row in build_strategy_outcome_rows(candidate, path, created_at_utc=generated):
        if row.get("strategy_id") == PREFILL_DELIVERY_STRATEGY_ID:
            return row
    return None


def action_for_scorer(scorer: dict[str, Any]) -> tuple[str, str, str, str]:
    status = str(scorer.get("strategy_status") or "")
    if status == "NOT_APPLICABLE_NOT_PREFILL_REDESIGN_DENOMINATOR":
        return (
            "KEEP",
            "KEEP_CURRENT_ENTRY_MODEL_NOT_IN_PREFILL_REDESIGN_DENOMINATOR",
            "KEPT_OUTSIDE_PREFILL_REDESIGN_DENOMINATOR",
            "NOT_APPLICABLE_OUTSIDE_NO_FILL_TP1_PREFILL_REDESIGN_DENOMINATOR",
        )
    if status == "REDESIGN_PREFILL_NEAR_MISS_ENTRY_OFFSET_050R_CHALLENGER":
        return (
            "IMPLEMENT_DEFAULT_OFF",
            "IMPLEMENT_DEFAULT_OFF_PREFILL_NEAR_MISS_ENTRY_OFFSET_050R_CHALLENGER",
            "IMPLEMENTATION_CANDIDATE_LINKED_ENTRY_OFFSET_SCORER_NO_DUPLICATE_PREFILL_R",
            "METADATA_ONLY_PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_SCORER",
        )
    if status == "REDESIGN_PREFILL_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL":
        return (
            "REDESIGN",
            "REDESIGN_PREFILL_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL",
            "REDESIGN_CONTROL_BUCKET_NOT_DEFAULT_ENTRY",
            "METADATA_ONLY_RETEST_REDESIGN_CONTROL_PROXY_R_NOT_ASSIGNED",
        )
    return (
        "SOURCE_REPAIR",
        "SOURCE_REPAIR_REQUIRED_PREFILL_ENTRY_REDESIGN_BUCKET",
        "SOURCE_REPAIR_REQUIRED_FOR_PREFILL_BUCKET_ROUTING",
        "SOURCE_REPAIR_REQUIRED_PREFILL_ENTRY_DISTANCE_BUCKET",
    )


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    source_rows = read_jsonl(INPUT_ACTION_LEDGER)
    candidates = latest_by_candidate(read_jsonl(INPUT_STRATEGY_FOLLOW))
    paths = latest_path_by_candidate(read_jsonl(INPUT_PATH_FOLLOW))
    linked_rows, linked_summary = linked_entry_offset_rows()
    linked_by_candidate = {
        str(row.get("candidate_id") or ""): row for row in linked_rows if row.get("candidate_id")
    }

    out: list[dict[str, Any]] = []
    target_rows = 0
    target_missing_inputs = 0
    bucket_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    score_counts: Counter[str] = Counter()
    branch_counts: Counter[str] = Counter()
    target_action_counts: Counter[str] = Counter()
    target_impl_counts: Counter[str] = Counter()
    linked_no_fill_action_counts: Counter[str] = Counter()
    linked_no_fill_branch_counts: Counter[str] = Counter()

    for idx, row in enumerate(source_rows, start=1):
        new = dict(row)
        if row.get("strategy_id") != PREFILL_DELIVERY_STRATEGY_ID:
            new["prefill_bucketed_scorer_status"] = "NOT_TARGET_ROW"
            out.append(new)
            continue

        target_rows += 1
        scorer = scorer_row_for(
            source_row=row,
            candidates=candidates,
            paths=paths,
            generated=generated,
        )
        new["source_line_no"] = row.get("source_line_no") or idx
        new["before_action_class"] = row.get("action_class")
        new["before_implementation_decision"] = row.get("implementation_decision")
        new["before_branch_decision"] = row.get("branch_decision")
        new["before_scoring_boundary"] = row.get("scoring_boundary")
        new["before_proxy_r"] = row.get("after_proxy_r")
        new["generated_utc"] = generated
        new["safe_flags"] = SAFE_FLAGS
        new["no_promotion"] = True
        new["no_live_behavior"] = True
        new["no_shadow_log_append"] = True
        new["exact_r"] = None
        new["after_proxy_r"] = None
        new["proxy_r_delta"] = None
        new["selected_shift_proxy_r"] = None
        new["selected_shift_r"] = None
        new["selected_shift_status"] = None
        new["source_capture_surface"] = "prefill_delivery_bucketed_scorer_output"
        new["primitive_family"] = "prefill_delivery_adverse_reversal_path"
        new["source_artifact"] = str(INPUT_LIVE_MECHANICAL_SOURCE)

        linked = linked_by_candidate.get(str(row.get("candidate_id") or "")) or {}
        if linked.get("prefill_adverse_no_fill_denominator") is True:
            linked_no_fill_action_counts[str(linked.get("action_class") or "")] += 1
            linked_no_fill_branch_counts[str(linked.get("branch_decision") or "")] += 1
        new["linked_entry_offset_action_class"] = linked.get("action_class")
        new["linked_entry_offset_branch_decision"] = linked.get("branch_decision")
        new["linked_entry_offset_selected_proxy_r"] = linked.get("selected_proxy_r")
        new["linked_entry_offset_score_status"] = linked.get("score_status")
        new["linked_entry_offset_outcome_status"] = linked.get("outcome_status")

        if scorer is None:
            target_missing_inputs += 1
            new.update(
                {
                    "prefill_bucketed_scorer_status": "INPUT_MISSING",
                    "action_class": "SOURCE_REPAIR",
                    "implementation_decision": "SOURCE_REPAIR_REQUIRED_PREFILL_CANDIDATE_OR_PATH_INPUT_MISSING",
                    "coverage_status": "SOURCE_REPAIR_REQUIRED_FOR_PREFILL_BUCKET_ROUTING",
                    "current_action": "REPAIR_MISSING_PREFILL_CANDIDATE_OR_PATH_INPUT",
                    "next_action": "REPAIR_MISSING_PREFILL_CANDIDATE_OR_PATH_INPUT",
                    "data_requirement_state": "SOURCE_REPAIR_REQUIRED_PREFILL_INPUT_MISSING",
                }
            )
            out.append(new)
            continue

        action_class, implementation_decision, coverage_status, data_state = action_for_scorer(scorer)
        bucket = str(scorer.get("entry_retest_redesign_bucket") or "")
        status_counts[str(scorer.get("strategy_status") or "")] += 1
        score_counts[str(scorer.get("score_status") or "")] += 1
        bucket_counts[bucket] += 1
        branch_counts[str(scorer.get("branch_decision") or "")] += 1
        target_action_counts[action_class] += 1
        target_impl_counts[implementation_decision] += 1

        new.update(
            {
                "prefill_bucketed_scorer_status": "REPAIRED_BUCKETED_SCORER_OUTPUT",
                "action_class": action_class,
                "implementation_decision": implementation_decision,
                "coverage_status": coverage_status,
                "current_action": implementation_decision,
                "next_action": scorer.get("implementation_candidate"),
                "data_requirement_state": data_state,
                "after_strategy_status": scorer.get("strategy_status"),
                "after_score_status": scorer.get("score_status"),
                "after_outcome_status": scorer.get("outcome_status"),
                "branch_decision": scorer.get("branch_decision"),
                "decision_evidence": scorer.get("decision_evidence"),
                "scoring_boundary": scorer.get("scoring_boundary"),
                "implementation_candidate": scorer.get("implementation_candidate"),
                "status_reason": scorer.get("status_reason"),
                "entry_touch_distance_status": scorer.get("entry_touch_distance_status"),
                "nearest_distance_to_entry_r": scorer.get("nearest_distance_to_entry_r"),
                "entry_retest_redesign_bucket": scorer.get("entry_retest_redesign_bucket"),
                "entry_retest_redesign_bucket_basis": scorer.get(
                    "entry_retest_redesign_bucket_basis"
                ),
                "entry_retest_redesign_fill_claim_status": scorer.get(
                    "entry_retest_redesign_fill_claim_status"
                ),
                "entry_retest_redesign_tick_replay_requirement": scorer.get(
                    "entry_retest_redesign_tick_replay_requirement"
                ),
                "m15_path_provenance_status": scorer.get("m15_path_provenance_status"),
                "no_leak_status": scorer.get("no_leak_status"),
                "manual_backfill_status": "ACTION_QUEUE_REFRESHED_FROM_BUCKETED_PREFILL_SCORER_OUTPUT",
            }
        )
        out.append(new)

    before_actions = Counter(row.get("action_class") for row in source_rows)
    after_actions = Counter(row.get("action_class") for row in out)
    before_impl = Counter(row.get("implementation_decision") for row in source_rows)
    after_impl = Counter(row.get("implementation_decision") for row in out)
    before_proxy = proxy_stats(source_rows)
    after_proxy = proxy_stats(out)
    target_after = [row for row in out if row.get("strategy_id") == PREFILL_DELIVERY_STRATEGY_ID]
    generic_after = sum(
        1
        for row in target_after
        if row.get("implementation_decision") == GENERIC_IMPL
        or row.get("branch_decision") == GENERIC_BRANCH
        or row.get("scoring_boundary") == GENERIC_BOUNDARY
    )
    linked_no_fill_rows = [
        row for row in linked_rows if row.get("prefill_adverse_no_fill_denominator") is True
    ]
    linked_values = [
        value for row in linked_no_fill_rows if (value := safe_float(row.get("selected_proxy_r"))) is not None
    ]

    summary = {
        "route_id": ROUTE_ID,
        "evidence_class": "MAIN_ORCH24_PREFILL_DELIVERY_BUCKETED_SCORER_OUTPUT",
        "generated_utc": generated,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": (
            "Versioned action queue after prefill delivery scorer repair. Generic no-scorer "
            "rows are replaced by explicit no-fill TP1 denominator buckets. Prefill rows are "
            "metadata/branch-decision rows and do not duplicate entry-offset proxy R."
        ),
        "rows": len(out),
        "input_action_rows": len(source_rows),
        "prefill_target_rows": target_rows,
        "prefill_missing_candidate_or_path_inputs": target_missing_inputs,
        "generic_no_scorer_rows_before": before_impl.get(GENERIC_IMPL, 0),
        "generic_no_scorer_rows_after": generic_after,
        "entry_retest_redesign_bucket_counts": dict(sorted(bucket_counts.items())),
        "prefill_strategy_status_counts": dict(sorted(status_counts.items())),
        "prefill_score_status_counts": dict(sorted(score_counts.items())),
        "prefill_branch_decision_counts": dict(sorted(branch_counts.items())),
        "prefill_target_action_class_counts": dict(sorted(target_action_counts.items())),
        "prefill_target_implementation_decision_counts": dict(sorted(target_impl_counts.items())),
        "action_class_counts_before": dict(sorted(before_actions.items())),
        "action_class_counts_after": dict(sorted(after_actions.items())),
        "action_class_delta_vs_previous": {
            key: after_actions.get(key, 0) - before_actions.get(key, 0)
            for key in sorted(set(before_actions) | set(after_actions))
            if after_actions.get(key, 0) - before_actions.get(key, 0)
        },
        "implementation_decision_counts_before": dict(sorted(before_impl.items())),
        "implementation_decision_counts_after": dict(sorted(after_impl.items())),
        "proxy_before": before_proxy,
        "proxy_after": after_proxy,
        "prefill_metadata_numeric_proxy_rows": 0,
        "prefill_metadata_proxy_r_sum": 0.0,
        "numeric_proxy_row_delta": after_proxy["numeric_proxy_rows"] - before_proxy["numeric_proxy_rows"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "exact_r_rows": 0,
        "linked_entry_offset_no_fill_rows": len(linked_no_fill_rows),
        "linked_entry_offset_numeric_proxy_rows": len(linked_values),
        "linked_entry_offset_proxy_r_sum": round(sum(linked_values), 8),
        "linked_entry_offset_action_class_counts_on_no_fill": dict(
            sorted(linked_no_fill_action_counts.items())
        ),
        "linked_entry_offset_branch_decision_counts_on_no_fill": dict(
            sorted(linked_no_fill_branch_counts.items())
        ),
        "linked_entry_offset_summary_numeric_proxy_rows": linked_summary.get("numeric_proxy_rows"),
        "linked_entry_offset_summary_proxy_r_sum": linked_summary.get("proxy_r_sum"),
        "plate_decision": "PREFILL_DELIVERY_GENERIC_NO_SCORER_REPLACED_WITH_BUCKETED_SCORER_OUTPUT_AND_LINKED_ENTRY_OFFSET_PROXY_BOUNDARY",
    }
    return out, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    inputs = {
        "input_action_ledger": INPUT_ACTION_LEDGER,
        "strategy_follow_candidates": INPUT_STRATEGY_FOLLOW,
        "candidate_path_follow": INPUT_PATH_FOLLOW,
        "live_mechanical_shadow_source": INPUT_LIVE_MECHANICAL_SOURCE,
        "live_mechanical_shadow_tests": INPUT_LIVE_MECHANICAL_TESTS,
        "linked_entry_offset_ledger": INPUT_LINKED_ENTRY_OFFSET_LEDGER,
        "linked_entry_offset_summary": INPUT_LINKED_ENTRY_OFFSET_SUMMARY,
    }
    outputs = {
        "ledger": OUTPUT_LEDGER,
        "summary": OUTPUT_SUMMARY,
    }
    return {
        "route_id": ROUTE_ID,
        "evidence_class": summary["evidence_class"],
        "generated_utc": summary["generated_utc"],
        "safe_flags": SAFE_FLAGS,
        "inputs": {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "bytes": path.stat().st_size if path.exists() else None,
            }
            for name, path in inputs.items()
        },
        "outputs": {
            name: {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for name, path in outputs.items()
        },
        "summary_counts": {
            "rows": summary["rows"],
            "prefill_target_rows": summary["prefill_target_rows"],
            "generic_no_scorer_rows_after": summary["generic_no_scorer_rows_after"],
            "entry_retest_redesign_bucket_counts": summary[
                "entry_retest_redesign_bucket_counts"
            ],
            "numeric_proxy_row_delta": summary["numeric_proxy_row_delta"],
            "proxy_r_sum_delta": summary["proxy_r_sum_delta"],
            "exact_r_rows": summary["exact_r_rows"],
        },
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary))
    print(
        json.dumps(
            {
                "ok": True,
                "rows": summary["rows"],
                "prefill_target_rows": summary["prefill_target_rows"],
                "generic_no_scorer_rows_after": summary["generic_no_scorer_rows_after"],
                "bucket_counts": summary["entry_retest_redesign_bucket_counts"],
                "numeric_proxy_row_delta": summary["numeric_proxy_row_delta"],
                "proxy_r_sum_delta": summary["proxy_r_sum_delta"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
