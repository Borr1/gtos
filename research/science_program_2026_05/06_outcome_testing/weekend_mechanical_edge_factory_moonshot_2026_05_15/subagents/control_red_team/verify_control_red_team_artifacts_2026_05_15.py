#!/usr/bin/env python3
"""Lightweight verifier for Worker D control red-team artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CHECKLIST = ROOT / "CONTROL_RED_TEAM_CHECKLIST_2026-05-15.md"
MATRIX = ROOT / "CONTROL_RED_TEAM_TEST_MATRIX_2026-05-15.json"
MANIFEST = ROOT / "CONTROL_RED_TEAM_OUTPUT_MANIFEST_2026-05-15.json"
RESULT = ROOT / "CONTROL_RED_TEAM_VERIFICATION_RESULT_2026-05-15.json"

REQUIRED_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

REQUIRED_CATEGORIES = {
    "duplicate_denominator",
    "concentration_precheck",
    "neighbor_window_placebo",
    "shuffled_label_control",
    "leave_symbol_session_regime_out",
    "purged_embargoed_split",
    "cost_friction_stress",
    "source_bias_missingness",
    "fail_closed_sensitivity",
    "multiple_testing_dsr",
    "cpcv_pbo",
    "neutral_vs_strategy_performance",
}

REQUIRED_PHRASES = [
    "duplicate-effective-N",
    "neighbor-window",
    "shuffled-label",
    "leave-one-symbol",
    "leave-one-session",
    "leave-one-regime",
    "purged",
    "embargoed",
    "cost",
    "friction",
    "source-bias",
    "fail-closed",
    "DSR",
    "PBO",
    "neutral target movement",
    "R/PnL",
    "expectancy",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-result", action="store_true")
    args = parser.parse_args()

    issues: list[str] = []
    for path in (CHECKLIST, MATRIX, MANIFEST):
        if not path.exists():
            issues.append(f"missing artifact: {path.name}")

    matrix: dict[str, Any] = {}
    manifest: dict[str, Any] = {}
    checklist_text = ""

    if MATRIX.exists():
        matrix = load_json(MATRIX)
    if MANIFEST.exists():
        manifest = load_json(MANIFEST)
    if CHECKLIST.exists():
        checklist_text = CHECKLIST.read_text(encoding="utf-8")

    for doc_name, doc in (("matrix", matrix), ("manifest", manifest)):
        flags = doc.get("safe_flags", {})
        for key, expected in REQUIRED_FLAGS.items():
            if flags.get(key) != expected:
                issues.append(f"{doc_name} safe flag mismatch: {key}={flags.get(key)!r}")

    forbidden = matrix.get("forbidden_surfaces", {})
    for key, value in forbidden.items():
        if value is not False:
            issues.append(f"forbidden surface is not closed: {key}={value!r}")

    tests = matrix.get("test_matrix", [])
    ids = [row.get("id") for row in tests]
    if len(ids) != len(set(ids)):
        issues.append("duplicate test ids in matrix")

    categories = {row.get("category") for row in tests}
    missing_categories = sorted(REQUIRED_CATEGORIES - categories)
    if missing_categories:
        issues.append(f"missing required categories: {missing_categories}")

    declared_coverage = set(matrix.get("required_control_coverage", []))
    missing_declared = sorted(REQUIRED_CATEGORIES - declared_coverage)
    if missing_declared:
        issues.append(f"required_control_coverage missing: {missing_declared}")

    missing_phrases = [phrase for phrase in REQUIRED_PHRASES if phrase not in checklist_text]
    if missing_phrases:
        issues.append(f"checklist missing required phrases: {missing_phrases}")

    result = {
        "schema_version": "control_red_team_verification_result_v1",
        "route_id": "weekend_mechanical_edge_factory_moonshot_2026_05_15_control_red_team",
        "ok": not issues,
        "issues": issues,
        "checked_artifacts": [
            CHECKLIST.name,
            MATRIX.name,
            MANIFEST.name,
        ],
        "test_count": len(tests),
        "required_category_count": len(REQUIRED_CATEGORIES),
        "safe_flags": REQUIRED_FLAGS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }

    if args.write_result:
        RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
