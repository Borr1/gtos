"""Verify SCID read-only monitoring alignment expansion artifacts."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
BUILDER_PATH = HERE / "build_scid_forward_capture_readonly_monitoring_alignment_expansion_2026_05_12.py"
SPEC = importlib.util.spec_from_file_location("scid_readonly_alignment_builder", BUILDER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load builder from {BUILDER_PATH}")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)

ROOT: Path = builder.ROOT
ROUTE_DIR: Path = builder.ROUTE_DIR
PREFIX: str = builder.PREFIX
DATE_TAG: str = builder.DATE_TAG
ROUTE_REL = builder.display_path(ROUTE_DIR)
G12_PROMPT_REL = builder.display_path(builder.G12_PROMPT)


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
        if not line.strip() or len(line) < 4:
            continue
        rows.append({"status": line[:2].strip(), "path": line[3:].replace("\\", "/")})
    return rows


def assert_true(checks: list[dict[str, Any]], name: str, condition: bool, detail: Any = None) -> None:
    checks.append({"check": name, "status": "PASS" if condition else "FAIL", "detail": detail})


def required_files() -> list[Path]:
    stems = [
        "CONTEXT_ANCHOR",
        "ACCEPTED_AUDIT_RECONCILIATION",
        "SEARCHED_ROOT_LEDGER",
        "EXCLUDED_ROOT_LEDGER",
        "READ_ONLY_SHAPE_INVENTORY",
        "FIELD_GROUP_COVERAGE_GAP_MATRIX",
        "FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER",
        "SHAPE_FINGERPRINT_HASH_MANIFEST",
        "SOURCE_CAPTURE_APPROVAL_GATE_LEDGER",
        "SATURATION_SELF_REDTEAM_LEDGER",
        "DECISION_LEDGER",
        "COMPLETION_AUDIT",
        "CLOSEOUT_VERIFICATION",
        "OUTPUT_MANIFEST",
    ]
    files = [
        BUILDER_PATH,
        Path(__file__).resolve(),
        HERE / "test_scid_forward_capture_readonly_monitoring_alignment_expansion_2026_05_12.py",
        builder.G12_PROMPT,
    ]
    for stem in stems:
        files.extend([output_path(stem, "json"), output_path(stem, "md")])
    return files


def verify_required_files(checks: list[dict[str, Any]]) -> None:
    missing = [builder.display_path(path) for path in required_files() if not path.exists()]
    assert_true(checks, "required_files_exist", not missing, {"missing": missing, "required_count": len(required_files())})


def verify_safe_flags(checks: list[dict[str, Any]]) -> None:
    failures = []
    for path in sorted(ROUTE_DIR.glob(f"{PREFIX}_*.json")):
        if path.name.endswith(f"_VERIFICATION_RESULT_{DATE_TAG}.json"):
            continue
        payload = load_json(path)
        if not isinstance(payload, dict):
            continue
        expected = {
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
            "opens_live_trading_behavior": False,
            "opens_raw_market_data_blob_commit": False,
            "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        }
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                failures.append({"path": builder.display_path(path), "key": key, "value": payload.get(key)})
    assert_true(checks, "safe_flags_closed_in_route_json", not failures, failures)


def verify_context_and_reconciliation(checks: list[dict[str, Any]]) -> None:
    context = load_json(output_path("CONTEXT_ANCHOR"))
    recon = load_json(output_path("ACCEPTED_AUDIT_RECONCILIATION"))
    assert_true(
        checks,
        "mandatory_context_recorded",
        all(context["mandatory_context_files_read_after_preflight"].values()),
        context["mandatory_context_files_read_after_preflight"],
    )
    assert_true(
        checks,
        "accepted_boundary_preserves_3014_and_ten_groups",
        context["accepted_boundary_preserved"]["candidate_input_row_ids"] == 3014
        and context["accepted_boundary_preserved"]["duplicate_proxy_denominator_keys"] == 3014
        and len(context["accepted_boundary_preserved"]["capture_groups"]) == 10,
        context["accepted_boundary_preserved"],
    )
    assert_true(
        checks,
        "g12_offline_decision_preserved",
        recon["accepted_g12_offline_terminal_decision"]
        == "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
        recon["accepted_g12_offline_terminal_decision"],
    )


def verify_search_and_inventory(checks: list[dict[str, Any]]) -> None:
    searched = load_json(output_path("SEARCHED_ROOT_LEDGER"))
    inventory = load_json(output_path("READ_ONLY_SHAPE_INVENTORY"))
    saturation = load_json(output_path("SATURATION_SELF_REDTEAM_LEDGER"))
    fingerprints = load_json(output_path("SHAPE_FINGERPRINT_HASH_MANIFEST"))
    parsed_roots = [root for root in searched["searched_roots"] if root["files_parsed_for_shape"] > 0]
    external_parsed = [
        root
        for root in parsed_roots
        if root["root_path"].startswith("C:/tmp/gtos_otb/")
        or root["root_path"].startswith("C:/Users/MSI/Documents/ai-trading-agent")
    ]
    assert_true(
        checks,
        "searched_more_than_first_twelve_artifacts",
        searched["parsed_shape_file_count"] > 12,
        {"searched_root_count": searched["searched_root_count"], "parsed_shape_file_count": searched["parsed_shape_file_count"]},
    )
    assert_true(
        checks,
        "searched_external_or_prior_roots",
        len(external_parsed) >= 1,
        {"external_parsed_root_count": len(external_parsed), "external_root_labels": [root["root_label"] for root in external_parsed]},
    )
    assert_true(
        checks,
        "shape_inventory_rows_match_count",
        inventory["shape_artifact_count"] == fingerprints["shape_fingerprint_count"],
        {
            "shape_artifact_count": inventory["shape_artifact_count"],
            "shape_fingerprint_count": fingerprints["shape_fingerprint_count"],
        },
    )
    assert_true(
        checks,
        "shape_inventory_shape_only",
        inventory["raw_values_copied"] is False and inventory["producer_files_modified"] == [],
        {
            "raw_values_copied": inventory["raw_values_copied"],
            "producer_files_modified": inventory["producer_files_modified"],
            "artifact_rows_sample_count": inventory["artifact_rows_sample_count"],
        },
    )
    fingerprint_failures = [
        row["path"]
        for row in inventory["artifact_rows_sample"]
        if not row.get("shape_fingerprint_sha256") or not row.get("safe_shape_fingerprint_sha256") or row.get("raw_values_copied")
    ]
    assert_true(checks, "every_inventory_sample_row_has_shape_fingerprint", not fingerprint_failures, fingerprint_failures[:20])
    assert_true(
        checks,
        "saturation_prevents_shallow_inventory",
        saturation["not_first_twelve_artifacts_only"]
        and saturation["external_or_prior_local_roots_searched"] >= 1
        and saturation["all_ten_capture_groups_in_matrix"],
        saturation,
    )


def verify_coverage_and_gates(checks: list[dict[str, Any]]) -> None:
    coverage = load_json(output_path("FIELD_GROUP_COVERAGE_GAP_MATRIX"))
    gates = load_json(output_path("SOURCE_CAPTURE_APPROVAL_GATE_LEDGER"))
    observed_groups = sorted(row["field_group"] for row in coverage["coverage_rows"])
    expected_groups = sorted(builder.CAPTURE_GROUPS)
    assert_true(checks, "coverage_matrix_has_all_ten_groups", observed_groups == expected_groups, observed_groups)
    assert_true(checks, "capture_group_count_ten", coverage["capture_group_count"] == 10, coverage["capture_group_count"])
    gate_groups = sorted(row["field_group"] for row in gates["gate_rows"])
    assert_true(checks, "capture_gate_rows_for_all_groups", gate_groups == expected_groups, gate_groups)
    bad_gate_rows = [
        row
        for row in gates["gate_rows"]
        if row["historical_truth_inference_allowed"] or row["live_wiring_authorized_by_this_route"]
    ]
    assert_true(checks, "capture_gates_do_not_infer_historical_truth_or_live_wiring", not bad_gate_rows, bad_gate_rows)
    vague_requirements = [
        row["field_group"]
        for row in gates["gate_rows"]
        if "source_hash" not in row["producer_capture_requirement"] or "as_of" not in row["producer_capture_requirement"]
    ]
    assert_true(checks, "capture_requirements_include_source_hash_and_asof", not vague_requirements, vague_requirements)


def verify_forbidden_and_fingerprints(checks: list[dict[str, Any]]) -> None:
    forbidden = load_json(output_path("FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER"))
    excluded = load_json(output_path("EXCLUDED_ROOT_LEDGER"))
    fingerprints = load_json(output_path("SHAPE_FINGERPRINT_HASH_MANIFEST"))
    assert_true(
        checks,
        "forbidden_ledger_has_exclusions",
        forbidden["forbidden_file_exclusion_count"] > 0
        and forbidden["result"] == "PASS_FORBIDDEN_KEY_SHAPES_EXCLUDED_FROM_COVERAGE",
        forbidden,
    )
    assert_true(checks, "excluded_root_ledger_nonempty", len(excluded["static_excluded_roots"]) >= 5, excluded)
    assert_true(
        checks,
        "fingerprint_manifest_count_positive",
        fingerprints["shape_fingerprint_count"] > 12 and fingerprints["raw_values_copied"] is False,
        fingerprints["shape_fingerprint_count"],
    )
    raw_blob_rows = [row for row in fingerprints["fingerprint_rows"] if str(row["path"]).endswith(tuple(builder.RAW_BLOB_SUFFIXES))]
    assert_true(checks, "fingerprint_manifest_no_raw_blob_rows", not raw_blob_rows, raw_blob_rows[:20])


def verify_prompt_and_manifest(checks: list[dict[str, Any]]) -> None:
    prompt_text = builder.G12_PROMPT.read_text(encoding="utf-8") if builder.G12_PROMPT.exists() else ""
    required_phrases = [
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
        "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_CONTROL_EVIDENCE_ONLY",
        "REPAIR_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_BEFORE_USE",
        "broker account/order/history/deal/position evidence",
        "raw market-data blobs",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in prompt_text]
    assert_true(checks, "g12_prompt_contains_required_boundaries_and_decisions", not missing, missing)
    manifest = load_json(output_path("OUTPUT_MANIFEST"))
    paths = {row["path"] for row in manifest["artifacts"]}
    assert_true(checks, "output_manifest_includes_g12_prompt", G12_PROMPT_REL in paths, G12_PROMPT_REL)
    raw_manifest = [row for row in manifest["artifacts"] if row["raw_market_blob"]]
    assert_true(checks, "output_manifest_no_raw_market_blobs", not raw_manifest, raw_manifest)


def verify_md_json_pairs(checks: list[dict[str, Any]]) -> None:
    mismatches = []
    for json_path in sorted(ROUTE_DIR.glob(f"{PREFIX}_*.json")):
        if json_path.name.endswith(f"_VERIFICATION_RESULT_{DATE_TAG}.json"):
            continue
        md_path = json_path.with_suffix(".md")
        if not md_path.exists():
            continue
        if load_json(json_path) != md_json_payload(md_path):
            mismatches.append(builder.display_path(json_path))
    assert_true(checks, "json_md_pairs_match", not mismatches, mismatches)


def verify_scoped_git_surface(checks: list[dict[str, Any]]) -> None:
    rows = git_status()
    allowed_prefixes = (
        f"{ROUTE_REL}/",
        G12_PROMPT_REL,
        ".context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
    )
    scoped = [row for row in rows if any(row["path"].startswith(prefix) for prefix in allowed_prefixes)]
    forbidden = [
        row
        for row in scoped
        if row["path"].startswith(("src/", "config/", "prompts/", "scripts/", "shadow_logs/", "data/"))
        or row["path"].endswith(tuple(builder.RAW_BLOB_SUFFIXES))
    ]
    assert_true(
        checks,
        "scoped_git_surface_only_route_prompt_context",
        not forbidden,
        {"scoped_entries": scoped, "forbidden_scoped": forbidden},
    )


def verify() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    verify_required_files(checks)
    verify_safe_flags(checks)
    verify_context_and_reconciliation(checks)
    verify_search_and_inventory(checks)
    verify_coverage_and_gates(checks)
    verify_forbidden_and_fingerprints(checks)
    verify_prompt_and_manifest(checks)
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
        "terminal_decision": "VERIFIED_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_READY_FOR_G12_AUDIT"
        if not failed
        else "REPAIR_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_BEFORE_G12_AUDIT",
        "ok": not failed,
        "check_count": len(checks),
        "failed_check_count": len(failed),
        "failed_checks": failed,
        "checks": checks,
    }
    write_json(output_path("VERIFICATION_RESULT"), result)
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
