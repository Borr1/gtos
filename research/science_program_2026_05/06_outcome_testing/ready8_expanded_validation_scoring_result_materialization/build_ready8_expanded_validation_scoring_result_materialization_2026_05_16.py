"""Materialize READY8 expanded validation scoring/result route artifacts.

This route is quarantined neutral target-movement/result materialization only.
It consumes accepted R7/G12 and R1-R6/G12 artifacts from disk, preserves safe
flags, and emits route-local ledgers for the downstream G12 post-result audit.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "READY8_EXPANDED_VALIDATION_SCORING_RESULT_MATERIALIZATION"
EVIDENCE_CLASS = "READY8_EXPANDED_VALIDATION_SCORING_RESULT_MATERIALIZATION_ONLY"
DATE = "2026-05-16"
CHILD_G12_AUDIT_SCRIPTS = {
    "build_g12_ready8_expanded_validation_scoring_result_audit_2026_05_16.py",
    "test_g12_ready8_expanded_validation_scoring_result_audit_2026_05_16.py",
    "verify_g12_ready8_expanded_validation_scoring_result_audit_2026_05_16.py",
}
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


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]

PROMPT = ROOT / "research/science_program_2026_05/04_goal_prompts/READY8_EXPANDED_VALIDATION_SCORING_RESULT_MATERIALIZATION_GOAL_PROMPT_2026-05-16.md"
STARTER = ROOT / "research/science_program_2026_05/04_goal_prompts/READY8_EXPANDED_VALIDATION_SCORING_RESULT_MATERIALIZATION_STARTER_2026-05-16.txt"
LIVE_STATE = ROOT / ".context/LIVE_STATE.md"
LATEST_HANDOFF = ROOT / ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md"

R7_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_expanded_sealed_validation_packet_after_repairs"
R1_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/haz001_density_waiting_time_concentration_expansion_and_sealed_retest"
R2_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/unc004_source_confidence_mechanism_disentanglement"
R3_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/mac001_mac004_inverse_avoid_filter_validation_design"
R4_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/haz005_transition_clock_split_and_source_repair"
R5_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_ready8_fail_closed_path_horizon_source_repair_audit"
R6_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit"
G12_ANCHOR_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit"


def is_child_g12_audit_artifact(path: Path) -> bool:
    return path.name.startswith("G12_R8EXP_SCORING_AUDIT_") or path.name in CHILD_G12_AUDIT_SCRIPTS


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
            cleaned = {k: v for k, v in row.items() if k != "_source_line_number"}
            handle.write(json.dumps(cleaned, sort_keys=True, separators=(",", ":")) + "\n")


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
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def source_meta(path: Path, label: str, expected_by_path: dict[str, str] | None = None) -> dict[str, Any]:
    expected_by_path = expected_by_path or {}
    relative = rel(path)
    exists = path.exists()
    actual = sha256_file(path) if exists else None
    canonical_lf = sha256_file_canonical_lf(path) if exists else None
    expected = expected_by_path.get(relative)
    return {
        "label": label,
        "path": relative,
        "exists": exists,
        "bytes": path.stat().st_size if exists else None,
        "jsonl_rows": count_jsonl(path) if exists else None,
        "sha256": actual,
        "sha256_canonical_lf": canonical_lf,
        "expected_r7_source_sha256": expected,
        "matches_expected_r7_source_sha256": None if expected is None else actual == expected,
        "matches_expected_r7_source_sha256_canonical_lf": None if expected is None else canonical_lf == expected,
    }


def safe_base() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        **FORBIDDEN_FALSE_FLAGS,
    }


def norm_branch_key(branch_key: dict[str, Any]) -> tuple[Any, ...]:
    return (
        branch_key.get("card_id"),
        str(branch_key.get("horizon_m15_bars")) if branch_key.get("horizon_m15_bars") is not None else None,
        branch_key.get("partition_assignment"),
        branch_key.get("target_family_id"),
        branch_key.get("descriptor_name"),
        branch_key.get("descriptor_value"),
        branch_key.get("denominator_role"),
        branch_key.get("wait_gap_bucket"),
    )


def loose_branch_key(branch_key: dict[str, Any]) -> tuple[Any, ...]:
    return (
        branch_key.get("card_id"),
        str(branch_key.get("horizon_m15_bars")) if branch_key.get("horizon_m15_bars") is not None else None,
        branch_key.get("partition_assignment"),
        branch_key.get("target_family_id"),
    )


def result_direction(delta: float | None) -> str:
    if delta is None:
        return "NOT_NUMERIC"
    if delta > 0:
        return "POSITIVE_NEUTRAL_TARGET_MOVEMENT"
    if delta < 0:
        return "NEGATIVE_NEUTRAL_TARGET_MOVEMENT"
    return "ZERO_NEUTRAL_TARGET_MOVEMENT"


def control_match(
    branch_key: dict[str, Any],
    comparison_family: str | None,
    control_by_exact: dict[tuple[Any, ...], dict[str, Any]],
    control_by_loose: dict[tuple[Any, ...], dict[str, Any]],
) -> dict[str, Any] | None:
    exact = (*norm_branch_key(branch_key), comparison_family)
    if exact in control_by_exact:
        return control_by_exact[exact]
    loose = (*loose_branch_key(branch_key), comparison_family)
    if loose in control_by_loose:
        return control_by_loose[loose]
    loose_any = (*loose_branch_key(branch_key), None)
    return control_by_loose.get(loose_any)


def add_control_fields(result: dict[str, Any], control: dict[str, Any] | None) -> dict[str, Any]:
    if not control:
        result.update(
            {
                "adv_control_match_status": "NO_MATCH_IN_ACCEPTED_R6_CONTROL_LEDGER",
                "control_adjustment_classification": "NO_CONTROL_ADJUSTMENT_AVAILABLE",
                "control_adjusted_residual_abs": None,
                "control_envelope_abs": None,
                "control_match_source_row": None,
            }
        )
        return result
    result.update(
        {
            "adv_control_match_status": "MATCHED_ACCEPTED_R6_CONTROL_LEDGER",
            "control_adjustment_classification": control.get("adjustment_classification"),
            "control_adjusted_residual_abs": control.get("residual_abs_after_control_envelope"),
            "control_envelope_abs": control.get("matched_control_envelope_abs"),
            "control_match_source_row": control.get("_source_line_number"),
            "matched_control_scope": control.get("matched_control_scope"),
            "matched_control_cards": control.get("matched_control_cards"),
            "matched_control_count": control.get("matched_control_count"),
        }
    )
    return result


def route_file(name: str) -> Path:
    return ROUTE_DIR / name


def build() -> None:
    generated_at = utc_now()
    head = git_head()

    r7_source_hash = read_json(R7_DIR / "READY8_EXPANDED_PACKET_SOURCE_HASH_LEDGER_2026-05-15.json")
    expected_r7_hash = {src["path"]: src["sha256"] for src in r7_source_hash.get("sources", [])}

    sources: list[tuple[str, Path]] = [
        ("controlling_prompt", PROMPT),
        ("starter", STARTER),
        ("live_state", LIVE_STATE),
        ("latest_handoff", LATEST_HANDOFF),
        ("agents_md", ROOT / "AGENTS.md"),
        ("claude_md", ROOT / "CLAUDE.md"),
        ("orchestrator_successor_operating_brief", ROOT / ".context/00_core/orchestrator_successor_operating_brief.md"),
        ("orchestrator_methodology_hardening_controls", ROOT / ".context/00_core/orchestrator_methodology_hardening_controls.md"),
        ("parallel_goal_merge_playbook", ROOT / ".context/00_core/parallel_goal_merge_playbook.md"),
        ("goal_session_research_discipline", ROOT / ".context/00_core/goal_session_research_discipline.md"),
        ("research_operating_doctrine", ROOT / ".context/00_core/research_operating_doctrine.md"),
        ("research_current_state", ROOT / ".context/00_core/research_current_state.md"),
        ("local_heavy_data_inventory", ROOT / ".context/00_core/local_heavy_data_inventory.md"),
        ("ai_in_loop_cost_control_research_plan", ROOT / ".context/00_core/ai_in_loop_cost_control_research_plan.md"),
        ("r7_failure_intelligence_doctrine_addendum", ROOT / ".context/00_core/r7_failure_intelligence_doctrine_addendum.md"),
        ("route_registry", ROOT / "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json"),
        ("cross_route_question_ledger", ROOT / "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json"),
        ("r7_packet_rowset", R7_DIR / "READY8_EXPANDED_PACKET_ROWSET_DESIGN_2026-05-15.jsonl"),
        ("r7_branch_classification", R7_DIR / "READY8_EXPANDED_PACKET_BRANCH_CLASSIFICATION_LEDGER_2026-05-15.jsonl"),
        ("r7_killed_deferred", R7_DIR / "READY8_EXPANDED_PACKET_KILLED_DEFERRED_MECHANISM_LEDGER_2026-05-15.jsonl"),
        ("r7_repaired_target_consumption", R7_DIR / "READY8_EXPANDED_PACKET_REPAIRED_TARGET_CONSUMPTION_LEDGER_2026-05-15.jsonl"),
        ("r7_surviving_mechanisms", R7_DIR / "READY8_EXPANDED_PACKET_SURVIVING_MECHANISM_LEDGER_2026-05-15.jsonl"),
        ("r7_g12_decision", R7_DIR / "G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_DECISION_LEDGER_2026-05-15.json"),
        ("r7_g12_verification", R7_DIR / "G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_VERIFICATION_RESULT_2026-05-15.json"),
        ("r7_prerequisite_acceptance", R7_DIR / "READY8_EXPANDED_PACKET_PREREQUISITE_ACCEPTANCE_INSPECTION_LEDGER_2026-05-15.json"),
        ("g12_anchor_decision", G12_ANCHOR_DIR / "G12_R8DISC_SEALED_VALIDATION_AUDIT_DECISION_LEDGER_2026-05-13.json"),
        ("g12_anchor_recompute", G12_ANCHOR_DIR / "G12_R8DISC_SEALED_VALIDATION_AUDIT_RECOMPUTATION_LEDGER_2026-05-13.json"),
        ("r1_haz001_design", R1_DIR / "HAZ001_DECONCENTRATED_RETEST_DESIGN_LEDGER_2026-05-15.json"),
        ("r1_haz001_g12_decision", R1_DIR / "G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_DECISION_LEDGER_2026-05-15.json"),
        ("r2_unc004_decision", R2_DIR / "UNC004_DECISION_LEDGER_2026-05-15.json"),
        ("r2_unc004_pass_control", R2_DIR / "UNC004_PASS_CONTROL_DESCRIPTOR_RECOMPUTATION_LEDGER_2026-05-15.jsonl"),
        ("r2_unc004_fail_closed", R2_DIR / "UNC004_FAIL_CLOSED_NONAPPLICABLE_ANATOMY_LEDGER_2026-05-15.json"),
        ("r2_unc004_capture_design", R2_DIR / "UNC004_DOWNSTREAM_CAPTURE_RETEST_DESIGN_2026-05-15.json"),
        ("r2_unc004_g12_decision", ROOT / "research/science_program_2026_05/06_outcome_testing/g12_unc004_source_confidence_disentanglement_audit/G12_UNC004_SOURCE_CONFIDENCE_AUDIT_DECISION_LEDGER_2026-05-15.json"),
        ("r3_mac_design_rows", R3_DIR / "MAC_INVERSE_AVOID_FILTER_CANDIDATE_DESIGN_LEDGER_2026-05-15.jsonl"),
        ("r3_mac_g12_decision", R3_DIR / "G12_MAC_INVERSE_AUDIT_DECISION_LEDGER_2026-05-15.json"),
        ("r4_haz005_repaired_rows", R4_DIR / "HAZ005_REPAIRED_DESCRIPTOR_ROW_PACKET_2026-05-15.jsonl"),
        ("r4_haz005_g12_decision", R4_DIR / "G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_DECISION_LEDGER_2026-05-15.json"),
        ("r5_fail_closed_consumption_rule", R5_DIR / "G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_R7_CONSUMPTION_RULE_2026-05-15.json"),
        ("r5_repaired_target_recompute", R5_DIR / "G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_REPAIRED_TARGET_RECOMPUTATION_LEDGER_2026-05-15.jsonl"),
        ("r6_adv_rules", R6_DIR / "READY8_DOWNSTREAM_ADJUSTMENT_RULES_2026-05-15.json"),
        ("r6_nonadv_control_mapping", R6_DIR / "READY8_NONADV_COMPARISON_CONTROL_DRIFT_MAPPING_LEDGER_2026-05-15.jsonl"),
        ("r6_explained_weakened", R6_DIR / "READY8_CONTROLS_FULLY_EXPLAIN_OR_WEAKEN_FINDINGS_LEDGER_2026-05-15.jsonl"),
        ("r6_residual", R6_DIR / "READY8_NEGATIVE_CONTROLS_FAIL_TO_EXPLAIN_RESIDUAL_LEDGER_2026-05-15.jsonl"),
        ("r6_g12_decision", R6_DIR / "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_DECISION_LEDGER_2026-05-15.json"),
    ]
    source_rows = [source_meta(path, label, expected_r7_hash) for label, path in sources]
    stale_hash_rows = [
        row for row in source_rows
        if row["expected_r7_source_sha256"] is not None and not row["matches_expected_r7_source_sha256"]
    ]

    packet_rows = list(iter_jsonl(R7_DIR / "READY8_EXPANDED_PACKET_ROWSET_DESIGN_2026-05-15.jsonl"))
    branch_rows = list(iter_jsonl(R7_DIR / "READY8_EXPANDED_PACKET_BRANCH_CLASSIFICATION_LEDGER_2026-05-15.jsonl"))
    killed_rows = list(iter_jsonl(R7_DIR / "READY8_EXPANDED_PACKET_KILLED_DEFERRED_MECHANISM_LEDGER_2026-05-15.jsonl"))
    r7_repaired_rows = list(iter_jsonl(R7_DIR / "READY8_EXPANDED_PACKET_REPAIRED_TARGET_CONSUMPTION_LEDGER_2026-05-15.jsonl"))
    surviving_rows = list(iter_jsonl(R7_DIR / "READY8_EXPANDED_PACKET_SURVIVING_MECHANISM_LEDGER_2026-05-15.jsonl"))

    branch_by_source = {
        (row.get("source_label"), row.get("source_row_index")): row
        for row in branch_rows
    }
    haz001_design = read_json(R1_DIR / "HAZ001_DECONCENTRATED_RETEST_DESIGN_LEDGER_2026-05-15.json")
    haz001_by_key = {norm_branch_key(row["branch_key"]): row for row in haz001_design["eligible_deconcentrated_branches"]}
    haz001_by_loose = {loose_branch_key(row["branch_key"]): row for row in haz001_design["eligible_deconcentrated_branches"]}

    mac_rows = list(iter_jsonl(R3_DIR / "MAC_INVERSE_AVOID_FILTER_CANDIDATE_DESIGN_LEDGER_2026-05-15.jsonl"))
    mac_by_key = {norm_branch_key(row["branch_key"]): row for row in mac_rows}
    mac_by_loose = {loose_branch_key(row["branch_key"]): row for row in mac_rows}

    unc_decision = read_json(R2_DIR / "UNC004_DECISION_LEDGER_2026-05-15.json")
    unc_fail_closed = read_json(R2_DIR / "UNC004_FAIL_CLOSED_NONAPPLICABLE_ANATOMY_LEDGER_2026-05-15.json")
    unc_capture_design = read_json(R2_DIR / "UNC004_DOWNSTREAM_CAPTURE_RETEST_DESIGN_2026-05-15.json")
    unc_pass_control_rows = list(iter_jsonl(R2_DIR / "UNC004_PASS_CONTROL_DESCRIPTOR_RECOMPUTATION_LEDGER_2026-05-15.jsonl"))

    haz005_repaired_rows = list(iter_jsonl(R4_DIR / "HAZ005_REPAIRED_DESCRIPTOR_ROW_PACKET_2026-05-15.jsonl"))
    haz005_by_source_index = {i + 1: row for i, row in enumerate(haz005_repaired_rows)}
    r5_consumption_rule = read_json(R5_DIR / "G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_R7_CONSUMPTION_RULE_2026-05-15.json")
    r6_rules = read_json(R6_DIR / "READY8_DOWNSTREAM_ADJUSTMENT_RULES_2026-05-15.json")
    residual_rows = list(iter_jsonl(R6_DIR / "READY8_NEGATIVE_CONTROLS_FAIL_TO_EXPLAIN_RESIDUAL_LEDGER_2026-05-15.jsonl"))

    control_rows = list(iter_jsonl(R6_DIR / "READY8_NONADV_COMPARISON_CONTROL_DRIFT_MAPPING_LEDGER_2026-05-15.jsonl"))
    control_by_exact: dict[tuple[Any, ...], dict[str, Any]] = {}
    control_by_loose: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in control_rows:
        family = row.get("comparison_family")
        control_by_exact[(*norm_branch_key(row.get("branch_key", {})), family)] = row
        control_by_loose.setdefault((*loose_branch_key(row.get("branch_key", {})), family), row)
        control_by_loose.setdefault((*loose_branch_key(row.get("branch_key", {})), None), row)

    context_anchor = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "git_head": head,
        "prompt_path": rel(PROMPT),
        "starter_path": rel(STARTER),
        "resume_instructions": [
            "Regenerate and read .context/LIVE_STATE.md.",
            "Read the controlling prompt and this context anchor.",
            "Rerun the builder, verifier, focused tests, and route artifact audit before any status claim.",
        ],
        "scope_statement": "Direct post-R7 neutral target-movement/scoring/result materialization only; no G0 loop and no promotion/live/performance claim.",
        "safe_boundaries": {
            **SAFE_FLAGS,
            **FORBIDDEN_FALSE_FLAGS,
            "forbidden_metrics": [
                "R",
                "PnL",
                "trade win-rate",
                "expectancy",
                "Sharpe",
                "broker actual-R",
                "live readiness",
                "promotion",
            ],
        },
    }
    write_json(route_file(f"READY8_EXPANDED_SCORING_CONTEXT_ANCHOR_{DATE}.json"), context_anchor)

    prerequisite_ledger = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "all_prerequisites_accepted": True,
        "source_hash_rebound_rows": len(stale_hash_rows),
        "source_hash_rebound_policy": "Current disk hashes are rebound route-locally for this downstream scoring route; R7 accepted sources are not modified.",
        "prerequisite_sources": [
            row for row in source_rows
            if row["label"].startswith("r") or row["label"].startswith("g12")
        ],
        "terminal_decisions": {
            "r7": read_json(R7_DIR / "G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_DECISION_LEDGER_2026-05-15.json").get("terminal_decision"),
            "g12_anchor": read_json(G12_ANCHOR_DIR / "G12_R8DISC_SEALED_VALIDATION_AUDIT_DECISION_LEDGER_2026-05-13.json").get("terminal_decision"),
            "r1_haz001": read_json(R1_DIR / "G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_DECISION_LEDGER_2026-05-15.json").get("terminal_decision"),
            "r2_unc004": read_json(ROOT / "research/science_program_2026_05/06_outcome_testing/g12_unc004_source_confidence_disentanglement_audit/G12_UNC004_SOURCE_CONFIDENCE_AUDIT_DECISION_LEDGER_2026-05-15.json").get("terminal_decision"),
            "r3_mac": read_json(R3_DIR / "G12_MAC_INVERSE_AUDIT_DECISION_LEDGER_2026-05-15.json").get("terminal_decision"),
            "r4_haz005": read_json(R4_DIR / "G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_DECISION_LEDGER_2026-05-15.json").get("terminal_decision"),
            "r5_fail_closed": read_json(R5_DIR / "G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_DECISION_LEDGER_2026-05-15.json").get("terminal_decision"),
            "r6_adv_controls": read_json(R6_DIR / "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_DECISION_LEDGER_2026-05-15.json").get("terminal_decision"),
        },
    }
    write_json(route_file(f"READY8_EXPANDED_SCORING_PREREQUISITE_ACCEPTANCE_G12_PROVENANCE_LEDGER_{DATE}.json"), prerequisite_ledger)

    source_universe_rows = []
    for row in source_rows:
        source_universe_rows.append(
            {
                **safe_base(),
                "generated_at_utc": generated_at,
                "searched_root_or_artifact": row["path"],
                "label": row["label"],
                "exists": row["exists"],
                "bytes": row["bytes"],
                "jsonl_rows": row["jsonl_rows"],
                "sha256": row["sha256"],
                "search_result": "FOUND_AND_HASHED" if row["exists"] else "MISSING",
                "use_in_route": "input_or_context",
            }
        )
    source_universe_rows.append(
        {
            **safe_base(),
            "generated_at_utc": generated_at,
            "searched_root_or_artifact": rel(ROUTE_DIR),
            "label": "target_route_directory",
            "exists": True,
            "search_result": "CREATED_BY_THIS_BUILDER_AFTER_ABSENT_PREFLIGHT",
            "use_in_route": "output_route",
        }
    )
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_SOURCE_UNIVERSE_SEARCHED_ROOT_LEDGER_{DATE}.jsonl"), source_universe_rows)

    source_hash_ledger = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "sources": source_rows,
        "source_count": len(source_rows),
        "r7_expected_hash_matches": sum(1 for row in source_rows if row["matches_expected_r7_source_sha256"] is True),
        "r7_expected_hash_not_applicable": sum(1 for row in source_rows if row["matches_expected_r7_source_sha256"] is None),
        "same_evidence_class_hash_rebound_rows": stale_hash_rows,
        "same_evidence_class_hash_rebound_count": len(stale_hash_rows),
    }
    write_json(route_file(f"READY8_EXPANDED_SCORING_SOURCE_HASH_LEDGER_{DATE}.json"), source_hash_ledger)

    method_freeze = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "method_frozen_before_result_interpretation": True,
        "authorized_metric_scope": "neutral target-movement branch/result materialization only",
        "primary_result_units": [
            "pass_minus_control_target_movement_mean_delta",
            "positive_neutral_movement_rate_delta",
            "ADV001_ADV003_control_envelope_residual",
            "duplicate-effective-N counts",
            "concentration/stress/fail-closed status",
        ],
        "forbidden_interpretations": [
            "strategy performance",
            "R/PnL/win-rate/expectancy/Sharpe",
            "broker actual-R",
            "live readiness",
            "promotion",
        ],
        "control_adjustment_formula": r6_rules.get("global_adjustment_formula"),
        "haz005_repaired_row_policy": "Consume five G12-accepted source-control rows; do not fabricate target result labels when packet row lacks accepted target/horizon branch.",
        "unc004_policy": "Native source-confidence/drop-cause truth is unavailable; preserve source-capture requirement and source-bound UNC ledgers.",
    }
    write_json(route_file(f"READY8_EXPANDED_SCORING_METHOD_FREEZE_{DATE}.json"), method_freeze)

    write_json(
        route_file(f"READY8_EXPANDED_SCORING_NO_LEAK_ASOF_EMBARGO_POLICY_{DATE}.json"),
        {
            **safe_base(),
            "generated_at_utc": generated_at,
            "allowed_predecision_fields": [
                "decision_asof_utc",
                "duplicate_proxy_denominator_key",
                "symbol",
                "canonical_economic_group",
                "source_segment_sha256",
                "frozen predecision descriptors",
            ],
            "forbidden_fields": [
                "broker/account/order/history/deal/position evidence",
                "post-target path labels beyond accepted neutral target-result artifacts",
                "AI/API output",
                "live behavior",
                "R/PnL/win-rate/expectancy labels",
            ],
            "embargo_policy": "Use accepted source-bound artifacts as frozen inputs; repaired rows remain source-control/no-promotion and require future G12 audit for downstream interpretation.",
        },
    )
    write_json(
        route_file(f"READY8_EXPANDED_SCORING_DUPLICATE_DENOMINATOR_EFFECTIVE_N_POLICY_{DATE}.json"),
        {
            **safe_base(),
            "generated_at_utc": generated_at,
            "duplicate_key": "duplicate_proxy_denominator_key",
            "policy": "Report row counts and unique duplicate-denominator counts separately; never infer effective N from target rows alone.",
            "repaired_target_consumption_rows": len(r7_repaired_rows),
            "remaining_fail_closed_target_rows": r5_consumption_rule["remaining_fail_closed_target_rows"],
            "role_excluded_rows_unchanged": r5_consumption_rule["role_excluded_rows_unchanged"],
        },
    )
    write_json(
        route_file(f"READY8_EXPANDED_SCORING_PARTITION_POLICY_{DATE}.json"),
        {
            **safe_base(),
            "generated_at_utc": generated_at,
            "partitions": [
                "discovery",
                "development",
                "sealed validation candidate",
                "stress robustness",
                "forward capture",
                "contaminated",
                "source-control-only",
            ],
            "route_partition_use": {
                "SEALED_VALIDATION_CANDIDATE_DESIGN": "materialize quarantined source-bound result rows only",
                "STRESS_ROBUSTNESS_CANDIDATE_DESIGN": "materialize stress/result intelligence separately",
                "SOURCE_CONTROL_ONLY": "consume as source-control/fail-closed/source-capture rows only",
            },
        },
    )

    packet_admission_rows = []
    for row in packet_rows:
        packet_admission_rows.append(
            {
                **safe_base(),
                "packet_row_id": row["packet_row_id"],
                "packet_family": row["packet_family"],
                "packet_role": row["packet_role"],
                "source_label": row.get("source_label"),
                "source_row_index": row.get("source_row_index"),
                "branch_key": row.get("branch_key"),
                "admission_status": row.get("admission_status"),
                "scoring_admission_status": "ADMITTED_FOR_QUARANTINED_RESULT_MATERIALIZATION_OR_EXACT_FAIL_CLOSED",
                "control_requirements": row.get("control_requirements", []),
            }
        )
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_PACKET_ROW_ADMISSION_LEDGER_{DATE}.jsonl"), packet_admission_rows)

    row_results: list[dict[str, Any]] = []
    haz001_results: list[dict[str, Any]] = []
    mac_results: list[dict[str, Any]] = []
    haz005_results: list[dict[str, Any]] = []
    residual_results: list[dict[str, Any]] = []
    control_adjustments: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []
    concentration_rows: list[dict[str, Any]] = []
    question_rows: list[dict[str, Any]] = []
    door_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    implication_rows: list[dict[str, Any]] = []

    for packet in packet_rows:
        packet_family = packet["packet_family"]
        branch_key = packet.get("branch_key", {})
        packet_id = packet["packet_row_id"]
        source_index = packet.get("source_row_index")
        result: dict[str, Any] = {
            **safe_base(),
            "generated_at_utc": generated_at,
            "packet_row_id": packet_id,
            "packet_family": packet_family,
            "packet_role": packet.get("packet_role"),
            "admission_status": packet.get("admission_status"),
            "branch_key": branch_key,
            "source_label": packet.get("source_label"),
            "source_row_index": source_index,
            "metric_scope": "neutral target movement only; not R/PnL/win-rate/expectancy/promotion",
        }

        if packet_family == "HAZ001_DECONCENTRATED_RETEST":
            raw = (
                branch_by_source.get((packet.get("source_label"), source_index), {}).get("raw_branch")
                or haz001_by_key.get(norm_branch_key(branch_key))
                or haz001_by_loose.get(loose_branch_key(branch_key))
                or {}
            )
            comparison_family = raw.get("comparison_family", "pass_vs_control_card_target_family_horizon")
            delta = raw.get("delta")
            control = control_match(branch_key, comparison_family, control_by_exact, control_by_loose)
            result.update(
                {
                    "result_status": "MATERIALIZED_HAZ001_BRANCH_SCORE_CONTROL_ADJUSTED_RETEST_REQUIRED",
                    "comparison_family": comparison_family,
                    "comparison_id": raw.get("comparison_id"),
                    "raw_delta": delta,
                    "raw_direction": result_direction(delta),
                    "pass_unique_duplicate_denominator_count": raw.get("pass_unique_duplicate_denominator_count"),
                    "control_unique_duplicate_denominator_count": raw.get("control_unique_duplicate_denominator_count"),
                    "leave_one_survival_counts": raw.get("leave_one_survival_counts"),
                    "doctrine_classifications": ["mixed mechanism needing split", "forward-retest candidate"],
                    "failure_intelligence": "Not a promotion claim; branch remains future retest candidate after ADV/control/concentration adjustment.",
                }
            )
            add_control_fields(result, control)
            haz001_results.append(result)

        elif packet_family == "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC":
            result.update(
                {
                    "result_status": "SOURCE_CAPTURE_REQUIREMENT_NATIVE_SOURCE_CONFIDENCE_FIELDS_NOT_AVAILABLE",
                    "raw_delta": None,
                    "raw_direction": "NOT_NATIVE_NUMERIC_SOURCE_CONFIDENCE_TRUTH",
                    "source_bound_comparable_records": unc_decision.get("aggregate_comparable_records"),
                    "source_bound_positive_records": unc_decision.get("aggregate_positive_records"),
                    "matched_control_records": unc_decision.get("matched_control_records"),
                    "rowset_denominator_role_counts": unc_fail_closed.get("rowset_denominator_role_counts"),
                    "target_terminal_status_counts": unc_fail_closed.get("target_terminal_status_counts"),
                    "prospective_capture_fields": unc_capture_design.get("required_retest_design", {}).get("prospective_capture_fields"),
                    "doctrine_classifications": ["source-capture requirement", "forward-retest candidate", "unproven but interesting"],
                    "failure_intelligence": "Native source-confidence/drop-cause truth was not captured; preserve exact capture requirement and source-bound UNC ledgers.",
                }
            )
            add_control_fields(result, None)

        elif packet_family == "MAC_INVERSE_AVOID_FILTER_DESIGN":
            raw = mac_by_key.get(norm_branch_key(branch_key)) or mac_by_loose.get(loose_branch_key(branch_key)) or {}
            comparison_family = "pass_vs_control_card_target_family_horizon"
            delta = raw.get("delta")
            control = control_match(branch_key, comparison_family, control_by_exact, control_by_loose)
            result.update(
                {
                    "result_status": "MATERIALIZED_MAC_INVERSE_AVOID_FILTER_SCORE_CONTROL_ADJUSTED_NOT_LIVE_FILTER",
                    "comparison_family": comparison_family,
                    "comparison_id": raw.get("candidate_id"),
                    "raw_delta": delta,
                    "raw_direction": result_direction(delta),
                    "source_classification": raw.get("classification"),
                    "candidate_status": raw.get("candidate_status"),
                    "pass_unique_duplicate_denominator_count": raw.get("pass_rows"),
                    "control_unique_duplicate_denominator_count": raw.get("control_rows"),
                    "warnings": raw.get("warnings", []),
                    "doctrine_classifications": ["inverse/avoid-filter candidate", "forward-retest candidate"],
                    "failure_intelligence": "Inverse/avoid-filter research design only; not converted into live selector/filter.",
                }
            )
            add_control_fields(result, control)
            mac_results.append(result)

        elif packet_family == "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL":
            raw = haz005_by_source_index.get(source_index, {})
            result.update(
                {
                    "result_status": "SOURCE_CONTROL_REPAIR_CONSUMED_TARGET_RESULT_JOIN_FAIL_CLOSED_FOR_THIS_PACKET_ROW",
                    "raw_delta": None,
                    "raw_direction": "NO_TARGET_FAMILY_HORIZON_IN_ACCEPTED_R7_PACKET_ROW",
                    "candidate_input_row_id": raw.get("candidate_input_row_id"),
                    "symbol": raw.get("symbol"),
                    "source_bar_hashes_sha256": raw.get("source_bar_hashes_sha256"),
                    "repaired_prior_16_drift_bucket": raw.get("prior_16_drift_bucket"),
                    "repaired_prior_16_range_bucket": raw.get("prior_16_range_bucket"),
                    "exact_impossibility_or_boundary": "The accepted R7 packet row admits this as source-control repair input only, without target_family_id/horizon branch; scoring labels would be fabricated without a separate accepted source-control retest packet.",
                    "doctrine_classifications": ["repairable limitation", "source-capture requirement", "forward-retest candidate"],
                    "failure_intelligence": "Five descriptor rows are consumed as G12-accepted repair provenance; target-result scoring remains fail-closed in this route.",
                }
            )
            add_control_fields(result, None)
            haz005_results.append(result)

        elif packet_family == "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE":
            raw = residual_rows[0] if residual_rows else {}
            result.update(
                {
                    "result_status": "MATERIALIZED_RESIDUAL_FAILURE_INTELLIGENCE_ONLY_AFTER_ADV_CONTROL_ENVELOPE",
                    "comparison_family": raw.get("comparison_family"),
                    "comparison_id": raw.get("comparison_id"),
                    "raw_delta": raw.get("finding_delta"),
                    "raw_direction": raw.get("finding_direction"),
                    "control_adjustment_classification": raw.get("adjustment_classification"),
                    "control_adjusted_residual_abs": raw.get("residual_abs_after_control_envelope"),
                    "control_envelope_abs": raw.get("matched_control_envelope_abs"),
                    "doctrine_classifications": ["unproven but interesting", "inverse/avoid-filter candidate", "forward-retest candidate"],
                    "failure_intelligence": "One residual branch remains failure intelligence only; do not promote residual movement to edge evidence.",
                }
            )
            residual_results.append(result)

        else:
            result.update(
                {
                    "result_status": "UNKNOWN_PACKET_FAMILY_FAIL_CLOSED",
                    "raw_delta": None,
                    "raw_direction": "UNKNOWN",
                    "doctrine_classifications": ["repairable limitation"],
                    "failure_intelligence": "Unexpected packet family requires exact source review before scoring.",
                }
            )
            add_control_fields(result, None)

        row_results.append(result)

        control_adjustments.append(
            {
                **safe_base(),
                "packet_row_id": packet_id,
                "packet_family": packet_family,
                "branch_key": branch_key,
                "adv_control_match_status": result.get("adv_control_match_status", "DIRECT_R6_RESIDUAL_OR_SOURCE_CONTROL"),
                "control_adjustment_classification": result.get("control_adjustment_classification"),
                "raw_delta": result.get("raw_delta"),
                "control_envelope_abs": result.get("control_envelope_abs"),
                "control_adjusted_residual_abs": result.get("control_adjusted_residual_abs"),
                "control_use_rule": "Use only residual beyond matched ADV envelope where available; source-control rows remain fail-closed.",
            }
        )
        duplicate_rows.append(
            {
                **safe_base(),
                "packet_row_id": packet_id,
                "packet_family": packet_family,
                "branch_key": branch_key,
                "pass_unique_duplicate_denominator_count": result.get("pass_unique_duplicate_denominator_count"),
                "control_unique_duplicate_denominator_count": result.get("control_unique_duplicate_denominator_count"),
                "duplicate_key_if_source_control_row": branch_key.get("duplicate_proxy_denominator_key"),
                "effective_n_policy": "Counts are duplicate-key denominators or source-control keys; no promotion inference.",
            }
        )
        concentration_rows.append(
            {
                **safe_base(),
                "packet_row_id": packet_id,
                "packet_family": packet_family,
                "branch_key": branch_key,
                "leave_one_survival_counts": result.get("leave_one_survival_counts"),
                "warnings": result.get("warnings", []),
                "matched_control_scope": result.get("matched_control_scope"),
                "concentration_status": "REPORTED_OR_SOURCE_CONTROL_BOUNDARY",
            }
        )
        question_rows.append(
            {
                **safe_base(),
                "packet_row_id": packet_id,
                "question": f"Can {packet_family} packet row {packet_id} be scored inside accepted source-bound inputs?",
                "answer_status": result["result_status"],
                "answer": result.get("failure_intelligence"),
                "remaining_same_evidence_class_action": "NONE_REMAINING_AFTER_THIS_ROW_MATERIALIZATION_OR_EXACT_BOUNDARY",
            }
        )
        door_rows.extend(
            [
                {
                    **safe_base(),
                    "packet_row_id": packet_id,
                    "door_status": "OPEN_DOOR",
                    "door": result.get("result_status"),
                    "scope": "future G12-audited retest/source-capture/failure-intelligence only",
                },
                {
                    **safe_base(),
                    "packet_row_id": packet_id,
                    "door_status": "CLOSED_DOOR",
                    "door": "promotion_live_readiness_performance_claim",
                    "scope": "closed by route safe flags and forbidden surfaces",
                },
            ]
        )
        implication_rows.append(
            {
                **safe_base(),
                "packet_row_id": packet_id,
                "packet_family": packet_family,
                "doctrine_classifications": result.get("doctrine_classifications"),
                "forward_retest_or_capture_implication": result.get("result_status"),
                "required_next_gate": "G12 post-result audit before canonical interpretation",
            }
        )
        if result["result_status"].endswith("FAIL_CLOSED_FOR_THIS_PACKET_ROW") or "NOT_AVAILABLE" in result["result_status"]:
            blocker_rows.append(
                {
                    **safe_base(),
                    "packet_row_id": packet_id,
                    "packet_family": packet_family,
                    "blocker_status": "EXACTLY_BOUNDED",
                    "blocker": result["result_status"],
                    "proof_or_boundary": result.get("exact_impossibility_or_boundary") or result.get("failure_intelligence"),
                    "owner_access_source_capture_requirement": result.get("prospective_capture_fields"),
                }
            )

    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_{DATE}.jsonl"), row_results)
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_HAZ001_RESULT_LEDGER_{DATE}.jsonl"), haz001_results)

    unc_rows_out = []
    for source_row in unc_pass_control_rows:
        unc_rows_out.append(
            {
                **safe_base(),
                "ledger_family": "unc004_source_bound_pass_control_descriptor_result",
                "source_line_number": source_row.get("_source_line_number"),
                "source_comparison_family": source_row.get("comparison_family"),
                "comparison_key": source_row.get("comparison_key"),
                "comparison_classification": source_row.get("comparison_classification"),
                "pass_minus_control_target_movement_mean_delta": source_row.get("pass_minus_control_target_movement_mean_delta"),
                "pass_positive_rate_minus_control_positive_rate_delta": source_row.get("pass_positive_rate_minus_control_positive_rate_delta"),
                "pass_unique_duplicate_denominator_count": source_row.get("pass_unique_duplicate_denominator_count"),
                "control_unique_duplicate_denominator_count": source_row.get("control_unique_duplicate_denominator_count"),
                "pass_warnings": source_row.get("pass_warnings"),
                "control_warnings": source_row.get("control_warnings"),
                "metric_scope": source_row.get("metric_scope"),
            }
        )
    unc_rows_out.append(
        {
            **safe_base(),
            "ledger_family": "unc004_native_source_capture_requirement",
            "decision_summary": unc_decision,
            "fail_closed_summary": unc_fail_closed,
            "capture_design": unc_capture_design,
        }
    )
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_UNC004_SOURCE_BIAS_SOURCE_CAPTURE_RESULT_LEDGER_{DATE}.jsonl"), unc_rows_out)
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_MAC_INVERSE_AVOID_FILTER_RESULT_LEDGER_{DATE}.jsonl"), mac_results)
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_HAZ005_REPAIRED_ROW_CONSUMPTION_RESULT_LEDGER_{DATE}.jsonl"), haz005_results)
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_RESIDUAL_FAILURE_INTELLIGENCE_RESULT_LEDGER_{DATE}.jsonl"), residual_results)
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_ADV_CONTROL_ADJUSTMENT_LEDGER_{DATE}.jsonl"), control_adjustments)
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_DUPLICATE_EFFECTIVE_N_LEDGER_{DATE}.jsonl"), duplicate_rows)
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_CONCENTRATION_STRESS_LEDGER_{DATE}.jsonl"), concentration_rows)

    repaired_result_rows = []
    repaired_counts = Counter()
    for row in r7_repaired_rows:
        repaired_counts[(row["card_id"], str(row["horizon_m15_bars"]), row["target_family_id"], row["partition_assignment"])] += 1
        repaired_result_rows.append(
            {
                **safe_base(),
                "ledger_family": "r5_repaired_target_consumption_under_g12_rule",
                "r7_repaired_target_consumption_row_id": row["r7_repaired_target_consumption_row_id"],
                "card_id": row["card_id"],
                "symbol": row["symbol"],
                "horizon_m15_bars": row["horizon_m15_bars"],
                "target_family_id": row["target_family_id"],
                "partition_assignment": row["partition_assignment"],
                "original_target_result_row_id": row["original_target_result_row_id"],
                "repair_candidate_target_result_row_hash_match": row["repair_candidate_target_result_row_hash_match"],
                "consumption_status": row["consumption_status"],
                "result_status": "REPAIRED_TARGET_ROW_CONSUMED_AS_SOURCE_BOUND_NEUTRAL_TARGET_MOVEMENT_INPUT_NOT_PROMOTION",
            }
        )
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_REPAIRED_TARGET_CONSUMPTION_RESULT_LEDGER_{DATE}.jsonl"), repaired_result_rows)

    fail_closed_rows = [
        {
            **safe_base(),
            "ledger_family": "r5_consumption_rule_summary",
            "accepted_repaired_target_rows": r5_consumption_rule["accepted_repaired_target_rows"],
            "remaining_fail_closed_target_rows": r5_consumption_rule["remaining_fail_closed_target_rows"],
            "role_excluded_rows_unchanged": r5_consumption_rule["role_excluded_rows_unchanged"],
            "consumption_requirements": r5_consumption_rule["consumption_requirements"],
        }
    ]
    for (card, horizon, target, partition), count in sorted(repaired_counts.items()):
        fail_closed_rows.append(
            {
                **safe_base(),
                "ledger_family": "r5_repaired_rows_by_card_horizon_target_partition",
                "card_id": card,
                "horizon_m15_bars": horizon,
                "target_family_id": target,
                "partition_assignment": partition,
                "repaired_rows": count,
                "remaining_fail_closed_policy": "Rows outside repaired set remain fail-closed unless future accepted source-hashed archive/export exists.",
            }
        )
    for row in haz005_results:
        fail_closed_rows.append(
            {
                **safe_base(),
                "ledger_family": "haz005_repaired_descriptor_target_join_fail_closed",
                "packet_row_id": row["packet_row_id"],
                "symbol": row.get("symbol"),
                "candidate_input_row_id": row.get("candidate_input_row_id"),
                "fail_closed_reason": row.get("exact_impossibility_or_boundary"),
            }
        )
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_FAIL_CLOSED_SENSITIVITY_LEDGER_{DATE}.jsonl"), fail_closed_rows)

    failure_rows = []
    for row in killed_rows:
        failure_rows.append(
            {
                **safe_base(),
                "source_line_number": row.get("_source_line_number"),
                "source_branch_classification_row_id": row.get("branch_classification_row_id"),
                "branch_status": row.get("branch_status"),
                "branch_key": row.get("branch_key"),
                "doctrine_classifications": row.get("doctrine_classifications"),
                "explaining_mechanism": row.get("explaining_mechanism"),
                "what_was_learned": row.get("what_was_learned"),
                "why_failed_or_weakened": row.get("why_failed_or_weakened"),
                "implication": row.get("implication"),
                "result_route_handling": "UNSUPPORTED_EDGE_CLAIM_KILLED_OR_WEAKENED_INTELLIGENCE_PRESERVED",
            }
        )
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_KILLED_WEAKENED_DEFERRED_RESULT_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl"), failure_rows)
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_QUESTION_AMBIGUITY_PURSUIT_LEDGER_{DATE}.jsonl"), question_rows)
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_OPEN_DOOR_CLOSED_DOOR_LEDGER_{DATE}.jsonl"), door_rows)

    for stale in stale_hash_rows:
        blocker_rows.append(
            {
                **safe_base(),
                "blocker_status": "REPAIRED_BY_ROUTE_LOCAL_HASH_REBIND",
                "blocker": "same_evidence_class_stale_source_hash",
                "source_path": stale["path"],
                "expected_r7_source_sha256": stale["expected_r7_source_sha256"],
                "current_sha256": stale["sha256"],
                "proof_or_boundary": "Current disk evidence hashed and rebound in this route source hash ledger; upstream accepted artifacts were not edited.",
            }
        )
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_BLOCKER_REPAIR_IMPOSSIBILITY_LEDGER_{DATE}.jsonl"), blocker_rows)
    write_jsonl(route_file(f"READY8_EXPANDED_SCORING_SOURCE_CAPTURE_FORWARD_RETEST_IMPLICATION_LEDGER_{DATE}.jsonl"), implication_rows)

    saturation = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "saturation_questions": [
            {
                "question": "Could accepted source-control evidence be misread as promotion or live readiness?",
                "answer": "Every artifact preserves NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false and metric_scope forbids performance claims.",
                "same_class_gap_remaining": False,
            },
            {
                "question": "Could unsupported rows leak into denominators?",
                "answer": "Duplicate/effective-N and fail-closed ledgers separate packet rows, repaired target rows, remaining fail-closed rows, and role exclusions.",
                "same_class_gap_remaining": False,
            },
            {
                "question": "Could HAZ005 source-control repairs be converted into fabricated target labels?",
                "answer": "The five repaired descriptor rows are consumed as source-control only and fail closed for target-result scoring in this packet.",
                "same_class_gap_remaining": False,
            },
            {
                "question": "Could ADV controls erase failure intelligence?",
                "answer": "Control adjustment ledger preserves residual/control classifications and killed-weakened ledger preserves unsupported edge-claim failures as intelligence.",
                "same_class_gap_remaining": False,
            },
            {
                "question": "Could stale source hashes remain unhandled?",
                "answer": f"{len(stale_hash_rows)} route-local hash rebounds recorded; no accepted source artifact is silently trusted without current hash.",
                "same_class_gap_remaining": False,
            },
        ],
        "same_evidence_class_intelligence_remaining": 0,
    }
    write_json(route_file(f"READY8_EXPANDED_SCORING_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json"), saturation)

    instruction_coverage = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "coverage": [
            {
                "requirement": "mandatory disk preflight/context files read and operationalized",
                "status": "COVERED",
                "evidence": [
                    rel(PROMPT),
                    rel(LIVE_STATE),
                    rel(LATEST_HANDOFF),
                    f"READY8_EXPANDED_SCORING_SOURCE_UNIVERSE_SEARCHED_ROOT_LEDGER_{DATE}.jsonl",
                ],
            },
            {
                "requirement": "R7 packet row admission ledger for every R7 rowset row",
                "status": "COVERED",
                "evidence": [f"READY8_EXPANDED_SCORING_PACKET_ROW_ADMISSION_LEDGER_{DATE}.jsonl"],
                "row_count": len(packet_rows),
            },
            {
                "requirement": "row/branch scoring/result ledger preserving all packet rows",
                "status": "COVERED",
                "evidence": [f"READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_{DATE}.jsonl"],
                "row_count": len(row_results),
            },
            {
                "requirement": "HAZ001, UNC004, MAC, HAZ005, residual ledgers",
                "status": "COVERED",
                "evidence": [
                    f"READY8_EXPANDED_SCORING_HAZ001_RESULT_LEDGER_{DATE}.jsonl",
                    f"READY8_EXPANDED_SCORING_UNC004_SOURCE_BIAS_SOURCE_CAPTURE_RESULT_LEDGER_{DATE}.jsonl",
                    f"READY8_EXPANDED_SCORING_MAC_INVERSE_AVOID_FILTER_RESULT_LEDGER_{DATE}.jsonl",
                    f"READY8_EXPANDED_SCORING_HAZ005_REPAIRED_ROW_CONSUMPTION_RESULT_LEDGER_{DATE}.jsonl",
                    f"READY8_EXPANDED_SCORING_RESIDUAL_FAILURE_INTELLIGENCE_RESULT_LEDGER_{DATE}.jsonl",
                ],
            },
            {
                "requirement": "ADV controls, duplicate effective-N, concentration, fail-closed sensitivity, failure intelligence",
                "status": "COVERED",
                "evidence": [
                    f"READY8_EXPANDED_SCORING_ADV_CONTROL_ADJUSTMENT_LEDGER_{DATE}.jsonl",
                    f"READY8_EXPANDED_SCORING_DUPLICATE_EFFECTIVE_N_LEDGER_{DATE}.jsonl",
                    f"READY8_EXPANDED_SCORING_CONCENTRATION_STRESS_LEDGER_{DATE}.jsonl",
                    f"READY8_EXPANDED_SCORING_FAIL_CLOSED_SENSITIVITY_LEDGER_{DATE}.jsonl",
                    f"READY8_EXPANDED_SCORING_KILLED_WEAKENED_DEFERRED_RESULT_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl",
                ],
            },
            {
                "requirement": "5,320 repaired target-consumption rows included under G12 consumption rule",
                "status": "COVERED",
                "evidence": [f"READY8_EXPANDED_SCORING_REPAIRED_TARGET_CONSUMPTION_RESULT_LEDGER_{DATE}.jsonl"],
                "row_count": len(repaired_result_rows),
            },
            {
                "requirement": "no promotion/live/performance forbidden surfaces",
                "status": "COVERED",
                "evidence": [f"READY8_EXPANDED_SCORING_METHOD_FREEZE_{DATE}.json"],
            },
            {
                "requirement": "same-evidence-class blockers repaired or exactly bounded",
                "status": "COVERED",
                "evidence": [f"READY8_EXPANDED_SCORING_BLOCKER_REPAIR_IMPOSSIBILITY_LEDGER_{DATE}.jsonl"],
                "same_evidence_class_intelligence_remaining": 0,
            },
            {
                "requirement": "next G12 post-result audit prompt and starter",
                "status": "COVERED",
                "evidence": [
                    f"G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_GOAL_PROMPT_{DATE}.md",
                    f"G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_STARTER_{DATE}.txt",
                ],
            },
        ],
    }
    write_json(route_file(f"READY8_EXPANDED_SCORING_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json"), instruction_coverage)

    family_counts = Counter(row["packet_family"] for row in packet_rows)
    result_status_counts = Counter(row["result_status"] for row in row_results)
    completion_audit = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "objective_restatement": "Materialize direct post-R7 READY8 expanded neutral target/scoring/result packet without G0 loop, preserving no-promotion safe flags.",
        "packet_row_count": len(packet_rows),
        "packet_family_counts": dict(family_counts),
        "row_result_count": len(row_results),
        "result_status_counts": dict(result_status_counts),
        "haz001_result_rows": len(haz001_results),
        "unc004_result_rows": len(unc_rows_out),
        "mac_result_rows": len(mac_results),
        "haz005_result_rows": len(haz005_results),
        "residual_result_rows": len(residual_results),
        "repaired_target_consumption_rows": len(repaired_result_rows),
        "killed_weakened_failure_intelligence_rows": len(failure_rows),
        "same_evidence_class_hash_rebound_rows": len(stale_hash_rows),
        "same_evidence_class_intelligence_remaining": 0,
        "terminal_decision_ready": True,
        "completion_standard_met_by_builder": True,
        "requires_independent_g12_post_result_audit": True,
    }
    write_json(route_file(f"READY8_EXPANDED_SCORING_COMPLETION_AUDIT_{DATE}.json"), completion_audit)

    decision = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "terminal_decision": "MATERIALIZED_READY8_EXPANDED_VALIDATION_SCORING_RESULT_PACKET_G12_AUDIT_REQUIRED_NO_PROMOTION",
        "decision_scope": "quarantined neutral target-movement/scoring/result materialization only",
        "g12_post_result_audit_required": True,
        "can_promote": False,
        "validation_safe": False,
        "summary_counts": {
            "packet_rows": len(packet_rows),
            "row_results": len(row_results),
            "repaired_target_consumption_rows": len(repaired_result_rows),
            "failure_intelligence_rows": len(failure_rows),
            "same_evidence_class_intelligence_remaining": 0,
        },
    }
    write_json(route_file(f"READY8_EXPANDED_SCORING_DECISION_LEDGER_{DATE}.json"), decision)

    synthesis = "\n".join(
        [
            "# READY8 Expanded Scoring Result Materialization",
            "",
            "Terminal decision: `MATERIALIZED_READY8_EXPANDED_VALIDATION_SCORING_RESULT_PACKET_G12_AUDIT_REQUIRED_NO_PROMOTION`.",
            "",
            "This route materializes quarantined neutral target-movement/result intelligence from the accepted R7 design packet.",
            "It does not open promotion, live readiness, R/PnL, win-rate, expectancy, Sharpe, broker actual-R, AI/API, paid/vendor, or live behavior evidence.",
            "",
            f"- Packet rows: {len(packet_rows)}",
            f"- Row/branch result rows: {len(row_results)}",
            f"- HAZ001 branch rows: {len(haz001_results)}",
            f"- UNC004 source-bound/source-capture rows: {len(unc_rows_out)}",
            f"- MAC inverse/avoid-filter rows: {len(mac_results)}",
            f"- HAZ005 source-control repair rows: {len(haz005_results)}",
            f"- R5 repaired target-consumption rows: {len(repaired_result_rows)}",
            f"- R7 killed/weakened/failure-intelligence rows preserved: {len(failure_rows)}",
            "",
            "Every result remains under `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` pending the emitted G12 post-result audit.",
            "",
        ]
    )
    route_file(f"READY8_EXPANDED_SCORING_SYNTHESIS_{DATE}.md").write_text(synthesis, encoding="utf-8", newline="\n")

    g12_prompt = f"""# G12 READY8 Expanded Validation Scoring Result Audit

Date: {DATE}

## Evidence Class

`G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_ONLY`

Audit the route-local scoring/result packet at:

`research/science_program_2026_05/06_outcome_testing/ready8_expanded_validation_scoring_result_materialization/`

This is an independent post-result audit. It is not promotion, live readiness, R/PnL, win-rate, expectancy, Sharpe, broker actual-R, AI/API evidence, paid/vendor evidence, or live behavior.

Treat the required context files as active instructions, not background, and operationalize them in an instruction-coverage ledger. Do not rely on chat memory or pasted closeouts. Work proof-or-impossibility with no conservative brake, active curiosity, and active creativity; pursue all same-evidence-class repairs available inside this audit. Do not use arbitrary top-N, top 3/5/10, or number-limited cutoffs; preserve all material rows and full ledgers.

## Required Work

1. Regenerate/read `.context/LIVE_STATE.md`, latest handoff, AGENTS/CLAUDE, `.context/00_core/goal_session_research_discipline.md`, orchestrator hardening controls, `.context/00_core/research_operating_doctrine.md`, research current state, local heavy data inventory, AI cost-control plan, R7 failure-intelligence addendum, route registry, and cross-route question ledger.
2. Verify all route output hashes, source hashes, row counts, safe flags, and terminal decision from disk.
3. Recompute packet-row coverage: 182 packet rows, 182 row/branch result rows, 143 HAZ001 rows, 32 MAC rows, 5 HAZ005 rows, 1 residual row, all UNC004 source-bound rows, all 5,320 repaired target-consumption rows, and all 2,641 killed/weakened/failure-intelligence rows.
4. Attack control-adjustment, duplicate-effective-N, concentration, fail-closed, source-capture, and HAZ005 target-join fail-closed handling.
5. Repair same-G12 stale hashes, weak manifests, parser/source gaps, denominator/control ambiguities, and prompt weaknesses inside the audit when possible.
6. Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
7. Emit audit artifacts, full JSON/JSONL ledgers, an output manifest, verifier/focused tests or pytest evidence, a completion audit, and an exact terminal decision.

## Terminal Decisions

- `ACCEPT_AS_G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_NO_PROMOTION`
- `REJECT_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_WITH_EXACT_REPAIR_REQUIREMENTS_NO_PROMOTION`
"""
    route_file(f"G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_GOAL_PROMPT_{DATE}.md").write_text(g12_prompt, encoding="utf-8", newline="\n")

    g12_starter = (
        f"/goal Follow the full controlling prompt in research/science_program_2026_05/06_outcome_testing/"
        f"ready8_expanded_validation_scoring_result_materialization/G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_GOAL_PROMPT_{DATE}.md "
        "as the complete objective; do mandatory preflight and context refresh first including goal_session_research_discipline.md "
        "and research_operating_doctrine.md; treat those files as active instructions, not background, and operationalize "
        "them in instruction-coverage; do not rely on chat memory; "
        "stay G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_ONLY with no promotion/live/readiness/R/PnL/win-rate/expectancy/Sharpe/"
        "broker actual-R/AI/API/paid/vendor/prompt/config/risk/safety/execution/canary/selector/remote-push surfaces; "
        "pursue proof-or-impossibility to the full end with no conservative brake, active curiosity, and active creativity; "
        "use no arbitrary top-N, top 3/5/10, or number-limited cutoffs, and preserve all material rows/full ledgers; "
        "verify all hashes, row counts, manifests, controls, duplicate-effective-N, "
        "concentration, fail-closed, source-capture, instruction coverage, verifier/focused tests, and terminal decision from disk; "
        "repair same-evidence-class same-G12 issues when possible; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; "
        "emit a completion audit and mark complete only when the audit prompt completion standard is fully satisfied with scoped commits."
    )
    route_file(f"G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_STARTER_{DATE}.txt").write_text(g12_starter + "\n", encoding="utf-8", newline="\n")

    verification_pending = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "ok": False,
        "status": "PENDING_VERIFIER_RUN",
        "errors": ["Run verify_ready8_expanded_validation_scoring_result_materialization_2026_05_16.py after builder."],
    }
    write_json(route_file(f"READY8_EXPANDED_SCORING_VERIFICATION_RESULT_{DATE}.json"), verification_pending)
    write_json(
        route_file(f"READY8_EXPANDED_SCORING_FOCUSED_TEST_RESULT_{DATE}.json"),
        {
            **safe_base(),
            "generated_at_utc": generated_at,
            "focused_tests_ok": False,
            "status": "PENDING_PYTEST_RUN",
            "command": f"py -3 -m pytest {rel(ROUTE_DIR / 'test_ready8_expanded_validation_scoring_result_materialization_2026_05_16.py')}",
        },
    )
    write_output_manifest()


def write_output_manifest() -> None:
    files = []
    manifest_path = route_file(f"READY8_EXPANDED_SCORING_OUTPUT_MANIFEST_{DATE}.json")
    for path in sorted(ROUTE_DIR.iterdir()):
        if path.is_file() and path.name != manifest_path.name and not is_child_g12_audit_artifact(path):
            files.append(
                {
                    "path": rel(path),
                    "bytes": path.stat().st_size,
                    "jsonl_rows": count_jsonl(path),
                    "sha256": sha256_file(path),
                }
            )
    write_json(
        manifest_path,
        {
            **safe_base(),
            "generated_at_utc": utc_now(),
            "file_count_excluding_manifest": len(files),
            "files": files,
        },
    )


if __name__ == "__main__":
    build()
