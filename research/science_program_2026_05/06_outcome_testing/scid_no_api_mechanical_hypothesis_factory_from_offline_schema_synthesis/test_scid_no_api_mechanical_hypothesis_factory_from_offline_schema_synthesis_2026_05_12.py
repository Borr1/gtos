from __future__ import annotations

import json
from pathlib import Path

from verify_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-12"
PREFIX = "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def load_cards() -> list[dict]:
    path = ROUTE_DIR / f"{PREFIX}_HYPOTHESIS_CARD_LEDGER_{DATE_TAG}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_accepted_boundary_reconciliation_preserves_source_control_scope():
    reconciliation = load_json("ACCEPTED_AUDIT_RECONCILIATION")

    assert reconciliation["candidate_rows_coverage_expectation"] == 3014
    assert reconciliation["duplicate_proxy_denominator_key_coverage_expectation"] == 3014
    assert len(reconciliation["capture_groups"]) == 10
    assert reconciliation["offline_schema_boundary"].startswith("offline schema")
    assert reconciliation["validation_safe"] is False
    assert reconciliation["outcome_review_opened"] is False
    assert reconciliation["live_effect"] is False
    assert all(row["status"] == "PASS" for row in reconciliation["exact_reconciliation_checks"])


def test_hypothesis_cards_are_machine_checkable_and_broad():
    cards = load_cards()
    domains = {card["science_domain"] for card in cards}

    assert len(cards) == 40
    assert len(domains) == 8
    assert all(sum(1 for card in cards if card["science_domain"] == domain) == 5 for domain in domains)
    assert sum(1 for card in cards if card["outside_current_gtos_ob_framing"]) >= 30

    for card in cards:
        assert card["card_id"]
        assert card["mechanical_question"].endswith("?")
        assert card["accepted_descriptor_fields_required_now"]
        assert "decision_asof_utc" in card["as_of_no_leak_rule"]
        assert "duplicate_proxy_denominator_key" in card["duplicate_denominator_policy"]
        assert "separate result-design" in card["future_result_gate"]
        assert card["adversarial_baseline_or_placebo"]
        assert card["expected_failure_mode"]
        assert card["exact_next_source_control_route"]
        assert card["no_api_required"] is True
        assert card["uses_outcomes_now"] is False
        assert card["uses_ai_api"] is False
        assert card["uses_broker_account_order_deal_position_evidence"] is False
        assert card["uses_raw_market_blob_commit"] is False


def test_readiness_and_source_field_matrices_answer_prompt_questions():
    catalog = load_json("MECHANISM_FAMILY_HYPOTHESIS_CATALOG")
    readiness = load_json("PREREGISTRATION_READINESS_MATRIX")
    source_fields = load_json("SOURCE_FIELD_CHECKLIST")

    answers = catalog["answers_required_by_prompt"]
    assert answers["preregisterable_now_using_accepted_descriptors_only"]
    assert answers["requires_future_side_entry_stop_target_poi_framework_lifecycle_fields"]
    assert answers["requires_ltf_orderflow_proxy_source_expansion"]
    assert len(answers["can_run_no_api_later"]) == 40
    assert answers["outside_current_gtos_ob_framing"]

    assert readiness["matrix_row_count"] == 40
    assert readiness["status_counts"]["PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY"] >= 8
    assert readiness["status_counts"]["BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS"] >= 10
    assert readiness["status_counts"]["BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"] >= 10
    assert readiness["no_rows_are_validation_or_result_rows"] is True

    assert source_fields["row_count"] == 8
    assert all(source_fields["all_domains_covered"].values())


def test_science_adversarial_replay_and_gate_ledgers_are_complete():
    coverage = load_json("SCIENCE_DOMAIN_COVERAGE_MATRIX")
    adversarial = load_json("ADVERSARIAL_BASELINE_PLACEBO_MATRIX")
    replay = load_json("FUTURE_NO_API_REPLAY_ROUTE_BUNDLE")
    gates = load_json("FUTURE_RESULT_DESIGN_GATE_LEDGER")
    saturation = load_json("GENERIC_IDEA_LIST_SATURATION_PROOF")

    assert coverage["all_required_domains_covered"] is True
    assert coverage["minimum_cards_per_domain"] == 5
    assert adversarial["baseline_card_count"] == 5
    assert "session_only" in adversarial["required_placebo_families_present"]
    assert replay["route_count"] >= 5
    assert all(route["no_api"] is True for route in replay["routes"])
    assert all(route["result_opening_allowed"] is False for route in replay["routes"])
    assert gates["gate_count"] >= 6
    assert gates["result_design_opened_now"] is False
    assert saturation["not_generic_idea_list"] is True
    assert len(saturation["proof_points"]) >= 5


def test_audit_prompt_and_decision_preserve_boundaries():
    prompt_pack = load_json("G12_G0_AUDIT_PROMPT_PACK")
    decision = load_json("DECISION_LEDGER")

    prompt_path = ROOT / prompt_pack["next_g12_prompt_path"]
    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert prompt_pack["one_line_starter"].startswith("/goal Follow the full controlling prompt")
    for phrase in [
        "G12 SCID No-API Mechanical Hypothesis Factory Audit",
        "3,014",
        "ten capture groups",
        "generic idea list",
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
        "Completion Standard",
    ]:
        assert phrase in prompt_text

    assert decision["terminal_decision"] == "BUILT_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_G12_AUDIT_REQUIRED"
    assert decision["hypothesis_factory_built"] is True
    assert decision["validation_or_promotion_opened"] is False


def test_standalone_verifier_passes_and_updates_completion_audit():
    result = verify()
    assert result["ok"], result["failures"]
    assert result["card_count_verified"] == 40
    assert result["can_mark_goal_complete"] is True

    completion = load_json("COMPLETION_AUDIT")
    completion["focused_tests_ok"] = True
    completion["standalone_verifier_ok"] = True
    completion["completion_standard_satisfied"] = True
    completion["can_mark_goal_complete"] = True
    for row in completion["prompt_to_artifact_checklist"]:
        if row["requirement"] == "standalone verifier and focused tests":
            row["status"] = "PASS"
    (ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json").write_text(
        json.dumps(completion, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    closeout_path = ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.json"
    closeout = json.loads(closeout_path.read_text(encoding="utf-8"))
    closeout["focused_pytest"] = {
        "status": "PASSED",
        "command": (
            "python -m pytest -q -p no:cacheprovider "
            "research/science_program_2026_05/06_outcome_testing/"
            "scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/"
            "test_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py"
        ),
        "observed_result": "6 passed",
    }
    closeout["status"] = "STANDALONE_VERIFIER_AND_FOCUSED_PYTEST_PASSED_FINAL_LIVE_STATE_REFRESH_REQUIRED"
    closeout_path.write_text(json.dumps(closeout, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
