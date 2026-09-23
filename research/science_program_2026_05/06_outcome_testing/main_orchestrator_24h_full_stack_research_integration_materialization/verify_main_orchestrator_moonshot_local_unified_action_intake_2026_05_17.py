"""Verify main-side moonshot local unified action intake."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_LOCAL_UNIFIED_ACTION_INTAKE_LEDGER_{DATE}.jsonl"
OUTPUT_IMPLEMENTATION_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_LOCAL_UNIFIED_IMPLEMENTATION_CANDIDATE_LEDGER_{DATE}.jsonl"
)
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_LOCAL_UNIFIED_ACTION_INTAKE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_LOCAL_UNIFIED_ACTION_INTAKE_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_LOCAL_UNIFIED_ACTION_INTAKE_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_FAMILY_COUNTS = {
    "CURRENT_CLAIM_OPPORTUNITY_AUDIT": 128,
    "DEFAULT_OFF_CODE_CANDIDATE": 553,
    "GUARD_REGISTRY_SPEC": 6232,
    "NOFILL_REDESIGN_SCORING": 9408,
    "RECHECK": 2,
    "SCORE_WITH_CONTROL": 299,
    "SOURCE_CONTROL_REPAIR": 1294,
}

EXPECTED_ACTION_CLASS_COUNTS = {
    "CONTROL_SCORE": 299,
    "CURRENT_CLAIM_REJECTION": 128,
    "GUARD_SPEC": 6232,
    "IMPLEMENTATION_CANDIDATE": 553,
    "RECHECK": 2,
    "REDESIGN_SCORE": 9408,
    "SOURCE_REPAIR": 1294,
}

EXPECTED_SOURCE_FILE_COUNTS = {
    "computed_action_recheck_source": 2,
    "current_claim_opportunity_audit": 128,
    "default_off_code_candidate": 553,
    "exact_control_source_repair": 1294,
    "guard_registry_spec": 6232,
    "nofill_redesign_scoring": 9408,
    "score_with_control": 299,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def require(condition: bool, issues: list[str], message: str) -> None:
    if not condition:
        issues.append(message)


def main() -> None:
    issues: list[str] = []
    rows = read_jsonl(OUTPUT_LEDGER)
    implementation_rows = read_jsonl(OUTPUT_IMPLEMENTATION_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)

    require(len(rows) == 17916, issues, f"expected 17916 intake rows, got {len(rows)}")
    require(summary.get("rows") == 17916, issues, f"summary rows wrong: {summary.get('rows')}")
    require(len(implementation_rows) == 553, issues, f"expected 553 implementation candidates, got {len(implementation_rows)}")
    require(summary.get("implementation_candidate_rows") == 553, issues, "summary implementation count wrong")
    require(
        Counter(row.get("computed_action_family") for row in rows) == Counter(EXPECTED_FAMILY_COUNTS),
        issues,
        f"family counts wrong: {Counter(row.get('computed_action_family') for row in rows)}",
    )
    require(
        Counter(row.get("main_action_class") for row in rows) == Counter(EXPECTED_ACTION_CLASS_COUNTS),
        issues,
        f"main action class counts wrong: {Counter(row.get('main_action_class') for row in rows)}",
    )
    require(summary.get("computed_action_family_counts") == EXPECTED_FAMILY_COUNTS, issues, "summary family counts wrong")
    require(summary.get("main_action_class_counts") == EXPECTED_ACTION_CLASS_COUNTS, issues, "summary action class counts wrong")
    require(summary.get("source_file_row_counts") == EXPECTED_SOURCE_FILE_COUNTS, issues, "source file row counts wrong")
    require(summary.get("result_json_computed_action_family_counts") == EXPECTED_FAMILY_COUNTS, issues, "result JSON family counts wrong")
    require(summary.get("runtime_computed_action_family_counts") == EXPECTED_FAMILY_COUNTS, issues, "runtime family counts wrong")
    require(summary.get("result_json_all_action_result_rows_consumed") is True, issues, "result JSON did not consume all rows")
    require(summary.get("runtime_candidate_use_allowed_now") is False, issues, "runtime candidate use should be false")
    require(summary.get("runtime_score_allowed") is False, issues, "runtime score allowed should be false")
    require(summary.get("runtime_unconditional_scalar_use_allowed") is False, issues, "unconditional scalar use should be false")
    require(summary.get("candidate_use_allowed_now_true_rows") == 0, issues, "candidate use true rows should be zero")
    require(summary.get("live_effect_true_rows") == 0, issues, "live effect true rows should be zero")
    require(summary.get("proxy_delta_counted_as_r_rows") == 0, issues, "proxy deltas must not be counted as R")
    require(summary.get("numeric_proxy_delta_rows", 0) > 0, issues, "numeric proxy delta rows missing")
    require(summary.get("source_files", {}).keys() >= EXPECTED_SOURCE_FILE_COUNTS.keys(), issues, "source file hashes missing")
    require(
        all(info.get("sha256") and info.get("size_bytes", 0) > 0 for info in summary.get("source_files", {}).values()),
        issues,
        "one or more source files missing hash/size",
    )
    require(summary.get("moonshot_snapshot", {}).get("head_short"), issues, "moonshot head snapshot missing")
    require(summary.get("moonshot_snapshot", {}).get("is_dirty") is True, issues, "moonshot dirty state should be recorded true")
    require(manifest.get("safe_flags", {}).get("NO_PROMOTION_VERDICT") is True, issues, "manifest safe flag missing")

    ids = [row.get("intake_row_id") for row in rows]
    require(len(ids) == len(set(ids)), issues, "intake row ids are not unique")
    require(ids[0] == "MAIN-ORCH24-MOONSHOT-ACTION-INTAKE-000001", issues, "first intake id wrong")
    require(ids[-1] == "MAIN-ORCH24-MOONSHOT-ACTION-INTAKE-017916", issues, "last intake id wrong")
    require(
        all(row.get("safe_flags", {}).get("NO_PROMOTION_VERDICT") is True for row in rows),
        issues,
        "safe flags missing on intake rows",
    )
    require(all(row.get("no_live_behavior") is True for row in rows), issues, "no_live_behavior missing")
    require(all(row.get("no_shadow_log_append") is True for row in rows), issues, "no_shadow_log_append missing")
    require(
        all(row.get("proxy_delta_counted_as_r") is False for row in rows),
        issues,
        "at least one row counts proxy delta as R",
    )
    require(
        all(row.get("main_action_class") == "IMPLEMENTATION_CANDIDATE" for row in implementation_rows),
        issues,
        "implementation ledger contains non-candidate rows",
    )
    require(
        {row.get("intake_row_id") for row in implementation_rows}
        == {row.get("intake_row_id") for row in rows if row.get("main_action_class") == "IMPLEMENTATION_CANDIDATE"},
        issues,
        "implementation ledger does not match full ledger filter",
    )
    require(
        all(safe_float(row.get("computed_proxy_delta")) is not None for row in implementation_rows),
        issues,
        "implementation candidate rows should carry computed proxy deltas",
    )

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "implementation_candidate_rows": len(implementation_rows),
        "main_action_class_counts": dict(sorted(Counter(row.get("main_action_class") for row in rows).items())),
        "computed_action_family_counts": dict(sorted(Counter(row.get("computed_action_family") for row in rows).items())),
        "numeric_proxy_delta_rows": summary.get("numeric_proxy_delta_rows"),
        "numeric_proxy_delta_sum_not_r": summary.get("numeric_proxy_delta_sum_not_r"),
        "candidate_use_allowed_now_true_rows": summary.get("candidate_use_allowed_now_true_rows"),
        "live_effect_true_rows": summary.get("live_effect_true_rows"),
        "proxy_delta_counted_as_r_rows": summary.get("proxy_delta_counted_as_r_rows"),
        "safe_flags": summary.get("safe_flags"),
    }
    write_json(OUTPUT_VERIFICATION, result)
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
