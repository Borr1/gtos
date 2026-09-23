#!/usr/bin/env python3
"""Verify expanded-market repair implementation handoff checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION"

INPUT_ARTIFACT_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ARTIFACT_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_EVIDENCE_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
HANDOFF_LEDGER = ROUTE_DIR / f"{PREFIX}_HANDOFF_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_repair_implementation_handoff.py",
    ROUTE_DIR / "build_expanded_market_repair_implementation_handoff_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    HANDOFF_LEDGER,
    EVIDENCE_LEDGER,
    CONTROL_LEDGER,
    AGGREGATE_LEDGER,
    ISSUE_LEDGER,
    SYSTEM_LEDGER,
    SUMMARY_PATH,
]


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


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


def ids_from(path: Path, field: str) -> set[str]:
    return {str(row.get(field) or "") for row in iter_jsonl(path)}


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}

    input_artifact_execution_ids = ids_from(
        INPUT_ARTIFACT_EXECUTION_LEDGER,
        "expanded_market_repair_final_artifact_execution_row_id",
    )
    input_evidence_execution_ids = ids_from(
        INPUT_EVIDENCE_EXECUTION_LEDGER,
        "expanded_market_repair_final_artifact_evidence_execution_row_id",
    )
    input_control_execution_ids = ids_from(
        INPUT_CONTROL_EXECUTION_LEDGER,
        "expanded_market_repair_final_artifact_execution_control_row_id",
    )

    handoff_input_ids: set[str] = set()
    handoff_count = 0
    handoff_ready_count = 0
    decision_counts: Counter[str] = Counter()
    for row in iter_jsonl(HANDOFF_LEDGER):
        handoff_count += 1
        handoff_input_ids.add(str(row.get("input_repair_final_artifact_execution_row_id") or ""))
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more handoff rows failed branch-local boundary checks")
            break
        if row.get("implementation_handoff_status") == "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_HANDOFF_READY":
            handoff_ready_count += 1
        else:
            issues.append("one or more handoff rows is not ready")
            break
        required_fields = [
            "implementation_handoff_scope",
            "implementation_handoff_signature_sha256",
            "implementation_handoff_acceptance_sha256",
            "implementation_handoff_function_name",
            "implementation_handoff_expression",
            "implementation_handoff_scope_sha256",
            "implementation_handoff_source_path",
            "implementation_handoff_source_file_sha256",
            "implementation_handoff_entry_reference",
            "implementation_handoff_path_order_result",
            "implementation_handoff_fill_status",
            "implementation_handoff_proxy_entry_price",
            "implementation_handoff_proxy_denominator_price",
            "implementation_handoff_proxy_target_price",
            "implementation_handoff_proxy_stop_price",
            "implementation_handoff_cost_adjusted_simulated_r",
            "implementation_handoff_stress_simulated_r",
            "implementation_handoff_effective_n",
        ]
        if any(row.get(field) in (None, "", {}) for field in required_fields):
            issues.append("one or more handoff rows lacks required implementation packet fields")
            break

    evidence_input_ids: set[str] = set()
    evidence_count = 0
    for row in iter_jsonl(EVIDENCE_LEDGER):
        evidence_count += 1
        evidence_input_ids.add(str(row.get("input_repair_final_artifact_evidence_execution_row_id") or ""))
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more evidence handoff rows failed branch-local boundary checks")
            break
        if row.get("implementation_handoff_evidence_status") != "PRESERVED_NONCANDIDATE_REPAIR_IMPLEMENTATION_HANDOFF_EVIDENCE":
            issues.append("one or more evidence handoff rows lacks preservation status")
            break

    control_input_ids: set[str] = set()
    control_count = 0
    control_pass_count = 0
    for row in iter_jsonl(CONTROL_LEDGER):
        control_count += 1
        control_input_ids.add(str(row.get("input_repair_final_artifact_execution_control_row_id") or ""))
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more handoff control rows failed branch-local boundary checks")
            break
        if row.get("control_status") == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_CONTROL_PASS":
            control_pass_count += 1
        else:
            issues.append("one or more handoff controls did not pass")
            break
        if row.get("implementation_handoff_matches_execution") is not True:
            issues.append("handoff controls must prove execution match")
            break
        if row.get("noncandidate_scope_leakage_count") != 0:
            issues.append("handoff controls must report zero leakage")
            break
        if not row.get("implementation_handoff_acceptance_sha256"):
            issues.append("handoff controls must carry acceptance hash")
            break

    aggregates = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if handoff_count != 1734 or handoff_ready_count != 1734:
        issues.append("handoff count mismatch")
    if handoff_input_ids != input_artifact_execution_ids:
        issues.append("handoff rows do not consume every final artifact execution row")
    if evidence_count != 44386:
        issues.append("evidence handoff count mismatch")
    if evidence_input_ids != input_evidence_execution_ids:
        issues.append("evidence rows do not consume every final artifact evidence execution row")
    if control_count != 1734 or control_pass_count != 1734:
        issues.append("handoff control count mismatch")
    if control_input_ids != input_control_execution_ids:
        issues.append("handoff controls do not consume every final artifact execution control row")
    if counts.get("implementation_handoff_rows") != handoff_count:
        issues.append("result handoff count mismatch")
    if counts.get("ready_implementation_handoff_rows") != handoff_ready_count:
        issues.append("result ready handoff count mismatch")
    if counts.get("evidence_rows") != evidence_count:
        issues.append("result evidence count mismatch")
    if counts.get("control_rows") != control_count or counts.get("control_pass_rows") != control_pass_count:
        issues.append("result control count mismatch")
    if counts.get("decision_counts") != dict(sorted(decision_counts.items())):
        issues.append("decision count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate count mismatch")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if any(not boundary_ok(row) for row in aggregates + issue_rows + system_rows + [result]):
        issues.append("one or more non-row outputs failed branch-local boundary checks")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    print(
        json.dumps(
            {
                "ok": not issues,
                "issues": issues,
                "counts": {
                    "handoff_rows": handoff_count,
                    "evidence_rows": evidence_count,
                    "control_rows": control_count,
                    "aggregate_rows": len(aggregates),
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
