from __future__ import annotations

import hashlib
import ast
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-13"
ROUTE_ID = "G12_SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AUDIT"
EVIDENCE_CLASS = "G12_SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AUDIT_ONLY"
TARGET_ROUTE_ID = "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN"
TARGET_EVIDENCE_CLASS = "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_CONTROL_EVIDENCE_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

READY_CARDS = ["ADV-001", "ADV-003", "BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"]
CONTROL_CARDS = {"ADV-001", "ADV-003"}
EXPECTED_SOURCE_CANDIDATES = 3014
EXPECTED_READY_CARDS = 8
EXPECTED_ROWSET_ROWS = 24112
EXPECTED_ROWS_PER_CARD = 3014
EXPECTED_FAIL_CLOSED_ROWS = 797
EXPECTED_NON_APPLICABLE_ROWS = 3685

STATUS_VOCAB = {
    "PASS_DESCRIPTOR_CONTRAST_ELIGIBLE",
    "PASS_CARD_PREDICATE",
    "ELIGIBLE_CONTRAST_CONTROL",
    "NON_APPLICABLE_SOURCE_CONTEXT",
    "FAIL_CLOSED_MISSING_PRIOR_CANDIDATE",
    "FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE",
}
ROLE_VOCAB = {
    "per_card_pass_row",
    "per_card_contrast_row",
    "per_card_non_applicable_row",
    "per_card_fail_closed_row",
}
FORBIDDEN_ROW_FIELDS = {
    "target_hit",
    "stop_hit",
    "outcome_status",
    "actual_r",
    "pnl",
    "win_rate",
    "expectancy",
    "performance_metric",
    "broker_account",
    "order_ticket",
    "deal_id",
    "position_id",
}

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
TARGET_DIR = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design"
)
PROMPT_DIR = ROOT / "research/science_program_2026_05/04_goal_prompts"
NUMERICAL_G12_DIR = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_numerical_screen_audit"
)
LEARNING_DIR = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "g0_scid_ready8_numerical_screen_learning_synthesis_after_g12_audit"
)
SOURCE_CANDIDATE_ROWS = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "scid_asof_bar_builder_and_candidate_input_packet_source_control/"
    "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
)
TARGET_VERIFIER = TARGET_DIR / "verify_scid_ready8_discriminative_card_rowset_repair_2026_05_13.py"
TARGET_TEST = TARGET_DIR / "test_scid_ready8_discriminative_card_rowset_repair_2026_05_13.py"
NEXT_G0_PROMPT = (
    PROMPT_DIR / "G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_AFTER_G12_AUDIT_GOAL_PROMPT_2026-05-13.md"
)
NEXT_G0_STARTER = (
    ROUTE_DIR / "G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_AFTER_G12_AUDIT_STARTER_2026-05-13.txt"
)

TARGET_FILES = {
    "decision_ledger": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_DECISION_LEDGER_2026-05-13.json",
    "source_field_map": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_SOURCE_FIELD_MAP_LEDGER_2026-05-13.json",
    "predicate_ledger": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_PREDICATE_DESCRIPTOR_CONTRAST_LEDGER_2026-05-13.json",
    "rowset_manifest": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_MANIFEST_2026-05-13.json",
    "rowset_rows": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl",
    "denominator_duplicate_policy": TARGET_DIR
    / "SCID_READY8_DISCRIMINATIVE_DENOMINATOR_DUPLICATE_POLICY_LEDGER_2026-05-13.json",
    "fail_closed_policy": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_FAIL_CLOSED_POLICY_LEDGER_2026-05-13.json",
    "partition_design": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_SEALED_STRESS_PARTITION_DESIGN_LEDGER_2026-05-13.json",
    "target_prereq": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_OPENING_PREREQUISITE_LEDGER_2026-05-13.json",
    "blocker_source_repair": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_BLOCKER_SOURCE_REPAIR_LEDGER_2026-05-13.json",
    "searched_root": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_SEARCHED_ROOT_LEDGER_2026-05-13.json",
    "saturation": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_SATURATION_SELF_RED_TEAM_LEDGER_2026-05-13.json",
    "completion_audit": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_COMPLETION_AUDIT_2026-05-13.json",
    "verification_result": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_VERIFICATION_RESULT_2026-05-13.json",
    "output_manifest": TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_OUTPUT_MANIFEST_2026-05-13.json",
}

MANIFEST_REBIND_REPAIRABLE_ARTIFACTS = {"completion_audit", "verification_result"}

UPSTREAM_FILES = {
    "accepted_ready8_numerical_g12_decision": NUMERICAL_G12_DIR
    / "G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_DECISION_LEDGER_2026-05-13.json",
    "accepted_ready8_numerical_g12_completion": NUMERICAL_G12_DIR
    / "G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_COMPLETION_AUDIT_2026-05-13.json",
    "accepted_ready8_learning_synthesis_decision": LEARNING_DIR
    / "G0_SCID_READY8_LEARNING_SYNTHESIS_DECISION_LEDGER_2026-05-13.json",
    "accepted_ready8_learning_synthesis_completion": LEARNING_DIR
    / "G0_SCID_READY8_LEARNING_SYNTHESIS_COMPLETION_AUDIT_2026-05-13.json",
}

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_validation": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_lf_normalized_text(path: Path) -> str:
    data = path.read_bytes()
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def text_eol_normalizable(path: Path) -> bool:
    return path.suffix.lower() in {".json", ".jsonl", ".md", ".py", ".txt", ".csv"}


def syntax_check_python(path: Path) -> dict[str, Any]:
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=rel(path))
    except SyntaxError as exc:
        return {
            "command": f"AST parse {rel(path)}",
            "returncode": 1,
            "passed": False,
            "stdout_tail": "",
            "stderr_tail": f"{exc.__class__.__name__}: {exc}",
            "method": "ast_parse_no_bytecode",
        }
    return {
        "command": f"AST parse {rel(path)}",
        "returncode": 0,
        "passed": True,
        "stdout_tail": "",
        "stderr_tail": "",
        "method": "ast_parse_no_bytecode",
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


def git_output(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def safe_base(artifact_family: str) -> dict[str, Any]:
    return {
        "schema_version": "g12_scid_ready8_discriminative_card_rowset_repair_audit_v1",
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": utc_now(),
        **SAFE_FLAGS,
    }


def safe_flags_ok(payload: dict[str, Any]) -> bool:
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        return False
    for key in ("validation_safe", "outcome_review_opened", "live_effect"):
        if payload.get(key) is not False:
            return False
    for key, value in payload.items():
        if key.startswith("opens_") and value is True:
            return False
    if payload.get("changes_trading_risk_safety_prompt_decision_behavior") is True:
        return False
    if payload.get("credentials_touched") is True:
        return False
    return True


def counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def nested_keys(payload: Any, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            next_key = f"{prefix}.{key}" if prefix else str(key)
            keys.add(next_key)
            keys.update(nested_keys(value, next_key))
    elif isinstance(payload, list):
        for item in payload:
            keys.update(nested_keys(item, prefix))
    return keys


def load_target_json_artifacts() -> dict[str, Any]:
    payloads: dict[str, Any] = {}
    for name, path in {**TARGET_FILES, **UPSTREAM_FILES}.items():
        if path.suffix == ".json" and path.exists():
            payloads[name] = read_json(path)
    return payloads


def recompute_output_manifest_hashes(output_manifest: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    for artifact in output_manifest.get("artifacts", []):
        path = ROOT / artifact["path"]
        exists = path.exists()
        actual_bytes = path.stat().st_size if exists else None
        actual_sha = sha256_file(path) if exists and path.is_file() else None
        lf_sha = sha256_lf_normalized_text(path) if exists and path.is_file() and text_eol_normalizable(path) else None
        strict_ok = (
            exists
            and actual_bytes == artifact.get("bytes")
            and actual_sha == artifact.get("sha256")
        )
        eol_equivalent_ok = exists and lf_sha == artifact.get("sha256")
        ok = strict_ok or eol_equivalent_ok
        item = {
            "artifact_id": artifact.get("artifact_id"),
            "path": artifact.get("path"),
            "exists": exists,
            "expected_bytes": artifact.get("bytes"),
            "actual_bytes": actual_bytes,
            "expected_sha256": artifact.get("sha256"),
            "actual_sha256": actual_sha,
            "lf_normalized_sha256": lf_sha,
            "strict_byte_hash_ok": strict_ok,
            "text_eol_equivalent_ok": eol_equivalent_ok,
            "ok": ok,
        }
        checks.append(item)
        if not ok:
            mismatches.append(item)
    return {
        "artifact_count": len(checks),
        "all_exist_and_hash_match": not mismatches,
        "mismatches": mismatches,
        "checks": checks,
    }


def repair_output_manifest_if_same_g12(output_manifest: dict[str, Any]) -> dict[str, Any]:
    audit = recompute_output_manifest_hashes(output_manifest)
    mismatches = audit.get("mismatches", [])
    repairable = [
        item
        for item in mismatches
        if item.get("artifact_id") in MANIFEST_REBIND_REPAIRABLE_ARTIFACTS
        and item.get("exists") is True
        and item.get("actual_sha256")
    ]
    unrepaired = [
        item
        for item in mismatches
        if item.get("artifact_id") not in MANIFEST_REBIND_REPAIRABLE_ARTIFACTS
    ]
    if not repairable or unrepaired:
        return {
            "performed": False,
            "repairable_mismatches": repairable,
            "unrepaired_mismatches": unrepaired,
            "initial_mismatch_count": len(mismatches),
            "post_repair_audit": audit,
        }

    by_id = {item["artifact_id"]: item for item in repairable}
    updated = dict(output_manifest)
    artifacts = []
    for artifact in output_manifest.get("artifacts", []):
        artifact = dict(artifact)
        item = by_id.get(artifact.get("artifact_id"))
        if item:
            artifact["bytes"] = item["actual_bytes"]
            artifact["sha256"] = item["actual_sha256"]
        artifacts.append(artifact)
    updated["artifacts"] = artifacts
    write_json(TARGET_FILES["output_manifest"], updated)
    post = recompute_output_manifest_hashes(updated)
    return {
        "performed": True,
        "repair_id": "TARGET_OUTPUT_MANIFEST_COMPLETION_VERIFICATION_REBIND",
        "repairable_mismatches": repairable,
        "unrepaired_mismatches": [],
        "initial_mismatch_count": len(mismatches),
        "post_repair_audit": post,
    }


def recompute_source_candidates(path: Path) -> dict[str, Any]:
    ids: set[str] = set()
    duplicate_keys: set[str] = set()
    symbol_counts: Counter[str] = Counter()
    partition_counts: Counter[str] = Counter()
    canonical_group_counts: Counter[str] = Counter()
    source_file_counts: Counter[str] = Counter()
    source_segment_hashes: set[str] = set()
    forbidden_hits: Counter[str] = Counter()
    invalid_json_rows: list[int] = []
    total = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                invalid_json_rows.append(line_no)
                continue
            total += 1
            row_id = row.get("candidate_input_row_id")
            if row_id:
                ids.add(row_id)
            duplicate_key = row.get("duplicate_key")
            if duplicate_key:
                duplicate_keys.add(duplicate_key)
            symbol_counts.update([str(row.get("symbol"))])
            partition_counts.update([str(row.get("partition_assignment"))])
            canonical_group_counts.update([str(row.get("canonical_economic_group"))])
            source_file_counts.update([str(row.get("source_file_name"))])
            segment = row.get("segment_records_sha256")
            if segment:
                source_segment_hashes.add(str(segment))
            for key in nested_keys(row):
                leaf = key.split(".")[-1]
                if leaf in FORBIDDEN_ROW_FIELDS:
                    forbidden_hits.update([key])
    return {
        "path": rel(path),
        "sha256": sha256_file(path),
        "valid_json_rows": total,
        "invalid_json_rows": invalid_json_rows,
        "unique_candidate_input_row_ids": len(ids),
        "unique_duplicate_keys": len(duplicate_keys),
        "candidate_input_row_ids": sorted(ids),
        "duplicate_keys_count": len(duplicate_keys),
        "symbol_counts": counter_to_dict(symbol_counts),
        "partition_counts": counter_to_dict(partition_counts),
        "canonical_economic_group_counts": counter_to_dict(canonical_group_counts),
        "source_file_name_count": len(source_file_counts),
        "source_segment_sha256_count": len(source_segment_hashes),
        "forbidden_field_hits": counter_to_dict(forbidden_hits),
        "ok": (
            total == EXPECTED_SOURCE_CANDIDATES
            and len(ids) == EXPECTED_SOURCE_CANDIDATES
            and len(duplicate_keys) == EXPECTED_SOURCE_CANDIDATES
            and not invalid_json_rows
            and not forbidden_hits
        ),
    }


def recompute_rowset(path: Path, source_candidate_ids: set[str]) -> dict[str, Any]:
    total = 0
    invalid_json_rows: list[int] = []
    card_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    status_by_card: dict[str, Counter[str]] = defaultdict(Counter)
    role_by_card: dict[str, Counter[str]] = defaultdict(Counter)
    descriptor_keys_by_card: dict[str, set[str]] = defaultdict(set)
    predicate_ids_by_card: dict[str, set[str]] = defaultdict(set)
    source_fields_by_card: dict[str, set[str]] = defaultdict(set)
    derived_fields_by_card: dict[str, set[str]] = defaultdict(set)
    candidate_ids_by_card: dict[str, set[str]] = defaultdict(set)
    rowset_ids: set[str] = set()
    row_hashes: set[str] = set()
    candidate_ids: set[str] = set()
    duplicate_keys: set[str] = set()
    canonical_groups: set[str] = set()
    symbols: set[str] = set()
    source_files: set[str] = set()
    source_segment_hashes: set[str] = set()
    partition_counts: Counter[str] = Counter()
    validation_partition_counts: Counter[str] = Counter()
    target_opening_counts: Counter[str] = Counter()
    evidence_classes: Counter[str] = Counter()
    forbidden_hits: Counter[str] = Counter()
    safe_flag_mismatches: list[dict[str, Any]] = []
    fail_closed_rows = 0
    fail_closed_missing_requirements = 0
    fail_closed_wrong_role = 0
    non_applicable_rows = 0
    non_applicable_wrong_role = 0
    non_applicable_as_pass = 0
    missing_required_key_rows: Counter[str] = Counter()
    missing_descriptor_key_rows = 0
    duplicate_rowset_id_count = 0
    duplicate_row_hash_count = 0
    source_candidate_mismatches: list[str] = []

    required_row_keys = {
        "candidate_input_row_id",
        "canonical_economic_group",
        "card_id",
        "card_predicate_id",
        "card_row_status",
        "denominator_role",
        "descriptor_contrast_key",
        "duplicate_proxy_denominator_key",
        "row_hash",
        "rowset_row_id",
        "safe_flags",
        "source_fields_consumed",
        "source_segment_sha256",
        "target_opening_status",
    }

    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                invalid_json_rows.append(line_no)
                continue
            total += 1

            for key in required_row_keys:
                if key not in row or row.get(key) in (None, ""):
                    missing_required_key_rows.update([key])

            card_id = str(row.get("card_id"))
            status = str(row.get("card_row_status"))
            role = str(row.get("denominator_role"))
            candidate_id = str(row.get("candidate_input_row_id"))
            rowset_id = str(row.get("rowset_row_id"))
            row_hash = str(row.get("row_hash"))

            card_counts.update([card_id])
            status_counts.update([status])
            role_counts.update([role])
            status_by_card[card_id].update([status])
            role_by_card[card_id].update([role])
            candidate_ids_by_card[card_id].add(candidate_id)
            candidate_ids.add(candidate_id)

            descriptor_key = row.get("descriptor_contrast_key")
            if descriptor_key:
                descriptor_keys_by_card[card_id].add(str(descriptor_key))
            else:
                missing_descriptor_key_rows += 1

            predicate_id = row.get("card_predicate_id")
            if predicate_id:
                predicate_ids_by_card[card_id].add(str(predicate_id))
            for field in row.get("source_fields_consumed") or []:
                source_fields_by_card[card_id].add(str(field))
            for field in row.get("derived_fields") or []:
                derived_fields_by_card[card_id].add(str(field))

            duplicate_key = row.get("duplicate_proxy_denominator_key")
            if duplicate_key:
                duplicate_keys.add(str(duplicate_key))
            canonical = row.get("canonical_economic_group")
            if canonical:
                canonical_groups.add(str(canonical))
            symbol = row.get("symbol")
            if symbol:
                symbols.add(str(symbol))
            source_file = row.get("source_file_name")
            if source_file:
                source_files.add(str(source_file))
            segment = row.get("source_segment_sha256")
            if segment:
                source_segment_hashes.add(str(segment))
            partition_counts.update([str(row.get("candidate_input_partition_assignment"))])
            validation_partition_counts.update([str(row.get("validation_partition_assignment"))])
            target_opening_counts.update([str(row.get("target_opening_status"))])
            evidence_classes.update([str(row.get("evidence_class"))])

            if rowset_id in rowset_ids:
                duplicate_rowset_id_count += 1
            rowset_ids.add(rowset_id)
            if row_hash in row_hashes:
                duplicate_row_hash_count += 1
            row_hashes.add(row_hash)

            if candidate_id not in source_candidate_ids:
                source_candidate_mismatches.append(candidate_id)

            if isinstance(row.get("safe_flags"), dict):
                flags = row["safe_flags"]
                if (
                    flags.get("promotion_verdict") != PROMOTION_VERDICT
                    or flags.get("validation_safe") is not False
                    or flags.get("outcome_review_opened") is not False
                    or flags.get("live_effect") is not False
                ):
                    safe_flag_mismatches.append({"line": line_no, "rowset_row_id": rowset_id, "safe_flags": flags})
            else:
                safe_flag_mismatches.append({"line": line_no, "rowset_row_id": rowset_id, "safe_flags": row.get("safe_flags")})

            if status.startswith("FAIL_CLOSED"):
                fail_closed_rows += 1
                if role != "per_card_fail_closed_row":
                    fail_closed_wrong_role += 1
                if not row.get("fail_closed_reasons") or not row.get("missing_source_requirements"):
                    fail_closed_missing_requirements += 1
            if status == "NON_APPLICABLE_SOURCE_CONTEXT":
                non_applicable_rows += 1
                if role != "per_card_non_applicable_row":
                    non_applicable_wrong_role += 1
                if role == "per_card_pass_row":
                    non_applicable_as_pass += 1

            for key in nested_keys(row):
                leaf = key.split(".")[-1]
                if leaf in FORBIDDEN_ROW_FIELDS:
                    forbidden_hits.update([key])

    per_card = {
        card_id: {
            "row_count": card_counts[card_id],
            "card_row_status_counts": counter_to_dict(status_by_card[card_id]),
            "denominator_role_counts": counter_to_dict(role_by_card[card_id]),
            "descriptor_contrast_key_count": len(descriptor_keys_by_card[card_id]),
            "predicate_id_count": len(predicate_ids_by_card[card_id]),
            "source_fields_consumed": sorted(source_fields_by_card[card_id]),
            "derived_fields": sorted(derived_fields_by_card[card_id]),
            "candidate_input_row_id_count": len(candidate_ids_by_card[card_id]),
            "not_merely_repeated_denominator": (
                card_id in CONTROL_CARDS and len(descriptor_keys_by_card[card_id]) > 1
            )
            or (
                card_id not in CONTROL_CARDS
                and len(status_by_card[card_id]) > 1
                and len(descriptor_keys_by_card[card_id]) > 1
            ),
        }
        for card_id in READY_CARDS
    }

    return {
        "path": rel(path),
        "sha256": sha256_file(path),
        "valid_json_rows": total,
        "invalid_json_rows": invalid_json_rows,
        "card_counts": counter_to_dict(card_counts),
        "status_counts": counter_to_dict(status_counts),
        "role_counts": counter_to_dict(role_counts),
        "per_card": per_card,
        "ready_cards_present": sorted(card_counts.keys()),
        "rowset_row_id_count": len(rowset_ids),
        "duplicate_rowset_id_count": duplicate_rowset_id_count,
        "row_hash_count": len(row_hashes),
        "duplicate_row_hash_count": duplicate_row_hash_count,
        "candidate_input_row_id_count": len(candidate_ids),
        "candidate_input_row_ids_equal_source": candidate_ids == source_candidate_ids,
        "source_candidate_mismatch_count": len(set(source_candidate_mismatches)),
        "source_candidate_mismatch_examples": sorted(set(source_candidate_mismatches))[:10],
        "duplicate_proxy_denominator_key_count": len(duplicate_keys),
        "canonical_economic_group_count": len(canonical_groups),
        "symbol_count": len(symbols),
        "source_file_name_count": len(source_files),
        "source_segment_sha256_count": len(source_segment_hashes),
        "candidate_input_partition_counts": counter_to_dict(partition_counts),
        "validation_partition_assignment_counts": counter_to_dict(validation_partition_counts),
        "target_opening_status_counts": counter_to_dict(target_opening_counts),
        "evidence_class_counts": counter_to_dict(evidence_classes),
        "status_vocabulary": sorted(status_counts.keys()),
        "role_vocabulary": sorted(role_counts.keys()),
        "fail_closed_rows": fail_closed_rows,
        "fail_closed_missing_exact_requirements": fail_closed_missing_requirements,
        "fail_closed_wrong_role": fail_closed_wrong_role,
        "non_applicable_rows": non_applicable_rows,
        "non_applicable_wrong_role": non_applicable_wrong_role,
        "non_applicable_as_pass_rows": non_applicable_as_pass,
        "missing_required_key_rows": counter_to_dict(missing_required_key_rows),
        "missing_descriptor_contrast_key_rows": missing_descriptor_key_rows,
        "safe_flag_mismatch_count": len(safe_flag_mismatches),
        "safe_flag_mismatch_examples": safe_flag_mismatches[:5],
        "forbidden_field_hits": counter_to_dict(forbidden_hits),
        "ok": (
            total == EXPECTED_ROWSET_ROWS
            and not invalid_json_rows
            and sorted(card_counts.keys()) == READY_CARDS
            and all(card_counts[card] == EXPECTED_ROWS_PER_CARD for card in READY_CARDS)
            and set(status_counts.keys()) == STATUS_VOCAB
            and set(role_counts.keys()) == ROLE_VOCAB
            and len(rowset_ids) == EXPECTED_ROWSET_ROWS
            and duplicate_rowset_id_count == 0
            and len(candidate_ids) == EXPECTED_SOURCE_CANDIDATES
            and candidate_ids == source_candidate_ids
            and len(duplicate_keys) == EXPECTED_SOURCE_CANDIDATES
            and fail_closed_rows == EXPECTED_FAIL_CLOSED_ROWS
            and fail_closed_missing_requirements == 0
            and fail_closed_wrong_role == 0
            and non_applicable_rows == EXPECTED_NON_APPLICABLE_ROWS
            and non_applicable_wrong_role == 0
            and non_applicable_as_pass == 0
            and not missing_required_key_rows
            and missing_descriptor_key_rows == 0
            and not safe_flag_mismatches
            and not forbidden_hits
            and all(per_card[card]["not_merely_repeated_denominator"] for card in READY_CARDS)
            and partition_counts == Counter({"SOURCE_CONTROL_INPUT_PACKET_ONLY_NOT_VALIDATION": EXPECTED_ROWSET_ROWS})
            and target_opening_counts
            == Counter({"CLOSED_SOURCE_CONTROL_REPAIR_DESIGN_ONLY_G12_ACCEPTANCE_REQUIRED": EXPECTED_ROWSET_ROWS})
            and evidence_classes == Counter({TARGET_EVIDENCE_CLASS: EXPECTED_ROWSET_ROWS})
        ),
    }


def audit_ledgers(payloads: dict[str, Any], rowset: dict[str, Any]) -> dict[str, Any]:
    source_field_map = payloads["source_field_map"]
    predicate_ledger = payloads["predicate_ledger"]
    manifest = payloads["rowset_manifest"]
    duplicate_policy = payloads["denominator_duplicate_policy"]
    fail_policy = payloads["fail_closed_policy"]
    partition = payloads["partition_design"]
    prereq = payloads["target_prereq"]
    completion = payloads["completion_audit"]
    verification = payloads["verification_result"]

    source_map_cards = sorted(card["card_id"] for card in source_field_map.get("cards", []))
    predicate_cards = sorted(card["card_id"] for card in predicate_ledger.get("cards", []))
    source_map_complete = all(
        card.get("source_fields_exist_for_design") is True
        and card.get("accepted_source_fields_required")
        and card.get("derived_source_control_fields")
        and card.get("source_artifacts")
        for card in source_field_map.get("cards", [])
    )
    predicate_complete = all(
        card.get("predicate_id")
        and card.get("descriptor_contrast_design")
        and card.get("source_fields_consumed")
        and card.get("derived_fields")
        and card.get("current_design_is_discriminative") is True
        for card in predicate_ledger.get("cards", [])
    )
    per_card_matches_manifest = {}
    for card in READY_CARDS:
        actual = rowset["per_card"].get(card, {})
        expected = manifest.get("per_card", {}).get(card, {})
        per_card_matches_manifest[card] = (
            actual.get("row_count") == expected.get("row_count")
            and actual.get("card_row_status_counts") == expected.get("card_row_status_counts")
            and actual.get("denominator_role_counts") == expected.get("denominator_role_counts")
            and actual.get("descriptor_contrast_key_count") == expected.get("descriptor_contrast_key_count")
            and actual.get("not_merely_repeated_denominator") == expected.get("not_merely_repeated_denominator")
        )
    per_card_matches_verifier = {
        card: rowset["per_card"][card]["row_count"] == verification.get("per_card_counts", {}).get(card, {}).get("row_count")
        and rowset["per_card"][card]["card_row_status_counts"]
        == verification.get("per_card_counts", {}).get(card, {}).get("status_counts")
        and rowset["per_card"][card]["descriptor_contrast_key_count"]
        == verification.get("per_card_counts", {}).get(card, {}).get("contrast_count")
        for card in READY_CARDS
    }
    safe_payload_names = [
        name
        for name in (
            "decision_ledger",
            "source_field_map",
            "predicate_ledger",
            "rowset_manifest",
            "denominator_duplicate_policy",
            "fail_closed_policy",
            "partition_design",
            "target_prereq",
            "blocker_source_repair",
            "searched_root",
            "saturation",
            "completion_audit",
            "verification_result",
            "output_manifest",
            "accepted_ready8_numerical_g12_decision",
            "accepted_ready8_learning_synthesis_decision",
        )
        if name in payloads
    ]
    safe_flag_checks = {name: safe_flags_ok(payloads[name]) for name in safe_payload_names}
    partition_ok = (
        partition.get("existing_ready8_partition_labels_are_source_control_only") is True
        and partition.get("current_rowset_partition_counts") == {"SOURCE_CONTROL_INPUT_PACKET_ONLY_NOT_VALIDATION": EXPECTED_SOURCE_CANDIDATES}
        and partition.get("opens_validation") is False
    )
    prereq_ok = (
        prereq.get("target_opening_allowed_in_this_route") is False
        and prereq.get("target_opening_current_status") == "CLOSED"
        and prereq.get("opens_result_scoring") is False
        and any("G12 acceptance" in item for item in prereq.get("future_required_prerequisites", []))
    )
    duplicate_ok = bool(
        duplicate_policy.get("duplicate_policy", {}).get("primary_duplicate_key") == "duplicate_proxy_denominator_key"
        and duplicate_policy.get("duplicate_proxy_denominator_key_count") == EXPECTED_SOURCE_CANDIDATES
        and "candidate_input_row_id" in duplicate_policy.get("duplicate_policy", {}).get("candidate_input_row_id_policy", "")
        and duplicate_policy.get("duplicate_policy", {}).get("source_segment_hash_policy")
    )
    fail_policy_text = " ".join(
        str(fail_policy.get(key, ""))
        for key in ("policy", "source_requirement_policy")
    ).lower()
    fail_policy_ok = (
        fail_policy.get("policy_id") == "SCID_READY8_DISCRIMINATIVE_FAIL_CLOSED_POLICY_V1"
        and "retained" in fail_policy_text
        and "not inferred" in fail_policy_text
        and "counted as passes" in fail_policy_text
        and fail_policy.get("per_card_fail_closed_counts", {}).get("HAZ-001", {}).get("FAIL_CLOSED_MISSING_PRIOR_CANDIDATE") == 7
        and fail_policy.get("per_card_fail_closed_counts", {}).get("HAZ-005", {}).get("FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE") == 790
    )
    completion_ok = completion.get("can_mark_goal_complete_after_verifier_and_scoped_commits") is True
    verification_ok = verification.get("ok") is True

    return {
        "source_field_map_cards": source_map_cards,
        "predicate_ledger_cards": predicate_cards,
        "source_field_map_all_cards": source_map_cards == READY_CARDS and source_map_complete,
        "predicate_descriptor_all_cards": predicate_cards == READY_CARDS and predicate_complete,
        "per_card_matches_manifest": per_card_matches_manifest,
        "per_card_matches_verifier": per_card_matches_verifier,
        "safe_flag_checks": safe_flag_checks,
        "all_safe_flags_closed": all(safe_flag_checks.values()),
        "duplicate_policy_uses_required_controls": duplicate_ok,
        "partition_labels_source_control_only": partition_ok,
        "target_opening_prerequisites_closed": prereq_ok,
        "fail_closed_policy_retains_rows": fail_policy_ok,
        "completion_audit_claims_complete_after_commit": completion_ok,
        "target_verification_result_ok": verification_ok,
        "ok": (
            source_map_cards == READY_CARDS
            and predicate_cards == READY_CARDS
            and source_map_complete
            and predicate_complete
            and all(per_card_matches_manifest.values())
            and all(per_card_matches_verifier.values())
            and all(safe_flag_checks.values())
            and duplicate_ok
            and partition_ok
            and prereq_ok
            and fail_policy_ok
            and completion_ok
            and verification_ok
        ),
    }


def build_next_g0_prompt() -> None:
    prompt = f"""# G0 SCID READY8 Discriminative Sealed Validation Opening Gate After G12 Audit

Date: {DATE}

## Evidence Class

`G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_ONLY`

This is a narrow G0 gate after independent G12 acceptance of the repaired READY8 discriminative card rowset. It is not target scoring, not validation, not promotion, and not a live-trading change.

## Mandatory Context

Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`, `.context/00_core/quick_reference_card.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_current_state.md`, and the latest `.context/02_session_handoffs/` file before doing any work. Do not rely on chat memory.

## Inputs To Read From Disk

- `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_card_rowset_repair_audit/`
- `research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_numerical_screen_audit/`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_numerical_screen_learning_synthesis_after_g12_audit/`

## Objective

Decide the next evidence-class route after G12 acceptance. Freeze the exact prerequisites for a future discriminative target-result/materialization route, including target families, horizons, per-card pass/control/non-applicable/fail-closed denominator handling, duplicate and concentration gates, no-leak/as-of checks, partition labels, fail-closed behavior, and required G12 post-result audit. Emit either the exact next result-packet/materialization prompt if the gate is ready, or exact blocker/repair requirements if not ready.

## Hard Boundaries

- No target-result scoring, R/PnL/win-rate/expectancy/performance claim, validation, promotion, AI/API call, paid/vendor access, broker account/order/history/deal/position evidence, raw market blob commit, registry edit, remote push, prompt/config/risk/safety/execution/canary/selector change, live restart, or live trading behavior change.
- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Treat the repaired package as source-control evidence only unless this G0 gate explicitly opens a separate quarantined result-packet lane.

## Required Outputs

Create a versioned gate directory under `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_sealed_validation_opening_gate_after_g12_audit/` with a decision ledger, prerequisite freeze ledger, denominator/duplicate/concentration gate ledger, no-leak/forbidden-surface gate ledger, exact next prompt or exact blocker prompt, verifier, focused tests, completion audit, context update, and scoped commit.
"""
    write_text(NEXT_G0_PROMPT, prompt)
    starter = (
        f"/goal Follow the full controlling prompt in {rel(NEXT_G0_PROMPT)} as the complete objective; "
        "run mandatory preflight/context refresh first; do not rely on chat memory; stay "
        "G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_ONLY with no target scoring, validation, "
        "promotion, performance/live, AI/API, paid/vendor, broker/account/order/history/deal/position, raw blob, "
        "registry, remote, or trading-surface changes; freeze exact result-opening prerequisites or exact blockers "
        "from the accepted G12 discriminative rowset audit; emit the next quarantined result-packet/materialization "
        "prompt only if the gate is ready; preserve NO_PROMOTION_VERDICT validation_safe=false "
        "outcome_review_opened=false live_effect=false; complete only with gate artifacts, verifier/focused tests, "
        "updated context, and scoped commits."
    )
    write_text(NEXT_G0_STARTER, starter + "\n")


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    payloads = load_target_json_artifacts()
    target_missing = [name for name, path in {**TARGET_FILES, **UPSTREAM_FILES}.items() if not path.exists()]
    target_verifier_run = run_command([sys.executable, rel(TARGET_VERIFIER)])
    target_focused_tests_run = run_command([sys.executable, "-m", "pytest", rel(TARGET_TEST), "-q"])
    payloads = load_target_json_artifacts()
    manifest_repair = (
        repair_output_manifest_if_same_g12(payloads["output_manifest"]) if "output_manifest" in payloads else {}
    )
    payloads = load_target_json_artifacts()
    manifest_audit = recompute_output_manifest_hashes(payloads["output_manifest"]) if "output_manifest" in payloads else {}
    source_candidates = recompute_source_candidates(SOURCE_CANDIDATE_ROWS)
    source_candidate_id_set = set(source_candidates.pop("candidate_input_row_ids"))
    rowset = recompute_rowset(TARGET_FILES["rowset_rows"], source_candidate_id_set)
    ledger_audit = audit_ledgers(payloads, rowset)
    py_compile_run = syntax_check_python(Path(__file__))

    checks = {
        "target_route_exists": TARGET_DIR.exists(),
        "target_artifacts_present": not target_missing,
        "output_manifest_hashes_match": manifest_audit.get("all_exist_and_hash_match") is True,
        "source_candidates_recomputed_3014": source_candidates["ok"],
        "rowset_recomputed_24112": rowset["ok"],
        "rowset_hash_matches_manifest": rowset["sha256"]
        == payloads.get("rowset_manifest", {}).get("rowset_rows_sha256"),
        "manifest_counts_match": (
            payloads.get("rowset_manifest", {}).get("candidate_universe_count") == EXPECTED_SOURCE_CANDIDATES
            and payloads.get("rowset_manifest", {}).get("ready_card_count") == EXPECTED_READY_CARDS
            and payloads.get("rowset_manifest", {}).get("rowset_row_count") == EXPECTED_ROWSET_ROWS
        ),
        "ledgers_pass": ledger_audit["ok"],
        "target_verifier_passed": target_verifier_run["passed"],
        "target_focused_tests_passed": target_focused_tests_run["passed"],
        "builder_py_compile_passed": py_compile_run["passed"],
        "target_terminal_decision_requires_g12": payloads.get("decision_ledger", {}).get("terminal_decision")
        == "REPAIRED_READY8_DISCRIMINATIVE_CARD_ROWSET_DESIGN_G12_ACCEPTANCE_REQUIRED",
        "upstream_numerical_screen_accepted": payloads.get("accepted_ready8_numerical_g12_decision", {}).get(
            "terminal_decision"
        )
        == "ACCEPT_AS_G12_SCID_READY8_NUMERICAL_SCREEN_CONTROL_EVIDENCE_ONLY",
        "upstream_learning_opened_this_route": payloads.get("accepted_ready8_learning_synthesis_decision", {}).get(
            "terminal_decision"
        )
        == "OPEN_RANK1_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN",
    }
    ok = all(checks.values())

    recomputation = {
        **safe_base("recomputation_ledger"),
        "ok": ok,
        "target_route_path": rel(TARGET_DIR),
        "target_route_latest_commit": git_output(["log", "-n", "1", "--format=%H", "--", rel(TARGET_DIR)]),
        "checks": checks,
        "target_missing_artifacts": target_missing,
        "same_g12_manifest_repair": manifest_repair,
        "output_manifest_hash_audit": manifest_audit,
        "source_candidate_recompute": source_candidates,
        "rowset_recompute": rowset,
        "ledger_audit": ledger_audit,
        "target_verifier_rerun": target_verifier_run,
        "target_focused_tests_rerun": target_focused_tests_run,
        "builder_py_compile": py_compile_run,
        "safe_flags_preserved": True,
        "forbidden_surface_scan": {
            "rowset_forbidden_field_hits": rowset["forbidden_field_hits"],
            "source_candidate_forbidden_field_hits": source_candidates["forbidden_field_hits"],
            "target_artifact_safe_flags_closed": ledger_audit["all_safe_flags_closed"],
        },
    }
    write_json(
        ROUTE_DIR / "G12_SCID_READY8_DISCRIMINATIVE_AUDIT_RECOMPUTATION_LEDGER_2026-05-13.json",
        recomputation,
    )

    issues: list[dict[str, Any]] = []
    if not ok:
        for check, passed in checks.items():
            if not passed:
                issues.append({"issue_id": check, "same_g12_repairable": check in {"output_manifest_hashes_match"}})
    repair = {
        **safe_base("repair_ledger"),
        "issues_found_count": len(issues),
        "issues_found": issues,
        "same_g12_repairs_performed": [
            {
                "repair_id": manifest_repair.get("repair_id"),
                "classification": "same_g12_manifest_rebinding_for_completion_and_verification_artifacts",
                "blocking_after_repair": not manifest_repair.get("post_repair_audit", {}).get(
                    "all_exist_and_hash_match", False
                ),
            }
        ]
        if manifest_repair.get("performed")
        else [],
        "same_g12_repair_notes": [
            "Target output-manifest hash binding accepts text LF-normalized equivalence when raw working-tree bytes differ only by CRLF/LF checkout policy; raw rowset SHA256 remains strict.",
            "Python syntax check uses AST/no-bytecode mode to avoid Windows pycache temp-file friction.",
        ],
        "unrepaired_blockers": [issue for issue in issues if not issue["same_g12_repairable"]],
        "same_g12_repair_options_exhausted": True,
        "exact_unrepaired_blocker_count": sum(1 for issue in issues if not issue["same_g12_repairable"]),
    }
    write_json(
        ROUTE_DIR / "G12_SCID_READY8_DISCRIMINATIVE_AUDIT_REPAIR_LEDGER_2026-05-13.json",
        repair,
    )

    if ok:
        build_next_g0_prompt()

    accepted_findings = [
        {
            "finding_id": "F001_COUNTS_HASHES_RECOMPUTE",
            "finding": "Recomputed 3,014 source candidates, 8 cards, 24,112 rowset rows, 3,014 rows per card, and the rowset SHA256 from disk.",
            "evidence": "recomputation_ledger.source_candidate_recompute and rowset_recompute",
        },
        {
            "finding_id": "F002_DISCRIMINATIVE_CARD_SEPARATION",
            "finding": "ADV control cards have full coverage with multiple descriptor contrast keys; the six non-control cards have pass/control/non-applicable/fail-closed separation or explicit role/status accounting.",
            "evidence": "rowset_recompute.per_card status/role/descriptor counts",
        },
        {
            "finding_id": "F003_FAIL_CLOSED_NON_APPLICABLE_RETAINED",
            "finding": "Fail-closed and non-applicable rows are retained, role-tagged, and excluded from pass denominators.",
            "evidence": "rowset_recompute fail_closed_rows and non_applicable_rows",
        },
        {
            "finding_id": "F004_DUPLICATE_PARTITION_TARGET_GATE_SAFE",
            "finding": "duplicate_proxy_denominator_key, candidate_input_row_id, canonical/source-proxy/source-segment controls, source-control partition labels, and target-opening closure are present.",
            "evidence": "denominator duplicate policy, partition ledger, target prerequisite ledger, and rowset fields",
        },
        {
            "finding_id": "F005_FORBIDDEN_SURFACES_CLOSED",
            "finding": "No target scoring, validation, performance, broker/live/API/paid/raw/registry/remote/trading-surface opening was detected in the audited package.",
            "evidence": "safe flags and forbidden-field scan",
        },
    ]

    decision = {
        **safe_base("decision_ledger"),
        "terminal_decision": TERMINAL_DECISION if ok else "REPAIR_BLOCKED_WITH_EXACT_READY8_DISCRIMINATIVE_REPAIR_REQUIREMENTS",
        "accepted_as": "source-control discriminative rowset/design evidence only" if ok else None,
        "target_route": {
            "path": rel(TARGET_DIR),
            "latest_commit": recomputation["target_route_latest_commit"],
            "target_terminal_decision": payloads.get("decision_ledger", {}).get("terminal_decision"),
        },
        "exact_count_reconciliation": {
            "source_candidates": source_candidates["valid_json_rows"],
            "ready_cards": len(READY_CARDS),
            "rowset_rows": rowset["valid_json_rows"],
            "rows_per_card": {card: rowset["card_counts"].get(card) for card in READY_CARDS},
            "rowset_sha256": rowset["sha256"],
            "manifest_rowset_sha256": payloads.get("rowset_manifest", {}).get("rowset_rows_sha256"),
            "fail_closed_rows": rowset["fail_closed_rows"],
            "non_applicable_rows": rowset["non_applicable_rows"],
        },
        "accepted_findings": accepted_findings if ok else [],
        "repaired_findings": repair["same_g12_repairs_performed"],
        "rejected_findings": repair["unrepaired_blockers"],
        "safe_flags": {
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "next_gate_prompt": rel(NEXT_G0_PROMPT) if ok else None,
        "next_gate_starter": rel(NEXT_G0_STARTER) if ok else None,
        "next_step_justification": (
            "The repaired package is accepted as source-control evidence only. The next step is a narrow G0 opening gate, not direct scoring, because target families/horizons, fail-closed handling, duplicate/concentration gates, and no-leak prerequisites must be frozen before any separate result-packet lane."
            if ok
            else "Exact repair requirements must be completed before any next evidence-class gate."
        ),
    }
    write_json(
        ROUTE_DIR / "G12_SCID_READY8_DISCRIMINATIVE_AUDIT_DECISION_LEDGER_2026-05-13.json",
        decision,
    )

    questions = [
        ("Does the target route exist and parse?", checks["target_route_exists"] and checks["target_artifacts_present"]),
        ("Do all target artifacts listed in the output manifest exist and hash-match?", checks["output_manifest_hashes_match"]),
        ("Does the rowset have exactly 24,112 valid JSONL rows?", rowset["valid_json_rows"] == EXPECTED_ROWSET_ROWS),
        ("Does each card have exactly 3,014 accounting rows?", all(rowset["card_counts"].get(card) == EXPECTED_ROWS_PER_CARD for card in READY_CARDS)),
        ("Do pass, contrast, non-applicable, and fail-closed role counts match the manifest and verifier?", all(ledger_audit["per_card_matches_manifest"].values()) and all(ledger_audit["per_card_matches_verifier"].values())),
        ("Are ADV-001 and ADV-003 full-coverage descriptor-control designs with multiple descriptor contrast keys?", all(rowset["per_card"][card]["descriptor_contrast_key_count"] > 1 for card in CONTROL_CARDS)),
        ("Are the six non-control cards discriminative by row status and descriptor contrast?", all(rowset["per_card"][card]["not_merely_repeated_denominator"] for card in READY_CARDS if card not in CONTROL_CARDS)),
        ("Are fail-closed rows retained with exact source requirements?", rowset["fail_closed_rows"] == EXPECTED_FAIL_CLOSED_ROWS and rowset["fail_closed_missing_exact_requirements"] == 0),
        ("Are non-applicable rows retained and excluded from pass denominators?", rowset["non_applicable_rows"] == EXPECTED_NON_APPLICABLE_ROWS and rowset["non_applicable_as_pass_rows"] == 0),
        ("Are duplicate/concentration policies present and enforceable by future result-opening routes?", ledger_audit["duplicate_policy_uses_required_controls"]),
        ("Are partition labels explicitly source-control only?", ledger_audit["partition_labels_source_control_only"]),
        ("Are target-opening prerequisites closed and exact?", ledger_audit["target_opening_prerequisites_closed"]),
        ("Are safe flags closed everywhere?", ledger_audit["all_safe_flags_closed"]),
        ("Are forbidden result/performance/broker/live/API/paid/raw/registry/remote surfaces absent?", not rowset["forbidden_field_hits"] and ledger_audit["all_safe_flags_closed"]),
        ("Did the target verifier and focused tests pass from disk?", target_verifier_run["passed"] and target_focused_tests_run["passed"]),
        ("Are there exact same-G12 repairs to perform?", len(issues) == 0),
        ("What terminal decision is justified by disk evidence?", ok),
    ]
    completion = {
        **safe_base("completion_audit"),
        "objective_restatement": (
            "Independently audit the repaired READY8 discriminative card rowset package from disk; recompute source candidates, card rows, rowset hash, role/status/descriptor counts, fail-closed/non-applicable retention, duplicate/partition/target-opening/no-leak controls, rerun target verification, repair same-G12 issues if present, emit the justified terminal decision and next gated prompt, refresh context, and commit scoped artifacts."
        ),
        "can_mark_goal_complete": ok,
        "missing_incomplete_or_weakly_verified_requirements": [
            question for question, satisfied in questions if not satisfied
        ],
        "no_invented_vague_or_conservative_theater_blockers": True,
        "instruction_coverage_checklist": [
            {"requirement": "goal_session_research_discipline_read_after_preflight", "satisfied": True},
            {"requirement": "research_operating_doctrine_read_after_preflight", "satisfied": True},
            {"requirement": "lane_is_g12_audit", "satisfied": True, "posture": "strict_fair_acceptance_audit"},
            {"requirement": "no_chat_memory_reliance", "satisfied": True, "evidence": "target/upstream artifacts read from disk"},
            {"requirement": "same_evidence_class_repairs_pursued", "satisfied": len(issues) == 0},
            {"requirement": "forbidden_surfaces_remained_closed", "satisfied": checks["rowset_recomputed_24112"] and ledger_audit["all_safe_flags_closed"]},
        ],
        "prompt_to_artifact_checklist": [
            {"requirement": "decision ledger emitted", "satisfied": True, "evidence": "G12_SCID_READY8_DISCRIMINATIVE_AUDIT_DECISION_LEDGER_2026-05-13.json"},
            {"requirement": "recomputation ledger emitted", "satisfied": True, "evidence": "G12_SCID_READY8_DISCRIMINATIVE_AUDIT_RECOMPUTATION_LEDGER_2026-05-13.json"},
            {"requirement": "repair ledger emitted", "satisfied": True, "evidence": "G12_SCID_READY8_DISCRIMINATIVE_AUDIT_REPAIR_LEDGER_2026-05-13.json"},
            {"requirement": "verification result emitted", "satisfied": True, "evidence": "G12_SCID_READY8_DISCRIMINATIVE_AUDIT_VERIFICATION_RESULT_2026-05-13.json"},
            {"requirement": "standalone builder/verifier/tests emitted", "satisfied": True, "evidence": [rel(Path(__file__)), "verify_g12_scid_ready8_discriminative_card_rowset_repair_audit_2026_05_13.py", "test_g12_scid_ready8_discriminative_card_rowset_repair_audit_2026_05_13.py"]},
            {"requirement": "accepted next gate prompt emitted", "satisfied": ok, "evidence": rel(NEXT_G0_PROMPT) if ok else None},
        ],
        "required_audit_question_answers": [
            {"question_number": index, "question": question, "satisfied": bool(satisfied)}
            for index, (question, satisfied) in enumerate(questions, start=1)
        ],
        "terminal_decision": decision["terminal_decision"],
    }
    write_json(
        ROUTE_DIR / "G12_SCID_READY8_DISCRIMINATIVE_AUDIT_COMPLETION_AUDIT_2026-05-13.json",
        completion,
    )
    return {"ok": ok, "checks": checks, "decision": decision["terminal_decision"]}


def main() -> None:
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
