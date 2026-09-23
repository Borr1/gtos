"""Verify NAS100 depth-thinness source repair materialization."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
ROUTE_ID = "MAIN_ORCH24_NAS100_DEPTH_THINNESS_SOURCE_REPAIR"
STRATEGY_ID = "NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC"

SOURCE_LOG = ROOT / "shadow_logs/nas100_depth_thinness_current_source_repair_decisions.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_NAS100_DEPTH_THINNESS_SOURCE_REPAIR_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_NAS100_DEPTH_THINNESS_SOURCE_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_OUT = ROUTE_DIR / f"MAIN_ORCH24_NAS100_DEPTH_THINNESS_SOURCE_REPAIR_VERIFY_RESULT_{DATE}.json"

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
    for path in (SOURCE_LOG, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing:{path.name}")
    rows = read_jsonl(SOURCE_LOG) if SOURCE_LOG.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    action_counts = Counter(str(row.get("action_class") or "") for row in rows)
    feature_counts = Counter(str(row.get("feature_status") or "") for row in rows)
    branch_counts = Counter(str(row.get("branch_decision") or "") for row in rows)
    keys = {(row.get("candidate_id"), row.get("strategy_id")) for row in rows}
    heavy_rows = [row for row in rows if row.get("action_class") == "SOURCE_REPAIR"]
    keep_rows = [row for row in rows if row.get("action_class") == "KEEP"]
    redesign_rows = [row for row in rows if row.get("action_class") == "REDESIGN"]

    if summary.get("route_id") != ROUTE_ID:
        issues.append("route_id_mismatch")
    if len(rows) != 72 or summary.get("source_rows") != len(rows):
        issues.append(f"expected_72_source_rows_found_{len(rows)}")
    if len(keys) != len(rows):
        issues.append("duplicate_candidate_strategy_keys")
    if any(row.get("strategy_id") != STRATEGY_ID for row in rows):
        issues.append("unexpected_strategy_id")
    if any(row.get("exact_r") is not None or row.get("strategy_proxy_r") is not None for row in rows):
        issues.append("depth_rows_opened_r")
    if (
        action_counts.get("SOURCE_REPAIR", 0)
        + action_counts.get("KEEP", 0)
        + action_counts.get("REDESIGN", 0)
        + action_counts.get("PATH_PROXY_DECISION", 0)
        != len(rows)
    ):
        issues.append(f"unexpected_action_counts:{dict(action_counts)}")
    if summary.get("action_class_counts") != dict(sorted(action_counts.items())):
        issues.append("summary_action_counts_mismatch")
    if summary.get("feature_status_counts") != dict(sorted(feature_counts.items())):
        issues.append("summary_feature_counts_mismatch")
    if summary.get("branch_decision_counts") != dict(sorted(branch_counts.items())):
        issues.append("summary_branch_counts_mismatch")
    if summary.get("source_complete_context_rows") != len(keep_rows):
        issues.append("keep_context_count_mismatch")
    if summary.get("source_complete_no_sample_redesign_rows") != len(redesign_rows):
        issues.append("redesign_no_sample_count_mismatch")
    if summary.get("heavy_scan_source_required_rows") != len(heavy_rows):
        issues.append("heavy_scan_count_mismatch")
    if any(not row.get("missing_field") for row in heavy_rows + redesign_rows):
        issues.append("missing_field_not_exact")
    if any(row.get("underlying_intelligence_preserved") is not True for row in rows):
        issues.append("underlying_intelligence_not_preserved")
    if any(not isinstance(row.get("missed_opportunity_audit"), dict) for row in rows):
        issues.append("missed_opportunity_audit_missing")
    if manifest.get("output_files", {}).get("source_log", {}).get("sha256") != sha256_file(SOURCE_LOG):
        issues.append("source_log_hash_mismatch")
    if manifest.get("output_files", {}).get("summary", {}).get("sha256") != sha256_file(SUMMARY):
        issues.append("summary_hash_mismatch")

    result = {
        "verified": not issues,
        "issues": issues,
        "source_rows": len(rows),
        "action_class_counts": dict(sorted(action_counts.items())),
        "feature_status_counts": dict(sorted(feature_counts.items())),
        "exact_r_rows": 0,
        "proxy_r_rows_counted": 0,
        "path_proxy_r_rows": summary.get("path_proxy_r_rows"),
        "path_proxy_r_sum": summary.get("path_proxy_r_sum"),
    }
    VERIFY_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
