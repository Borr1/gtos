#!/usr/bin/env python3
"""Recompute Route C ladder controls after in-window CLEAR_BOOK repair.

The first Route C ladder control packet treated 393 local depth rows as
no-prior-clear blockers. The in-window CLEAR_BOOK repair converted 342 of
those rows into exact boundary ladder features and left 51 precise blockers.
This builder normalizes the repaired fields into the ladder-control surface and
recomputes the full Route C controls without dropping the 10,382-row
denominator.
"""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

BASE_SCRIPT = ROUTE_DIR / "build_sierra_depth_ladder_route_c_controls_2026_05_16.py"
AFTER_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_AFTER_IN_WINDOW_CLEAR_JOIN_LEDGER_{STAMP}.jsonl"
OLD_CONTROL_RESULT = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_RESULT_{STAMP}.json"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_AFTER_IN_WINDOW_CLEAR_RESULT_{STAMP}.json"
EFFECTIVE_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_AFTER_IN_WINDOW_CLEAR_JOIN_LEDGER_{STAMP}.jsonl"
BUCKET_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_AFTER_IN_WINDOW_CLEAR_BUCKET_CONTROL_LEDGER_{STAMP}.jsonl"
NEIGHBOR_PAIR_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_AFTER_IN_WINDOW_CLEAR_NEIGHBOR_INTRADAY_PAIR_LEDGER_{STAMP}.jsonl"
NEIGHBOR_BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_AFTER_IN_WINDOW_CLEAR_NEIGHBOR_INTRADAY_BUCKET_LEDGER_{STAMP}.jsonl"
CONTROL_DELTA_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_AFTER_IN_WINDOW_CLEAR_DELTA_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_AFTER_IN_WINDOW_CLEAR_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_AFTER_IN_WINDOW_CLEAR_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Route C Sierra ladder controls recomputed after in-window CLEAR_BOOK repair; "
    "source-control and descriptor evidence only, with no strategy validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or live deployment"
)


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("base_ladder_controls", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import base ladder controls from {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_base_module()


def first_present(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def normalize_after_repair_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    updated_status = str(row.get("updated_ladder_join_status"))
    updated_bucket = str(row.get("updated_ladder_snapshot_bucket"))
    out["evidence_boundary"] = EVIDENCE_BOUNDARY
    out["safe_flags"] = SAFE_FLAGS
    out["pre_repair_ladder_join_status"] = row.get("ladder_join_status")
    out["pre_repair_ladder_snapshot_bucket"] = row.get("ladder_snapshot_bucket")
    out["ladder_join_status"] = updated_status
    out["ladder_snapshot_bucket"] = updated_bucket
    out["event15_start_utc"] = first_present(row, "event15_start_utc", "bar_start_utc")
    out["event15_end_utc"] = first_present(row, "event15_end_utc", "canonical_m15_close_utc")
    out["effective_ladder_denominator_version"] = "after_in_window_clear_repair"

    if updated_status == "LADDER_FEATURE_JOINED_AFTER_IN_WINDOW_CLEAR_REPAIR":
        mapping = {
            "ladder_event_boundary60_sample_count": "in_window_event_boundary60_sample_count",
            "ladder_event_boundary60_median_depth10_imbalance": "in_window_event_boundary60_median_depth10_imbalance",
            "ladder_event_boundary60_median_total_depth10": "in_window_event_boundary60_median_total_depth10",
            "ladder_event_boundary60_median_wall_concentration10": "in_window_event_boundary60_median_wall_concentration10",
            "ladder_event_boundary60_mid_change_ticks": "in_window_event_boundary60_mid_change_ticks",
            "ladder_pre_boundary60_sample_count": "in_window_pre_boundary60_sample_count",
            "ladder_pre_boundary60_median_depth10_imbalance": "in_window_pre_boundary60_median_depth10_imbalance",
            "ladder_pre_boundary60_median_total_depth10": "in_window_pre_boundary60_median_total_depth10",
        }
        for target, source in mapping.items():
            out[target] = row.get(source)
        out["ladder_event_boundary60_imbalance_sign"] = BASE.sign_bucket(
            out.get("ladder_event_boundary60_median_depth10_imbalance")
        )
        out["ladder_replay_status"] = row.get("in_window_clear_primary_repair_status")
        out["ladder_sample_method"] = "IN_WINDOW_CLEAR_BOUNDARY60"
    elif "FEATURE" in updated_status:
        out["ladder_event_boundary60_imbalance_sign"] = BASE.sign_bucket(
            out.get("ladder_event_boundary60_median_depth10_imbalance")
        )
    else:
        out["ladder_event_boundary60_imbalance_sign"] = "unknown"
    return out


def descriptor_stats_after(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stats = BASE.descriptor_stats_original(rows)
    row_count = len(rows)
    in_window_repaired = sum(
        1 for row in rows
        if row.get("ladder_join_status") == "LADDER_FEATURE_JOINED_AFTER_IN_WINDOW_CLEAR_REPAIR"
    )
    in_window_no_event = sum(
        1 for row in rows
        if row.get("ladder_snapshot_bucket") == "IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_NO_EVENT_SAMPLES"
    )
    no_in_window_clear = sum(
        1 for row in rows
        if row.get("ladder_snapshot_bucket") == "BLOCKED_NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL"
    )
    prior_no_event = sum(
        1 for row in rows
        if row.get("ladder_snapshot_bucket") == "LADDER_BOUNDARY60_NO_EVENT_SAMPLES"
    )
    stats.update(
        {
            "in_window_repaired_feature_rows": in_window_repaired,
            "in_window_repaired_feature_share": in_window_repaired / row_count if row_count else None,
            "in_window_event_no_sample_rows": in_window_no_event,
            "in_window_event_no_sample_share": in_window_no_event / row_count if row_count else None,
            "remaining_no_in_window_clear_rows": no_in_window_clear,
            "remaining_no_in_window_clear_share": no_in_window_clear / row_count if row_count else None,
            "prior_no_event_sample_rows": prior_no_event,
            "prior_no_event_sample_share": prior_no_event / row_count if row_count else None,
        }
    )
    return stats


def classify_control_after(stats: dict[str, Any], denom: dict[str, Any]) -> str:
    if stats["n"] < 20:
        return "UNDERPOWERED_LADDER_GROUP_N_LT_20"
    if stats.get("source_gap_share") is not None and stats["source_gap_share"] >= 0.80:
        return "SOURCE_GAP_DOMINATES_LADDER_CONTEXT"
    if stats.get("in_window_event_no_sample_share") is not None and stats["in_window_event_no_sample_share"] >= 0.50:
        return "IN_WINDOW_CLEAR_EVENT_NO_SAMPLE_DOMINATES_CONTEXT"
    if stats.get("remaining_no_in_window_clear_share") is not None and stats["remaining_no_in_window_clear_share"] >= 0.50:
        return "REMAINING_NO_IN_WINDOW_CLEAR_DOMINATES_CONTEXT"
    if stats.get("no_prior_clear_share") is not None and stats["no_prior_clear_share"] >= 0.50:
        return "NO_PRIOR_CLEAR_DOMINATES_LADDER_CONTEXT"
    if stats.get("feature_share") == 0:
        return "NO_LADDER_FEATURE_ROWS_IN_GROUP"
    route_delta = BASE.delta(
        stats.get("route_c_delta_alignment_descriptor_share"),
        denom.get("route_c_delta_alignment_descriptor_share"),
    )
    if route_delta is None:
        return "NO_DIRECTIONAL_DESCRIPTOR_AVAILABLE"
    if route_delta >= 0.10:
        return "LADDER_BUCKET_ABOVE_DENOMINATOR_DESCRIPTIVE"
    if route_delta <= -0.10:
        return "LADDER_BUCKET_BELOW_DENOMINATOR_AVOID_OR_WEAKENING_DESCRIPTOR"
    if abs(route_delta) <= 0.05:
        return "LADDER_BUCKET_NEAR_DENOMINATOR_GENERIC_CONTEXT"
    return "LADDER_BUCKET_MIXED_SMALL_DESCRIPTOR_DIFFERENCE"


def next_action_for_control_after(bucket: str) -> str:
    if bucket == "IN_WINDOW_CLEAR_EVENT_NO_SAMPLE_DOMINATES_CONTEXT":
        return "run record-level event-boundary fallback for exact in-window no-sample rows before interpreting event ladder state"
    if bucket == "REMAINING_NO_IN_WINDOW_CLEAR_DOMINATES_CONTEXT":
        return "search same-source earlier records, alternate roots, and source-date proxies for rows with no in-window clear before canonical"
    if bucket == "SOURCE_GAP_DOMINATES_LADDER_CONTEXT":
        return "continue exact missing .depth source-date acquisition and source-date proxy design"
    if bucket == "UNDERPOWERED_LADDER_GROUP_N_LT_20":
        return "preserve row-level denominator and aggregate only through explicit same-source or same-mechanism controls"
    return BASE.next_action_for_control_original(bucket)


def patch_base_for_after_repair() -> None:
    BASE.descriptor_stats_original = BASE.descriptor_stats
    BASE.classify_control_original = BASE.classify_control
    BASE.next_action_for_control_original = BASE.next_action_for_control
    BASE.descriptor_stats = descriptor_stats_after
    BASE.classify_control = classify_control_after
    BASE.next_action_for_control = next_action_for_control_after
    BASE.EVIDENCE_BOUNDARY = EVIDENCE_BOUNDARY
    BASE.SAFE_FLAGS = SAFE_FLAGS


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return dict(sorted((str(key), value) for key, value in counter.items()))


def build_delta_rows(
    old_result: dict[str, Any],
    new_counts: dict[str, int],
    control_bucket_counts: Counter[str],
    neighbor_bucket_counts: Counter[str],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    def add(kind: str, key: str, old_value: Any, new_value: Any, context: dict[str, Any] | None = None) -> None:
        delta_value = None
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            delta_value = new_value - old_value
        out.append(
            {
                "route_id": ROUTE_ID,
                "delta_id": f"SIERRA-LADDER-AFTER-REPAIR-DELTA-{len(out) + 1:05d}",
                "delta_kind": kind,
                "delta_key": key,
                "old_value": old_value,
                "new_value": new_value,
                "delta_value": delta_value,
                "context": context or {},
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )

    for key in sorted(set(old_result["counts"]) | set(new_counts)):
        add("count", key, old_result["counts"].get(key), new_counts.get(key))
    for bucket in sorted(set(old_result["control_bucket_counts"]) | set(control_bucket_counts)):
        add("control_bucket_count", bucket, old_result["control_bucket_counts"].get(bucket, 0), control_bucket_counts.get(bucket, 0))
    for bucket in sorted(set(old_result["neighbor_control_bucket_counts"]) | set(neighbor_bucket_counts)):
        add(
            "neighbor_control_bucket_count",
            bucket,
            old_result["neighbor_control_bucket_counts"].get(bucket, 0),
            neighbor_bucket_counts.get(bucket, 0),
        )

    status_transitions = Counter(
        (row.get("pre_repair_ladder_join_status"), row.get("ladder_join_status"))
        for row in rows
    )
    for (old_status, new_status), count in sorted(status_transitions.items(), key=lambda item: (str(item[0][0]), str(item[0][1]))):
        add(
            "join_status_transition_count",
            f"{old_status}->{new_status}",
            None,
            count,
            {"old_status": old_status, "new_status": new_status},
        )
    bucket_transitions = Counter(
        (row.get("pre_repair_ladder_snapshot_bucket"), row.get("ladder_snapshot_bucket"))
        for row in rows
    )
    for (old_bucket, new_bucket), count in sorted(bucket_transitions.items(), key=lambda item: (str(item[0][0]), str(item[0][1]))):
        add(
            "snapshot_bucket_transition_count",
            f"{old_bucket}->{new_bucket}",
            None,
            count,
            {"old_bucket": old_bucket, "new_bucket": new_bucket},
        )
    return out


def build_questions_after(
    control_bucket_counts: Counter[str],
    neighbor_bucket_counts: Counter[str],
    counts: dict[str, int],
    delta_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = BASE.build_questions(control_bucket_counts, neighbor_bucket_counts, counts)
    start = len(rows)
    extra = [
        (
            "after_repair_denominator_delta",
            "How do the old no-prior-clear controls change when the denominator is recomputed with the 342 repaired exact ladder rows?",
            "use the delta ledger plus recomputed bucket controls as the active control denominator before mutation scoring",
        ),
        (
            "remaining_51_blocker_split",
            "Which of the 51 remaining repaired-denominator blockers can be converted by record-level fallback or source search now?",
            "run an immediate blocker split/repair packet for exact event no-sample and no-in-window-clear families",
        ),
        (
            "repaired_feature_mutation_context",
            "Which mutation rows outside the earlier imbalanced split change once the 342 repaired exact ladder features are available?",
            "join effective ladder buckets into all 54 current mutation rows without narrowing to affected examples",
        ),
    ]
    for offset, (family, question, action) in enumerate(extra, 1):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-ROUTEC-AFTER-REPAIR-Q-{start + offset:03d}",
                "question_family": family,
                "row_count": counts["effective_join_rows"],
                "question": question,
                "next_same_resource_action": action,
                "delta_rows": len(delta_rows),
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_route_c_control_after_in_window_clear_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_route_c_control_after_in_window_clear_result", "created"),
        (EFFECTIVE_JOIN_LEDGER, "sierra_depth_ladder_route_c_control_after_in_window_clear_join_ledger", "created"),
        (BUCKET_CONTROL_LEDGER, "sierra_depth_ladder_route_c_control_after_in_window_clear_bucket_control_ledger", "created"),
        (NEIGHBOR_PAIR_LEDGER, "sierra_depth_ladder_route_c_control_after_in_window_clear_neighbor_pair_ledger", "created"),
        (NEIGHBOR_BUCKET_LEDGER, "sierra_depth_ladder_route_c_control_after_in_window_clear_neighbor_bucket_ledger", "created"),
        (CONTROL_DELTA_LEDGER, "sierra_depth_ladder_route_c_control_after_in_window_clear_delta_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_route_c_control_after_in_window_clear_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_route_c_control_after_in_window_clear_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {BASE.relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": BASE.relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], buckets: Counter[str]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_route_c_controls_after_in_window_clear",
        "status": "done",
        "route": "sierra_depth_ladder_route_c_controls_recomputed_after_repair",
        "details": "Recomputed Route C ladder controls after the in-window CLEAR_BOOK repair and preserved old-vs-new control deltas.",
        "counts": counts,
        "control_bucket_counts": counter_dict(buckets),
        "artifacts": [
            BASE.relative(Path(__file__).resolve()),
            BASE.relative(RESULT_PATH),
            BASE.relative(EFFECTIVE_JOIN_LEDGER),
            BASE.relative(BUCKET_CONTROL_LEDGER),
            BASE.relative(NEIGHBOR_PAIR_LEDGER),
            BASE.relative(NEIGHBOR_BUCKET_LEDGER),
            BASE.relative(CONTROL_DELTA_LEDGER),
            BASE.relative(QUESTION_LEDGER),
            BASE.relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {BASE.relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(
    generated_utc: str,
    counts: dict[str, int],
    control_buckets: Counter[str],
    neighbor_buckets: Counter[str],
) -> None:
    lines = [
        "# Sierra Depth Ladder Route C Controls After In-Window Clear Repair",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: repaired Route C/Sierra ladder source-control descriptors only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Ladder Control Buckets", ""])
    for bucket, count in sorted(control_buckets.items()):
        lines.append(f"- `{bucket}`: `{count}`")
    lines.extend(["", "## Neighbor Control Buckets", ""])
    for bucket, count in sorted(neighbor_buckets.items()):
        lines.append(f"- `{bucket}`: `{count}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Split and repair the `51` remaining blockers immediately: exact event-boundary no-sample rows versus no in-window clear before canonical.",
            "- Use the effective `831` feature-row denominator for mutation-context work instead of the stale `489`-row prior-clear denominator.",
            "- Keep exact missing `.depth` source-date acquisition active while building best-available same-source proxies.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    patch_base_for_after_repair()
    generated_utc = BASE.utc_now()
    input_rows = BASE.read_jsonl(AFTER_JOIN_LEDGER)
    effective_rows = [normalize_after_repair_row(row) for row in input_rows]
    bucket_controls, control_bucket_counts = BASE.build_bucket_controls(effective_rows)
    feature_rows = [row for row in effective_rows if "FEATURE" in str(row.get("ladder_join_status"))]
    neighbor_pairs, neighbor_buckets = BASE.build_neighbor_pairs(feature_rows)
    neighbor_bucket_counts = Counter(str(row["control_bucket"]) for row in neighbor_buckets)

    counts = {
        "after_repair_join_input_rows": len(input_rows),
        "effective_join_rows": len(effective_rows),
        "effective_ladder_feature_join_rows": len(feature_rows),
        "effective_ladder_blocker_join_rows": sum(1 for row in effective_rows if "BLOCKER" in str(row.get("ladder_join_status"))),
        "effective_source_gap_ladder_rows": sum(1 for row in effective_rows if row.get("ladder_join_status") == "LADDER_SOURCE_GAP_MISSING_DEPTH_FILE"),
        "pre_repair_no_prior_clear_rows": sum(
            1 for row in effective_rows
            if row.get("pre_repair_ladder_snapshot_bucket") == "LADDER_BOUNDARY60_BLOCKED_NO_PRIOR_CLEAR_BOOK_BEFORE_WINDOW"
        ),
        "effective_old_no_prior_clear_rows": sum(
            1 for row in effective_rows
            if row.get("ladder_snapshot_bucket") == "LADDER_BOUNDARY60_BLOCKED_NO_PRIOR_CLEAR_BOOK_BEFORE_WINDOW"
        ),
        "remaining_no_in_window_clear_rows": sum(
            1 for row in effective_rows
            if row.get("ladder_snapshot_bucket") == "BLOCKED_NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL"
        ),
        "remaining_in_window_event_no_sample_rows": sum(
            1 for row in effective_rows
            if row.get("ladder_snapshot_bucket") == "IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_NO_EVENT_SAMPLES"
        ),
        "prior_boundary60_no_event_sample_rows": sum(
            1 for row in effective_rows
            if row.get("ladder_snapshot_bucket") == "LADDER_BOUNDARY60_NO_EVENT_SAMPLES"
        ),
        "bucket_control_rows": len(bucket_controls),
        "neighbor_pair_rows": len(neighbor_pairs),
        "neighbor_bucket_rows": len(neighbor_buckets),
        "control_delta_rows": 0,
        "question_rows": 0,
    }
    old_result = json.loads(OLD_CONTROL_RESULT.read_text(encoding="utf-8"))
    delta_rows = build_delta_rows(old_result, counts, control_bucket_counts, neighbor_bucket_counts, effective_rows)
    counts["control_delta_rows"] = len(delta_rows)
    questions = build_questions_after(control_bucket_counts, neighbor_bucket_counts, counts, delta_rows)
    counts["question_rows"] = len(questions)

    BASE.write_jsonl(EFFECTIVE_JOIN_LEDGER, effective_rows)
    BASE.write_jsonl(BUCKET_CONTROL_LEDGER, bucket_controls)
    BASE.write_jsonl(NEIGHBOR_PAIR_LEDGER, neighbor_pairs)
    BASE.write_jsonl(NEIGHBOR_BUCKET_LEDGER, neighbor_buckets)
    BASE.write_jsonl(CONTROL_DELTA_LEDGER, delta_rows)
    BASE.write_jsonl(QUESTION_LEDGER, questions)
    result = {
        "schema": "sierra_depth_ladder_route_c_control_after_in_window_clear_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_AFTER_IN_WINDOW_CLEAR_REPAIR",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "control_bucket_counts": counter_dict(control_bucket_counts),
        "neighbor_control_bucket_counts": counter_dict(neighbor_bucket_counts),
        "old_control_bucket_counts": old_result["control_bucket_counts"],
        "old_neighbor_control_bucket_counts": old_result["neighbor_control_bucket_counts"],
        "not_completion": "This repaired control packet deepens Route C but does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "split and pursue the 51 remaining after-repair blockers",
            "feed effective ladder buckets into all current mutation rows",
            "continue exact missing .depth source-date acquisition and same-source proxy construction",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, control_bucket_counts)
    write_summary(generated_utc, counts, control_bucket_counts, neighbor_bucket_counts)
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
