"""Verify the SCID forward-capture offline schema implementation package.

This verifier is intentionally offline and read-only except for writing its own
verification result artifact. It checks generated schemas, fixtures, alignment
ledgers, manifest-repair policy, G12 prompt handoff, and scoped git surface.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
BUILDER_PATH = HERE / "build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py"
SPEC = importlib.util.spec_from_file_location("scid_forward_capture_builder", BUILDER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load builder from {BUILDER_PATH}")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)

ROOT: Path = builder.ROOT
ROUTE_DIR: Path = builder.ROUTE_DIR
SCHEMA_DIR: Path = builder.SCHEMA_DIR
FIXTURE_DIR: Path = builder.FIXTURE_DIR
PREFIX: str = builder.PREFIX
DATE_TAG: str = builder.DATE_TAG
ROUTE_REL = builder.repo_path(ROUTE_DIR)
PROMPT_REL = builder.repo_path(builder.NEXT_G12_PROMPT)


def output_path(stem: str, suffix: str = "json") -> Path:
    return builder.output_path(stem, suffix)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def md_json_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    start = text.index("```json") + len("```json")
    end = text.rindex("```")
    return json.loads(text[start:end].strip())


def git_status() -> list[dict[str, str]]:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    rows = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        rows.append({"status": line[:2].strip(), "path": line[3:].replace("\\", "/")})
    return rows


def assert_true(checks: list[dict[str, Any]], name: str, condition: bool, detail: Any = None) -> None:
    checks.append({"check": name, "status": "PASS" if condition else "FAIL", "detail": detail})


def required_route_files() -> list[Path]:
    json_md_stems = [
        "CONTEXT_ANCHOR",
        "ACCEPTED_G12_G0_HANDOFF_RECONCILIATION",
        "FIELD_GROUP_SCHEMA_LEDGER",
        "PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT",
        "FIXTURE_MANIFEST",
        "FIXTURE_VALIDATION_RESULT_LEDGER",
        "READ_ONLY_MONITORING_ALIGNMENT_LEDGER",
        "MANIFEST_HASH_POLICY_LEDGER",
        "G12_ACCEPTANCE_CRITERIA_LEDGER",
        "SATURATION_SELF_REDTEAM_LEDGER",
        "COMPLETION_AUDIT",
        "CLOSEOUT_VERIFICATION",
        "OUTPUT_MANIFEST",
    ]
    files = [
        BUILDER_PATH,
        Path(__file__).resolve(),
        HERE / "test_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
        builder.NEXT_G12_PROMPT,
    ]
    for stem in json_md_stems:
        files.extend([output_path(stem, "json"), output_path(stem, "md")])
    files.append(SCHEMA_DIR / f"{builder.SCHEMA_VERSION}_master.schema.json")
    files.extend(SCHEMA_DIR / f"{builder.SCHEMA_VERSION}_{group}.schema.json" for group in builder.FIELD_GROUPS)
    return files


def verify_required_files(checks: list[dict[str, Any]]) -> None:
    files = required_route_files()
    missing = [builder.repo_path(path) for path in files if not path.exists()]
    assert_true(checks, "required_route_files_exist", not missing, {"missing": missing, "required_count": len(files)})


def verify_safe_flags(checks: list[dict[str, Any]]) -> None:
    json_paths = sorted(ROUTE_DIR.glob(f"{PREFIX}_*.json"))
    safe_failures = []
    for path in json_paths:
        if path.name.endswith("_VERIFICATION_RESULT_2026-05-12.json"):
            continue
        payload = load_json(path)
        if not isinstance(payload, dict):
            continue
        expected = {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        }
        for key, value in expected.items():
            if payload.get(key) != value:
                safe_failures.append({"path": builder.repo_path(path), "key": key, "value": payload.get(key)})
    assert_true(checks, "safe_flags_closed_in_route_json", not safe_failures, safe_failures)


def verify_schema_ledger(checks: list[dict[str, Any]]) -> None:
    expected_groups = sorted(builder.FIELD_GROUPS)
    ledger = load_json(output_path("FIELD_GROUP_SCHEMA_LEDGER", "json"))
    assert_true(checks, "schema_ledger_route_id", ledger.get("route_id") == builder.ROUTE_ID, ledger.get("route_id"))
    assert_true(checks, "schema_group_count_10", ledger.get("group_schema_count") == 10, ledger.get("group_schema_count"))
    assert_true(checks, "schema_file_count_11", ledger.get("total_schema_file_count") == 11, ledger.get("total_schema_file_count"))
    assert_true(
        checks,
        "schema_candidate_and_duplicate_coverage_3014",
        ledger.get("candidate_rows_coverage_expectation") == 3014
        and ledger.get("duplicate_proxy_denominator_key_coverage_expectation") == 3014,
        {
            "candidate_rows_coverage_expectation": ledger.get("candidate_rows_coverage_expectation"),
            "duplicate_proxy_denominator_key_coverage_expectation": ledger.get("duplicate_proxy_denominator_key_coverage_expectation"),
        },
    )
    observed_groups = sorted(row["field_group"] for row in ledger.get("field_groups", []))
    assert_true(checks, "schema_groups_match_accepted_contract", observed_groups == expected_groups, observed_groups)

    group_schema_failures = []
    for group in expected_groups:
        path = SCHEMA_DIR / f"{builder.SCHEMA_VERSION}_{group}.schema.json"
        schema = load_json(path)
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        missing_common = sorted(set(builder.COMMON_FIELD_NAMES) - set(required))
        missing_props = sorted(set(required) - set(properties))
        if missing_common or missing_props or schema.get("additionalProperties") is not False:
            group_schema_failures.append(
                {
                    "field_group": group,
                    "missing_common": missing_common,
                    "missing_properties": missing_props,
                    "additionalProperties": schema.get("additionalProperties"),
                }
            )
    assert_true(checks, "group_schemas_have_common_fields_and_closed_properties", not group_schema_failures, group_schema_failures)


def verify_contract(checks: list[dict[str, Any]]) -> None:
    contract = load_json(output_path("PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT", "json"))
    parser = contract.get("parser_contract", {})
    redaction = contract.get("redaction_contract", {})
    asof = contract.get("asof_contract", {})
    assert_true(checks, "parser_contract_fail_closed_duplicate_hash_policy", all(key in parser for key in [
        "schema_version_check",
        "source_hash_policy",
        "duplicate_policy",
        "fail_closed_policy",
    ]), parser)
    assert_true(
        checks,
        "redaction_contract_forbids_broker_account_order_deal_position",
        "broker_account_order_deal_position" in redaction.get("policy_id", "").lower()
        and {"account_id", "broker_order_id", "deal_id", "position_id"}.issubset(set(redaction.get("forbidden_values", []))),
        redaction,
    )
    assert_true(checks, "asof_contract_source_not_after_decision", "<= decision_asof_utc" in asof.get("common_check", ""), asof)
    assert_true(checks, "field_group_contracts_complete", sorted(contract.get("field_group_contracts", {})) == sorted(builder.FIELD_GROUPS), None)


def verify_fixtures(checks: list[dict[str, Any]]) -> None:
    manifest = load_json(output_path("FIXTURE_MANIFEST", "json"))
    fixture_result = load_json(output_path("FIXTURE_VALIDATION_RESULT_LEDGER", "json"))
    recomputed = builder.validate_fixtures(manifest)
    stable_recomputed = dict(recomputed)
    stable_recomputed.pop("generated_at_utc", None)

    required_categories = {
        "valid_pass",
        "missing_field_fail_closed",
        "ltf_unavailable",
        "orderflow_proxy_unavailable",
        "forbidden_broker_identifier",
        "stale_asof_violation",
        "duplicate_denominator_consistency",
        "manifest_binding_repair_continuity",
    }
    observed_categories = {item["category"] for item in manifest.get("fixtures", [])}
    missing_group_fixtures = sorted(set(builder.FIELD_GROUPS) - set(manifest.get("field_groups_with_missing_fixture", [])))

    assert_true(checks, "fixture_categories_complete", required_categories.issubset(observed_categories), sorted(observed_categories))
    assert_true(checks, "missing_required_fixture_for_every_group", not missing_group_fixtures, missing_group_fixtures)
    assert_true(checks, "fixture_validation_ledger_expected_behavior", fixture_result.get("all_expected_behavior_observed") is True, fixture_result)
    assert_true(
        checks,
        "fixture_validation_recomputed_expected_behavior",
        recomputed.get("all_expected_behavior_observed") is True,
        stable_recomputed,
    )
    assert_true(
        checks,
        "fixture_pass_fail_counts_match_manifest",
        recomputed.get("valid_fixture_pass_count") == sum(1 for item in manifest["fixtures"] if item["expected_valid"])
        and recomputed.get("invalid_fixture_fail_closed_count") == sum(1 for item in manifest["fixtures"] if not item["expected_valid"]),
        {
            "valid_fixture_pass_count": recomputed.get("valid_fixture_pass_count"),
            "invalid_fixture_fail_closed_count": recomputed.get("invalid_fixture_fail_closed_count"),
            "fixture_count": len(manifest.get("fixtures", [])),
        },
    )

    specific_expected = {
        "ltf_unavailable_fail_closed_valid": True,
        "orderflow_proxy_unavailable_fail_closed_valid": True,
        "forbidden_broker_identifier_fail_closed": False,
        "stale_asof_violation_fail_closed": False,
        "duplicate_denominator_consistency_valid": True,
        "duplicate_denominator_mismatch_fail_closed": False,
        "manifest_binding_repair_continuity": True,
    }
    by_id = {row["fixture_id"]: row["observed_valid"] for row in recomputed["fixture_results"]}
    mismatches = {key: by_id.get(key) for key, expected in specific_expected.items() if by_id.get(key) is not expected}
    assert_true(checks, "specific_fixture_expected_results", not mismatches, mismatches)


def verify_monitoring_alignment(checks: list[dict[str, Any]]) -> None:
    alignment = load_json(output_path("READ_ONLY_MONITORING_ALIGNMENT_LEDGER", "json"))
    assert_true(checks, "monitoring_alignment_read_only", alignment.get("read_only_alignment_only") is True, alignment)
    assert_true(checks, "monitoring_alignment_no_wiring", alignment.get("live_wiring_added") is False and alignment.get("producer_files_modified") == [], alignment)
    assert_true(checks, "monitoring_alignment_target_count", alignment.get("alignment_target_count", 0) >= 10, alignment.get("alignment_target_count"))
    assert_true(checks, "monitoring_alignment_covers_all_groups", alignment.get("missing_alignment_groups") == [], alignment.get("missing_alignment_groups"))
    unsafe_rows = [
        row
        for row in alignment.get("alignment_targets", [])
        if row.get("producer_modified") or row.get("running_process_altered") or row.get("raw_values_copied")
    ]
    assert_true(checks, "monitoring_alignment_shape_only_no_raw_values", not unsafe_rows, unsafe_rows)


def verify_manifest_policy(checks: list[dict[str, Any]]) -> None:
    policy = load_json(output_path("MANIFEST_HASH_POLICY_LEDGER", "json"))
    repair = policy.get("repair_policy", {})
    expected = {
        "current_g12_prompt_hash_supersedes_stale_pre_hardening_hash": True,
        "builder_output_manifest_self_hash_is_non_blocking": True,
        "all_other_source_input_hash_mismatches_are_strict_blockers": True,
    }
    assert_true(checks, "manifest_repair_policy_exact", all(repair.get(key) is value for key, value in expected.items()), repair)
    assert_true(checks, "manifest_no_blocking_unrepaired_hash_mismatches", policy.get("blocking_unrepaired_hash_mismatches") == [], policy)
    assert_true(checks, "manifest_no_raw_market_blob_inputs", policy.get("raw_market_blob_inputs_committed_by_this_route") == [], policy)


def verify_g12_prompt(checks: list[dict[str, Any]]) -> None:
    prompt = builder.NEXT_G12_PROMPT.read_text(encoding="utf-8") if builder.NEXT_G12_PROMPT.exists() else ""
    required_phrases = [
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
        "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
        "REPAIR_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_BEFORE_USE",
        "broker account/order/history/deal/position evidence",
        "raw market-data blob commits",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in prompt]
    assert_true(checks, "next_g12_prompt_contains_acceptance_and_safe_flags", not missing, missing)


def verify_output_manifest(checks: list[dict[str, Any]]) -> None:
    manifest = load_json(output_path("OUTPUT_MANIFEST", "json"))
    paths = {row["path"] for row in manifest.get("artifacts", [])}
    assert_true(checks, "output_manifest_route_id", manifest.get("route_id") == builder.ROUTE_ID, manifest.get("route_id"))
    assert_true(checks, "output_manifest_schema_count_11", manifest.get("schema_file_count") == 11, manifest.get("schema_file_count"))
    assert_true(checks, "output_manifest_fixture_count_at_least_17", manifest.get("fixture_file_count", 0) >= 17, manifest.get("fixture_file_count"))
    assert_true(checks, "output_manifest_includes_next_g12_prompt", PROMPT_REL in paths, PROMPT_REL)


def verify_scoped_git_surface(checks: list[dict[str, Any]]) -> None:
    rows = git_status()
    scoped_prefixes = (
        f"{ROUTE_REL}/",
        PROMPT_REL,
        ".context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
    )
    scoped_rows = [row for row in rows if row["path"].startswith(scoped_prefixes)]
    forbidden_scoped = [
        row
        for row in scoped_rows
        if row["path"].startswith(("src/", "config/", "prompts/", "scripts/", "shadow_logs/", "data/"))
        or "raw_market" in row["path"].lower()
    ]
    assert_true(
        checks,
        "git_scoped_surface_contains_only_route_prompt_and_context_refresh",
        not forbidden_scoped,
        {
            "forbidden_scoped": forbidden_scoped,
            "scoped_surface_policy": "Only route artifacts, generated G12 prompt, and context refresh files are in-scope; unrelated dirty worktree entries are ignored and not serialized because they are runtime-volatile.",
        },
    )


def verify_md_json_pairs(checks: list[dict[str, Any]]) -> None:
    mismatches = []
    for json_path in sorted(ROUTE_DIR.glob(f"{PREFIX}_*.json")):
        if json_path.name.endswith("_VERIFICATION_RESULT_2026-05-12.json"):
            continue
        md_path = json_path.with_suffix(".md")
        if not md_path.exists():
            continue
        json_payload = load_json(json_path)
        md_payload = md_json_payload(md_path)
        if json_payload != md_payload:
            mismatches.append(builder.repo_path(json_path))
    assert_true(checks, "json_md_pairs_match", not mismatches, mismatches)


def verify() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    verify_required_files(checks)
    verify_safe_flags(checks)
    verify_schema_ledger(checks)
    verify_contract(checks)
    verify_fixtures(checks)
    verify_monitoring_alignment(checks)
    verify_manifest_policy(checks)
    verify_g12_prompt(checks)
    verify_output_manifest(checks)
    verify_md_json_pairs(checks)
    verify_scoped_git_surface(checks)

    failed = [check for check in checks if check["status"] != "PASS"]
    result = {
        "artifact_family": "verification_result",
        "route_id": builder.ROUTE_ID,
        "evidence_class": builder.EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "terminal_decision": "VERIFIED_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_READY_FOR_G12_AUDIT"
        if not failed
        else "REPAIR_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_BEFORE_G12_AUDIT",
        "ok": not failed,
        "can_mark_goal_complete_after_scoped_commits_and_live_state_refresh": not failed,
        "check_count": len(checks),
        "failed_check_count": len(failed),
        "failed_checks": failed,
        "checks": checks,
    }
    write_json(output_path("VERIFICATION_RESULT", "json"), result)
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
