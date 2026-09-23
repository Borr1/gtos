from __future__ import annotations

import json
from pathlib import Path

import build_g12_scid_asof_sealed_validation_design_audit_2026_05_11 as route


ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-11"
PREFIX = "G12_SCID_ASOF_SEALED_VALIDATION_DESIGN"


def load_json(name: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{name}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_packet_reconciliation_exact_counts_and_gates() -> None:
    payload = load_json("PACKET_RECONCILIATION_AUDIT")
    checks = {row["check_id"]: row for row in payload["exact_count_checks"]}

    assert payload["terminal_decision_consumed"] == "ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY"
    assert payload["g0_evidence_class"] == "G0_SCID_ASOF_PACKET_SOURCE_CONTROL_SYNTHESIS_AND_VALIDATION_DESIGN_ONLY"
    assert payload["g0_verifier_ok"] is True
    assert payload["g0_can_mark_goal_complete"] is True
    assert checks["source_control_bars"]["actual"] == 7567
    assert checks["candidate_input_rows"]["actual"] == 3014
    assert checks["sealed_design_rows"]["actual"] == 2432
    assert checks["stress_design_rows"]["actual"] == 582
    assert checks["accepted_scid_segments"]["actual"] == 9
    assert checks["candidate_denominator_groups"]["actual"] == 7
    assert checks["discovery_exclusions"]["actual"] == 365
    assert checks["adversarial_baselines"]["actual"] == 4
    assert payload["all_counts_reconciled"] is True


def test_row_partition_uniqueness_and_deterministic_split() -> None:
    payload = load_json("ROW_PARTITION_AUDIT")
    summary = payload["summary"]

    assert summary["checks_pass"] is True
    assert summary["partition_rows"] == 3014
    assert summary["unique_partition_candidate_ids"] == 3014
    assert summary["partition_counts"]["SEALED_VALIDATION_CANDIDATE_DESIGN"] == 2432
    assert summary["partition_counts"]["STRESS_ROBUSTNESS_CANDIDATE_DESIGN"] == 582
    assert payload["checks"]["partition_matches_candidate_input_set"] is True
    assert payload["checks"]["deterministic_mod5_partition_recomputed"] is True
    assert payload["checks"]["duplicate_proxy_keys_unique"] is True


def test_noleak_duplicate_science_and_falsification_controls() -> None:
    noleak = load_json("NOLEAK_AUDIT")
    duplicate = load_json("DUPLICATE_PROXY_AUDIT")
    science = load_json("SCIENCE_HORIZON_AUDIT")
    falsification = load_json("FALSIFICATION_AUDIT")

    assert noleak["summary"]["checks_pass"] is True
    assert noleak["checks"]["planned_metrics_names_only_no_computation"] is True
    assert duplicate["summary"]["checks_pass"] is True
    assert duplicate["checks"]["xauusd_primary_gc"] is True
    assert duplicate["checks"]["us30_primary_ym"] is True
    assert "XAUUSD_MGC" not in duplicate["candidate_symbols"]
    assert "US30_MYM" not in duplicate["candidate_symbols"]
    assert science["summary"]["checks_pass"] is True
    assert science["checks"]["all_expected_science_families_present"] is True
    assert falsification["summary"]["checks_pass"] is True
    assert falsification["checks"]["required_stop_phrases_present"] is True


def test_decision_next_prompt_and_verifier_acceptance() -> None:
    decision = load_json("AUDIT_DECISION_LEDGER")
    repair = load_json("REPAIR_BLOCKER_LEDGER")

    assert decision["terminal_decision"] == route.ACCEPT_DECISION
    assert decision["accepted_design_control_evidence_only"] is True
    assert decision["accepted_validation_execution"] is False
    assert decision["accepted_promotion"] is False
    assert repair["repair_blocker_count"] == 0
    assert repair["execution_prompt_emitted"] is True
    assert route.NEXT_EXECUTION_PROMPT.exists()
    prompt = route.NEXT_EXECUTION_PROMPT.read_text(encoding="utf-8")
    assert route.ACCEPT_DECISION in prompt
    assert "no promotion authority" in prompt
    assert "no live authority" in prompt

    result = route.verify_route(write_result=False, run_focused_tests=False)
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True
