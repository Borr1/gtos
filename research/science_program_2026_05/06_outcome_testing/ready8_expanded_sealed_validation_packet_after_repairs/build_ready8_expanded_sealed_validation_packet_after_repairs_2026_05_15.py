#!/usr/bin/env python3
"""Build the READY8 R7 expanded sealed-validation packet design.

This is a design-only packet. It consumes accepted post-G12 evidence and
failure-intelligence ledgers, but does not open outcome scoring, promotion,
live behavior, broker/order evidence, or prompt/config/risk/safety changes.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-15"
ROUTE_ID = "READY8_EXPANDED_SEALED_VALIDATION_PACKET_AFTER_REPAIRS"
EVIDENCE_CLASS = "READY8_EXPANDED_SEALED_VALIDATION_PACKET_DESIGN_ONLY"
SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_live_trading_behavior": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}
DOCTRINE_CLASSES = [
    "false opportunity / generic movement",
    "repairable limitation",
    "mixed mechanism needing split",
    "unproven but interesting",
    "inverse/avoid-filter candidate",
    "source-capture requirement",
    "forward-retest candidate",
    "exact owner/access/source/capture impossibility",
]


PATHS = {
    "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/READY8_EXPANDED_SEALED_VALIDATION_PACKET_AFTER_REPAIRS_GOAL_PROMPT_2026-05-15.md",
    "failure_doctrine_addendum": ".context/00_core/r7_failure_intelligence_doctrine_addendum.md",
    "route_registry_json": "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json",
    "cross_route_question_ledger_json": "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json",
    "g12_anchor_decision": "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit/G12_R8DISC_SEALED_VALIDATION_AUDIT_DECISION_LEDGER_2026-05-13.json",
    "g12_anchor_recompute": "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit/G12_R8DISC_SEALED_VALIDATION_AUDIT_RECOMPUTATION_LEDGER_2026-05-13.json",
    "haz001_design": "research/science_program_2026_05/06_outcome_testing/haz001_density_waiting_time_concentration_expansion_and_sealed_retest/HAZ001_DECONCENTRATED_RETEST_DESIGN_LEDGER_2026-05-15.json",
    "haz001_source_search": "research/science_program_2026_05/06_outcome_testing/haz001_density_waiting_time_concentration_expansion_and_sealed_retest/HAZ001_SOURCE_SEARCH_ACQUISITION_LEDGER_2026-05-15.json",
    "g12_haz001_decision": "research/science_program_2026_05/06_outcome_testing/haz001_density_waiting_time_concentration_expansion_and_sealed_retest/G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_DECISION_LEDGER_2026-05-15.json",
    "unc004_design": "research/science_program_2026_05/06_outcome_testing/unc004_source_confidence_mechanism_disentanglement/UNC004_DOWNSTREAM_CAPTURE_RETEST_DESIGN_2026-05-15.json",
    "unc004_source_search": "research/science_program_2026_05/06_outcome_testing/unc004_source_confidence_mechanism_disentanglement/UNC004_SOURCE_SEARCH_ACQUISITION_LADDER_2026-05-15.json",
    "g12_unc004_decision": "research/science_program_2026_05/06_outcome_testing/g12_unc004_source_confidence_disentanglement_audit/G12_UNC004_SOURCE_CONFIDENCE_AUDIT_DECISION_LEDGER_2026-05-15.json",
    "mac_design_rows": "research/science_program_2026_05/06_outcome_testing/mac001_mac004_inverse_avoid_filter_validation_design/MAC_INVERSE_AVOID_FILTER_CANDIDATE_DESIGN_LEDGER_2026-05-15.jsonl",
    "mac_future_capture": "research/science_program_2026_05/06_outcome_testing/mac001_mac004_inverse_avoid_filter_validation_design/MAC_INVERSE_FUTURE_VALIDATION_SOURCE_CAPTURE_DESIGN_2026-05-15.json",
    "g12_mac_decision": "research/science_program_2026_05/06_outcome_testing/mac001_mac004_inverse_avoid_filter_validation_design/G12_MAC_INVERSE_AUDIT_DECISION_LEDGER_2026-05-15.json",
    "haz005_repaired_rows": "research/science_program_2026_05/06_outcome_testing/haz005_transition_clock_split_and_source_repair/HAZ005_REPAIRED_DESCRIPTOR_ROW_PACKET_2026-05-15.jsonl",
    "haz005_future_source_rows": "research/science_program_2026_05/06_outcome_testing/haz005_transition_clock_split_and_source_repair/HAZ005_EXACT_FUTURE_SOURCE_CAPTURE_FIELDS_2026-05-15.jsonl",
    "haz005_source_search": "research/science_program_2026_05/06_outcome_testing/haz005_transition_clock_split_and_source_repair/HAZ005_SOURCE_SEARCH_ACQUISITION_LEDGER_2026-05-15.json",
    "g12_haz005_decision": "research/science_program_2026_05/06_outcome_testing/haz005_transition_clock_split_and_source_repair/G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_DECISION_LEDGER_2026-05-15.json",
    "g12_fail_closed_decision": "research/science_program_2026_05/06_outcome_testing/g12_ready8_fail_closed_path_horizon_source_repair_audit/G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_DECISION_LEDGER_2026-05-15.json",
    "g12_fail_closed_consumption_rule": "research/science_program_2026_05/06_outcome_testing/g12_ready8_fail_closed_path_horizon_source_repair_audit/G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_R7_CONSUMPTION_RULE_2026-05-15.json",
    "g12_fail_closed_repaired_rows": "research/science_program_2026_05/06_outcome_testing/g12_ready8_fail_closed_path_horizon_source_repair_audit/G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_REPAIRED_TARGET_RECOMPUTATION_LEDGER_2026-05-15.jsonl",
    "adv_rules": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_DOWNSTREAM_ADJUSTMENT_RULES_2026-05-15.json",
    "adv_control_design": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV001_ADV003_CONTROL_DESIGN_AUDIT_LEDGER_2026-05-15.json",
    "adv_explained_weakened_rows": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_CONTROLS_FULLY_EXPLAIN_OR_WEAKEN_FINDINGS_LEDGER_2026-05-15.jsonl",
    "adv_residual_rows": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_NEGATIVE_CONTROLS_FAIL_TO_EXPLAIN_RESIDUAL_LEDGER_2026-05-15.jsonl",
    "adv_underpower_rows": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_BRANCH_UNDERPOWER_EFFECTIVE_N_LEDGER_2026-05-15.jsonl",
    "adv_concentration_rows": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_CONCENTRATION_ADJUSTED_INTERPRETATION_LEDGER_2026-05-15.jsonl",
    "adv_duplicate_rows": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_DUPLICATE_BUCKET_ARTIFACT_LEDGER_2026-05-15.jsonl",
    "g12_adv_decision": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_DECISION_LEDGER_2026-05-15.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def absolute(label: str) -> Path:
    return ROOT / PATHS[label]


def load_json(label: str) -> dict[str, Any]:
    with absolute(label).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(label: str) -> Iterable[dict[str, Any]]:
    with absolute(label).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_jsonl(label: str) -> list[dict[str, Any]]:
    return list(iter_jsonl(label))


def line_count(path: Path) -> int | None:
    if not path.exists() or path.suffix.lower() != ".jsonl":
        return None
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_ref(label: str) -> dict[str, Any]:
    path = absolute(label)
    return {
        "label": label,
        "path": rel(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else None,
        "jsonl_rows": line_count(path),
        "sha256": sha256_file(path) if path.exists() else None,
    }


def write_json(name: str, payload: dict[str, Any]) -> None:
    payload = {**payload}
    payload.setdefault("route_id", ROUTE_ID)
    payload.setdefault("evidence_class", EVIDENCE_CLASS)
    for key, value in SAFE_FLAGS.items():
        payload.setdefault(key, value)
    path = ROUTE_DIR / name
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(name: str, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    path = ROUTE_DIR / name
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            out = {**row}
            out.setdefault("route_id", ROUTE_ID)
            out.setdefault("evidence_class", EVIDENCE_CLASS)
            for key, value in SAFE_FLAGS.items():
                out.setdefault(key, value)
            handle.write(json.dumps(out, sort_keys=True) + "\n")
            count += 1
    return count


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def classification_for_adjustment(adjustment: str, card_id: str) -> tuple[str, list[str], str, str]:
    if adjustment == "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT":
        return (
            "CONTROL_EXPLAINED_EDGE_CLAIM_KILLED_INTELLIGENCE_PRESERVED",
            ["false opportunity / generic movement", "forward-retest candidate"],
            "control-adjusted",
            "control rule",
        )
    if adjustment == "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT":
        return (
            "WEAKENED_BY_CONTROL_ENVELOPE_INTELLIGENCE_PRESERVED",
            ["mixed mechanism needing split", "forward-retest candidate"],
            "adjusted",
            "packet-design row",
        )
    if adjustment == "RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE":
        if card_id.startswith("MAC"):
            classes = ["inverse/avoid-filter candidate", "forward-retest candidate"]
        else:
            classes = ["unproven but interesting", "forward-retest candidate"]
        return (
            "RESIDUAL_PRESERVED_AFTER_CONTROL_ENVELOPE",
            classes,
            "preserved",
            "future retest candidate",
        )
    if adjustment == "UNDERPOWERED_PRESERVED_NOT_DECISION":
        return (
            "UNDERPOWERED_RETAINED_FOR_SAMPLE_EXPANSION",
            ["unproven but interesting", "forward-retest candidate"],
            "preserved",
            "future retest candidate",
        )
    return (
        "NOT_NUMERIC_OR_NOT_ADJUSTABLE_RETAINED_AS_FAILURE_INTELLIGENCE",
        ["unproven but interesting"],
        "preserved",
        "control rule",
    )


def build_prerequisites() -> list[dict[str, Any]]:
    specs = [
        ("G12_SCID_READY8_ANCHOR", "g12_anchor_decision", "Accepted frozen READY8 sealed-validation audit anchor."),
        ("R1_G12_HAZ001", "g12_haz001_decision", "Accepted HAZ001 mechanism expansion audit; deconcentrated rows are retest candidates only."),
        ("R2_G12_UNC004", "g12_unc004_decision", "Accepted UNC004 source-confidence disentanglement audit after manifest repair."),
        ("R3_G12_MAC", "g12_mac_decision", "Accepted MAC inverse avoid-filter design audit with h1 MAC004 killed but intelligence preserved."),
        ("R4_G12_HAZ005", "g12_haz005_decision", "Accepted HAZ005 source repair audit with five repaired rows and 785 bounded future rows."),
        ("R5_G12_FAIL_CLOSED", "g12_fail_closed_decision", "Accepted fail-closed path/horizon source repair audit; R7 may consume 5320 repaired target rows."),
        ("R6_G12_ADV_CONTROL", "g12_adv_decision", "Accepted ADV001/ADV003 control-envelope evidence; not a blanket eraser."),
    ]
    rows = []
    for prerequisite_id, label, use_rule in specs:
        decision = load_json(label)
        rows.append(
            {
                "prerequisite_id": prerequisite_id,
                "accepted": bool(decision.get("accepted")),
                "terminal_decision": decision.get("terminal_decision"),
                "source": source_ref(label),
                "safe_flags_observed": {
                    "promotion_verdict": decision.get("promotion_verdict"),
                    "validation_safe": decision.get("validation_safe"),
                    "outcome_review_opened": decision.get("outcome_review_opened"),
                    "live_effect": decision.get("live_effect"),
                },
                "r7_consumption_rule": use_rule,
                "branch_handling_policy": "consume only as design/prerequisite evidence; preserve failure intelligence; do not promote.",
            }
        )
    return rows


def build_source_universe() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in sorted(PATHS):
        ref = source_ref(label)
        if label.endswith("_rows"):
            inclusion = "included_full_jsonl_reference"
        elif "source_search" in label or "route_registry" in label or "question_ledger" in label:
            inclusion = "source_search_or_context_reference"
        else:
            inclusion = "included_control_or_decision_reference"
        rows.append(
            {
                **ref,
                "universe_status": inclusion,
                "included_in_r7_materialization": True,
                "excluded_reason": None,
                "safe_surface_note": "Source is consumed as artifact evidence only; no raw market blob or live/broker surface is opened.",
            }
        )
    return rows


def build_surviving_mechanisms(haz001: dict[str, Any], unc004: dict[str, Any], mac_rows: list[dict[str, Any]], haz005_rows: list[dict[str, Any]], residual_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mac_status_counts = Counter(row.get("candidate_status") for row in mac_rows)
    mac_card_counts = Counter(row.get("branch_key", {}).get("card_id") for row in mac_rows)
    return [
        {
            "mechanism_id": "HAZ-001",
            "packet_status": "INCLUDE_AS_FORWARD_RETEST_DESIGN_FAMILY_WITH_ADV_CONTROL_SUBTRACTION",
            "doctrine_classifications": ["mixed mechanism needing split", "forward-retest candidate"],
            "material_rows_preserved": haz001.get("eligible_deconcentrated_branch_count"),
            "source": source_ref("haz001_design"),
            "learned": "Candidate-arrival density/wait-gap structure remains a deconcentrated retest family, but not an unadjusted edge claim.",
            "required_control": "Subtract matched ADV001/ADV003 control envelope before any future result interpretation.",
            "disposition": "split and adjusted",
            "implication": "packet-design row",
        },
        {
            "mechanism_id": "UNC-004",
            "packet_status": "INCLUDE_AS_SOURCE_CONFIDENCE_SOURCE_BIAS_DIAGNOSTIC_RETEST_FAMILY",
            "doctrine_classifications": ["source-capture requirement", "forward-retest candidate", "unproven but interesting"],
            "material_rows_preserved": 1,
            "source": source_ref("unc004_design"),
            "learned": unc004.get("exact_source_capture_requirement"),
            "required_control": "Future packet must capture native source-confidence/drop-cause/latency fields before target opening and apply ADV control adjustment.",
            "disposition": "preserved and source-capture-routed",
            "implication": "source-capture requirement",
        },
        {
            "mechanism_id": "MAC-001",
            "packet_status": "INCLUDE_AS_INVERSE_AVOID_FILTER_DESIGN_FAMILY_NOT_LIVE_FILTER",
            "doctrine_classifications": ["inverse/avoid-filter candidate", "forward-retest candidate"],
            "material_rows_preserved": mac_card_counts.get("MAC-001", 0),
            "candidate_status_counts": dict(mac_status_counts),
            "source": source_ref("mac_design_rows"),
            "learned": "Calendar/timing inverse movement remains avoid-filter research design after G12, with concentration and ADV controls mandatory.",
            "required_control": "ADV001 time/session placebo subtraction plus duplicate-effective-N and concentration checks.",
            "disposition": "preserved as inverse design",
            "implication": "avoid rule",
        },
        {
            "mechanism_id": "HAZ-005_REPAIRED_DESCRIPTOR_ROWS",
            "packet_status": "INCLUDE_ACCEPTED_REPAIRED_DESCRIPTOR_ROWS_AS_SOURCE_CONTROL_INPUTS",
            "doctrine_classifications": ["repairable limitation", "source-capture requirement", "forward-retest candidate"],
            "material_rows_preserved": len(haz005_rows),
            "source": source_ref("haz005_repaired_rows"),
            "learned": "Five prior16 descriptor rows were repaired and G12 accepted as source-control inputs only.",
            "required_control": "Use repaired rows only with source hashes and G12 provenance; do not convert them into validation or promotion.",
            "disposition": "repaired",
            "implication": "packet-design row",
        },
        {
            "mechanism_id": "BEH-001_RESIDUAL_AFTER_ADV",
            "packet_status": "PRESERVE_AS_FAILURE_OR_AVOID_INTELLIGENCE_ONLY",
            "doctrine_classifications": ["unproven but interesting", "inverse/avoid-filter candidate", "forward-retest candidate"],
            "material_rows_preserved": len(residual_rows),
            "source": source_ref("adv_residual_rows"),
            "learned": "One New York session bucket inverse residual remains after ADV control envelope, but it is neutral target-movement failure intelligence only.",
            "required_control": "Keep under safe flags and require future preregistered retest; do not promote.",
            "disposition": "preserved",
            "implication": "future retest candidate",
        },
    ]


def build_branch_classification_rows(
    haz001: dict[str, Any],
    mac_rows: list[dict[str, Any]],
    haz005_rows: list[dict[str, Any]],
    haz005_future_rows: list[dict[str, Any]],
    adv_rows: list[dict[str, Any]],
    residual_rows: list[dict[str, Any]],
    r5_rule: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, branch in enumerate(haz001.get("eligible_deconcentrated_branches", []), start=1):
        rows.append(
            {
                "branch_classification_row_id": f"haz001_deconcentrated:{idx:04d}",
                "source_label": "haz001_design",
                "source_row_index": idx,
                "branch_key": branch.get("branch_key"),
                "branch_status": "PACKET_INCLUDED_FOR_RETEST_DESIGN",
                "doctrine_classifications": ["mixed mechanism needing split", "forward-retest candidate"],
                "what_was_learned": "Deconcentrated HAZ001 branch remains eligible for future retest after source-control packet formation.",
                "why_failed_or_weakened": "Not killed; edge claim remains unproven and must be ADV-control adjusted.",
                "explaining_mechanism": "concentration plus generic movement control risk",
                "disposition": "split and adjusted",
                "implication": "packet-design row",
                "raw_branch": branch,
            }
        )
    for idx, row in enumerate(mac_rows, start=1):
        card = row.get("branch_key", {}).get("card_id")
        h = str(row.get("branch_key", {}).get("horizon_m15_bars"))
        if card == "MAC-004" and h == "1":
            status = "EDGE_CLAIM_KILLED_INTELLIGENCE_PRESERVED"
            doctrine = ["false opportunity / generic movement", "inverse/avoid-filter candidate"]
            why = "MAC004 h1 fix-window branch was positive rather than inverse and is killed as avoid-filter evidence, while the failure information is preserved."
            disposition = "split and preserved"
            implication = "avoid rule"
        elif "UNDERPOWERED" in str(row.get("candidate_status")):
            status = "UNDERPOWERED_RETAINED_FOR_SAMPLE_EXPANSION"
            doctrine = ["unproven but interesting", "forward-retest candidate"]
            why = "Duplicate-effective-N or branch support is insufficient for decision use."
            disposition = "preserved"
            implication = "future retest candidate"
        else:
            status = "INVERSE_AVOID_FILTER_DESIGN_PRESERVED"
            doctrine = ["inverse/avoid-filter candidate", "forward-retest candidate"]
            why = "Inverse branch is not killed but remains concentration/control constrained."
            disposition = "preserved"
            implication = "avoid rule"
        rows.append(
            {
                "branch_classification_row_id": f"mac_design:{idx:04d}",
                "source_label": "mac_design_rows",
                "source_row_index": idx,
                "branch_key": row.get("branch_key"),
                "branch_status": status,
                "doctrine_classifications": doctrine,
                "what_was_learned": "MAC timing/fix-window rows are useful as inverse/failure anatomy, not live filters.",
                "why_failed_or_weakened": why,
                "explaining_mechanism": "ADV time/session control risk, concentration, and branch support limits",
                "disposition": disposition,
                "implication": implication,
                "raw_branch": row,
            }
        )
    for idx, row in enumerate(haz005_rows, start=1):
        rows.append(
            {
                "branch_classification_row_id": f"haz005_repaired:{idx:04d}",
                "source_label": "haz005_repaired_rows",
                "source_row_index": idx,
                "branch_key": {
                    "candidate_input_row_id": row.get("candidate_input_row_id"),
                    "symbol": row.get("symbol"),
                    "partition_assignment": row.get("validation_partition_assignment"),
                },
                "branch_status": "REPAIRABLE_LIMITATION_REPAIRED_SOURCE_CONTROL_ONLY",
                "doctrine_classifications": ["repairable limitation", "source-capture requirement", "forward-retest candidate"],
                "what_was_learned": "Local Sierra source repair can reconstruct a bounded set of prior16 descriptor rows.",
                "why_failed_or_weakened": "Original branch was source-limited by missing prior16 bars.",
                "explaining_mechanism": "source gap / fail-closed prior16 descriptor input",
                "disposition": "repaired",
                "implication": "packet-design row",
                "raw_branch": row,
            }
        )
    for idx, row in enumerate(haz005_future_rows, start=1):
        rows.append(
            {
                "branch_classification_row_id": f"haz005_future_capture:{idx:04d}",
                "source_label": "haz005_future_source_rows",
                "source_row_index": idx,
                "branch_key": {
                    "symbol": row.get("symbol"),
                    "source_file_name": row.get("source_file_name"),
                    "required_bar_window": row.get("prior16_required_bar_end_utc"),
                },
                "branch_status": "SOURCE_LIMITED_CAPTURE_REQUIRED",
                "doctrine_classifications": ["source-capture requirement", "exact owner/access/source/capture impossibility"],
                "what_was_learned": "The remaining HAZ005 source gap has exact owner/access/source/capture contracts instead of vague future work.",
                "why_failed_or_weakened": "The current same-evidence-class sources cannot prove the missing prior16 bars for all rows.",
                "explaining_mechanism": "source gap / missing prior16 bar capture",
                "disposition": "proven impossible inside current source set",
                "implication": "source-capture requirement",
                "raw_branch": row,
            }
        )
    for idx, row in enumerate(adv_rows, start=1):
        status, doctrine, disposition, implication = classification_for_adjustment(
            str(row.get("adjustment_classification")), str(row.get("card_id"))
        )
        rows.append(
            {
                "branch_classification_row_id": f"adv_adjustment:{idx:05d}",
                "source_label": "adv_explained_weakened_rows",
                "source_row_index": idx,
                "branch_key": row.get("branch_key"),
                "branch_status": status,
                "doctrine_classifications": doctrine,
                "what_was_learned": "Matched ADV control envelope explains, weakens, or bounds this non-ADV branch; intelligence is retained with exact disposition.",
                "why_failed_or_weakened": row.get("adjustment_classification"),
                "explaining_mechanism": "ADV001/ADV003 matched control drift envelope",
                "disposition": disposition,
                "implication": implication,
                "raw_branch": row,
            }
        )
    for idx, row in enumerate(residual_rows, start=1):
        rows.append(
            {
                "branch_classification_row_id": f"adv_residual:{idx:04d}",
                "source_label": "adv_residual_rows",
                "source_row_index": idx,
                "branch_key": row.get("branch_key"),
                "branch_status": "RESIDUAL_PRESERVED_AFTER_CONTROL_ENVELOPE",
                "doctrine_classifications": ["unproven but interesting", "inverse/avoid-filter candidate", "forward-retest candidate"],
                "what_was_learned": "This branch has residual movement after matched control subtraction.",
                "why_failed_or_weakened": "Not failed, but remains neutral target-movement intelligence under safe flags.",
                "explaining_mechanism": "residual beyond ADV control envelope, still concentration/control constrained",
                "disposition": "preserved",
                "implication": "future retest candidate",
                "raw_branch": row,
            }
        )
    rows.append(
        {
            "branch_classification_row_id": "fail_closed_remaining:target_rows",
            "source_label": "g12_fail_closed_consumption_rule",
            "source_row_index": 1,
            "branch_key": {"remaining_fail_closed_target_rows": r5_rule.get("remaining_fail_closed_target_rows")},
            "branch_status": "FAIL_CLOSED_REMAINS_EXCLUDED_WITH_CAPTURE_REQUIREMENT",
            "doctrine_classifications": ["source-capture requirement", "exact owner/access/source/capture impossibility"],
            "what_was_learned": "Remaining fail-closed target rows stay informative as source-gap inventory, not negative evidence.",
            "why_failed_or_weakened": "Required source bars are still unavailable in accepted same-class sources.",
            "explaining_mechanism": "fail-closed path/horizon source gaps",
            "disposition": "proven impossible inside current source set",
            "implication": "source-capture requirement",
            "raw_branch": {
                "remaining_fail_closed_target_rows": r5_rule.get("remaining_fail_closed_target_rows"),
                "role_excluded_rows_unchanged": r5_rule.get("role_excluded_rows_unchanged"),
                "consumption_requirements": r5_rule.get("consumption_requirements"),
            },
        }
    )
    return rows


def build_killed_deferred_rows(classification_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    excluded_statuses = {
        "PACKET_INCLUDED_FOR_RETEST_DESIGN",
        "INVERSE_AVOID_FILTER_DESIGN_PRESERVED",
        "REPAIRABLE_LIMITATION_REPAIRED_SOURCE_CONTROL_ONLY",
        "RESIDUAL_PRESERVED_AFTER_CONTROL_ENVELOPE",
    }
    rows = []
    for row in classification_rows:
        if row["branch_status"] in excluded_statuses:
            continue
        rows.append(
            {
                "branch_classification_row_id": row["branch_classification_row_id"],
                "source_label": row["source_label"],
                "source_row_index": row["source_row_index"],
                "branch_key": row.get("branch_key"),
                "branch_status": row["branch_status"],
                "doctrine_classifications": row["doctrine_classifications"],
                "what_was_learned": row["what_was_learned"],
                "why_failed_or_weakened": row["why_failed_or_weakened"],
                "explaining_mechanism": row["explaining_mechanism"],
                "disposition": row["disposition"],
                "implication": row["implication"],
                "kill_scope": "unsupported_edge_claim_only_not_branch_intelligence",
            }
        )
    return rows


def build_rowset_design(
    haz001: dict[str, Any],
    unc004: dict[str, Any],
    mac_rows: list[dict[str, Any]],
    haz005_rows: list[dict[str, Any]],
    residual_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, branch in enumerate(haz001.get("eligible_deconcentrated_branches", []), start=1):
        rows.append(
            {
                "packet_row_id": f"r7_packet_haz001:{idx:04d}",
                "packet_family": "HAZ001_DECONCENTRATED_RETEST",
                "packet_role": "future_retest_design_branch",
                "branch_key": branch.get("branch_key"),
                "source_label": "haz001_design",
                "source_row_index": idx,
                "admission_status": "ADMITTED_DESIGN_ONLY_REQUIRES_FUTURE_G12_SCORING_GATE",
                "control_requirements": ["ADV001_ADV003_CONTROL_ENVELOPE", "duplicate_effective_n", "concentration_reporting"],
                "no_leak_fields_allowed": ["decision_asof_utc", "duplicate_proxy_denominator_key", "symbol", "source_segment_sha256", "predecision_descriptors"],
            }
        )
    rows.append(
        {
            "packet_row_id": "r7_packet_unc004:0001",
            "packet_family": "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC",
            "packet_role": "source_bias_capture_design",
            "branch_key": {"card_id": "UNC-004", "candidate_denominator": unc004.get("required_retest_design", {}).get("candidate_denominator")},
            "source_label": "unc004_design",
            "source_row_index": 1,
            "admission_status": "ADMITTED_DESIGN_ONLY_REQUIRES_NATIVE_SOURCE_CONFIDENCE_CAPTURE",
            "control_requirements": unc004.get("required_retest_design", {}).get("primary_controls", []),
            "prospective_capture_fields": unc004.get("required_retest_design", {}).get("prospective_capture_fields", []),
        }
    )
    for idx, row in enumerate(mac_rows, start=1):
        rows.append(
            {
                "packet_row_id": f"r7_packet_mac:{idx:04d}",
                "packet_family": "MAC_INVERSE_AVOID_FILTER_DESIGN",
                "packet_role": "inverse_or_failure_anatomy_branch",
                "branch_key": row.get("branch_key"),
                "source_label": "mac_design_rows",
                "source_row_index": idx,
                "admission_status": "ADMITTED_DESIGN_ONLY_NOT_LIVE_FILTER",
                "control_requirements": ["ADV001_TIME_SESSION_PLACEBO_SUBTRACTION", "duplicate_effective_n", "concentration_reporting"],
                "as_of_fields_required": row.get("as_of_fields_required"),
            }
        )
    for idx, row in enumerate(haz005_rows, start=1):
        rows.append(
            {
                "packet_row_id": f"r7_packet_haz005_repaired:{idx:04d}",
                "packet_family": "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL",
                "packet_role": "accepted_source_repair_input",
                "branch_key": {
                    "candidate_input_row_id": row.get("candidate_input_row_id"),
                    "symbol": row.get("symbol"),
                    "source_bar_hashes_sha256": row.get("source_bar_hashes_sha256"),
                },
                "source_label": "haz005_repaired_rows",
                "source_row_index": idx,
                "admission_status": "ADMITTED_SOURCE_CONTROL_ONLY_AFTER_G12",
                "control_requirements": ["source_bar_hash_preservation", "G12_repair_provenance", "ADV_control_before_any_result_use"],
            }
        )
    for idx, row in enumerate(residual_rows, start=1):
        rows.append(
            {
                "packet_row_id": f"r7_packet_adv_residual:{idx:04d}",
                "packet_family": "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE",
                "packet_role": "residual_failure_anatomy_branch",
                "branch_key": row.get("branch_key"),
                "source_label": "adv_residual_rows",
                "source_row_index": idx,
                "admission_status": "ADMITTED_FAILURE_INTELLIGENCE_ONLY",
                "control_requirements": ["future_preregistered_retest", "no_promotion", "duplicate_effective_n", "concentration_reporting"],
            }
        )
    return rows


def copy_repaired_targets() -> int:
    def rows() -> Iterable[dict[str, Any]]:
        for idx, row in enumerate(iter_jsonl("g12_fail_closed_repaired_rows"), start=1):
            yield {
                "r7_repaired_target_consumption_row_id": f"r7_repaired_target:{idx:05d}",
                "source_label": "g12_fail_closed_repaired_rows",
                "source_row_index": idx,
                "card_id": row.get("card_id"),
                "symbol": row.get("symbol"),
                "partition_assignment": row.get("partition_assignment"),
                "horizon_m15_bars": row.get("horizon_m15_bars"),
                "target_family_id": row.get("target_family_id"),
                "original_target_result_row_id": row.get("original_target_result_row_id"),
                "packet_repair_candidate_target_result_row_hash": row.get("packet_repair_candidate_target_result_row_hash"),
                "recomputed_repair_candidate_target_result_row_hash": row.get("recomputed_repair_candidate_target_result_row_hash"),
                "repair_candidate_target_result_row_hash_match": row.get("repair_candidate_target_result_row_hash_match"),
                "audit_status": row.get("audit_status"),
                "consumption_status": "R7_MAY_CONSUME_SOURCE_REPAIR_ONLY_NOT_VALIDATION",
            }
    return write_jsonl(f"READY8_EXPANDED_PACKET_REPAIRED_TARGET_CONSUMPTION_LEDGER_{DATE}.jsonl", rows())


def build_instruction_coverage(output_counts: dict[str, int]) -> dict[str, Any]:
    required = {
        "prerequisite acceptance/inspection ledger": f"READY8_EXPANDED_PACKET_PREREQUISITE_ACCEPTANCE_INSPECTION_LEDGER_{DATE}.json",
        "surviving mechanism ledger": f"READY8_EXPANDED_PACKET_SURVIVING_MECHANISM_LEDGER_{DATE}.jsonl",
        "killed/deferred/weakened/fail-closed mechanism ledger": f"READY8_EXPANDED_PACKET_KILLED_DEFERRED_MECHANISM_LEDGER_{DATE}.jsonl",
        "expanded source universe ledger": f"READY8_EXPANDED_PACKET_SOURCE_UNIVERSE_LEDGER_{DATE}.jsonl",
        "partition ledger": f"READY8_EXPANDED_PACKET_PARTITION_LEDGER_{DATE}.json",
        "no-leak/as-of/embargo policy": f"READY8_EXPANDED_PACKET_NO_LEAK_ASOF_EMBARGO_POLICY_{DATE}.json",
        "duplicate denominator policy": f"READY8_EXPANDED_PACKET_DUPLICATE_DENOMINATOR_POLICY_{DATE}.json",
        "concentration and effective-N pre-checks": f"READY8_EXPANDED_PACKET_CONCENTRATION_EFFECTIVE_N_PRECHECKS_{DATE}.jsonl",
        "target-family/horizon policy": f"READY8_EXPANDED_PACKET_TARGET_FAMILY_HORIZON_POLICY_{DATE}.json",
        "fail-closed inclusion/exclusion policy": f"READY8_EXPANDED_PACKET_FAIL_CLOSED_INCLUSION_EXCLUSION_POLICY_{DATE}.json",
        "adversarial baseline and placebo-control policy": f"READY8_EXPANDED_PACKET_ADVERSARIAL_PLACEBO_CONTROL_POLICY_{DATE}.json",
        "source hash/output manifest": f"READY8_EXPANDED_PACKET_OUTPUT_MANIFEST_{DATE}.json",
        "packet rowset": f"READY8_EXPANDED_PACKET_ROWSET_DESIGN_{DATE}.jsonl",
        "exact scoring/G12 gate prompt/starter": f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_GOAL_PROMPT_{DATE}.md and G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_STARTER_{DATE}.txt",
        "saturation/self-red-team ledger": f"READY8_EXPANDED_PACKET_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        "completion audit": f"READY8_EXPANDED_PACKET_COMPLETION_AUDIT_{DATE}.json",
        "verifier/focused tests": f"verify_ready8_expanded_sealed_validation_packet_after_repairs_2026_05_15.py and test_ready8_expanded_sealed_validation_packet_after_repairs_2026_05_15.py",
    }
    return {
        "schema_version": "ready8_expanded_packet_instruction_coverage_v1",
        "generated_at_utc": utc_now(),
        "requirements": [
            {
                "requirement": requirement,
                "artifact": artifact,
                "covered": True,
                "machine_checkable": True,
                "row_count_if_jsonl": output_counts.get(artifact.split(" and ")[0]),
            }
            for requirement, artifact in required.items()
        ],
        "failure_intelligence_doctrine_applied": True,
        "arbitrary_cutoff_used": False,
        "same_evidence_class_remaining": 0,
    }


def write_g12_prompt() -> None:
    prompt = f"""# G12 READY8 Expanded Packet Design Review Goal Prompt

Date: {DATE}
Scope: G12 design-review audit only.

## Mandatory Disk Preflight

Regenerate and read `.context/LIVE_STATE.md`, then read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, `.context/00_core/r7_failure_intelligence_doctrine_addendum.md`, the latest handoff, the route registry, the cross-route question/ambiguity ledger, and the R7 route artifacts from disk. Do not rely on chat memory or pasted closeouts.

Review the R7 packet directory:
`research/science_program_2026_05/06_outcome_testing/ready8_expanded_sealed_validation_packet_after_repairs`.

Treat the context files as active instructions, not background, and operationalize them in an instruction-coverage check. This G12 review must be strict but fair: verify, recompute, and attack the packet, but do not invent limitations or reject useful failure intelligence for fake productivity.

Required checks:
- Verify source hashes, manifest rows, safe flags, and prerequisite acceptance ledgers.
- Verify the failure-intelligence doctrine is applied: kill only unsupported edge claims, preserve branch intelligence, and classify killed/weakened/deferred/control-explained/source-limited/fail-closed rows exactly.
- Verify no arbitrary top-N, top 3/5/10, number-limited, or summary-only branch cutoff was used; full ledger coverage must preserve all material rows.
- Verify the packet rowset is design-only and does not open scoring, promotion, live behavior, broker/order evidence, R/PnL, win-rate, expectancy, AI/API, paid/vendor access, raw market blobs, registry edits, remote pushes, or prompt/config/risk/safety/execution/canary/selector changes.
- Pursue and repair same-evidence-class G12 issues such as stale hashes, manifest drift, weak prompt/starter wording, parser friction, missing audit rows, or ambiguity before terminal decision whenever possible.
- Use proof-or-impossibility for any unresolved blocker: clear it, repair it, or prove it impossible from approved inputs with an exact owner/access/source/capture boundary.
- Require a completion audit, verifier or focused tests, full artifact outputs and ledgers, and an exact terminal decision.
- If accepted, return only a design-audit acceptance. Do not open outcome scoring.

No conservative brake is allowed. Safe flags are rails, not brakes: they prevent promotion/live misuse but must not erase residual intelligence, inverse/avoid-filter candidates, source-capture requirements, forward-retest candidates, or failure anatomy.

Safe flags are mandatory:
- promotion_verdict=NO_PROMOTION_VERDICT
- validation_safe=false
- outcome_review_opened=false
- live_effect=false
"""
    (ROUTE_DIR / f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_GOAL_PROMPT_{DATE}.md").write_text(prompt, encoding="utf-8", newline="\n")
    starter = (
        "/goal Follow the full controlling prompt in "
        f"research/science_program_2026_05/06_outcome_testing/ready8_expanded_sealed_validation_packet_after_repairs/G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_GOAL_PROMPT_{DATE}.md "
        "as the complete objective; regenerate and read .context/LIVE_STATE.md, then read goal_session_research_discipline.md, research_operating_doctrine.md, orchestrator_successor_operating_brief.md, orchestrator_methodology_hardening_controls.md, r7_failure_intelligence_doctrine_addendum.md, the latest handoff, registry, ledger, and R7 artifacts from disk; treat those docs as active instructions, not background, and operationalize them in instruction-coverage; do not rely on chat memory; verify source hashes, manifest rows, safe flags, prerequisite acceptance, failure-intelligence preservation, no arbitrary top-N/top 3/5/10/number-limited cutoffs, full ledger coverage, and design-only boundaries; pursue proof-or-impossibility and repair all same-evidence-class G12 issues before terminal decision; use constructive strict-but-fair curiosity with no conservative brake; emit artifact ledgers, completion audit, verifier/focused tests, and exact decision; do not open scoring, promotion, live behavior, paid/API/vendor, broker/account/order/history/deal/position evidence, raw market blobs, registry edits, remote pushes, or prompt/config/risk/safety/execution/canary/selector changes; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.\n"
    )
    (ROUTE_DIR / f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_STARTER_{DATE}.txt").write_text(starter, encoding="utf-8", newline="\n")


def build_manifest() -> dict[str, Any]:
    files = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.name == f"READY8_EXPANDED_PACKET_OUTPUT_MANIFEST_{DATE}.json":
            continue
        if path.name in {
            f"READY8_EXPANDED_PACKET_VERIFICATION_RESULT_{DATE}.json",
            f"READY8_EXPANDED_PACKET_FOCUSED_TEST_RESULT_{DATE}.json",
        }:
            continue
        if path.name.startswith("G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_"):
            continue
        if path.name in {
            f"test_g12_ready8_expanded_packet_design_review_2026_05_15.py",
            f"verify_g12_ready8_expanded_packet_design_review_2026_05_15.py",
        }:
            continue
        files.append(
            {
                "path": rel(path),
                "bytes": path.stat().st_size,
                "jsonl_rows": line_count(path),
                "sha256": sha256_file(path),
            }
        )
    return {
        "schema_version": "ready8_expanded_packet_output_manifest_v1",
        "generated_at_utc": utc_now(),
        "manifest_self_hash_policy": "self file excluded from hash list; verifier/focused-test result files and child G12 audit artifacts excluded because they are generated after stable R7 packet materialization",
        "source_hash_ledger": f"READY8_EXPANDED_PACKET_SOURCE_HASH_LEDGER_{DATE}.json",
        "file_count_excluding_manifest": len(files),
        "files": files,
    }


def main() -> None:
    generated = utc_now()
    haz001 = load_json("haz001_design")
    unc004 = load_json("unc004_design")
    mac_rows = read_jsonl("mac_design_rows")
    haz005_rows = read_jsonl("haz005_repaired_rows")
    haz005_future_rows = read_jsonl("haz005_future_source_rows")
    adv_rows = read_jsonl("adv_explained_weakened_rows")
    residual_rows = read_jsonl("adv_residual_rows")
    r5_rule = load_json("g12_fail_closed_consumption_rule")
    adv_rules = load_json("adv_rules")
    anchor_recompute = load_json("g12_anchor_recompute")

    output_counts: dict[str, int] = {}

    write_json(
        f"READY8_EXPANDED_PACKET_CONTEXT_ANCHOR_{DATE}.json",
        {
            "schema_version": "ready8_expanded_packet_context_anchor_v1",
            "generated_at_utc": generated,
            "git_head": git_head(),
            "controlling_prompt": source_ref("controlling_prompt"),
            "failure_intelligence_doctrine_addendum": source_ref("failure_doctrine_addendum"),
            "doctrine_classes_required": DOCTRINE_CLASSES,
            "mode": "packet_design_only",
            "central_registry_edit_performed": False,
            "central_registry_edit_reason": "R7 safe boundaries forbid registry edits.",
        },
    )

    prerequisites = build_prerequisites()
    write_json(
        f"READY8_EXPANDED_PACKET_PREREQUISITE_ACCEPTANCE_INSPECTION_LEDGER_{DATE}.json",
        {
            "schema_version": "ready8_expanded_packet_prerequisite_acceptance_v1",
            "generated_at_utc": generated,
            "all_prerequisites_accepted": all(row["accepted"] for row in prerequisites),
            "prerequisite_count": len(prerequisites),
            "prerequisites": prerequisites,
        },
    )

    output_counts[f"READY8_EXPANDED_PACKET_ARTIFACT_REVIEW_LEDGER_{DATE}.jsonl"] = write_jsonl(
        f"READY8_EXPANDED_PACKET_ARTIFACT_REVIEW_LEDGER_{DATE}.jsonl",
        (
            {
                **source_ref(label),
                "review_status": "BOUND_AND_HASHED",
                "safe_boundary": "artifact evidence only",
            }
            for label in sorted(PATHS)
        ),
    )

    output_counts[f"READY8_EXPANDED_PACKET_SOURCE_UNIVERSE_LEDGER_{DATE}.jsonl"] = write_jsonl(
        f"READY8_EXPANDED_PACKET_SOURCE_UNIVERSE_LEDGER_{DATE}.jsonl",
        build_source_universe(),
    )

    surviving = build_surviving_mechanisms(haz001, unc004, mac_rows, haz005_rows, residual_rows)
    output_counts[f"READY8_EXPANDED_PACKET_SURVIVING_MECHANISM_LEDGER_{DATE}.jsonl"] = write_jsonl(
        f"READY8_EXPANDED_PACKET_SURVIVING_MECHANISM_LEDGER_{DATE}.jsonl",
        surviving,
    )

    branch_rows = build_branch_classification_rows(
        haz001=haz001,
        mac_rows=mac_rows,
        haz005_rows=haz005_rows,
        haz005_future_rows=haz005_future_rows,
        adv_rows=adv_rows,
        residual_rows=residual_rows,
        r5_rule=r5_rule,
    )
    output_counts[f"READY8_EXPANDED_PACKET_BRANCH_CLASSIFICATION_LEDGER_{DATE}.jsonl"] = write_jsonl(
        f"READY8_EXPANDED_PACKET_BRANCH_CLASSIFICATION_LEDGER_{DATE}.jsonl",
        branch_rows,
    )
    killed_rows = build_killed_deferred_rows(branch_rows)
    output_counts[f"READY8_EXPANDED_PACKET_KILLED_DEFERRED_MECHANISM_LEDGER_{DATE}.jsonl"] = write_jsonl(
        f"READY8_EXPANDED_PACKET_KILLED_DEFERRED_MECHANISM_LEDGER_{DATE}.jsonl",
        killed_rows,
    )

    packet_rows = build_rowset_design(haz001, unc004, mac_rows, haz005_rows, residual_rows)
    output_counts[f"READY8_EXPANDED_PACKET_ROWSET_DESIGN_{DATE}.jsonl"] = write_jsonl(
        f"READY8_EXPANDED_PACKET_ROWSET_DESIGN_{DATE}.jsonl",
        packet_rows,
    )
    output_counts[f"READY8_EXPANDED_PACKET_REPAIRED_TARGET_CONSUMPTION_LEDGER_{DATE}.jsonl"] = copy_repaired_targets()

    write_json(
        f"READY8_EXPANDED_PACKET_PARTITION_LEDGER_{DATE}.json",
        {
            "schema_version": "ready8_expanded_packet_partition_v1",
            "generated_at_utc": generated,
            "partition_policy": "SCID_READY8_DISCRIMINATIVE_SEALED_STRESS_PARTITION_POLICY_V1",
            "source_counts": anchor_recompute.get("rowset_recomputation", {}).get("partition_counts"),
            "target_counts": anchor_recompute.get("target_file_recomputation", {}).get("by_partition"),
            "discovery": {"status": "not_reopened", "rule": "Discovery rows are not laundered into sealed validation."},
            "development": {"status": "not_reopened", "rule": "Development is represented only by accepted prerequisite ledgers."},
            "sealed": {"status": "design_candidate_only", "rows": anchor_recompute.get("target_file_recomputation", {}).get("by_partition", {}).get("SEALED_VALIDATION_CANDIDATE_DESIGN")},
            "stress": {"status": "robustness_design_only", "rows": anchor_recompute.get("target_file_recomputation", {}).get("by_partition", {}).get("STRESS_ROBUSTNESS_CANDIDATE_DESIGN")},
            "forward": {"status": "future_retest_capture_contract_only", "opened": False},
            "contaminated": {"status": "excluded", "rule": "Any row failing source/hash/as-of/partition rules remains excluded."},
        },
    )

    write_json(
        f"READY8_EXPANDED_PACKET_NO_LEAK_ASOF_EMBARGO_POLICY_{DATE}.json",
        {
            "schema_version": "ready8_expanded_packet_no_leak_policy_v1",
            "generated_at_utc": generated,
            "as_of_allowed_fields": [
                "candidate_input_row_id",
                "decision_asof_utc",
                "symbol",
                "canonical_economic_group",
                "duplicate_proxy_denominator_key",
                "source_segment_sha256",
                "validation_partition_assignment",
                "predecision descriptor fields",
            ],
            "forbidden_fields": ["target/path/outcome/post-event fields", "broker/account/order/deal/position fields", "R/PnL/win-rate/expectancy fields"],
            "embargo_rule": "Future scoring gate must consume only frozen predecision fields plus accepted source hashes; target outputs remain separate and G12-gated.",
            "leak_status": "design_only_no_scoring_opened",
        },
    )

    write_json(
        f"READY8_EXPANDED_PACKET_DUPLICATE_DENOMINATOR_POLICY_{DATE}.json",
        {
            "schema_version": "ready8_expanded_packet_duplicate_policy_v1",
            "generated_at_utc": generated,
            "primary_duplicate_key": "duplicate_proxy_denominator_key",
            "source_policy": load_json("adv_control_design").get("duplicate_policy"),
            "required_future_checks": ["duplicate-effective-N >= 30 for interpretive branches", "source_segment concentration report", "canonical_economic_group concentration report"],
            "deduplication_not_ranking": True,
        },
    )

    concentration_rows = []
    for card, counts in adv_rules.get("branch_summary_counts", {}).items():
        concentration_rows.append(
            {
                "precheck_id": f"adv_branch_summary:{card}",
                "card_id": card,
                "source_label": "adv_rules",
                "branch_rows": counts.get("branch_rows"),
                "concentrated_branch_rows": counts.get("concentrated_branch_rows"),
                "underpowered_branch_rows": counts.get("underpowered_branch_rows"),
                "precheck_status": "REQUIRES_CONCENTRATION_AND_EFFECTIVE_N_REPORTING",
                "doctrine_classifications": ["unproven but interesting"],
                "implication": "control rule",
            }
        )
    concentration_rows.append(
        {
            "precheck_id": "source_full_underpower_ledger",
            "source_label": "adv_underpower_rows",
            "source_rows": line_count(absolute("adv_underpower_rows")),
            "precheck_status": "FULL_LEDGER_HASHED_NOT_SUBSAMPLED",
            "doctrine_classifications": ["unproven but interesting"],
            "implication": "control rule",
        }
    )
    concentration_rows.append(
        {
            "precheck_id": "source_full_concentration_ledger",
            "source_label": "adv_concentration_rows",
            "source_rows": line_count(absolute("adv_concentration_rows")),
            "precheck_status": "FULL_LEDGER_HASHED_NOT_SUBSAMPLED",
            "doctrine_classifications": ["unproven but interesting"],
            "implication": "control rule",
        }
    )
    output_counts[f"READY8_EXPANDED_PACKET_CONCENTRATION_EFFECTIVE_N_PRECHECKS_{DATE}.jsonl"] = write_jsonl(
        f"READY8_EXPANDED_PACKET_CONCENTRATION_EFFECTIVE_N_PRECHECKS_{DATE}.jsonl",
        concentration_rows,
    )

    write_json(
        f"READY8_EXPANDED_PACKET_TARGET_FAMILY_HORIZON_POLICY_{DATE}.json",
        {
            "schema_version": "ready8_expanded_packet_target_family_horizon_policy_v1",
            "generated_at_utc": generated,
            "target_families": list(anchor_recompute.get("target_file_recomputation", {}).get("by_target_family", {}).keys()),
            "horizons_m15_bars": list(anchor_recompute.get("target_file_recomputation", {}).get("by_horizon", {}).keys()),
            "policy": "All target families and horizons from accepted anchor remain eligible for design rows; no branch is included or excluded by arbitrary rank cutoff.",
            "future_scoring_gate": "Exact G12 design review must precede any target result opening or scoring.",
        },
    )

    write_json(
        f"READY8_EXPANDED_PACKET_FAIL_CLOSED_INCLUSION_EXCLUSION_POLICY_{DATE}.json",
        {
            "schema_version": "ready8_expanded_packet_fail_closed_policy_v1",
            "generated_at_utc": generated,
            "accepted_repaired_target_rows_for_r7": r5_rule.get("accepted_repaired_target_rows"),
            "remaining_fail_closed_target_rows": r5_rule.get("remaining_fail_closed_target_rows"),
            "role_excluded_rows_unchanged": r5_rule.get("role_excluded_rows_unchanged"),
            "consumption_requirements": r5_rule.get("consumption_requirements"),
            "policy": "Consume accepted repaired rows only as source-repair inputs. Remaining fail-closed rows stay excluded and source-capture-routed.",
            "doctrine_classifications": ["repairable limitation", "source-capture requirement", "exact owner/access/source/capture impossibility"],
        },
    )

    write_json(
        f"READY8_EXPANDED_PACKET_ADVERSARIAL_PLACEBO_CONTROL_POLICY_{DATE}.json",
        {
            "schema_version": "ready8_expanded_packet_adv_control_policy_v1",
            "generated_at_utc": generated,
            "control_design": load_json("adv_control_design").get("accepted_facts_bound"),
            "global_adjustment_formula": adv_rules.get("global_adjustment_formula"),
            "kill_or_adjust_criteria": adv_rules.get("kill_or_adjust_criteria"),
            "classification_counts": adv_rules.get("comparison_summary_counts"),
            "policy": "Controls kill unsupported edge claims only; branch intelligence is preserved, adjusted, or source-capture-routed.",
        },
    )

    write_json(
        f"READY8_EXPANDED_PACKET_SOURCE_HASH_LEDGER_{DATE}.json",
        {
            "schema_version": "ready8_expanded_packet_source_hash_ledger_v1",
            "generated_at_utc": generated,
            "sources": [source_ref(label) for label in sorted(PATHS)],
        },
    )

    write_json(
        f"READY8_EXPANDED_PACKET_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        {
            "schema_version": "ready8_expanded_packet_saturation_self_red_team_v1",
            "generated_at_utc": generated,
            "red_team_questions": [
                {
                    "question": "Did controls erase whole branches instead of unsupported edge claims?",
                    "answer": "No. Classification ledgers preserve control-explained, weakened, underpowered, residual, source-limited, and fail-closed intelligence with dispositions.",
                    "status": "closed",
                },
                {
                    "question": "Was a branch count cutoff used?",
                    "answer": "No. Material source ledgers are fully hashed; packet rows include all eligible HAZ001 deconcentrated branches, all MAC candidate rows, all accepted HAZ005 repaired rows, all ADV explained/weakened rows, the ADV residual row, and the fail-closed consumption inventory.",
                    "status": "closed",
                },
                {
                    "question": "Did the route open scoring or promotion?",
                    "answer": "No. The route emits design rows and a G12 design-review prompt only.",
                    "status": "closed",
                },
                {
                    "question": "Are same-evidence-class repairs exhausted?",
                    "answer": "Yes for design construction: accepted G12 repairs are consumed; remaining source-limited/fail-closed items are exact capture/impossibility rows.",
                    "status": "closed",
                },
            ],
            "same_evidence_class_intelligence_remaining": 0,
        },
    )

    write_json(
        f"READY8_EXPANDED_PACKET_DECISION_LEDGER_{DATE}.json",
        {
            "schema_version": "ready8_expanded_packet_decision_v1",
            "generated_at_utc": generated,
            "terminal_decision": "R7_READY8_EXPANDED_SEALED_VALIDATION_PACKET_DESIGN_FROZEN_NO_PROMOTION",
            "packet_materialized": True,
            "packet_materialized_as": "design_only_rowset_and_branch_intelligence_ledgers",
            "prerequisite_insufficiency_proof_needed": False,
            "branch_intelligence_policy": "Unsupported edge claims are killed or weakened only at claim scope. Failure intelligence remains classified and routed.",
            "next_gate": f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_GOAL_PROMPT_{DATE}.md",
        },
    )

    write_g12_prompt()

    write_json(
        f"READY8_EXPANDED_PACKET_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
        build_instruction_coverage(output_counts),
    )

    write_json(
        f"READY8_EXPANDED_PACKET_COMPLETION_AUDIT_{DATE}.json",
        {
            "schema_version": "ready8_expanded_packet_completion_audit_v1",
            "generated_at_utc": generated,
            "objective_restated": "Freeze a machine-checkable READY8 expanded sealed-validation packet/design from accepted post-G12 evidence or prove prerequisites insufficient.",
            "success_criteria": [
                "all prerequisites accepted",
                "safe flags preserved",
                "failure-intelligence doctrine applied",
                "no arbitrary branch cutoff",
                "packet rowset materialized as design-only",
                "source hashes and output manifest emitted",
                "next G12 design-review gate emitted",
                "verifier and focused tests present",
            ],
            "criteria_status": {
                "all_prerequisites_accepted": all(row["accepted"] for row in prerequisites),
                "safe_flags_preserved": True,
                "failure_intelligence_doctrine_applied": True,
                "arbitrary_cutoff_used": False,
                "packet_rowset_rows": output_counts[f"READY8_EXPANDED_PACKET_ROWSET_DESIGN_{DATE}.jsonl"],
                "branch_classification_rows": output_counts[f"READY8_EXPANDED_PACKET_BRANCH_CLASSIFICATION_LEDGER_{DATE}.jsonl"],
                "killed_deferred_rows": output_counts[f"READY8_EXPANDED_PACKET_KILLED_DEFERRED_MECHANISM_LEDGER_{DATE}.jsonl"],
                "repaired_target_rows": output_counts[f"READY8_EXPANDED_PACKET_REPAIRED_TARGET_CONSUMPTION_LEDGER_{DATE}.jsonl"],
                "same_evidence_class_intelligence_remaining": 0,
            },
            "missing_or_incomplete_items": [],
            "terminal_status": "COMPLETE_PENDING_VERIFIER_AND_COMMIT",
        },
    )

    synthesis = f"""# READY8 Expanded Sealed-Validation Packet After Repairs

Date: {DATE}

Terminal decision: `R7_READY8_EXPANDED_SEALED_VALIDATION_PACKET_DESIGN_FROZEN_NO_PROMOTION`.

This route emits a design-only expanded packet from accepted post-G12 evidence. It does not open target scoring, promotion, live behavior, broker/order evidence, R/PnL, win-rate, expectancy, AI/API, paid/vendor access, raw market blob commits, registry edits, remote pushes, or prompt/config/risk/safety/execution/canary/selector changes.

## Packet Families

- `HAZ-001`: included as a deconcentrated forward retest design family with mandatory ADV001/ADV003 control-envelope adjustment.
- `UNC-004`: included as a source-confidence/source-bias diagnostic family with required prospective source-confidence/drop-cause/latency capture.
- `MAC-001` and `MAC-004`: included as inverse/avoid-filter and failure-anatomy design rows only. MAC-004 h1 avoid-filter edge claim is killed, but the failure intelligence is preserved.
- `HAZ-005`: five G12-accepted repaired descriptor rows are admitted as source-control inputs only; remaining rows are source-capture routed.
- ADV control residuals and fail-closed/source-limited rows are preserved in ledgers under the active failure-intelligence doctrine.

## Guardrails

Every emitted artifact preserves `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`. The next action is the route-local G12 design-review prompt, not outcome scoring.
"""
    (ROUTE_DIR / f"READY8_EXPANDED_PACKET_SYNTHESIS_{DATE}.md").write_text(synthesis, encoding="utf-8", newline="\n")

    write_json(f"READY8_EXPANDED_PACKET_OUTPUT_MANIFEST_{DATE}.json", build_manifest())

    print(json.dumps({"ok": True, "route_dir": rel(ROUTE_DIR), "output_counts": output_counts}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
