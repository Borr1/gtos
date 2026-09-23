"""Merge duplicated pending-lifecycle action rows.

The current action ledger carries one pending-lifecycle row from the
FVG/structural recompute and one from the pending source-derivation recompute
for every candidate. The FVG/structural row has already consumed the latest
pending tick-spread repairs, so this plate keeps it as canonical and preserves
the derivation row as duplicate source evidence without counting its proxy R
again.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_ACTION_RECLASS_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_ACTION_RECLASS_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_DUPLICATE_MERGE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_DUPLICATE_MERGE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_DUPLICATE_MERGE_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

TARGET_PRIMITIVE = "pending_lifecycle_fill_cancel_expiry_source_capture"
CANONICAL_SOURCE_PLATE = "fvg_structural_scorer_candidate_recompute"
DUPLICATE_SOURCE_PLATE = "pending_lifecycle_source_derivation_recompute"


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
            if line.strip():
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


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "proxy_r_mean": round(sum(values) / len(values), 8) if values else None,
    }


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "") for row in rows))


def is_pending(row: dict[str, Any]) -> bool:
    return row.get("primitive_family") == TARGET_PRIMITIVE


def materialize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    generated = utc_now()
    by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if is_pending(row):
            by_candidate[str(row.get("candidate_id") or "")].append(row)

    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if not is_pending(row):
            row["pending_duplicate_merge_status"] = "NOT_TARGET_ROW"
            output.append(row)
            continue

        candidate_group = by_candidate[str(row.get("candidate_id") or "")]
        if row.get("source_plate") == CANONICAL_SOURCE_PLATE:
            row["pending_duplicate_merge_status"] = "CANONICAL_PENDING_LIFECYCLE_ROW_PROXY_COUNTED"
            row["proxy_counting_decision"] = "COUNT_CANONICAL_PENDING_LIFECYCLE_ROW_ONCE"
            row["duplicate_pending_row_count_for_candidate"] = len(candidate_group) - 1
            stats["canonical_pending_rows_counted"] += 1
        elif row.get("source_plate") == DUPLICATE_SOURCE_PLATE:
            before_proxy = safe_float(row.get("after_proxy_r"))
            row["before_pending_duplicate_merge_after_proxy_r"] = before_proxy
            row["before_pending_duplicate_merge_source_plate"] = row.get("source_plate")
            row["pending_duplicate_merge_status"] = "MERGED_DUPLICATE_PENDING_SOURCE_DERIVATION_ROW"
            row["canonical_source_plate"] = CANONICAL_SOURCE_PLATE
            row["merged_duplicate_proxy_reference_r"] = before_proxy
            row["after_proxy_r"] = None
            row["current_claim_proxy_counted"] = False
            row["proxy_counting_decision"] = "EXCLUDED_FROM_IMPLEMENTATION_PROXY_DENOMINATOR_DUPLICATE_PENDING_ROW"
            row["decision_evidence"] = (
                "Pending source-derivation row duplicates the same candidate/strategy surface already counted "
                "through the FVG/structural recompute row that consumed latest tick-spread repairs."
            )
            row["scoring_boundary"] = "NO_DUPLICATE_R_FOR_PENDING_LIFECYCLE_SOURCE_DERIVATION_COPY"
            row["current_action"] = "MERGE_DUPLICATE_PENDING_SOURCE_DERIVATION_ROW_INTO_CANONICAL_PENDING_SCORER"
            row["next_action"] = "MERGE_DUPLICATE_PENDING_SOURCE_DERIVATION_ROW_INTO_CANONICAL_PENDING_SCORER"
            row["underlying_intelligence_preserved"] = True
            stats["duplicate_pending_rows_merged"] += 1
            if before_proxy is not None:
                stats["duplicate_pending_numeric_proxy_rows_excluded"] += 1
        else:
            row["pending_duplicate_merge_status"] = "PENDING_ROW_UNEXPECTED_SOURCE_PLATE"
            stats["unexpected_pending_source_plate_rows"] += 1
        output.append(row)
    return output, dict(stats)


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
    canonical = [
        row
        for row in output_rows
        if row.get("pending_duplicate_merge_status") == "CANONICAL_PENDING_LIFECYCLE_ROW_PROXY_COUNTED"
    ]
    duplicate = [
        row
        for row in output_rows
        if row.get("pending_duplicate_merge_status") == "MERGED_DUPLICATE_PENDING_SOURCE_DERIVATION_ROW"
    ]
    canonical_values = [value for row in canonical if (value := safe_float(row.get("after_proxy_r"))) is not None]
    duplicate_values = [
        value for row in duplicate if (value := safe_float(row.get("merged_duplicate_proxy_reference_r"))) is not None
    ]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_PENDING_DUPLICATE_MERGE",
        "claim_boundary": (
            "Deduplicates pending-lifecycle action rows by counting only the canonical row that consumed "
            "latest tick-spread repairs and preserving the pending source-derivation row as duplicate evidence. "
            "No live behavior, validation, promotion, broker operation, AI/API call, or shadow append is opened."
        ),
        "rows": len(output_rows),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "action_class_counts_after": counter(output_rows, "action_class"),
        "action_class_counts_changed": counter(output_rows, "action_class") != counter(input_rows, "action_class"),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_delta": after_proxy["numeric_proxy_rows"] - before_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "canonical_pending_rows_counted": len(canonical),
        "canonical_pending_numeric_proxy_rows": len(canonical_values),
        "canonical_pending_proxy_r_sum": round(sum(canonical_values), 8),
        "duplicate_pending_rows_merged": len(duplicate),
        "duplicate_pending_numeric_proxy_rows_excluded": len(duplicate_values),
        "duplicate_pending_proxy_reference_r_sum": round(sum(duplicate_values), 8),
        "merge_status_counts": counter(output_rows, "pending_duplicate_merge_status"),
        "repair_stats": stats,
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "PENDING_LIFECYCLE_DUPLICATE_SOURCE_DERIVATION_ROWS_MERGED",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "duplicate_pending_rows_merged": len(duplicate),
                "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
                "proxy_r_sum_after": after_proxy["proxy_r_sum"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
