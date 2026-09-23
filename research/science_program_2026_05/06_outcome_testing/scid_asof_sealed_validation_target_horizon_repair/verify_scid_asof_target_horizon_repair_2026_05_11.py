"""Verifier for the SCID as-of target/horizon repair route."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import build_scid_asof_target_horizon_repair_2026_05_11 as route


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = route.PREFIX
DATE_TAG = route.DATE_TAG
VERIFICATION_RESULT = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"

REQUIRED_FILES = [
    f"{PREFIX}_REPAIR_CONTEXT_ANCHOR_{DATE_TAG}.md",
    f"{PREFIX}_BLOCKER_RECONCILIATION_{DATE_TAG}.json",
    f"{PREFIX}_SOURCE_FIELD_INVENTORY_{DATE_TAG}.json",
    f"{PREFIX}_SEARCH_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_RULEBOOK_{DATE_TAG}.json",
    f"{PREFIX}_FAMILY_EXECUTABILITY_MATRIX_{DATE_TAG}.json",
    f"{PREFIX}_NEUTRAL_TARGET_CONTRACT_{DATE_TAG}.json",
    f"{PREFIX}_SOURCE_FIELD_DERIVATION_CONTRACT_{DATE_TAG}.json",
    f"{PREFIX}_SOURCE_FIELD_EXPANSION_EXECUTION_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_NOLEAK_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_MULTIPLE_TESTING_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_SOURCE_EXPANSION_REQUIREMENTS_{DATE_TAG}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md",
    f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json",
    "build_scid_asof_target_horizon_repair_2026_05_11.py",
    "verify_scid_asof_target_horizon_repair_2026_05_11.py",
    "test_scid_asof_target_horizon_repair_2026_05_11.py",
]
EXPECTED_JSON_FILES = [
    f"{PREFIX}_REPAIR_CONTEXT_ANCHOR_{DATE_TAG}.json",
    f"{PREFIX}_BLOCKER_RECONCILIATION_{DATE_TAG}.json",
    f"{PREFIX}_SOURCE_FIELD_INVENTORY_{DATE_TAG}.json",
    f"{PREFIX}_SEARCH_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_RULEBOOK_{DATE_TAG}.json",
    f"{PREFIX}_FAMILY_EXECUTABILITY_MATRIX_{DATE_TAG}.json",
    f"{PREFIX}_NEUTRAL_TARGET_CONTRACT_{DATE_TAG}.json",
    f"{PREFIX}_SOURCE_FIELD_DERIVATION_CONTRACT_{DATE_TAG}.json",
    f"{PREFIX}_SOURCE_FIELD_EXPANSION_EXECUTION_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_NOLEAK_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_MULTIPLE_TESTING_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_SOURCE_EXPANSION_REQUIREMENTS_{DATE_TAG}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json",
]
SAFE_FALSE_FLAGS = set(route.SAFE_FALSE_FLAGS)
RAW_SUFFIXES = (".scid", ".depth", ".parquet", ".csv", ".dly", ".bin", ".jsonl.gz")
RESULT_ROW_NAME_FRAGMENTS = (
    "RESULT_ROWS",
    "QUARANTINED_RESULTS",
    "SEALED_RESULTS",
    "STRESS_RESULTS",
    "BASELINE_RESULTS",
)
ALLOWED_SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/",
    "research/science_program_2026_05/04_goal_prompts/G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_GOAL_PROMPT_2026-05-11.md",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)


def record(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)


def parse_python(path: Path, failures: list[str]) -> None:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        failures.append(f"syntax parse failed for {repo_path(path)}: {exc}")


def check_safe_flags(payload: dict[str, Any], path: Path, failures: list[str]) -> None:
    record(payload.get("promotion_verdict") == "NO_PROMOTION_VERDICT", failures, f"{repo_path(path)} promotion verdict not safe")
    for flag in SAFE_FALSE_FLAGS:
        if flag in payload:
            record(payload.get(flag) is False, failures, f"{repo_path(path)} flag {flag} is not false")


def raw_blob_audit(paths: list[Path]) -> dict[str, Any]:
    entries = []
    issues = []
    for path in paths:
        if not path.exists():
            continue
        candidates = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
        for candidate in candidates:
            rel = repo_path(candidate)
            size = candidate.stat().st_size
            raw_suffix = rel.endswith(RAW_SUFFIXES)
            too_large = size > 100_000_000
            entries.append({"path": rel, "bytes": size, "raw_suffix": raw_suffix, "too_large": too_large})
            if raw_suffix or too_large:
                issues.append({"path": rel, "bytes": size, "raw_suffix": raw_suffix, "too_large": too_large})
    return {"entries_checked": len(entries), "issues": issues}


def dirty_state_audit() -> dict[str, Any]:
    proc = run_git(["status", "--short"])
    entries = []
    scoped_forbidden = []
    scoped_raw = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in ALLOWED_SCOPED_PREFIXES)
        entry = {"status": line[:2], "path": path, "scoped_to_this_route": scoped}
        entries.append(entry)
        if scoped and not any(path.startswith(prefix) for prefix in ALLOWED_SCOPED_PREFIXES):
            scoped_forbidden.append(entry)
        if scoped and path.endswith(RAW_SUFFIXES):
            scoped_raw.append(entry)
    return {
        "git_status_returncode": proc.returncode,
        "entries": entries,
        "scoped_forbidden_entries": scoped_forbidden,
        "scoped_raw_blob_entries": scoped_raw,
        "unrelated_dirty_entries_recorded_informational_only": [entry for entry in entries if not entry["scoped_to_this_route"]],
    }


def verify_route(write_result: bool = True, run_focused_tests: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    required = [ROUTE_DIR / name for name in REQUIRED_FILES]
    if VERIFICATION_RESULT.exists():
        required.append(VERIFICATION_RESULT)
    for path in required:
        record(path.exists(), failures, f"missing required file: {repo_path(path)}")

    json_payloads: dict[str, dict[str, Any]] = {}
    for name in EXPECTED_JSON_FILES:
        path = ROUTE_DIR / name
        if not path.exists():
            continue
        try:
            payload = load_json(path)
            json_payloads[name] = payload
            check_safe_flags(payload, path, failures)
        except json.JSONDecodeError as exc:
            failures.append(f"json parse failed for {repo_path(path)}: {exc}")

    for path in [route.CANDIDATE_ROWS, route.BAR_ROWS, route.G0_ROW_PARTITION_LEDGER]:
        try:
            rows = load_jsonl(path)
            record(len(rows) > 0, failures, f"jsonl empty or missing rows: {repo_path(path)}")
        except json.JSONDecodeError as exc:
            failures.append(f"jsonl parse failed for {repo_path(path)}: {exc}")

    for script in [
        ROUTE_DIR / "build_scid_asof_target_horizon_repair_2026_05_11.py",
        ROUTE_DIR / "verify_scid_asof_target_horizon_repair_2026_05_11.py",
        ROUTE_DIR / "test_scid_asof_target_horizon_repair_2026_05_11.py",
    ]:
        if script.exists():
            parse_python(script, failures)

    blocker = json_payloads.get(f"{PREFIX}_BLOCKER_RECONCILIATION_{DATE_TAG}.json", {})
    exact_counts = blocker.get("exact_count_reconciliation", {})
    record(blocker.get("blocker_reconstructed_from_disk") is True, failures, "predecessor blocker not reconstructed")
    record(all(item.get("pass") is True for item in exact_counts.values()), failures, "exact count reconciliation failed")

    inventory = json_payloads.get(f"{PREFIX}_SOURCE_FIELD_INVENTORY_{DATE_TAG}.json", {})
    record(inventory.get("counts", {}).get("candidate_rows") == 3014, failures, "candidate inventory count mismatch")
    record(inventory.get("counts", {}).get("bar_rows") == 7567, failures, "bar inventory count mismatch")
    record(
        inventory.get("neutral_derivation_coverage", {}).get("coverage_counts_are_not_result_metrics") is True,
        failures,
        "source coverage counts not marked as non-result metrics",
    )

    search = json_payloads.get(f"{PREFIX}_SEARCH_LEDGER_{DATE_TAG}.json", {})
    record(search.get("total_hits_by_group", {}).get("family_ids", 0) > 0, failures, "family search ledger has no hits")
    record(search.get("git_history_search") is not None, failures, "git history search missing")

    rulebook = json_payloads.get(f"{PREFIX}_RULEBOOK_{DATE_TAG}.json", {})
    target_defs = rulebook.get("target_definitions", [])
    record(rulebook.get("target_scope") == "SOURCE_SAFE_NEUTRAL_BAR_BEHAVIOR_ONLY_NOT_STRATEGY_EDGE", failures, "rulebook target scope unsafe")
    record(rulebook.get("horizon_set_m15_bars") == [1, 4, 16, 32], failures, "horizon set mismatch")
    record(len(target_defs) == 8, failures, "neutral target definition count mismatch")
    record(all(defn.get("strategy_edge_interpretation_allowed") is False for defn in target_defs), failures, "target allows strategy edge interpretation")

    matrix = json_payloads.get(f"{PREFIX}_FAMILY_EXECUTABILITY_MATRIX_{DATE_TAG}.json", {})
    rows = matrix.get("matrix_rows", [])
    statuses = {row.get("repair_status") for row in rows}
    record(len(rows) == 11, failures, "family matrix does not decide 11 families")
    record(statuses <= {"SOURCE_SAFE_NEUTRAL_TARGET_ONLY", "CONTROL_ONLY"}, failures, f"unexpected family statuses: {statuses}")
    record(all(row.get("strategy_specific_execution_allowed") is False for row in rows), failures, "a family is strategy executable")
    record(sum(1 for row in rows if row.get("repair_status") == "CONTROL_ONLY") == 4, failures, "control-only count mismatch")
    record(sum(1 for row in rows if row.get("repair_status") == "SOURCE_SAFE_NEUTRAL_TARGET_ONLY") == 7, failures, "neutral-only count mismatch")

    neutral = json_payloads.get(f"{PREFIX}_NEUTRAL_TARGET_CONTRACT_{DATE_TAG}.json", {})
    record(neutral.get("contract_status") == "SOURCE_SAFE_NEUTRAL_TARGETS_FROZEN_G12_AUDIT_REQUIRED", failures, "neutral contract status mismatch")

    derivation = json_payloads.get(f"{PREFIX}_SOURCE_FIELD_DERIVATION_CONTRACT_{DATE_TAG}.json", {})
    derivation_rows = derivation.get("family_missing_field_derivation_results", [])
    record(len(derivation_rows) == 11, failures, "derivation contract family count mismatch")
    record(
        all(row.get("accepted_bar_derivation_attempted") is True for row in derivation_rows),
        failures,
        "not every missing field family attempted accepted-bar derivation",
    )

    expansion = json_payloads.get(f"{PREFIX}_SOURCE_FIELD_EXPANSION_EXECUTION_LEDGER_{DATE_TAG}.json", {})
    record(expansion.get("all_families_pursued_to_same_class_closure") is True, failures, "source expansion ledger not saturated")

    source_requirements = json_payloads.get(f"{PREFIX}_SOURCE_EXPANSION_REQUIREMENTS_{DATE_TAG}.json", {})
    reqs = source_requirements.get("requirements", [])
    record(len(reqs) == 11, failures, "source expansion requirements count mismatch")
    record(
        sum(1 for row in reqs if row.get("requirement_status", "").startswith("EXACT_PROSPECTIVE")) == 7,
        failures,
        "strategy source expansion requirements count mismatch",
    )

    multiple = json_payloads.get(f"{PREFIX}_MULTIPLE_TESTING_LEDGER_{DATE_TAG}.json", {})
    record(multiple.get("neutral_target_definition_count") == 8, failures, "multiple-testing target count mismatch")
    record(multiple.get("this_route_adds_result_rows") is False, failures, "multiple-testing ledger says result rows added")

    completion = json_payloads.get(f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json", {})
    checklist = completion.get("prompt_to_artifact_checklist", [])
    record(completion.get("can_mark_goal_complete") is True, failures, "completion audit cannot mark complete")
    record(checklist and all(item.get("status") == "PASS" for item in checklist), failures, "completion checklist has non-PASS item")

    record(route.NEXT_G12_PROMPT.exists(), failures, "next G12 audit prompt missing")
    if route.NEXT_G12_PROMPT.exists():
        prompt = route.NEXT_G12_PROMPT.read_text(encoding="utf-8")
        record("G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_ONLY" in prompt, failures, "next G12 prompt evidence class missing")
        record("Do not generate result rows" in prompt, failures, "next G12 prompt result boundary missing")

    route_files = [p for p in ROUTE_DIR.rglob("*") if p.is_file()]
    result_row_files = [
        repo_path(path)
        for path in route_files
        if any(fragment in path.name.upper() for fragment in RESULT_ROW_NAME_FRAGMENTS)
    ]
    record(not result_row_files, failures, f"result-row-like artifacts emitted: {result_row_files}")

    raw_audit = raw_blob_audit([ROUTE_DIR, route.NEXT_G12_PROMPT])
    record(not raw_audit["issues"], failures, f"raw blob audit issues: {raw_audit['issues']}")

    dirty_audit = dirty_state_audit()
    record(not dirty_audit["scoped_raw_blob_entries"], failures, "scoped raw blob entries in git status")
    record(not dirty_audit["scoped_forbidden_entries"], failures, "scoped forbidden entries in git status")

    pytest_result: dict[str, Any] | None = None
    if run_focused_tests:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "--basetemp",
                str(ROOT / ".pytest_tmp_scid_target_horizon"),
                str(ROUTE_DIR / "test_scid_asof_target_horizon_repair_2026_05_11.py"),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        pytest_result = {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
        record(proc.returncode == 0, failures, "focused pytest failed")

    result = {
        **route.COMMON_SAFE_FIELDS,
        "artifact_family": "verification_result",
        "generated_at_utc": route.now_utc(),
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "failures": failures,
        "warnings": warnings,
        "raw_blob_audit": raw_audit,
        "dirty_state_scoped_diff_audit": dirty_audit,
        "focused_pytest": pytest_result,
        "required_files_checked": [repo_path(path) for path in required],
        "json_files_checked": [repo_path(ROUTE_DIR / name) for name in EXPECTED_JSON_FILES],
    }
    if write_result:
        VERIFICATION_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--run-focused-tests", action="store_true")
    args = parser.parse_args()
    result = verify_route(write_result=not args.no_write, run_focused_tests=args.run_focused_tests)
    print(json.dumps({"ok": result["ok"], "can_mark_goal_complete": result["can_mark_goal_complete"], "failures": result["failures"]}, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
