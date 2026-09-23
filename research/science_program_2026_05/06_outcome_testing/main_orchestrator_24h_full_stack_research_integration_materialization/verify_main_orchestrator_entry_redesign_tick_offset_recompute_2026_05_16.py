"""Verify the entry-redesign tick-offset recompute artifacts."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_OUTPUT_MANIFEST_{DATE}.json"
RESULT = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_VERIFICATION_RESULT_{DATE}.json"
SHIFT_KEYS = ("0.25", "0.5", "1")
ENTRY_BUCKETS = {
    "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE",
    "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def shift_values(rows: list[dict[str, Any]], shift: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = ((row.get("offset_shift_outcomes") or {}).get(shift) or {}).get("proxy_r")
        parsed = safe_float(value)
        if parsed is not None:
            values.append(parsed)
    return values


def main() -> None:
    errors: list[str] = []
    for path in [LEDGER, SUMMARY, MANIFEST]:
        if not path.exists():
            errors.append(f"missing artifact: {path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != summary.get("rows"):
        errors.append(f"summary rows mismatch: ledger={len(rows)} summary={summary.get('rows')}")
    if len({row.get("candidate_id") for row in rows}) != summary.get("candidate_rows"):
        errors.append("candidate row count mismatch")

    bucket_counts = Counter(str(row.get("entry_retest_redesign_bucket")) for row in rows)
    if dict(bucket_counts) != summary.get("entry_retest_redesign_bucket_counts"):
        errors.append("entry bucket counts mismatch")
    expected_buckets = {
        "NOT_A_NO_FILL_TP1_ENTRY_REDESIGN_ROW": 177,
        "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE": 94,
        "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE": 3,
    }
    if dict(bucket_counts) != expected_buckets:
        errors.append(f"unexpected current bucket counts: {dict(bucket_counts)}")

    affected = [row for row in rows if row.get("entry_retest_redesign_bucket") in ENTRY_BUCKETS]
    source_counts = Counter(str(row.get("tick_source_status")) for row in affected)
    if dict(source_counts) != summary.get("tick_source_status_counts_for_affected_rows"):
        errors.append("tick source status counts mismatch")
    if source_counts.get("TICK_REPLAY_SOURCE_COMPLETE") != 95:
        errors.append(f"expected 95 tick-complete affected rows, got {source_counts}")
    if source_counts.get("TICK_SOURCE_INCOMPLETE_BAD_PARQUET") != 2:
        errors.append(f"expected 2 bad-parquet affected rows, got {source_counts}")

    by_bucket: dict[str, list[dict[str, Any]]] = {bucket: [] for bucket in ENTRY_BUCKETS}
    for row in affected:
        by_bucket[str(row.get("entry_retest_redesign_bucket"))].append(row)

    expected_shift_status = {
        ("NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE", "0.25"): {"NO_FILL_AT_SHIFT": 3},
        ("NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE", "0.5"): {"TP1_AFTER_SHIFT_FILL": 3},
        ("NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE", "1"): {"TP1_AFTER_SHIFT_FILL": 3},
        ("FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE", "0.25"): {
            "NO_FILL_AT_SHIFT": 92,
            "TICK_SOURCE_MISSING_OR_BAD": 2,
        },
        ("FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE", "0.5"): {
            "NO_FILL_AT_SHIFT": 82,
            "TP1_AFTER_SHIFT_FILL": 10,
            "TICK_SOURCE_MISSING_OR_BAD": 2,
        },
        ("FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE", "1"): {
            "NO_FILL_AT_SHIFT": 57,
            "TP1_AFTER_SHIFT_FILL": 35,
            "TICK_SOURCE_MISSING_OR_BAD": 2,
        },
    }
    for (bucket, shift), expected in expected_shift_status.items():
        actual = Counter(
            str(((row.get("offset_shift_outcomes") or {}).get(shift) or {}).get("outcome_status"))
            for row in by_bucket[bucket]
        )
        if dict(actual) != expected:
            errors.append(f"shift status mismatch for {bucket} {shift}: {dict(actual)}")
        summary_actual = (
            summary.get("shift_summary_by_bucket", {})
            .get(bucket, {})
            .get(shift, {})
            .get("outcome_status_counts")
        )
        if summary_actual != expected:
            errors.append(f"summary shift status mismatch for {bucket} {shift}: {summary_actual}")

    for bucket, rows_for_bucket in by_bucket.items():
        for shift in SHIFT_KEYS:
            values = shift_values(rows_for_bucket, shift)
            summary_item = summary.get("shift_summary_by_bucket", {}).get(bucket, {}).get(shift, {})
            if len(values) != summary_item.get("numeric_proxy_rows"):
                errors.append(f"numeric proxy count mismatch for {bucket} {shift}")
            if round(sum(values), 8) != summary_item.get("proxy_r_sum"):
                errors.append(f"proxy sum mismatch for {bucket} {shift}")

    if any(row.get("exact_r") is not None for row in rows):
        errors.append("exact_r must remain null for all tick proxy rows")
    if any(row.get("safe_flags", {}).get("live_effect") is not False for row in rows):
        errors.append("live_effect safe flag opened")
    if any(row.get("no_shadow_log_append") is not True for row in rows):
        errors.append("builder must not append to shadow logs")

    for name, artifact in (manifest.get("output_artifacts") or {}).items():
        path = ROUTE_DIR / name
        if not path.exists():
            errors.append(f"manifest output missing: {name}")
            continue
        if sha256_file(path) != artifact.get("sha256"):
            errors.append(f"manifest hash mismatch: {name}")

    result = {
        "ok": not errors,
        "errors": errors,
        "rows": len(rows),
        "candidate_rows": len({row.get("candidate_id") for row in rows}),
        "bucket_counts": dict(bucket_counts),
        "tick_source_status_counts_for_affected_rows": dict(source_counts),
        "safe_flags": summary.get("safe_flags"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
