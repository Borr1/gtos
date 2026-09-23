#!/usr/bin/env python3
"""Verify NOFILL_CAT_V3_SOURCE_CONTROL_REBUILD artifacts."""

from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
LANE_PREFIX = "research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_source_control_rebuild/"

EXPECTED_FAMILY_COUNTS = {
    "accepted": 225,
    "source_control": 4,
    "source_impossible": 4,
    "blocked": 0,
    "reject": 65,
}
MAY3_ROWS = {
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
}
XAU_ROW = "NOFILL-CAT-ROW-0241"
USDJPY_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}
TARGET_ROWS = MAY3_ROWS | {XAU_ROW} | USDJPY_ROWS

JSON_ARTIFACTS = [
    f"NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_{DATE}.json",
    f"NOFILL_CAT_V3_ACCEPTED_OR_SOURCE_CONTROL_PACKET_{DATE}.json",
    f"NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_{DATE}.json",
    f"NOFILL_CAT_V3_REJECT_LEDGER_{DATE}.json",
    f"NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json",
    f"NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json",
    f"NOFILL_CAT_V3_SOURCE_ROOT_SEARCH_LEDGER_{DATE}.json",
    f"NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.json",
]
JSONL_ARTIFACTS = [
    f"NOFILL_CAT_V3_ROW_DECISION_LEDGER_{DATE}.jsonl",
]
MD_ARTIFACTS = [
    f"NOFILL_CAT_V3_CONTEXT_ANCHOR_{DATE}.md",
    f"NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_{DATE}.md",
    f"NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_{DATE}.md",
    f"NOFILL_CAT_V3_REJECT_LEDGER_{DATE}.md",
    f"NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
    f"NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.md",
    f"NOFILL_CAT_V3_SOURCE_ROOT_SEARCH_LEDGER_{DATE}.md",
    f"NOFILL_CAT_V3_LEARNING_AND_LIMITATIONS_{DATE}.md",
    f"NOFILL_CAT_V3_G12_NEXT_PROMPT_PACK_{DATE}.md",
    f"NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.md",
]
PY_FILES = [
    "build_nofill_cat_v3_source_control_rebuild_2026_05_09.py",
    "verify_nofill_cat_v3_source_control_rebuild_2026_05_09.py",
    "test_nofill_cat_v3_source_control_rebuild_2026_05_09.py",
]

ALLOWED_DIRTY_PREFIXES = (
    LANE_PREFIX,
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
)
FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "run_agent.py",
    "scripts/canary",
    "scripts/fn_smoke_trade",
    "scripts/mt5",
)
FORBIDDEN_KEY_PARTS = (
    "actual_r",
    "account_history",
    "broker_actual",
    "broker_deal",
    "broker_order",
    "broker_position",
    "dsr",
    "expectancy",
    "hidden_label",
    "live_order",
    "live_trade_result",
    "mt5_account",
    "mt5_deal",
    "mt5_history",
    "mt5_order",
    "mt5_position",
    "pbo",
    "performance",
    "profit",
    "r_multiple",
    "result",
    "reward_r",
    "synthetic_r",
    "win_rate",
)


def load_json(name: str) -> dict[str, Any]:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (OUT_DIR / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def scan_forbidden_keys(payload: Any, path: str = "") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_l = str(key).lower()
            if key not in {"outcome_review_opened", "promotion_verdict"} and any(part in key_l for part in FORBIDDEN_KEY_PARTS):
                hits.append({"path": f"{path}.{key}" if path else str(key), "key": str(key)})
            hits.extend(scan_forbidden_keys(value, f"{path}.{key}" if path else str(key)))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            hits.extend(scan_forbidden_keys(item, f"{path}[{index}]"))
    return hits


def artifact_presence() -> dict[str, Any]:
    expected = JSON_ARTIFACTS + JSONL_ARTIFACTS + MD_ARTIFACTS + PY_FILES
    missing = [name for name in expected if not (OUT_DIR / name).exists()]
    return {"status": "PASS" if not missing else "FAIL", "expected_count": len(expected), "missing": missing}


def parse_artifacts() -> tuple[dict[str, Any], dict[str, Any]]:
    payloads: dict[str, Any] = {}
    errors = []
    for name in JSON_ARTIFACTS:
        try:
            payloads[name] = load_json(name)
        except Exception as exc:
            errors.append({"path": name, "error": str(exc)})
    for name in JSONL_ARTIFACTS:
        try:
            payloads[name] = load_jsonl(name)
        except Exception as exc:
            errors.append({"path": name, "error": str(exc)})
    return payloads, {"status": "PASS" if not errors else "FAIL", "errors": errors}


def markdown_posture() -> dict[str, Any]:
    missing = []
    for name in MD_ARTIFACTS:
        path = OUT_DIR / name
        if path.exists() and PROMOTION_VERDICT not in path.read_text(encoding="utf-8"):
            missing.append(name)
    return {"status": "PASS" if not missing else "FAIL", "missing_no_promotion_verdict": missing}


def flag_check(payloads: dict[str, Any]) -> dict[str, Any]:
    issues = []
    for name, payload in payloads.items():
        candidates = payload if isinstance(payload, list) else [payload]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            row_id = candidate.get("packet_row_id", "artifact")
            if candidate.get("promotion_verdict") != PROMOTION_VERDICT:
                issues.append(f"{name}:{row_id}:promotion_verdict")
            if candidate.get("validation_safe") is not False:
                issues.append(f"{name}:{row_id}:validation_safe")
            if candidate.get("outcome_review_opened") is not False:
                issues.append(f"{name}:{row_id}:outcome_review_opened")
            if candidate.get("live_effect") is not False:
                issues.append(f"{name}:{row_id}:live_effect")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def counts_and_targets(payloads: dict[str, Any]) -> dict[str, Any]:
    issues = []
    rows = payloads[f"NOFILL_CAT_V3_ROW_DECISION_LEDGER_{DATE}.jsonl"]
    universe = payloads[f"NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_{DATE}.json"]
    packet = payloads[f"NOFILL_CAT_V3_ACCEPTED_OR_SOURCE_CONTROL_PACKET_{DATE}.json"]
    blockers = payloads[f"NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_{DATE}.json"]
    rejects = payloads[f"NOFILL_CAT_V3_REJECT_LEDGER_{DATE}.json"]

    ids = [row["packet_row_id"] for row in rows]
    family_counter = Counter(row["v3_terminal_family"] for row in rows)
    family_counts = {key: family_counter.get(key, 0) for key in EXPECTED_FAMILY_COUNTS}
    row_by_id = {row["packet_row_id"]: row for row in rows}
    if len(rows) != 298:
        issues.append(f"row_count={len(rows)}")
    if len(ids) != len(set(ids)):
        issues.append("duplicate_packet_row_id")
    if family_counts != EXPECTED_FAMILY_COUNTS:
        issues.append(f"family_counts={family_counts}")
    if universe["v3_reconciliation"]["terminal_family_counts"] != EXPECTED_FAMILY_COUNTS:
        issues.append("universe_family_counts")
    if packet["accepted_denominator_row_count"] != 225:
        issues.append("packet_accepted_denominator_count")
    if packet["source_control_non_denominator_row_count"] != 4:
        issues.append("packet_source_control_count")
    if blockers["unresolved_blocker_count"] != 0 or blockers["source_impossible_count"] != 4:
        issues.append("blocker_impossibility_counts")
    if rejects["rejected_row_count"] != 65:
        issues.append("reject_count")
    if set(row_by_id) & TARGET_ROWS != TARGET_ROWS:
        issues.append("missing_target_rows")

    for row_id in MAY3_ROWS:
        row = row_by_id[row_id]
        if row["v3_terminal_state"] != "SOURCE_CONTROL_MARKET_SESSION_EMPTY":
            issues.append(f"{row_id}:may3_state")
        if row["in_accepted_packet_denominator"]:
            issues.append(f"{row_id}:denominator")
    row = row_by_id[XAU_ROW]
    if row["v3_terminal_state"] != "SOURCE_CONTROL_INPUT_ONLY_NO_ENTRY_THROUGH_CANCEL":
        issues.append("0241_state")
    if row["in_accepted_packet_denominator"]:
        issues.append("0241_denominator")
    for row_id in USDJPY_ROWS:
        row = row_by_id[row_id]
        if row["v3_terminal_state"] != "SOURCE_IMPOSSIBLE_EXACT_ORDERING":
            issues.append(f"{row_id}:impossible_state")
        if row["in_accepted_packet_denominator"]:
            issues.append(f"{row_id}:denominator")
        if not row["exact_next_source_needed"]:
            issues.append(f"{row_id}:missing_exact_next_source")
    for row in rows:
        if row["v3_terminal_family"] in {"source_control", "source_impossible", "reject", "blocked"}:
            if row["categorical_lifecycle_label"] is not None or row["lifecycle_label_assigned"]:
                issues.append(f"{row['packet_row_id']}:nonaccepted_label")
            if row["in_accepted_packet_denominator"]:
                issues.append(f"{row['packet_row_id']}:nonaccepted_denominator")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def no_forbidden_keys(payloads: dict[str, Any]) -> dict[str, Any]:
    hits = []
    for name, payload in payloads.items():
        hits.extend({"artifact": name, **hit} for hit in scan_forbidden_keys(payload))
    return {"status": "PASS" if not hits else "FAIL", "hits": hits[:50], "hit_count": len(hits)}


def source_hash_and_search(payloads: dict[str, Any]) -> dict[str, Any]:
    issues = []
    hash_audit = payloads[f"NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json"]
    search = payloads[f"NOFILL_CAT_V3_SOURCE_ROOT_SEARCH_LEDGER_{DATE}.json"]
    duplicate = payloads[f"NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json"]
    completion = payloads[f"NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.json"]
    if hash_audit["status"] != "PASS":
        issues.append("hash_audit_not_pass")
    if hash_audit["missing_artifact_records"]:
        issues.append("missing_artifact_records")
    if search["source_sequence_route_found"] is not False:
        issues.append("source_sequence_route_found_not_false")
    if duplicate["status"] != "PASS":
        issues.append("duplicate_audit_not_pass")
    if completion["can_mark_goal_complete"] is not True:
        issues.append("completion_audit_not_complete")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def py_compile_check() -> dict[str, Any]:
    errors = []
    for name in PY_FILES:
        try:
            py_compile.compile(str(OUT_DIR / name), doraise=True)
        except Exception as exc:
            errors.append({"path": name, "error": str(exc)})
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def git_diff_check() -> dict[str, Any]:
    try:
        status = subprocess.check_output(["git", "status", "--short"], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT)
    except Exception as exc:
        return {"status": "WARN", "error": str(exc), "dirty_paths_informational_only": []}

    dirty_paths = []
    forbidden_workspace = []
    for line in status.splitlines():
        if not line.strip() or line.startswith("warning:"):
            continue
        path = line[3:].replace("\\", "/")
        dirty_paths.append(path)
        if any(path.startswith(prefix) for prefix in FORBIDDEN_LIVE_PREFIXES):
            forbidden_workspace.append(path)

    try:
        committed_raw = subprocess.check_output(
            ["git", "diff", "--name-only", "--diff-filter=ACMRT", "HEAD^1", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        )
        committed_paths = [line.replace("\\", "/") for line in committed_raw.splitlines() if line.strip()]
    except Exception:
        committed_raw = subprocess.check_output(
            ["git", "show", "--pretty=", "--name-only", "--diff-filter=ACMRT", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        )
        committed_paths = [line.replace("\\", "/") for line in committed_raw.splitlines() if line.strip()]

    forbidden_committed = [
        path for path in committed_paths
        if any(path.startswith(prefix) for prefix in FORBIDDEN_LIVE_PREFIXES)
    ]
    return {
        "status": "PASS" if not forbidden_committed else "FAIL",
        "committed_diff_paths": committed_paths,
        "forbidden_committed_live_surface_paths": forbidden_committed,
        "dirty_paths_informational_only": dirty_paths,
        "forbidden_workspace_paths_informational_only": forbidden_workspace,
    }


def main() -> int:
    presence = artifact_presence()
    payloads, parse = parse_artifacts()
    checks = {
        "artifact_presence": presence,
        "parse_artifacts": parse,
        "markdown_posture": markdown_posture(),
    }
    if parse["status"] == "PASS":
        checks.update(
            {
                "flags": flag_check(payloads),
                "counts_and_targets": counts_and_targets(payloads),
                "no_forbidden_output_keys": no_forbidden_keys(payloads),
                "source_hash_and_search": source_hash_and_search(payloads),
            }
        )
    checks["py_compile"] = py_compile_check()
    checks["git_diff"] = git_diff_check()
    ok = all(check.get("status") == "PASS" for check in checks.values())
    result = {
        "ok": ok,
        "can_mark_goal_complete": ok,
        "checks": checks,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
