"""Verify moonshot source guard selection materialization."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_GUARD_SELECTION_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_GUARD_SELECTION_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_GUARD_SELECTION_OUTPUT_MANIFEST_{DATE}.json"
RESULT = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_GUARD_SELECTION_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_CLASS_COUNTS = {
    "DENOMINATOR_GUARD": 111,
    "DENOMINATOR_GUARD_ADVERSE_CONTEXT": 8,
    "SOURCE_CONFIDENCE_GUARD": 6112,
    "SOURCE_REPAIR": 1,
}

EXPECTED_DECISION_COUNTS = {
    "REGISTER_DENOMINATOR_GUARD_ADVERSE_CONTEXT_DEFAULT_OFF": 8,
    "REGISTER_DENOMINATOR_GUARD_POSITIVE_CONTEXT_DEFAULT_OFF": 111,
    "REGISTER_NOFILL_FAR_MISS_SOURCE_CONFIDENCE_GUARD_DEFAULT_OFF": 6112,
    "REPAIR_SCOPE_BEFORE_DENOMINATOR_OR_SOURCE_CONFIDENCE_GUARD": 1,
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

    class_counts = dict(Counter(row.get("guard_selection_class") for row in rows))
    decision_counts = dict(Counter(row.get("guard_selection_decision") for row in rows))
    proxy_values = [float(row["proxy_delta_reference"]) for row in rows if row.get("proxy_delta_reference") is not None]
    proxy_sum = round(sum(proxy_values), 8)

    require(len(rows) == 6232, issues, f"expected 6232 rows, got {len(rows)}")
    require(class_counts == EXPECTED_CLASS_COUNTS, issues, f"class counts mismatch: {class_counts}")
    require(decision_counts == EXPECTED_DECISION_COUNTS, issues, f"decision counts mismatch: {decision_counts}")
    require(summary.get("rows") == len(rows), issues, "summary row count mismatch")
    require(summary.get("guard_selection_class_counts") == EXPECTED_CLASS_COUNTS, issues, "summary class counts mismatch")
    require(
        summary.get("guard_selection_decision_counts") == EXPECTED_DECISION_COUNTS,
        issues,
        "summary decision counts mismatch",
    )
    require(summary.get("source_confidence_guard_rows") == 6112, issues, "source confidence guard mismatch")
    require(summary.get("denominator_guard_rows") == 111, issues, "denominator guard mismatch")
    require(summary.get("adverse_context_guard_rows") == 8, issues, "adverse context guard mismatch")
    require(summary.get("source_repair_rows") == 1, issues, "source repair mismatch")
    require(summary.get("unclassified_rows") == 0, issues, "unclassified rows not zero")
    require(summary.get("proxy_delta_reference_rows") == 120, issues, "proxy reference rows mismatch")
    require(approx_equal(float(summary.get("proxy_delta_reference_sum_not_r")), proxy_sum), issues, "proxy sum mismatch")
    require(approx_equal(float(summary.get("proxy_delta_reference_sum_not_r")), 4.68), issues, "expected proxy sum mismatch")
    require(summary.get("proxy_delta_reference_counted_as_r_rows") == 0, issues, "proxy references counted as R")
    require(summary.get("source_completeness_action_rows") == 6232, issues, "source completeness count mismatch")
    require(summary.get("opportunity_preserved_rows") == 6232, issues, "opportunity preservation count mismatch")
    require(
        summary.get("underlying_intelligence_preserved_rows") == 6232,
        issues,
        "underlying intelligence preservation count mismatch",
    )
    require(summary.get("live_effect_true_rows") == 0, issues, "live effect true rows present")
    require(summary.get("no_live_behavior_false_rows") == 0, issues, "no_live_behavior false rows present")

    require(manifest.get("counts", {}).get("rows") == 6232, issues, "manifest row mismatch")
    require(manifest.get("counts", {}).get("source_confidence_guard_rows") == 6112, issues, "manifest source guard mismatch")
    require(manifest.get("counts", {}).get("denominator_guard_rows") == 111, issues, "manifest denominator mismatch")
    require(manifest.get("counts", {}).get("adverse_context_guard_rows") == 8, issues, "manifest adverse mismatch")
    require(manifest.get("counts", {}).get("source_repair_rows") == 1, issues, "manifest source repair mismatch")

    for row in rows:
        row_id = row.get("guard_selection_row_id")
        require(bool(row_id), issues, "row missing guard selection row id")
        require(row.get("source_input_line_no"), issues, f"{row_id} missing source input line")
        require(row.get("source_input_sha256"), issues, f"{row_id} missing source input sha")
        require(row.get("source_artifact"), issues, f"{row_id} missing original source artifact")
        require(row.get("source_line_no"), issues, f"{row_id} missing original source line")
        require(row.get("source_completeness_action") is True, issues, f"{row_id} missing source action")
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
        "guard_selection_class_counts": class_counts,
        "guard_selection_decision_counts": decision_counts,
        "proxy_delta_reference_rows": summary.get("proxy_delta_reference_rows"),
        "proxy_delta_reference_sum_not_r": summary.get("proxy_delta_reference_sum_not_r"),
        "source_confidence_guard_rows": summary.get("source_confidence_guard_rows"),
        "denominator_guard_rows": summary.get("denominator_guard_rows"),
        "adverse_context_guard_rows": summary.get("adverse_context_guard_rows"),
        "source_repair_rows": summary.get("source_repair_rows"),
        "safe_flags": summary.get("safe_flags"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
