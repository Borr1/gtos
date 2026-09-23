"""Verify the READY8 discriminative quarantined target-result packet."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE_DIR))

import build_scid_ready8_discriminative_quarantined_target_result_packet_2026_05_13 as builder


RESULT_PATH = ROUTE_DIR / f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE_TAG}.json"


def load_json(path: Path) -> Any:
    return builder.load_json(path)


def iter_jsonl(path: Path):
    with open(builder.io_path(path), "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                yield line_no, json.loads(line)


def required_files() -> list[Path]:
    return [
        Path(builder.__file__),
        Path(__file__),
        ROUTE_DIR / "test_scid_ready8_discriminative_quarantined_target_result_packet_2026_05_13.py",
        builder.NEXT_G12_PROMPT,
        builder.NEXT_G12_STARTER,
        *builder.result_paths(),
        ROUTE_DIR / f"{builder.PREFIX}_TARGET_SOURCE_JOIN_LEDGER_{builder.DATE_TAG}.json",
        ROUTE_DIR / f"{builder.PREFIX}_DUPLICATE_DENOMINATOR_LEDGER_{builder.DATE_TAG}.json",
        ROUTE_DIR / f"{builder.PREFIX}_PARTITION_CONTROL_LEDGER_{builder.DATE_TAG}.json",
        ROUTE_DIR / f"{builder.PREFIX}_SIDECAR_QUALITY_DIAGNOSTICS_LEDGER_{builder.DATE_TAG}.json",
        ROUTE_DIR / f"{builder.PREFIX}_ADJACENT_NOAPI_ROUTE_FAMILY_SIDECAR_LEDGER_{builder.DATE_TAG}.json",
        ROUTE_DIR / f"{builder.PREFIX}_SAME_EVIDENCE_CLASS_BLOCKER_REPAIR_LEDGER_{builder.DATE_TAG}.json",
        ROUTE_DIR / f"{builder.PREFIX}_SATURATION_SELF_RED_TEAM_{builder.DATE_TAG}.md",
        ROUTE_DIR / f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE_TAG}.json",
        ROUTE_DIR / f"{builder.PREFIX}_FOCUSED_TEST_RESULT_{builder.DATE_TAG}.json",
        ROUTE_DIR / f"{builder.PREFIX}_OUTPUT_MANIFEST_{builder.DATE_TAG}.json",
    ]


def safe_flags_closed(row: dict[str, Any]) -> bool:
    return (
        row.get("promotion_verdict") == "NO_PROMOTION_VERDICT"
        and row.get("validation_safe") is False
        and row.get("outcome_review_opened") is False
        and row.get("live_effect") is False
        and row.get("opens_validation") is False
        and row.get("opens_result_scoring") is False
        and row.get("opens_strategy_edge_claims") is False
        and row.get("opens_ai_api") is False
        and row.get("opens_paid_or_vendor_access") is False
        and row.get("opens_broker_account_order_history_deal_position_evidence") is False
        and row.get("opens_live_trading_behavior") is False
        and row.get("opens_live_restart") is False
        and row.get("opens_prompt_config_risk_safety_execution_canary_selector_edit") is False
        and row.get("opens_raw_market_data_blob_commit") is False
        and row.get("opens_registry_edit") is False
        and row.get("opens_remote_push") is False
    )


def verify() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    checks: dict[str, bool] = {}

    files = required_files()
    checks["required_files_exist"] = all(builder.path_exists(path) for path in files)
    for path in files:
        if not builder.path_exists(path):
            issues.append({"check": "required_files_exist", "path": builder.repo_path(path)})

    json_files = [path for path in files if path.suffix == ".json" and builder.path_exists(path)]
    checks["json_parse_ok"] = True
    for path in json_files:
        try:
            load_json(path)
        except Exception as exc:  # pragma: no cover - defensive verifier reporting
            checks["json_parse_ok"] = False
            issues.append({"check": "json_parse_ok", "path": builder.repo_path(path), "error": str(exc)})

    join = load_json(ROUTE_DIR / f"{builder.PREFIX}_TARGET_SOURCE_JOIN_LEDGER_{builder.DATE_TAG}.json")
    duplicate = load_json(ROUTE_DIR / f"{builder.PREFIX}_DUPLICATE_DENOMINATOR_LEDGER_{builder.DATE_TAG}.json")
    blocker = load_json(ROUTE_DIR / f"{builder.PREFIX}_SAME_EVIDENCE_CLASS_BLOCKER_REPAIR_LEDGER_{builder.DATE_TAG}.json")
    completion = load_json(ROUTE_DIR / f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE_TAG}.json")
    manifest = load_json(ROUTE_DIR / f"{builder.PREFIX}_OUTPUT_MANIFEST_{builder.DATE_TAG}.json")
    focused = load_json(ROUTE_DIR / f"{builder.PREFIX}_FOCUSED_TEST_RESULT_{builder.DATE_TAG}.json")

    checks["terminal_decision_allowed"] = join.get("terminal_decision") == builder.TERMINAL_DECISION
    checks["safe_flags_closed_in_ledgers"] = all(
        ledger.get("promotion_verdict") == "NO_PROMOTION_VERDICT"
        and ledger.get("validation_safe") is False
        and ledger.get("outcome_review_opened") is False
        and ledger.get("live_effect") is False
        for ledger in (join, duplicate, blocker, completion, manifest)
    )
    checks["focused_tests_recorded_passed"] = focused.get("status") == "passed"
    checks["completion_instruction_coverage_passes"] = completion.get("all_instruction_coverage_satisfied") is True
    checks["no_terminal_blockers"] = blocker.get("terminal_blocker_count") == 0
    checks["input_hashes_match"] = (
        (
            join.get("input_hash_checks", {}).get("rowset_rows_sha256_matches_manifest") is True
            or join.get("input_hash_checks", {}).get("rowset_rows_lf_sha256_matches_manifest") is True
        )
        and (
            join.get("input_hash_checks", {}).get("bar_rows_sha256_matches_manifest") is True
            or join.get("input_hash_checks", {}).get("bar_rows_lf_sha256_matches_manifest") is True
        )
    )
    checks["binds_repaired_discriminative_rowset_hash"] = (
        join.get("input_hash_checks", {}).get("rowset_rows_lf_sha256_matches_required_repaired_discriminative") is True
        and join.get("input_hash_checks", {}).get("rowset_rows_sha256_required_repaired_discriminative") == builder.REPAIRED_ROWSET_SHA256
    )
    checks["does_not_bind_old_redundant_ready8_rowset"] = (
        join.get("input_hash_checks", {}).get("rowset_rows_sha256_is_not_old_redundant") is True
        and join.get("input_hash_checks", {}).get("old_redundant_rowset_sha256_forbidden") == builder.OLD_REDUNDANT_ROWSET_SHA256
    )
    checks["denominator_counts_exact"] = (
        duplicate.get("source_candidate_count") == builder.EXPECTED["source_candidates"]
        and duplicate.get("ready8_rowset_row_count") == builder.EXPECTED["rowset_rows"]
        and duplicate.get("target_terminal_combination_count") == builder.EXPECTED["target_rows"]
        and duplicate.get("blocked_or_expansion_row_count") == 0
    )
    checks["denominator_roles_preserved"] = set(duplicate.get("per_denominator_role_counts", {})) == {
        "per_card_pass_row",
        "per_card_contrast_row",
        "per_card_non_applicable_row",
        "per_card_fail_closed_row",
    }
    checks["adv_placebo_control_status_preserved"] = set(duplicate.get("adversarial_placebo_control_cards", {})) == {
        "ADV-001",
        "ADV-003",
    }

    bars_by_end, _, duplicate_bar_keys = builder.build_bars_by_end()
    rowset_map = {row["rowset_row_id"]: row for row in builder.iter_jsonl(builder.READY8_ROWSET_ROWS)}
    rowset_id_counts = Counter(row.get("rowset_row_id") for row in builder.iter_jsonl(builder.READY8_ROWSET_ROWS))
    duplicate_state = {"rowset_id_counts": rowset_id_counts}

    target_count = 0
    per_card_counts: Counter = Counter()
    status_counts: Counter = Counter()
    family_counts: Counter = Counter()
    horizon_counts: Counter = Counter()
    card_ids: set[str] = set()
    target_ids: set[str] = set()
    forbidden_field_hits: list[dict[str, Any]] = []
    hash_mismatch_count = 0
    recompute_mismatch_count = 0
    source_hash_mismatch_count = 0
    safe_flag_failure_count = 0
    jsonl_parse_ok = True

    for path in builder.result_paths():
        try:
            for line_no, row in iter_jsonl(path):
                target_count += 1
                per_card_counts[row.get("card_id")] += 1
                status_counts[row.get("terminal_status")] += 1
                family_counts[row.get("target_family_id")] += 1
                horizon_counts[row.get("horizon_m15_bars")] += 1
                card_ids.add(row.get("card_id"))
                target_ids.add(row.get("target_result_row_id"))
                forbidden = sorted(set(row) & builder.FORBIDDEN_EXACT_FIELDS)
                if forbidden:
                    forbidden_field_hits.append({"path": builder.repo_path(path), "line": line_no, "fields": forbidden})
                if not safe_flags_closed(row):
                    safe_flag_failure_count += 1

                row_without_hash = dict(row)
                expected_hash = row_without_hash.pop("target_result_row_hash")
                if builder.sha256_json(row_without_hash) != expected_hash:
                    hash_mismatch_count += 1
                if builder.sha256_json(row.get("source_bar_hashes_consumed", [])) != row.get("source_bar_hashes_consumed_sha256"):
                    source_hash_mismatch_count += 1

                rowset_row = rowset_map.get(row.get("rowset_row_id"))
                if rowset_row is None:
                    recompute_mismatch_count += 1
                    continue
                expected = builder.compute_target_result(
                    rowset_row,
                    row["target_family_id"],
                    int(row["horizon_m15_bars"]),
                    bars_by_end,
                    duplicate_state,
                )
                if expected != row:
                    recompute_mismatch_count += 1
        except Exception as exc:  # pragma: no cover - defensive verifier reporting
            jsonl_parse_ok = False
            issues.append({"check": "jsonl_parse_ok", "path": builder.repo_path(path), "error": str(exc)})

    checks["jsonl_parse_ok"] = jsonl_parse_ok
    checks["target_count_exact"] = target_count == builder.EXPECTED["target_rows"]
    checks["per_card_target_counts_exact"] = all(
        per_card_counts.get(card_id) == builder.EXPECTED["target_rows_per_card"] for card_id in builder.READY_CARD_IDS
    )
    checks["ready_cards_only"] = card_ids == set(builder.READY_CARD_IDS)
    checks["target_families_exact"] = family_counts == Counter({family: builder.EXPECTED["rowset_rows"] * len(builder.HORIZONS) for family in builder.TARGET_FAMILIES})
    checks["horizons_exact"] = horizon_counts == Counter({horizon: builder.EXPECTED["rowset_rows"] * len(builder.TARGET_FAMILIES) for horizon in builder.HORIZONS})
    checks["target_ids_unique"] = len(target_ids) == target_count
    checks["target_hashes_valid"] = hash_mismatch_count == 0
    checks["source_hashes_valid"] = source_hash_mismatch_count == 0
    checks["full_recompute_matches"] = recompute_mismatch_count == 0
    checks["forbidden_exact_fields_absent"] = not forbidden_field_hits
    checks["safe_flags_closed_in_rows"] = safe_flag_failure_count == 0
    checks["duplicate_bar_keys_absent"] = not duplicate_bar_keys
    checks["next_g12_prompt_exists"] = builder.path_exists(builder.NEXT_G12_PROMPT) and builder.path_exists(builder.NEXT_G12_STARTER)
    checks["manifest_hashes_exist"] = all(item.get("exists") and item.get("sha256") for item in manifest.get("artifacts", []))
    checks["no_validation_or_promotion"] = (
        manifest.get("promotion_verdict") == "NO_PROMOTION_VERDICT"
        and manifest.get("validation_safe") is False
        and manifest.get("live_effect") is False
    )

    if forbidden_field_hits:
        issues.append({"check": "forbidden_exact_fields_absent", "hits": forbidden_field_hits[:20]})
    if recompute_mismatch_count:
        issues.append({"check": "full_recompute_matches", "mismatch_count": recompute_mismatch_count})
    if hash_mismatch_count:
        issues.append({"check": "target_hashes_valid", "mismatch_count": hash_mismatch_count})
    if source_hash_mismatch_count:
        issues.append({"check": "source_hashes_valid", "mismatch_count": source_hash_mismatch_count})
    if safe_flag_failure_count:
        issues.append({"check": "safe_flags_closed_in_rows", "failure_count": safe_flag_failure_count})
    if duplicate_bar_keys:
        issues.append({"check": "duplicate_bar_keys_absent", "count": len(duplicate_bar_keys)})

    ok = all(checks.values()) and not issues
    return {
        "artifact_family": "verification_result",
        "schema_version": "scid_ready8_discriminative_quarantined_target_result_packet_verifier_v1",
        "route_id": builder.ROUTE_ID,
        "evidence_class": builder.EVIDENCE_CLASS,
        "generated_at_utc": builder.now_utc(),
        "terminal_decision": builder.TERMINAL_DECISION,
        "ok": ok,
        "can_mark_goal_complete_after_commit_and_closeout": ok,
        "checks": checks,
        "issues": issues,
        "target_result_row_count": target_count,
        "status_counts": dict(sorted(status_counts.items())),
        "per_card_target_counts": dict(sorted(per_card_counts.items())),
        "target_family_counts": dict(sorted(family_counts.items())),
        "horizon_counts": dict(sorted(horizon_counts.items())),
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
        "opens_live_restart": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "credentials_touched": False,
        "changes_trading_risk_safety_prompt_decision_behavior": False,
    }


def main() -> int:
    result = verify()
    builder.write_json(RESULT_PATH, result)
    builder.refresh_manifest()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
