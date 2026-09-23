from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
INPUT_SOURCE_LEDGER = ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_SOURCE_LEDGER_2026-05-17.jsonl"
OUTPUT_SOURCE_LOG = Path("shadow_logs/pending_lifecycle_tick_spread_reconstruction.jsonl")
SUMMARY = ROUTE_DIR / "MAIN_ORCH24_PENDING_TICK_SPREAD_DEFAULT_SOURCE_MATERIALIZATION_SUMMARY_2026-05-17.json"
MANIFEST = ROUTE_DIR / "MAIN_ORCH24_PENDING_TICK_SPREAD_DEFAULT_SOURCE_MATERIALIZATION_OUTPUT_MANIFEST_2026-05-17.json"
VERIFY_RESULT = ROUTE_DIR / "MAIN_ORCH24_PENDING_TICK_SPREAD_DEFAULT_SOURCE_MATERIALIZATION_VERIFY_RESULT_2026-05-17.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    issues: list[str] = []
    source_rows = read_jsonl(INPUT_SOURCE_LEDGER)
    output_rows = read_jsonl(OUTPUT_SOURCE_LOG)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    if source_rows != output_rows:
        issues.append("output_source_log_does_not_match_route_source_ledger")
    if len(output_rows) != 11:
        issues.append(f"expected_11_rows_found_{len(output_rows)}")
    statuses = Counter(str(row.get("decision_spread_status") or "") for row in output_rows)
    if statuses.get("TICK_PARQUET_AT_OR_BEFORE_DECISION_WITHIN_2S_SOURCE_SAFE") != 10:
        issues.append("expected_10_source_safe_tick_rows")
    if statuses.get("TICK_PARQUET_NO_PRIOR_TICK_WITHIN_2S_SOURCE_UNSAFE") != 1:
        issues.append("expected_1_unsafe_source_requirement_row")
    if summary.get("rows") != len(output_rows):
        issues.append("summary_rows_mismatch")
    if summary.get("tick_reconstruction_success_rows") != 10:
        issues.append("summary_success_rows_not_10")
    if summary.get("remaining_source_requirement_rows") != 1:
        issues.append("summary_remaining_requirement_not_1")
    if manifest.get("outputs", {}).get("default_source_log", {}).get("sha256") != sha256_file(OUTPUT_SOURCE_LOG):
        issues.append("manifest_output_hash_mismatch")
    if manifest.get("inputs", {}).get("route_local_source_ledger", {}).get("sha256") != sha256_file(INPUT_SOURCE_LEDGER):
        issues.append("manifest_input_hash_mismatch")
    if manifest.get("safe_flags", {}).get("live_effect") is not False:
        issues.append("manifest_live_effect_not_false")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(output_rows),
        "tick_reconstruction_success_rows": statuses.get(
            "TICK_PARQUET_AT_OR_BEFORE_DECISION_WITHIN_2S_SOURCE_SAFE", 0
        ),
        "tick_reconstruction_unsafe_rows": statuses.get(
            "TICK_PARQUET_NO_PRIOR_TICK_WITHIN_2S_SOURCE_UNSAFE", 0
        ),
        "output_source_log_sha256": sha256_file(OUTPUT_SOURCE_LOG),
        "safe_flags": summary.get("safe_flags"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
