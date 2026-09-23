from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-12"
PREFIX = "G0_SCID_BLOCKED_UNBLOCKING"
EVIDENCE_CLASS = "G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_AFTER_G12_FUTURE_CAPTURE_SOURCE_AUDIT_ONLY"


def read_json(stem: str):
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}.json").read_text(encoding="utf-8"))


def load_verifier():
    path = ROUTE_DIR / "verify_g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit_2026_05_12.py"
    spec = importlib.util.spec_from_file_location("g0_blocked_verify", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_standalone_verifier_passes_with_focused_pending_allowed():
    verifier = load_verifier()
    result = verifier.verify(write=False, allow_focused_pending=True)
    assert result["ok"], result["failures"]


def test_reconciliation_counts_and_safe_flags():
    reconciliation = read_json("ROUTE_RECONCILIATION_LEDGER")
    assert reconciliation["evidence_class"] == EVIDENCE_CLASS
    assert reconciliation["blocked32_card_count"] == 32
    assert reconciliation["blocked15_card_count"] == 15
    assert reconciliation["blocked17_card_count"] == 17
    assert reconciliation["capture_group_count"] == 10
    assert reconciliation["recovered_source_state_rows"] == 1213
    assert len(reconciliation["card_route_rows"]) == 32
    assert not reconciliation["opens_result_scoring"]
    assert not reconciliation["validation_safe"]
    assert reconciliation["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_denominator_quarantine_preserves_blocked_status():
    denominator = read_json("DENOMINATOR_QUARANTINE_GATE_LEDGER")
    assert denominator["accepted_40_denominator_count"] == 40
    assert denominator["ready8_count"] == 8
    assert denominator["blocked15_count"] == 15
    assert denominator["blocked17_count"] == 17
    assert denominator["recovered_source_state_rows"] == 1213
    assert denominator["recovered_rows_are_result_denominator_rows"] is False
    assert denominator["accepted_40_result_denominator_unblocked_by_recovered_rows"] is False
    assert denominator["blocked_cards_may_score_results_now"] is False
    assert denominator["outcome_review_opened"] is False
    assert denominator["live_effect"] is False


def test_route_bundle_preserves_broad_non_ob_domains_and_prompt_pack():
    bundle = read_json("RANKED_ROUTE_BUNDLE")
    prompt_pack = read_json("NEXT_PROMPT_STARTER_LEDGER")
    routes = bundle["routes"]
    domains = {domain for route in routes for domain in route["domain_breadth"]}
    required = {
        "source-state",
        "lifecycle",
        "LTF",
        "orderflow/proxy",
        "baseline-control",
        "failure-anatomy",
        "non-OB",
        "cross-domain",
    }
    assert bundle["route_count"] >= 8
    assert required <= domains
    assert bundle["non_ob_cross_domain_routes_present"] is True
    assert bundle["orderflow_proxy_ltf_lifecycle_baseline_failure_routes_present"] is True
    assert prompt_pack["prompt_count"] == bundle["route_count"]
    assert prompt_pack["starter_count"] == bundle["route_count"]
    assert prompt_pack["all_starters_one_physical_line"] is True
    for row in prompt_pack["prompt_pack"]:
        repo_root = Path(__file__).resolve().parents[4]
        assert (repo_root / row["prompt_path"]).exists()
        assert (repo_root / row["starter_path"]).exists()


def test_instruction_coverage_and_blocker_pursuit_are_exact():
    coverage = read_json("MANDATORY_INSTRUCTION_COVERAGE_AUDIT")
    blocker = read_json("SAME_EVIDENCE_BLOCKER_PURSUIT_LEDGER")
    assert coverage["goal_session_research_discipline_read_after_preflight"] is True
    assert coverage["research_operating_doctrine_read_after_preflight"] is True
    assert coverage["local_heavy_data_inventory_read_after_preflight"] is True
    assert coverage["ai_in_loop_cost_control_read_after_preflight"] is True
    assert "active non-conservative" in coverage["posture_applied"]
    assert len(coverage["outside_current_gtos_ob_routes_considered"]) >= 8
    assert blocker["unresolved_vague_blockers"] == []
    assert blocker["every_item_has_exact_next_requirement"] is True
    assert len(blocker["capture_group_rows"]) == 10


def test_completion_audit_has_all_required_lines_pending_only_verifier_and_tests_initially():
    completion = read_json("COMPLETION_AUDIT")
    requirements = {item["requirement"]: item["satisfied"] for item in completion["prompt_to_artifact_checklist"]}
    assert "standalone verifier passed" in requirements
    assert "focused tests passed" in requirements
    for requirement, satisfied in requirements.items():
        if requirement not in {"standalone verifier passed", "focused tests passed"}:
            assert satisfied, requirement
