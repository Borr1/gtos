#!/usr/bin/env python3
"""Verify NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_REBUILD artifacts."""

from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
LANE_PREFIX = "research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/"

EXPECTED_DECISIONS = {
    "ACCEPT_PRIOR_CATEGORICAL_LABEL": 52,
    "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 173,
    "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 8,
    "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
    "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
}
EXPECTED_ACCEPTED_LABELS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_BLOCKER_CODES = {
    "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE": 4,
    "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP": 1,
    "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED": 1,
    "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3,
}

JSON_ARTIFACTS = [
    f"NOFILL_CAT_V2_REBUILD_CONTRACT_{DATE}.json",
    f"NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_{DATE}.json",
    f"NOFILL_CAT_V2_ACCEPTED_PACKET_{DATE}.json",
    f"NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.json",
    f"NOFILL_CAT_V2_REJECT_LEDGER_{DATE}.json",
    f"NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json",
    f"NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json",
    f"NOFILL_CAT_V2_COMPLETION_AUDIT_{DATE}.json",
]

JSONL_ARTIFACTS = [
    f"NOFILL_CAT_V2_ROW_DECISION_LEDGER_{DATE}.jsonl",
]

MD_ARTIFACTS = [
    f"NOFILL_CAT_V2_CONTEXT_ANCHOR_{DATE}.md",
    f"NOFILL_CAT_V2_REBUILD_CONTRACT_{DATE}.md",
    f"NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_{DATE}.md",
    f"NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.md",
    f"NOFILL_CAT_V2_REJECT_LEDGER_{DATE}.md",
    f"NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
    f"NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.md",
    f"NOFILL_CAT_V2_LEARNING_LEDGER_{DATE}.md",
    f"NOFILL_CAT_V2_G12_NEXT_PROMPT_PACK_{DATE}.md",
    f"NOFILL_CAT_V2_COMPLETION_AUDIT_{DATE}.md",
]

PY_FILES = [
    "build_nofill_lifecycle_categorical_result_packet_v2_rebuild_2026_05_09.py",
    "verify_nofill_lifecycle_categorical_result_packet_v2_rebuild_2026_05_09.py",
    "test_nofill_lifecycle_categorical_result_packet_v2_rebuild_2026_05_09.py",
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
    "scripts/canary",
    "scripts/fn_smoke_trade",
    "scripts/mt5",
    "run_agent.py",
)

FORBIDDEN_OUTPUT_KEY_PARTS = (
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
    "profit",
    "r_multiple",
    "reward_r",
    "synthetic_r",
    "win_rate",
)


def load_json(name: str) -> dict[str, Any]:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (OUT_DIR / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def counter(items: list[Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in items:
        key = str(item)
        out[key] = out.get(key, 0) + 1
    return out


def scan_forbidden_keys(payload: Any, path: str = "") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_l = str(key).lower()
            if any(part in key_l for part in FORBIDDEN_OUTPUT_KEY_PARTS):
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


def markdown_promotion() -> dict[str, Any]:
    missing = []
    for name in MD_ARTIFACTS:
        path = OUT_DIR / name
        if path.exists() and PROMOTION_VERDICT not in path.read_text(encoding="utf-8"):
            missing.append(name)
    return {"status": "PASS" if not missing else "FAIL", "missing_promotion_verdict": missing}


def flags(payloads: dict[str, Any]) -> dict[str, Any]:
    issues = []
    for name, payload in payloads.items():
        if isinstance(payload, dict):
            if payload.get("promotion_verdict") != PROMOTION_VERDICT:
                issues.append(f"{name}: promotion_verdict")
            if payload.get("validation_safe") is not False:
                issues.append(f"{name}: validation_safe")
            if payload.get("outcome_review_opened") is not False:
                issues.append(f"{name}: outcome_review_opened")
            if payload.get("live_effect") is not False:
                issues.append(f"{name}: live_effect")
        if isinstance(payload, list):
            for row in payload:
                if row.get("promotion_verdict") != PROMOTION_VERDICT:
                    issues.append(f"{name}:{row.get('packet_row_id')}: promotion_verdict")
                if row.get("validation_safe") is not False:
                    issues.append(f"{name}:{row.get('packet_row_id')}: validation_safe")
                if row.get("outcome_review_opened") is not False:
                    issues.append(f"{name}:{row.get('packet_row_id')}: outcome_review_opened")
                if row.get("live_effect") is not False:
                    issues.append(f"{name}:{row.get('packet_row_id')}: live_effect")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def counts_and_overlap(payloads: dict[str, Any]) -> dict[str, Any]:
    issues = []
    all_rows = payloads[f"NOFILL_CAT_V2_ROW_DECISION_LEDGER_{DATE}.jsonl"]
    accepted = payloads[f"NOFILL_CAT_V2_ACCEPTED_PACKET_{DATE}.json"]["rows"]
    blockers = payloads[f"NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.json"]["rows"]
    rejects = payloads[f"NOFILL_CAT_V2_REJECT_LEDGER_{DATE}.json"]["rows"]
    universe = payloads[f"NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_{DATE}.json"]

    if len(all_rows) != 298:
        issues.append(f"row_decision_count={len(all_rows)}")
    if len(accepted) != 225:
        issues.append(f"accepted_count={len(accepted)}")
    if len(blockers) != 8:
        issues.append(f"blocked_count={len(blockers)}")
    if len(rejects) != 65:
        issues.append(f"reject_count={len(rejects)}")
    if universe["status"] != "PASS":
        issues.append("universe status not PASS")
    if universe["decision_counts"] != EXPECTED_DECISIONS:
        issues.append({"decision_counts": universe["decision_counts"]})
    if universe["accepted_decision_counts"] != {
        "ACCEPT_PRIOR_CATEGORICAL_LABEL": 52,
        "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 173,
    }:
        issues.append({"accepted_decision_counts": universe["accepted_decision_counts"]})
    accepted_ids = {row["packet_row_id"] for row in accepted}
    blocker_ids = {row["packet_row_id"] for row in blockers}
    reject_ids = {row["packet_row_id"] for row in rejects}
    if accepted_ids & blocker_ids:
        issues.append({"accepted_blocked_overlap": sorted(accepted_ids & blocker_ids)})
    if accepted_ids & reject_ids:
        issues.append({"accepted_reject_overlap": sorted(accepted_ids & reject_ids)})
    if blocker_ids & reject_ids:
        issues.append({"blocked_reject_overlap": sorted(blocker_ids & reject_ids)})
    if len(accepted_ids | blocker_ids | reject_ids) != 298:
        issues.append("partition ids do not cover 298 unique rows")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def label_and_blocker_rules(payloads: dict[str, Any]) -> dict[str, Any]:
    issues = []
    accepted = payloads[f"NOFILL_CAT_V2_ACCEPTED_PACKET_{DATE}.json"]["rows"]
    blockers = payloads[f"NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.json"]["rows"]
    rejects = payloads[f"NOFILL_CAT_V2_REJECT_LEDGER_{DATE}.json"]["rows"]
    accepted_packet = payloads[f"NOFILL_CAT_V2_ACCEPTED_PACKET_{DATE}.json"]
    blocker_ledger = payloads[f"NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.json"]
    if accepted_packet["accepted_label_counts"] != EXPECTED_ACCEPTED_LABELS:
        issues.append({"accepted_label_counts": accepted_packet["accepted_label_counts"]})
    if any(row.get("categorical_input_label") is None for row in accepted):
        issues.append("accepted row missing categorical_input_label")
    if any(row.get("in_accepted_packet_denominator") is not True for row in accepted):
        issues.append("accepted row not in denominator")
    if any(row.get("categorical_input_label") is not None or row.get("categorical_lifecycle_label") is not None for row in blockers):
        issues.append("blocker row has label")
    if any(row.get("categorical_input_label") is not None or row.get("categorical_lifecycle_label") is not None for row in rejects):
        issues.append("reject row has label")
    if any(row.get("in_accepted_packet_denominator") for row in blockers + rejects):
        issues.append("blocker/reject row counted in denominator")
    if blocker_ledger["blocker_code_counts"] != EXPECTED_BLOCKER_CODES:
        issues.append({"blocker_code_counts": blocker_ledger["blocker_code_counts"]})
    if blocker_ledger["blocker_summary"] != {
        "original_oti2_source_gap_rows": 1,
        "oti3_same_tick_order_ambiguities": 4,
        "oti4_may3_source_gaps": 3,
    }:
        issues.append({"blocker_summary": blocker_ledger["blocker_summary"]})
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def source_duplicate_completion(payloads: dict[str, Any]) -> dict[str, Any]:
    issues = []
    source = payloads[f"NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json"]
    duplicate = payloads[f"NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json"]
    completion = payloads[f"NOFILL_CAT_V2_COMPLETION_AUDIT_{DATE}.json"]
    if source["status"] != "PASS":
        issues.append("source audit not PASS")
    if source["missing_control_inputs"]:
        issues.append("missing control inputs")
    if source["forbidden_generated_key_hits"]:
        issues.append({"forbidden_generated_key_hits": source["forbidden_generated_key_hits"][:5]})
    if source["inherited_g12_source_hash_record_count"] != 174:
        issues.append("inherited G12 source hash record count != 174")
    if len(source["oti3_same_timestamp_red_team_checks"]) != 4:
        issues.append("OTI3 same timestamp check count != 4")
    if len(source["oti4_may3_source_gap_red_team_checks"]) != 3:
        issues.append("OTI4 May3 source gap check count != 3")
    if duplicate["status"] != "PASS":
        issues.append("duplicate audit not PASS")
    if duplicate["accepted_rows"] != 225 or duplicate["accepted_unique_nofill_duplicate_keys"] != 182:
        issues.append("duplicate accepted row/key counts mismatch")
    if duplicate["rejected_noncanonical_duplicate_rows"] != 39:
        issues.append("noncanonical duplicate reject count mismatch")
    if duplicate["sample_floor_status"] != "NOT_A_VALIDATION_OR_PROMOTION_LANE_NO_SAMPLE_FLOOR_CLAIM":
        issues.append("sample floor status mismatch")
    if completion["completion_status"] != "PASS" or completion["can_mark_goal_complete"] is not True:
        issues.append("completion audit not PASS")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def forbidden_generated_keys(payloads: dict[str, Any]) -> dict[str, Any]:
    hits = []
    for name, payload in payloads.items():
        for hit in scan_forbidden_keys(payload):
            hits.append({"artifact": name, **hit})
    return {"status": "PASS" if not hits else "FAIL", "hits": hits[:50], "hit_count": len(hits)}


def py_compile_check() -> dict[str, Any]:
    results = []
    for name in PY_FILES:
        try:
            py_compile.compile(str(OUT_DIR / name), doraise=True)
            results.append({"path": name, "status": "PASS"})
        except Exception as exc:
            results.append({"path": name, "status": "FAIL", "error": str(exc)})
    return {"status": "PASS" if all(row["status"] == "PASS" for row in results) else "FAIL", "results": results}


def live_surface_check() -> dict[str, Any]:
    status_result = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True)
    workspace_dirty_paths = []
    for line in status_result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].replace("\\", "/")
        workspace_dirty_paths.append(path)

    commit_result = subprocess.run(
        ["git", "log", "--format=%H", "-n", "1", "--", LANE_PREFIX],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    lane_commit = commit_result.stdout.strip()
    committed_paths: list[str] = []
    diff_returncode = 1
    if lane_commit:
        diff_result = subprocess.run(
            ["git", "diff", "--name-only", f"{lane_commit}^1", lane_commit, "--", LANE_PREFIX],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )
        diff_returncode = diff_result.returncode
        committed_paths = [line.strip().replace("\\", "/") for line in diff_result.stdout.splitlines() if line.strip()]

    disallowed = [
        path
        for path in committed_paths
        if not path.startswith(ALLOWED_DIRTY_PREFIXES)
    ]
    live_surface = [path for path in committed_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    git_ok = status_result.returncode == 0 and commit_result.returncode == 0 and bool(lane_commit) and diff_returncode == 0
    return {
        "status": "PASS" if git_ok and not disallowed and not live_surface else "FAIL",
        "check_scope": "latest_committed_lane_diff",
        "lane_commit": lane_commit,
        "changed_paths": committed_paths,
        "workspace_dirty_paths": workspace_dirty_paths,
        "disallowed_paths": disallowed,
        "live_surface_paths": live_surface,
    }


def run() -> dict[str, Any]:
    presence = artifact_presence()
    payloads, parse = parse_artifacts()
    checks = {
        "artifact_presence": presence,
        "json_jsonl_parse": parse,
        "markdown_promotion": markdown_promotion(),
    }
    if parse["status"] == "PASS":
        checks.update(
            {
                "flags": flags(payloads),
                "counts_and_overlap": counts_and_overlap(payloads),
                "label_and_blocker_rules": label_and_blocker_rules(payloads),
                "source_duplicate_completion": source_duplicate_completion(payloads),
                "forbidden_generated_keys": forbidden_generated_keys(payloads),
            }
        )
    checks["py_compile"] = py_compile_check()
    checks["live_surface_check"] = live_surface_check()
    status = "PASS" if all(check["status"] == "PASS" for check in checks.values()) else "FAIL"
    return {
        "artifact_family": "NOFILL_CAT_V2_VERIFICATION",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "verification_status": status,
        "can_mark_goal_complete": status == "PASS",
        "checks": checks,
    }


def main() -> int:
    report = run()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["verification_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
