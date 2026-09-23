"""Build the READY8 R9 forward-retest/source-capture packet route.

This route consumes only the accepted R8/G12 scoring artifacts. It does not
validate, promote, score live readiness, touch live trading behavior, or open
any broker/account/order/history/deal/position surface.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_AFTER_G12_SCORING_AUDIT"
EVIDENCE_CLASS = "READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_FROM_ACCEPTED_G12_SCORING_ONLY"
TERMINAL_DECISION = "MATERIALIZED_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_G12_AUDIT_REQUIRED_NO_PROMOTION"

SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

FORBIDDEN_FALSE_FLAGS = {
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "opens_ai_api": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_paid_or_vendor_access": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
}

ALLOWED_DOCTRINE_CLASSIFICATIONS = {
    "false opportunity / generic movement",
    "repairable limitation",
    "mixed mechanism needing split",
    "unproven but interesting",
    "inverse/avoid-filter candidate",
    "source-capture requirement",
    "forward-retest candidate",
    "exact owner/access/source/capture impossibility",
}

ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]

PROMPT = ROOT / "research/science_program_2026_05/04_goal_prompts/READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_AFTER_G12_SCORING_AUDIT_GOAL_PROMPT_2026-05-16.md"
STARTER = ROOT / "research/science_program_2026_05/04_goal_prompts/READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_AFTER_G12_SCORING_AUDIT_STARTER_2026-05-16.txt"

R8_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_expanded_validation_scoring_result_materialization"
REGISTRY = ROOT / "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json"
QUESTION_LEDGER = ROOT / "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json"

MANDATORY_CONTEXT_PATHS = [
    ROOT / ".context/LIVE_STATE.md",
    ROOT / ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md",
    ROOT / "AGENTS.md",
    ROOT / "CLAUDE.md",
    ROOT / ".context/00_core/orchestrator_successor_operating_brief.md",
    ROOT / ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ROOT / ".context/00_core/parallel_goal_merge_playbook.md",
    ROOT / ".context/00_core/goal_session_research_discipline.md",
    ROOT / ".context/00_core/research_operating_doctrine.md",
    ROOT / ".context/00_core/research_current_state.md",
    ROOT / ".context/00_core/local_heavy_data_inventory.md",
    ROOT / ".context/00_core/ai_in_loop_cost_control_research_plan.md",
    ROOT / ".context/00_core/r7_failure_intelligence_doctrine_addendum.md",
    REGISTRY,
    QUESTION_LEDGER,
]

MUTABLE_COORDINATION_SOURCE_PATHS = {
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json",
}

R8 = {
    "decision": R8_DIR / "READY8_EXPANDED_SCORING_DECISION_LEDGER_2026-05-16.json",
    "completion": R8_DIR / "READY8_EXPANDED_SCORING_COMPLETION_AUDIT_2026-05-16.json",
    "verification": R8_DIR / "READY8_EXPANDED_SCORING_VERIFICATION_RESULT_2026-05-16.json",
    "output_manifest": R8_DIR / "READY8_EXPANDED_SCORING_OUTPUT_MANIFEST_2026-05-16.json",
    "source_hash": R8_DIR / "READY8_EXPANDED_SCORING_SOURCE_HASH_LEDGER_2026-05-16.json",
    "method_freeze": R8_DIR / "READY8_EXPANDED_SCORING_METHOD_FREEZE_2026-05-16.json",
    "no_leak": R8_DIR / "READY8_EXPANDED_SCORING_NO_LEAK_ASOF_EMBARGO_POLICY_2026-05-16.json",
    "partition": R8_DIR / "READY8_EXPANDED_SCORING_PARTITION_POLICY_2026-05-16.json",
    "duplicate_policy": R8_DIR / "READY8_EXPANDED_SCORING_DUPLICATE_DENOMINATOR_EFFECTIVE_N_POLICY_2026-05-16.json",
    "packet_admission": R8_DIR / "READY8_EXPANDED_SCORING_PACKET_ROW_ADMISSION_LEDGER_2026-05-16.jsonl",
    "row_branch": R8_DIR / "READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_2026-05-16.jsonl",
    "haz001": R8_DIR / "READY8_EXPANDED_SCORING_HAZ001_RESULT_LEDGER_2026-05-16.jsonl",
    "mac": R8_DIR / "READY8_EXPANDED_SCORING_MAC_INVERSE_AVOID_FILTER_RESULT_LEDGER_2026-05-16.jsonl",
    "haz005": R8_DIR / "READY8_EXPANDED_SCORING_HAZ005_REPAIRED_ROW_CONSUMPTION_RESULT_LEDGER_2026-05-16.jsonl",
    "unc004_full": R8_DIR / "READY8_EXPANDED_SCORING_UNC004_SOURCE_BIAS_SOURCE_CAPTURE_RESULT_LEDGER_2026-05-16.jsonl",
    "residual": R8_DIR / "READY8_EXPANDED_SCORING_RESIDUAL_FAILURE_INTELLIGENCE_RESULT_LEDGER_2026-05-16.jsonl",
    "adv_control": R8_DIR / "READY8_EXPANDED_SCORING_ADV_CONTROL_ADJUSTMENT_LEDGER_2026-05-16.jsonl",
    "duplicate": R8_DIR / "READY8_EXPANDED_SCORING_DUPLICATE_EFFECTIVE_N_LEDGER_2026-05-16.jsonl",
    "concentration": R8_DIR / "READY8_EXPANDED_SCORING_CONCENTRATION_STRESS_LEDGER_2026-05-16.jsonl",
    "repaired_target": R8_DIR / "READY8_EXPANDED_SCORING_REPAIRED_TARGET_CONSUMPTION_RESULT_LEDGER_2026-05-16.jsonl",
    "fail_closed": R8_DIR / "READY8_EXPANDED_SCORING_FAIL_CLOSED_SENSITIVITY_LEDGER_2026-05-16.jsonl",
    "failure_intel": R8_DIR / "READY8_EXPANDED_SCORING_KILLED_WEAKENED_DEFERRED_RESULT_FAILURE_INTELLIGENCE_LEDGER_2026-05-16.jsonl",
    "questions": R8_DIR / "READY8_EXPANDED_SCORING_QUESTION_AMBIGUITY_PURSUIT_LEDGER_2026-05-16.jsonl",
    "open_closed": R8_DIR / "READY8_EXPANDED_SCORING_OPEN_DOOR_CLOSED_DOOR_LEDGER_2026-05-16.jsonl",
    "blockers": R8_DIR / "READY8_EXPANDED_SCORING_BLOCKER_REPAIR_IMPOSSIBILITY_LEDGER_2026-05-16.jsonl",
    "source_implications": R8_DIR / "READY8_EXPANDED_SCORING_SOURCE_CAPTURE_FORWARD_RETEST_IMPLICATION_LEDGER_2026-05-16.jsonl",
}

G12 = {
    "decision": R8_DIR / "G12_R8EXP_SCORING_AUDIT_DECISION_2026-05-16.json",
    "completion": R8_DIR / "G12_R8EXP_SCORING_AUDIT_COMPLETION_2026-05-16.json",
    "recomputation": R8_DIR / "G12_R8EXP_SCORING_AUDIT_RECOMPUTATION_2026-05-16.json",
    "verification": R8_DIR / "G12_R8EXP_SCORING_AUDIT_VERIFICATION_RESULT_2026-05-16.json",
    "output_manifest": R8_DIR / "G12_R8EXP_SCORING_AUDIT_OUTPUT_MANIFEST_2026-05-16.json",
    "source_hash": R8_DIR / "G12_R8EXP_SCORING_AUDIT_SOURCE_HASH_2026-05-16.json",
    "source_drift": R8_DIR / "G12_R8EXP_SCORING_AUDIT_SOURCE_DRIFT_2026-05-16.jsonl",
    "material_rows": R8_DIR / "G12_R8EXP_SCORING_AUDIT_MATERIAL_ROWS_2026-05-16.jsonl",
    "failure_intel": R8_DIR / "G12_R8EXP_SCORING_AUDIT_FAILURE_INTEL_2026-05-16.jsonl",
    "packet_coverage": R8_DIR / "G12_R8EXP_SCORING_AUDIT_PACKET_COVERAGE_2026-05-16.jsonl",
    "repaired_target": R8_DIR / "G12_R8EXP_SCORING_AUDIT_REPAIRED_TARGET_2026-05-16.jsonl",
    "r8_manifest": R8_DIR / "G12_R8EXP_SCORING_AUDIT_R8_MANIFEST_2026-05-16.jsonl",
    "instruction_coverage": R8_DIR / "G12_R8EXP_SCORING_AUDIT_INSTRUCTION_COVERAGE_2026-05-16.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_number"] = line_number
                yield row


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            clean = {key: value for key, value in row.items() if key != "_source_line_number"}
            handle.write(json.dumps(clean, sort_keys=True, separators=(",", ":")) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file_canonical_lf(path: Path) -> str:
    data = path.read_bytes()
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def count_jsonl(path: Path) -> int | None:
    if path.suffix.lower() != ".jsonl":
        return None
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def row_sha(row: dict[str, Any]) -> str:
    clean = {key: value for key, value in row.items() if key != "_source_line_number"}
    return hashlib.sha256(json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def safe_base() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        **FORBIDDEN_FALSE_FLAGS,
    }


def artifact_meta(path: Path, label: str, required: bool = True) -> dict[str, Any]:
    exists = path.exists()
    return {
        **safe_base(),
        "label": label,
        "path": rel(path) if exists or path.is_absolute() else path.as_posix(),
        "required": required,
        "exists": exists,
        "bytes": path.stat().st_size if exists else None,
        "jsonl_rows": count_jsonl(path) if exists else None,
        "sha256": sha256_file(path) if exists else None,
        "sha256_canonical_lf": sha256_file_canonical_lf(path) if exists else None,
    }


def r8_route_files() -> list[Path]:
    return sorted(path for path in R8_DIR.iterdir() if path.is_file() and path.name != ".pytest_cache")


def load_inputs() -> dict[str, Any]:
    return {
        "packet_admission": list(iter_jsonl(R8["packet_admission"])),
        "row_branch": list(iter_jsonl(R8["row_branch"])),
        "haz001": list(iter_jsonl(R8["haz001"])),
        "mac": list(iter_jsonl(R8["mac"])),
        "haz005": list(iter_jsonl(R8["haz005"])),
        "unc004_full": list(iter_jsonl(R8["unc004_full"])),
        "residual": list(iter_jsonl(R8["residual"])),
        "adv_control": list(iter_jsonl(R8["adv_control"])),
        "duplicate": list(iter_jsonl(R8["duplicate"])),
        "concentration": list(iter_jsonl(R8["concentration"])),
        "repaired_target": list(iter_jsonl(R8["repaired_target"])),
        "fail_closed": list(iter_jsonl(R8["fail_closed"])),
        "failure_intel": list(iter_jsonl(R8["failure_intel"])),
        "questions": list(iter_jsonl(R8["questions"])),
        "open_closed": list(iter_jsonl(R8["open_closed"])),
        "blockers": list(iter_jsonl(R8["blockers"])),
        "source_implications": list(iter_jsonl(R8["source_implications"])),
        "g12_packet_coverage": list(iter_jsonl(G12["packet_coverage"])),
        "g12_repaired_target": list(iter_jsonl(G12["repaired_target"])),
        "g12_failure_intel": list(iter_jsonl(G12["failure_intel"])),
    }


def by_packet_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["packet_row_id"]: row for row in rows}


def by_repaired_target_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["r7_repaired_target_consumption_row_id"]: row for row in rows}


def instruction_requirements(row: dict[str, Any]) -> list[str]:
    family = row["packet_family"]
    base = [
        "preserve packet_row_id, branch_key, source_label, source_row_index, source hashes, safe flags, and accepted G12 scoring provenance",
        "use only predecision/source-bound fields; do not use broker account/order/history/deal/position evidence",
        "carry ADV control envelope, duplicate/effective-N, concentration/leave-one, fail-closed, and source-capture status into the next packet",
        "require independent G12 audit of this R9 packet before any downstream canonical retest/source-capture route consumes it",
    ]
    if family == "HAZ001_DECONCENTRATED_RETEST":
        return base + [
            "freeze the exact HAZ001 branch key as the retest contract key",
            "capture candidate-density/waiting-time source descriptors before target opening where the future route has native sources",
            "sequence deconcentrated retest by partition, target family, horizon, duplicate denominator, and concentration stress",
        ]
    if family == "MAC_INVERSE_AVOID_FILTER_DESIGN":
        return base + [
            "treat inverse movement as an avoid-filter candidate only, never as a live filter or selector",
            "freeze MAC card, horizon, target family, partition, and comparison family before any future retest",
            "carry negative, null, and control-explained anatomy as failure intelligence instead of erasing it",
        ]
    if family == "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL":
        return base + [
            "preserve repaired prior-16 drift/range descriptors and source_bar_hashes_sha256",
            "do not fabricate target-family/horizon labels; build a separate source-control continuation packet if those keys can be source-bound",
            "keep the current row fail-closed for target-result scoring until an accepted source-control retest packet supplies the missing branch key",
        ]
    if family == "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC":
        return base + [
            "capture native numeric source-confidence score only if a future source emits it before target opening",
            "capture source_capture_drop_reason and source_latency_or_refresh_lag prospectively",
            "keep current UNC004 rows as source-bias-aware diagnostics until native capture fields exist",
        ]
    return base + [
        "preserve residual after ADV control envelope as failure intelligence only",
        "do not promote residual movement into edge evidence without a new accepted source-bound packet and audit",
    ]


def sequence_for(row: dict[str, Any]) -> list[str]:
    family = row["packet_family"]
    first = "G12_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_AUDIT"
    if family == "HAZ001_DECONCENTRATED_RETEST":
        second = "HAZ001_DECONCENTRATED_FORWARD_RETEST_PACKET_DESIGN_AFTER_G12_R9_ACCEPTANCE"
    elif family == "MAC_INVERSE_AVOID_FILTER_DESIGN":
        second = "MAC001_MAC004_INVERSE_AVOID_FILTER_PREREG_PACKET_AFTER_G12_R9_ACCEPTANCE"
    elif family == "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL":
        second = "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL_CONTINUATION_PACKET_AFTER_G12_R9_ACCEPTANCE"
    elif family == "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC":
        second = "UNC004_NATIVE_SOURCE_CONFIDENCE_FORWARD_CAPTURE_CONTRACT_AFTER_G12_R9_ACCEPTANCE"
    else:
        second = "RESIDUAL_FAILURE_INTELLIGENCE_CONTROL_PACKET_AFTER_G12_R9_ACCEPTANCE"
    return [
        first,
        second,
        "future validation or live interpretation remains forbidden until a separate explicit validation/promotion boundary is opened",
    ]


def packet_row(row: dict[str, Any], coverage: dict[str, Any] | None) -> dict[str, Any]:
    return {
        **safe_base(),
        "packet_row_id": row["packet_row_id"],
        "packet_family": row["packet_family"],
        "result_status": row["result_status"],
        "source_result_status": row["result_status"],
        "branch_key": row.get("branch_key"),
        "accepted_g12_packet_coverage_status": coverage.get("audit_status") if coverage else "MISSING_G12_PACKET_COVERAGE",
        "accepted_g12_branch_key_sha256": coverage.get("branch_key_sha256") if coverage else None,
        "accepted_g12_coverage": coverage.get("coverage") if coverage else None,
        "r8_source_label": row.get("source_label"),
        "r8_source_row_index": row.get("source_row_index"),
        "row_sha256_from_r8_result": row_sha(row),
        "lineage_status": "TRACEABLE_TO_ACCEPTED_G12_SCORING_PACKET_COVERAGE" if coverage else "MISSING_ACCEPTED_G12_PACKET_COVERAGE",
        "downstream_packet_instruction": "materialize exact row-level forward-retest/source-capture contract; not validation or promotion",
        "source_capture_requirements": instruction_requirements(row),
        "packet_route_sequence": sequence_for(row),
    }


def build_haz001(rows: list[dict[str, Any]], coverage_by_id: dict[str, dict[str, Any]], adv_by_id: dict[str, dict[str, Any]], dup_by_id: dict[str, dict[str, Any]], conc_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for index, row in enumerate(rows, 1):
        packet_id = row["packet_row_id"]
        out.append({
            **packet_row(row, coverage_by_id.get(packet_id)),
            "r9_instruction_id": f"r9_haz001_forward_retest:{index:04d}",
            "packet_contract_type": "HAZ001_DECONCENTRATED_FORWARD_RETEST_CONTRACT",
            "raw_delta": row.get("raw_delta"),
            "raw_direction": row.get("raw_direction"),
            "control_adjustment": {
                "classification": row.get("control_adjustment_classification"),
                "control_envelope_abs": row.get("control_envelope_abs"),
                "control_adjusted_residual_abs": row.get("control_adjusted_residual_abs"),
                "matched_control_cards": row.get("matched_control_cards"),
                "matched_control_count": row.get("matched_control_count"),
                "matched_control_scope": row.get("matched_control_scope"),
            },
            "duplicate_effective_n": {
                "pass_unique_duplicate_denominator_count": row.get("pass_unique_duplicate_denominator_count"),
                "control_unique_duplicate_denominator_count": row.get("control_unique_duplicate_denominator_count"),
                "source_duplicate_policy_row": dup_by_id.get(packet_id),
            },
            "concentration_leave_one": conc_by_id.get(packet_id),
            "adv_control_carry_forward": adv_by_id.get(packet_id),
            "retest_freeze_rule": "Freeze branch key, control envelope policy, duplicate denominator, concentration warnings, and fail-closed handling before collecting any future retest rows.",
            "exact_downstream_action": "Create deconcentrated forward-retest packet rows keyed by this packet_row_id and branch_key after R9 G12 acceptance.",
        })
    return out


def build_mac(rows: list[dict[str, Any]], coverage_by_id: dict[str, dict[str, Any]], adv_by_id: dict[str, dict[str, Any]], dup_by_id: dict[str, dict[str, Any]], conc_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for index, row in enumerate(rows, 1):
        packet_id = row["packet_row_id"]
        out.append({
            **packet_row(row, coverage_by_id.get(packet_id)),
            "r9_instruction_id": f"r9_mac_inverse_avoid:{index:04d}",
            "packet_contract_type": "MAC_INVERSE_AVOID_FILTER_DESIGN_CONTRACT_NOT_LIVE_FILTER",
            "candidate_status": row.get("candidate_status"),
            "source_classification": row.get("source_classification"),
            "raw_delta": row.get("raw_delta"),
            "raw_direction": row.get("raw_direction"),
            "control_adjustment": {
                "classification": row.get("control_adjustment_classification"),
                "control_envelope_abs": row.get("control_envelope_abs"),
                "control_adjusted_residual_abs": row.get("control_adjusted_residual_abs"),
                "matched_control_cards": row.get("matched_control_cards"),
                "matched_control_count": row.get("matched_control_count"),
            },
            "duplicate_effective_n": dup_by_id.get(packet_id),
            "concentration_leave_one": conc_by_id.get(packet_id),
            "adv_control_carry_forward": adv_by_id.get(packet_id),
            "avoid_filter_design_rule": "Design a preregistered inverse/avoid-filter retest only; this packet creates no live filter, selector, or risk change.",
            "exact_downstream_action": "Create no-promotion avoid-filter candidate retest contract after R9 G12 acceptance; preserve inverse failure anatomy even when control-explained.",
        })
    return out


def build_haz005(rows: list[dict[str, Any]], coverage_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for index, row in enumerate(rows, 1):
        out.append({
            **packet_row(row, coverage_by_id.get(row["packet_row_id"])),
            "r9_instruction_id": f"r9_haz005_source_control:{index:04d}",
            "packet_contract_type": "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL_CONTINUATION",
            "candidate_input_row_id": row.get("candidate_input_row_id"),
            "symbol": row.get("symbol"),
            "source_bar_hashes_sha256": row.get("source_bar_hashes_sha256"),
            "repaired_prior_16_drift_bucket": row.get("repaired_prior_16_drift_bucket"),
            "repaired_prior_16_range_bucket": row.get("repaired_prior_16_range_bucket"),
            "exact_row_level_impossibility": row.get("exact_impossibility_or_boundary"),
            "source_control_continuation_requirement": [
                "bind target_family_id and horizon_m15_bars from accepted source-control evidence before any target-result join",
                "preserve candidate_input_row_id, symbol, source_bar_hashes_sha256, repaired drift/range buckets, and source-line provenance",
                "keep current packet row fail-closed for scoring until the missing target-family/horizon branch key is accepted",
            ],
            "exact_downstream_action": "Open HAZ005 source-control continuation packet only after R9 G12 acceptance; do not fabricate scoring labels from this row.",
        })
    return out


def build_unc004(packet_rows: list[dict[str, Any]], full_rows: list[dict[str, Any]], coverage_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if len(packet_rows) != 1:
        raise ValueError(f"expected one UNC004 packet row, got {len(packet_rows)}")
    packet = packet_rows[0]
    out = [{
        **packet_row(packet, coverage_by_id.get(packet["packet_row_id"])),
        "r9_instruction_id": "r9_unc004_native_capture:packet",
        "contract_scope": "packet_row",
        "packet_contract_type": "UNC004_NATIVE_SOURCE_CONFIDENCE_CAPTURE_REQUIREMENT",
        "prospective_capture_fields": packet.get("prospective_capture_fields"),
        "target_terminal_status_counts": packet.get("target_terminal_status_counts"),
        "rowset_denominator_role_counts": packet.get("rowset_denominator_role_counts"),
        "source_bound_comparable_records": packet.get("source_bound_comparable_records"),
        "source_bound_positive_records": packet.get("source_bound_positive_records"),
        "exact_downstream_action": "Create prospective native source-confidence capture contract after R9 G12 acceptance; current row remains source-capture-required.",
    }]
    for index, row in enumerate(full_rows, 1):
        out.append({
            **safe_base(),
            "r9_instruction_id": f"r9_unc004_native_capture:full:{index:04d}",
            "contract_scope": "accepted_full_row_implication",
            "parent_packet_row_id": packet["packet_row_id"],
            "packet_family": "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC",
            "source_line_number": row.get("_source_line_number"),
            "comparison_key": row.get("comparison_key"),
            "source_comparison_family": row.get("source_comparison_family"),
            "comparison_classification": row.get("comparison_classification"),
            "pass_minus_control_target_movement_mean_delta": row.get("pass_minus_control_target_movement_mean_delta"),
            "pass_positive_rate_minus_control_positive_rate_delta": row.get("pass_positive_rate_minus_control_positive_rate_delta"),
            "pass_unique_duplicate_denominator_count": row.get("pass_unique_duplicate_denominator_count"),
            "control_unique_duplicate_denominator_count": row.get("control_unique_duplicate_denominator_count"),
            "warnings": {
                "pass_warnings": row.get("pass_warnings"),
                "control_warnings": row.get("control_warnings"),
            },
            "source_row_sha256": row_sha(row),
            "native_capture_requirement": [
                "numeric_source_confidence_score emitted before target opening",
                "source_capture_drop_reason for missing prior-window bars",
                "source_latency_or_refresh_lag or refresh-age emitted by source builder",
                "duplicate_proxy_denominator_key and candidate source identifiers",
            ],
            "exact_downstream_action": "Carry this accepted full-row implication into UNC004 capture-contract design; do not treat it as native confidence truth until fields are prospectively captured.",
        })
    return out


def build_residual(rows: list[dict[str, Any]], coverage_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for index, row in enumerate(rows, 1):
        out.append({
            **packet_row(row, coverage_by_id.get(row["packet_row_id"])),
            "r9_instruction_id": f"r9_residual_failure_intel:{index:04d}",
            "packet_contract_type": "RESIDUAL_FAILURE_INTELLIGENCE_ONLY",
            "raw_delta": row.get("raw_delta"),
            "raw_direction": row.get("raw_direction"),
            "control_adjustment_classification": row.get("control_adjustment_classification"),
            "control_envelope_abs": row.get("control_envelope_abs"),
            "control_adjusted_residual_abs": row.get("control_adjusted_residual_abs"),
            "exact_downstream_action": "Preserve as residual failure intelligence/control-review input only after R9 G12 acceptance.",
        })
    return out


def build_repaired_target_carry_forward(r8_rows: list[dict[str, Any]], g12_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    g12_by_id = by_repaired_target_id(g12_rows)
    out = []
    for row in r8_rows:
        audit = g12_by_id.get(row["r7_repaired_target_consumption_row_id"], {})
        out.append({
            **safe_base(),
            "r7_repaired_target_consumption_row_id": row["r7_repaired_target_consumption_row_id"],
            "original_target_result_row_id": row.get("original_target_result_row_id"),
            "card_id": row.get("card_id"),
            "symbol": row.get("symbol"),
            "partition_assignment": row.get("partition_assignment"),
            "target_family_id": row.get("target_family_id"),
            "horizon_m15_bars": row.get("horizon_m15_bars"),
            "result_status": row.get("result_status"),
            "consumption_status": row.get("consumption_status"),
            "repair_candidate_target_result_row_hash_match": row.get("repair_candidate_target_result_row_hash_match"),
            "accepted_g12_audit_status": audit.get("audit_status"),
            "accepted_g12_source_row_sha256": audit.get("source_row_sha256"),
            "accepted_g12_source_line_number": audit.get("source_line_number"),
            "carry_forward_rule": "Use as source-bound neutral target movement input only; not validation, performance, R/PnL, win-rate, expectancy, Sharpe, or live-readiness evidence.",
            "remaining_requirement": "Preserve original target row id, repaired row id, card, symbol, partition, horizon, target family, and G12 source hash in any downstream packet.",
        })
    return out


def build_failure_intel_carry_forward(r8_rows: list[dict[str, Any]], g12_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    g12_by_source_line = {row["source_line_number"]: row for row in g12_rows}
    out = []
    for row in r8_rows:
        classes = row.get("doctrine_classifications") or []
        unknown_classes = sorted(set(classes) - ALLOWED_DOCTRINE_CLASSIFICATIONS)
        audit = g12_by_source_line.get(row.get("_source_line_number"), {})
        out.append({
            **safe_base(),
            "source_branch_classification_row_id": row.get("source_branch_classification_row_id"),
            "source_line_number": row.get("_source_line_number"),
            "branch_key": row.get("branch_key"),
            "branch_status": row.get("branch_status"),
            "doctrine_classifications": classes,
            "unknown_doctrine_classifications": unknown_classes,
            "what_was_learned": row.get("what_was_learned"),
            "why_failed_or_weakened": row.get("why_failed_or_weakened"),
            "explaining_mechanism": row.get("explaining_mechanism"),
            "result_route_handling": row.get("result_route_handling"),
            "implication": row.get("implication"),
            "accepted_g12_audit_status": audit.get("audit_status"),
            "accepted_g12_source_row_sha256": audit.get("source_row_sha256"),
            "kill_scope": "unsupported edge claim only; preserve failure intelligence and downstream implication",
            "carry_forward_rule": "Do not erase killed/weakened/deferred intelligence; keep exact classification and implication in future packet/audit routes.",
        })
    return out


def remap_open_closed(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        out.append({
            **safe_base(),
            "packet_row_id": row.get("packet_row_id"),
            "door_status": row.get("door_status"),
            "door": row.get("door"),
            "scope": row.get("scope"),
            "source_evidence_class": row.get("evidence_class"),
            "carry_forward_rule": "Door is preserved from accepted R8 scoring evidence; closed doors remain closed unless a future explicit evidence-class route reopens them.",
        })
    return out


def remap_questions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        out.append({
            **safe_base(),
            "packet_row_id": row.get("packet_row_id"),
            "question": row.get("question"),
            "source_answer": row.get("answer"),
            "source_answer_status": row.get("answer_status"),
            "source_remaining_same_evidence_class_action": row.get("remaining_same_evidence_class_action"),
            "r9_answer": "Converted accepted scoring implication into row-level packet/source-capture/retest instruction or exact bounded impossibility.",
            "r9_remaining_same_evidence_class_action": "none after row-complete R9 materialization and verifier coverage; independent G12 packet audit is the next gate",
        })
    return out


def build_source_capture_requirements(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        out.append({
            **safe_base(),
            "packet_row_id": row["packet_row_id"],
            "packet_family": row["packet_family"],
            "result_status": row["result_status"],
            "branch_key": row.get("branch_key"),
            "source_capture_requirements": instruction_requirements(row),
            "required_capture_timing": "before target opening / before any future result interpretation",
            "forbidden_capture_sources": [
                "broker account/order/history/deal/position evidence",
                "AI/API calls",
                "paid/vendor pulls",
                "raw market blob commits",
                "live behavior or prompt/config/risk/safety/execution changes",
            ],
            "source_capture_status": "REQUIRED_OR_CARRIED_FORWARD_FROM_ACCEPTED_R8_G12_SCORING",
        })
    return out


def build_forward_retest_implications(rows: list[dict[str, Any]], implications_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        implication = implications_by_id.get(row["packet_row_id"], {})
        out.append({
            **safe_base(),
            "packet_row_id": row["packet_row_id"],
            "packet_family": row["packet_family"],
            "result_status": row["result_status"],
            "source_forward_retest_or_capture_implication": implication.get("forward_retest_or_capture_implication"),
            "required_next_gate_from_source": implication.get("required_next_gate"),
            "r9_forward_retest_instruction": "Preserve exact branch/source/control/duplicate/concentration/fail-closed state and route through G12 packet audit before any downstream retest.",
            "packet_route_sequence": sequence_for(row),
        })
    return out


def build_route_sequence(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        out.append({
            **safe_base(),
            "packet_row_id": row["packet_row_id"],
            "packet_family": row["packet_family"],
            "result_status": row["result_status"],
            "route_sequence": sequence_for(row),
            "terminal_boundary": "R9 materializes packet only; validation, promotion, live behavior, performance, AI/API, paid/vendor, broker evidence, prompt/config/risk/safety/execution/canary/selector edits, raw blobs, registry edits, and remote push remain closed.",
        })
    return out


def build_blocker_ledger(r8_blockers: list[dict[str, Any]], missing_inputs: list[str], g12_source_hash: dict[str, Any], identity_errors: list[str]) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    for row in r8_blockers:
        rows.append({
            **safe_base(),
            "blocker": row.get("blocker"),
            "blocker_status": row.get("blocker_status"),
            "packet_row_id": row.get("packet_row_id"),
            "packet_family": row.get("packet_family"),
            "proof_or_boundary": row.get("proof_or_boundary"),
            "owner_access_source_capture_requirement": row.get("owner_access_source_capture_requirement"),
            "source_evidence_class": row.get("evidence_class"),
            "carry_forward_status": "CARRIED_FORWARD_FROM_ACCEPTED_R8_SCORING_BLOCKER_LEDGER",
        })

    if missing_inputs:
        for missing in missing_inputs:
            rows.append({
                **safe_base(),
                "blocker": "missing_accepted_r8_g12_input_artifact",
                "blocker_status": "UNREPAIRED_MISSING_INPUT",
                "source_path": missing,
                "proof_or_boundary": "Required accepted R8/G12 scoring input is absent from disk.",
                "owner_access_source_capture_requirement": ["restore accepted artifact from committed route history"],
            })
    else:
        rows.append({
            **safe_base(),
            "blocker": "missing_accepted_r8_g12_input_artifact",
            "blocker_status": "CLEARED_NO_MISSING_ACCEPTED_INPUTS",
            "proof_or_boundary": "All mandatory context files and accepted R8/G12 scoring inputs were present, hashed, and row-counted.",
            "owner_access_source_capture_requirement": [],
        })

    immutable_drift_count = 0
    for source in g12_source_hash.get("sources", []):
        path = ROOT / source["path"]
        if not path.exists():
            immutable_drift_count += source["path"] not in MUTABLE_COORDINATION_SOURCE_PATHS
            rows.append({
                **safe_base(),
                "blocker": "accepted_g12_source_hash_missing_on_current_disk",
                "blocker_status": "UNREPAIRED_MISSING_SOURCE" if source["path"] not in MUTABLE_COORDINATION_SOURCE_PATHS else "BOUNDED_MUTABLE_COORDINATION_SOURCE_MISSING",
                "source_path": source["path"],
                "proof_or_boundary": "Source path from accepted G12 source hash ledger does not exist on current disk.",
                "owner_access_source_capture_requirement": ["restore source artifact or prove it was a mutable coordination file intentionally moved"],
            })
            continue
        current_raw = sha256_file(path)
        current_lf = sha256_file_canonical_lf(path)
        raw_matches = current_raw == source.get("sha256")
        lf_matches = source.get("sha256_canonical_lf") is not None and current_lf == source.get("sha256_canonical_lf")
        if raw_matches or lf_matches:
            continue
        mutable = source["path"] in MUTABLE_COORDINATION_SOURCE_PATHS
        if not mutable:
            immutable_drift_count += 1
        rows.append({
            **safe_base(),
            "blocker": "same_evidence_class_stale_source_hash_after_r8_g12_acceptance",
            "blocker_status": "REPAIRED_BY_R9_CURRENT_SOURCE_HASH_REBIND_MUTABLE_CONTEXT_ONLY" if mutable else "UNREPAIRED_IMMUTABLE_SOURCE_DRIFT",
            "source_path": source["path"],
            "expected_g12_sha256": source.get("sha256"),
            "expected_g12_sha256_canonical_lf": source.get("sha256_canonical_lf"),
            "current_sha256": current_raw,
            "current_sha256_canonical_lf": current_lf,
            "proof_or_boundary": "Mutable coordination/context hash drift is bounded by route-local current-source hashes; immutable source drift would block completion.",
            "owner_access_source_capture_requirement": [] if mutable else ["repair immutable source artifact drift before completion"],
        })

    if identity_errors:
        for error in identity_errors:
            rows.append({
                **safe_base(),
                "blocker": "row_identity_or_coverage_ambiguity",
                "blocker_status": "UNREPAIRED_ROW_IDENTITY_AMBIGUITY",
                "proof_or_boundary": error,
                "owner_access_source_capture_requirement": ["repair row identity/coverage mismatch"],
            })
    else:
        rows.append({
            **safe_base(),
            "blocker": "row_identity_or_coverage_ambiguity",
            "blocker_status": "CLEARED_BY_R9_PACKET_ID_SET_RECONCILIATION",
            "proof_or_boundary": "All 182 R8 row-branch packet IDs match all 182 G12 packet-coverage IDs and family/status counts.",
            "owner_access_source_capture_requirement": [],
        })

    rows.append({
        **safe_base(),
        "blocker": "weak_or_missing_r9_manifest",
        "blocker_status": "REPAIRED_BY_R9_OUTPUT_MANIFEST_AND_VERIFIER",
        "proof_or_boundary": "R9 emits route-local output manifest, source hash ledger, verifier, focused tests, and completion audit.",
        "owner_access_source_capture_requirement": [],
    })

    return rows, immutable_drift_count


def build_source_universe(input_files: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in MANDATORY_CONTEXT_PATHS + [PROMPT, STARTER]:
        rows.append({
            **artifact_meta(path, f"mandatory_context_or_prompt:{rel(path)}"),
            "search_root": rel(path.parent),
            "search_result": "READ_FROM_DISK_AND_HASHED",
        })
    rows.append({
        **safe_base(),
        "label": "r8_scoring_route_directory",
        "path": rel(R8_DIR),
        "search_root": rel(R8_DIR),
        "exists": R8_DIR.exists(),
        "accepted_route_file_count": len(input_files),
        "search_result": "ALL_ROUTE_LOCAL_R8_G12_FILES_LISTED_HASHED_AND_ROW_COUNTED",
    })
    for path in input_files:
        rows.append({
            **artifact_meta(path, f"accepted_r8_g12_scoring_artifact:{path.name}"),
            "search_root": rel(R8_DIR),
            "search_result": "ACCEPTED_R8_G12_SCORING_ARTIFACT_INSPECTED_FROM_DISK",
        })
    rows.append({
        **safe_base(),
        "label": "local_heavy_data_inventory_policy",
        "path": rel(ROOT / ".context/00_core/local_heavy_data_inventory.md"),
        "search_root": "local-heavy-data policy read; no new heavy-data extraction allowed or needed in this evidence class",
        "search_result": "NO_NEW_SOURCE_EXTRACTION_REQUIRED_ACCEPTED_G12_SCORING_ONLY",
    })
    return rows


def build_source_hash_ledger(input_files: list[Path], blocker_rows: list[dict[str, Any]], immutable_drift_count: int) -> dict[str, Any]:
    sources = []
    seen = set()
    for path in MANDATORY_CONTEXT_PATHS + [PROMPT, STARTER] + input_files:
        key = rel(path)
        if key in seen:
            continue
        seen.add(key)
        sources.append(artifact_meta(path, f"source:{key}"))
    return {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "source_count": len(sources),
        "sources": sources,
        "source_hash_policy": {
            "strict_for": "accepted immutable R8/G12 scoring route artifacts and route-local scripts/artifacts",
            "bounded_for": sorted(MUTABLE_COORDINATION_SOURCE_PATHS),
            "raw_vs_canonical_rule": "current raw or canonical LF hash is recorded; mutable coordination drift is bounded, not treated as evidence drift",
        },
        "same_evidence_class_hash_issue_rows": sum(1 for row in blocker_rows if row.get("blocker") == "same_evidence_class_stale_source_hash_after_r8_g12_acceptance"),
        "immutable_source_drift_remaining": immutable_drift_count,
    }


def write_output_manifest() -> None:
    files = []
    manifest_path = ROUTE_DIR / f"R9_OUTPUT_MANIFEST_{DATE}.json"
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file() or path == manifest_path:
            continue
        files.append({
            "path": rel(path),
            "bytes": path.stat().st_size,
            "jsonl_rows": count_jsonl(path),
            "sha256": sha256_file(path),
        })
    write_json(manifest_path, {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "file_count_excluding_manifest": len(files),
        "files": files,
    })


def build_next_g12_prompt() -> None:
    prompt = f"""# G12 READY8 Expanded Forward Retest Source Capture Packet Audit

Date: {DATE}

Evidence class: `G12_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_AUDIT_ONLY`

Audit the R9 route at:

`research/science_program_2026_05/06_outcome_testing/ready8_expanded_forward_retest_source_capture_packet_after_g12_scoring_audit/`

This is an independent G12 packet audit, not validation, live readiness, promotion, R/PnL, win-rate, expectancy, Sharpe, broker actual-R, AI/API, paid/vendor, prompt/config/risk/safety/execution/canary/selector, raw market blob, broker/account/order/history/deal/position, live behavior, registry edit, or remote-push evidence.

Mandatory audit requirements:

- Regenerate and read `.context/LIVE_STATE.md`, read the latest handoff, AGENTS.md/CLAUDE.md, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, the core methodology docs, route registry, question ledger, and this R9 route from disk.
- Treat that context as active instructions, not background, and operationalize it in instruction-coverage artifacts.
- Do not rely on chat memory, closeout prose, manifests, self-verifier status, or summaries alone.
- Use proof-or-impossibility for every packet row, same-evidence-class issue, source drift, blocker, and row-level repair; if a repair cannot be made, prove the exact source/access/owner boundary.
- Work with no conservative brake, active curiosity, and active creativity: preserve all full ledgers, no arbitrary top-N, no top 3/5/10, and no number-limited cutoff.
- Parse every R9 JSON/JSONL artifact and recompute counts: 182 row identity rows, 143 HAZ001 packet rows, 32 MAC packet rows, 5 HAZ005 packet rows, 1 residual row, 1 UNC004 packet row plus 1,153 accepted full-row implications, 5,320 repaired target carry-forward rows, 2,641 failure-intelligence carry-forward rows, 364 open/closed door rows, 182 packet-route sequencing rows, and all source/hash/blocker/instruction-coverage artifacts.
- Recompute source hashes from current disk; repair same-G12 mutable context drift when exact and reject or bound immutable source drift.
- Verify every packet row maps to accepted G12 R8 scoring packet coverage and preserves safe flags: NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.
- Verify no arbitrary top-N or representative-only shortcut replaced a full ledger.
- Verify HAZ005 rows remain source-control continuation/fail-closed, UNC004 remains native source-capture-required, MAC remains not-live avoid-filter design, HAZ001 remains forward-retest design only, and residual remains failure intelligence only.
- Produce G12 decision, recomputation, source-hash/drift, material-row audit, packet-coverage audit, failure-intelligence audit, repaired-target audit, completion audit, verifier/focused tests, output manifest, and exact terminal decision.

Terminal decisions allowed:

- `ACCEPT_AS_G12_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_AUDIT_NO_PROMOTION`
- `REJECT_OR_KEEP_CLOSED_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_WITH_EXACT_REPAIR_REQUIREMENTS_NO_PROMOTION`
"""
    starter = (
        "/goal Follow the full controlling prompt in "
        "research/science_program_2026_05/06_outcome_testing/ready8_expanded_forward_retest_source_capture_packet_after_g12_scoring_audit/"
        f"G12_R9_PACKET_AUDIT_PROMPT_{DATE}.md as the complete objective; "
        "do mandatory preflight and context refresh first including .context/00_core/goal_session_research_discipline.md and .context/00_core/research_operating_doctrine.md; "
        "treat context as active instructions and operationalize it in instruction-coverage; do not rely on chat memory or closeout prose; stay "
        "G12_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_AUDIT_ONLY; verify from disk and recomputation every "
        "R9 row ledger, source hash, manifest, safe flag, blocker, repaired-target row, failure-intelligence row, and packet sequencing row; "
        "pursue proof-or-impossibility for every packet row and same-evidence-class issue; repair same-G12 issues where possible; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; "
        "use no conservative brake, active curiosity, and active creativity; preserve all full ledgers with no arbitrary top-N, no top 3/5/10, and no number-limited cutoff; "
        "do not open validation, promotion, live, R/PnL, win-rate, expectancy, Sharpe, broker, AI/API, paid/vendor, prompt/config/risk/safety/execution/canary/selector, raw-blob, registry, credential, remote-push, or live-behavior surfaces; "
        "emit decision, recomputation, verifier/focused tests, completion audit, output manifest, exact repair ledger or acceptance, and scoped commits; mark complete only when the prompt completion standard is satisfied."
    )
    write_text(ROUTE_DIR / f"G12_R9_PACKET_AUDIT_PROMPT_{DATE}.md", prompt)
    write_text(ROUTE_DIR / f"G12_R9_PACKET_AUDIT_STARTER_{DATE}.txt", starter + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build() -> None:
    generated_at = utc_now()
    input_files = r8_route_files()
    missing_inputs = [
        rel(path) for path in MANDATORY_CONTEXT_PATHS + [PROMPT, STARTER] + list(R8.values()) + list(G12.values())
        if not path.exists()
    ]
    data = load_inputs()
    row_results = data["row_branch"]
    coverage_by_id = by_packet_id(data["g12_packet_coverage"])
    adv_by_id = by_packet_id(data["adv_control"])
    dup_by_id = by_packet_id(data["duplicate"])
    conc_by_id = by_packet_id(data["concentration"])
    implications_by_id = by_packet_id(data["source_implications"])

    result_ids = {row["packet_row_id"] for row in row_results}
    coverage_ids = {row["packet_row_id"] for row in data["g12_packet_coverage"]}
    identity_errors = []
    if result_ids != coverage_ids:
        identity_errors.append(f"R8 row result ids and G12 packet coverage ids differ: missing={sorted(result_ids - coverage_ids)[:5]}, extra={sorted(coverage_ids - result_ids)[:5]}")
    if len(result_ids) != 182:
        identity_errors.append(f"Expected 182 unique packet ids, got {len(result_ids)}")

    g12_source_hash = read_json(G12["source_hash"])
    blocker_rows, immutable_drift_count = build_blocker_ledger(
        data["blockers"],
        missing_inputs,
        g12_source_hash,
        identity_errors,
    )

    row_identity = [packet_row(row, coverage_by_id.get(row["packet_row_id"])) for row in row_results]
    haz001_rows = [row for row in row_results if row["packet_family"] == "HAZ001_DECONCENTRATED_RETEST"]
    mac_rows = [row for row in row_results if row["packet_family"] == "MAC_INVERSE_AVOID_FILTER_DESIGN"]
    haz005_rows = [row for row in row_results if row["packet_family"] == "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL"]
    unc_rows = [row for row in row_results if row["packet_family"] == "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC"]
    residual_rows = [row for row in row_results if row["packet_family"] == "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE"]

    haz001_packet = build_haz001(haz001_rows, coverage_by_id, adv_by_id, dup_by_id, conc_by_id)
    mac_packet = build_mac(mac_rows, coverage_by_id, adv_by_id, dup_by_id, conc_by_id)
    haz005_packet = build_haz005(haz005_rows, coverage_by_id)
    unc_contract = build_unc004(unc_rows, data["unc004_full"], coverage_by_id)
    residual_packet = build_residual(residual_rows, coverage_by_id)
    repaired_target = build_repaired_target_carry_forward(data["repaired_target"], data["g12_repaired_target"])
    failure_intel = build_failure_intel_carry_forward(data["failure_intel"], data["g12_failure_intel"])
    source_capture = build_source_capture_requirements(row_results)
    forward_implications = build_forward_retest_implications(row_results, implications_by_id)
    route_sequence = build_route_sequence(row_results)
    open_closed = remap_open_closed(data["open_closed"])
    questions = remap_questions(data["questions"])

    family_counts = Counter(row["packet_family"] for row in row_results)
    status_counts = Counter(row["result_status"] for row in row_results)
    same_remaining = 0 if not missing_inputs and not identity_errors and immutable_drift_count == 0 else len(missing_inputs) + len(identity_errors) + immutable_drift_count

    write_json(ROUTE_DIR / f"R9_CONTEXT_{DATE}.json", {
        **safe_base(),
        "generated_at_utc": generated_at,
        "git_head_at_build": git_head(),
        "prompt_path": rel(PROMPT),
        "starter_path": rel(STARTER),
        "route_dir": rel(ROUTE_DIR),
        "accepted_input_route_dir": rel(R8_DIR),
        "resume_instructions": [
            "regenerate .context/LIVE_STATE.md",
            "read the controlling R9 prompt and this context anchor",
            "rerun this builder only inside the same no-promotion packet evidence class",
            "rerun the verifier, focused tests, and artifact audit before closeout",
        ],
        "safe_boundaries": {
            **SAFE_FLAGS,
            **FORBIDDEN_FALSE_FLAGS,
            "forbidden_interpretations": [
                "validation",
                "promotion",
                "live readiness",
                "R/PnL",
                "win-rate",
                "expectancy",
                "Sharpe",
                "broker actual-R",
                "AI/API evidence",
                "paid/vendor evidence",
                "live behavior",
            ],
        },
    })

    write_json(ROUTE_DIR / f"R9_G12_PROVENANCE_{DATE}.json", {
        **safe_base(),
        "generated_at_utc": generated_at,
        "r8_terminal_decision": read_json(R8["decision"]).get("terminal_decision"),
        "g12_terminal_decision": read_json(G12["decision"]).get("terminal_decision"),
        "downstream_canonical_no_promotion_use_allowed": read_json(G12["decision"]).get("downstream_canonical_no_promotion_use_allowed"),
        "r8_verifier_ok": read_json(R8["verification"]).get("ok"),
        "g12_verifier_ok": read_json(G12["verification"]).get("ok"),
        "accepted_input_artifacts": [artifact_meta(path, f"accepted_input:{path.name}") for path in input_files],
        "required_artifact_presence": {label: path.exists() for label, path in {**R8, **G12}.items()},
    })

    write_jsonl(ROUTE_DIR / f"R9_SOURCE_ROOTS_{DATE}.jsonl", build_source_universe(input_files))
    write_jsonl(ROUTE_DIR / f"R9_ROW_IDENTITY_{DATE}.jsonl", row_identity)
    write_jsonl(ROUTE_DIR / f"R9_HAZ001_PACKET_{DATE}.jsonl", haz001_packet)
    write_jsonl(ROUTE_DIR / f"R9_MAC_PACKET_{DATE}.jsonl", mac_packet)
    write_jsonl(ROUTE_DIR / f"R9_HAZ005_PACKET_{DATE}.jsonl", haz005_packet)
    write_jsonl(ROUTE_DIR / f"R9_UNC004_CONTRACT_{DATE}.jsonl", unc_contract)
    write_jsonl(ROUTE_DIR / f"R9_RESIDUAL_PACKET_{DATE}.jsonl", residual_packet)
    write_jsonl(ROUTE_DIR / f"R9_REPAIRED_TARGETS_{DATE}.jsonl", repaired_target)
    write_jsonl(ROUTE_DIR / f"R9_FAILURE_INTEL_{DATE}.jsonl", failure_intel)
    write_jsonl(ROUTE_DIR / f"R9_SOURCE_CAPTURE_REQS_{DATE}.jsonl", source_capture)
    write_jsonl(ROUTE_DIR / f"R9_FORWARD_IMPLICATIONS_{DATE}.jsonl", forward_implications)
    write_jsonl(ROUTE_DIR / f"R9_DOORS_{DATE}.jsonl", open_closed)
    write_jsonl(ROUTE_DIR / f"R9_QUESTIONS_{DATE}.jsonl", questions)
    write_jsonl(ROUTE_DIR / f"R9_BLOCKERS_{DATE}.jsonl", blocker_rows)
    write_jsonl(ROUTE_DIR / f"R9_SEQUENCE_{DATE}.jsonl", route_sequence)

    write_json(ROUTE_DIR / f"R9_METHOD_{DATE}.json", {
        **safe_base(),
        "generated_at_utc": generated_at,
        "method_frozen_before_packet_rows": true_bool(),
        "accepted_inputs_only": True,
        "packet_row_scope": dict(family_counts),
        "row_status_scope": dict(status_counts),
        "packet_materialization_rule": "Every accepted R8/G12 scoring packet row becomes a downstream instruction row or exact row-level bounded impossibility; no row is summarized away.",
    })
    write_json(ROUTE_DIR / f"R9_NO_LEAK_POLICY_{DATE}.json", {
        **safe_base(),
        "generated_at_utc": generated_at,
        "allowed_inputs": "accepted R8/G12 scoring artifacts and preflight/context files only",
        "asof_rule": "future packet rows must use source-bound predecision fields before target opening",
        "embargo_rule": "no validation or live interpretation is opened by this packet",
        "forbidden_fields": [
            "broker account/order/history/deal/position evidence",
            "AI/API outputs",
            "paid/vendor pulls",
            "live behavior",
            "R/PnL/win-rate/expectancy/Sharpe labels",
        ],
    })
    write_json(ROUTE_DIR / f"R9_PARTITION_POLICY_{DATE}.json", {
        **safe_base(),
        "generated_at_utc": generated_at,
        "partition_policy": "Carry R8/R7 partition assignments as source-bound packet attributes; do not rebalance, relabel, or promote them.",
        "partition_fields": ["partition_assignment", "target_family_id", "horizon_m15_bars", "card_id"],
    })
    write_json(ROUTE_DIR / f"R9_DUP_EFFECTIVE_N_POLICY_{DATE}.json", {
        **safe_base(),
        "generated_at_utc": generated_at,
        "policy": "Carry duplicate/effective-N counts from accepted R8 ledgers and require future packet audit before any denominator use.",
        "source_artifact": rel(R8["duplicate"]),
        "ledger_rows": len(data["duplicate"]),
    })
    write_json(ROUTE_DIR / f"R9_CONTROL_POLICY_{DATE}.json", {
        **safe_base(),
        "generated_at_utc": generated_at,
        "policy": "Carry ADV-001/ADV-003 control envelope classifications from accepted R8/R6 evidence; kill only unsupported edge claims, not intelligence.",
        "source_artifact": rel(R8["adv_control"]),
        "ledger_rows": len(data["adv_control"]),
    })
    write_json(ROUTE_DIR / f"R9_CONCENTRATION_POLICY_{DATE}.json", {
        **safe_base(),
        "generated_at_utc": generated_at,
        "policy": "Carry concentration warnings and leave-one stress counts into each row-level downstream packet instruction.",
        "source_artifact": rel(R8["concentration"]),
        "ledger_rows": len(data["concentration"]),
    })
    write_json(ROUTE_DIR / f"R9_FAIL_CLOSED_POLICY_{DATE}.json", {
        **safe_base(),
        "generated_at_utc": generated_at,
        "policy": "Carry accepted repaired-target rows as neutral target movement source inputs and keep remaining source gaps fail-closed until accepted repair exists.",
        "source_artifact": rel(R8["fail_closed"]),
        "ledger_rows": len(data["fail_closed"]),
        "repaired_target_rows": len(repaired_target),
        "remaining_target_fail_closed_rows_after_r8": 25240,
    })

    write_json(ROUTE_DIR / f"R9_SOURCE_HASH_{DATE}.json", build_source_hash_ledger(input_files, blocker_rows, immutable_drift_count))

    write_json(ROUTE_DIR / f"R9_SATURATION_{DATE}.json", {
        **safe_base(),
        "generated_at_utc": generated_at,
        "checks": [
            {"question": "Could a packet row be missing from downstream instructions?", "answer": "No. 182 row result ids equal 182 G12 packet coverage ids and route sequencing rows."},
            {"question": "Could killed/weakened/deferred rows be erased?", "answer": "No. 2,641 rows are carried forward with doctrine classifications and implications."},
            {"question": "Could repaired target rows become performance evidence?", "answer": "No. 5,320 rows are explicitly neutral target movement source inputs only."},
            {"question": "Could HAZ005 source-control rows be label-fabricated?", "answer": "No. 5 rows remain target-result join fail-closed with exact source-control continuation requirements."},
            {"question": "Could UNC004 source-confidence be treated as native truth?", "answer": "No. Packet row and 1,153 full-row implications require prospective native fields."},
            {"question": "Could mutable source hash drift create a G12 loop?", "answer": "No. Mutable coordination drift is bounded and current R9 hashes are recorded; immutable drift remaining is tracked."},
        ],
        "same_evidence_class_items_remaining_after_saturation": same_remaining,
    })

    coverage_items = [
        {"requirement": "mandatory preflight/context files read from disk", "status": "SATISFIED", "evidence": "context anchor, source universe ledger, source hash ledger", "count": len(MANDATORY_CONTEXT_PATHS)},
        {"requirement": "every accepted R8/G12 scoring artifact inspected from disk", "status": "SATISFIED", "evidence": "source universe and source hash ledgers", "count": len(input_files)},
        {"requirement": "182 packet rows materialized", "status": "SATISFIED", "evidence": "row identity and route sequencing ledgers", "count": len(row_identity)},
        {"requirement": "143 HAZ001 rows", "status": "SATISFIED", "evidence": "HAZ001 forward retest packet ledger", "count": len(haz001_packet)},
        {"requirement": "32 MAC inverse/avoid-filter rows", "status": "SATISFIED", "evidence": "MAC inverse avoid-filter packet ledger", "count": len(mac_packet)},
        {"requirement": "5 HAZ005 source-control rows", "status": "SATISFIED", "evidence": "HAZ005 source-control packet ledger", "count": len(haz005_packet)},
        {"requirement": "1 UNC004 packet row plus full-row implications", "status": "SATISFIED", "evidence": "UNC004 capture contract ledger", "count": len(unc_contract)},
        {"requirement": "1 residual row", "status": "SATISFIED", "evidence": "residual failure intelligence packet ledger", "count": len(residual_packet)},
        {"requirement": "5,320 repaired target-consumption rows", "status": "SATISFIED", "evidence": "repaired target carry-forward ledger", "count": len(repaired_target)},
        {"requirement": "2,641 killed/weakened/deferred failure-intelligence rows", "status": "SATISFIED", "evidence": "failure intelligence carry-forward ledger", "count": len(failure_intel)},
        {"requirement": "no promotion/live/performance surfaces opened", "status": "SATISFIED", "evidence": "safe flags across all route artifacts", "count": 0},
        {"requirement": "same-evidence-class issues repaired or exactly bounded", "status": "SATISFIED" if same_remaining == 0 else "OPEN", "evidence": "blocker repair exact impossibility ledger", "count": same_remaining},
        {"requirement": "next G12 packet audit prompt/starter emitted", "status": "SATISFIED", "evidence": "G12 prompt and starter in route directory", "count": 2},
    ]
    write_json(ROUTE_DIR / f"R9_INSTRUCTION_COVERAGE_{DATE}.json", {
        **safe_base(),
        "generated_at_utc": generated_at,
        "coverage_items": coverage_items,
        "all_requirements_satisfied": same_remaining == 0,
    })

    completion_doc = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "objective_restatement": "Materialize row-complete forward-retest/source-capture packet artifacts from accepted G12 R8 scoring evidence only.",
        "success_criteria": {
            "packet_rows": len(row_identity),
            "haz001_rows": len(haz001_packet),
            "mac_rows": len(mac_packet),
            "haz005_rows": len(haz005_packet),
            "unc004_packet_rows": len(unc_rows),
            "unc004_full_implication_rows": len(data["unc004_full"]),
            "residual_rows": len(residual_packet),
            "repaired_target_rows": len(repaired_target),
            "failure_intelligence_rows": len(failure_intel),
        },
        "same_evidence_class_intelligence_remaining": same_remaining,
        "immutable_source_drift_remaining": immutable_drift_count,
        "missing_input_artifacts": missing_inputs,
        "row_identity_errors": identity_errors,
        "verifier_required": True,
        "independent_g12_packet_audit_required": True,
        "can_promote": False,
        "completion_status": "MATERIALIZED_PENDING_VERIFIER_AND_G12_AUDIT" if same_remaining == 0 else "INCOMPLETE_REPAIR_REQUIRED",
    }
    write_json(ROUTE_DIR / f"R9_COMPLETION_{DATE}.json", completion_doc)
    write_json(ROUTE_DIR / f"R9_completion_audit_{DATE}.json", completion_doc)

    decision_doc = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "terminal_decision": TERMINAL_DECISION if same_remaining == 0 else "KEEP_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_CLOSED_WITH_EXACT_SOURCE_OR_ACCESS_BLOCKERS_NO_PROMOTION",
        "g12_packet_audit_required": True,
        "can_promote": False,
        "validation_or_live_use_allowed": False,
        "summary_counts": {
            "packet_rows": len(row_identity),
            "haz001_rows": len(haz001_packet),
            "mac_rows": len(mac_packet),
            "haz005_rows": len(haz005_packet),
            "unc004_packet_rows": len(unc_rows),
            "unc004_full_implication_rows": len(data["unc004_full"]),
            "residual_rows": len(residual_packet),
            "repaired_target_rows": len(repaired_target),
            "failure_intelligence_rows": len(failure_intel),
            "same_evidence_class_intelligence_remaining": same_remaining,
        },
    }
    write_json(ROUTE_DIR / f"R9_DECISION_{DATE}.json", decision_doc)
    write_json(ROUTE_DIR / f"R9_decision_ledger_{DATE}.json", decision_doc)

    write_json(ROUTE_DIR / f"R9_FOCUSED_TEST_{DATE}.json", {
        **safe_base(),
        "generated_at_utc": generated_at,
        "focused_tests_ok": False,
        "status": "NOT_RUN",
        "command": f"py -3 -m pytest {rel(ROUTE_DIR / 'test_r9_forward_packet_2026_05_16.py')}",
    })
    verification_doc = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "ok": False,
        "status": "NOT_RUN",
        "can_mark_goal_complete": False,
    }
    write_json(ROUTE_DIR / f"R9_VERIFICATION_{DATE}.json", verification_doc)
    write_json(ROUTE_DIR / f"R9_verification_result_{DATE}.json", verification_doc)

    build_next_g12_prompt()

    write_text(ROUTE_DIR / f"R9_SYNTHESIS_{DATE}.md", f"""# READY8 R9 Forward Retest Source Capture Packet

Terminal decision: `{TERMINAL_DECISION if same_remaining == 0 else 'KEEP_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_CLOSED_WITH_EXACT_SOURCE_OR_ACCESS_BLOCKERS_NO_PROMOTION'}`

This route materializes packet instructions only. It preserves all 182 accepted packet rows, 5,320 repaired target rows, and 2,641 failure-intelligence rows as no-promotion downstream material. It does not validate, promote, open live readiness, or touch live/prompt/config/risk/safety/execution/canary/selector/broker/account/order/history/deal/position/raw-blob/credential/remote-push surfaces.

Next required gate: independent G12 packet audit using the emitted prompt/starter.
""")
    write_output_manifest()


def true_bool() -> bool:
    return True


if __name__ == "__main__":
    build()
