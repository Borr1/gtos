from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from build_g0_nofill_cat_v2_synthesis_control_route_2026_05_09 import (
    EXPECTED_ACCEPTED_SPLIT,
    EXPECTED_DUPLICATE_POSTURE,
    EXPECTED_LABEL_COUNTS,
    EXPECTED_PARTITION,
    EXPECTED_SOURCE_LANE_COUNTS,
    PROMOTION_VERDICT,
    REPO_ROOT,
    ROUTE_DIR,
    ROW_LEDGER,
    recompute_counts,
    read_jsonl,
    required_output_files,
)


ALLOWED_CHANGED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_g0_synthesis_control_route/",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)
FORBIDDEN_CHANGED_PREFIXES = (
    "src/",
    "prompts/",
    "config/agent_config.yaml",
    "config/profiles/",
    "scripts/canary",
    "scripts/canary_fixtures/",
    "run_agent.py",
)
FORBIDDEN_JSON_TRUE_FLAGS = ("validation_safe", "outcome_review_opened", "live_effect")
FORBIDDEN_DECISION_KEYS = {
    "broker_actual_r",
    "account_history",
    "live_order_label",
    "hidden_label",
    "r_multiple",
    "win_rate",
    "expectancy",
    "sharpe",
    "result_score",
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def flatten_json(obj: Any, path: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            rows.extend(flatten_json(value, child))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            rows.extend(flatten_json(value, f"{path}[{idx}]"))
    else:
        rows.append((path, obj))
    return rows


def run(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    return {
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def git_paths(args: list[str]) -> list[str]:
    proc = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        return [f"GIT_ERROR: {proc.stderr.strip()}"]
    return [line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]


def live_surface_check() -> dict[str, Any]:
    working_paths = git_paths(["diff", "--name-only", "HEAD"])
    staged_paths = git_paths(["diff", "--cached", "--name-only"])
    latest_commit_paths = git_paths(["diff", "--name-only", "HEAD~1..HEAD"])
    # On main, live monitoring may leave unrelated runtime/research dirt in the
    # workspace. Verify this lane by its committed diff while keeping workspace
    # dirt visible as informational context.
    if latest_commit_paths and not any(path.startswith("GIT_ERROR:") for path in latest_commit_paths):
        checked_paths = sorted(set(staged_paths + latest_commit_paths))
        checked_scope = "latest_committed_lane_diff"
    else:
        checked_paths = sorted(set(working_paths + staged_paths + latest_commit_paths))
        checked_scope = "workspace_and_commit_diff"
    forbidden = [
        path
        for path in checked_paths
        if any(path.startswith(prefix) for prefix in FORBIDDEN_CHANGED_PREFIXES)
        or (
            path
            and not path.startswith("GIT_ERROR:")
            and not any(path.startswith(prefix) for prefix in ALLOWED_CHANGED_PREFIXES)
        )
    ]
    return {
        "working_paths": working_paths,
        "staged_paths": staged_paths,
        "latest_commit_paths": latest_commit_paths,
        "checked_paths": checked_paths,
        "checked_scope": checked_scope,
        "workspace_paths_informational_only": checked_scope == "latest_committed_lane_diff",
        "forbidden_paths": forbidden,
        "status": "PASS" if not forbidden else "FAIL",
    }


def verify_generated_json() -> dict[str, Any]:
    json_paths = sorted(ROUTE_DIR.glob("G0_NOFILL_CAT_V2_*.json"))
    parsed = {}
    bad_flags = []
    forbidden_key_hits = []
    for path in json_paths:
        data = read_json(path)
        parsed[path.name] = True
        flat = flatten_json(data)
        for key_path, value in flat:
            leaf = key_path.split(".")[-1]
            leaf = leaf.split("[")[0]
            if leaf in FORBIDDEN_JSON_TRUE_FLAGS and value is not False:
                bad_flags.append({"file": path.name, "path": key_path, "value": value})
            normalized_leaf = leaf.lower()
            if normalized_leaf in FORBIDDEN_DECISION_KEYS:
                forbidden_key_hits.append({"file": path.name, "path": key_path})
        text = path.read_text(encoding="utf-8", errors="replace")
        if PROMOTION_VERDICT not in text:
            bad_flags.append({"file": path.name, "path": "text", "value": "missing NO_PROMOTION_VERDICT"})
    return {
        "json_files": list(parsed),
        "bad_flags": bad_flags,
        "forbidden_key_hits": forbidden_key_hits,
        "status": "PASS" if parsed and not bad_flags and not forbidden_key_hits else "FAIL",
    }


def verify_markdown() -> dict[str, Any]:
    md_paths = sorted(path for path in ROUTE_DIR.glob("G0_NOFILL_CAT_V2_*.md") if path.name != "NOFILL_CAT_V2_G0_SYNTHESIS_CONTROL_ROUTE_GOAL_PROMPT_2026-05-09.md")
    missing = []
    for path in md_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        if PROMOTION_VERDICT not in text:
            missing.append(path.name)
    return {"markdown_files": [path.name for path in md_paths], "missing_promotion_verdict": missing, "status": "PASS" if md_paths and not missing else "FAIL"}


def verify_counts() -> dict[str, Any]:
    counts = recompute_counts(read_jsonl(ROW_LEDGER))
    failures = []
    if counts["partition"] != EXPECTED_PARTITION:
        failures.append({"partition": counts["partition"]})
    if counts["accepted_split"] != EXPECTED_ACCEPTED_SPLIT:
        failures.append({"accepted_split": counts["accepted_split"]})
    if counts["accepted_label_counts"] != dict(sorted(EXPECTED_LABEL_COUNTS.items())):
        failures.append({"accepted_label_counts": counts["accepted_label_counts"]})
    if counts["accepted_source_lane_counts"] != dict(sorted(EXPECTED_SOURCE_LANE_COUNTS.items())):
        failures.append({"accepted_source_lane_counts": counts["accepted_source_lane_counts"]})
    for key, expected in EXPECTED_DUPLICATE_POSTURE.items():
        if counts["duplicate_posture"].get(key) != expected:
            failures.append({f"duplicate_posture.{key}": counts["duplicate_posture"].get(key)})
    blocked_with_label = [
        row["packet_row_id"]
        for row in counts["blocked_rows"]
        if row.get("categorical_input_label") is not None
        or row.get("in_accepted_packet_denominator") is not False
    ]
    rejected_with_label = [
        row["packet_row_id"]
        for row in counts["rejected_rows"]
        if row.get("categorical_input_label") is not None
        or row.get("in_accepted_packet_denominator") is not False
    ]
    if blocked_with_label:
        failures.append({"blocked_with_label_or_denominator": blocked_with_label})
    if rejected_with_label:
        failures.append({"rejected_with_label_or_denominator": rejected_with_label})
    summary = {
        "partition": counts["partition"],
        "accepted_split": counts["accepted_split"],
        "accepted_label_counts": counts["accepted_label_counts"],
        "accepted_source_lane_counts": counts["accepted_source_lane_counts"],
        "duplicate_posture": counts["duplicate_posture"],
        "blocker_code_counts": counts["blocker_code_counts"],
        "reject_decision_counts": counts["reject_decision_counts"],
    }
    return {"counts": summary, "failures": failures, "status": "PASS" if not failures else "FAIL"}


def verify_required_files() -> dict[str, Any]:
    missing = []
    for name in required_output_files():
        if not (ROUTE_DIR / name).exists():
            missing.append(name)
    return {"missing": missing, "status": "PASS" if not missing else "FAIL"}


def main() -> int:
    required = verify_required_files()
    counts = verify_counts()
    json_check = verify_generated_json()
    md_check = verify_markdown()
    py_compile = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(ROUTE_DIR / "build_g0_nofill_cat_v2_synthesis_control_route_2026_05_09.py"),
            str(ROUTE_DIR / "verify_g0_nofill_cat_v2_synthesis_control_route_2026_05_09.py"),
            str(ROUTE_DIR / "test_g0_nofill_cat_v2_synthesis_control_route_2026_05_09.py"),
        ]
    )
    pytest = run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(ROUTE_DIR / "test_g0_nofill_cat_v2_synthesis_control_route_2026_05_09.py"),
            "-q",
        ]
    )
    live_surface = live_surface_check()
    checks = {
        "required_files": required,
        "counts": counts,
        "generated_json": json_check,
        "markdown": md_check,
        "py_compile": py_compile,
        "focused_pytest": pytest,
        "live_surface_diff": live_surface,
    }
    status = all(
        [
            required["status"] == "PASS",
            counts["status"] == "PASS",
            json_check["status"] == "PASS",
            md_check["status"] == "PASS",
            py_compile["returncode"] == 0,
            pytest["returncode"] == 0,
            live_surface["status"] == "PASS",
        ]
    )
    result = {
        "route_id": "NOFILL_CAT_V2_G0_SYNTHESIS_CONTROL_ROUTE",
        "status": "PASS" if status else "FAIL",
        "can_mark_goal_complete": status,
        "checks": checks,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if status else 1


if __name__ == "__main__":
    raise SystemExit(main())
