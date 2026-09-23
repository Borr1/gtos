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
OUTPUT_SOURCE_LOG = Path("shadow_logs/swing_protected_stop_current_claim_repair_decisions.jsonl")
SUMMARY = (
    ROUTE_DIR
    / "MAIN_ORCH24_SWING_PROTECTED_REPAIR_DEFAULT_SOURCE_MATERIALIZATION_SUMMARY_2026-05-17.json"
)
MANIFEST = (
    ROUTE_DIR
    / "MAIN_ORCH24_SWING_PROTECTED_REPAIR_DEFAULT_SOURCE_MATERIALIZATION_OUTPUT_MANIFEST_2026-05-17.json"
)
VERIFY_RESULT = (
    ROUTE_DIR
    / "MAIN_ORCH24_SWING_PROTECTED_REPAIR_DEFAULT_SOURCE_MATERIALIZATION_VERIFY_RESULT_2026-05-17.json"
)
TARGET_STRATEGY = "V2_STRUCT_SWING_PROTECTED"
SOURCE_STATUS = "ACTION_LEDGER_REPAIRED_SWING_PROTECTED_CURRENT_CLAIM_DECISION"


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
    target_rows = [row for row in action_rows if row.get("strategy_id") == TARGET_STRATEGY]
    output_rows = read_jsonl(OUTPUT_SOURCE_LOG)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    target_keys = {(row.get("candidate_id"), row.get("strategy_id"), row.get("row_id")) for row in target_rows}
    output_keys = {(row.get("candidate_id"), row.get("strategy_id"), row.get("source_row_id")) for row in output_rows}
    statuses = Counter(str(row.get("source_decision_status") or "") for row in output_rows)
    action_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    counted_proxy = [
        value
        for row in output_rows
        if row.get("proxy_r_counting_decision")
        == "COUNT_AS_DEFAULT_OFF_SWING_PROTECTED_STRATEGY_PROXY_R"
        and (value := safe_float(row.get("after_proxy_r"))) is not None
    ]
    reference_proxy = [
        value
        for row in output_rows
        if row.get("proxy_r_counting_decision") == "REFERENCE_ONLY_NOT_COUNTED_AS_STRATEGY_PROXY_R"
        and (value := safe_float(row.get("opportunity_proxy_r_reference"))) is not None
    ]
    source_required_rows = [
        row
        for row in output_rows
        if row.get("opportunity_proxy_reference_status")
        == "NO_NUMERIC_PROXY_CURRENT_ROW_SOURCE_OR_LTF_REQUIRED"
    ]

    if target_keys != output_keys:
        issues.append("output_source_log_keyset_does_not_match_target_action_rows")
    if len(output_rows) != 274:
        issues.append(f"expected_274_rows_found_{len(output_rows)}")
    if statuses.get(SOURCE_STATUS) != 274:
        issues.append("expected_274_repaired_swing_protected_current_claim_decisions")
    if action_counts != Counter({"IMPLEMENT_DEFAULT_OFF": 156, "KILL": 89, "REDESIGN": 29}):
        issues.append(f"unexpected_action_counts:{dict(action_counts)}")
    if len(counted_proxy) != 156:
        issues.append(f"expected_156_counted_proxy_rows_found_{len(counted_proxy)}")
    if round(sum(counted_proxy), 8) != 40.5:
        issues.append("expected_counted_proxy_sum_40_5")
    if len(reference_proxy) != 15:
        issues.append(f"expected_15_reference_proxy_rows_found_{len(reference_proxy)}")
    if round(sum(reference_proxy), 8) != -15.0:
        issues.append("expected_reference_proxy_sum_minus_15")
    if len(source_required_rows) != 14:
        issues.append(f"expected_14_source_requirement_rows_found_{len(source_required_rows)}")
    if any(
        row.get("proxy_r_counting_decision") == "REFERENCE_ONLY_NOT_COUNTED_AS_STRATEGY_PROXY_R"
        and str(row.get("opportunity_proxy_reference_status") or "").startswith("COUNTED_AS")
        for row in output_rows
    ):
        issues.append("reference_rows_marked_counted")
    if summary.get("rows") != len(output_rows):
        issues.append("summary_rows_mismatch")
    if summary.get("proxy_r_rows_counted_as_default_off_strategy") != len(counted_proxy):
        issues.append("summary_counted_proxy_rows_mismatch")
    if summary.get("proxy_r_sum_counted_as_default_off_strategy") != round(sum(counted_proxy), 8):
        issues.append("summary_counted_proxy_sum_mismatch")
    if summary.get("proxy_r_rows_referenced_not_counted") != len(reference_proxy):
        issues.append("summary_reference_proxy_rows_mismatch")
    if summary.get("proxy_r_sum_referenced_not_counted") != round(sum(reference_proxy), 8):
        issues.append("summary_reference_proxy_sum_mismatch")
    if summary.get("rows_requiring_source_cost_fill_repair") != len(source_required_rows):
        issues.append("summary_source_requirement_rows_mismatch")
    if summary.get("missed_opportunity_audit_rows") != 144:
        issues.append("expected_144_missed_opportunity_audit_rows")
    if summary.get("underlying_intelligence_preserved_rows") != 144:
        issues.append("expected_144_underlying_intelligence_preserved_rows")
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
        "source_decision_status_counts": dict(sorted(statuses.items())),
        "action_class_counts": dict(sorted(action_counts.items())),
        "proxy_r_rows_counted_as_default_off_strategy": len(counted_proxy),
        "proxy_r_sum_counted_as_default_off_strategy": round(sum(counted_proxy), 8),
        "proxy_r_rows_referenced_not_counted": len(reference_proxy),
        "proxy_r_sum_referenced_not_counted": round(sum(reference_proxy), 8),
        "rows_requiring_source_cost_fill_repair": len(source_required_rows),
        "missed_opportunity_audit_rows": sum(
            1 for row in output_rows if isinstance(row.get("missed_opportunity_audit"), dict)
        ),
        "underlying_intelligence_preserved_rows": sum(
            1 for row in output_rows if row.get("underlying_intelligence_preserved") is True
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
