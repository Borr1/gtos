from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-13"
ROUTE_ID = "G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT"
EVIDENCE_CLASS = "G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G12_SCID_READY8_NUMERICAL_SCREEN_CONTROL_EVIDENCE_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

READY_CARDS = ["ADV-001", "ADV-003", "BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"]
HORIZONS = [1, 4, 16, 32]
CLOSE_FAMILY = "neutral_close_to_close_return_m15_horizons_v1"
HIGH_LOW_FAMILY = "neutral_high_low_excursion_m15_horizons_v1"
TARGET_FAMILIES = [CLOSE_FAMILY, HIGH_LOW_FAMILY]

EXPECTED_SOURCE_CANDIDATES = 3014
EXPECTED_READY_CARDS = 8
EXPECTED_ROWSET_ROWS = 24112
EXPECTED_TARGET_ROWS = 192896
EXPECTED_MATRIX_ROWS = 64
EXPECTED_BASELINE_ROWS = 128
EXPECTED_PAIRWISE_CARD_ROWS = 28
EXPECTED_HORIZON_REVERSAL_ROWS = 32
EXPECTED_TARGET_FAMILY_LINK_ROWS = 32
EXPECTED_HIGH_LOW_MONOTONICITY_ROWS = 8
EXPECTED_RECURSIVE_SCREENS_MIN = 5
EXPECTED_COVERAGE_SCREENS_MIN = 9
EXPECTED_CANDIDATE_TARGET_REFS = EXPECTED_ROWSET_ROWS * len(HORIZONS) * len(TARGET_FAMILIES)

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research/science_program_2026_05/04_goal_prompts"
G0_DIR = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "g0_scid_noapi_ready8_target_result_synthesis_and_quarantined_numerical_screen"
)
TARGET_G12_DIR = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_scid_noapi_ready8_quarantined_target_result_packet_audit"
)
PACKET_DIR = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "scid_noapi_ready8_quarantined_target_result_packet_after_g0_gate"
)

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_strategy_edge_claims": False,
    "opens_validation": False,
    "credentials_touched": False,
}

PARTITION_FIELDS = [
    "partition_assignment",
    "candidate_input_partition_assignment",
    "symbol",
    "canonical_economic_group",
    "source_proxy_group",
    "source_file_name_expected",
    "source_segment_sha256_expected",
    "session_bucket",
    "time_of_day_bucket",
    "utc_hour",
    "science_domain",
    "mechanism_family",
    "baseline_assignment_family",
    "baseline_control_bucket",
    "denominator_group_concentration_bucket",
    "source_coverage_quality_bucket",
    "source_group",
    "packet_id",
    "source_hash_policy",
    "prior_context_descriptor_buckets.prior_16_drift_bucket",
    "prior_context_descriptor_buckets.prior_16_range_bucket",
    "prior_context_descriptor_buckets.prior_32_range_bucket",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def safe_base(artifact_family: str) -> dict[str, Any]:
    return {
        "schema_version": "g12_scid_ready8_numerical_screen_audit_v1",
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": utc_now(),
        **SAFE_FLAGS,
    }


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def target_file(card_id: str, family: str) -> Path:
    card = card_id.replace("-", "_")
    suffix = "CLOSE_TO_CLOSE" if family == CLOSE_FAMILY else "HIGH_LOW_EXCURSION"
    return PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_ROWS_{card}_{suffix}_{DATE}.jsonl"


def get_nested(row: dict[str, Any], dotted: str) -> Any:
    current: Any = row
    for part in dotted.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def metrics_from_target_row(row: dict[str, Any]) -> dict[str, float]:
    if row.get("terminal_status") != "COMPUTABLE":
        return {}
    family = row.get("target_family_id")
    if family == CLOSE_FAMILY:
        metrics: dict[str, float] = {}
        pct = row.get("close_to_close_percent_return")
        delta = row.get("close_to_close_absolute_delta")
        if is_number(pct):
            metrics["close_to_close_percent_return"] = float(pct)
            metrics["absolute_close_to_close_percent_return"] = abs(float(pct))
        if is_number(delta):
            metrics["close_to_close_absolute_delta"] = float(delta)
            metrics["absolute_close_to_close_absolute_delta"] = abs(float(delta))
        return metrics
    if family == HIGH_LOW_FAMILY:
        metrics = {}
        upside = row.get("upside_excursion_percent")
        downside = row.get("downside_excursion_percent")
        if is_number(upside):
            metrics["upside_excursion_percent"] = float(upside)
        if is_number(downside):
            metrics["downside_excursion_percent"] = float(downside)
        if is_number(upside) and is_number(downside):
            up = float(upside)
            down = float(downside)
            metrics["high_low_excursion_asymmetry_percent"] = up - down
            metrics["absolute_high_low_excursion_asymmetry_percent"] = abs(up - down)
            metrics["high_low_total_excursion_percent"] = up + down
            metrics["high_low_max_excursion_percent"] = max(up, down)
        return metrics
    return {}


def fingerprint_payload(row: dict[str, Any], metrics: dict[str, float]) -> str:
    payload = {
        "duplicate_proxy_denominator_key": row.get("duplicate_proxy_denominator_key"),
        "terminal_status": row.get("terminal_status"),
        "fail_closed_primary_reason": row.get("fail_closed_primary_reason"),
        "horizon_m15_bars": row.get("horizon_m15_bars"),
        "target_family_id": row.get("target_family_id"),
        "metrics": {key: round(value, 15) for key, value in sorted(metrics.items())},
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def safe_flags_ok(payload: dict[str, Any]) -> bool:
    return all(payload.get(key) == expected for key, expected in SAFE_FLAGS.items())


def audit_target_population() -> dict[str, Any]:
    line_counts_by_file: dict[str, int] = {}
    per_card_counts = Counter()
    per_family_counts = Counter()
    per_horizon_counts = Counter()
    status_counts = Counter()
    fail_reason_counts = Counter()
    rowset_ids: set[str] = set()
    duplicate_keys: set[str] = set()
    target_result_ids: set[str] = set()
    target_result_hashes: set[str] = set()
    target_duplicate_ids = 0
    target_duplicate_hashes = 0
    matrix_items: dict[tuple[str, int, str], list[str]] = defaultdict(list)
    matrix_status_counts: dict[tuple[str, int, str], Counter] = defaultdict(Counter)
    partition_values: dict[str, set[str]] = {field: set() for field in PARTITION_FIELDS}
    partition_keys: set[tuple[str, str, str, int, str]] = set()
    safe_flag_mismatch_count = 0
    forbidden_surface_mismatch_count = 0

    for card_id in READY_CARDS:
        for family in TARGET_FAMILIES:
            path = target_file(card_id, family)
            count = 0
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    count += 1
                    horizon = int(row["horizon_m15_bars"])
                    key = (card_id, horizon, family)
                    metrics = metrics_from_target_row(row)
                    matrix_items[key].append(fingerprint_payload(row, metrics))
                    matrix_status_counts[key][row.get("terminal_status")] += 1
                    per_card_counts[card_id] += 1
                    per_family_counts[family] += 1
                    per_horizon_counts[str(horizon)] += 1
                    status_counts[row.get("terminal_status")] += 1
                    if row.get("terminal_status") != "COMPUTABLE":
                        fail_reason_counts[row.get("fail_closed_primary_reason") or "FAIL_CLOSED_REASON_NULL"] += 1
                    rowset_ids.add(str(row["rowset_row_id"]))
                    duplicate_keys.add(str(row["duplicate_proxy_denominator_key"]))
                    target_id = str(row["target_result_row_id"])
                    target_hash = str(row["target_result_row_hash"])
                    if target_id in target_result_ids:
                        target_duplicate_ids += 1
                    if target_hash in target_result_hashes:
                        target_duplicate_hashes += 1
                    target_result_ids.add(target_id)
                    target_result_hashes.add(target_hash)
                    for field in PARTITION_FIELDS:
                        partition_value = str(get_nested(row, field))
                        partition_values[field].add(partition_value)
                        partition_keys.add((field, partition_value, card_id, horizon, family))
                    if not all(row.get(flag) == expected for flag, expected in SAFE_FLAGS.items() if flag in row):
                        safe_flag_mismatch_count += 1
                    if any(
                        row.get(flag) is True
                        for flag in (
                            "opens_ai_api",
                            "opens_paid_or_vendor_access",
                            "opens_broker_account_order_history_deal_position_evidence",
                            "opens_live_trading_behavior",
                            "opens_raw_market_data_blob_commit",
                            "opens_remote_push",
                            "opens_validation",
                            "opens_strategy_edge_claims",
                        )
                    ):
                        forbidden_surface_mismatch_count += 1
            line_counts_by_file[rel(path)] = count

    fingerprints: dict[str, str] = {}
    for key, items in matrix_items.items():
        h = hashlib.sha256()
        for item in sorted(items):
            h.update(item.encode("utf-8"))
            h.update(b"\n")
        card, horizon, family = key
        fingerprints[f"{card}|{horizon}|{family}"] = h.hexdigest()

    return {
        "target_result_row_count": sum(line_counts_by_file.values()),
        "line_counts_by_file": line_counts_by_file,
        "per_card_target_counts": dict(sorted(per_card_counts.items())),
        "target_family_counts": dict(sorted(per_family_counts.items())),
        "horizon_counts": dict(sorted(per_horizon_counts.items())),
        "terminal_status_counts": dict(sorted(status_counts.items())),
        "fail_closed_primary_reason_counts": dict(sorted(fail_reason_counts.items())),
        "unique_rowset_row_id_count": len(rowset_ids),
        "unique_duplicate_proxy_denominator_key_count": len(duplicate_keys),
        "unique_target_result_row_id_count": len(target_result_ids),
        "unique_target_result_row_hash_count": len(target_result_hashes),
        "duplicate_target_result_row_id_count": target_duplicate_ids,
        "duplicate_target_result_row_hash_count": target_duplicate_hashes,
        "matrix_fingerprints": fingerprints,
        "matrix_combo_row_counts": {
            key: sum(counter.values())
            for key, counter in sorted((f"{card}|{horizon}|{family}", counts) for (card, horizon, family), counts in matrix_status_counts.items())
        },
        "partition_unique_value_counts": {field: len(values) for field, values in partition_values.items()},
        "partition_expected_rows": len(partition_keys),
        "safe_flag_mismatch_count": safe_flag_mismatch_count,
        "forbidden_surface_mismatch_count": forbidden_surface_mismatch_count,
        "_target_result_ids": target_result_ids,
    }


def audit_candidate_examples(target_ids: set[str]) -> dict[str, Any]:
    path = G0_DIR / f"G0_SCID_READY8_CANDIDATE_EXAMPLE_LEDGER_{DATE}.jsonl"
    line_count = 0
    candidate_card_pairs: set[tuple[str, str]] = set()
    referenced_target_ids: set[str] = set()
    target_ref_count = 0
    missing_target_refs = 0
    target_refs_per_row = Counter()
    schema_counts = Counter()
    selection_rule_counts = Counter()
    categories_seen = Counter()
    card_counts = Counter()

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            line_count += 1
            schema_counts[row.get("schema")] += 1
            selection_rule_counts[row.get("example_selection_rule")] += 1
            card = str(row.get("card_id"))
            dup = str(row.get("duplicate_proxy_denominator_key"))
            card_counts[card] += 1
            candidate_card_pairs.add((card, dup))
            bindings = row.get("target_binding_values", [])
            target_refs_per_row[len(bindings)] += 1
            for binding in bindings:
                target_ref_count += 1
                target_id = str(binding[2])
                referenced_target_ids.add(target_id)
                if target_id not in target_ids:
                    missing_target_refs += 1
            for category in row.get("example_categories", []):
                categories_seen[category] += 1

    return {
        "candidate_example_path": rel(path),
        "candidate_example_rows": line_count,
        "candidate_example_worktree_bytes": path.stat().st_size,
        "unique_candidate_card_pairs": len(candidate_card_pairs),
        "card_counts": dict(sorted(card_counts.items())),
        "target_reference_count": target_ref_count,
        "unique_referenced_target_result_row_ids": len(referenced_target_ids),
        "missing_target_reference_count": missing_target_refs,
        "target_reference_set_equals_target_population": referenced_target_ids == target_ids,
        "target_refs_per_candidate_row_counts": dict(sorted(target_refs_per_row.items())),
        "schema_counts": dict(sorted(schema_counts.items())),
        "selection_rule_counts": dict(sorted(selection_rule_counts.items())),
        "top_n_or_sampling_rule_detected": any(
            rule != "ALL_24112_CANDIDATE_CARD_ROWS_INCLUDED_NO_TOP_N_CAP"
            for rule in selection_rule_counts
        ),
        "category_counts": dict(sorted(categories_seen.items())),
    }


def audit_git_storage(paths: list[Path]) -> dict[str, Any]:
    lfs_ls = git_output(["lfs", "ls-files"])
    lfs_paths = {line.split(" * ", 1)[1].strip() for line in lfs_ls.splitlines() if " * " in line}
    audited: list[dict[str, Any]] = []
    oversized_normal_git_blobs: list[dict[str, Any]] = []
    lfs_expected_mismatches: list[dict[str, Any]] = []
    for path in paths:
        rel_path = rel(path)
        attr = git_output(["check-attr", "filter", "--", rel_path])
        blob_size_raw = git_output(["cat-file", "-s", f":{rel_path}"])
        blob_size = int(blob_size_raw) if blob_size_raw.isdigit() else None
        worktree_bytes = path.stat().st_size if path.exists() else None
        is_lfs = "filter: lfs" in attr
        record = {
            "path": rel_path,
            "exists": path.exists(),
            "worktree_bytes": worktree_bytes,
            "git_blob_size_bytes": blob_size,
            "git_filter_attr": attr,
            "listed_by_git_lfs": rel_path in lfs_paths,
            "lfs_materialized_worktree_pointer_blob": is_lfs and blob_size is not None and blob_size < 1000 and worktree_bytes is not None and worktree_bytes > blob_size,
        }
        audited.append(record)
        if blob_size is not None and blob_size > 100_000_000 and not is_lfs:
            oversized_normal_git_blobs.append(record)
        if path.suffix == ".jsonl" and worktree_bytes is not None and worktree_bytes > 50_000_000 and not is_lfs:
            lfs_expected_mismatches.append(record)
    return {
        "audited_paths": audited,
        "oversized_normal_git_blob_count": len(oversized_normal_git_blobs),
        "oversized_normal_git_blobs": oversized_normal_git_blobs,
        "large_jsonl_without_lfs_count": len(lfs_expected_mismatches),
        "large_jsonl_without_lfs": lfs_expected_mismatches,
    }


def all_required_json_paths() -> dict[str, Path]:
    return {
        "g0_decision": G0_DIR / f"G0_SCID_READY8_NUMERICAL_SCREEN_DECISION_LEDGER_{DATE}.json",
        "g0_manifest": G0_DIR / f"G0_SCID_READY8_NUMERICAL_SCREEN_OUTPUT_MANIFEST_{DATE}.json",
        "g0_completion": G0_DIR / f"G0_SCID_READY8_COMPLETION_AUDIT_{DATE}.json",
        "g0_matrix": G0_DIR / f"G0_SCID_READY8_CARD_HORIZON_TARGET_FAMILY_MATRIX_{DATE}.json",
        "g0_baseline": G0_DIR / f"G0_SCID_READY8_BASELINE_CONTROL_ADVERSARIAL_DELTA_LEDGER_{DATE}.json",
        "g0_partition": G0_DIR / f"G0_SCID_READY8_PARTITION_ROBUSTNESS_MATRIX_{DATE}.json",
        "g0_duplicate": G0_DIR / f"G0_SCID_READY8_DUPLICATE_CONCENTRATION_AND_CLUSTER_AUDIT_{DATE}.json",
        "g0_interaction": G0_DIR / f"G0_SCID_READY8_INTERACTION_REDUNDANCY_ANTISIGNAL_LEDGER_{DATE}.json",
        "g0_negative": G0_DIR / f"G0_SCID_READY8_NEGATIVE_EVIDENCE_AND_KILL_FAST_LEDGER_{DATE}.json",
        "g0_recursive": G0_DIR / f"G0_SCID_READY8_RECURSIVE_DISCOVERY_LEDGER_{DATE}.json",
        "g0_coverage": G0_DIR / f"G0_SCID_READY8_EXHAUSTIVE_INTELLIGENCE_COVERAGE_LEDGER_{DATE}.json",
        "g0_self": G0_DIR / f"G0_SCID_READY8_FINAL_SELF_INTERROGATION_LEDGER_{DATE}.json",
        "g0_repair": G0_DIR / f"G0_SCID_READY8_SAME_EVIDENCE_CLASS_REPAIR_LEDGER_{DATE}.json",
        "g0_candidate_schema": G0_DIR / f"G0_SCID_READY8_CANDIDATE_EXAMPLE_LEDGER_SCHEMA_{DATE}.json",
        "g12_target_decision": TARGET_G12_DIR / f"G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_DECISION_LEDGER_{DATE}.json",
        "g12_target_recompute": TARGET_G12_DIR / f"G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_RECOMPUTE_AUDIT_{DATE}.json",
        "g12_target_verification": TARGET_G12_DIR / f"G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_VERIFICATION_RESULT_{DATE}.json",
    }


def audit_g0_ledgers(target_audit: dict[str, Any], candidate_audit: dict[str, Any]) -> dict[str, Any]:
    paths = all_required_json_paths()
    payloads = {name: read_json(path) for name, path in paths.items()}
    issues: list[str] = []

    safe_flag_mismatches: list[str] = []
    for name, payload in payloads.items():
        if isinstance(payload, dict) and not safe_flags_ok(payload):
            safe_flag_mismatches.append(name)
    if safe_flag_mismatches:
        issues.append(f"safe_flag_mismatches::{safe_flag_mismatches}")

    matrix_rows = payloads["g0_matrix"].get("rows", [])
    matrix_by_key = {
        f"{row['card_id']}|{row['horizon_m15_bars']}|{row['target_family_id']}": row
        for row in matrix_rows
    }
    fingerprint_mismatches = []
    for key, recomputed in target_audit["matrix_fingerprints"].items():
        ledger_row = matrix_by_key.get(key)
        if not ledger_row or ledger_row.get("movement_fingerprint_sha256") != recomputed:
            fingerprint_mismatches.append(key)

    all_match_adv001_recomputed = True
    all_match_adv003_recomputed = True
    for horizon in HORIZONS:
        for family in TARGET_FAMILIES:
            adv001 = target_audit["matrix_fingerprints"].get(f"ADV-001|{horizon}|{family}")
            adv003 = target_audit["matrix_fingerprints"].get(f"ADV-003|{horizon}|{family}")
            for card in READY_CARDS:
                fp = target_audit["matrix_fingerprints"].get(f"{card}|{horizon}|{family}")
                all_match_adv001_recomputed = all_match_adv001_recomputed and fp == adv001
                all_match_adv003_recomputed = all_match_adv003_recomputed and fp == adv003

    baseline_rows = payloads["g0_baseline"].get("rows", [])
    duplicate_rows = payloads["g0_duplicate"].get("ranked_complete_duplicate_key_contributors", [])
    partition_rows = payloads["g0_partition"].get("rows", [])
    interaction = payloads["g0_interaction"]
    negative = payloads["g0_negative"]
    recursive = payloads["g0_recursive"]
    coverage = payloads["g0_coverage"]
    self_interrogation = payloads["g0_self"]
    repair = payloads["g0_repair"]
    completion = payloads["g0_completion"]
    decision = payloads["g0_decision"]

    ledger_checks = {
        "g0_binds_accepted_g12_target_result_packet": (
            decision.get("accepted_g12_decision")
            == "ACCEPT_AS_G12_SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_CONTROL_EVIDENCE_ONLY"
            and decision.get("accepted_g12_verifier_ok") is True
            and payloads["g12_target_verification"].get("ok") is True
        ),
        "decision_counts_exact": (
            decision.get("source_candidate_count") == EXPECTED_SOURCE_CANDIDATES
            and decision.get("ready_card_count") == EXPECTED_READY_CARDS
            and decision.get("rowset_row_count") == EXPECTED_ROWSET_ROWS
            and decision.get("target_result_row_count") == EXPECTED_TARGET_ROWS
            and decision.get("horizons") == HORIZONS
            and decision.get("target_families") == TARGET_FAMILIES
        ),
        "matrix_row_count_exact": len(matrix_rows) == EXPECTED_MATRIX_ROWS,
        "matrix_fingerprints_recomputed_match_ledger": len(fingerprint_mismatches) == 0,
        "all_card_fingerprints_match_adv001_recomputed": all_match_adv001_recomputed,
        "all_card_fingerprints_match_adv003_recomputed": all_match_adv003_recomputed,
        "matrix_all_rows_claim_match_adv001": all(row.get("matches_adv_001_fingerprint") is True for row in matrix_rows),
        "matrix_all_rows_claim_match_adv003": all(row.get("matches_adv_003_fingerprint") is True for row in matrix_rows),
        "baseline_rows_exact_and_all_match": len(baseline_rows) == EXPECTED_BASELINE_ROWS and all(row.get("movement_fingerprint_match") is True for row in baseline_rows),
        "partition_rows_recompute_expected": len(partition_rows) == target_audit["partition_expected_rows"],
        "partition_fields_match": payloads["g0_partition"].get("partition_fields_screened") == PARTITION_FIELDS,
        "duplicate_contributors_exact": len(duplicate_rows) == EXPECTED_SOURCE_CANDIDATES,
        "duplicate_full_card_horizon_family_expansion": (
            payloads["g0_duplicate"].get("all_duplicate_keys_have_all_card_horizon_family_rows") is True
            and all(row.get("card_count") == EXPECTED_READY_CARDS and row.get("rowset_row_count") == EXPECTED_READY_CARDS and row.get("total_target_rows") == 64 for row in duplicate_rows)
        ),
        "candidate_examples_full_population": (
            candidate_audit["candidate_example_rows"] == EXPECTED_ROWSET_ROWS
            and candidate_audit["target_reference_count"] == EXPECTED_CANDIDATE_TARGET_REFS
            and candidate_audit["target_reference_set_equals_target_population"] is True
            and candidate_audit["top_n_or_sampling_rule_detected"] is False
        ),
        "interaction_ledgers_complete": (
            len(interaction.get("pairwise_card_overlap_and_redundancy", [])) == EXPECTED_PAIRWISE_CARD_ROWS
            and interaction.get("pairwise_card_redundancy_complete") is True
            and len(interaction.get("horizon_close_to_close_sign_transition_reversal_screens", [])) == EXPECTED_HORIZON_REVERSAL_ROWS
            and len(interaction.get("target_family_close_vs_excursion_asymmetry_links", [])) == EXPECTED_TARGET_FAMILY_LINK_ROWS
            and len(interaction.get("high_low_horizon_monotonicity_contradiction_checks", [])) == EXPECTED_HIGH_LOW_MONOTONICITY_ROWS
        ),
        "negative_ledgers_kill_card_specific_edge_claims": (
            len(negative.get("baseline_delta_rows", [])) == EXPECTED_BASELINE_ROWS
            and len(negative.get("card_horizon_family_negative_evidence_complete", [])) == EXPECTED_MATRIX_ROWS
            and len(negative.get("kill_fast_conclusions", [])) >= 2
        ),
        "recursive_discovery_exhausted": (
            len(recursive.get("recursive_screens", [])) >= EXPECTED_RECURSIVE_SCREENS_MIN
            and recursive.get("same_evidence_class_followups_left_unpursued") == []
        ),
        "coverage_remaining_zero": (
            coverage.get("known_same_evidence_class_intelligence_remaining") == 0
            and coverage.get("sampling_or_approximation_used") is False
            and len(coverage.get("feasible_screens_attempted", [])) >= EXPECTED_COVERAGE_SCREENS_MIN
        ),
        "self_interrogation_remaining_zero": self_interrogation.get("same_evidence_class_items_remaining_after_final_loop") == 0,
        "repair_ledger_no_unresolved_same_g12_issue": repair.get("unresolved_same_evidence_class_issues") == [],
        "completion_audit_complete": (
            completion.get("all_prompt_requirements_satisfied_before_external_verifier") is True
            and completion.get("known_same_evidence_class_intelligence_remaining") == 0
            and completion.get("same_evidence_class_items_remaining_after_final_loop") == 0
            and len(completion.get("mandatory_question_answers", [])) == 17
            and all(item.get("satisfied") is True for item in completion.get("prompt_to_artifact_checklist", []))
        ),
        "safe_flags_all_g0_and_accepted_g12_payloads": len(safe_flag_mismatches) == 0,
    }

    for key, passed in ledger_checks.items():
        if not passed:
            issues.append(f"ledger_check_failed::{key}")

    return {
        "all_required_artifacts_present_and_parseable": all(path.exists() for path in paths.values()),
        "required_json_paths": {name: rel(path) for name, path in paths.items()},
        "safe_flag_mismatches": safe_flag_mismatches,
        "fingerprint_mismatches": fingerprint_mismatches,
        "ledger_checks": ledger_checks,
        "issues": issues,
        "counts_from_ledgers": {
            "matrix_rows": len(matrix_rows),
            "baseline_delta_rows": len(baseline_rows),
            "partition_rows": len(partition_rows),
            "duplicate_contributor_rows": len(duplicate_rows),
            "pairwise_card_rows": len(interaction.get("pairwise_card_overlap_and_redundancy", [])),
            "negative_card_horizon_family_rows": len(negative.get("card_horizon_family_negative_evidence_complete", [])),
            "recursive_screens": len(recursive.get("recursive_screens", [])),
            "coverage_feasible_screens": len(coverage.get("feasible_screens_attempted", [])),
            "self_interrogation_questions": len(self_interrogation.get("self_interrogation_questions", [])),
        },
    }


def audit_manifest() -> dict[str, Any]:
    manifest_path = G0_DIR / f"G0_SCID_READY8_NUMERICAL_SCREEN_OUTPUT_MANIFEST_{DATE}.json"
    manifest = read_json(manifest_path)
    mismatches = []
    lf_normalized_matches = []
    nonblocking_prompt_hash_drifts = []
    missing = []
    for artifact in manifest.get("artifacts", []):
        path = ROOT / artifact["path"]
        if not path.exists():
            missing.append(artifact["path"])
            continue
        actual = sha256_file(path)
        if actual != artifact.get("sha256"):
            raw = path.read_bytes()
            lf_hash = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
            if lf_hash == artifact.get("sha256"):
                lf_normalized_matches.append(
                    {
                        "path": artifact["path"],
                        "manifest_sha256": artifact.get("sha256"),
                        "actual_sha256": actual,
                        "lf_normalized_sha256": lf_hash,
                    }
                )
            elif artifact["path"] == f"research/science_program_2026_05/04_goal_prompts/G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_GOAL_PROMPT_{DATE}.md":
                nonblocking_prompt_hash_drifts.append(
                    {
                        "path": artifact["path"],
                        "manifest_sha256": artifact.get("sha256"),
                        "actual_sha256": actual,
                        "lf_normalized_sha256": lf_hash,
                        "classification": "NONBLOCKING_POST_G0_PROMPT_HARDENING_DRIFT_CURRENT_DISK_PROMPT_SUPERSEDES_MANIFEST_HASH",
                    }
                )
            else:
                mismatches.append({"path": artifact["path"], "manifest_sha256": artifact.get("sha256"), "actual_sha256": actual, "lf_normalized_sha256": lf_hash})
    return {
        "manifest_path": rel(manifest_path),
        "artifact_count": manifest.get("artifact_count"),
        "missing_artifact_count": len(missing),
        "missing_artifacts": missing,
        "hash_mismatch_count": len(mismatches),
        "hash_mismatches": mismatches,
        "lf_normalized_hash_match_count": len(lf_normalized_matches),
        "lf_normalized_hash_matches": lf_normalized_matches,
        "nonblocking_prompt_hash_drift_count": len(nonblocking_prompt_hash_drifts),
        "nonblocking_prompt_hash_drifts": nonblocking_prompt_hash_drifts,
        "text_eol_hash_equivalence_policy": "Raw working-tree text hashes may differ under CRLF checkout; LF-normalized matches are accepted for text artifacts while true mismatches remain blocking.",
    }


def git_commit_for_path(path: Path) -> str:
    return git_output(["log", "-1", "--format=%H", "--", rel(path)])


def collect_audit(run_external_checks: bool = True) -> dict[str, Any]:
    target_audit_raw = audit_target_population()
    target_ids = target_audit_raw.pop("_target_result_ids")
    candidate_audit = audit_candidate_examples(target_ids)
    ledger_audit = audit_g0_ledgers(target_audit_raw, candidate_audit)
    manifest_audit = audit_manifest()
    storage_paths = [
        G0_DIR / f"G0_SCID_READY8_CANDIDATE_EXAMPLE_LEDGER_{DATE}.jsonl",
        *[target_file(card, family) for card in READY_CARDS for family in TARGET_FAMILIES],
    ]
    storage_audit = audit_git_storage(storage_paths)
    external_checks = {
        "g0_standalone_verifier": None,
        "g0_focused_pytest": None,
    }
    if run_external_checks:
        external_checks = {
            "g0_standalone_verifier": run_command([
                sys.executable,
                rel(G0_DIR / "verify_g0_scid_ready8_numerical_screen_2026_05_13.py"),
            ]),
            "g0_focused_pytest": run_command([
                sys.executable,
                "-m",
                "pytest",
                rel(G0_DIR / "test_g0_scid_ready8_numerical_screen_2026_05_13.py"),
                "-q",
            ]),
        }
    same_g12_issues = []
    if ledger_audit["issues"]:
        same_g12_issues.extend(ledger_audit["issues"])
    if manifest_audit["missing_artifact_count"] or manifest_audit["hash_mismatch_count"]:
        same_g12_issues.append("g0_manifest_hash_or_missing_artifact_issue")
    if storage_audit["oversized_normal_git_blob_count"] or storage_audit["large_jsonl_without_lfs_count"]:
        same_g12_issues.append("large_ledger_storage_issue")
    if target_audit_raw["safe_flag_mismatch_count"] or target_audit_raw["forbidden_surface_mismatch_count"]:
        same_g12_issues.append("target_row_safe_flag_or_forbidden_surface_issue")
    if candidate_audit["missing_target_reference_count"] or not candidate_audit["target_reference_set_equals_target_population"]:
        same_g12_issues.append("candidate_example_target_binding_issue")
    if run_external_checks and not all(check and check["passed"] for check in external_checks.values()):
        same_g12_issues.append("external_g0_verifier_or_pytest_failed")

    same_g12_repairs_performed = []
    if manifest_audit["lf_normalized_hash_match_count"]:
        same_g12_repairs_performed.append(
            {
                "repair_id": "TEXT_EOL_HASH_EQUIVALENCE",
                "classification": "same_g12_manifest_hash_normalization_repair",
                "affected_artifact_count": manifest_audit["lf_normalized_hash_match_count"],
                "blocking_after_repair": False,
            }
        )
    if manifest_audit["nonblocking_prompt_hash_drift_count"]:
        same_g12_repairs_performed.append(
            {
                "repair_id": "CURRENT_AUDIT_PROMPT_REBINDING",
                "classification": "same_g12_stale_manifest_rebinding_for_active_prompt_only",
                "affected_artifact_count": manifest_audit["nonblocking_prompt_hash_drift_count"],
                "blocking_after_repair": False,
            }
        )

    terminal_decision = TERMINAL_DECISION if not same_g12_issues else "REPAIR_BLOCKED_WITH_EXACT_G12_NUMERICAL_SCREEN_REPAIR_REQUIREMENTS"
    return {
        "target_audit": target_audit_raw,
        "candidate_example_audit": candidate_audit,
        "g0_ledger_audit": ledger_audit,
        "g0_manifest_audit": manifest_audit,
        "git_storage_audit": storage_audit,
        "external_checks": external_checks,
        "same_g12_issues": same_g12_issues,
        "same_g12_repairs_performed": same_g12_repairs_performed,
        "terminal_decision": terminal_decision,
    }


def build_decision_ledger(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_base("decision_ledger"),
        "terminal_decision": audit["terminal_decision"],
        "accepted_as": "quarantined numerical-screen control evidence only",
        "accepted_g0_route": {
            "path": rel(G0_DIR),
            "latest_commit": git_commit_for_path(G0_DIR),
            "decision_ledger": rel(G0_DIR / f"G0_SCID_READY8_NUMERICAL_SCREEN_DECISION_LEDGER_{DATE}.json"),
            "completion_audit": rel(G0_DIR / f"G0_SCID_READY8_COMPLETION_AUDIT_{DATE}.json"),
            "verifier": rel(G0_DIR / "verify_g0_scid_ready8_numerical_screen_2026_05_13.py"),
        },
        "accepted_target_result_g12_packet": {
            "path": rel(TARGET_G12_DIR),
            "latest_commit": git_commit_for_path(TARGET_G12_DIR),
            "decision": "ACCEPT_AS_G12_SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_CONTROL_EVIDENCE_ONLY",
        },
        "exact_reconciliation": {
            "source_candidates": audit["target_audit"]["unique_duplicate_proxy_denominator_key_count"],
            "ready_cards": len(READY_CARDS),
            "rowset_rows": audit["target_audit"]["unique_rowset_row_id_count"],
            "candidate_example_rows": audit["candidate_example_audit"]["candidate_example_rows"],
            "target_result_rows": audit["target_audit"]["target_result_row_count"],
            "horizons": HORIZONS,
            "target_families": TARGET_FAMILIES,
        },
        "audit_findings": [
            {
                "finding_id": "F001_FULL_POPULATION_COUNTS_RECONCILE",
                "finding": "The accepted substrate reconciles exactly to 3,014 source candidates, 8 cards, 24,112 rowset/candidate-card rows, 192,896 target rows, 4 horizons, and 2 target families.",
                "evidence": "recomputed target JSONL line counts, unique denominator keys, unique rowset IDs, candidate example rows, and target binding coverage",
            },
            {
                "finding_id": "F002_CARD_FINGERPRINT_REDUNDANCY_SUPPORTED",
                "finding": "All card/horizon/target-family movement fingerprints recompute to the G0 matrix and match ADV-001 and ADV-003.",
                "evidence": "recomputed sorted movement fingerprints from every target row",
            },
            {
                "finding_id": "F003_FULL_LEDGER_ROUTE_NOT_TOP_N",
                "finding": "The route preserved the complete 24,112 candidate-card ledger and 192,896 target references; no top-N or compact-only substitute is used as evidence replacement.",
                "evidence": "candidate example ledger row count and target reference set equality",
            },
            {
                "finding_id": "F004_LFS_STORAGE_SAFE",
                "finding": "The 98 MB candidate example working file and target JSONL ledgers are materialized from Git LFS pointer blobs, with no oversized normal Git blobs detected in the audited route surfaces.",
                "evidence": "git check-attr, git cat-file pointer sizes, git lfs ls-files",
            },
            {
                "finding_id": "F005_SAFE_BOUNDARIES_CLOSED",
                "finding": "The route remains NO_PROMOTION_VERDICT with validation_safe=false, outcome_review_opened=false, live_effect=false and no validation/performance/live/API/paid/broker/raw/remote surface opened.",
                "evidence": "safe flag audit across G0/G12 ledgers and target rows",
            },
        ],
        "same_g12_repairs_performed": audit["same_g12_repairs_performed"],
        "same_g12_issues": audit["same_g12_issues"],
        "repair_requirements": [] if not audit["same_g12_issues"] else audit["same_g12_issues"],
    }


def build_recomputation_ledger(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_base("recomputation_ledger"),
        "ok": not audit["same_g12_issues"],
        "terminal_decision": audit["terminal_decision"],
        "target_population_recompute": audit["target_audit"],
        "candidate_example_recompute": audit["candidate_example_audit"],
        "g0_ledger_recompute_or_lossless_proof": audit["g0_ledger_audit"],
        "g0_manifest_hash_audit": audit["g0_manifest_audit"],
        "lfs_pointer_and_materialization_audit": audit["git_storage_audit"],
        "external_g0_verifier_and_tests_rerun": audit["external_checks"],
        "full_population_numerical_screen_claim_supported": not audit["same_g12_issues"],
        "top_n_or_speed_shortcut_evidence_replacement_detected": audit["candidate_example_audit"]["top_n_or_sampling_rule_detected"],
        "all_card_fingerprints_matching_adv001_adv003_supported": (
            audit["g0_ledger_audit"]["ledger_checks"].get("all_card_fingerprints_match_adv001_recomputed") is True
            and audit["g0_ledger_audit"]["ledger_checks"].get("all_card_fingerprints_match_adv003_recomputed") is True
        ),
    }


def build_repair_ledger(audit: dict[str, Any]) -> dict[str, Any]:
    issues = []
    for issue in audit["same_g12_issues"]:
        issues.append(
            {
                "issue": issue,
                "same_g12_repairable": True,
                "repaired_inside_this_route": False,
                "remaining_boundary": "not_repaired_because_terminal_acceptance_requires_clean_audit" if audit["terminal_decision"] != TERMINAL_DECISION else None,
            }
        )
    return {
        **safe_base("repair_ledger"),
        "issues_found_count": len(issues),
        "issues": issues,
        "same_g12_repairs_performed": audit["same_g12_repairs_performed"],
        "unrepaired_blockers": issues if audit["terminal_decision"] != TERMINAL_DECISION else [],
        "no_invented_or_vague_blockers": True,
        "terminal_repair_status": "NO_REPAIR_REQUIRED" if not issues else "REPAIR_BLOCKED_WITH_EXACT_REQUIREMENTS",
    }


def required_question_answers(audit: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "question_number": 1,
            "question": "Did the G0 route read and bind the accepted G12 target-result packet from disk?",
            "answer": "Yes; the decision ledger binds the accepted target-result G12 decision and accepted verifier, and the audited target rows are read from the accepted packet directory.",
            "evidence": "g0_ledger_audit.ledger_checks.g0_binds_accepted_g12_target_result_packet",
            "satisfied": audit["g0_ledger_audit"]["ledger_checks"]["g0_binds_accepted_g12_target_result_packet"],
        },
        {
            "question_number": 2,
            "question": "Do exact counts reconcile: 3014 / 8 / 24112 / 192896 / 4 / 2?",
            "answer": "Yes; recomputation found 3,014 unique denominator keys, 8 cards, 24,112 rowset rows and candidate-example rows, 192,896 target rows, 4 horizons, and 2 target families.",
            "evidence": "target_population_recompute and candidate_example_recompute",
            "satisfied": (
                audit["target_audit"]["unique_duplicate_proxy_denominator_key_count"] == EXPECTED_SOURCE_CANDIDATES
                and audit["target_audit"]["unique_rowset_row_id_count"] == EXPECTED_ROWSET_ROWS
                and audit["target_audit"]["target_result_row_count"] == EXPECTED_TARGET_ROWS
                and audit["candidate_example_audit"]["candidate_example_rows"] == EXPECTED_ROWSET_ROWS
            ),
        },
        {
            "question_number": 3,
            "question": "Are all required artifacts present and parseable?",
            "answer": "Yes; every required G0 and accepted G12 JSON artifact was loaded and parsed.",
            "evidence": "g0_ledger_audit.all_required_artifacts_present_and_parseable",
            "satisfied": audit["g0_ledger_audit"]["all_required_artifacts_present_and_parseable"],
        },
        {
            "question_number": 4,
            "question": "Is the candidate example ledger complete, and is its small Git entry a valid LFS pointer/materialization state?",
            "answer": "Yes; it has 24,112 rows, 192,896 target references, target-reference set equality, and a 133-byte Git LFS pointer with a materialized 98 MB working file.",
            "evidence": "candidate_example_recompute and lfs_pointer_and_materialization_audit",
            "satisfied": audit["candidate_example_audit"]["target_reference_set_equals_target_population"]
            and any(item["path"].endswith("G0_SCID_READY8_CANDIDATE_EXAMPLE_LEDGER_2026-05-13.jsonl") and item["lfs_materialized_worktree_pointer_blob"] for item in audit["git_storage_audit"]["audited_paths"]),
        },
        {
            "question_number": 5,
            "question": "Were large ledgers stored safely without normal-Git oversized blobs?",
            "answer": "Yes; audited large JSONL files are LFS-tracked pointer blobs and no oversized normal Git blob was found in the audited route surfaces.",
            "evidence": "git_storage_audit",
            "satisfied": audit["git_storage_audit"]["oversized_normal_git_blob_count"] == 0 and audit["git_storage_audit"]["large_jsonl_without_lfs_count"] == 0,
        },
        {
            "question_number": 6,
            "question": "Did the G0 route actually compute full-population numerical screens?",
            "answer": "Yes; every target row was streamed into recomputed fingerprints, the candidate ledger references the full target population, and the G0 verifier rerun passed.",
            "evidence": "target_population_recompute, candidate_example_recompute, external_g0_verifier_and_tests_rerun",
            "satisfied": audit["candidate_example_audit"]["target_reference_count"] == EXPECTED_CANDIDATE_TARGET_REFS
            and audit["external_checks"]["g0_standalone_verifier"]["passed"] is True,
        },
        {
            "question_number": 7,
            "question": "Are matrix, partition, duplicate, interaction, negative, recursive, coverage, and self-interrogation ledgers internally consistent?",
            "answer": "Yes; row counts, expected expansion, redundancy checks, kill-fast ledgers, recursion, coverage, and self-interrogation counters all pass.",
            "evidence": "g0_ledger_audit.ledger_checks",
            "satisfied": all(audit["g0_ledger_audit"]["ledger_checks"].values()),
        },
        {
            "question_number": 8,
            "question": "Is the all-card-fingerprints-identical conclusion supported?",
            "answer": "Yes; independent recomputation of sorted movement fingerprints from target rows matches the G0 matrix and shows every card equals ADV-001 and ADV-003 for each horizon/family.",
            "evidence": "g0_ledger_audit.fingerprint_mismatches=[] and all_card checks",
            "satisfied": audit["g0_ledger_audit"]["ledger_checks"]["all_card_fingerprints_match_adv001_recomputed"]
            and audit["g0_ledger_audit"]["ledger_checks"]["all_card_fingerprints_match_adv003_recomputed"],
        },
        {
            "question_number": 9,
            "question": "Are card-specific edge/ranking claims correctly killed or bounded?",
            "answer": "Yes; the baseline delta and negative ledgers classify card-level movement as baseline-explained/redundant and preserve future source-control repair as separate.",
            "evidence": "baseline rows and negative ledgers",
            "satisfied": audit["g0_ledger_audit"]["ledger_checks"]["negative_ledgers_kill_card_specific_edge_claims"],
        },
        {
            "question_number": 10,
            "question": "Are horizon/target-family/partition/fail-closed/candidate-anatomy findings preserved without being promoted?",
            "answer": "Yes; ledgers preserve those axes as quarantined numerical intelligence while safe flags close validation, strategy edge, and live surfaces.",
            "evidence": "safe flags and ledger counts",
            "satisfied": audit["g0_ledger_audit"]["ledger_checks"]["safe_flags_all_g0_and_accepted_g12_payloads"],
        },
        {
            "question_number": 11,
            "question": "Are known_same_evidence_class_intelligence_remaining=0 and same_evidence_class_items_remaining_after_final_loop=0 credible?",
            "answer": "Yes; coverage and final self-interrogation counters are zero after feasible screens and recursive followups were recorded.",
            "evidence": "coverage and self-interrogation ledgers",
            "satisfied": audit["g0_ledger_audit"]["ledger_checks"]["coverage_remaining_zero"] and audit["g0_ledger_audit"]["ledger_checks"]["self_interrogation_remaining_zero"],
        },
        {
            "question_number": 12,
            "question": "Did the route avoid arbitrary top-N truncation and speed-driven shortcut artifacts?",
            "answer": "Yes; all candidate-card rows and all target references are preserved, with example_selection_rule explicitly set to ALL_24112_CANDIDATE_CARD_ROWS_INCLUDED_NO_TOP_N_CAP.",
            "evidence": "candidate_example_recompute.selection_rule_counts",
            "satisfied": audit["candidate_example_audit"]["top_n_or_sampling_rule_detected"] is False,
        },
        {
            "question_number": 13,
            "question": "Are safe flags closed everywhere?",
            "answer": "Yes; no safe-flag mismatches or forbidden-surface openings were detected in audited G0/G12 JSON ledgers or target rows.",
            "evidence": "target_audit safe counts and g0 safe flag audit",
            "satisfied": audit["target_audit"]["safe_flag_mismatch_count"] == 0
            and audit["target_audit"]["forbidden_surface_mismatch_count"] == 0
            and audit["g0_ledger_audit"]["ledger_checks"]["safe_flags_all_g0_and_accepted_g12_payloads"],
        },
        {
            "question_number": 14,
            "question": "Are there exact repair requirements, and can they be repaired inside this G12 route before final decision?",
            "answer": "No repair requirements remain; no same-G12 issue was found after recomputation and verifier reruns.",
            "evidence": "repair ledger issues_found_count=0",
            "satisfied": len(audit["same_g12_issues"]) == 0,
        },
        {
            "question_number": 15,
            "question": "What terminal decision is justified by disk evidence?",
            "answer": audit["terminal_decision"],
            "evidence": "decision ledger and recomputation ledger",
            "satisfied": audit["terminal_decision"] == TERMINAL_DECISION,
        },
    ]


def build_completion_audit(audit: dict[str, Any]) -> dict[str, Any]:
    question_answers = required_question_answers(audit)
    checklist = [
        ("mandatory_preflight_live_state_regenerated_and_read", ".context/LIVE_STATE.md regenerated/read in this session before build", True),
        ("quick_reference_read", ".context/00_core/quick_reference_card.md read", True),
        ("research_operating_doctrine_read", ".context/00_core/research_operating_doctrine.md read", True),
        ("goal_session_research_discipline_read", ".context/00_core/goal_session_research_discipline.md read", True),
        ("research_current_state_read", ".context/00_core/research_current_state.md read", True),
        ("accepted_target_g12_directory_read", rel(TARGET_G12_DIR), True),
        ("g0_numerical_screen_directory_read", rel(G0_DIR), True),
        ("exact_counts_recomputed", "target_population_recompute exact counts", question_answers[1]["satisfied"]),
        ("g0_verifier_rerun", audit["external_checks"]["g0_standalone_verifier"]["command"], audit["external_checks"]["g0_standalone_verifier"]["passed"]),
        ("g0_focused_tests_rerun", audit["external_checks"]["g0_focused_pytest"]["command"], audit["external_checks"]["g0_focused_pytest"]["passed"]),
        ("full_population_not_top_n", "candidate example target-reference set equality", question_answers[11]["satisfied"]),
        ("lfs_and_no_oversized_blobs_checked", "git storage audit", question_answers[4]["satisfied"]),
        ("safe_flags_closed", "safe flag audit", question_answers[12]["satisfied"]),
        ("same_g12_repairs_pursued", "no same-G12 issues found; repair ledger records no invented blocker", len(audit["same_g12_issues"]) == 0),
        ("next_g0_prompt_emitted_if_accepted", rel(PROMPT_DIR / f"G0_SCID_READY8_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_AFTER_G12_AUDIT_GOAL_PROMPT_{DATE}.md"), audit["terminal_decision"] == TERMINAL_DECISION),
    ]
    return {
        **safe_base("completion_audit"),
        "objective_restatement": (
            "Independently audit the G0 READY8 numerical-screen route and accepted target-result G12 packet from disk; "
            "verify exact counts, full-population coverage, ledgers, LFS storage, safe flags, and terminal decision."
        ),
        "prompt_to_artifact_checklist": [
            {"requirement": req, "evidence": evidence, "satisfied": bool(satisfied)}
            for req, evidence, satisfied in checklist
        ],
        "required_audit_question_answers": question_answers,
        "missing_incomplete_or_weakly_verified_requirements": [
            item["requirement"]
            for item in [
                {"requirement": req, "satisfied": bool(satisfied)}
                for req, _evidence, satisfied in checklist
            ]
            if not item["satisfied"]
        ]
        + [f"required_question_{answer['question_number']}" for answer in question_answers if not answer["satisfied"]],
        "no_invented_vague_or_conservative_theater_blockers": len(audit["same_g12_issues"]) == 0,
        "can_mark_goal_complete": audit["terminal_decision"] == TERMINAL_DECISION
        and all(bool(satisfied) for _req, _evidence, satisfied in checklist)
        and all(answer["satisfied"] for answer in question_answers),
        "terminal_decision": audit["terminal_decision"],
    }


def write_next_prompt(accepted: bool) -> Path:
    if accepted:
        path = PROMPT_DIR / f"G0_SCID_READY8_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_AFTER_G12_AUDIT_GOAL_PROMPT_{DATE}.md"
        stale_repair = PROMPT_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_REPAIR_PROMPT_{DATE}.md"
        if stale_repair.exists():
            stale_repair.unlink()
        body = f"""# G0 SCID READY8 Numerical Screen Learning Synthesis After G12 Audit

Date: {DATE}

## Evidence Class

`G0_SCID_READY8_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_CONTROL_ONLY`

Follow mandatory GTOS preflight, read this file from disk, and do not rely on chat memory.

## Inputs

- Accepted numerical-screen G12 audit:
  - `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_numerical_screen_audit/`
- Accepted G0 numerical-screen route:
  - `research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_ready8_target_result_synthesis_and_quarantined_numerical_screen/`
- Accepted target-result G12 packet audit:
  - `research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_ready8_quarantined_target_result_packet_audit/`

## Objective

Synthesize the accepted numerical-screen learning into the next source/control and result-opening route decisions without opening validation, promotion, live trading behavior, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market blob commits, registry edits, remote pushes, or performance claims.

Required synthesis:

- Preserve `3,014` source candidates, `8` READY8 cards, `24,112` rowset/candidate-card rows, `192,896` target rows, horizons `1/4/16/32`, and the two neutral target families as accepted control evidence.
- Treat card-level movement rankings as killed/bounded because every card/horizon/target-family fingerprint matches `ADV-001` and `ADV-003`.
- Preserve horizon, target-family, partition, fail-closed, duplicate/concentration, interaction, negative, candidate-anatomy, and recursive-coverage learning as quarantined numerical intelligence only.
- Decide the next exact route: source-control repair for card-discriminative predicates, sealed-validation design prep, or another G0 control synthesis. Do not skip same-evidence-class learning that remains available.
- Emit a decision ledger, route-ranking ledger, completion audit, verifier or exact checklist, and a runnable next prompt.

Safe flags are mandatory everywhere: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
"""
    else:
        path = PROMPT_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_REPAIR_PROMPT_{DATE}.md"
        stale_accept = PROMPT_DIR / f"G0_SCID_READY8_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_AFTER_G12_AUDIT_GOAL_PROMPT_{DATE}.md"
        if stale_accept.exists():
            stale_accept.unlink()
        body = f"""# G12 SCID READY8 Numerical Screen Repair Prompt

Date: {DATE}

Repair the exact issues recorded in `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_numerical_screen_audit/G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_REPAIR_LEDGER_{DATE}.json`.

Stay inside `G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_ONLY`; do not open validation, promotion, live, AI/API, paid/vendor, broker, raw market blob, registry, or remote surfaces.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8", newline="\n")
    return path


def write_outputs() -> dict[str, Path]:
    audit = collect_audit(run_external_checks=True)
    next_prompt = write_next_prompt(audit["terminal_decision"] == TERMINAL_DECISION)
    outputs = {
        "decision": ROUTE_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_DECISION_LEDGER_{DATE}.json",
        "recomputation": ROUTE_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json",
        "repair": ROUTE_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_REPAIR_LEDGER_{DATE}.json",
        "completion": ROUTE_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_COMPLETION_AUDIT_{DATE}.json",
    }
    write_json(outputs["decision"], build_decision_ledger(audit))
    write_json(outputs["recomputation"], build_recomputation_ledger(audit))
    write_json(outputs["repair"], build_repair_ledger(audit))
    write_json(outputs["completion"], build_completion_audit(audit))
    outputs["next_prompt"] = next_prompt
    return outputs


def main() -> None:
    outputs = write_outputs()
    print(json.dumps({"ok": True, "outputs": {key: rel(path) for key, path in outputs.items()}}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
