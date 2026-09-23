#!/usr/bin/env python3
"""Materialize M15-only interval collapse/proxy variants for branch replay."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

REPLAY_EXEC_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_PACKET_RESULT_2026-05-16.json"
M15_ONLY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_ONLY_INTERVAL_ROUTE_LEDGER_2026-05-16.jsonl"
PATH_AMBIGUITY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_AMBIGUITY_LEDGER_2026-05-16.jsonl"
REPLAY_SOURCE_ORDERING_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_SOURCE_ORDERING_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_RESULT_2026-05-16.json"
BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_BRANCH_LEDGER_2026-05-16.jsonl"
AMBIGUITY_SUPPORT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_AMBIGUITY_SUPPORT_LEDGER_2026-05-16.jsonl"
PROXY_VARIANT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_PROXY_VARIANT_LEDGER_2026-05-16.jsonl"
REQUIREMENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_REQUIREMENT_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch M15 interval collapse packet only. It preserves M15 same-bar ambiguity "
    "rows and emits bounded proxy variants for M15-only target/stop ordering. It "
    "does not assert exact chronology, change live behavior, or claim broker R/PnL, "
    "realized expectancy, win-rate, validation, live-readiness, or promotion."
)
PROXY_VARIANTS = ("STOP_FIRST_BOUND", "TARGET_FIRST_BOUND", "MIDPOINT", "CLOSE_DIRECTION_PROXY")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no, "_source_path": str(path)}


def rows(path: Path) -> list[dict[str, Any]]:
    return list(read_jsonl(path) or [])


def write_jsonl(path: Path, output_rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in output_rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def norm(value: Any) -> str:
    if value is None:
        return "None"
    try:
        return f"{float(value):.10g}"
    except (TypeError, ValueError):
        return str(value)


def compact_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (norm(row.get("route_candidate_id")), norm(row.get("entry_variant")), norm(row.get("target_stop_contract_id")))


def by_branch(input_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in input_rows}


def source_manifest_rows() -> tuple[list[dict[str, Any]], str]:
    source_paths = [REPLAY_EXEC_RESULT_PATH, M15_ONLY_PATH, PATH_AMBIGUITY_PATH, REPLAY_SOURCE_ORDERING_PATH]
    manifest_rows = []
    for index, path in enumerate(source_paths, 1):
        manifest_rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-M15-COLLAPSE-SOURCE-{index:03d}",
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "status": "HASHED",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(manifest_rows, sort_keys=True).encode("utf-8")).hexdigest()
    return manifest_rows, manifest_hash


def interval_sign_class(row: dict[str, Any]) -> str:
    low = row.get("interval_rstyle_lower_mean")
    high = row.get("interval_rstyle_upper_mean")
    if low is None or high is None:
        return "INTERVAL_NO_NUMERIC_BOUNDS"
    if low <= 0 <= high:
        return "INTERVAL_STRADDLES_ZERO"
    if low > 0:
        return "INTERVAL_ALL_POSITIVE"
    if high < 0:
        return "INTERVAL_ALL_NEGATIVE"
    return "INTERVAL_MIXED_NONZERO"


def proxy_value(row: dict[str, Any], variant: str) -> Any:
    if variant == "STOP_FIRST_BOUND":
        return row.get("interval_rstyle_lower_mean")
    if variant == "TARGET_FIRST_BOUND":
        return row.get("interval_rstyle_upper_mean")
    return row.get("interval_rstyle_midpoint_mean")


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    artifact_paths = [
        RESULT_PATH,
        BRANCH_PATH,
        AMBIGUITY_SUPPORT_PATH,
        PROXY_VARIANT_PATH,
        REQUIREMENT_PATH,
        BUCKET_PATH,
        QUESTION_PATH,
        SOURCE_MANIFEST_PATH,
        SUMMARY_PATH,
        Path(__file__).resolve(),
    ]
    records = [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "category": "historical_ohlc_gtos_replay_branch_m15_interval_collapse",
        }
        for path in artifact_paths
    ]
    manifest["historical_ohlc_branch_m15_interval_collapse_packet_2026_05_16"] = {
        "generated_utc": generated_at,
        "result": records[0],
        "artifacts": records,
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
    }
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "event_type": "branch_m15_interval_collapse_packet_built",
        "artifact": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = ["# Branch M15 Interval Collapse Packet", "", f"Generated UTC: `{result['generated_utc']}`", "", "## Boundary", "", CLAIM_BOUNDARY, "", "## Counts", ""]
    for key, value in result["counts"].items():
        lines.append(f"- {key}: {value}")
    for category in ["interval_sign_class", "support_match_status", "proxy_variant", "target_stop_result"]:
        lines.extend(["", f"## {category}", ""])
        for bucket, count in result["bucket_distributions"].get(category, {}).items():
            lines.append(f"- {bucket}: {count}")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows()
    replay_result = read_json(REPLAY_EXEC_RESULT_PATH)
    m15_rows = rows(M15_ONLY_PATH)
    ambiguity_rows = rows(PATH_AMBIGUITY_PATH)
    source_ordering_by_branch = by_branch(rows(REPLAY_SOURCE_ORDERING_PATH))
    branch_ids_by_key: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for row in m15_rows:
        branch_ids_by_key[compact_key(row)].append(str(row.get("branch_queue_id")))
    ambiguity_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    support_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[str]] = defaultdict(Counter)

    for index, ambiguity in enumerate(ambiguity_rows, 1):
        matched_branch_ids = branch_ids_by_key.get(compact_key(ambiguity), [])
        status = "MATCHED_ACTIVE_M15_INTERVAL_BRANCH" if matched_branch_ids else "UNMATCHED_TO_ACTIVE_186_M15_INTERVAL_QUEUE"
        for branch_id in matched_branch_ids or [None]:
            if branch_id:
                ambiguity_by_branch[branch_id].append(ambiguity)
            support_rows.append(
                {
                    "m15_interval_ambiguity_support_id": f"OHLC-GTOS-M15-COLLAPSE-SUPPORT-{len(support_rows) + 1:05d}",
                    "branch_queue_id": branch_id,
                    "support_match_status": status,
                    **{key: ambiguity.get(key) for key in ["path_control_id", "cost_fill_id", "event_id", "route_candidate_id", "symbol", "side", "entry_variant", "target_stop_contract_id", "cost_model", "ambiguous_bar_offset", "ambiguity_status"]},
                    "exact_chronology_claim": False,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )
        bucket_counters["support_match_status"][status] += 1

    branch_rows = []
    proxy_variant_rows = []
    requirement_rows = []
    for index, branch in enumerate(m15_rows, 1):
        branch_id = str(branch.get("branch_queue_id"))
        support_count = len(ambiguity_by_branch.get(branch_id, []))
        interval_class = interval_sign_class(branch)
        source_ordering = source_ordering_by_branch.get(branch_id, {})
        branch_rows.append(
            {
                "m15_interval_collapse_branch_id": f"OHLC-GTOS-M15-COLLAPSE-BRANCH-{index:05d}",
                **{key: branch.get(key) for key in ["branch_queue_id", "route_candidate_id", "symbol", "route_session", "side", "entry_variant", "target_stop_contract_id", "target_multiple", "stop_multiple"]},
                "interval_sign_class": interval_class,
                "interval_preservation_class": branch.get("interval_preservation_class"),
                "branch_result_class": branch.get("branch_result_class"),
                "target_stop_result": branch.get("target_stop_result"),
                "support_rows_matched": support_count,
                "upstream_path_ambiguity_rows": branch.get("path_ambiguity_rows"),
                "support_row_match_status": "SUPPORT_ROWS_MATCH_UPSTREAM_COUNT" if support_count == branch.get("path_ambiguity_rows") else "SUPPORT_ROWS_DIFFER_FROM_UPSTREAM_COUNT",
                "m15_only_is_exact_chronology": False,
                "exact_chronology_claim": False,
                "interval_rstyle_lower_mean": branch.get("interval_rstyle_lower_mean"),
                "interval_rstyle_midpoint_mean": branch.get("interval_rstyle_midpoint_mean"),
                "interval_rstyle_upper_mean": branch.get("interval_rstyle_upper_mean"),
                "m15_only_proxy_variants": branch.get("m15_only_proxy_variants"),
                "source_execution_class": source_ordering.get("source_execution_class"),
                "ordering_execution_class": source_ordering.get("ordering_execution_class"),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        for variant in PROXY_VARIANTS:
            proxy_variant_rows.append(
                {
                    "m15_interval_proxy_variant_id": f"OHLC-GTOS-M15-COLLAPSE-PROXY-{len(proxy_variant_rows) + 1:05d}",
                    "branch_queue_id": branch_id,
                    "proxy_variant": variant,
                    "proxy_rstyle_value": proxy_value(branch, variant),
                    "proxy_value_source": "INTERVAL_LOWER_BOUND" if variant == "STOP_FIRST_BOUND" else "INTERVAL_UPPER_BOUND" if variant == "TARGET_FIRST_BOUND" else "INTERVAL_MIDPOINT_PROXY",
                    "exact_chronology_claim": False,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )
            bucket_counters["proxy_variant"][variant] += 1
        requirement_rows.append(
            {
                "m15_interval_requirement_id": f"OHLC-GTOS-M15-COLLAPSE-REQ-{index:05d}",
                "branch_queue_id": branch_id,
                "requirement_status": "M1_OR_TICK_CHRONOLOGY_NOT_AVAILABLE_USE_INTERVAL_PROXY",
                "support_rows_matched": support_count,
                "exact_chronology_claim": False,
                "next_repair_or_proxy_action": "Use interval proxy variants now; only collapse to exact chronology if owned M1/tick source is later found for this historical window.",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        bucket_counters["interval_sign_class"][interval_class] += 1
        bucket_counters["target_stop_result"][str(branch.get("target_stop_result"))] += 1
        bucket_counters["support_row_match_status"][branch_rows[-1]["support_row_match_status"]] += 1

    question_rows = [
        {"question_id": "OHLC-GTOS-M15-COLLAPSE-QUESTION-001", "question": "Which active M15-only branches are interval-sign stable versus straddling zero?", "answer_route": "Use branch interval-sign classes."},
        {"question_id": "OHLC-GTOS-M15-COLLAPSE-QUESTION-002", "question": "Which same-M15 ambiguity rows map into active M15 interval branches versus other branch families?", "answer_route": "Use ambiguity support match status."},
        {"question_id": "OHLC-GTOS-M15-COLLAPSE-QUESTION-003", "question": "Which proxy variant provides conservative, optimistic, and midpoint bounds for each branch?", "answer_route": "Use proxy variant ledger."},
    ]
    for row in question_rows:
        row.update({"safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "generated_utc": generated_at, "not_completion": True})

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-M15-COLLAPSE-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "row_count": int(count),
                    "share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                }
            )

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_PACKET",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_replay_execution_branch_rows": replay_result.get("counts", {}).get("branch_replay_execution_rows"),
            "input_m15_only_branch_rows": len(m15_rows),
            "input_path_ambiguity_rows": len(ambiguity_rows),
            "m15_interval_branch_rows": len(branch_rows),
            "m15_interval_ambiguity_support_rows": len(support_rows),
            "m15_interval_proxy_variant_rows": len(proxy_variant_rows),
            "m15_interval_requirement_rows": len(requirement_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_rows),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "source_manifest_hash": manifest_hash,
    }
    for path, output_rows in [
        (BRANCH_PATH, branch_rows),
        (AMBIGUITY_SUPPORT_PATH, support_rows),
        (PROXY_VARIANT_PATH, proxy_variant_rows),
        (REQUIREMENT_PATH, requirement_rows),
        (BUCKET_PATH, bucket_rows),
        (QUESTION_PATH, question_rows),
        (SOURCE_MANIFEST_PATH, source_rows),
    ]:
        write_jsonl(path, output_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
