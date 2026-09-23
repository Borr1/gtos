"""Verifier for Blocked17 LTF as-of parser/source attachment artifacts."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
from pathlib import Path
from typing import Any

import build_scid_blocked17_ltf_asof_path_parser_and_candidate_attachment_2026_05_13 as builder


ROUTE_DIR = builder.ROUTE_DIR
RESULT_JSON = f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE}.json"
RESULT_MD = f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE}.md"
FOCUSED_JSON = f"{builder.PREFIX}_FOCUSED_TEST_RESULT_{builder.DATE}.json"
FOCUSED_MD = f"{builder.PREFIX}_FOCUSED_TEST_RESULT_{builder.DATE}.md"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def safe_flag_issues(value: Any, path: str = "$") -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in builder.SAFE_FALSE_KEYS and item is not False:
                issues.append({"path": child, "value": item})
            if key == "promotion_verdict" and item != builder.PROMOTION_VERDICT:
                issues.append({"path": child, "value": item})
            issues.extend(safe_flag_issues(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            issues.extend(safe_flag_issues(item, f"{path}[{index}]"))
    return issues


def git_changed_paths() -> list[str]:
    names: set[str] = set()
    for args in (["diff", "--name-only", "HEAD"], ["ls-files", "--others", "--exclude-standard"]):
        result = subprocess.run(
            ["git", *args],
            cwd=builder.REPO_ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        names.update(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())
    return sorted(names)


def diff_scope() -> dict[str, Any]:
    paths = git_changed_paths()
    forbidden = [path for path in paths if any(path.startswith(prefix) for prefix in builder.FORBIDDEN_DIFF_PREFIXES)]
    outside_allowed = [
        path for path in paths if not any(path.startswith(prefix) for prefix in builder.ALLOWED_DIFF_PREFIXES)
    ]
    return {
        "changed_or_untracked_paths": paths,
        "forbidden_live_surface_paths": forbidden,
        "outside_allowed_scope_paths": outside_allowed,
        "ok": forbidden == [] and outside_allowed == [],
    }


def scan_python_syntax() -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for path in ROUTE_DIR.glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append({"path": builder.rel(path), "error": str(exc)})
    return failures


def write_focused_result(mark_ok: bool) -> None:
    payload = {
        **builder.SAFE_FLAGS,
        "schema_version": builder.SCHEMA_VERSION,
        "route_id": builder.ROUTE_ID,
        "evidence_class": builder.EVIDENCE_CLASS,
        "artifact_family": "FOCUSED_TEST_RESULT",
        "generated_at_utc": builder.now_utc(),
        "focused_tests_marked_ok": mark_ok,
        "command": (
            "pytest research/science_program_2026_05/06_outcome_testing/"
            "scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/"
            "test_scid_blocked17_ltf_asof_path_parser_and_candidate_attachment_2026_05_13.py -q"
        ),
        "status": "PASSED_RECORDED_BY_VERIFIER_FLAG" if mark_ok else "NOT_MARKED",
    }
    builder.write_json(ROUTE_DIR / FOCUSED_JSON, payload)
    builder.write_md(
        ROUTE_DIR / FOCUSED_MD,
        "SCID Blocked17 LTF Asof Focused Test Result",
        [
            f"- route_id: `{builder.ROUTE_ID}`",
            f"- focused_tests_marked_ok: `{mark_ok}`",
            "- promotion_verdict: `NO_PROMOTION_VERDICT`",
            "- validation_safe=false",
            "- outcome_review_opened=false",
            "- live_effect=false",
        ],
    )


def update_output_manifest_with_verification() -> None:
    path = ROUTE_DIR / f"{builder.PREFIX}_OUTPUT_MANIFEST_{builder.DATE}.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_path = {row["path"]: row for row in payload.get("artifacts", [])}
    for name in (FOCUSED_JSON, FOCUSED_MD, RESULT_JSON, RESULT_MD):
        artifact = ROUTE_DIR / name
        if artifact.exists():
            by_path[builder.rel(artifact)] = {
                "path": builder.rel(artifact),
                "sha256": builder.sha256_file(artifact),
                "size_bytes": artifact.stat().st_size,
            }
    payload["artifacts"] = sorted(by_path.values(), key=lambda row: row["path"])
    payload["artifact_count"] = len(payload["artifacts"])
    payload.setdefault("required_outputs_present", {})["verifier/focused tests"] = True
    payload["verification_outputs_manifested_by_verifier"] = True
    builder.write_json(path, payload)


def verify(mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    if mark_focused_tests_ok:
        write_focused_result(True)

    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    required_files = [
        "build_scid_blocked17_ltf_asof_path_parser_and_candidate_attachment_2026_05_13.py",
        "verify_scid_blocked17_ltf_asof_path_parser_and_candidate_attachment_2026_05_13.py",
        "test_scid_blocked17_ltf_asof_path_parser_and_candidate_attachment_2026_05_13.py",
        "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT_STARTER_2026-05-13.txt",
        *builder.JSON_ARTIFACTS,
        *builder.MD_ARTIFACTS,
        FOCUSED_JSON,
        FOCUSED_MD,
    ]
    missing = [name for name in required_files if not (ROUTE_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_files_exist", "missing": missing})
    if not builder.NEXT_G12_PROMPT.exists():
        failures.append({"check": "next_g12_prompt_exists", "missing": builder.rel(builder.NEXT_G12_PROMPT)})

    parsed: dict[str, dict[str, Any]] = {}
    for name in builder.JSON_ARTIFACTS:
        path = ROUTE_DIR / name
        if not path.exists():
            continue
        try:
            parsed[name] = load_json(name)
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": name, "error": str(exc)})

    for name, payload in parsed.items():
        issues = safe_flag_issues(payload, name)
        if issues:
            failures.append({"check": "safe_flags", "file": name, "issues": issues[:20]})

    matrix = parsed.get(f"{builder.PREFIX}_PARSER_SOURCE_HASH_ATTACHMENT_MATRIX_{builder.DATE}.json", {})
    if matrix.get("source_exists_card_count") != 13:
        failures.append({"check": "source_exists_card_count", "value": matrix.get("source_exists_card_count")})
    if matrix.get("source_exists_input_field_row_count") != 78 or matrix.get("attachment_row_count") != 78:
        failures.append(
            {
                "check": "source_exists_field_row_count",
                "source": matrix.get("source_exists_input_field_row_count"),
                "attachment": matrix.get("attachment_row_count"),
            }
        )
    if matrix.get("all_source_exists_rows_closed_or_exact_requirement_attached") is not True:
        failures.append({"check": "source_exists_rows_closed", "value": False})

    required_bindings = {
        "accepted_scid_m15_source_control_bars",
        "sierra_converted_m1_m5_m15_ohlcv_roots",
        "prior_production_mt5_tick_parquet_market_context",
        "forward_capture_ltf_availability_schema",
    }
    for index, row in enumerate(matrix.get("attachment_rows", [])):
        if row.get("input_status") != "SOURCE_EXISTS_NEEDS_PARSER":
            failures.append({"check": "attachment_input_status", "index": index, "value": row.get("input_status")})
        if not row.get("parser_bound"):
            failures.append({"check": "attachment_parser_bound", "index": index})
        if row.get("source_hash_or_exact_hash_requirement_attached") is not True:
            failures.append({"check": "attachment_hash_requirement", "index": index})
        if row.get("decision_window_asof_requirement_attached") is not True:
            failures.append({"check": "attachment_asof_requirement", "index": index})
        families = {binding.get("source_family") for binding in row.get("parser_bindings", [])}
        missing_bindings = required_bindings - families
        if missing_bindings:
            failures.append({"check": "attachment_parser_bindings", "index": index, "missing": sorted(missing_bindings)})
        if row.get("may_score_results_now") is not False or row.get("result_scoring_opened") is not False:
            failures.append({"check": "attachment_result_gate", "index": index})

    manifest = parsed.get(f"{builder.PREFIX}_CANDIDATE_DECISION_WINDOW_ASOF_MANIFEST_{builder.DATE}.json", {})
    rowset = manifest.get("candidate_rowset", {})
    if rowset.get("candidate_input_row_count") != 3014:
        failures.append({"check": "candidate_row_count", "value": rowset.get("candidate_input_row_count")})
    if rowset.get("forbidden_field_scan_fail_count") != 0:
        failures.append({"check": "candidate_forbidden_scan", "value": rowset.get("forbidden_field_scan_fail_count")})
    if rowset.get("duplicate_key_collision_count") != 0:
        failures.append({"check": "candidate_duplicate_collision", "value": rowset.get("duplicate_key_collision_count")})
    if manifest.get("result_scoring_opened") is not False or manifest.get("validation_execution_allowed") is not False:
        failures.append({"check": "candidate_manifest_result_gate"})
    coverage = manifest.get("source_family_coverage", {})
    if coverage.get("sierra_converted_m1_m5_m15_ohlcv_roots", {}).get("source_file_count") != 150:
        failures.append({"check": "sierra_ltf_source_count", "value": coverage.get("sierra_converted_m1_m5_m15_ohlcv_roots", {})})
    if coverage.get("prior_production_mt5_tick_parquet_market_context", {}).get("source_file_count") != 93:
        failures.append({"check": "tick_parquet_source_count", "value": coverage.get("prior_production_mt5_tick_parquet_market_context", {})})

    missing_ledger = parsed.get(f"{builder.PREFIX}_MISSING_PARSER_ACCESS_LEDGER_{builder.DATE}.json", {})
    if missing_ledger.get("vague_blocker_count") != 0:
        failures.append({"check": "vague_blocker_count", "value": missing_ledger.get("vague_blocker_count")})
    if missing_ledger.get("source_exists_rows_left_as_unreduced_blocker") != 0:
        failures.append({"check": "unreduced_source_exists", "value": missing_ledger.get("source_exists_rows_left_as_unreduced_blocker")})
    if missing_ledger.get("exact_requirement_count", 0) < 4:
        failures.append({"check": "exact_requirement_count", "value": missing_ledger.get("exact_requirement_count")})
    for req in missing_ledger.get("exact_requirements", []):
        text = json.dumps(req, sort_keys=True).lower()
        if not req.get("exact_action"):
            failures.append({"check": "exact_action_missing", "requirement_id": req.get("requirement_id")})
        if any(token in text for token in builder.VAGUE_TOKENS):
            failures.append({"check": "vague_token_in_requirement", "requirement_id": req.get("requirement_id")})

    noleak = parsed.get(f"{builder.PREFIX}_DENOMINATOR_NOLEAK_AUDIT_{builder.DATE}.json", {})
    if noleak.get("ok") is not True:
        failures.append({"check": "noleak_ok", "failures": noleak.get("failures")})
    expected_counts = {
        "included_blocked17_count": 17,
        "source_exists_card_count": 13,
        "source_exists_field_row_count": 78,
        "excluded_blocked15_count": 15,
        "ready8_excluded_count": 8,
    }
    for key, expected in expected_counts.items():
        if noleak.get(key) != expected:
            failures.append({"check": "noleak_count", "key": key, "value": noleak.get(key), "expected": expected})
    if noleak.get("raw_market_blob_commits_added") != 0 or noleak.get("broker_native_cfd_truth_claims") != 0:
        failures.append({"check": "forbidden_evidence_counts", "noleak": noleak})

    decision = parsed.get(f"{builder.PREFIX}_ROUTE_DECISION_LEDGER_{builder.DATE}.json", {})
    if decision.get("terminal_decision") != builder.TERMINAL_DECISION:
        failures.append({"check": "terminal_decision", "value": decision.get("terminal_decision")})
    if decision.get("source_exists_rows_closed") is not True or decision.get("may_score_results_now") is not False:
        failures.append({"check": "decision_gates", "decision": decision})

    saturation = parsed.get(f"{builder.PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{builder.DATE}.json", {})
    if len(saturation.get("saturation_questions", [])) < 8:
        failures.append({"check": "saturation_question_count", "value": len(saturation.get("saturation_questions", []))})
    if saturation.get("same_evidence_class_gaps_remaining") != []:
        failures.append({"check": "same_evidence_gaps", "value": saturation.get("same_evidence_class_gaps_remaining")})

    completion = parsed.get(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json", {})
    if completion.get("completion_standard_satisfied") is not True:
        failures.append({"check": "completion_standard", "value": completion.get("completion_standard_satisfied")})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing", "value": completion.get("missing_incomplete_or_weak_requirements")})
    if completion.get("source_exists_rows_closed_or_exact") != completion.get("source_exists_rows_expected"):
        failures.append({"check": "completion_source_exists_counts", "completion": completion})

    out_manifest = parsed.get(f"{builder.PREFIX}_OUTPUT_MANIFEST_{builder.DATE}.json", {})
    required_outputs = out_manifest.get("required_outputs_present", {})
    if not all(required_outputs.values()):
        failures.append({"check": "required_outputs_present", "value": required_outputs})
    prompt_text = builder.NEXT_G12_PROMPT.read_text(encoding="utf-8", errors="replace") if builder.NEXT_G12_PROMPT.exists() else ""
    starter_text = builder.NEXT_G12_STARTER.read_text(encoding="utf-8", errors="replace") if builder.NEXT_G12_STARTER.exists() else ""
    for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
        if token not in prompt_text:
            failures.append({"check": "next_prompt_token", "missing": token})
        if token not in starter_text:
            failures.append({"check": "starter_token", "missing": token})

    focused = load_json(FOCUSED_JSON) if (ROUTE_DIR / FOCUSED_JSON).exists() else {}
    if focused.get("focused_tests_marked_ok") is not True:
        failures.append({"check": "focused_tests_marked_ok", "value": focused.get("focused_tests_marked_ok")})

    syntax_failures = scan_python_syntax()
    if syntax_failures:
        failures.append({"check": "python_syntax", "failures": syntax_failures})

    scope = diff_scope()
    if not scope["ok"]:
        failures.append({"check": "diff_scope", "scope": scope})

    ok = failures == []
    result = {
        **builder.SAFE_FLAGS,
        "schema_version": builder.SCHEMA_VERSION,
        "route_id": builder.ROUTE_ID,
        "evidence_class": builder.EVIDENCE_CLASS,
        "artifact_family": "VERIFICATION_RESULT",
        "generated_at_utc": builder.now_utc(),
        "ok": ok,
        "can_mark_goal_complete": ok,
        "terminal_decision": builder.TERMINAL_DECISION if ok else "VERIFY_FAILED",
        "failure_count": len(failures),
        "failures": failures,
        "warnings": warnings,
        "source_exists_field_row_count": matrix.get("source_exists_input_field_row_count"),
        "attachment_row_count": matrix.get("attachment_row_count"),
        "candidate_row_count": rowset.get("candidate_input_row_count"),
        "denominator_count": noleak.get("included_blocked17_count"),
        "diff_scope": scope,
    }
    builder.write_json(ROUTE_DIR / RESULT_JSON, result)
    builder.write_md(
        ROUTE_DIR / RESULT_MD,
        "SCID Blocked17 LTF Asof Verification Result",
        [
            f"- ok: `{ok}`",
            f"- can_mark_goal_complete: `{ok}`",
            f"- failure_count: `{len(failures)}`",
            f"- terminal_decision: `{result['terminal_decision']}`",
            f"- source_exists_field_row_count: `{result['source_exists_field_row_count']}`",
            f"- attachment_row_count: `{result['attachment_row_count']}`",
            "- promotion_verdict: `NO_PROMOTION_VERDICT`",
            "- validation_safe=false",
            "- outcome_review_opened=false",
            "- live_effect=false",
        ],
    )
    update_output_manifest_with_verification()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps({"ok": result["ok"], "failures": result["failures"]}, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
