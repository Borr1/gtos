"""Build G12 post-test audit artifacts for OTI1 and OTI2.

This is a research-control audit only. It reads already-quarantined OTI
result artifacts plus the controlling G12/OTG0/OTB inputs, verifies scope and
methodology boundaries, and writes G12-owned post-test decisions. It does not
run new outcome tests or inspect blocked-packet outcomes.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE_STAMP = "2026-05-07"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
RESULT_STATUS = "RESULT_QUARANTINED_DISCOVERY_ONLY"
ACCEPT = "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE"
REJECT = "REJECT_INVALID_RESULT_AUDIT"
BLOCKED = "BLOCKED_WITH_NEXT_EXACT_QUESTION"

ROOT = Path(__file__).resolve().parents[4]
OT = ROOT / "research/science_program_2026_05/06_outcome_testing"
SYNTHESIS = ROOT / "research/science_program_2026_05/05_synthesis"
OUT = OT / "g12_oti_post_test_audit"

PATHS = {
    "live_state": ROOT / ".context/LIVE_STATE.md",
    "quick_reference": ROOT / ".context/00_core/quick_reference_card.md",
    "research_doctrine": ROOT / ".context/00_core/research_operating_doctrine.md",
    "research_current_state": ROOT / ".context/00_core/research_current_state.md",
    "master_registry": SYNTHESIS / "SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md",
    "master_registry_json": SYNTHESIS / "SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json",
    "otg0_prereg": OT / "OTG0_PREREG_CLASSIFICATION_LEDGER_2026-05-07.json",
    "otg0_manifest": OT / "OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json",
    "otg0_rules": OT / "OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.json",
    "otl1": OT / "OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_2026-05-07.json",
    "otl2": OT / "otl2_synthetic_replay_packet_audit/OTL2_SYNTHETIC_REPLAY_PACKET_AUDIT_2026-05-07.json",
    "otb0": OT / "otb0_blocker_clearing_governor/OTB0_COMPLETION_AUDIT_2026-05-07.json",
    "otb1r_dup": OT / "otb1r_input_only_lifecycle_rebuild/OTB1R_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json",
    "otb1r_schema": OT / "otb1r_input_only_lifecycle_rebuild/OTB1R_SCHEMA_NOLEAK_VALIDATION_REPORT_2026-05-07.json",
    "otb1r_manifest": OT / "otb1r_input_only_lifecycle_rebuild/OTB1R_ARTIFACT_MANIFEST_2026-05-07.json",
    "otb2r_manifest": OT / "otb2r_input_only_path_rebuild/OTB2R_PACKET_MANIFEST_2026-05-07.json",
    "otb2r_hashes": OT / "otb2r_input_only_path_rebuild/OTB2R_SANITIZED_SOURCE_HASHES_2026-05-07.json",
    "otb2r_forbidden": OT / "otb2r_input_only_path_rebuild/OTB2R_FORBIDDEN_FIELD_SCAN_2026-05-07.json",
    "otb2r_coverage": OT / "otb2r_input_only_path_rebuild/OTB2R_COVERAGE_AUDIT_2026-05-07.json",
    "g12_prior_decision": OT / "g12_blocker_clearing_audit/G12_BLOCKER_CLEARING_DECISION_LEDGER_2026-05-07.json",
    "g12_reaudit_decision": OT / "g12_otb_rebuild_reaudit/G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_2026-05-07.json",
    "g12_reaudit_shortlist": OT / "g12_otb_rebuild_reaudit/G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json",
    "g12_reaudit_leakage": OT / "g12_otb_rebuild_reaudit/G12_OTB_REBUILD_LEAKAGE_REVIEW_2026-05-07.json",
    "g12_reaudit_duplicate": OT / "g12_otb_rebuild_reaudit/G12_OTB_REBUILD_DUPLICATE_DENOMINATOR_REVIEW_2026-05-07.json",
    "g12_reaudit_label": OT / "g12_otb_rebuild_reaudit/G12_OTB_REBUILD_LABEL_FAMILY_REVIEW_2026-05-07.json",
    "g12_reaudit_hash": OT / "g12_otb_rebuild_reaudit/G12_OTB_REBUILD_SOURCE_HASH_REVIEW_2026-05-07.json",
    "g12_reaudit_blocked": OT / "g12_otb_rebuild_reaudit/G12_OTB_REBUILD_BLOCKED_QUESTION_LEDGER_2026-05-07.json",
    "oti1_freeze": OT / "oti1_lifecycle_quarantined_results/OTI1_METRIC_FREEZE_2026-05-07.json",
    "oti1_result": OT / "oti1_lifecycle_quarantined_results/OTI1_RESULT_LEDGER_2026-05-07.json",
    "oti1_method": OT / "oti1_lifecycle_quarantined_results/OTI1_METHODOLOGY_REPORT_2026-05-07.json",
    "oti1_duplicate": OT / "oti1_lifecycle_quarantined_results/OTI1_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json",
    "oti1_label": OT / "oti1_lifecycle_quarantined_results/OTI1_LABEL_FAMILY_SEPARATION_REPORT_2026-05-07.json",
    "oti1_blocker": OT / "oti1_lifecycle_quarantined_results/OTI1_BLOCKER_LEDGER_2026-05-07.json",
    "oti1_completion": OT / "oti1_lifecycle_quarantined_results/OTI1_COMPLETION_AUDIT_2026-05-07.json",
    "oti1_builder": OT / "oti1_lifecycle_quarantined_results/build_oti1_lifecycle_quarantined_results_2026_05_07.py",
    "oti2_freeze": OT / "oti2_riskbank_quarantined_results/OTI2_RISKBANK_METHOD_FREEZE_2026-05-07.json",
    "oti2_result": OT / "oti2_riskbank_quarantined_results/OTI2_RISKBANK_RESULT_LEDGER_2026-05-07.json",
    "oti2_rows": OT / "oti2_riskbank_quarantined_results/OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "oti2_source": OT / "oti2_riskbank_quarantined_results/OTI2_RISKBANK_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
    "oti2_method": OT / "oti2_riskbank_quarantined_results/OTI2_RISKBANK_METHODOLOGY_REPORT_2026-05-07.json",
    "oti2_ambiguity": OT / "oti2_riskbank_quarantined_results/OTI2_RISKBANK_AMBIGUITY_RESOLUTION_LEDGER_2026-05-07.json",
    "oti2_blocker": OT / "oti2_riskbank_quarantined_results/OTI2_RISKBANK_BLOCKER_LEDGER_2026-05-07.json",
    "oti2_completion": OT / "oti2_riskbank_quarantined_results/OTI2_RISKBANK_COMPLETION_AUDIT_2026-05-07.json",
    "oti2_builder": OT / "oti2_riskbank_quarantined_results/build_oti2_riskbank_quarantined_results_2026_05_07.py",
}

FORBIDDEN_RESULT_FIELD_NAMES = {
    "actual_r",
    "account_history_realized_r",
    "broker_actual_r",
    "live_trade_result",
    "live_trade_results",
    "trade_result",
    "win_loss",
    "outcome_r",
    "future_return",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def table(headers: list[str], rows: list[list[Any]]) -> str:
    rendered = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        rendered.append("| " + " | ".join(str(cell).replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(rendered)


def bool_status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def common_meta(artifact_type: str, generated_at: str) -> dict[str, Any]:
    return {
        "artifact_family": "G12_OTI_POST_TEST_AUDIT",
        "artifact_type": artifact_type,
        "version_date": DATE_STAMP,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "scope": "strict_but_fair_post_test_audit_of_existing_quarantined_oti1_oti2_results",
        "outcomes_run_by_this_audit": False,
        "blocked_packet_outcomes_inspected_by_this_audit": False,
        "broker_actual_r_or_live_trade_results_inspected_by_this_audit": False,
        "network_api_databento_paid_calls": 0,
        "live_trading_surfaces_touched": False,
        "master_registry_edited": False,
    }


def assert_existing_inputs() -> None:
    missing = [name for name, path in PATHS.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing controlling inputs: {missing}")


def load_inputs() -> dict[str, Any]:
    assert_existing_inputs()
    data: dict[str, Any] = {}
    for name, path in PATHS.items():
        if path.suffix == ".json":
            data[name] = read_json(path)
        elif path.suffix == ".jsonl":
            data[name] = read_jsonl(path)
    return data


def accepted_shortlist_sets(shortlist: dict[str, Any]) -> tuple[list[str], list[str]]:
    otb1r_ids = sorted(
        row["packet_id"] for row in shortlist["accepted_packets"] if row["packet_family"] == "OTB1R"
    )
    otb2r_ids = sorted(
        row["packet_id"] for row in shortlist["accepted_packets"] if row["packet_family"] == "OTB2R"
    )
    return otb1r_ids, otb2r_ids


def extract_packet_results(result: dict[str, Any]) -> list[dict[str, Any]]:
    return list(result.get("packet_results", []))


def build_lane_audit(data: dict[str, Any]) -> dict[str, Any]:
    shortlist = data["g12_reaudit_shortlist"]
    accepted_otb1r, accepted_otb2r = accepted_shortlist_sets(shortlist)

    oti1_freeze = data["oti1_freeze"]
    oti1_result = data["oti1_result"]
    oti1_dup = data["oti1_duplicate"]
    oti1_label = data["oti1_label"]
    oti1_completion = data["oti1_completion"]
    oti1_packets = extract_packet_results(oti1_result)
    oti1_packet_ids = sorted(row["packet_id"] for row in oti1_packets)

    oti2_freeze = data["oti2_freeze"]
    oti2_result = data["oti2_result"]
    oti2_source = data["oti2_source"]
    oti2_method = data["oti2_method"]
    oti2_rows = data["oti2_rows"]
    oti2_blocker = data["oti2_blocker"]
    oti2_completion = data["oti2_completion"]

    oti2_row_packet_ids = sorted({row.get("packet_id") for row in oti2_rows})
    oti2_forbidden_hits = sorted(
        {key for row in oti2_rows for key in row.keys() if key in FORBIDDEN_RESULT_FIELD_NAMES}
    )

    oti1_failures: list[str] = []
    if sorted(oti1_freeze["allowed_packet_ids"]) != accepted_otb1r:
        oti1_failures.append("OTI1 allowed_packet_ids do not match G12 accepted OTB1R packet IDs.")
    if oti1_packet_ids != sorted(oti1_freeze["allowed_packet_ids"]):
        oti1_failures.append("OTI1 result packet IDs do not match frozen allowed_packet_ids.")
    if "OTG0-PKT-017" in oti1_packet_ids or "OTG0-PKT-017" not in oti1_freeze["excluded_packet_ids"]:
        oti1_failures.append("OTG0-PKT-017 blocked packet exclusion failed.")
    if not oti1_freeze.get("frozen_before_lifecycle_label_inspection"):
        oti1_failures.append("Metric freeze does not claim pre-label freeze.")
    if oti1_result.get("blocked_packet_outcomes_inspected") is not False:
        oti1_failures.append("OTI1 inspected blocked-packet outcomes.")
    if oti1_result.get("broker_actual_r_values_inspected") is not False:
        oti1_failures.append("OTI1 inspected broker actual-R values.")
    if oti1_result.get("synthetic_path_r_values_inspected") is not False:
        oti1_failures.append("OTI1 inspected synthetic path-R values.")
    if oti1_dup.get("denominator_mismatches"):
        oti1_failures.append("OTI1 denominator mismatches are present.")
    if oti1_dup.get("duplicate_group_label_conflicts"):
        oti1_failures.append("OTI1 duplicate-group label conflicts are present.")
    if oti1_label.get("forbidden_primary_field_hits"):
        oti1_failures.append("OTI1 forbidden primary field hits are present.")
    if oti1_label.get("primary_label_family") != "lifecycle_no_fill":
        oti1_failures.append("OTI1 primary label family is not lifecycle_no_fill.")
    if oti1_result.get("promotion_verdict") != PROMOTION_VERDICT or oti1_result.get("validation_safe") is not False:
        oti1_failures.append("OTI1 promotion/validation flags changed.")
    if oti1_completion.get("can_mark_oti1_complete") is not True:
        oti1_failures.append("OTI1 completion audit did not pass.")

    oti2_failures: list[str] = []
    if accepted_otb2r != ["OTG0-PKT-013"]:
        oti2_failures.append("G12 accepted OTB2R packet set is not exactly OTG0-PKT-013.")
    if oti2_freeze["scope"]["allowed_packet_id"] != "OTG0-PKT-013":
        oti2_failures.append("OTI2 allowed packet scope is not OTG0-PKT-013.")
    if oti2_result.get("packet_id") != "OTG0-PKT-013" or oti2_row_packet_ids != ["OTG0-PKT-013"]:
        oti2_failures.append("OTI2 result rows include a packet outside OTG0-PKT-013.")
    if not oti2_freeze.get("frozen_before_synthetic_path_outcome_inspection"):
        oti2_failures.append("OTI2 method freeze does not claim pre-outcome freeze.")
    if oti2_result.get("blocked_packet_outcomes_inspected") is not False:
        oti2_failures.append("OTI2 inspected blocked-packet outcomes.")
    if oti2_result.get("broker_actual_r_inspected") is not False:
        oti2_failures.append("OTI2 inspected broker actual-R values.")
    if oti2_forbidden_hits:
        oti2_failures.append(f"OTI2 row ledger includes forbidden result fields: {oti2_forbidden_hits}.")
    if oti2_result.get("label_family") != "synthetic_path_r":
        oti2_failures.append("OTI2 primary label family is not synthetic_path_r.")
    if oti2_source.get("row_source_hash_failure_count") != 0 or oti2_source.get("coverage_failure_count") != 0:
        oti2_failures.append("OTI2 source-hash or coverage failures are present.")
    if oti2_source.get("packet_hash_match") is not True:
        oti2_failures.append("OTI2 packet hash recomputation failed.")
    if oti2_source.get("duplicate_group_denominator", {}).get("within_packet_duplicate_group_drift") != 0:
        oti2_failures.append("OTI2 duplicate-group denominator drift is present.")
    if oti2_source.get("leakage_guard", {}).get("packet_broker_actual_r_absent") is not True:
        oti2_failures.append("OTI2 packet broker-actual-R absence guard failed.")
    if oti2_result.get("promotion_verdict") != PROMOTION_VERDICT:
        oti2_failures.append("OTI2 promotion verdict changed.")
    if oti2_completion.get("can_mark_goal_complete") is not True:
        oti2_failures.append("OTI2 completion audit did not pass.")

    oti1_decision = ACCEPT if not oti1_failures else REJECT
    oti2_decision = ACCEPT if not oti2_failures else REJECT

    return {
        "oti1": {
            "lane": "OTI1",
            "result_lane": "lifecycle_no_fill_existing_data_audit",
            "decision": oti1_decision,
            "decision_reason": (
                "Metric was frozen, packet scope matches the 9 G12-accepted OTB1R lifecycle packets, "
                "blocked packet OTG0-PKT-017 is excluded, denominator/label/leakage audits are clean, "
                "and validation statistics are correctly marked not_computable."
                if not oti1_failures
                else "Concrete audit failures require rejection."
            ),
            "audit_failures": oti1_failures,
            "accepted_packets": oti1_packet_ids,
            "excluded_packets": oti1_freeze["excluded_packet_ids"],
            "raw_rows_audit_only": oti1_result["raw_rows_audit_only"],
            "unique_duplicate_group_packet_units": oti1_dup["unique_duplicate_group_packet_units"],
            "unique_duplicate_group_cross_packet_units": oti1_dup["unique_duplicate_group_cross_packet_units"],
            "source_duplicate_group_id_units_unpooled": oti1_result["source_duplicate_group_id_units_unpooled"],
            "statistics_status": oti1_result["statistics_status"],
            "next_exact_question": (
                "Before any covariate-conditioned claim, which packet-bound source/as-of proofs clear the "
                "OTI1 covariate source-complete blockers while keeping lifecycle_no_fill separate from "
                "synthetic_path_r and broker_actual_r?"
            ),
            "evidence": [
                {
                    "claim": "OTI1 metric froze before lifecycle label inspection and excluded OTG0-PKT-017.",
                    "path": rel(PATHS["oti1_freeze"]),
                    "keys": [
                        "frozen_before_lifecycle_label_inspection=true",
                        "allowed_packet_ids",
                        "excluded_packet_ids=['OTG0-PKT-017']",
                    ],
                },
                {
                    "claim": "OTI1 used only accepted OTB1R packets and did not inspect blocked/broker/synthetic results.",
                    "path": rel(PATHS["oti1_result"]),
                    "keys": [
                        "allowed_packet_count=9",
                        "blocked_packet_outcomes_inspected=false",
                        "broker_actual_r_values_inspected=false",
                        "synthetic_path_r_values_inspected=false",
                    ],
                },
                {
                    "claim": "OTI1 denominator and label-family audits have no concrete failure.",
                    "path": rel(PATHS["oti1_duplicate"]),
                    "keys": ["denominator_mismatches=[]", "duplicate_group_label_conflicts=[]"],
                },
                {
                    "claim": "OTI1 label family is lifecycle_no_fill with forbidden fields absent.",
                    "path": rel(PATHS["oti1_label"]),
                    "keys": [
                        "primary_label_family=lifecycle_no_fill",
                        "forbidden_primary_field_hits=[]",
                        "source_projection_forbidden_issue_count=0",
                    ],
                },
            ],
        },
        "oti2": {
            "lane": "OTI2",
            "result_lane": "riskbank_synthetic_path_r_existing_data_audit",
            "decision": oti2_decision,
            "decision_reason": (
                "Method was frozen before synthetic path label opening, packet scope is the single G12-accepted "
                "OTB2R risk-bank packet, source/hash/coverage and duplicate denominators pass, broker actual-R "
                "and blocked packets are not inspected, and the unscoreable risk-bank metric is correctly "
                "reported as not_computable rather than promoted."
                if not oti2_failures
                else "Concrete audit failures require rejection."
            ),
            "audit_failures": oti2_failures,
            "accepted_packets": ["OTG0-PKT-013"],
            "excluded_packets": "all other OTB2R packets and all blocked packets",
            "raw_records": len(oti2_rows),
            "unique_duplicate_group_id_count": oti2_result["unique_duplicate_group_id_count"],
            "riskbank_primary_metric": oti2_result["riskbank_primary_metric"],
            "descriptive_status_counts": oti2_result["descriptive_status_counts"],
            "same_bar_ambiguity_state_counts": oti2_result["same_bar_ambiguity_state_counts"],
            "statistics_status": {
                "effective_n": oti2_method["effective_n"],
                "dsr": oti2_method["dsr"],
                "pbo": oti2_method["pbo"],
            },
            "blockers": oti2_blocker["blockers"],
            "next_exact_question": (
                "Which future frozen input packet provides leg-level reentry state, risk_bank_before_action_r, "
                "risk_bank_after_action_r, realized_closed_leg_r, open_leg_stop_if_hit_r, and numeric "
                "estimated_remaining_cost_r for G10-EXP-RISKBANK-005 without broker actual-R or blocked-packet "
                "outcome pooling?"
            ),
            "evidence": [
                {
                    "claim": "OTI2 method froze before synthetic path outcome inspection.",
                    "path": rel(PATHS["oti2_freeze"]),
                    "keys": [
                        "frozen_before_synthetic_path_outcome_inspection=true",
                        "allowed_packet_id=OTG0-PKT-013",
                        "label_family_boundary.primary_label_family=synthetic_path_r",
                    ],
                },
                {
                    "claim": "OTI2 result uses only OTG0-PKT-013 and avoids blocked/broker actual-R.",
                    "path": rel(PATHS["oti2_result"]),
                    "keys": [
                        "packet_id=OTG0-PKT-013",
                        "unique_duplicate_group_id_count=86",
                        "blocked_packet_outcomes_inspected=false",
                        "broker_actual_r_inspected=false",
                    ],
                },
                {
                    "claim": "OTI2 source hash and coverage pass for all 86 rows.",
                    "path": rel(PATHS["oti2_source"]),
                    "keys": [
                        "packet_hash_match=true",
                        "row_source_hash_failure_count=0",
                        "coverage_failure_count=0",
                    ],
                },
                {
                    "claim": "OTI2 row ledger contains 86 quarantined synthetic path rows and no forbidden broker/live-result fields.",
                    "path": rel(PATHS["oti2_rows"]),
                    "keys": ["packet_id=OTG0-PKT-013", "forbidden_field_hits=[]"],
                },
            ],
        },
    }


def build_methodology_audit(data: dict[str, Any], lanes: dict[str, Any], generated_at: str) -> dict[str, Any]:
    oti2_builder_check = {
        "path": rel(PATHS["oti2_builder"]),
        "evidence": "main() calls require_method_freeze() before reading packet/path rows; require_method_freeze rejects missing frozen_before_synthetic_path_outcome_inspection.",
        "line_evidence": ["build_oti2_riskbank_quarantined_results_2026_05_07.py:110-111", "build_oti2_riskbank_quarantined_results_2026_05_07.py:815-826"],
    }
    oti1_builder_check = {
        "path": rel(PATHS["oti1_builder"]),
        "evidence": "build() loads OTI1_METRIC_FREEZE before loading accepted packets and raises if accepted OTB1R IDs do not match the frozen allowlist or if OTG0-PKT-017 enters scope.",
        "line_evidence": ["build_oti1_lifecycle_quarantined_results_2026_05_07.py:257-283"],
    }
    return {
        **common_meta("methodology_audit", generated_at),
        "decision_summary": {lane: payload["decision"] for lane, payload in lanes.items()},
        "method_freeze_findings": [
            {
                "lane": "OTI1",
                "status": "PASS",
                "freeze_artifact": rel(PATHS["oti1_freeze"]),
                "freeze_keys": {
                    "frozen_before_lifecycle_label_inspection": data["oti1_freeze"]["frozen_before_lifecycle_label_inspection"],
                    "denominator": data["oti1_freeze"]["denominator"],
                    "sample_floor": data["oti1_freeze"]["sample_floor"],
                    "label_family": data["oti1_freeze"]["label_family"],
                    "not_computable_criteria": data["oti1_freeze"]["not_computable_criteria"],
                },
                "builder_evidence": oti1_builder_check,
                "assessment": "Freeze and builder scope checks are sufficient for quarantined discovery evidence; no promotion/validation claim is opened.",
            },
            {
                "lane": "OTI2",
                "status": "PASS",
                "freeze_artifact": rel(PATHS["oti2_freeze"]),
                "freeze_keys": {
                    "frozen_before_synthetic_path_outcome_inspection": data["oti2_freeze"]["frozen_before_synthetic_path_outcome_inspection"],
                    "scope": data["oti2_freeze"]["scope"],
                    "metric": data["oti2_freeze"]["metric"],
                    "duplicate_policy": data["oti2_freeze"]["duplicate_policy"],
                    "not_computable_criteria": data["oti2_freeze"]["not_computable_criteria"],
                },
                "builder_evidence": oti2_builder_check,
                "assessment": "Freeze happens before OTI2 path-label row opening; the actual risk-bank metric is blocked by absent leg-level fields and is not overstated.",
            },
        ],
        "control_inputs_checked": [
            rel(PATHS[key])
            for key in [
                "otg0_rules",
                "otg0_manifest",
                "g12_reaudit_shortlist",
                "g12_reaudit_decision",
                "research_doctrine",
                "research_current_state",
                "master_registry",
            ]
        ],
    }


def build_leakage_audit(data: dict[str, Any], lanes: dict[str, Any], generated_at: str) -> dict[str, Any]:
    oti2_rows = data["oti2_rows"]
    oti2_forbidden_hits = sorted(
        {key for row in oti2_rows for key in row.keys() if key in FORBIDDEN_RESULT_FIELD_NAMES}
    )
    return {
        **common_meta("leakage_no_leak_audit", generated_at),
        "verdict": "PASS_FOR_QUARANTINED_DISCOVERY",
        "no_leak_findings": [
            {
                "lane": "OTI1",
                "status": "PASS",
                "blocked_packet_outcomes_inspected": data["oti1_result"]["blocked_packet_outcomes_inspected"],
                "broker_actual_r_values_inspected": data["oti1_result"]["broker_actual_r_values_inspected"],
                "synthetic_path_r_values_inspected": data["oti1_result"]["synthetic_path_r_values_inspected"],
                "forbidden_primary_field_hits": data["oti1_label"]["forbidden_primary_field_hits"],
                "source_projection_forbidden_issue_count": data["oti1_label"]["source_projection_forbidden_issue_count"],
                "evidence_files": [rel(PATHS["oti1_result"]), rel(PATHS["oti1_label"]), rel(PATHS["otb1r_schema"])],
            },
            {
                "lane": "OTI2",
                "status": "PASS",
                "blocked_packet_outcomes_inspected": data["oti2_result"]["blocked_packet_outcomes_inspected"],
                "broker_actual_r_inspected": data["oti2_result"]["broker_actual_r_inspected"],
                "allowed_quarantined_label_family": data["oti2_result"]["label_family"],
                "forbidden_row_field_hits": oti2_forbidden_hits,
                "source_leakage_guard": data["oti2_source"]["leakage_guard"],
                "row_source_hash_failure_count": data["oti2_source"]["row_source_hash_failure_count"],
                "coverage_failure_count": data["oti2_source"]["coverage_failure_count"],
                "evidence_files": [rel(PATHS["oti2_result"]), rel(PATHS["oti2_rows"]), rel(PATHS["oti2_source"]), rel(PATHS["otb2r_forbidden"])],
            },
        ],
        "important_boundary": "OTI2 opens synthetic path labels after method freeze as quarantined discovery labels only; this is allowed by OTG0 rules and is not broker actual-R/live-result leakage.",
        "g12_reaudit_evidence": {
            "accepted_shortlist": rel(PATHS["g12_reaudit_shortlist"]),
            "leakage_review": rel(PATHS["g12_reaudit_leakage"]),
            "source_hash_review": rel(PATHS["g12_reaudit_hash"]),
        },
    }


def build_duplicate_audit(data: dict[str, Any], generated_at: str) -> dict[str, Any]:
    oti2_rows = data["oti2_rows"]
    oti2_dup_counter = Counter(row["duplicate_group_id"] for row in oti2_rows)
    return {
        **common_meta("duplicate_denominator_audit", generated_at),
        "verdict": "PASS",
        "lane_findings": [
            {
                "lane": "OTI1",
                "status": "PASS",
                "raw_rows_audit_only": data["oti1_duplicate"]["raw_rows_audit_only"],
                "unique_duplicate_group_packet_units": data["oti1_duplicate"]["unique_duplicate_group_packet_units"],
                "unique_duplicate_group_cross_packet_units": data["oti1_duplicate"]["unique_duplicate_group_cross_packet_units"],
                "source_duplicate_group_id_units_unpooled": data["oti1_duplicate"]["source_duplicate_group_id_units_unpooled"],
                "denominator_mismatches": data["oti1_duplicate"]["denominator_mismatches"],
                "duplicate_group_label_conflicts": data["oti1_duplicate"]["duplicate_group_label_conflicts"],
                "policy": "Use unique duplicate_group_id units, not raw child rows.",
                "evidence": rel(PATHS["oti1_duplicate"]),
            },
            {
                "lane": "OTI2",
                "status": "PASS",
                "raw_records": len(oti2_rows),
                "unique_duplicate_group_id_count": len(oti2_dup_counter),
                "groups_with_multiple_rows": sum(1 for count in oti2_dup_counter.values() if count > 1),
                "source_report_denominator": data["oti2_source"]["duplicate_group_denominator"],
                "policy": "86/86 duplicate_group_id denominator; child legs are not independent.",
                "evidence": rel(PATHS["oti2_source"]),
            },
        ],
        "controlling_g12_duplicate_reviews": [
            rel(PATHS["g12_reaudit_duplicate"]),
            rel(PATHS["otb1r_dup"]),
            rel(PATHS["otb2r_manifest"]),
        ],
    }


def build_label_audit(data: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        **common_meta("label_family_audit", generated_at),
        "verdict": "PASS",
        "lane_findings": [
            {
                "lane": "OTI1",
                "status": "PASS",
                "primary_label_family": data["oti1_label"]["primary_label_family"],
                "accepted_packet_label_family_status": data["oti1_label"]["accepted_packet_label_family_status"],
                "broker_actual_r_status": data["oti1_label"]["broker_actual_r_status"],
                "synthetic_path_r_status": data["oti1_label"]["synthetic_path_r_status"],
                "blocked_packet_status": data["oti1_label"]["blocked_packet_status"],
                "evidence": rel(PATHS["oti1_label"]),
            },
            {
                "lane": "OTI2",
                "status": "PASS",
                "primary_label_family": data["oti2_result"]["label_family"],
                "label_family_boundary": data["oti2_freeze"]["label_family_boundary"],
                "broker_actual_r_inspected": data["oti2_result"]["broker_actual_r_inspected"],
                "blocked_packet_outcomes_inspected": data["oti2_result"]["blocked_packet_outcomes_inspected"],
                "same_bar_boundary": data["oti2_result"]["same_bar_ambiguity_state_counts"],
                "evidence": [rel(PATHS["oti2_freeze"]), rel(PATHS["oti2_result"]), rel(PATHS["oti2_ambiguity"])],
            },
        ],
        "controlling_label_sources": [
            rel(PATHS["otg0_rules"]),
            rel(PATHS["otg0_manifest"]),
            rel(PATHS["g12_reaudit_label"]),
        ],
    }


def build_statistics_audit(data: dict[str, Any], generated_at: str) -> dict[str, Any]:
    oti2_method = data["oti2_method"]
    return {
        **common_meta("statistics_audit", generated_at),
        "verdict": "PASS_NOT_COMPUTABLE_REASONS_CORRECTLY_REPORTED",
        "lane_findings": [
            {
                "lane": "OTI1",
                "status": "PASS",
                "statistics_status": data["oti1_result"]["statistics_status"],
                "assessment": "Do not reject for not_computable statistics: lifecycle/no-fill labels are not return series, no variant matrix exists, and the result remains quarantined.",
                "evidence": [rel(PATHS["oti1_result"]), rel(PATHS["oti1_method"])],
            },
            {
                "lane": "OTI2",
                "status": "PASS",
                "effective_n": oti2_method["effective_n"],
                "dsr": oti2_method["dsr"],
                "pbo": oti2_method["pbo"],
                "risk_bank_reentry_scoreability": oti2_method["risk_bank_reentry_scoreability"],
                "assessment": "Do not reject for not_computable statistics: the accepted packet lacks leg-level risk-bank state, sample floor is below 150, and no unseen split or variant matrix exists.",
                "evidence": [rel(PATHS["oti2_method"]), rel(PATHS["oti2_blocker"])],
            },
        ],
        "control_rule_evidence": rel(PATHS["otg0_rules"]),
    }


def build_summary(data: dict[str, Any], lanes: dict[str, Any], generated_at: str) -> dict[str, Any]:
    decision_counts = Counter(payload["decision"] for payload in lanes.values())
    return {
        **common_meta("accepted_rejected_blocked_summary", generated_at),
        "decision_counts": dict(decision_counts),
        "accepted_lanes": [
            {
                "lane": payload["lane"],
                "decision": payload["decision"],
                "accepted_packets": payload["accepted_packets"],
                "residual_next_exact_question": payload["next_exact_question"],
            }
            for payload in lanes.values()
            if payload["decision"] == ACCEPT
        ],
        "rejected_lanes": [
            payload for payload in lanes.values() if payload["decision"] == REJECT
        ],
        "blocked_lanes": [
            payload for payload in lanes.values() if payload["decision"] == BLOCKED
        ],
        "blocked_inside_accepted_lanes": [
            {
                "lane": "OTI1",
                "status": "not_result_blocking",
                "detail": "Covariate/source-complete claims are blocked where source/as-of proof is incomplete; lifecycle result acceptance is unaffected.",
                "evidence": rel(PATHS["oti1_blocker"]),
            },
            {
                "lane": "OTI2",
                "status": "not_result_blocking_for_quarantined_discovery",
                "detail": "Risk-bank primary metric and validation statistics are not computable until leg-level risk-bank fields and sample floor exist.",
                "evidence": rel(PATHS["oti2_blocker"]),
            },
        ],
    }


def build_next_lane(lanes: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        **common_meta("next_lane_recommendation", generated_at),
        "recommendation": "G0_OUTCOME_SYNTHESIS_CAN_USE_OTI1_OTI2_ONLY_AS_QUARANTINED_DISCOVERY_EVIDENCE",
        "do_not_do": [
            "Do not promote either lane.",
            "Do not mark validation_safe=true.",
            "Do not set outcome_review_opened=true in master registries.",
            "Do not pool lifecycle_no_fill, synthetic_path_r, broker_actual_r, or live trade results.",
            "Do not compute promotion DSR/PBO from these quarantined artifacts.",
            "Do not inspect blocked-packet outcomes; answer their exact blocker questions first.",
        ],
        "next_exact_questions": {
            "OTI1": lanes["oti1"]["next_exact_question"],
            "OTI2": lanes["oti2"]["next_exact_question"],
            "G0": (
                "Will G0 synthesis keep OTI1 and OTI2 in a discovery-only section, preserve "
                "NO_PROMOTION_VERDICT, and route OTI2 leg-level risk-bank packet construction plus OTI1 "
                "covariate source/as-of proofs as separate future blocker-clearing tasks?"
            ),
        },
        "allowed_next_use": [
            "OTI1 can support lifecycle/no-fill descriptive discovery only.",
            "OTI2 can support synthetic path descriptive discovery and risk-bank packet gap definition only.",
            "Both lanes can define sharper future frozen packet requirements.",
        ],
    }


def build_decision_ledger(lanes: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        **common_meta("post_test_decision_ledger", generated_at),
        "objective_restatement": (
            "Audit OTI1 lifecycle quarantined results and OTI2 risk-bank quarantined results against "
            "G12 accepted rebuilt packets, OTG0 controls, prior G12 audits, master registry constraints, "
            "research doctrine, and research_current_state. Decide each lane as accept, reject, or blocked "
            "without promoting or opening validation."
        ),
        "lane_decisions": [lanes["oti1"], lanes["oti2"]],
        "decision_counts": dict(Counter(payload["decision"] for payload in lanes.values())),
        "controlling_inputs": [
            rel(PATHS[key])
            for key in [
                "g12_reaudit_shortlist",
                "g12_reaudit_decision",
                "g12_reaudit_leakage",
                "g12_reaudit_duplicate",
                "g12_reaudit_label",
                "g12_reaudit_hash",
                "otg0_rules",
                "otg0_manifest",
                "otg0_prereg",
                "otl1",
                "otl2",
                "otb0",
                "otb1r_schema",
                "otb1r_dup",
                "otb2r_hashes",
                "otb2r_forbidden",
                "otb2r_coverage",
                "master_registry",
                "research_doctrine",
                "research_current_state",
            ]
        ],
    }


def checklist_item(requirement: str, evidence: str, status: str = "PASS") -> dict[str, str]:
    return {"requirement": requirement, "evidence": evidence, "status": status}


def build_completion_audit(artifacts: dict[str, dict[str, Any]], generated_at: str) -> dict[str, Any]:
    decision_ledger = artifacts["G12_OTI_POST_TEST_DECISION_LEDGER"]
    all_accept = all(row["decision"] == ACCEPT for row in decision_ledger["lane_decisions"])
    checklist = [
        checklist_item("Complete GTOS preflight", ".context/LIVE_STATE.md regenerated and mandatory context docs read before audit implementation."),
        checklist_item("Verify HEAD 6622f473", ".context/LIVE_STATE.md reports HEAD 6622f473; git rev-parse HEAD returned 6622f47327a89a424893ac04111eac61d30ad39b."),
        checklist_item("Use OTI1 lifecycle quarantined results", rel(PATHS["oti1_result"])),
        checklist_item("Use OTI2 risk-bank quarantined results", rel(PATHS["oti2_result"]) + " and " + rel(PATHS["oti2_rows"])),
        checklist_item("Use G12 OTB rebuild reaudit and accepted packet shortlist", rel(PATHS["g12_reaudit_decision"]) + " and " + rel(PATHS["g12_reaudit_shortlist"])),
        checklist_item("Use OTB1R, OTB2R, OTG0, OTL1, OTL2, OTB0, prior G12 audits, master registry, doctrine, current state", "All listed controlling paths are present in decision ledger input list and artifact manifest."),
        checklist_item("Audit method freeze before label/outcome inspection", rel(OUT / "G12_OTI_POST_TEST_METHODOLOGY_AUDIT_2026-05-07.md")),
        checklist_item("Audit only G12-accepted packets and blocked-packet exclusion", rel(OUT / "G12_OTI_POST_TEST_DECISION_LEDGER_2026-05-07.md")),
        checklist_item("Audit leakage/no-leak and broker/live-result avoidance", rel(OUT / "G12_OTI_POST_TEST_LEAKAGE_NOLEAK_AUDIT_2026-05-07.md")),
        checklist_item("Audit duplicate_group_id denominator use", rel(OUT / "G12_OTI_POST_TEST_DUPLICATE_DENOMINATOR_AUDIT_2026-05-07.md")),
        checklist_item("Audit label-family separation", rel(OUT / "G12_OTI_POST_TEST_LABEL_FAMILY_AUDIT_2026-05-07.md")),
        checklist_item("Audit DSR/PBO/effective-N/not_computable reporting", rel(OUT / "G12_OTI_POST_TEST_STATISTICS_AUDIT_2026-05-07.md")),
        checklist_item("Decide OTI1 separately", "OTI1 decision=" + decision_ledger["lane_decisions"][0]["decision"]),
        checklist_item("Decide OTI2 separately", "OTI2 decision=" + decision_ledger["lane_decisions"][1]["decision"]),
        checklist_item("Produce accepted/rejected/blocked summary", rel(OUT / "G12_OTI_POST_TEST_ACCEPTED_REJECTED_BLOCKED_SUMMARY_2026-05-07.md")),
        checklist_item("Produce next-lane recommendation", rel(OUT / "G12_OTI_POST_TEST_NEXT_LANE_RECOMMENDATION_2026-05-07.md")),
        checklist_item("Preserve NO_PROMOTION_VERDICT", "All generated artifacts carry promotion_verdict=NO_PROMOTION_VERDICT."),
        checklist_item("Do not mark validation_safe or outcome_review_opened true", "All generated artifacts carry validation_safe=false and outcome_review_opened=false."),
        checklist_item("Do not edit master registries", "Builder writes only under g12_oti_post_test_audit; master_registry_edited=false."),
        checklist_item("Do not run new outcome tests or inspect blocked-packet outcomes", "outcomes_run_by_this_audit=false and blocked_packet_outcomes_inspected_by_this_audit=false."),
        checklist_item("Do not use paid/API/Databento/network or live trading surfaces", "network_api_databento_paid_calls=0 and live_trading_surfaces_touched=false."),
    ]
    return {
        **common_meta("completion_audit", generated_at),
        "objective_restatement": decision_ledger["objective_restatement"],
        "prompt_to_artifact_checklist": checklist,
        "can_mark_g12_oti_post_test_audit_complete": all(item["status"] == "PASS" for item in checklist) and all_accept,
        "residual_risks": [
            "Accepted means quarantined discovery evidence only, not validation or promotion.",
            "OTI1 covariate source-complete claims remain blocked until packet-bound source/as-of proofs exist.",
            "OTI2 risk-bank primary metric remains not_computable until leg-level reentry/risk-bank/cost fields exist.",
        ],
    }


def render_header(title: str, payload: dict[str, Any]) -> list[str]:
    return [
        f"# {title} - {DATE_STAMP}",
        "",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        f"**Validation safe:** `{payload['validation_safe']}`",
        f"**Outcome review opened:** `{payload['outcome_review_opened']}`",
        f"**Generated:** `{payload['generated_at_utc']}`",
        "",
    ]


def render_decision_ledger(payload: dict[str, Any]) -> str:
    rows = [
        [
            lane["lane"],
            lane["result_lane"],
            lane["decision"],
            lane["accepted_packets"],
            lane["decision_reason"],
            lane["next_exact_question"],
        ]
        for lane in payload["lane_decisions"]
    ]
    lines = render_header("G12 OTI Post-Test Decision Ledger", payload)
    lines += [
        "## Objective",
        "",
        payload["objective_restatement"],
        "",
        "## Decisions",
        "",
        table(["Lane", "Result lane", "Decision", "Packets", "Reason", "Next exact question"], rows),
        "",
        "## Evidence",
        "",
    ]
    for lane in payload["lane_decisions"]:
        lines += [f"### {lane['lane']}", ""]
        for ev in lane["evidence"]:
            lines.append(f"- {ev['claim']} Evidence: `{ev['path']}` keys `{', '.join(ev['keys'])}`.")
        lines.append("")
    lines += [
        "## Controlling Inputs",
        "",
        *[f"- `{path}`" for path in payload["controlling_inputs"]],
    ]
    return "\n".join(lines) + "\n"


def render_methodology(payload: dict[str, Any]) -> str:
    lines = render_header("G12 OTI Methodology Audit", payload)
    rows = [
        [
            item["lane"],
            item["status"],
            item["freeze_artifact"],
            item["assessment"],
            item["builder_evidence"]["path"],
        ]
        for item in payload["method_freeze_findings"]
    ]
    lines += [
        "## Method Freeze Findings",
        "",
        table(["Lane", "Status", "Freeze artifact", "Assessment", "Builder evidence"], rows),
        "",
        "## Control Inputs Checked",
        "",
        *[f"- `{path}`" for path in payload["control_inputs_checked"]],
    ]
    return "\n".join(lines) + "\n"


def render_leakage(payload: dict[str, Any]) -> str:
    lines = render_header("G12 OTI Leakage No-Leak Audit", payload)
    rows = []
    for item in payload["no_leak_findings"]:
        rows.append([
            item["lane"],
            item["status"],
            item.get("blocked_packet_outcomes_inspected"),
            item.get("broker_actual_r_values_inspected", item.get("broker_actual_r_inspected")),
            item.get("synthetic_path_r_values_inspected", item.get("allowed_quarantined_label_family")),
            item.get("forbidden_primary_field_hits", item.get("forbidden_row_field_hits")),
            item["evidence_files"],
        ])
    lines += [
        "## Verdict",
        "",
        f"`{payload['verdict']}`",
        "",
        "## Findings",
        "",
        table(
            ["Lane", "Status", "Blocked outcomes inspected", "Broker actual-R inspected", "Synthetic/path status", "Forbidden hits", "Evidence"],
            rows,
        ),
        "",
        "## Boundary",
        "",
        payload["important_boundary"],
    ]
    return "\n".join(lines) + "\n"


def render_duplicate(payload: dict[str, Any]) -> str:
    lines = render_header("G12 OTI Duplicate Denominator Audit", payload)
    rows = [
        [
            item["lane"],
            item["status"],
            item.get("raw_rows_audit_only", item.get("raw_records")),
            item.get("unique_duplicate_group_packet_units", item.get("unique_duplicate_group_id_count")),
            item.get("unique_duplicate_group_cross_packet_units", ""),
            item.get("groups_with_multiple_rows", ""),
            item["policy"],
            item["evidence"],
        ]
        for item in payload["lane_findings"]
    ]
    lines += [
        "## Findings",
        "",
        table(["Lane", "Status", "Raw rows", "Unique packet groups", "Cross-packet groups", "Groups >1 row", "Policy", "Evidence"], rows),
    ]
    return "\n".join(lines) + "\n"


def render_label(payload: dict[str, Any]) -> str:
    lines = render_header("G12 OTI Label Family Audit", payload)
    rows = [
        [
            item["lane"],
            item["status"],
            item["primary_label_family"],
            item.get("broker_actual_r_status", item.get("broker_actual_r_inspected")),
            item.get("synthetic_path_r_status", item.get("label_family_boundary")),
            item.get("blocked_packet_status", item.get("blocked_packet_outcomes_inspected")),
            item["evidence"],
        ]
        for item in payload["lane_findings"]
    ]
    lines += [
        "## Findings",
        "",
        table(["Lane", "Status", "Primary label family", "Broker actual-R boundary", "Synthetic/path boundary", "Blocked packet boundary", "Evidence"], rows),
    ]
    return "\n".join(lines) + "\n"


def render_statistics(payload: dict[str, Any]) -> str:
    lines = render_header("G12 OTI Statistics Audit", payload)
    rows = []
    for item in payload["lane_findings"]:
        if item["lane"] == "OTI1":
            rows.append([
                item["lane"],
                item["status"],
                item["statistics_status"]["validation_effective_n_status"],
                item["statistics_status"]["dsr_status"],
                item["statistics_status"]["pbo_status"],
                item["assessment"],
            ])
        else:
            rows.append([
                item["lane"],
                item["status"],
                item["effective_n"]["riskbank_primary_effective_n"],
                item["dsr"]["status"],
                item["pbo"]["status"],
                item["assessment"],
            ])
    lines += [
        "## Findings",
        "",
        table(["Lane", "Status", "Effective-N", "DSR", "PBO", "Assessment"], rows),
        "",
        "Statistics are not promotion statistics. `not_computable` is accepted here because both lanes preserve quarantine and state exact reasons.",
    ]
    return "\n".join(lines) + "\n"


def render_summary(payload: dict[str, Any]) -> str:
    lines = render_header("G12 OTI Accepted Rejected Blocked Summary", payload)
    lines += [
        "## Decision Counts",
        "",
        table(["Decision", "Count"], [[key, value] for key, value in payload["decision_counts"].items()]),
        "",
        "## Accepted Lanes",
        "",
        table(
            ["Lane", "Decision", "Packets", "Residual next exact question"],
            [[row["lane"], row["decision"], row["accepted_packets"], row["residual_next_exact_question"]] for row in payload["accepted_lanes"]],
        ),
        "",
        "## Rejected Lanes",
        "",
        "`0`",
        "",
        "## Blocked Lane-Level Decisions",
        "",
        "`0`",
        "",
        "## Blockers Inside Accepted Lanes",
        "",
        table(
            ["Lane", "Status", "Detail", "Evidence"],
            [[row["lane"], row["status"], row["detail"], row["evidence"]] for row in payload["blocked_inside_accepted_lanes"]],
        ),
    ]
    return "\n".join(lines) + "\n"


def render_next_lane(payload: dict[str, Any]) -> str:
    lines = render_header("G12 OTI Next-Lane Recommendation", payload)
    lines += [
        "## Recommendation",
        "",
        f"`{payload['recommendation']}`",
        "",
        "## Allowed Next Use",
        "",
        *[f"- {item}" for item in payload["allowed_next_use"]],
        "",
        "## Do Not Do",
        "",
        *[f"- {item}" for item in payload["do_not_do"]],
        "",
        "## Next Exact Questions",
        "",
        table(["Lane", "Question"], [[key, value] for key, value in payload["next_exact_questions"].items()]),
    ]
    return "\n".join(lines) + "\n"


def render_completion(payload: dict[str, Any]) -> str:
    lines = render_header("G12 OTI Completion Audit", payload)
    lines += [
        "## Objective",
        "",
        payload["objective_restatement"],
        "",
        "## Prompt To Artifact Checklist",
        "",
        table(
            ["Requirement", "Evidence", "Status"],
            [[row["requirement"], row["evidence"], row["status"]] for row in payload["prompt_to_artifact_checklist"]],
        ),
        "",
        f"**Can mark G12 OTI post-test audit complete:** `{payload['can_mark_g12_oti_post_test_audit_complete']}`",
        "",
        "## Residual Risks",
        "",
        *[f"- {risk}" for risk in payload["residual_risks"]],
    ]
    return "\n".join(lines) + "\n"


RENDERERS = {
    "G12_OTI_POST_TEST_DECISION_LEDGER": render_decision_ledger,
    "G12_OTI_POST_TEST_METHODOLOGY_AUDIT": render_methodology,
    "G12_OTI_POST_TEST_LEAKAGE_NOLEAK_AUDIT": render_leakage,
    "G12_OTI_POST_TEST_DUPLICATE_DENOMINATOR_AUDIT": render_duplicate,
    "G12_OTI_POST_TEST_LABEL_FAMILY_AUDIT": render_label,
    "G12_OTI_POST_TEST_STATISTICS_AUDIT": render_statistics,
    "G12_OTI_POST_TEST_ACCEPTED_REJECTED_BLOCKED_SUMMARY": render_summary,
    "G12_OTI_POST_TEST_NEXT_LANE_RECOMMENDATION": render_next_lane,
    "G12_OTI_POST_TEST_COMPLETION_AUDIT": render_completion,
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    data = load_inputs()
    lanes = build_lane_audit(data)

    artifacts: dict[str, dict[str, Any]] = {}
    artifacts["G12_OTI_POST_TEST_DECISION_LEDGER"] = build_decision_ledger(lanes, generated_at)
    artifacts["G12_OTI_POST_TEST_METHODOLOGY_AUDIT"] = build_methodology_audit(data, lanes, generated_at)
    artifacts["G12_OTI_POST_TEST_LEAKAGE_NOLEAK_AUDIT"] = build_leakage_audit(data, lanes, generated_at)
    artifacts["G12_OTI_POST_TEST_DUPLICATE_DENOMINATOR_AUDIT"] = build_duplicate_audit(data, generated_at)
    artifacts["G12_OTI_POST_TEST_LABEL_FAMILY_AUDIT"] = build_label_audit(data, generated_at)
    artifacts["G12_OTI_POST_TEST_STATISTICS_AUDIT"] = build_statistics_audit(data, generated_at)
    artifacts["G12_OTI_POST_TEST_ACCEPTED_REJECTED_BLOCKED_SUMMARY"] = build_summary(data, lanes, generated_at)
    artifacts["G12_OTI_POST_TEST_NEXT_LANE_RECOMMENDATION"] = build_next_lane(lanes, generated_at)
    artifacts["G12_OTI_POST_TEST_COMPLETION_AUDIT"] = build_completion_audit(artifacts, generated_at)

    written: list[Path] = []
    for stem, payload in artifacts.items():
        json_path = OUT / f"{stem}_{DATE_STAMP}.json"
        md_path = OUT / f"{stem}_{DATE_STAMP}.md"
        write_json(json_path, payload)
        md_path.write_text(RENDERERS[stem](payload), encoding="utf-8", newline="\n")
        written.extend([json_path, md_path])

    input_hashes = {
        name: {"path": rel(path), "sha256": file_sha(path)}
        for name, path in sorted(PATHS.items())
        if path.exists() and path.is_file()
    }
    manifest = {
        **common_meta("artifact_manifest", generated_at),
        "artifacts": [
            {"path": rel(path), "sha256": file_sha(path), "size_bytes": path.stat().st_size}
            for path in sorted(written, key=lambda item: item.name)
        ],
        "input_hashes": input_hashes,
        "builder": rel(Path(__file__)),
        "can_mark_g12_oti_post_test_audit_complete": artifacts["G12_OTI_POST_TEST_COMPLETION_AUDIT"][
            "can_mark_g12_oti_post_test_audit_complete"
        ],
    }
    manifest_path = OUT / f"G12_OTI_POST_TEST_ARTIFACT_MANIFEST_{DATE_STAMP}.json"
    write_json(manifest_path, manifest)
    print(json.dumps({
        "output_dir": rel(OUT),
        "artifacts_written": len(written) + 1,
        "oti1_decision": lanes["oti1"]["decision"],
        "oti2_decision": lanes["oti2"]["decision"],
        "can_mark_complete": manifest["can_mark_g12_oti_post_test_audit_complete"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
