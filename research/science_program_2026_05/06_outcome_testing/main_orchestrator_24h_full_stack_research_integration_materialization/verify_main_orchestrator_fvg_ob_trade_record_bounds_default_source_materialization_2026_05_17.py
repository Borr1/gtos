"""Verify FVG/OB trade-record bounds default source materialization."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
SOURCE_LOG = ROOT / "shadow_logs/fvg_ob_trade_record_bounds_current_repair_decisions.jsonl"
SUMMARY = (
    ROUTE_DIR
    / "MAIN_ORCH24_FVG_OB_TR_BOUNDS_SOURCE_SUMMARY_2026-05-17.json"
)
MANIFEST = (
    ROUTE_DIR
    / "MAIN_ORCH24_FVG_OB_TR_BOUNDS_SOURCE_MANIFEST_2026-05-17.json"
)
VERIFY_OUT = (
    ROUTE_DIR
    / "MAIN_ORCH24_FVG_OB_TR_BOUNDS_SOURCE_VERIFY_RESULT_2026-05-17.json"
)
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
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
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def main() -> None:
    issues: list[str] = []
    for path in (SOURCE_LOG, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing:{path.name}")

    rows = read_jsonl(SOURCE_LOG) if SOURCE_LOG.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    proxy_refs = [
        value for row in rows if (value := safe_float(row.get("opportunity_proxy_r_reference"))) is not None
    ]
    if len(rows) != 1:
        issues.append(f"expected_1_source_row_found_{len(rows)}")
    if summary.get("rows") != len(rows):
        issues.append("summary_rows_mismatch")
    if summary.get("safe_flags") != SAFE_FLAGS or manifest.get("safe_flags") != SAFE_FLAGS:
        issues.append("safe_flags_changed")
    if summary.get("proxy_r_rows_referenced_not_counted") != len(proxy_refs):
        issues.append("proxy_reference_rows_mismatch")
    if summary.get("proxy_r_sum_referenced_not_counted") != round(sum(proxy_refs), 8):
        issues.append("proxy_reference_sum_mismatch")
    if summary.get("counted_strategy_proxy_r_rows") != 0:
        issues.append("counted_strategy_proxy_opened")
    if any(row.get("after_proxy_r") is not None for row in rows):
        issues.append("source_row_after_proxy_r_not_null")
    if rows:
        row = rows[0]
        if row.get("source_decision_status") != (
            "ACTION_LEDGER_REPAIRED_FVG_OB_TRADE_RECORD_BOUNDS_DECISION"
        ):
            issues.append("source_decision_status_mismatch")
        if row.get("candidate_id") != "GBPJPY_2026-05-04T03:00:00+00:00":
            issues.append("candidate_id_mismatch")
        if row.get("strategy_id") != "FVG_OB_CONFLUENCE_OB_AFTER_FVG":
            issues.append("strategy_id_mismatch")
        if row.get("branch_decision") != (
            "REDESIGN_FVG_OB_BUCKET_REPAIRED_AS_FVG_ONLY_NO_OB_CONFLUENCE"
        ):
            issues.append("branch_decision_mismatch")
        if row.get("opportunity_proxy_reference_status") != (
            "REFERENCE_ONLY_SHARED_PATH_PROXY_NOT_FVG_OB_IMPLEMENTATION"
        ):
            issues.append("proxy_reference_status_mismatch")
        if not isinstance(row.get("fvg_exact_bounds"), dict):
            issues.append("missing_fvg_exact_bounds")
        if row.get("ob_leg_status") != (
            "NO_OB_BOUNDS_IN_TRADE_RECORD_L2_OB_CHECKS_SKIPPED_FVG_FILL_PATH"
        ):
            issues.append("ob_leg_status_mismatch")
        if row.get("underlying_intelligence_preserved") is not True:
            issues.append("underlying_intelligence_not_preserved")
        if not isinstance(row.get("missed_opportunity_audit"), dict):
            issues.append("missing_missed_opportunity_audit")
    if SOURCE_LOG.exists() and manifest.get("outputs", {}).get("default_source_log", {}).get(
        "sha256"
    ) != sha256_file(SOURCE_LOG):
        issues.append("source_log_hash_mismatch")
    if SUMMARY.exists() and manifest.get("outputs", {}).get("summary", {}).get(
        "sha256"
    ) != sha256_file(SUMMARY):
        issues.append("summary_hash_mismatch")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "proxy_r_rows_referenced_not_counted": len(proxy_refs),
        "proxy_r_sum_referenced_not_counted": round(sum(proxy_refs), 8),
        "counted_strategy_proxy_r_rows": summary.get("counted_strategy_proxy_r_rows"),
        "safe_flags": SAFE_FLAGS,
    }
    VERIFY_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
