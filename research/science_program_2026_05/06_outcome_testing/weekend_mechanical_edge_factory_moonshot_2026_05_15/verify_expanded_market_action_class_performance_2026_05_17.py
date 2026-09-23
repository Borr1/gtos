#!/usr/bin/env python3
"""Verify expanded-market action-class performance checkpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_ACTION_CLASS_PERF"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECON_SCORER_EXEC"

INPUT_MEMBER_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_EVIDENCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NONIMPLEMENT_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_action_class_performance.py",
    ROUTE_DIR / "build_expanded_market_action_class_performance_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, ROW_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
OBSERVED_R_FIELDS = (
    "observed_gross_simulated_r",
    "observed_cost_adjusted_simulated_r",
    "observed_stress_simulated_r",
    "observed_deconcentrated_cost_adjusted_simulated_r",
    "observed_deconcentrated_stress_simulated_r",
)


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def read_text(path: Path) -> str:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def boundary_ok(row: dict[str, Any]) -> bool:
    boundary = row.get("research_boundary") or {}
    return (
        boundary.get("boundary_schema") == "concrete_branch_local_research_boundary_v1"
        and boundary.get("artifact_scope") == "branch_local_research"
        and boundary.get("production_import_path") is False
        and boundary.get("mutates_order_risk_prompt_safety_or_mt5") is False
        and boundary.get("runtime_candidate_use_permitted") is False
        and boundary.get("unconditional_scalar_use_permitted") is False
    )


def blocked_terms() -> list[str]:
    return [
        "NO_" + "PROMOTION_" + "VERDICT",
        "validation" + "_safe",
        "outcome_" + "review_" + "opened",
        "live_" + "effect",
        "safe" + "_flags",
        "owner_" + "r",
        "broker_" + "r",
        "exact_" + "live_" + "r",
        "live_" + "account_" + "truth",
    ]


def scan_blocked_terms(paths: list[Path]) -> list[str]:
    issues: list[str] = []
    terms = blocked_terms()
    for path in paths:
        text = read_text(path)
        for term in terms:
            if term in text:
                issues.append(f"blocked term {term!r} found in {path.relative_to(REPO)}")
    return issues


def missing_observed_fields(row: dict[str, Any]) -> list[str]:
    return [field for field in OBSERVED_R_FIELDS if row.get(field) in (None, "")]


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    member_input = read_jsonl(INPUT_MEMBER_LEDGER)
    evidence_input = read_jsonl(INPUT_EVIDENCE_LEDGER)
    rows = read_jsonl(ROW_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    expected_counts = {
        "input_member_execution_rows": len(member_input),
        "input_evidence_execution_rows": len(evidence_input),
        "action_class_performance_rows": len(rows),
        "aggregate_rows": len(aggregates),
        "issue_rows": len(issue_rows),
        "system_rows": len(system_rows),
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            issues.append(f"{key} mismatch: result has {counts.get(key)!r}, observed {expected!r}")
    if len(member_input) != 5389:
        issues.append(f"member input count changed from 5389 to {len(member_input)}")
    if len(evidence_input) != 40731:
        issues.append(f"evidence input count changed from 40731 to {len(evidence_input)}")
    if len(rows) != 46120:
        issues.append(f"action row count changed from 46120 to {len(rows)}")
    if issue_rows:
        issues.append("issue ledger must be empty")
    action_counts = counts.get("action_class_counts") or {}
    expected_action_counts = {
        "avoid": 9688,
        "default-off": 1715,
        "follow": 5389,
        "redesign-source-expansion": 3348,
        "redesign-source-repair": 6046,
        "redesign-weak-edge": 19934,
    }
    if action_counts != expected_action_counts:
        issues.append(f"action class counts mismatch: {action_counts!r}")
    if counts.get("scored_action_rows") != 16792:
        issues.append("scored action rows must equal follow plus avoid plus default-off rows")
    if counts.get("missing_action_rows") != 29328:
        issues.append("missing action rows must equal redesign rows")
    if any(not boundary_ok(row) for row in rows + aggregates + issue_rows + system_rows + [result]):
        issues.append("one or more rows failed branch-local boundary checks")
    if any(not row.get("source_path") or not row.get("source_file_sha256") for row in rows):
        issues.append("one or more action rows lacks source path/hash")
    if any(missing_observed_fields(row) for row in rows):
        issues.append("one or more action rows lacks observed simulated R fields")
    for row in rows:
        action_class = row.get("action_class")
        primary_missing = row.get("primary_action_cost_adjusted_simulated_r") is None
        missing_fields = row.get("action_missing_simulated_fields") or []
        if action_class in {"follow", "avoid", "default-off"} and primary_missing:
            issues.append(f"scored action row missing primary R: {row.get('expanded_market_action_class_performance_row_id')}")
            break
        if str(action_class).startswith("redesign") and (
            not primary_missing or missing_fields != ["concrete_replay_implementation_for_redesign_action_r"]
        ):
            issues.append("redesign rows must carry the concrete missing action field")
            break
        if action_class == "avoid" and row.get("proxy_inverse_cost_adjusted_simulated_r") is None:
            issues.append("avoid rows must carry proxy inverse R")
            break
        if action_class == "default-off" and row.get("default_off_account_simulated_r") != 0.0:
            issues.append("default-off rows must carry zero account-action R")
            break
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    print(
        json.dumps(
            {
                "ok": not issues,
                "issues": issues,
                "counts": {
                    "action_class_performance_rows": len(rows),
                    "aggregate_rows": len(aggregates),
                    "scored_action_rows": counts.get("scored_action_rows"),
                    "missing_action_rows": counts.get("missing_action_rows"),
                    "issue_rows": len(issue_rows),
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
