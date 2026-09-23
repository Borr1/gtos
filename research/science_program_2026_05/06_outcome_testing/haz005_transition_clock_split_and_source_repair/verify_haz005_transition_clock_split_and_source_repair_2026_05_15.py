#!/usr/bin/env python3
"""Verify HAZ-005 transition-clock split and source-repair artifacts.

This verifier stays inside the route evidence class. It checks generated
derived ledgers, hashes, row counts, safe flags, repair admission boundaries,
and exact future source-capture contracts. It does not open broker/API/live
surfaces and does not write raw market data.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "HAZ005_TRANSITION_CLOCK_SPLIT_AND_SOURCE_REPAIR"
EVIDENCE_CLASS = "READY8_HAZ005_TRANSITION_CLOCK_SPLIT_AND_SOURCE_REPAIR_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DATE = "2026-05-15"

SCRIPT_PATH = Path(__file__).resolve()
ROUTE_DIR = SCRIPT_PATH.parent
REPO = SCRIPT_PATH.parents[4]

MANIFEST_PATH = ROUTE_DIR / f"HAZ005_OUTPUT_MANIFEST_{DATE}.json"
COMPLETION_PATH = ROUTE_DIR / f"HAZ005_COMPLETION_AUDIT_{DATE}.json"
DECISION_PATH = ROUTE_DIR / f"HAZ005_DECISION_LEDGER_{DATE}.json"
INPUT_BINDING_PATH = ROUTE_DIR / f"HAZ005_ACCEPTED_INPUT_BINDING_LEDGER_{DATE}.json"
SENSITIVITY_PATH = ROUTE_DIR / f"HAZ005_SENSITIVITY_LEDGER_{DATE}.json"
SATURATION_PATH = ROUTE_DIR / f"HAZ005_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json"
VERIFICATION_RESULT_PATH = ROUTE_DIR / f"HAZ005_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_OUTPUT_KEYS = {
    "concentration",
    "context_anchor",
    "descriptor_split",
    "explanation",
    "future_capture",
    "horizon_reversal",
    "input_binding",
    "instruction_coverage",
    "interaction",
    "next_g12_prompt",
    "next_g12_starter",
    "one_vs_rest",
    "pass_control",
    "repair",
    "repaired_packet",
    "saturation",
    "sensitivity",
    "source_scan",
    "source_search",
    "synthesis",
}

JSONL_COUNT_KEYS = {
    "concentration": "concentration_rows",
    "descriptor_split": "descriptor_split_rows",
    "explanation": "explanation_rows",
    "future_capture": "future_capture_rows",
    "horizon_reversal": "horizon_reversal_rows",
    "interaction": "interaction_rows",
    "one_vs_rest": "one_vs_rest_rows",
    "pass_control": "pass_control_rows",
    "repair": "fail_closed_repair_rows",
    "repaired_packet": "repaired_packet_rows",
    "source_scan": "source_scan_rows",
}

EXPECTED_COUNTS = {
    "concentration_rows": 6784,
    "descriptor_split_rows": 8576,
    "explanation_rows": 896,
    "fail_closed_repair_rows": 790,
    "future_capture_rows": 7,
    "horizon_reversal_rows": 200,
    "interaction_rows": 400,
    "one_vs_rest_rows": 1664,
    "pass_control_rows": 896,
    "repaired_packet_rows": 5,
    "source_scan_rows": 7,
}

REQUIRED_CAPTURE_FIELDS = {
    "candidate_input_row_id",
    "duplicate_proxy_denominator_key",
    "symbol",
    "source_file_name",
    "entry_reference_time_utc",
    "prior16_required_bar_end_utc",
    "bar_status",
    "open",
    "high",
    "low",
    "close",
    "source_record_count",
    "source_timestamp_min_utc_ms",
    "source_timestamp_max_utc_ms",
    "source_byte_start",
    "source_byte_end_exclusive",
    "bar_hash",
    "segment_or_source_range_sha256",
    "calendar_session_closed_proof_if_no_records",
}

FORBIDDEN_TRUE_FIELDS = {
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_live_trading_behavior",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "changes_trading_risk_safety_prompt_decision_behavior",
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO.resolve())).replace("\\", "/")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                yield line_number, json.loads(line)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_route_safe_fields(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    if payload.get("route_id") != ROUTE_ID:
        failures.append(f"{label}: route_id mismatch")
    if payload.get("evidence_class") != EVIDENCE_CLASS:
        failures.append(f"{label}: evidence_class mismatch")
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        failures.append(f"{label}: promotion_verdict mismatch")
    for field in FORBIDDEN_TRUE_FIELDS:
        if payload.get(field) is not False:
            failures.append(f"{label}: {field} must be false")
    return failures


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: Any = None) -> None:
    checks.append({"name": name, "ok": bool(ok), "detail": detail})


def verify() -> tuple[bool, dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    required_json_paths = [
        MANIFEST_PATH,
        COMPLETION_PATH,
        DECISION_PATH,
        INPUT_BINDING_PATH,
        SENSITIVITY_PATH,
        SATURATION_PATH,
    ]
    missing_required = [rel(path) for path in required_json_paths if not path.exists()]
    add_check(checks, "required_json_artifacts_exist", not missing_required, missing_required)
    if missing_required:
        failures.extend(f"missing required artifact {path}" for path in missing_required)

    manifest = read_json(MANIFEST_PATH)
    completion = read_json(COMPLETION_PATH)
    decision = read_json(DECISION_PATH)
    input_binding = read_json(INPUT_BINDING_PATH)
    sensitivity = read_json(SENSITIVITY_PATH)
    saturation = read_json(SATURATION_PATH)

    for label, payload in [
        ("manifest", manifest),
        ("completion", completion),
        ("decision", decision),
        ("input_binding", input_binding),
        ("sensitivity", sensitivity),
        ("saturation", saturation),
    ]:
        label_failures = check_route_safe_fields(payload, label)
        add_check(checks, f"{label}_safe_flags", not label_failures, label_failures)
        failures.extend(label_failures)

    output_counts = manifest.get("output_counts", {})
    add_check(checks, "expected_output_counts", output_counts == EXPECTED_COUNTS, output_counts)
    if output_counts != EXPECTED_COUNTS:
        failures.append("manifest output_counts differ from expected frozen HAZ-005 counts")

    add_check(
        checks,
        "completion_counts_match_manifest",
        completion.get("output_counts") == output_counts,
        completion.get("output_counts"),
    )
    if completion.get("output_counts") != output_counts:
        failures.append("completion output_counts differ from manifest")

    checklist_rows = completion.get("prompt_to_artifact_checklist", [])
    checklist_failures = [
        f"{row.get('requirement')}: {row.get('status')}"
        for row in checklist_rows
        if row.get("status") != "DONE"
    ]
    checklist_artifact_failures = []
    for row in checklist_rows:
        artifact = row.get("artifact")
        artifacts = artifact if isinstance(artifact, list) else [artifact]
        for artifact_path in artifacts:
            if isinstance(artifact_path, str) and artifact_path.startswith("research/") and not (REPO / artifact_path).exists():
                checklist_artifact_failures.append(artifact_path)
    add_check(
        checks,
        "completion_prompt_to_artifact_checklist_done",
        not checklist_failures and not checklist_artifact_failures,
        {"status_failures": checklist_failures, "missing_artifacts": checklist_artifact_failures},
    )
    failures.extend(checklist_failures)
    failures.extend(f"completion checklist artifact missing: {path}" for path in checklist_artifact_failures)

    output_rows = manifest.get("outputs", [])
    output_by_key = {row.get("artifact_key"): row for row in output_rows}
    keys = set(output_by_key)
    add_check(checks, "manifest_has_expected_output_keys", keys == EXPECTED_OUTPUT_KEYS, sorted(keys))
    if keys != EXPECTED_OUTPUT_KEYS:
        failures.append("manifest output keys differ from expected route outputs")

    hash_failures: list[str] = []
    line_count_failures: list[str] = []
    row_route_failures: list[str] = []
    jsonl_rows_by_key: dict[str, list[dict[str, Any]]] = {}
    for key, row in sorted(output_by_key.items()):
        path = REPO / row["path"]
        if not path.exists():
            hash_failures.append(f"{key}: path missing")
            continue
        if row.get("exists") is not True:
            hash_failures.append(f"{key}: manifest exists flag is not true")
        actual_size = path.stat().st_size
        if row.get("size_bytes") != actual_size:
            hash_failures.append(f"{key}: size mismatch {row.get('size_bytes')} != {actual_size}")
        actual_sha = sha256_file(path)
        if row.get("sha256") != actual_sha:
            hash_failures.append(f"{key}: sha mismatch")
        if key in JSONL_COUNT_KEYS:
            rows = [payload for _, payload in iter_jsonl(path)]
            jsonl_rows_by_key[key] = rows
            expected_count = output_counts[JSONL_COUNT_KEYS[key]]
            if len(rows) != expected_count:
                line_count_failures.append(f"{key}: {len(rows)} != {expected_count}")
            for index, payload in enumerate(rows, start=1):
                route_failures = check_route_safe_fields(payload, f"{key}:{index}")
                if route_failures:
                    row_route_failures.extend(route_failures[:3])
                    if len(row_route_failures) > 20:
                        break
        elif path.suffix == ".json" and key != "manifest":
            payload = read_json(path)
            if isinstance(payload, dict) and payload.get("route_id") == ROUTE_ID:
                route_failures = check_route_safe_fields(payload, key)
                if route_failures:
                    row_route_failures.extend(route_failures)

    add_check(checks, "manifest_hashes_and_sizes_match_disk", not hash_failures, hash_failures)
    failures.extend(hash_failures)
    add_check(checks, "jsonl_counts_match_manifest", not line_count_failures, line_count_failures)
    failures.extend(line_count_failures)
    add_check(checks, "jsonl_rows_keep_route_safe_flags", not row_route_failures, row_route_failures[:20])
    failures.extend(row_route_failures)

    repair_status_counts = Counter(row["repair_status"] for row in jsonl_rows_by_key.get("repair", []))
    expected_repair_status = {
        "NOT_REPAIRABLE_FROM_SEARCHED_SAME_EVIDENCE_CLASS_SOURCES": 785,
        "REPAIRED_FROM_LOCAL_SIERRA_CANDIDATE_REQUIRES_G12": 5,
    }
    add_check(checks, "repair_status_counts", dict(repair_status_counts) == expected_repair_status, dict(repair_status_counts))
    if dict(repair_status_counts) != expected_repair_status:
        failures.append("fail-closed repair status counts differ from expected")

    repaired_packet_rows = jsonl_rows_by_key.get("repaired_packet", [])
    repaired_packet_ok = (
        len(repaired_packet_rows) == 5
        and all(row.get("source_admission_status") == "CANDIDATE_REPAIR_PACKET_REQUIRES_G12_SOURCE_AUDIT" for row in repaired_packet_rows)
        and all(row.get("repair_source_basis") == "local_sierra_full_file_candidate_repair_requires_G12" for row in repaired_packet_rows)
    )
    add_check(checks, "repaired_packet_requires_g12_before_admission", repaired_packet_ok, repaired_packet_rows)
    if not repaired_packet_ok:
        failures.append("repaired packet rows must remain G12-gated candidate repairs")

    future_capture_rows = jsonl_rows_by_key.get("future_capture", [])
    future_capture_ok = (
        len(future_capture_rows) == 7
        and all(set(row.get("required_capture_fields", [])) == REQUIRED_CAPTURE_FIELDS for row in future_capture_rows)
        and all(row.get("missing_prior16_bar_end_utc") for row in future_capture_rows)
    )
    add_check(checks, "future_capture_contracts_are_exact", future_capture_ok, [row.get("symbol") for row in future_capture_rows])
    if not future_capture_ok:
        failures.append("future source-capture rows must have exact required fields and missing bar windows")

    expected_decision_counts = {
        "haz005_fail_closed_rows": 790,
        "repaired_descriptor_packet_rows": 5,
        "future_capture_contract_rows": 7,
        "materiality_observed": True,
    }
    add_check(
        checks,
        "decision_summary_matches_route_result",
        decision.get("summary") == expected_decision_counts,
        decision.get("summary"),
    )
    if decision.get("summary") != expected_decision_counts:
        failures.append("decision summary does not match expected HAZ-005 route result")

    sensitivity_ok = (
        sensitivity.get("original_role_counts") == {
            "per_card_contrast_row": 1465,
            "per_card_fail_closed_row": 790,
            "per_card_pass_row": 759,
        }
        and sensitivity.get("repaired_role_counts") == {
            "per_card_contrast_row": 1470,
            "per_card_fail_closed_row": 785,
            "per_card_pass_row": 759,
        }
        and sensitivity.get("reclassified_candidate_count") == 5
        and sensitivity.get("materiality_observed") is True
    )
    add_check(checks, "sensitivity_role_shift_is_bounded", sensitivity_ok, {
        "original": sensitivity.get("original_role_counts"),
        "repaired": sensitivity.get("repaired_role_counts"),
        "reclassified": sensitivity.get("reclassified_candidate_count"),
    })
    if not sensitivity_ok:
        failures.append("sensitivity role counts or reclassification count changed")

    shift_rows = sensitivity.get("headline_pass_control_shift_rows", [])
    h1_h4_positive = all(
        row.get("repaired_classification") == "POSITIVE_NEUTRAL_TARGET_MOVEMENT"
        for row in shift_rows
        if row.get("horizon_m15_bars") in {1, 4}
    )
    h16_inverse = all(
        row.get("repaired_classification") == "INVERSE_NEUTRAL_TARGET_MOVEMENT"
        for row in shift_rows
        if row.get("horizon_m15_bars") == 16
    )
    add_check(checks, "horizon_reversal_anatomy_preserved", h1_h4_positive and h16_inverse, {
        "h1_h4_positive": h1_h4_positive,
        "h16_inverse": h16_inverse,
    })
    if not (h1_h4_positive and h16_inverse):
        failures.append("horizon reversal anatomy is not preserved")

    input_counts_ok = input_binding.get("accepted_global_counts_from_prompt") == {
        "computable_rows": 162336,
        "fail_closed_rows": 30560,
        "rowset_rows": 24112,
        "source_candidates": 3014,
        "target_rows": 192896,
    }
    add_check(checks, "accepted_g12_anchor_counts_bound", input_counts_ok, input_binding.get("accepted_global_counts_from_prompt"))
    if not input_counts_ok:
        failures.append("accepted G12 anchor counts are not bound as expected")

    source_summary = saturation.get("source_search_summary", {})
    no_raw_blob_ok = source_summary.get("raw_blob_committed") is False and not list(ROUTE_DIR.glob("*.scid"))
    add_check(checks, "no_raw_market_blob_committed", no_raw_blob_ok, source_summary)
    if not no_raw_blob_ok:
        failures.append("route directory must not contain raw market blobs")

    next_prompt = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_PROMPT_{DATE}.md"
    next_starter = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_STARTER_{DATE}.txt"
    next_gate_ok = next_prompt.exists() and next_starter.exists() and "G12" in next_prompt.read_text(encoding="utf-8")
    add_check(checks, "next_g12_prompt_and_starter_exist", next_gate_ok, [rel(next_prompt), rel(next_starter)])
    if not next_gate_ok:
        failures.append("next G12 prompt/starter missing or malformed")

    ok = not failures
    result = {
        "artifact_family": "verification_result",
        "schema_version": "haz005_verification_result_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_live_trading_behavior": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "changes_trading_risk_safety_prompt_decision_behavior": False,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "ok": ok,
        "checks": checks,
        "failures": failures,
        "verified_artifacts": {
            "manifest": rel(MANIFEST_PATH),
            "completion_audit": rel(COMPLETION_PATH),
            "decision": rel(DECISION_PATH),
            "input_binding": rel(INPUT_BINDING_PATH),
            "sensitivity": rel(SENSITIVITY_PATH),
            "saturation": rel(SATURATION_PATH),
        },
        "closeout_readiness": {
            "can_mark_goal_complete_after_verifier_and_commit": ok,
            "requires_g12_before_validation_admission": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    return ok, result


def main() -> None:
    ok, result = verify()
    with VERIFICATION_RESULT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"ok": ok, "verification_result": rel(VERIFICATION_RESULT_PATH)}, indent=2, sort_keys=True))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
