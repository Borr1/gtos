"""Verifier for the SCID Blocked15 POI/bounds contract repair route."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import build_scid_blocked15_poi_bounds_source_capture_contract_repair_2026_05_13 as builder


RESULT_PATH = builder.OUTPUTS["verification_result_json"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_or_jsonl(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [load_json(path)]


def parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def walk_keys(value: Any, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, subvalue in value.items():
            key_str = str(key)
            full = f"{prefix}.{key_str}" if prefix else key_str
            keys.append(full)
            keys.extend(walk_keys(subvalue, full))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            keys.extend(walk_keys(item, f"{prefix}[{index}]"))
    return keys


def has_forbidden_key(row: dict[str, Any]) -> list[str]:
    forbidden = []
    for key in walk_keys(row):
        lowered = key.lower()
        if any(fragment in lowered for fragment in builder.FORBIDDEN_KEY_FRAGMENTS):
            allowed = {
                "redaction_policy_id",
                "forbidden_value_policy_id",
                "fixture_expected_issue_codes",
                "opens_broker_account_order_history_deal_position_evidence",
            } | set(builder.SAFE_FLAGS)
            if key.split(".")[-1] not in allowed:
                forbidden.append(key)
    return forbidden


def validate_poi_fixture_row(
    row: dict[str, Any],
    candidate_duplicate_registry: dict[str, str],
) -> dict[str, Any]:
    issues: list[str] = []
    missing = [field for field in builder.REQUIRED_ROW_FIELDS if field not in row]
    if missing:
        issues.append("missing_required_fields")

    if row.get("schema_version") != builder.SCHEMA_VERSION:
        issues.append("schema_version_mismatch")
    if row.get("route_id") != builder.ROUTE_ID:
        issues.append("route_id_mismatch")
    if row.get("evidence_class") != builder.EVIDENCE_CLASS:
        issues.append("evidence_class_mismatch")

    for flag, expected in builder.SAFE_FLAGS.items():
        if row.get(flag) != expected:
            issues.append(f"safe_flag_mismatch:{flag}")

    forbidden = has_forbidden_key(row)
    if forbidden:
        issues.append("forbidden_key")

    decision_dt = parse_dt(row.get("decision_asof_utc"))
    source_dt = parse_dt(row.get("source_observed_asof_utc"))
    mso_dt = parse_dt(row.get("mso_snapshot_asof_utc"))
    if decision_dt is None or source_dt is None or source_dt > decision_dt:
        issues.append("source_after_decision_asof")
    if decision_dt is None or mso_dt is None or mso_dt > decision_dt:
        issues.append("mso_after_decision_asof")

    for ref in row.get("source_bar_refs") or []:
        bar_end = parse_dt(ref.get("bar_end_exclusive_utc"))
        if decision_dt is None or bar_end is None or bar_end > decision_dt:
            issues.append("source_bar_after_decision_asof")
        if any(key in ref for key in ("open", "high", "low", "close", "volume", "raw_ohlc")):
            issues.append("raw_market_blob_in_source_bar_ref")

    if row.get("poi_type_enum_ob_fvg_breaker_swing_other_none") not in builder.POI_ENUM_V1:
        issues.append("bad_poi_type_enum")
    if row.get("poi_mechanism_family") not in builder.POI_MECHANISM_FAMILIES:
        issues.append("bad_poi_mechanism_family")

    if row.get("field_status") == "POI_BOUNDS_CAPTURED_SOURCE_SAFE":
        lower = row.get("poi_lower_bound")
        upper = row.get("poi_upper_bound")
        if not isinstance(lower, (int, float)) or not isinstance(upper, (int, float)):
            issues.append("missing_poi_bounds")
        elif lower > upper:
            issues.append("inverted_poi_bounds")

    source_bar_refs = row.get("source_bar_refs") or []
    if row.get("source_bar_set_hash") != builder.stable_hash(source_bar_refs):
        issues.append("source_bar_set_hash_mismatch")

    commitment = row.get("mso_snapshot_commitment")
    if not isinstance(commitment, dict) or row.get("mso_snapshot_hash") != builder.stable_hash(commitment):
        issues.append("mso_snapshot_hash_mismatch")
    else:
        selected = row.get("selected_poi_id")
        detected = commitment.get("detected_poi_refs") or []
        selected_rows = [poi for poi in detected if poi.get("poi_id") == selected]
        if row.get("field_status") == "POI_BOUNDS_CAPTURED_SOURCE_SAFE" and not selected_rows:
            issues.append("selected_poi_missing_from_snapshot")
        source_ids = {ref.get("source_bar_id") for ref in source_bar_refs}
        for poi in selected_rows:
            if not set(poi.get("poi_source_bar_ids") or []).issubset(source_ids):
                issues.append("poi_source_bar_ids_not_in_source_refs")
            detect_dt = parse_dt(poi.get("poi_detection_asof_utc"))
            if decision_dt is None or detect_dt is None or detect_dt > decision_dt:
                issues.append("poi_detection_after_decision_asof")

    expected_source_hash = builder.stable_hash({k: v for k, v in row.items() if k != "source_hash"})
    if row.get("source_hash_policy") == "STRICT_SHA256_REQUIRED" and row.get("source_hash") != expected_source_hash:
        issues.append("source_hash_mismatch")

    candidate_id = str(row.get("candidate_input_row_id"))
    duplicate_key = str(row.get("duplicate_proxy_denominator_key"))
    if candidate_id:
        prior = candidate_duplicate_registry.get(candidate_id)
        if prior is None:
            candidate_duplicate_registry[candidate_id] = duplicate_key
        elif prior != duplicate_key:
            issues.append("duplicate_key_drift")

    return {
        "ok": not issues,
        "issues": sorted(set(issues)),
        "missing_fields": missing,
        "forbidden_keys": forbidden,
    }


def git_status_paths() -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "status", "--short"],
            cwd=builder.REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return []
    return [line[3:].replace("\\", "/") for line in proc.stdout.splitlines() if len(line) >= 4]


def verify() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    manifest = load_json(builder.OUTPUTS["output_manifest_json"])
    source_contract = load_json(builder.OUTPUTS["source_logger_contract_json"])
    card_ledger = load_json(builder.OUTPUTS["card_requirement_ledger_json"])
    mso_schema = load_json(builder.OUTPUTS["mso_schema_json"])
    fixture_manifest = load_json(builder.OUTPUTS["fixture_manifest_json"])
    instruction = load_json(builder.OUTPUTS["instruction_coverage_json"])
    saturation = load_json(builder.OUTPUTS["saturation_json"])
    completion = load_json(builder.OUTPUTS["completion_audit_json"])

    if source_contract.get("source_logger_id") != "source_safe_mso_snapshot_and_poi_logger":
        issues.append({"code": "source_logger_id_mismatch", "detail": source_contract.get("source_logger_id")})
    source_field_names = {field["name"] for field in source_contract.get("field_contracts", [])}
    missing_contract_fields = set(builder.REQUIRED_ROW_FIELDS) - source_field_names
    if missing_contract_fields:
        issues.append({"code": "missing_contract_fields", "detail": sorted(missing_contract_fields)})
    if set(source_contract.get("target_cards", [])) != builder.TARGET_CARD_ID_SET:
        issues.append({"code": "target_card_set_mismatch", "detail": source_contract.get("target_cards")})
    if not set(builder.POI_MECHANISM_FAMILIES) <= set(source_contract.get("poi_mechanism_families_v2", [])):
        issues.append({"code": "poi_mechanism_family_coverage", "detail": source_contract.get("poi_mechanism_families_v2")})

    card_ids = [row.get("card_id") for row in card_ledger.get("requirements", [])]
    if tuple(card_ids) != builder.TARGET_CARD_IDS:
        issues.append({"code": "card_requirement_order_or_count", "detail": card_ids})
    for row in card_ledger.get("requirements", []):
        if row.get("card_may_score_results_now") is not False:
            issues.append({"code": "card_result_gate_opened", "detail": row.get("card_id")})
        if row.get("accepted_40_denominator_unblocked_now") is not False:
            issues.append({"code": "denominator_unblocked", "detail": row.get("card_id")})
        if "poi_type_bounds_source" not in row.get("required_capture_groups", []):
            issues.append({"code": "target_card_missing_poi_dependency", "detail": row.get("card_id")})

    if mso_schema.get("raw_market_blob_policy") != "Only source pointers and hashes are committed in this route; raw OHLC/tick/depth blobs are forbidden.":
        issues.append({"code": "raw_market_blob_policy_missing", "detail": mso_schema.get("raw_market_blob_policy")})
    if "detected_poi_refs" not in mso_schema.get("mso_snapshot_commitment_schema", {}):
        issues.append({"code": "mso_schema_missing_detected_poi_refs", "detail": mso_schema.get("mso_snapshot_commitment_schema")})

    expected_fixture_coverage = fixture_manifest.get("coverage", {})
    uncovered = [name for name, covered in expected_fixture_coverage.items() if not covered]
    if uncovered:
        issues.append({"code": "fixture_coverage_false", "detail": uncovered})

    registry: dict[str, str] = {}
    fixture_failures = []
    for fixture_row in fixture_manifest.get("fixture_rows", []):
        path = builder.REPO_ROOT / fixture_row["path"]
        if not path.exists():
            fixture_failures.append({"path": fixture_row["path"], "issues": ["fixture_missing"]})
            continue
        if fixture_row.get("sha256") != builder.file_sha256(path):
            fixture_failures.append({"path": fixture_row["path"], "issues": ["fixture_manifest_hash_mismatch"]})
            continue
        for row in load_json_or_jsonl(path):
            result = validate_poi_fixture_row(row, registry)
            expected = row.get("fixture_expected_status")
            expected_issues = set(row.get("fixture_expected_issue_codes") or [])
            result_issues = set(result["issues"])
            if expected == "PASS" and not result["ok"]:
                fixture_failures.append({"path": fixture_row["path"], "issues": result["issues"]})
            if expected == "FAIL":
                if result["ok"]:
                    fixture_failures.append({"path": fixture_row["path"], "issues": ["expected_failure_passed"]})
                missing_expected = expected_issues - result_issues
                if missing_expected:
                    fixture_failures.append(
                        {
                            "path": fixture_row["path"],
                            "issues": result["issues"],
                            "missing_expected_issues": sorted(missing_expected),
                        }
                    )
    if fixture_failures:
        issues.append({"code": "fixture_validation_failure", "detail": fixture_failures})

    if not instruction.get("all_required_items_covered"):
        issues.append({"code": "instruction_coverage_incomplete", "detail": instruction.get("rows")})
    unresolved_saturation = [row for row in saturation.get("rows", []) if row.get("status") not in {"RESOLVED", "REDUCED_TO_EXACT_CAPTURE_REQUIREMENT"}]
    if unresolved_saturation:
        issues.append({"code": "saturation_unresolved", "detail": unresolved_saturation})
    if not completion.get("completion_standard_met"):
        issues.append({"code": "completion_standard_not_met", "detail": completion})

    raw_extensions = {".scid", ".depth", ".parquet", ".csv", ".bin", ".dly"}
    raw_manifest_paths = [
        artifact["path"]
        for artifact in manifest.get("artifacts", [])
        if Path(artifact["path"]).suffix.lower() in raw_extensions
    ]
    if raw_manifest_paths:
        issues.append({"code": "raw_market_blob_in_manifest", "detail": raw_manifest_paths})

    for artifact in manifest.get("artifacts", []):
        path = builder.REPO_ROOT / artifact["path"]
        if not path.exists():
            issues.append({"code": "manifest_artifact_missing", "detail": artifact})
        elif artifact.get("key") in {"output_manifest_json", "output_manifest_md", "verification_result_json"}:
            continue
        elif artifact.get("sha256") != builder.file_sha256(path):
            issues.append({"code": "manifest_hash_mismatch", "detail": artifact})

    for artifact in (
        source_contract,
        card_ledger,
        mso_schema,
        fixture_manifest,
        instruction,
        saturation,
        completion,
        manifest,
    ):
        for flag, expected in builder.SAFE_FLAGS.items():
            if artifact.get(flag) != expected:
                issues.append({"code": "artifact_safe_flag_mismatch", "detail": {"flag": flag, "value": artifact.get(flag)}})

    dirty_paths = git_status_paths()
    forbidden_dirty = [
        path
        for path in dirty_paths
        if path.startswith(("src/", "config/", "prompts/", "scripts/canary_fixtures/"))
    ]
    if forbidden_dirty:
        issues.append({"code": "forbidden_surface_dirty", "detail": forbidden_dirty})

    result = {
        "ok": not issues,
        "route_id": builder.ROUTE_ID,
        "evidence_class": builder.EVIDENCE_CLASS,
        "terminal_decision": (
            "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_READY_FOR_G12_AUDIT"
            if not issues
            else "REPAIR_REQUIRED"
        ),
        "target_cards_verified": list(builder.TARGET_CARD_IDS),
        "fixture_count": len(fixture_manifest.get("fixture_rows", [])),
        "issues": issues,
        "dirty_workspace_paths_observed": dirty_paths,
        "safe_flags": {
            "promotion_verdict": builder.PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    return result


def main() -> int:
    result = verify()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "issues": result["issues"], "result": builder.rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
