"""Verify moonshot source/control selection materialization."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_SOURCE_CONTROL_SELECTION_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_SOURCE_CONTROL_SELECTION_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_SOURCE_CONTROL_SELECTION_OUTPUT_MANIFEST_{DATE}.json"
RESULT = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_SOURCE_CONTROL_SELECTION_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_CLASS_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 39,
    "REDESIGN": 584,
    "SOURCE_REPAIR": 671,
}

EXPECTED_DECISION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF_MARKET_GAP_CODE_CONTROL_PROXY": 19,
    "IMPLEMENT_DEFAULT_OFF_SHADOW_SOURCE_GUARD_SCOPE_PROXY": 20,
    "REDESIGN_MARKET_GAP_CODE_ADVERSE_AVOID_CONTEXT": 270,
    "REDESIGN_MARKET_GAP_CODE_NEUTRAL_CONTROL_SCOPE": 20,
    "REDESIGN_SHADOW_SOURCE_GUARD_ADVERSE_AVOID_CONTEXT": 268,
    "REDESIGN_SHADOW_SOURCE_GUARD_NEUTRAL_SOURCE_SCOPE": 26,
    "SOURCE_REPAIR_DEFAULT_OFF_APPLICATION_EXACT_CONTROL_DENOMINATOR": 111,
    "SOURCE_REPAIR_NOFILL_NEAR_MISS_ATTACH_SATISFIED_SOURCE": 560,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def require(condition: bool, issues: list[str], message: str) -> None:
    if not condition:
        issues.append(message)


def approx_equal(left: float, right: float, tolerance: float = 1e-9) -> bool:
    return abs(left - right) <= tolerance


def verify() -> dict[str, Any]:
    issues: list[str] = []
    rows = read_jsonl(LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    class_counts = dict(Counter(row.get("source_control_selection_class") for row in rows))
    decision_counts = dict(Counter(row.get("source_control_selection_decision") for row in rows))
    proxy_values = [float(row["proxy_delta_reference"]) for row in rows if row.get("proxy_delta_reference") is not None]
    proxy_sum = round(sum(proxy_values), 8)

    require(len(rows) == 1294, issues, f"expected 1294 rows, got {len(rows)}")
    require(class_counts == EXPECTED_CLASS_COUNTS, issues, f"class counts mismatch: {class_counts}")
    require(decision_counts == EXPECTED_DECISION_COUNTS, issues, f"decision counts mismatch: {decision_counts}")
    require(summary.get("rows") == len(rows), issues, "summary row count mismatch")
    require(
        summary.get("source_control_selection_class_counts") == EXPECTED_CLASS_COUNTS,
        issues,
        "summary class counts mismatch",
    )
    require(
        summary.get("source_control_selection_decision_counts") == EXPECTED_DECISION_COUNTS,
        issues,
        "summary decision counts mismatch",
    )
    require(summary.get("implement_default_off_rows") == 39, issues, "implement rows mismatch")
    require(summary.get("redesign_rows") == 584, issues, "redesign rows mismatch")
    require(summary.get("source_repair_rows") == 671, issues, "source repair rows mismatch")
    require(summary.get("unclassified_rows") == 0, issues, "unclassified rows not zero")
    require(summary.get("proxy_delta_reference_rows") == 623, issues, "proxy reference rows mismatch")
    require(approx_equal(float(summary.get("proxy_delta_reference_sum_not_r")), proxy_sum), issues, "proxy sum mismatch")
    require(
        approx_equal(float(summary.get("proxy_delta_reference_sum_not_r")), -128.839535),
        issues,
        "expected proxy sum mismatch",
    )
    require(
        approx_equal(float(summary.get("implement_default_off_proxy_delta_reference_sum_not_r")), 2.428532),
        issues,
        "implement proxy sum mismatch",
    )
    require(
        approx_equal(float(summary.get("redesign_proxy_delta_reference_sum_not_r")), -131.268067),
        issues,
        "redesign proxy sum mismatch",
    )
    require(summary.get("source_repair_proxy_delta_reference_sum_not_r") == 0, issues, "source repair proxy sum mismatch")
    require(summary.get("proxy_delta_reference_counted_as_r_rows") == 0, issues, "proxy references counted as R")
    require(summary.get("opportunity_preserved_rows") == 1294, issues, "opportunity preservation count mismatch")
    require(
        summary.get("underlying_intelligence_preserved_rows") == 1294,
        issues,
        "underlying intelligence preservation count mismatch",
    )
    require(summary.get("live_effect_true_rows") == 0, issues, "live effect true rows present")
    require(summary.get("no_live_behavior_false_rows") == 0, issues, "no_live_behavior false rows present")

    require(manifest.get("counts", {}).get("rows") == 1294, issues, "manifest row mismatch")
    require(manifest.get("counts", {}).get("implement_default_off_rows") == 39, issues, "manifest implement mismatch")
    require(manifest.get("counts", {}).get("redesign_rows") == 584, issues, "manifest redesign mismatch")
    require(manifest.get("counts", {}).get("source_repair_rows") == 671, issues, "manifest source repair mismatch")

    for row in rows:
        row_id = row.get("source_control_selection_row_id")
        require(bool(row_id), issues, "row missing source-control selection row id")
        require(row.get("source_input_line_no"), issues, f"{row_id} missing source input line")
        require(row.get("source_input_sha256"), issues, f"{row_id} missing source input sha")
        require(row.get("source_artifact"), issues, f"{row_id} missing original source artifact")
        require(row.get("source_line_no"), issues, f"{row_id} missing original source line")
        require(row.get("proxy_delta_reference_counted_as_r") is False, issues, f"{row_id} counts proxy as R")
        require(row.get("counted_exact_r") is False, issues, f"{row_id} counts exact R")
        require(row.get("counted_proxy_r") is False, issues, f"{row_id} counts proxy R")
        require(row.get("opportunity_preserved") is True, issues, f"{row_id} did not preserve opportunity")
        require(
            row.get("underlying_intelligence_preserved") is True,
            issues,
            f"{row_id} did not preserve underlying intelligence",
        )
        audit = row.get("missed_opportunity_audit") or {}
        require(bool(audit.get("what_was_tried")), issues, f"{row_id} audit missing what_was_tried")
        require(bool(audit.get("why_not_live_or_independently_countable")), issues, f"{row_id} audit missing boundary")
        require(bool(audit.get("mechanism_remains_useful")), issues, f"{row_id} audit missing mechanism")
        require(bool(audit.get("downstream_path")), issues, f"{row_id} audit missing downstream")
        require(row.get("candidate_use_allowed_now") is False, issues, f"{row_id} candidate use allowed")
        require(row.get("runtime_score_allowed") is False, issues, f"{row_id} runtime score allowed")
        require(row.get("live_effect") is False, issues, f"{row_id} live effect true")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "source_control_selection_class_counts": class_counts,
        "source_control_selection_decision_counts": decision_counts,
        "proxy_delta_reference_rows": summary.get("proxy_delta_reference_rows"),
        "proxy_delta_reference_sum_not_r": summary.get("proxy_delta_reference_sum_not_r"),
        "implement_default_off_rows": summary.get("implement_default_off_rows"),
        "redesign_rows": summary.get("redesign_rows"),
        "source_repair_rows": summary.get("source_repair_rows"),
        "safe_flags": summary.get("safe_flags"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
