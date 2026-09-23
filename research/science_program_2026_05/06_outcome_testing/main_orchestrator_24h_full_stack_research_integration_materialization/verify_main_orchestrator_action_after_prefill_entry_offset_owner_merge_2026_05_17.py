"""Verify prefill entry-offset owner merge action ledger."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_ENTRY_OFFSET_OWNER_MERGE_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_ENTRY_OFFSET_OWNER_MERGE_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_ENTRY_OFFSET_OWNER_MERGE_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_OUT = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_ENTRY_OFFSET_OWNER_MERGE_VERIFICATION_RESULT_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

TARGET_SURFACE = "prefill_delivery_after_entry_offset_repair_decision"
OWNER = "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"
FAR_BRANCH = "REDESIGN_PREFILL_FAR_MISS_RETEST_CONTROL_MERGED_INTO_ENTRY_OFFSET_050R"
NEAR_BRANCH = "MERGE_PREFILL_NEAR_MISS_INTO_ENTRY_OFFSET_050R_IMPLEMENTATION"
PROXY_COUNTING = "PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_NOT_DUPLICATED"
STANDALONE_FVG_NEGATIVE_BRANCH = "REDESIGN_STANDALONE_FVG_POI_SCORER_CURRENT_PROXY_NEGATIVE_SMALL_N"


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


def approx(left: float | None, right: float | None, tolerance: float = 1e-8) -> bool:
    if left is None or right is None:
        return left is right
    return abs(left - right) <= tolerance


def proxy_summary(rows: list[dict[str, Any]]) -> tuple[int, float]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return len(values), round(sum(values), 8)


def has_opportunity_preservation(row: dict[str, Any]) -> bool:
    required = (
        "opportunity_preservation_status",
        "opportunity_owner_row_id",
        "opportunity_owner_source_artifact",
        "opportunity_proxy_reference_status",
        "opportunity_not_independently_countable_reason",
        "opportunity_useful_mechanism",
        "opportunity_downstream_paths",
    )
    return (
        all(row.get(field) not in (None, "", []) for field in required)
        and isinstance(row.get("missed_opportunity_audit"), dict)
        and row.get("underlying_intelligence_preserved") is True
    )


def main() -> None:
    issues: list[str] = []
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    touched = [
        row
        for row in rows
        if row.get("prefill_entry_offset_owner_merge_status") == "MERGED_TO_ENTRY_OFFSET_PROXY_OWNER"
    ]
    far = [row for row in touched if row.get("branch_decision") == FAR_BRANCH]
    near = [row for row in touched if row.get("branch_decision") == NEAR_BRANCH]
    numeric_count, proxy_sum = proxy_summary(rows)
    reference_values = [value for row in touched if (value := safe_float(row.get("prefill_proxy_reference_r"))) is not None]
    action_counts = Counter(str(row.get("action_class") or "") for row in rows)
    branch_counts = Counter(str(row.get("branch_decision") or "") for row in touched)
    weak_fvg = [row for row in rows if row.get("branch_decision") == STANDALONE_FVG_NEGATIVE_BRANCH]
    weak_fvg_values = [value for row in weak_fvg if (value := safe_float(row.get("opportunity_proxy_r_reference"))) is not None]
    source_requirements = [row for row in rows if row.get("action_class") == "PRESERVE_REQUIREMENT"]
    source_requirement_values = [
        value for row in source_requirements if (value := safe_float(row.get("opportunity_proxy_r_reference"))) is not None
    ]
    audited_rows = [row for row in rows if isinstance(row.get("missed_opportunity_audit"), dict)]

    if len(rows) != 3426:
        issues.append(f"expected_3426_rows_got_{len(rows)}")
    if summary.get("rows") != len(rows):
        issues.append("summary row count mismatch")
    if summary.get("safe_flags") != SAFE_FLAGS or manifest.get("safe_flags") != SAFE_FLAGS:
        issues.append("safe flags changed")
    if summary.get("exact_r_rows") != 0:
        issues.append("exact R rows opened unexpectedly")
    if len(touched) != 13:
        issues.append(f"expected_13_touched_rows_got_{len(touched)}")
    if len(far) != 10:
        issues.append(f"expected_10_far_merge_rows_got_{len(far)}")
    if len(near) != 3:
        issues.append(f"expected_3_near_merge_rows_got_{len(near)}")
    if numeric_count != 697 or not approx(proxy_sum, 57.40613887):
        issues.append(f"proxy total changed unexpectedly:{numeric_count}:{proxy_sum}")
    if summary.get("numeric_proxy_row_delta") != 0 or not approx(summary.get("proxy_r_sum_delta"), 0.0):
        issues.append("counted proxy R changed")
    if len(reference_values) != 13 or not approx(round(sum(reference_values), 8), 8.66977687):
        issues.append("reference proxy R mismatch")
    if summary.get("rows_owner_merged") != 13:
        issues.append("rows_owner_merged_not_13")
    if summary.get("rows_removed_from_standalone_implementation") != 13:
        issues.append("rows_removed_from_standalone_implementation_not_13")
    if summary.get("rows_preserved_as_entry_offset_owned") != 13:
        issues.append("rows_preserved_as_entry_offset_owned_not_13")
    if summary.get("reference_proxy_numeric_rows") != 13:
        issues.append("summary_reference_proxy_rows_not_13")
    if not approx(summary.get("reference_proxy_r_sum_not_counted"), 8.66977687):
        issues.append("summary_reference_proxy_sum_mismatch")
    expected_delta = {"IMPLEMENT_DEFAULT_OFF": -13, "KEEP": 3, "REDESIGN": 10}
    if summary.get("action_class_delta_vs_previous") != expected_delta:
        issues.append(f"action delta mismatch:{summary.get('action_class_delta_vs_previous')}")
    expected_after_counts = {
        "IMPLEMENT_DEFAULT_OFF": 418,
        "KEEP": 435,
        "KILL": 967,
        "PRESERVE_REQUIREMENT": 98,
        "REDESIGN": 1508,
    }
    for key, expected in expected_after_counts.items():
        if action_counts.get(key) != expected:
            issues.append(f"action_count_{key}_expected_{expected}_got_{action_counts.get(key)}")
    if summary.get("kill_count_delta") != 0 or action_counts.get("KILL") != 967:
        issues.append("kill count changed")
    if summary.get("remaining_prefill_default_off_without_proxy_rows") != 0:
        issues.append("prefill default-off rows without proxy remain")
    if branch_counts.get(FAR_BRANCH) != 10 or branch_counts.get(NEAR_BRANCH) != 3:
        issues.append(f"branch count mismatch:{dict(branch_counts)}")
    if len(weak_fvg) != 18:
        issues.append(f"weak_fvg_rows_expected_18_got_{len(weak_fvg)}")
    if len(weak_fvg_values) != 5 or not approx(round(sum(weak_fvg_values), 8), -5.0):
        issues.append("weak_fvg_proxy_reference_mismatch")
    if summary.get("standalone_fvg_negative_small_n_rows_audited") != 18:
        issues.append("summary_weak_fvg_audited_not_18")
    if len(source_requirements) != 98:
        issues.append(f"source_requirement_rows_expected_98_got_{len(source_requirements)}")
    if len(source_requirement_values) != 14 or not approx(round(sum(source_requirement_values), 8), -0.791975):
        issues.append("source_requirement_proxy_reference_mismatch")
    if summary.get("rows_requiring_source_cost_fill_repair_after") != 98:
        issues.append("summary_source_cost_fill_repair_rows_not_98")
    if summary.get("source_requirement_rows_audit_repaired") != 43:
        issues.append("summary_source_requirement_audit_repaired_not_43")
    if summary.get("source_requirement_rows_opportunity_preserved") != 98:
        issues.append("summary_source_requirement_preserved_not_98")
    if summary.get("opportunity_preservation_rows_touched") != 74:
        issues.append("summary_opportunity_preservation_rows_touched_not_74")
    if summary.get("rows_with_missed_opportunity_audit_after") != 2576 or len(audited_rows) != 2576:
        issues.append("missed_opportunity_audit_total_mismatch")
    if summary.get("redesign_rows_missing_missed_opportunity_audit_after") != 0:
        issues.append("redesign rows missing audit")
    if summary.get("preserve_requirement_rows_missing_missed_opportunity_audit_after") != 0:
        issues.append("preserve requirement rows missing audit")
    if summary.get("kill_rows_missing_missed_opportunity_audit_after") != 0:
        issues.append("kill rows missing audit")

    for row in far:
        if row.get("action_class") != "REDESIGN":
            issues.append("far prefill owner merge row is not REDESIGN")
            break
        if row.get("underlying_intelligence_preserved") is not True:
            issues.append("far row did not preserve underlying intelligence")
            break
        if not has_opportunity_preservation(row):
            issues.append("far row missing opportunity preservation fields")
            break
    for row in near:
        if row.get("action_class") != "KEEP":
            issues.append("near prefill owner merge row is not KEEP")
            break
        if row.get("underlying_intelligence_preserved") is not True:
            issues.append("near row did not preserve underlying intelligence")
            break
        if not has_opportunity_preservation(row):
            issues.append("near row missing opportunity preservation fields")
            break
    for row in touched:
        if row.get("after_proxy_r") is not None:
            issues.append("touched prefill row duplicated counted proxy R")
            break
        if row.get("prefill_proxy_reference_owner") != OWNER:
            issues.append("touched row missing entry-offset proxy owner")
            break
        if row.get("prefill_proxy_counting_decision") != PROXY_COUNTING:
            issues.append("touched row missing no-duplicate proxy decision")
            break
        audit = row.get("missed_opportunity_audit")
        if not isinstance(audit, dict) or audit.get("kill_scope") != "NOT_KILLED_MERGED_ENTRY_OFFSET_OWNER":
            issues.append("touched row missing not-killed missed-opportunity audit")
            break
        if row.get("safe_flags") != SAFE_FLAGS or row.get("no_live_behavior") is not True:
            issues.append("touched row safe flags missing")
            break
        if row.get("opportunity_proxy_reference_status") != "REFERENCE_ONLY_NOT_COUNTED_DUPLICATE_ENTRY_OFFSET_OWNER":
            issues.append("touched row missing reference-only proxy status")
            break
        if safe_float(row.get("opportunity_proxy_r_reference")) is None:
            issues.append("touched row missing proxy R reference")
            break

    for row in weak_fvg:
        audit = row.get("missed_opportunity_audit")
        if not has_opportunity_preservation(row):
            issues.append("weak FVG negative row missing opportunity preservation")
            break
        if audit.get("kill_scope") != "NOT_KILLED_CURRENT_STANDALONE_FVG_CLAIM_REDESIGN":
            issues.append("weak FVG negative row audit scope mismatch")
            break
        if "redesign" not in row.get("opportunity_downstream_paths", []):
            issues.append("weak FVG row missing redesign downstream path")
            break

    for row in source_requirements:
        audit = row.get("missed_opportunity_audit")
        if not has_opportunity_preservation(row):
            issues.append("source requirement row missing opportunity preservation")
            break
        if not str(audit.get("kill_scope") or "").startswith("NOT_KILLED"):
            issues.append("source requirement row audit scope mismatch")
            break
        if "source requirement" not in row.get("opportunity_downstream_paths", []):
            issues.append("source requirement row missing downstream source requirement path")
            break

    no_proxy_impl = [
        row
        for row in rows
        if row.get("source_capture_surface") == TARGET_SURFACE
        and row.get("action_class") == "IMPLEMENT_DEFAULT_OFF"
        and row.get("after_proxy_r") is None
    ]
    if no_proxy_impl:
        issues.append(f"remaining no-proxy prefill implementations:{len(no_proxy_impl)}")

    if LEDGER.exists() and manifest.get("outputs", {}).get("ledger", {}).get("sha256") != sha256_file(LEDGER):
        issues.append("ledger manifest hash mismatch")
    if SUMMARY.exists() and manifest.get("outputs", {}).get("summary", {}).get("sha256") != sha256_file(SUMMARY):
        issues.append("summary manifest hash mismatch")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "touched_rows": len(touched),
        "far_miss_rows_merged_to_redesign": len(far),
        "near_miss_rows_merged_to_entry_offset": len(near),
        "numeric_proxy_rows_after": numeric_count,
        "proxy_r_sum_after": proxy_sum,
        "reference_proxy_numeric_rows": len(reference_values),
        "reference_proxy_r_sum_not_counted": round(sum(reference_values), 8),
        "rows_owner_merged": len(touched),
        "rows_removed_from_standalone_implementation": summary.get("rows_removed_from_standalone_implementation"),
        "rows_preserved_as_entry_offset_owned": summary.get("rows_preserved_as_entry_offset_owned"),
        "standalone_fvg_negative_small_n_rows_audited": len(weak_fvg),
        "standalone_fvg_negative_small_n_proxy_reference_rows": len(weak_fvg_values),
        "standalone_fvg_negative_small_n_proxy_reference_sum": round(sum(weak_fvg_values), 8),
        "rows_requiring_source_cost_fill_repair_after": len(source_requirements),
        "source_requirement_rows_audit_repaired": summary.get("source_requirement_rows_audit_repaired"),
        "source_requirement_proxy_reference_rows": len(source_requirement_values),
        "source_requirement_proxy_reference_sum": round(sum(source_requirement_values), 8),
        "opportunity_preservation_rows_touched": summary.get("opportunity_preservation_rows_touched"),
        "rows_with_missed_opportunity_audit_after": len(audited_rows),
        "action_class_counts_after": dict(sorted(action_counts.items())),
        "prefill_owner_merge_branch_counts": dict(sorted(branch_counts.items())),
        "safe_flags": SAFE_FLAGS,
    }
    VERIFY_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
