"""Verify full-ledger opportunity preservation repair."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_SCORER_SPLIT_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_OUT = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_VERIFICATION_RESULT_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
PREFILL_OWNER_STATUS = "MERGED_TO_ENTRY_OFFSET_PROXY_OWNER"
ENTRY_OFFSET_OWNER = "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"
PREFILL_PROXY_COUNTING = "PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_NOT_DUPLICATED"
FVG_NEGATIVE_BRANCH = "REDESIGN_STANDALONE_FVG_POI_SCORER_CURRENT_PROXY_NEGATIVE_SMALL_N"
REQUIRED_ACTION_CLASSES = {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
FULL_PRESERVATION_FIELDS = (
    "opportunity_preservation_status",
    "opportunity_owner_row_id",
    "opportunity_owner_source_artifact",
    "opportunity_proxy_reference_status",
    "opportunity_not_independently_countable_reason",
    "opportunity_useful_mechanism",
    "opportunity_downstream_paths",
)
AUDIT_FIELDS = (
    "kill_scope",
    "current_claim",
    "unsupported_reason",
    "what_was_tried",
    "what_could_make_it_work",
    "preserve_as",
    "next_route",
)


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


def opportunity_required(row: dict[str, Any]) -> bool:
    return (
        row.get("action_class") in REQUIRED_ACTION_CLASSES
        or row.get("prefill_entry_offset_owner_merge_status") == PREFILL_OWNER_STATUS
    )


def has_full_preservation(row: dict[str, Any]) -> bool:
    audit = row.get("missed_opportunity_audit")
    return (
        all(row.get(field) not in (None, "", []) for field in FULL_PRESERVATION_FIELDS)
        and isinstance(row.get("opportunity_downstream_paths"), list)
        and isinstance(audit, dict)
        and all(audit.get(field) not in (None, "", []) for field in AUDIT_FIELDS)
        and row.get("underlying_intelligence_preserved") is True
    )


def main() -> None:
    issues: list[str] = []
    for path in (INPUT_LEDGER, OUTPUT_LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing:{path.name}")

    input_rows = read_jsonl(INPUT_LEDGER) if INPUT_LEDGER.exists() else []
    rows = read_jsonl(OUTPUT_LEDGER) if OUTPUT_LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    input_ids = [row.get("row_id") for row in input_rows]
    output_ids = [row.get("row_id") for row in rows]
    row_identity_preserved = input_ids == output_ids
    row_ids_unique = len(set(output_ids)) == len(output_ids)
    input_proxy_rows, input_proxy_sum = proxy_summary(input_rows)
    proxy_rows, proxy_sum = proxy_summary(rows)
    input_action_counts = Counter(str(row.get("action_class") or "") for row in input_rows)
    action_counts = Counter(str(row.get("action_class") or "") for row in rows)
    required_rows = [row for row in rows if opportunity_required(row)]
    missing_preservation = [row for row in required_rows if not has_full_preservation(row)]
    prefill_owner_rows = [
        row for row in rows if row.get("prefill_entry_offset_owner_merge_status") == PREFILL_OWNER_STATUS
    ]
    prefill_refs = [
        value for row in prefill_owner_rows if (value := safe_float(row.get("prefill_proxy_reference_r"))) is not None
    ]
    fvg_negative_rows = [row for row in rows if row.get("branch_decision") == FVG_NEGATIVE_BRANCH]
    source_cost_fill_repair_rows = [
        row
        for row in rows
        if row.get("action_class") == "PRESERVE_REQUIREMENT"
        or any(
            token in str(row.get("branch_decision") or "").upper()
            for token in (
                "SOURCE_REQUIRED",
                "SOURCE_REPAIR",
                "SOURCE_COST",
                "EXACT_SOURCE",
                "TICK_ORDER",
                "ORDERING",
                "R_OUTCOME_SOURCE",
                "PARTIAL_REPAIR",
            )
        )
    ]

    if len(rows) != 3426:
        issues.append(f"expected_3426_rows_got_{len(rows)}")
    if len(input_rows) != len(rows):
        issues.append("input_output_row_count_mismatch")
    if not row_identity_preserved:
        issues.append("row_id_or_order_changed")
    if not row_ids_unique:
        issues.append("row_ids_not_unique")
    if summary.get("rows") != len(rows):
        issues.append("summary_rows_mismatch")
    if summary.get("safe_flags") != SAFE_FLAGS or manifest.get("safe_flags") != SAFE_FLAGS:
        issues.append("safe_flags_changed")
    if summary.get("exact_r_rows") != 0:
        issues.append("exact_r_opened")
    if action_counts != input_action_counts or summary.get("action_class_delta") != {}:
        issues.append("action_classes_changed")
    if proxy_rows != input_proxy_rows or not approx(proxy_sum, input_proxy_sum):
        issues.append("counted_proxy_changed")
    if proxy_rows != 709 or not approx(proxy_sum, 33.19811387):
        issues.append(f"unexpected_proxy_total:{proxy_rows}:{proxy_sum}")
    if summary.get("numeric_proxy_row_delta") != 0 or not approx(summary.get("proxy_r_sum_delta"), 0.0):
        issues.append("summary_proxy_delta_not_zero")
    if len(required_rows) != summary.get("opportunity_preservation_required_rows"):
        issues.append("required_opportunity_row_count_mismatch")
    if missing_preservation:
        issues.append(f"missing_full_opportunity_preservation:{len(missing_preservation)}")
    if summary.get("opportunity_preservation_missing_after") != 0:
        issues.append("summary_missing_after_not_zero")
    if summary.get("opportunity_preservation_rows_repaired") != 2489:
        issues.append(f"expected_2489_repaired_rows_got_{summary.get('opportunity_preservation_rows_repaired')}")
    if len(prefill_owner_rows) != 13:
        issues.append(f"expected_13_prefill_owner_rows_got_{len(prefill_owner_rows)}")
    if sum(row.get("action_class") == "REDESIGN" for row in prefill_owner_rows) != 13:
        issues.append("prefill_owner_rows_not_all_redesigned")
    if len(prefill_refs) != 13 or not approx(round(sum(prefill_refs), 8), 8.66977687):
        issues.append("prefill_proxy_reference_mismatch")
    for row in prefill_owner_rows:
        if row.get("after_proxy_r") is not None:
            issues.append("prefill_owner_row_duplicates_counted_proxy")
            break
        if row.get("prefill_proxy_reference_owner") != ENTRY_OFFSET_OWNER:
            issues.append("prefill_owner_reference_owner_mismatch")
            break
        if row.get("prefill_proxy_counting_decision") != PREFILL_PROXY_COUNTING:
            issues.append("prefill_proxy_counting_decision_mismatch")
            break
        if "entry-offset merge" not in row.get("opportunity_downstream_paths", []):
            issues.append("prefill_owner_row_missing_downstream_entry_offset_merge")
            break
    if summary.get("rows_owner_merged") != 13:
        issues.append("summary_rows_owner_merged_not_13")
    if summary.get("rows_redesigned") != 13:
        issues.append("summary_rows_redesigned_not_13")
    if summary.get("proxy_r_rows_referenced") != 13:
        issues.append("summary_proxy_reference_rows_not_13")
    if not approx(summary.get("proxy_r_sum_referenced"), 8.66977687):
        issues.append("summary_proxy_reference_sum_mismatch")
    if summary.get("rows_removed_from_standalone_implementation") != 13:
        issues.append("summary_standalone_removed_not_13")
    if summary.get("rows_preserved_as_entry_offset_owned") != 13:
        issues.append("summary_entry_offset_owned_not_13")
    if len(fvg_negative_rows) != 18:
        issues.append(f"expected_18_fvg_negative_rows_got_{len(fvg_negative_rows)}")
    if not all(has_full_preservation(row) for row in fvg_negative_rows):
        issues.append("fvg_negative_rows_missing_preservation")
    if not all(
        {"redesign", "tighter target", "shorter horizon"}.issubset(set(row.get("opportunity_downstream_paths", [])))
        for row in fvg_negative_rows
    ):
        issues.append("fvg_negative_rows_missing_redesign_path")
    if summary.get("standalone_fvg_negative_small_n_rows_with_audit") != 18:
        issues.append("summary_fvg_negative_audit_not_18")
    if summary.get("rows_requiring_source_cost_fill_repair") != len(source_cost_fill_repair_rows):
        issues.append("source_cost_fill_repair_count_mismatch")
    if summary.get("rows_with_missed_opportunity_audit") != sum(
        isinstance(row.get("missed_opportunity_audit"), dict) for row in rows
    ):
        issues.append("missed_opportunity_audit_count_mismatch")
    if manifest.get("input_files", {}).get("input_ledger", {}).get("sha256") != sha256_file(INPUT_LEDGER):
        issues.append("input_ledger_hash_mismatch")
    if manifest.get("output_files", {}).get("ledger", {}).get("sha256") != sha256_file(OUTPUT_LEDGER):
        issues.append("output_ledger_hash_mismatch")
    if manifest.get("output_files", {}).get("summary", {}).get("sha256") != sha256_file(SUMMARY):
        issues.append("output_summary_hash_mismatch")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "input_rows": len(input_rows),
        "row_identity_preserved": row_identity_preserved,
        "row_order_preserved": row_identity_preserved,
        "row_ids_unique": row_ids_unique,
        "action_class_counts_after": dict(sorted(action_counts.items())),
        "numeric_proxy_rows_after": proxy_rows,
        "proxy_r_sum_after": proxy_sum,
        "opportunity_preservation_required_rows": len(required_rows),
        "opportunity_preservation_rows_repaired": summary.get("opportunity_preservation_rows_repaired"),
        "opportunity_preservation_missing_after": len(missing_preservation),
        "rows_owner_merged": len(prefill_owner_rows),
        "rows_redesigned": sum(row.get("action_class") == "REDESIGN" for row in prefill_owner_rows),
        "proxy_r_rows_referenced": len(prefill_refs),
        "proxy_r_sum_referenced": round(sum(prefill_refs), 8),
        "rows_removed_from_standalone_implementation": summary.get("rows_removed_from_standalone_implementation"),
        "rows_preserved_as_entry_offset_owned": summary.get("rows_preserved_as_entry_offset_owned"),
        "rows_requiring_source_cost_fill_repair": len(source_cost_fill_repair_rows),
        "source_requirement_action_class_rows": action_counts.get("PRESERVE_REQUIREMENT", 0),
        "rows_with_missed_opportunity_audit": summary.get("rows_with_missed_opportunity_audit"),
        "standalone_fvg_negative_small_n_rows": len(fvg_negative_rows),
        "proxy_ownership_verified": not any(
            row.get("after_proxy_r") is not None
            or row.get("prefill_proxy_reference_owner") != ENTRY_OFFSET_OWNER
            or row.get("prefill_proxy_counting_decision") != PREFILL_PROXY_COUNTING
            for row in prefill_owner_rows
        ),
        "safe_flags": SAFE_FLAGS,
    }
    VERIFY_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
