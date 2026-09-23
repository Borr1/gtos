"""Verify pending-lifecycle decision-spread source-capture repair."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_CAPTURE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_CAPTURE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_CAPTURE_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = (
    ROUTE_DIR
    / f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_CAPTURE_VERIFICATION_RESULT_{DATE}.json"
)
INPUT_EXECUTION = Path("src/components/execution.py")
INPUT_PENDING_TESTS = Path("tests/test_pending_limit_lifecycle_logger.py")

REQUIRED_EXECUTION_TOKENS = [
    "decision_spread_value_source_safe: float | None = None",
    "decision_spread_unit: str | None = None",
    "decision_spread_value = getattr(",
]
REQUIRED_TEST_TOKENS = [
    "test_execution_persists_decision_spread_from_limit_intent",
]


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
    failures: list[str] = []
    for path in [OUTPUT_LEDGER, OUTPUT_SUMMARY, OUTPUT_MANIFEST, INPUT_EXECUTION, INPUT_PENDING_TESTS]:
        if not path.exists():
            failures.append(f"missing_path:{path}")
    if failures:
        result = {"ok": False, "failures": failures}
        OUTPUT_VERIFICATION.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, sort_keys=True))
        return

    rows = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)
    execution_text = INPUT_EXECUTION.read_text(encoding="utf-8")
    test_text = INPUT_PENDING_TESTS.read_text(encoding="utf-8")

    if len(rows) != 4:
        failures.append(f"unexpected_ledger_rows:{len(rows)}")
    if summary.get("rows") != 4:
        failures.append("summary_rows_mismatch")
    if summary.get("safe_flags") != SAFE_FLAGS:
        failures.append("summary_safe_flags_mismatch")
    if summary.get("current_proxy_r_sum_delta") != 0.0:
        failures.append("current_proxy_delta_not_zero")
    if summary.get("current_missing_field_delta") != 0:
        failures.append("current_missing_delta_not_zero")
    if summary.get("exact_r_rows") != 0:
        failures.append("exact_r_opened")
    if summary.get("current_missing_field_counts_before") != summary.get(
        "current_missing_field_counts_after"
    ):
        failures.append("current_missing_counts_changed_without_backfill_source")

    for token in REQUIRED_EXECUTION_TOKENS:
        if token not in execution_text:
            failures.append(f"missing_execution_token:{token}")
    for token in REQUIRED_TEST_TOKENS:
        if token not in test_text:
            failures.append(f"missing_test_token:{token}")

    decisions = {row.get("implementation_decision") for row in rows}
    if "IMPLEMENT_PENDING_INTENT_DECISION_SPREAD_SOURCE_CAPTURE" not in decisions:
        failures.append("missing_decision_spread_value_implementation_row")
    if "IMPLEMENT_PENDING_INTENT_DECISION_SPREAD_UNIT_CAPTURE" not in decisions:
        failures.append("missing_decision_spread_unit_implementation_row")

    for name, meta in manifest.get("outputs", {}).items():
        path = Path(meta.get("path", ""))
        if not path.exists():
            failures.append(f"manifest_output_missing:{name}")
        elif sha256_file(path) != meta.get("sha256"):
            failures.append(f"manifest_output_hash_mismatch:{name}")

    result = {
        "ok": not failures,
        "failures": failures,
        "ledger_rows": len(rows),
        "current_proxy_r_sum_delta": summary.get("current_proxy_r_sum_delta"),
        "current_missing_field_delta": summary.get("current_missing_field_delta"),
        "exact_r_rows": summary.get("exact_r_rows"),
        "safe_flags": SAFE_FLAGS,
    }
    OUTPUT_VERIFICATION.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
