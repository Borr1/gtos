#!/usr/bin/env python3
"""Deepen source-unavailable branch execution into stress/acquisition rows."""

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
REPLAY_EXEC_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_UNAVAILABLE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_UNAVAILABLE_ACQUISITION_LEDGER_2026-05-16.jsonl"
SOURCE_PROXY_STRESS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_PROXY_STRESS_INTERVAL_LEDGER_2026-05-16.jsonl"
EXACT_UNAVAILABLE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_UNAVAILABLE_STRESS_LEDGER_2026-05-16.jsonl"
GRADIENT_EXACT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_GRADIENT_EXACT_SPREAD_LEDGER_2026-05-16.jsonl"
SOURCE_WINDOW_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_EXACT_SPREAD_SOURCE_WINDOW_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_RESULT_2026-05-16.json"
BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_BRANCH_LEDGER_2026-05-16.jsonl"
SUPPORT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_SUPPORT_LEDGER_2026-05-16.jsonl"
SOURCE_WINDOW_REQUIREMENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_WINDOW_REQUIREMENT_LEDGER_2026-05-16.jsonl"
DESCRIPTOR_SPLIT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_DESCRIPTOR_SPLIT_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch source-stress/acquisition packet only. It preserves every exact-spread "
    "unavailable stress row, maps rows into the active source-unavailable branch "
    "queue where keys match, materializes source-window requirements, and keeps "
    "stress-pair descriptor bounds without live behavior, broker R/PnL, realized "
    "expectancy, win-rate, validation, live-readiness, or promotion claims."
)


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


def branch_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        norm(row.get("route_candidate_id")),
        norm(row.get("entry_variant")),
        norm(row.get("target_stop_contract_id")),
        norm(row.get("symbol")),
        norm(row.get("side")),
        norm(row.get("target_multiple")),
        norm(row.get("stop_multiple")),
    )


def by_branch(input_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in input_rows}


def source_manifest_rows() -> tuple[list[dict[str, Any]], str]:
    source_paths = [
        REPLAY_EXEC_RESULT_PATH,
        REPLAY_EXEC_BRANCH_PATH,
        SOURCE_UNAVAILABLE_PATH,
        SOURCE_PROXY_STRESS_PATH,
        EXACT_UNAVAILABLE_PATH,
        GRADIENT_EXACT_PATH,
        SOURCE_WINDOW_PATH,
    ]
    manifest_rows = []
    for index, path in enumerate(source_paths, 1):
        manifest_rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-SRC-STRESS-SOURCE-{index:03d}",
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "status": "HASHED",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(manifest_rows, sort_keys=True).encode("utf-8")).hexdigest()
    return manifest_rows, manifest_hash


def descriptor_split(low_status: str | None, high_status: str | None) -> str:
    if low_status == high_status:
        return "LOW_HIGH_STRESS_DESCRIPTOR_STABLE"
    low = str(low_status)
    high = str(high_status)
    if "TARGET" in low and "STOP" in high:
        return "LOW_TARGET_HIGH_STOP_STRESS_FLIP"
    if "STOP" in low and "TARGET" in high:
        return "LOW_STOP_HIGH_TARGET_STRESS_FLIP"
    if "NO_TARGET" in low or "NO_TARGET" in high or "NO_TOUCH" in low or "NO_TOUCH" in high:
        return "LOW_HIGH_STRESS_TOUCHLESS_OR_PARTIAL_FLIP"
    return "LOW_HIGH_STRESS_DESCRIPTOR_DIFFERENT"


def branch_stress_class(split_counts: Counter[str], branch: dict[str, Any]) -> str:
    if not split_counts:
        return "NO_EXACT_UNAVAILABLE_SUPPORT_ROW_MATCH"
    if split_counts == Counter({"LOW_HIGH_STRESS_DESCRIPTOR_STABLE": sum(split_counts.values())}):
        return "SOURCE_STRESS_DESCRIPTOR_STABLE_BOUNDED"
    if any("FLIP" in status for status in split_counts):
        return "SOURCE_STRESS_DESCRIPTOR_FLIPS_TARGET_STOP"
    if float(branch.get("rstyle_lower_mean") or 0) <= 0 <= float(branch.get("rstyle_upper_mean") or 0):
        return "SOURCE_STRESS_INTERVAL_STRADDLES_ZERO"
    return "SOURCE_STRESS_DESCRIPTOR_MIXED_NONFLIP"


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    artifact_paths = [
        RESULT_PATH,
        BRANCH_PATH,
        SUPPORT_PATH,
        SOURCE_WINDOW_REQUIREMENT_PATH,
        DESCRIPTOR_SPLIT_PATH,
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
            "category": "historical_ohlc_gtos_replay_branch_source_stress_acquisition",
        }
        for path in artifact_paths
    ]
    manifest["historical_ohlc_branch_source_stress_acquisition_packet_2026_05_16"] = {
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
        "event_type": "branch_source_stress_acquisition_packet_built",
        "artifact": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = ["# Branch Source Stress Acquisition Packet", "", f"Generated UTC: `{result['generated_utc']}`", "", "## Boundary", "", CLAIM_BOUNDARY, "", "## Counts", ""]
    for key, value in result["counts"].items():
        lines.append(f"- {key}: {value}")
    for category in ["branch_stress_class", "support_match_status", "descriptor_split_class", "source_window_status"]:
        lines.extend(["", f"## {category}", ""])
        for bucket, count in result["bucket_distributions"].get(category, {}).items():
            lines.append(f"- {bucket}: {count}")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows()
    replay_result = read_json(REPLAY_EXEC_RESULT_PATH)
    replay_branches = by_branch(rows(REPLAY_EXEC_BRANCH_PATH))
    source_unavailable_rows = rows(SOURCE_UNAVAILABLE_PATH)
    source_proxy_rows = rows(SOURCE_PROXY_STRESS_PATH)
    exact_unavailable_rows = rows(EXACT_UNAVAILABLE_PATH)
    gradient_rows = rows(GRADIENT_EXACT_PATH)
    source_window_rows = rows(SOURCE_WINDOW_PATH)
    gradient_by_sig = {row.get("cost_sensitivity_signature_id"): row for row in gradient_rows}
    source_window_by_key = {row.get("source_window_key"): row for row in source_window_rows}

    branch_ids_by_key: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for row in source_unavailable_rows:
        branch_ids_by_key[branch_key(row)].append(str(row.get("branch_queue_id")))

    exact_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    support_rows: list[dict[str, Any]] = []
    source_window_requirement_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[str]] = defaultdict(Counter)
    unique_source_window_keys: set[str] = set()

    for index, exact in enumerate(exact_unavailable_rows, 1):
        matched_branch_ids = branch_ids_by_key.get(branch_key(exact), [])
        gradient = gradient_by_sig.get(exact.get("cost_sensitivity_signature_id"), {})
        source_window = source_window_by_key.get(gradient.get("source_window_key"), {})
        support_match_status = "MATCHED_ACTIVE_SOURCE_UNAVAILABLE_BRANCH" if matched_branch_ids else "UNMATCHED_TO_ACTIVE_138_BRANCH_QUEUE"
        descriptor_class = descriptor_split(exact.get("low_spread_descriptor_status"), exact.get("high_spread_descriptor_status"))
        source_window_key = gradient.get("source_window_key")
        if source_window_key:
            unique_source_window_keys.add(str(source_window_key))
        emit_branch_ids = matched_branch_ids or [None]
        for branch_id in emit_branch_ids:
            if branch_id:
                exact_by_branch[branch_id].append(exact)
            support_rows.append(
                {
                    "source_stress_support_id": f"OHLC-GTOS-SRC-STRESS-SUPPORT-{len(support_rows) + 1:05d}",
                    "branch_queue_id": branch_id,
                    "support_match_status": support_match_status,
                    "unavailable_stress_id": exact.get("unavailable_stress_id"),
                    "cost_sensitivity_signature_id": exact.get("cost_sensitivity_signature_id"),
                    **{key: exact.get(key) for key in ["route_candidate_id", "symbol", "side", "entry_variant", "target_stop_contract_id", "target_multiple", "stop_multiple"]},
                    "exact_spread_source_status": exact.get("exact_spread_source_status"),
                    "exact_spread_proxy_bucket": exact.get("exact_spread_proxy_bucket"),
                    "low_spread_descriptor_status": exact.get("low_spread_descriptor_status"),
                    "high_spread_descriptor_status": exact.get("high_spread_descriptor_status"),
                    "descriptor_split_class": descriptor_class,
                    "source_window_key": source_window_key,
                    "reference_time_utc": gradient.get("reference_time_utc"),
                    "source_time_utc": gradient.get("source_time_utc"),
                    "extract_start_utc": source_window.get("extract_start_utc"),
                    "extract_end_utc": source_window.get("extract_end_utc"),
                    "ticks_returned": source_window.get("ticks_returned"),
                    "valid_spread_ticks": source_window.get("valid_spread_ticks"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )
        source_window_requirement_rows.append(
            {
                "source_window_requirement_id": f"OHLC-GTOS-SRC-STRESS-WINDOW-{index:05d}",
                "source_window_key": source_window_key,
                "cost_sensitivity_signature_id": exact.get("cost_sensitivity_signature_id"),
                "support_match_status": support_match_status,
                "matched_branch_count": len(matched_branch_ids),
                "symbol": exact.get("symbol"),
                "exact_spread_source_status": exact.get("exact_spread_source_status"),
                "source_window_status": source_window.get("exact_source_status") or "SOURCE_WINDOW_ROW_NOT_FOUND",
                "reference_time_utc": gradient.get("reference_time_utc"),
                "source_time_utc": gradient.get("source_time_utc"),
                "extract_start_utc": source_window.get("extract_start_utc"),
                "extract_end_utc": source_window.get("extract_end_utc"),
                "ticks_returned": source_window.get("ticks_returned"),
                "valid_spread_ticks": source_window.get("valid_spread_ticks"),
                "next_repair_or_proxy_action": "Preserve low/high spread stress bounds and attempt broader owned MT5/history source only if available; do not wait for future data.",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        bucket_counters["support_match_status"][support_match_status] += 1
        bucket_counters["descriptor_split_class"][descriptor_class] += 1
        bucket_counters["source_window_status"][source_window.get("exact_source_status") or "SOURCE_WINDOW_ROW_NOT_FOUND"] += 1

    source_proxy_by_branch = by_branch(source_proxy_rows)
    branch_rows = []
    descriptor_split_rows = []
    for index, branch in enumerate(source_unavailable_rows, 1):
        branch_id = str(branch.get("branch_queue_id"))
        support = exact_by_branch.get(branch_id, [])
        split_counts = Counter(descriptor_split(row.get("low_spread_descriptor_status"), row.get("high_spread_descriptor_status")) for row in support)
        stress_class = branch_stress_class(split_counts, branch)
        replay_branch = replay_branches.get(branch_id, {})
        branch_rows.append(
            {
                "source_stress_acquisition_branch_id": f"OHLC-GTOS-SRC-STRESS-BRANCH-{index:05d}",
                **{key: branch.get(key) for key in ["branch_queue_id", "route_candidate_id", "symbol", "route_session", "side", "entry_variant", "target_stop_contract_id", "target_multiple", "stop_multiple"]},
                "branch_stress_class": stress_class,
                "branch_execution_class": replay_branch.get("branch_execution_class"),
                "source_execution_class": replay_branch.get("source_execution_class"),
                "ordering_execution_class": replay_branch.get("ordering_execution_class"),
                "support_rows_matched": len(support),
                "upstream_unavailable_support_rows": branch.get("unavailable_support_rows"),
                "support_row_match_status": "SUPPORT_ROWS_MATCH_UPSTREAM_COUNT" if len(support) == branch.get("unavailable_support_rows") else "SUPPORT_ROWS_DIFFER_FROM_UPSTREAM_COUNT",
                "descriptor_split_counts": compact_counter(split_counts),
                "stress_interval_policy": source_proxy_by_branch.get(branch_id, {}).get("stress_interval_policy"),
                "rstyle_lower_mean": branch.get("rstyle_lower_mean"),
                "rstyle_midpoint_mean": branch.get("rstyle_midpoint_mean"),
                "rstyle_upper_mean": branch.get("rstyle_upper_mean"),
                "target_stop_result": branch.get("target_stop_result"),
                "exact_missing_geometry_or_source_reason": replay_branch.get("exact_missing_geometry_or_source_reason"),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        descriptor_split_rows.append(
            {
                "descriptor_split_id": f"OHLC-GTOS-SRC-STRESS-SPLIT-{index:05d}",
                "branch_queue_id": branch_id,
                "branch_stress_class": stress_class,
                "descriptor_split_counts": compact_counter(split_counts),
                "support_rows_matched": len(support),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        bucket_counters["branch_stress_class"][stress_class] += 1
        bucket_counters["support_row_match_status"][branch_rows[-1]["support_row_match_status"]] += 1

    question_rows = [
        {"question_id": "OHLC-GTOS-SRC-STRESS-QUESTION-001", "question": "Which source-unavailable branches have matched exact stress rows and which upstream support counts differ?", "answer_route": "Use branch and support ledgers."},
        {"question_id": "OHLC-GTOS-SRC-STRESS-QUESTION-002", "question": "Which low/high spread stress rows flip target/stop descriptors versus remain stable?", "answer_route": "Use descriptor split ledger and support descriptor classes."},
        {"question_id": "OHLC-GTOS-SRC-STRESS-QUESTION-003", "question": "Which MT5 source windows failed closed and what immediate proxy/action remains?", "answer_route": "Use source-window requirement ledger."},
    ]
    for row in question_rows:
        row.update({"safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "generated_utc": generated_at, "not_completion": True})

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-SRC-STRESS-BUCKET-{len(bucket_rows) + 1:05d}",
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
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_PACKET",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_replay_execution_branch_rows": replay_result.get("counts", {}).get("branch_replay_execution_rows"),
            "input_source_unavailable_branch_rows": len(source_unavailable_rows),
            "input_source_proxy_stress_rows": len(source_proxy_rows),
            "input_exact_unavailable_stress_rows": len(exact_unavailable_rows),
            "input_gradient_exact_spread_rows": len(gradient_rows),
            "input_source_window_rows": len(source_window_rows),
            "source_stress_acquisition_branch_rows": len(branch_rows),
            "source_stress_support_rows": len(support_rows),
            "source_window_requirement_rows": len(source_window_requirement_rows),
            "descriptor_split_rows": len(descriptor_split_rows),
            "unique_source_window_keys": len(unique_source_window_keys),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_rows),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "source_manifest_hash": manifest_hash,
    }
    for path, output_rows in [
        (BRANCH_PATH, branch_rows),
        (SUPPORT_PATH, support_rows),
        (SOURCE_WINDOW_REQUIREMENT_PATH, source_window_requirement_rows),
        (DESCRIPTOR_SPLIT_PATH, descriptor_split_rows),
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
