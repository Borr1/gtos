from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
INPUT_ACTION_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_2026-05-17.jsonl"
)
OUTPUT_SOURCE_LOG = Path("shadow_logs/standalone_fvg_poi_current_claim_repair_decisions.jsonl")
SUMMARY = (
    ROUTE_DIR / "MAIN_ORCH24_STANDALONE_FVG_REPAIR_DEFAULT_SOURCE_MATERIALIZATION_SUMMARY_2026-05-17.json"
)
MANIFEST = (
    ROUTE_DIR
    / "MAIN_ORCH24_STANDALONE_FVG_REPAIR_DEFAULT_SOURCE_MATERIALIZATION_OUTPUT_MANIFEST_2026-05-17.json"
)
VERIFY_RESULT = (
    ROUTE_DIR / "MAIN_ORCH24_STANDALONE_FVG_REPAIR_DEFAULT_SOURCE_MATERIALIZATION_VERIFY_RESULT_2026-05-17.json"
)
TARGET_BRANCH = "REDESIGN_STANDALONE_FVG_POI_SCORER_CURRENT_PROXY_NEGATIVE_SMALL_N"


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
    action_rows = read_jsonl(INPUT_ACTION_LEDGER)
    target_rows = [row for row in action_rows if row.get("branch_decision") == TARGET_BRANCH]
    output_rows = read_jsonl(OUTPUT_SOURCE_LOG)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    target_keys = {(row.get("candidate_id"), row.get("strategy_id"), row.get("row_id")) for row in target_rows}
    output_keys = {(row.get("candidate_id"), row.get("strategy_id"), row.get("source_row_id")) for row in output_rows}
    proxy_refs = [
        value
        for row in output_rows
        if (value := safe_float(row.get("opportunity_proxy_r_reference"))) is not None
    ]
    statuses = Counter(str(row.get("source_decision_status") or "") for row in output_rows)

    if target_keys != output_keys:
        issues.append("output_source_log_keyset_does_not_match_target_action_rows")
    if len(output_rows) != 18:
        issues.append(f"expected_18_rows_found_{len(output_rows)}")
    if statuses.get("ACTION_LEDGER_REPAIRED_CURRENT_CLAIM_DECISION") != 18:
        issues.append("expected_18_repaired_current_claim_decisions")
    if len(proxy_refs) != 5:
        issues.append(f"expected_5_proxy_refs_found_{len(proxy_refs)}")
    if round(sum(proxy_refs), 8) != -5.0:
        issues.append("expected_proxy_ref_sum_minus_5")
    if any(row.get("opportunity_proxy_reference_status") != "REFERENCE_ONLY_CURRENT_STANDALONE_FVG_CLAIM_NOT_COUNTED" for row in output_rows):
        issues.append("proxy_reference_status_not_reference_only")
    if any(row.get("underlying_intelligence_preserved") is not True for row in output_rows):
        issues.append("underlying_intelligence_not_preserved")
    if any(not isinstance(row.get("missed_opportunity_audit"), dict) for row in output_rows):
        issues.append("missed_opportunity_audit_missing")
    if any(row.get("safe_flags", {}).get("live_effect") is not False for row in output_rows):
        issues.append("live_effect_flag_not_false")
    if summary.get("rows") != len(output_rows):
        issues.append("summary_rows_mismatch")
    if summary.get("proxy_r_rows_referenced_not_counted") != len(proxy_refs):
        issues.append("summary_proxy_ref_rows_mismatch")
    if summary.get("proxy_r_sum_referenced_not_counted") != round(sum(proxy_refs), 8):
        issues.append("summary_proxy_ref_sum_mismatch")
    if summary.get("missed_opportunity_audit_rows") != len(output_rows):
        issues.append("summary_missed_audit_rows_mismatch")
    if manifest.get("outputs", {}).get("default_source_log", {}).get("sha256") != sha256_file(OUTPUT_SOURCE_LOG):
        issues.append("manifest_output_hash_mismatch")
    if manifest.get("inputs", {}).get("action_ledger", {}).get("sha256") != sha256_file(INPUT_ACTION_LEDGER):
        issues.append("manifest_input_hash_mismatch")
    if manifest.get("safe_flags", {}).get("live_effect") is not False:
        issues.append("manifest_live_effect_not_false")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(output_rows),
        "proxy_r_rows_referenced_not_counted": len(proxy_refs),
        "proxy_r_sum_referenced_not_counted": round(sum(proxy_refs), 8),
        "source_decision_status_counts": dict(sorted(statuses.items())),
        "output_source_log_sha256": sha256_file(OUTPUT_SOURCE_LOG),
        "safe_flags": summary.get("safe_flags"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
