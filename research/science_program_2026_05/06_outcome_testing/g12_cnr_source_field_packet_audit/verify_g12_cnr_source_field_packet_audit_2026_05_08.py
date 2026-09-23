#!/usr/bin/env python
"""Verifier for the G12 CNR source-field packet audit artifacts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


LANE_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
DATE = "2026-05-08"

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ACCEPT = "ACCEPT_INPUT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT_ONLY"
BLOCK = "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENT"
REJECT = "REJECT_INVALID_PACKET_CLEARING"
CONTEXT_ONLY = "CONTEXT_ONLY_NOT_RESULT_ELIGIBLE"

REQUIRED_JSON = [
    "G12_CNR_SOURCE_FIELD_PACKET_DECISION_LEDGER",
    "G12_CNR_READY_ROW_SHORTLIST",
    "G12_CNR_EXACT_BLOCKER_LEDGER",
    "G12_CNR_SOURCE_HASH_AND_ASOF_AUDIT",
    "G12_CNR_NOLEAK_AND_LABEL_AUDIT",
    "G12_CNR_DUPLICATE_SAMPLE_FLOOR_AUDIT",
    "G12_CNR_TIMING_TARGET_COVERAGE_AUDIT",
    "G12_CNR_ANTI_BOXING_LOCAL_DATA_SEARCH_LEDGER",
    "G12_CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE",
    "G12_CNR_SOURCE_FIELD_PACKET_AUDIT_COMPLETION_AUDIT",
]

REQUIRED_MD = REQUIRED_JSON + ["G12_CNR_NEXT_LANE_PROMPT_PACK"]
REQUIRED_FALSE_FLAGS = (
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "account_history_accessed",
    "broker_actual_r_accessed",
    "live_order_state_accessed",
    "live_trade_results_accessed",
    "blocked_packet_outcome_source_read",
)
REQUIRED_ZERO_FIELDS = ("mt5_order_calls", "order_calls", "paid_data_calls", "databento_calls", "api_calls", "canary_calls")

ALLOWED_DIFF_PREFIXES = {
    "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/",
}
FORBIDDEN_DIFF_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/start",
    "run_agent.py",
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-c", "core.excludesfile=", *args],
            cwd=ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except Exception as exc:
        return f"ERROR:{type(exc).__name__}:{exc}"


def verify_flags(payload: dict[str, Any], label: str, issues: list[str]) -> None:
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        issues.append(f"{label}: promotion_verdict is not {PROMOTION_VERDICT}")
    for flag in REQUIRED_FALSE_FLAGS:
        if payload.get(flag) is not False:
            issues.append(f"{label}: {flag} is not false")
    for field in REQUIRED_ZERO_FIELDS:
        if payload.get(field, 0) not in (0, None):
            issues.append(f"{label}: {field} is not zero")


def verify() -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}

    for base in REQUIRED_JSON:
        path = LANE_DIR / f"{base}_{DATE}.json"
        if not path.exists():
            issues.append(f"missing JSON artifact {path.name}")
            continue
        try:
            payload = load_json(path)
        except Exception as exc:
            issues.append(f"cannot parse {path.name}: {type(exc).__name__}: {exc}")
            continue
        payloads[base] = payload
        verify_flags(payload, path.name, issues)

    for base in REQUIRED_MD:
        path = LANE_DIR / f"{base}_{DATE}.md"
        if not path.exists():
            issues.append(f"missing MD artifact {path.name}")
            continue
        text = path.read_text(encoding="utf-8")
        if "NO_PROMOTION_VERDICT" not in text or "Validation safe: `false`" not in text or "Live effect: `false`" not in text:
            issues.append(f"{path.name}: missing visible no-promotion/false flags")

    decision = payloads.get("G12_CNR_SOURCE_FIELD_PACKET_DECISION_LEDGER", {})
    ready = payloads.get("G12_CNR_READY_ROW_SHORTLIST", {})
    blockers = payloads.get("G12_CNR_EXACT_BLOCKER_LEDGER", {})
    source_hash = payloads.get("G12_CNR_SOURCE_HASH_AND_ASOF_AUDIT", {})
    noleak = payloads.get("G12_CNR_NOLEAK_AND_LABEL_AUDIT", {})
    duplicate = payloads.get("G12_CNR_DUPLICATE_SAMPLE_FLOOR_AUDIT", {})
    coverage = payloads.get("G12_CNR_TIMING_TARGET_COVERAGE_AUDIT", {})
    anti_boxing = payloads.get("G12_CNR_ANTI_BOXING_LOCAL_DATA_SEARCH_LEDGER", {})
    completion = payloads.get("G12_CNR_SOURCE_FIELD_PACKET_AUDIT_COMPLETION_AUDIT", {})

    counts = decision.get("decision_counts", {})
    if decision.get("row_count") != 6200:
        issues.append(f"decision row_count expected 6200, got {decision.get('row_count')}")
    if counts.get(ACCEPT) != 102:
        issues.append(f"accepted ready rows expected 102, got {counts.get(ACCEPT)}")
    if counts.get(BLOCK) != 6098:
        issues.append(f"blocked rows expected 6098, got {counts.get(BLOCK)}")
    if counts.get(REJECT, 0) != 0 or counts.get(CONTEXT_ONLY, 0) != 0:
        issues.append(f"unexpected reject/context counts: reject={counts.get(REJECT)}, context={counts.get(CONTEXT_ONLY)}")

    if ready.get("ready_row_count") != 102 or len(ready.get("rows", [])) != 102:
        issues.append("ready shortlist does not contain exactly 102 rows")
    if blockers.get("blocked_row_count") != 6098 or len(blockers.get("rows", [])) != 6098:
        issues.append("blocker ledger does not contain exactly 6098 rows")
    if blockers.get("all_blocked_rows_have_exact_requirements") is not True:
        issues.append("not all blocked rows have exact source-field requirements")

    if source_hash.get("strict_hash_mismatch_count") != 0:
        issues.append(f"strict source hash mismatches present: {source_hash.get('strict_hash_mismatch_count')}")
    if source_hash.get("missing_required_count") != 0:
        issues.append(f"missing required source files present: {source_hash.get('missing_required_count')}")
    if source_hash.get("asof_status") != "PASS":
        issues.append(f"asof audit not PASS: {source_hash.get('asof_status')}")

    if noleak.get("scan_status") != "PASS":
        issues.append(f"no-leak scan not PASS: {noleak.get('scan_status')}")
    if noleak.get("label_family_boundary", {}).get("broker_actual_r_used") is not False:
        issues.append("broker_actual_r_used is not false")
    if noleak.get("label_family_boundary", {}).get("post_entry_r_used") is not False:
        issues.append("post_entry_r_used is not false")

    if duplicate.get("upstream_comparison_status") != "PASS":
        issues.append("duplicate audit does not match upstream denominator report")
    if duplicate.get("sample_floor_status") != "PACKET_AUDIT_ALLOWED_NO_VALIDATION_CLAIM":
        issues.append("sample floor status implies validation/promotion claim")

    if coverage.get("coverage_status") != "PASS":
        issues.append("timing-target coverage is not PASS")

    searched_roots = anti_boxing.get("searched_roots", [])
    if len(searched_roots) < 5:
        issues.append("anti-boxing ledger did not search enough local-heavy-data roots")
    if not any("data\\ticks" in item.get("root", "") or "data/ticks" in item.get("root", "") for item in searched_roots):
        issues.append("anti-boxing ledger did not record data/ticks search")
    if not any(item.get("skipped_result_or_quarantine_dirs", 0) >= 0 for item in searched_roots):
        issues.append("anti-boxing ledger does not record result/quarantine skip policy")

    if completion.get("status") not in {"PASS_COMPLETION_AUDIT_VERIFICATION_COMMANDS_RUN"}:
        issues.append(f"completion audit status unexpected: {completion.get('status')}")

    lane_dirs = [p.name.lower() for p in LANE_DIR.iterdir() if p.is_dir()]
    bad_dirs = [name for name in lane_dirs if "result" in name or "quarantine" in name]
    if bad_dirs:
        issues.append(f"result/quarantine-like directories exist in audit lane: {bad_dirs}")

    diff_names = [line.strip().replace("\\", "/") for line in git_output(["diff", "--name-only"]).splitlines() if line.strip() and not line.startswith("warning:")]
    staged_names = [line.strip().replace("\\", "/") for line in git_output(["diff", "--cached", "--name-only"]).splitlines() if line.strip() and not line.startswith("warning:")]
    status_names = []
    for line in git_output(["status", "--short"]).splitlines():
        if not line.strip() or line.startswith("warning:"):
            continue
        status_names.append(line[2:].strip().replace("\\", "/"))
    all_diff_names = sorted(set(diff_names + staged_names + status_names))
    forbidden_diff = [name for name in all_diff_names if name.startswith(FORBIDDEN_DIFF_PREFIXES)]
    unscoped_diff = [
        name
        for name in all_diff_names
        if name and not any(name.startswith(prefix) for prefix in ALLOWED_DIFF_PREFIXES)
    ]
    if forbidden_diff:
        issues.append(f"forbidden live-surface diff paths present: {forbidden_diff}")
    if unscoped_diff:
        warnings.append(f"unscoped non-live diff paths present and must not be committed for this lane: {unscoped_diff}")

    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "warnings": warnings,
        "decision_counts": counts,
        "ready_rows": ready.get("ready_row_count"),
        "blocked_rows": blockers.get("blocked_row_count"),
        "source_hash_dynamic_allowed_changes": source_hash.get("dynamic_hash_changed_allowed_count"),
        "diff_names": all_diff_names,
    }


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
