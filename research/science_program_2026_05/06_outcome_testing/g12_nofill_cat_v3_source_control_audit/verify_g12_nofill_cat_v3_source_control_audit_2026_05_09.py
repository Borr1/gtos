from __future__ import annotations

import argparse
import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ROUTE_ID = "G12_NOFILL_CAT_V3_SOURCE_CONTROL_AUDIT"
ROOT = Path(__file__).resolve().parents[4]
LANE_DIR = Path(__file__).resolve().parent

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
EXPECTED_FAMILY_COUNTS = {
    "accepted": 225,
    "blocked": 0,
    "reject": 65,
    "source_control": 4,
    "source_impossible": 4,
}
REQUIRED_FILES = [
    f"G12_NOFILL_CAT_V3_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_CAT_V3_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_CAT_V3_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V3_SOURCE_CONTROL_ROW_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V3_SOURCE_CONTROL_ROW_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V3_SOURCE_IMPOSSIBILITY_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V3_SOURCE_IMPOSSIBILITY_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V3_REJECT_DENOMINATOR_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V3_REJECT_DENOMINATOR_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V3_LEARNING_AND_LIMITATIONS_{DATE}.md",
    f"G12_NOFILL_CAT_V3_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V3_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_{DATE}.md",
    "build_g12_nofill_cat_v3_source_control_audit_2026_05_09.py",
    "verify_g12_nofill_cat_v3_source_control_audit_2026_05_09.py",
    "test_g12_nofill_cat_v3_source_control_audit_2026_05_09.py",
]
JSON_FILES = [name for name in REQUIRED_FILES if name.endswith(".json")]
MD_FILES = [name for name in REQUIRED_FILES if name.endswith(".md")]
PY_FILES = [name for name in REQUIRED_FILES if name.endswith(".py")]

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary_fixtures/",
    "scripts/canary_test",
    "scripts/fn_smoke_trade",
    "scripts/mt5",
    "run_agent.py",
    "start_all.bat",
)
ALLOWED_WORKSPACE_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v3_source_control_audit/",
)
ALLOWED_WORKSPACE_FILES = {
    ".context/LIVE_STATE.md",
}
FORBIDDEN_KEY_PARTS = (
    "actual_r",
    "account_history",
    "broker_actual",
    "broker_deal",
    "broker_order",
    "broker_position",
    "hidden_label",
    "live_order",
    "live_trade_result",
    "mt5_account",
    "mt5_deal",
    "mt5_history",
    "mt5_order",
    "mt5_position",
    "r_multiple",
    "reward_r",
    "synthetic_r",
    "win_rate",
    "expectancy",
    "profit",
    "dsr",
    "pbo",
)
ALLOWED_FORBIDDEN_KEY_NAMES = {"outcome_review_opened", "promotion_verdict"}


def read_json(name: str) -> Any:
    return json.loads((LANE_DIR / name).read_text(encoding="utf-8"))


def git_lines(args: list[str]) -> list[str]:
    try:
        output = subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT)
    except Exception as exc:
        return [f"GIT_UNAVAILABLE:{exc!r}"]
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip() and not line.startswith("warning:")]


def git_status_paths() -> list[str]:
    try:
        output = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True, stderr=subprocess.STDOUT)
    except Exception as exc:
        return [f"GIT_STATUS_UNAVAILABLE:{exc!r}"]
    paths = []
    for line in output.splitlines():
        if not line.strip() or line.lower().startswith("warning:") or len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        paths.append(path.replace("\\", "/"))
    return paths


def allowed_workspace_path(path: str) -> bool:
    return path in ALLOWED_WORKSPACE_FILES or any(path.startswith(prefix) for prefix in ALLOWED_WORKSPACE_PREFIXES)


def scan_forbidden_keys(payload: Any, path: str = "") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_s = str(key)
            key_l = key_s.lower()
            if key_s not in ALLOWED_FORBIDDEN_KEY_NAMES and any(part in key_l for part in FORBIDDEN_KEY_PARTS):
                hits.append({"path": f"{path}.{key_s}" if path else key_s, "key": key_s})
            hits.extend(scan_forbidden_keys(value, f"{path}.{key_s}" if path else key_s))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            hits.extend(scan_forbidden_keys(item, f"{path}[{index}]"))
    return hits


def command_result(args: list[str], *, timeout: int = 180) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        env=env,
    )
    return {
        "args": args,
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "output_tail": (proc.stdout or "")[-4000:],
    }


def verify(*, run_external: bool = True) -> dict[str, Any]:
    issues: list[str] = []
    missing = [name for name in REQUIRED_FILES if not (LANE_DIR / name).exists()]
    if missing:
        issues.append(f"missing required files: {missing}")
        return {"ok": False, "can_mark_goal_complete": False, "issues": issues}

    payloads = {name: read_json(name) for name in JSON_FILES}
    markdown_missing_posture = [
        name for name in MD_FILES if PROMOTION_VERDICT not in (LANE_DIR / name).read_text(encoding="utf-8")
    ]
    if markdown_missing_posture:
        issues.append(f"markdown files missing NO_PROMOTION_VERDICT: {markdown_missing_posture}")

    for name, payload in payloads.items():
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append(f"{name}: promotion posture mismatch")
        if payload.get("validation_safe") is not False:
            issues.append(f"{name}: validation_safe not false")
        if payload.get("outcome_review_opened") is not False:
            issues.append(f"{name}: outcome_review_opened not false")
        if payload.get("live_effect") is not False:
            issues.append(f"{name}: live_effect not false")
        if payload.get("status") not in {None, "PASS"}:
            issues.append(f"{name}: status {payload.get('status')}")

    universe = payloads[f"G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_{DATE}.json"]
    source_control = payloads[f"G12_NOFILL_CAT_V3_SOURCE_CONTROL_ROW_AUDIT_{DATE}.json"]
    source_impossible = payloads[f"G12_NOFILL_CAT_V3_SOURCE_IMPOSSIBILITY_AUDIT_{DATE}.json"]
    rejects = payloads[f"G12_NOFILL_CAT_V3_REJECT_DENOMINATOR_AUDIT_{DATE}.json"]
    hashes = payloads[f"G12_NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json"]
    duplicates = payloads[f"G12_NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json"]
    decision = payloads[f"G12_NOFILL_CAT_V3_DECISION_LEDGER_{DATE}.json"]
    completion = payloads[f"G12_NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.json"]

    if universe["row_count"] != 298 or universe["unique_packet_row_ids"] != 298:
        issues.append("universe row identity count mismatch")
    if universe["terminal_family_counts"] != EXPECTED_FAMILY_COUNTS:
        issues.append("terminal family counts mismatch")
    if universe["accepted_row_field_mismatch_count"] != 0:
        issues.append("accepted row field mismatch")
    expected_targets = MAY3_ROWS | {XAU_ROW} | USDJPY_ROWS
    if set(universe["target_row_states"]) != expected_targets:
        issues.append("target row identity set mismatch")
    for row_id in MAY3_ROWS:
        row = universe["target_row_states"][row_id]
        if row["v3_terminal_state"] != "SOURCE_CONTROL_MARKET_SESSION_EMPTY":
            issues.append(f"{row_id}: May3 state mismatch")
        if row["in_accepted_packet_denominator"] or row["categorical_lifecycle_label"] is not None:
            issues.append(f"{row_id}: May3 denominator/label violation")
    xau = universe["target_row_states"][XAU_ROW]
    if xau["v3_terminal_state"] != "SOURCE_CONTROL_INPUT_ONLY_NO_ENTRY_THROUGH_CANCEL":
        issues.append("0241 state mismatch")
    if xau["in_accepted_packet_denominator"] or xau["categorical_lifecycle_label"] is not None:
        issues.append("0241 denominator/label violation")
    for row_id in USDJPY_ROWS:
        row = universe["target_row_states"][row_id]
        if row["v3_terminal_state"] != "SOURCE_IMPOSSIBLE_EXACT_ORDERING":
            issues.append(f"{row_id}: USDJPY state mismatch")
        if row["in_accepted_packet_denominator"] or row["categorical_lifecycle_label"] is not None:
            issues.append(f"{row_id}: USDJPY denominator/label violation")

    source_control_ids = {row["packet_row_id"] for row in source_control["row_audits"]}
    if source_control_ids != MAY3_ROWS | {XAU_ROW}:
        issues.append("source-control row audit identity mismatch")
    if not all(row["accepted"] for row in source_control["row_audits"]):
        issues.append("source-control row audit not accepted")
    if not all(row["v3_denominator"] is False for row in source_control["row_audits"]):
        issues.append("source-control denominator violation")

    source_impossible_ids = {row["packet_row_id"] for row in source_impossible["row_audits"]}
    if source_impossible_ids != USDJPY_ROWS:
        issues.append("source-impossible row audit identity mismatch")
    if not all(row["same_tick_impossibility_holds"] for row in source_impossible["row_audits"]):
        issues.append("source-impossible exact-row check failed")
    if source_impossible["source_search"]["source_sequence_route_found"] is not False:
        issues.append("source sequence route unexpectedly found")

    if rejects["rejected_row_count"] != 65 or not rejects["reject_rows_outside_labels_denominators"]:
        issues.append("reject boundary failed")
    if hashes["strict_failure_count"] != 0 or hashes["missing_record_count"] != 0:
        issues.append("source hash strict failure or missing record")
    if hashes["noleak_checks"]["forbidden_output_key_hit_count"] != 0:
        issues.append("upstream V3 forbidden output key hit")
    if any(value for key, value in hashes["noleak_checks"].items() if key.endswith("_true_count")):
        issues.append("unsafe flag true in no-leak audit")
    if duplicates["accepted_denominator_row_count"] != 225:
        issues.append("duplicate audit accepted denominator count mismatch")
    if any(duplicates["nonaccepted_denominator_violations"].values()):
        issues.append("nonaccepted denominator violation")
    if duplicates["sample_floor_policy"]["scored_sample_floor_opened"] is not False:
        issues.append("sample floor unexpectedly opened")

    if decision["overall_decision"] != "ACCEPT_V3_AS_SOURCE_CONTROL_CATEGORICAL_INPUT_EVIDENCE_ONLY":
        issues.append("decision ledger overall decision mismatch")
    if completion["can_mark_goal_complete"] is not True or completion["missing_incomplete_or_weak_requirements"]:
        issues.append("completion audit not complete")

    forbidden_json_key_hits = []
    for name, payload in payloads.items():
        forbidden_json_key_hits.extend({"artifact": name, **hit} for hit in scan_forbidden_keys(payload))
    if forbidden_json_key_hits:
        issues.append(f"forbidden JSON output keys found: {forbidden_json_key_hits[:20]}")

    status_paths = git_status_paths()
    unallowed_workspace = [path for path in status_paths if not allowed_workspace_path(path)]
    forbidden_workspace = [path for path in status_paths if any(path.startswith(prefix) for prefix in FORBIDDEN_LIVE_PREFIXES)]
    head_paths = git_lines(["git", "show", "--pretty=", "--name-only", "--diff-filter=ACMRT", "HEAD"])
    if not head_paths:
        head_paths = git_lines(["git", "diff", "--name-only", "--diff-filter=ACMRT", "HEAD^1", "HEAD"])
    forbidden_head = [path for path in head_paths if any(path.startswith(prefix) for prefix in FORBIDDEN_LIVE_PREFIXES)]
    if forbidden_head:
        issues.append(f"forbidden live-surface HEAD paths: {forbidden_head}")

    py_compile_errors = []
    for name in PY_FILES:
        try:
            py_compile.compile(str(LANE_DIR / name), doraise=True)
        except Exception as exc:
            py_compile_errors.append({"path": name, "error": str(exc)})
    if py_compile_errors:
        issues.append(f"py_compile errors: {py_compile_errors}")

    external = {"enabled": run_external, "ok": True}
    if run_external:
        pytest = command_result(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-q",
                str(LANE_DIR / f"test_g12_nofill_cat_v3_source_control_audit_2026_05_09.py"),
                "--basetemp",
                str(ROOT / ".pytest_tmp_g12_nofill_cat_v3_audit"),
            ],
            timeout=180,
        )
        external = {"enabled": True, "focused_pytest": pytest, "ok": pytest["ok"]}
        if not pytest["ok"]:
            issues.append("focused pytest failed")

    ok = not issues
    return {
        "ok": ok,
        "can_mark_goal_complete": ok,
        "issues": issues,
        "checks": {
            "required_files_count": len(REQUIRED_FILES),
            "json_files_count": len(JSON_FILES),
            "markdown_posture_missing": markdown_missing_posture,
            "universe": {
                "row_count": universe["row_count"],
                "terminal_family_counts": universe["terminal_family_counts"],
                "accepted_row_field_mismatch_count": universe["accepted_row_field_mismatch_count"],
            },
            "source_control_rows": sorted(source_control_ids),
            "source_impossible_rows": sorted(source_impossible_ids),
            "reject_count": rejects["rejected_row_count"],
            "source_hash": {
                "source_hash_record_count": hashes["source_hash_record_count"],
                "strict_failure_count": hashes["strict_failure_count"],
                "missing_record_count": hashes["missing_record_count"],
                "mutable_context_mismatch_count": hashes["mutable_context_mismatch_count"],
                "line_ending_only_mismatch_count": hashes["line_ending_only_mismatch_count"],
            },
            "git_scope": {
                "workspace_paths_informational_only": status_paths,
                "unallowed_workspace_paths_informational_only": unallowed_workspace,
                "forbidden_workspace_paths_informational_only": forbidden_workspace,
                "head_paths": head_paths,
                "forbidden_head_paths": forbidden_head,
            },
            "py_compile_errors": py_compile_errors,
            "external": external,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-external", action="store_true")
    args = parser.parse_args()
    result = verify(run_external=not args.skip_external)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
