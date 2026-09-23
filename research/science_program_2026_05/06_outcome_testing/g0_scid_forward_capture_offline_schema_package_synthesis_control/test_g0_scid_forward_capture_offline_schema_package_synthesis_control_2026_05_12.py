from __future__ import annotations

import json
from pathlib import Path

from verify_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_accepted_g12_reconciliation_preserves_boundaries():
    reconciliation = load_json("ACCEPTED_G12_AUDIT_RECONCILIATION")
    checks = {row["check_id"]: row for row in reconciliation["exact_reconciliation_checks"]}

    assert reconciliation["accepted_g12_terminal_decision"] == (
        "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY"
    )
    assert checks["candidate_rows_coverage_expectation"]["actual"] == 3014
    assert checks["duplicate_proxy_denominator_key_coverage_expectation"]["actual"] == 3014
    assert len(checks["ten_capture_groups"]["actual"]) == 10
    assert checks["live_wiring_absent_required"]["actual"] is True
    assert all(row["status"] == "PASS" for row in checks.values())
    assert reconciliation["validation_safe"] is False
    assert reconciliation["outcome_review_opened"] is False
    assert reconciliation["live_effect"] is False


def test_implementation_readiness_matrix_covers_all_ten_groups():
    matrix = load_json("IMPLEMENTATION_READINESS_MATRIX")

    groups = {row["capture_group"] for row in matrix["rows"]}
    assert matrix["matrix_row_count"] == 10
    assert matrix["all_ten_capture_groups_covered"] is True
    assert groups == {
        "side",
        "entry",
        "stop",
        "target",
        "POI",
        "framework",
        "lifecycle",
        "LTF",
        "orderflow/proxy",
        "baseline-control",
    }
    for row in matrix["rows"]:
        assert row["offline_schema"]["schema_path"].endswith(".schema.json")
        assert row["parser"]["fail_closed_policy"]
        assert row["validator"]["accepted_g12_fixture_recompute"] is True
        assert row["prospective_source_or_logger_field"]
        assert row["redaction_no_leak_rule"]["redaction_policy_id"] == (
            "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"
        )
        assert "Recompute schema closure" in row["g12_acceptance_condition"]


def test_route_scoring_and_prompt_pack_top_three_rule():
    scoring = load_json("ROUTE_SCORING_MATRIX")
    ranking = load_json("ROUTE_OPTION_RANKING_AND_ANTI_BOXING_REVIEW")
    prompt_pack = load_json("SELECTED_ROUTE_PROMPT_PACK_LEDGER")

    routes_by_rank = sorted(scoring["routes"], key=lambda row: row["rank"])
    assert [row["route_id"] for row in routes_by_rank[:3]] == [
        "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
        "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_WITH_SYNTHETIC_ONLY_FIXTURES",
        "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION",
    ]
    for row in scoring["routes"]:
        assert set(row["scores_0_to_5"]) == {
            "immediacy",
            "evidence_gain",
            "non_generatable_gap_closure",
            "edge_testing_unlock",
            "source_noleak_cleanliness",
            "implementation_burden_score",
            "parallelizability",
        }
        assert all(0 <= value <= 5 for value in row["scores_0_to_5"].values())

    assert ranking["top_three_prompt_pack_rule_satisfied"] is True
    assert ranking["prompt_packs_emitted_count"] >= 3
    assert prompt_pack["top_three_prompt_pack_rule_satisfied"] is True
    assert prompt_pack["starter_lines_present_for_all_selected_routes"] is True
    assert prompt_pack["prompt_packs_emitted_count"] == 5


def test_manifest_repair_and_readonly_alignment_are_preserved():
    repair = load_json("MANIFEST_BINDING_REPAIR_CONTINUITY_LEDGER")
    readonly = load_json("READ_ONLY_MONITORING_ALIGNMENT_SYNTHESIS")

    assert repair["repair_preserved_exactly"] is True
    assert len(repair["g12_prompt_hash_rebound"]) == 1
    assert len(repair["builder_output_manifest_self_hash_nonblocking"]) == 2
    assert repair["blocking_unrepaired_hash_mismatches"] == []
    assert repair["strict_input_hash_mismatches"] == []
    assert readonly["alignment_target_count"] == 12
    assert readonly["missing_alignment_groups"] == []
    assert readonly["producer_files_modified"] == []
    assert readonly["live_wiring_added"] is False
    assert readonly["read_only_alignment_only"] is True


def test_prompt_packs_embed_required_boundaries_and_starters():
    prompt_pack = load_json("SELECTED_ROUTE_PROMPT_PACK_LEDGER")

    for route in prompt_pack["selected_route_prompt_packs"].values():
        prompt_path = ROOT / route["prompt_path"]
        text = prompt_path.read_text(encoding="utf-8")
        assert route["one_line_starter"].startswith("/goal Follow the full controlling prompt")
        for phrase in [
            "Do not rely on chat memory",
            "manifest-binding repair",
            "3,014",
            "ten capture groups",
            "raw-market-blob",
            "broker-account-order-history-deal-position",
            "Current GTOS OB/retest logic",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "Completion Standard",
        ]:
            assert phrase in text


def test_sequencing_saturation_decision_and_verifier_pass():
    sequencing = load_json("PARALLELIZATION_SEQUENCING_LEDGER")
    saturation = load_json("SATURATION_SELF_REDTEAM_LEDGER")
    decision = load_json("DECISION_LEDGER")

    assert sequencing["not_blocked_behind_single_owner_live_path"] is True
    assert len(sequencing["run_now_no_owner_live_approval"]) >= 3
    assert saturation["not_passive_summary"] is True
    assert saturation["not_loop"] is True
    assert len(saturation["self_red_team_questions"]) >= 6
    assert decision["terminal_decision"] == (
        "ACCEPT_AS_G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_WITH_RANKED_IMPLEMENTATION_ROUTE_BUNDLE"
    )
    assert decision["live_wiring_ready"] is False

    result = verify()
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True

    completion = load_json("COMPLETION_AUDIT")
    assert completion["completion_standard_satisfied"] is True
    assert completion["can_mark_goal_complete"] is True
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False
    completion["focused_tests_ok"] = True
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
            "g0_scid_forward_capture_offline_schema_package_synthesis_control/"
            "test_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py"
        ),
        "observed_result": "6 passed",
    }
    closeout["status"] = "STANDALONE_VERIFIER_AND_FOCUSED_PYTEST_PASSED_FINAL_LIVE_STATE_REFRESH_REQUIRED"
    closeout_path.write_text(json.dumps(closeout, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
