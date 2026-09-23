#!/usr/bin/env python3
"""Join no-event ladder fallback rows into same-source neighbor controls."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

FALLBACK_FEATURE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_FALLBACK_FEATURE_LEDGER_{STAMP}.jsonl"
NEIGHBOR_PAIR_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_NEIGHBOR_INTRADAY_PAIR_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_NEIGHBOR_CONTROL_RESULT_{STAMP}.json"
PAIR_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_NEIGHBOR_PAIR_LEDGER_{STAMP}.jsonl"
TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_NEIGHBOR_TARGET_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_NEIGHBOR_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_NEIGHBOR_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_NEIGHBOR_CONTROL_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra .depth no-event fallback rows joined to same-source intraday "
    "neighbor controls; no strategy validation, trade outcome, R/PnL, "
    "expectancy, live-readiness, or promotion"
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def median(values: list[Any]) -> float | None:
    clean = sorted(v for v in (safe_float(value) for value in values) if v is not None)
    if not clean:
        return None
    mid = len(clean) // 2
    if len(clean) % 2:
        return clean[mid]
    return (clean[mid - 1] + clean[mid]) / 2.0


def bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def side_payload(pair: dict[str, Any], side: str) -> dict[str, Any]:
    return {
        "request_id": pair.get(f"{side}_request_id"),
        "command_bucket": pair.get(f"{side}_command_bucket"),
        "ladder_bucket": pair.get(f"{side}_ladder_bucket"),
        "route_c_delta_aligned_with_future": pair.get(f"{side}_route_c_delta_aligned_with_future"),
    }


def proxy_neighbor_relation(target: dict[str, Any], neighbor_ladder_bucket: str | None) -> str:
    proxy_bucket = str(target.get("fallback_event15_proxy_bucket"))
    if proxy_bucket == "FALLBACK_RECORD_LEVEL_EVENT15_NO_SAMPLES":
        return "TARGET_EVENT15_PROXY_NO_SAMPLES"
    if proxy_bucket.endswith("MISSING"):
        return "TARGET_EVENT15_PROXY_MISSING"
    if not neighbor_ladder_bucket:
        return "NEIGHBOR_LADDER_BUCKET_MISSING"
    if "NO_EVENT_SAMPLES" in neighbor_ladder_bucket:
        return "NEIGHBOR_BOUNDARY60_NO_EVENT_CONTEXT"
    if "BALANCED" in proxy_bucket and "BALANCED" in neighbor_ladder_bucket:
        return "TARGET_PROXY_BALANCED_NEIGHBOR_BALANCED"
    if "IMBALANCED" in proxy_bucket and "IMBALANCED" in neighbor_ladder_bucket:
        return "TARGET_PROXY_IMBALANCED_NEIGHBOR_IMBALANCED"
    if "IMBALANCED" in proxy_bucket and "BALANCED" in neighbor_ladder_bucket:
        return "TARGET_PROXY_IMBALANCED_NEIGHBOR_BALANCED_SPLIT"
    if "BALANCED" in proxy_bucket and "IMBALANCED" in neighbor_ladder_bucket:
        return "TARGET_PROXY_BALANCED_NEIGHBOR_IMBALANCED_SPLIT"
    return "TARGET_PROXY_NEIGHBOR_MIXED_OR_UNKNOWN"


def build_pair_rows(fallback_rows: list[dict[str, Any]], neighbor_pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fallback_by_request = {str(row.get("request_id")): row for row in fallback_rows}
    out: list[dict[str, Any]] = []
    for pair in neighbor_pairs:
        for target_side, neighbor_side in (("left", "right"), ("right", "left")):
            target_id = str(pair.get(f"{target_side}_request_id"))
            if target_id not in fallback_by_request:
                continue
            target = fallback_by_request[target_id]
            neighbor = side_payload(pair, neighbor_side)
            target_aligned = bool_or_none(target.get("route_c_delta_aligned_with_future"))
            neighbor_aligned = bool_or_none(neighbor.get("route_c_delta_aligned_with_future"))
            same_alignment = None
            if target_aligned is not None and neighbor_aligned is not None:
                same_alignment = target_aligned == neighbor_aligned
            relation = proxy_neighbor_relation(target, str(neighbor.get("ladder_bucket")))
            out.append(
                {
                    "target_neighbor_pair_id": f"SIERRA-DEPTH-LADDER-NO-EVENT-PAIR-{len(out) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "source_symbol": pair.get("source_symbol"),
                    "source_date": pair.get("source_date"),
                    "source_proxy_family": target.get("source_proxy_family"),
                    "pair_id": pair.get("pair_id"),
                    "target_side": target_side,
                    "target_request_id": target_id,
                    "neighbor_request_id": neighbor.get("request_id"),
                    "target_route_c_queue_id": target.get("route_c_queue_id"),
                    "target_route_c_symbol": target.get("route_c_symbol"),
                    "target_route_c_primitive_flag": target.get("route_c_primitive_flag"),
                    "target_route_c_mechanism_family": target.get("route_c_mechanism_family"),
                    "target_route_c_full_control_bucket": target.get("route_c_full_control_bucket"),
                    "target_route_c_residual_transfer_class": target.get("route_c_residual_transfer_class"),
                    "target_route_c_delta_aligned_with_future": target_aligned,
                    "neighbor_route_c_delta_aligned_with_future": neighbor_aligned,
                    "same_route_alignment_bool": same_alignment,
                    "target_command_bucket": target.get("command_feature_bucket"),
                    "neighbor_command_bucket": neighbor.get("command_bucket"),
                    "same_command_bucket": target.get("command_feature_bucket") == neighbor.get("command_bucket"),
                    "target_previous_ladder_bucket": target.get("previous_ladder_snapshot_bucket"),
                    "target_fallback_ladder_snapshot_bucket": target.get("fallback_ladder_snapshot_bucket"),
                    "target_event15_proxy_bucket": target.get("fallback_event15_proxy_bucket"),
                    "target_event15_imbalance_sign": target.get("fallback_event15_imbalance_sign"),
                    "target_event15_median_depth10_imbalance": target.get("fallback_event15_record_median_depth10_imbalance"),
                    "target_event15_median_total_depth10": target.get("fallback_event15_record_median_total_depth10"),
                    "target_event15_record_count": target.get("fallback_event15_record_count"),
                    "target_command_fallback_relation_bucket": target.get("command_fallback_route_relation_bucket"),
                    "neighbor_ladder_bucket": neighbor.get("ladder_bucket"),
                    "proxy_neighbor_relation_bucket": relation,
                    "abs_route_c_future_change_delta": pair.get("abs_route_c_future_change_delta"),
                    "offset_bucket": pair.get("offset_bucket"),
                    "minutes_between_event15": pair.get("minutes_between_event15"),
                }
            )
    return out


def target_control_bucket(target: dict[str, Any], pair_rows: list[dict[str, Any]]) -> str:
    proxy_bucket = str(target.get("fallback_event15_proxy_bucket"))
    if not pair_rows:
        return "NO_SAME_SOURCE_NEIGHBOR_PAIRS"
    if proxy_bucket == "FALLBACK_RECORD_LEVEL_EVENT15_NO_SAMPLES":
        return "TARGET_EVENT15_PROXY_SOURCE_GAP_REMAINS"
    if proxy_bucket.endswith("MISSING"):
        return "TARGET_EVENT15_PROXY_BOOK_IMBALANCE_MISSING"
    same_alignment_values = [row.get("same_route_alignment_bool") for row in pair_rows if row.get("same_route_alignment_bool") is not None]
    if len(pair_rows) < 20:
        return "UNDERPOWERED_TARGET_NEIGHBOR_N_LT_20"
    if not same_alignment_values:
        return "TARGET_NEIGHBOR_ALIGNMENT_UNKNOWN"
    share = sum(1 for value in same_alignment_values if value is True) / len(same_alignment_values)
    if share >= 0.65:
        return "SAME_SOURCE_NEIGHBOR_ALIGNMENT_GENERIC_CONTEXT"
    if share <= 0.35:
        return "SAME_SOURCE_NEIGHBOR_ALIGNMENT_WEAKENING_CONTEXT"
    return "SAME_SOURCE_NEIGHBOR_ALIGNMENT_MIXED_DESCRIPTOR"


def build_target_rows(fallback_rows: list[dict[str, Any]], pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pair_rows:
        pairs_by_target[str(row.get("target_request_id"))].append(row)
    out: list[dict[str, Any]] = []
    for target in sorted(fallback_rows, key=lambda item: str(item.get("request_id"))):
        request_id = str(target.get("request_id"))
        pairs = pairs_by_target.get(request_id, [])
        same_alignment_values = [row.get("same_route_alignment_bool") for row in pairs if row.get("same_route_alignment_bool") is not None]
        same_command_values = [row.get("same_command_bucket") for row in pairs if row.get("same_command_bucket") is not None]
        row = {
            "target_summary_id": f"SIERRA-DEPTH-LADDER-NO-EVENT-TARGET-{len(out) + 1:04d}",
            "route_id": ROUTE_ID,
            "safe_flags": SAFE_FLAGS,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "target_request_id": request_id,
            "source_symbol": target.get("source_symbol"),
            "source_date": target.get("source_date"),
            "route_c_queue_id": target.get("route_c_queue_id"),
            "route_c_symbol": target.get("route_c_symbol"),
            "route_c_primitive_flag": target.get("route_c_primitive_flag"),
            "route_c_mechanism_family": target.get("route_c_mechanism_family"),
            "route_c_full_control_bucket": target.get("route_c_full_control_bucket"),
            "route_c_residual_transfer_class": target.get("route_c_residual_transfer_class"),
            "route_c_delta_aligned_with_future": target.get("route_c_delta_aligned_with_future"),
            "fallback_ladder_snapshot_bucket": target.get("fallback_ladder_snapshot_bucket"),
            "event15_proxy_bucket": target.get("fallback_event15_proxy_bucket"),
            "event15_imbalance_sign": target.get("fallback_event15_imbalance_sign"),
            "event15_record_count": target.get("fallback_event15_record_count"),
            "event15_median_depth10_imbalance": target.get("fallback_event15_record_median_depth10_imbalance"),
            "event15_median_total_depth10": target.get("fallback_event15_record_median_total_depth10"),
            "command_fallback_relation_bucket": target.get("command_fallback_route_relation_bucket"),
            "neighbor_pair_rows": len(pairs),
            "neighbor_request_count": len({row.get("neighbor_request_id") for row in pairs}),
            "same_route_alignment_count": sum(1 for value in same_alignment_values if value is True),
            "known_route_alignment_pair_count": len(same_alignment_values),
            "same_route_alignment_share": (
                sum(1 for value in same_alignment_values if value is True) / len(same_alignment_values)
                if same_alignment_values
                else None
            ),
            "same_command_bucket_count": sum(1 for value in same_command_values if value is True),
            "known_command_pair_count": len(same_command_values),
            "same_command_bucket_share": (
                sum(1 for value in same_command_values if value is True) / len(same_command_values)
                if same_command_values
                else None
            ),
            "median_abs_route_c_future_change_delta": median([row.get("abs_route_c_future_change_delta") for row in pairs]),
            "neighbor_ladder_bucket_counts": dict(sorted(Counter(str(row.get("neighbor_ladder_bucket")) for row in pairs).items())),
            "proxy_neighbor_relation_counts": dict(sorted(Counter(str(row.get("proxy_neighbor_relation_bucket")) for row in pairs).items())),
        }
        row["target_neighbor_control_bucket"] = target_control_bucket(target, pairs)
        out.append(row)
    return out


def build_bucket_rows(pair_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: Counter[tuple[str, str, str, str, str]] = Counter()
    for row in pair_rows:
        grouped[
            (
                str(row.get("target_event15_proxy_bucket")),
                str(row.get("target_command_fallback_relation_bucket")),
                str(row.get("proxy_neighbor_relation_bucket")),
                str(row.get("neighbor_ladder_bucket")),
                str(row.get("target_route_c_full_control_bucket")),
            )
        ] += 1
    target_control_counts = Counter(str(row.get("target_neighbor_control_bucket")) for row in target_rows)
    out: list[dict[str, Any]] = []
    for ordinal, (key, count) in enumerate(sorted(grouped.items()), start=1):
        proxy_bucket, command_relation, proxy_neighbor_relation, neighbor_ladder, route_control = key
        out.append(
            {
                "bucket_id": f"SIERRA-DEPTH-LADDER-NO-EVENT-NEIGHBOR-BUCKET-{ordinal:04d}",
                "bucket_family": "pair_relation",
                "event15_proxy_bucket": proxy_bucket,
                "command_fallback_relation_bucket": command_relation,
                "proxy_neighbor_relation_bucket": proxy_neighbor_relation,
                "neighbor_ladder_bucket": neighbor_ladder,
                "route_c_full_control_bucket": route_control,
                "row_count": count,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    for bucket, count in sorted(target_control_counts.items()):
        out.append(
            {
                "bucket_id": f"SIERRA-DEPTH-LADDER-NO-EVENT-NEIGHBOR-BUCKET-{len(out) + 1:04d}",
                "bucket_family": "target_control",
                "target_neighbor_control_bucket": bucket,
                "target_count": count,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return out


def build_question_rows(bucket_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    control_counts = Counter(str(row.get("target_neighbor_control_bucket")) for row in target_rows)
    for bucket, count in sorted(control_counts.items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-NO-EVENT-NEIGHBOR-Q-{len(rows) + 1:03d}",
                "question_family": "target_control_bucket",
                "bucket": bucket,
                "row_count": count,
                "question": f"What same-resource mutation follows for every no-event target in {bucket}?",
                "next_same_resource_action": next_action(bucket),
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    relation_counts = Counter(str(row.get("proxy_neighbor_relation_bucket")) for row in bucket_rows if row.get("bucket_family") == "pair_relation")
    for bucket, count in sorted(relation_counts.items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-NO-EVENT-NEIGHBOR-Q-{len(rows) + 1:03d}",
                "question_family": "proxy_neighbor_relation_bucket",
                "bucket": bucket,
                "row_count": count,
                "question": f"Does relation bucket {bucket} behave like generic same-source context, weakening evidence, or a split descriptor across all pair-bucket rows?",
                "next_same_resource_action": "join to fallback target summaries and Route C transfer classes; preserve as descriptor only unless separately validated",
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def next_action(bucket: str) -> str:
    if bucket == "SAME_SOURCE_NEIGHBOR_ALIGNMENT_GENERIC_CONTEXT":
        return "treat fallback proxy as generic same-source context unless independent residual survives stronger controls"
    if bucket == "SAME_SOURCE_NEIGHBOR_ALIGNMENT_WEAKENING_CONTEXT":
        return "preserve as weakening/avoid descriptor candidate and inspect source-date concentration"
    if bucket == "SAME_SOURCE_NEIGHBOR_ALIGNMENT_MIXED_DESCRIPTOR":
        return "split by source symbol, session, route primitive, and event15 proxy bucket"
    if bucket == "TARGET_EVENT15_PROXY_SOURCE_GAP_REMAINS":
        return "preserve exact source/capture requirement; no ladder proxy available"
    if bucket == "TARGET_EVENT15_PROXY_BOOK_IMBALANCE_MISSING":
        return "inspect book completeness and top-depth construction before using proxy"
    if bucket == "UNDERPOWERED_TARGET_NEIGHBOR_N_LT_20":
        return "retain full row ledger and expand same-source denominator if more local source exists"
    return "manual target control review required"


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_no_event_neighbor_control_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_no_event_neighbor_control_result", "created"),
        (PAIR_LEDGER, "sierra_depth_ladder_no_event_neighbor_pair_ledger", "created"),
        (TARGET_LEDGER, "sierra_depth_ladder_no_event_neighbor_target_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_no_event_neighbor_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_no_event_neighbor_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_no_event_neighbor_control_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], target_control_counts: Counter[str]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_no_event_neighbor_controls",
        "status": "done",
        "route": "sierra_depth_ladder_no_event_neighbor_controls",
        "details": "Joined every no-event fallback target to every existing same-source intraday ladder neighbor pair and emitted per-target control buckets.",
        "counts": counts,
        "target_control_bucket_counts": dict(sorted(target_control_counts.items())),
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(PAIR_LEDGER),
            relative(TARGET_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], target_control_counts: Counter[str], proxy_relation_counts: Counter[str]) -> None:
    lines = [
        "# Sierra Depth Ladder No-Event Neighbor Controls",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: no-event fallback descriptor rows joined to same-source intraday neighbor controls. No validation, R/PnL, expectancy, live-readiness, promotion, or completion claim.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Target Control Buckets", ""])
    for key, value in sorted(target_control_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Proxy/Neighbor Relation Buckets", ""])
    for key, value in sorted(proxy_relation_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- This packet only tests whether no-event fallback proxy rows are generic same-source behavior or need split/weakening descriptors.",
            "- Neighbor controls are descriptive and use Route C movement fields already present in the route ledger; they are not broker outcomes or promotion evidence.",
            "- Every target-neighbor pair touching a fallback target is preserved; no pair subset or top-N cutoff is used.",
            "",
            "## Next Same-Resource Work",
            "",
            "- Recompute ladder source/capture requirements after incorporating exact boundary60 proof and neighbor-control buckets.",
            "- Split the remaining imbalanced ladder descriptors by command-ladder sign, fallback proxy, and neighbor context.",
            "- Continue exact missing `.depth` source-date acquisition where owned/current/free/public routes exist.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    fallback_rows = read_jsonl(FALLBACK_FEATURE_LEDGER)
    neighbor_pairs = read_jsonl(NEIGHBOR_PAIR_LEDGER)
    pair_rows = build_pair_rows(fallback_rows, neighbor_pairs)
    target_rows = build_target_rows(fallback_rows, pair_rows)
    buckets = build_bucket_rows(pair_rows, target_rows)
    target_control_counts = Counter(str(row.get("target_neighbor_control_bucket")) for row in target_rows)
    proxy_relation_counts = Counter(str(row.get("proxy_neighbor_relation_bucket")) for row in pair_rows)
    counts = {
        "fallback_feature_input_rows": len(fallback_rows),
        "neighbor_pair_input_rows": len(neighbor_pairs),
        "target_neighbor_pair_rows": len(pair_rows),
        "target_summary_rows": len(target_rows),
        "target_with_neighbor_rows": sum(1 for row in target_rows if int(row.get("neighbor_pair_rows") or 0) > 0),
        "target_without_neighbor_rows": sum(1 for row in target_rows if int(row.get("neighbor_pair_rows") or 0) == 0),
        "bucket_rows": len(buckets),
        "question_rows": 0,
    }
    questions = build_question_rows(buckets, target_rows, counts)
    counts["question_rows"] = len(questions)

    write_jsonl(PAIR_LEDGER, pair_rows)
    write_jsonl(TARGET_LEDGER, target_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    result = {
        "schema": "sierra_depth_ladder_no_event_neighbor_control_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_NO_EVENT_NEIGHBOR_CONTROL_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "target_control_bucket_counts": dict(sorted(target_control_counts.items())),
        "proxy_neighbor_relation_counts": dict(sorted(proxy_relation_counts.items())),
        "next_same_resource_work": [
            "recompute ladder source/capture requirements after no-event fallback neighbor controls",
            "split remaining imbalanced descriptors by command-ladder/fallback-neighbor relation",
            "continue exact missing .depth source-date acquisition",
        ],
        "not_completion": "This neighbor-control packet deepens one Route C blocker family and does not complete the 60-hour moonshot objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, target_control_counts)
    write_summary(generated_utc, counts, target_control_counts, proxy_relation_counts)
    print(json.dumps({"ok": True, "counts": counts, "target_control_counts": dict(target_control_counts), "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
