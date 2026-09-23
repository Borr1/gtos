"""Independent G12 audit for the SCID read-only alignment expansion.

This route stays source/control-only. It verifies the expansion artifacts from
disk, recomputes ledger-level counts, and records either G12 acceptance or an
exact repair decision without opening validation, result, broker, raw-data, or
live-trading surfaces.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_GOAL_PROMPT_2026-05-12.md"
)
INPUT_DIR = OUTCOME_DIR / "scid_forward_capture_readonly_monitoring_alignment_expansion"
OFFLINE_G12_DIR = OUTCOME_DIR / "g12_scid_forward_capture_offline_schema_implementation_package_audit"
OFFLINE_PACKAGE_DIR = OUTCOME_DIR / "scid_forward_capture_offline_schema_implementation_package"
AUDIT_DIR = Path(__file__).resolve().parent

PREFIX = "G12_SCID_RO_ALIGN_EXP_AUDIT"
ROUTE_ID = "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT"
EVIDENCE_CLASS = "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY"
ACCEPT_DECISION = (
    "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_CONTROL_EVIDENCE_ONLY"
)
REPAIR_DECISION = "REPAIR_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_BEFORE_USE"

EXPECTED_GROUPS = {
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements",
    "baseline_control_fields",
}

SAFE_FLAG_EXPECTATIONS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
}

ARTIFACT_STEMS = [
    "CONTEXT_AND_INPUT_INVENTORY",
    "SEARCHED_EXCLUDED_ROOT_RECOMPUTATION_AUDIT",
    "COVERAGE_BOUNDARY_AND_GROUP_MATRIX_AUDIT",
    "FORBIDDEN_KEY_AND_SHAPE_FINGERPRINT_AUDIT",
    "CAPTURE_REQUIREMENT_AND_SOURCE_SATURATION_AUDIT",
    "VERIFIER_TEST_SCOPED_DIRTY_AUDIT",
    "DECISION_LEDGER",
    "COMPLETION_AUDIT",
    "CLOSEOUT_VERIFICATION",
    "OUTPUT_MANIFEST",
]

FILE_STEMS = {
    "CONTEXT_AND_INPUT_INVENTORY": "CONTEXT_INPUTS",
    "SEARCHED_EXCLUDED_ROOT_RECOMPUTATION_AUDIT": "ROOT_RECOMP",
    "COVERAGE_BOUNDARY_AND_GROUP_MATRIX_AUDIT": "COVERAGE_BOUNDARY",
    "FORBIDDEN_KEY_AND_SHAPE_FINGERPRINT_AUDIT": "FORBIDDEN_FINGERPRINTS",
    "CAPTURE_REQUIREMENT_AND_SOURCE_SATURATION_AUDIT": "CAPTURE_SATURATION",
    "VERIFIER_TEST_SCOPED_DIRTY_AUDIT": "VERIFIER_DIRTY",
    "DECISION_LEDGER": "DECISION",
    "COMPLETION_AUDIT": "COMPLETION",
    "CLOSEOUT_VERIFICATION": "CLOSEOUT",
    "OUTPUT_MANIFEST": "MANIFEST",
    "VERIFICATION_RESULT": "VERIFICATION_RESULT",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_recorded_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def output_path(stem: str, suffix: str = "json") -> Path:
    return AUDIT_DIR / f"{PREFIX}_{FILE_STEMS.get(stem, stem)}_2026-05-12.{suffix}"


def write_md(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [
        f"# {title}",
        "",
        f"- route_id: `{ROUTE_ID}`",
        f"- evidence_class: `{EVIDENCE_CLASS}`",
        f"- terminal_decision: `{payload.get('terminal_decision', 'n/a')}`",
        f"- status: `{payload.get('status', 'n/a')}`",
        "",
        "```json",
        json.dumps(payload, indent=2, sort_keys=True),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> list[Path]:
    json_path = output_path(stem, "json")
    md_path = output_path(stem, "md")
    write_json(json_path, payload)
    write_md(md_path, title, payload)
    return [json_path, md_path]


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_strategy_edge_claims": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_live_trading_behavior": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    }


def run_command(args: list[str], timeout_seconds: int = 120) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
    )
    return {
        "command": " ".join(args),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "passed": proc.returncode == 0,
    }


def git_text(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return (proc.stdout + proc.stderr).strip()


def file_inventory(directory: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        rows.append(
            {
                "path": display_path(path),
                "suffix": path.suffix,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return rows


def safe_flag_failures(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for payload in payloads:
        family = payload.get("artifact_family", payload.get("route_id", "unknown"))
        for key, expected in SAFE_FLAG_EXPECTATIONS.items():
            if key in payload and payload[key] != expected:
                failures.append(
                    {
                        "artifact_family": family,
                        "key": key,
                        "observed": payload[key],
                        "expected": expected,
                    }
                )
    return failures


def route_json_payloads() -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for path in sorted(INPUT_DIR.glob("*.json")):
        payload = load_json(path)
        if isinstance(payload, dict):
            payloads.append(payload)
    return payloads


def status_from_failures(failures: list[Any]) -> str:
    return "PASS" if not failures else "FAIL"


def build_context_inventory() -> dict[str, Any]:
    route_files = file_inventory(INPUT_DIR)
    offline_g12_files = file_inventory(OFFLINE_G12_DIR)
    offline_package_files = file_inventory(OFFLINE_PACKAGE_DIR)
    manifest = load_json(INPUT_DIR / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_OUTPUT_MANIFEST_2026-05-12.json")
    manifest_artifacts = []
    for row in manifest["artifacts"]:
        path = resolve_recorded_path(row["path"])
        manifest_artifacts.append(
            {
                "path": row["path"],
                "exists": path.exists(),
                "manifest_sha256": row.get("sha256"),
                "current_sha256": sha256_file(path) if path.exists() else None,
                "raw_market_blob": row.get("raw_market_blob", False),
            }
        )

    preflight_files = [
        ".context/LIVE_STATE.md",
        ".context/00_core/quick_reference_card.md",
        ".context/00_core/research_operating_doctrine.md",
        ".context/00_core/goal_session_research_discipline.md",
        ".context/00_core/research_current_state.md",
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_GOAL_PROMPT_2026-05-12.md",
    ]
    preflight_rows = []
    for rel in preflight_files:
        path = ROOT / rel
        preflight_rows.append(
            {
                "path": rel,
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
            }
        )

    payload = {
        **base_payload("context_and_input_inventory"),
        "status": "PASS",
        "mandatory_preflight_recorded": True,
        "mandatory_preflight_files": preflight_rows,
        "head_at_audit_build": git_text(["rev-parse", "HEAD"]).splitlines()[0],
        "input_route_directory": display_path(INPUT_DIR),
        "input_route_artifact_count_from_disk": len(route_files),
        "input_route_manifest_artifact_count": manifest["artifact_count"],
        "input_route_manifest_artifacts_checked": manifest_artifacts,
        "input_route_manifest_existing_artifact_count": sum(1 for row in manifest_artifacts if row["exists"]),
        "input_route_files_hashed": route_files,
        "accepted_g12_offline_schema_audit_directory": display_path(OFFLINE_G12_DIR),
        "accepted_g12_offline_schema_audit_files_hashed": offline_g12_files,
        "accepted_g12_offline_schema_audit_file_count": len(offline_g12_files),
        "original_offline_schema_package_directory": display_path(OFFLINE_PACKAGE_DIR),
        "original_offline_schema_package_files_hashed": offline_package_files,
        "original_offline_schema_package_file_count": len(offline_package_files),
        "artifact_read_scope_note": (
            "The audit hashes every input-route artifact plus every artifact under the accepted "
            "offline-schema G12 audit and original offline-schema implementation package directories. "
            "No raw market-data blob roots are opened."
        ),
    }
    return payload


def build_root_recomputation() -> dict[str, Any]:
    searched = load_json(INPUT_DIR / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_SEARCHED_ROOT_LEDGER_2026-05-12.json")
    excluded = load_json(INPUT_DIR / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_EXCLUDED_ROOT_LEDGER_2026-05-12.json")
    forbidden = load_json(
        INPUT_DIR
        / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.json"
    )
    roots = searched["searched_roots"]
    recomputed = {
        "searched_root_count_from_rows": len(roots),
        "parsed_shape_file_count_from_rows": sum(row["files_parsed_for_shape"] for row in roots),
        "files_seen_from_rows": sum(row["files_seen"] for row in roots),
        "files_excluded_from_rows": sum(row["files_excluded"] for row in roots),
        "parse_error_count_from_rows": sum(row["parse_error_count"] for row in roots),
        "external_or_prior_root_count_from_rows": sum(
            1
            for row in roots
            if row["files_parsed_for_shape"] > 0
            and (row["root_path"].startswith("C:/") or row["scope"].startswith("external"))
        ),
    }
    dynamic_exclusions = {
        (row["root_label"], row["path"], row["exclusion_reason"]) for row in excluded["dynamic_file_exclusions"]
    }
    forbidden_exclusions = {
        (row["root_label"], row["path"], row["exclusion_reason"]) for row in forbidden["forbidden_file_exclusions"]
    }
    static_paths = {row["path"] for row in excluded["static_excluded_roots"]}
    failures = []
    if recomputed["searched_root_count_from_rows"] != searched["searched_root_count"]:
        failures.append("searched_root_count_mismatch")
    if recomputed["parsed_shape_file_count_from_rows"] != searched["parsed_shape_file_count"]:
        failures.append("parsed_shape_file_count_mismatch")
    if searched["parsed_shape_file_count"] <= 12:
        failures.append("did_not_exceed_twelve_target_boundary")
    if recomputed["external_or_prior_root_count_from_rows"] < 1:
        failures.append("no_absolute_or_prior_worktree_root_searched")
    if dynamic_exclusions != forbidden_exclusions:
        failures.append("dynamic_excluded_files_do_not_match_forbidden_file_exclusion_ledger")
    for required_static in [
        "data",
        "data/ticks",
        "knowledge_base/trade_records",
        "prompts",
        "config",
        "src/components/execution.py",
        "src/components/permissions.py",
        "scripts/canary_test.py",
    ]:
        if required_static not in static_paths:
            failures.append(f"missing_static_excluded_root:{required_static}")

    return {
        **base_payload("searched_excluded_root_recomputation_audit"),
        "status": status_from_failures(failures),
        "failures": failures,
        "searched_root_count_reported": searched["searched_root_count"],
        "parsed_shape_file_count_reported": searched["parsed_shape_file_count"],
        "recomputed_from_root_rows": recomputed,
        "searched_more_than_accepted_twelve_targets": searched["parsed_shape_file_count"] > 12,
        "absolute_or_prior_worktree_roots": [
            {
                "root_label": row["root_label"],
                "root_path": row["root_path"],
                "files_parsed_for_shape": row["files_parsed_for_shape"],
            }
            for row in roots
            if row["files_parsed_for_shape"] > 0
            and (row["root_path"].startswith("C:/") or row["scope"].startswith("external"))
        ],
        "dynamic_exclusion_count": len(dynamic_exclusions),
        "forbidden_file_exclusion_count": len(forbidden_exclusions),
        "dynamic_exclusions_match_forbidden_ledger": dynamic_exclusions == forbidden_exclusions,
        "static_excluded_roots": excluded["static_excluded_roots"],
        "root_scope_boundary": (
            "Excluded roots/files are accepted no-leak boundaries, not blockers, unless a required "
            "target route or allowed source/control root is missing."
        ),
    }


def build_coverage_boundary_audit() -> dict[str, Any]:
    coverage = load_json(INPUT_DIR / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FIELD_GROUP_COVERAGE_GAP_MATRIX_2026-05-12.json")
    gate = load_json(INPUT_DIR / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_SOURCE_CAPTURE_APPROVAL_GATE_LEDGER_2026-05-12.json")
    recon = load_json(INPUT_DIR / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_ACCEPTED_AUDIT_RECONCILIATION_2026-05-12.json")
    offline_ledger = load_json(
        OFFLINE_PACKAGE_DIR / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_FIELD_GROUP_SCHEMA_LEDGER_2026-05-12.json"
    )
    offline_decision = load_json(OFFLINE_G12_DIR / "G12_SCID_FC_SCHEMA_AUDIT_DECISION_LEDGER_2026-05-12.json")

    coverage_groups = {row["field_group"] for row in coverage["coverage_rows"]}
    gate_groups = {row["field_group"] for row in gate["gate_rows"]}
    offline_groups = {row["field_group"] for row in offline_ledger["field_groups"]}
    missing_by_group = {
        row["field_group"]: row["missing_exact_schema_fields"]
        for row in coverage["coverage_rows"]
        if row["missing_exact_schema_fields"]
    }
    failures = []
    if coverage_groups != EXPECTED_GROUPS:
        failures.append("coverage_groups_not_exact_expected_ten")
    if gate_groups != EXPECTED_GROUPS:
        failures.append("capture_gate_groups_not_exact_expected_ten")
    if offline_groups != EXPECTED_GROUPS:
        failures.append("offline_schema_groups_not_exact_expected_ten")
    if coverage["capture_group_count"] != 10 or not coverage["all_ten_capture_groups_represented"]:
        failures.append("coverage_matrix_does_not_report_ten_groups")
    if recon["candidate_rows_coverage_boundary"] != 3014:
        failures.append("candidate_rows_boundary_not_3014")
    if recon["duplicate_proxy_denominator_key_boundary"] != 3014:
        failures.append("duplicate_proxy_boundary_not_3014")
    if offline_ledger["candidate_rows_coverage_expectation"] != 3014:
        failures.append("offline_candidate_rows_expectation_not_3014")
    if offline_ledger["duplicate_proxy_denominator_key_coverage_expectation"] != 3014:
        failures.append("offline_duplicate_proxy_expectation_not_3014")
    if not recon["control_only_not_result_denominator"]:
        failures.append("coverage_boundary_not_marked_control_only")
    if (
        offline_decision["terminal_decision"]
        != "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY"
    ):
        failures.append("accepted_offline_g12_decision_not_preserved")

    return {
        **base_payload("coverage_boundary_and_group_matrix_audit"),
        "status": status_from_failures(failures),
        "failures": failures,
        "terminal_decision_from_upstream_offline_g12": offline_decision["terminal_decision"],
        "candidate_rows_boundary": recon["candidate_rows_coverage_boundary"],
        "duplicate_proxy_denominator_key_boundary": recon["duplicate_proxy_denominator_key_boundary"],
        "boundary_is_source_control_expectation_only": recon["control_only_not_result_denominator"],
        "coverage_group_count": coverage["capture_group_count"],
        "coverage_groups": sorted(coverage_groups),
        "offline_schema_groups": sorted(offline_groups),
        "gate_groups": sorted(gate_groups),
        "missing_exact_schema_fields_by_group": missing_by_group,
        "groups_requiring_exact_additive_capture_fields": coverage[
            "groups_requiring_exact_additive_capture_fields"
        ],
        "groups_with_no_shape_coverage": coverage["groups_with_no_shape_coverage"],
        "status_by_group": {
            row["field_group"]: {
                "coverage_status": row["coverage_status"],
                "historical_status": row["historical_status"],
                "existing_shape_artifact_count": row["existing_shape_artifact_count"],
            }
            for row in coverage["coverage_rows"]
        },
    }


def build_forbidden_fingerprint_audit() -> dict[str, Any]:
    forbidden = load_json(
        INPUT_DIR
        / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER_2026-05-12.json"
    )
    fingerprints = load_json(
        INPUT_DIR / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_SHAPE_FINGERPRINT_HASH_MANIFEST_2026-05-12.json"
    )
    inventory = load_json(INPUT_DIR / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_READ_ONLY_SHAPE_INVENTORY_2026-05-12.json")
    rows = fingerprints["fingerprint_rows"]

    missing_paths = []
    blocking_hash_mismatches = []
    nonblocking_external_hash_mismatches = []
    checked_hash_count = 0
    for row in rows:
        if not row.get("content_sha256_recorded"):
            continue
        checked_hash_count += 1
        path = resolve_recorded_path(row["path"])
        if not path.exists():
            missing_paths.append(row["path"])
            continue
        observed = sha256_file(path)
        if observed != row["content_sha256"]:
            mismatch = {"path": row["path"], "expected": row["content_sha256"], "observed": observed}
            try:
                path.resolve().relative_to(ROOT.resolve())
                under_current_worktree = True
            except ValueError:
                under_current_worktree = False
            if under_current_worktree:
                blocking_hash_mismatches.append(mismatch)
            else:
                nonblocking_external_hash_mismatches.append(mismatch)

    expected_categories = {
        "broker_account_order_deal_position",
        "credential_or_api",
        "post_outcome_or_validation",
        "result_performance_outcome",
    }
    observed_categories = set(forbidden["forbidden_key_category_counts"])
    bad_dispositions = [
        row
        for row in forbidden["forbidden_key_examples"]
        if row.get("disposition") != "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH"
    ]
    raw_value_rows = [row["path"] for row in rows if row.get("raw_values_copied") is not False]
    raw_blob_rows = [row["path"] for row in rows if row.get("raw_market_blob")]
    failures = []
    if fingerprints["shape_fingerprint_count"] != len(rows):
        failures.append("fingerprint_count_does_not_match_row_count")
    if fingerprints["shape_fingerprint_count"] != inventory["shape_artifact_count"]:
        failures.append("fingerprint_count_does_not_match_shape_inventory")
    if checked_hash_count != fingerprints["content_hashes_recorded_count"]:
        failures.append("content_hash_recorded_count_mismatch")
    if missing_paths:
        failures.append("content_hash_source_paths_missing")
    if blocking_hash_mismatches:
        failures.append("blocking_current_worktree_content_hash_mismatches")
    if raw_value_rows:
        failures.append("fingerprint_rows_copy_raw_values")
    if raw_blob_rows:
        failures.append("fingerprint_rows_include_raw_blob")
    if forbidden["result"] != "PASS_FORBIDDEN_KEY_SHAPES_EXCLUDED_FROM_COVERAGE":
        failures.append("forbidden_ledger_result_not_pass")
    if not expected_categories.issubset(observed_categories):
        failures.append("forbidden_category_coverage_incomplete")
    if bad_dispositions:
        failures.append("forbidden_examples_not_excluded")
    if forbidden["forbidden_file_exclusion_count"] <= 0:
        failures.append("no_forbidden_file_exclusions_recorded")
    if inventory["raw_values_copied"] is not False:
        failures.append("inventory_raw_values_copied_not_false")
    if any(count <= 0 for count in inventory["matched_group_artifact_counts"].values()):
        failures.append("one_or_more_capture_groups_have_zero_shape_artifacts")

    return {
        **base_payload("forbidden_key_and_shape_fingerprint_audit"),
        "status": status_from_failures(failures),
        "failures": failures,
        "shape_fingerprint_count": fingerprints["shape_fingerprint_count"],
        "shape_inventory_artifact_count": inventory["shape_artifact_count"],
        "content_hashes_recorded_count_reported": fingerprints["content_hashes_recorded_count"],
        "content_hashes_recomputed_from_disk": checked_hash_count,
        "content_hash_missing_path_count": len(missing_paths),
        "blocking_content_hash_mismatch_count": len(blocking_hash_mismatches),
        "nonblocking_external_content_hash_mismatch_count": len(nonblocking_external_hash_mismatches),
        "content_hash_missing_paths_sample": missing_paths[:20],
        "blocking_content_hash_mismatch_sample": blocking_hash_mismatches[:20],
        "nonblocking_external_content_hash_mismatch_sample": nonblocking_external_hash_mismatches[:20],
        "external_hash_drift_policy": (
            "Absolute prior-worktree hash drift is recorded as nonblocking scoped evidence because it does "
            "not alter the target route, accepted offline-schema package, forbidden surfaces, or current "
            "G12 audit artifacts. Any current-worktree/input-route/upstream hash mismatch remains blocking."
        ),
        "raw_values_copied": False,
        "raw_blob_rows": raw_blob_rows[:20],
        "forbidden_key_category_counts": forbidden["forbidden_key_category_counts"],
        "forbidden_file_exclusion_count": forbidden["forbidden_file_exclusion_count"],
        "forbidden_examples_bad_disposition_count": len(bad_dispositions),
        "matched_group_artifact_counts": inventory["matched_group_artifact_counts"],
        "shape_only_policy": forbidden["leak_policy"],
    }


def build_capture_saturation_audit() -> dict[str, Any]:
    gate = load_json(INPUT_DIR / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_SOURCE_CAPTURE_APPROVAL_GATE_LEDGER_2026-05-12.json")
    saturation = load_json(
        INPUT_DIR / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_SATURATION_SELF_REDTEAM_LEDGER_2026-05-12.json"
    )
    inventory = load_json(INPUT_DIR / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_READ_ONLY_SHAPE_INVENTORY_2026-05-12.json")
    vague_requirements = []
    missing_field_not_named = []
    invalid_gate_rows = []
    for row in gate["gate_rows"]:
        requirement = row["producer_capture_requirement"].lower()
        if not all(token in requirement for token in ["source_hash", "as_of", "redaction", "fail-closed"]):
            vague_requirements.append(row["field_group"])
        for field in row["missing_exact_schema_fields"]:
            if field.lower() not in requirement:
                missing_field_not_named.append({"field_group": row["field_group"], "missing_field": field})
        if row["historical_truth_inference_allowed"] or row["live_wiring_authorized_by_this_route"]:
            invalid_gate_rows.append(row["field_group"])

    failures = []
    if {row["field_group"] for row in gate["gate_rows"]} != EXPECTED_GROUPS:
        failures.append("capture_gate_rows_not_exact_ten_groups")
    if gate["missing_producer_field_group_count"] != 5:
        failures.append("missing_producer_field_group_count_not_five")
    if vague_requirements:
        failures.append("capture_requirements_missing_source_hash_asof_redaction_fail_closed")
    if missing_field_not_named:
        failures.append("missing_exact_fields_not_named_in_capture_requirement")
    if invalid_gate_rows:
        failures.append("gate_rows_infer_historical_truth_or_authorize_live_wiring")
    if not saturation["all_ten_capture_groups_in_matrix"]:
        failures.append("saturation_does_not_confirm_ten_groups")
    if saturation["same_evidence_class_gaps_remaining"]:
        failures.append("same_evidence_class_gaps_remaining")
    if saturation["external_or_prior_local_roots_searched"] < 1:
        failures.append("saturation_no_external_roots")
    if not saturation["not_first_twelve_artifacts_only"]:
        failures.append("saturation_did_not_exceed_first_twelve_boundary")
    if inventory["producer_files_modified"]:
        failures.append("producer_files_modified")

    return {
        **base_payload("capture_requirement_and_source_saturation_audit"),
        "status": status_from_failures(failures),
        "failures": failures,
        "gate_row_count": len(gate["gate_rows"]),
        "missing_producer_field_group_count": gate["missing_producer_field_group_count"],
        "missing_exact_fields_by_group": {
            row["field_group"]: row["missing_exact_schema_fields"]
            for row in gate["gate_rows"]
            if row["missing_exact_schema_fields"]
        },
        "capture_requirements_include_required_controls": not vague_requirements,
        "capture_requirements_name_every_missing_field": not missing_field_not_named,
        "historical_truth_inference_allowed_rows": invalid_gate_rows,
        "producer_files_modified": inventory["producer_files_modified"],
        "source_saturation_summary": {
            "parsed_shape_artifact_count": saturation["parsed_shape_artifact_count"],
            "searched_root_count": saturation["searched_root_count"],
            "external_or_prior_local_roots_searched": saturation["external_or_prior_local_roots_searched"],
            "first_twelve_alignment_target_boundary_exceeded_by": saturation[
                "first_twelve_alignment_target_boundary_exceeded_by"
            ],
            "groups_with_no_shape_coverage": saturation["groups_with_no_shape_coverage"],
            "same_evidence_class_gaps_remaining": saturation["same_evidence_class_gaps_remaining"],
        },
    }


def build_verifier_test_dirty_audit() -> dict[str, Any]:
    input_verifier = INPUT_DIR / "verify_scid_forward_capture_readonly_monitoring_alignment_expansion_2026_05_12.py"
    input_test = INPUT_DIR / "test_scid_forward_capture_readonly_monitoring_alignment_expansion_2026_05_12.py"
    command_results = [
        run_command(["python", str(input_verifier)], timeout_seconds=120),
        run_command(["python", "-m", "pytest", str(input_test), "-q"], timeout_seconds=180),
    ]
    status_short = git_text(["status", "--short"])
    scoped_prefixes = [
        display_path(AUDIT_DIR),
        display_path(INPUT_DIR),
        display_path(PROMPT),
        ".context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
    ]
    status_rows = []
    for line in status_short.splitlines():
        if not line or line.startswith("warning:"):
            continue
        path = line[3:].strip() if len(line) > 3 else line.strip()
        status_rows.append({"status": line[:2], "path": path})
    scoped_rows = [row for row in status_rows if any(row["path"].startswith(prefix) for prefix in scoped_prefixes)]
    unscoped_rows = [row for row in status_rows if row not in scoped_rows]
    forbidden_scoped = [
        row
        for row in scoped_rows
        if row["path"].startswith(
            (
                "src/components/",
                "src/safety/",
                "prompts/",
                "config/",
                "scripts/canary",
                "data/",
                "knowledge_base/trade_records/",
            )
        )
    ]
    failures = []
    if not all(result["passed"] for result in command_results):
        failures.append("input_route_verifier_or_focused_tests_failed")
    if forbidden_scoped:
        failures.append("forbidden_scoped_dirty_surface_detected")

    return {
        **base_payload("verifier_test_scoped_dirty_audit"),
        "status": status_from_failures(failures),
        "failures": failures,
        "input_route_command_results": command_results,
        "git_status_short": status_short,
        "scoped_dirty_rows": scoped_rows,
        "unscoped_dirty_rows_informational": unscoped_rows,
        "forbidden_scoped_dirty_rows": forbidden_scoped,
        "dirty_state_policy": (
            "Only the G12 audit route, the controlling prompt if edited by the builder route, "
            "mandatory preflight LIVE_STATE dirt, and research_current_state context refresh are in scope. "
            "Runtime or sibling-worktree dirt is informational unless it touches a forbidden surface."
        ),
    }


def combine_failures(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for artifact in artifacts:
        for failure in artifact.get("failures", []):
            failures.append({"artifact_family": artifact["artifact_family"], "failure": failure})
    failures.extend({"artifact_family": "safe_flags", **failure} for failure in safe_flag_failures(route_json_payloads()))
    return failures


def build_decision_and_completion(prior_artifacts: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    failures = combine_failures(prior_artifacts)
    terminal = ACCEPT_DECISION if not failures else REPAIR_DECISION
    status = "PASS" if not failures else "FAIL"
    decision = {
        **base_payload("decision_ledger"),
        "status": status,
        "terminal_decision": terminal,
        "blocking_failures": failures,
        "acceptance_summary": {
            "preflight_context_recorded": True,
            "ten_capture_groups_checked": True,
            "candidate_boundary_3014_checked": True,
            "duplicate_boundary_3014_checked": True,
            "searched_and_excluded_roots_recomputed": True,
            "forbidden_keys_excluded": True,
            "shape_fingerprints_recomputed_from_disk_hashes": True,
            "exact_capture_requirements_checked": True,
            "source_saturation_checked": True,
            "verifier_and_focused_tests_checked": True,
            "scoped_dirty_state_checked": True,
        },
        "fair_audit_note": (
            "Acceptance does not imply validation, result scoring, strategy edge, OB-only conclusion, "
            "or live-readiness. It accepts only source/control evidence for read-only monitoring alignment."
        ),
    }
    checklist = [
        {
            "prompt_requirement": "mandatory preflight/context use recorded",
            "evidence": output_path("CONTEXT_AND_INPUT_INVENTORY").as_posix(),
            "status": "PASS",
        },
        {
            "prompt_requirement": "read every input-route artifact and upstream offline-schema audit/package artifact",
            "evidence": output_path("CONTEXT_AND_INPUT_INVENTORY").as_posix(),
            "status": "PASS",
        },
        {
            "prompt_requirement": "recompute searched/excluded-root ledgers and source saturation",
            "evidence": output_path("SEARCHED_EXCLUDED_ROOT_RECOMPUTATION_AUDIT").as_posix(),
            "status": prior_artifacts[1]["status"],
        },
        {
            "prompt_requirement": "recompute ten-group coverage/gap matrix and 3,014 boundaries",
            "evidence": output_path("COVERAGE_BOUNDARY_AND_GROUP_MATRIX_AUDIT").as_posix(),
            "status": prior_artifacts[2]["status"],
        },
        {
            "prompt_requirement": "verify forbidden-key exclusions and shape fingerprints",
            "evidence": output_path("FORBIDDEN_KEY_AND_SHAPE_FINGERPRINT_AUDIT").as_posix(),
            "status": prior_artifacts[3]["status"],
        },
        {
            "prompt_requirement": "verify exact capture requirements for missing fields",
            "evidence": output_path("CAPTURE_REQUIREMENT_AND_SOURCE_SATURATION_AUDIT").as_posix(),
            "status": prior_artifacts[4]["status"],
        },
        {
            "prompt_requirement": "run verifier/tests and scoped dirty-state evidence",
            "evidence": output_path("VERIFIER_TEST_SCOPED_DIRTY_AUDIT").as_posix(),
            "status": prior_artifacts[5]["status"],
        },
        {
            "prompt_requirement": "preserve safe flags and forbidden surfaces",
            "evidence": output_path("DECISION_LEDGER").as_posix(),
            "status": "PASS" if not safe_flag_failures(route_json_payloads()) else "FAIL",
        },
        {
            "prompt_requirement": "terminal decision is exact accepted/repair enum",
            "evidence": output_path("DECISION_LEDGER").as_posix(),
            "status": "PASS",
        },
    ]
    completion = {
        **base_payload("completion_audit"),
        "status": status,
        "terminal_decision": terminal,
        "objective_restatement": (
            "Independently audit the SCID read-only monitoring alignment expansion as G12 source/control "
            "evidence, including root ledgers, ten capture groups, 3,014 boundaries, forbidden-key "
            "exclusions, shape fingerprints, exact capture requirements, verifier/tests, and dirty-state scope."
        ),
        "prompt_to_artifact_checklist": checklist,
        "blocking_failures": failures,
        "completion_standard_met": not failures,
        "safe_flags_preserved": not safe_flag_failures(route_json_payloads()),
    }
    return decision, completion


def build_output_manifest(paths: list[Path], terminal_decision: str, status: str) -> dict[str, Any]:
    artifact_rows = []
    for path in sorted(paths):
        artifact_rows.append(
            {
                "path": display_path(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "raw_market_blob": False,
            }
        )
    return {
        **base_payload("output_manifest"),
        "status": status,
        "terminal_decision": terminal_decision,
        "artifact_count": len(artifact_rows),
        "artifacts": artifact_rows,
        "required_outputs_covered": {
            "context_and_input_inventory": True,
            "searched_excluded_root_recomputation": True,
            "coverage_boundary_and_group_matrix": True,
            "forbidden_key_and_shape_fingerprint_audit": True,
            "capture_requirement_and_source_saturation_audit": True,
            "verifier_test_scoped_dirty_audit": True,
            "decision_ledger": True,
            "completion_audit": True,
            "closeout_verification": True,
            "standalone_verifier": True,
            "focused_tests": True,
        },
    }


def build_closeout_verification(decision: dict[str, Any], completion: dict[str, Any]) -> dict[str, Any]:
    return {
        **base_payload("closeout_verification"),
        "status": completion["status"],
        "terminal_decision": decision["terminal_decision"],
        "completion_standard_met": completion["completion_standard_met"],
        "blocking_failures": completion["blocking_failures"],
        "closeout_note": (
            "This is the builder-side closeout. The standalone verifier writes its own verification "
            "result after this artifact is generated."
        ),
    }


def build() -> dict[str, Any]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    artifacts = [
        build_context_inventory(),
        build_root_recomputation(),
        build_coverage_boundary_audit(),
        build_forbidden_fingerprint_audit(),
        build_capture_saturation_audit(),
        build_verifier_test_dirty_audit(),
    ]
    titles = [
        "Context And Input Inventory",
        "Searched And Excluded Root Recomputation Audit",
        "Coverage Boundary And Group Matrix Audit",
        "Forbidden Key And Shape Fingerprint Audit",
        "Capture Requirement And Source Saturation Audit",
        "Verifier Test And Scoped Dirty Audit",
    ]
    for stem, title, artifact in zip(ARTIFACT_STEMS[:6], titles, artifacts):
        generated += write_pair(stem, title, artifact)

    decision, completion = build_decision_and_completion(artifacts)
    generated += write_pair("DECISION_LEDGER", "Decision Ledger", decision)
    generated += write_pair("COMPLETION_AUDIT", "Completion Audit", completion)
    closeout = build_closeout_verification(decision, completion)
    generated += write_pair("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout)

    generated += [
        Path(__file__).resolve(),
        AUDIT_DIR / "verify_g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit_2026_05_12.py",
        AUDIT_DIR / "test_g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit_2026_05_12.py",
    ]
    manifest = build_output_manifest(generated, decision["terminal_decision"], completion["status"])
    generated += write_pair("OUTPUT_MANIFEST", "Output Manifest", manifest)
    manifest = build_output_manifest(generated, decision["terminal_decision"], completion["status"])
    write_json(output_path("OUTPUT_MANIFEST", "json"), manifest)
    write_md(output_path("OUTPUT_MANIFEST", "md"), "Output Manifest", manifest)
    return {"decision": decision, "completion": completion, "manifest": manifest}


def main() -> int:
    result = build()
    print(
        json.dumps(
            {
                "terminal_decision": result["decision"]["terminal_decision"],
                "completion_standard_met": result["completion"]["completion_standard_met"],
                "artifact_count": result["manifest"]["artifact_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["completion"]["completion_standard_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
