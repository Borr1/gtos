from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE_STAMP = "2026-05-08"
CONTRACT_ID = "NOFILL_LIFECYCLE_CLOSURE_RESULT_CONTRACT_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ROW_0127_EXPECTED_SHA256 = "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
ROW_0127_FIRST_TOUCH = "2026-05-06T07:15:00.634000Z"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]

JSON_ARTIFACTS = [
    f"NOFILL_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_UNIVERSE_AND_EXCLUSION_LEDGER_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_POLICY_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_BLOCKER_LEDGER_{DATE_STAMP}.json",
    f"NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.json",
]

MD_ARTIFACTS = [
    f"NOFILL_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE_STAMP}.md",
    f"NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE_STAMP}.md",
    f"NOFILL_RESULT_CONTRACT_UNIVERSE_AND_EXCLUSION_LEDGER_{DATE_STAMP}.md",
    f"NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS_{DATE_STAMP}.md",
    f"NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_{DATE_STAMP}.md",
    f"NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA_{DATE_STAMP}.md",
    f"NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_POLICY_{DATE_STAMP}.md",
    f"NOFILL_RESULT_CONTRACT_BLOCKER_LEDGER_{DATE_STAMP}.md",
    f"NOFILL_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE_STAMP}.md",
    f"NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.md",
]

PY_FILES = [
    "build_nofill_lifecycle_result_contract_design_2026_05_08.py",
    "verify_nofill_lifecycle_result_contract_design_2026_05_08.py",
    "test_nofill_lifecycle_result_contract_design_2026_05_08.py",
]

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/fn_smoke_trade",
    "scripts/mt5",
    "tests/canary",
)


def load_json(name: str) -> dict[str, Any]:
    with (OUT_DIR / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def run(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    return {
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-3000:],
        "stderr_tail": proc.stderr[-3000:],
        "status": "PASS" if proc.returncode == 0 else "FAIL",
    }


def check_artifact_presence() -> dict[str, Any]:
    expected = JSON_ARTIFACTS + MD_ARTIFACTS + PY_FILES
    missing = [name for name in expected if not (OUT_DIR / name).exists()]
    return {"status": "PASS" if not missing else "FAIL", "missing": missing, "expected_count": len(expected)}


def check_json_parse() -> dict[str, Any]:
    parsed = []
    errors = []
    for name in JSON_ARTIFACTS:
        try:
            load_json(name)
            parsed.append(name)
        except Exception as exc:  # pragma: no cover - diagnostic path
            errors.append({"path": name, "error": str(exc)})
    return {"status": "PASS" if not errors else "FAIL", "parsed_count": len(parsed), "errors": errors}


def check_flags(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for name, payload in payloads.items():
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append(f"{name}: promotion_verdict")
        if payload.get("validation_safe") is not False:
            issues.append(f"{name}: validation_safe")
        if payload.get("outcome_review_opened") is not False:
            issues.append(f"{name}: outcome_review_opened")
        if payload.get("live_effect") is not False:
            issues.append(f"{name}: live_effect")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_objective_coverage(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    rulebook = payloads["NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-08.json"]
    universe = payloads["NOFILL_RESULT_CONTRACT_UNIVERSE_AND_EXCLUSION_LEDGER_2026-05-08.json"]
    fields = payloads["NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS_2026-05-08.json"]
    parser = payloads["NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_2026-05-08.json"]
    noleak = payloads["NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA_2026-05-08.json"]
    duplicate = payloads["NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_POLICY_2026-05-08.json"]
    blockers = payloads["NOFILL_RESULT_CONTRACT_BLOCKER_LEDGER_2026-05-08.json"]

    required_rulebook_sections = [
        "eligible_universe",
        "result_label_families",
        "entry_fill_cancel_expiry_semantics",
        "side_aware_touch_parser",
        "source_hierarchy",
        "same_bar_and_terminal_order_policy",
        "duplicate_denominator_policy",
        "sample_floor_policy",
        "no_leak_asof_schema",
        "source_hash_and_cache_policy",
        "dsr_pbo_effective_n_policy",
        "exact_next_lane_gates",
    ]
    for section in required_rulebook_sections:
        if section not in rulebook:
            issues.append(f"missing rulebook section {section}")

    if rulebook["starting_evidence_locked"]["g12_decision"] != "ACCEPT_CORRECTED_SOURCE_PACKET_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE":
        issues.append("G12 decision not preserved")
    if rulebook["starting_evidence_locked"]["packet_rows"] != 298:
        issues.append("packet row count not preserved")
    if rulebook["starting_evidence_locked"]["source_blocked_exact"] != 0:
        issues.append("source_blocked_exact not zero")
    if rulebook["starting_evidence_locked"]["row_0127_source_sha256"] != ROW_0127_EXPECTED_SHA256:
        issues.append("row 0127 sha mismatch in rulebook")
    if rulebook["starting_evidence_locked"]["row_0127_first_terminal_area_touch_utc"] != ROW_0127_FIRST_TOUCH:
        issues.append("row 0127 first touch mismatch")

    if universe["source_packet"]["packet_rows"] != 298:
        issues.append("universe packet rows != 298")
    if universe["source_packet"]["source_closed_rows"] != 298:
        issues.append("universe source closed rows != 298")
    if universe["source_packet"]["source_blocked_exact_rows"] != 0:
        issues.append("universe source blocked exact rows != 0")
    if universe["exclusions"]["six_t3_rows"]["t3_row_count"] != 6:
        issues.append("six T3 exclusion count not preserved")
    if universe["exclusions"]["blocked_94_cnr061"]["blocked_rows"] != 94:
        issues.append("blocked 94 CNR061 count not preserved")
    if universe["current_result_opening_status"]["result_rows_opened"] != 0:
        issues.append("result rows were opened")
    if universe["current_result_opening_status"]["r_or_performance_rows_scored"] != 0:
        issues.append("R/performance rows scored")

    if "entry_touched_at_utc" not in fields["required_pending_intent_closure_fields"]:
        issues.append("pending-intent entry_touched_at_utc requirement missing")
    if parser["side_rules"]["LONG"]["entry_touch"] != "ask <= entry_price":
        issues.append("LONG entry parser mismatch")
    if parser["side_rules"]["SHORT"]["entry_touch"] != "bid >= entry_price":
        issues.append("SHORT entry parser mismatch")
    if "broker_actual_r" not in noleak["forbidden_fields"]:
        issues.append("forbidden broker_actual_r not in noleak schema")
    if duplicate["current_duplicate_state"]["nofill_duplicate_key_unique"] != 196:
        issues.append("duplicate key unique count changed")
    if duplicate["sample_floor_policy"]["future_result_validation"]["minimum_unique_nofill_duplicate_key_overall"] < 100:
        issues.append("validation sample floor too weak")
    if "BLOCK_RESULT_FORBIDDEN_FIELD" not in blockers["result_contract_blocker_rules"]:
        issues.append("forbidden-field blocker missing")
    if blockers["row_0127_status"]["source_sha256"] != ROW_0127_EXPECTED_SHA256:
        issues.append("row 0127 sha mismatch in blocker ledger")

    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_source_hashes(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    anchor = payloads[f"NOFILL_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE_STAMP}.json"]
    missing = []
    mismatches = []
    checked = 0
    row_0127_seen = False
    for record in anchor["source_files_read_or_hashed"]:
        if not record["exists"]:
            missing.append(record["path"])
            continue
        if record["path"].endswith("OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"):
            row_0127_seen = True
            if record["sha256"] != ROW_0127_EXPECTED_SHA256:
                mismatches.append({"path": record["path"], "expected": ROW_0127_EXPECTED_SHA256, "actual": record["sha256"]})
        checked += 1
    if not row_0127_seen:
        missing.append("row_0127_otr061_source_hash_record")
    return {
        "status": "PASS" if not missing and not mismatches else "FAIL",
        "checked": checked,
        "missing": missing,
        "mismatches": mismatches,
    }


def check_live_surface_diff() -> dict[str, Any]:
    workspace_proc = subprocess.run(["git", "diff", "--name-only"], cwd=REPO_ROOT, text=True, capture_output=True)
    workspace_names = [line.strip().replace("\\", "/") for line in workspace_proc.stdout.splitlines() if line.strip()]
    committed_proc = subprocess.run(["git", "diff", "--name-only", "HEAD^1", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True)
    committed_names = [line.strip().replace("\\", "/") for line in committed_proc.stdout.splitlines() if line.strip()]
    lane_prefix = "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_result_contract_design/"
    use_committed_scope = committed_proc.returncode == 0 and any(name.startswith(lane_prefix) for name in committed_names)
    names = committed_names if use_committed_scope else workspace_names
    forbidden = [name for name in names if name.startswith(FORBIDDEN_LIVE_PREFIXES)]
    return {
        "status": "PASS" if (committed_proc.returncode == 0 if use_committed_scope else workspace_proc.returncode == 0) and not forbidden else "FAIL",
        "checked_scope": "committed_diff_HEAD_parent" if use_committed_scope else "workspace_diff",
        "changed_paths": names,
        "workspace_changed_path_count_observed": len(workspace_names),
        "workspace_changed_paths_observed_sample": workspace_names[:50],
        "forbidden_live_surface_changed_paths": forbidden,
        "checked_prefixes": list(FORBIDDEN_LIVE_PREFIXES),
    }


def check_py_compile() -> dict[str, Any]:
    results = []
    for name in PY_FILES:
        try:
            py_compile.compile(str(OUT_DIR / name), doraise=True)
            results.append({"path": name, "status": "PASS"})
        except Exception as exc:  # pragma: no cover - diagnostic path
            results.append({"path": name, "status": "FAIL", "error": str(exc)})
    return {"status": "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL", "results": results}


def run_focused_pytest() -> dict[str, Any]:
    if os.environ.get("NOFILL_RESULT_CONTRACT_SKIP_NESTED_PYTEST") == "1":
        return {"status": "SKIPPED", "reason": "NOFILL_RESULT_CONTRACT_SKIP_NESTED_PYTEST=1"}
    env = dict(os.environ)
    env["NOFILL_RESULT_CONTRACT_SKIP_NESTED_PYTEST"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            str(OUT_DIR / "test_nofill_lifecycle_result_contract_design_2026_05_08.py"),
            "-q",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    return {
        "command": f"{sys.executable} -B -m pytest -p no:cacheprovider {OUT_DIR / 'test_nofill_lifecycle_result_contract_design_2026_05_08.py'} -q",
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-3000:],
        "stderr_tail": proc.stderr[-3000:],
        "status": "PASS" if proc.returncode == 0 else "FAIL",
    }


def write_completion_audit(payloads: dict[str, dict[str, Any]], verification: dict[str, Any]) -> None:
    audit_name = f"NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.json"
    audit = payloads[audit_name]
    all_pass = all(
        value.get("status") in ("PASS", "SKIPPED")
        for key, value in verification.items()
        if isinstance(value, dict)
    )
    # Focused pytest is only SKIPPED when verify_contract is called from pytest.
    if verification.get("focused_pytest", {}).get("status") == "SKIPPED":
        all_pass = all(
            value.get("status") == "PASS"
            for key, value in verification.items()
            if isinstance(value, dict) and key != "focused_pytest"
        )
    audit["verification_results"] = verification
    audit["can_mark_goal_complete"] = bool(all_pass)
    audit["missing_or_weak_requirements"] = [] if all_pass else ["One or more verifier checks failed."]
    audit["completion_status"] = "PASS_FROZEN_RESULT_CONTRACT_DESIGN" if all_pass else "FAIL_CONTRACT_DESIGN_VERIFICATION"
    for item in audit["prompt_to_artifact_checklist"]:
        item["status"] = "PASS" if all_pass else "RECHECK_REQUIRED"
    (OUT_DIR / audit_name).write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_body = "\n".join(
        [
            f"Completion status: `{audit['completion_status']}`",
            f"Can mark goal complete: `{str(audit['can_mark_goal_complete']).lower()}`",
            "",
            "## Verification",
            "",
            "\n".join(f"- `{key}`: `{value.get('status')}`" for key, value in verification.items() if isinstance(value, dict)),
            "",
            "All outputs remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.",
        ]
    )
    (OUT_DIR / f"NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.md").write_text(
        f"# NOFILL Result Contract Completion Audit\n\n{md_body}\n",
        encoding="utf-8",
    )


def verify_contract(run_pytest: bool = True, write_audit: bool = True) -> dict[str, Any]:
    presence = check_artifact_presence()
    parse = check_json_parse()
    payloads = {name: load_json(name) for name in JSON_ARTIFACTS if (OUT_DIR / name).exists()}
    results = {
        "artifact_presence": presence,
        "json_parse": parse,
        "flags": check_flags(payloads),
        "objective_coverage": check_objective_coverage(payloads),
        "source_hashes": check_source_hashes(payloads),
        "py_compile": check_py_compile(),
        "live_surface_diff": check_live_surface_diff(),
    }
    if run_pytest:
        results["focused_pytest"] = run_focused_pytest()
    else:
        results["focused_pytest"] = {"status": "SKIPPED", "reason": "called with run_pytest=False"}

    results["verification_status"] = {
        "status": "PASS"
        if all(value.get("status") in ("PASS", "SKIPPED") for value in results.values() if isinstance(value, dict))
        else "FAIL"
    }
    if write_audit and f"NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE_STAMP}.json" in payloads:
        write_completion_audit(payloads, results)
    return results


def main() -> None:
    results = verify_contract(run_pytest=True, write_audit=True)
    status = results["verification_status"]["status"]
    print(json.dumps({"verification_status": status, "can_mark_goal_complete": status == "PASS", "results": results}, indent=2, sort_keys=True))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
