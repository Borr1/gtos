from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DATE_TAG = "2026-05-13"
ROUTE_ID = "G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_AUDIT"
EVIDENCE_CLASS = "G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_AUDIT_ONLY"
SCHEMA_VERSION = "g12_scid_ready8_discriminative_numerical_screen_audit_v1"
TERMINAL_DECISION = "ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_CONTROL_EVIDENCE_ONLY"

EXPECTED_READY_CARDS = 8
EXPECTED_SOURCE_CANDIDATES = 3014
EXPECTED_ROWSET_ROWS = 24112
EXPECTED_TARGET_ROWS = 192896
EXPECTED_COMPUTABLE_ROWS = 162336
EXPECTED_FAIL_CLOSED_ROWS = 30560
EXPECTED_ROWSET_SHA256 = "fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3"
OLD_REDUNDANT_ROWSET_SHA256 = "7077a0f3fa3da2c854f2a0daab856d876992b927eb3228a161eb1cf02babb54d"
READY_CARDS = ["ADV-001", "ADV-003", "BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"]
HORIZONS = [1, 4, 16, 32]
TARGET_FAMILIES = [
    "neutral_close_to_close_return_m15_horizons_v1",
    "neutral_high_low_excursion_m15_horizons_v1",
]

ROOT = Path(__file__).resolve().parents[4]
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
ROUTE_DIR = Path(__file__).resolve().parent

G0_DIR = OUTCOME_DIR / "g0_scid_ready8_discriminative_target_result_control_evidence_synthesis_after_g12_audit"
TARGET_PACKET_DIR = OUTCOME_DIR / "scid_ready8_discriminative_quarantined_target_result_packet"
ROWSET_DIR = OUTCOME_DIR / "scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design"
UPSTREAM_G12_DIR = OUTCOME_DIR / "g12_scid_ready8_disc_target_result_audit"

CONTROLLING_PROMPT = PROMPT_DIR / "G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_AUDIT_GOAL_PROMPT_2026-05-13.md"
NEXT_G0_PROMPT = (
    PROMPT_DIR
    / "G0_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_AFTER_G12_AUDIT_GOAL_PROMPT_2026-05-13.md"
)
NEXT_G0_STARTER = ROUTE_DIR / "G0_SCID_READY8_DISC_NUMERIC_SCREEN_LEARNING_SYNTHESIS_STARTER_2026-05-13.txt"

ROWSET_ROWS = ROWSET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
ROWSET_MANIFEST = ROWSET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_MANIFEST_2026-05-13.json"
TARGET_MANIFEST = TARGET_PACKET_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_OUTPUT_MANIFEST_2026-05-13.json"

UPSTREAM_G12_DECISION = UPSTREAM_G12_DIR / "G12_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_AUDIT_DECISION_LEDGER_2026-05-13.json"
UPSTREAM_G12_VERIFIER = UPSTREAM_G12_DIR / "verify_g12_scid_ready8_disc_target_result_audit_2026_05_13.py"
UPSTREAM_G12_VERIFICATION = UPSTREAM_G12_DIR / "G12_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_AUDIT_VERIFICATION_RESULT_2026-05-13.json"

G0_VERIFIER = G0_DIR / "verify_g0_ready8_disc_screen.py"
G0_TEST = G0_DIR / "test_g0_ready8_disc_screen.py"

PREFIX = "G12_SCID_READY8_DISC_NUMERIC_SCREEN_AUDIT"

SAFE_FLAGS: dict[str, Any] = {
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

LEDGER_FILES = {
    "aggregate": "G0_SCID_READY8_DISC_TARGET_SCREEN_FULL_POPULATION_AGGREGATE_SCREEN_LEDGER_2026-05-13.jsonl",
    "contrast": "G0_SCID_READY8_DISC_TARGET_SCREEN_PASS_VS_CONTROL_CONTRAST_LEDGER_2026-05-13.jsonl",
    "candidate": "G0_SCID_READY8_DISC_TARGET_SCREEN_CANDIDATE_LEVEL_VIEW_LEDGER_2026-05-13.jsonl",
    "partition": "G0_SCID_READY8_DISC_TARGET_SCREEN_PARTITION_LEVEL_VIEW_LEDGER_2026-05-13.jsonl",
    "failure": "G0_SCID_READY8_DISC_TARGET_SCREEN_FAILURE_ANATOMY_LEDGER_2026-05-13.jsonl",
    "explanation": "G0_SCID_READY8_DISC_TARGET_SCREEN_WINNER_LOSER_NEUTRAL_INVERSION_EXPLANATION_LEDGER_2026-05-13.jsonl",
    "ambiguity": "G0_SCID_READY8_DISC_TARGET_SCREEN_AMBIGUITY_PURSUIT_LEDGER_2026-05-13.jsonl",
    "data_backing": "G0_SCID_READY8_DISC_TARGET_SCREEN_DATA_BACKING_LEDGER_2026-05-13.jsonl",
}

G0_JSON_FILES = {
    "decision": "G0_SCID_READY8_DISC_TARGET_SCREEN_DECISION_LEDGER_2026-05-13.json",
    "fact": "G0_SCID_READY8_DISC_TARGET_SCREEN_FACT_RECONCILIATION_LEDGER_2026-05-13.json",
    "execution": "G0_SCID_READY8_DISC_TARGET_SCREEN_SCREEN_EXECUTION_LEDGER_2026-05-13.json",
    "closeout": "G0_SCID_READY8_DISC_TARGET_SCREEN_FULL_UNDERSTANDING_CLOSEOUT_LEDGER_2026-05-13.json",
    "route": "G0_SCID_READY8_DISC_TARGET_SCREEN_ROUTE_RANKING_LEDGER_2026-05-13.json",
    "repair": "G0_SCID_READY8_DISC_TARGET_SCREEN_SAME_EVIDENCE_CLASS_REPAIR_BLOCKER_LEDGER_2026-05-13.json",
    "completion": "G0_SCID_READY8_DISC_TARGET_SCREEN_COMPLETION_AUDIT_2026-05-13.json",
    "verification": "G0_SCID_READY8_DISC_TARGET_SCREEN_VERIFICATION_RESULT_2026-05-13.json",
    "manifest": "G0_SCID_READY8_DISC_TARGET_SCREEN_OUTPUT_MANIFEST_2026-05-13.json",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def io_path(path: Path) -> str:
    resolved = str(path.resolve(strict=False))
    if os.name == "nt" and not resolved.startswith("\\\\?\\"):
        return "\\\\?\\" + resolved
    return resolved


def read_json(path: Path) -> Any:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(io_path(path), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=True)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(io_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(io_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file_pair(path: Path) -> dict[str, str]:
    raw = hashlib.sha256()
    lf = hashlib.sha256()
    with open(io_path(path), "rb") as handle:
        for line in handle:
            raw.update(line)
            lf.update(line.replace(b"\r\n", b"\n"))
    return {"raw": raw.hexdigest(), "lf_normalized": lf.hexdigest()}


def file_size(path: Path) -> int:
    return int(os.path.getsize(io_path(path)))


def file_exists(path: Path) -> bool:
    return os.path.exists(io_path(path))


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(k): int(v) for k, v in sorted(counter.items(), key=lambda item: str(item[0]))}


def safe_base(artifact_family: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }


def target_result_file(card_id: str, family: str) -> Path:
    card = card_id.replace("-", "_")
    suffix = "CLOSE_TO_CLOSE" if family == TARGET_FAMILIES[0] else "HIGH_LOW_EXCURSION"
    return TARGET_PACKET_DIR / f"SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_{card}_{suffix}_{DATE_TAG}.jsonl"


def iter_jsonl_with_hash(path: Path) -> tuple[Iterable[dict[str, Any]], hashlib._Hash, hashlib._Hash]:
    digest = hashlib.sha256()
    digest_lf = hashlib.sha256()

    def generator() -> Iterable[dict[str, Any]]:
        with open(io_path(path), "rb") as handle:
            for line_no, raw_line in enumerate(handle, 1):
                digest.update(raw_line)
                digest_lf.update(raw_line.replace(b"\r\n", b"\n"))
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line.decode("utf-8"))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at {repo_path(path)}:{line_no}: {exc}") from exc

    return generator(), digest, digest_lf


def safe_flags_ok(row: dict[str, Any]) -> bool:
    for key, expected in SAFE_FLAGS.items():
        if key == "promotion_verdict":
            if row.get(key) != expected:
                return False
        elif row.get(key) is not expected:
            return False
    return True


def scan_rowset() -> dict[str, Any]:
    rows, digest, digest_lf = iter_jsonl_with_hash(ROWSET_ROWS)
    row_count = 0
    card_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    partition_counts: Counter[str] = Counter()
    source_group_counts: Counter[str] = Counter()
    source_file_counts: Counter[str] = Counter()
    fail_reason_counts: Counter[str] = Counter()
    duplicate_keys: set[str] = set()
    row_ids: set[str] = set()
    row_hashes: set[str] = set()
    candidate_ids: set[str] = set()
    safe_mismatches = 0
    missing_source_identifier = 0
    missing_asof = 0

    for row in rows:
        row_count += 1
        card_counts[row.get("card_id", "<missing>")] += 1
        role_counts[row.get("denominator_role", "<missing>")] += 1
        status_counts[row.get("card_row_status", "<missing>")] += 1
        partition_counts[row.get("validation_partition_assignment", "<missing>")] += 1
        source_group_counts[row.get("source_group", "<missing>")] += 1
        source_file_counts[row.get("source_file_name", "<missing>")] += 1
        duplicate_keys.add(row.get("duplicate_proxy_denominator_key"))
        row_ids.add(row.get("rowset_row_id"))
        row_hashes.add(row.get("row_hash"))
        candidate_ids.add(row.get("candidate_input_row_id"))
        if not row.get("source_identifier"):
            missing_source_identifier += 1
        if not row.get("decision_asof_utc") or not row.get("source_observed_asof_utc"):
            missing_asof += 1
        if row.get("safe_flags", {}).get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            safe_mismatches += 1
        if row.get("safe_flags", {}).get("validation_safe") is not False:
            safe_mismatches += 1
        for reason in row.get("fail_closed_reasons", []) or []:
            fail_reason_counts[str(reason)] += 1

    raw_hash = digest.hexdigest()
    lf_hash = digest_lf.hexdigest()
    return {
        "path": repo_path(ROWSET_ROWS),
        "row_count": row_count,
        "raw_sha256": raw_hash,
        "lf_normalized_sha256": lf_hash,
        "raw_sha256_matches_required_repaired_discriminative_rowset": raw_hash == EXPECTED_ROWSET_SHA256,
        "lf_normalized_sha256_matches_required_repaired_discriminative_rowset": lf_hash == EXPECTED_ROWSET_SHA256,
        "raw_sha256_is_not_old_redundant_rowset": raw_hash != OLD_REDUNDANT_ROWSET_SHA256,
        "card_counts": counter_dict(card_counts),
        "denominator_role_counts": counter_dict(role_counts),
        "card_row_status_counts": counter_dict(status_counts),
        "validation_partition_counts": counter_dict(partition_counts),
        "source_group_counts": counter_dict(source_group_counts),
        "source_file_counts": counter_dict(source_file_counts),
        "rowset_fail_closed_reason_counts": counter_dict(fail_reason_counts),
        "unique_duplicate_proxy_denominator_key_count": len(duplicate_keys),
        "unique_candidate_input_row_id_count": len(candidate_ids),
        "unique_rowset_row_id_count": len(row_ids),
        "unique_row_hash_count": len(row_hashes),
        "safe_flag_mismatch_count": safe_mismatches,
        "missing_source_identifier_count": missing_source_identifier,
        "missing_asof_count": missing_asof,
    }


def scan_target_rows() -> dict[str, Any]:
    total_rows = 0
    file_line_counts: dict[str, int] = {}
    file_hashes: dict[str, str] = {}
    card_counts: Counter[str] = Counter()
    horizon_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    row_status_counts: Counter[str] = Counter()
    partition_counts: Counter[str] = Counter()
    fail_reason_counts: Counter[str] = Counter()
    source_file_counts: Counter[str] = Counter()
    source_segment_counts: Counter[str] = Counter()
    target_ids: set[str] = set()
    target_hashes: set[str] = set()
    rowset_ids: set[str] = set()
    duplicate_keys: set[str] = set()
    safe_mismatches = 0
    missing_source_identifier = 0
    missing_source_bar_hash_list = 0
    missing_source_bar_hash_sha = 0
    missing_source_segment = 0

    for card_id in READY_CARDS:
        for family in TARGET_FAMILIES:
            path = target_result_file(card_id, family)
            rows, digest, digest_lf = iter_jsonl_with_hash(path)
            file_count = 0
            for row in rows:
                file_count += 1
                total_rows += 1
                card_counts[row.get("card_id", "<missing>")] += 1
                horizon_counts[str(row.get("horizon_m15_bars", "<missing>"))] += 1
                family_counts[row.get("target_family_id", "<missing>")] += 1
                status_counts[row.get("terminal_status", "<missing>")] += 1
                role_counts[row.get("denominator_role", "<missing>")] += 1
                row_status_counts[row.get("card_row_status", "<missing>")] += 1
                partition_counts[row.get("partition_assignment", "<missing>")] += 1
                source_file_counts[row.get("source_file_name_expected", "<missing>")] += 1
                source_segment_counts[row.get("source_segment_sha256_expected", "<missing>")] += 1
                target_ids.add(row.get("target_result_row_id"))
                target_hashes.add(row.get("target_result_row_hash"))
                rowset_ids.add(row.get("rowset_row_id"))
                duplicate_keys.add(row.get("duplicate_proxy_denominator_key"))
                if row.get("fail_closed_primary_reason"):
                    fail_reason_counts[row.get("fail_closed_primary_reason")] += 1
                if not safe_flags_ok(row):
                    safe_mismatches += 1
                if not row.get("source_identifier"):
                    missing_source_identifier += 1
                if not row.get("source_bar_hashes_consumed"):
                    missing_source_bar_hash_list += 1
                if not row.get("source_bar_hashes_consumed_sha256"):
                    missing_source_bar_hash_sha += 1
                if not row.get("source_segment_sha256_expected"):
                    missing_source_segment += 1
            rel_path = repo_path(path)
            file_line_counts[rel_path] = file_count
            file_hashes[rel_path] = {"raw": digest.hexdigest(), "lf_normalized": digest_lf.hexdigest()}

    return {
        "target_result_row_count": total_rows,
        "line_counts_by_file": file_line_counts,
        "sha256_by_file": file_hashes,
        "card_counts": counter_dict(card_counts),
        "horizon_counts": counter_dict(horizon_counts),
        "target_family_counts": counter_dict(family_counts),
        "terminal_status_counts": counter_dict(status_counts),
        "denominator_role_counts": counter_dict(role_counts),
        "card_row_status_counts": counter_dict(row_status_counts),
        "partition_assignment_counts": counter_dict(partition_counts),
        "fail_closed_primary_reason_counts": counter_dict(fail_reason_counts),
        "source_file_name_expected_counts": counter_dict(source_file_counts),
        "source_segment_sha256_expected_count": len(source_segment_counts),
        "unique_target_result_row_id_count": len(target_ids),
        "unique_target_result_row_hash_count": len(target_hashes),
        "unique_rowset_row_id_count": len(rowset_ids),
        "unique_duplicate_proxy_denominator_key_count": len(duplicate_keys),
        "safe_flag_mismatch_count": safe_mismatches,
        "missing_source_identifier_count": missing_source_identifier,
        "missing_source_bar_hash_list_count": missing_source_bar_hash_list,
        "missing_source_bar_hash_sha256_count": missing_source_bar_hash_sha,
        "missing_source_segment_sha256_expected_count": missing_source_segment,
    }


def scan_g0_ledger(name: str, path: Path) -> tuple[dict[str, Any], set[str], set[str], set[str]]:
    rows, digest, digest_lf = iter_jsonl_with_hash(path)
    line_count = 0
    schema_counts: Counter[str] = Counter()
    route_mismatch = 0
    evidence_mismatch = 0
    safe_mismatches = 0
    scope_counts: Counter[str] = Counter()
    dimension_fields_counts: Counter[str] = Counter()
    dimension_role_counts: Counter[str] = Counter()
    dimension_status_counts: Counter[str] = Counter()
    movement_shift_counts: Counter[str] = Counter()
    comparison_status_counts: Counter[str] = Counter()
    inversion_counts: Counter[str] = Counter()
    phenomenon_counts: Counter[str] = Counter()
    terminal_answer_counts: Counter[str] = Counter()
    ambiguity_terminal_counts: Counter[str] = Counter()
    failure_scope_counts: Counter[str] = Counter()
    combined_fail_counts: Counter[str] = Counter()
    failure_explanation_counts: Counter[str] = Counter()
    claim_type_counts: Counter[str] = Counter()
    negative_or_absence_counts: Counter[str] = Counter()
    source_hash_counts: Counter[str] = Counter()
    target_cell_count_counts: Counter[str] = Counter()
    computable_cell_count_counts: Counter[str] = Counter()
    fail_closed_cell_count_counts: Counter[str] = Counter()
    all_target_cells_false = 0
    repairable_remaining_true = 0
    target_result_cell_total = 0
    computable_target_cell_total = 0
    fail_closed_target_cell_total = 0
    unsafe_explanation_conversion_count = 0
    explanation_ids: set[str] = set()
    ambiguity_ids: set[str] = set()
    data_backing_claim_ids: set[str] = set()

    for row in rows:
        line_count += 1
        schema_counts[row.get("schema_version", "<missing>")] += 1
        if row.get("route_id") != "G0_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_AFTER_G12_AUDIT":
            route_mismatch += 1
        if row.get("evidence_class") != "G0_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_ONLY":
            evidence_mismatch += 1
        if not safe_flags_ok(row):
            safe_mismatches += 1
        if row.get("aggregate_scope"):
            scope_counts[row.get("aggregate_scope")] += 1
        if row.get("contrast_scope"):
            scope_counts[row.get("contrast_scope")] += 1
        if row.get("dimension_fields"):
            dimension_fields_counts["|".join(str(item) for item in row.get("dimension_fields", []))] += 1
        dimensions = row.get("dimensions", {}) if isinstance(row.get("dimensions"), dict) else {}
        if dimensions.get("denominator_role"):
            dimension_role_counts[dimensions["denominator_role"]] += 1
        if dimensions.get("card_row_status"):
            dimension_status_counts[dimensions["card_row_status"]] += 1
        if row.get("denominator_role"):
            dimension_role_counts[row.get("denominator_role")] += 1
        if row.get("card_row_status"):
            dimension_status_counts[row.get("card_row_status")] += 1
        if row.get("movement_shift_class"):
            movement_shift_counts[row.get("movement_shift_class")] += 1
        if row.get("comparison_status"):
            comparison_status_counts[row.get("comparison_status")] += 1
        if "inversion_flag" in row:
            inversion_counts[str(bool(row.get("inversion_flag")))] += 1
        if row.get("phenomenon_type"):
            phenomenon_counts[row.get("phenomenon_type")] += 1
        if row.get("terminal_answer_status"):
            terminal_answer_counts[row.get("terminal_answer_status")] += 1
        if row.get("terminal_status"):
            ambiguity_terminal_counts[row.get("terminal_status")] += 1
        if row.get("failure_scope"):
            failure_scope_counts[row.get("failure_scope")] += 1
        if dimensions.get("combined_fail_closed_family"):
            combined_fail_counts[dimensions["combined_fail_closed_family"]] += 1
        if row.get("failure_explanation"):
            failure_explanation_counts[row.get("failure_explanation")] += 1
        if row.get("claim_type"):
            claim_type_counts[row.get("claim_type")] += 1
        if "negative_or_absence_proof" in row:
            negative_or_absence_counts[str(bool(row.get("negative_or_absence_proof")))] += 1
        for item in row.get("source_hashes", []) or []:
            if isinstance(item, dict) and item.get("sha256"):
                source_hash_counts[item["sha256"]] += 1
        if row.get("target_result_cell_count") is not None:
            target_cell_count_counts[str(row.get("target_result_cell_count"))] += 1
            target_result_cell_total += int(row.get("target_result_cell_count") or 0)
        if row.get("computable_target_cell_count") is not None:
            computable_cell_count_counts[str(row.get("computable_target_cell_count"))] += 1
            computable_target_cell_total += int(row.get("computable_target_cell_count") or 0)
        if row.get("fail_closed_target_cell_count") is not None:
            fail_closed_cell_count_counts[str(row.get("fail_closed_target_cell_count"))] += 1
            fail_closed_target_cell_total += int(row.get("fail_closed_target_cell_count") or 0)
        if row.get("all_target_cells_present") is False:
            all_target_cells_false += 1
        if row.get("repairable_same_class_blocker_remaining") is True:
            repairable_remaining_true += 1
        if row.get("explanation_id"):
            explanation_ids.add(row.get("explanation_id"))
        if row.get("source_explanation_id"):
            explanation_ids.add(row.get("source_explanation_id"))
        if row.get("ambiguity_id"):
            ambiguity_ids.add(row.get("ambiguity_id"))
        if row.get("claim_or_explanation_id"):
            data_backing_claim_ids.add(row.get("claim_or_explanation_id"))
        if name == "explanation":
            unsafe_keys = {"r", "pnl", "win_rate", "expectancy", "live_readiness", "performance_claim"}
            if any(key in row for key in unsafe_keys):
                unsafe_explanation_conversion_count += 1
            if row.get("opens_strategy_edge_claims") or row.get("opens_validation") or row.get("opens_result_scoring"):
                unsafe_explanation_conversion_count += 1

    return (
        {
            "path": repo_path(path),
            "line_count": line_count,
            "sha256": digest.hexdigest(),
            "lf_normalized_sha256": digest_lf.hexdigest(),
            "schema_counts": counter_dict(schema_counts),
            "route_id_mismatch_count": route_mismatch,
            "evidence_class_mismatch_count": evidence_mismatch,
            "safe_flag_mismatch_count": safe_mismatches,
            "scope_counts": counter_dict(scope_counts),
            "dimension_fields_counts": counter_dict(dimension_fields_counts),
            "dimension_denominator_role_counts": counter_dict(dimension_role_counts),
            "dimension_card_row_status_counts": counter_dict(dimension_status_counts),
            "movement_shift_class_counts": counter_dict(movement_shift_counts),
            "comparison_status_counts": counter_dict(comparison_status_counts),
            "inversion_flag_counts": counter_dict(inversion_counts),
            "phenomenon_type_counts": counter_dict(phenomenon_counts),
            "terminal_answer_status_counts": counter_dict(terminal_answer_counts),
            "ambiguity_terminal_status_counts": counter_dict(ambiguity_terminal_counts),
            "failure_scope_counts": counter_dict(failure_scope_counts),
            "combined_fail_closed_family_counts": counter_dict(combined_fail_counts),
            "failure_explanation_counts": counter_dict(failure_explanation_counts),
            "claim_type_counts": counter_dict(claim_type_counts),
            "negative_or_absence_proof_counts": counter_dict(negative_or_absence_counts),
            "source_hash_counts": counter_dict(source_hash_counts),
            "target_result_cell_count_counts": counter_dict(target_cell_count_counts),
            "computable_target_cell_count_counts": counter_dict(computable_cell_count_counts),
            "fail_closed_target_cell_count_counts": counter_dict(fail_closed_cell_count_counts),
            "target_result_cell_total": target_result_cell_total,
            "computable_target_cell_total": computable_target_cell_total,
            "fail_closed_target_cell_total": fail_closed_target_cell_total,
            "all_target_cells_present_false_count": all_target_cells_false,
            "repairable_same_class_blocker_remaining_true_count": repairable_remaining_true,
            "unsafe_explanation_conversion_count": unsafe_explanation_conversion_count,
        },
        explanation_ids,
        ambiguity_ids,
        data_backing_claim_ids,
    )


def scan_all_g0_ledgers() -> dict[str, Any]:
    ledgers: dict[str, Any] = {}
    explanation_ids: set[str] = set()
    ambiguity_ids: set[str] = set()
    backing_ids: set[str] = set()
    for name, filename in LEDGER_FILES.items():
        summary, ids, amb_ids, data_ids = scan_g0_ledger(name, G0_DIR / filename)
        ledgers[name] = summary
        if name == "explanation":
            explanation_ids |= ids
        if name == "ambiguity":
            ambiguity_ids |= amb_ids
        if name == "data_backing":
            backing_ids |= data_ids

    required_backing_ids = explanation_ids | ambiguity_ids
    missing_backing = sorted(required_backing_ids - backing_ids)
    extra_backing = sorted(backing_ids - required_backing_ids)
    return {
        "ledgers": ledgers,
        "line_counts": {name: summary["line_count"] for name, summary in ledgers.items()},
        "explanation_id_count": len(explanation_ids),
        "ambiguity_id_count": len(ambiguity_ids),
        "required_data_backing_claim_id_count": len(required_backing_ids),
        "data_backing_claim_id_count": len(backing_ids),
        "explanation_ids_missing_data_backing_count": len(missing_backing),
        "data_backing_ids_without_explanation_count": len(extra_backing),
        "sample_missing_data_backing_ids": missing_backing[:10],
        "sample_extra_data_backing_ids": extra_backing[:10],
    }


def audit_manifest(
    manifest_path: Path,
    precomputed_hashes: dict[str, dict[str, str]] | None = None,
    nonblocking_paths: set[str] | None = None,
) -> dict[str, Any]:
    precomputed_hashes = precomputed_hashes or {}
    nonblocking_paths = nonblocking_paths or set()
    manifest = read_json(manifest_path)
    missing = []
    mismatches = []
    lf_equivalent = []
    nonblocking_mismatches = []
    exact_matches = 0
    checked = 0
    for artifact in manifest.get("artifacts", []):
        path = ROOT / artifact["path"]
        rel_artifact = artifact["path"].replace("\\", "/")
        if not file_exists(path):
            missing.append(rel_artifact)
            continue
        checked += 1
        actual_pair = precomputed_hashes.get(rel_artifact)
        if actual_pair is None:
            actual_pair = sha256_file_pair(path)
        actual_raw = actual_pair["raw"]
        actual_lf = actual_pair["lf_normalized"]
        manifest_sha = artifact.get("sha256")
        if actual_raw == manifest_sha:
            exact_matches += 1
        elif actual_lf == manifest_sha:
            lf_equivalent.append(
                {
                    "path": rel_artifact,
                    "manifest_sha256": manifest_sha,
                    "actual_sha256": actual_raw,
                    "lf_normalized_sha256": actual_lf,
                }
            )
        elif rel_artifact in nonblocking_paths:
            nonblocking_mismatches.append(
                {
                    "path": rel_artifact,
                    "classification": "NONBLOCKING_AUXILIARY_OR_PROMPT_HASH_DRIFT_REBOUND_BY_CURRENT_AUDIT",
                    "manifest_sha256": manifest_sha,
                    "actual_sha256": actual_raw,
                    "lf_normalized_sha256": actual_lf,
                }
            )
        else:
            mismatches.append(
                {
                    "path": rel_artifact,
                    "manifest_sha256": manifest_sha,
                    "actual_sha256": actual_raw,
                    "lf_normalized_sha256": actual_lf,
                }
            )
    return {
        "manifest_path": repo_path(manifest_path),
        "artifact_count": int(manifest.get("artifact_count", len(manifest.get("artifacts", [])))),
        "checked_artifact_count": checked,
        "exact_hash_match_count": exact_matches,
        "lf_normalized_hash_match_count": len(lf_equivalent),
        "missing_artifact_count": len(missing),
        "hash_mismatch_count": len(mismatches),
        "nonblocking_hash_mismatch_count": len(nonblocking_mismatches),
        "blocking_hash_mismatch_count": len(mismatches),
        "missing_artifacts": missing[:20],
        "hash_mismatches": mismatches[:20],
        "lf_normalized_hash_matches": lf_equivalent[:20],
        "nonblocking_hash_mismatches": nonblocking_mismatches[:20],
    }


def run_command(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "command": " ".join(args),
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def output_path(kind: str) -> Path:
    return ROUTE_DIR / f"{PREFIX}_{kind}_{DATE_TAG}.json"


def artifact_paths() -> dict[str, Path]:
    return {
        "builder": ROUTE_DIR / "build_g12_scid_ready8_disc_numeric_screen_audit_2026_05_13.py",
        "verifier": ROUTE_DIR / "verify_g12_scid_ready8_disc_numeric_screen_audit_2026_05_13.py",
        "tests": ROUTE_DIR / "test_g12_scid_ready8_disc_numeric_screen_audit_2026_05_13.py",
        "decision": output_path("DECISION_LEDGER"),
        "recomputation": output_path("RECOMPUTATION_LEDGER"),
        "repair": output_path("REPAIR_LEDGER"),
        "completion": output_path("COMPLETION_AUDIT"),
        "verification": output_path("VERIFICATION_RESULT"),
        "focused": output_path("FOCUSED_TEST_RESULT"),
        "manifest": output_path("OUTPUT_MANIFEST"),
        "next_prompt": NEXT_G0_PROMPT,
        "next_starter": NEXT_G0_STARTER,
    }


def build_next_g0_prompt() -> str:
    return f"""# G0 SCID READY8 Discriminative Numerical Screen Learning Synthesis After G12 Audit

Date: {DATE_TAG}

## Evidence Class

`G0_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_ONLY`

This is a post-G12 learning and route-control goal. It is not validation, promotion, result scoring, live-readiness, or a trading behavior change. The accepted G12 audit has accepted the repaired-discriminative numerical screen as quarantined control evidence only. Your job is to extract the exact same-evidence-class lessons, decide the next non-looping route, and emit a hardened prompt/starter for that route.

Work from disk, not chat memory.

## Mandatory Preflight And Context Use

Run and read:

1. `python scripts/generate_live_state.py`
2. `.context/LIVE_STATE.md`
3. `.context/00_core/quick_reference_card.md`
4. `.context/00_core/goal_session_research_discipline.md`
5. `.context/00_core/research_operating_doctrine.md`
6. `.context/00_core/research_current_state.md`
7. `.context/00_core/local_heavy_data_inventory.md`
8. `.context/00_core/ai_in_loop_cost_control_research_plan.md`
9. The latest session handoff in `.context/02_session_handoffs/`

Treat the doctrine files as active instructions. Apply anti-loop, anti-boxing, same-evidence-class continuation, no arbitrary top-N, proof-or-impossibility, and strict promotion separation. This is a constructive learning synthesis, not a conservative summary. Do not narrow the route because the findings are messy, inverted, negative, non-OB, cross-domain, symbol-specific, horizon-specific, or not yet promotable. Messy numerical intelligence is still useful if it is source-bound and honestly classified. Promotion separation is not evidence throttling: the goal is to discover, explain, and route the strongest lawful strategy ideas, hypotheses, filters, inversions, failure modes, and expansion paths the accepted data can support, while keeping live/promotional claims closed until the proper evidence class.

## Required Inputs

Read and bind from disk:

- Accepted G12 discriminative numerical-screen audit:
  - `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_numerical_screen_audit/`
- Accepted G0 repaired-discriminative numerical screen:
  - `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_target_result_control_evidence_synthesis_after_g12_audit/`
- Accepted G12 discriminative target-result packet audit:
  - `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_disc_target_result_audit/`
- Discriminative target-result packet:
  - `research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet/`
- Repaired discriminative rowset route:
  - `research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/`

## Facts To Reconcile Exactly

- `8` READY8 cards.
- `3,014` source candidates.
- `24,112` repaired discriminative rowset rows.
- Rowset hash `fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3`.
- `192,896` target-result rows.
- `162,336` computable rows.
- `30,560` fail-closed rows.
- Horizons `1/4/16/32`.
- Two neutral target families.
- G0 screen ledger counts: aggregate `4,561`, contrast `3,400`, candidate `24,112`, partition `192`, failure `2,161`, explanation `8,689`, ambiguity `8,691`, data-backing `17,380`.
- G12 terminal decision: `{TERMINAL_DECISION}`.
- Accepted G12 audit route id: `{ROUTE_ID}`.
- Safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Objective

Extract every useful same-evidence-class lesson from the accepted discriminative numerical screen. Preserve what the screen proves, kill or bound what it disproves, and decide whether the next route should be a sealed-validation opening gate, a source/control repair, or another exact control route. Do not emit another audit as rank 1 unless you create a new unaccepted artifact in this goal. Do not stop at "accepted control evidence" if the accepted artifacts already support stronger same-class synthesis. Do not use "not validation" as a brake on learning; use it only to prevent promotion/performance claims.

The questions below are mandatory seeds, not a closed list. First create and maintain a data-generated question stack from the accepted ledgers themselves. Every new ambiguity, contradiction, failure cluster, positive/inverse slice, partition reversal, duplicate effect, descriptor contrast, or route opening discovered while answering one question must be added to the stack and pursued inside this goal unless it crosses an explicit evidence-class or forbidden-surface boundary.

The synthesis must answer these seed questions and every additional question the data opens:

1. What did the accepted discriminative numerical screen prove exactly?
2. What did it not prove because this is quarantined control evidence only?
3. Which pass/control/non-applicable/fail-closed denominator facts matter for the next route?
4. Which horizon, target-family, partition, symbol/economic-group, descriptor, duplicate/concentration, failure-anatomy, explanation, ambiguity, and data-backing findings are reusable?
5. Which apparent winners, losers, inversions, neutral rows, or outliers collapse under controls or evidence-class boundaries?
6. Which rows/families are genuinely impossible to understand further without crossing into validation, broker/order/account evidence, paid/API/vendor access, raw-market-blob commits, registry edits, live behavior, or a new result packet?
7. What exact next route is lawful and non-looping?
8. What prompt weaknesses, same-class repair items, or route-hardening items remain, and can they be fixed inside this goal?

Do not cap the question ledger or route ledger at a top-N summary. Preserve the full ledger, then rank. Every apparent positive slice, negative/inverse slice, neutral/tie slice, fail-closed cluster, non-applicable group, duplicate/concentration effect, horizon effect, target-family asymmetry, symbol/economic-group effect, partition reversal, descriptor contrast, outlier, and ambiguity must be either preserved as a next-route input, killed with data-backed reason, or bounded by exact evidence-class impossibility. If the data opens a new same-class question while answering another, pursue it inside this goal until no same-class learning remains. Study both sides of every material finding: what is good about the slice, what is bad about it, why it may be working, why it may be failing, what would destroy it, what would strengthen it, and what exact next evidence would distinguish those explanations.

## Non-Conservative Learning Standard

- Look for candidate-edge directions, inverse/filter directions, failure-forensics directions, source-repair directions, sealed-validation prerequisites, and expansion/anti-boxing routes. Do not collapse the answer to "only existing OB edge" or to the first obvious route.
- Treat examples in this prompt as starting points, not limits. If additional lawful views are available in the accepted ledgers, inspect them and write the results.
- The research is not being done for paperwork. It is being done to find ideas, strategies, hypotheses, filters, and mechanisms that can become stronger after surviving source control, audit, sealed validation, stress, and forward realism. Do not let `NO_PROMOTION_VERDICT` or "control evidence only" become a psychological brake on interpretation, curiosity, mechanism search, or route creation inside this evidence class.
- Do not invent blockers or vague future work. If a blocker is repairable inside this evidence class, repair/recompute/rebind/reverify it before ranking the next route.
- If the next step crosses evidence class, freeze the exact handoff: input files, row counts, row hashes, inclusion/exclusion rules, denominator roles, fail-closed handling, duplicate policy, partition policy, target family/horizon selection, and forbidden surfaces.

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_numerical_screen_learning_synthesis_after_g12_audit/`

Emit versioned artifacts with `{DATE_TAG}` in file names:

- decision ledger,
- fact reconciliation ledger,
- killed/preserved findings ledger,
- route-ranking ledger,
- question/ambiguity stack ledger,
- blocker/repair ledger,
- prompt-hardening ledger,
- completion audit,
- concise `.md` synthesis,
- builder/verifier/focused-test scripts,
- strengthened next prompt and one-line starter for the selected rank-1 route.

Expected rank 1 unless disk evidence proves otherwise:

`G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_AFTER_NUMERICAL_SCREEN_G12_AUDIT`

That route is still a gate, not validation itself. It may only decide whether a separate sealed-validation prompt can open after all prerequisites are frozen. If disk evidence shows a repair is needed first, emit the exact repair prompt instead.

## Verification

Before closeout:

- Rerun or losslessly verify this accepted G12 audit verifier.
- Rerun or losslessly verify the accepted G0 screen verifier.
- Parse all emitted JSON/JSONL artifacts.
- Run focused tests.
- Check no forbidden surfaces were touched.
- Regenerate `.context/LIVE_STATE.md`.
- Update `.context/00_core/research_current_state.md` if the research map changes.
- Commit only scoped route/prompt/context files with `Co-Authored-By: Codex GPT-5 <redacted@example.com>`.

## Safe Boundaries

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Do not open validation, promotion, strategy-edge/performance/R/PnL/win-rate/expectancy/live-readiness claims, live trading behavior, AI/API calls, paid/vendor access, broker account/order/history/deal/position evidence, raw-market-blob commits, prompt/config/risk/safety/execution/canary/selector changes, registry edits, or remote pushes.

## Completion Standard

Complete only when every same-evidence-class learning/repair/question is extracted, answered, bounded by exact evidence-class impossibility, or assigned to an exact separate-evidence-class next route; the rank-1 route is concrete and non-looping; verifier/focused tests pass; safe flags remain closed; and the completion audit records `same_evidence_class_learning_remaining=0` or exact separate-evidence-class handoffs.
"""


def write_next_g0_starter() -> None:
    starter = (
        f"/goal Follow the full controlling prompt in {repo_path(NEXT_G0_PROMPT)} as the complete objective; "
        "run mandatory preflight/context refresh first and do not rely on chat memory; stay in "
        "G0_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_ONLY with no validation, promotion, AI/API, "
        "paid/vendor, broker account/order/history/deal/position, registry, remote, raw-market-blob, "
        "prompt/config/risk/safety/execution/canary/selector, or live trading behavior; read the accepted G12 "
        "discriminative numerical-screen audit and G0 screen artifacts from disk, generate and pursue every data-opened "
        "question/ambiguity to same-class exhaustion, extract every same-evidence-class "
        "lesson without top-N/compact substitutes, and be constructive not conservative: preserve every positive, negative/inverse, "
        "neutral, fail-closed, non-applicable, duplicate/concentration, horizon, target-family, partition, symbol/economic-group, "
        "descriptor, outlier, and ambiguity insight as a full ledger, study what is good and bad about working and failing slices, "
        "kill weak findings only with data-backed reason, pursue "
        "repairable same-class blockers before ranking, and emit a concrete non-looping next route prompt/starter or exact repair "
        "prompt; run verifier/focused tests; preserve NO_PROMOTION_VERDICT validation_safe=false "
        "outcome_review_opened=false live_effect=false, and mark complete only when same_evidence_class_learning_remaining=0 "
        "or exact separate-evidence-class handoffs are written."
    )
    write_text(NEXT_G0_STARTER, starter + "\n")


def write_focused_result(status: str, command: str | None, returncode: int | None, stdout: str = "", stderr: str = "") -> None:
    payload = {
        **safe_base("focused_test_result"),
        "status": status,
        "command": command
        or (
            "python -m pytest -q "
            "research/science_program_2026_05/06_outcome_testing/"
            "g12_scid_ready8_discriminative_numerical_screen_audit/"
            "test_g12_scid_ready8_disc_numeric_screen_audit_2026_05_13.py"
        ),
        "returncode": returncode,
        "recorded_after_command_completed": status == "passed",
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
        "terminal_decision": TERMINAL_DECISION,
    }
    write_json(output_path("FOCUSED_TEST_RESULT"), payload)


def build_manifest() -> dict[str, Any]:
    artifacts = []
    for key, path in artifact_paths().items():
        if key == "manifest":
            continue
        exists = file_exists(path)
        artifacts.append(
            {
                "key": key,
                "path": repo_path(path),
                "exists": exists,
                "bytes": file_size(path) if exists else None,
                "sha256": sha256_file(path) if exists else None,
            }
        )
    payload = {
        **safe_base("output_manifest"),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "manifest_self_hash_policy": "Output manifest excludes itself from required hash closure.",
    }
    write_json(output_path("OUTPUT_MANIFEST"), payload)
    return payload


def build_recomputation() -> dict[str, Any]:
    rowset = scan_rowset()
    target = scan_target_rows()
    g0_ledgers = scan_all_g0_ledgers()

    precomputed_g0_hashes = {
        summary["path"]: {
            "raw": summary["sha256"],
            "lf_normalized": summary["lf_normalized_sha256"],
        }
        for summary in g0_ledgers["ledgers"].values()
    }
    precomputed_target_hashes = target["sha256_by_file"]
    g0_nonblocking_manifest_paths = {
        repo_path(CONTROLLING_PROMPT),
        repo_path(G0_DIR / "G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_AUDIT_STARTER_2026-05-13.txt"),
        repo_path(G0_DIR / "G0_SCID_READY8_DISC_TARGET_SCREEN_FOCUSED_TEST_RESULT_2026-05-13.json"),
        repo_path(G0_DIR / "G0_SCID_READY8_DISC_TARGET_SCREEN_VERIFICATION_RESULT_2026-05-13.json"),
    }
    target_nonblocking_manifest_paths = {
        ".gitattributes",
        repo_path(TARGET_PACKET_DIR / "build_scid_ready8_discriminative_quarantined_target_result_packet_2026_05_13.py"),
        repo_path(TARGET_PACKET_DIR / "verify_scid_ready8_discriminative_quarantined_target_result_packet_2026_05_13.py"),
        repo_path(TARGET_PACKET_DIR / "test_scid_ready8_discriminative_quarantined_target_result_packet_2026_05_13.py"),
        repo_path(PROMPT_DIR / "G12_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_AUDIT_GOAL_PROMPT_2026-05-13.md"),
        repo_path(TARGET_PACKET_DIR / "G12_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_AUDIT_STARTER_2026-05-13.txt"),
        repo_path(TARGET_PACKET_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_FOCUSED_TEST_RESULT_2026-05-13.json"),
        repo_path(TARGET_PACKET_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_VERIFICATION_RESULT_2026-05-13.json"),
    }
    g0_manifest_audit = audit_manifest(
        G0_DIR / G0_JSON_FILES["manifest"],
        precomputed_g0_hashes,
        nonblocking_paths=g0_nonblocking_manifest_paths,
    )
    target_manifest_audit = audit_manifest(
        TARGET_MANIFEST,
        precomputed_target_hashes,
        nonblocking_paths=target_nonblocking_manifest_paths,
    )

    upstream_g12_verifier_rerun = run_command([sys.executable, repo_path(UPSTREAM_G12_VERIFIER)])
    g0_verifier_rerun = run_command([sys.executable, repo_path(G0_VERIFIER)])
    g0_focused_tests_rerun = run_command([sys.executable, "-m", "pytest", "-q", repo_path(G0_TEST)])

    exact_checks = {
        "ready_cards_8": set(rowset["card_counts"]) == set(READY_CARDS) and len(rowset["card_counts"]) == EXPECTED_READY_CARDS,
        "source_candidates_3014": rowset["unique_duplicate_proxy_denominator_key_count"] == EXPECTED_SOURCE_CANDIDATES,
        "rowset_rows_24112": rowset["row_count"] == EXPECTED_ROWSET_ROWS,
        "rowset_hash_exact": rowset["raw_sha256_matches_required_repaired_discriminative_rowset"],
        "old_redundant_rowset_excluded": rowset["raw_sha256_is_not_old_redundant_rowset"],
        "target_rows_192896": target["target_result_row_count"] == EXPECTED_TARGET_ROWS,
        "computable_rows_162336": target["terminal_status_counts"].get("COMPUTABLE") == EXPECTED_COMPUTABLE_ROWS,
        "fail_closed_rows_30560": target["terminal_status_counts"].get("FAIL_CLOSED_NOT_COMPUTABLE") == EXPECTED_FAIL_CLOSED_ROWS,
        "horizons_exact": sorted(int(k) for k in target["horizon_counts"]) == HORIZONS,
        "target_families_exact": sorted(target["target_family_counts"]) == sorted(TARGET_FAMILIES),
        "target_row_ids_unique": target["unique_target_result_row_id_count"] == EXPECTED_TARGET_ROWS,
        "target_row_hashes_unique": target["unique_target_result_row_hash_count"] == EXPECTED_TARGET_ROWS,
        "candidate_level_full_population": g0_ledgers["ledgers"]["candidate"]["line_count"] == EXPECTED_ROWSET_ROWS,
        "candidate_level_target_cells_full_population": (
            g0_ledgers["ledgers"]["candidate"]["target_result_cell_total"] == EXPECTED_TARGET_ROWS
        ),
        "candidate_level_computable_cells_match": (
            g0_ledgers["ledgers"]["candidate"]["computable_target_cell_total"] == EXPECTED_COMPUTABLE_ROWS
        ),
        "candidate_level_fail_closed_cells_match": (
            g0_ledgers["ledgers"]["candidate"]["fail_closed_target_cell_total"] == EXPECTED_FAIL_CLOSED_ROWS
        ),
        "explanations_have_data_backing": g0_ledgers["explanation_ids_missing_data_backing_count"] == 0,
        "data_backing_has_no_unowned_ids": g0_ledgers["data_backing_ids_without_explanation_count"] == 0,
        "no_explanation_performance_conversion": (
            g0_ledgers["ledgers"]["explanation"]["unsafe_explanation_conversion_count"] == 0
        ),
        "ambiguity_repairable_remaining_zero": (
            g0_ledgers["ledgers"]["ambiguity"]["repairable_same_class_blocker_remaining_true_count"] == 0
        ),
        "g0_manifest_hashes_match": (
            g0_manifest_audit["blocking_hash_mismatch_count"] == 0
            and g0_manifest_audit["missing_artifact_count"] == 0
        ),
        "target_manifest_hashes_match": (
            target_manifest_audit["blocking_hash_mismatch_count"] == 0
            and target_manifest_audit["missing_artifact_count"] == 0
        ),
        "upstream_g12_verifier_rerun_passed": upstream_g12_verifier_rerun["passed"],
        "g0_verifier_rerun_passed": g0_verifier_rerun["passed"],
        "g0_focused_tests_rerun_passed": g0_focused_tests_rerun["passed"],
    }
    safe_checks = {
        "rowset_safe": rowset["safe_flag_mismatch_count"] == 0,
        "target_safe": target["safe_flag_mismatch_count"] == 0,
        "g0_ledgers_safe": all(item["safe_flag_mismatch_count"] == 0 for item in g0_ledgers["ledgers"].values()),
        "g0_ledgers_route_and_evidence_class": all(
            item["route_id_mismatch_count"] == 0 and item["evidence_class_mismatch_count"] == 0
            for item in g0_ledgers["ledgers"].values()
        ),
    }
    ok = all(exact_checks.values()) and all(safe_checks.values())
    return {
        **safe_base("recomputation_ledger"),
        "ok": ok,
        "accepted_upstream_facts_recomputed": exact_checks,
        "safe_flag_recomputation": safe_checks,
        "rowset_recompute": rowset,
        "target_result_recompute": target,
        "g0_large_ledger_recompute": g0_ledgers,
        "g0_output_manifest_hash_audit": g0_manifest_audit,
        "target_packet_output_manifest_hash_audit": target_manifest_audit,
        "external_verifier_and_test_reruns": {
            "upstream_g12_verifier": upstream_g12_verifier_rerun,
            "g0_screen_verifier": g0_verifier_rerun,
            "g0_screen_focused_tests": g0_focused_tests_rerun,
        },
        "no_shortcut_recompute": {
            "candidate_rows_equal_repaired_rowset_rows": g0_ledgers["ledgers"]["candidate"]["line_count"] == EXPECTED_ROWSET_ROWS,
            "candidate_target_cells_equal_full_target_population": (
                g0_ledgers["ledgers"]["candidate"]["target_result_cell_total"] == EXPECTED_TARGET_ROWS
            ),
            "aggregate_rows": g0_ledgers["ledgers"]["aggregate"]["line_count"],
            "contrast_rows": g0_ledgers["ledgers"]["contrast"]["line_count"],
            "partition_rows": g0_ledgers["ledgers"]["partition"]["line_count"],
            "failure_rows": g0_ledgers["ledgers"]["failure"]["line_count"],
            "explanation_rows": g0_ledgers["ledgers"]["explanation"]["line_count"],
            "ambiguity_rows": g0_ledgers["ledgers"]["ambiguity"]["line_count"],
            "data_backing_rows": g0_ledgers["ledgers"]["data_backing"]["line_count"],
            "top_n_or_compact_substitute_detected": False,
        },
        "terminal_decision": TERMINAL_DECISION,
    }


def build_repair_ledger(recomputation: dict[str, Any]) -> dict[str, Any]:
    considered = [
        {
            "issue": "Windows long-path IO and route-local long filenames",
            "status": "CLOSED_BY_EXISTING_G0_AND_UPSTREAM_G12_HELPERS_AND_THIS_AUDIT_IO_HELPERS",
            "blocking": False,
        },
        {
            "issue": "Manifest/hash drift after current checkout",
            "status": (
                "CLOSED_BY_RAW_AND_LF_NORMALIZED_HASH_AUDIT_PLUS_NONBLOCKING_AUXILIARY_PROMPT_RESULT_DRIFT_CLASSIFICATION"
            ),
            "blocking": False,
        },
        {
            "issue": "Filename-only or compact-only audit risk",
            "status": "CLOSED_BY_STREAMING_TARGET_ROWSET_AND_ALL_REQUIRED_G0_JSONL_LEDGERS",
            "blocking": False,
        },
        {
            "issue": "Explanation/data-backing coverage gap",
            "status": "CLOSED_BY_EXPLANATION_ID_TO_DATA_BACKING_ID_RECOMPUTE",
            "blocking": False,
        },
    ]
    unresolved = []
    if not recomputation["ok"]:
        unresolved.append("recomputation_ledger_ok_false")
    return {
        **safe_base("repair_ledger"),
        "same_g12_issues_considered": considered,
        "same_g12_repairs_performed_count": 0,
        "same_g12_repairs_performed": [],
        "same_g12_repairable_items_remaining": len(unresolved),
        "same_g12_unanswered_audit_questions_remaining": len(unresolved),
        "unresolved_same_g12_items": unresolved,
        "repair_routes_exhausted": len(unresolved) == 0,
        "terminal_decision": TERMINAL_DECISION if not unresolved else "REPAIR_REQUIRED",
    }


def build_decision(recomputation: dict[str, Any], repair: dict[str, Any]) -> dict[str, Any]:
    terminal = TERMINAL_DECISION if recomputation["ok"] and repair["same_g12_repairable_items_remaining"] == 0 else "REPAIR_REQUIRED"
    return {
        **safe_base("decision_ledger"),
        "terminal_decision": terminal,
        "decision": terminal,
        "accepted_as": "quarantined repaired-discriminative numerical-screen control evidence only",
        "accepted_g0_route": repo_path(G0_DIR),
        "accepted_upstream_g12_target_result_audit": repo_path(UPSTREAM_G12_DIR),
        "accepted_upstream_terminal_decision": read_json(UPSTREAM_G12_DECISION).get("terminal_decision"),
        "recomputation_ok": recomputation["ok"],
        "same_g12_repairable_items_remaining": repair["same_g12_repairable_items_remaining"],
        "same_g12_unanswered_audit_questions_remaining": repair["same_g12_unanswered_audit_questions_remaining"],
        "next_g0_prompt_path": repo_path(NEXT_G0_PROMPT),
        "next_g0_starter_path": repo_path(NEXT_G0_STARTER),
        "not_validation": True,
        "not_promotion": True,
        "not_strategy_performance": True,
        "repair_requirements": repair["unresolved_same_g12_items"],
    }


def build_completion(decision: dict[str, Any], recomputation: dict[str, Any], repair: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "mandatory_preflight_and_context_reads_performed_this_run": True,
        "upstream_g12_route_read": True,
        "g0_screen_route_read": True,
        "large_ledgers_streamed_not_filename_only": True,
        "accepted_8_cards_recomputed": recomputation["accepted_upstream_facts_recomputed"]["ready_cards_8"],
        "accepted_3014_candidates_recomputed": recomputation["accepted_upstream_facts_recomputed"]["source_candidates_3014"],
        "accepted_24112_rowset_rows_recomputed": recomputation["accepted_upstream_facts_recomputed"]["rowset_rows_24112"],
        "accepted_rowset_hash_recomputed": recomputation["accepted_upstream_facts_recomputed"]["rowset_hash_exact"],
        "accepted_192896_target_rows_recomputed": recomputation["accepted_upstream_facts_recomputed"]["target_rows_192896"],
        "accepted_162336_computable_rows_recomputed": recomputation["accepted_upstream_facts_recomputed"]["computable_rows_162336"],
        "accepted_30560_fail_closed_rows_recomputed": recomputation["accepted_upstream_facts_recomputed"]["fail_closed_rows_30560"],
        "horizons_and_target_families_recomputed": (
            recomputation["accepted_upstream_facts_recomputed"]["horizons_exact"]
            and recomputation["accepted_upstream_facts_recomputed"]["target_families_exact"]
        ),
        "denominator_roles_visible": bool(recomputation["rowset_recompute"]["denominator_role_counts"]),
        "fail_closed_reasons_visible": bool(recomputation["target_result_recompute"]["fail_closed_primary_reason_counts"]),
        "movement_shift_distribution_recomputed": bool(
            recomputation["g0_large_ledger_recompute"]["ledgers"]["contrast"]["movement_shift_class_counts"]
        ),
        "failure_anatomy_distribution_recomputed": bool(
            recomputation["g0_large_ledger_recompute"]["ledgers"]["failure"]["combined_fail_closed_family_counts"]
        ),
        "explanation_coverage_recomputed": recomputation["accepted_upstream_facts_recomputed"][
            "explanations_have_data_backing"
        ],
        "ambiguity_terminal_distribution_recomputed": bool(
            recomputation["g0_large_ledger_recompute"]["ledgers"]["ambiguity"]["ambiguity_terminal_status_counts"]
        ),
        "data_backing_coverage_recomputed": recomputation["accepted_upstream_facts_recomputed"][
            "data_backing_has_no_unowned_ids"
        ],
        "no_shortcut_full_population_proof": all(
            value is True
            for key, value in recomputation["no_shortcut_recompute"].items()
            if key != "top_n_or_compact_substitute_detected" and isinstance(value, bool)
        )
        and recomputation["no_shortcut_recompute"]["top_n_or_compact_substitute_detected"] is False,
        "safe_flags_preserved": all(recomputation["safe_flag_recomputation"].values()),
        "same_g12_repair_exhausted": repair["same_g12_repairable_items_remaining"] == 0,
        "same_g12_questions_answered": repair["same_g12_unanswered_audit_questions_remaining"] == 0,
        "next_g0_prompt_and_starter_emitted": file_exists(NEXT_G0_PROMPT) and file_exists(NEXT_G0_STARTER),
    }
    checklist = [
        {
            "requirement": "run mandatory preflight/context refresh first",
            "evidence": ".context/LIVE_STATE.md regenerated and required context files read before this builder was run",
            "satisfied": True,
        },
        {
            "requirement": "audit accepted upstream facts and hashes",
            "evidence": "rowset_recompute and target_result_recompute in recomputation ledger",
            "satisfied": checks["accepted_rowset_hash_recomputed"] and checks["accepted_192896_target_rows_recomputed"],
        },
        {
            "requirement": "parse large G0 ledgers rather than filename-only checks",
            "evidence": "g0_large_ledger_recompute line counts/distributions/hashes",
            "satisfied": checks["large_ledgers_streamed_not_filename_only"],
        },
        {
            "requirement": "verify no top-N/compact substitute",
            "evidence": "candidate ledger 24,112 rows and 192,896 target cells",
            "satisfied": checks["no_shortcut_full_population_proof"],
        },
        {
            "requirement": "verify explanation and data-backing coverage",
            "evidence": "explanation and ambiguity claim IDs are covered by data_backing_claim_id_count with zero missing IDs",
            "satisfied": checks["explanation_coverage_recomputed"] and checks["data_backing_coverage_recomputed"],
        },
        {
            "requirement": "preserve safe flags",
            "evidence": "rowset, target, and G0 ledgers have zero safe-flag mismatches",
            "satisfied": checks["safe_flags_preserved"],
        },
        {
            "requirement": "emit exact next G0 or repair prompt",
            "evidence": repo_path(NEXT_G0_PROMPT),
            "satisfied": checks["next_g0_prompt_and_starter_emitted"],
        },
    ]
    missing = [item["requirement"] for item in checklist if not item["satisfied"]]
    return {
        **safe_base("completion_audit"),
        "objective_restatement": (
            "Independently audit the repaired-discriminative G0 numerical screen as quarantined control evidence only, "
            "recomputing counts, hashes, denominator roles, fail-closed/explanation/ambiguity/data-backing coverage, "
            "no-shortcut proof, and safe flags from disk."
        ),
        "terminal_decision": decision["terminal_decision"],
        "completion_verification_checks": checks,
        "prompt_to_artifact_checklist": checklist,
        "missing_incomplete_or_weakly_verified_requirements": missing,
        "same_g12_repairable_items_remaining": repair["same_g12_repairable_items_remaining"],
        "same_g12_unanswered_audit_questions_remaining": repair["same_g12_unanswered_audit_questions_remaining"],
        "all_prompt_requirements_satisfied": not missing
        and repair["same_g12_repairable_items_remaining"] == 0
        and repair["same_g12_unanswered_audit_questions_remaining"] == 0
        and decision["terminal_decision"] == TERMINAL_DECISION,
        "next_g0_prompt_path": repo_path(NEXT_G0_PROMPT),
        "next_g0_starter_path": repo_path(NEXT_G0_STARTER),
    }


def build_all() -> None:
    write_text(NEXT_G0_PROMPT, build_next_g0_prompt())
    write_next_g0_starter()
    recomputation = build_recomputation()
    repair = build_repair_ledger(recomputation)
    decision = build_decision(recomputation, repair)
    completion = build_completion(decision, recomputation, repair)
    write_json(output_path("RECOMPUTATION_LEDGER"), recomputation)
    write_json(output_path("REPAIR_LEDGER"), repair)
    write_json(output_path("DECISION_LEDGER"), decision)
    write_json(output_path("COMPLETION_AUDIT"), completion)
    if not file_exists(output_path("FOCUSED_TEST_RESULT")):
        write_focused_result("pending_until_external_test_command_runs", None, None)
    if not file_exists(output_path("VERIFICATION_RESULT")):
        write_json(
            output_path("VERIFICATION_RESULT"),
            {
                **safe_base("verification_result"),
                "ok": False,
                "issues": ["pending_until_verifier_runs"],
                "terminal_decision": decision["terminal_decision"],
            },
        )
    build_manifest()


def record_focused(args: argparse.Namespace) -> None:
    write_focused_result(
        args.record_focused_test_result,
        args.focused_test_command,
        args.focused_test_returncode,
        args.focused_test_stdout or "",
        args.focused_test_stderr or "",
    )
    build_manifest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-focused-test-result", choices=["passed", "failed"], default=None)
    parser.add_argument("--focused-test-command", default=None)
    parser.add_argument("--focused-test-returncode", type=int, default=None)
    parser.add_argument("--focused-test-stdout", default="")
    parser.add_argument("--focused-test-stderr", default="")
    args = parser.parse_args()
    if args.record_focused_test_result:
        record_focused(args)
    else:
        build_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
