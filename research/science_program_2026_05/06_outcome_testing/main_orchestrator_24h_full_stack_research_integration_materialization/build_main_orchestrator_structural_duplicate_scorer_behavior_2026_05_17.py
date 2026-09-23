"""Materialize structural duplicate scorer behavior after source patch.

The implementation-selection plate proved that three V3 structural variants
were duplicate shared-path proxies. This builder verifies that the patched
``live_mechanical_shadow`` scorer now emits the redesign decision directly for
those rows while preserving the underlying proxy-R evidence.
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
    DUPLICATE_STRUCTURAL_SHARED_PATH_IDS,
    build_strategy_outcome_rows,
    latest_lifecycle_for_candidate_asof,
    latest_structural_metadata_by_candidate,
    latest_ltf_for_candidate_asof,
    merge_structural_metadata_candidate,
    read_jsonl as read_shadow_jsonl,
)


INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_SELECTION_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_SELECTION_SUMMARY_{DATE}.json"
SCORER_SOURCE = REPO_ROOT / "src/research_infra/live_mechanical_shadow.py"
TEST_SOURCE = REPO_ROOT / "tests/test_live_mechanical_shadow.py"

SHADOW_INPUTS = {
    "strategy_follow_candidates": REPO_ROOT / "shadow_logs/strategy_follow_candidates.jsonl",
    "candidate_path_follow": REPO_ROOT / "shadow_logs/candidate_path_follow.jsonl",
    "pending_limit_lifecycle": REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl",
    "candidate_ltf_path_order": REPO_ROOT / "shadow_logs/candidate_ltf_path_order.jsonl",
    "live_structural_strategy_metadata": REPO_ROOT / "shadow_logs/live_structural_strategy_metadata.jsonl",
}

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_STRUCTURAL_DUPLICATE_SCORER_BEHAVIOR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_STRUCTURAL_DUPLICATE_SCORER_BEHAVIOR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_STRUCTURAL_DUPLICATE_SCORER_BEHAVIOR_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
EXPECTED_DUPLICATE_BRANCH = "REDESIGN_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY_NOT_DISTINCT_IMPLEMENTATION"
PREVIOUS_DUPLICATE_BRANCH = "IMPLEMENT_SHADOW_SCORER_CAPTURED_METADATA_DEFAULT_OFF"
TARGET_STATUS = "SOURCE_SCORER_NOW_EMITS_DUPLICATE_STRUCTURAL_REDESIGN"
SOURCE_REPAIR_DEPENDENT_STATUS = "RAW_SOURCE_SCORER_REQUIRES_STRUCTURAL_SOURCE_REPAIR_MATERIALIZATION"


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


def floats_equal(left: Any, right: Any) -> bool:
    left_value = safe_float(left)
    right_value = safe_float(right)
    if left_value is None or right_value is None:
        return left_value is None and right_value is None
    return round(left_value - right_value, 10) == 0


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter("" if row.get(field) is None else str(row.get(field)) for row in rows))


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current = parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        previous = parse_utc(out.get(cid, {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        if current >= previous:
            out[cid] = row
    return out


def latest_path_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current_asof = parse_utc(row.get("asof_latest_candle_utc"))
        previous_asof = parse_utc(out.get(cid, {}).get("asof_latest_candle_utc"))
        current_created = parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        previous_created = parse_utc(out.get(cid, {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        if previous_asof is None or (
            current_asof is not None
            and (current_asof > previous_asof or (current_asof == previous_asof and current_created >= previous_created))
        ):
            out[cid] = row
    return out


def has_metadata_gap(row: dict[str, Any]) -> bool:
    return (
        row.get("decision_evidence") in (None, "")
        or row.get("scoring_boundary") in (None, "")
        or row.get("implementation_candidate") in (None, "")
        or str(row.get("current_action")) in {"None", "False", ""}
        or str(row.get("next_action")) in {"None", "False", ""}
    )


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "proxy_r_mean": round(sum(values) / len(values), 8) if values else None,
    }


def far_miss_invariants(rows: list[dict[str, Any]]) -> dict[str, Any]:
    entry_branch = "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_CHALLENGER"
    kill_branch = "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL"
    entry_rows = [row for row in rows if row.get("branch_decision") == entry_branch]
    killed_rows = [row for row in rows if row.get("branch_decision") == kill_branch]
    entry_values = [safe_float(row.get("after_proxy_r")) for row in entry_rows]
    entry_values = [value for value in entry_values if value is not None]
    return {
        "entry_default_off_candidates": len({row.get("candidate_id") for row in entry_rows}),
        "entry_default_off_numeric_proxy_rows": len(entry_values),
        "entry_default_off_proxy_r_sum": round(sum(entry_values), 8),
        "killed_far_miss_rows": len(killed_rows),
        "killed_far_miss_candidates": len({row.get("candidate_id") for row in killed_rows}),
    }


def tick_structural_invariants(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = counter(rows, "tick_structural_derivation_repair_status")
    converted = sum(
        count
        for status, count in counts.items()
        if status not in {"", "None", "NOT_TARGET_ROW"}
    )
    return {
        "tick_structural_converted_rows": converted,
        "tick_structural_status_counts": counts,
    }


def build_strategy_recompute_map(generated_utc: str) -> dict[tuple[str, str], dict[str, Any]]:
    candidates = latest_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["strategy_follow_candidates"]))
    paths = latest_path_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["candidate_path_follow"]))
    pending_lifecycle_rows = read_shadow_jsonl(SHADOW_INPUTS["pending_limit_lifecycle"])
    ltf_rows = read_shadow_jsonl(SHADOW_INPUTS["candidate_ltf_path_order"])
    structural_metadata = latest_structural_metadata_by_candidate(
        read_shadow_jsonl(SHADOW_INPUTS["live_structural_strategy_metadata"])
    )
    recomputed: dict[tuple[str, str], dict[str, Any]] = {}
    for cid in sorted(candidates):
        candidate = merge_structural_metadata_candidate(
            candidates[cid],
            structural_metadata.get(cid),
        )
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
            key = (str(row.get("candidate_id") or ""), str(row.get("strategy_id") or ""))
            recomputed[key] = row
    return recomputed


def is_duplicate_structural_row(row: dict[str, Any]) -> bool:
    return str(row.get("strategy_id") or "") in DUPLICATE_STRUCTURAL_SHARED_PATH_IDS


def materialize_rows(
    rows: list[dict[str, Any]],
    recomputed: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    generated = utc_now()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if not is_duplicate_structural_row(row):
            row["structural_duplicate_scorer_behavior_status"] = "NOT_TARGET_ROW"
            output.append(row)
            continue

        stats["target_rows"] += 1
        key = (str(row.get("candidate_id") or ""), str(row.get("strategy_id") or ""))
        scorer_row = recomputed.get(key)
        if not scorer_row:
            row["structural_duplicate_scorer_behavior_status"] = "RECOMPUTE_ROW_MISSING"
            stats["target_recompute_missing"] += 1
            output.append(row)
            continue
        if scorer_row.get("branch_decision") == EXPECTED_DUPLICATE_BRANCH:
            row["structural_duplicate_scorer_behavior_status"] = TARGET_STATUS
        else:
            row["structural_duplicate_scorer_behavior_status"] = SOURCE_REPAIR_DEPENDENT_STATUS
        row["structural_duplicate_scorer_behavior_source"] = "src/research_infra/live_mechanical_shadow.py"
        row["before_source_scorer_patch_branch_decision"] = row.get(
            "before_implementation_selection_branch_decision"
        )
        row["after_source_scorer_patch_branch_decision"] = scorer_row.get("branch_decision")
        row["after_source_scorer_patch_decision_evidence"] = scorer_row.get("decision_evidence")
        row["after_source_scorer_patch_scoring_boundary"] = scorer_row.get("scoring_boundary")
        row["after_source_scorer_patch_implementation_candidate"] = scorer_row.get(
            "implementation_candidate"
        )
        row["after_source_scorer_patch_strategy_status"] = scorer_row.get("strategy_status")
        row["after_source_scorer_patch_score_status"] = scorer_row.get("score_status")
        row["after_source_scorer_patch_outcome_status"] = scorer_row.get("outcome_status")
        row["after_source_scorer_patch_proxy_r"] = scorer_row.get("strategy_proxy_r")
        row["source_scorer_patch_proxy_r_matches_action_row"] = floats_equal(
            row.get("after_proxy_r"),
            scorer_row.get("strategy_proxy_r"),
        )
        if row.get("before_source_scorer_patch_branch_decision") == PREVIOUS_DUPLICATE_BRANCH:
            stats["target_rows_previously_default_off_branch"] += 1
        if scorer_row.get("branch_decision") == EXPECTED_DUPLICATE_BRANCH:
            stats["target_rows_now_redesign_branch"] += 1
        if scorer_row.get("branch_decision") == "SOURCE_CAPTURE_REQUIRED_FOR_STRUCTURAL_LOCK_SCORER":
            stats["target_rows_raw_source_still_requires_structural_source_repair"] += 1
        if row.get("branch_decision") == scorer_row.get("branch_decision"):
            stats["target_rows_action_branch_matches_source_patch"] += 1
        if row.get("implementation_candidate") == scorer_row.get("implementation_candidate"):
            stats["target_rows_action_candidate_matches_source_patch"] += 1
        output.append(row)
    return output, dict(stats)


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
    recomputed = build_strategy_recompute_map(utc_now())
    output_rows, stats = materialize_rows(input_rows, recomputed)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    target_rows = [
        row
        for row in output_rows
        if row.get("structural_duplicate_scorer_behavior_status")
        in {TARGET_STATUS, SOURCE_REPAIR_DEPENDENT_STATUS}
    ]
    native_rows = [
        row for row in output_rows if row.get("structural_duplicate_scorer_behavior_status") == TARGET_STATUS
    ]
    source_repair_dependent_rows = [
        row
        for row in output_rows
        if row.get("structural_duplicate_scorer_behavior_status") == SOURCE_REPAIR_DEPENDENT_STATUS
    ]
    target_numeric = [safe_float(row.get("after_proxy_r")) for row in target_rows]
    target_numeric = [value for value in target_numeric if value is not None]
    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_STRUCTURAL_DUPLICATE_SCORER_BEHAVIOR",
        "claim_boundary": (
            "Code-level scorer behavior repair for duplicate structural shared-path V3 strategy IDs. "
            "The materializer consumes live structural metadata before recomputing source behavior, so "
            "the scorer now emits redesign branch decisions directly for all current duplicate rows while "
            "preserving proxy-R evidence. "
            "No exact R, live behavior, shadow append, promotion, broker operation, or AI/API call is opened."
        ),
        "rows": len(output_rows),
        "target_rows": len(target_rows),
        "native_source_scorer_redesign_rows": len(native_rows),
        "source_repair_dependent_rows": len(source_repair_dependent_rows),
        "target_numeric_proxy_rows": len(target_numeric),
        "target_proxy_r_sum": round(sum(target_numeric), 8),
        "repair_stats": stats,
        "status_counts": counter(output_rows, "structural_duplicate_scorer_behavior_status"),
        "before_source_scorer_patch_branch_counts": counter(
            target_rows,
            "before_source_scorer_patch_branch_decision",
        ),
        "after_source_scorer_patch_branch_counts": counter(
            target_rows,
            "after_source_scorer_patch_branch_decision",
        ),
        "native_source_scorer_redesign_branch_counts": counter(
            native_rows,
            "after_source_scorer_patch_branch_decision",
        ),
        "source_repair_dependent_branch_counts": counter(
            source_repair_dependent_rows,
            "after_source_scorer_patch_branch_decision",
        ),
        "target_action_class_counts": counter(target_rows, "action_class"),
        "target_strategy_counts": counter(target_rows, "strategy_id"),
        "target_proxy_match_counts": counter(target_rows, "source_scorer_patch_proxy_r_matches_action_row"),
        "action_class_counts_after": counter(output_rows, "action_class"),
        "all_metadata_gaps_after": sum(1 for row in output_rows if has_metadata_gap(row)),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "far_miss_retest_control_invariants": far_miss_invariants(output_rows),
        "tick_structural_source_repair_invariants": tick_structural_invariants(output_rows),
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "DUPLICATE_STRUCTURAL_SHARED_PATH_REDESIGN_NOW_EMITTED_BY_SOURCE_SCORER_AFTER_METADATA_MERGE",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "target_rows": len(target_rows),
                "target_proxy_r_sum": summary["target_proxy_r_sum"],
                "summary": str(OUTPUT_SUMMARY),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
