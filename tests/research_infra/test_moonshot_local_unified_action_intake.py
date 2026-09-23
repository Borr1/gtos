from src.research_infra.moonshot_local_unified_action_intake import (
    apply_control_score_selection,
    apply_claim_audit_selection,
    apply_guard_selection,
    apply_implementation_selection,
    apply_nofill_redesign_selection,
    apply_source_control_selection,
    claim_audit_selection_for_row,
    compact_intake_row,
    control_score_selection_for_row,
    guard_selection_for_row,
    implementation_selection_for_row,
    main_decision_for_row,
    nofill_redesign_selection_for_row,
    source_control_selection_for_row,
    summarize_guard_selection,
    summarize_intake,
    summarize_implementation_selection,
    summarize_nofill_redesign_selection,
    summarize_claim_audit_selection,
    summarize_control_score_selection,
    summarize_source_control_selection,
)


def test_default_off_candidate_is_research_only_implementation_candidate():
    row = {
        "computed_action_family": "DEFAULT_OFF_CODE_CANDIDATE",
        "computed_action_status": "DEFAULT_OFF_CODE_CANDIDATE_PROXY_DELTA_COMPUTED",
        "computed_proxy_delta": 0.25,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }

    decision = main_decision_for_row(row)

    assert decision["main_action_class"] == "IMPLEMENTATION_CANDIDATE"
    assert decision["main_decision"] == "IMPLEMENT_DEFAULT_OFF_CODE_CANDIDATE_WITH_SOURCE_GUARD_NO_LIVE_EFFECT"
    assert decision["main_safety_state"] == "RESEARCH_ONLY_DEFAULT_OFF_NO_LIVE_EFFECT"
    assert decision["proxy_delta_numeric"] == 0.25
    assert decision["proxy_delta_counted_as_r"] is False


def test_live_or_runtime_use_flags_are_review_required():
    row = {
        "computed_action_family": "GUARD_REGISTRY_SPEC",
        "candidate_use_allowed_now": True,
        "live_effect": False,
    }

    decision = main_decision_for_row(row)

    assert decision["main_action_class"] == "GUARD_SPEC"
    assert decision["main_safety_state"] == "UNEXPECTED_LIVE_OR_RUNTIME_USE_FLAG_REVIEW_REQUIRED"


def test_compact_intake_row_preserves_source_ownership_and_safe_flags():
    row = {
        "computed_action_family": "CURRENT_CLAIM_OPPORTUNITY_AUDIT",
        "computed_action_status": "CURRENT_CLAIM_REJECTION_OPPORTUNITY_ROUTE_COMPUTED",
        "computed_proxy_delta": None,
        "input_unified_system_action_result_row_id": "A-1",
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }

    compact = compact_intake_row(
        row,
        intake_row_id="INTAKE-000001",
        source_artifact="source.jsonl",
        source_line_no=7,
        source_sha256="abc123",
    )

    assert compact["intake_row_id"] == "INTAKE-000001"
    assert compact["source_artifact"] == "source.jsonl"
    assert compact["source_line_no"] == 7
    assert compact["source_sha256"] == "abc123"
    assert compact["main_action_class"] == "CURRENT_CLAIM_REJECTION"
    assert compact["safe_flags"]["NO_PROMOTION_VERDICT"] is True
    assert compact["safe_flags"]["validation_safe"] is False
    assert compact["no_live_behavior"] is True


def test_summarize_intake_counts_families_and_no_r_duplication():
    rows = [
        compact_intake_row(
            {
                "computed_action_family": "DEFAULT_OFF_CODE_CANDIDATE",
                "computed_action_status": "DEFAULT_OFF_CODE_CANDIDATE_PROXY_DELTA_COMPUTED",
                "computed_proxy_delta": 0.2,
                "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_POSITIVE",
                "source_component": "shadow_source_guard",
                "market_expansion_decision": "shadow-candidate",
                "candidate_use_allowed_now": False,
                "live_effect": False,
            },
            intake_row_id="INTAKE-000001",
            source_artifact="a.jsonl",
            source_line_no=1,
            source_sha256="sha",
        ),
        compact_intake_row(
            {
                "computed_action_family": "SOURCE_CONTROL_REPAIR",
                "computed_action_status": "SOURCE_OR_CONTROL_REPAIR_RESULT_ROW",
                "computed_proxy_delta": None,
                "source_component": "market_gap_code",
                "market_expansion_decision": "source-repair",
                "candidate_use_allowed_now": False,
                "live_effect": False,
            },
            intake_row_id="INTAKE-000002",
            source_artifact="b.jsonl",
            source_line_no=2,
            source_sha256="sha",
        ),
    ]

    summary = summarize_intake(rows)

    assert summary["rows"] == 2
    assert summary["default_off_code_candidate_rows"] == 1
    assert summary["numeric_proxy_delta_rows"] == 1
    assert summary["numeric_proxy_delta_sum_not_r"] == 0.2
    assert summary["proxy_delta_counted_as_r_rows"] == 0
    assert summary["candidate_use_allowed_now_true_rows"] == 0
    assert summary["live_effect_true_rows"] == 0


def test_implementation_selection_implements_guarded_positive_candidate():
    row = {
        "source_component": "market_gap_code",
        "computed_decision": "KEEP_DEFAULT_OFF_CODE_CANDIDATE_WITH_SOURCE_GUARD",
        "implementation_implication": "branch_local_entry_geometry_spec_candidate",
        "computed_proxy_delta": 0.25,
        "live_effect": False,
    }

    selected = implementation_selection_for_row(row)

    assert selected["selection_class"] == "IMPLEMENT_DEFAULT_OFF"
    assert selected["selection_decision"] == "IMPLEMENT_DEFAULT_OFF_MARKET_GAP_ENTRY_GEOMETRY_SPEC"
    assert selected["downstream_path"] == "entry_geometry"
    assert selected["proxy_delta_reference"] == 0.25
    assert selected["proxy_delta_reference_counted_as_r"] is False
    assert selected["opportunity_preserved"] is True


def test_implementation_selection_redesigns_negative_without_erasing_intelligence():
    row = {
        "source_component": "registry_scorer_module_system",
        "computed_decision": "KEEP_DEFAULT_OFF_CODE_CANDIDATE_CONTROL_OR_REDESIGN_REQUIRED",
        "computed_proxy_delta": -0.4,
        "live_effect": False,
    }

    selected = apply_implementation_selection(row)

    assert selected["selection_class"] == "REDESIGN"
    assert selected["selection_decision"] == "REDESIGN_SYSTEM_MODULE_SCALAR_CLAIM_PRESERVE_CONTEXT"
    assert selected["downstream_path"] == "context_feature"
    assert selected["underlying_intelligence_preserved"] is True
    assert selected["proxy_delta_reference_counted_as_r"] is False


def test_summarize_implementation_selection_keeps_all_opportunities_and_no_r_counting():
    rows = [
        apply_implementation_selection(
            {
                "source_component": "shadow_source_guard",
                "computed_decision": "KEEP_DEFAULT_OFF_CODE_CANDIDATE_WITH_SOURCE_GUARD",
                "computed_proxy_delta": 0.47,
                "implementation_implication": "ENABLE_ENTRY_GEOMETRY_SHADOW_RULE",
                "live_effect": False,
            }
        ),
        apply_implementation_selection(
            {
                "source_component": "default_off_application",
                "computed_decision": "KEEP_DEFAULT_OFF_CODE_CANDIDATE_CONTROL_OR_REDESIGN_REQUIRED",
                "computed_proxy_delta": -0.1,
                "implementation_implication": "branch_local_default_off_horizon_targetability_redesign_candidate",
                "live_effect": False,
            }
        ),
    ]

    summary = summarize_implementation_selection(rows)

    assert summary["rows"] == 2
    assert summary["selection_class_counts"] == {"IMPLEMENT_DEFAULT_OFF": 1, "REDESIGN": 1}
    assert summary["proxy_delta_reference_rows"] == 2
    assert summary["proxy_delta_reference_sum_not_r"] == 0.37
    assert summary["proxy_delta_reference_counted_as_r_rows"] == 0
    assert summary["opportunity_preserved_rows"] == 2
    assert summary["underlying_intelligence_preserved_rows"] == 2


def test_guard_selection_registers_nofill_source_confidence_guard():
    row = {
        "source_component": "nofill_far_miss_source_confidence",
        "market_expansion_decision": "proxy/control feature",
        "computed_proxy_delta": None,
        "live_effect": False,
    }

    selected = guard_selection_for_row(row)

    assert selected["guard_selection_class"] == "SOURCE_CONFIDENCE_GUARD"
    assert selected["guard_selection_decision"] == "REGISTER_NOFILL_FAR_MISS_SOURCE_CONFIDENCE_GUARD_DEFAULT_OFF"
    assert selected["downstream_path"] == "nofill_source_confidence_guard"
    assert selected["source_completeness_action"] is True
    assert selected["proxy_delta_reference_counted_as_r"] is False


def test_guard_selection_preserves_adverse_context_instead_of_killing():
    row = {
        "source_component": "shadow_source_guard",
        "market_expansion_decision": "proxy/control feature",
        "proxy_delta_numeric": -0.1,
        "live_effect": False,
    }

    selected = apply_guard_selection(row)

    assert selected["guard_selection_class"] == "DENOMINATOR_GUARD_ADVERSE_CONTEXT"
    assert selected["guard_selection_decision"] == "REGISTER_DENOMINATOR_GUARD_ADVERSE_CONTEXT_DEFAULT_OFF"
    assert selected["downstream_path"] == "avoid_or_context_guard"
    assert selected["underlying_intelligence_preserved"] is True
    assert selected["opportunity_preserved"] is True


def test_summarize_guard_selection_counts_source_actions_and_no_r_counting():
    rows = [
        apply_guard_selection(
            {
                "source_component": "shadow_source_guard",
                "market_expansion_decision": "proxy/control feature",
                "proxy_delta_numeric": 0.05,
                "live_effect": False,
            }
        ),
        apply_guard_selection(
            {
                "source_component": "shadow_source_guard",
                "market_expansion_decision": "source-repair",
                "proxy_delta_numeric": -0.07,
                "live_effect": False,
            }
        ),
    ]

    summary = summarize_guard_selection(rows)

    assert summary["rows"] == 2
    assert summary["guard_selection_class_counts"] == {"DENOMINATOR_GUARD": 1, "SOURCE_REPAIR": 1}
    assert summary["source_completeness_action_rows"] == 2
    assert summary["proxy_delta_reference_rows"] == 2
    assert summary["proxy_delta_reference_sum_not_r"] == -0.02
    assert summary["proxy_delta_reference_counted_as_r_rows"] == 0
    assert summary["opportunity_preserved_rows"] == 2


def test_nofill_selection_implements_strong_positive_retest_variant():
    row = {
        "source_component": "nofill_far_miss_retest",
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
        "proxy_delta_numeric": 0.5,
        "live_effect": False,
    }

    selected = nofill_redesign_selection_for_row(row)

    assert selected["nofill_selection_class"] == "IMPLEMENT_DEFAULT_OFF"
    assert selected["nofill_selection_decision"] == "IMPLEMENT_DEFAULT_OFF_FAR_MISS_RETEST_REDESIGN_VARIANT"
    assert selected["downstream_path"] == "retest_redesign"
    assert selected["proxy_delta_reference"] == 0.5
    assert selected["proxy_delta_reference_counted_as_r"] is False
    assert selected["opportunity_preserved"] is True


def test_nofill_selection_redesigns_negative_avoid_without_erasing_mechanism():
    row = {
        "source_component": "nofill_far_miss_avoid",
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_NEGATIVE",
        "proxy_delta_numeric": -0.5,
        "live_effect": False,
    }

    selected = apply_nofill_redesign_selection(row)

    assert selected["nofill_selection_class"] == "REDESIGN"
    assert selected["nofill_selection_decision"] == "REDESIGN_AVOID_INVERSE_VARIANT_CURRENT_PROXY_NEGATIVE"
    assert selected["downstream_path"] == "avoid_inverse_redesign"
    assert selected["underlying_intelligence_preserved"] is True


def test_nofill_selection_routes_missing_proxy_to_source_repair():
    row = {
        "source_component": "nofill_near_miss_offset",
        "computed_proxy_delta_class": "COMPUTED_DELTA_NOT_AVAILABLE_SOURCE_OR_CONTROL_REQUIRED",
        "proxy_delta_numeric": None,
        "live_effect": False,
    }

    selected = apply_nofill_redesign_selection(row)

    assert selected["nofill_selection_class"] == "SOURCE_REPAIR"
    assert selected["nofill_selection_decision"] == "SOURCE_REPAIR_NEAR_MISS_OFFSET_CONTROL_REQUIRED"
    assert selected["downstream_path"] == "source_requirement"
    assert selected["proxy_delta_reference"] is None


def test_summarize_nofill_selection_keeps_opportunities_and_proxy_boundaries():
    rows = [
        apply_nofill_redesign_selection(
            {
                "source_component": "nofill_near_miss_market_entry",
                "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
                "proxy_delta_numeric": 0.3,
                "symbol": "GBPJPY",
                "route_session": None,
                "live_effect": False,
            }
        ),
        apply_nofill_redesign_selection(
            {
                "source_component": "nofill_near_miss_market_entry",
                "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_NEGATIVE",
                "proxy_delta_numeric": -0.5,
                "symbol": "GBPJPY",
                "route_session": None,
                "live_effect": False,
            }
        ),
        apply_nofill_redesign_selection(
            {
                "source_component": "nofill_near_miss_market_entry",
                "computed_proxy_delta_class": "COMPUTED_DELTA_NOT_AVAILABLE_SOURCE_OR_CONTROL_REQUIRED",
                "proxy_delta_numeric": None,
                "symbol": "GBPJPY",
                "route_session": None,
                "live_effect": False,
            }
        ),
    ]

    summary = summarize_nofill_redesign_selection(rows)

    assert summary["rows"] == 3
    assert summary["nofill_selection_class_counts"] == {
        "IMPLEMENT_DEFAULT_OFF": 1,
        "REDESIGN": 1,
        "SOURCE_REPAIR": 1,
    }
    assert summary["proxy_delta_reference_rows"] == 2
    assert summary["proxy_delta_reference_sum_not_r"] == -0.2
    assert summary["proxy_delta_reference_counted_as_r_rows"] == 0
    assert summary["opportunity_preserved_rows"] == 3


def test_source_control_selection_keeps_unavailable_delta_as_source_repair():
    row = {
        "source_component": "nofill_near_miss_source_requirement",
        "computed_proxy_delta_class": "COMPUTED_DELTA_NOT_AVAILABLE_SOURCE_OR_CONTROL_REQUIRED",
        "proxy_delta_numeric": None,
        "live_effect": False,
    }

    selected = source_control_selection_for_row(row)

    assert selected["source_control_selection_class"] == "SOURCE_REPAIR"
    assert selected["source_control_selection_decision"] == "SOURCE_REPAIR_NOFILL_NEAR_MISS_ATTACH_SATISFIED_SOURCE"
    assert selected["downstream_path"] == "entry_replay_source_attachment"
    assert selected["proxy_delta_reference"] is None
    assert selected["opportunity_preserved"] is True


def test_source_control_selection_implements_positive_market_gap_default_off():
    row = {
        "source_component": "market_gap_code",
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_POSITIVE",
        "proxy_delta_numeric": 0.05,
        "live_effect": False,
    }

    selected = apply_source_control_selection(row)

    assert selected["source_control_selection_class"] == "IMPLEMENT_DEFAULT_OFF"
    assert selected["source_control_selection_decision"] == "IMPLEMENT_DEFAULT_OFF_MARKET_GAP_CODE_CONTROL_PROXY"
    assert selected["downstream_path"] == "market_gap_control_candidate"
    assert selected["proxy_delta_reference_counted_as_r"] is False


def test_source_control_selection_redesigns_adverse_source_guard_without_kill():
    row = {
        "source_component": "shadow_source_guard",
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_NEGATIVE",
        "proxy_delta_numeric": -0.5,
        "live_effect": False,
    }

    selected = apply_source_control_selection(row)

    assert selected["source_control_selection_class"] == "REDESIGN"
    assert selected["source_control_selection_decision"] == "REDESIGN_SHADOW_SOURCE_GUARD_ADVERSE_AVOID_CONTEXT"
    assert selected["downstream_path"] == "source_guard_avoid_context"
    assert selected["underlying_intelligence_preserved"] is True


def test_summarize_source_control_selection_preserves_proxy_boundaries():
    rows = [
        apply_source_control_selection(
            {
                "source_component": "shadow_source_guard",
                "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_POSITIVE",
                "proxy_delta_numeric": 0.2,
                "symbol": "NAS100",
                "route_session": "tokyo_kz",
                "live_effect": False,
            }
        ),
        apply_source_control_selection(
            {
                "source_component": "shadow_source_guard",
                "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_WEAK_NEGATIVE",
                "proxy_delta_numeric": -0.1,
                "symbol": "NAS100",
                "route_session": "tokyo_kz",
                "live_effect": False,
            }
        ),
        apply_source_control_selection(
            {
                "source_component": "default_off_application",
                "computed_proxy_delta_class": "COMPUTED_DELTA_NOT_AVAILABLE_SOURCE_OR_CONTROL_REQUIRED",
                "proxy_delta_numeric": None,
                "symbol": "NAS100",
                "route_session": "tokyo_kz",
                "live_effect": False,
            }
        ),
    ]

    summary = summarize_source_control_selection(rows)

    assert summary["rows"] == 3
    assert summary["source_control_selection_class_counts"] == {
        "IMPLEMENT_DEFAULT_OFF": 1,
        "REDESIGN": 1,
        "SOURCE_REPAIR": 1,
    }
    assert summary["proxy_delta_reference_rows"] == 2
    assert summary["proxy_delta_reference_sum_not_r"] == 0.1
    assert summary["proxy_delta_reference_counted_as_r_rows"] == 0
    assert summary["opportunity_preserved_rows"] == 3


def test_control_score_selection_implements_positive_source_guard():
    row = {
        "source_component": "shadow_source_guard",
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_POSITIVE",
        "proxy_delta_numeric": 0.25,
        "live_effect": False,
    }

    selected = control_score_selection_for_row(row)

    assert selected["control_score_selection_class"] == "IMPLEMENT_DEFAULT_OFF"
    assert selected["control_score_selection_decision"] == "IMPLEMENT_DEFAULT_OFF_CONTROL_SCORE_SOURCE_GUARD"
    assert selected["downstream_path"] == "source_guard_control_candidate"
    assert selected["proxy_delta_reference_counted_as_r"] is False
    assert selected["opportunity_preserved"] is True


def test_control_score_selection_redesigns_neutral_market_gap():
    row = {
        "source_component": "market_gap_code",
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_NEUTRAL",
        "proxy_delta_numeric": 0.0,
        "live_effect": False,
    }

    selected = apply_control_score_selection(row)

    assert selected["control_score_selection_class"] == "REDESIGN"
    assert selected["control_score_selection_decision"] == "REDESIGN_CONTROL_SCORE_MARKET_GAP_NOT_POSITIVE"
    assert selected["downstream_path"] == "market_gap_context_redesign"
    assert selected["underlying_intelligence_preserved"] is True


def test_control_score_selection_routes_missing_delta_to_source_repair():
    row = {
        "source_component": "default_off_scorer_application",
        "computed_proxy_delta_class": "COMPUTED_DELTA_NOT_AVAILABLE_SOURCE_OR_CONTROL_REQUIRED",
        "proxy_delta_numeric": None,
        "live_effect": False,
    }

    selected = apply_control_score_selection(row)

    assert selected["control_score_selection_class"] == "SOURCE_REPAIR"
    assert selected["control_score_selection_decision"] == "SOURCE_REPAIR_CONTROL_SCORE_EXACT_DENOMINATOR_REQUIRED"
    assert selected["downstream_path"] == "exact_control_denominator"
    assert selected["proxy_delta_reference"] is None


def test_summarize_control_score_selection_keeps_proxy_references_non_counted():
    rows = [
        apply_control_score_selection(
            {
                "source_component": "default_off_scorer_application",
                "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
                "proxy_delta_numeric": 0.4,
                "symbol": "NAS100",
                "route_session": "ny_core",
                "live_effect": False,
            }
        ),
        apply_control_score_selection(
            {
                "source_component": "default_off_scorer_application",
                "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_WEAK_NEGATIVE",
                "proxy_delta_numeric": -0.15,
                "symbol": "NAS100",
                "route_session": "ny_core",
                "live_effect": False,
            }
        ),
        apply_control_score_selection(
            {
                "source_component": "default_off_scorer_application",
                "computed_proxy_delta_class": "COMPUTED_DELTA_NOT_AVAILABLE_SOURCE_OR_CONTROL_REQUIRED",
                "proxy_delta_numeric": None,
                "symbol": "NAS100",
                "route_session": "ny_core",
                "live_effect": False,
            }
        ),
    ]

    summary = summarize_control_score_selection(rows)

    assert summary["rows"] == 3
    assert summary["control_score_selection_class_counts"] == {
        "IMPLEMENT_DEFAULT_OFF": 1,
        "REDESIGN": 1,
        "SOURCE_REPAIR": 1,
    }
    assert summary["proxy_delta_reference_rows"] == 2
    assert summary["proxy_delta_reference_sum_not_r"] == 0.25
    assert summary["proxy_delta_reference_counted_as_r_rows"] == 0
    assert summary["opportunity_preserved_rows"] == 3


def test_claim_audit_selection_rejects_source_proxy_claim_only():
    row = {
        "main_action_class": "CURRENT_CLAIM_REJECTION",
        "implementation_implication": "do_not_use_current_source_proxy_claim_as_scorer_preserve_avoid_redesign_intelligence",
        "proxy_delta_numeric": None,
        "live_effect": False,
    }

    selected = claim_audit_selection_for_row(row)

    assert selected["claim_audit_selection_class"] == "REDESIGN"
    assert (
        selected["claim_audit_selection_decision"]
        == "REJECT_CURRENT_SOURCE_PROXY_CLAIM_PRESERVE_AVOID_REDESIGN_INTELLIGENCE"
    )
    assert selected["downstream_path"] == "avoid_redesign_context_or_source_capture"
    assert selected["opportunity_preserved"] is True


def test_claim_audit_selection_preserves_horizon_failure_intelligence():
    row = {
        "main_action_class": "CURRENT_CLAIM_REJECTION",
        "implementation_implication": "do_not_use_current_horizon_claim_as_scorer_preserve_targetability_failure_intelligence",
        "proxy_delta_numeric": None,
        "live_effect": False,
    }

    selected = apply_claim_audit_selection(row)

    assert selected["claim_audit_selection_class"] == "REDESIGN"
    assert (
        selected["claim_audit_selection_decision"]
        == "REJECT_CURRENT_HORIZON_CLAIM_PRESERVE_TARGETABILITY_FAILURE_INTELLIGENCE"
    )
    assert selected["downstream_path"] == "horizon_targetability_redesign"
    assert selected["underlying_intelligence_preserved"] is True


def test_claim_audit_selection_routes_recheck_to_source_repair():
    row = {
        "main_action_class": "RECHECK",
        "implementation_implication": "repair_horizon_targetability_before_rejecting_current_claim",
        "proxy_delta_numeric": None,
        "live_effect": False,
    }

    selected = apply_claim_audit_selection(row)

    assert selected["claim_audit_selection_class"] == "SOURCE_REPAIR"
    assert selected["claim_audit_selection_decision"] == "RECHECK_REPAIR_HORIZON_TARGETABILITY_BEFORE_DECISION"
    assert selected["downstream_path"] == "horizon_targetability_source_recheck"
    assert selected["proxy_delta_reference"] is None


def test_summarize_claim_audit_selection_keeps_zero_proxy_boundary():
    rows = [
        apply_claim_audit_selection(
            {
                "main_action_class": "CURRENT_CLAIM_REJECTION",
                "implementation_implication": (
                    "do_not_use_current_source_proxy_claim_as_scorer_preserve_avoid_redesign_intelligence"
                ),
                "symbol": "GBPJPY",
                "route_session": "tokyo_kz",
                "proxy_delta_numeric": None,
                "live_effect": False,
            }
        ),
        apply_claim_audit_selection(
            {
                "main_action_class": "RECHECK",
                "implementation_implication": "repair_horizon_targetability_before_rejecting_current_claim",
                "symbol": "NAS100",
                "route_session": "off_core_session",
                "proxy_delta_numeric": None,
                "live_effect": False,
            }
        ),
    ]

    summary = summarize_claim_audit_selection(rows)

    assert summary["rows"] == 2
    assert summary["claim_audit_selection_class_counts"] == {"REDESIGN": 1, "SOURCE_REPAIR": 1}
    assert summary["proxy_delta_reference_rows"] == 0
    assert summary["proxy_delta_reference_sum_not_r"] == 0
    assert summary["proxy_delta_reference_counted_as_r_rows"] == 0
    assert summary["opportunity_preserved_rows"] == 2
