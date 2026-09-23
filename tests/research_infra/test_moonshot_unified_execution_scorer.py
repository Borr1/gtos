import hashlib

from src.research_infra.moonshot_unified_execution_scorer import (
    classify_market_gap_candidate,
    classify_unified_branch_decision,
    concentration_artifact_class,
    rstyle_proxy_signal_class,
    score_branch_candidate,
    score_market_gap_candidate,
)
from src.research_infra.moonshot_replay_code_candidate import (
    avoid_policy_code_candidate,
    concentration_guard_code_candidate,
    entry_variant_code_candidate,
    market_gap_code_candidate,
    source_materialization_code_candidate,
)
from src.research_infra.moonshot_replay_shadow_scorer import score_code_candidate
from src.research_infra.moonshot_source_materialization import (
    classify_materialization,
    exact_missing_reason,
    materialization_proxy_fields,
)
from src.research_infra.moonshot_shadow_source_guard_bundle import (
    classify_denominator_guard,
    classify_enable_bundle,
    classify_horizon_repair_action,
    classify_score_control,
    classify_source_guard,
)
from src.research_infra.moonshot_observable_scorer_implementation import (
    control_experiment_spec,
    denominator_enforcement_spec,
    horizon_repair_execution_spec,
    observable_rule_spec,
    primitive_coverage_state,
    source_guard_policy_spec,
)
from src.research_infra.moonshot_observable_execution import (
    classify_control_execution,
    classify_coverage_action,
    classify_denominator_execution,
    classify_horizon_repair_execution as classify_observable_horizon_repair_execution,
    classify_observable_execution,
    classify_source_policy_execution,
)
from src.research_infra.moonshot_observable_action_results import (
    control_lookup_requirement_result,
    controlled_observable_score_result,
    denominator_guarded_observable_result,
    horizon_work_order_result as observable_horizon_work_order_result,
    source_policy_action_result,
)
from src.research_infra.moonshot_observable_implementation_candidates import (
    control_implementation_candidate,
    coverage_implementation_candidate,
    denominator_implementation_candidate,
    horizon_implementation_candidate,
    observable_implementation_candidate,
    source_implementation_candidate,
)
from src.research_infra.moonshot_observable_runtime_work import (
    control_scope_build_attempt,
    parse_scope_key,
    runtime_work_decision,
    source_repair_runtime_work,
)
from src.research_infra.moonshot_observable_scorer_execution import (
    control_comparator_execution,
    control_scope_execution,
    controlled_scorer_execution,
    source_repair_execution,
    source_scorer_execution,
)
from src.research_infra.moonshot_observable_implementation_synthesis import (
    control_registry_synthesis,
    control_scope_implementation_synthesis,
    denominator_guard_registry_synthesis,
    exact_control_build_action,
    observable_registry_synthesis,
    scorer_registration_synthesis,
    source_repair_action_synthesis,
)
from src.research_infra.moonshot_observable_code_integration_candidates import (
    control_registry_code_candidate,
    control_scope_code_candidate,
    denominator_guard_code_candidate,
    exact_control_builder_code_candidate,
    observable_registry_code_candidate,
    scorer_code_integration_candidate,
    source_repair_code_candidate,
)
from src.research_infra.moonshot_branch_local_observable_registry import (
    coverage_sidecar_registry_materialization,
    registry_module_materialization,
)
from src.research_infra.moonshot_branch_local_observable_scorers import scorer_module_materialization
from src.research_infra.moonshot_branch_local_source_repair_work import (
    exact_control_work_materialization,
    horizon_sidecar_work_materialization,
    source_repair_work_materialization,
)
from src.research_infra.moonshot_branch_local_repair_execution import (
    exact_control_repair_execution,
    horizon_sidecar_repair_execution,
    source_repair_work_execution,
)
from src.research_infra.moonshot_branch_local_repair_acquisition_proxy import (
    control_member_proxy_replay,
    exact_control_acquisition_requirement,
    horizon_proxy_stress,
    source_acquisition_proxy_requirement,
)
from src.research_infra.moonshot_branch_local_control_source_split import (
    control_member_relation_split,
    exact_control_relation_split,
    horizon_rebuild_split,
    scope_acquisition_plan,
    source_acquisition_split,
)
from src.research_infra.moonshot_branch_local_denominator_source_rebuild import (
    control_member_denominator_evidence,
    exact_control_scope_denominator_rebuild,
    exact_control_target_rebuild,
    horizon_materialization_rebuild,
    scope_rebuild_action,
    source_materialization_rebuild,
)
from src.research_infra.moonshot_branch_local_denominator_source_execution import (
    exact_control_scope_execution,
    exact_control_target_execution,
    horizon_rebuild_execution,
    source_rebuild_execution,
)
from src.research_infra.moonshot_branch_local_denominator_source_action_candidates import (
    acquisition_requirement_from_action,
    exact_control_scope_action_candidate,
    exact_control_target_action_candidate,
    horizon_repair_action_candidate,
    scope_rollup_action_candidate,
    source_proxy_kill_action_candidate,
)
from src.research_infra.moonshot_branch_local_denominator_source_acquisition_execution import (
    acquisition_requirement_execution,
    exact_control_scope_build_execution,
    exact_control_target_build_execution,
    horizon_repair_rescore_execution,
    source_exact_rebuild_execution,
)
from src.research_infra.moonshot_branch_local_denominator_source_resolution import (
    exact_control_scope_resolution,
    exact_control_target_resolution,
    horizon_resolution,
    implementation_resolution,
    next_compute_action,
    source_resolution,
)
from src.research_infra.moonshot_branch_local_denominator_source_action_execution import (
    guarded_scorer_spec,
    next_action_execution,
    terminal_kill_preservation,
)
from src.research_infra.moonshot_branch_local_denominator_guarded_scorers import (
    event_matches_guarded_scope,
    register_research_only_guarded_scope_proxy_scorer,
    score_guarded_scope_proxy_event,
)
from src.research_infra.moonshot_branch_local_denominator_detail_execution import (
    detail_execution_from_next_action,
    scope_detail_rollup,
    terminal_detail_from_kill,
)
from src.research_infra.moonshot_branch_local_denominator_detail_decisions import (
    default_off_implementation_decision,
    exact_control_expansion_decision,
    horizon_decision,
    scorer_behavior_decision,
    source_completeness_decision,
)
from src.research_infra.moonshot_branch_local_denominator_default_off_scorers import (
    event_matches_default_off_scope,
    register_default_off_scorer,
    score_default_off_event,
)
from src.research_infra.moonshot_branch_local_denominator_default_off_application import (
    current_claim_rejection_audit,
    default_off_application_decision,
    exact_control_blocker_decision,
    scorer_application_decision,
)
from src.research_infra.moonshot_branch_local_denominator_exact_control_effective_n import (
    control_member_effective_n_row,
    exact_control_blocker_effective_n_decision,
    exact_control_scope_effective_n_decision,
    member_effective_identity,
)
from src.research_infra.moonshot_branch_local_denominator_exact_control_construction import (
    exact_control_blocker_construction,
    exact_control_denominator_event_row,
    exact_control_scope_construction,
    sierra_translation_proxy_row,
)
from src.research_infra.moonshot_branch_local_denominator_exact_control_scorer_redesign import (
    exact_control_blocker_runtime_decision,
    exact_control_event_score,
    exact_control_scope_runtime_spec,
)
from src.research_infra.moonshot_branch_local_denominator_exact_control_implementation_candidates import (
    exact_control_blocker_implementation_candidate,
    exact_control_code_path_spec,
    exact_control_event_implementation_observation,
    exact_control_scope_implementation_candidate,
)
from src.research_infra.moonshot_branch_local_denominator_exact_control_runtime_router import (
    duplicate_scope_audit_row,
    effective_scope_registration,
    register_exact_control_code_path,
    route_exact_control_event,
)
from src.research_infra.moonshot_branch_local_denominator_exact_control_redesign_resolution import (
    redesign_blocker_resolution,
    redesign_event_signal_resolution,
    redesign_scope_resolution,
)
from src.research_infra.moonshot_branch_local_denominator_exact_control_redesign_module_integration import (
    redesign_blocker_module_integration,
    redesign_code_surface_registration,
    redesign_event_module_observation,
    redesign_scope_module_integration,
)
from src.research_infra.moonshot_branch_local_denominator_exact_control_redesign_module_execution import (
    redesign_code_surface_execution,
    redesign_event_module_execution,
    redesign_scope_module_execution,
)
from src.research_infra.moonshot_branch_local_denominator_exact_control_redesign_module_delta_comparator import (
    default_scope_candidates,
    redesign_event_module_delta_comparison,
    redesign_registry_candidate_from_comparison,
    redesign_scope_module_delta_comparison,
)
from src.research_infra.moonshot_branch_local_denominator_exact_control_redesign_final_registry import (
    final_registry_code_spec,
    final_registry_event_application,
    final_registry_row,
)
from src.research_infra.moonshot_branch_local_denominator_exact_control_redesign_registry_scorer_modules import (
    module_observation_metrics,
    scorer_module_code_candidate,
    scorer_module_event_application,
    scorer_module_registration,
)
from src.research_infra.moonshot_branch_local_unified_system_recommendation_merge import (
    rollup_row as unified_system_rollup_row,
    unified_system_candidate,
)
from src.research_infra.moonshot_branch_local_unified_system_work_order_execution import (
    work_order_from_unified_candidate,
    work_order_rollup,
)
from src.research_infra.moonshot_branch_local_unified_system_action_results import (
    action_result_from_work_order,
    action_result_rollup,
)
from src.research_infra.moonshot_branch_local_unified_system_computed_actions import (
    computed_action_result,
    computed_action_rollup,
    computed_market_timeframe_expansion_row,
)
from src.research_infra.moonshot_branch_local_unified_system_implementation_execution import (
    default_off_module_spec,
    implementation_execution_decision,
    market_transfer_decision,
    nofill_variant_comparator,
    source_builder_spec,
)
from src.research_infra.moonshot_branch_local_unified_system_executable_artifacts import (
    code_surface_artifact,
    executable_artifact_decision,
    market_source_action,
    nofill_comparator_outcome,
    source_control_builder_execution,
)
from src.research_infra.moonshot_branch_local_unified_system_runtime_surfaces import (
    event_matches_runtime_surface,
    nofill_replay_surface,
    runtime_surface_decision,
    runtime_surface_self_test,
    score_runtime_surface_event,
    scorer_registry_surface,
    source_replay_surface,
)
from src.research_infra.moonshot_branch_local_unified_system_candidate_synthesis import (
    candidate_execution_row,
    candidate_role_from_emission,
    nofill_component_row,
    scorer_component_row,
    source_component_row,
)
from src.research_infra.moonshot_branch_local_unified_system_candidate_runtime import (
    candidate_runtime_decision,
    candidate_runtime_family,
    candidate_runtime_self_test,
    component_runtime_binding,
    event_matches_candidate_runtime,
    execute_candidate_runtime,
    market_runtime_binding,
)
from src.research_infra.moonshot_branch_local_unified_system_candidate_dispatch import (
    candidate_dispatch_decision,
    candidate_dispatch_family,
    candidate_dispatch_self_test,
    component_dispatch_plan,
    event_matches_candidate_dispatch,
    execute_candidate_dispatch,
    market_transfer_dispatch,
)
from src.research_infra.moonshot_branch_local_unified_system_candidate_materialization import (
    candidate_materialization_decision,
    candidate_materialization_family,
    guard_enforcement_materialization,
    market_action_materialization,
    nofill_comparator_materialization,
    scorer_code_surface_materialization,
    source_control_builder_materialization,
)
from src.research_infra.moonshot_branch_local_unified_system_candidate_implementation import (
    candidate_implementation_decision,
    guard_registry_action as candidate_guard_registry_action,
    market_priority_action as candidate_market_priority_action,
    nofill_execution_action as candidate_nofill_execution_action,
    scorer_code_integration_candidate as candidate_scorer_code_integration_candidate,
    source_control_run_action as candidate_source_control_run_action,
)
from src.research_infra.moonshot_branch_local_unified_system_candidate_implementation_execution import (
    candidate_implementation_execution_result,
    guard_registry_artifact as candidate_guard_registry_artifact,
    market_priority_execution_output as candidate_market_priority_execution_output,
    nofill_comparator_output as candidate_nofill_comparator_output,
    scorer_module_artifact as candidate_scorer_module_artifact,
    source_control_run_output as candidate_source_control_run_output,
)
from src.research_infra.moonshot_branch_local_unified_system_candidate_execution_integration import (
    execution_integration_decision as candidate_execution_integration_decision,
    guard_bound_integration_row as candidate_guard_bound_integration_row,
    market_system_integration_row as candidate_market_system_integration_row,
    nofill_result_row as candidate_nofill_result_row,
    registry_module_row as candidate_registry_module_row,
    source_control_result_row as candidate_source_control_result_row,
)
from src.research_infra.moonshot_branch_local_unified_system_candidate_integrated_scoring_result import (
    default_off_module_result as candidate_default_off_module_result,
    guard_binding_result as candidate_guard_binding_result,
    integrated_decision as candidate_integrated_scoring_decision,
    market_transfer_decision as candidate_market_transfer_decision,
    nofill_comparator_result_table as candidate_nofill_comparator_result_table,
    source_control_builder_result as candidate_source_control_builder_result,
)
from src.research_infra.moonshot_branch_local_unified_system_candidate_integrated_result_execution import (
    guard_dispatch_output as candidate_guard_dispatch_output,
    integrated_result_execution as candidate_integrated_result_execution,
    market_transfer_dispatch as candidate_market_transfer_dispatch,
    nofill_comparator_execution_output as candidate_nofill_comparator_execution_output,
    scorer_registry_dispatch as candidate_scorer_registry_dispatch,
    source_control_execution_output as candidate_source_control_execution_output,
)
from src.research_infra.moonshot_integrated_result_numeric_scorer import (
    classify_target_stop_order as numeric_classify_target_stop_order,
    cost_stress_evidence as numeric_cost_stress_evidence,
    exact_r_evidence as numeric_exact_r_evidence,
    numeric_result_row as numeric_integrated_result_row,
    numeric_rollup as numeric_integrated_rollup,
    proxy_r_evidence as numeric_proxy_r_evidence,
)
from src.research_infra.moonshot_numeric_decision_modules import (
    avoid_inverse_filter_spec as numeric_avoid_inverse_filter_spec,
    event_matches_numeric_module,
    execute_numeric_module_event,
    module_record_from_numeric_result,
    source_geometry_repair_spec as numeric_source_geometry_repair_spec,
)
from src.research_infra.moonshot_numeric_module_registry_router import (
    build_numeric_module_registry,
    event_from_numeric_result,
    route_numeric_event,
    router_application_row,
    scope_router_decision,
    source_repair_execution_row as numeric_source_repair_execution_row,
)
from src.research_infra.moonshot_branch_local_shadow_scorer_compute import (
    build_shadow_scorer_registry,
    exact_r_from_geometry,
    repair_queue_row as numeric_shadow_repair_queue_row,
    score_scope_event as numeric_shadow_score_scope_event,
    scored_numeric_event,
)
from src.research_infra.moonshot_broker_source_repair import (
    build_source_index as broker_source_build_source_index,
    implementation_decision_row as broker_source_implementation_decision_row,
    repair_result_row as broker_source_repair_result_row,
    source_observation as broker_source_observation,
)
from src.research_infra.moonshot_repaired_proxy_scope_scorer import (
    build_registry as repaired_proxy_build_registry,
    event_application_row as repaired_proxy_event_application_row,
    registry_row_from_decision as repaired_proxy_registry_row_from_decision,
    score_event_with_repaired_scope,
)
from src.research_infra.moonshot_repaired_proxy_execution_specs import (
    avoid_comparator_spec_from_event as repaired_proxy_avoid_comparator_spec_from_event,
    default_off_scorer_spec_from_event as repaired_proxy_default_off_scorer_spec_from_event,
    exact_proxy_bridge_row as repaired_proxy_exact_proxy_bridge_row,
    repair_task_from_event as repaired_proxy_repair_task_from_event,
    summarize_cost_by_symbol as repaired_proxy_summarize_cost_by_symbol,
)
from src.research_infra.moonshot_repaired_proxy_execution_registry import (
    avoid_comparator_execution_row as repaired_proxy_avoid_comparator_execution_row,
    build_execution_registry as repaired_proxy_build_execution_registry,
    execution_event_application_row as repaired_proxy_execution_event_application_row,
    market_replay_population_row as repaired_proxy_market_replay_population_row,
    registry_symbol_counts as repaired_proxy_registry_symbol_counts,
    repair_execution_row as repaired_proxy_repair_execution_row,
)
from src.research_infra.moonshot_repaired_proxy_replay_population import (
    control_population_contract_row as repaired_proxy_control_population_contract_row,
    replay_scope_contract_row as repaired_proxy_replay_scope_contract_row,
    repair_scope_rows_from_executions as repaired_proxy_repair_scope_rows_from_executions,
    source_probe_row as repaired_proxy_source_probe_row,
)
from src.research_infra.moonshot_repaired_proxy_replay_numeric_execution import (
    control_numeric_event_row as repaired_proxy_control_numeric_event_row,
    replay_numeric_event_row as repaired_proxy_replay_numeric_event_row,
    source_numeric_metric_row as repaired_proxy_source_numeric_metric_row,
)
from src.research_infra.moonshot_repaired_proxy_replay_score_rerun import (
    control_context_rows as repaired_proxy_control_context_rows,
    replay_context_modifier as repaired_proxy_replay_context_modifier,
    rerun_score_row as repaired_proxy_rerun_score_row,
)
from src.research_infra.moonshot_repaired_proxy_score_bridge_rebuild import (
    rebuilt_bridge_row as repaired_proxy_rebuilt_bridge_row,
    score_context_index as repaired_proxy_score_context_index,
    score_scope_summary_rows as repaired_proxy_score_scope_summary_rows,
    scope_summary_join_lookups as repaired_proxy_scope_summary_join_lookups,
    select_scope_summary as repaired_proxy_select_scope_summary,
)
from src.research_infra.moonshot_repaired_proxy_score_bridge_action_packet import (
    action_scope_rows as repaired_proxy_action_scope_rows,
    comparator_packet_rows as repaired_proxy_comparator_packet_rows,
    repair_routing_rows as repaired_proxy_repair_routing_rows,
)
from src.research_infra.moonshot_repaired_proxy_comparator_input_repair_work import (
    comparator_input_rows as repaired_proxy_comparator_input_rows,
    repair_work_order_rows as repaired_proxy_repair_work_order_rows,
    rerun_plan_rows as repaired_proxy_rerun_plan_rows,
)
from src.research_infra.moonshot_repaired_proxy_repair_execution import (
    field_coverage_rows as repaired_proxy_repair_field_coverage_rows,
    repair_execution_rows as repaired_proxy_repair_execution_rows,
    rerun_gate_rows as repaired_proxy_repair_rerun_gate_rows,
)
from src.research_infra.moonshot_repaired_proxy_repair_acquisition import (
    acquisition_batch_rows as repaired_proxy_acquisition_batch_rows,
    acquisition_requirement_rows as repaired_proxy_acquisition_requirement_rows,
    source_candidate_rows as repaired_proxy_source_candidate_rows,
)
from src.research_infra.moonshot_repaired_proxy_repair_acquisition_lookup import (
    field_fulfillment_rows as repaired_proxy_lookup_field_fulfillment_rows,
    lookup_execution_rows as repaired_proxy_lookup_execution_rows,
    repair_rerun_readiness_rows as repaired_proxy_lookup_repair_rerun_readiness_rows,
    scan_source_records as repaired_proxy_scan_source_records,
)
from src.research_infra.moonshot_repaired_proxy_repair_source_exhaustion import (
    repair_execution_exhaustion_rows as repaired_proxy_repair_execution_exhaustion_rows,
    requirement_exhaustion_rows as repaired_proxy_requirement_exhaustion_rows,
    source_family_exhaustion_rows as repaired_proxy_source_family_exhaustion_rows,
)
from src.research_infra.moonshot_repaired_proxy_comparator_execution import (
    comparator_action_rows as repaired_proxy_comparator_action_rows,
    comparator_execution_rows as repaired_proxy_comparator_execution_rows,
    proxy_r_surface_rows as repaired_proxy_comparator_proxy_r_surface_rows,
)
from src.research_infra.moonshot_repaired_proxy_symbol_action_packet import (
    comparator_nonregistration_rows as repaired_proxy_symbol_comparator_nonregistration_rows,
    comparator_registration_rows as repaired_proxy_symbol_comparator_registration_rows,
    symbol_action_packet_rows as repaired_proxy_symbol_action_packet_rows,
    symbol_proxy_surface_rows as repaired_proxy_symbol_proxy_surface_rows,
)
from src.research_infra.moonshot_repaired_proxy_registration_specs import (
    nonregistration_context_rows as repaired_proxy_registration_nonregistration_context_rows,
    registration_spec_rows as repaired_proxy_registration_spec_rows,
    runtime_guard_rows as repaired_proxy_registration_runtime_guard_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_candidate_bundle import (
    guard_check_rows as repaired_proxy_runtime_candidate_guard_check_rows,
    nonregistration_review_rows as repaired_proxy_runtime_candidate_nonregistration_review_rows,
    runtime_candidate_rows as repaired_proxy_runtime_candidate_rows,
    symbol_candidate_bundle_rows as repaired_proxy_symbol_candidate_bundle_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_candidate_registry import (
    evaluate_runtime_candidate_event as repaired_proxy_evaluate_runtime_candidate_event,
    registry_event_probe_rows as repaired_proxy_registry_event_probe_rows,
    registry_module_rows as repaired_proxy_registry_module_rows,
    symbol_registry_rollup_rows as repaired_proxy_symbol_registry_rollup_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_execution import (
    replay_module_match_rows as repaired_proxy_replay_module_match_rows,
    replay_registry_execution_rows as repaired_proxy_replay_registry_execution_rows,
    replay_symbol_outcome_rows as repaired_proxy_replay_symbol_outcome_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_recommendation import (
    replay_signal_route_rows as repaired_proxy_replay_signal_route_rows,
    symbol_recommendation_rows as repaired_proxy_symbol_recommendation_rows,
    unmatched_scope_review_rows as repaired_proxy_unmatched_scope_review_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_inventory_alignment import (
    signal_inventory_alignment_rows as repaired_proxy_signal_inventory_alignment_rows,
    symbol_inventory_alignment_rows as repaired_proxy_symbol_inventory_alignment_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_advancement import (
    action_conflict_review_rows as repaired_proxy_action_conflict_review_rows,
    advancement_decision_rows as repaired_proxy_advancement_decision_rows,
    represented_surface_rows as repaired_proxy_represented_surface_rows,
    symbol_advancement_rows as repaired_proxy_symbol_advancement_rows,
    unmatched_scope_advancement_rows as repaired_proxy_unmatched_scope_advancement_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_comparison_packet import (
    comparison_packet_rows as repaired_proxy_comparison_packet_rows,
    comparison_scope_rows as repaired_proxy_comparison_scope_rows,
    review_sidecar_rows as repaired_proxy_review_sidecar_rows,
    system_comparison_rows as repaired_proxy_system_comparison_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_comparison_summary import (
    scope_comparison_rows as repaired_proxy_summary_scope_comparison_rows,
    sidecar_attachment_rows as repaired_proxy_summary_sidecar_attachment_rows,
    signal_comparison_rows as repaired_proxy_summary_signal_comparison_rows,
    system_summary_rows as repaired_proxy_summary_system_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_sidecar_aware_score import (
    packet_score_rows as repaired_proxy_packet_score_rows,
    scope_score_rows as repaired_proxy_scope_score_rows,
    sidecar_score_impact_rows as repaired_proxy_sidecar_score_impact_rows,
    system_score_rows as repaired_proxy_system_score_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_sidecar_aware_decision import (
    packet_decision_rows as repaired_proxy_packet_decision_rows,
    scope_decision_rows as repaired_proxy_scope_decision_rows,
    sidecar_decision_rows as repaired_proxy_sidecar_decision_rows,
    system_decision_rows as repaired_proxy_system_decision_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_decision_bundle import (
    final_packet_bundle_rows as repaired_proxy_final_packet_bundle_rows,
    final_scope_bundle_rows as repaired_proxy_final_scope_bundle_rows,
    final_sidecar_bundle_rows as repaired_proxy_final_sidecar_bundle_rows,
    system_bundle_rows as repaired_proxy_system_bundle_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_decision_application import (
    packet_application_rows as repaired_proxy_packet_application_rows,
    scope_application_rows as repaired_proxy_scope_application_rows,
    sidecar_application_rows as repaired_proxy_sidecar_application_rows,
    system_application_rows as repaired_proxy_system_application_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_decision_application_comparison import (
    advance_packet_rows as repaired_proxy_advance_packet_rows,
    held_review_scope_rows as repaired_proxy_held_review_scope_rows,
    packet_scope_comparison_rows as repaired_proxy_packet_scope_comparison_rows,
    scope_review_comparison_rows as repaired_proxy_scope_review_comparison_rows,
    sidecar_scope_comparison_rows as repaired_proxy_sidecar_scope_comparison_rows,
    system_review_comparison_rows as repaired_proxy_system_review_comparison_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_ranked_packet import (
    held_scope_context_rows as repaired_proxy_held_scope_context_rows,
    next_branch_local_packet_rows as repaired_proxy_next_branch_local_packet_rows,
    ranked_advance_packet_rows as repaired_proxy_ranked_advance_packet_rows,
    system_ranked_packet_rows as repaired_proxy_system_ranked_packet_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_implementation_steps import (
    implementation_action_rows as repaired_proxy_implementation_action_rows,
    implementation_next_step_rows as repaired_proxy_implementation_next_step_rows,
    implementation_scope_rollup_rows as repaired_proxy_implementation_scope_rollup_rows,
    system_implementation_step_rows as repaired_proxy_system_implementation_step_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_spec_materialization import (
    comparator_spec_rows as repaired_proxy_comparator_spec_rows,
    scorer_spec_rows as repaired_proxy_scorer_spec_rows,
    spec_batch_rows as repaired_proxy_spec_batch_rows,
    system_spec_materialization_rows as repaired_proxy_system_spec_materialization_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_spec_execution import (
    comparator_spec_execution_rows as repaired_proxy_comparator_spec_execution_rows,
    scorer_spec_execution_rows as repaired_proxy_scorer_spec_execution_rows,
    spec_execution_result_rows as repaired_proxy_spec_execution_result_rows,
    spec_execution_scope_rollup_rows as repaired_proxy_spec_execution_scope_rollup_rows,
    system_spec_execution_rows as repaired_proxy_system_spec_execution_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_performance import (
    aggregate_performance_rows as repaired_proxy_aggregate_performance_rows,
    missing_simulated_field_rows as repaired_proxy_missing_simulated_field_rows,
    performance_rows as repaired_proxy_performance_rows,
    system_performance_rows as repaired_proxy_system_performance_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_repair import (
    aggregate_geometry_rows as repaired_proxy_aggregate_geometry_rows,
    geometry_repair_rows as repaired_proxy_geometry_repair_rows,
    missing_geometry_field_rows as repaired_proxy_missing_geometry_field_rows,
    system_geometry_rows as repaired_proxy_system_geometry_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_implementation import (
    aggregate_implementation_rows as repaired_proxy_aggregate_geometry_implementation_rows,
    geometry_implementation_rows as repaired_proxy_geometry_implementation_rows,
    implementation_self_test_rows as repaired_proxy_geometry_implementation_self_test_rows,
    system_implementation_rows as repaired_proxy_system_geometry_implementation_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_tables import (
    avoid_intelligence_table_rows as repaired_proxy_geometry_avoid_table_rows,
    kill_table_rows as repaired_proxy_geometry_kill_table_rows,
    redirection_task_rows as repaired_proxy_geometry_redirection_task_rows,
    scorer_table_rows as repaired_proxy_geometry_scorer_table_rows,
    system_table_rows as repaired_proxy_system_geometry_table_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_execution import (
    aggregate_table_execution_rows as repaired_proxy_aggregate_geometry_table_execution_rows,
    avoid_table_execution_rows as repaired_proxy_avoid_geometry_table_execution_rows,
    scorer_table_execution_rows as repaired_proxy_scorer_geometry_table_execution_rows,
    source_gap_rows as repaired_proxy_geometry_table_source_gap_rows,
    system_table_execution_rows as repaired_proxy_system_geometry_table_execution_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_observations import (
    aggregate_observation_rows as repaired_proxy_aggregate_geometry_table_observation_rows,
    avoid_observation_rows as repaired_proxy_avoid_geometry_table_observation_rows,
    scorer_observation_rows as repaired_proxy_scorer_geometry_table_observation_rows,
    source_gap_preservation_rows as repaired_proxy_geometry_table_observation_source_gap_rows,
    system_observation_rows as repaired_proxy_system_geometry_table_observation_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_code_candidates import (
    aggregate_code_candidate_rows as repaired_proxy_aggregate_geometry_table_code_candidate_rows,
    avoid_code_candidate_rows as repaired_proxy_avoid_geometry_table_code_candidate_rows,
    scorer_code_candidate_rows as repaired_proxy_scorer_geometry_table_code_candidate_rows,
    source_gap_code_candidate_rows as repaired_proxy_geometry_table_source_gap_code_candidate_rows,
    system_code_candidate_rows as repaired_proxy_system_geometry_table_code_candidate_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_code_surfaces import (
    aggregate_code_surface_rows as repaired_proxy_aggregate_geometry_table_code_surface_rows,
    avoid_code_surface_rows as repaired_proxy_avoid_geometry_table_code_surface_rows,
    execute_code_surface as repaired_proxy_execute_geometry_table_code_surface,
    scorer_code_surface_rows as repaired_proxy_scorer_geometry_table_code_surface_rows,
    surface_self_test_rows as repaired_proxy_geometry_table_code_surface_self_test_rows,
    system_code_surface_rows as repaired_proxy_system_geometry_table_code_surface_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_code_surface_execution import (
    aggregate_code_surface_execution_rows as repaired_proxy_aggregate_geometry_table_code_surface_execution_rows,
    code_surface_execution_rows as repaired_proxy_geometry_table_code_surface_execution_rows,
    execution_issue_rows as repaired_proxy_geometry_table_code_surface_execution_issue_rows,
    system_code_surface_execution_rows as repaired_proxy_system_geometry_table_code_surface_execution_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_recommendations import (
    aggregate_recommendation_rows as repaired_proxy_aggregate_geometry_table_recommendation_rows,
    recommendation_rows as repaired_proxy_geometry_table_recommendation_rows,
    system_recommendation_rows as repaired_proxy_system_geometry_table_recommendation_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_performance_matrix import (
    aggregate_matrix_rows as repaired_proxy_aggregate_geometry_table_performance_matrix_rows,
    performance_matrix_rows as repaired_proxy_geometry_table_performance_matrix_rows,
    simulated_missing_field_rows as repaired_proxy_geometry_table_performance_matrix_missing_rows,
    source_join_issue_rows as repaired_proxy_geometry_table_performance_matrix_join_rows,
    system_matrix_rows as repaired_proxy_system_geometry_table_performance_matrix_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_matrix_surfaces import (
    aggregate_surface_rows as repaired_proxy_aggregate_geometry_table_matrix_surface_rows,
    avoid_surface_rows as repaired_proxy_geometry_table_matrix_avoid_surface_rows,
    execute_matrix_surface as repaired_proxy_execute_geometry_table_matrix_surface,
    scorer_surface_rows as repaired_proxy_geometry_table_matrix_scorer_surface_rows,
    surface_self_test_rows as repaired_proxy_geometry_table_matrix_surface_self_test_rows,
    system_surface_rows as repaired_proxy_system_geometry_table_matrix_surface_rows,
    terminal_decision_rows as repaired_proxy_geometry_table_matrix_terminal_rows,
)
from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_matrix_surface_execution import (
    aggregate_execution_rows as repaired_proxy_aggregate_geometry_table_matrix_surface_execution_rows,
    execution_issue_rows as repaired_proxy_geometry_table_matrix_surface_execution_issue_rows,
    surface_execution_rows as repaired_proxy_geometry_table_matrix_surface_execution_rows,
    system_execution_rows as repaired_proxy_system_geometry_table_matrix_surface_execution_rows,
    terminal_execution_rows as repaired_proxy_geometry_table_matrix_terminal_execution_rows,
)
from src.research_infra.moonshot_expanded_market_proxy_r_performance import (
    aggregate_performance_rows as aggregate_expanded_market_performance_rows,
    load_ohlc_rows as load_expanded_market_ohlc_rows,
    noncomputable_row as expanded_market_noncomputable_row,
    parse_dt as parse_expanded_market_dt,
    performance_row_from_score as expanded_market_performance_row_from_score,
    score_source_session_horizon as score_expanded_market_source_session_horizon,
)
from src.research_infra.moonshot_expanded_market_side_pair_robustness import (
    aggregate_side_pair_rows as aggregate_expanded_market_side_pair_rows,
    side_pair_rows as expanded_market_side_pair_rows,
    system_side_pair_rows as expanded_market_system_side_pair_rows,
)
from src.research_infra.moonshot_expanded_market_temporal_robustness import (
    aggregate_temporal_rows as aggregate_expanded_market_temporal_rows,
    system_temporal_rows as expanded_market_system_temporal_rows,
    temporal_pair_rows as expanded_market_temporal_pair_rows,
    temporal_profile as expanded_market_temporal_profile,
)
from src.research_infra.moonshot_expanded_market_intrabar_geometry import (
    aggregate_intrabar_rows as aggregate_expanded_market_intrabar_rows,
    geometry_row_from_profile as expanded_market_intrabar_geometry_row_from_profile,
    intrabar_profile as expanded_market_intrabar_profile,
    intrabar_path_result as expanded_market_intrabar_path_result,
)
from src.research_infra.moonshot_expanded_market_implementation_selection import (
    aggregate_implementation_selection_rows as aggregate_expanded_market_implementation_selection_rows,
    implementation_selection_rows as expanded_market_implementation_selection_rows,
    system_implementation_selection_rows as expanded_market_system_implementation_selection_rows,
)
from src.research_infra.moonshot_expanded_market_code_candidates import (
    aggregate_code_candidate_rows as aggregate_expanded_market_code_candidate_rows,
    candidate_matches_scope as expanded_market_candidate_matches_scope,
    code_candidate_rows as expanded_market_code_candidate_rows,
    system_code_candidate_rows as expanded_market_system_code_candidate_rows,
)
from src.research_infra.moonshot_expanded_market_code_candidate_execution import (
    aggregate_execution_rows as aggregate_expanded_market_code_candidate_execution_rows,
    execute_code_candidates as execute_expanded_market_code_candidates,
    system_execution_rows as expanded_market_system_code_candidate_execution_rows,
)
from src.research_infra.moonshot_expanded_market_leakage_reduction import (
    aggregate_reduction_rows as aggregate_expanded_market_leakage_reduction_rows,
    leakage_reduction_rows as expanded_market_leakage_reduction_rows,
    system_reduction_rows as expanded_market_system_leakage_reduction_rows,
)
from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (
    aggregate_execution_rows as aggregate_expanded_market_reduced_surface_execution_rows,
    execute_reduced_surfaces as execute_expanded_market_reduced_surfaces,
    reduced_surface_rows as expanded_market_reduced_surface_rows,
    self_test_rows as expanded_market_reduced_surface_self_test_rows,
    system_execution_rows as expanded_market_system_reduced_surface_execution_rows,
)
from src.research_infra.moonshot_expanded_market_reduced_implementation_candidates import (
    aggregate_candidate_rows as aggregate_expanded_market_reduced_implementation_candidate_rows,
    implementation_candidate_rows as expanded_market_reduced_implementation_candidate_rows,
    system_candidate_rows as expanded_market_system_reduced_implementation_candidate_rows,
)
from src.research_infra.moonshot_expanded_market_final_branch_artifacts import (
    aggregate_artifact_rows as aggregate_expanded_market_final_artifact_rows,
    artifact_evidence_execution_rows as expanded_market_final_artifact_evidence_execution_rows,
    final_artifact_rows as expanded_market_final_artifact_rows,
    system_artifact_rows as expanded_market_system_final_artifact_rows,
)
from src.research_infra.moonshot_expanded_market_portfolio_artifact_selection import (
    aggregate_selection_rows as aggregate_expanded_market_portfolio_selection_rows,
    portfolio_selection_rows as expanded_market_portfolio_selection_rows,
    system_selection_rows as expanded_market_system_portfolio_selection_rows,
)
from src.research_infra.moonshot_expanded_market_deconcentration_execution import (
    aggregate_deconcentration_rows as aggregate_expanded_market_deconcentration_rows,
    deconcentration_rows as expanded_market_deconcentration_rows,
    system_deconcentration_rows as expanded_market_system_deconcentration_rows,
)
from src.research_infra.moonshot_expanded_market_final_review_execution import (
    aggregate_final_review_rows as aggregate_expanded_market_final_review_rows,
    final_review_rows as expanded_market_final_review_rows,
    system_final_review_rows as expanded_market_system_final_review_rows,
)
from src.research_infra.moonshot_expanded_market_package_slices import (
    aggregate_package_rows as aggregate_expanded_market_package_rows,
    package_slice_rows as expanded_market_package_slice_rows,
    system_package_rows as expanded_market_system_package_rows,
)
from src.research_infra.moonshot_expanded_market_package_review_execution import (
    aggregate_review_artifact_rows as aggregate_expanded_market_package_review_rows,
    package_review_execution_rows as expanded_market_package_review_execution_rows,
    system_review_execution_rows as expanded_market_system_package_review_execution_rows,
)
from src.research_infra.moonshot_expanded_market_package_review_preservation import (
    aggregate_preservation_rows as aggregate_expanded_market_package_preservation_rows,
    package_review_preservation_rows as expanded_market_package_review_preservation_rows,
    system_preservation_rows as expanded_market_system_package_preservation_rows,
)
from src.research_infra.moonshot_expanded_market_final_implementation_decisions import (
    aggregate_final_implementation_decision_rows as aggregate_expanded_market_final_implementation_decision_rows,
    final_implementation_decision_rows as expanded_market_final_implementation_decision_rows,
    system_final_implementation_decision_rows as expanded_market_system_final_implementation_decision_rows,
)
from src.research_infra.moonshot_expanded_market_unpackaged_evidence_resolution import (
    system_resolution_rows as expanded_market_system_unpackaged_evidence_resolution_rows,
    unpackaged_evidence_resolution_rows as expanded_market_unpackaged_evidence_resolution_rows,
)
from src.research_infra.moonshot_expanded_market_repackage_execution import (
    expanded_market_repackage_execution_rows,
    system_repackage_execution_rows as expanded_market_system_repackage_execution_rows,
)
from src.research_infra.moonshot_expanded_market_repackage_final_decisions import (
    repackage_final_decision_rows as expanded_market_repackage_final_decision_rows,
    system_repackage_final_decision_rows as expanded_market_system_repackage_final_decision_rows,
)
from src.research_infra.moonshot_expanded_market_unified_final_decisions import (
    system_unified_final_decision_rows as expanded_market_system_unified_final_decision_rows,
    unified_final_decision_rows as expanded_market_unified_final_decision_rows,
)
from src.research_infra.moonshot_expanded_market_unified_numeric_evidence import (
    system_unified_numeric_evidence_rows as expanded_market_system_unified_numeric_evidence_rows,
    unified_numeric_evidence_rows as expanded_market_unified_numeric_evidence_rows,
)
from src.research_infra.moonshot_expanded_market_unified_stress_qualification import (
    system_unified_stress_qualification_rows as expanded_market_system_unified_stress_qualification_rows,
    unified_stress_qualification_rows as expanded_market_unified_stress_qualification_rows,
)
from src.research_infra.moonshot_expanded_market_unified_implementation_actions import (
    system_unified_implementation_action_rows as expanded_market_system_unified_implementation_action_rows,
    unified_implementation_action_rows as expanded_market_unified_implementation_action_rows,
)
from src.research_infra.moonshot_expanded_market_unified_action_surfaces import (
    system_unified_action_surface_rows as expanded_market_system_unified_action_surface_rows,
    unified_action_surface_rows as expanded_market_unified_action_surface_rows,
)
from src.research_infra.moonshot_expanded_market_unified_action_surface_execution import (
    system_unified_action_surface_execution_rows as expanded_market_system_unified_action_surface_execution_rows,
    unified_action_surface_execution_rows as expanded_market_unified_action_surface_execution_rows,
)
from src.research_infra.moonshot_expanded_market_unified_strict_action_surface_repair import (
    system_unified_strict_action_surface_repair_rows as expanded_market_system_unified_strict_action_surface_repair_rows,
    unified_strict_action_surface_repair_rows as expanded_market_unified_strict_action_surface_repair_rows,
)
from src.research_infra.moonshot_expanded_market_unified_strict_implementation_readiness import (
    system_unified_strict_implementation_readiness_rows as expanded_market_system_unified_strict_implementation_readiness_rows,
    unified_strict_implementation_readiness_rows as expanded_market_unified_strict_implementation_readiness_rows,
)
from src.research_infra.moonshot_expanded_market_unified_strict_artifact_execution import (
    system_unified_strict_artifact_execution_rows as expanded_market_system_unified_strict_artifact_execution_rows,
    unified_strict_artifact_execution_rows as expanded_market_unified_strict_artifact_execution_rows,
)
from src.research_infra.moonshot_expanded_market_supplemental_source_performance import (
    aggregate_supplemental_performance_rows as aggregate_expanded_market_supplemental_source_performance_rows,
    copy_seed_floor_performance_rows as expanded_market_copy_seed_floor_performance_rows,
    missing_simulated_field_rows as expanded_market_supplemental_missing_simulated_field_rows,
    supplemental_performance_rows as expanded_market_supplemental_source_performance_rows,
    system_supplemental_performance_rows as expanded_market_system_supplemental_source_performance_rows,
)
from src.research_infra.moonshot_expanded_market_source_consensus_robustness import (
    aggregate_consensus_rows as aggregate_expanded_market_source_consensus_rows,
    source_consensus_rows as expanded_market_source_consensus_rows,
    system_source_consensus_rows as expanded_market_system_source_consensus_rows,
)
from src.research_infra.moonshot_expanded_market_consensus_deconcentration import (
    aggregate_deconcentration_rows as aggregate_expanded_market_consensus_deconcentration_rows,
    deconcentration_rows as expanded_market_consensus_deconcentration_rows,
    system_deconcentration_rows as expanded_market_system_consensus_deconcentration_rows,
)
from src.research_infra.moonshot_expanded_market_deconcentrated_implementation_selection import (
    aggregate_selection_rows as aggregate_expanded_market_deconcentrated_selection_rows,
    selection_rows as expanded_market_deconcentrated_selection_rows,
    system_selection_rows as expanded_market_system_deconcentrated_selection_rows,
)
from src.research_infra.moonshot_expanded_market_deconcentrated_scorer_surfaces import (
    matches_surface as expanded_market_deconcentrated_surface_matches,
    scorer_surface_rows as expanded_market_deconcentrated_scorer_surface_rows,
    system_surface_rows as expanded_market_system_deconcentrated_scorer_surface_rows,
)
from src.research_infra.moonshot_expanded_market_deconcentrated_scorer_surface_execution import (
    aggregate_execution_rows as aggregate_expanded_market_deconcentrated_scorer_surface_execution_rows,
    surface_execution_rows as expanded_market_deconcentrated_scorer_surface_execution_rows,
    system_execution_rows as expanded_market_system_deconcentrated_scorer_surface_execution_rows,
)
from src.research_infra.moonshot_expanded_market_action_class_performance import (
    action_class_performance_rows as expanded_market_action_class_performance_rows,
    aggregate_action_class_rows as aggregate_expanded_market_action_class_performance_rows,
    system_action_class_rows as expanded_market_system_action_class_performance_rows,
)
from src.research_infra.moonshot_expanded_market_source_repair_reachability import (
    aggregate_reachability_rows as aggregate_expanded_market_source_repair_reachability_rows,
    source_repair_reachability_rows as expanded_market_source_repair_reachability_rows,
    system_reachability_rows as expanded_market_system_source_repair_reachability_rows,
)
from src.research_infra.moonshot_expanded_market_alternate_source_scoring import (
    aggregate_scoring_rows as aggregate_expanded_market_alternate_source_scoring_rows,
    alternate_source_scoring_rows as expanded_market_alternate_source_scoring_rows,
    system_scoring_rows as expanded_market_system_alternate_source_scoring_rows,
)
from src.research_infra.moonshot_expanded_market_implementation_priority import (
    aggregate_priority_rows as aggregate_expanded_market_implementation_priority_rows,
    implementation_priority_rows as expanded_market_implementation_priority_rows,
    system_priority_rows as expanded_market_system_implementation_priority_rows,
)
from src.research_infra.moonshot_expanded_market_impl_candidates import (
    aggregate_impl_candidate_rows as aggregate_expanded_market_impl_candidate_rows,
    implementation_candidate_rows as expanded_market_impl_candidate_rows,
    matches_candidate_scope as expanded_market_impl_candidate_matches,
    system_impl_candidate_rows as expanded_market_system_impl_candidate_rows,
)
from src.research_infra.moonshot_expanded_market_impl_candidate_execution import (
    aggregate_execution_rows as aggregate_expanded_market_impl_candidate_execution_rows,
    execution_rows as expanded_market_impl_candidate_execution_rows,
)
from src.research_infra.moonshot_expanded_market_repair_application_table import (
    aggregate_application_rows as aggregate_expanded_market_repair_application_rows,
    application_rows as expanded_market_repair_application_rows,
)
from src.research_infra.moonshot_expanded_market_repair_application_execution import (
    aggregate_execution_rows as aggregate_expanded_market_repair_application_execution_rows,
    execution_rows as expanded_market_repair_application_execution_rows,
)
from src.research_infra.moonshot_expanded_market_repair_final_artifacts import (
    aggregate_final_artifact_rows as aggregate_expanded_market_repair_final_artifact_rows,
    final_artifact_rows as expanded_market_repair_final_artifact_rows,
)
from src.research_infra.moonshot_expanded_market_repair_final_artifact_execution import (
    aggregate_execution_rows as aggregate_expanded_market_repair_final_artifact_execution_rows,
    execution_rows as expanded_market_repair_final_artifact_execution_rows,
)
from src.research_infra.moonshot_expanded_market_repair_implementation_handoff import (
    aggregate_handoff_rows as aggregate_expanded_market_repair_implementation_handoff_rows,
    implementation_handoff_rows as expanded_market_repair_implementation_handoff_rows,
)
from src.research_infra.moonshot_expanded_market_repair_implementation_handoff_execution import (
    aggregate_execution_rows as aggregate_expanded_market_repair_implementation_handoff_execution_rows,
    execution_rows as expanded_market_repair_implementation_handoff_execution_rows,
)
from src.research_infra.moonshot_expanded_market_repair_implementation_acceptance import (
    acceptance_rows as expanded_market_repair_implementation_acceptance_rows,
    aggregate_acceptance_rows as aggregate_expanded_market_repair_implementation_acceptance_rows,
)
from src.research_infra.moonshot_expanded_market_repair_implementation_acceptance_execution import (
    aggregate_execution_rows as aggregate_expanded_market_repair_implementation_acceptance_execution_rows,
    execution_rows as expanded_market_repair_implementation_acceptance_execution_rows,
)


def test_unified_branch_decision_promotes_proxy_challenger_only_when_clean_keep():
    row = {
        "decision_direction": "KEEP_CHALLENGER",
        "system_decision_class": "M15_KEEP_TARGET_FIRST_CONSERVATIVE_BOUND",
        "primary_export_family": "M15",
        "branch_result_class": "POSITIVE_RSTYLE_PROXY_MIDPOINT",
        "rstyle_midpoint_mean": 0.25,
        "source_confidence_status": "EXACT_SOURCE_SUPPORTED_NO_COMPONENT_SOURCE_STRESS",
        "ambiguity_status": "NO_ORDERING_AMBIGUITY_RECORDED",
    }

    decision = classify_unified_branch_decision(row)

    assert decision["rstyle_proxy_signal_class"] == "RSTYLE_PROXY_POSITIVE_MIDPOINT"
    assert decision["unified_execution_decision"] == "IMPLEMENT_PROXY_CHALLENGER_SPEC"
    assert decision["implementation_candidate_type"] == "BRANCH_LOCAL_SCORER_SPEC"


def test_unified_branch_decision_keeps_no_scalar_binding_out_of_scorer():
    decision = classify_unified_branch_decision(
        {
            "primary_export_family": "BINDING",
            "system_decision_class": "BINDING_PRESERVE_TARGETSTOP_NA_NO_SCALAR_PROVENANCE",
            "branch_result_class": "NO_RSTYLE_PROXY_INTERVAL_AVAILABLE",
        }
    )

    assert decision["unified_execution_decision"] == "PRESERVE_PROVENANCE_REQUIREMENT"
    assert decision["implementation_candidate_type"] == "PROVENANCE_REQUIREMENT"


def test_market_gap_candidate_classes_are_action_driven():
    assert (
        classify_market_gap_candidate({"action_class": "SOURCE_EXPANSION_QUEUE", "movement_status": "SMALL_N_LT20"})[
            "implementation_candidate_type"
        ]
        == "MARKET_GAP_SOURCE_EXPANSION_SPEC"
    )
    assert (
        classify_market_gap_candidate({"action_class": "ENTRY_GEOMETRY_QUEUE"})["unified_execution_decision"]
        == "IMPLEMENT_MARKET_GAP_ENTRY_GEOMETRY_CHALLENGER"
    )
    assert (
        classify_market_gap_candidate({"action_class": "AVOID_INVERSE_QUEUE"})["implementation_candidate_type"]
        == "MARKET_GAP_AVOID_INVERSE_SPEC"
    )


def test_rstyle_proxy_signal_class_handles_ambiguous_and_missing():
    assert rstyle_proxy_signal_class({"branch_result_class": "AMBIGUOUS_INTERVAL_STRADDLES_ZERO", "rstyle_midpoint_mean": 0.2}) == (
        "RSTYLE_PROXY_AMBIGUOUS_INTERVAL"
    )
    assert rstyle_proxy_signal_class({"branch_result_class": "NO_RSTYLE_PROXY_INTERVAL_AVAILABLE"}) == "RSTYLE_PROXY_NO_SCALAR"


def test_concentration_artifact_class_identifies_missing_available_markets():
    assert (
        concentration_artifact_class(
            current_rows=0,
            market_gap_rows=60,
            full_tick_rows=60,
            current_total=386,
            market_gap_total=400,
        )
        == "CURRENT_BRANCH_DENOMINATOR_ARTIFACT_SYMBOL_AVAILABLE_OUTSIDE_BRANCH_QUEUE"
    )
    assert (
        concentration_artifact_class(
            current_rows=322,
            market_gap_rows=45,
            full_tick_rows=65,
            current_total=386,
            market_gap_total=400,
        )
        == "MECHANISM_CONCENTRATED_BUT_DENOMINATOR_NARROWNESS_CONFIRMED"
    )


def test_score_branch_candidate_prioritizes_market_entry_and_excludes_binding():
    scored = score_branch_candidate(
        {
            "unified_execution_decision": "IMPLEMENT_MARKET_ENTRY_CHALLENGER_SPEC",
            "rstyle_proxy_signal_class": "RSTYLE_PROXY_POSITIVE_MIDPOINT",
            "source_repair_pressure_class": "SOURCE_PRESSURE_EXACT_OR_CONFIRMED",
            "execution_pressure_class": "EXECUTION_PRESSURE_MARKET_ENTRY_COMPARATOR",
            "target_stop_result": "TARGET_FIRST_PROXY_DOMINANT",
            "rstyle_midpoint_mean": 0.3,
        }
    )
    assert scored["candidate_score_class"] == "BRANCH_MARKET_ENTRY_CHALLENGER_SCORE_NOW"
    assert scored["candidate_score_proxy"] > 0

    binding = score_branch_candidate({"unified_execution_decision": "PRESERVE_PROVENANCE_REQUIREMENT"})
    assert binding["candidate_score_class"] == "BRANCH_PROVENANCE_EXCLUDE_FROM_SCALAR_SCORER"


def test_score_market_gap_candidate_splits_source_entry_and_avoid():
    source = score_market_gap_candidate(
        {
            "action_class": "SOURCE_EXPANSION_QUEUE",
            "movement_status": "SMALL_N_LT20",
            "flagged_n": 18,
            "control_n": 100,
            "delta_mean_abs_future_change": 0.2,
        }
    )
    assert source["candidate_score_class"] == "MARKET_GAP_SOURCE_EXPANSION_HIGH_PRIORITY"
    assert source["additional_flagged_rows_needed_for_n20"] == 2

    entry = score_market_gap_candidate(
        {
            "action_class": "ENTRY_GEOMETRY_QUEUE",
            "movement_status": "POSITIVE_ABS_AND_NONNEGATIVE_ALIGNMENT_DELTA",
            "delta_alignment_rate": 0.1,
        }
    )
    assert entry["candidate_score_class"] == "MARKET_GAP_ENTRY_GEOMETRY_SCORE_NOW"

    avoid = score_market_gap_candidate(
        {
            "action_class": "AVOID_INVERSE_QUEUE",
            "movement_status": "FLAT_OR_NEGATIVE_ABS_DELTA",
        }
    )
    assert avoid["candidate_score_class"] == "MARKET_GAP_AVOID_INVERSE_SCORE_NOW"


def test_replay_code_candidate_accepts_entry_only_with_positive_interval():
    accepted = entry_variant_code_candidate(
        {
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "primitive_flag": "DELTA_IMPULSE_P95_SAME_SYMBOL_SESSION",
            "entry_variant": "PRIMITIVE_CLOSE_MARKET_ENTRY",
            "entry_replay_decision": "ENTRY_REPLAY_ACCEPT_CHALLENGER",
            "entry_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_POSITIVE",
            "entry_replay_proxy_score": 0.7,
        }
    )
    assert accepted["code_candidate_status"] == "ENTRY_CODE_IMPLEMENT_SHADOW_RULE_SPEC"
    assert accepted["shadow_runtime_effect"] == "shadow_entry_geometry_candidate"

    control = entry_variant_code_candidate(
        {
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "primitive_flag": "DELTA_IMPULSE_P95_SAME_SYMBOL_SESSION",
            "entry_variant": "STATUS_QUO_NO_BRANCH_CONTROL",
            "entry_replay_decision": "ENTRY_REPLAY_CONTROL_ONLY",
            "entry_proxy_r_style_result_class": "PROXY_R_CONTROL_NEUTRAL",
        }
    )
    assert control["code_candidate_status"] == "ENTRY_CODE_CONTROL_ONLY"


def test_replay_code_candidate_maps_avoid_source_and_concentration_actions():
    avoid = avoid_policy_code_candidate(
        {
            "symbol": "GBPJPY",
            "route_session": "off_core_session",
            "horizon_id": "h32",
            "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
            "policy_variant_type": "AVOID_FILTER_VARIANT",
            "policy_variant_replay_decision": "AVOID_POLICY_REPLAY_ACCEPT_FILTER",
            "policy_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_POSITIVE",
            "policy_variant_proxy_score": 0.6,
        }
    )
    assert avoid["code_candidate_status"] == "AVOID_CODE_IMPLEMENT_SHADOW_FILTER_SPEC"

    source = source_materialization_code_candidate(
        {
            "symbol": "NAS100",
            "route_session": "ny_core",
            "horizon_id": "h64",
            "primitive_flag": "RANGE_EXPANSION_P95",
            "source_acquisition_status": "SOURCE_ACQUISITION_NEAR_N20_OUTSIDE_BRANCH_REPLAY_PRIORITY",
            "source_rows_needed_to_n20": 3,
            "source_replay_priority_score": 0.5,
        }
    )
    assert source["code_candidate_status"] == "SOURCE_CODE_MATERIALIZE_HIGH_PRIORITY"

    concentration = concentration_guard_code_candidate(
        {
            "symbol": "US30",
            "route_session": "london_core",
            "horizon_id": "h16",
            "primitive_flag": "DELTA_IMPULSE_P95",
            "test_axis": "symbol_session_horizon",
            "concentration_replay_decision": "CONCENTRATION_REPLAY_DENOMINATOR_ARTIFACT_CONFIRMED",
            "current_branch_rows": 0,
            "market_gap_combo_rows": 12,
        }
    )
    assert concentration["code_candidate_status"] == "CONCENTRATION_CODE_FORCE_OUTSIDE_BRANCH_DENOMINATOR_GUARD"


def test_market_gap_code_candidate_preserves_outside_branch_implementation():
    row = market_gap_code_candidate(
        {
            "symbol": "NAS100",
            "route_session": "ny_core",
            "session_bucket": "ny_core_1330_1600",
            "horizon_id": "h16",
            "primitive_flag": "ABSORPTION_PROXY_CVD_DIVERGENCE_DELTA_P75",
            "market_gap_combo_id": "combo-1",
            "market_gap_replay_decision": "IMPLEMENT_ENTRY_GEOMETRY_CHALLENGER_CANDIDATE",
            "market_gap_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_POSITIVE",
            "market_gap_decision_score": 0.72,
            "outside_gbpjpy_xauusd_current_branch_box": True,
        }
    )
    assert row["code_candidate_status"] == "MARKET_GAP_CODE_IMPLEMENT_ENTRY_GEOMETRY_SPEC"
    assert row["outside_gbpjpy_xauusd_current_branch_box"] is True


def test_shadow_scorer_enables_entry_and_materializes_outside_source():
    entry = score_code_candidate(
        {
            "code_candidate_kind": "ENTRY_VARIANT_RULE",
            "code_candidate_status": "ENTRY_CODE_IMPLEMENT_SHADOW_RULE_SPEC",
            "proxy_score": 0.7,
            "outside_gbpjpy_xauusd_current_branch_box": False,
        }
    )
    assert entry["shadow_scorer_action"] == "ENABLE_ENTRY_GEOMETRY_SHADOW_RULE"
    assert entry["implementation_eligibility"] == "IMMEDIATE_SHADOW_ENABLE"
    assert entry["live_effect"] is False

    source = score_code_candidate(
        {
            "code_candidate_kind": "SOURCE_MATERIALIZATION_RULE",
            "code_candidate_status": "SOURCE_CODE_MATERIALIZE_OUTSIDE_BRANCH_DENOMINATOR",
            "proxy_score": 0.4,
            "source_rows_needed_to_n20": 5,
            "outside_gbpjpy_xauusd_current_branch_box": True,
        }
    )
    assert source["shadow_scorer_action"] == "MATERIALIZE_OUTSIDE_BRANCH_SOURCE_DENOMINATOR"
    assert source["shadow_scorer_action_family"] == "MATERIALIZE_SOURCE"


def test_shadow_scorer_keeps_concentration_guard_and_controls_separate():
    guard = score_code_candidate(
        {
            "code_candidate_kind": "CONCENTRATION_DENOMINATOR_GUARD",
            "code_candidate_status": "CONCENTRATION_CODE_FORCE_OUTSIDE_BRANCH_DENOMINATOR_GUARD",
        }
    )
    assert guard["shadow_scorer_action_family"] == "DENOMINATOR_GUARD"
    assert guard["implementation_eligibility"] == "GUARD_REQUIRED"

    control = score_code_candidate(
        {
            "code_candidate_kind": "ENTRY_VARIANT_RULE",
            "code_candidate_status": "ENTRY_CODE_CONTROL_ONLY",
        }
    )
    assert control["shadow_scorer_action"] == "PRESERVE_CONTROL_ONLY_DO_NOT_ENABLE"
    assert control["shadow_scorer_action_family"] == "CONTROL_ONLY"


def test_source_materialization_classifies_current_source_failclosed_guard():
    metrics = {
        "current_targetable_flagged_n": 8,
        "current_source_flagged_n": 24,
        "current_failclosed_flagged_n": 16,
        "current_failclosed_reason_counts": {"future_bar_not_contiguous": 16},
    }

    classified = classify_materialization(metrics)
    proxy = materialization_proxy_fields({"source_replay_priority_score": 0.4}, metrics)
    reason = exact_missing_reason(metrics)

    assert classified["source_materialization_execution_status"] == (
        "SOURCE_MATERIALIZATION_CURRENT_SOURCE_N20_HORIZON_FAILCLOSED"
    )
    assert classified["source_materialization_decision"] == "SCORE_WITH_HORIZON_FAILCLOSED_GUARD_AND_REPAIR_ROUTE"
    assert proxy["materialization_proxy_r_style_result_class"] == "PROXY_R_INTERVAL_STRADDLES_ZERO"
    assert "failclosed_flagged_n=16" in reason


def test_source_materialization_prefers_targetable_expanded_session_proxy():
    metrics = {
        "current_targetable_flagged_n": 7,
        "current_source_flagged_n": 9,
        "same_symbol_all_sessions_targetable_flagged_n": 42,
        "same_session_all_symbols_targetable_flagged_n": 70,
        "same_symbol_all_sessions_source_flagged_n": 50,
    }

    classified = classify_materialization(metrics)
    proxy = materialization_proxy_fields({"source_replay_priority_score": 0.6, "outside_gbpjpy_xauusd_current_branch_box": True}, metrics)

    assert classified["source_materialization_execution_status"] == (
        "SOURCE_MATERIALIZATION_SAME_SYMBOL_ALL_SESSION_TARGETABLE_PROXY_N20"
    )
    assert classified["materialization_proxy_scope"] == "same_symbol_all_sessions_targetable_primitive"
    assert proxy["materialization_proxy_score"] > 0.5


def test_shadow_source_guard_bundle_enables_branch_local_rule_only():
    decision = classify_enable_bundle(
        {
            "shadow_scorer_component": "market_gap_entry_geometry",
            "shadow_scorer_score": 0.72,
            "outside_gbpjpy_xauusd_current_branch_box": True,
        }
    )

    assert decision["bundle_stage"] == "IMPLEMENT_ENABLE"
    assert decision["bundle_decision"] == "ENABLE_MARKET_GAP_ENTRY_GEOMETRY_SHADOW_RULE"
    assert decision["bundle_permission"] == "ENABLE_IN_BRANCH_LOCAL_SHADOW_BUNDLE"
    assert decision["source_guard_requirement"] == "USE_GLOBAL_SOURCE_GUARD_AND_DENOMINATOR_SCOPE"
    assert decision["live_effect"] is False


def test_shadow_source_guard_bundle_splits_failclosed_source_repairs():
    source_decision = classify_source_guard(
        {
            "source_materialization_execution_status": "SOURCE_MATERIALIZATION_CURRENT_SOURCE_N20_HORIZON_FAILCLOSED",
            "materialization_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_NEGATIVE",
            "materialization_proxy_score": 0.2,
        }
    )
    repair = classify_horizon_repair_action(
        {
            "materialization_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_NEGATIVE",
            "current_failclosed_flagged_n": 21,
            "current_targetable_flagged_n": 1,
            "current_source_flagged_n": 22,
        }
    )

    assert source_decision["bundle_decision"] == "SOURCE_GUARD_FAILCLOSED_REPAIR_THEN_KILL_IF_NEGATIVE_PERSISTS"
    assert source_decision["bundle_permission"] == "BLOCK_SOURCE_ENABLE_REPAIR_THEN_KILL_IF_UNCHANGED"
    assert source_decision["source_repair_required"] is True
    assert repair["bundle_decision"] == "HORIZON_REPAIR_REBUILD_AND_KILL_IF_NEGATIVE_PERSISTS"
    assert repair["repair_action"] == "REBUILD_TARGETABLE_HORIZON_EVENTS_FROM_CURRENT_SOURCE_FLAGS"


def test_shadow_source_guard_bundle_controls_and_denominator_guards():
    control = classify_score_control({"code_candidate_status": "BRANCH_CODE_REDESIGN_FILLABILITY_THEN_SPEC"})
    guard = classify_denominator_guard(
        {"code_candidate_status": "CONCENTRATION_CODE_FORCE_OUTSIDE_BRANCH_DENOMINATOR_GUARD"}
    )

    assert control["bundle_decision"] == "CONTROL_SCORE_FILLABILITY_REDESIGN_BEFORE_ENABLE"
    assert control["bundle_permission"] == "CONTROL_REQUIRED_BEFORE_ENABLE"
    assert guard["bundle_decision"] == "DENOMINATOR_GUARD_FORCE_OUTSIDE_BRANCH_SCOPE"
    assert guard["bundle_permission"] == "DENOMINATOR_GUARD_REQUIRED"


def test_observable_scorer_registers_entry_rule_without_live_effect():
    spec = observable_rule_spec(
        {
            "bundle_decision": "ENABLE_ENTRY_GEOMETRY_SHADOW_RULE",
            "shadow_scorer_component": "entry_geometry",
            "bundle_priority_score": 0.72,
            "symbol": "GBPJPY",
            "route_session": "off_core_session",
            "horizon_id": "h16",
            "primitive_flag": "ABSORPTION_PROXY_CVD_DIVERGENCE_DELTA_P75",
        }
    )

    assert spec["implementation_stage"] == "OBSERVABLE_RULE_SPEC"
    assert spec["implementation_operation"] == "REGISTER_ENTRY_GEOMETRY_OBSERVABLE"
    assert spec["observable_family"] == "ENTRY_GEOMETRY_OBSERVABLE"
    assert spec["runtime_effect"] == "record_and_score_only"
    assert spec["live_effect"] is False


def test_observable_scorer_maps_source_policy_control_denominator_and_repair():
    source = source_guard_policy_spec(
        {
            "bundle_permission": "DO_NOT_ENABLE_SOURCE_DEPENDENT_RULE",
            "bundle_decision": "SOURCE_GUARD_REJECT_PROXY_UNTIL_EXACT_SOURCE_REPAIR",
            "source_repair_required": True,
            "bundle_priority_score": 0.41,
        }
    )
    assert source["implementation_status"] == "SOURCE_POLICY_BLOCK_UNTIL_EXACT_SOURCE_REPAIR"
    assert source["implementation_operation"] == "REQUIRE_EXACT_SOURCE_REPAIR_BEFORE_OBSERVABLE_ENABLE"

    control = control_experiment_spec(
        {
            "bundle_decision": "CONTROL_SCORE_AVOID_FILTER_WITH_INVERSE_CONTROL",
            "bundle_priority_score": 0.5,
        }
    )
    assert control["implementation_operation"] == "RUN_AVOID_INVERSE_SIBLING_COMPARATOR"
    assert control["control_required_before_enable"] is True

    denominator = denominator_enforcement_spec(
        {
            "bundle_decision": "DENOMINATOR_GUARD_FORCE_OUTSIDE_BRANCH_SCOPE",
            "bundle_priority_score": 0.5,
        }
    )
    assert denominator["implementation_status"] == "DENOMINATOR_ENFORCE_OUTSIDE_BRANCH_SCOPE"

    repair = horizon_repair_execution_spec(
        {
            "bundle_decision": "HORIZON_REPAIR_REBUILD_AND_RESCORE_INTERVAL",
            "bundle_priority_score": 0.8,
        }
    )
    assert repair["implementation_operation"] == "REBUILD_TARGETABLE_HORIZON_AND_RESCORE"


def test_primitive_coverage_state_preserves_active_lane_status():
    coverage = primitive_coverage_state({"implementation_stage": "CONTROL_EXPERIMENT_SPEC"})
    assert coverage["primitive_coverage_status"] == "COVERED_WITH_CONTROL_EXPERIMENT_REQUIREMENT"

    source = primitive_coverage_state({"implementation_stage": "SOURCE_GUARD_POLICY_SPEC"})
    assert source["primitive_coverage_status"] == "COVERED_WITH_SOURCE_GUARD_OR_REPAIR_REQUIREMENT"


def test_observable_execution_scores_controlled_entry_when_control_exists():
    decision = classify_observable_execution(
        {
            "observable_family": "ENTRY_GEOMETRY_OBSERVABLE",
            "scorer_binding": "status_quo_control_required",
            "implementation_priority_score": 0.7,
        },
        source_statuses=[],
        control_statuses=["CONTROL_EXPERIMENT_ENTRY_GEOMETRY_VS_STATUS_QUO"],
        denominator_statuses=[],
    )

    assert decision["execution_decision"] == "OBSERVABLE_EXECUTE_SCORE_WITH_CONTROL_NOW"
    assert decision["control_required"] is True
    assert decision["live_effect"] is False


def test_observable_execution_blocks_when_source_policy_requires_repair():
    decision = classify_observable_execution(
        {"observable_family": "AVOID_FILTER_OBSERVABLE", "implementation_priority_score": 0.6},
        source_statuses=["SOURCE_POLICY_BLOCK_UNTIL_EXACT_SOURCE_REPAIR"],
        control_statuses=[],
        denominator_statuses=["DENOMINATOR_ENFORCE_OUTSIDE_BRANCH_SCOPE"],
    )

    assert decision["execution_decision"] == "OBSERVABLE_EXECUTE_SOURCE_REPAIR_FIRST"
    assert decision["execution_permission"] == "BLOCK_REGISTER_UNTIL_SOURCE_REPAIR"


def test_observable_execution_helpers_map_source_control_denominator_horizon_and_coverage():
    source = classify_source_policy_execution({"implementation_status": "SOURCE_POLICY_FAILCLOSED_REPAIR_THEN_RESCORE"})
    assert source["execution_decision"] == "SOURCE_EXECUTE_HORIZON_REPAIR_AND_RESCORE"

    control = classify_control_execution({"implementation_status": "CONTROL_EXPERIMENT_SCORER_PATCH_ABLATION"})
    assert control["execution_decision"] == "CONTROL_EXECUTE_SCORER_PATCH_ABLATION"

    denominator = classify_denominator_execution({"implementation_status": "DENOMINATOR_ENFORCE_SOURCE_ROOT_COVERAGE"})
    assert denominator["execution_decision"] == "DENOMINATOR_EXECUTE_SOURCE_ROOT_COVERAGE_GUARD"

    horizon = classify_observable_horizon_repair_execution(
        {"implementation_status": "HORIZON_REPAIR_EXECUTE_THEN_KILL_IF_NEGATIVE_PERSISTS"}
    )
    assert horizon["execution_decision"] == "HORIZON_WORK_ORDER_REBUILD_THEN_KILL_IF_NEGATIVE"

    coverage = classify_coverage_action(
        {"covered_status_counts": {"COVERED_WITH_SOURCE_GUARD_OR_REPAIR_REQUIREMENT": 1}}
    )
    assert coverage["execution_decision"] == "COVERAGE_EXECUTE_SOURCE_POLICY_OR_REPAIR"


def test_observable_action_result_scores_positive_control_delta():
    result = controlled_observable_score_result(
        {
            "observable_family": "ENTRY_GEOMETRY_OBSERVABLE",
            "execution_priority_score": 0.72,
        },
        [
            {"execution_priority_score": 0.40},
            {"execution_priority_score": 0.46},
        ],
    )

    assert result["action_result_status"] == "CONTROL_SCORE_RESULT_POSITIVE_DELTA"
    assert result["action_result_decision"] == "ACTION_RESULT_KEEP_OBSERVABLE_CHALLENGER_UNDER_CONTROL"
    assert result["control_match_count"] == 2
    assert result["proxy_r_style_score_delta"] == 0.29
    assert result["live_effect"] is False


def test_observable_action_result_emits_exact_control_lookup_requirement():
    result = control_lookup_requirement_result(
        {
            "observable_family": "MARKET_GAP_ENTRY_GEOMETRY_OBSERVABLE",
            "observable_scope_key": "symbol=NAS100|session=ny_core|horizon=h16|primitive=gap",
            "denominator_guard_match_count": 4,
        }
    )

    assert result["action_result_status"] == "CONTROL_LOOKUP_RESULT_EXACT_SCOPE_REQUIRED"
    assert result["desired_control_family"] == "CONTROL_EXPERIMENT_MARKET_GAP_ENTRY_VS_STATUS_QUO"
    assert result["missing_control_scope_key"].startswith("symbol=NAS100")
    assert result["control_required"] is True


def test_observable_action_result_registers_denominator_guard_and_source_repair():
    guarded = denominator_guarded_observable_result(
        {"denominator_guard_match_count": 17},
        [{"input_implementation_status": "DENOMINATOR_ENFORCE_OUTSIDE_BRANCH_SCOPE"}],
    )
    repair = source_policy_action_result(
        {
            "execution_decision": "SOURCE_EXECUTE_HORIZON_REPAIR_AND_KILL_CHECK",
            "execution_priority_score": 0.33,
        }
    )
    horizon = observable_horizon_work_order_result(
        {
            "execution_decision": "HORIZON_WORK_ORDER_REBUILD_THEN_RESCORE",
            "execution_priority_score": 0.44,
        }
    )

    assert guarded["action_result_status"] == "DENOMINATOR_RESULT_STRONG_SCOPE_GUARD_REGISTER"
    assert guarded["guard_strength_score"] == 0.85
    assert repair["source_action_result_family"] == "SOURCE_ACTION_HORIZON_REPAIR_KILL_CHECK"
    assert repair["source_repair_required"] is True
    assert horizon["action_result_status"] == "HORIZON_ACTION_RESULT_REBUILD_RESCORE"


def test_observable_implementation_candidate_splits_ready_guarded_and_control_scope_work():
    ready = observable_implementation_candidate(
        {
            "action_result_status": "CONTROL_SCORE_RESULT_POSITIVE_DELTA",
            "observable_proxy_score": 0.61,
            "proxy_r_style_score_delta": 0.12,
        }
    )
    guarded = observable_implementation_candidate(
        {
            "action_result_status": "DENOMINATOR_RESULT_STRONG_SCOPE_GUARD_REGISTER",
            "guard_strength_score": 0.55,
        }
    )
    control_scope = observable_implementation_candidate(
        {
            "action_result_status": "CONTROL_LOOKUP_RESULT_EXACT_SCOPE_REQUIRED",
            "observable_proxy_score": 0.42,
        }
    )

    assert ready["implementation_candidate_status"] == "OBSERVABLE_IMPL_ENABLE_CONTROLLED_CHALLENGER_SCORER"
    assert ready["implementation_operation"] == "REGISTER_CONTROLLED_OBSERVABLE_SCORER"
    assert ready["branch_local_ready"] is True
    assert ready["implementation_priority_score"] > 0.61
    assert guarded["implementation_candidate_status"] == "OBSERVABLE_IMPL_REGISTER_DENOMINATOR_GUARDED_SHADOW"
    assert guarded["branch_local_ready"] is True
    assert control_scope["implementation_candidate_status"] == "OBSERVABLE_IMPL_BUILD_CONTROL_SCOPE_BEFORE_ENABLE"
    assert control_scope["control_builder_required"] is True
    assert control_scope["branch_local_ready"] is False


def test_source_implementation_candidate_preserves_scorers_and_repairs_separately():
    scorer = source_implementation_candidate(
        {
            "source_action_result_family": "SOURCE_ACTION_GUARDED_PROXY_SCOREABLE",
            "source_proxy_score": 0.7,
        }
    )
    ambiguous = source_implementation_candidate(
        {
            "source_action_result_family": "SOURCE_ACTION_AMBIGUOUS_PROXY_CONTROL_REQUIRED",
            "source_proxy_score": 0.5,
        }
    )
    repair = source_implementation_candidate(
        {
            "source_action_result_family": "SOURCE_ACTION_EXACT_SOURCE_REPAIR",
            "source_proxy_score": 0.3,
        }
    )
    kill_check = source_implementation_candidate(
        {
            "source_action_result_family": "SOURCE_ACTION_HORIZON_REPAIR_KILL_CHECK",
            "source_proxy_score": 0.2,
        }
    )

    assert scorer["implementation_candidate_status"] == "SOURCE_IMPL_GUARDED_PROXY_SCORER"
    assert scorer["branch_local_ready"] is True
    assert scorer["source_repair_required"] is False
    assert ambiguous["implementation_candidate_status"] == "SOURCE_IMPL_AMBIGUOUS_PROXY_CONTROL_SCORER"
    assert ambiguous["control_builder_required"] is True
    assert repair["implementation_operation"] == "BUILD_EXACT_SOURCE_REPAIR"
    assert repair["source_repair_required"] is True
    assert kill_check["implementation_operation"] == "BUILD_HORIZON_REPAIR_KILL_CHECK"
    assert kill_check["branch_local_ready"] is False


def test_control_denominator_horizon_and_coverage_implementation_helpers():
    control = control_implementation_candidate({"action_result_status": "CONTROL_RESULT_COMPARATOR_READY"})
    denominator = denominator_implementation_candidate(
        {"action_result_status": "DENOMINATOR_ACTION_RESULT_OUTSIDE_BRANCH_SCOPE_ENFORCED"}
    )
    horizon = horizon_implementation_candidate({"action_result_status": "HORIZON_ACTION_RESULT_REBUILD_KILL_CHECK"})
    coverage = coverage_implementation_candidate(
        {"action_result_status": "COVERAGE_ACTION_RESULT_CONTROL_EXPERIMENT_ACTIVE"}
    )

    assert control["implementation_candidate_status"] == "CONTROL_IMPL_COMPARATOR_READY"
    assert denominator["implementation_operation"] == "ENFORCE_OUTSIDE_BRANCH_SCOPE_DENOMINATOR"
    assert horizon["implementation_candidate_status"] == "HORIZON_IMPL_REBUILD_KILL_CHECK"
    assert horizon["source_repair_required"] is True
    assert coverage["implementation_candidate_status"] == "COVERAGE_IMPL_CONTROL_EXPERIMENT_ACTIVE"
    assert coverage["control_builder_required"] is True


def test_runtime_work_decision_registers_ready_and_repair_rows():
    controlled = runtime_work_decision(
        {
            "implementation_candidate_status": "OBSERVABLE_IMPL_ENABLE_CONTROLLED_CHALLENGER_SCORER",
            "implementation_priority_score": 0.7,
        }
    )
    source_repair = runtime_work_decision(
        {
            "implementation_candidate_status": "SOURCE_IMPL_HORIZON_REPAIR_KILL_CHECK",
            "implementation_priority_score": 0.3,
        }
    )

    assert controlled["runtime_work_status"] == "RUNTIME_WORK_ENABLE_CONTROLLED_OBSERVABLE_SCORER"
    assert controlled["runtime_decision"] == "EXECUTE_SCORER_REGISTRATION_NOW"
    assert controlled["runtime_ready"] is True
    assert source_repair["runtime_work_status"] == "RUNTIME_WORK_EXECUTE_SOURCE_REPAIR"
    assert source_repair["runtime_source_repair_required"] is True
    assert source_repair["runtime_ready"] is False


def test_control_scope_build_attempt_uses_best_same_resource_proxy():
    row = {
        "observable_scope_key": "symbol=GBPJPY|session=london_core|horizon=h16|primitive=SPREAD_SHOCK_P95",
    }
    controls = [
        {"implementation_candidate_row_id": f"c-{idx}", "observable_scope_key": f"symbol=GBPJPY|session=london_core|horizon=h32|primitive=p{idx}"}
        for idx in range(21)
    ]
    controls.extend(
        {"implementation_candidate_row_id": f"x-{idx}", "observable_scope_key": f"symbol=XAUUSD|session=ny_core|horizon=h16|primitive=p{idx}"}
        for idx in range(5)
    )

    attempt = control_scope_build_attempt(row, {"desired_control_family": "CONTROL_EXPERIMENT_ENTRY_GEOMETRY_VS_STATUS_QUO"}, controls)

    assert parse_scope_key(row["observable_scope_key"])["symbol"] == "GBPJPY"
    assert attempt["control_scope_build_status"] == "CONTROL_SCOPE_BUILDER_PROXY_SAME_SYMBOL_SESSION_N20"
    assert attempt["selected_control_count"] == 21
    assert attempt["runtime_control_required"] is True
    assert attempt["runtime_ready"] is False


def test_source_repair_runtime_work_splits_exact_horizon_and_duplicate_scope():
    exact = source_repair_runtime_work(
        {"implementation_candidate_status": "SOURCE_IMPL_EXACT_SOURCE_REPAIR_WORK_ORDER"},
        {"source_action_result_family": "SOURCE_ACTION_EXACT_SOURCE_REPAIR"},
        duplicate_scope_count=3,
    )
    kill = source_repair_runtime_work(
        {"implementation_candidate_status": "SOURCE_IMPL_HORIZON_REPAIR_KILL_CHECK"},
        {"source_action_result_family": "SOURCE_ACTION_HORIZON_REPAIR_KILL_CHECK"},
        duplicate_scope_count=1,
    )

    assert exact["source_repair_runtime_status"] == "SOURCE_REPAIR_RUNTIME_EXACT_SOURCE_REBUILD_OR_ACQUIRE"
    assert exact["duplicate_repair_scope_count"] == 3
    assert exact["fail_if_negative_persists"] is False
    assert kill["source_repair_runtime_status"] == "SOURCE_REPAIR_RUNTIME_REBUILD_HORIZON_KILL_CHECK"
    assert kill["fail_if_negative_persists"] is True


def test_observable_scorer_execution_scores_controlled_delta_and_ambiguous_source_controls():
    controlled = controlled_scorer_execution(
        {"runtime_work_status": "RUNTIME_WORK_ENABLE_CONTROLLED_OBSERVABLE_SCORER"},
        {
            "proxy_r_style_score_delta": 0.22,
            "expectancy_style_proxy_delta": 0.22,
            "observable_proxy_score": 0.8,
            "control_match_count": 24,
        },
    )
    ambiguous = source_scorer_execution(
        {"runtime_work_status": "RUNTIME_WORK_REGISTER_SOURCE_PROXY_SCORER"},
        {
            "source_action_result_family": "SOURCE_ACTION_AMBIGUOUS_PROXY_CONTROL_REQUIRED",
            "source_proxy_score": 0.5,
            "proxy_r_style_score_delta": 0.12,
        },
    )

    assert controlled["scorer_execution_status"] == "SCORER_EXECUTION_CONTROLLED_POSITIVE_DELTA"
    assert controlled["executable_now"] is True
    assert ambiguous["source_scorer_execution_status"] == "SOURCE_SCORER_EXECUTION_AMBIGUOUS_PROXY_CONTROL_SCORE"
    assert ambiguous["control_required"] is True
    assert ambiguous["executable_now"] is True


def test_observable_scorer_execution_keeps_underpowered_and_context_rows_out_of_scoring():
    control_scope = control_scope_execution(
        {
            "control_scope_build_status": "CONTROL_SCOPE_BUILDER_UNDERPOWERED_GLOBAL_PROXY_ONLY",
            "selected_control_count": 200,
        }
    )
    context_control = control_comparator_execution(
        {
            "runtime_work_status": "RUNTIME_WORK_PRESERVE_CONTEXT",
            "input_candidate_status": "CONTROL_IMPL_CONTEXT_ONLY",
        },
        {"control_proxy_score": 0.4},
    )

    assert control_scope["control_scope_execution_status"] == "CONTROL_SCOPE_EXECUTION_EXACT_CONTROL_BUILD_REQUIRED"
    assert control_scope["control_scope_can_score_now"] is False
    assert control_scope["executable_now"] is False
    assert context_control["control_execution_status"] == "CONTROL_EXECUTION_COMPARATOR_CONTEXT_ONLY"
    assert context_control["executable_now"] is False


def test_source_repair_execution_preserves_exact_and_horizon_causes():
    exact = source_repair_execution(
        {
            "source_repair_runtime_status": "SOURCE_REPAIR_RUNTIME_EXACT_SOURCE_REBUILD_OR_ACQUIRE",
            "duplicate_repair_scope_count": 2,
        },
        {"source_action_result_family": "SOURCE_ACTION_EXACT_SOURCE_REPAIR", "source_proxy_score": 0.2},
    )
    horizon = source_repair_execution(
        {
            "source_repair_runtime_status": "SOURCE_REPAIR_RUNTIME_REBUILD_HORIZON_KILL_CHECK",
            "fail_if_negative_persists": True,
        },
        {"source_action_result_family": "SOURCE_ACTION_HORIZON_REPAIR_KILL_CHECK"},
        {"current_failclosed_flagged_n": 21, "horizon_proxy_score": 0.08},
    )

    assert exact["source_repair_execution_status"] == "SOURCE_REPAIR_EXECUTION_EXACT_SOURCE_REBUILD_OR_ACQUIRE"
    assert "exact-source" in exact["exact_missing_geometry_or_source_reason"]
    assert horizon["source_repair_execution_status"] == "SOURCE_REPAIR_EXECUTION_HORIZON_REBUILD_KILL_CHECK"
    assert horizon["fail_if_negative_persists"] is True
    assert horizon["current_failclosed_flagged_n"] == 21


def test_implementation_synthesis_registers_controlled_guarded_and_ambiguous_scorers():
    controlled = scorer_registration_synthesis(
        {
            "execution_status": "SCORER_EXECUTION_CONTROLLED_POSITIVE_DELTA",
            "scorer_proxy_score": 0.74,
            "proxy_r_style_score_delta": 0.22,
            "control_match_count": 24,
        }
    )
    guarded = scorer_registration_synthesis(
        {
            "execution_status": "SOURCE_SCORER_EXECUTION_GUARDED_PROXY_SCORE",
            "source_scorer_proxy_score": 0.54,
            "source_proxy_score": 0.58,
        }
    )
    ambiguous = scorer_registration_synthesis(
        {
            "execution_status": "SOURCE_SCORER_EXECUTION_AMBIGUOUS_PROXY_CONTROL_SCORE",
            "source_scorer_proxy_score": 0.38,
            "runtime_control_required": True,
        }
    )

    assert controlled["implementation_synthesis_status"] == "SCORER_REGISTRATION_CONTROLLED_CHALLENGER_REGISTER"
    assert controlled["keep_kill_redesign_implement_decision"] == "IMPLEMENT"
    assert guarded["implementation_synthesis_status"] == "SCORER_REGISTRATION_SOURCE_GUARDED_PROXY_REGISTER"
    assert guarded["standalone_interpretation_allowed"] is True
    assert ambiguous["implementation_synthesis_status"] == "SCORER_REGISTRATION_SOURCE_AMBIGUOUS_CONTROL_GUARD_REGISTER"
    assert ambiguous["control_required"] is True
    assert ambiguous["standalone_interpretation_allowed"] is False


def test_implementation_synthesis_splits_registry_control_build_and_repair_actions():
    observable = observable_registry_synthesis(
        {
            "execution_status": "SCORER_EXECUTION_DENOMINATOR_GUARDED_OBSERVABLE_STRONG",
            "guard_strength_score": 0.85,
            "denominator_guard_match_count": 17,
        }
    )
    exact_control = control_scope_implementation_synthesis(
        {
            "control_scope_execution_status": "CONTROL_SCOPE_EXECUTION_EXACT_CONTROL_BUILD_REQUIRED",
            "selected_control_count": 200,
            "missing_control_scope_key": "symbol=NAS100|session=ny_core|horizon=h16|primitive=gap",
        }
    )
    exact_action = exact_control_build_action(
        {
            "control_scope_execution_status": "CONTROL_SCOPE_EXECUTION_EXACT_CONTROL_BUILD_REQUIRED",
            "selected_control_count": 200,
            "same_symbol_control_count": 12,
        }
    )
    control = control_registry_synthesis(
        {"control_execution_status": "CONTROL_EXECUTION_COMPARATOR_REGISTERED", "control_proxy_score": 0.42}
    )
    denominator = denominator_guard_registry_synthesis(
        {"denominator_execution_status": "DENOMINATOR_EXECUTION_GUARD_REGISTERED", "guard_strength_score": 0.8}
    )
    repair = source_repair_action_synthesis(
        {
            "source_repair_execution_status": "SOURCE_REPAIR_EXECUTION_HORIZON_REBUILD_KILL_CHECK",
            "exact_missing_geometry_or_source_reason": "horizon targetability is fail-closed",
            "fail_if_negative_persists": True,
        }
    )

    assert observable["implementation_synthesis_status"] == "OBSERVABLE_REGISTRY_DENOMINATOR_GUARDED_REGISTER"
    assert observable["keep_kill_redesign_implement_decision"] == "IMPLEMENT_WITH_DENOMINATOR_GUARD"
    assert exact_control["implementation_synthesis_status"] == "CONTROL_SCOPE_IMPLEMENT_EXACT_CONTROL_BUILD_REQUIRED"
    assert exact_control["branch_local_ready"] is False
    assert exact_action["implementation_action_status"] == "EXACT_CONTROL_BUILD_REQUIRED_UNDERPOWERED_GLOBAL_ONLY"
    assert control["implementation_synthesis_status"] == "CONTROL_REGISTRY_COMPARATOR_REGISTERED"
    assert denominator["implementation_synthesis_status"] == "DENOMINATOR_GUARD_REGISTRY_REGISTERED"
    assert repair["implementation_synthesis_status"] == "SOURCE_REPAIR_ACTION_HORIZON_REBUILD_KILL_CHECK"
    assert repair["fail_if_negative_persists"] is True


def test_code_integration_candidates_split_standalone_and_control_guarded_scorers():
    controlled = scorer_code_integration_candidate(
        {
            "implementation_synthesis_status": "SCORER_REGISTRATION_CONTROLLED_CHALLENGER_REGISTER",
            "scorer_registration_score": 0.74,
            "branch_local_ready": True,
        }
    )
    guarded = scorer_code_integration_candidate(
        {
            "implementation_synthesis_status": "SCORER_REGISTRATION_SOURCE_GUARDED_PROXY_REGISTER",
            "scorer_registration_score": 0.52,
        }
    )
    ambiguous = scorer_code_integration_candidate(
        {
            "implementation_synthesis_status": "SCORER_REGISTRATION_SOURCE_AMBIGUOUS_CONTROL_GUARD_REGISTER",
            "control_required": True,
            "scorer_registration_score": 0.39,
        }
    )

    assert controlled["code_integration_status"] == "CODE_INTEGRATION_CONTROLLED_OBSERVABLE_SCORER_PATCH"
    assert controlled["standalone_interpretation_allowed"] is True
    assert guarded["code_integration_status"] == "CODE_INTEGRATION_GUARDED_SOURCE_PROXY_SCORER_PATCH"
    assert guarded["control_guard_required"] is False
    assert ambiguous["code_integration_status"] == "CODE_INTEGRATION_AMBIGUOUS_SOURCE_PROXY_CONTROL_GUARD_SCORER_PATCH"
    assert ambiguous["standalone_interpretation_allowed"] is False
    assert ambiguous["control_guard_required"] is True


def test_code_integration_candidates_split_registry_control_and_repair_work_orders():
    observable = observable_registry_code_candidate(
        {"implementation_synthesis_status": "OBSERVABLE_REGISTRY_DENOMINATOR_GUARDED_REGISTER"}
    )
    control_scope_proxy = control_scope_code_candidate(
        {
            "implementation_synthesis_status": "CONTROL_SCOPE_IMPLEMENT_PROXY_SAME_SYMBOL_SESSION_GUARD",
            "selected_control_count": 24,
        }
    )
    exact_control = exact_control_builder_code_candidate(
        {
            "implementation_synthesis_status": "CONTROL_SCOPE_IMPLEMENT_EXACT_CONTROL_BUILD_REQUIRED",
            "exact_build_source_requirement": "build same-scope controls",
        }
    )
    control = control_registry_code_candidate(
        {"implementation_synthesis_status": "CONTROL_REGISTRY_COMPARATOR_REGISTERED"}
    )
    denominator = denominator_guard_code_candidate(
        {"implementation_synthesis_status": "DENOMINATOR_GUARD_REGISTRY_REGISTERED"}
    )
    repair = source_repair_code_candidate(
        {
            "implementation_synthesis_status": "SOURCE_REPAIR_ACTION_HORIZON_REBUILD_KILL_CHECK",
            "fail_if_negative_persists": True,
        }
    )

    assert observable["code_integration_status"] == "CODE_INTEGRATION_DENOMINATOR_GUARDED_OBSERVABLE_REGISTRY_PATCH"
    assert observable["denominator_guard_required"] is True
    assert control_scope_proxy["code_integration_status"] == "CODE_INTEGRATION_SESSION_PROXY_CONTROL_GUARD_PATCH"
    assert control_scope_proxy["branch_local_ready"] is True
    assert exact_control["code_integration_status"] == "CODE_INTEGRATION_EXACT_CONTROL_BUILDER_WORK_ORDER"
    assert exact_control["branch_local_ready"] is False
    assert control["code_integration_status"] == "CODE_INTEGRATION_CONTROL_COMPARATOR_REGISTRY_PATCH"
    assert denominator["code_integration_status"] == "CODE_INTEGRATION_DENOMINATOR_GUARD_PATCH"
    assert repair["code_integration_status"] == "CODE_INTEGRATION_HORIZON_REBUILD_KILL_CHECK_WORK_ORDER"
    assert repair["fail_if_negative_persists"] is True


def test_branch_local_module_materialization_builds_scorer_and_registry_records():
    scorer = scorer_module_materialization(
        {
            "code_integration_status": "CODE_INTEGRATION_AMBIGUOUS_SOURCE_PROXY_CONTROL_GUARD_SCORER_PATCH",
            "control_guard_required": True,
            "candidate_function_hint": "add_ambiguous_source_proxy_control_guard_spec",
        }
    )
    registry = registry_module_materialization(
        {
            "code_integration_status": "CODE_INTEGRATION_DENOMINATOR_GUARD_PATCH",
            "observable_scope_key": "symbol=NAS100|session=ny_core",
        }
    )
    coverage = coverage_sidecar_registry_materialization(
        {"code_integration_status": "CODE_INTEGRATION_COVERAGE_SIDECAR_SOURCE_OR_REPAIR_ACTIVE"}
    )

    assert scorer["module_materialization_status"] == "SCORER_MODULE_AMBIGUOUS_SOURCE_PROXY_CONTROL_GUARD_PATCH_READY"
    assert scorer["can_score_standalone"] is False
    assert scorer["module_patch_ready"] is True
    assert registry["module_materialization_status"] == "REGISTRY_MODULE_DENOMINATOR_GUARD_READY"
    assert registry["module_patch_ready"] is True
    assert coverage["module_materialization_status"] == "REGISTRY_MODULE_COVERAGE_SIDECAR_SOURCE_OR_REPAIR_ACTIVE"
    assert coverage["module_patch_ready"] is False


def test_branch_local_repair_materialization_keeps_work_orders_open():
    repair = source_repair_work_materialization(
        {
            "code_integration_status": "CODE_INTEGRATION_HORIZON_REBUILD_KILL_CHECK_WORK_ORDER",
            "fail_if_negative_persists": True,
        }
    )
    exact_control = exact_control_work_materialization(
        {
            "code_integration_status": "CODE_INTEGRATION_EXACT_CONTROL_BUILDER_WORK_ORDER",
            "exact_build_source_requirement": "build exact same-scope controls",
        }
    )
    horizon_sidecar = horizon_sidecar_work_materialization(
        {"code_integration_status": "CODE_INTEGRATION_HORIZON_SIDECAR_REBUILD_RESCORE"}
    )

    assert repair["module_materialization_status"] == "REPAIR_MODULE_HORIZON_REBUILD_KILL_CHECK_WORK_ORDER_OPEN"
    assert repair["repair_work_order_open"] is True
    assert repair["fail_if_negative_persists"] is True
    assert exact_control["module_materialization_status"] == "REPAIR_MODULE_EXACT_CONTROL_BUILD_WORK_ORDER_OPEN"
    assert exact_control["exact_control_build_required"] is True
    assert horizon_sidecar["module_materialization_status"] == "REPAIR_MODULE_HORIZON_SIDECAR_REBUILD_RESCORE"
    assert horizon_sidecar["repair_work_order_open"] is False


def test_branch_local_repair_execution_scores_controls_source_and_horizon_sidecars():
    module = {
        "module_materialization_row_id": "m1",
        "input_execution_bundle_row_id": "exec1",
        "observable_scope_key": "symbol=NAS100|session=off_core_session|horizon=h16|primitive=gap",
        "exact_build_source_requirement": "build exact same-scope controls",
        "source_code_candidate_id": "candidate1",
    }
    exact_control = exact_control_repair_execution(
        module,
        {
            "control_scope_execution_score": 0.44,
            "control_scope_proxy_quality": 0.2,
            "exact_control_count": 0,
            "same_symbol_control_count": 10,
            "same_symbol_session_control_count": 4,
            "selected_control_count": 231,
            "selected_control_runtime_work_row_ids": ["r1"],
            "selected_control_input_candidate_ids": ["c1"],
        },
    )
    source = source_repair_work_execution(
        {**module, "repair_family": "HORIZON_REBUILD_KILL_CHECK", "fail_if_negative_persists": True},
        {
            "source_proxy_score": 0.22,
            "horizon_proxy_score": 0.08,
            "current_source_flagged_n": 30,
            "current_targetable_flagged_n": 9,
            "current_failclosed_flagged_n": 21,
            "exact_missing_geometry_or_source_reason": "horizon targetability is fail-closed",
        },
    )
    horizon = horizon_sidecar_repair_execution(module, [source])

    assert exact_control["repair_execution_status"] == "REPAIR_EXECUTION_EXACT_CONTROL_GLOBAL_PROXY_ONLY_SCORE_WITHHELD"
    assert exact_control["control_proxy_score_lower_bound"] == 0.088
    assert exact_control["exact_control_requirement_open"] is True
    assert source["repair_execution_status"] == "REPAIR_EXECUTION_HORIZON_REBUILD_KILL_CHECK_PROXY_SCORED"
    assert source["current_failclosed_ratio"] == 0.7
    assert source["fail_if_negative_persists"] is True
    assert horizon["repair_execution_status"] == "REPAIR_EXECUTION_HORIZON_SIDECAR_LINKED_TO_SOURCE_REPAIR_SCOPE"
    assert horizon["linked_source_repair_execution_count"] == 1


def test_branch_local_repair_acquisition_proxy_builds_member_and_source_requirements():
    exact = exact_control_acquisition_requirement(
        {
            "repair_execution_row_id": "target",
            "scope_symbol": "NAS100",
            "scope_session": "off_core_session",
            "scope_horizon": "h16",
            "scope_primitive": "gap",
            "exact_control_count": 0,
            "same_symbol_session_control_count": 4,
            "same_symbol_control_count": 10,
            "selected_control_count": 231,
            "control_proxy_score_lower_bound": 0.088,
        }
    )
    member = control_member_proxy_replay(
        exact,
        {
            "execution_bundle_row_id": "control-exec",
            "input_runtime_work_row_id": "runtime-control",
            "input_implementation_candidate_row_id": "candidate-control",
            "scope_symbol": "NAS100",
            "scope_session": "ny_core",
            "scope_horizon": "h16",
            "scope_primitive": "gap",
            "control_proxy_score": 0.54,
        },
        "runtime-control",
        "candidate-control",
        1,
    )
    source = source_acquisition_proxy_requirement(
        {
            "repair_execution_row_id": "source",
            "source_repair_family": "HORIZON_REBUILD_RESCORE",
            "source_proxy_score": 0.34,
            "horizon_proxy_score": 0.08,
            "source_minus_horizon_proxy_delta": 0.26,
            "current_source_flagged_n": 22,
            "current_targetable_flagged_n": 1,
            "current_failclosed_flagged_n": 21,
            "current_failclosed_ratio": 0.954545,
            "source_repair_requirement_open": True,
        }
    )
    stress = horizon_proxy_stress({**source, "fail_if_negative_persists": True})

    assert exact["acquisition_proxy_status"] == "ACQUISITION_EXACT_CONTROL_NEEDS_EXACT_SCOPE_GLOBAL_PROXY_ONLY"
    assert exact["same_symbol_rows_needed_to_n20"] == 10
    assert member["control_member_relation"] == "CONTROL_MEMBER_RELATION_SAME_SYMBOL"
    assert member["member_lookup_status"] == "CONTROL_MEMBER_JOINED"
    assert source["acquisition_proxy_status"] == "ACQUISITION_HORIZON_REBUILD_RESCORE_REQUIRED"
    assert source["targetable_rows_needed_to_n20"] == 19
    assert stress["acquisition_proxy_status"] == "HORIZON_PROXY_STRESS_KILL_CHECK_ACTIVE"
    assert stress["failclosed_stress_score"] < source["source_proxy_score"]


def test_branch_local_control_source_split_preserves_relation_and_scope_actions():
    exact = {
        "acquisition_proxy_row_id": "exact-row",
        "input_repair_execution_row_id": "target",
        "symbol": "NAS100",
        "route_session": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "gap",
        "scope_symbol": "NAS100",
        "scope_session": "off_core_session",
        "scope_horizon": "h16",
        "scope_primitive": "gap",
        "exact_control_count": 0,
    }
    members = [
        {
            "acquisition_proxy_row_id": "member-1",
            "input_repair_execution_row_id": "target",
            "symbol": "NAS100",
            "route_session": "off_core_session",
            "horizon_id": "h16",
            "primitive_flag": "gap",
            "control_member_relation": "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION_HORIZON",
            "control_proxy_score": 0.42,
            "member_runtime_work_row_id": "runtime-1",
        },
        {
            "acquisition_proxy_row_id": "member-2",
            "input_repair_execution_row_id": "target",
            "symbol": "NAS100",
            "route_session": "off_core_session",
            "horizon_id": "h16",
            "primitive_flag": "gap",
            "control_member_relation": "CONTROL_MEMBER_RELATION_GLOBAL_CROSS_SYMBOL",
            "control_proxy_score": 0.22,
            "member_runtime_work_row_id": "runtime-2",
        },
    ]
    split = exact_control_relation_split(exact, members, duplicate_scope_row_count=4)
    member_split = control_member_relation_split(members[0], split, [members[0]])
    source = source_acquisition_split(
        {
            "acquisition_proxy_row_id": "source-row",
            "source_repair_family": "EXACT_SOURCE_REPAIR",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h32",
            "primitive_flag": "spread",
        }
    )
    horizon = horizon_rebuild_split({"fail_if_negative_persists": True})
    scope = scope_acquisition_plan(
        ("NAS100", "off_core_session", "h16", "gap"),
        [split],
        [],
        [],
    )

    assert split["control_source_split_status"] == (
        "CONTROL_SOURCE_SPLIT_EXACT_REQUIRED_KEEP_SAME_SYMBOL_SESSION_HORIZON_PROXY_UNDER_N20"
    )
    assert split["best_available_proxy_member_count"] == 1
    assert split["exact_control_rows_needed_to_n20"] == 20
    assert member_split["keep_for_strongest_available_proxy"] is True
    assert member_split["relation_group_member_count"] == 1
    assert source["control_source_split_status"] == "CONTROL_SOURCE_SPLIT_EXACT_SOURCE_REBUILD_REQUIRED"
    assert horizon["control_source_split_status"] == "CONTROL_SOURCE_SPLIT_HORIZON_KILL_CHECK_REBUILD_ACTIVE"
    assert scope["control_source_split_status"] == "CONTROL_SOURCE_SPLIT_SCOPE_EXACT_CONTROL_ONLY"


def test_branch_local_denominator_source_rebuild_joins_current_surfaces():
    exact = {
        "control_source_split_row_id": "split-exact",
        "input_repair_execution_row_id": "target",
        "symbol": "NAS100",
        "route_session": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "gap",
        "source_code_candidate_id": "code-exact",
        "exact_control_count": 0,
        "selected_control_member_count": 231,
        "best_available_proxy_relation": "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION",
        "best_available_proxy_member_count": 4,
    }
    target = exact_control_target_rebuild(
        exact,
        [{"bundle_stage": "IMPLEMENT_ENABLE", "bundle_permission": "ENABLE_IN_BRANCH_LOCAL_SHADOW_BUNDLE"}],
        [],
        [],
    )
    scope = exact_control_scope_denominator_rebuild(
        {
            "scope_acquisition_plan_row_id": "scope",
            "symbol": "NAS100",
            "route_session": "off_core_session",
            "horizon_id": "h16",
            "primitive_flag": "gap",
        },
        [exact] * 4,
        [{"bundle_stage": "IMPLEMENT_ENABLE", "bundle_permission": "ENABLE_IN_BRANCH_LOCAL_SHADOW_BUNDLE"}] * 4,
        [],
        [],
        [{"keep_for_strongest_available_proxy": True, "control_proxy_score": 0.4}] * 16,
    )
    member = control_member_denominator_evidence(
        {
            "control_member_relation_split_row_id": "member",
            "input_repair_execution_row_id": "target",
            "control_member_relation": "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION",
            "keep_for_strongest_available_proxy": True,
        },
        target,
    )
    source = source_materialization_rebuild(
        {"source_repair_family": "EXACT_SOURCE_REPAIR", "source_code_candidate_id": "source"},
        {
            "source_materialization_execution_status": "SOURCE_MATERIALIZATION_SAME_SYMBOL_ALL_SESSION_TARGETABLE_PROXY_N20",
            "current_targetable_flagged_n": 8,
            "current_source_flagged_n": 9,
            "same_symbol_all_sessions_targetable_flagged_n": 81,
            "same_symbol_all_sessions_source_flagged_n": 86,
        },
    )
    horizon = horizon_materialization_rebuild(
        {"source_repair_family": "HORIZON_REBUILD_KILL_CHECK", "current_failclosed_ratio": 0.8, "fail_if_negative_persists": True},
        {"failclosed_stress_score": 0.03, "fail_if_negative_persists": True},
        {
            "source_materialization_execution_status": "SOURCE_MATERIALIZATION_CURRENT_SOURCE_N20_HORIZON_FAILCLOSED",
            "current_source_flagged_n": 22,
            "current_targetable_flagged_n": 1,
            "current_failclosed_flagged_n": 21,
        },
    )
    scope_action = scope_rebuild_action(
        {"scope_acquisition_plan_row_id": "scope", "control_source_split_status": "CONTROL_SOURCE_SPLIT_SCOPE_EXACT_CONTROL_ONLY"},
        scope,
        [],
        [],
    )

    assert target["denominator_source_rebuild_status"] == (
        "DENOM_SOURCE_REBUILD_EXACT_CONTROL_GUARD_ONLY_TARGET_BUILD_REQUIRED"
    )
    assert target["proxy_scalar_interpretation_allowed"] is False
    assert scope["denominator_source_rebuild_status"] == (
        "DENOM_SOURCE_REBUILD_SCOPE_EXACT_CONTROL_GUARD_ONLY_BUILD_REQUIRED"
    )
    assert scope["current_shadow_guard_row_count"] == 4
    assert member["denominator_source_rebuild_status"] == "DENOM_SOURCE_REBUILD_MEMBER_BEST_PROXY_EVIDENCE"
    assert source["denominator_source_rebuild_status"] == (
        "DENOM_SOURCE_REBUILD_EXACT_SOURCE_UNDER_N20_EXPANDED_PROXY_AVAILABLE"
    )
    assert source["best_expanded_targetable_count"] == 81
    assert horizon["denominator_source_rebuild_status"] == (
        "DENOM_SOURCE_REBUILD_HORIZON_KILL_CHECK_EXACT_REPAIR_PATH"
    )
    assert horizon["current_targetable_gap_to_n20"] == 19
    assert scope_action["denominator_source_rebuild_decision"] == "EXECUTE_EXACT_CONTROL_DENOMINATOR_ACQUISITION"


def test_branch_local_denominator_source_execution_scores_keep_kill_redesign_paths():
    target = exact_control_target_execution(
        {
            "exact_control_count": 0,
            "best_available_proxy_member_count": 12,
            "best_available_proxy_score_mean": 0.62,
            "current_shadow_guard_row_count": 1,
        }
    )
    scope = exact_control_scope_execution(
        {
            "exact_control_target_row_count": 4,
            "best_proxy_member_count": 24,
            "best_proxy_score_mean": 0.6,
            "selected_control_member_count": 924,
        }
    )
    source = source_rebuild_execution(
        {
            "materialization_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_NEGATIVE",
            "current_targetable_flagged_n": 8,
            "current_source_flagged_n": 9,
            "current_exact_gap_to_n20": 12,
        },
        {"materialization_proxy_r_style_lower": -0.4, "materialization_proxy_r_style_upper": -0.1},
    )
    horizon = horizon_rebuild_execution(
        {
            "fail_if_negative_persists": True,
            "horizon_proxy_score": 0.08,
            "source_proxy_score": 0.34,
            "current_failclosed_ratio": 0.9,
            "current_targetable_gap_to_n20": 19,
        }
    )

    assert target["denominator_source_execution_status"] == (
        "DENOM_SOURCE_EXEC_EXACT_CONTROL_TARGET_PROXY_UNDER_N20_BUILD_REQUIRED"
    )
    assert target["proxy_scalar_interpretation_allowed"] is False
    assert scope["denominator_source_execution_status"] == (
        "DENOM_SOURCE_EXEC_EXACT_CONTROL_SCOPE_PROXY_N20_SCORE_WITH_GUARD"
    )
    assert scope["proxy_scalar_interpretation_allowed"] is True
    assert source["keep_kill_redesign_decision"] == "KILL_PROXY"
    assert source["exact_rebuild_required"] is True
    assert horizon["keep_kill_redesign_decision"] == "KILL_CHECK"
    assert horizon["proxy_scalar_interpretation_allowed"] is False


def test_branch_local_denominator_source_action_candidates_emit_concrete_next_actions():
    target_action = exact_control_target_action_candidate(
        {
            "denominator_source_execution_row_id": "target",
            "exact_control_count": 0,
            "best_available_proxy_rows_needed_to_n20": 8,
            "proxy_scalar_interpretation_allowed": False,
        }
    )
    scope_action = exact_control_scope_action_candidate(
        {
            "exact_control_scope_execution_row_id": "scope",
            "best_proxy_rows_needed_to_n20": 0,
            "best_proxy_member_count": 24,
            "proxy_scalar_interpretation_allowed": True,
        }
    )
    source_action = source_proxy_kill_action_candidate(
        {
            "denominator_source_execution_row_id": "source",
            "keep_kill_redesign_decision": "KILL_PROXY",
            "current_exact_gap_to_n20": 12,
            "materialization_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_NEGATIVE",
        }
    )
    horizon_action = horizon_repair_action_candidate(
        {
            "denominator_source_execution_row_id": "horizon",
            "keep_kill_redesign_decision": "REDESIGN",
            "current_targetable_gap_to_n20": 19,
        }
    )
    rollup = scope_rollup_action_candidate(
        {
            "scope_action_execution_row_id": "rollup",
            "denominator_source_execution_status": "DENOM_SOURCE_EXEC_SCOPE_SOURCE_PROXY_KILL_OR_REBUILD",
            "keep_kill_redesign_decision": "KILL_PROXY",
            "source_rebuild_execution_count": 1,
            "exact_rebuild_required": True,
        }
    )
    target_action["denominator_source_action_candidate_row_id"] = "action-target"
    acquisition = acquisition_requirement_from_action(target_action)

    assert target_action["denominator_source_action_status"] == (
        "DENOM_SOURCE_ACTION_EXACT_CONTROL_TARGET_BUILD_REQUIRED"
    )
    assert scope_action["keep_kill_redesign_decision"] == "KEEP_GUARDED_PROXY"
    assert scope_action["implementation_ready"] is True
    assert source_action["registry_action"] == "do_not_register_source_proxy_candidate"
    assert source_action["exact_rebuild_required"] is True
    assert horizon_action["implementation_candidate_family"] == "HORIZON_TARGETABILITY_REDESIGN"
    assert rollup["denominator_source_action_status"] == "DENOM_SOURCE_ACTION_SCOPE_SOURCE_PROXY_KILL_OR_REBUILD"
    assert acquisition["acquisition_requirement_family"] == "EXACT_CONTROL_TARGET_DENOMINATOR"


def test_branch_local_denominator_source_acquisition_execution_materializes_decisions():
    target_action = {
        "denominator_source_action_candidate_row_id": "action-target",
        "input_denominator_source_execution_row_id": "exec-target",
        "input_denominator_source_rebuild_row_id": "rebuild-target",
        "symbol": "EURUSD",
        "route_session": "london",
        "horizon_id": "h1",
        "primitive_flag": "sweep",
    }
    target_exec = {
        "best_available_proxy_relation": "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION",
        "best_available_proxy_member_count": 3,
        "proxy_control_score": 0.61,
        "input_repair_execution_row_id": "repair-target",
    }
    members = [
        {
            "control_member_relation": "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION",
            "control_proxy_score": 0.60,
            "keep_for_strongest_available_proxy": True,
        },
        {
            "control_member_relation": "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION",
            "control_proxy_score": 0.64,
            "keep_for_strongest_available_proxy": True,
        },
        {
            "control_member_relation": "CONTROL_MEMBER_RELATION_SAME_SYMBOL",
            "control_proxy_score": 0.30,
            "keep_for_strongest_available_proxy": False,
        },
    ]
    target = exact_control_target_build_execution(target_action, target_exec, members)
    scope = exact_control_scope_build_execution(
        {"exact_control_scope_action_row_id": "scope", "proxy_scalar_interpretation_allowed": True},
        [target],
    )
    source = source_exact_rebuild_execution(
        {
            "denominator_source_action_candidate_row_id": "action-source",
            "input_denominator_source_execution_row_id": "exec-source",
            "input_denominator_source_rebuild_row_id": "rebuild-source",
            "source_materialization_execution_id": "mat-source",
        },
        {
            "materialization_proxy_score": 0.08,
            "materialization_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_NEGATIVE",
            "materialization_proxy_r_style_lower": -0.60,
            "materialization_proxy_r_style_midpoint": -0.27,
            "materialization_proxy_r_style_upper": -0.02,
        },
        {
            "current_targetable_flagged_n": 7,
            "current_source_flagged_n": 16,
            "current_failclosed_flagged_n": 9,
            "best_expanded_targetable_count": 41,
        },
        {"source_materialization_execution_status": "SOURCE_MATERIALIZATION_PROXY_READY"},
    )
    horizon = horizon_repair_rescore_execution(
        {
            "denominator_source_action_candidate_row_id": "action-horizon",
            "input_denominator_source_execution_row_id": "exec-horizon",
            "input_denominator_source_rebuild_row_id": "rebuild-horizon",
            "fail_if_negative_persists": True,
        },
        {
            "source_proxy_score": 0.05,
            "horizon_proxy_score": 0.02,
            "source_minus_horizon_proxy_delta": 0.03,
        },
        {
            "current_targetable_flagged_n": 2,
            "current_failclosed_flagged_n": 21,
            "current_source_flagged_n": 23,
        },
    )
    acquisition = acquisition_requirement_execution(
        {
            "acquisition_requirement_row_id": "req",
            "input_action_candidate_row_id": "action-source",
            "acquisition_requirement_family": "EXACT_SOURCE_REBUILD",
            "rows_needed_to_n20": 13,
            "exact_rebuild_required": True,
        },
        source,
    )

    assert target["denominator_source_acquisition_status"] == (
        "DENOM_SOURCE_ACQ_EXEC_CONTROL_TARGET_EXACT_UNAVAILABLE_PROXY_UNDER_N20"
    )
    assert target["member_rows_examined"] == 3
    assert target["best_proxy_rows_needed_to_n20"] == 17
    assert target["proxy_scalar_interpretation_allowed"] is False
    assert scope["denominator_source_acquisition_status"] == (
        "DENOM_SOURCE_ACQ_EXEC_CONTROL_SCOPE_GUARDED_PROXY_CONFIRMED_BUILD_OPEN"
    )
    assert source["denominator_source_acquisition_status"] == (
        "DENOM_SOURCE_ACQ_EXEC_SOURCE_EXACT_UNDER_N20_NEGATIVE_PROXY_KILL_CONFIRMED"
    )
    assert source["keep_kill_redesign_decision"] == "KILL_PROXY"
    assert horizon["denominator_source_acquisition_status"] == (
        "DENOM_SOURCE_ACQ_EXEC_HORIZON_KILL_CONFIRMED_BY_REPAIR_UPPER_BOUND"
    )
    assert horizon["repaired_targetable_upper_bound_reaches_n20"] is True
    assert acquisition["matched_execution_row_id"] is None
    assert acquisition["keep_kill_redesign_decision"] == "KILL_PROXY"


def test_branch_local_denominator_source_resolution_splits_candidates_and_actions():
    target = exact_control_target_resolution(
        {
            "denominator_source_acquisition_execution_row_id": "target",
            "denominator_source_acquisition_status": "DENOM_SOURCE_ACQ_EXEC_CONTROL_TARGET_EXACT_UNAVAILABLE_PROXY_UNDER_N20",
            "best_available_proxy_member_count": 4,
            "best_proxy_rows_needed_to_n20": 16,
            "best_proxy_score": 0.62,
            "best_proxy_r_style_lower": -0.03,
            "best_proxy_r_style_midpoint": 0.27,
            "best_proxy_r_style_upper": 0.57,
            "best_proxy_r_style_result_class": "PROXY_R_INTERVAL_STRADDLES_ZERO",
            "proxy_scalar_interpretation_allowed": False,
            "keep_kill_redesign_decision": "BUILD_REQUIRED",
        }
    )
    scope = exact_control_scope_resolution(
        {
            "exact_control_scope_acquisition_execution_row_id": "scope",
            "denominator_source_acquisition_status": (
                "DENOM_SOURCE_ACQ_EXEC_CONTROL_SCOPE_GUARDED_PROXY_CONFIRMED_BUILD_OPEN"
            ),
            "target_action_rows": 4,
            "target_underpowered_rows": 4,
            "proxy_scalar_interpretation_allowed": True,
            "keep_kill_redesign_decision": "KEEP_GUARDED_PROXY",
        },
        [target],
    )
    source = source_resolution(
        {
            "denominator_source_acquisition_execution_row_id": "source",
            "denominator_source_acquisition_status": (
                "DENOM_SOURCE_ACQ_EXEC_SOURCE_EXACT_UNDER_N20_NEGATIVE_PROXY_KILL_CONFIRMED"
            ),
            "materialization_proxy_score": 0.10,
            "materialization_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_NEGATIVE",
            "proxy_contradiction_found": False,
            "keep_kill_redesign_decision": "KILL_PROXY",
        }
    )
    horizon = horizon_resolution(
        {
            "denominator_source_acquisition_execution_row_id": "horizon",
            "keep_kill_redesign_decision": "KILL",
            "source_proxy_score": 0.05,
            "repair_upper_proxy_r_style_lower": -0.52,
            "repair_upper_proxy_r_style_midpoint": -0.30,
            "repair_upper_proxy_r_style_upper": -0.08,
            "repair_upper_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_NEGATIVE",
        }
    )
    scope["denominator_source_resolution_row_id"] = "scope-resolution"
    source["denominator_source_resolution_row_id"] = "source-resolution"
    horizon["denominator_source_resolution_row_id"] = "horizon-resolution"

    scope_impl = implementation_resolution(scope)
    source_impl = implementation_resolution(source)
    source_next = next_compute_action(source)
    horizon_next = next_compute_action(horizon)

    assert target["candidate_implementation_state"] == "BLOCKED_EXACT_CONTROL_TARGET_BUILD"
    assert scope["candidate_implementation_state"] == "GUARDED_PROXY_IMPLEMENTATION_CANDIDATE"
    assert scope["scope_target_proxy_score_mean"] == 0.62
    assert scope_impl["implementation_resolution_status"] == "IMPLEMENT_GUARDED_SCOPE_PROXY_CANDIDATE"
    assert scope_impl["candidate_use_allowed_now"] is True
    assert source["candidate_implementation_state"] == "SOURCE_PROXY_KILLED"
    assert source_impl["implementation_resolution_status"] == "DO_NOT_IMPLEMENT_KILLED_CANDIDATE"
    assert source_next["next_same_resource_action"] == "exact_source_rebuild_contradiction_check_only"
    assert horizon["candidate_implementation_state"] == "HORIZON_KILLED"
    assert horizon_next is None


def test_branch_local_denominator_source_action_execution_materializes_specs_and_kills():
    guarded = guarded_scorer_spec(
        {
            "guarded_candidate_row_id": "guard",
            "denominator_source_resolution_row_id": "scope",
            "scope_target_proxy_score_mean": 0.608153,
            "target_action_rows": 4,
            "target_underpowered_rows": 4,
            "proxy_scalar_interpretation_allowed": True,
            "next_same_resource_action": "exact_control_scope_denominator_build",
        }
    )
    next_row = next_action_execution(
        {
            "next_compute_action_row_id": "next",
            "input_resolution_row_id": "scope",
            "candidate_implementation_state": "GUARDED_PROXY_IMPLEMENTATION_CANDIDATE",
            "next_same_resource_action": "exact_control_scope_denominator_build",
            "keep_kill_redesign_decision": "KEEP_GUARDED_PROXY",
        },
        {"denominator_source_resolution_status": "DENOM_SOURCE_RESOLUTION_EXACT_CONTROL_SCOPE_GUARDED_IMPLEMENTATION_CANDIDATE"},
    )
    killed = terminal_kill_preservation(
        {
            "terminal_kill_row_id": "kill",
            "denominator_source_resolution_row_id": "source",
            "candidate_implementation_state": "SOURCE_PROXY_KILLED",
            "keep_kill_redesign_decision": "KILL_PROXY",
            "decision_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_NEGATIVE",
        }
    )

    assert guarded["action_execution_status"] == "ACTION_EXEC_GUARDED_SCORER_SPEC_MATERIALIZED"
    assert guarded["guarded_proxy_score_class"] == "GUARDED_SCOPE_PROXY_SCORE_GE_060"
    assert guarded["candidate_use_allowed_now"] is True
    assert next_row["action_execution_status"] == "ACTION_EXEC_EXACT_CONTROL_SCOPE_GUARDED_SPEC_MATERIALIZED_BUILD_OPEN"
    assert next_row["candidate_use_allowed_now"] is True
    assert killed["action_execution_status"] == "ACTION_EXEC_TERMINAL_SOURCE_PROXY_KILL_PRESERVED"
    assert killed["candidate_use_allowed_now"] is False


def test_branch_local_denominator_guarded_scorer_registers_and_scope_scores_only():
    spec = {
        "guarded_scorer_spec_row_id": "guard-spec",
        "input_guarded_candidate_row_id": "guard-candidate",
        "input_resolution_row_id": "scope-resolution",
        "symbol": "USDJPY",
        "route_session": "tokyo_kz",
        "horizon_id": "h4",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "guarded_proxy_score_mean": 0.608153,
        "guarded_proxy_score_class": "GUARDED_SCOPE_PROXY_SCORE_GE_060",
        "proxy_scalar_interpretation_allowed": True,
        "candidate_use_allowed_now": True,
        "target_action_rows": 4,
        "target_underpowered_rows": 4,
        "outside_gbpjpy_xauusd_current_branch_box": True,
    }

    registration = register_research_only_guarded_scope_proxy_scorer(spec)
    matching_event = {
        "symbol": "USDJPY",
        "route_session": "tokyo_kz",
        "horizon_id": "h4",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
    }
    mismatch_event = {**matching_event, "symbol": "XAUUSD"}
    scored = score_guarded_scope_proxy_event(matching_event, registration)
    mismatch = score_guarded_scope_proxy_event(mismatch_event, registration)

    assert registration["guarded_scorer_registration_status"] == "GUARDED_SCORER_REGISTERED_RESEARCH_ONLY"
    assert registration["exact_control_build_still_open"] is True
    assert registration["unconditional_scalar_use_allowed"] is False
    assert event_matches_guarded_scope(matching_event, registration) is True
    assert scored["guarded_scope_proxy_event_status"] == "GUARDED_SCOPE_PROXY_EVENT_SCORE_EMITTED"
    assert scored["guarded_scope_proxy_score"] == 0.608153
    assert mismatch["guarded_scope_proxy_event_status"] == "GUARDED_SCOPE_PROXY_EVENT_SCOPE_MISMATCH"
    assert mismatch["guarded_scope_proxy_score"] is None


def test_branch_local_denominator_detail_execution_splits_build_source_horizon_and_terminal():
    target = detail_execution_from_next_action(
        {
            "action_execution_lane": "EXACT_CONTROL_TARGET_BUILD",
            "guarded_scorer_next_action_carryforward_row_id": "next-target",
            "rows_needed_to_n20": 16,
            "candidate_implementation_state": "BLOCKED_EXACT_CONTROL_TARGET_BUILD",
        }
    )
    guarded_scope = detail_execution_from_next_action(
        {
            "action_execution_lane": "EXACT_CONTROL_SCOPE_BUILD",
            "matched_guarded_scorer_registration_row_id": "guarded-reg",
            "candidate_implementation_state": "GUARDED_PROXY_IMPLEMENTATION_CANDIDATE",
        }
    )
    source = detail_execution_from_next_action(
        {
            "action_execution_lane": "SOURCE_CONTRADICTION_CHECK",
            "decision_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_NEGATIVE",
            "current_exact_gap_to_n20": 12,
            "candidate_implementation_state": "SOURCE_PROXY_KILLED",
        }
    )
    horizon = detail_execution_from_next_action({"action_execution_lane": "HORIZON_REDESIGN"})
    terminal = terminal_detail_from_kill(
        {
            "action_execution_status": "ACTION_EXEC_TERMINAL_SOURCE_PROXY_KILL_PRESERVED",
            "guarded_scorer_terminal_carryforward_row_id": "term",
            "candidate_implementation_state": "SOURCE_PROXY_KILLED",
        }
    )
    rollup = scope_detail_rollup(
        ("USDJPY", "tokyo_kz", "h4", "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION"),
        [guarded_scope],
    )

    assert target["detail_execution_status"] == "DETAIL_EXEC_EXACT_CONTROL_TARGET_EXACT_UNAVAILABLE_PROXY_UNDER_N20"
    assert target["candidate_use_allowed_now"] is False
    assert guarded_scope["detail_execution_status"] == (
        "DETAIL_EXEC_EXACT_CONTROL_SCOPE_GUARDED_SCORER_REGISTERED_BUILD_OPEN_TARGETS_UNDER_N20"
    )
    assert guarded_scope["candidate_use_allowed_now"] is True
    assert guarded_scope["unconditional_scalar_use_allowed"] is False
    assert source["detail_execution_decision"] == "KEEP_SOURCE_PROXY_KILL_UNLESS_EXACT_SOURCE_CONTRADICTS"
    assert horizon["detail_execution_status"] == "DETAIL_EXEC_HORIZON_REDESIGN_REPAIR_BOUND_SCOREABLE"
    assert terminal["detail_execution_family"] == "SOURCE_TERMINAL_KILL"
    assert terminal["candidate_use_allowed_now"] is False
    assert rollup["scope_detail_status"] == "DETAIL_SCOPE_GUARDED_SCORER_REGISTERED_EXACT_BUILD_OPEN"


def test_branch_local_denominator_detail_decisions_emit_default_off_and_kills():
    guarded_scope = {
        "denominator_detail_execution_row_id": "detail-guard",
        "detail_execution_family": "EXACT_CONTROL",
        "detail_execution_status": "DETAIL_EXEC_EXACT_CONTROL_SCOPE_GUARDED_SCORER_REGISTERED_BUILD_OPEN_TARGETS_UNDER_N20",
        "candidate_use_allowed_now": True,
        "matched_guarded_scorer_registration_row_id": "guarded-reg",
        "target_action_rows": 4,
        "target_underpowered_rows": 4,
    }
    source = {
        "denominator_detail_execution_row_id": "detail-source",
        "detail_execution_family": "SOURCE_CONTRADICTION",
        "detail_execution_status": "DETAIL_EXEC_SOURCE_CONTRADICTION_NO_CONTRADICTION_NEGATIVE_PROXY_PERSISTS",
        "decision_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_NEGATIVE",
        "proxy_contradiction_found": False,
    }
    horizon = {
        "denominator_detail_execution_row_id": "detail-horizon",
        "detail_execution_family": "HORIZON_REDESIGN",
        "detail_execution_status": "DETAIL_EXEC_HORIZON_REDESIGN_REPAIR_BOUND_SCOREABLE",
        "repaired_targetable_upper_bound_n": 23,
        "repair_upper_proxy_r_style_result_class": "PROXY_R_INTERVAL_STRADDLES_ZERO",
    }
    terminal = {
        "denominator_terminal_detail_row_id": "terminal-horizon",
        "detail_execution_family": "HORIZON_TERMINAL_KILL",
        "detail_execution_status": "DETAIL_EXEC_TERMINAL_HORIZON_KILL_PRESERVED",
        "terminal_decision": True,
    }

    exact_decision = exact_control_expansion_decision(guarded_scope)
    source_decision = source_completeness_decision(source)
    horizon_result = horizon_decision(horizon)
    terminal_result = horizon_decision(terminal)
    default_impl = default_off_implementation_decision(guarded_scope)
    behavior = scorer_behavior_decision(horizon)

    assert exact_decision["exact_control_expansion_status"] == (
        "EXACT_CONTROL_EXPANSION_SCOPE_GUARDED_SCORER_DEFAULT_OFF_READY_BUILD_OPEN"
    )
    assert exact_decision["unconditional_scalar_use_allowed"] is False
    assert source_decision["source_completeness_status"] == (
        "SOURCE_COMPLETENESS_NO_EXACT_CONTRADICTION_NEGATIVE_PROXY_KILL_PERSISTS"
    )
    assert source_decision["implementation_permission"] == "DO_NOT_IMPLEMENT_SOURCE_PROXY_BRANCH"
    assert horizon_result["horizon_detail_status"] == "HORIZON_DETAIL_REDESIGN_DEFAULT_OFF_TARGETABILITY_CANDIDATE"
    assert terminal_result["horizon_detail_status"] == "HORIZON_DETAIL_TERMINAL_KILL_PRESERVED"
    assert default_impl["default_off_implementation_status"] == "DEFAULT_OFF_GUARDED_SCOPE_SCORER_CANDIDATE"
    assert behavior["scorer_behavior_status"] == "SCORER_BEHAVIOR_HORIZON_REDESIGN_DEFAULT_OFF"


def test_branch_local_denominator_default_off_scorer_matches_scope_and_gates_kill_check():
    behavior = {
        "scorer_behavior_row_id": "behavior",
        "scorer_behavior_status": "SCORER_BEHAVIOR_HORIZON_REPAIR_RESCORER_DEFAULT_OFF",
        "input_detail_execution_row_id": "detail",
        "symbol": "XAGUSD",
        "route_session": "tokyo_kz",
        "horizon_id": "h32",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
    }
    registration = register_default_off_scorer(behavior, {"repair_upper_proxy_r_style_midpoint": 0.31})
    registration["default_off_scorer_registration_row_id"] = "registration"
    guarded = register_default_off_scorer(
        {**behavior, "scorer_behavior_status": "SCORER_BEHAVIOR_GUARDED_SCOPE_PROXY_MATCH_ONLY"},
        {"guarded_proxy_score_mean": 0.608153},
    )
    guarded["default_off_scorer_registration_row_id"] = "guarded"
    matching_event = {
        "symbol": "XAGUSD",
        "route_session": "tokyo_kz",
        "horizon_id": "h32",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
    }
    mismatch_event = {**matching_event, "symbol": "XAUUSD"}
    scored = score_default_off_event(matching_event, registration)
    mismatch = score_default_off_event(mismatch_event, registration)
    gate = register_default_off_scorer(
        {**behavior, "scorer_behavior_status": "SCORER_BEHAVIOR_HORIZON_KILL_CHECK_REPAIR_GATE"},
        {},
    )
    gate["default_off_scorer_registration_row_id"] = "gate"
    guarded_scored = score_default_off_event(matching_event, guarded)
    gated = score_default_off_event(matching_event, gate)

    assert registration["default_off_scorer_registration_status"] == (
        "DEFAULT_OFF_SCORER_REGISTERED_HORIZON_REPAIR_SCORE"
    )
    assert registration["unconditional_scalar_use_allowed"] is False
    assert guarded["default_off_scorer_registration_status"] == "DEFAULT_OFF_SCORER_REGISTERED_MATCH_SCOPE_SCORE"
    assert guarded["default_off_scorer_score"] == 0.608153
    assert event_matches_default_off_scope(matching_event, registration) is True
    assert scored["default_off_scorer_event_status"] == "DEFAULT_OFF_SCORER_EVENT_SCORE_EMITTED"
    assert scored["default_off_scorer_event_score"] == 0.31
    assert guarded_scored["default_off_scorer_event_status"] == "DEFAULT_OFF_SCORER_EVENT_SCORE_EMITTED"
    assert guarded_scored["default_off_scorer_event_score"] == 0.608153
    assert mismatch["default_off_scorer_event_status"] == "DEFAULT_OFF_SCORER_EVENT_SCOPE_MISMATCH"
    assert gated["default_off_scorer_event_status"] == "DEFAULT_OFF_SCORER_EVENT_KILL_CHECK_GATE_HELD"


def test_branch_local_denominator_default_off_application_preserves_blockers_and_rejection_audits():
    implementation = {
        "default_off_implementation_row_id": "impl",
        "input_detail_execution_row_id": "detail",
        "default_off_implementation_status": "DEFAULT_OFF_GUARDED_SCOPE_SCORER_CANDIDATE",
        "decision_result": "DEFAULT_OFF_SCORER_CANDIDATE",
        "detail_execution_family": "EXACT_CONTROL",
        "symbol": "XAGUSD",
        "route_session": "tokyo_kz",
        "horizon_id": "h32",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "candidate_use_allowed_now": True,
    }
    registration = {
        "default_off_scorer_registration_row_id": "registration",
        "default_off_scorer_kind": "DEFAULT_OFF_GUARDED_SCOPE_PROXY_SCORER",
        "default_off_scorer_score": 0.608153,
        "symbol": "XAGUSD",
        "route_session": "tokyo_kz",
        "horizon_id": "h32",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
    }
    exact = {
        "exact_control_expansion_status": "EXACT_CONTROL_EXPANSION_SCOPE_GUARDED_SCORER_DEFAULT_OFF_READY_BUILD_OPEN"
    }
    applied = default_off_application_decision(implementation, registration, exact)
    scorer_applied = scorer_application_decision(implementation, registration)

    assert applied["default_off_application_status"] == "DEFAULT_OFF_APPLICATION_GUARDED_SCOPE_SCORE_READY_EXACT_BUILD_OPEN"
    assert applied["default_off_application_score"] == 0.608153
    assert applied["exact_control_build_still_required"] is True
    assert scorer_applied["scorer_application_status"] == "SCORER_APPLICATION_SCORE_EMITTED_DEFAULT_OFF"

    blocked = {
        **implementation,
        "default_off_implementation_status": "DEFAULT_OFF_BLOCKED_EXACT_CONTROL_BUILD_REQUIRED",
        "decision_result": "BUILD_REQUIRED",
        "candidate_use_allowed_now": False,
    }
    target_exact = {
        "exact_control_expansion_status": "EXACT_CONTROL_EXPANSION_TARGET_EXACT_UNAVAILABLE_BUILD_REQUIRED",
        "exact_control_expansion_action": "build_exact_target_control_denominator_before_scalar_use",
        "exact_control_member_count": 0,
        "best_available_proxy_relation": "SAME_SYMBOL_SESSION",
        "best_available_proxy_member_count": 17,
        "best_proxy_rows_needed_to_n20": 3,
    }
    blocked_applied = default_off_application_decision(blocked, None, target_exact)
    blocker = exact_control_blocker_decision(blocked, target_exact)

    assert blocked_applied["default_off_application_status"] == (
        "DEFAULT_OFF_APPLICATION_EXACT_TARGET_CONTROL_BUILD_REQUIRED_NO_RUNTIME_SCORE"
    )
    assert blocked_applied["default_off_application_score"] is None
    assert blocker["exact_control_application_blocker_status"] == (
        "EXACT_CONTROL_APPLICATION_TARGET_BUILD_REQUIRED_NO_RUNTIME_SCORE"
    )
    assert blocker["best_proxy_rows_needed_to_n20"] == 3

    rejected = {
        **implementation,
        "default_off_implementation_status": "DEFAULT_OFF_KILLED_SOURCE_PROXY_NEGATIVE_NO_CONTRADICTION",
        "decision_result": "KILL_PRESERVED",
        "detail_execution_family": "SOURCE_CONTRADICTION",
        "candidate_use_allowed_now": False,
    }
    source = {
        "source_completeness_status": "SOURCE_COMPLETENESS_NO_EXACT_CONTRADICTION_NEGATIVE_PROXY_KILL_PERSISTS",
        "source_completeness_decision": "preserve_source_proxy_kill_and_use_as_failure_or_avoid_intelligence",
        "decision_proxy_r_style_result_class": "PROXY_R_INTERVAL_ALL_NEGATIVE",
    }
    rejection_applied = default_off_application_decision(rejected, None, None, source)
    audit = current_claim_rejection_audit(rejected, source, None)

    assert rejection_applied["default_off_application_decision_class"] == (
        "CURRENT_CLAIM_REJECTED_MECHANISM_PRESERVED"
    )
    assert rejection_applied["current_claim_rejection_audit_required"] is True
    assert audit["claim_rejected_scope"] == "CURRENT_CLAIM_ONLY_UNDERLYING_MECHANISM_PRESERVED"
    assert "avoid_filter" in audit["mechanism_or_intelligence_preserved_as"]


def test_branch_local_denominator_exact_control_effective_n_deduplicates_proxy_members():
    blocker = {
        "exact_control_blocker_row_id": "blocker",
        "exact_control_application_blocker_status": "EXACT_CONTROL_APPLICATION_TARGET_BUILD_REQUIRED_NO_RUNTIME_SCORE",
        "symbol": "USDJPY",
        "route_session": "tokyo_kz",
        "horizon_id": "h4",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "exact_control_member_count": 0,
        "best_available_proxy_member_count": 24,
    }
    execution = {
        "denominator_source_execution_row_id": "exec",
        "best_available_proxy_relation": "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION",
        "denominator_source_execution_status": "DENOM_SOURCE_EXEC_EXACT_CONTROL_TARGET_PROXY_UNDER_N20_BUILD_REQUIRED",
    }
    members = []
    for index in range(24):
        identity_group = index % 6
        members.append(
            {
                "control_member_relation_split_row_id": f"member-{index}",
                "symbol": "USDJPY",
                "route_session": "tokyo_kz",
                "horizon_id": "h4",
                "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
                "control_member_relation": "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION",
                "control_proxy_score": 0.61,
                "member_execution_bundle_row_id": f"member-exec-{identity_group}",
                "member_runtime_work_row_id": f"member-runtime-{identity_group}",
                "member_symbol": "USDJPY",
                "member_route_session": "tokyo_kz",
                "member_horizon_id": "h4",
                "member_primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
            }
        )

    decision = exact_control_blocker_effective_n_decision(blocker, execution, members)
    scope_decision = exact_control_scope_effective_n_decision(blocker, [blocker], members)
    first_member = control_member_effective_n_row(members[0], True, 4)

    assert decision["exact_control_effective_n_status"] == (
        "EXACT_CONTROL_EFFECTIVE_N_RAW_N20_DUPLICATE_INFLATED_BUILD_REQUIRED"
    )
    assert decision["raw_best_proxy_member_count"] == 24
    assert decision["effective_best_proxy_member_count"] == 6
    assert decision["runtime_score_allowed"] is False
    assert scope_decision["exact_control_scope_effective_n_status"] == (
        "EXACT_CONTROL_SCOPE_EFFECTIVE_N_RAW_N20_DUPLICATE_INFLATED"
    )
    assert first_member["member_effective_identity"] == member_effective_identity(members[0])
    assert first_member["member_effective_identity_first_seen"] is True
    assert first_member["member_effective_identity_duplicate_count"] == 4


def test_branch_local_denominator_exact_control_construction_builds_tick_control_and_preserves_redesign():
    scope = {
        "exact_control_scope_effective_n_row_id": "scope",
        "symbol": "USDJPY",
        "route_session": "tokyo_kz",
        "horizon_id": "h4",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "effective_best_proxy_member_count": 8,
    }
    control = {
        "flagged_n": 32,
        "control_n": 144,
        "flagged_mean_future_change_per_current_range": 0.50,
        "control_mean_future_change_per_current_range": 0.60,
        "flagged_delta_alignment_rate": 0.62,
        "control_delta_alignment_rate": 0.55,
    }
    constructed = exact_control_scope_construction(scope, control, denominator_event_count=144, flagged_event_count=32)
    blocker = exact_control_blocker_construction(
        {
            "exact_control_blocker_effective_n_row_id": "blocker-effn",
            "symbol": "USDJPY",
            "route_session": "tokyo_kz",
            "horizon_id": "h4",
            "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        },
        constructed,
    )
    event = exact_control_denominator_event_row(
        scope,
        {
            "symbol": "USDJPY",
            "session_bucket": "tokyo_core_0000_0300",
            "horizon_id": "h4",
            "primitive_flags": ["SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION"],
            "future_change_per_current_range": 0.7,
        },
        1,
    )
    sierra = sierra_translation_proxy_row(scope, None, "6JM26-CME", None)

    assert constructed["exact_control_construction_status"] == "EXACT_CONTROL_CONSTRUCTION_TICK_M15_N20_BUILT"
    assert constructed["branch_local_exact_control_score_allowed"] is True
    assert constructed["exact_control_result_class"] == "EXACT_CONTROL_NEGATIVE_TARGET_DELTA_ALIGNMENT_POSITIVE_SPLIT"
    assert blocker["current_claim_rejected"] is False
    assert blocker["mixed_or_redesign_required"] is True
    assert blocker["missed_opportunity_audit"]["underlying_mechanism_preserved"] is True
    assert event["primitive_present"] is True
    assert sierra["sierra_translation_status"] == "SIERRA_TRANSLATION_NO_TAXONOMY_EQUIVALENT"


def test_branch_local_denominator_exact_control_scorer_redesign_emits_scores_and_split_signals():
    positive_scope = {
        "exact_control_scope_construction_row_id": "scope-positive",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "exact_control_result_class": "EXACT_CONTROL_POSITIVE_TARGET_AND_ALIGNMENT_DELTA",
        "exact_control_proxy_r_style_delta": 0.875964,
        "exact_control_alignment_delta": 0.095681,
    }
    split_scope = {
        **positive_scope,
        "exact_control_scope_construction_row_id": "scope-split",
        "exact_control_result_class": "EXACT_CONTROL_NEGATIVE_TARGET_DELTA_ALIGNMENT_POSITIVE_SPLIT",
        "exact_control_proxy_r_style_delta": -0.290076,
        "exact_control_alignment_delta": 0.088329,
    }
    positive_spec = exact_control_scope_runtime_spec(positive_scope)
    split_spec = exact_control_scope_runtime_spec(split_scope)
    positive_decision = exact_control_blocker_runtime_decision(positive_scope, positive_spec)
    split_decision = exact_control_blocker_runtime_decision(split_scope, split_spec)
    event = {
        "exact_control_denominator_event_row_id": "event",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "primitive_present": True,
    }
    scored_event = exact_control_event_score(event, positive_spec)
    split_event = exact_control_event_score(event, split_spec)

    assert positive_spec["exact_control_scope_runtime_status"] == "EXACT_CONTROL_SCOPE_DEFAULT_OFF_SCORER_REGISTER"
    assert positive_decision["exact_control_blocker_runtime_status"] == "EXACT_CONTROL_BLOCKER_DEFAULT_OFF_SCORER_READY"
    assert scored_event["exact_control_event_runtime_status"] == "EXACT_CONTROL_EVENT_DEFAULT_OFF_SCORE_EMITTED"
    assert scored_event["default_off_exact_control_event_score"] == 0.875964
    assert split_spec["redesign_family"] == "REDESIGN_DIRECTIONAL_FEATURE_DROP_TARGET_MAGNITUDE_SCALAR"
    assert split_decision["exact_control_blocker_runtime_status"] == "EXACT_CONTROL_BLOCKER_SPLIT_REDESIGN_REQUIRED"
    assert split_event["exact_control_event_runtime_status"] == "EXACT_CONTROL_EVENT_REDESIGN_ALIGNMENT_SIGNAL_EMITTED"


def test_branch_local_denominator_exact_control_implementation_candidates_preserve_paths():
    positive_scope = {
        "exact_control_scope_runtime_spec_row_id": "scope-spec-positive",
        "input_scope_construction_row_id": "scope-positive",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "exact_control_scope_runtime_status": "EXACT_CONTROL_SCOPE_DEFAULT_OFF_SCORER_REGISTER",
        "exact_control_result_class": "EXACT_CONTROL_POSITIVE_TARGET_AND_ALIGNMENT_DELTA",
        "default_off_exact_control_score": 0.21103,
        "exact_control_alignment_delta": 0.091664,
    }
    split_scope = {
        **positive_scope,
        "exact_control_scope_runtime_spec_row_id": "scope-spec-split",
        "input_scope_construction_row_id": "scope-split",
        "exact_control_scope_runtime_status": "EXACT_CONTROL_SCOPE_SPLIT_REDESIGN_REGISTER",
        "exact_control_result_class": "EXACT_CONTROL_NEGATIVE_TARGET_DELTA_ALIGNMENT_POSITIVE_SPLIT",
        "default_off_exact_control_score": None,
        "redesign_family": "REDESIGN_TIGHTEN_TARGET_OR_SHORTER_HORIZON",
    }
    positive_blocker = {
        "exact_control_blocker_runtime_decision_row_id": "blocker-positive",
        "input_blocker_construction_row_id": "construct-positive",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "exact_control_blocker_runtime_status": "EXACT_CONTROL_BLOCKER_DEFAULT_OFF_SCORER_READY",
        "exact_control_result_class": "EXACT_CONTROL_POSITIVE_TARGET_AND_ALIGNMENT_DELTA",
        "default_off_exact_control_score": 0.21103,
        "exact_control_proxy_r_style_delta": 0.21103,
        "exact_control_alignment_delta": 0.091664,
    }
    split_blocker = {
        **positive_blocker,
        "exact_control_blocker_runtime_decision_row_id": "blocker-split",
        "input_blocker_construction_row_id": "construct-split",
        "exact_control_blocker_runtime_status": "EXACT_CONTROL_BLOCKER_SPLIT_REDESIGN_REQUIRED",
        "exact_control_result_class": "EXACT_CONTROL_NEGATIVE_TARGET_DELTA_ALIGNMENT_POSITIVE_SPLIT",
        "default_off_exact_control_score": None,
        "redesign_family": "REDESIGN_TIGHTEN_TARGET_OR_SHORTER_HORIZON",
    }
    scorer = {
        "exact_control_scope_default_off_scorer_row_id": "scorer-positive",
        "input_blocker_runtime_decision_row_id": "blocker-positive",
    }
    redesign = {
        "exact_control_redesign_execution_row_id": "redesign-split",
        "input_blocker_runtime_decision_row_id": "blocker-split",
    }
    score_event = {
        "exact_control_event_score_row_id": "event-score",
        "input_denominator_event_row_id": "event-source-score",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "primitive_present": True,
        "exact_control_event_runtime_status": "EXACT_CONTROL_EVENT_DEFAULT_OFF_SCORE_EMITTED",
        "default_off_exact_control_event_score": 0.21103,
    }
    redesign_event = {
        **score_event,
        "exact_control_event_score_row_id": "event-redesign",
        "input_denominator_event_row_id": "event-source-redesign",
        "exact_control_event_runtime_status": "EXACT_CONTROL_EVENT_REDESIGN_ALIGNMENT_SIGNAL_EMITTED",
        "default_off_exact_control_event_score": None,
        "redesign_alignment_signal": 0.130167,
        "redesign_family": "REDESIGN_TIGHTEN_TARGET_OR_SHORTER_HORIZON",
    }
    context_event = {
        **score_event,
        "exact_control_event_score_row_id": "event-context",
        "input_denominator_event_row_id": "event-source-context",
        "primitive_present": False,
        "exact_control_event_runtime_status": "EXACT_CONTROL_EVENT_DENOMINATOR_CONTROL_CONTEXT",
        "default_off_exact_control_event_score": None,
    }

    positive_scope_impl = exact_control_scope_implementation_candidate(positive_scope)
    split_scope_impl = exact_control_scope_implementation_candidate(split_scope)
    positive_blocker_impl = exact_control_blocker_implementation_candidate(positive_blocker, scorer, None)
    split_blocker_impl = exact_control_blocker_implementation_candidate(split_blocker, None, redesign)
    score_observation = exact_control_event_implementation_observation(score_event)
    redesign_observation = exact_control_event_implementation_observation(redesign_event)
    context_observation = exact_control_event_implementation_observation(context_event)
    code_path = exact_control_code_path_spec(positive_blocker_impl, 1)

    assert positive_scope_impl["exact_control_scope_implementation_status"] == (
        "EXACT_CONTROL_SCOPE_IMPLEMENT_DEFAULT_OFF_SCORER_CODE_PATH"
    )
    assert split_scope_impl["exact_control_scope_implementation_status"] == (
        "EXACT_CONTROL_SCOPE_IMPLEMENT_SPLIT_REDESIGN_CODE_PATH"
    )
    assert positive_blocker_impl["exact_control_blocker_implementation_status"] == (
        "EXACT_CONTROL_BLOCKER_IMPLEMENT_DEFAULT_OFF_SCORER_CANDIDATE"
    )
    assert positive_blocker_impl["input_scope_default_off_scorer_row_id"] == "scorer-positive"
    assert split_blocker_impl["exact_control_blocker_implementation_status"] == (
        "EXACT_CONTROL_BLOCKER_IMPLEMENT_SPLIT_REDESIGN_CANDIDATE"
    )
    assert split_blocker_impl["input_redesign_execution_row_id"] == "redesign-split"
    assert split_blocker_impl["missed_opportunity_preserved"] is True
    assert score_observation["exact_control_event_implementation_status"] == (
        "EXACT_CONTROL_EVENT_IMPLEMENTATION_SCORE_OBSERVATION"
    )
    assert redesign_observation["exact_control_event_implementation_status"] == (
        "EXACT_CONTROL_EVENT_IMPLEMENTATION_REDESIGN_SIGNAL_OBSERVATION"
    )
    assert context_observation["exact_control_event_implementation_status"] == (
        "EXACT_CONTROL_EVENT_IMPLEMENTATION_DENOMINATOR_CONTEXT_OBSERVATION"
    )
    assert code_path["code_path_status"] == "EXACT_CONTROL_CODE_PATH_DEFAULT_OFF_SCORER_SPEC"
    assert code_path["runtime_score_allowed"] is False
    assert code_path["unconditional_scalar_use_allowed"] is False
    assert code_path["live_effect"] is False


def test_branch_local_denominator_exact_control_runtime_router_dedupes_scope_lineage():
    default_code_path = {
        "exact_control_code_path_spec_row_id": "code-default-scope",
        "input_scope_runtime_spec_row_id": "scope-default",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "code_path_status": "EXACT_CONTROL_CODE_PATH_DEFAULT_OFF_SCORER_SPEC",
        "module_slot": "branch_local_exact_control_default_off_scorer_registry",
        "required_guard": "exact_scope_match_and_primitive_present",
        "default_off_exact_control_score": 0.21103,
    }
    duplicate_default_code_path = {
        **default_code_path,
        "exact_control_code_path_spec_row_id": "code-default-blocker",
        "input_scope_runtime_spec_row_id": None,
        "input_blocker_runtime_decision_row_id": "blocker-default",
    }
    split_code_path = {
        **default_code_path,
        "exact_control_code_path_spec_row_id": "code-split",
        "input_scope_runtime_spec_row_id": "scope-split",
        "code_path_status": "EXACT_CONTROL_CODE_PATH_SPLIT_REDESIGN_SPEC",
        "module_slot": "branch_local_exact_control_redesign_router",
        "required_guard": "exact_scope_match_and_redesign_family",
        "default_off_exact_control_score": None,
        "redesign_family": "REDESIGN_TIGHTEN_TARGET_OR_SHORTER_HORIZON",
    }
    default_registration = register_exact_control_code_path(default_code_path)
    default_registration["exact_control_runtime_code_path_registration_row_id"] = "runtime-default-scope"
    duplicate_registration = register_exact_control_code_path(duplicate_default_code_path)
    duplicate_registration["exact_control_runtime_code_path_registration_row_id"] = "runtime-default-blocker"
    split_registration = register_exact_control_code_path(split_code_path)
    split_registration["exact_control_runtime_code_path_registration_row_id"] = "runtime-split"
    effective_default = effective_scope_registration([default_registration, duplicate_registration])
    effective_default["exact_control_effective_scope_registration_row_id"] = "effective-default"
    effective_split = effective_scope_registration([split_registration])
    effective_split["exact_control_effective_scope_registration_row_id"] = "effective-split"
    score_event = {
        "exact_control_event_implementation_observation_row_id": "event-score",
        "input_event_score_row_id": "score-row",
        "input_denominator_event_row_id": "denom-score",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "primitive_present": True,
    }
    redesign_event = {
        **score_event,
        "redesign_alignment_signal": 0.13,
        "redesign_family": "REDESIGN_TIGHTEN_TARGET_OR_SHORTER_HORIZON",
    }
    context_event = {**score_event, "primitive_present": False}
    scored = route_exact_control_event(score_event, effective_default)
    redesigned = route_exact_control_event(redesign_event, effective_split)
    context = route_exact_control_event(context_event, effective_default)
    audit = duplicate_scope_audit_row(effective_default)

    assert default_registration["runtime_registration_status"] == (
        "EXACT_CONTROL_RUNTIME_REGISTER_DEFAULT_OFF_SCORER_CODE_PATH"
    )
    assert duplicate_registration["runtime_code_path_lineage"] == "BLOCKER_SPEC"
    assert effective_default["effective_scope_registration_status"] == (
        "EXACT_CONTROL_RUNTIME_EFFECTIVE_DEFAULT_OFF_SCORER_SCOPE"
    )
    assert effective_default["linked_code_path_count"] == 2
    assert effective_default["duplicate_code_path_count"] == 1
    assert effective_default["duplicate_handling_status"] == (
        "DUPLICATE_CODE_PATH_LINEAGE_DEDUPED_FOR_RUNTIME_PRESERVED_FOR_AUDIT"
    )
    assert effective_split["effective_scope_registration_status"] == (
        "EXACT_CONTROL_RUNTIME_EFFECTIVE_SPLIT_REDESIGN_SCOPE"
    )
    assert scored["runtime_event_routing_status"] == "EXACT_CONTROL_RUNTIME_EVENT_DEFAULT_OFF_SCORE_EMITTED"
    assert scored["runtime_event_score"] == 0.21103
    assert redesigned["runtime_event_routing_status"] == "EXACT_CONTROL_RUNTIME_EVENT_REDESIGN_SIGNAL_ROUTED"
    assert redesigned["runtime_redesign_alignment_signal"] == 0.13
    assert context["runtime_event_routing_status"] == "EXACT_CONTROL_RUNTIME_EVENT_DENOMINATOR_CONTEXT"
    assert audit["audit_decision"] == "preserve_all_code_path_rows_but_route_events_once_per_effective_scope"
    assert audit["runtime_score_allowed"] is False
    assert audit["unconditional_scalar_use_allowed"] is False


def test_branch_local_denominator_exact_control_redesign_resolution_turns_split_into_decision():
    split_scope = {
        "exact_control_effective_scope_registration_row_id": "scope-split",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "effective_runtime_family": "SPLIT_REDESIGN_ROUTER",
        "redesign_family": "REDESIGN_TIGHTEN_TARGET_OR_SHORTER_HORIZON",
    }
    transfer_scope = {
        **split_scope,
        "exact_control_effective_scope_registration_row_id": "scope-transfer",
        "horizon_id": "h4",
        "effective_runtime_family": "DEFAULT_OFF_SCORER",
        "redesign_family": None,
        "default_off_exact_control_score": 0.21103,
    }
    events = [
        {
            "symbol": "USDJPY",
            "route_session": "off_core_session",
            "tick_session_bucket": "off_core_session",
            "horizon_id": "h16",
            "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
            "primitive_present": True,
            "future_change_per_current_range": 0.10,
            "delta_aligned_with_future": True,
        },
        {
            "symbol": "USDJPY",
            "route_session": "off_core_session",
            "tick_session_bucket": "off_core_session",
            "horizon_id": "h16",
            "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
            "primitive_present": True,
            "future_change_per_current_range": -0.20,
            "delta_aligned_with_future": True,
        },
        {
            "symbol": "USDJPY",
            "route_session": "off_core_session",
            "tick_session_bucket": "off_core_session",
            "horizon_id": "h16",
            "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
            "primitive_present": False,
            "future_change_per_current_range": 0.30,
            "delta_aligned_with_future": False,
        },
    ]
    scope_resolution = redesign_scope_resolution(split_scope, events, [split_scope, transfer_scope])
    scope_resolution["exact_control_redesign_scope_resolution_row_id"] = "resolution-scope"
    blocker = {
        "exact_control_blocker_implementation_candidate_row_id": "blocker-split",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "redesign_family": "REDESIGN_TIGHTEN_TARGET_OR_SHORTER_HORIZON",
    }
    event = {
        "exact_control_event_runtime_routing_row_id": "event-signal",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "runtime_redesign_alignment_signal": 0.5,
        "redesign_family": "REDESIGN_TIGHTEN_TARGET_OR_SHORTER_HORIZON",
        "future_change_per_current_range": 0.10,
        "delta_aligned_with_future": True,
    }
    blocker_resolution = redesign_blocker_resolution(blocker, scope_resolution)
    event_resolution = redesign_event_signal_resolution(event, scope_resolution)

    assert scope_resolution["horizon_transfer_status"] == (
        "REDESIGN_RESOLUTION_HORIZON_TRANSFER_DEFAULT_OFF_SCORER_AVAILABLE"
    )
    assert scope_resolution["transfer_target_horizon_id"] == "h4"
    assert scope_resolution["redesign_resolution_decision"] == (
        "REDESIGN_RESOLVE_SWITCH_TO_SHORTER_HORIZON_DEFAULT_OFF_SCORER"
    )
    assert scope_resolution["missed_opportunity_preserved"] is True
    assert blocker_resolution["redesign_resolution_decision"] == scope_resolution["redesign_resolution_decision"]
    assert blocker_resolution["candidate_use_allowed_now"] is False
    assert event_resolution["redesign_event_resolution_status"] == (
        "REDESIGN_EVENT_SIGNAL_CONSUMED_IN_SCOPE_DECISION"
    )
    assert event_resolution["runtime_redesign_alignment_signal"] == 0.5
    assert event_resolution["runtime_score_allowed"] is False


def test_branch_local_denominator_exact_control_redesign_module_integration_registers_slots():
    scope_resolution = {
        "exact_control_redesign_scope_resolution_row_id": "resolution-scope",
        "input_effective_scope_registration_row_id": "effective-split",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "redesign_family": "REDESIGN_DIRECTIONAL_FEATURE_DROP_TARGET_MAGNITUDE_SCALAR",
        "redesign_resolution_decision": "REDESIGN_RESOLVE_DIRECTIONAL_CONTEXT_FEATURE_DROP_TARGET_SCALAR",
        "redesign_resolution_action": "implement_directional_alignment_context_feature_default_off",
        "redesign_alignment_delta": 0.15,
        "redesign_exact_target_delta": -0.20,
        "underlying_mechanism_preserved_as": "redesign_or_directional_context_or_horizon_transfer_or_avoid_inverse_candidate",
    }
    scope_module = redesign_scope_module_integration(scope_resolution)
    scope_module["exact_control_redesign_scope_module_integration_row_id"] = "scope-module"
    blocker_resolution = {
        **scope_resolution,
        "exact_control_redesign_blocker_resolution_row_id": "blocker-resolution",
        "input_blocker_implementation_candidate_row_id": "blocker-split",
    }
    event_resolution = {
        **scope_resolution,
        "exact_control_redesign_event_signal_resolution_row_id": "event-resolution",
        "input_event_runtime_routing_row_id": "event-runtime",
        "runtime_redesign_alignment_signal": 0.42,
        "future_change_per_current_range": 0.12,
        "delta_aligned_with_future": True,
    }
    blocker_module = redesign_blocker_module_integration(blocker_resolution, scope_module)
    event_module = redesign_event_module_observation(event_resolution, scope_module)
    code_surface = redesign_code_surface_registration(scope_module, 1)

    assert scope_module["redesign_module_integration_status"] == (
        "REDESIGN_MODULE_REGISTER_DIRECTIONAL_CONTEXT_FEATURE"
    )
    assert scope_module["module_slot"] == "branch_local_exact_control_directional_context_feature"
    assert "delta_aligned_with_future" in scope_module["required_runtime_fields"]
    assert blocker_module["input_scope_module_integration_row_id"] == "scope-module"
    assert blocker_module["missed_opportunity_preserved"] is True
    assert event_module["event_module_observation_status"] == (
        "REDESIGN_EVENT_CONSUMED_BY_BRANCH_LOCAL_MODULE_SLOT"
    )
    assert event_module["runtime_redesign_alignment_signal"] == 0.42
    assert code_surface["code_surface_status"] == "REDESIGN_MODULE_CODE_SURFACE_REGISTERED_DEFAULT_OFF"
    assert code_surface["runtime_score_allowed"] is False
    assert code_surface["unconditional_scalar_use_allowed"] is False


def test_branch_local_denominator_exact_control_redesign_module_execution_preserves_controls():
    scope_module = {
        "exact_control_redesign_scope_module_integration_row_id": "scope-module",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "module_slot": "branch_local_exact_control_tighter_target_stress_tester",
        "required_guard": "exact_scope_match_and_target_delta_near_zero_alignment_positive",
        "redesign_resolution_decision": "REDESIGN_RESOLVE_TIGHTEN_TARGET_STRESS_FIRST",
    }
    runtime_events = [
        {
            "exact_control_event_runtime_routing_row_id": "event-signal",
            "symbol": "USDJPY",
            "route_session": "off_core_session",
            "tick_session_bucket": "off_core_session",
            "horizon_id": "h16",
            "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
            "primitive_present": True,
            "future_change_per_current_range": 0.10,
            "delta_aligned_with_future": True,
            "runtime_redesign_alignment_signal": 0.25,
        },
        {
            "exact_control_event_runtime_routing_row_id": "event-control",
            "symbol": "USDJPY",
            "route_session": "off_core_session",
            "tick_session_bucket": "off_core_session",
            "horizon_id": "h16",
            "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
            "primitive_present": False,
            "future_change_per_current_range": -0.05,
            "delta_aligned_with_future": False,
        },
    ]
    scope_execution = redesign_scope_module_execution(scope_module, runtime_events)
    scope_execution["exact_control_redesign_scope_module_execution_row_id"] = "scope-exec"
    signal_event = redesign_event_module_execution(runtime_events[0], scope_execution)
    control_event = redesign_event_module_execution(runtime_events[1], scope_execution)
    non_module_event = redesign_event_module_execution({**runtime_events[0], "primitive_flag": "OTHER"}, None)
    code_surface = redesign_code_surface_execution(
        {
            "exact_control_redesign_code_surface_registration_row_id": "code-surface",
            **scope_module,
        },
        scope_execution,
    )

    assert scope_execution["module_scope_signal_event_rows"] == 1
    assert scope_execution["module_scope_control_event_rows"] == 1
    assert scope_execution["module_execution_status"] == "REDESIGN_MODULE_SCOPE_EXECUTE_TIGHTER_TARGET_STRESS"
    assert scope_execution["module_execution_target_delta"] == 0.15
    assert signal_event["event_module_execution_status"] == (
        "REDESIGN_MODULE_EXECUTION_TIGHTER_TARGET_STRESS_SIGNAL"
    )
    assert control_event["module_scope_relation"] == "MODULE_SCOPE_CONTROL_EVENT"
    assert non_module_event["module_scope_relation"] == "NON_MODULE_SCOPE_CONTEXT_EVENT"
    assert code_surface["code_surface_execution_status"] == (
        "REDESIGN_MODULE_CODE_SURFACE_EXECUTED_DEFAULT_OFF_OBSERVATION"
    )
    assert code_surface["runtime_score_allowed"] is False


def test_branch_local_denominator_exact_control_redesign_module_delta_comparator_registers_default_off_candidate():
    scope_execution = {
        "exact_control_redesign_scope_module_execution_row_id": "scope-exec",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "module_slot": "branch_local_exact_control_shorter_horizon_transfer_router",
        "module_scope_signal_event_rows": 12,
        "module_scope_control_event_rows": 44,
        "module_execution_target_delta": -0.25,
        "module_execution_alignment_delta": 0.15,
        "transfer_target_horizon_id": "h4",
        "transfer_target_score": 0.21,
    }
    effective_scope_rows = [
        {
            "exact_control_effective_scope_registration_row_id": "default-h4",
            "symbol": "USDJPY",
            "route_session": "off_core_session",
            "tick_session_bucket": "off_core_session",
            "horizon_id": "h4",
            "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
            "effective_runtime_family": "DEFAULT_OFF_SCORER",
            "default_off_exact_control_score": 0.21,
        },
        {
            "exact_control_effective_scope_registration_row_id": "default-h32",
            "symbol": "USDJPY",
            "route_session": "off_core_session",
            "tick_session_bucket": "off_core_session",
            "horizon_id": "h32",
            "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
            "effective_runtime_family": "DEFAULT_OFF_SCORER",
            "default_off_exact_control_score": 0.19,
        },
    ]
    event_execution = {
        "exact_control_redesign_event_module_execution_row_id": "event-exec",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "module_slot": "branch_local_exact_control_shorter_horizon_transfer_router",
        "module_scope_relation": "MODULE_SCOPE_SIGNAL_EVENT",
        "event_module_execution_status": "REDESIGN_MODULE_EXECUTION_SHORTER_HORIZON_TRANSFER_SIGNAL",
        "future_change_per_current_range": 0.12,
        "delta_aligned_with_future": True,
        "runtime_redesign_alignment_signal": 0.33,
    }

    candidates = default_scope_candidates(scope_execution, effective_scope_rows)
    comparison = redesign_scope_module_delta_comparison(scope_execution, effective_scope_rows)
    comparison["exact_control_redesign_scope_module_delta_comparison_row_id"] = "scope-delta"
    event_comparison = redesign_event_module_delta_comparison(event_execution, comparison)
    registry_candidate = redesign_registry_candidate_from_comparison(comparison, 1)

    assert len(candidates) == 2
    assert comparison["same_mechanism_shorter_default_off_candidate_count"] == 1
    assert comparison["best_shorter_default_off_horizon_id"] == "h4"
    assert comparison["module_delta_comparator_decision"] == (
        "MODULE_DELTA_REGISTER_SHORTER_HORIZON_TRANSFER_CANDIDATE"
    )
    assert comparison["target_delta_use"] == "TARGET_DELTA_NEGATIVE_DO_NOT_USE_AS_SCALAR"
    assert event_comparison["event_delta_comparison_status"] == "MODULE_DELTA_EVENT_CONSUMED_IN_SCOPE_COMPARATOR"
    assert event_comparison["registry_candidate_class"] == "FINAL_REGISTRY_CANDIDATE_SHORTER_HORIZON_TRANSFER"
    assert registry_candidate["registry_candidate_status"] == "REDESIGN_FINAL_REGISTRY_CANDIDATE_DEFAULT_OFF"
    assert registry_candidate["runtime_score_allowed"] is False
    assert registry_candidate["unconditional_scalar_use_allowed"] is False
    assert registry_candidate["live_effect"] is False


def test_branch_local_denominator_exact_control_redesign_final_registry_applies_exact_scope_events():
    registry_candidate = {
        "exact_control_redesign_registry_candidate_row_id": "candidate-row",
        "input_scope_module_delta_comparison_row_id": "scope-delta",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "module_slot": "branch_local_exact_control_tighter_target_stress_tester",
        "module_delta_comparator_decision": "MODULE_DELTA_REGISTER_TIGHTER_TARGET_STRESS_CANDIDATE",
        "registry_candidate_class": "FINAL_REGISTRY_CANDIDATE_TIGHTER_TARGET_STRESS",
        "target_delta_use": "TARGET_DELTA_NEGATIVE_DO_NOT_USE_AS_SCALAR",
        "module_execution_target_delta": -0.20,
        "module_execution_alignment_delta": 0.16,
    }
    scope_comparison = {
        **registry_candidate,
        "same_mechanism_default_off_candidate_count": 1,
        "same_mechanism_shorter_default_off_candidate_count": 0,
        "best_default_off_horizon_id": "h4",
        "best_default_off_score": 0.31,
        "transfer_target_horizon_id": None,
        "transfer_target_score": None,
    }
    registry = final_registry_row(registry_candidate, scope_comparison, 1)
    code_spec = final_registry_code_spec(registry, 1)
    signal_event = {
        "exact_control_redesign_event_module_delta_comparison_row_id": "event-signal",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "module_slot": "branch_local_exact_control_tighter_target_stress_tester",
        "module_scope_relation": "MODULE_SCOPE_SIGNAL_EVENT",
        "future_change_per_current_range": 0.42,
        "delta_aligned_with_future": True,
        "runtime_redesign_alignment_signal": 0.25,
    }
    control_event = {**signal_event, "exact_control_redesign_event_module_delta_comparison_row_id": "event-control", "module_scope_relation": "MODULE_SCOPE_CONTROL_EVENT"}
    context_event = {**signal_event, "exact_control_redesign_event_module_delta_comparison_row_id": "event-context", "primitive_flag": "OTHER"}
    signal_application = final_registry_event_application(signal_event, registry)
    control_application = final_registry_event_application(control_event, registry)
    context_application = final_registry_event_application(context_event, None)

    assert registry["final_registry_status"] == "FINAL_RED_REGISTRY_TIGHTER_TARGET_STRESS_DEFAULT_OFF"
    assert registry["target_delta_use"] == "TARGET_DELTA_NEGATIVE_DO_NOT_USE_AS_SCALAR"
    assert registry["missed_opportunity_preserved"] is True
    assert code_spec["code_spec_status"] == "FINAL_RED_REGISTRY_CODE_SPEC_DEFAULT_OFF_EXACT_SCOPE"
    assert code_spec["exact_scope_guard"] == "symbol_session_horizon_primitive_match"
    assert signal_application["event_final_registry_application_status"] == (
        "FINAL_RED_REGISTRY_EVENT_TIGHTER_TARGET_STRESS_SIGNAL"
    )
    assert signal_application["final_registry_event_join_state"] == "FINAL_RED_REGISTRY_EVENT_JOINED_EXACT_SCOPE"
    assert control_application["event_final_registry_application_status"] == (
        "FINAL_RED_REGISTRY_EVENT_SAME_SCOPE_CONTROL_CONTEXT"
    )
    assert context_application["event_final_registry_application_status"] == (
        "FINAL_RED_REGISTRY_EVENT_NON_SCOPE_CONTEXT"
    )
    assert context_application["final_registry_event_join_state"] == (
        "FINAL_RED_REGISTRY_EVENT_NO_EXACT_SCOPE_CONTEXT"
    )
    assert context_application["target_delta_use"] is None
    assert signal_application["runtime_score_allowed"] is False
    assert code_spec["unconditional_scalar_use_allowed"] is False


def test_branch_local_denominator_exact_control_redesign_registry_scorer_module_computes_scope_metrics():
    registry = {
        "exact_control_redesign_final_registry_row_id": "registry-row",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "implementation_family": "entry_geometry_or_avoid_inverse_split_default_off",
        "final_registry_status": "FINAL_RED_REGISTRY_ENTRY_AVOID_INVERSE_SPLIT_DEFAULT_OFF",
        "registry_candidate_class": "FINAL_REGISTRY_CANDIDATE_ENTRY_AVOID_INVERSE_SPLIT",
        "module_slot": "branch_local_exact_control_entry_avoid_inverse_splitter",
        "target_delta_use": "TARGET_DELTA_NEGATIVE_DO_NOT_USE_AS_SCALAR",
        "module_execution_target_delta": -0.12,
        "module_execution_alignment_delta": 0.18,
        "same_mechanism_default_off_candidate_count": 0,
        "same_mechanism_shorter_default_off_candidate_count": 0,
        "underlying_mechanism_preserved_as": "entry_geometry_or_avoid_inverse_split_default_off",
    }
    code_spec = {
        "exact_control_redesign_final_registry_code_spec_row_id": "code-spec",
        "input_final_registry_row_id": "registry-row",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "exact_scope_guard": "symbol_session_horizon_primitive_match",
        "event_application_guard": "exact_scope_match_preserve_signal_control_context",
    }
    signal_event = {
        "exact_control_redesign_final_registry_event_application_row_id": "event-signal",
        "input_final_registry_row_id": "registry-row",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "tick_session_bucket": "off_core_session",
        "horizon_id": "h16",
        "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
        "event_final_registry_application_status": "FINAL_RED_REGISTRY_EVENT_ENTRY_AVOID_INVERSE_SIGNAL",
        "final_registry_event_join_state": "FINAL_RED_REGISTRY_EVENT_JOINED_EXACT_SCOPE",
        "module_scope_relation": "MODULE_SCOPE_SIGNAL_EVENT",
        "future_change_per_current_range": 0.30,
        "delta_aligned_with_future": True,
        "target_delta_use": "TARGET_DELTA_NEGATIVE_DO_NOT_USE_AS_SCALAR",
    }
    control_event = {
        **signal_event,
        "exact_control_redesign_final_registry_event_application_row_id": "event-control",
        "event_final_registry_application_status": "FINAL_RED_REGISTRY_EVENT_SAME_SCOPE_CONTROL_CONTEXT",
        "module_scope_relation": "MODULE_SCOPE_CONTROL_EVENT",
        "future_change_per_current_range": -0.10,
        "delta_aligned_with_future": False,
    }
    context_event = {
        **signal_event,
        "exact_control_redesign_final_registry_event_application_row_id": "event-context",
        "input_final_registry_row_id": None,
        "event_final_registry_application_status": "FINAL_RED_REGISTRY_EVENT_NON_SCOPE_CONTEXT",
        "final_registry_event_join_state": "FINAL_RED_REGISTRY_EVENT_NO_EXACT_SCOPE_CONTEXT",
        "module_scope_relation": "NON_MODULE_SCOPE_CONTEXT_EVENT",
        "target_delta_use": None,
    }

    metrics = module_observation_metrics([signal_event, control_event])
    module = scorer_module_registration(code_spec, registry, [signal_event, control_event], 1)
    module["exact_control_redesign_registry_scorer_module_row_id"] = "module-row"
    signal_application = scorer_module_event_application(signal_event, module)
    control_application = scorer_module_event_application(control_event, module)
    context_application = scorer_module_event_application(context_event, None)
    code_candidate = scorer_module_code_candidate(module, 1)

    assert metrics["signal_event_rows"] == 1
    assert metrics["same_scope_control_event_rows"] == 1
    assert metrics["alignment_rate_delta_signal_minus_control"] == 1.0
    assert metrics["future_change_mean_delta_signal_minus_control"] == 0.4
    assert module["module_registration_status"] == (
        "REGISTRY_SCORER_MODULE_ENTRY_AVOID_INVERSE_SPLIT_DEFAULT_OFF_EXACT_SCOPE"
    )
    assert module["target_delta_scalar_use_allowed"] is False
    assert module["module_runtime_score"] is None
    assert signal_application["module_event_application_status"] == (
        "REGISTRY_SCORER_MODULE_EVENT_SIGNAL_OBSERVATION"
    )
    assert control_application["module_event_application_status"] == (
        "REGISTRY_SCORER_MODULE_EVENT_SAME_SCOPE_CONTROL_CONTEXT"
    )
    assert context_application["module_event_application_status"] == (
        "REGISTRY_SCORER_MODULE_EVENT_NON_SCOPE_CONTEXT"
    )
    assert context_application["input_registry_scorer_module_row_id"] is None
    assert code_candidate["code_candidate_status"] == (
        "REGISTRY_SCORER_MODULE_CODE_CANDIDATE_DEFAULT_OFF_EXACT_SCOPE"
    )
    assert code_candidate["module_runtime_score_allowed"] is False


def test_branch_local_unified_system_recommendation_merge_preserves_repair_and_implement_actions():
    module_row = unified_system_candidate(
        "registry_scorer_module",
        {
            "exact_control_redesign_registry_scorer_module_row_id": "module-1",
            "mechanical_scope_key": "symbol=NAS100|session=ny|horizon=h4|primitive=DELTA",
            "system_recommendation_status": "SYSTEM_RECOMMEND_TIGHTER_TARGET_STRESS_DEFAULT_OFF_MODULE",
            "alignment_delta_mean": 0.12,
        },
        1,
    )
    source_row = unified_system_candidate(
        "market_gap_code",
        {
            "market_gap_code_id": "market-1",
            "mechanical_scope_key": "symbol=GBPJPY|session=london|horizon=h16|primitive=ABS",
            "code_candidate_status": "MARKET_GAP_CODE_SOURCE_MATERIALIZATION_REQUIRED",
            "proxy_score": 0.41,
        },
        2,
    )
    rejected_row = unified_system_candidate(
        "default_off_application",
        {
            "default_off_application_row_id": "app-1",
            "mechanical_scope_key": "symbol=USDJPY|session=off|horizon=h8|primitive=RANGE",
            "default_off_application_status": "DEFAULT_OFF_APPLICATION_SOURCE_PROXY_CURRENT_CLAIM_REJECTED_AUDIT_PRESERVED",
        },
        3,
    )
    rollup = unified_system_rollup_row(("component", "IMPLEMENT"), [module_row, source_row, rejected_row], 1, "test")

    assert module_row["unified_decision_group"] == "IMPLEMENT"
    assert module_row["unified_system_decision"] == "KEEP_AS_BRANCH_LOCAL_DEFAULT_OFF_MODULE"
    assert source_row["unified_decision_group"] == "SOURCE_OR_CONTROL_REPAIR"
    assert source_row["unified_action_class"] == "MARKET_GAP_SOURCE_MATERIALIZATION_REQUIRED"
    assert rejected_row["unified_action_class"] == "CURRENT_CLAIM_REJECTED_MECHANISM_PRESERVED"
    assert rejected_row["current_claim_only_rejection_scope"] == (
        "CURRENT_CLAIM_ONLY_UNDERLYING_MECHANISM_PRESERVED"
    )
    assert rollup["candidate_rows"] == 3
    assert rollup["implement_rows"] == 1
    assert rollup["source_or_control_repair_rows"] == 1
    assert rollup["preserve_audit_rows"] == 1
    assert rollup["runtime_score_allowed"] is False


def test_branch_local_unified_work_order_consumes_implementation_source_and_audit_rows():
    module_row = {
        "unified_system_candidate_row_id": "candidate-module",
        "source_component": "registry_scorer_module",
        "source_row_id": "module-1",
        "mechanical_scope_key": "symbol=NAS100|session=ny|horizon=h4|primitive=DELTA",
        "unified_action_class": "IMPLEMENT_DEFAULT_OFF_MODULE_CANDIDATE",
        "unified_decision_group": "IMPLEMENT",
        "unified_system_decision": "KEEP_AS_BRANCH_LOCAL_DEFAULT_OFF_MODULE",
    }
    source_row = {
        "unified_system_candidate_row_id": "candidate-source",
        "source_component": "nofill_near_miss_source_requirement",
        "source_row_id": "source-1",
        "mechanical_scope_key": "symbol=GBPJPY|session=ny|horizon=None|primitive=None",
        "unified_action_class": "NOFILL_NEAR_MISS_SOURCE_REQUIREMENT",
        "unified_decision_group": "SOURCE_OR_CONTROL_REPAIR",
        "source_confidence_status": "SATISFIED_EXACT_TICK_FIRST_SPREAD_AND_CLOSEST_TOUCH",
    }
    rejected_row = {
        "unified_system_candidate_row_id": "candidate-reject",
        "source_component": "default_off_application",
        "source_row_id": "app-1",
        "mechanical_scope_key": "symbol=USDJPY|session=off|horizon=h8|primitive=RANGE",
        "unified_action_class": "CURRENT_CLAIM_REJECTED_MECHANISM_PRESERVED",
        "unified_decision_group": "PRESERVE_AUDIT",
        "current_claim_only_rejection_scope": "CURRENT_CLAIM_ONLY_UNDERLYING_MECHANISM_PRESERVED",
    }

    module_work = work_order_from_unified_candidate(module_row, 1)
    source_work = work_order_from_unified_candidate(source_row, 2)
    audit_work = work_order_from_unified_candidate(rejected_row, 3)
    rollup = work_order_rollup(("test",), [module_work, source_work, audit_work], 1, "test")

    assert module_work["work_order_family"] == "IMPLEMENTATION"
    assert module_work["executable_next_action"] == "REGISTER_DEFAULT_OFF_SCORER_MODULE_SPEC"
    assert module_work["row_consumption_status"] == "UNIFIED_ROW_CONSUMED_IN_BRANCH_LOCAL_WORK_ORDER"
    assert source_work["work_order_family"] == "SOURCE_CONTROL_REPAIR"
    assert source_work["executable_next_action"] == "CONSUME_SATISFIED_NOFILL_SOURCE_IN_ENTRY_REPLAY"
    assert audit_work["work_order_family"] == "AUDIT_PRESERVATION"
    assert audit_work["missed_opportunity_audit_required"] is True
    assert audit_work["summary_only_terminal"] is False
    assert rollup["work_order_rows"] == 3
    assert rollup["work_order_family_counts"]["IMPLEMENTATION"] == 1
    assert rollup["work_order_family_counts"]["SOURCE_CONTROL_REPAIR"] == 1
    assert rollup["work_order_family_counts"]["AUDIT_PRESERVATION"] == 1


def test_branch_local_unified_work_order_routes_nofill_variants_and_guards():
    avoid = work_order_from_unified_candidate(
        {
            "unified_system_candidate_row_id": "candidate-avoid",
            "source_component": "nofill_far_miss_avoid",
            "source_row_id": "avoid-1",
            "mechanical_scope_key": "symbol=GBPJPY|session=tokyo|horizon=None|primitive=None",
            "unified_action_class": "NOFILL_FAR_MISS_AVOID_FILTER_CANDIDATE",
            "unified_decision_group": "REDESIGN",
        },
        1,
    )
    market_entry = work_order_from_unified_candidate(
        {
            "unified_system_candidate_row_id": "candidate-market",
            "source_component": "nofill_near_miss_market_entry",
            "source_row_id": "market-1",
            "mechanical_scope_key": "symbol=XAUUSD|session=ny|horizon=None|primitive=None",
            "unified_action_class": "NOFILL_NEAR_MISS_MARKET_ENTRY_VARIANT",
            "unified_decision_group": "REDESIGN",
        },
        2,
    )
    source_confidence = work_order_from_unified_candidate(
        {
            "unified_system_candidate_row_id": "candidate-guard",
            "source_component": "nofill_far_miss_source_confidence",
            "source_row_id": "guard-1",
            "mechanical_scope_key": "symbol=GBPJPY|session=tokyo|horizon=None|primitive=None",
            "unified_action_class": "NOFILL_SOURCE_CONFIDENCE_CONTEXT_CANDIDATE",
            "unified_decision_group": "GUARD",
        },
        3,
    )

    assert avoid["executable_next_action"] == "EXECUTE_NOFILL_AVOID_OR_INVERSE_VARIANT"
    assert avoid["target_artifact_kind"] == "redesign_nofill_avoid_inverse"
    assert market_entry["executable_next_action"] == "EXECUTE_NEAR_MISS_MARKET_ENTRY_PROXY_VARIANT"
    assert market_entry["target_artifact_kind"] == "redesign_near_miss_market_entry"
    assert source_confidence["work_order_family"] == "GUARD"
    assert source_confidence["executable_next_action"] == "REGISTER_NOFILL_SOURCE_CONFIDENCE_GUARD"
    assert source_confidence["runtime_score_allowed"] is False


def test_branch_local_unified_action_results_materialize_all_work_order_families():
    implementation = work_order_from_unified_candidate(
        {
            "unified_system_candidate_row_id": "candidate-impl",
            "source_component": "registry_scorer_module",
            "source_row_id": "module-1",
            "symbol": "NAS100",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "primitive_flag": "DELTA",
            "mechanical_scope_key": "symbol=NAS100|session=ny|horizon=h16|primitive=DELTA",
            "unified_action_class": "IMPLEMENT_DEFAULT_OFF_MODULE_CANDIDATE",
            "unified_decision_group": "IMPLEMENT",
            "proxy_or_module_score": 0.66,
        },
        1,
    )
    source_repair = work_order_from_unified_candidate(
        {
            "unified_system_candidate_row_id": "candidate-source",
            "source_component": "default_off_application",
            "source_row_id": "app-1",
            "mechanical_scope_key": "symbol=NAS100|session=ny|horizon=h16|primitive=DELTA",
            "unified_action_class": "BUILD_EXACT_CONTROL_DENOMINATOR",
            "unified_decision_group": "SOURCE_OR_CONTROL_REPAIR",
        },
        2,
    )
    redesign = work_order_from_unified_candidate(
        {
            "unified_system_candidate_row_id": "candidate-redesign",
            "source_component": "nofill_far_miss_retest",
            "source_row_id": "retest-1",
            "mechanical_scope_key": "symbol=XAUUSD|session=ny|horizon=None|primitive=None",
            "unified_action_class": "NOFILL_FAR_MISS_RETEST_REDESIGN_CANDIDATE",
            "unified_decision_group": "REDESIGN",
        },
        3,
    )
    audit = work_order_from_unified_candidate(
        {
            "unified_system_candidate_row_id": "candidate-audit",
            "source_component": "default_off_application",
            "source_row_id": "app-2",
            "mechanical_scope_key": "symbol=GBPJPY|session=london|horizon=h32|primitive=DELTA",
            "unified_action_class": "CURRENT_CLAIM_REJECTED_MECHANISM_PRESERVED",
            "unified_decision_group": "PRESERVE_AUDIT",
            "current_claim_only_rejection_scope": "CURRENT_CLAIM_ONLY_UNDERLYING_MECHANISM_PRESERVED",
        },
        4,
    )
    market_context = {
        "market_timeframe_session_horizon_expansion_row_id": "market-1",
        "decision": "shadow-candidate",
        "tradability_status": "configured-observer-or-live-shadow",
        "available_timeframes": ["M15", "H1"],
        "exact_R_availability": "broker_exact_R_not_available",
        "proxy_R_availability": "proxy_score_available",
        "fillability_no_fill_status": "not_fillability_specific",
    }

    implementation_result = action_result_from_work_order(implementation, 1, market_context)
    source_result = action_result_from_work_order(source_repair, 2, market_context)
    redesign_result = action_result_from_work_order(redesign, 3, market_context)
    audit_result = action_result_from_work_order(audit, 4, market_context)
    rollup = action_result_rollup(
        ("test",),
        [implementation_result, source_result, redesign_result, audit_result],
        1,
        "test",
    )

    assert implementation_result["action_result_family"] == "IMPLEMENTATION_RESULT"
    assert implementation_result["proxy_r_style_result"] == "PROXY_R_STYLE_STRONG_POSITIVE"
    assert implementation_result["action_execution_status"] == "BRANCH_LOCAL_DEFAULT_OFF_SPEC_MATERIALIZED"
    assert source_result["action_execution_status"] == "EXACT_CONTROL_DENOMINATOR_BUILD_ACTION_MATERIALIZED"
    assert source_result["proxy_r_style_result"] == "PROXY_R_NOT_COMPUTED_SOURCE_OR_CONTROL_ACTION_FIRST"
    assert redesign_result["action_result_family"] == "REDESIGN_EXECUTION_RESULT"
    assert redesign_result["proxy_r_style_result"] == "PROXY_R_NOT_COMPUTED_REDESIGN_REPLAY_REQUIRED"
    assert audit_result["action_result_family"] == "AUDIT_PRESERVATION_RESULT"
    assert audit_result["missed_opportunity_preserved"] is True
    assert audit_result["summary_only_terminal"] is False
    assert implementation_result["market_expansion_row_id"] == "market-1"
    assert rollup["action_result_rows"] == 4
    assert rollup["action_result_family_counts"]["IMPLEMENTATION_RESULT"] == 1
    assert rollup["action_result_family_counts"]["SOURCE_CONTROL_REPAIR_RESULT"] == 1


def test_branch_local_unified_computed_actions_score_sidecars_and_nofill_variants():
    action = {
        "unified_system_action_result_row_id": "action-score",
        "input_unified_system_work_order_row_id": "work-1",
        "source_component": "default_off_scorer_application",
        "source_row_id": "score-1",
        "symbol": "NAS100",
        "route_session": "ny_core",
        "horizon_id": "h16",
        "primitive_flag": "DELTA",
        "mechanical_scope_key": "symbol=NAS100|session=ny|horizon=h16|primitive=DELTA",
        "action_result_family": "SCORE_WITH_CONTROL_RESULT",
        "action_execution_status": "CONTROL_SCORE_RESULT_ROW_MATERIALIZED",
        "target_artifact_kind": "score_with_control_default_off",
        "market_expansion_decision": "proxy/control feature",
        "tradability_status": "configured-observer-or-live-shadow",
        "available_timeframes": ["M1", "M15", "H1"],
        "exact_R_availability": "broker_exact_R_not_available",
        "proxy_R_availability": "proxy_score_available",
        "fillability_no_fill_status": "not_fillability_specific",
        "missed_opportunity_preserved": True,
    }
    sidecar = {
        "scorer_application_row_id": "score-1",
        "default_off_scorer_event_score": 0.08,
    }
    nofill_action = {
        **action,
        "unified_system_action_result_row_id": "action-market",
        "source_component": "nofill_near_miss_market_entry",
        "source_row_id": "market-1",
        "action_result_family": "REDESIGN_EXECUTION_RESULT",
        "action_execution_status": "REDESIGN_VARIANT_ACTION_RESULT_MATERIALIZED",
        "target_artifact_kind": "redesign_near_miss_market_entry",
        "fillability_no_fill_status": "fillability_or_no_fill_rows_present",
    }
    nofill_sidecar = {
        "near_miss_entry_control_market_branch_id": "market-1",
        "market_first_touch_status": "STOP_TOUCH_FIRST_OR_ONLY_M15_PROXY",
    }

    score_result = computed_action_result(action, 1, sidecar)
    nofill_result = computed_action_result(nofill_action, 2, nofill_sidecar)
    rollup = computed_action_rollup(("test",), [score_result, nofill_result], 1, "test")

    assert score_result["computed_action_family"] == "SCORE_WITH_CONTROL"
    assert score_result["computed_action_status"] == "CONTROL_SCORE_DELTA_COMPUTED_FROM_SOURCE_SIDECAR"
    assert score_result["computed_proxy_delta"] == 0.08
    assert score_result["computed_proxy_delta_class"] == "COMPUTED_PROXY_DELTA_POSITIVE"
    assert nofill_result["computed_action_family"] == "NOFILL_REDESIGN_SCORING"
    assert nofill_result["computed_action_status"] == "NEAR_MISS_MARKET_ENTRY_TARGET_STOP_PROXY_SCORED"
    assert nofill_result["computed_proxy_score_basis"] == "STOP_FIRST_PROXY"
    assert nofill_result["computed_proxy_delta_class"] == "COMPUTED_PROXY_DELTA_STRONG_NEGATIVE"
    assert nofill_result["summary_only_terminal"] is False
    assert rollup["computed_action_rows"] == 2
    assert rollup["source_sidecar_joined_rows"] == 2


def test_branch_local_unified_computed_market_expansion_preserves_required_fields():
    base = {
        "market_timeframe_session_horizon_expansion_row_id": "market-1",
        "coverage_source": "data_inventory_available_not_yet_consumed_by_current_work_orders",
        "symbol": "SPX_ES",
        "broker_proxy_mapping": "ES futures proxy",
        "tradability_status": "historical-source-available-non-prod",
        "data_source": ["Sierra"],
        "source_files": ["data/sierra/ES.scid"],
        "available_timeframes": ["M1", "M5", "M15", "H1"],
        "session_kz_offkz_coverage": ["off_kz", "ny_kz"],
        "route_session": "ALL_SESSIONS",
        "horizon_id": "ALL_HORIZONS",
        "primitive_flag": "ALL_PRIMITIVES",
        "source_component": "data_inventory",
        "spread_cost_source": "Sierra tick proxy",
        "replay_result_row_counts": {"work_order_rows": 0, "data_timeframe_file_count": 4},
        "exact_R_availability": "broker_exact_R_not_available",
        "proxy_R_availability": "historical_proxy_available",
        "fillability_no_fill_status": "not_fillability_specific",
        "missing_evidence": ["broker_realized_R_not_present"],
        "decision": "merge-as-system-input",
    }
    computed = {
        "computed_action_family": "SCORE_WITH_CONTROL",
        "computed_action_status": "CONTROL_SCORE_DELTA_COMPUTED_FROM_SOURCE_SIDECAR",
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_POSITIVE",
        "computed_proxy_delta": 0.12,
        "source_component": "market_gap_code",
        "source_sidecar_joined": True,
    }

    row = computed_market_timeframe_expansion_row(base, [computed], 1)
    empty_row = computed_market_timeframe_expansion_row({**base, "market_timeframe_session_horizon_expansion_row_id": "market-2"}, [], 2)

    for required in (
        "symbol",
        "broker_proxy_mapping",
        "tradability_status",
        "data_source",
        "available_timeframes",
        "session_kz_offkz_coverage",
        "spread_cost_source",
        "replay_result_row_counts",
        "exact_R_availability",
        "proxy_R_availability",
        "fillability_no_fill_status",
        "missing_evidence",
        "decision",
    ):
        assert required in row
    assert row["computed_action_rows"] == 1
    assert row["computed_delta_rows"] == 1
    assert row["computed_action_family_counts"]["SCORE_WITH_CONTROL"] == 1
    assert row["current_output_path_coverage"] == "CURRENT_COMPUTED_ACTION_ROWS_CONSUMED_FOR_MARKET_SCOPE"
    assert empty_row["computed_action_rows"] == 0
    assert empty_row["current_output_path_coverage"] == "MARKET_SCOPE_PRESERVED_WITHOUT_CURRENT_COMPUTED_ACTION_ROWS"
    assert "no_current_computed_action_row_for_inventory_or_unconsumed_scope" in empty_row["missing_evidence"]
    assert row["summary_only_terminal"] is False


def test_branch_local_unified_implementation_execution_materializes_concrete_actions():
    default_off = {
        "unified_system_computed_action_row_id": "computed-1",
        "input_unified_system_action_result_row_id": "action-1",
        "computed_action_family": "DEFAULT_OFF_CODE_CANDIDATE",
        "computed_action_status": "DEFAULT_OFF_CODE_CANDIDATE_PROXY_DELTA_COMPUTED",
        "source_component": "market_gap_code",
        "source_row_id": "market-code-1",
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
        "computed_proxy_delta": 0.18,
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
        "market_expansion_decision": "shadow-candidate",
        "tradability_status": "historical-source-available-non-prod",
        "available_timeframes": ["M1", "M15"],
    }
    source = {
        **default_off,
        "unified_system_computed_action_row_id": "computed-2",
        "computed_action_family": "SOURCE_CONTROL_REPAIR",
        "computed_action_status": "EXACT_CONTROL_DENOMINATOR_BUILD_RESULT_ROW",
        "computed_proxy_delta": None,
        "source_rows_needed_to_n20_proxy": 12,
        "source_repair_required": True,
    }
    nofill = {
        **default_off,
        "unified_system_computed_action_row_id": "computed-3",
        "computed_action_family": "NOFILL_REDESIGN_SCORING",
        "computed_action_status": "NEAR_MISS_MARKET_ENTRY_TARGET_STOP_PROXY_SCORED",
        "source_component": "nofill_near_miss_market_entry",
        "computed_proxy_delta": -0.65,
        "computed_proxy_score_basis": "STOP_FIRST_PROXY",
        "pass_control_delta_proxy": -0.65,
        "expectancy_style_proxy_delta": -0.65,
    }
    market = {
        "market_timeframe_session_horizon_expansion_row_id": "market-1",
        "symbol": "SPX_ES",
        "broker_proxy_mapping": "ES futures proxy",
        "tradability_status": "historical-source-available-non-prod",
        "data_source": ["Sierra"],
        "available_timeframes": ["M1", "M5", "M15"],
        "session_kz_offkz_coverage": ["ny_kz", "off_kz"],
        "spread_cost_source": "Sierra tick proxy",
        "decision": "source-repair",
        "coverage_source": "data_inventory_available_not_yet_consumed_by_current_work_orders",
        "computed_action_rows": 0,
        "computed_delta_rows": 0,
        "missing_evidence": ["exact_source_required"],
    }

    decision = implementation_execution_decision(default_off, 1)
    module = default_off_module_spec(default_off, 1)
    source_builder = source_builder_spec(source, 1)
    comparator = nofill_variant_comparator(nofill, 1)
    transfer = market_transfer_decision(market, 1)

    assert decision["execution_action_class"] == "IMPLEMENT_DEFAULT_OFF_MODULE_SPEC_WITH_GUARD"
    assert decision["execution_priority_tier"] == "STRONG_POSITIVE_DELTA"
    assert module["module_family"] == "market_gap_entry_or_avoid_module"
    assert module["module_spec_status"] == "DEFAULT_OFF_MODULE_SPEC_READY_WITH_POSITIVE_PROXY"
    assert source_builder["source_builder_action_class"] == "BUILD_EXACT_CONTROL_DENOMINATOR"
    assert source_builder["source_builder_status"] == "SOURCE_BUILDER_EXACT_CONTROL"
    assert comparator["variant_action_class"] == "ROUTE_NOFILL_VARIANT_TO_AVOID_OR_INVERSE"
    assert comparator["opportunity_preserved_as"] == "avoid_inverse_retest_source_or_entry_redesign_intelligence"
    assert transfer["market_transfer_status"] == "MARKET_SCOPE_SOURCE_REPAIR_OR_PROXY_REQUIRED_NO_CURRENT_COMPUTED_ACTION_ROWS"
    assert transfer["runtime_score_allowed"] is False


def test_branch_local_unified_executable_artifacts_consume_implementation_rows():
    execution = {
        "implementation_execution_decision_row_id": "exec-1",
        "input_unified_system_computed_action_row_id": "computed-1",
        "computed_action_family": "DEFAULT_OFF_CODE_CANDIDATE",
        "execution_action_class": "IMPLEMENT_DEFAULT_OFF_MODULE_SPEC_WITH_GUARD",
        "execution_decision_class": "IMPLEMENTATION_SPEC_READY_DEFAULT_OFF",
        "execution_priority_tier": "STRONG_POSITIVE_DELTA",
        "source_component": "market_gap_code",
        "source_row_id": "market-code-1",
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
        "computed_proxy_delta": 0.18,
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
        "computed_proxy_score_basis": "proxy_score",
        "market_expansion_decision": "shadow-candidate",
        "tradability_status": "historical-source-available-non-prod",
        "available_timeframes": ["M1", "M15"],
    }
    module = {
        **execution,
        "default_off_module_spec_row_id": "module-1",
        "module_family": "market_gap_entry_or_avoid_module",
        "module_spec_status": "DEFAULT_OFF_MODULE_SPEC_READY_WITH_POSITIVE_PROXY",
        "candidate_function_name": "score_market_gap_entry_or_avoid_module_00001",
        "guard_requirements": ["source_confidence_guard", "same_scope_control_lookup"],
        "required_runtime_fields": ["symbol", "route_session", "horizon_id", "primitive_flag"],
    }
    source = {
        **execution,
        "source_builder_spec_row_id": "source-1",
        "source_builder_action_class": "BUILD_EXACT_CONTROL_DENOMINATOR",
        "source_builder_status": "SOURCE_BUILDER_EXACT_CONTROL",
        "source_rows_needed_to_n20_proxy": 0,
        "builder_output_contract": "exact_control_or_source_proxy_result_then_rescore_same_scope",
    }
    nofill = {
        **execution,
        "nofill_variant_comparator_row_id": "nofill-1",
        "variant_comparator_status": "NOFILL_VARIANT_NEGATIVE_PROXY",
        "variant_action_class": "ROUTE_NOFILL_VARIANT_TO_AVOID_OR_INVERSE",
        "variant_next_action": "preserve_negative_variant_as_avoid_inverse_or_entry_failure_intelligence",
        "target_stop_proxy_basis": "STOP_FIRST_PROXY",
        "pass_control_delta_proxy": -0.65,
        "expectancy_style_proxy_delta": -0.65,
        "opportunity_preserved_as": "avoid_inverse_retest_source_or_entry_redesign_intelligence",
        "computed_proxy_delta": -0.65,
    }
    market = {
        "market_transfer_decision_row_id": "market-transfer-1",
        "input_market_timeframe_session_horizon_expansion_row_id": "market-1",
        "market_transfer_status": "MARKET_SCOPE_SOURCE_REPAIR_OR_PROXY_REQUIRED_NO_CURRENT_COMPUTED_ACTION_ROWS",
        "market_transfer_action": "execute_source_repair_or_proxy_for_market_scope",
        "symbol": "SPX_ES",
        "broker_proxy_mapping": "ES futures proxy",
        "tradability_status": "historical-source-available-non-prod",
        "data_source": ["Sierra"],
        "available_timeframes": ["M1", "M5", "M15"],
        "session_kz_offkz_coverage": ["ny_kz", "off_kz"],
        "spread_cost_source": "Sierra tick proxy",
        "decision": "source-repair",
        "computed_action_rows": 0,
        "missing_evidence": ["exact_source_required"],
    }

    artifact = executable_artifact_decision(execution, 1)
    code = code_surface_artifact(module, 1)
    source_exec = source_control_builder_execution(source, 1)
    nofill_outcome = nofill_comparator_outcome(nofill, 1)
    market_action = market_source_action(market, 1)

    assert artifact["executable_artifact_family"] == "CODE_SURFACE_ARTIFACT"
    assert artifact["executable_artifact_status"] == "EXECUTABLE_CODE_SURFACE_READY_DEFAULT_OFF"
    assert code["code_surface_status"] == "CODE_SURFACE_STRONG_POSITIVE_DEFAULT_OFF_READY"
    assert code["proposed_module_path"].endswith("moonshot_branch_local_unified_system_executable_artifacts.py")
    assert source_exec["source_control_builder_execution_status"] == "EXACT_CONTROL_DENOMINATOR_BUILDER_EXECUTABLE_FROM_CURRENT_SCOPE"
    assert source_exec["same_resource_execution_available"] is True
    assert nofill_outcome["nofill_comparator_outcome_status"] == "NOFILL_NEGATIVE_VARIANT_FORCE_AVOID_INVERSE_OR_ENTRY_FAILURE_ROLE"
    assert nofill_outcome["nofill_system_role"] == "avoid_inverse_filter_or_failure_feature"
    assert market_action["market_source_action_status"] == "MARKET_SOURCE_REPAIR_OR_PROXY_ACTION_MATERIALIZED"
    assert market_action["summary_only_terminal"] is False


def test_branch_local_unified_runtime_surfaces_execute_scope_behavior():
    executable = {
        "executable_artifact_decision_row_id": "artifact-1",
        "input_implementation_execution_decision_row_id": "exec-1",
        "input_unified_system_computed_action_row_id": "computed-1",
        "executable_artifact_family": "CODE_SURFACE_ARTIFACT",
        "executable_artifact_status": "EXECUTABLE_CODE_SURFACE_READY_DEFAULT_OFF",
        "source_component": "market_gap_code",
        "source_row_id": "market-code-1",
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
        "computed_proxy_delta": 0.18,
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
        "computed_proxy_score_basis": "proxy_score",
        "tradability_status": "historical-source-available-non-prod",
        "available_timeframes": ["M1", "M15"],
    }
    code = {
        **executable,
        "code_surface_artifact_row_id": "code-1",
        "input_unified_system_computed_action_row_id": "computed-1",
        "code_surface_status": "CODE_SURFACE_STRONG_POSITIVE_DEFAULT_OFF_READY",
        "candidate_function_name": "score_market_gap_entry_or_avoid_module_00001",
        "branch_local_registry_key": "registry-key",
        "event_match_contract": "match scope",
        "score_contract": "default-off observation",
        "guard_requirements": ["source_confidence_guard"],
    }
    source = {
        **executable,
        "source_control_builder_execution_row_id": "source-1",
        "source_control_builder_execution_status": "EXACT_CONTROL_DENOMINATOR_BUILDER_EXECUTABLE_FROM_CURRENT_SCOPE",
        "same_resource_execution_available": True,
        "missing_source_proof": [],
        "source_rows_needed_to_n20_proxy": 0,
    }
    nofill = {
        **executable,
        "nofill_comparator_outcome_row_id": "nofill-1",
        "nofill_comparator_outcome_status": "NOFILL_NEGATIVE_VARIANT_FORCE_AVOID_INVERSE_OR_ENTRY_FAILURE_ROLE",
        "nofill_system_role": "avoid_inverse_filter_or_failure_feature",
        "target_stop_proxy_basis": "STOP_FIRST_PROXY",
        "computed_proxy_delta": -0.65,
    }

    surface = runtime_surface_decision(executable, 1)
    event = {
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
    }
    scored = score_runtime_surface_event(surface, event)
    self_test = runtime_surface_self_test(surface, 1)
    registry = scorer_registry_surface(code, 1)
    source_runtime = source_replay_surface(source, 1)
    nofill_runtime = nofill_replay_surface(nofill, 1)

    assert surface["runtime_surface_family"] == "SCORER_REGISTRY_RUNTIME_SURFACE"
    assert surface["runtime_surface_status"] == "RUNTIME_SURFACE_IMPLEMENTATION_READY_DEFAULT_OFF"
    assert event_matches_runtime_surface(surface, event) is True
    assert scored["emitted_observation_class"] == "EMIT_DEFAULT_OFF_POSITIVE_SCORER_OBSERVATION"
    assert scored["default_off_observation_score"] == 0.18
    assert self_test["positive_scope_match_result"] is True
    assert self_test["negative_scope_mismatch_result"] is False
    assert registry["scorer_registry_status"] == "SCORER_RUNTIME_REGISTERED_DEFAULT_OFF"
    assert source_runtime["source_replay_status"] == "SOURCE_REPLAY_EXACT_CONTROL_BUILD_CALLABLE_READY"
    assert nofill_runtime["nofill_replay_status"] == "NOFILL_REPLAY_AVOID_INVERSE_SCORER_READY"
    assert nofill_runtime["runtime_score_allowed"] is False


def test_branch_local_unified_candidate_synthesis_maps_runtime_emissions_to_components():
    runtime = {
        "runtime_surface_decision_row_id": "runtime-1",
        "input_executable_artifact_decision_row_id": "artifact-1",
        "input_unified_system_computed_action_row_id": "computed-1",
        "runtime_surface_family": "SCORER_REGISTRY_RUNTIME_SURFACE",
        "runtime_surface_status": "RUNTIME_SURFACE_IMPLEMENTATION_READY_DEFAULT_OFF",
        "runtime_surface_key": "runtime-key",
        "source_component": "market_gap_code",
        "source_row_id": "market-code-1",
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
        "computed_proxy_delta": 0.18,
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
        "computed_proxy_score_basis": "proxy_score",
    }
    self_test = {
        "runtime_surface_self_test_row_id": "selftest-1",
        "input_runtime_surface_decision_row_id": "runtime-1",
        "emitted_observation_class": "EMIT_DEFAULT_OFF_POSITIVE_SCORER_OBSERVATION",
        "positive_scope_match_result": True,
        "negative_scope_mismatch_result": False,
        "default_off_observation_score": 0.18,
    }
    scorer = {
        **runtime,
        "scorer_registry_surface_row_id": "scorer-1",
        "scorer_registry_status": "SCORER_RUNTIME_REGISTERED_DEFAULT_OFF",
        "registered_callable_name": "score_market_gap_entry_or_avoid_module_00001",
        "branch_local_registry_key": "registry-key",
        "guard_requirements": ["source_confidence_guard"],
    }
    source = {
        **runtime,
        "source_replay_surface_row_id": "source-1",
        "source_replay_status": "SOURCE_REPLAY_EXACT_CONTROL_BUILD_CALLABLE_READY",
        "same_resource_execution_available": True,
        "missing_source_proof": [],
    }
    nofill = {
        **runtime,
        "nofill_replay_surface_row_id": "nofill-1",
        "nofill_replay_status": "NOFILL_REPLAY_AVOID_INVERSE_SCORER_READY",
        "nofill_system_role": "avoid_inverse_filter_or_failure_feature",
        "target_stop_proxy_basis": "STOP_FIRST_PROXY",
        "computed_proxy_delta": -0.65,
    }

    role, status = candidate_role_from_emission("EMIT_DEFAULT_OFF_POSITIVE_SCORER_OBSERVATION")
    candidate = candidate_execution_row(runtime, self_test, 1)
    scorer_component = scorer_component_row(scorer, 1)
    source_component = source_component_row(source, 1)
    nofill_component = nofill_component_row(nofill, 1)

    assert role == "DEFAULT_OFF_POSITIVE_SCORER_COMPONENT"
    assert status == "CANDIDATE_SCORER_OBSERVATION_READY"
    assert candidate["candidate_system_role"] == "DEFAULT_OFF_POSITIVE_SCORER_COMPONENT"
    assert candidate["candidate_execution_status"] == "CANDIDATE_SCORER_OBSERVATION_READY"
    assert candidate["positive_scope_match_result"] is True
    assert candidate["negative_scope_mismatch_result"] is True
    assert scorer_component["candidate_component_role"] == "default_off_scorer_registry"
    assert source_component["candidate_component_status"] == "SOURCE_REPLAY_EXACT_CONTROL_BUILD_CALLABLE_READY"
    assert nofill_component["candidate_component_role"] == "avoid_inverse_filter_or_failure_feature"
    assert nofill_component["runtime_score_allowed"] is False


def test_branch_local_unified_candidate_runtime_executes_scope_checked_observations():
    candidate = {
        "candidate_execution_row_id": "candidate-1",
        "input_runtime_surface_decision_row_id": "runtime-1",
        "input_executable_artifact_decision_row_id": "artifact-1",
        "input_unified_system_computed_action_row_id": "computed-1",
        "candidate_system_role": "NOFILL_POSITIVE_CHALLENGER_COMPONENT",
        "candidate_execution_status": "CANDIDATE_NOFILL_CHALLENGER_READY",
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
        "source_component": "nofill_component",
        "source_row_id": "nofill-1",
        "computed_proxy_delta": 0.22,
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
        "default_off_observation_score": 0.22,
    }
    source_component = {
        **candidate,
        "source_component_row_id": "source-component-1",
        "candidate_component_status": "SOURCE_REPLAY_EXACT_CONTROL_BUILD_CALLABLE_READY",
        "candidate_component_role": "source_or_control_replay_builder",
        "component_execution_contract": "build exact control/source replay/proxy observation for same mechanical scope",
    }
    market_component = {
        "market_component_row_id": "market-component-1",
        "candidate_component_status": "MARKET_SOURCE_RUNTIME_PROXY_CONTROL_READY",
        "candidate_component_role": "market_proxy_control_feature",
        "symbol": "NAS100_NQ",
        "broker_proxy_mapping": "NAS100_NQ",
        "tradability_status": "futures_proxy_context",
        "data_source": ["historical_ohlc"],
        "available_timeframes": ["M1", "M15", "H1"],
        "session_kz_offkz_coverage": ["ny_core", "off_kz"],
    }

    family, status, callable_base, emission = candidate_runtime_family("NOFILL_POSITIVE_CHALLENGER_COMPONENT")
    runtime = candidate_runtime_decision(candidate, 1)
    match_event = {
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
    }
    mismatch_event = {**match_event, "mechanical_scope_key": "different"}
    matched = execute_candidate_runtime(runtime, match_event)
    mismatched = execute_candidate_runtime(runtime, mismatch_event)
    self_test = candidate_runtime_self_test(runtime, 1)
    source_binding = component_runtime_binding(source_component, 1, "SOURCE")
    market_binding = market_runtime_binding(market_component, 1)

    assert family == "NOFILL_CHALLENGER_RUNTIME_COMPONENT"
    assert status == "CANDIDATE_RUNTIME_NOFILL_CHALLENGER_READY_DEFAULT_OFF"
    assert callable_base == "score_nofill_challenger_candidate_observation"
    assert emission == "EMIT_CANDIDATE_NOFILL_CHALLENGER_OBSERVATION"
    assert runtime["candidate_runtime_component_family"] == "NOFILL_CHALLENGER_RUNTIME_COMPONENT"
    assert runtime["candidate_runtime_status"] == "CANDIDATE_RUNTIME_NOFILL_CHALLENGER_READY_DEFAULT_OFF"
    assert event_matches_candidate_runtime(runtime, match_event) is True
    assert matched["candidate_runtime_emission_class"] == "EMIT_CANDIDATE_NOFILL_CHALLENGER_OBSERVATION"
    assert matched["default_off_observation_score"] == 0.22
    assert mismatched["candidate_runtime_emission_class"] == "NO_EMIT_SCOPE_MISMATCH"
    assert self_test["positive_scope_match_result"] is True
    assert self_test["negative_scope_mismatch_result"] is False
    assert source_binding["component_runtime_binding_status"] == "COMPONENT_RUNTIME_BINDING_READY"
    assert market_binding["market_runtime_binding_status"] == "MARKET_RUNTIME_PROXY_CONTROL_BINDING_READY"
    assert runtime["runtime_score_allowed"] is False


def test_branch_local_unified_candidate_dispatch_materializes_runtime_bindings():
    runtime = {
        "candidate_runtime_decision_row_id": "runtime-1",
        "input_candidate_execution_row_id": "candidate-1",
        "input_runtime_surface_decision_row_id": "surface-1",
        "input_executable_artifact_decision_row_id": "artifact-1",
        "input_unified_system_computed_action_row_id": "computed-1",
        "candidate_runtime_component_family": "AVOID_INVERSE_RUNTIME_COMPONENT",
        "candidate_runtime_status": "CANDIDATE_RUNTIME_AVOID_INVERSE_FILTER_READY_DEFAULT_OFF",
        "candidate_runtime_key": "runtime-key",
        "candidate_runtime_emission_class": "EMIT_CANDIDATE_AVOID_INVERSE_FILTER_OBSERVATION",
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
        "source_component": "nofill_component",
        "source_row_id": "nofill-1",
        "computed_proxy_delta": -0.31,
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_NEGATIVE",
        "default_off_observation_score": 0.31,
    }
    component = {
        **runtime,
        "component_runtime_binding_row_id": "component-runtime-1",
        "input_component_row_id": "nofill-component-1",
        "candidate_component_status": "NOFILL_REPLAY_AVOID_INVERSE_SCORER_READY",
        "candidate_component_role": "avoid_inverse_filter_or_failure_feature",
        "component_runtime_binding_status": "COMPONENT_RUNTIME_BINDING_READY",
        "component_execution_contract": "score no-fill variant against status-quo control",
    }
    market = {
        "market_runtime_binding_row_id": "market-runtime-1",
        "input_market_component_row_id": "market-component-1",
        "candidate_component_status": "MARKET_SOURCE_RUNTIME_SHADOW_DEFAULT_OFF_READY",
        "candidate_component_role": "shadow_candidate_default_off",
        "market_runtime_binding_status": "MARKET_RUNTIME_SHADOW_DEFAULT_OFF_BINDING_READY",
        "symbol": "NAS100_NQ",
        "broker_proxy_mapping": "NAS100_NQ",
        "tradability_status": "futures_proxy_context",
        "data_source": ["historical_ohlc"],
        "available_timeframes": ["M1", "M15", "H1"],
        "session_kz_offkz_coverage": ["ny_core", "off_kz"],
    }

    family, status, callable_base, dispatch_class = candidate_dispatch_family("AVOID_INVERSE_RUNTIME_COMPONENT")
    dispatch = candidate_dispatch_decision(runtime, 1)
    event = {
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
    }
    matched = execute_candidate_dispatch(dispatch, event)
    mismatched = execute_candidate_dispatch(dispatch, {**event, "mechanical_scope_key": "different"})
    self_test = candidate_dispatch_self_test(dispatch, 1)
    nofill_plan = component_dispatch_plan(component, 1, "NOFILL")
    market_plan = market_transfer_dispatch(market, 1)

    assert family == "AVOID_INVERSE_FILTER_MODULE_DISPATCH"
    assert status == "CANDIDATE_DISPATCH_AVOID_INVERSE_READY_DEFAULT_OFF"
    assert callable_base == "materialize_avoid_inverse_filter_module"
    assert dispatch_class == "DISPATCH_AVOID_INVERSE_FILTER_MODULE"
    assert dispatch["candidate_dispatch_family"] == "AVOID_INVERSE_FILTER_MODULE_DISPATCH"
    assert dispatch["candidate_dispatch_status"] == "CANDIDATE_DISPATCH_AVOID_INVERSE_READY_DEFAULT_OFF"
    assert event_matches_candidate_dispatch(dispatch, event) is True
    assert matched["candidate_dispatch_execution_action"] == "MATERIALIZE_AVOID_INVERSE_FILTER_MODULE"
    assert matched["default_off_observation_score"] == 0.31
    assert mismatched["candidate_dispatch_execution_class"] == "NO_DISPATCH_SCOPE_MISMATCH"
    assert self_test["positive_scope_match_result"] is True
    assert self_test["negative_scope_mismatch_result"] is False
    assert nofill_plan["component_dispatch_plan_status"] == "COMPONENT_DISPATCH_PLAN_READY"
    assert nofill_plan["component_dispatch_action"] == "instantiate_nofill_variant_comparator_or_avoid_filter"
    assert market_plan["market_transfer_dispatch_status"] == "MARKET_DISPATCH_SHADOW_DEFAULT_OFF_CANDIDATE_READY"
    assert dispatch["runtime_score_allowed"] is False


def test_branch_local_unified_candidate_materialization_consumes_dispatch_plans():
    dispatch = {
        "candidate_dispatch_decision_row_id": "dispatch-1",
        "input_candidate_runtime_decision_row_id": "runtime-1",
        "input_candidate_execution_row_id": "candidate-1",
        "input_unified_system_computed_action_row_id": "computed-1",
        "candidate_dispatch_family": "NOFILL_CHALLENGER_MODULE_DISPATCH",
        "candidate_dispatch_status": "CANDIDATE_DISPATCH_NOFILL_CHALLENGER_READY_DEFAULT_OFF",
        "candidate_dispatch_action_class": "DISPATCH_NOFILL_CHALLENGER_MODULE",
        "candidate_dispatch_key": "dispatch-key",
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
        "source_component": "nofill_component",
        "source_row_id": "nofill-1",
        "computed_proxy_delta": 0.22,
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
    }
    component_plan = {
        **dispatch,
        "component_dispatch_plan_row_id": "component-dispatch-1",
        "input_component_runtime_binding_row_id": "component-runtime-1",
        "component_type": "NOFILL",
        "candidate_component_status": "NOFILL_REPLAY_POSITIVE_CHALLENGER_SCORER_READY",
        "candidate_component_role": "positive_challenger_or_market_entry_variant",
        "component_runtime_binding_status": "COMPONENT_RUNTIME_BINDING_READY",
        "component_dispatch_plan_status": "COMPONENT_DISPATCH_PLAN_READY",
        "component_dispatch_action": "instantiate_nofill_variant_comparator_or_avoid_filter",
    }
    scorer_plan = {
        **component_plan,
        "component_type": "SCORER",
        "candidate_component_role": "default_off_scorer_registry",
    }
    source_plan = {
        **component_plan,
        "component_type": "SOURCE",
        "candidate_component_role": "source_or_control_replay_builder",
    }
    guard_plan = {
        **component_plan,
        "component_type": "GUARD",
        "candidate_component_role": "fail_closed_guard_binding",
    }
    market_plan = {
        "market_transfer_dispatch_row_id": "market-dispatch-1",
        "input_market_runtime_binding_row_id": "market-runtime-1",
        "market_transfer_dispatch_status": "MARKET_DISPATCH_SOURCE_REPAIR_OR_PROXY_ACTION_READY",
        "market_transfer_dispatch_action": "execute_source_repair_or_proxy_for_market_scope",
        "symbol": "NAS100_NQ",
        "broker_proxy_mapping": "NAS100_NQ",
        "tradability_status": "futures_proxy_context",
        "data_source": ["historical_ohlc"],
        "available_timeframes": ["M1", "M15", "H1"],
        "session_kz_offkz_coverage": ["ny_core", "off_kz"],
    }

    family, status, action = candidate_materialization_family("NOFILL_CHALLENGER_MODULE_DISPATCH")
    materialized = candidate_materialization_decision(dispatch, 1)
    scorer = scorer_code_surface_materialization(scorer_plan, 1)
    source = source_control_builder_materialization(source_plan, 1)
    nofill = nofill_comparator_materialization(component_plan, 1)
    guard = guard_enforcement_materialization(guard_plan, 1)
    market = market_action_materialization(market_plan, 1)

    assert family == "NOFILL_CHALLENGER_COMPARATOR_MATERIALIZATION"
    assert status == "MATERIALIZE_NOFILL_CHALLENGER_COMPARATOR_READY"
    assert action == "write_status_quo_vs_nofill_challenger_comparator"
    assert materialized["candidate_materialization_family"] == "NOFILL_CHALLENGER_COMPARATOR_MATERIALIZATION"
    assert materialized["candidate_materialization_status"] == "MATERIALIZE_NOFILL_CHALLENGER_COMPARATOR_READY"
    assert scorer["scorer_materialization_status"] == "SCORER_CODE_SURFACE_READY_DEFAULT_OFF_WITH_GUARD"
    assert source["source_control_materialization_status"] == "SOURCE_CONTROL_BUILDER_EXECUTABLE"
    assert source["same_resource_execution_available"] is True
    assert nofill["nofill_materialization_status"] == "NOFILL_MATERIALIZE_POSITIVE_CHALLENGER_COMPARATOR"
    assert guard["guard_enforcement_status"] == "GUARD_ENFORCEMENT_REGISTERED_FAIL_CLOSED"
    assert market["market_action_materialization_status"] == "MARKET_ACTION_SOURCE_REPAIR_OR_PROXY_MATERIALIZED"
    assert materialized["runtime_score_allowed"] is False


def test_branch_local_unified_candidate_implementation_consumes_materialized_surfaces():
    materialized = {
        "candidate_materialization_decision_row_id": "materialized-1",
        "input_candidate_dispatch_decision_row_id": "dispatch-1",
        "input_candidate_runtime_decision_row_id": "runtime-1",
        "input_candidate_execution_row_id": "candidate-1",
        "input_unified_system_computed_action_row_id": "computed-1",
        "candidate_materialization_family": "NOFILL_CHALLENGER_COMPARATOR_MATERIALIZATION",
        "candidate_materialization_status": "MATERIALIZE_NOFILL_CHALLENGER_COMPARATOR_READY",
        "candidate_materialization_key": "materialized-key",
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
        "source_component": "nofill_component",
        "source_row_id": "nofill-1",
        "computed_proxy_delta": 0.22,
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
        "default_off_observation_score": 0.22,
    }
    scorer_materialized = {
        **materialized,
        "scorer_code_surface_materialization_row_id": "scorer-materialized-1",
        "scorer_materialization_status": "SCORER_CODE_SURFACE_READY_DEFAULT_OFF_WITH_GUARD",
        "branch_local_registry_key": "registry-key",
        "candidate_callable_name": "score_candidate_dispatch_default_off_00001",
        "required_guards": ["source_confidence_guard"],
    }
    source_materialized = {
        **materialized,
        "source_control_builder_materialization_row_id": "source-materialized-1",
        "source_control_materialization_status": "SOURCE_CONTROL_BUILDER_EXECUTABLE",
        "same_resource_execution_available": True,
        "missing_source_proof": [],
        "builder_spec": "build exact/source/proxy/control observation",
    }
    nofill_materialized = {
        **materialized,
        "nofill_comparator_materialization_row_id": "nofill-materialized-1",
        "nofill_materialization_status": "NOFILL_MATERIALIZE_POSITIVE_CHALLENGER_COMPARATOR",
        "nofill_system_role": "positive_nofill_challenger",
        "status_quo_control_required": True,
        "opportunity_preserved_as": "positive_challenger",
    }
    guard_materialized = {
        **materialized,
        "guard_enforcement_materialization_row_id": "guard-materialized-1",
        "guard_family": "source_control_or_denominator_guard",
        "fail_closed_condition": "missing_source_confidence_control_denominator_or_market_transfer_evidence",
        "guard_spec": "fail closed before score use",
    }
    market_materialized = {
        "market_action_materialization_row_id": "market-materialized-1",
        "input_market_transfer_dispatch_row_id": "market-dispatch-1",
        "market_action_materialization_status": "MARKET_ACTION_SOURCE_REPAIR_OR_PROXY_MATERIALIZED",
        "market_action_materialization_role": "source_acquisition_or_proxy_control",
        "market_action_materialization_action": "execute_source_repair_or_proxy_for_market_scope",
        "symbol": "NAS100_NQ",
        "broker_proxy_mapping": "NAS100_NQ",
        "tradability_status": "futures_proxy_context",
        "data_source": ["historical_ohlc"],
        "available_timeframes": ["M1", "M15", "H1"],
        "session_kz_offkz_coverage": ["ny_core", "off_kz"],
    }

    implementation = candidate_implementation_decision(materialized, 1)
    scorer = candidate_scorer_code_integration_candidate(scorer_materialized, 1)
    source = candidate_source_control_run_action(source_materialized, 1)
    nofill = candidate_nofill_execution_action(nofill_materialized, 1)
    guard = candidate_guard_registry_action(guard_materialized, 1)
    market = candidate_market_priority_action(market_materialized, 1)

    assert implementation["candidate_implementation_action"] == "IMPLEMENT_NOFILL_CHALLENGER_COMPARATOR"
    assert implementation["candidate_implementation_status"] == "IMPLEMENTATION_READY_NOFILL_CHALLENGER"
    assert scorer["scorer_code_integration_status"] == "SCORER_CODE_INTEGRATION_CANDIDATE_READY_DEFAULT_OFF"
    assert source["source_control_run_status"] == "SOURCE_CONTROL_RUN_QUEUE_EXECUTE_NOW"
    assert nofill["nofill_execution_status"] == "NOFILL_EXECUTE_POSITIVE_CHALLENGER_COMPARATOR"
    assert guard["guard_registry_status"] == "GUARD_REGISTRY_BIND_FAIL_CLOSED_READY"
    assert market["market_priority_status"] == "MARKET_PRIORITY_SOURCE_REPAIR_OR_PROXY_NOW"
    assert implementation["runtime_score_allowed"] is False


def test_branch_local_unified_candidate_implementation_execution_consumes_actions():
    implementation = {
        "candidate_implementation_decision_row_id": "impl-1",
        "input_unified_system_computed_action_row_id": "computed-1",
        "candidate_implementation_action": "IMPLEMENT_NOFILL_CHALLENGER_COMPARATOR",
        "candidate_implementation_status": "IMPLEMENTATION_READY_NOFILL_CHALLENGER",
        "candidate_implementation_key": "impl-key",
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
        "source_component": "nofill_component",
        "source_row_id": "nofill-1",
        "computed_proxy_delta": 0.22,
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
        "default_off_observation_score": 0.22,
    }
    scorer = {
        **implementation,
        "scorer_code_integration_candidate_row_id": "scorer-1",
        "scorer_code_integration_status": "SCORER_CODE_INTEGRATION_CANDIDATE_READY_DEFAULT_OFF",
        "branch_local_registry_key": "registry-key",
        "candidate_callable_name": "score_candidate_dispatch_default_off_00001",
        "required_guards": ["source_confidence_guard"],
    }
    source = {
        **implementation,
        "source_control_run_action_row_id": "source-1",
        "source_control_run_status": "SOURCE_CONTROL_RUN_QUEUE_EXECUTE_NOW",
        "builder_spec": "build exact/source/proxy/control observation",
        "same_resource_execution_available": True,
        "missing_source_proof": [],
    }
    nofill = {
        **implementation,
        "nofill_execution_action_row_id": "nofill-1",
        "nofill_execution_status": "NOFILL_EXECUTE_POSITIVE_CHALLENGER_COMPARATOR",
        "status_quo_control_required": True,
        "opportunity_preserved_as": "positive_challenger",
    }
    guard = {
        **implementation,
        "guard_registry_action_row_id": "guard-1",
        "guard_family": "source_control_or_denominator_guard",
        "fail_closed_condition": "missing_source_confidence_control_denominator_or_market_transfer_evidence",
        "guard_spec": "fail closed before score use",
    }
    market = {
        "market_priority_action_row_id": "market-1",
        "market_priority_status": "MARKET_PRIORITY_SOURCE_REPAIR_OR_PROXY_NOW",
        "symbol": "NAS100_NQ",
        "broker_proxy_mapping": "NAS100_NQ",
        "tradability_status": "futures_proxy_context",
        "data_source": ["historical_ohlc"],
        "available_timeframes": ["M1", "M15", "H1"],
        "session_kz_offkz_coverage": ["ny_core", "off_kz"],
    }

    execution = candidate_implementation_execution_result(implementation, 1)
    scorer_artifact = candidate_scorer_module_artifact(scorer, 1)
    source_output = candidate_source_control_run_output(source, 1)
    nofill_output = candidate_nofill_comparator_output(nofill, 1)
    guard_artifact = candidate_guard_registry_artifact(guard, 1)
    market_output = candidate_market_priority_execution_output(market, 1)

    assert execution["implementation_execution_family"] == "EXECUTE_NOFILL_CHALLENGER_COMPARATOR_OUTPUT"
    assert execution["implementation_execution_status"] == "CANDIDATE_IMPLEMENTATION_EXECUTED_NOFILL_CHALLENGER_COMPARATOR"
    assert scorer_artifact["scorer_module_artifact_status"] == "SCORER_MODULE_ARTIFACT_DEFAULT_OFF_REGISTERED"
    assert source_output["source_control_output_status"] == "SOURCE_CONTROL_OUTPUT_EXECUTABLE_BUILDER_SPEC"
    assert nofill_output["nofill_output_status"] == "NOFILL_OUTPUT_POSITIVE_CHALLENGER_COMPARATOR_READY"
    assert guard_artifact["guard_registry_artifact_status"] == "GUARD_REGISTRY_ARTIFACT_BOUND_FAIL_CLOSED"
    assert market_output["market_priority_execution_status"] == "MARKET_PRIORITY_SOURCE_REPAIR_OR_PROXY_NOW_EXECUTED"
    assert execution["runtime_score_allowed"] is False


def test_branch_local_unified_candidate_execution_integration_consumes_outputs():
    execution = {
        "candidate_implementation_execution_result_row_id": "exec-1",
        "input_candidate_implementation_decision_row_id": "impl-1",
        "input_unified_system_computed_action_row_id": "computed-1",
        "implementation_execution_family": "EXECUTE_NOFILL_CHALLENGER_COMPARATOR_OUTPUT",
        "implementation_execution_status": "CANDIDATE_IMPLEMENTATION_EXECUTED_NOFILL_CHALLENGER_COMPARATOR",
        "implementation_execution_key": "exec-key",
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
        "source_component": "nofill_component",
        "source_row_id": "nofill-1",
        "computed_proxy_delta": 0.22,
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
    }
    registry = {
        **execution,
        "scorer_module_artifact_row_id": "scorer-artifact-1",
        "scorer_module_artifact_status": "SCORER_MODULE_ARTIFACT_DEFAULT_OFF_REGISTERED",
        "branch_local_registry_key": "registry-key",
        "candidate_callable_name": "score_candidate_dispatch_default_off_00001",
        "required_guards": ["source_confidence_guard"],
        "event_match_policy": "match scope",
    }
    source = {
        **execution,
        "source_control_output_row_id": "source-output-1",
        "source_control_output_status": "SOURCE_CONTROL_OUTPUT_EXECUTABLE_BUILDER_SPEC",
        "builder_spec": "build exact/source/proxy/control observation",
        "same_resource_execution_available": True,
        "missing_source_proof": [],
    }
    nofill = {
        **execution,
        "nofill_comparator_output_row_id": "nofill-output-1",
        "nofill_output_status": "NOFILL_OUTPUT_POSITIVE_CHALLENGER_COMPARATOR_READY",
        "nofill_system_role": "positive_challenger_comparator",
        "status_quo_control_required": True,
    }
    guard = {
        **execution,
        "guard_registry_artifact_row_id": "guard-artifact-1",
        "guard_family": "source_control_or_denominator_guard",
        "fail_closed_condition": "missing_source_confidence_control_denominator_or_market_transfer_evidence",
        "guard_spec": "fail closed before score use",
    }
    market = {
        "market_priority_execution_output_row_id": "market-output-1",
        "market_priority_execution_status": "MARKET_PRIORITY_SOURCE_REPAIR_OR_PROXY_NOW_EXECUTED",
        "symbol": "NAS100_NQ",
        "broker_proxy_mapping": "NAS100_NQ",
        "tradability_status": "futures_proxy_context",
        "data_source": ["historical_ohlc"],
        "available_timeframes": ["M1", "M15", "H1"],
        "session_kz_offkz_coverage": ["ny_core", "off_kz"],
    }

    integration = candidate_execution_integration_decision(execution, 1)
    registry_row = candidate_registry_module_row(registry, 1)
    source_row = candidate_source_control_result_row(source, 1)
    nofill_row = candidate_nofill_result_row(nofill, 1)
    guard_row = candidate_guard_bound_integration_row(guard, 1)
    market_row = candidate_market_system_integration_row(market, 1)

    assert integration["execution_integration_family"] == "INTEGRATE_NOFILL_CHALLENGER_COMPARATOR_RESULT"
    assert integration["execution_integration_status"] == "EXECUTION_INTEGRATION_NOFILL_CHALLENGER_READY"
    assert registry_row["registry_module_status"] == "REGISTRY_MODULE_DEFAULT_OFF_EVENT_MATCH_READY"
    assert source_row["source_control_result_status"] == "SOURCE_CONTROL_RESULT_BUILDER_EXECUTION_READY"
    assert nofill_row["nofill_result_status"] == "NOFILL_RESULT_POSITIVE_CHALLENGER_SCORABLE"
    assert guard_row["guard_bound_status"] == "GUARD_BOUND_INTEGRATION_FAIL_CLOSED_READY"
    assert market_row["market_system_integration_status"] == "MARKET_SYSTEM_INTEGRATION_SOURCE_REPAIR_PROXY_READY"
    assert integration["runtime_score_allowed"] is False


def test_branch_local_unified_candidate_integrated_scoring_result_consumes_integration_rows():
    integration = {
        "execution_integration_decision_row_id": "integration-1",
        "input_candidate_implementation_execution_result_row_id": "exec-1",
        "input_unified_system_computed_action_row_id": "computed-1",
        "execution_integration_family": "INTEGRATE_NOFILL_CHALLENGER_COMPARATOR_RESULT",
        "execution_integration_status": "EXECUTION_INTEGRATION_NOFILL_CHALLENGER_READY",
        "integration_result_key": "integration-key",
        "integration_proxy_delta": 0.22,
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
        "source_component": "nofill_component",
        "source_row_id": "nofill-1",
        "computed_proxy_delta": 0.22,
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
        "source_manifest_hash": "hash-current",
        "upstream_source_manifest_hash": "hash-upstream",
    }
    registry = {
        **integration,
        "registry_module_row_id": "registry-1",
        "registry_module_status": "REGISTRY_MODULE_DEFAULT_OFF_EVENT_MATCH_READY",
        "branch_local_registry_key": "registry-key",
        "candidate_callable_name": "score_candidate_dispatch_default_off_00001",
        "required_guards": ["source_confidence_guard"],
        "event_match_policy": "match scope",
    }
    source = {
        **integration,
        "source_control_result_row_id": "source-1",
        "source_control_result_status": "SOURCE_CONTROL_RESULT_BUILDER_EXECUTION_READY",
        "builder_spec": "build exact/source/proxy/control observation",
        "same_resource_execution_available": True,
        "missing_source_proof": [],
        "result_rejoin_contract": "same scope before use",
    }
    nofill = {
        **integration,
        "nofill_result_row_id": "nofill-1",
        "nofill_result_status": "NOFILL_RESULT_POSITIVE_CHALLENGER_SCORABLE",
        "nofill_system_role": "positive_challenger_comparator",
        "status_quo_control_required": True,
        "opportunity_preserved_as": "positive_challenger",
    }
    guard = {
        **integration,
        "guard_bound_integration_row_id": "guard-1",
        "guard_family": "source_control_or_denominator_guard",
        "fail_closed_condition": "missing_source_confidence_control_denominator_or_market_transfer_evidence",
        "guard_spec": "fail closed before score use",
    }
    market = {
        "market_system_integration_row_id": "market-1",
        "market_system_integration_status": "MARKET_SYSTEM_INTEGRATION_SOURCE_REPAIR_PROXY_READY",
        "symbol": "NAS100_NQ",
        "broker_proxy_mapping": "NAS100_NQ",
        "tradability_status": "futures_proxy_context",
        "data_source": ["historical_ohlc"],
        "available_timeframes": ["M1", "M15", "H1"],
        "session_kz_offkz_coverage": ["ny_core", "off_kz"],
        "source_manifest_hash": "hash-current",
    }

    decision = candidate_integrated_scoring_decision(integration, 1)
    module = candidate_default_off_module_result(registry, 1)
    source_result = candidate_source_control_builder_result(source, 1)
    nofill_result = candidate_nofill_comparator_result_table(nofill, 1)
    guard_result = candidate_guard_binding_result(guard, 1)
    market_result = candidate_market_transfer_decision(market, 1)

    assert decision["integrated_result_decision"] == "KEEP_NOFILL_CHALLENGER_COMPARATOR_RESULT"
    assert decision["keep_kill_redesign_implement_decision"] == "KEEP_NOFILL_CHALLENGER_COMPARATOR_RESULT"
    assert decision["underlying_mechanism_preserved"] is True
    assert module["module_result_decision"] == "IMPLEMENT_DEFAULT_OFF_MODULE_SPEC"
    assert source_result["source_builder_decision"] == "RUN_EXACT_OR_SAME_SCOPE_CONTROL_BUILDER"
    assert nofill_result["nofill_comparator_decision"] == "KEEP_NOFILL_POSITIVE_CHALLENGER_COMPARATOR"
    assert guard_result["guard_binding_status"] == "GUARD_BINDING_FAIL_CLOSED_ATTACHED"
    assert market_result["market_transfer_decision"] == "MARKET_SOURCE_REPAIR_OR_PROXY_EXECUTE"
    assert decision["runtime_score_allowed"] is False


def test_branch_local_unified_candidate_integrated_result_execution_consumes_result_tables():
    decision = {
        "integrated_scoring_decision_row_id": "integrated-1",
        "input_execution_integration_decision_row_id": "integration-1",
        "input_unified_system_computed_action_row_id": "computed-1",
        "integrated_result_decision": "KEEP_NOFILL_CHALLENGER_COMPARATOR_RESULT",
        "integration_result_key": "integration-key",
        "symbol": "NAS100_NQ",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "MARKET_GAP",
        "mechanical_scope_key": "symbol=NAS100_NQ|session=ny_core|horizon=h4|primitive=MARKET_GAP",
        "source_component": "nofill_component",
        "source_row_id": "nofill-1",
        "computed_proxy_delta": 0.22,
        "computed_proxy_delta_class": "COMPUTED_PROXY_DELTA_STRONG_POSITIVE",
        "integrated_proxy_delta_band": "PROXY_DELTA_POSITIVE",
    }
    module = {
        **decision,
        "default_off_module_result_row_id": "module-1",
        "module_result_decision": "IMPLEMENT_DEFAULT_OFF_MODULE_SPEC",
        "branch_local_registry_key": "registry-key",
        "candidate_callable_name": "score_candidate_dispatch_default_off_00001",
        "event_match_policy": "match scope",
        "required_guards": ["source_confidence_guard"],
    }
    source = {
        **decision,
        "source_control_builder_result_row_id": "source-1",
        "source_builder_decision": "RUN_EXACT_OR_SAME_SCOPE_CONTROL_BUILDER",
        "builder_spec": "build exact/source/proxy/control observation",
        "same_resource_execution_available": True,
        "missing_source_proof": [],
        "missing_source_proof_count": 0,
    }
    nofill = {
        **decision,
        "nofill_comparator_result_table_row_id": "nofill-1",
        "nofill_comparator_decision": "KEEP_NOFILL_POSITIVE_CHALLENGER_COMPARATOR",
        "nofill_system_role": "positive_challenger_comparator",
        "status_quo_control_required": True,
    }
    guard = {
        **decision,
        "guard_binding_result_row_id": "guard-1",
        "guard_binding_decision": "BIND_FAIL_CLOSED_GUARD_TO_RESULT_COMPONENT",
        "guard_family": "source_control_or_denominator_guard",
        "fail_closed_condition": "missing_source_confidence_control_denominator_or_market_transfer_evidence",
        "guard_spec": "fail closed before score use",
    }
    market = {
        "market_transfer_decision_row_id": "market-1",
        "market_transfer_decision": "MARKET_SOURCE_REPAIR_OR_PROXY_EXECUTE",
        "symbol": "NAS100_NQ",
        "broker_proxy_mapping": "NAS100_NQ",
        "tradability_status": "futures_proxy_context",
        "data_source": ["historical_ohlc"],
        "available_timeframes": ["M1", "M15", "H1"],
        "session_kz_offkz_coverage": ["ny_core", "off_kz"],
    }

    execution = candidate_integrated_result_execution(decision, 1)
    registry = candidate_scorer_registry_dispatch(module, 1)
    source_output = candidate_source_control_execution_output(source, 1)
    nofill_output = candidate_nofill_comparator_execution_output(nofill, 1)
    guard_output = candidate_guard_dispatch_output(guard, 1)
    market_output = candidate_market_transfer_dispatch(market, 1)

    assert execution["integrated_result_execution_family"] == "EXECUTE_NOFILL_STATUS_QUO_COMPARATOR_SCORING"
    assert execution["integrated_result_execution_status"] == "INTEGRATED_RESULT_EXECUTION_NOFILL_COMPARATOR_READY"
    assert registry["scorer_registry_dispatch_status"] == "SCORER_REGISTRY_CODE_EMITTED_DEFAULT_OFF"
    assert source_output["source_control_execution_status"] == "SOURCE_CONTROL_EXECUTION_EXACT_BUILDER_OUTPUT_READY"
    assert nofill_output["nofill_comparator_execution_status"] == "NOFILL_EXECUTION_STATUS_QUO_CHALLENGER_SCORING_READY"
    assert nofill_output["status_quo_comparator_scoring_ready"] is True
    assert guard_output["guard_dispatch_status"] == "GUARD_DISPATCH_FAIL_CLOSED_ACTIVE_IN_BRANCH_LOCAL_RESULT"
    assert market_output["market_transfer_dispatch_action"] == "MARKET_SOURCE_REPAIR_OR_PROXY_EXECUTE"
    assert execution["runtime_score_allowed"] is False


def test_numeric_integrated_result_row_computes_proxy_r_and_exact_missing_proof():
    execution = {
        "integrated_result_execution_row_id": "exec-1",
        "input_unified_system_computed_action_row_id": "computed-1",
        "integrated_result_execution_family": "EXECUTE_NOFILL_STATUS_QUO_COMPARATOR_SCORING",
        "integrated_result_execution_status": "INTEGRATED_RESULT_EXECUTION_NOFILL_COMPARATOR_READY",
        "source_component": "nofill_near_miss_market_entry",
        "source_row_id": "OHLC-GTOS-NEARMISS-MARKET-BRANCH-00001",
        "symbol": "GBPJPY",
        "route_session": "tokyo_kz",
        "horizon_id": "h4",
        "primitive_flag": "SWEEP_LOW_CLOSE_BACK_INSIDE_16",
        "computed_proxy_delta": 0.18,
    }
    computed = {
        "unified_system_computed_action_row_id": "computed-1",
        "computed_action_family": "NOFILL_REDESIGN_SCORING",
        "computed_action_status": "NEAR_MISS_MARKET_ENTRY_TARGET_STOP_PROXY_SCORED",
        "computed_decision": "COMPARE_MARKET_ENTRY_PROXY_TO_RETEST_LIMIT_CONTROL",
        "computed_proxy_delta": 0.18,
        "expectancy_style_proxy_delta": 0.18,
        "pass_control_delta_proxy": 0.18,
    }
    branch = {
        "branch_queue_id": "OHLC-GTOS-COST-FILL-PATH-SYNTH-BRANCH-00010",
        "rstyle_midpoint_mean": 0.136175,
        "rstyle_lower_mean": 0.119673,
        "rstyle_upper_mean": 0.152677,
        "expectancy_style_proxy": {"midpoint_mean": 0.136175},
        "rstyle_proxy_all_components": {
            "status_counts": {
                "TARGET_TOUCH_BEFORE_STOP_M15_PROXY": 10,
                "STOP_TOUCH_BEFORE_TARGET_M15_PROXY": 2,
            }
        },
        "cost_sensitivity": {
            "branch_status_cost_counters": {
                "COST_INVARIANT_DESCRIPTOR": 10,
                "ZERO_TO_SPREAD_PROXY_DESCRIPTOR_SHIFT": 2,
            }
        },
    }
    sidecar = {
        "market_first_touch_status": "TARGET_TOUCH_BEFORE_STOP_M15_PROXY",
        "market_spread_proxy_price_distance": 0.015,
    }

    row = numeric_integrated_result_row(
        execution,
        computed,
        branch,
        sidecar,
        1,
        branch_match_count=1,
        branch_match_status="SIDECAR_SCOPE_UNIQUE_BRANCH_MATCH",
    )

    assert row["proxy_r_status"] == "PROXY_RSTYLE_FROM_BRANCH_REPLAY_TABLE"
    assert row["proxy_r_value"] == 0.136175
    assert row["expectancy_proxy_value"] == 0.136175
    assert row["target_stop_order_class"] == "TARGET_FIRST_PROXY_DOMINANT"
    assert row["cost_stress_status"] == "COST_STRESS_COMPUTED_FROM_SPREAD_SENSITIVITY_COUNTS"
    assert row["exact_r_status"] == "EXACT_R_NOT_COMPUTABLE_MISSING_BROKER_EXECUTION_GEOMETRY"
    assert "deal_ticket" in row["exact_missing_field_proof"]
    assert row["keep_kill_redesign_implement_decision"] == "KEEP_NOFILL_CHALLENGER_COMPARATOR_STRONG_POSITIVE"


def test_numeric_integrated_result_row_converts_negative_proxy_to_avoid_inverse_role():
    execution = {
        "integrated_result_execution_row_id": "exec-2",
        "input_unified_system_computed_action_row_id": "computed-2",
        "integrated_result_execution_family": "EXECUTE_AVOID_INVERSE_FEATURE_EMISSION",
        "source_component": "nofill_far_miss_avoid",
        "source_row_id": "OHLC-GTOS-NOFILL-FAR-AVOID-00001",
        "symbol": "XAUUSD",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "computed_proxy_delta": -0.22,
    }
    computed = {
        "unified_system_computed_action_row_id": "computed-2",
        "computed_action_family": "NOFILL_REDESIGN_SCORING",
        "computed_action_status": "NOFILL_AVOID_OR_INVERSE_VARIANT_PROXY_SCORED",
        "computed_decision": "SCORE_AVOID_INVERSE_VARIANT_WITH_SIBLING_CONTROL",
        "computed_proxy_delta": -0.22,
        "expectancy_style_proxy_delta": -0.22,
    }

    row = numeric_integrated_result_row(execution, computed, None, None, 2)

    assert row["proxy_r_status"] == "PROXY_RSTYLE_FROM_COMPUTED_SIGNED_DELTA"
    assert row["proxy_r_class"] == "STRONG_NEGATIVE_PROXY_R"
    assert row["negative_or_failure_intelligence_role"] == "avoid_inverse_or_entry_failure_filter"
    assert row["keep_kill_redesign_implement_decision"] == "CONVERT_STRONG_NEGATIVE_TO_AVOID_INVERSE_OR_FAILURE_FILTER"


def test_numeric_helpers_classify_cost_target_stop_and_rollup():
    target_class, counts, basis = numeric_classify_target_stop_order(
        {"target_stop_result_counts": {"TARGET_TOUCH_BEFORE_STOP_M15_PROXY": 3, "STOP_TOUCH_BEFORE_TARGET_M15_PROXY": 1}}
    )
    cost = numeric_cost_stress_evidence(
        {"cost_sensitivity": {"branch_status_cost_counters": {"COST_INVARIANT_DESCRIPTOR": 3, "SPREAD_PROXY_GRADIENT_DESCRIPTOR_SENSITIVE": 1}}}
    )
    exact = numeric_exact_r_evidence({"exact_r": 0.75})
    proxy = numeric_proxy_r_evidence({"computed_proxy_delta": 0.1})
    rollup = numeric_integrated_rollup(
        ("family",),
        [
            {
                "proxy_r_value": 0.1,
                "expectancy_proxy_value": 0.1,
                "keep_kill_redesign_implement_decision": "KEEP_POSITIVE_PROXY_R_WITH_CONTROL",
                "exact_r_status": "EXACT_R_NOT_COMPUTABLE_MISSING_BROKER_EXECUTION_GEOMETRY",
                "proxy_r_class": "POSITIVE_PROXY_R",
                "target_stop_order_class": target_class,
                "cost_stress_status": cost["cost_stress_status"],
            }
        ],
        1,
        "family_expectancy",
    )

    assert target_class == "TARGET_FIRST_PROXY_DOMINANT"
    assert counts["TARGET_TOUCH_BEFORE_STOP_M15_PROXY"] == 3
    assert basis == "target_count_gt_stop_count"
    assert cost["cost_sensitive_share"] == 0.25
    assert exact["exact_r_value"] == 0.75
    assert proxy["proxy_r_value"] == 0.1
    assert rollup["proxy_r_mean"] == 0.1


def test_numeric_decision_module_executes_default_off_score_and_mismatch():
    numeric = {
        "numeric_result_row_id": "numeric-1",
        "input_integrated_result_execution_row_id": "exec-1",
        "source_component": "registry_scorer_module",
        "source_row_id": "source-1",
        "symbol": "NAS100",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "ABSORPTION_PROXY",
        "mechanical_scope_key": "symbol=NAS100|session=ny_core|horizon=h4|primitive=ABSORPTION_PROXY",
        "keep_kill_redesign_implement_decision": "IMPLEMENT_DEFAULT_OFF_SCORER_RESEARCH_MODULE",
        "decision_proxy_value": 0.21,
        "proxy_r_value": 0.19,
        "proxy_r_class": "STRONG_POSITIVE_PROXY_R",
        "exact_r_status": "EXACT_R_NOT_COMPUTABLE_MISSING_BROKER_EXECUTION_GEOMETRY",
    }

    module = module_record_from_numeric_result(numeric, 1)
    matching = execute_numeric_module_event(
        {
            "mechanical_scope_key": "symbol=NAS100|session=ny_core|horizon=h4|primitive=ABSORPTION_PROXY",
            "source_component": "registry_scorer_module",
        },
        module,
    )
    mismatch = execute_numeric_module_event({"symbol": "XAUUSD", "source_component": "registry_scorer_module"}, module)

    assert module["numeric_module_role"] == "DEFAULT_OFF_NUMERIC_SCORER_MODULE"
    assert module["score_emit_allowed_when_matched"] is True
    assert matching["numeric_module_event_status"] == "NUMERIC_MODULE_EVENT_DEFAULT_OFF_SCORE_EMITTED"
    assert matching["numeric_module_event_score"] == 0.21
    assert mismatch["numeric_module_event_status"] == "NUMERIC_MODULE_EVENT_SCOPE_MISMATCH"
    assert event_matches_numeric_module({"symbol": "NAS100", "route_session": "ny_core", "horizon_id": "h4", "primitive_flag": "ABSORPTION_PROXY", "source_component": "registry_scorer_module"}, module)


def test_numeric_decision_module_emits_avoid_and_repair_specs():
    negative = {
        "numeric_result_row_id": "numeric-2",
        "input_integrated_result_execution_row_id": "exec-2",
        "source_component": "nofill_far_miss_avoid",
        "source_row_id": "source-2",
        "symbol": "XAUUSD",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "SWEEP_FAILURE",
        "keep_kill_redesign_implement_decision": "CONVERT_STRONG_NEGATIVE_TO_AVOID_INVERSE_OR_FAILURE_FILTER",
        "decision_proxy_value": -0.24,
        "proxy_r_value": -0.24,
        "proxy_r_class": "STRONG_NEGATIVE_PROXY_R",
        "target_stop_order_class": "STOP_FIRST_PROXY_DOMINANT",
        "negative_or_failure_intelligence_role": "avoid_inverse_or_entry_failure_filter",
        "exact_missing_field_proof": ["deal_ticket"],
        "exact_r_status": "EXACT_R_NOT_COMPUTABLE_MISSING_BROKER_EXECUTION_GEOMETRY",
    }
    repair = {
        **negative,
        "numeric_result_row_id": "numeric-3",
        "keep_kill_redesign_implement_decision": "SOURCE_GEOMETRY_REPAIR_OR_GUARD_BINDING_REQUIRED",
        "exact_r_status": "EXACT_R_NOT_COMPUTABLE_SOURCE_JOIN_ABSENT",
    }

    avoid_module = module_record_from_numeric_result(negative, 2)
    avoid_event = execute_numeric_module_event(
        {"symbol": "XAUUSD", "route_session": "ny_core", "horizon_id": "h4", "primitive_flag": "SWEEP_FAILURE", "source_component": "nofill_far_miss_avoid"},
        avoid_module,
    )
    avoid_spec = numeric_avoid_inverse_filter_spec(negative, 1)
    repair_module = module_record_from_numeric_result(repair, 3)
    repair_event = execute_numeric_module_event(
        {"symbol": "XAUUSD", "route_session": "ny_core", "horizon_id": "h4", "primitive_flag": "SWEEP_FAILURE", "source_component": "nofill_far_miss_avoid"},
        repair_module,
    )
    repair_spec = numeric_source_geometry_repair_spec(repair, 1)

    assert avoid_module["numeric_module_role"] == "AVOID_INVERSE_OR_FAILURE_FILTER_MODULE"
    assert avoid_event["avoid_inverse_filter_emitted"] is True
    assert avoid_spec["filter_action"] == "avoid_current_entry_when_scope_matches_stop_first_proxy"
    assert repair_module["numeric_module_role"] == "SOURCE_GEOMETRY_REPAIR_MODULE"
    assert repair_event["numeric_module_event_status"] == "NUMERIC_MODULE_EVENT_SOURCE_GEOMETRY_REPAIR_REQUIRED"
    assert repair_spec["repair_action"] == "acquire_or_rebuild_missing_source_join_before_exact_r"


def test_numeric_module_registry_router_applies_score_and_scope_decision():
    numeric = {
        "numeric_result_row_id": "numeric-1",
        "source_component": "registry_scorer_module",
        "source_row_id": "source-1",
        "symbol": "NAS100",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "ABSORPTION_PROXY",
        "mechanical_scope_key": "symbol=NAS100|session=ny_core|horizon=h4|primitive=ABSORPTION_PROXY",
        "keep_kill_redesign_implement_decision": "IMPLEMENT_DEFAULT_OFF_SCORER_RESEARCH_MODULE",
        "decision_proxy_value": 0.21,
        "proxy_r_value": 0.19,
        "proxy_r_class": "STRONG_POSITIVE_PROXY_R",
        "exact_r_status": "EXACT_R_NOT_COMPUTABLE_MISSING_BROKER_EXECUTION_GEOMETRY",
    }
    module = module_record_from_numeric_result(numeric, 1)
    registry = build_numeric_module_registry([module])
    routed = route_numeric_event(event_from_numeric_result(numeric), registry)
    application = router_application_row(numeric, routed, 1)
    scope = scope_router_decision([application], 1, ("NAS100", "ny_core", "h4", "registry_scorer_module"))

    assert registry["module_count"] == 1
    assert routed["numeric_module_event_status"] == "NUMERIC_MODULE_EVENT_DEFAULT_OFF_SCORE_EMITTED"
    assert application["router_application_action"] == "REGISTER_DEFAULT_OFF_SCORER_SURFACE"
    assert scope["router_scope_decision"] == "IMPLEMENT_DEFAULT_OFF_SCORER_SCOPE_WITH_GUARDS"


def test_numeric_source_repair_execution_preserves_missing_geometry_proof():
    spec = {
        "source_geometry_repair_spec_row_id": "repair-1",
        "input_numeric_result_row_id": "numeric-1",
        "symbol": "XAUUSD",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "primitive_flag": "SWEEP_FAILURE",
        "source_component": "source_join",
        "source_row_id": "source-1",
        "repair_action": "join_or_reconstruct_broker_execution_geometry_fields",
        "missing_field_count": 2,
        "exact_missing_field_proof": ["deal_ticket", "filled_price"],
    }

    execution = numeric_source_repair_execution_row(spec, 1)

    assert execution["source_repair_execution_status"] == "SOURCE_REPAIR_EXECUTION_BROKER_EXECUTION_GEOMETRY_FIELDS_REQUIRED"
    assert execution["exact_repair_possible_from_current_packet"] is False
    assert execution["opportunity_preserved"] is True


def test_numeric_shadow_scorer_computes_exact_r_when_geometry_exists():
    exact = exact_r_from_geometry(
        {
            "trade_direction": "BUY",
            "executed_entry_price": 100.0,
            "executed_exit_price": 103.0,
            "executed_stop_price": 98.0,
            "commission_r": 0.05,
            "slippage_r": 0.02,
        }
    )

    assert exact["exact_r_compute_status"] == "EXACT_R_COMPUTED_FROM_BROKER_GEOMETRY"
    assert exact["raw_exact_r_before_cost"] == 1.5
    assert exact["exact_r_value"] == 1.43


def test_numeric_shadow_scorer_scores_proxy_and_scope_with_avoid_penalty():
    positive = scored_numeric_event(
        {
            "numeric_result_row_id": "numeric-1",
            "symbol": "NAS100",
            "route_session": "ny_core",
            "horizon_id": "h4",
            "primitive_flag": "ABSORPTION_PROXY",
            "source_component": "registry_scorer_module",
            "decision_proxy_value": 0.25,
            "proxy_r_class": "STRONG_POSITIVE_PROXY_R",
            "keep_kill_redesign_implement_decision": "IMPLEMENT_DEFAULT_OFF_SCORER_RESEARCH_MODULE",
        },
        1,
    )
    negative = scored_numeric_event(
        {
            "numeric_result_row_id": "numeric-2",
            "symbol": "NAS100",
            "route_session": "ny_core",
            "horizon_id": "h4",
            "primitive_flag": "ABSORPTION_PROXY",
            "source_component": "registry_scorer_module",
            "decision_proxy_value": -0.35,
            "proxy_r_class": "STRONG_NEGATIVE_PROXY_R",
            "keep_kill_redesign_implement_decision": "CONVERT_STRONG_NEGATIVE_TO_AVOID_INVERSE_OR_FAILURE_FILTER",
        },
        2,
    )
    repair = numeric_shadow_repair_queue_row(
        {
            "source_repair_proof_row_id": "repair-1",
            "input_numeric_result_row_id": "numeric-1",
            "symbol": "NAS100",
            "route_session": "ny_core",
            "horizon_id": "h4",
            "source_component": "registry_scorer_module",
            "source_repair_system_decision": "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R",
            "exact_missing_field_proof": ["deal_ticket"],
        },
        1,
    )
    registry = build_shadow_scorer_registry([positive, negative], [repair])
    scope = numeric_shadow_score_scope_event(
        {
            "scope_system_decision_row_id": "scope-1",
            "symbol": "NAS100",
            "route_session": "ny_core",
            "horizon_id": "h4",
            "source_component": "registry_scorer_module",
            "router_scope_decision": "IMPLEMENT_DEFAULT_OFF_SCORER_SCOPE_WITH_GUARDS",
        },
        registry,
        1,
    )

    assert positive["shadow_score_basis"] == "proxy_r"
    assert negative["shadow_decision"] == "SCORE_AVOID_INVERSE_OR_FAILURE_FILTER_PROXY_EVENT"
    assert repair["repair_queue"] == "BROKER_EXECUTION_GEOMETRY_EXACT_R_REPAIR_QUEUE"
    assert scope["net_shadow_score"] == -0.1
    assert scope["scope_shadow_decision"] == "AVOID_INVERSE_OR_FAILURE_FILTER_FIRST"


def test_broker_source_repair_joins_exact_r_only_on_direct_identifier():
    source_index = broker_source_build_source_index(
        [
            broker_source_observation(
                "account_pnl_truth_reconciliation.jsonl",
                {
                    "trade_id": "XAUUSD_2026-05-01_london_0815",
                    "symbol": "XAUUSD",
                    "result_r": -0.7395,
                    "actual_r_claim_allowed": True,
                },
                1,
                "shadow_logs/account_pnl_truth_reconciliation.jsonl",
            )
        ]
    )
    repair = {
        "source_repair_queue_row_id": "repair-1",
        "input_numeric_result_row_id": "numeric-1",
        "symbol": "XAUUSD",
        "route_session": "london_core",
        "source_component": "registry_scorer_module",
        "repair_queue": "BROKER_EXECUTION_GEOMETRY_EXACT_R_REPAIR_QUEUE",
        "exact_missing_field_proof": ["deal_ticket"],
    }
    numeric = {
        "numeric_result_row_id": "numeric-1",
        "trade_id": "XAUUSD_2026-05-01_london_0815",
        "proxy_r_value": 0.2,
        "matched_branch_queue_id": "branch-1",
        "target_stop_order_class": "TARGET_FIRST_PROXY_DOMINANT",
    }

    row = broker_source_repair_result_row(repair, numeric, None, source_index, 1)

    assert row["exact_broker_join_status"] == "EXACT_R_JOINED_FROM_DIRECT_LOCAL_BROKER_IDENTIFIER"
    assert row["exact_broker_r_value"] == -0.7395
    assert row["hard_repair_decision"] == "IMPLEMENT_AVOID_OR_FAILURE_FILTER_FROM_EXACT_R"
    assert row["runtime_score_allowed"] is False


def test_broker_source_repair_attaches_branch_proxy_without_exact_overclaim():
    source_index = broker_source_build_source_index([])
    repair = {
        "source_repair_queue_row_id": "repair-1",
        "input_numeric_result_row_id": "numeric-1",
        "symbol": "GBPJPY",
        "route_session": "tokyo_kz",
        "source_component": "nofill_far_miss_source_confidence",
        "repair_queue": "SOURCE_JOIN_REPAIR_QUEUE",
        "exact_missing_field_proof": ["deal_ticket"],
    }
    numeric = {
        "numeric_result_row_id": "numeric-1",
        "matched_branch_queue_id": "OHLC-GTOS-COST-FILL-PATH-SYNTH-BRANCH-00177",
        "proxy_r_value": None,
    }
    branch = {
        "branch_queue_id": "OHLC-GTOS-COST-FILL-PATH-SYNTH-BRANCH-00177",
        "route_candidate_id": "GBPJPY|tokyo_kz|LOWER_WICK_EXHAUSTION|h4",
        "primary_selector_score": 0.05213,
    }

    row = broker_source_repair_result_row(repair, numeric, branch, source_index, 1)

    assert row["exact_broker_join_status"] == "EXACT_R_NOT_JOINABLE_NO_DIRECT_TRADE_CANDIDATE_OR_TICKET_IDENTIFIER"
    assert row["branch_source_status"] == "BRANCH_SOURCE_ATTACHED_FROM_MATCHED_BRANCH_QUEUE"
    assert row["source_repaired_proxy_status"] == "BRANCH_SOURCE_PROXY_ATTACHED_FROM_MATCHED_BRANCH"
    assert row["source_repaired_proxy_value"] == 0.05213
    assert row["hard_repair_decision"] == "KEEP_SOURCE_REPAIRED_PROXY_AS_DEFAULT_OFF_SCORER_OR_GUARD_INPUT"


def test_broker_source_implementation_decision_uses_repaired_negative_proxy():
    scope = {
        "scope_score_decision_row_id": "scope-1",
        "symbol": "GBPJPY",
        "route_session": "tokyo_kz",
        "horizon_id": None,
        "source_component": "nofill_far_miss_avoid",
        "aggregate_scope_key": "symbol=GBPJPY|route_session=tokyo_kz|horizon_id=|source_component=nofill_far_miss_avoid",
        "scope_shadow_decision": "AVOID_INVERSE_OR_FAILURE_FILTER_FIRST",
    }
    decision = broker_source_implementation_decision_row(
        scope,
        [{"source_repaired_proxy_value": -1.0, "hard_repair_decision": "KEEP_SOURCE_REPAIRED_NEGATIVE_PROXY_AS_AVOID_OR_REDESIGN_INPUT"}],
        [{"shadow_score": -1.0}],
        1,
    )

    assert decision["implementation_decision"] == "IMPLEMENT_SCOPE_AVOID_OR_REDESIGN_FROM_REPAIRED_NEGATIVE_PROXY"
    assert decision["scope_negative_repaired_proxy_rows"] == 1


def test_repaired_proxy_scope_scorer_emits_default_off_score_from_repair_rows():
    decision = {
        "broker_source_implementation_decision_row_id": "decision-1",
        "symbol": "GBPJPY",
        "route_session": "tokyo_kz",
        "horizon_id": None,
        "source_component": "nofill_far_miss_retest",
        "aggregate_scope_key": "symbol=GBPJPY|route_session=tokyo_kz|horizon_id=|source_component=nofill_far_miss_retest",
        "implementation_decision": "IMPLEMENT_SCOPE_DEFAULT_OFF_PROXY_SCORER_WITH_SOURCE_REPAIR_GUARDS",
        "scope_repaired_proxy_mean": 0.25,
    }
    event = {
        "shadow_scorer_event_score_row_id": "event-1",
        "input_numeric_result_row_id": "numeric-1",
        "symbol": "GBPJPY",
        "route_session": "tokyo_kz",
        "horizon_id": None,
        "source_component": "nofill_far_miss_retest",
        "aggregate_scope_key": decision["aggregate_scope_key"],
        "shadow_score": 0.1,
    }
    registry_row = repaired_proxy_registry_row_from_decision(decision, 1)
    registry = repaired_proxy_build_registry([registry_row])
    application = repaired_proxy_event_application_row(
        event,
        registry["by_scope"][decision["aggregate_scope_key"]],
        [{"source_repaired_proxy_value": 0.5}],
        1,
    )

    assert registry_row["registry_role"] == "DEFAULT_OFF_REPAIRED_PROXY_SCORER_SCOPE"
    assert application["repaired_proxy_event_status"] == "REPAIRED_PROXY_EVENT_DEFAULT_OFF_SCORE_EMITTED"
    assert application["repaired_proxy_event_score"] == 0.5
    assert application["emits_default_off_score"] is True


def test_repaired_proxy_scope_scorer_emits_avoid_and_repair_required():
    avoid_registry = repaired_proxy_registry_row_from_decision(
        {
            "broker_source_implementation_decision_row_id": "decision-2",
            "symbol": "GBPJPY",
            "route_session": "tokyo_kz",
            "horizon_id": None,
            "source_component": "nofill_far_miss_avoid",
            "aggregate_scope_key": "symbol=GBPJPY|route_session=tokyo_kz|horizon_id=|source_component=nofill_far_miss_avoid",
            "implementation_decision": "IMPLEMENT_SCOPE_AVOID_OR_REDESIGN_FROM_REPAIRED_NEGATIVE_PROXY",
            "scope_repaired_proxy_mean": -0.6,
        },
        2,
    )
    repair_registry = repaired_proxy_registry_row_from_decision(
        {
            "broker_source_implementation_decision_row_id": "decision-3",
            "symbol": "GBPJPY",
            "route_session": "london_core",
            "horizon_id": "h32",
            "source_component": "default_off_application",
            "aggregate_scope_key": "symbol=GBPJPY|route_session=london_core|horizon_id=h32|source_component=default_off_application",
            "implementation_decision": "SOURCE_OR_BROKER_GEOMETRY_REPAIR_REMAINS_REQUIRED_FOR_SCOPE",
        },
        3,
    )
    avoid_event = score_event_with_repaired_scope(
        {
            "symbol": "GBPJPY",
            "route_session": "tokyo_kz",
            "horizon_id": None,
            "source_component": "nofill_far_miss_avoid",
            "aggregate_scope_key": avoid_registry["aggregate_scope_key"],
        },
        avoid_registry,
        [],
    )
    repair_event = score_event_with_repaired_scope(
        {
            "symbol": "GBPJPY",
            "route_session": "london_core",
            "horizon_id": "h32",
            "source_component": "default_off_application",
            "aggregate_scope_key": repair_registry["aggregate_scope_key"],
        },
        repair_registry,
        [],
    )

    assert avoid_event["emits_avoid_or_redesign"] is True
    assert avoid_event["repaired_proxy_event_score"] == -0.6
    assert repair_event["emits_source_repair_required"] is True
    assert repair_event["repaired_proxy_event_score"] is None


def test_repaired_proxy_execution_specs_use_concrete_boundaries():
    event = {
        "repaired_proxy_event_application_row_id": "app-1",
        "input_numeric_result_row_id": "numeric-1",
        "input_shadow_scorer_event_score_row_id": "event-1",
        "input_repaired_proxy_scope_registry_row_id": "scope-1",
        "symbol": "GBPJPY",
        "route_session": "tokyo_kz",
        "horizon_id": "h16",
        "primitive_flag": "LOWER_WICK_EXHAUSTION",
        "source_component": "nofill_far_miss_retest",
        "aggregate_scope_key": "symbol=GBPJPY|route_session=tokyo_kz|horizon_id=h16|source_component=nofill_far_miss_retest",
        "repaired_proxy_event_score": 0.35,
        "repaired_proxy_event_score_source": "repair_result_source_repaired_proxy_mean",
        "required_guards": ["source_repair_guard"],
    }

    spec = repaired_proxy_default_off_scorer_spec_from_event(event, 1)

    assert spec["score_value"] == 0.35
    assert spec["scorer_registration_action"] == "REGISTER_BRANCH_LOCAL_DEFAULT_OFF_REPAIRED_PROXY_SCORER"
    assert spec["research_boundary"]["artifact_scope"] == "branch_local_research"
    assert spec["research_boundary"]["runtime_candidate_use_permitted"] is False
    assert spec["unconditional_scalar_use_allowed"] is False


def test_repaired_proxy_avoid_repair_and_bridge_rows_are_executable():
    avoid_event = {
        "repaired_proxy_event_application_row_id": "app-2",
        "input_numeric_result_row_id": "numeric-2",
        "symbol": "XAGUSD",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "source_component": "registry_scorer_module",
        "aggregate_scope_key": "symbol=XAGUSD|route_session=ny_core|horizon_id=h4|source_component=registry_scorer_module",
        "repaired_proxy_event_score": -0.12,
        "repaired_proxy_event_score_source": "repair_result_source_repaired_proxy_mean",
    }
    repair_event = {
        "repaired_proxy_event_application_row_id": "app-3",
        "input_numeric_result_row_id": "numeric-3",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "horizon_id": "h16",
        "source_component": "default_off_application",
        "primitive_flag": "SPREAD_SHOCK_P95",
        "aggregate_scope_key": "symbol=USDJPY|route_session=off_core_session|horizon_id=h16|source_component=default_off_application",
    }
    exact_join = {
        "exact_broker_join_status": "EXACT_R_NOT_JOINABLE_NO_DIRECT_TRADE_CANDIDATE_OR_TICKET_IDENTIFIER",
        "exact_missing_field_proof": ["deal_ticket", "executed_entry_price"],
    }
    cost_summary = {"mean_cost_r": 0.02, "stress_cost_r": 0.05, "cost_source_rows": 3}

    avoid_spec = repaired_proxy_avoid_comparator_spec_from_event(avoid_event, 1)
    repair_task = repaired_proxy_repair_task_from_event(
        repair_event,
        exact_join,
        {"symbol_exact_r_rows": 2, "source_rows": 5},
        1,
    )
    bridge = repaired_proxy_exact_proxy_bridge_row(avoid_event, {"proxy_r_value": -0.12}, exact_join, cost_summary, 1)

    assert avoid_spec["comparator_direction"] == "avoid_or_redesign"
    assert repair_task["repair_path"] == "REBUILD_DIRECT_IDENTIFIER_FROM_SYMBOL_TIME_LIFECYCLE_OR_TRADE_RECORD"
    assert bridge["net_proxy_r"] == -0.14
    assert bridge["stress_proxy_r"] == -0.17


def test_repaired_proxy_cost_summary_uses_symbol_groups():
    rows = [
        {"source_symbol": "GBPJPY", "cost_r": 0.10},
        {"source_symbol": "GBPJPY", "cost_r": 0.20},
        {"source_symbol": "XAUUSD", "cost_r": 0.05},
    ]

    summary = repaired_proxy_summarize_cost_by_symbol(rows)

    assert summary["GBPJPY"]["cost_source_rows"] == 2
    assert summary["GBPJPY"]["mean_cost_r"] == 0.15
    assert summary["XAUUSD"]["stress_cost_r"] == 0.05


def test_repaired_proxy_execution_registry_routes_full_spec_families():
    default_spec = {
        "default_off_scorer_spec_id": "default-1",
        "input_repaired_proxy_event_application_row_id": "app-1",
        "aggregate_scope_key": "symbol=GBPJPY|route_session=tokyo_kz|horizon_id=h16|source_component=registry",
        "symbol": "GBPJPY",
        "route_session": "tokyo_kz",
        "horizon_id": "h16",
        "source_component": "registry",
        "score_value": 0.24,
        "required_guards": ["source_repair_guard"],
    }
    avoid_spec = {
        "avoid_comparator_spec_id": "avoid-1",
        "input_repaired_proxy_event_application_row_id": "app-2",
        "aggregate_scope_key": "symbol=XAGUSD|route_session=ny_core|horizon_id=h4|source_component=registry",
        "symbol": "XAGUSD",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "source_component": "registry",
        "comparator_score": -0.11,
        "required_guards": ["avoid_scope_guard"],
    }
    repair_task = {
        "repair_task_id": "repair-1",
        "input_repaired_proxy_event_application_row_id": "app-3",
        "aggregate_scope_key": "symbol=USDJPY|route_session=off_core_session|horizon_id=h16|source_component=default",
        "symbol": "USDJPY",
        "route_session": "off_core_session",
        "horizon_id": "h16",
        "source_component": "default",
    }

    registry = repaired_proxy_build_execution_registry([default_spec], [avoid_spec], [repair_task])
    default_app = repaired_proxy_execution_event_application_row(
        {
            "exact_proxy_bridge_row_id": "bridge-1",
            "input_repaired_proxy_event_application_row_id": "app-1",
            "aggregate_scope_key": default_spec["aggregate_scope_key"],
            "symbol": "GBPJPY",
            "net_proxy_r": 0.20,
            "stress_proxy_r": 0.18,
            "exact_r_status": "missing_direct_identifier",
        },
        registry,
        1,
    )
    avoid_app = repaired_proxy_execution_event_application_row(
        {
            "exact_proxy_bridge_row_id": "bridge-2",
            "input_repaired_proxy_event_application_row_id": "app-2",
            "aggregate_scope_key": avoid_spec["aggregate_scope_key"],
            "symbol": "XAGUSD",
            "net_proxy_r": -0.13,
        },
        registry,
        2,
    )

    assert len(registry["default_scope_rows"]) == 1
    assert len(registry["avoid_scope_rows"]) == 1
    assert default_app["execution_registry_status"] == "EXECUTION_REGISTRY_DEFAULT_OFF_SCORER_EVENT_REGISTERED"
    assert default_app["emitted_repaired_proxy_score"] == 0.24
    assert avoid_app["execution_registry_status"] == "EXECUTION_REGISTRY_AVOID_REDESIGN_COMPARATOR_EVENT_REGISTERED"
    assert avoid_app["research_boundary"]["production_import_path"] is False


def test_repaired_proxy_execution_registry_comparator_repair_and_market_rows():
    avoid_spec = {
        "avoid_comparator_spec_id": "avoid-2",
        "input_repaired_proxy_event_application_row_id": "app-4",
        "aggregate_scope_key": "symbol=XAUUSD|route_session=london_kz|horizon_id=h8|source_component=registry",
        "symbol": "XAUUSD",
        "route_session": "london_kz",
        "horizon_id": "h8",
        "source_component": "registry",
        "comparator_score": -0.2,
    }
    default_scope = {"default_off_scope_registry_row_id": "scope-1", "score_mean": 0.1}
    bridge = {"exact_proxy_bridge_row_id": "bridge-4", "net_proxy_r": -0.22, "stress_proxy_r": -0.25}
    repair_task = {
        "repair_task_id": "repair-2",
        "input_repaired_proxy_event_application_row_id": "app-5",
        "aggregate_scope_key": "symbol=USDJPY|route_session=off_core_session|horizon_id=h16|source_component=default",
        "symbol": "USDJPY",
        "repair_path": "ACQUIRE_OR_RECONSTRUCT_BROKER_EXECUTION_GEOMETRY",
        "missing_geometry_or_identifier_fields": ["deal_ticket"],
        "direct_search_keys_present": {},
    }
    symbol_counts = repaired_proxy_registry_symbol_counts(
        [{"symbol": "XAUUSD", "aggregate_scope_key": avoid_spec["aggregate_scope_key"], "score_value": 0.1}],
        [avoid_spec],
        [repair_task],
    )

    comparator = repaired_proxy_avoid_comparator_execution_row(avoid_spec, default_scope, bridge, 1)
    repair = repaired_proxy_repair_execution_row(repair_task, 1)
    market = repaired_proxy_market_replay_population_row(
        {
            "market_population_row_id": "market-1",
            "symbol": "XAUUSD",
            "timeframe": "M15",
            "source_path": "data/XAUUSD_M15.csv",
            "sha256": "abc",
            "row_count": 100,
        },
        symbol_counts,
        1,
    )

    assert comparator["avoid_comparator_execution_status"] == (
        "AVOID_COMPARATOR_CONFIRMED_NEGATIVE_PROXY_WITH_DEFAULT_SCOPE_CONTEXT"
    )
    assert comparator["score_minus_same_scope_default"] == -0.3
    assert repair["repair_execution_status"] == "REPAIR_EXECUTION_DIRECT_IDENTIFIER_ABSENT_AFTER_LOCAL_SOURCE_SEARCH"
    assert market["market_replay_population_action"] == "MATERIALIZE_SYMBOL_M15_REPLAY_NUMERIC_POPULATION"


def test_repaired_proxy_replay_population_probe_and_contract(tmp_path):
    source = tmp_path / "data" / "XAUUSD_M15.csv"
    source.parent.mkdir()
    source.write_text("time,open,high,low,close\n2026-01-01,1,2,0,1.5\n", encoding="utf-8")
    market_row = {
        "market_replay_population_row_id": "market-1",
        "symbol": "XAUUSD",
        "timeframe": "M15",
        "source_path": "data/XAUUSD_M15.csv",
        "source_row_count": 1,
    }
    scope_row = {
        "default_off_scope_registry_row_id": "scope-1",
        "registry_family": "default_off_repaired_proxy_scorer",
        "aggregate_scope_key": "symbol=XAUUSD|route_session=london_kz|horizon_id=h8|source_component=registry",
        "symbol": "XAUUSD",
        "route_session": "london_kz",
        "horizon_id": "h8",
        "source_component": "registry",
    }

    probe = repaired_proxy_source_probe_row(market_row, tmp_path, 1)
    contract = repaired_proxy_replay_scope_contract_row(scope_row, market_row, probe, 1)

    assert probe["source_exists"] is True
    assert probe["has_ohlc_columns"] is True
    assert contract["replay_contract_action"] == "SCOPE_READY_FOR_M15_REPLAY_NUMERIC_PASS"
    assert contract["research_boundary"]["production_import_path"] is False


def test_repaired_proxy_replay_population_repair_and_control_rows():
    repair_rows = [
        {
            "repair_execution_row_id": "repair-1",
            "repair_execution_status": "REPAIR_EXECUTION_DIRECT_IDENTIFIER_ABSENT_AFTER_LOCAL_SOURCE_SEARCH",
            "aggregate_scope_key": "symbol=USDJPY|route_session=off_core_session|horizon_id=h16|source_component=default",
            "symbol": "USDJPY",
            "route_session": "off_core_session",
            "horizon_id": "h16",
            "source_component": "default",
        },
        {
            "repair_execution_row_id": "repair-2",
            "repair_execution_status": "REPAIR_EXECUTION_DIRECT_IDENTIFIER_ABSENT_AFTER_LOCAL_SOURCE_SEARCH",
            "aggregate_scope_key": "symbol=USDJPY|route_session=off_core_session|horizon_id=h16|source_component=default",
            "symbol": "USDJPY",
            "route_session": "off_core_session",
            "horizon_id": "h16",
            "source_component": "default",
        },
    ]
    probe = {
        "source_probe_row_id": "probe-1",
        "source_exists": True,
        "has_ohlc_columns": True,
    }
    market_row = {
        "market_replay_population_row_id": "market-2",
        "symbol": "DXY",
        "timeframe": "D1",
        "source_path": "data/DXY_D1.csv",
        "source_row_count": 100,
    }

    repair_scopes = repaired_proxy_repair_scope_rows_from_executions(repair_rows)
    control = repaired_proxy_control_population_contract_row(market_row, probe, 1)

    assert len(repair_scopes) == 1
    assert repair_scopes[0]["repair_execution_rows"] == 2
    assert control["control_population_action"] == "USE_AS_CROSS_MARKET_CONTROL_POPULATION"


def test_repaired_proxy_replay_numeric_execution_streams_source_metrics(tmp_path):
    source = tmp_path / "data" / "GBPUSD_M15.csv"
    source.parent.mkdir()
    source.write_text(
        "time,open,high,low,close,tick_volume,spread\n"
        "2026-01-01 00:00:00,1.00,1.05,0.99,1.03,10,2\n"
        "2026-01-01 00:15:00,1.03,1.08,1.02,1.06,14,3\n",
        encoding="utf-8",
    )
    metric = repaired_proxy_source_numeric_metric_row(
        {
            "input_market_replay_population_row_id": "market-1",
            "symbol": "GBPUSD",
            "market_timeframe": "M15",
            "market_source_path": "data/GBPUSD_M15.csv",
        },
        tmp_path,
        1,
    )

    assert metric["numeric_metric_status"] == "SOURCE_NUMERIC_METRICS_READY"
    assert metric["parsed_ohlc_rows"] == 2
    assert metric["spread_mean"] == 2.5
    assert metric["tick_volume_mean"] == 12.0
    assert metric["close_return_pct"] == 0.06


def test_repaired_proxy_replay_numeric_execution_rows_bind_metrics():
    metric = {
        "source_numeric_metric_row_id": "metric-1",
        "numeric_metric_status": "SOURCE_NUMERIC_METRICS_READY",
        "rows_streamed": 10,
        "parsed_ohlc_rows": 10,
        "close_return_pct": 0.02,
        "mean_range_pct": 0.01,
        "mean_abs_close_change_pct": 0.005,
        "spread_mean": 2.0,
        "tick_volume_mean": 100.0,
    }
    contract = {
        "replay_scope_contract_row_id": "contract-1",
        "input_registry_scope_row_id": "scope-1",
        "registry_family": "default_off_repaired_proxy_scorer",
        "aggregate_scope_key": "symbol=GBPUSD|route_session=london_core|horizon_id=h16|source_component=registry",
        "symbol": "GBPUSD",
        "route_session": "london_core",
        "horizon_id": "h16",
        "source_component": "registry",
        "market_timeframe": "M15",
        "market_source_path": "data/GBPUSD_M15.csv",
        "replay_contract_action": "SCOPE_READY_FOR_M15_REPLAY_NUMERIC_PASS",
    }
    control = {
        "control_population_contract_row_id": "control-1",
        "symbol": "DXY",
        "timeframe": "D1",
        "source_path": "data/DXY_D1.csv",
        "control_population_action": "USE_AS_CROSS_MARKET_CONTROL_POPULATION",
    }

    replay_row = repaired_proxy_replay_numeric_event_row(contract, metric, {"score_mean": 0.3}, 1)
    control_row = repaired_proxy_control_numeric_event_row(control, metric, 1)

    assert replay_row["replay_numeric_event_status"] == "REPLAY_NUMERIC_EVENT_READY"
    assert replay_row["registry_scope_score_mean"] == 0.3
    assert replay_row["source_parsed_ohlc_rows"] == 10
    assert control_row["control_numeric_action"] == "JOIN_AS_CROSS_MARKET_NUMERIC_CONTROL"


def test_repaired_proxy_replay_score_rerun_uses_control_context():
    controls = [
        {
            "timeframe": "M15",
            "symbol": "DXY",
            "source_close_return_pct": 0.01,
            "source_mean_range_pct": 0.02,
            "source_mean_abs_close_change_pct": 0.01,
        },
        {
            "timeframe": "M15",
            "symbol": "EURUSD",
            "source_close_return_pct": 0.03,
            "source_mean_range_pct": 0.04,
            "source_mean_abs_close_change_pct": 0.02,
        },
    ]
    contexts = repaired_proxy_control_context_rows(controls)
    replay_row = {
        "registry_family": "default_off_repaired_proxy_scorer",
        "replay_numeric_event_row_id": "event-1",
        "input_registry_scope_row_id": "scope-1",
        "registry_scope_score_mean": 0.2,
        "symbol": "GBPJPY",
        "market_timeframe": "M15",
        "source_close_return_pct": 0.04,
        "source_mean_range_pct": 0.03,
        "source_mean_abs_close_change_pct": 0.02,
        "source_spread_mean": 2.0,
    }

    modifier = repaired_proxy_replay_context_modifier(replay_row, contexts[0])
    rerun = repaired_proxy_rerun_score_row(replay_row, contexts[0], 1)

    assert contexts[0]["control_return_mean"] == 0.02
    assert modifier["friction_component"] == -0.02
    assert rerun["replay_score_rerun_status"] == "REPLAY_SCORE_RERUN_DEFAULT_OFF_SCORER_EMITTED"
    assert rerun["replay_rerun_score"] is not None
    assert rerun["research_boundary"]["runtime_candidate_use_permitted"] is False


def test_repaired_proxy_replay_score_rerun_keeps_repair_context_without_scalar():
    replay_row = {
        "registry_family": "source_or_broker_geometry_repair",
        "replay_numeric_event_row_id": "event-2",
        "input_registry_scope_row_id": "repair-scope-1",
        "symbol": "USDJPY",
        "market_timeframe": "H1",
        "source_close_return_pct": 0.01,
        "source_mean_range_pct": 0.02,
        "source_mean_abs_close_change_pct": 0.01,
    }

    rerun = repaired_proxy_rerun_score_row(replay_row, None, 1)

    assert rerun["replay_rerun_score"] is None
    assert rerun["replay_score_rerun_action"] == "PRESERVE_REPAIR_SCOPE_WITH_REPLAY_NUMERIC_CONTEXT"


def test_repaired_proxy_score_bridge_rebuild_joins_scope_summary():
    score_rows = [
        {
            "aggregate_scope_key": "symbol=XAUUSD|route_session=ny_core|horizon_id=h16|source_component=registry",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "registry",
            "registry_family": "default_off_repaired_proxy_scorer",
            "replay_rerun_score": 0.2,
            "replay_context_modifier": 0.01,
            "market_timeframe": "M15",
            "market_source_path": "data/XAUUSD_M15.csv",
            "replay_score_rerun_action": "KEEP_DEFAULT_OFF_SCORER_FOR_BRANCH_LOCAL_REPLAY",
            "replay_score_rerun_status": "REPLAY_SCORE_RERUN_DEFAULT_OFF_SCORER_EMITTED",
        },
        {
            "aggregate_scope_key": "symbol=XAUUSD|route_session=ny_core|horizon_id=h16|source_component=registry",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "registry",
            "registry_family": "default_off_repaired_proxy_scorer",
            "replay_rerun_score": 0.4,
            "replay_context_modifier": 0.03,
            "market_timeframe": "H1",
            "market_source_path": "data/XAUUSD_H1.csv",
            "replay_score_rerun_action": "KEEP_DEFAULT_OFF_SCORER_FOR_BRANCH_LOCAL_REPLAY",
            "replay_score_rerun_status": "REPLAY_SCORE_RERUN_DEFAULT_OFF_SCORER_EMITTED",
        },
    ]
    bridge = {
        "exact_proxy_bridge_row_id": "bridge-1",
        "input_repaired_proxy_event_application_row_id": "app-1",
        "aggregate_scope_key": "symbol=XAUUSD|route_session=ny_core|horizon_id=h16|source_component=registry",
        "symbol": "XAUUSD",
        "net_proxy_r": 0.5,
        "exact_r_status": "missing",
    }

    summary = repaired_proxy_score_scope_summary_rows(score_rows)[0]
    rebuilt = repaired_proxy_rebuilt_bridge_row(bridge, summary, 1)

    assert summary["score_mean"] == 0.3
    assert rebuilt["rerun_scope_score_mean"] == 0.3
    assert rebuilt["score_context_net_proxy_index"] == 0.53
    assert rebuilt["score_bridge_rebuild_status"] == "SCORE_BRIDGE_REBUILT_WITH_REPLAY_SCORE_SCOPE"


def test_repaired_proxy_score_bridge_rebuild_uses_computed_scope_key_when_bridge_key_missing():
    score_rows = [
        {
            "aggregate_scope_key": (
                "symbol=NAS100|route_session=off_core_session|horizon_id=h4|"
                "source_component=registry_scorer_module"
            ),
            "symbol": "NAS100",
            "route_session": "off_core_session",
            "horizon_id": "h4",
            "source_component": "registry_scorer_module",
            "registry_family": "default_off_repaired_proxy_scorer",
            "replay_rerun_score": 0.2,
            "replay_context_modifier": 0.01,
        }
    ]
    bridge = {
        "exact_proxy_bridge_row_id": "bridge-3",
        "symbol": "NAS100",
        "route_session": "off_core_session",
        "horizon_id": "h4",
        "source_component": "registry_scorer_module",
        "net_proxy_r": 0.1,
    }

    summaries = repaired_proxy_score_scope_summary_rows(score_rows)
    scope_summary, join_method = repaired_proxy_select_scope_summary(
        bridge,
        repaired_proxy_scope_summary_join_lookups(summaries),
    )
    rebuilt = repaired_proxy_rebuilt_bridge_row(bridge, scope_summary, 1, join_method)

    assert join_method == "computed_aggregate_scope_key"
    assert rebuilt["input_score_scope_summary_row_id"] == summaries[0]["score_scope_summary_row_id"]
    assert rebuilt["score_scope_join_method"] == "computed_aggregate_scope_key"
    assert rebuilt["score_bridge_rebuild_status"] == "SCORE_BRIDGE_REBUILT_WITH_REPLAY_SCORE_SCOPE"


def test_repaired_proxy_score_bridge_rebuild_preserves_unmatched_bridge():
    rebuilt = repaired_proxy_rebuilt_bridge_row(
        {"exact_proxy_bridge_row_id": "bridge-2", "aggregate_scope_key": "missing", "net_proxy_r": -0.2},
        None,
        1,
        "no_replay_score_scope_match",
    )

    assert repaired_proxy_score_context_index(-0.2, None) == -0.2
    assert rebuilt["score_bridge_next_action"] == "PRESERVE_ORIGINAL_EXACT_PROXY_BRIDGE_AND_RECHECK_SCOPE_JOIN"


def test_repaired_proxy_score_bridge_action_packet_groups_comparator_scope():
    bridge_rows = [
        {
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "rerun_registry_family": "default_off_repaired_proxy_scorer",
            "score_bridge_rebuild_status": "SCORE_BRIDGE_REBUILT_WITH_REPLAY_SCORE_SCOPE",
            "score_bridge_next_action": "USE_SCORE_FIELDS_FOR_BRANCH_LOCAL_COMPARATOR_PACKET",
            "score_context_net_proxy_index": 0.3,
            "net_proxy_r": 0.2,
            "gross_proxy_r": 0.25,
            "input_score_scope_summary_row_id": "scope-1",
            "primitive_flag": "flag-a",
            "exact_r_status": "missing_identifier",
            "score_scope_join_method": "computed_aggregate_scope_key",
        },
        {
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "rerun_registry_family": "default_off_repaired_proxy_scorer",
            "score_bridge_rebuild_status": "SCORE_BRIDGE_REBUILT_WITH_REPLAY_SCORE_SCOPE",
            "score_bridge_next_action": "USE_SCORE_FIELDS_FOR_BRANCH_LOCAL_COMPARATOR_PACKET",
            "score_context_net_proxy_index": 0.5,
            "net_proxy_r": 0.4,
            "gross_proxy_r": 0.45,
            "input_score_scope_summary_row_id": "scope-1",
            "primitive_flag": "flag-b",
            "exact_r_status": "missing_identifier",
            "score_scope_join_method": "computed_aggregate_scope_key",
        },
    ]

    action_rows = repaired_proxy_action_scope_rows(bridge_rows)
    packets = repaired_proxy_comparator_packet_rows(action_rows)

    assert len(action_rows) == 1
    assert action_rows[0]["bridge_rows"] == 2
    assert action_rows[0]["score_context_index_mean"] == 0.4
    assert action_rows[0]["action_scope_status"] == "ACTION_SCOPE_READY_FOR_SCORE_AUGMENTED_COMPARATOR_PACKET"
    assert len(packets) == 1
    assert packets[0]["comparator_packet_status"] == "COMPARATOR_PACKET_DEFAULT_OFF_SCORER_CONTEXT_READY"


def test_repaired_proxy_score_bridge_action_packet_routes_repairs_and_missing_scope():
    repair_rows = [
        {
            "score_rebuilt_bridge_row_id": "bridge-1",
            "score_bridge_rebuild_status": "SCORE_BRIDGE_REBUILT_WITH_REPAIR_CONTEXT_SCOPE",
            "exact_r_status": "EXACT_R_NOT_JOINABLE_NO_DIRECT_TRADE_CANDIDATE_OR_TICKET_IDENTIFIER",
            "symbol": "USDJPY",
            "source_component": "default_off_application",
        },
        {
            "score_rebuilt_bridge_row_id": "bridge-2",
            "score_bridge_rebuild_status": "SCORE_BRIDGE_REBUILT_NO_REPLAY_SCORE_SCOPE_MATCH",
            "exact_r_status": "EXACT_R_NOT_JOINABLE_NO_DIRECT_TRADE_CANDIDATE_OR_TICKET_IDENTIFIER",
            "source_component": "registry_scorer_module_system",
        },
    ]

    routed = repaired_proxy_repair_routing_rows(repair_rows)

    assert [row["repair_route_family"] for row in routed] == [
        "IDENTIFIER_LINKAGE_REPAIR_REQUIRED",
        "SCOPE_IDENTITY_REPAIR_REQUIRED",
    ]
    assert routed[0]["repair_route_next_step"] == "REPAIR_IDENTIFIER_OR_GEOMETRY_FIELDS_THEN_RERUN_EXACT_PROXY_BRIDGE"
    assert routed[1]["repair_route_next_step"] == "REPAIR_SCOPE_IDENTITY_BEFORE_SCORE_JOIN"


def test_repaired_proxy_comparator_input_preserves_packet_fields():
    packet_rows = [
        {
            "comparator_packet_row_id": "packet-1",
            "input_action_scope_row_id": "scope-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "rerun_registry_family": "default_off_repaired_proxy_scorer",
            "bridge_rows": 3,
            "score_context_index_count": 3,
            "score_context_index_mean": 0.12,
            "net_proxy_r_count": 3,
            "net_proxy_r_mean": 0.1,
            "primitive_flag_count": 2,
        }
    ]

    inputs = repaired_proxy_comparator_input_rows(packet_rows)

    assert inputs[0]["input_comparator_packet_row_id"] == "packet-1"
    assert inputs[0]["comparator_input_family"] == "DEFAULT_OFF_SCORER_COMPARATOR_INPUT"
    assert inputs[0]["comparator_input_status"] == "COMPARATOR_INPUT_READY_BRANCH_LOCAL_PACKET_ONLY"
    assert inputs[0]["bridge_rows"] == 3


def test_repaired_proxy_repair_work_orders_emit_required_fields_and_rerun_plan():
    repair_rows = [
        {
            "repair_routing_row_id": "repair-1",
            "input_score_rebuilt_bridge_row_id": "bridge-1",
            "input_exact_proxy_bridge_row_id": "exact-1",
            "repair_route_family": "IDENTIFIER_LINKAGE_REPAIR_REQUIRED",
            "symbol": "USDJPY",
        },
        {
            "repair_routing_row_id": "repair-2",
            "input_score_rebuilt_bridge_row_id": "bridge-2",
            "input_exact_proxy_bridge_row_id": "exact-2",
            "repair_route_family": "SCOPE_IDENTITY_REPAIR_REQUIRED",
        },
    ]
    comparator_inputs = [{"comparator_input_row_id": "input-1"}]

    work_orders = repaired_proxy_repair_work_order_rows(repair_rows)
    plan = repaired_proxy_rerun_plan_rows(comparator_inputs, work_orders)

    assert work_orders[0]["required_fields"] == [
        "direct_trade_candidate_identifier",
        "ticket_identifier",
        "candidate_lock_metadata",
    ]
    assert work_orders[1]["required_fields"] == ["symbol", "route_session", "horizon_id", "source_component"]
    assert len(plan) == 4
    assert plan[1]["dependent_rows"] == 2


def test_repaired_proxy_repair_execution_blocks_missing_identifier_fields():
    work_orders = [
        {
            "repair_work_order_row_id": "work-1",
            "repair_route_family": "IDENTIFIER_LINKAGE_REPAIR_REQUIRED",
            "required_fields": [
                "direct_trade_candidate_identifier",
                "ticket_identifier",
                "candidate_lock_metadata",
            ],
            "symbol": "USDJPY",
        },
        {
            "repair_work_order_row_id": "work-2",
            "repair_route_family": "SCOPE_IDENTITY_REPAIR_REQUIRED",
            "required_fields": ["symbol", "route_session", "horizon_id", "source_component"],
            "source_component": "registry_scorer_module_system",
        },
    ]

    executions = repaired_proxy_repair_execution_rows(work_orders)
    gate = repaired_proxy_repair_rerun_gate_rows(executions)
    fields = repaired_proxy_repair_field_coverage_rows(executions)

    assert executions[0]["repair_execution_status"] == "REPAIR_EXECUTION_BLOCKED_MISSING_DIRECT_IDENTIFIER_FIELDS"
    assert executions[1]["repair_execution_status"] == "REPAIR_EXECUTION_BLOCKED_MISSING_SCOPE_IDENTITY_FIELDS"
    assert executions[1]["present_required_fields"] == ["source_component"]
    assert gate[0]["rerun_eligible_rows"] == 0
    assert gate[0]["rerun_gate_status"] == "EXACT_PROXY_RERUN_GATE_HELD_ALL_REPAIR_WORK_ORDERS_BLOCKED"
    assert len(fields) == 7


def test_repaired_proxy_repair_acquisition_expands_missing_fields():
    execution_rows = [
        {
            "repair_execution_row_id": "exec-1",
            "input_repair_work_order_row_id": "work-1",
            "repair_route_family": "IDENTIFIER_LINKAGE_REPAIR_REQUIRED",
            "missing_required_fields": ["ticket_identifier", "candidate_lock_metadata"],
        },
        {
            "repair_execution_row_id": "exec-2",
            "input_repair_work_order_row_id": "work-2",
            "repair_route_family": "SCOPE_IDENTITY_REPAIR_REQUIRED",
            "missing_required_fields": ["symbol", "horizon_id"],
            "source_component": "registry_scorer_module_system",
        },
    ]

    requirements = repaired_proxy_acquisition_requirement_rows(execution_rows)
    batches = repaired_proxy_acquisition_batch_rows(requirements)
    sources = repaired_proxy_source_candidate_rows(batches)

    assert len(requirements) == 4
    assert {row["missing_required_field"] for row in requirements} == {
        "ticket_identifier",
        "candidate_lock_metadata",
        "symbol",
        "horizon_id",
    }
    assert len(batches) == 4
    assert any(row["acquisition_source_family"] == "BROKER_ORDER_DEAL_TICKET_SOURCE" for row in requirements)
    assert sources


def test_repaired_proxy_repair_acquisition_lookup_requires_exact_join_for_fulfillment():
    requirements = [
        {
            "acquisition_requirement_row_id": "req-1",
            "input_repair_execution_row_id": "exec-1",
            "input_exact_proxy_bridge_row_id": "bridge-1",
            "missing_required_field": "ticket_identifier",
            "acquisition_source_family": "BROKER_ORDER_DEAL_TICKET_SOURCE",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h4",
        },
        {
            "acquisition_requirement_row_id": "req-2",
            "input_repair_execution_row_id": "exec-2",
            "input_exact_proxy_bridge_row_id": "bridge-2",
            "missing_required_field": "direct_trade_candidate_identifier",
            "acquisition_source_family": "CANDIDATE_OR_DECISION_IDENTIFIER_SOURCE",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h4",
        },
    ]
    source_candidates = [
        {
            "source_candidate_row_id": "source-1",
            "source_candidate_name": "mt5_deal_history",
            "missing_required_field": "ticket_identifier",
            "acquisition_source_family": "BROKER_ORDER_DEAL_TICKET_SOURCE",
        },
        {
            "source_candidate_row_id": "source-2",
            "source_candidate_name": "trade_record_rows",
            "missing_required_field": "direct_trade_candidate_identifier",
            "acquisition_source_family": "CANDIDATE_OR_DECISION_IDENTIFIER_SOURCE",
        },
    ]
    scan_results = {
        "mt5_deal_history": repaired_proxy_scan_source_records(
            "mt5_deal_history",
            [{"exact_proxy_bridge_row_id": "bridge-1", "deal_ticket": 12345}],
            [requirements[0]],
        ),
        "trade_record_rows": repaired_proxy_scan_source_records(
            "trade_record_rows",
            [{"symbol": "XAUUSD", "route_session": "ny_core", "horizon_id": "h4", "candidate_id": "cand-1"}],
            [requirements[1]],
        ),
    }

    lookup_rows = repaired_proxy_lookup_execution_rows(requirements, source_candidates, scan_results)
    fulfillment = repaired_proxy_lookup_field_fulfillment_rows(requirements, lookup_rows)
    readiness = repaired_proxy_lookup_repair_rerun_readiness_rows(fulfillment)

    assert lookup_rows[0]["lookup_execution_status"] == "FIELD_ACQUIRED_FROM_EXACT_SOURCE_JOIN"
    assert lookup_rows[0]["acquired_value"] == "12345"
    assert lookup_rows[1]["lookup_execution_status"] == "FIELD_OBSERVED_IN_SCOPE_MATCH_WITHOUT_ROW_KEY"
    assert fulfillment[0]["field_fulfillment_status"] == "FIELD_FULFILLED_BY_BRANCH_LOCAL_LOOKUP"
    assert fulfillment[1]["field_fulfillment_status"] == "FIELD_NOT_FULFILLED_SCOPE_MATCH_NOT_ROW_UNIQUE"
    assert readiness[0]["repair_rerun_ready"] is True
    assert readiness[1]["repair_rerun_ready"] is False


def test_repaired_proxy_repair_source_exhaustion_summarizes_unfulfilled_rows():
    field_rows = [
        {
            "input_acquisition_requirement_row_id": "req-1",
            "input_repair_execution_row_id": "exec-1",
            "missing_required_field": "symbol",
            "acquisition_source_family": "SCOPE_IDENTITY_SOURCE",
            "field_fulfillment_status": "FIELD_NOT_FULFILLED_EXACT_JOIN_FIELD_ABSENT",
        },
        {
            "input_acquisition_requirement_row_id": "req-2",
            "input_repair_execution_row_id": "exec-2",
            "missing_required_field": "ticket_identifier",
            "acquisition_source_family": "BROKER_ORDER_DEAL_TICKET_SOURCE",
            "field_fulfillment_status": "FIELD_NOT_FULFILLED_FIELD_PRESENT_WITHOUT_JOIN",
        },
    ]
    lookup_rows = [
        {
            "input_acquisition_requirement_row_id": "req-1",
            "source_candidate_name": "execution_spec_rows",
            "lookup_execution_status": "EXACT_SOURCE_JOIN_FOUND_FIELD_ABSENT",
            "source_rows_scanned": 4,
            "exact_join_rows": 1,
        },
        {
            "input_acquisition_requirement_row_id": "req-2",
            "source_candidate_name": "mt5_deal_history",
            "lookup_execution_status": "FIELD_PRESENT_IN_SOURCE_WITHOUT_REQUIREMENT_JOIN",
            "source_rows_scanned": 5,
            "source_field_present_rows": 2,
        },
    ]

    requirements = repaired_proxy_requirement_exhaustion_rows(field_rows, lookup_rows)
    families = repaired_proxy_source_family_exhaustion_rows(requirements)
    executions = repaired_proxy_repair_execution_exhaustion_rows(requirements)

    assert requirements[0]["exhaustion_class"] == "ROW_KEY_JOINED_BUT_REQUIRED_FIELD_ABSENT_IN_BRANCH_LOCAL_SOURCES"
    assert requirements[1]["exhaustion_class"] == "FIELD_EXISTS_IN_SOURCE_FAMILY_BUT_REQUIREMENT_HAS_NO_ROW_KEY_JOIN"
    assert len(families) == 2
    assert executions[0]["repair_execution_exhaustion_status"] == (
        "SCOPE_IDENTITY_REPAIR_EXHAUSTED_EXACT_JOIN_FIELDS_ABSENT"
    )
    assert executions[1]["repair_execution_exhaustion_status"] == "DIRECT_IDENTIFIER_REPAIR_EXHAUSTED_NO_ROW_KEY_JOIN"


def test_repaired_proxy_comparator_execution_routes_default_and_avoid_inputs():
    comparator_inputs = [
        {
            "comparator_input_row_id": "input-1",
            "comparator_input_family": "DEFAULT_OFF_SCORER_COMPARATOR_INPUT",
            "bridge_rows": 12,
            "score_context_index_mean": 0.12,
            "net_proxy_r_mean": 0.1,
            "symbol": "XAUUSD",
            "route_session": "ny_core",
        },
        {
            "comparator_input_row_id": "input-2",
            "comparator_input_family": "AVOID_REDESIGN_COMPARATOR_INPUT",
            "bridge_rows": 8,
            "score_context_index_mean": -0.2,
            "net_proxy_r_mean": -0.18,
            "symbol": "XAUUSD",
            "route_session": "ny_core",
        },
    ]
    gate = [{"source_exhaustion_gate_status": "EXACT_PROXY_RERUN_GATE_HELD_SOURCE_EXHAUSTION_PROVEN_CURRENT_BRANCH"}]

    executions = repaired_proxy_comparator_execution_rows(comparator_inputs, gate)
    proxy_rows = repaired_proxy_comparator_proxy_r_surface_rows(executions)
    actions = repaired_proxy_comparator_action_rows(executions)

    assert executions[0]["comparator_execution_action"] == "REGISTER_DEFAULT_OFF_SCORER_COMPARATOR"
    assert executions[1]["comparator_execution_action"] == "REGISTER_AVOID_REDESIGN_COMPARATOR"
    assert all(row["source_exhaustion_gate_status"] == gate[0]["source_exhaustion_gate_status"] for row in executions)
    assert proxy_rows[0]["proxy_r_surface_status"] == "COMPARATOR_PROXY_R_SURFACE_AVAILABLE_CURRENT_BRANCH"
    assert {row["comparator_execution_action"] for row in actions} == {
        "REGISTER_DEFAULT_OFF_SCORER_COMPARATOR",
        "REGISTER_AVOID_REDESIGN_COMPARATOR",
    }


def test_repaired_proxy_symbol_action_packet_preserves_registration_split():
    execution_rows = [
        {
            "comparator_execution_row_id": "exec-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "comparator_input_family": "DEFAULT_OFF_SCORER_COMPARATOR_INPUT",
            "comparator_execution_action": "REGISTER_DEFAULT_OFF_SCORER_COMPARATOR",
            "bridge_rows": 10,
            "net_proxy_r_mean": 0.1,
            "score_context_index_mean": 0.2,
            "source_exhaustion_gate_status": "EXACT_PROXY_RERUN_GATE_HELD_SOURCE_EXHAUSTION_PROVEN_CURRENT_BRANCH",
        },
        {
            "comparator_execution_row_id": "exec-2",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "comparator_input_family": "AVOID_REDESIGN_COMPARATOR_INPUT",
            "comparator_execution_action": "REGISTER_AVOID_REDESIGN_COMPARATOR",
            "bridge_rows": 5,
            "net_proxy_r_mean": -0.3,
            "score_context_index_mean": -0.4,
            "source_exhaustion_gate_status": "EXACT_PROXY_RERUN_GATE_HELD_SOURCE_EXHAUSTION_PROVEN_CURRENT_BRANCH",
        },
        {
            "comparator_execution_row_id": "exec-3",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "comparator_execution_action": "HOLD_DEFAULT_OFF_SCORER_CONTEXT",
            "bridge_rows": 1,
            "net_proxy_r_mean": 0.0,
            "score_context_index_mean": 0.01,
        },
    ]

    packets = repaired_proxy_symbol_action_packet_rows(execution_rows)
    registrations = repaired_proxy_symbol_comparator_registration_rows(execution_rows)
    nonregistrations = repaired_proxy_symbol_comparator_nonregistration_rows(execution_rows)
    proxy_rows = repaired_proxy_symbol_proxy_surface_rows(packets)

    assert len(packets) == 1
    assert packets[0]["comparator_execution_rows"] == 3
    assert packets[0]["registration_candidate_rows"] == 2
    assert packets[0]["symbol_action_packet_status"] == "SYMBOL_ACTION_PACKET_MIXED_DEFAULT_AND_AVOID_REGISTRATION"
    assert len(registrations) == 2
    assert {row["registration_family"] for row in registrations} == {
        "DEFAULT_OFF_SCORER_COMPARATOR_REGISTRATION",
        "AVOID_REDESIGN_COMPARATOR_REGISTRATION",
    }
    assert len(nonregistrations) == 1
    assert proxy_rows[0]["symbol_proxy_surface_status"] == (
        "SYMBOL_PROXY_R_SURFACE_MATERIALIZED_FROM_COMPARATOR_EXECUTION"
    )


def test_repaired_proxy_registration_specs_materialize_guarded_branch_local_specs():
    registration_rows = [
        {
            "comparator_registration_row_id": "reg-1",
            "input_comparator_execution_row_id": "exec-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registration_family": "DEFAULT_OFF_SCORER_COMPARATOR_REGISTRATION",
            "bridge_rows": 10,
            "net_proxy_r_mean": 0.1,
            "score_context_index_mean": 0.2,
            "source_exhaustion_gate_status": "EXACT_PROXY_RERUN_GATE_HELD_SOURCE_EXHAUSTION_PROVEN_CURRENT_BRANCH",
        },
        {
            "comparator_registration_row_id": "reg-2",
            "input_comparator_execution_row_id": "exec-2",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "registration_family": "AVOID_REDESIGN_COMPARATOR_REGISTRATION",
            "bridge_rows": 5,
            "net_proxy_r_mean": -0.3,
            "score_context_index_mean": -0.4,
            "source_exhaustion_gate_status": "EXACT_PROXY_RERUN_GATE_HELD_SOURCE_EXHAUSTION_PROVEN_CURRENT_BRANCH",
        },
    ]
    nonregistration_rows = [
        {
            "comparator_nonregistration_row_id": "nonreg-1",
            "input_comparator_execution_row_id": "exec-3",
            "comparator_execution_action": "HOLD_DEFAULT_OFF_SCORER_CONTEXT",
            "bridge_rows": 1,
        }
    ]

    specs = repaired_proxy_registration_spec_rows(registration_rows)
    guards = repaired_proxy_registration_runtime_guard_rows(specs)
    nonreg = repaired_proxy_registration_nonregistration_context_rows(nonregistration_rows)

    assert [row["registration_spec_family"] for row in specs] == [
        "default_off_repaired_proxy_scorer_comparator",
        "avoid_redesign_repaired_proxy_comparator",
    ]
    assert specs[0]["registration_parameters"]["score_context_index_min"] == 0.05
    assert specs[1]["registration_parameters"]["net_proxy_r_max"] == 0.0
    assert guards[0]["guard_conditions"]["production_import_path"] is False
    assert guards[0]["runtime_guard_status"] == "BRANCH_LOCAL_REGISTRATION_GUARD_MATERIALIZED"
    assert nonreg[0]["nonregistration_context_status"] == "NONREGISTRATION_CONTEXT_PRESERVED_FOR_BRANCH_LOCAL_REVIEW"


def test_repaired_proxy_runtime_candidate_bundle_materializes_guard_checked_rows():
    specs = [
        {
            "registration_spec_row_id": "spec-1",
            "input_comparator_registration_row_id": "reg-1",
            "input_comparator_execution_row_id": "exec-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registration_family": "DEFAULT_OFF_SCORER_COMPARATOR_REGISTRATION",
            "registration_spec_family": "default_off_repaired_proxy_scorer_comparator",
            "bridge_rows": 10,
            "net_proxy_r_mean": 0.1,
            "score_context_index_mean": 0.2,
            "source_exhaustion_gate_status": "EXACT_PROXY_RERUN_GATE_HELD_SOURCE_EXHAUSTION_PROVEN_CURRENT_BRANCH",
            "registration_parameters": {"score_context_index_min": 0.05, "net_proxy_r_min": 0.0},
            "required_guards": ["source_exhaustion_gate_attached", "exact_proxy_repair_rerun_not_required"],
        },
        {
            "registration_spec_row_id": "spec-2",
            "input_comparator_registration_row_id": "reg-2",
            "input_comparator_execution_row_id": "exec-2",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "registration_family": "AVOID_REDESIGN_COMPARATOR_REGISTRATION",
            "registration_spec_family": "avoid_redesign_repaired_proxy_comparator",
            "bridge_rows": 5,
            "net_proxy_r_mean": -0.3,
            "score_context_index_mean": -0.4,
            "source_exhaustion_gate_status": "EXACT_PROXY_RERUN_GATE_HELD_SOURCE_EXHAUSTION_PROVEN_CURRENT_BRANCH",
            "registration_parameters": {"score_context_index_max": -0.05, "net_proxy_r_max": 0.0},
            "required_guards": ["source_exhaustion_gate_attached", "exact_proxy_repair_rerun_not_required"],
        },
    ]
    guards = [
        {
            "runtime_guard_row_id": "guard-1",
            "input_registration_spec_row_id": "spec-1",
            "guard_conditions": {
                "production_import_path": False,
                "order_risk_prompt_safety_mt5_mutation": False,
                "source_exhaustion_gate_status": "EXACT_PROXY_RERUN_GATE_HELD_SOURCE_EXHAUSTION_PROVEN_CURRENT_BRANCH",
                "exact_proxy_repair_rerun_required": False,
            },
        },
        {
            "runtime_guard_row_id": "guard-2",
            "input_registration_spec_row_id": "spec-2",
            "guard_conditions": {
                "production_import_path": False,
                "order_risk_prompt_safety_mt5_mutation": False,
                "source_exhaustion_gate_status": "EXACT_PROXY_RERUN_GATE_HELD_SOURCE_EXHAUSTION_PROVEN_CURRENT_BRANCH",
                "exact_proxy_repair_rerun_required": False,
            },
        },
    ]
    nonregistration_rows = [
        {
            "nonregistration_context_row_id": "nonreg-1",
            "input_comparator_nonregistration_row_id": "nonreg-input-1",
            "input_comparator_execution_row_id": "exec-3",
            "comparator_execution_action": "HOLD_DEFAULT_OFF_SCORER_CONTEXT",
            "bridge_rows": 2,
        }
    ]

    candidates = repaired_proxy_runtime_candidate_rows(specs)
    guard_checks = repaired_proxy_runtime_candidate_guard_check_rows(candidates, guards)
    bundles = repaired_proxy_symbol_candidate_bundle_rows(candidates, guard_checks)
    nonreg_review = repaired_proxy_runtime_candidate_nonregistration_review_rows(nonregistration_rows)

    assert [row["runtime_candidate_kind"] for row in candidates] == [
        "DEFAULT_OFF_SCORER",
        "AVOID_REDESIGN_COMPARATOR",
    ]
    assert candidates[0]["production_import_path"] is False
    assert all(row["guard_check_passed"] is True for row in guard_checks)
    assert {row["runtime_candidate_family"] for row in bundles} == {
        "branch_local_default_off_repaired_proxy_scorer_candidate",
        "branch_local_avoid_redesign_repaired_proxy_comparator_candidate",
    }
    assert sum(row["candidate_rows"] for row in bundles) == 2
    assert nonreg_review[0]["review_action"] == "RETAIN_CONTEXT_FOR_BRANCH_LOCAL_THRESHOLD_REVIEW"


def test_repaired_proxy_runtime_candidate_registry_executes_branch_local_probes():
    candidates = [
        {
            "runtime_candidate_row_id": "candidate-1",
            "input_registration_spec_row_id": "spec-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "runtime_candidate_family": "branch_local_default_off_repaired_proxy_scorer_candidate",
            "runtime_candidate_kind": "DEFAULT_OFF_SCORER",
            "branch_local_parameters": {"score_context_index_min": 0.05, "net_proxy_r_min": 0.0},
            "bridge_rows": 10,
            "net_proxy_r_mean": 0.1,
            "score_context_index_mean": 0.2,
        },
        {
            "runtime_candidate_row_id": "candidate-2",
            "input_registration_spec_row_id": "spec-2",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "runtime_candidate_family": "branch_local_avoid_redesign_repaired_proxy_comparator_candidate",
            "runtime_candidate_kind": "AVOID_REDESIGN_COMPARATOR",
            "branch_local_parameters": {"score_context_index_max": -0.05, "net_proxy_r_max": 0.0},
            "bridge_rows": 5,
            "net_proxy_r_mean": -0.3,
            "score_context_index_mean": -0.4,
        },
    ]
    guards = [
        {
            "guard_check_row_id": "guard-1",
            "input_runtime_candidate_row_id": "candidate-1",
            "guard_check_passed": True,
            "guard_check_status": "RUNTIME_CANDIDATE_GUARD_CHECK_PASSED_BRANCH_LOCAL",
        },
        {
            "guard_check_row_id": "guard-2",
            "input_runtime_candidate_row_id": "candidate-2",
            "guard_check_passed": True,
            "guard_check_status": "RUNTIME_CANDIDATE_GUARD_CHECK_PASSED_BRANCH_LOCAL",
        },
    ]

    registry = repaired_proxy_registry_module_rows(candidates, guards)
    probes = repaired_proxy_registry_event_probe_rows(registry)
    rollups = repaired_proxy_symbol_registry_rollup_rows(registry, probes)
    mismatch = repaired_proxy_evaluate_runtime_candidate_event(registry[0], {"symbol": "USDJPY"})

    assert [row["registry_entry_status"] for row in registry] == [
        "RUNTIME_CANDIDATE_REGISTRY_ENTRY_REGISTERED_BRANCH_LOCAL",
        "RUNTIME_CANDIDATE_REGISTRY_ENTRY_REGISTERED_BRANCH_LOCAL",
    ]
    assert probes[0]["probe_event_outcome"] == "DEFAULT_OFF_SCORER_EVENT_ACCEPTED_BRANCH_LOCAL"
    assert probes[1]["probe_event_outcome"] == "AVOID_REDESIGN_COMPARATOR_EVENT_TRIGGERED_BRANCH_LOCAL"
    assert mismatch["candidate_event_outcome"] == "RUNTIME_CANDIDATE_EVENT_SCOPE_MISMATCH"
    assert sum(row["registry_module_rows"] for row in rollups) == 2


def test_repaired_proxy_runtime_replay_execution_preserves_replay_denominator():
    registry = [
        {
            "registry_module_row_id": "registry-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "runtime_candidate_family": "branch_local_default_off_repaired_proxy_scorer_candidate",
            "runtime_candidate_kind": "DEFAULT_OFF_SCORER",
            "branch_local_parameters": {"score_context_index_min": 0.05, "net_proxy_r_min": 0.0},
            "registry_entry_status": "RUNTIME_CANDIDATE_REGISTRY_ENTRY_REGISTERED_BRANCH_LOCAL",
        },
        {
            "registry_module_row_id": "registry-2",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "runtime_candidate_family": "branch_local_avoid_redesign_repaired_proxy_comparator_candidate",
            "runtime_candidate_kind": "AVOID_REDESIGN_COMPARATOR",
            "branch_local_parameters": {"score_context_index_max": -0.05, "net_proxy_r_max": 0.0},
            "registry_entry_status": "RUNTIME_CANDIDATE_REGISTRY_ENTRY_REGISTERED_BRANCH_LOCAL",
        },
    ]
    score_rows = [
        {
            "replay_score_rerun_row_id": "score-1",
            "registry_family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "replay_rerun_score": 0.2,
        },
        {
            "replay_score_rerun_row_id": "score-2",
            "registry_family": "avoid_redesign_repaired_proxy_comparator",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "replay_rerun_score": -0.3,
        },
        {
            "replay_score_rerun_row_id": "score-3",
            "registry_family": "source_or_broker_geometry_repair",
            "symbol": "XAUUSD",
            "source_component": "market_gap_code",
        },
    ]

    executions = repaired_proxy_replay_registry_execution_rows(score_rows, registry)
    matches = repaired_proxy_replay_module_match_rows(score_rows, registry)
    rollups = repaired_proxy_replay_symbol_outcome_rows(executions)

    assert len(executions) == 3
    assert executions[0]["replay_registry_execution_status"] == (
        "REPLAY_REGISTRY_EXECUTION_CANDIDATE_TRIGGERED_BRANCH_LOCAL"
    )
    assert executions[2]["replay_registry_execution_status"] == (
        "REPLAY_REGISTRY_EXECUTION_REPAIR_CONTEXT_NO_RUNTIME_CANDIDATE"
    )
    assert [row["module_event_outcome"] for row in matches] == [
        "DEFAULT_OFF_SCORER_EVENT_ACCEPTED_BRANCH_LOCAL",
        "AVOID_REDESIGN_COMPARATOR_EVENT_TRIGGERED_BRANCH_LOCAL",
    ]
    assert sum(row["replay_registry_execution_rows"] for row in rollups) == 3


def test_repaired_proxy_runtime_replay_recommendation_routes_signal_and_review_rows():
    execution_rows = [
        {
            "replay_registry_execution_row_id": "exec-1",
            "replay_registry_execution_status": "REPLAY_REGISTRY_EXECUTION_CANDIDATE_TRIGGERED_BRANCH_LOCAL",
            "registry_family": "default_off_repaired_proxy_scorer",
            "runtime_candidate_family": "branch_local_default_off_repaired_proxy_scorer_candidate",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "replay_rerun_score": 0.2,
            "matching_registry_module_rows": 1,
        },
        {
            "replay_registry_execution_row_id": "exec-2",
            "replay_registry_execution_status": "REPLAY_REGISTRY_EXECUTION_NO_MATCHING_RUNTIME_CANDIDATE",
            "registry_family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h32",
            "source_component": "shadow_source_guard",
            "replay_rerun_score": 0.1,
        },
    ]
    symbol_rows = [
        {
            "replay_symbol_outcome_row_id": "symbol-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "registry_family": "default_off_repaired_proxy_scorer",
            "replay_registry_execution_rows": 1,
            "matched_registry_module_rows": 1,
        },
        {
            "replay_symbol_outcome_row_id": "symbol-2",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h32",
            "registry_family": "default_off_repaired_proxy_scorer",
            "replay_registry_execution_rows": 1,
            "matched_registry_module_rows": 0,
        },
    ]

    route_rows = repaired_proxy_replay_signal_route_rows(execution_rows)
    symbol_recs = repaired_proxy_symbol_recommendation_rows(symbol_rows, route_rows)
    unmatched = repaired_proxy_unmatched_scope_review_rows(route_rows)

    assert [row["replay_signal_route_class"] for row in route_rows] == [
        "DEFAULT_OFF_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL",
        "REPLAY_SCOPE_UNMATCHED_REVIEW_BRANCH_LOCAL",
    ]
    assert symbol_recs[0]["symbol_recommendation"] == (
        "BRANCH_LOCAL_DEFAULT_OFF_REPLAY_SIGNAL_RECOMMENDED_FOR_COMPARISON"
    )
    assert symbol_recs[1]["symbol_recommendation"] == "BRANCH_LOCAL_REPLAY_SCOPE_MATCH_REVIEW_REQUIRED"
    assert len(unmatched) == 1


def test_repaired_proxy_runtime_replay_inventory_alignment_sanitizes_unified_inventory():
    signal_rows = [
        {
            "replay_signal_route_row_id": "route-1",
            "replay_signal_route_class": "DEFAULT_OFF_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        },
        {
            "replay_signal_route_row_id": "route-2",
            "replay_signal_route_class": "REPLAY_SCOPE_UNMATCHED_REVIEW_BRANCH_LOCAL",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h32",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        },
    ]
    unified_rows = [
        {
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "unified_decision_group": "IMPLEMENT",
            "unified_action_class": "IMPLEMENT_DEFAULT_OFF_SCORER_CANDIDATE",
        }
    ]

    alignment = repaired_proxy_signal_inventory_alignment_rows(signal_rows, unified_rows)
    symbol_rows = repaired_proxy_symbol_inventory_alignment_rows(alignment)

    assert alignment[0]["inventory_alignment_class"] == "INVENTORY_ALIGNMENT_EXACT_SCOPE_COMPATIBLE"
    assert alignment[0]["inventory_decision_group_counts"] == {"IMPLEMENT": 1}
    assert alignment[1]["inventory_alignment_class"] == "INVENTORY_ALIGNMENT_REPLAY_SCOPE_UNMATCHED_REVIEW"
    assert sum(row["signal_inventory_alignment_rows"] for row in symbol_rows) == 2


def test_repaired_proxy_runtime_replay_advancement_splits_represented_conflict_and_unmatched():
    alignment_rows = [
        {
            "signal_inventory_alignment_row_id": "align-1",
            "replay_signal_route_class": "DEFAULT_OFF_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL",
            "inventory_alignment_class": "INVENTORY_ALIGNMENT_EXACT_SCOPE_COMPATIBLE",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        },
        {
            "signal_inventory_alignment_row_id": "align-2",
            "replay_signal_route_class": "AVOID_REDESIGN_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL",
            "inventory_alignment_class": "INVENTORY_ALIGNMENT_EXACT_SCOPE_PRESENT_DIFFERENT_ACTION",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "registry_family": "avoid_redesign_repaired_proxy_comparator",
            "inventory_decision_group_counts": {"SCORE_WITH_CONTROL": 1},
            "inventory_action_classes": ["IMPLEMENT_DEFAULT_OFF_SCORER_CANDIDATE"],
        },
        {
            "signal_inventory_alignment_row_id": "align-3",
            "replay_signal_route_class": "REPLAY_SCOPE_UNMATCHED_REVIEW_BRANCH_LOCAL",
            "inventory_alignment_class": "INVENTORY_ALIGNMENT_REPLAY_SCOPE_UNMATCHED_REVIEW",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h32",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        },
    ]

    decisions = repaired_proxy_advancement_decision_rows(alignment_rows)
    represented = repaired_proxy_represented_surface_rows(decisions)
    conflicts = repaired_proxy_action_conflict_review_rows(decisions)
    unmatched = repaired_proxy_unmatched_scope_advancement_rows(decisions)
    symbol_rows = repaired_proxy_symbol_advancement_rows(decisions)

    assert [row["advancement_family"] for row in decisions] == [
        "REPRESENTED_SIGNAL_ADVANCES",
        "EXACT_SCOPE_ACTION_CONFLICT_REVIEW",
        "UNMATCHED_SCOPE_REVIEW",
    ]
    assert represented[0]["represented_surface_status"] == "REPRESENTED_REPLAY_SURFACE_READY_FOR_COMPARISON_PACKET"
    assert conflicts[0]["action_conflict_review_status"] == "ACTION_CONFLICT_REVIEW_REQUIRED_BEFORE_COMPARISON_PACKET"
    assert unmatched[0]["unmatched_scope_advancement_status"] == "SCOPE_MATCH_REVIEW_REQUIRED_BEFORE_COMPARISON_PACKET"
    assert sum(row["advancement_decision_rows"] for row in symbol_rows) == 3


def test_repaired_proxy_runtime_replay_comparison_packet_materializes_sidecars():
    represented = [
        {
            "represented_surface_row_id": "represented-1",
            "input_advancement_decision_row_id": "decision-1",
            "replay_signal_route_class": "DEFAULT_OFF_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL",
            "inventory_alignment_class": "INVENTORY_ALIGNMENT_EXACT_SCOPE_COMPATIBLE",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        }
    ]
    conflicts = [
        {
            "action_conflict_review_row_id": "conflict-1",
            "input_advancement_decision_row_id": "decision-2",
            "replay_signal_route_class": "AVOID_REDESIGN_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL",
            "inventory_alignment_class": "INVENTORY_ALIGNMENT_EXACT_SCOPE_PRESENT_DIFFERENT_ACTION",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "registry_family": "avoid_redesign_repaired_proxy_comparator",
            "inventory_decision_group_counts": {"SCORE_WITH_CONTROL": 1},
        }
    ]
    unmatched = [
        {
            "unmatched_scope_advancement_row_id": "unmatched-1",
            "input_advancement_decision_row_id": "decision-3",
            "replay_signal_route_class": "REPLAY_SCOPE_UNMATCHED_REVIEW_BRANCH_LOCAL",
            "inventory_alignment_class": "INVENTORY_ALIGNMENT_REPLAY_SCOPE_UNMATCHED_REVIEW",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h32",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        }
    ]

    packet = repaired_proxy_comparison_packet_rows(represented)
    sidecars = repaired_proxy_review_sidecar_rows(conflicts, unmatched)
    scopes = repaired_proxy_comparison_scope_rows(packet, sidecars)
    system_rows = repaired_proxy_system_comparison_rows(packet, sidecars, scopes)

    assert packet[0]["comparison_packet_role"] == "DEFAULT_OFF_REPLAY_SIGNAL_COMPARISON_INPUT"
    assert [row["review_sidecar_family"] for row in sidecars] == [
        "ACTION_CONFLICT_REVIEW_SIDECAR",
        "UNMATCHED_SCOPE_REVIEW_SIDECAR",
    ]
    assert sum(row["comparison_packet_rows"] for row in scopes) == 1
    assert sum(row["review_sidecar_rows"] for row in scopes) == 2
    assert system_rows[0]["comparison_packet_rows"] == 1


def test_repaired_proxy_runtime_replay_comparison_summary_attaches_sidecars():
    packet_rows = [
        {
            "comparison_packet_row_id": "packet-1",
            "comparison_packet_role": "DEFAULT_OFF_REPLAY_SIGNAL_COMPARISON_INPUT",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        }
    ]
    sidecar_rows = [
        {
            "comparison_review_sidecar_row_id": "sidecar-1",
            "review_sidecar_family": "ACTION_CONFLICT_REVIEW_SIDECAR",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        },
        {
            "comparison_review_sidecar_row_id": "sidecar-2",
            "review_sidecar_family": "UNMATCHED_SCOPE_REVIEW_SIDECAR",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h32",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        },
    ]

    scope_rows = repaired_proxy_summary_scope_comparison_rows(packet_rows, sidecar_rows)
    signal_rows = repaired_proxy_summary_signal_comparison_rows(packet_rows, sidecar_rows)
    attachments = repaired_proxy_summary_sidecar_attachment_rows(packet_rows, sidecar_rows)
    system_rows = repaired_proxy_summary_system_rows(scope_rows, signal_rows, attachments)

    assert scope_rows[0]["scope_comparison_class"] == "SCOPE_COMPARISON_DEFAULT_OFF_SIGNAL_ONLY"
    assert any(row["scope_comparison_class"] == "SCOPE_COMPARISON_SIDECAR_ONLY_REVIEW" for row in scope_rows)
    assert signal_rows[0]["signal_count_balance"] == "DEFAULT_OFF_REPRESENTED_COUNT_DOMINANT"
    assert [row["sidecar_attachment_class"] for row in attachments] == [
        "SIDECAR_ATTACHED_TO_REPRESENTED_SCOPE",
        "SIDECAR_ONLY_SCOPE_REVIEW",
    ]
    assert system_rows[0]["sidecar_attachment_rows"] == 2


def test_repaired_proxy_runtime_replay_sidecar_aware_score_damps_attached_sidecars():
    packet_rows = [
        {
            "comparison_packet_row_id": "packet-1",
            "comparison_packet_role": "DEFAULT_OFF_REPLAY_SIGNAL_COMPARISON_INPUT",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        }
    ]
    scope_rows = [
        {
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "registry_family": "default_off_repaired_proxy_scorer",
            "scope_comparison_class": "SCOPE_COMPARISON_DEFAULT_OFF_SIGNAL_ONLY",
            "comparison_packet_rows": 1,
            "review_sidecar_rows": 1,
        }
    ]
    signal_rows = [
        {
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "signal_count_balance": "DEFAULT_OFF_REPRESENTED_COUNT_DOMINANT",
        }
    ]
    attachments = [
        {
            "sidecar_attachment_row_id": "attach-1",
            "comparison_review_sidecar_row_id": "sidecar-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
            "sidecar_attachment_class": "SIDECAR_ATTACHED_TO_REPRESENTED_SCOPE",
        }
    ]

    packet_scores = repaired_proxy_packet_score_rows(packet_rows, scope_rows, signal_rows)
    scope_scores = repaired_proxy_scope_score_rows(packet_scores, scope_rows)
    impacts = repaired_proxy_sidecar_score_impact_rows(attachments, scope_rows)
    system_rows = repaired_proxy_system_score_rows(packet_scores, scope_scores, impacts)

    assert packet_scores[0]["sidecar_aware_comparison_score"] == 0.5
    assert packet_scores[0]["score_usage"] == "BRANCH_LOCAL_COMPARISON_PRIORITY_ONLY"
    assert scope_scores[0]["sidecar_aware_score_mean"] == 0.5
    assert impacts[0]["sidecar_score_impact_class"] == "SIDECAR_DAMPS_REPRESENTED_SCOPE_SCORE"
    assert system_rows[0]["packet_score_rows"] == 1


def test_repaired_proxy_runtime_replay_sidecar_aware_decision_routes_scores_and_sidecars():
    packet_scores = [
        {
            "packet_score_row_id": "score-1",
            "input_comparison_packet_row_id": "packet-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
            "comparison_packet_role": "DEFAULT_OFF_REPLAY_SIGNAL_COMPARISON_INPUT",
            "sidecar_aware_comparison_score": 0.8,
            "sidecar_aware_score_class": "COMPARISON_SCORE_HIGH_CLEAR",
            "scope_review_sidecar_rows": 0,
        }
    ]
    scope_scores = [
        {
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "registry_family": "default_off_repaired_proxy_scorer",
            "scope_comparison_class": "SCOPE_COMPARISON_DEFAULT_OFF_SIGNAL_ONLY",
            "comparison_packet_rows": 1,
            "review_sidecar_rows": 0,
        }
    ]
    sidecar_impacts = [
        {
            "sidecar_score_impact_row_id": "impact-1",
            "input_sidecar_attachment_row_id": "attach-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h32",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
            "sidecar_score_impact_class": "SIDECAR_HELD_FOR_SCOPE_REVIEW",
        }
    ]

    packet_decisions = repaired_proxy_packet_decision_rows(packet_scores)
    scope_decisions = repaired_proxy_scope_decision_rows(packet_decisions, scope_scores)
    sidecar_decisions = repaired_proxy_sidecar_decision_rows(sidecar_impacts)
    system_rows = repaired_proxy_system_decision_rows(packet_decisions, scope_decisions, sidecar_decisions)

    assert packet_decisions[0]["packet_decision_family"] == "PACKET_DECISION_CLEAR_ADVANCE"
    assert scope_decisions[0]["scope_decision_class"] == "SCOPE_DECISION_HAS_CLEAR_ADVANCE_PACKET"
    assert sidecar_decisions[0]["sidecar_decision_family"] == "SIDECAR_DECISION_SCOPE_REVIEW_REQUIREMENT"
    assert system_rows[0]["packet_decision_rows"] == 1


def test_repaired_proxy_runtime_replay_decision_bundle_preserves_decision_denominators():
    packet_decisions = [
        {
            "packet_decision_row_id": "packet-decision-1",
            "packet_decision_family": "PACKET_DECISION_CLEAR_ADVANCE",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        }
    ]
    scope_decisions = [
        {
            "scope_decision_row_id": "scope-decision-1",
            "scope_decision_class": "SCOPE_DECISION_HAS_CLEAR_ADVANCE_PACKET",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "registry_family": "default_off_repaired_proxy_scorer",
        }
    ]
    sidecar_decisions = [
        {
            "sidecar_decision_row_id": "sidecar-decision-1",
            "sidecar_decision_family": "SIDECAR_DECISION_SCORE_DAMPER",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        }
    ]

    packet_bundle = repaired_proxy_final_packet_bundle_rows(packet_decisions)
    scope_bundle = repaired_proxy_final_scope_bundle_rows(scope_decisions)
    sidecar_bundle = repaired_proxy_final_sidecar_bundle_rows(sidecar_decisions)
    system_rows = repaired_proxy_system_bundle_rows(packet_bundle, scope_bundle, sidecar_bundle)

    assert packet_bundle[0]["final_packet_bundle_class"] == "FINAL_BUNDLE_PACKET_CLEAR_ADVANCE"
    assert scope_bundle[0]["final_scope_bundle_class"] == "FINAL_BUNDLE_SCOPE_CLEAR_ADVANCE"
    assert sidecar_bundle[0]["final_sidecar_bundle_class"] == "FINAL_BUNDLE_SIDECAR_SCORE_DAMPER"
    assert system_rows[0]["final_packet_bundle_rows"] == 1


def test_repaired_proxy_runtime_replay_decision_application_preserves_bundle_denominators():
    packet_bundle = [
        {
            "final_packet_bundle_row_id": "packet-bundle-1",
            "final_packet_bundle_class": "FINAL_BUNDLE_PACKET_CLEAR_ADVANCE",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        }
    ]
    scope_bundle = [
        {
            "final_scope_bundle_row_id": "scope-bundle-1",
            "final_scope_bundle_class": "FINAL_BUNDLE_SCOPE_CLEAR_ADVANCE",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "registry_family": "default_off_repaired_proxy_scorer",
            "comparison_packet_rows": 1,
            "review_sidecar_rows": 0,
        }
    ]
    sidecar_bundle = [
        {
            "final_sidecar_bundle_row_id": "sidecar-bundle-1",
            "final_sidecar_bundle_class": "FINAL_BUNDLE_SIDECAR_SCOPE_REVIEW_REQUIREMENT",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h32",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        }
    ]

    packet_apps = repaired_proxy_packet_application_rows(packet_bundle)
    scope_apps = repaired_proxy_scope_application_rows(scope_bundle, packet_apps)
    sidecar_apps = repaired_proxy_sidecar_application_rows(sidecar_bundle)
    system_apps = repaired_proxy_system_application_rows(packet_apps, scope_apps, sidecar_apps)

    assert packet_apps[0]["packet_application_family"] == "PACKET_APPLICATION_CLEAR_ADVANCE"
    assert scope_apps[0]["scope_application_family"] == "SCOPE_APPLICATION_CLEAR_ADVANCE"
    assert sidecar_apps[0]["sidecar_application_family"] == "SIDECAR_APPLICATION_SCOPE_REVIEW_REQUIREMENT"
    assert system_apps[0]["packet_application_rows"] == 1


def test_repaired_proxy_runtime_replay_decision_application_comparison_links_packets_to_review_scopes():
    packet_apps = [
        {
            "packet_application_row_id": "packet-app-1",
            "packet_application_family": "PACKET_APPLICATION_CLEAR_ADVANCE",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        },
        {
            "packet_application_row_id": "packet-app-2",
            "packet_application_family": "PACKET_APPLICATION_REVIEW_HOLD",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "registry_family": "avoid_redesign_repaired_proxy_comparator",
        },
    ]
    scope_apps = [
        {
            "scope_application_row_id": "scope-app-1",
            "scope_application_family": "SCOPE_APPLICATION_CLEAR_ADVANCE",
            "scope_application_action": "APPLY_SCOPE_AS_CLEAR_BRANCH_LOCAL_COMPARISON_SCOPE",
            "scope_comparison_class": "SCOPE_COMPARISON_DEFAULT_OFF_SIGNAL_ONLY",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "registry_family": "default_off_repaired_proxy_scorer",
        },
        {
            "scope_application_row_id": "scope-app-2",
            "scope_application_family": "SCOPE_APPLICATION_REVIEW_HOLD",
            "scope_application_action": "HOLD_SCOPE_FOR_PACKET_OR_SIDECAR_REVIEW",
            "scope_comparison_class": "SCOPE_COMPARISON_REPRESENTED_WITH_REVIEW",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "horizon_id": "h32",
            "registry_family": "avoid_redesign_repaired_proxy_comparator",
        },
    ]
    sidecar_apps = [
        {
            "sidecar_application_row_id": "sidecar-app-1",
            "sidecar_application_family": "SIDECAR_APPLICATION_SCOPE_REVIEW_REQUIREMENT",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "registry_family": "avoid_redesign_repaired_proxy_comparator",
        }
    ]

    scope_rows = repaired_proxy_scope_review_comparison_rows(scope_apps, packet_apps, sidecar_apps)
    packet_rows = repaired_proxy_packet_scope_comparison_rows(packet_apps, scope_rows)
    sidecar_rows = repaired_proxy_sidecar_scope_comparison_rows(sidecar_apps, scope_rows)
    advance_rows = repaired_proxy_advance_packet_rows(packet_rows)
    held_rows = repaired_proxy_held_review_scope_rows(scope_rows)
    system_rows = repaired_proxy_system_review_comparison_rows(
        scope_rows,
        packet_rows,
        sidecar_rows,
        advance_rows,
        held_rows,
    )

    assert scope_rows[0]["scope_review_comparison_class"] == "SCOPE_REVIEW_COMPARISON_CLEAR_ADVANCE_READY"
    assert scope_rows[1]["scope_review_comparison_class"] == "SCOPE_REVIEW_COMPARISON_HELD_SCOPE_WITH_HELD_PACKETS"
    assert packet_rows[0]["packet_scope_comparison_family"] == "PACKET_SCOPE_COMPARISON_ADVANCE_PACKET_WITH_ADVANCE_SCOPE"
    assert packet_rows[1]["packet_scope_comparison_family"] == "PACKET_SCOPE_COMPARISON_HELD_PACKET_WITH_HELD_SCOPE"
    assert sidecar_rows[0]["sidecar_scope_comparison_family"] == (
        "SIDECAR_SCOPE_COMPARISON_REVIEW_REQUIREMENT_ON_HELD_SCOPE"
    )
    assert len(advance_rows) == 1
    assert len(held_rows) == 1
    assert system_rows[0]["advance_packet_rows"] == 1


def test_repaired_proxy_runtime_replay_ranked_packet_orders_all_advance_rows():
    advance_packets = [
        {
            "advance_packet_row_id": "advance-1",
            "packet_scope_comparison_row_id": "packet-scope-1",
            "packet_application_family": "PACKET_APPLICATION_CLEAR_ADVANCE",
            "sidecar_aware_comparison_score": 0.9,
            "scope_review_comparison_class": "SCOPE_REVIEW_COMPARISON_CLEAR_ADVANCE_READY",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        },
        {
            "advance_packet_row_id": "advance-2",
            "packet_scope_comparison_row_id": "packet-scope-2",
            "packet_application_family": "PACKET_APPLICATION_CONTEXT_ADVANCE",
            "sidecar_aware_comparison_score": 0.7,
            "scope_review_comparison_class": "SCOPE_REVIEW_COMPARISON_CONTEXT_ADVANCE_WITH_ATTACHED_REVIEW_CONTEXT",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "registry_family": "avoid_redesign_repaired_proxy_comparator",
        },
    ]
    held_scopes = [
        {
            "held_review_scope_row_id": "held-1",
            "scope_review_comparison_row_id": "scope-review-1",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "horizon_id": "h16",
            "registry_family": "avoid_redesign_repaired_proxy_comparator",
            "scope_review_comparison_class": "SCOPE_REVIEW_COMPARISON_HELD_SCOPE_WITH_HELD_PACKETS",
            "held_packet_rows": 4,
            "sidecar_scope_requirement_rows": 10,
        }
    ]

    held_context = repaired_proxy_held_scope_context_rows(held_scopes)
    ranked = repaired_proxy_ranked_advance_packet_rows(advance_packets, held_context)
    next_packet = repaired_proxy_next_branch_local_packet_rows(ranked)
    system_rows = repaired_proxy_system_ranked_packet_rows(ranked, held_context, next_packet)

    assert [row["packet_rank"] for row in ranked] == [1, 2]
    assert ranked[0]["input_advance_packet_row_id"] == "advance-1"
    assert ranked[1]["coarse_held_scope_rows"] == 1
    assert len(next_packet) == 2
    assert system_rows[0]["ranked_advance_packet_rows"] == 2


def test_repaired_proxy_runtime_replay_implementation_steps_map_ranked_packets_to_families():
    next_packets = [
        {
            "next_branch_local_packet_row_id": "next-1",
            "input_ranked_advance_packet_row_id": "ranked-1",
            "packet_rank": 1,
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
            "comparison_packet_role": "DEFAULT_OFF_REPLAY_SIGNAL_COMPARISON_INPUT",
            "packet_rank_score": 1.0,
            "packet_rank_tier": "RANKED_PACKET_DIRECT_CLEAR_BATCH",
        },
        {
            "next_branch_local_packet_row_id": "next-2",
            "input_ranked_advance_packet_row_id": "ranked-2",
            "packet_rank": 2,
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "registry_family": "avoid_redesign_repaired_proxy_comparator",
            "comparison_packet_role": "AVOID_REDESIGN_REPLAY_SIGNAL_COMPARISON_INPUT",
            "packet_rank_score": 0.7,
            "packet_rank_tier": "RANKED_PACKET_ADVANCE_WITH_CONTEXT_BATCH",
        },
    ]

    actions = repaired_proxy_implementation_action_rows(next_packets)
    rollups = repaired_proxy_implementation_scope_rollup_rows(actions)
    next_steps = repaired_proxy_implementation_next_step_rows(actions)
    system_rows = repaired_proxy_system_implementation_step_rows(actions, rollups, next_steps)

    assert actions[0]["implementation_step_family"] == "IMPLEMENTATION_STEP_READY_SCORER_BATCH"
    assert actions[1]["implementation_step_family"] == "IMPLEMENTATION_STEP_CONTEXT_COMPARATOR_BATCH"
    assert len(rollups) == 2
    assert len(next_steps) == 2
    assert system_rows[0]["implementation_action_rows"] == 2


def test_repaired_proxy_runtime_replay_spec_materialization_splits_scorer_and_comparator_specs():
    actions = [
        {
            "implementation_action_row_id": "action-1",
            "implementation_family": "IMPLEMENTATION_FAMILY_DEFAULT_OFF_SCORER",
            "implementation_step_family": "IMPLEMENTATION_STEP_READY_SCORER_BATCH",
            "packet_rank": 1,
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
        },
        {
            "implementation_action_row_id": "action-2",
            "implementation_family": "IMPLEMENTATION_FAMILY_AVOID_REDESIGN_COMPARATOR",
            "implementation_step_family": "IMPLEMENTATION_STEP_CONTEXT_COMPARATOR_BATCH",
            "packet_rank": 2,
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "registry_family": "avoid_redesign_repaired_proxy_comparator",
        },
    ]

    scorer_specs = repaired_proxy_scorer_spec_rows(actions)
    comparator_specs = repaired_proxy_comparator_spec_rows(actions)
    batches = repaired_proxy_spec_batch_rows(scorer_specs, comparator_specs)
    system_rows = repaired_proxy_system_spec_materialization_rows(scorer_specs, comparator_specs, batches)

    assert scorer_specs[0]["branch_local_spec_kind"] == "DEFAULT_OFF_REPAIRED_PROXY_SCORER_SPEC"
    assert comparator_specs[0]["branch_local_spec_kind"] == "AVOID_REDESIGN_REPAIRED_PROXY_COMPARATOR_SPEC"
    assert len(batches) == 2
    assert system_rows[0]["scorer_spec_rows"] == 1


def test_repaired_proxy_runtime_replay_spec_execution_joins_exact_replay_scores():
    scorer_specs = [
        {
            "scorer_spec_row_id": "scorer-spec-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
            "packet_rank": 1,
            "packet_rank_score": 1.0,
            "spec_context_mode": "SPEC_CONTEXT_READY_BATCH",
        }
    ]
    comparator_specs = [
        {
            "comparator_spec_row_id": "comparator-spec-1",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "registry_family": "avoid_redesign_repaired_proxy_comparator",
            "packet_rank": 2,
            "packet_rank_score": 0.8,
            "spec_context_mode": "SPEC_CONTEXT_ATTACHED_CONTEXT_BATCH",
        }
    ]
    default_reruns = [
        {
            "replay_score_rerun_row_id": "rerun-1",
            "input_replay_numeric_event_row_id": "event-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
            "replay_rerun_score": 0.22,
            "replay_score_rerun_action": "KEEP_DEFAULT_OFF_SCORER_FOR_BRANCH_LOCAL_REPLAY",
            "replay_score_rerun_status": "REPLAY_SCORE_RERUN_DEFAULT_OFF_SCORER_EMITTED",
        }
    ]
    avoid_reruns = [
        {
            "replay_score_rerun_row_id": "rerun-2",
            "input_replay_numeric_event_row_id": "event-2",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "registry_family": "avoid_redesign_repaired_proxy_comparator",
            "replay_rerun_score": -0.3,
            "replay_score_rerun_action": "KEEP_AVOID_REDESIGN_COMPARATOR_FOR_BRANCH_LOCAL_REPLAY",
            "replay_score_rerun_status": "REPLAY_SCORE_RERUN_AVOID_COMPARATOR_EMITTED",
        }
    ]

    scorer_execution = repaired_proxy_scorer_spec_execution_rows(scorer_specs, default_reruns)
    comparator_execution = repaired_proxy_comparator_spec_execution_rows(comparator_specs, avoid_reruns)
    results = repaired_proxy_spec_execution_result_rows(scorer_execution, comparator_execution)
    rollups = repaired_proxy_spec_execution_scope_rollup_rows(results)
    system_rows = repaired_proxy_system_spec_execution_rows(
        scorer_execution,
        comparator_execution,
        results,
        rollups,
    )

    assert scorer_execution[0]["spec_execution_join_status"] == "SPEC_EXECUTION_REPLAY_SCORE_JOINED_EXACT"
    assert scorer_execution[0]["scorer_spec_execution_class"] == "SCORER_SPEC_EXECUTION_POSITIVE_REPLAY_SCORE"
    assert comparator_execution[0]["comparator_spec_execution_class"] == (
        "COMPARATOR_SPEC_EXECUTION_STRONG_AVOID_SCORE"
    )
    assert len(results) == 2
    assert system_rows[0]["spec_execution_result_rows"] == 2


def test_repaired_proxy_runtime_replay_performance_preserves_rows_and_proxy_r():
    scorer_execution = [
        {
            "scorer_spec_execution_row_id": "exec-scorer-1",
            "input_replay_numeric_event_row_id": "event-1",
            "input_replay_score_rerun_row_id": "rerun-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "market_timeframe": "M5",
            "market_source_path": "data/XAUUSD_M5.csv",
            "source_component": "shadow_source_guard",
            "registry_family": "default_off_repaired_proxy_scorer",
            "scorer_spec_execution_class": "SCORER_SPEC_EXECUTION_POSITIVE_REPLAY_SCORE",
            "source_close_return_pct": 0.02,
            "source_return_minus_control": 0.01,
            "replay_rerun_score": 0.2,
        }
    ]
    comparator_execution = [
        {
            "comparator_spec_execution_row_id": "exec-comparator-1",
            "input_replay_numeric_event_row_id": "event-2",
            "input_replay_score_rerun_row_id": "rerun-2",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "horizon_id": "h32",
            "market_timeframe": "M5",
            "market_source_path": "data/GBPUSD_M5.csv",
            "source_component": "market_gap_code",
            "registry_family": "avoid_redesign_repaired_proxy_comparator",
            "comparator_spec_execution_class": "COMPARATOR_SPEC_EXECUTION_STRONG_AVOID_SCORE",
            "source_close_return_pct": -0.03,
            "source_return_minus_control": -0.02,
            "replay_rerun_score": -0.3,
        }
    ]
    numeric_rows = [
        {
            "replay_numeric_event_row_id": "event-1",
            "source_mean_abs_close_change_pct": 0.01,
            "source_mean_range_pct": 0.02,
            "source_spread_mean": 0.001,
        },
        {
            "replay_numeric_event_row_id": "event-2",
            "source_mean_abs_close_change_pct": 0.01,
            "source_mean_range_pct": 0.02,
            "source_spread_mean": 0.001,
        },
    ]

    rows = repaired_proxy_performance_rows(scorer_execution, comparator_execution, numeric_rows)
    aggregates = repaired_proxy_aggregate_performance_rows(rows)
    missing = repaired_proxy_missing_simulated_field_rows(rows)
    system = repaired_proxy_system_performance_rows(rows, aggregates, missing)

    assert len(rows) == 2
    assert rows[0]["gross_simulated_r"] == 2.0
    assert rows[0]["cost_adjusted_simulated_r"] == 1.9
    assert rows[1]["follow_inverse_default_off_avoid_class"] == "AVOID_PROXY"
    assert rows[1]["gross_simulated_r"] == 3.0
    assert rows[1]["row_disposition"] == "CARRY_AS_AVOID_INTELLIGENCE"
    assert missing == []
    assert sum(row["row_count"] for row in aggregates) == 2
    assert system[0]["rows_with_proxy_r"] == 2


def test_repaired_proxy_runtime_replay_geometry_repair_streams_proxy_path(tmp_path):
    source_dir = tmp_path / "data"
    source_dir.mkdir()
    source_path = source_dir / "TEST_M5.csv"
    source_path.write_text(
        "time,open,high,low,close\n"
        "2026-01-01 00:00,100,100.5,99.8,100.2\n"
        "2026-01-01 00:05,100.2,101.2,100.1,101.0\n",
        encoding="utf-8",
    )
    perf_rows = [
        {
            "performance_row_id": "perf-1",
            "input_replay_numeric_event_row_id": "event-1",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "TEST",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "follow_inverse_default_off_avoid_class": "DEFAULT_OFF_FOLLOW_PROXY",
            "default_off_avoid_class": "default_off",
            "side": "LONG_PROXY_FROM_SOURCE_CLOSE_SIGN",
            "stop_target_or_proxy_denominator_value": 0.01,
            "cost_adjustment_r": 0.0,
            "missing_simulated_fields": ["exact_entry_price"],
        }
    ]
    numeric_rows = [
        {
            "replay_numeric_event_row_id": "event-1",
            "input_source_numeric_metric_row_id": "metric-1",
            "market_source_path": "data/TEST_M5.csv",
        }
    ]
    metric_rows = [
        {
            "source_numeric_metric_row_id": "metric-1",
            "source_path": "data/TEST_M5.csv",
            "first_time": "2026-01-01 00:00",
            "last_time": "2026-01-01 00:05",
            "first_open": 100.0,
            "last_close": 101.0,
            "parsed_ohlc_rows": 2,
        }
    ]

    rows, scans = repaired_proxy_geometry_repair_rows(perf_rows, numeric_rows, metric_rows, tmp_path)
    aggregates = repaired_proxy_aggregate_geometry_rows(rows)
    missing = repaired_proxy_missing_geometry_field_rows(rows)
    system = repaired_proxy_system_geometry_rows(rows, aggregates, scans, missing)

    assert len(rows) == 1
    assert rows[0]["path_order_result"] == "TARGET_FIRST_PROXY_PATH"
    assert rows[0]["action_adjusted_geometry_r"] == 1.0
    assert rows[0]["geometry_repair_decision"] == "IMPLEMENT_BRANCH_LOCAL_REPLAY_GEOMETRY_PROTOTYPE"
    assert scans[0]["parsed_ohlc_rows"] == 2
    assert sum(row["row_count"] for row in aggregates) == 1
    assert system[0]["deterministic_geometry_r_rows"] == 1


def test_repaired_proxy_runtime_replay_geometry_implementation_self_tests_candidates():
    geometry_rows = [
        {
            "geometry_repair_row_id": "geom-1",
            "input_performance_row_id": "perf-1",
            "geometry_repair_decision": "IMPLEMENT_BRANCH_LOCAL_REPLAY_GEOMETRY_PROTOTYPE",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "family": "default_off_repaired_proxy_scorer",
            "default_off_avoid_class": "default_off",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abc",
            "proxy_trade_direction": "LONG",
            "proxy_entry_price": 100.0,
            "proxy_target_price": 101.0,
            "proxy_stop_price": 99.0,
            "proxy_denominator_price": 1.0,
            "path_order_result": "TARGET_FIRST_PROXY_PATH",
            "action_adjusted_geometry_r": 1.0,
            "cost_adjusted_geometry_r": 1.0,
            "geometry_result_class": "WIN",
            "remaining_missing_geometry_fields": ["exact_entry_price"],
            "remaining_missing_geometry_field_count": 1,
        },
        {
            "geometry_repair_row_id": "geom-2",
            "input_performance_row_id": "perf-2",
            "geometry_repair_decision": "CARRY_AS_AVOID_INTELLIGENCE_FROM_GEOMETRY",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "market_timeframe": "M5",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "family": "avoid_redesign_repaired_proxy_comparator",
            "default_off_avoid_class": "avoid",
            "source_path": "data/GBPUSD_M5.csv",
            "source_file_sha256": "def",
            "proxy_trade_direction": "LONG",
            "proxy_entry_price": 100.0,
            "proxy_target_price": 101.0,
            "proxy_stop_price": 99.0,
            "proxy_denominator_price": 1.0,
            "path_order_result": "STOP_FIRST_PROXY_PATH",
            "action_adjusted_geometry_r": 1.0,
            "cost_adjusted_geometry_r": 1.0,
            "geometry_result_class": "WIN",
            "remaining_missing_geometry_fields": ["exact_stop_price"],
            "remaining_missing_geometry_field_count": 1,
        },
    ]
    aggregate_geometry = [
        {
            "aggregate_geometry_row_id": "agg-1",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "default_off_avoid_class": "default_off",
            "effective_n": 1,
            "expectancy_cost_adjusted_geometry_r": 1.0,
            "geometry_keep_kill_redesign_implement_decision": "REDESIGN_DEFAULT_OFF_FROM_GEOMETRY",
        },
        {
            "aggregate_geometry_row_id": "agg-2",
            "family": "avoid_redesign_repaired_proxy_comparator",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "market_timeframe": "M5",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "default_off_avoid_class": "avoid",
            "effective_n": 1,
            "expectancy_cost_adjusted_geometry_r": 1.0,
            "geometry_keep_kill_redesign_implement_decision": "REDESIGN_AVOID_COMPARATOR_FROM_GEOMETRY",
        },
    ]

    rows = repaired_proxy_geometry_implementation_rows(geometry_rows)
    aggregates = repaired_proxy_aggregate_geometry_implementation_rows(aggregate_geometry, rows)
    self_tests = repaired_proxy_geometry_implementation_self_test_rows(rows)
    system = repaired_proxy_system_geometry_implementation_rows(rows, aggregates, self_tests)

    assert rows[0]["implementation_kind"] == "GEOMETRY_SCORER_PROTOTYPE_IMPLEMENTATION"
    assert rows[1]["implementation_kind"] == "GEOMETRY_AVOID_INTELLIGENCE_IMPLEMENTATION"
    assert all(row["implementation_self_test_status"] == "GEOMETRY_IMPLEMENTATION_SELF_TEST_PASS" for row in rows)
    assert len(aggregates) == 2
    assert system[0]["implementation_self_test_rows"] == 2


def test_repaired_proxy_runtime_replay_geometry_tables_split_concrete_outputs():
    implementation_rows = [
        {
            "geometry_implementation_row_id": "impl-1",
            "implementation_kind": "GEOMETRY_SCORER_PROTOTYPE_IMPLEMENTATION",
            "implementation_action": "IMPLEMENT_GEOMETRY_SCORER_PROTOTYPE_BRANCH_LOCAL",
            "implementation_payload": {
                "symbol": "XAUUSD",
                "route_session": "ny_core",
                "market_timeframe": "M5",
                "horizon_id": "h16",
                "source_component": "shadow_source_guard",
                "family": "default_off_repaired_proxy_scorer",
                "source_path": "data/XAUUSD_M5.csv",
                "source_file_sha256": "abc",
                "proxy_trade_direction": "LONG",
                "proxy_entry_price": 100.0,
                "proxy_target_price": 101.0,
                "proxy_stop_price": 99.0,
                "proxy_denominator_price": 1.0,
                "path_order_result": "TARGET_FIRST_PROXY_PATH",
                "expected_cost_adjusted_geometry_r": 0.99,
                "remaining_missing_geometry_fields": ["exact_entry_price"],
            },
        },
        {
            "geometry_implementation_row_id": "impl-2",
            "implementation_kind": "GEOMETRY_AVOID_INTELLIGENCE_IMPLEMENTATION",
            "implementation_action": "IMPLEMENT_GEOMETRY_AVOID_INTELLIGENCE_BRANCH_LOCAL",
            "implementation_payload": {
                "symbol": "GBPUSD",
                "route_session": "london_core",
                "market_timeframe": "M5",
                "horizon_id": "h32",
                "source_component": "market_gap_code",
                "family": "avoid_redesign_repaired_proxy_comparator",
                "source_path": "data/GBPUSD_M5.csv",
                "source_file_sha256": "def",
                "proxy_trade_direction": "LONG",
                "proxy_entry_price": 100.0,
                "proxy_target_price": 101.0,
                "proxy_stop_price": 99.0,
                "proxy_denominator_price": 1.0,
                "path_order_result": "STOP_FIRST_PROXY_PATH",
                "expected_cost_adjusted_geometry_r": 0.98,
                "remaining_missing_geometry_fields": ["exact_stop_price"],
            },
        },
        {
            "geometry_implementation_row_id": "impl-3",
            "implementation_kind": "GEOMETRY_DEFAULT_OFF_KILL_IMPLEMENTATION",
            "implementation_action": "KILL_DEFAULT_OFF_BRANCH_LOCAL",
            "implementation_payload": {
                "symbol": "NAS100",
                "route_session": "ny_core",
                "market_timeframe": "M5",
                "horizon_id": "h16",
                "source_component": "shadow_source_guard",
                "family": "default_off_repaired_proxy_scorer",
                "source_path": "data/NAS100_M5.csv",
                "source_file_sha256": "ghi",
                "path_order_result": "STOP_FIRST_PROXY_PATH",
                "expected_cost_adjusted_geometry_r": -1.01,
                "remaining_missing_geometry_fields": [],
            },
        },
    ]
    aggregate_rows = [
        {
            "aggregate_implementation_row_id": "agg-1",
            "aggregate_implementation_action": "OPEN_BRANCH_LOCAL_REDIRECTION_TASK_FOR_AGGREGATE",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "NAS100",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "default_off_avoid_class": "default_off",
            "row_count": 1,
            "effective_n": 1,
            "expectancy_cost_adjusted_geometry_r": -1.01,
            "geometry_aggregate_decision": "REDESIGN_DEFAULT_OFF_FROM_GEOMETRY",
        }
    ]

    scorer_rows = repaired_proxy_geometry_scorer_table_rows(implementation_rows)
    avoid_rows = repaired_proxy_geometry_avoid_table_rows(implementation_rows)
    kill_rows = repaired_proxy_geometry_kill_table_rows(implementation_rows)
    redirection_rows = repaired_proxy_geometry_redirection_task_rows(aggregate_rows)
    system_rows = repaired_proxy_system_geometry_table_rows(scorer_rows, avoid_rows, kill_rows, redirection_rows)

    assert scorer_rows[0]["table_application_status"] == "BRANCH_LOCAL_GEOMETRY_SCORER_TABLE_READY"
    assert avoid_rows[0]["table_application_status"] == "BRANCH_LOCAL_GEOMETRY_AVOID_INTELLIGENCE_TABLE_READY"
    assert kill_rows[0]["kill_reason"] == "KILL_DEFAULT_OFF_BRANCH_LOCAL"
    assert redirection_rows[0]["table_application_status"] == "BRANCH_LOCAL_REDIRECTION_TASK_READY"
    assert system_rows[0]["geometry_scorer_table_rows"] == 1
    assert system_rows[0]["geometry_kill_table_rows"] == 1


def test_repaired_proxy_runtime_replay_geometry_table_execution_joins_held_geometry():
    implementation_rows = [
        {
            "geometry_implementation_row_id": "impl-1",
            "input_geometry_repair_row_id": "geom-1",
            "input_performance_row_id": "perf-1",
            "default_off_avoid_class": "default_off",
            "family": "default_off_repaired_proxy_scorer",
        },
        {
            "geometry_implementation_row_id": "impl-2",
            "input_geometry_repair_row_id": "geom-2",
            "input_performance_row_id": "perf-2",
            "default_off_avoid_class": "avoid",
            "family": "avoid_redesign_repaired_proxy_comparator",
        },
    ]
    geometry_rows = [
        {
            "geometry_repair_row_id": "geom-1",
            "input_performance_row_id": "perf-1",
            "input_replay_numeric_event_row_id": "event-1",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abc",
            "path_order_result": "TARGET_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "action_adjusted_geometry_r": 1.0,
            "cost_adjusted_geometry_r": 0.99,
            "stress_geometry_r": 0.9,
            "geometry_result_class": "WIN",
            "win_count": 1,
            "loss_count": 0,
            "flat_count": 0,
            "no_fill_count": 0,
            "target_first_count": 1,
            "stop_first_count": 0,
            "neither_count": 0,
            "ambiguous_count": 0,
        },
        {
            "geometry_repair_row_id": "geom-2",
            "input_performance_row_id": "perf-2",
            "input_replay_numeric_event_row_id": "event-2",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "source_path": "data/GBPUSD_M5.csv",
            "source_file_sha256": "def",
            "path_order_result": "STOP_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "action_adjusted_geometry_r": 1.0,
            "cost_adjusted_geometry_r": 0.98,
            "stress_geometry_r": 0.88,
            "geometry_result_class": "WIN",
            "win_count": 1,
            "loss_count": 0,
            "flat_count": 0,
            "no_fill_count": 0,
            "target_first_count": 0,
            "stop_first_count": 1,
            "neither_count": 0,
            "ambiguous_count": 0,
        },
    ]
    performance_rows = [
        {
            "performance_row_id": "perf-1",
            "input_replay_numeric_event_row_id": "event-1",
            "follow_inverse_default_off_avoid_class": "DEFAULT_OFF_FOLLOW_PROXY",
        },
        {
            "performance_row_id": "perf-2",
            "input_replay_numeric_event_row_id": "event-2",
            "follow_inverse_default_off_avoid_class": "AVOID_PROXY",
        },
    ]
    scorer_table = [
        {
            "geometry_scorer_table_row_id": "scorer-1",
            "input_geometry_implementation_row_id": "impl-1",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abc",
            "proxy_trade_direction": "LONG",
            "proxy_entry_price": 100.0,
            "proxy_stop_price": 99.0,
            "proxy_target_price": 101.0,
            "proxy_denominator_price": 1.0,
            "path_order_result": "TARGET_FIRST_PROXY_PATH",
            "remaining_missing_geometry_fields": [],
        }
    ]
    avoid_table = [
        {
            "geometry_avoid_table_row_id": "avoid-1",
            "input_geometry_implementation_row_id": "impl-2",
            "family": "avoid_redesign_repaired_proxy_comparator",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "market_timeframe": "M5",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "source_path": "data/GBPUSD_M5.csv",
            "source_file_sha256": "def",
            "proxy_trade_direction": "LONG",
            "proxy_entry_price": 100.0,
            "proxy_stop_price": 99.0,
            "proxy_target_price": 101.0,
            "proxy_denominator_price": 1.0,
            "path_order_result": "STOP_FIRST_PROXY_PATH",
            "remaining_missing_geometry_fields": [],
        }
    ]

    scorer_exec = repaired_proxy_scorer_geometry_table_execution_rows(
        scorer_table,
        implementation_rows,
        geometry_rows,
        performance_rows,
    )
    avoid_exec = repaired_proxy_avoid_geometry_table_execution_rows(
        avoid_table,
        implementation_rows,
        geometry_rows,
        performance_rows,
    )
    gap_rows = repaired_proxy_geometry_table_source_gap_rows(scorer_exec + avoid_exec)
    aggregate_rows = repaired_proxy_aggregate_geometry_table_execution_rows(scorer_exec + avoid_exec)
    system_rows = repaired_proxy_system_geometry_table_execution_rows(
        scorer_exec,
        avoid_exec,
        aggregate_rows,
        gap_rows,
    )

    assert scorer_exec[0]["source_join_status"] == "HELD_REPLAY_GEOMETRY_JOINED"
    assert scorer_exec[0]["table_execution_class"] == "GEOMETRY_SCORER_EXECUTION_POSITIVE_REPLAY_R"
    assert avoid_exec[0]["table_execution_decision"] == "CARRY_BRANCH_LOCAL_AVOID_INTELLIGENCE_OBSERVATION"
    assert gap_rows == []
    assert sum(row["row_count"] for row in aggregate_rows) == 2
    assert system_rows[0]["joined_replay_geometry_rows"] == 2


def test_repaired_proxy_runtime_replay_geometry_table_observations_preserve_execution_rows():
    scorer_execution = [
        {
            "geometry_table_execution_row_id": "exec-scorer-1",
            "input_geometry_table_row_id": "scorer-table-1",
            "input_geometry_implementation_row_id": "impl-1",
            "input_geometry_repair_row_id": "geom-1",
            "input_performance_row_id": "perf-1",
            "input_replay_numeric_event_row_id": "event-1",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "default_off_avoid_class": "default_off",
            "follow_inverse_default_off_avoid_class": "DEFAULT_OFF_FOLLOW_PROXY",
            "entry_reference": "GEOMETRY_TABLE:data/XAUUSD_M5.csv:scorer-table-1",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abc",
            "path_order_result": "TARGET_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "gross_simulated_r": 1.0,
            "cost_adjusted_simulated_r": 0.99,
            "stress_simulated_r": 0.9,
            "win_count": 1,
            "loss_count": 0,
            "flat_count": 0,
            "no_fill_count": 0,
            "target_first_count": 1,
            "stop_first_count": 0,
            "neither_count": 0,
            "ambiguous_count": 0,
            "source_gap_fields": [],
        }
    ]
    avoid_execution = [
        {
            "geometry_table_execution_row_id": "exec-avoid-1",
            "input_geometry_table_row_id": "avoid-table-1",
            "input_geometry_implementation_row_id": "impl-2",
            "input_geometry_repair_row_id": "geom-2",
            "input_performance_row_id": "perf-2",
            "input_replay_numeric_event_row_id": "event-2",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "family": "avoid_redesign_repaired_proxy_comparator",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "market_timeframe": "M5",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "default_off_avoid_class": "avoid",
            "follow_inverse_default_off_avoid_class": "AVOID_PROXY",
            "entry_reference": "GEOMETRY_TABLE:data/GBPUSD_M5.csv:avoid-table-1",
            "source_path": "data/GBPUSD_M5.csv",
            "source_file_sha256": "def",
            "path_order_result": "STOP_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "gross_simulated_r": 1.0,
            "cost_adjusted_simulated_r": 0.98,
            "stress_simulated_r": 0.88,
            "win_count": 1,
            "loss_count": 0,
            "flat_count": 0,
            "no_fill_count": 0,
            "target_first_count": 0,
            "stop_first_count": 1,
            "neither_count": 0,
            "ambiguous_count": 0,
            "source_gap_fields": [],
        }
    ]

    scorer_rows = repaired_proxy_scorer_geometry_table_observation_rows(scorer_execution)
    avoid_rows = repaired_proxy_avoid_geometry_table_observation_rows(avoid_execution)
    gap_rows = repaired_proxy_geometry_table_observation_source_gap_rows(scorer_rows + avoid_rows)
    aggregate_rows = repaired_proxy_aggregate_geometry_table_observation_rows(scorer_rows + avoid_rows)
    system_rows = repaired_proxy_system_geometry_table_observation_rows(
        scorer_rows,
        avoid_rows,
        aggregate_rows,
        gap_rows,
    )

    assert scorer_rows[0]["observation_signal"] == "GEOMETRY_SCORER_OBSERVATION_REPLAY_POSITIVE"
    assert avoid_rows[0]["observation_action"] == "RETAIN_BRANCH_LOCAL_AVOID_INTELLIGENCE_OBSERVATION"
    assert gap_rows == []
    assert sum(row["row_count"] for row in aggregate_rows) == 2
    assert system_rows[0]["total_observation_rows"] == 2


def test_repaired_proxy_runtime_replay_geometry_table_code_candidates_preserve_observations():
    scorer_observations = [
        {
            "geometry_table_observation_row_id": "obs-scorer-1",
            "input_geometry_table_execution_row_id": "exec-scorer-1",
            "input_geometry_table_row_id": "scorer-table-1",
            "input_geometry_repair_row_id": "geom-1",
            "input_performance_row_id": "perf-1",
            "input_replay_numeric_event_row_id": "event-1",
            "observation_kind": "scorer",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "default_off_avoid_class": "default_off",
            "follow_inverse_default_off_avoid_class": "DEFAULT_OFF_FOLLOW_PROXY",
            "entry_reference": "GEOMETRY_TABLE:data/XAUUSD_M5.csv:scorer-table-1",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abcdef123456",
            "path_order_result": "TARGET_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "gross_simulated_r": 1.0,
            "cost_adjusted_simulated_r": 0.99,
            "stress_simulated_r": 0.9,
            "win_count": 1,
            "loss_count": 0,
            "flat_count": 0,
            "no_fill_count": 0,
            "target_first_count": 1,
            "stop_first_count": 0,
            "neither_count": 0,
            "ambiguous_count": 0,
            "source_gap_fields": [],
        }
    ]
    avoid_observations = [
        {
            "geometry_table_observation_row_id": "obs-avoid-1",
            "input_geometry_table_execution_row_id": "exec-avoid-1",
            "input_geometry_table_row_id": "avoid-table-1",
            "input_geometry_repair_row_id": "geom-2",
            "input_performance_row_id": "perf-2",
            "input_replay_numeric_event_row_id": "event-2",
            "observation_kind": "avoid",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "family": "avoid_redesign_repaired_proxy_comparator",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "market_timeframe": "M5",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "default_off_avoid_class": "avoid",
            "follow_inverse_default_off_avoid_class": "AVOID_PROXY",
            "entry_reference": "GEOMETRY_TABLE:data/GBPUSD_M5.csv:avoid-table-1",
            "source_path": "data/GBPUSD_M5.csv",
            "source_file_sha256": "fedcba654321",
            "path_order_result": "STOP_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "gross_simulated_r": 1.0,
            "cost_adjusted_simulated_r": 0.98,
            "stress_simulated_r": 0.88,
            "win_count": 1,
            "loss_count": 0,
            "flat_count": 0,
            "no_fill_count": 0,
            "target_first_count": 0,
            "stop_first_count": 1,
            "neither_count": 0,
            "ambiguous_count": 0,
            "source_gap_fields": [],
        }
    ]

    scorer_rows = repaired_proxy_scorer_geometry_table_code_candidate_rows(scorer_observations)
    avoid_rows = repaired_proxy_avoid_geometry_table_code_candidate_rows(avoid_observations)
    gap_rows = repaired_proxy_geometry_table_source_gap_code_candidate_rows(scorer_rows + avoid_rows)
    aggregate_rows = repaired_proxy_aggregate_geometry_table_code_candidate_rows(scorer_rows + avoid_rows)
    system_rows = repaired_proxy_system_geometry_table_code_candidate_rows(
        scorer_rows,
        avoid_rows,
        aggregate_rows,
        gap_rows,
    )

    assert scorer_rows[0]["code_candidate_action"] == "IMPLEMENT_BRANCH_LOCAL_GEOMETRY_SCORER_CODE_CANDIDATE"
    assert avoid_rows[0]["code_candidate_action"] == "IMPLEMENT_BRANCH_LOCAL_GEOMETRY_AVOID_CODE_CANDIDATE"
    assert scorer_rows[0]["implementation_contract"]["production_import_permitted"] is False
    assert gap_rows == []
    assert sum(row["row_count"] for row in aggregate_rows) == 2
    assert system_rows[0]["total_code_candidate_rows"] == 2


def test_repaired_proxy_runtime_replay_geometry_table_code_surfaces_execute_scope_match():
    scorer_candidates = [
        {
            "geometry_table_code_candidate_row_id": "cand-scorer-1",
            "input_geometry_table_observation_row_id": "obs-scorer-1",
            "input_geometry_table_execution_row_id": "exec-scorer-1",
            "input_geometry_repair_row_id": "geom-1",
            "input_performance_row_id": "perf-1",
            "input_replay_numeric_event_row_id": "event-1",
            "code_candidate_kind": "GEOMETRY_SCORER_CODE_CANDIDATE",
            "branch_local_candidate_key": "key-1",
            "branch_local_candidate_function": "score_scorer_xauusd",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "default_off_avoid_class": "default_off",
            "follow_inverse_default_off_avoid_class": "DEFAULT_OFF_FOLLOW_PROXY",
            "entry_reference": "GEOMETRY_TABLE:data/XAUUSD_M5.csv:scorer-table-1",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abcdef123456",
            "path_order_result": "TARGET_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "gross_simulated_r": 1.0,
            "cost_adjusted_simulated_r": 0.99,
            "stress_simulated_r": 0.9,
            "win_count": 1,
            "loss_count": 0,
            "flat_count": 0,
            "no_fill_count": 0,
            "target_first_count": 1,
            "stop_first_count": 0,
            "neither_count": 0,
            "ambiguous_count": 0,
            "source_gap_fields": [],
        }
    ]
    avoid_candidates = [
        {
            "geometry_table_code_candidate_row_id": "cand-avoid-1",
            "input_geometry_table_observation_row_id": "obs-avoid-1",
            "input_geometry_table_execution_row_id": "exec-avoid-1",
            "input_geometry_repair_row_id": "geom-2",
            "input_performance_row_id": "perf-2",
            "input_replay_numeric_event_row_id": "event-2",
            "code_candidate_kind": "GEOMETRY_AVOID_CODE_CANDIDATE",
            "branch_local_candidate_key": "key-2",
            "branch_local_candidate_function": "score_avoid_gbpusd",
            "family": "avoid_redesign_repaired_proxy_comparator",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "market_timeframe": "M5",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "default_off_avoid_class": "avoid",
            "follow_inverse_default_off_avoid_class": "AVOID_PROXY",
            "entry_reference": "GEOMETRY_TABLE:data/GBPUSD_M5.csv:avoid-table-1",
            "source_path": "data/GBPUSD_M5.csv",
            "source_file_sha256": "fedcba654321",
            "path_order_result": "STOP_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "gross_simulated_r": 1.0,
            "cost_adjusted_simulated_r": 0.98,
            "stress_simulated_r": 0.88,
            "win_count": 1,
            "loss_count": 0,
            "flat_count": 0,
            "no_fill_count": 0,
            "target_first_count": 0,
            "stop_first_count": 1,
            "neither_count": 0,
            "ambiguous_count": 0,
            "source_gap_fields": [],
        }
    ]

    scorer_surfaces = repaired_proxy_scorer_geometry_table_code_surface_rows(scorer_candidates)
    avoid_surfaces = repaired_proxy_avoid_geometry_table_code_surface_rows(avoid_candidates)
    self_tests = repaired_proxy_geometry_table_code_surface_self_test_rows(scorer_surfaces + avoid_surfaces)
    aggregate_rows = repaired_proxy_aggregate_geometry_table_code_surface_rows(
        scorer_surfaces + avoid_surfaces,
        self_tests,
    )
    system_rows = repaired_proxy_system_geometry_table_code_surface_rows(
        scorer_surfaces,
        avoid_surfaces,
        self_tests,
        aggregate_rows,
    )
    event = {
        "symbol": "XAUUSD",
        "route_session": "ny_core",
        "market_timeframe": "M5",
        "horizon_id": "h16",
        "source_component": "shadow_source_guard",
        "source_file_sha256": "abcdef123456",
        "path_order_result": "TARGET_FIRST_PROXY_PATH",
    }

    execution = repaired_proxy_execute_geometry_table_code_surface(scorer_surfaces[0], event)

    assert execution["surface_match"] is True
    assert execution["surface_score"] == 0.99
    assert all(row["surface_self_test_status"] == "GEOMETRY_CODE_SURFACE_SELF_TEST_PASS" for row in self_tests)
    assert sum(row["row_count"] for row in aggregate_rows) == 2
    assert system_rows[0]["total_code_surface_rows"] == 2


def test_repaired_proxy_runtime_replay_geometry_table_code_surface_execution_preserves_passes():
    surfaces = [
        {
            "geometry_table_code_surface_row_id": "surface-1",
            "input_geometry_table_code_candidate_row_id": "cand-1",
            "input_geometry_table_observation_row_id": "obs-1",
            "input_geometry_table_execution_row_id": "exec-1",
            "input_geometry_repair_row_id": "geom-1",
            "input_performance_row_id": "perf-1",
            "input_replay_numeric_event_row_id": "event-1",
            "code_surface_kind": "GEOMETRY_SCORER_EXECUTABLE_SURFACE",
            "surface_function": "score_scorer_xauusd",
            "surface_action": "EMIT_BRANCH_LOCAL_SCORER_REPLAY_OBSERVATION",
            "surface_cost_adjusted_simulated_r": 0.99,
            "production_import_permitted": False,
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "default_off_avoid_class": "default_off",
            "entry_reference": "GEOMETRY_TABLE:data/XAUUSD_M5.csv:scorer-table-1",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abcdef123456",
            "path_order_result": "TARGET_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "cost_adjusted_simulated_r": 0.99,
            "stress_simulated_r": 0.9,
        }
    ]
    observations = [
        {
            "geometry_table_observation_row_id": "obs-1",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "source_file_sha256": "abcdef123456",
            "path_order_result": "TARGET_FIRST_PROXY_PATH",
            "cost_adjusted_simulated_r": 0.99,
        }
    ]

    rows = repaired_proxy_geometry_table_code_surface_execution_rows(surfaces, observations)
    issues = repaired_proxy_geometry_table_code_surface_execution_issue_rows(rows)
    aggregates = repaired_proxy_aggregate_geometry_table_code_surface_execution_rows(rows)
    system = repaired_proxy_system_geometry_table_code_surface_execution_rows(rows, issues, aggregates)

    assert rows[0]["surface_execution_status"] == "CODE_SURFACE_EXECUTION_PASS"
    assert rows[0]["surface_score"] == 0.99
    assert issues == []
    assert aggregates[0]["aggregate_code_surface_execution_status"] == "KEEP_SCORER_CODE_SURFACE_EXECUTION_GROUP"
    assert system[0]["code_surface_execution_rows"] == 1


def test_repaired_proxy_runtime_replay_geometry_table_recommendations_keep_passing_surfaces():
    execution_rows = [
        {
            "geometry_table_code_surface_execution_row_id": "exec-surface-1",
            "input_geometry_table_code_surface_row_id": "surface-1",
            "input_geometry_table_observation_row_id": "obs-1",
            "input_replay_numeric_event_row_id": "event-1",
            "surface_execution_status": "CODE_SURFACE_EXECUTION_PASS",
            "code_surface_kind": "GEOMETRY_SCORER_EXECUTABLE_SURFACE",
            "surface_function": "score_scorer_xauusd",
            "surface_score": 0.99,
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "default_off_avoid_class": "default_off",
            "entry_reference": "GEOMETRY_TABLE:data/XAUUSD_M5.csv:scorer-table-1",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abcdef123456",
            "path_order_result": "TARGET_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "cost_adjusted_simulated_r": 0.99,
            "stress_simulated_r": 0.9,
        }
    ]

    rows = repaired_proxy_geometry_table_recommendation_rows(execution_rows)
    aggregates = repaired_proxy_aggregate_geometry_table_recommendation_rows(rows)
    system = repaired_proxy_system_geometry_table_recommendation_rows(rows, aggregates)

    assert rows[0]["recommendation_kind"] == "KEEP_BRANCH_LOCAL_SCORER_RECOMMENDATION"
    assert rows[0]["recommendation_action"] == "RETAIN_SCORER_SURFACE_FOR_BRANCH_LOCAL_REPLAY_REVIEW"
    assert aggregates[0]["aggregate_recommendation_action"] == "KEEP_SCORER_RECOMMENDATION_GROUP"
    assert system[0]["recommendation_rows"] == 1


def test_repaired_proxy_runtime_replay_geometry_table_performance_matrix_preserves_all_rows():
    performance_rows = [
        {
            "performance_row_id": "perf-1",
            "input_replay_numeric_event_row_id": "event-1",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "side": "LONG_PROXY_FROM_SOURCE_CLOSE_SIGN",
            "follow_inverse_default_off_avoid_class": "DEFAULT_OFF_FOLLOW_PROXY",
            "default_off_avoid_class": "default_off",
            "entry_reference": "PROXY_AGGREGATE_SOURCE:data/XAUUSD_M5.csv:M5:event-1",
            "entry_reference_type": "AGGREGATE_REPLAY_SOURCE_PROXY",
            "stop_target_or_proxy_denominator_field": "source_mean_abs_close_change_pct",
            "stop_target_or_proxy_denominator_value": 0.001,
            "path_order_result": "AMBIGUOUS_PROXY_AGGREGATE_NO_EXACT_TARGET_STOP",
            "fill_status": "PROXY_FILL_ASSUMED_FROM_REPLAY_SOURCE",
            "gross_simulated_r": 2.0,
            "cost_adjusted_simulated_r": 1.9,
            "stress_simulated_r": 1.2,
            "row_disposition": "IMPLEMENT_BRANCH_LOCAL_REPLAY_PROTOTYPE",
            "duplicate_key": "event-1",
            "effective_n_key": "event-1",
            "missing_simulated_fields": [],
        },
        {
            "performance_row_id": "perf-2",
            "input_replay_numeric_event_row_id": "event-2",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "family": "avoid_redesign_repaired_proxy_comparator",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "market_timeframe": "M5",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "side": "SHORT_PROXY_FROM_SOURCE_CLOSE_SIGN",
            "follow_inverse_default_off_avoid_class": "AVOID_PROXY",
            "default_off_avoid_class": "avoid",
            "entry_reference": "PROXY_AGGREGATE_SOURCE:data/GBPUSD_M5.csv:M5:event-2",
            "entry_reference_type": "AGGREGATE_REPLAY_SOURCE_PROXY",
            "stop_target_or_proxy_denominator_field": "source_mean_range_pct",
            "stop_target_or_proxy_denominator_value": 0.002,
            "path_order_result": "AMBIGUOUS_PROXY_AGGREGATE_NO_EXACT_TARGET_STOP",
            "fill_status": "PROXY_FILL_ASSUMED_FROM_REPLAY_SOURCE",
            "gross_simulated_r": 1.0,
            "cost_adjusted_simulated_r": 0.8,
            "stress_simulated_r": 0.5,
            "row_disposition": "CARRY_AS_AVOID_INTELLIGENCE",
            "duplicate_key": "event-2",
            "effective_n_key": "event-2",
            "missing_simulated_fields": [],
        },
        {
            "performance_row_id": "perf-3",
            "input_replay_numeric_event_row_id": "event-3",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "side": "LONG_PROXY_FROM_SOURCE_CLOSE_SIGN",
            "follow_inverse_default_off_avoid_class": "DEFAULT_OFF_FOLLOW_PROXY",
            "default_off_avoid_class": "default_off",
            "entry_reference": "PROXY_AGGREGATE_SOURCE:data/XAUUSD_M5.csv:M5:event-3",
            "entry_reference_type": "AGGREGATE_REPLAY_SOURCE_PROXY",
            "stop_target_or_proxy_denominator_field": "source_mean_abs_close_change_pct",
            "stop_target_or_proxy_denominator_value": 0.001,
            "path_order_result": "AMBIGUOUS_PROXY_AGGREGATE_NO_EXACT_TARGET_STOP",
            "fill_status": "PROXY_FILL_ASSUMED_FROM_REPLAY_SOURCE",
            "gross_simulated_r": -1.0,
            "cost_adjusted_simulated_r": -1.1,
            "stress_simulated_r": -1.2,
            "row_disposition": "KILL_BRANCH_LOCAL_DEFAULT_OFF_ROW",
            "duplicate_key": "event-3",
            "effective_n_key": "event-3",
            "missing_simulated_fields": [],
        },
    ]
    geometry_rows = [
        {
            "geometry_repair_row_id": "geom-1",
            "input_performance_row_id": "perf-1",
            "input_replay_numeric_event_row_id": "event-1",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "default_off_avoid_class": "default_off",
            "proxy_trade_direction": "LONG",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abc123",
            "proxy_entry_price": 2000.0,
            "proxy_stop_price": 1998.0,
            "proxy_target_price": 2002.0,
            "proxy_denominator_pct": 0.001,
            "proxy_denominator_price": 2.0,
            "path_order_result": "TARGET_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "path_scan_status": "PROXY_PATH_SCAN_COMPLETE",
            "first_touch_time": "2026-05-01 13:00:00",
            "first_touch_bar_index": 2,
            "action_adjusted_geometry_r": 1.0,
            "cost_adjustment_r": 0.0,
            "cost_adjusted_geometry_r": 1.0,
            "stress_geometry_r": 1.0,
            "geometry_result_class": "WIN",
            "target_first_count": 1,
            "stop_first_count": 0,
            "neither_count": 0,
            "ambiguous_count": 0,
            "geometry_repair_decision": "IMPLEMENT_BRANCH_LOCAL_REPLAY_GEOMETRY_PROTOTYPE",
            "remaining_missing_geometry_fields": [],
        },
        {
            "geometry_repair_row_id": "geom-2",
            "input_performance_row_id": "perf-2",
            "input_replay_numeric_event_row_id": "event-2",
            "family": "avoid_redesign_repaired_proxy_comparator",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "market_timeframe": "M5",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "default_off_avoid_class": "avoid",
            "proxy_trade_direction": "SHORT",
            "source_path": "data/GBPUSD_M5.csv",
            "source_file_sha256": "def456",
            "proxy_entry_price": 1.25,
            "proxy_stop_price": 1.252,
            "proxy_target_price": 1.248,
            "proxy_denominator_pct": 0.002,
            "proxy_denominator_price": 0.002,
            "path_order_result": "STOP_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "path_scan_status": "PROXY_PATH_SCAN_COMPLETE",
            "first_touch_time": "2026-05-01 08:00:00",
            "first_touch_bar_index": 3,
            "action_adjusted_geometry_r": 1.0,
            "cost_adjustment_r": 0.0,
            "cost_adjusted_geometry_r": 1.0,
            "stress_geometry_r": 0.8,
            "geometry_result_class": "WIN",
            "target_first_count": 0,
            "stop_first_count": 1,
            "neither_count": 0,
            "ambiguous_count": 0,
            "geometry_repair_decision": "CARRY_AS_AVOID_INTELLIGENCE_FROM_GEOMETRY",
            "remaining_missing_geometry_fields": [],
        },
        {
            "geometry_repair_row_id": "geom-3",
            "input_performance_row_id": "perf-3",
            "input_replay_numeric_event_row_id": "event-3",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "default_off_avoid_class": "default_off",
            "proxy_trade_direction": "LONG",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abc123",
            "path_order_result": "STOP_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "path_scan_status": "PROXY_PATH_SCAN_COMPLETE",
            "action_adjusted_geometry_r": -1.0,
            "cost_adjustment_r": 0.0,
            "cost_adjusted_geometry_r": -1.0,
            "stress_geometry_r": -1.0,
            "geometry_result_class": "LOSS",
            "target_first_count": 0,
            "stop_first_count": 1,
            "neither_count": 0,
            "ambiguous_count": 0,
            "geometry_repair_decision": "KILL_DEFAULT_OFF_FROM_GEOMETRY",
            "remaining_missing_geometry_fields": [],
        },
    ]
    recommendation_rows = [
        {
            "geometry_table_recommendation_row_id": "rec-1",
            "input_replay_numeric_event_row_id": "event-1",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "default_off_avoid_class": "default_off",
            "path_order_result": "TARGET_FIRST_PROXY_PATH",
            "source_file_sha256": "abc123",
            "entry_reference": "GEOMETRY_TABLE:data/XAUUSD_M5.csv:table-1",
            "recommendation_kind": "KEEP_BRANCH_LOCAL_SCORER_RECOMMENDATION",
            "recommendation_action": "RETAIN_SCORER_SURFACE_FOR_BRANCH_LOCAL_REPLAY_REVIEW",
            "surface_function": "score_xauusd",
            "surface_score": 1.0,
        },
        {
            "geometry_table_recommendation_row_id": "rec-2",
            "input_replay_numeric_event_row_id": "event-2",
            "family": "avoid_redesign_repaired_proxy_comparator",
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "market_timeframe": "M5",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "default_off_avoid_class": "avoid",
            "path_order_result": "STOP_FIRST_PROXY_PATH",
            "source_file_sha256": "def456",
            "entry_reference": "GEOMETRY_TABLE:data/GBPUSD_M5.csv:table-2",
            "recommendation_kind": "KEEP_BRANCH_LOCAL_AVOID_INTELLIGENCE_RECOMMENDATION",
            "recommendation_action": "RETAIN_AVOID_INTELLIGENCE_SURFACE_FOR_BRANCH_LOCAL_REPLAY_REVIEW",
            "surface_function": "score_gbpusd_avoid",
            "surface_score": 1.0,
        },
    ]
    broader_rows = [
        {
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "unified_decision_group": "IMPLEMENT",
            "unified_action_class": "IMPLEMENT_DEFAULT_OFF_SCORER_CANDIDATE",
        },
        {
            "symbol": "GBPUSD",
            "route_session": "london_core",
            "horizon_id": "h32",
            "source_component": "market_gap_code",
            "unified_decision_group": "REDESIGN",
            "unified_action_class": "MARKET_GAP_AVOID_FILTER_IMPLEMENT_CANDIDATE",
        },
    ]

    rows = repaired_proxy_geometry_table_performance_matrix_rows(
        performance_rows,
        geometry_rows,
        recommendation_rows,
        broader_rows,
    )
    aggregates = repaired_proxy_aggregate_geometry_table_performance_matrix_rows(rows)
    missing_rows = repaired_proxy_geometry_table_performance_matrix_missing_rows(rows)
    join_rows = repaired_proxy_geometry_table_performance_matrix_join_rows(rows)
    system = repaired_proxy_system_geometry_table_performance_matrix_rows(rows, aggregates, missing_rows, join_rows)

    assert len(rows) == 3
    assert rows[0]["keep_kill_redesign_implement_decision"] == "IMPLEMENT_BRANCH_LOCAL_SCORER_FROM_REPLAY_GEOMETRY_TABLE"
    assert rows[1]["keep_kill_redesign_implement_decision"] == "CARRY_AS_AVOID_INTELLIGENCE_FROM_REPLAY_GEOMETRY_TABLE"
    assert rows[2]["keep_kill_redesign_implement_decision"] == "KILL_DEFAULT_OFF_FROM_REPLAY_GEOMETRY"
    assert rows[0]["scope_row_count"] == 2
    assert rows[0]["broader_recommendation_exact_scope_rows"] == 1
    assert sum(row["row_count"] for row in aggregates) == 3
    assert missing_rows == []
    assert join_rows == []
    assert system[0]["performance_matrix_rows"] == 3


def test_repaired_proxy_runtime_replay_geometry_table_matrix_surfaces_preserve_surface_and_terminal_rows():
    matrix_rows = [
        {
            "performance_matrix_row_id": "matrix-1",
            "input_performance_row_id": "perf-1",
            "input_geometry_repair_row_id": "geom-1",
            "input_geometry_table_recommendation_row_id": "rec-1",
            "input_replay_numeric_event_row_id": "event-1",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "side": "LONG_PROXY_FROM_SOURCE_CLOSE_SIGN",
            "proxy_trade_direction": "LONG",
            "follow_inverse_default_off_avoid_class": "DEFAULT_OFF_FOLLOW_PROXY",
            "default_off_avoid_class": "default_off",
            "entry_reference": "GEOMETRY_TABLE:data/XAUUSD_M5.csv:table-1",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abc123",
            "path_order_result": "TARGET_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "proxy_entry_price": 2000.0,
            "proxy_stop_price": 1998.0,
            "proxy_target_price": 2002.0,
            "stop_target_or_proxy_denominator_field": "source_mean_abs_close_change_pct",
            "stop_target_or_proxy_denominator_value": 0.001,
            "gross_simulated_r": 1.0,
            "cost_adjusted_simulated_r": 1.0,
            "stress_simulated_r": 0.9,
            "result_class": "WIN",
            "win_count": 1,
            "loss_count": 0,
            "flat_count": 0,
            "no_fill_count": 0,
            "target_first_count": 1,
            "stop_first_count": 0,
            "neither_count": 0,
            "ambiguous_count": 0,
            "effective_n_key": "event-1",
            "scope_effective_n": 1,
            "scope_duplicate_row_count": 0,
            "scope_concentration_share_of_all_rows": 0.5,
            "broader_recommendation_scope_status": "BROADER_BRANCH_LOCAL_RECOMMENDATION_EXACT_SCOPE_PRESENT",
            "keep_kill_redesign_implement_decision": "IMPLEMENT_BRANCH_LOCAL_SCORER_FROM_REPLAY_GEOMETRY_TABLE",
        },
        {
            "performance_matrix_row_id": "matrix-2",
            "input_performance_row_id": "perf-2",
            "input_geometry_repair_row_id": "geom-2",
            "input_geometry_table_recommendation_row_id": None,
            "input_replay_numeric_event_row_id": "event-2",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "side": "LONG_PROXY_FROM_SOURCE_CLOSE_SIGN",
            "proxy_trade_direction": "LONG",
            "follow_inverse_default_off_avoid_class": "DEFAULT_OFF_FOLLOW_PROXY",
            "default_off_avoid_class": "default_off",
            "entry_reference": "PROXY_AGGREGATE_SOURCE:data/XAUUSD_M5.csv:M5:event-2",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abc123",
            "path_order_result": "STOP_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "gross_simulated_r": -1.0,
            "cost_adjusted_simulated_r": -1.0,
            "stress_simulated_r": -1.0,
            "result_class": "LOSS",
            "win_count": 0,
            "loss_count": 1,
            "flat_count": 0,
            "no_fill_count": 0,
            "target_first_count": 0,
            "stop_first_count": 1,
            "neither_count": 0,
            "ambiguous_count": 0,
            "effective_n_key": "event-2",
            "scope_effective_n": 1,
            "scope_duplicate_row_count": 0,
            "scope_concentration_share_of_all_rows": 0.5,
            "broader_recommendation_scope_status": "BROADER_BRANCH_LOCAL_RECOMMENDATION_EXACT_SCOPE_PRESENT",
            "keep_kill_redesign_implement_decision": "KILL_DEFAULT_OFF_FROM_REPLAY_GEOMETRY",
        },
    ]

    scorer_rows = repaired_proxy_geometry_table_matrix_scorer_surface_rows(matrix_rows)
    avoid_rows = repaired_proxy_geometry_table_matrix_avoid_surface_rows(matrix_rows)
    terminal_rows = repaired_proxy_geometry_table_matrix_terminal_rows(matrix_rows)
    self_tests = repaired_proxy_geometry_table_matrix_surface_self_test_rows(scorer_rows + avoid_rows)
    aggregates = repaired_proxy_aggregate_geometry_table_matrix_surface_rows(
        scorer_rows,
        avoid_rows,
        terminal_rows,
        self_tests,
    )
    system = repaired_proxy_system_geometry_table_matrix_surface_rows(
        scorer_rows,
        avoid_rows,
        terminal_rows,
        self_tests,
        aggregates,
    )
    execution = repaired_proxy_execute_geometry_table_matrix_surface(scorer_rows[0], scorer_rows[0])

    assert len(scorer_rows) == 1
    assert len(avoid_rows) == 0
    assert len(terminal_rows) == 1
    assert scorer_rows[0]["surface_action"] == "EMIT_BRANCH_LOCAL_SCORER_MATRIX_OBSERVATION"
    assert terminal_rows[0]["terminal_action"] == "KILL_DEFAULT_OFF_FROM_REPLAY_GEOMETRY"
    assert execution["surface_match"] is True
    assert execution["surface_score"] == 1.0
    assert self_tests[0]["surface_self_test_status"] == "PERFORMANCE_MATRIX_SURFACE_SELF_TEST_PASS"
    assert sum(row["row_count"] for row in aggregates) == 2
    assert system[0]["total_matrix_rows_consumed"] == 2


def test_repaired_proxy_runtime_replay_geometry_table_matrix_surface_execution_preserves_rows():
    matrix_rows = [
        {
            "performance_matrix_row_id": "matrix-1",
            "input_performance_row_id": "perf-1",
            "input_geometry_repair_row_id": "geom-1",
            "input_geometry_table_recommendation_row_id": "rec-1",
            "input_replay_numeric_event_row_id": "event-1",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "side": "LONG_PROXY_FROM_SOURCE_CLOSE_SIGN",
            "proxy_trade_direction": "LONG",
            "follow_inverse_default_off_avoid_class": "DEFAULT_OFF_FOLLOW_PROXY",
            "default_off_avoid_class": "default_off",
            "entry_reference": "GEOMETRY_TABLE:data/XAUUSD_M5.csv:table-1",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abc123",
            "path_order_result": "TARGET_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "gross_simulated_r": 1.0,
            "cost_adjusted_simulated_r": 1.0,
            "stress_simulated_r": 0.9,
            "result_class": "WIN",
            "win_count": 1,
            "loss_count": 0,
            "flat_count": 0,
            "no_fill_count": 0,
            "target_first_count": 1,
            "stop_first_count": 0,
            "neither_count": 0,
            "ambiguous_count": 0,
            "effective_n_key": "event-1",
            "scope_effective_n": 1,
            "scope_concentration_share_of_all_rows": 0.5,
            "keep_kill_redesign_implement_decision": "IMPLEMENT_BRANCH_LOCAL_SCORER_FROM_REPLAY_GEOMETRY_TABLE",
        },
        {
            "performance_matrix_row_id": "matrix-2",
            "input_performance_row_id": "perf-2",
            "input_geometry_repair_row_id": "geom-2",
            "input_replay_numeric_event_row_id": "event-2",
            "branch": "branch_local_repaired_proxy_runtime_replay",
            "family": "default_off_repaired_proxy_scorer",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "market_timeframe": "M5",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "side": "LONG_PROXY_FROM_SOURCE_CLOSE_SIGN",
            "proxy_trade_direction": "LONG",
            "follow_inverse_default_off_avoid_class": "DEFAULT_OFF_FOLLOW_PROXY",
            "default_off_avoid_class": "default_off",
            "entry_reference": "PROXY_AGGREGATE_SOURCE:data/XAUUSD_M5.csv:M5:event-2",
            "source_path": "data/XAUUSD_M5.csv",
            "source_file_sha256": "abc123",
            "path_order_result": "STOP_FIRST_PROXY_PATH",
            "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN",
            "gross_simulated_r": -1.0,
            "cost_adjusted_simulated_r": -1.0,
            "stress_simulated_r": -1.0,
            "result_class": "LOSS",
            "win_count": 0,
            "loss_count": 1,
            "flat_count": 0,
            "no_fill_count": 0,
            "target_first_count": 0,
            "stop_first_count": 1,
            "neither_count": 0,
            "ambiguous_count": 0,
            "effective_n_key": "event-2",
            "scope_effective_n": 1,
            "scope_concentration_share_of_all_rows": 0.5,
            "keep_kill_redesign_implement_decision": "KILL_DEFAULT_OFF_FROM_REPLAY_GEOMETRY",
        },
    ]
    scorer_rows = repaired_proxy_geometry_table_matrix_scorer_surface_rows(matrix_rows)
    terminal_rows = repaired_proxy_geometry_table_matrix_terminal_rows(matrix_rows)

    surface_exec = repaired_proxy_geometry_table_matrix_surface_execution_rows(scorer_rows, matrix_rows)
    terminal_exec = repaired_proxy_geometry_table_matrix_terminal_execution_rows(terminal_rows, matrix_rows)
    issues = repaired_proxy_geometry_table_matrix_surface_execution_issue_rows(surface_exec, terminal_exec)
    aggregates = repaired_proxy_aggregate_geometry_table_matrix_surface_execution_rows(surface_exec, terminal_exec)
    system = repaired_proxy_system_geometry_table_matrix_surface_execution_rows(
        surface_exec,
        terminal_exec,
        issues,
        aggregates,
    )

    assert surface_exec[0]["surface_execution_status"] == "PERFORMANCE_MATRIX_SURFACE_EXECUTION_PASS"
    assert terminal_exec[0]["terminal_execution_status"] == "TERMINAL_MATRIX_DECISION_EXECUTION_PRESERVED"
    assert issues == []
    assert sum(row["row_count"] for row in aggregates) == 2
    assert system[0]["total_execution_rows"] == 2


def test_expanded_market_proxy_r_performance_scores_ohlc_source(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    source_path = data_dir / "TEST_M15.csv"
    source_path.write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-01-01 00:00:00,100,101,99.8,100.5,1",
                "2026-01-01 00:15:00,100.5,102,100.4,101.5,1",
                "2026-01-01 00:30:00,101.5,103,101.4,102.5,1",
                "2026-01-01 00:45:00,102.5,104,102.4,103.5,1",
                "2026-01-01 01:00:00,103.5,105,103.4,104.5,1",
                "2026-01-01 01:15:00,104.5,106,104.4,105.5,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rows, meta = load_expanded_market_ohlc_rows(tmp_path, "data/TEST_M15.csv")
    source = {
        "source_path": "data/TEST_M15.csv",
        "source_symbol": "TEST",
        "source_timeframe": "M15",
        **meta,
    }

    score = score_expanded_market_source_session_horizon(
        source,
        rows,
        "ALL_SESSIONS",
        "h4",
        "LONG",
        {"cost_adjustment_r": 0.0, "stress_cost_adjustment_r": 0.0, "cost_proxy_status": "test"},
    )
    perf = expanded_market_performance_row_from_score(
        {
            "market_timeframe_session_horizon_expansion_row_id": "exp-1",
            "symbol": "TEST",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h4",
            "source_component": "test_component",
            "decision": "score",
        },
        source,
        "ALL_SESSIONS",
        "h4",
        "LONG",
        score,
        1,
        "market-1",
    )
    aggregates = aggregate_expanded_market_performance_rows([perf])

    assert score["score_status"] == "EXPANDED_MARKET_PROXY_R_SCORED"
    assert perf["gross_simulated_r"] is not None
    assert perf["effective_n"] > 0
    assert perf["source_path"] == "data/TEST_M15.csv"
    assert sum(row["row_count"] for row in aggregates) == 1
    assert aggregates[0]["effective_n"] == perf["effective_n"]


def test_expanded_market_proxy_r_noncomputable_row_keeps_missing_fields():
    row = expanded_market_noncomputable_row(
        {
            "market_timeframe_session_horizon_expansion_row_id": "exp-2",
            "symbol": "SYSTEM_LEVEL",
            "route_session": "REGISTERED_OR_CONFIGURED_SESSIONS_NOT_YET_ROUTED",
            "horizon_id": "NO_CURRENT_WORK_ORDER_HORIZON",
            "source_component": "data_inventory",
            "decision": "source-repair",
        },
        "EXPANSION_ROW_HAS_NO_NUMERIC_HORIZON_ROUTE",
        1,
        missing_fields=["numeric_horizon_id"],
    )

    assert row["input_expansion_matrix_row_id"] == "exp-2"
    assert row["missing_simulated_fields"] == ["numeric_horizon_id"]
    assert row["keep_kill_redesign_implement_decision"] == "REDESIGN_EXPANDED_MARKET_REPLAY_IMPLEMENTATION"


def _expanded_market_side_pair_input(row_id, side, cost_adjusted_r):
    return {
        "expanded_market_performance_row_id": row_id,
        "input_expansion_matrix_row_id": "exp-side-1",
        "input_market_population_row_id": "market-side-1",
        "source_path": "data/TEST_M15.csv",
        "source_file_sha256": "abc123",
        "symbol": "TEST",
        "source_symbol": "TEST",
        "market_timeframe": "M15",
        "route_session": "london_kz",
        "horizon_id": "h16",
        "seed_source_component": "unit_test",
        "side": side,
        "cost_adjusted_simulated_r": cost_adjusted_r,
        "gross_simulated_r": cost_adjusted_r + 0.01,
        "stress_simulated_r": cost_adjusted_r - 0.01,
        "effective_n": 30,
        "duplicate_row_count": 0,
        "concentration_top_month_share": 0.25,
        "path_order_counts": {"HORIZON_CLOSE_TARGET_PROXY_RESULT": 20, "HORIZON_CLOSE_STOP_PROXY_RESULT": 10},
        "win_count": 20 if cost_adjusted_r > 0 else 10,
        "loss_count": 10 if cost_adjusted_r > 0 else 20,
        "zero_count": 0,
    }


def test_expanded_market_side_pair_robustness_scores_long_short_pair():
    long_row = _expanded_market_side_pair_input("perf-long", "LONG", 0.25)
    short_row = _expanded_market_side_pair_input("perf-short", "SHORT", -0.10)

    pairs, issues = expanded_market_side_pair_rows([long_row, short_row])
    aggregates = aggregate_expanded_market_side_pair_rows(pairs)
    system = expanded_market_system_side_pair_rows(pairs, aggregates, issues, 2)

    assert issues == []
    assert len(pairs) == 1
    assert pairs[0]["winner_side"] == "LONG"
    assert pairs[0]["side_edge_spread_cost_adjusted_r"] == 0.35
    assert pairs[0]["keep_kill_redesign_implement_decision"] == "IMPLEMENT_EXPANDED_MARKET_SIDE_FILTER"
    assert sum(row["row_count"] for row in aggregates) == 1
    assert system[0]["side_pair_rows"] == 1


def test_expanded_market_side_pair_robustness_preserves_unpaired_issue_row():
    long_row = _expanded_market_side_pair_input("perf-long-only", "LONG", 0.25)

    pairs, issues = expanded_market_side_pair_rows([long_row])

    assert pairs == []
    assert len(issues) == 1
    assert issues[0]["input_performance_row_id"] == "perf-long-only"
    assert issues[0]["missing_side"] == "SHORT"


def test_expanded_market_temporal_robustness_replays_side_pair_folds(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    source_path = data_dir / "TEST_M15.csv"
    source_path.write_text(
        "\n".join(
            ["time,open,high,low,close,volume"]
            + [
                f"2026-01-01 {hour:02d}:00:00,{100 + hour},{101 + hour},{99 + hour},{100.5 + hour},1"
                for hour in range(30)
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    ohlc_rows, _ = load_expanded_market_ohlc_rows(tmp_path, "data/TEST_M15.csv")
    long_perf = _expanded_market_side_pair_input("perf-long", "LONG", 0.25)
    short_perf = _expanded_market_side_pair_input("perf-short", "SHORT", -0.10)
    long_perf.update(
        {
            "source_path": "data/TEST_M15.csv",
            "market_timeframe": "M15",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h4",
            "cost_adjustment_r": 0.0,
            "stress_cost_adjustment_r": 0.0,
        }
    )
    short_perf.update(
        {
            "source_path": "data/TEST_M15.csv",
            "market_timeframe": "M15",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h4",
            "cost_adjustment_r": 0.0,
            "stress_cost_adjustment_r": 0.0,
        }
    )
    side_pairs, _ = expanded_market_side_pair_rows([long_perf, short_perf])
    profiles = {
        "perf-long": expanded_market_temporal_profile(long_perf, ohlc_rows),
        "perf-short": expanded_market_temporal_profile(short_perf, ohlc_rows),
    }

    temporal_rows, fold_rows, issues = expanded_market_temporal_pair_rows(side_pairs, profiles)
    aggregates = aggregate_expanded_market_temporal_rows(temporal_rows)
    system = expanded_market_system_temporal_rows(temporal_rows, fold_rows, aggregates, issues, len(side_pairs))

    assert issues == []
    assert len(temporal_rows) == 1
    assert len(fold_rows) == 4
    assert temporal_rows[0]["overall_winner_side"] == "LONG"
    assert temporal_rows[0]["winner_consistency_share"] == 1.0
    assert sum(row["row_count"] for row in aggregates) == 1
    assert system[0]["temporal_fold_rows"] == 4


def test_expanded_market_intrabar_path_result_identifies_target_and_ambiguous():
    target_first_rows = [
        {"close": 100.0, "high": 100.2, "low": 99.8},
        {"close": 101.0, "high": 101.2, "low": 100.4},
        {"close": 101.5, "high": 101.7, "low": 101.0},
    ]
    ambiguous_rows = [
        {"close": 100.0, "high": 100.2, "low": 99.8},
        {"close": 100.1, "high": 101.2, "low": 98.8},
    ]

    target = expanded_market_intrabar_path_result(target_first_rows, 0, 2, "LONG", 1.0)
    ambiguous = expanded_market_intrabar_path_result(ambiguous_rows, 0, 1, "LONG", 1.0)

    assert target[0] == "TARGET_FIRST_INTRABAR_PATH"
    assert target[1] == 1.0
    assert ambiguous[0] == "AMBIGUOUS_TARGET_AND_STOP_SAME_BAR"
    assert ambiguous[1] == 0.0


def test_expanded_market_intrabar_geometry_profile_scores_ohlc_source(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    source_path = data_dir / "TEST_M15.csv"
    source_path.write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-01-01 00:00:00,100,100.2,99.8,100,1",
                "2026-01-01 00:15:00,100,101.2,100.4,101,1",
                "2026-01-01 00:30:00,101,102.2,100.8,102,1",
                "2026-01-01 00:45:00,102,103.2,101.8,103,1",
                "2026-01-01 01:00:00,103,104.2,102.8,104,1",
                "2026-01-01 01:15:00,104,105.2,103.8,105,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rows, _ = load_expanded_market_ohlc_rows(tmp_path, "data/TEST_M15.csv")
    performance_row = _expanded_market_side_pair_input("perf-long", "LONG", 0.25)
    performance_row.update(
        {
            "expanded_market_performance_row_id": "perf-long",
            "source_path": "data/TEST_M15.csv",
            "market_timeframe": "M15",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h2",
            "cost_adjustment_r": 0.0,
            "stress_cost_adjustment_r": 0.0,
            "seed_source_component": "unit_test",
        }
    )

    profile = expanded_market_intrabar_profile(performance_row, rows)
    geometry = expanded_market_intrabar_geometry_row_from_profile(performance_row, profile, 1)
    aggregates = aggregate_expanded_market_intrabar_rows([geometry])

    assert profile["profile_status"] == "EXPANDED_MARKET_INTRABAR_GEOMETRY_REPLAYED"
    assert geometry["target_first_count"] > 0
    assert geometry["cost_adjusted_simulated_r"] is not None
    assert sum(row["row_count"] for row in aggregates) == 1


def test_expanded_market_implementation_selection_requires_aligned_evidence():
    pair = {
        "side_pair_robustness_row_id": "pair-1",
        "input_long_performance_row_id": "perf-long",
        "input_short_performance_row_id": "perf-short",
        "symbol": "TEST",
        "source_symbol": "TEST",
        "market_timeframe": "M15",
        "route_session": "london_kz",
        "horizon_id": "h16",
        "source_component": "unit_test",
        "source_path": "data/TEST_M15.csv",
        "source_file_sha256": "abc123",
        "winner_side": "LONG",
        "loser_side": "SHORT",
        "side_edge_spread_cost_adjusted_r": 0.45,
        "effective_n": 50,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_SIDE_FILTER",
    }
    temporal = {
        "temporal_robustness_row_id": "temporal-1",
        "input_side_pair_robustness_row_id": "pair-1",
        "winner_consistency_share": 1.0,
        "positive_winner_fold_share": 1.0,
        "recent_half_winner_cost_adjusted_simulated_r": 0.20,
        "recent_quarter_winner_cost_adjusted_simulated_r": 0.25,
        "min_test_effective_n": 40,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_TEMPORAL_SIDE_FILTER",
    }
    selected = {
        "intrabar_geometry_row_id": "intrabar-long",
        "input_expanded_market_performance_row_id": "perf-long",
        "cost_adjusted_simulated_r": 0.30,
        "target_first_count": 35,
        "stop_first_count": 10,
        "neither_count": 5,
        "ambiguous_count": 0,
        "effective_n": 50,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_INTRABAR_SCORER",
    }
    rejected = {
        "intrabar_geometry_row_id": "intrabar-short",
        "input_expanded_market_performance_row_id": "perf-short",
        "cost_adjusted_simulated_r": -0.15,
        "target_first_count": 10,
        "stop_first_count": 35,
        "neither_count": 5,
        "ambiguous_count": 0,
        "effective_n": 50,
        "keep_kill_redesign_implement_decision": "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_INTRABAR",
    }

    rows, issues = expanded_market_implementation_selection_rows(
        [pair],
        {"pair-1": temporal},
        {"perf-long": selected, "perf-short": rejected},
    )
    aggregates = aggregate_expanded_market_implementation_selection_rows(rows)
    system = expanded_market_system_implementation_selection_rows(rows, aggregates, issues, 1)

    assert issues == []
    assert rows[0]["selected_side"] == "LONG"
    assert rows[0]["keep_kill_redesign_implement_decision"] == "IMPLEMENT_EXPANDED_MARKET_BRANCH_LOCAL_SIDE_FILTER"
    assert rows[0]["selected_minus_rejected_intrabar_cost_adjusted_r"] == 0.45
    assert sum(row["row_count"] for row in aggregates) == 1
    assert system[0]["implementation_selection_rows"] == 1


def test_expanded_market_code_candidates_preserve_implement_and_evidence_rows():
    implement = {
        "implementation_selection_row_id": "select-1",
        "input_side_pair_robustness_row_id": "pair-1",
        "input_temporal_robustness_row_id": "temporal-1",
        "input_selected_intrabar_geometry_row_id": "intrabar-long",
        "symbol": "TEST",
        "source_symbol": "TEST",
        "market_timeframe": "M15",
        "route_session": "london_kz",
        "horizon_id": "h16",
        "source_component": "unit_test",
        "source_path": "data/TEST_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "rejected_side": "SHORT",
        "selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "rejected_intrabar_cost_adjusted_simulated_r": -0.15,
        "selected_minus_rejected_intrabar_cost_adjusted_r": 0.45,
        "temporal_winner_consistency_share": 1.0,
        "temporal_positive_winner_fold_share": 1.0,
        "effective_n": 40,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_BRANCH_LOCAL_SIDE_FILTER",
    }
    redesign = {
        **implement,
        "implementation_selection_row_id": "select-2",
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_IMPLEMENTATION_SELECTION",
    }

    candidates, evidence, self_tests = expanded_market_code_candidate_rows([implement, redesign])
    aggregates = aggregate_expanded_market_code_candidate_rows(candidates, evidence)
    system = expanded_market_system_code_candidate_rows(candidates, evidence, self_tests, aggregates, 2)

    assert len(candidates) == 1
    assert len(evidence) == 1
    assert len(self_tests) == 1
    assert self_tests[0]["self_test_status"] == "CODE_CANDIDATE_SELF_TEST_PASS"
    assert expanded_market_candidate_matches_scope(candidates[0], candidates[0]["candidate_scope"])
    assert evidence[0]["keep_kill_redesign_implement_decision"] == "REDESIGN_EXPANDED_MARKET_CODE_EVIDENCE"
    assert sum(row["row_count"] for row in aggregates) == 2
    assert system[0]["code_candidate_rows"] == 1


def test_expanded_market_code_candidate_execution_detects_scope_leakage():
    implement = {
        "implementation_selection_row_id": "select-1",
        "symbol": "TEST",
        "source_symbol": "TEST",
        "market_timeframe": "M15",
        "route_session": "london_kz",
        "horizon_id": "h16",
        "source_component": "unit_test",
        "selected_side": "LONG",
        "selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "selected_minus_rejected_intrabar_cost_adjusted_r": 0.45,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_BRANCH_LOCAL_SIDE_FILTER",
    }
    redesign = {
        **implement,
        "implementation_selection_row_id": "select-2",
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_IMPLEMENTATION_SELECTION",
    }
    candidates, _, _ = expanded_market_code_candidate_rows([implement])

    executions, matches = execute_expanded_market_code_candidates(candidates, [implement, redesign])
    aggregates = aggregate_expanded_market_code_candidate_execution_rows(executions)
    system = expanded_market_system_code_candidate_execution_rows(executions, matches, aggregates, 1, 2)

    assert len(executions) == 1
    assert len(matches) == 2
    assert executions[0]["matched_implement_rows"] == 1
    assert executions[0]["matched_nonimplement_rows"] == 1
    assert executions[0]["keep_kill_redesign_implement_decision"] == "REDESIGN_EXPANDED_MARKET_CODE_CANDIDATE_SCOPE_LEAKAGE"
    assert sum(row["row_count"] for row in aggregates) == 1
    assert system[0]["code_candidate_match_rows"] == 2


def test_expanded_market_leakage_reduction_narrows_source_and_preserves_pass():
    implement = {
        "implementation_selection_row_id": "select-1",
        "symbol": "TEST",
        "source_symbol": "TEST",
        "market_timeframe": "M15",
        "route_session": "london_kz",
        "horizon_id": "h16",
        "source_component": "unit_test",
        "source_path": "data/TEST_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "rejected_intrabar_cost_adjusted_simulated_r": -0.15,
        "selected_minus_rejected_intrabar_cost_adjusted_r": 0.45,
        "temporal_winner_consistency_share": 1.0,
        "temporal_positive_winner_fold_share": 1.0,
        "selected_intrabar_target_first_count": 30,
        "selected_intrabar_stop_first_count": 5,
        "selected_intrabar_neither_count": 1,
        "selected_intrabar_ambiguous_count": 0,
        "effective_n": 36,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_BRANCH_LOCAL_SIDE_FILTER",
    }
    redesign = {
        **implement,
        "implementation_selection_row_id": "select-2",
        "source_path": "data/TEST_ALT_M15.csv",
        "source_file_sha256": "def456",
        "selected_intrabar_cost_adjusted_simulated_r": 0.10,
        "selected_minus_rejected_intrabar_cost_adjusted_r": 0.15,
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_IMPLEMENTATION_SELECTION",
    }
    candidates, _, _ = expanded_market_code_candidate_rows([implement])

    leaking_executions, _ = execute_expanded_market_code_candidates(candidates, [implement, redesign])
    reduced_rows, reduced_matches = expanded_market_leakage_reduction_rows(candidates, leaking_executions, [implement, redesign])
    aggregates = aggregate_expanded_market_leakage_reduction_rows(reduced_rows)
    system = expanded_market_system_leakage_reduction_rows(reduced_rows, reduced_matches, aggregates, 1)

    assert leaking_executions[0]["keep_kill_redesign_implement_decision"] == (
        "REDESIGN_EXPANDED_MARKET_CODE_CANDIDATE_SCOPE_LEAKAGE"
    )
    assert reduced_rows[0]["keep_kill_redesign_implement_decision"] == (
        "IMPLEMENT_EXPANDED_MARKET_LEAKAGE_REDUCED_CODE_CANDIDATE"
    )
    assert reduced_rows[0]["source_path"] == "data/TEST_M15.csv"
    assert reduced_rows[0]["matched_implement_rows"] == 1
    assert reduced_rows[0]["matched_nonimplement_rows"] == 0
    assert len(reduced_matches) == 1
    assert reduced_matches[0]["match_status"] == "REDUCED_IMPLEMENT_MATCH"
    assert sum(row["row_count"] for row in aggregates) == 1
    assert system[0]["reduced_pass_rows"] == 1

    clean_executions, _ = execute_expanded_market_code_candidates(candidates, [implement])
    preserved_rows, preserved_matches = expanded_market_leakage_reduction_rows(candidates, clean_executions, [implement])

    assert preserved_rows[0]["keep_kill_redesign_implement_decision"] == (
        "IMPLEMENT_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_PRESERVED"
    )
    assert preserved_rows[0]["source_file_sha256"] == "abc123"
    assert len(preserved_matches) == 1


def test_expanded_market_reduced_surface_execution_replays_clean_matches():
    implement = {
        "implementation_selection_row_id": "select-1",
        "symbol": "TEST",
        "source_symbol": "TEST",
        "market_timeframe": "M15",
        "route_session": "london_kz",
        "horizon_id": "h16",
        "source_component": "unit_test",
        "source_path": "data/TEST_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "rejected_intrabar_cost_adjusted_simulated_r": -0.15,
        "selected_minus_rejected_intrabar_cost_adjusted_r": 0.45,
        "temporal_winner_consistency_share": 1.0,
        "temporal_positive_winner_fold_share": 1.0,
        "selected_intrabar_target_first_count": 30,
        "selected_intrabar_stop_first_count": 5,
        "selected_intrabar_neither_count": 1,
        "selected_intrabar_ambiguous_count": 0,
        "effective_n": 36,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_BRANCH_LOCAL_SIDE_FILTER",
    }
    redesign = {
        **implement,
        "implementation_selection_row_id": "select-2",
        "source_file_sha256": "def456",
        "selected_intrabar_cost_adjusted_simulated_r": 0.10,
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_IMPLEMENTATION_SELECTION",
    }
    candidates, _, _ = expanded_market_code_candidate_rows([implement])
    leaking_executions, _ = execute_expanded_market_code_candidates(candidates, [implement, redesign])
    reduced_rows, reduced_matches = expanded_market_leakage_reduction_rows(candidates, leaking_executions, [implement, redesign])

    surfaces = expanded_market_reduced_surface_rows(reduced_rows)
    self_tests = expanded_market_reduced_surface_self_test_rows(surfaces, reduced_matches)
    executions, matches = execute_expanded_market_reduced_surfaces(surfaces, [implement, redesign])
    aggregates = aggregate_expanded_market_reduced_surface_execution_rows(executions)
    system = expanded_market_system_reduced_surface_execution_rows(surfaces, self_tests, executions, matches, aggregates, 1, 2)

    assert len(surfaces) == 1
    assert "source_file_sha256" in surfaces[0]["branch_local_code_expression"]
    assert self_tests[0]["self_test_status"] == "REDUCED_SURFACE_SELF_TEST_PASS"
    assert executions[0]["execution_status"] == "REDUCED_SURFACE_EXECUTION_PASS"
    assert executions[0]["matched_implement_rows"] == 1
    assert executions[0]["matched_nonimplement_rows"] == 0
    assert len(matches) == 1
    assert matches[0]["match_status"] == "REDUCED_SURFACE_IMPLEMENT_MATCH"
    assert sum(row["row_count"] for row in aggregates) == 1
    assert system[0]["execution_pass_rows"] == 1


def test_expanded_market_reduced_implementation_candidates_preserve_replay_geometry():
    implement = {
        "implementation_selection_row_id": "select-1",
        "symbol": "TEST",
        "source_symbol": "TEST",
        "market_timeframe": "M15",
        "route_session": "london_kz",
        "horizon_id": "h16",
        "source_component": "unit_test",
        "source_path": "data/TEST_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "rejected_intrabar_cost_adjusted_simulated_r": -0.15,
        "selected_minus_rejected_intrabar_cost_adjusted_r": 0.45,
        "temporal_winner_consistency_share": 1.0,
        "temporal_positive_winner_fold_share": 1.0,
        "selected_intrabar_target_first_count": 30,
        "selected_intrabar_stop_first_count": 5,
        "selected_intrabar_neither_count": 1,
        "selected_intrabar_ambiguous_count": 0,
        "effective_n": 36,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_BRANCH_LOCAL_SIDE_FILTER",
    }
    candidates, _, _ = expanded_market_code_candidate_rows([implement])
    clean_executions, _ = execute_expanded_market_code_candidates(candidates, [implement])
    reduced_rows, reduced_matches = expanded_market_leakage_reduction_rows(candidates, clean_executions, [implement])
    surfaces = expanded_market_reduced_surface_rows(reduced_rows)
    executions, matches = execute_expanded_market_reduced_surfaces(surfaces, [implement])

    implementation_candidates, evidence = expanded_market_reduced_implementation_candidate_rows(
        surfaces, executions, matches
    )
    aggregates = aggregate_expanded_market_reduced_implementation_candidate_rows(implementation_candidates)
    system = expanded_market_system_reduced_implementation_candidate_rows(
        implementation_candidates,
        evidence,
        aggregates,
        len(executions),
        len(matches),
    )

    assert len(implementation_candidates) == 1
    assert len(evidence) == 1
    assert implementation_candidates[0]["implementation_candidate_status"] == "IMPLEMENTATION_CANDIDATE_READY"
    assert implementation_candidates[0]["source_file_sha256"] == "abc123"
    assert implementation_candidates[0]["selected_intrabar_target_first_count_total"] == 30
    assert implementation_candidates[0]["selected_intrabar_stop_first_count_total"] == 5
    assert implementation_candidates[0]["target_first_share"] == round(30 / 36, 9)
    assert implementation_candidates[0]["average_selected_minus_rejected_intrabar_cost_adjusted_r"] == 0.45
    assert evidence[0]["matched_decision_family"] == "implement"
    assert sum(row["row_count"] for row in aggregates) == 1
    assert system[0]["ready_candidate_rows"] == 1


def test_expanded_market_final_branch_artifacts_execute_evidence_and_controls():
    implement = {
        "implementation_selection_row_id": "select-1",
        "symbol": "TEST",
        "source_symbol": "TEST",
        "market_timeframe": "M15",
        "route_session": "london_kz",
        "horizon_id": "h16",
        "source_component": "unit_test",
        "source_path": "data/TEST_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "rejected_intrabar_cost_adjusted_simulated_r": -0.15,
        "selected_minus_rejected_intrabar_cost_adjusted_r": 0.45,
        "temporal_winner_consistency_share": 1.0,
        "temporal_positive_winner_fold_share": 1.0,
        "selected_intrabar_target_first_count": 30,
        "selected_intrabar_stop_first_count": 5,
        "selected_intrabar_neither_count": 1,
        "selected_intrabar_ambiguous_count": 0,
        "effective_n": 36,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_BRANCH_LOCAL_SIDE_FILTER",
    }
    candidates, _, _ = expanded_market_code_candidate_rows([implement])
    clean_executions, _ = execute_expanded_market_code_candidates(candidates, [implement])
    reduced_rows, reduced_matches = expanded_market_leakage_reduction_rows(candidates, clean_executions, [implement])
    surfaces = expanded_market_reduced_surface_rows(reduced_rows)
    executions, matches = execute_expanded_market_reduced_surfaces(surfaces, [implement])
    implementation_candidates, evidence = expanded_market_reduced_implementation_candidate_rows(
        surfaces, executions, matches
    )

    artifacts = expanded_market_final_artifact_rows(implementation_candidates)
    evidence_executions, controls = expanded_market_final_artifact_evidence_execution_rows(artifacts, evidence)
    aggregates = aggregate_expanded_market_final_artifact_rows(artifacts)
    system = expanded_market_system_final_artifact_rows(
        artifacts,
        evidence_executions,
        controls,
        aggregates,
        len(implementation_candidates),
        len(evidence),
    )

    assert len(artifacts) == 1
    assert artifacts[0]["artifact_status"] == "FINAL_BRANCH_LOCAL_ARTIFACT_READY"
    assert artifacts[0]["source_path"] == "data/TEST_M15.csv"
    assert len(evidence_executions) == 1
    assert evidence_executions[0]["artifact_match"] is True
    assert len(controls) == 1
    assert controls[0]["control_rejected"] is True
    assert sum(row["row_count"] for row in aggregates) == 1
    assert system[0]["evidence_execution_pass_rows"] == 1
    assert system[0]["control_rejected_rows"] == 1


def test_expanded_market_portfolio_selection_preserves_concentration_redesigns():
    base_artifact = {
        "final_branch_artifact_row_id": "artifact-1",
        "input_implementation_candidate_row_id": "candidate-1",
        "artifact_family": "expanded_market_reduced_side_filter",
        "artifact_module_path": "src/research_infra/moonshot_expanded_market_final_branch_artifacts.py",
        "artifact_function_name": "final_scope_1",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "london_kz",
        "horizon_id": "h16",
        "source_component": "unit_test",
        "source_path": "data/TEST_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "branch_local_code_expression": "row scope",
        "artifact_scope_sha256": "scope-1",
        "matched_selection_rows": 1,
        "matched_implement_rows": 1,
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "average_selected_minus_rejected_intrabar_cost_adjusted_r": 0.45,
        "target_first_share": 0.60,
        "stop_first_share": 0.30,
        "target_first_minus_stop_first_share": 0.30,
        "matched_effective_n_sum": 36,
        "matched_effective_n_min": 36,
        "matched_effective_n_max": 36,
        "selected_intrabar_target_first_count_total": 30,
        "selected_intrabar_stop_first_count_total": 5,
        "selected_intrabar_neither_count_total": 1,
        "selected_intrabar_ambiguous_count_total": 0,
        "artifact_status": "FINAL_BRANCH_LOCAL_ARTIFACT_READY",
    }
    artifacts = [
        {**base_artifact, "final_branch_artifact_row_id": "artifact-1", "input_implementation_candidate_row_id": "candidate-1"},
        {**base_artifact, "final_branch_artifact_row_id": "artifact-2", "input_implementation_candidate_row_id": "candidate-2"},
        {
            **base_artifact,
            "final_branch_artifact_row_id": "artifact-3",
            "input_implementation_candidate_row_id": "candidate-3",
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "source_component": "other_component",
            "source_path": "data/OTHER_M15.csv",
            "source_file_sha256": "def456",
        },
    ]
    evidence = [
        {
            "final_branch_artifact_evidence_execution_row_id": f"evidence-{index}",
            "input_final_branch_artifact_row_id": artifact["final_branch_artifact_row_id"],
            "symbol": artifact["symbol"],
            "source_symbol": artifact["source_symbol"],
            "market_timeframe": artifact["market_timeframe"],
            "route_session": artifact["route_session"],
            "horizon_id": artifact["horizon_id"],
            "source_component": artifact["source_component"],
            "source_path": artifact["source_path"],
            "source_file_sha256": artifact["source_file_sha256"],
            "selected_side": artifact["selected_side"],
            "artifact_match": True,
            "selected_intrabar_cost_adjusted_simulated_r": 0.30,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.45,
            "effective_n": 36,
        }
        for index, artifact in enumerate(artifacts, start=1)
    ]

    selections, selection_evidence, concentration = expanded_market_portfolio_selection_rows(artifacts, evidence)
    aggregates = aggregate_expanded_market_portfolio_selection_rows(selections)
    system = expanded_market_system_portfolio_selection_rows(
        selections, selection_evidence, concentration, aggregates, len(artifacts), len(evidence)
    )

    assert len(selections) == 3
    assert len(selection_evidence) == 3
    assert any(row["keep_kill_redesign_implement_decision"].startswith("REDESIGN") for row in selections)
    assert any(row["keep_kill_redesign_implement_decision"].startswith("IMPLEMENT") for row in selections)
    assert any(row["concentration_status"] == "CONCENTRATION_GUARD_REQUIRED" for row in concentration)
    assert sum(row["row_count"] for row in aggregates) == 3
    assert system[0]["selected_rows"] == 1
    assert system[0]["preserved_redesign_or_kill_rows"] == 2


def test_expanded_market_deconcentration_executes_capacity_and_preserves_blocked_rows():
    base_selection = {
        "portfolio_artifact_selection_row_id": "selection-1",
        "input_final_branch_artifact_row_id": "artifact-1",
        "input_implementation_candidate_row_id": "candidate-1",
        "portfolio_selection_status": "PORTFOLIO_ARTIFACT_SELECTED",
        "symbol": "USDJPY",
        "source_symbol": "USDJPY",
        "market_timeframe": "M15",
        "route_session": "tokyo_kz",
        "horizon_id": "h16",
        "source_component": "base_component",
        "source_path": "data/USDJPY_M15.csv",
        "source_file_sha256": "base123",
        "selected_side": "LONG",
        "artifact_family": "expanded_market_reduced_side_filter",
        "artifact_function_name": "final_scope_1",
        "branch_local_code_expression": "base row scope",
        "artifact_scope_sha256": "scope-base",
        "matched_selection_rows": 1,
        "matched_implement_rows": 1,
        "evidence_execution_rows": 1,
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.20,
        "average_selected_minus_rejected_intrabar_cost_adjusted_r": 0.30,
        "target_first_share": 0.60,
        "stop_first_share": 0.30,
        "target_first_minus_stop_first_share": 0.30,
        "selection_precision": 1.0,
        "matched_effective_n_sum": 20,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PORTFOLIO_ARTIFACT",
        "follow_inverse_default_off_avoid_class": "follow",
    }
    guarded_a = {
        **base_selection,
        "portfolio_artifact_selection_row_id": "selection-2",
        "input_final_branch_artifact_row_id": "artifact-2",
        "input_implementation_candidate_row_id": "candidate-2",
        "portfolio_selection_status": "PORTFOLIO_ARTIFACT_PRESERVED_FOR_REDESIGN_OR_KILL",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "route_session": "london_kz",
        "source_component": "guard_component_a",
        "source_path": "data/XAUUSD_A_M15.csv",
        "source_file_sha256": "guard-a",
        "artifact_function_name": "final_scope_2",
        "branch_local_code_expression": "guard row scope a",
        "artifact_scope_sha256": "scope-guard-a",
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.50,
        "average_selected_minus_rejected_intrabar_cost_adjusted_r": 0.40,
        "target_first_minus_stop_first_share": 0.40,
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_PORTFOLIO_CONCENTRATION_GUARD_REQUIRED",
    }
    guarded_b = {
        **guarded_a,
        "portfolio_artifact_selection_row_id": "selection-3",
        "input_final_branch_artifact_row_id": "artifact-3",
        "input_implementation_candidate_row_id": "candidate-3",
        "source_component": "guard_component_b",
        "source_path": "data/XAUUSD_B_M15.csv",
        "source_file_sha256": "guard-b",
        "artifact_function_name": "final_scope_3",
        "branch_local_code_expression": "guard row scope b",
        "artifact_scope_sha256": "scope-guard-b",
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.10,
        "average_selected_minus_rejected_intrabar_cost_adjusted_r": 0.10,
        "target_first_minus_stop_first_share": 0.10,
    }
    selections = [base_selection, guarded_a, guarded_b]
    evidence = [
        {
            "portfolio_artifact_selection_evidence_row_id": f"selection-evidence-{index}",
            "input_portfolio_artifact_selection_row_id": row["portfolio_artifact_selection_row_id"],
            "input_final_branch_artifact_row_id": row["input_final_branch_artifact_row_id"],
            "input_final_branch_artifact_evidence_execution_row_id": f"artifact-evidence-{index}",
            "symbol": row["symbol"],
            "source_symbol": row["source_symbol"],
            "market_timeframe": row["market_timeframe"],
            "route_session": row["route_session"],
            "horizon_id": row["horizon_id"],
            "source_component": row["source_component"],
            "source_path": row["source_path"],
            "source_file_sha256": row["source_file_sha256"],
            "selected_side": row["selected_side"],
            "artifact_match": True,
            "selected_intrabar_cost_adjusted_simulated_r": row["average_selected_intrabar_cost_adjusted_simulated_r"],
            "selected_minus_rejected_intrabar_cost_adjusted_r": row[
                "average_selected_minus_rejected_intrabar_cost_adjusted_r"
            ],
            "effective_n": row["matched_effective_n_sum"],
        }
        for index, row in enumerate(selections, start=1)
    ]

    rows, deconcentration_evidence, capacity = expanded_market_deconcentration_rows(selections, evidence)
    aggregates = aggregate_expanded_market_deconcentration_rows(rows)
    system = expanded_market_system_deconcentration_rows(
        rows, deconcentration_evidence, capacity, aggregates, len(selections), len(evidence)
    )

    assert len(rows) == 3
    assert len(deconcentration_evidence) == 3
    assert rows[0]["keep_kill_redesign_implement_decision"] == "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATION_BASE_SELECTED"
    assert any(
        row["keep_kill_redesign_implement_decision"]
        == "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATION_CAPACITY_SELECTED"
        for row in rows
    )
    blocked = [
        row
        for row in rows
        if row["keep_kill_redesign_implement_decision"]
        == "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_CAPACITY_BLOCKED"
    ]
    assert len(blocked) == 1
    assert "symbol" in blocked[0]["capacity_blocking_dimensions"]
    assert sum(row["row_count"] for row in aggregates) == 3
    assert system[0]["base_selected_rows"] == 1
    assert system[0]["capacity_added_rows"] == 1
    assert system[0]["redesign_preserved_rows"] == 1


def test_expanded_market_final_review_recomputes_evidence_and_preserves_capacity_blocks():
    selected = {
        "deconcentration_row_id": "decon-1",
        "input_portfolio_artifact_selection_row_id": "selection-1",
        "input_final_branch_artifact_row_id": "artifact-1",
        "input_implementation_candidate_row_id": "candidate-1",
        "symbol": "USDJPY",
        "source_symbol": "USDJPY",
        "market_timeframe": "M15",
        "route_session": "tokyo_kz",
        "horizon_id": "h16",
        "source_component": "unit_component",
        "source_path": "data/USDJPY_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "artifact_family": "expanded_market_reduced_side_filter",
        "artifact_function_name": "final_scope_1",
        "branch_local_code_expression": "row scope",
        "artifact_scope_sha256": "scope-1",
        "base_selected_input": True,
        "capacity_selected": True,
        "capacity_blocking_dimensions": [],
        "evidence_execution_rows": 2,
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "average_selected_minus_rejected_intrabar_cost_adjusted_r": 0.40,
        "target_first_share": 0.60,
        "stop_first_share": 0.30,
        "target_first_minus_stop_first_share": 0.30,
        "matched_effective_n_sum": 80,
        "deconcentration_score": 1.0,
    }
    blocked = {
        **selected,
        "deconcentration_row_id": "decon-2",
        "input_portfolio_artifact_selection_row_id": "selection-2",
        "input_final_branch_artifact_row_id": "artifact-2",
        "input_implementation_candidate_row_id": "candidate-2",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "source_path": "data/XAUUSD_M15.csv",
        "source_file_sha256": "def456",
        "artifact_function_name": "final_scope_2",
        "artifact_scope_sha256": "scope-2",
        "base_selected_input": False,
        "capacity_selected": False,
        "capacity_blocking_dimensions": ["symbol"],
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.10,
        "average_selected_minus_rejected_intrabar_cost_adjusted_r": 0.20,
    }
    evidence = [
        {
            "deconcentration_evidence_row_id": "evidence-1",
            "input_deconcentration_row_id": "decon-1",
            "input_portfolio_artifact_selection_evidence_row_id": "selection-evidence-1",
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/USDJPY_M15.csv",
            "source_file_sha256": "abc123",
            "selected_side": "LONG",
            "artifact_match": True,
            "selected_intrabar_cost_adjusted_simulated_r": 0.20,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.30,
            "effective_n": 40,
        },
        {
            "deconcentration_evidence_row_id": "evidence-2",
            "input_deconcentration_row_id": "decon-1",
            "input_portfolio_artifact_selection_evidence_row_id": "selection-evidence-2",
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/USDJPY_M15.csv",
            "source_file_sha256": "abc123",
            "selected_side": "LONG",
            "artifact_match": True,
            "selected_intrabar_cost_adjusted_simulated_r": 0.40,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.50,
            "effective_n": 40,
        },
        {
            "deconcentration_evidence_row_id": "evidence-3",
            "input_deconcentration_row_id": "decon-2",
            "input_portfolio_artifact_selection_evidence_row_id": "selection-evidence-3",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "def456",
            "selected_side": "LONG",
            "artifact_match": True,
            "selected_intrabar_cost_adjusted_simulated_r": 0.10,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.20,
            "effective_n": 40,
        },
        {
            "deconcentration_evidence_row_id": "evidence-4",
            "input_deconcentration_row_id": "decon-2",
            "input_portfolio_artifact_selection_evidence_row_id": "selection-evidence-4",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "def456",
            "selected_side": "LONG",
            "artifact_match": True,
            "selected_intrabar_cost_adjusted_simulated_r": 0.10,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.20,
            "effective_n": 40,
        },
    ]
    capacity = [
        {
            "deconcentration_capacity_row_id": "capacity-1",
            "capacity_dimension": "symbol",
            "capacity_value": "USDJPY",
            "input_artifact_rows": 1,
            "selected_artifact_rows": 1,
            "redesign_preserved_rows": 0,
            "capacity_limit_rows": 2,
            "capacity_status": "CAPACITY_REMAINING",
        },
        {
            "deconcentration_capacity_row_id": "capacity-2",
            "capacity_dimension": "symbol",
            "capacity_value": "XAUUSD",
            "input_artifact_rows": 2,
            "selected_artifact_rows": 1,
            "redesign_preserved_rows": 1,
            "capacity_limit_rows": 1,
            "capacity_status": "CAPACITY_FILLED_OR_EXCEEDED_INPUT",
        },
    ]

    rows, review_evidence, review_capacity, issues = expanded_market_final_review_rows(
        [selected, blocked], evidence, capacity
    )
    aggregates = aggregate_expanded_market_final_review_rows(rows)
    system = expanded_market_system_final_review_rows(
        rows, review_evidence, review_capacity, issues, aggregates, 2, len(evidence), len(capacity)
    )

    assert len(rows) == 2
    assert len(review_evidence) == 4
    assert not issues
    assert rows[0]["recomputed_average_selected_intrabar_cost_adjusted_simulated_r"] == 0.30
    assert rows[0]["keep_kill_redesign_implement_decision"] == "IMPLEMENT_EXPANDED_MARKET_FINAL_REVIEW_BRANCH_LOCAL"
    assert rows[1]["keep_kill_redesign_implement_decision"] == "REDESIGN_EXPANDED_MARKET_FINAL_REVIEW_CAPACITY_BLOCKED"
    assert rows[1]["capacity_blocking_dimensions"] == ["symbol"]
    assert sum(row["row_count"] for row in aggregates) == 2
    assert system[0]["implement_rows"] == 1
    assert system[0]["redesign_rows"] == 1


def test_expanded_market_package_slices_preserve_members_evidence_and_redesign_controls():
    base = {
        "symbol": "USDJPY",
        "source_symbol": "USDJPY",
        "market_timeframe": "M15",
        "route_session": "tokyo_kz",
        "horizon_id": "h16",
        "source_component": "unit_component",
        "source_path": "data/USDJPY_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "artifact_function_name": "final_scope_1",
        "artifact_scope_sha256": "scope-1",
        "final_review_evidence_rows": 1,
        "row_average_selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "recomputed_average_selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "final_review_score": 0.70,
        "max_capacity_utilization": 0.50,
        "evidence_effective_n_sum": 40,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_FINAL_REVIEW_BRANCH_LOCAL",
    }
    review_rows = [
        {**base, "final_review_row_id": "review-1", "input_deconcentration_row_id": "decon-1"},
        {
            **base,
            "final_review_row_id": "review-2",
            "input_deconcentration_row_id": "decon-2",
            "source_path": "data/USDJPY_M15_B.csv",
            "source_file_sha256": "def456",
            "final_review_score": 0.80,
        },
        {
            **base,
            "final_review_row_id": "review-3",
            "input_deconcentration_row_id": "decon-3",
            "final_review_score": 0.20,
            "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_FINAL_REVIEW_CAPACITY_BLOCKED",
        },
    ]
    evidence = [
        {
            "final_review_evidence_row_id": f"review-evidence-{index}",
            "input_final_review_row_id": row["final_review_row_id"],
            "symbol": row["symbol"],
            "source_symbol": row["source_symbol"],
            "market_timeframe": row["market_timeframe"],
            "route_session": row["route_session"],
            "horizon_id": row["horizon_id"],
            "source_component": row["source_component"],
            "source_path": row["source_path"],
            "source_file_sha256": row["source_file_sha256"],
            "selected_side": row["selected_side"],
            "selected_intrabar_cost_adjusted_simulated_r": row[
                "row_average_selected_intrabar_cost_adjusted_simulated_r"
            ],
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.40,
            "effective_n": 40,
        }
        for index, row in enumerate(review_rows, start=1)
    ]

    packages, members, package_evidence, redesign, controls, self_tests = expanded_market_package_slice_rows(
        review_rows, evidence
    )
    aggregates = aggregate_expanded_market_package_rows(packages)
    system = expanded_market_system_package_rows(
        packages, members, package_evidence, redesign, controls, self_tests, aggregates, len(review_rows), len(evidence)
    )

    assert len(packages) == 1
    assert len(members) == 2
    assert len(package_evidence) == 3
    assert len(redesign) == 1
    assert controls[0]["same_scope_redesign_rows"] == 1
    assert controls[0]["package_expression_leaked_redesign_rows"] == 0
    assert self_tests[0]["self_test_status"] == "PACKAGE_SLICE_SELF_TEST_PASS"
    assert sum(row["package_member_rows"] for row in aggregates) == 2
    assert system[0]["package_member_rows"] == 2
    assert system[0]["package_redesign_carry_rows"] == 1


def test_expanded_market_package_review_executes_artifacts_and_preserves_redesign_evidence():
    package = {
        "package_slice_row_id": "package-1",
        "package_key_sha256": "pkg-sha",
        "symbol": "USDJPY",
        "market_timeframe": "M15",
        "route_session": "tokyo_kz",
        "horizon_id": "h16",
        "source_component": "unit_component",
        "selected_side": "LONG",
        "branch_local_package_expression": "row scope",
        "member_rows": 1,
        "package_evidence_rows": 1,
        "source_path_count": 1,
        "source_file_sha256_count": 1,
        "source_paths": ["data/USDJPY_M15.csv"],
        "source_file_sha256_values": ["abc123"],
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "average_recomputed_selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "average_final_review_score": 0.70,
        "min_final_review_score": 0.70,
        "max_final_review_score": 0.70,
        "average_max_capacity_utilization": 0.50,
        "evidence_effective_n_sum": 40,
        "same_scope_redesign_rows": 1,
    }
    member = {
        "package_member_row_id": "member-1",
        "input_package_slice_row_id": "package-1",
        "input_final_review_row_id": "review-1",
        "input_deconcentration_row_id": "decon-1",
        "symbol": "USDJPY",
        "source_symbol": "USDJPY",
        "market_timeframe": "M15",
        "route_session": "tokyo_kz",
        "horizon_id": "h16",
        "source_component": "unit_component",
        "source_path": "data/USDJPY_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "artifact_function_name": "final_scope_1",
        "artifact_scope_sha256": "scope-1",
        "final_review_score": 0.70,
        "row_average_selected_intrabar_cost_adjusted_simulated_r": 0.30,
    }
    evidence = [
        {
            "package_evidence_row_id": "evidence-1",
            "input_package_slice_row_id": "package-1",
            "input_final_review_row_id": "review-1",
            "input_final_review_evidence_row_id": "review-evidence-1",
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/USDJPY_M15.csv",
            "source_file_sha256": "abc123",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.30,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.40,
            "effective_n": 40,
        },
        {
            "package_evidence_row_id": "evidence-2",
            "input_package_slice_row_id": None,
            "input_final_review_row_id": "review-2",
            "input_final_review_evidence_row_id": "review-evidence-2",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "def456",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.10,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.20,
            "effective_n": 40,
        },
    ]
    redesign = [
        {
            "package_redesign_carry_row_id": "redesign-1",
            "input_final_review_row_id": "review-2",
            "input_deconcentration_row_id": "decon-2",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "def456",
            "selected_side": "LONG",
            "capacity_blocking_dimensions": ["symbol"],
            "final_review_score": 0.20,
            "final_review_evidence_rows": 1,
        }
    ]
    control = {
        "package_control_row_id": "control-1",
        "input_package_slice_row_id": "package-1",
        "same_scope_redesign_rows": 1,
        "package_expression_rejected_redesign_rows": 1,
        "package_expression_leaked_redesign_rows": 0,
        "control_status": "PACKAGE_CONTROL_PASS",
    }
    self_test = {
        "package_self_test_row_id": "self-test-1",
        "input_package_slice_row_id": "package-1",
        "positive_member_rows": 1,
        "positive_package_match_rows": 1,
        "self_test_status": "PACKAGE_SLICE_SELF_TEST_PASS",
    }

    artifacts, member_exec, evidence_exec, redesign_exec, control_exec = expanded_market_package_review_execution_rows(
        [package], [member], evidence, redesign, [control], [self_test]
    )
    aggregates = aggregate_expanded_market_package_review_rows(artifacts)
    system = expanded_market_system_package_review_execution_rows(
        artifacts, member_exec, evidence_exec, redesign_exec, control_exec, aggregates, 1, 1, len(evidence), 1
    )

    assert len(artifacts) == 1
    assert artifacts[0]["package_review_execution_status"] == "PACKAGE_REVIEW_EXECUTION_PASS"
    assert len(member_exec) == 1
    assert len(evidence_exec) == 2
    assert any(row["package_review_evidence_execution_status"] == "PACKAGE_REVIEW_EVIDENCE_PRESERVED" for row in evidence_exec)
    assert len(redesign_exec) == 1
    assert len(control_exec) == 1
    assert sum(row["member_rows"] for row in aggregates) == 1
    assert system[0]["artifact_pass_rows"] == 1
    assert system[0]["evidence_pass_rows"] == 1


def test_expanded_market_package_review_preservation_keeps_candidates_and_terminal_rows():
    artifact = {
        "package_review_artifact_row_id": "artifact-1",
        "input_package_slice_row_id": "package-1",
        "package_key_sha256": "pkg-sha",
        "symbol": "USDJPY",
        "market_timeframe": "M15",
        "route_session": "tokyo_kz",
        "horizon_id": "h16",
        "source_component": "unit_component",
        "selected_side": "LONG",
        "branch_local_package_expression": "row scope",
        "package_artifact_expression_sha256": "expr-sha",
        "member_rows_executed": 1,
        "evidence_rows_executed": 1,
        "source_path_count": 1,
        "source_file_sha256_count": 1,
        "source_paths": ["data/USDJPY_M15.csv"],
        "source_file_sha256_values": ["abc123"],
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "average_recomputed_selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "average_final_review_score": 0.70,
        "min_final_review_score": 0.70,
        "max_final_review_score": 0.70,
        "average_max_capacity_utilization": 0.50,
        "evidence_effective_n_sum": 40,
        "same_scope_redesign_rows": 1,
        "package_review_execution_status": "PACKAGE_REVIEW_EXECUTION_PASS",
    }
    member = {
        "package_review_member_execution_row_id": "member-exec-1",
        "input_package_review_artifact_row_id": "artifact-1",
        "input_package_member_row_id": "member-1",
        "input_final_review_row_id": "review-1",
        "input_deconcentration_row_id": "decon-1",
        "symbol": "USDJPY",
        "source_symbol": "USDJPY",
        "market_timeframe": "M15",
        "route_session": "tokyo_kz",
        "horizon_id": "h16",
        "source_component": "unit_component",
        "source_path": "data/USDJPY_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "artifact_function_name": "final_scope_1",
        "artifact_scope_sha256": "scope-1",
        "final_review_score": 0.70,
        "row_average_selected_intrabar_cost_adjusted_simulated_r": 0.30,
    }
    evidence = [
        {
            "package_review_evidence_execution_row_id": "evidence-exec-1",
            "input_package_review_artifact_row_id": "artifact-1",
            "input_final_review_row_id": "review-1",
            "input_final_review_evidence_row_id": "review-evidence-1",
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/USDJPY_M15.csv",
            "source_file_sha256": "abc123",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.30,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.40,
            "effective_n": 40,
            "package_review_evidence_execution_status": "PACKAGE_REVIEW_EVIDENCE_EXECUTION_PASS",
        },
        {
            "package_review_evidence_execution_row_id": "evidence-exec-2",
            "input_package_review_artifact_row_id": None,
            "input_final_review_row_id": "review-2",
            "input_final_review_evidence_row_id": "review-evidence-2",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "def456",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.10,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.20,
            "effective_n": 40,
            "package_review_evidence_execution_status": "PACKAGE_REVIEW_EVIDENCE_PRESERVED",
        },
    ]
    redesign = [
        {
            "package_review_redesign_execution_row_id": "redesign-exec-1",
            "input_package_redesign_carry_row_id": "redesign-1",
            "input_final_review_row_id": "review-2",
            "input_deconcentration_row_id": "decon-2",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "def456",
            "selected_side": "LONG",
            "capacity_blocking_dimensions": ["symbol"],
            "final_review_score": 0.20,
            "final_review_evidence_rows": 1,
        }
    ]

    candidates, members, preserved_evidence, preserved_redesign, self_tests = (
        expanded_market_package_review_preservation_rows([artifact], [member], evidence, redesign)
    )
    aggregates = aggregate_expanded_market_package_preservation_rows(candidates)
    system = expanded_market_system_package_preservation_rows(
        candidates, members, preserved_evidence, preserved_redesign, self_tests, aggregates, 1, 1, len(evidence), 1
    )

    assert len(candidates) == 1
    assert candidates[0]["preservation_status"] == "PACKAGE_REVIEW_PRESERVATION_READY"
    assert len(members) == 1
    assert len(preserved_evidence) == 2
    assert len(preserved_redesign) == 1
    assert self_tests[0]["self_test_status"] == "PACKAGE_REVIEW_PRESERVATION_SELF_TEST_PASS"
    assert sum(row["member_rows"] for row in aggregates) == 1
    assert system[0]["ready_candidate_rows"] == 1


def test_expanded_market_final_implementation_decisions_preserve_all_rows():
    candidate = {
        "package_preservation_candidate_row_id": "candidate-1",
        "input_package_review_artifact_row_id": "artifact-1",
        "input_package_slice_row_id": "package-1",
        "package_key_sha256": "pkg-sha",
        "symbol": "USDJPY",
        "market_timeframe": "M15",
        "route_session": "tokyo_kz",
        "horizon_id": "h16",
        "source_component": "unit_component",
        "selected_side": "LONG",
        "branch_local_package_expression": "row scope",
        "package_artifact_expression_sha256": "expr-sha",
        "member_rows_preserved": 1,
        "evidence_rows_preserved": 1,
        "source_path_count": 1,
        "source_file_sha256_count": 1,
        "source_paths": ["data/USDJPY_M15.csv"],
        "source_file_sha256_values": ["abc123"],
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "average_recomputed_selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "average_final_review_score": 0.70,
        "min_final_review_score": 0.70,
        "max_final_review_score": 0.70,
        "average_max_capacity_utilization": 0.50,
        "evidence_effective_n_sum": 40,
        "same_scope_redesign_rows": 1,
        "preservation_status": "PACKAGE_REVIEW_PRESERVATION_READY",
    }
    member = {
        "package_preservation_member_row_id": "member-1",
        "input_package_preservation_candidate_row_id": "candidate-1",
        "input_final_review_row_id": "review-1",
        "input_deconcentration_row_id": "decon-1",
        "symbol": "USDJPY",
        "source_symbol": "USDJPY",
        "market_timeframe": "M15",
        "route_session": "tokyo_kz",
        "horizon_id": "h16",
        "source_component": "unit_component",
        "source_path": "data/USDJPY_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "artifact_function_name": "final_scope_1",
        "artifact_scope_sha256": "scope-1",
        "final_review_score": 0.70,
        "row_average_selected_intrabar_cost_adjusted_simulated_r": 0.30,
    }
    evidence = [
        {
            "package_preservation_evidence_row_id": "evidence-1",
            "input_package_preservation_candidate_row_id": "candidate-1",
            "input_final_review_row_id": "review-1",
            "input_final_review_evidence_row_id": "review-evidence-1",
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/USDJPY_M15.csv",
            "source_file_sha256": "abc123",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.30,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.40,
            "effective_n": 40,
            "package_review_evidence_execution_status": "PACKAGE_REVIEW_EVIDENCE_EXECUTION_PASS",
        },
        {
            "package_preservation_evidence_row_id": "evidence-2",
            "input_package_preservation_candidate_row_id": None,
            "input_final_review_row_id": "review-2",
            "input_final_review_evidence_row_id": "review-evidence-2",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "def456",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.10,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.20,
            "effective_n": 20,
            "package_review_evidence_execution_status": "PACKAGE_REVIEW_EVIDENCE_PRESERVED",
        },
    ]
    redesign = [
        {
            "package_preservation_redesign_row_id": "redesign-1",
            "input_final_review_row_id": "review-2",
            "input_deconcentration_row_id": "decon-2",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "def456",
            "selected_side": "LONG",
            "capacity_blocking_dimensions": ["symbol"],
            "final_review_score": 0.20,
            "final_review_evidence_rows": 1,
        }
    ]

    decisions, members, final_evidence, final_redesign, controls = (
        expanded_market_final_implementation_decision_rows([candidate], [member], evidence, redesign)
    )
    aggregates = aggregate_expanded_market_final_implementation_decision_rows(decisions)
    system = expanded_market_system_final_implementation_decision_rows(
        decisions, members, final_evidence, final_redesign, controls, aggregates, 1, 1, len(evidence), 1
    )

    assert len(decisions) == 1
    assert decisions[0]["final_implementation_decision_status"] == "FINAL_IMPLEMENTATION_DECISION_READY"
    assert len(members) == 1
    assert len(final_evidence) == 2
    assert len(final_redesign) == 1
    assert len(controls) == 1
    assert {row["final_implementation_evidence_status"] for row in final_evidence} == {
        "FINAL_IMPLEMENTATION_EVIDENCE_DECISION_PASS",
        "FINAL_IMPLEMENTATION_EVIDENCE_UNPACKAGED",
    }
    assert sum(row["member_rows"] for row in aggregates) == 1
    assert system[0]["ready_final_implementation_decision_rows"] == 1
    assert system[0]["unpackaged_evidence_rows"] == 1


def test_expanded_market_unpackaged_evidence_resolution_builds_repackage_candidates():
    evidence = [
        {
            "final_implementation_evidence_row_id": "final-evidence-1",
            "input_final_implementation_decision_row_id": "decision-1",
            "input_package_preservation_candidate_row_id": "candidate-1",
            "input_package_preservation_evidence_row_id": "evidence-1",
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": "data/USDJPY_M15.csv",
            "source_file_sha256": "abc123",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.30,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.40,
            "effective_n": 40,
            "final_implementation_evidence_status": "FINAL_IMPLEMENTATION_EVIDENCE_DECISION_PASS",
        },
        {
            "final_implementation_evidence_row_id": "final-evidence-2",
            "input_final_implementation_decision_row_id": None,
            "input_package_preservation_candidate_row_id": None,
            "input_package_preservation_evidence_row_id": "evidence-2",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "ny_kz",
            "horizon_id": "h8",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "def456",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.25,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.30,
            "effective_n": 25,
            "final_implementation_evidence_status": "FINAL_IMPLEMENTATION_EVIDENCE_UNPACKAGED",
        },
    ]
    redesign = [
        {
            "final_implementation_redesign_row_id": "final-redesign-1",
            "input_package_preservation_redesign_row_id": "redesign-1",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "ny_kz",
            "horizon_id": "h8",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "def456",
            "selected_side": "LONG",
            "capacity_blocking_dimensions": ["symbol"],
            "final_review_score": 0.20,
        }
    ]

    resolution, candidates, terminal_redesign, aggregates = expanded_market_unpackaged_evidence_resolution_rows(
        evidence, redesign
    )
    system = expanded_market_system_unpackaged_evidence_resolution_rows(
        resolution, candidates, terminal_redesign, aggregates, len(evidence), len(redesign)
    )

    assert len(resolution) == 2
    assert len(candidates) == 1
    assert len(terminal_redesign) == 1
    assert {row["resolution_status"] for row in resolution} == {
        "UNPACKAGED_EVIDENCE_RESOLUTION_ALREADY_IMPLEMENTED",
        "UNPACKAGED_EVIDENCE_RESOLUTION_REPACKAGE_REQUIRED",
    }
    assert candidates[0]["effective_n_sum"] == 25
    assert system[0]["already_implemented_evidence_rows"] == 1
    assert system[0]["repackage_required_evidence_rows"] == 1


def test_expanded_market_repackage_execution_verifies_source_and_preserves_rows(tmp_path):
    source = tmp_path / "data" / "XAUUSD_M15.csv"
    source.parent.mkdir()
    source.write_text("time,open,high,low,close\n2026-01-01,1,2,0,1.5\n", encoding="utf-8")
    import hashlib

    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    candidate = {
        "unpackaged_repackage_candidate_row_id": "repackage-1",
        "symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "selected_side": "LONG",
        "source_path": "data/XAUUSD_M15.csv",
        "source_file_sha256": source_hash,
        "unpackaged_evidence_rows": 1,
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.25,
        "min_selected_intrabar_cost_adjusted_simulated_r": 0.25,
        "max_selected_intrabar_cost_adjusted_simulated_r": 0.25,
        "effective_n_sum": 25,
    }
    resolution = [
        {
            "unpackaged_evidence_resolution_row_id": "resolution-1",
            "input_final_implementation_evidence_row_id": "final-evidence-1",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "ny_kz",
            "horizon_id": "h8",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": source_hash,
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.25,
            "selected_minus_rejected_intrabar_cost_adjusted_r": 0.30,
            "effective_n": 25,
            "resolution_status": "UNPACKAGED_EVIDENCE_RESOLUTION_REPACKAGE_REQUIRED",
        },
        {
            "unpackaged_evidence_resolution_row_id": "resolution-2",
            "input_final_implementation_evidence_row_id": "final-evidence-2",
            "input_final_implementation_decision_row_id": "decision-1",
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h8",
            "source_component": "unit_component",
            "source_path": "data/USDJPY_M15.csv",
            "source_file_sha256": "existing",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.15,
            "effective_n": 40,
            "resolution_status": "UNPACKAGED_EVIDENCE_RESOLUTION_ALREADY_IMPLEMENTED",
        },
    ]
    terminal = [
        {
            "unpackaged_terminal_redesign_row_id": "terminal-1",
            "input_final_implementation_redesign_row_id": "redesign-1",
            "input_package_preservation_redesign_row_id": "preserved-redesign-1",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "ny_kz",
            "horizon_id": "h8",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": source_hash,
            "selected_side": "LONG",
            "capacity_blocking_dimensions": ["symbol"],
            "final_review_score": 0.20,
        }
    ]

    executions, repackage_evidence, existing_evidence, terminal_rows, aggregates = (
        expanded_market_repackage_execution_rows([candidate], resolution, terminal, tmp_path)
    )
    system = expanded_market_system_repackage_execution_rows(
        executions, repackage_evidence, existing_evidence, terminal_rows, aggregates, 1, len(resolution), len(terminal)
    )

    assert len(executions) == 1
    assert executions[0]["repackage_execution_status"] == "UNPACKAGED_REPACKAGE_EXECUTION_PASS"
    assert executions[0]["source_file_hash_match"] is True
    assert len(repackage_evidence) == 1
    assert len(existing_evidence) == 1
    assert len(terminal_rows) == 1
    assert terminal_rows[0]["terminal_redesign_execution_status"] == "REPACKAGE_TERMINAL_REDESIGN_SOURCE_PROOF_PASS"
    assert sum(row["candidate_evidence_rows_executed"] for row in aggregates) == 1
    assert system[0]["repackage_execution_pass_rows"] == 1
    assert system[0]["existing_evidence_preservation_rows"] == 1


def test_expanded_market_repackage_final_decisions_preserve_execution_evidence_and_terminal_rows():
    execution = {
        "repackage_execution_row_id": "execution-1",
        "input_unpackaged_repackage_candidate_row_id": "candidate-1",
        "symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "selected_side": "LONG",
        "source_path": "data/XAUUSD_M15.csv",
        "source_file_sha256": "abc123",
        "source_path_exists": True,
        "source_file_hash_match": True,
        "candidate_evidence_rows_executed": 1,
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.25,
        "min_selected_intrabar_cost_adjusted_simulated_r": 0.25,
        "max_selected_intrabar_cost_adjusted_simulated_r": 0.25,
        "repackage_execution_status": "UNPACKAGED_REPACKAGE_EXECUTION_PASS",
    }
    evidence = [
        {
            "repackage_evidence_execution_row_id": "evidence-1",
            "input_repackage_execution_row_id": "execution-1",
            "input_unpackaged_evidence_resolution_row_id": "resolution-1",
            "input_final_implementation_evidence_row_id": "final-evidence-1",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "ny_kz",
            "horizon_id": "h8",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "abc123",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.25,
            "effective_n": 25,
            "repackage_evidence_execution_status": "REPACKAGE_EVIDENCE_EXECUTION_PASS",
        }
    ]
    existing = [
        {
            "existing_evidence_preservation_row_id": "existing-1",
            "input_unpackaged_evidence_resolution_row_id": "resolution-2",
            "input_final_implementation_evidence_row_id": "final-evidence-2",
            "input_final_implementation_decision_row_id": "decision-1",
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h8",
            "source_component": "unit_component",
            "source_path": "data/USDJPY_M15.csv",
            "source_file_sha256": "def456",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.15,
            "effective_n": 40,
        }
    ]
    terminal = [
        {
            "repackage_terminal_redesign_execution_row_id": "terminal-1",
            "input_unpackaged_terminal_redesign_row_id": "terminal-source-1",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "ny_kz",
            "horizon_id": "h8",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "abc123",
            "source_path_exists": True,
            "source_file_hash_match": True,
            "selected_side": "LONG",
            "capacity_blocking_dimensions": ["symbol"],
            "final_review_score": 0.20,
        }
    ]

    decisions, final_evidence, final_existing, final_terminal, controls, aggregates = (
        expanded_market_repackage_final_decision_rows([execution], evidence, existing, terminal)
    )
    system = expanded_market_system_repackage_final_decision_rows(
        decisions, final_evidence, final_existing, final_terminal, controls, aggregates, 1, 1, 1, 1
    )

    assert len(decisions) == 1
    assert decisions[0]["repackage_final_decision_status"] == "REPACKAGE_FINAL_DECISION_READY"
    assert len(final_evidence) == 1
    assert len(final_existing) == 1
    assert len(final_terminal) == 1
    assert len(controls) == 1
    assert sum(row["candidate_evidence_rows_decided"] for row in aggregates) == 1
    assert system[0]["ready_repackage_final_decision_rows"] == 1
    assert system[0]["evidence_pass_rows"] == 1


def test_expanded_market_unified_final_decisions_merge_package_and_repackage_without_duplicate_existing_rows():
    package_decision = {
        "final_implementation_decision_row_id": "package-decision-1",
        "symbol": "USDJPY",
        "market_timeframe": "M15",
        "route_session": "tokyo_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "selected_side": "LONG",
        "source_paths": ["data/USDJPY_M15.csv"],
        "source_file_sha256_values": ["pkg-hash"],
        "evidence_rows_decided": 1,
        "member_rows_decided": 1,
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.20,
        "recomputed_evidence_effective_n_sum": 40,
    }
    package_member = {
        "final_implementation_member_row_id": "package-member-1",
        "input_final_implementation_decision_row_id": "package-decision-1",
        "symbol": "USDJPY",
        "source_symbol": "USDJPY",
        "market_timeframe": "M15",
        "route_session": "tokyo_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "source_path": "data/USDJPY_M15.csv",
        "source_file_sha256": "pkg-hash",
        "selected_side": "LONG",
        "artifact_function_name": "fn",
        "artifact_scope_sha256": "scope",
    }
    package_evidence = [
        {
            "final_implementation_evidence_row_id": "package-evidence-1",
            "input_final_implementation_decision_row_id": "package-decision-1",
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "market_timeframe": "M15",
            "route_session": "tokyo_kz",
            "horizon_id": "h8",
            "source_component": "unit_component",
            "source_path": "data/USDJPY_M15.csv",
            "source_file_sha256": "pkg-hash",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.20,
            "effective_n": 40,
            "final_implementation_evidence_status": "FINAL_IMPLEMENTATION_EVIDENCE_DECISION_PASS",
        },
        {
            "final_implementation_evidence_row_id": "package-evidence-2",
            "input_final_implementation_decision_row_id": None,
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "ny_kz",
            "horizon_id": "h8",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "rep-hash",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.25,
            "effective_n": 25,
            "final_implementation_evidence_status": "FINAL_IMPLEMENTATION_EVIDENCE_UNPACKAGED",
        },
    ]
    repackage_decision = {
        "repackage_final_decision_row_id": "repackage-decision-1",
        "symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "selected_side": "LONG",
        "source_path": "data/XAUUSD_M15.csv",
        "source_file_sha256": "rep-hash",
        "candidate_evidence_rows_decided": 1,
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.25,
        "effective_n_sum_decided": 25,
    }
    repackage_evidence = [
        {
            "repackage_final_evidence_row_id": "repackage-evidence-1",
            "input_repackage_final_decision_row_id": "repackage-decision-1",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "ny_kz",
            "horizon_id": "h8",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "rep-hash",
            "selected_side": "LONG",
            "selected_intrabar_cost_adjusted_simulated_r": 0.25,
            "effective_n": 25,
        }
    ]
    repackage_existing = [{"repackage_final_existing_evidence_row_id": "existing-duplicate-1"}]
    terminal = [
        {
            "repackage_final_terminal_redesign_row_id": "terminal-1",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "ny_kz",
            "horizon_id": "h8",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "rep-hash",
            "selected_side": "LONG",
            "capacity_blocking_dimensions": ["symbol"],
        }
    ]

    decisions, members, evidence, terminal_rows, aggregates = expanded_market_unified_final_decision_rows(
        [package_decision],
        [package_member],
        package_evidence,
        [repackage_decision],
        repackage_evidence,
        repackage_existing,
        terminal,
    )
    system = expanded_market_system_unified_final_decision_rows(
        decisions, members, evidence, terminal_rows, aggregates, 1, 1, len(package_evidence), 1, 1, 1, 1
    )

    assert len(decisions) == 2
    assert len(members) == 1
    assert len(evidence) == 2
    assert len(terminal_rows) == 1
    assert {row["decision_origin"] for row in decisions} == {"package_final", "repackage_final"}
    assert {row["evidence_origin"] for row in evidence} == {"package_final", "repackage_final"}
    assert system[0]["repackage_existing_rows_deduplicated"] == 1
    assert system[0]["ready_unified_final_decision_rows"] == 2


def test_expanded_market_unified_numeric_evidence_joins_final_rows_to_performance_geometry(tmp_path):
    source_rel = "data/XAUUSD_M15.csv"
    source_file = tmp_path / source_rel
    source_file.parent.mkdir(parents=True)
    source_file.write_text("time,open,high,low,close\n2026-01-01,1,2,0,1.5\n", encoding="utf-8")
    source_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
    decision = {
        "unified_final_decision_row_id": "decision-1",
        "decision_origin": "package_final",
        "symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "selected_side": "LONG",
        "follow_inverse_default_off_avoid_class": "follow",
    }
    evidence = {
        "unified_final_evidence_row_id": "evidence-1",
        "input_unified_final_decision_row_id": "decision-1",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "source_path": source_rel,
        "source_file_sha256": source_hash,
        "selected_side": "LONG",
        "selected_intrabar_cost_adjusted_simulated_r": 0.2,
        "effective_n": 30,
        "follow_inverse_default_off_avoid_class": "follow",
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_FINAL_EVIDENCE",
    }
    terminal = {
        "unified_final_terminal_redesign_row_id": "terminal-1",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "source_path": source_rel,
        "source_file_sha256": source_hash,
        "selected_side": "LONG",
        "follow_inverse_default_off_avoid_class": "redesign",
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_UNIFIED_FINAL_TERMINAL_CAPACITY",
    }
    performance = {
        "expanded_market_performance_row_id": "performance-1",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "seed_source_component": "unit_component",
        "source_path": source_rel,
        "source_file_sha256": source_hash,
        "side": "LONG",
        "entry_reference": "source_bar_close_then_forward_horizon_path",
        "entry_reference_time": "2026-01-01",
        "proxy_entry_price": 100.0,
        "proxy_stop_price": 99.0,
        "proxy_target_price": 101.0,
        "proxy_denominator_price": 1.0,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.25,
        "cost_adjusted_simulated_r": 0.18,
        "stress_simulated_r": -0.1,
        "win_count": 18,
        "loss_count": 12,
        "zero_count": 0,
        "target_first_count": 18,
        "stop_first_count": 12,
        "neither_count": 0,
        "ambiguous_count": 0,
        "duplicate_row_count": 0,
        "effective_n": 30,
        "effective_n_after_duplicate_collapse": 30,
        "concentration_top_month_share": 0.2,
    }
    intrabar = {
        "intrabar_geometry_row_id": "intrabar-1",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "source_path": source_rel,
        "source_file_sha256": source_hash,
        "side": "LONG",
        "entry_reference": "source_bar_close_then_intrabar_high_low_path",
        "entry_reference_time": "2026-01-01",
        "proxy_entry_price": 100.0,
        "proxy_stop_price": 99.0,
        "proxy_target_price": 101.0,
        "proxy_denominator_price": 1.0,
        "path_order_result": "TARGET_FIRST_INTRABAR_PATH",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.28,
        "cost_adjusted_simulated_r": 0.2,
        "horizon_close_proxy_cost_adjusted_simulated_r": 0.18,
        "stress_simulated_r": -0.05,
        "average_win": 0.8,
        "average_loss": -0.7,
        "win_count": 18,
        "loss_count": 12,
        "zero_count": 0,
        "target_first_count": 18,
        "stop_first_count": 12,
        "neither_count": 0,
        "ambiguous_count": 0,
        "duplicate_row_count": 0,
        "effective_n": 30,
        "effective_n_after_duplicate_collapse": 30,
        "concentration_top_month_share": 0.2,
        "average_first_touch_bars": 2.0,
    }

    evidence_rows, terminal_rows, decision_rows, source_access_rows, aggregate_rows, issues = (
        expanded_market_unified_numeric_evidence_rows(
            [decision], [evidence], [terminal], [performance], [intrabar], tmp_path
        )
    )
    system = expanded_market_system_unified_numeric_evidence_rows(
        evidence_rows,
        terminal_rows,
        decision_rows,
        source_access_rows,
        aggregate_rows,
        issues,
        {"unit": True},
    )

    assert not issues
    assert evidence_rows[0]["numeric_evidence_status"] == "UNIFIED_NUMERIC_EVIDENCE_REPLAYED"
    assert evidence_rows[0]["input_expanded_market_performance_row_id"] == "performance-1"
    assert evidence_rows[0]["input_intrabar_geometry_row_id"] == "intrabar-1"
    assert evidence_rows[0]["cost_adjusted_simulated_r"] == 0.2
    assert terminal_rows[0]["keep_kill_redesign_implement_decision"] == "REDESIGN_EXPANDED_MARKET_UNIFIED_NUMERIC_TERMINAL"
    assert decision_rows[0]["cost_adjusted_simulated_r"] == 0.2
    assert source_access_rows[0]["source_access_status"] == "SOURCE_PATH_HASH_CONFIRMED"
    assert system[0]["rows_with_simulated_r"] == 2


def test_expanded_market_unified_stress_qualification_splits_underpowered_and_terminal_capacity():
    base = {
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "source_path": "data/XAUUSD_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "entry_reference": "source_bar_close_then_intrabar_high_low_path",
        "proxy_entry_price": 100.0,
        "proxy_stop_price": 99.0,
        "proxy_target_price": 101.0,
        "proxy_denominator_price": 1.0,
        "path_order_result": "TARGET_FIRST_INTRABAR_PATH",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.25,
        "cost_adjusted_simulated_r": 0.2,
        "stress_simulated_r": 0.1,
        "win_count": 90,
        "loss_count": 60,
        "zero_count": 0,
        "flat_count": 0,
        "no_fill_count": 0,
        "average_win": 0.8,
        "average_loss": -0.7,
        "target_first_count": 90,
        "stop_first_count": 60,
        "neither_count": 0,
        "ambiguous_count": 0,
        "effective_n": 150,
        "effective_n_after_duplicate_collapse": 150,
        "duplicate_row_count": 0,
        "concentration_top_month_share": 0.2,
        "source_access_status": "SOURCE_PATH_HASH_CONFIRMED",
    }
    evidence = {
        **base,
        "unified_numeric_evidence_row_id": "numeric-evidence-1",
        "input_unified_final_evidence_row_id": "evidence-1",
        "input_unified_final_decision_row_id": "decision-1",
        "numeric_row_kind": "unified_final_evidence",
    }
    terminal = {
        **base,
        "unified_numeric_evidence_row_id": "numeric-terminal-1",
        "input_unified_final_terminal_redesign_row_id": "terminal-1",
        "numeric_row_kind": "unified_terminal_redesign",
    }
    decision = {
        **base,
        "unified_numeric_decision_row_id": "numeric-decision-1",
        "input_unified_final_decision_row_id": "decision-1",
        "numeric_evidence_rows": 1,
        "source_path_count": 1,
        "source_hash_count": 1,
        "effective_n": 99,
        "effective_n_after_duplicate_collapse": 99,
    }

    evidence_rows, terminal_rows, decision_rows, aggregate_rows, issue_rows = (
        expanded_market_unified_stress_qualification_rows([evidence], [terminal], [decision])
    )
    system = expanded_market_system_unified_stress_qualification_rows(
        evidence_rows,
        terminal_rows,
        decision_rows,
        aggregate_rows,
        issue_rows,
        {"unit": True},
    )

    assert evidence_rows[0]["keep_kill_redesign_implement_decision"] == "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRESS_QUALIFIED"
    assert terminal_rows[0]["stress_blocking_reason"] == "terminal_capacity_not_performance_failure"
    assert decision_rows[0]["stress_blocking_reason"] == "underpowered_effective_n"
    assert len(issue_rows) == 1
    assert system[0]["qualified_evidence_rows"] == 1
    assert system[0]["qualified_decision_rows"] == 0


def test_expanded_market_unified_implementation_actions_preserve_qualified_and_redesign_rows():
    qualified = {
        "unified_stress_qualification_row_id": "stress-evidence-1",
        "input_unified_final_evidence_row_id": "evidence-1",
        "input_unified_final_decision_row_id": "decision-1",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "source_path": "data/XAUUSD_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "entry_reference": "source_bar_close_then_intrabar_high_low_path",
        "proxy_entry_price": 100.0,
        "proxy_stop_price": 99.0,
        "proxy_target_price": 101.0,
        "proxy_denominator_price": 1.0,
        "path_order_result": "TARGET_FIRST_INTRABAR_PATH",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.25,
        "cost_adjusted_simulated_r": 0.2,
        "stress_simulated_r": 0.1,
        "win_count": 90,
        "loss_count": 60,
        "zero_count": 0,
        "flat_count": 0,
        "no_fill_count": 0,
        "target_first_count": 90,
        "stop_first_count": 60,
        "neither_count": 0,
        "ambiguous_count": 0,
        "effective_n": 150,
        "effective_n_after_duplicate_collapse": 150,
        "duplicate_row_count": 0,
        "target_first_share": 0.6,
        "stop_first_share": 0.4,
        "target_stop_edge_share": 0.2,
        "ambiguous_share": 0.0,
        "concentration_top_month_share": 0.2,
        "stress_blocking_reason": "all_numeric_stress_checks_pass",
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRESS_QUALIFIED",
    }
    terminal = {
        **qualified,
        "unified_stress_qualification_row_id": "stress-terminal-1",
        "input_unified_final_terminal_redesign_row_id": "terminal-1",
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_UNIFIED_STRESS_TERMINAL_CAPACITY",
        "stress_blocking_reason": "terminal_capacity_not_performance_failure",
    }
    decision = {
        **qualified,
        "unified_stress_decision_row_id": "stress-decision-1",
        "input_unified_numeric_decision_row_id": "numeric-decision-1",
        "source_path": None,
        "source_file_sha256": None,
    }

    evidence_actions, terminal_actions, decision_actions, redesign_actions, aggregates = (
        expanded_market_unified_implementation_action_rows([qualified], [terminal], [decision])
    )
    system = expanded_market_system_unified_implementation_action_rows(
        evidence_actions,
        terminal_actions,
        decision_actions,
        redesign_actions,
        aggregates,
        {"unit": True},
    )

    assert evidence_actions[0]["branch_local_action_status"] == "SCORER_ROW_ACTION_READY"
    assert evidence_actions[0]["keep_kill_redesign_implement_decision"] == "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SCORER_ROW"
    assert terminal_actions[0]["branch_local_action_status"] == "TERMINAL_CAPACITY_REDESIGN_ACTION"
    assert decision_actions[0]["branch_local_action_status"] == "DECISION_SCOPE_ACTION_READY"
    assert len(redesign_actions) == 1
    assert evidence_actions[0]["branch_local_action_expression_sha256"]
    assert system[0]["implementation_action_rows"] == 2
    assert system[0]["terminal_capacity_action_rows"] == 1


def test_expanded_market_unified_action_surfaces_group_implementation_actions_and_preserve_redesign():
    action = {
        "unified_implementation_action_row_id": "action-1",
        "action_row_kind": "evidence",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "source_path": "data/XAUUSD_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "cost_adjusted_simulated_r": 0.2,
        "stress_simulated_r": 0.1,
        "effective_n": 150,
        "target_first_count": 90,
        "stop_first_count": 60,
        "ambiguous_count": 0,
        "branch_local_action_family": "expanded_market_stress_qualified_scorer_row",
        "branch_local_action_scope": {"symbol": "XAUUSD"},
        "branch_local_action_scope_sha256": "scope-1",
        "branch_local_action_expression": "row.get('symbol') == 'XAUUSD'",
        "branch_local_action_expression_sha256": "expr-1",
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SCORER_ROW",
    }
    redesign = {
        "unified_redesign_action_row_id": "redesign-1",
        "input_unified_implementation_action_row_id": "action-redesign-1",
        "action_row_kind": "terminal",
        "symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "source_path": "data/XAUUSD_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "stress_blocking_reason": "terminal_capacity_not_performance_failure",
        "cost_adjusted_simulated_r": 0.2,
        "stress_simulated_r": 0.1,
        "effective_n": 150,
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_TERMINAL_CAPACITY",
        "follow_inverse_default_off_avoid_class": "redesign",
    }

    surfaces, members, self_tests, redesign_rows, aggregates = expanded_market_unified_action_surface_rows(
        [action], [], [redesign]
    )
    system = expanded_market_system_unified_action_surface_rows(
        surfaces, members, self_tests, redesign_rows, aggregates, {"unit": True}
    )

    assert len(surfaces) == 1
    assert surfaces[0]["action_surface_status"] == "ACTION_SURFACE_READY"
    assert members[0]["surface_member_match"] is True
    assert self_tests[0]["positive_scope_match"] is True
    assert self_tests[0]["negative_scope_mismatch_rejected"] is True
    assert len(redesign_rows) == 1
    assert system[0]["action_surface_rows"] == 1
    assert system[0]["surface_member_match_rows"] == 1


def test_expanded_market_unified_action_surface_execution_preserves_numeric_rows():
    action = {
        "unified_implementation_action_row_id": "action-1",
        "action_row_kind": "evidence",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "source_path": "data/XAUUSD_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "entry_reference": "source_bar_close_then_intrabar_high_low_path",
        "proxy_entry_price": 100.0,
        "proxy_stop_price": 99.0,
        "proxy_target_price": 101.0,
        "proxy_denominator_price": 1.0,
        "path_order_result": "TARGET_FIRST_INTRABAR_PATH",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.25,
        "cost_adjusted_simulated_r": 0.2,
        "stress_simulated_r": 0.1,
        "win_count": 90,
        "loss_count": 60,
        "flat_count": 0,
        "zero_count": 0,
        "no_fill_count": 0,
        "average_win": 0.8,
        "average_loss": -0.7,
        "target_first_count": 90,
        "stop_first_count": 60,
        "neither_count": 0,
        "ambiguous_count": 0,
        "effective_n": 150,
        "effective_n_after_duplicate_collapse": 150,
        "duplicate_row_count": 0,
        "target_first_share": 0.6,
        "stop_first_share": 0.4,
        "target_stop_edge_share": 0.2,
        "ambiguous_share": 0.0,
        "concentration_top_month_share": 0.2,
        "branch_local_action_family": "expanded_market_stress_qualified_scorer_row",
        "branch_local_action_scope": {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "M15",
            "route_session": "ny_kz",
            "horizon_id": "h8",
            "source_component": "unit_component",
            "source_path": "data/XAUUSD_M15.csv",
            "source_file_sha256": "abc123",
            "selected_side": "LONG",
            "minimum_cost_adjusted_simulated_r": 0.2,
            "minimum_stress_simulated_r": 0.1,
            "minimum_effective_n": 150,
            "minimum_target_stop_edge_share": 0.2,
            "maximum_ambiguous_share": 0.0,
            "maximum_concentration_top_month_share": 0.2,
        },
        "branch_local_action_scope_sha256": "scope-1",
        "branch_local_action_expression": "row.get('symbol') == 'XAUUSD'",
        "branch_local_action_expression_sha256": "expr-1",
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SCORER_ROW",
        "follow_inverse_default_off_avoid_class": "follow",
    }
    redesign_source = {
        **action,
        "unified_implementation_action_row_id": "action-redesign-1",
        "action_row_kind": "terminal",
        "branch_local_action_status": "TERMINAL_CAPACITY_REDESIGN_ACTION",
        "stress_blocking_reason": "terminal_capacity_not_performance_failure",
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_TERMINAL_CAPACITY",
        "follow_inverse_default_off_avoid_class": "redesign",
    }
    redesign = {
        "unified_redesign_action_row_id": "redesign-1",
        "input_unified_implementation_action_row_id": "action-redesign-1",
        "action_row_kind": "terminal",
        "symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "source_path": "data/XAUUSD_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "stress_blocking_reason": "terminal_capacity_not_performance_failure",
        "cost_adjusted_simulated_r": 0.2,
        "stress_simulated_r": 0.1,
        "effective_n": 150,
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_TERMINAL_CAPACITY",
        "follow_inverse_default_off_avoid_class": "redesign",
    }
    surfaces, members, self_tests, surface_redesigns, _ = expanded_market_unified_action_surface_rows(
        [action], [], [redesign]
    )
    surface_rows, member_rows, redesign_rows, aggregates, issues = (
        expanded_market_unified_action_surface_execution_rows(
            surfaces,
            members,
            surface_redesigns,
            [action],
            [],
            [redesign_source],
        )
    )
    system = expanded_market_system_unified_action_surface_execution_rows(
        surface_rows,
        member_rows,
        redesign_rows,
        aggregates,
        issues,
        {"unit": True},
    )

    assert not issues
    assert surface_rows[0]["execution_status"] == "ACTION_SURFACE_EXECUTION_PASS"
    assert member_rows[0]["execution_status"] == "ACTION_SURFACE_MEMBER_EXECUTION_PASS"
    assert member_rows[0]["gross_simulated_r"] == 0.25
    assert redesign_rows[0]["execution_status"] == "REDESIGN_ACTION_EXECUTION_PRESERVED_WITH_NUMERIC_PROOF"
    assert redesign_rows[0]["gross_simulated_r"] == 0.25
    assert system[0]["surface_execution_pass_rows"] == 1
    assert system[0]["member_execution_pass_rows"] == 1
    assert system[0]["redesign_execution_preserved_rows"] == 1


def test_expanded_market_unified_strict_action_surface_repair_hash_guards_broad_predicate():
    base = {
        "action_row_kind": "decision",
        "symbol": "XAUUSD",
        "source_symbol": None,
        "market_timeframe": "H1",
        "route_session": "london_core",
        "horizon_id": "h16",
        "source_component": "unit_component",
        "source_path": None,
        "source_file_sha256": None,
        "selected_side": "LONG",
        "entry_reference": None,
        "proxy_entry_price": None,
        "proxy_stop_price": None,
        "proxy_target_price": None,
        "proxy_denominator_price": None,
        "path_order_result": None,
        "fill_status": None,
        "gross_simulated_r": 0.2,
        "cost_adjusted_simulated_r": 0.18,
        "stress_simulated_r": 0.12,
        "win_count": 60,
        "loss_count": 40,
        "flat_count": 0,
        "zero_count": 0,
        "no_fill_count": 0,
        "average_win": 0.8,
        "average_loss": -0.7,
        "target_first_count": 60,
        "stop_first_count": 40,
        "neither_count": 0,
        "ambiguous_count": 0,
        "effective_n_after_duplicate_collapse": 100,
        "duplicate_row_count": 0,
        "target_first_share": 0.6,
        "stop_first_share": 0.4,
        "target_stop_edge_share": 0.2,
        "ambiguous_share": 0.0,
        "concentration_top_month_share": 0.2,
        "branch_local_action_family": "expanded_market_stress_qualified_decision_scope",
        "branch_local_action_expression": "row.get('symbol') == 'XAUUSD'",
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_DECISION_SCOPE",
        "follow_inverse_default_off_avoid_class": "follow",
    }
    low = {
        **base,
        "unified_implementation_action_row_id": "action-low",
        "effective_n": 100,
        "branch_local_action_scope": {
            "symbol": "XAUUSD",
            "source_symbol": None,
            "market_timeframe": "H1",
            "route_session": "london_core",
            "horizon_id": "h16",
            "source_component": "unit_component",
            "source_path": None,
            "source_file_sha256": None,
            "selected_side": "LONG",
            "minimum_cost_adjusted_simulated_r": 0.18,
            "minimum_stress_simulated_r": 0.12,
            "minimum_effective_n": 100,
            "minimum_target_stop_edge_share": 0.2,
            "maximum_ambiguous_share": 0.0,
            "maximum_concentration_top_month_share": 0.2,
        },
        "branch_local_action_scope_sha256": "scope-low",
        "branch_local_action_expression_sha256": "expr-low",
    }
    high = {
        **base,
        "unified_implementation_action_row_id": "action-high",
        "effective_n": 200,
        "effective_n_after_duplicate_collapse": 200,
        "branch_local_action_scope": {
            **low["branch_local_action_scope"],
            "minimum_effective_n": 200,
        },
        "branch_local_action_scope_sha256": "scope-high",
        "branch_local_action_expression_sha256": "expr-high",
    }
    surfaces, members, _, surface_redesigns, _ = expanded_market_unified_action_surface_rows(
        [low, high], [], []
    )
    low_surface_id = next(
        row["unified_action_surface_row_id"]
        for row in surfaces
        if row["action_surface_scope_sha256"] == "scope-low"
    )
    previous_issue = {
        "input_unified_action_surface_row_id": low_surface_id,
        "predicate_extra_match_rows": 1,
    }

    (
        strict_surfaces,
        strict_executions,
        member_executions,
        redesign_preservations,
        repair_proofs,
        aggregates,
        issues,
    ) = expanded_market_unified_strict_action_surface_repair_rows(
        surfaces,
        members,
        surface_redesigns,
        [previous_issue],
        [low, high],
        [],
        [],
    )
    system = expanded_market_system_unified_strict_action_surface_repair_rows(
        strict_surfaces,
        strict_executions,
        member_executions,
        redesign_preservations,
        repair_proofs,
        aggregates,
        issues,
        {"unit": True},
    )

    assert not issues
    assert len(repair_proofs) == 1
    assert repair_proofs[0]["previous_predicate_extra_match_rows"] == 1
    assert repair_proofs[0]["unexpected_strict_match_rows"] == 0
    assert system[0]["strict_surface_execution_pass_rows"] == 2
    assert system[0]["strict_member_execution_pass_rows"] == 2
    assert system[0]["hash_guard_repaired_surface_rows"] == 1


def test_expanded_market_unified_strict_implementation_readiness_preserves_rows():
    strict_surface = {
        "strict_action_surface_row_id": "strict-surface-1",
        "input_unified_action_surface_row_id": "surface-1",
        "strict_action_surface_expression": "row.get('symbol') == 'XAUUSD'",
        "strict_action_surface_function_name": "strict_surface",
    }
    strict_execution = {
        "strict_action_surface_execution_row_id": "strict-execution-1",
        "input_strict_action_surface_row_id": "strict-surface-1",
        "input_unified_action_surface_row_id": "surface-1",
        "strict_repair_mode": "HASH_GUARDED_PREDICATE_CLEAN",
        "strict_execution_status": "STRICT_ACTION_SURFACE_EXECUTION_PASS",
        "action_surface_family": "unit_family",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "selected_side": "LONG",
        "expected_member_action_rows": 1,
        "strict_execution_match_rows": 1,
        "average_cost_adjusted_simulated_r": 0.2,
        "average_stress_simulated_r": 0.1,
        "effective_n_sum": 150,
        "target_first_count_sum": 90,
        "stop_first_count_sum": 60,
        "neither_count_sum": 0,
        "ambiguous_count_sum": 0,
    }
    member = {
        "strict_action_surface_member_execution_row_id": "member-execution-1",
        "input_unified_implementation_action_row_id": "action-1",
        "input_strict_action_surface_row_id": "strict-surface-1",
        "input_unified_action_surface_row_id": "surface-1",
        "strict_repair_mode": "HASH_GUARDED_PREDICATE_CLEAN",
        "strict_member_execution_status": "STRICT_ACTION_SURFACE_MEMBER_EXECUTION_PASS",
        "action_row_kind": "evidence",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "source_path": "data/XAUUSD_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "gross_simulated_r": 0.25,
        "cost_adjusted_simulated_r": 0.2,
        "stress_simulated_r": 0.1,
        "effective_n": 150,
        "source_action_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SCORER_ROW",
    }
    redesign = {
        **member,
        "strict_action_surface_redesign_preservation_row_id": "redesign-preserve-1",
        "input_unified_implementation_action_row_id": "redesign-action-1",
        "strict_redesign_preservation_status": "STRICT_ACTION_SURFACE_REDESIGN_NUMERIC_PROOF_PRESERVED",
        "source_action_decision": "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_TERMINAL_CAPACITY",
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_TERMINAL_CAPACITY",
        "follow_inverse_default_off_avoid_class": "redesign",
    }

    surface_rows, member_rows, redesign_rows, aggregates, issues = (
        expanded_market_unified_strict_implementation_readiness_rows(
            [strict_surface],
            [strict_execution],
            [member],
            [redesign],
        )
    )
    system = expanded_market_system_unified_strict_implementation_readiness_rows(
        surface_rows,
        member_rows,
        redesign_rows,
        aggregates,
        issues,
        {"unit": True},
    )

    assert not issues
    assert surface_rows[0]["implementation_readiness_status"] == "STRICT_IMPLEMENTATION_READY"
    assert member_rows[0]["implementation_member_status"] == "STRICT_IMPLEMENTATION_MEMBER_READY"
    assert redesign_rows[0]["implementation_redesign_status"] == "STRICT_IMPLEMENTATION_REDESIGN_EVIDENCE_PRESERVED"
    assert system[0]["implementation_ready_surface_rows"] == 1
    assert system[0]["implementation_ready_member_rows"] == 1
    assert system[0]["redesign_evidence_preserved_rows"] == 1


def test_expanded_market_unified_strict_artifact_execution_materializes_and_controls():
    surface = {
        "strict_implementation_readiness_row_id": "ready-1",
        "input_strict_action_surface_row_id": "strict-surface-1",
        "input_unified_action_surface_row_id": "surface-1",
        "strict_action_surface_expression": "row.get('symbol') == 'XAUUSD'",
        "strict_action_surface_function_name": "strict_surface",
        "strict_repair_mode": "HASH_GUARDED_PREDICATE_CLEAN",
        "action_surface_family": "unit_family",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "selected_side": "LONG",
        "implementation_readiness_status": "STRICT_IMPLEMENTATION_READY",
        "average_cost_adjusted_simulated_r": 0.2,
        "average_stress_simulated_r": 0.1,
        "effective_n_sum": 150,
        "target_first_count_sum": 90,
        "stop_first_count_sum": 60,
        "neither_count_sum": 0,
        "ambiguous_count_sum": 0,
    }
    member = {
        "strict_implementation_member_row_id": "member-1",
        "input_strict_action_surface_row_id": "strict-surface-1",
        "input_unified_implementation_action_row_id": "action-1",
        "implementation_member_status": "STRICT_IMPLEMENTATION_MEMBER_READY",
        "action_row_kind": "evidence",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny_kz",
        "horizon_id": "h8",
        "source_component": "unit_component",
        "source_path": "data/XAUUSD_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "gross_simulated_r": 0.25,
        "cost_adjusted_simulated_r": 0.2,
        "stress_simulated_r": 0.1,
        "effective_n": 150,
        "missing_simulated_field": None,
        "missing_geometry_field": None,
        "source_action_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SCORER_ROW",
        "follow_inverse_default_off_avoid_class": "follow",
    }
    redesign = {
        **member,
        "strict_implementation_redesign_row_id": "redesign-1",
        "input_unified_implementation_action_row_id": "redesign-action-1",
        "source_action_decision": "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_TERMINAL_CAPACITY",
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_TERMINAL_CAPACITY",
        "follow_inverse_default_off_avoid_class": "redesign",
    }

    artifacts, member_executions, controls, redesigns, aggregates, issues = (
        expanded_market_unified_strict_artifact_execution_rows([surface], [member], [redesign])
    )
    system = expanded_market_system_unified_strict_artifact_execution_rows(
        artifacts,
        member_executions,
        controls,
        redesigns,
        aggregates,
        issues,
        {"unit": True},
    )

    assert not issues
    assert artifacts[0]["artifact_execution_status"] == "STRICT_IMPLEMENTATION_ARTIFACT_READY"
    assert member_executions[0]["artifact_member_execution_status"] == "STRICT_ARTIFACT_MEMBER_EXECUTION_PASS"
    assert controls[0]["positive_member_match"] is True
    assert controls[0]["negative_surface_mismatch_rejected"] is True
    assert redesigns[0]["artifact_redesign_status"] == "STRICT_ARTIFACT_REDESIGN_EVIDENCE_PRESERVED"
    assert system[0]["artifact_ready_rows"] == 1
    assert system[0]["artifact_member_execution_pass_rows"] == 1
    assert system[0]["artifact_control_pass_rows"] == 1


def test_expanded_market_supplemental_source_performance_preserves_seed_and_scores_grid():
    seed_input = {
        "expanded_market_performance_row_id": "seed-perf-1",
        "seed_source_component": "unit_seed",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h4",
        "side": "LONG",
        "source_path": "data/XAUUSD_M15.csv",
        "source_file_sha256": "seedhash",
        "source_access_status": "OHLC_CSV_REACHABLE",
        "source_rows_streamed": 100,
        "source_parsed_ohlc_rows": 100,
        "score_status": "EXPANDED_MARKET_PROXY_R_SCORED",
        "entry_reference": "unit",
        "entry_reference_time": "2026-01-01T00:00:00Z",
        "proxy_entry_price": 100.0,
        "proxy_denominator_price": 1.0,
        "proxy_target_price": 101.0,
        "proxy_stop_price": 99.0,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "path_order_counts": {"HORIZON_CLOSE_TARGET_PROXY_RESULT": 10},
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.2,
        "cost_adjusted_simulated_r": 0.19,
        "stress_simulated_r": 0.17,
        "cost_adjustment_r": 0.01,
        "stress_cost_adjustment_r": 0.03,
        "win_count": 6,
        "loss_count": 4,
        "zero_count": 0,
        "target_first_count": 6,
        "stop_first_count": 4,
        "neither_count": 0,
        "ambiguous_count": 0,
        "effective_n": 10,
        "duplicate_row_count": 0,
        "effective_n_after_duplicate_collapse": 10,
        "concentration_top_month_share": 1.0,
        "follow_inverse_default_off_avoid_class": "redesign",
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_SIGNAL_GEOMETRY",
    }
    seed_rows = expanded_market_copy_seed_floor_performance_rows([seed_input])
    source = {
        "supplemental_source_row_id": "source-1",
        "source_path": "research/unit_sierra_bars.jsonl",
        "source_file_sha256": "sourcehash",
        "source_symbol": "UNIT",
        "symbol": "UNIT",
        "source_timeframe": "M15",
        "source_access_status": "SIERRA_SOURCE_BOUND_M15_BARS_REACHABLE",
        "source_rows_streamed": 96,
        "source_parsed_ohlc_rows": 96,
        "source_first_time": "2026-01-01T00:00:00Z",
        "source_last_time": "2026-01-01T23:45:00Z",
        "source_record_selector": "source_symbol=UNIT",
        "source_record_selector_sha256": "selectorhash",
    }
    bars = []
    for index in range(96):
        hour = index // 4
        minute = (index % 4) * 15
        close = 100.0 + index * 0.2
        bars.append(
            {
                "time": f"2026-01-01T{hour:02d}:{minute:02d}:00Z",
                "dt": parse_expanded_market_dt(f"2026-01-01T{hour:02d}:{minute:02d}:00Z"),
                "open": close - 0.05,
                "high": close + 0.05,
                "low": close - 0.05,
                "close": close,
            }
        )
    additional = expanded_market_supplemental_source_performance_rows(
        [source],
        {"UNIT": bars},
        {"UNIT": {"symbol": "UNIT", "mean_cost_r": 0.01, "stress_cost_r": 0.03}},
        sequence_start=len(seed_rows) + 1,
    )
    combined = seed_rows + additional
    aggregates = aggregate_expanded_market_supplemental_source_performance_rows(combined)
    missing = expanded_market_supplemental_missing_simulated_field_rows(combined)
    system = expanded_market_system_supplemental_source_performance_rows(
        combined,
        aggregates,
        [source],
        missing,
        {"unit": True},
    )

    assert len(seed_rows) == 1
    assert len(additional) == 30
    assert len(missing) == 0
    assert all(row["source_path"] and row["source_file_sha256"] for row in combined)
    assert system[0]["input_seed_floor_performance_rows"] == 1
    assert system[0]["additional_source_performance_rows"] == 30
    assert sum(row["row_count"] for row in aggregates) == 31


def test_expanded_market_source_consensus_preserves_rows_and_groups_proxy_family():
    rows = []
    for row_id, family, symbol, path, cost_r in [
        ("perf-1", "cp216_seed_floor_ohlc_csv", "NAS100", "data/NAS100_M15.csv", 0.2),
        (
            "perf-2",
            "sierra_scid_source_bound_m15",
            "NQM26-CME",
            "research/sierra_bars.jsonl",
            0.15,
        ),
    ]:
        rows.append(
            {
                "expanded_market_supplemental_performance_row_id": row_id,
                "performance_source_family": family,
                "symbol": symbol,
                "source_symbol": symbol,
                "market_timeframe": "M15",
                "route_session": "ny_core",
                "horizon_id": "h4",
                "side": "LONG",
                "source_component": "unit",
                "source_path": path,
                "source_file_sha256": f"hash-{row_id}",
                "source_record_selector": row_id,
                "entry_reference": "unit",
                "entry_reference_time": "2026-01-01T13:00:00Z",
                "proxy_entry_price": 100.0,
                "proxy_denominator_price": 1.0,
                "proxy_target_price": 101.0,
                "proxy_stop_price": 99.0,
                "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
                "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
                "gross_simulated_r": cost_r + 0.01,
                "cost_adjusted_simulated_r": cost_r,
                "stress_simulated_r": cost_r - 0.03,
                "win_count": 30,
                "loss_count": 10,
                "zero_count": 0,
                "target_first_count": 30,
                "stop_first_count": 10,
                "neither_count": 0,
                "ambiguous_count": 0,
                "effective_n": 40,
                "duplicate_row_count": 0,
                "effective_n_after_duplicate_collapse": 40,
                "concentration_top_month_share": 0.5,
                "missing_simulated_fields": [],
            }
        )

    consensus, issues = expanded_market_source_consensus_rows(rows)
    aggregates = aggregate_expanded_market_source_consensus_rows(consensus)
    system = expanded_market_system_source_consensus_rows(consensus, aggregates, issues, {"unit": True})

    assert not issues
    assert len(consensus) == 2
    assert {row["input_supplemental_performance_row_id"] for row in consensus} == {"perf-1", "perf-2"}
    assert {row["symbol_family"] for row in consensus} == {"NAS100_NQ_FAMILY"}
    assert consensus[0]["consensus_source_path_count"] == 2
    assert consensus[0]["keep_kill_redesign_implement_decision"] == "IMPLEMENT_EXPANDED_MARKET_SOURCE_CONSENSUS_ROBUST"
    assert aggregates[0]["row_count"] == 2
    assert system[0]["source_consensus_rows"] == 2


def test_expanded_market_consensus_deconcentration_preserves_and_caps_source_path_weight():
    rows = []
    for row_id, path, effective_n, cost_r in [
        ("consensus-1", "source/a.csv", 60, 0.2),
        ("consensus-2", "source/b.csv", 40, 0.16),
    ]:
        rows.append(
            {
                "expanded_market_source_consensus_row_id": row_id,
                "input_supplemental_performance_row_id": f"perf-{row_id}",
                "performance_source_family": "unit",
                "symbol_family": "NAS100_NQ_FAMILY",
                "symbol": "NAS100",
                "source_symbol": "NAS100",
                "market_timeframe": "M15",
                "route_session": "ny_core",
                "horizon_id": "h4",
                "side": "LONG",
                "source_component": "unit",
                "source_path": path,
                "source_file_sha256": f"hash-{row_id}",
                "source_record_selector": row_id,
                "entry_reference": "unit",
                "entry_reference_time": "2026-01-01T13:00:00Z",
                "proxy_entry_price": 100.0,
                "proxy_denominator_price": 1.0,
                "proxy_target_price": 101.0,
                "proxy_stop_price": 99.0,
                "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
                "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
                "gross_simulated_r": cost_r + 0.01,
                "cost_adjusted_simulated_r": cost_r,
                "stress_simulated_r": cost_r - 0.03,
                "win_count": int(effective_n * 0.7),
                "loss_count": int(effective_n * 0.3),
                "zero_count": 0,
                "target_first_count": int(effective_n * 0.7),
                "stop_first_count": int(effective_n * 0.3),
                "neither_count": 0,
                "ambiguous_count": 0,
                "effective_n": effective_n,
                "duplicate_row_count": 0,
                "effective_n_after_duplicate_collapse": effective_n,
                "missing_simulated_fields": [],
                "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_SOURCE_CONSENSUS_ROBUST",
            }
        )

    decon, issues = expanded_market_consensus_deconcentration_rows(rows)
    aggregates = aggregate_expanded_market_consensus_deconcentration_rows(decon)
    system = expanded_market_system_consensus_deconcentration_rows(decon, aggregates, issues, {"unit": True})

    assert not issues
    assert len(decon) == 2
    assert {row["input_source_consensus_row_id"] for row in decon} == {"consensus-1", "consensus-2"}
    assert min(row["source_path_deconcentration_weight"] for row in decon) < 1.0
    assert decon[0]["keep_kill_redesign_implement_decision"] == "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_PERFORMANCE"
    assert aggregates[0]["row_count"] == 2
    assert system[0]["deconcentration_rows"] == 2


def test_expanded_market_deconcentrated_selection_maps_numeric_decisions():
    row = {
        "expanded_market_deconcentration_row_id": "decon-1",
        "input_source_consensus_row_id": "consensus-1",
        "performance_source_family": "unit",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "source_component": "unit",
        "source_path": "source/a.csv",
        "source_file_sha256": "hash-decon-1",
        "source_record_selector": "unit",
        "entry_reference": "unit",
        "entry_reference_time": "2026-01-01T13:00:00Z",
        "proxy_entry_price": 100.0,
        "proxy_denominator_price": 1.0,
        "proxy_target_price": 101.0,
        "proxy_stop_price": 99.0,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.21,
        "cost_adjusted_simulated_r": 0.2,
        "stress_simulated_r": 0.17,
        "deconcentrated_effective_n": 35.0,
        "deconcentrated_effective_n_sum": 75.0,
        "deconcentrated_cost_adjusted_simulated_r": 0.18,
        "deconcentrated_stress_simulated_r": 0.15,
        "deconcentrated_top_source_path_effective_n_share": 0.55,
        "source_path_deconcentration_weight": 0.8,
        "win_count": 30,
        "loss_count": 10,
        "zero_count": 0,
        "target_first_count": 30,
        "stop_first_count": 10,
        "neither_count": 0,
        "ambiguous_count": 0,
        "effective_n": 40,
        "missing_simulated_fields": [],
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_PERFORMANCE",
    }

    rows, issues = expanded_market_deconcentrated_selection_rows([row])
    aggregates = aggregate_expanded_market_deconcentrated_selection_rows(rows)
    system = expanded_market_system_deconcentrated_selection_rows(rows, aggregates, issues, {"unit": True})

    assert not issues
    assert rows[0]["input_deconcentration_row_id"] == "decon-1"
    assert rows[0]["keep_kill_redesign_implement_decision"] == "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_SCORER_CANDIDATE"
    assert rows[0]["follow_inverse_default_off_avoid_class"] == "follow"
    assert rows[0]["numeric_priority_score"] is not None
    assert "symbol_family=NAS100_NQ_FAMILY" in rows[0]["branch_local_selection_expression"]
    assert aggregates[0]["row_count"] == 1
    assert system[0]["selection_rows"] == 1


def test_expanded_market_deconcentrated_scorer_surfaces_split_implement_and_evidence():
    implement = {
        "expanded_market_deconcentrated_selection_row_id": "select-1",
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_SCORER_CANDIDATE",
        "follow_inverse_default_off_avoid_class": "follow",
        "performance_source_family": "unit",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "source_path": "source/a.csv",
        "source_file_sha256": "hash-a",
        "entry_reference": "unit",
        "proxy_entry_price": 100.0,
        "proxy_denominator_price": 1.0,
        "proxy_target_price": 101.0,
        "proxy_stop_price": 99.0,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.21,
        "cost_adjusted_simulated_r": 0.2,
        "stress_simulated_r": 0.17,
        "deconcentrated_effective_n": 35.0,
        "deconcentrated_cost_adjusted_simulated_r": 0.18,
        "deconcentrated_stress_simulated_r": 0.15,
        "numeric_priority_score": 0.19,
        "win_count": 30,
        "loss_count": 10,
        "zero_count": 0,
        "target_first_count": 30,
        "stop_first_count": 10,
        "neither_count": 0,
        "ambiguous_count": 0,
        "effective_n": 40,
    }
    evidence_input = {
        **implement,
        "expanded_market_deconcentrated_selection_row_id": "select-2",
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_DECONCENTRATED_WEAK_EDGE",
        "follow_inverse_default_off_avoid_class": "redesign",
        "side": "SHORT",
    }

    surfaces, members, evidence, self_tests, issues = expanded_market_deconcentrated_scorer_surface_rows(
        [implement, evidence_input]
    )
    system = expanded_market_system_deconcentrated_scorer_surface_rows(
        surfaces,
        members,
        evidence,
        self_tests,
        [],
        issues,
        {"unit": True},
    )

    assert not issues
    assert len(surfaces) == 1
    assert len(members) == 1
    assert len(evidence) == 1
    assert expanded_market_deconcentrated_surface_matches(surfaces[0], implement)
    assert self_tests[0]["self_test_status"] == "DECONCENTRATED_SCORER_SURFACE_SELF_TEST_PASS"
    assert system[0]["scorer_member_rows"] == 1
    assert system[0]["nonimplement_evidence_rows"] == 1


def test_expanded_market_deconcentrated_scorer_surface_execution_preserves_numeric_rows():
    implement = {
        "expanded_market_deconcentrated_selection_row_id": "select-1",
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_SCORER_CANDIDATE",
        "follow_inverse_default_off_avoid_class": "follow",
        "performance_source_family": "unit",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "source_component": "unit",
        "source_path": "source/a.csv",
        "source_file_sha256": "hash-a",
        "source_record_selector": "unit",
        "entry_reference": "unit",
        "entry_reference_time": "2026-01-01T13:00:00Z",
        "proxy_entry_price": 100.0,
        "proxy_denominator_price": 1.0,
        "proxy_target_price": 101.0,
        "proxy_stop_price": 99.0,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.21,
        "cost_adjusted_simulated_r": 0.2,
        "stress_simulated_r": 0.17,
        "deconcentrated_effective_n": 35.0,
        "deconcentrated_cost_adjusted_simulated_r": 0.18,
        "deconcentrated_stress_simulated_r": 0.15,
        "numeric_priority_score": 0.19,
        "win_count": 30,
        "loss_count": 10,
        "zero_count": 0,
        "target_first_count": 30,
        "stop_first_count": 10,
        "neither_count": 0,
        "ambiguous_count": 0,
        "effective_n": 40,
        "missing_simulated_fields": [],
    }
    evidence_input = {
        **implement,
        "expanded_market_deconcentrated_selection_row_id": "select-2",
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_DECONCENTRATED_WEAK_EDGE",
        "follow_inverse_default_off_avoid_class": "redesign",
        "side": "SHORT",
        "cost_adjusted_simulated_r": -0.05,
        "deconcentrated_cost_adjusted_simulated_r": -0.04,
    }

    surfaces, members, evidence, _, surface_issues = expanded_market_deconcentrated_scorer_surface_rows(
        [implement, evidence_input]
    )
    surface_exec, member_exec, evidence_exec, issues = expanded_market_deconcentrated_scorer_surface_execution_rows(
        surfaces,
        members,
        evidence,
        [implement, evidence_input],
    )
    aggregates = aggregate_expanded_market_deconcentrated_scorer_surface_execution_rows(
        surface_exec,
        member_exec,
        evidence_exec,
    )
    system = expanded_market_system_deconcentrated_scorer_surface_execution_rows(
        surfaces,
        members,
        evidence,
        surface_exec,
        member_exec,
        evidence_exec,
        aggregates,
        issues,
        {"unit": True},
    )

    assert not surface_issues
    assert not issues
    assert len(surface_exec) == 1
    assert len(member_exec) == 1
    assert len(evidence_exec) == 1
    assert surface_exec[0]["execution_status"] == "DECONCENTRATED_SCORER_SURFACE_EXECUTION_PASS"
    assert surface_exec[0]["matched_nonimplement_rows"] == 0
    assert member_exec[0]["input_selection_row_id"] == "select-1"
    assert member_exec[0]["cost_adjusted_simulated_r"] == 0.2
    assert evidence_exec[0]["input_selection_row_id"] == "select-2"
    assert evidence_exec[0]["win_count"] == 30
    assert aggregates[0]["row_count"] == 1
    assert system[0]["surface_execution_pass_rows"] == 1


def test_expanded_market_action_class_performance_maps_follow_avoid_and_redesign():
    base = {
        "input_selection_row_id": "select-1",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "performance_source_family": "unit",
        "source_component": "unit",
        "source_path": "source/a.csv",
        "source_file_sha256": "hash-a",
        "source_record_selector": "unit",
        "entry_reference": "unit",
        "entry_reference_time": "2026-01-01T13:00:00Z",
        "proxy_entry_price": 100.0,
        "proxy_denominator_price": 1.0,
        "proxy_target_price": 101.0,
        "proxy_stop_price": 99.0,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.21,
        "cost_adjusted_simulated_r": 0.2,
        "stress_simulated_r": 0.17,
        "deconcentrated_effective_n": 35.0,
        "deconcentrated_cost_adjusted_simulated_r": 0.18,
        "deconcentrated_stress_simulated_r": 0.15,
        "win_count": 30,
        "loss_count": 10,
        "zero_count": 0,
        "target_first_count": 30,
        "stop_first_count": 10,
        "neither_count": 0,
        "ambiguous_count": 0,
        "effective_n": 40,
    }
    member = {
        **base,
        "expanded_market_deconcentrated_scorer_member_execution_row_id": "member-exec-1",
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_SCORER_MEMBER_EXECUTION",
        "follow_inverse_default_off_avoid_class": "follow",
    }
    avoid = {
        **base,
        "input_selection_row_id": "select-2",
        "expanded_market_deconcentrated_nonimplement_evidence_execution_row_id": "evidence-exec-1",
        "keep_kill_redesign_implement_decision": "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_DECONCENTRATED_SCOPE",
        "follow_inverse_default_off_avoid_class": "avoid",
        "gross_simulated_r": -0.11,
        "cost_adjusted_simulated_r": -0.12,
        "stress_simulated_r": -0.15,
        "deconcentrated_cost_adjusted_simulated_r": -0.1,
        "deconcentrated_stress_simulated_r": -0.13,
    }
    redesign = {
        **avoid,
        "input_selection_row_id": "select-3",
        "expanded_market_deconcentrated_nonimplement_evidence_execution_row_id": "evidence-exec-2",
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_DECONCENTRATED_WEAK_EDGE",
        "follow_inverse_default_off_avoid_class": "redesign",
    }

    rows, issues = expanded_market_action_class_performance_rows([member], [avoid, redesign])
    aggregates = aggregate_expanded_market_action_class_performance_rows(rows)
    system = expanded_market_system_action_class_performance_rows(rows, aggregates, issues, {"unit": True})

    assert not issues
    assert [row["action_class"] for row in rows] == ["follow", "avoid", "redesign-weak-edge"]
    assert rows[0]["primary_action_cost_adjusted_simulated_r"] == 0.18
    assert rows[1]["primary_action_cost_adjusted_simulated_r"] == 0.1
    assert rows[1]["proxy_inverse_cost_adjusted_simulated_r"] == 0.1
    assert rows[2]["primary_action_cost_adjusted_simulated_r"] is None
    assert rows[2]["action_missing_simulated_fields"] == ["concrete_replay_implementation_for_redesign_action_r"]
    assert system[0]["action_class_performance_rows"] == 3
    assert system[0]["scored_action_rows"] == 2
    assert system[0]["missing_action_rows"] == 1


def test_expanded_market_source_repair_reachability_uses_alternate_scored_sources():
    base = {
        "expanded_market_action_class_performance_row_id": "action-1",
        "input_selection_row_id": "select-1",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "performance_source_family": "unit",
        "source_component": "unit",
        "source_path": "source/a.csv",
        "source_file_sha256": "hash-a",
        "source_record_selector": "unit",
        "entry_reference": "unit",
        "entry_reference_time": "2026-01-01T13:00:00Z",
        "proxy_entry_price": 100.0,
        "proxy_denominator_price": 1.0,
        "proxy_target_price": 101.0,
        "proxy_stop_price": 99.0,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "observed_gross_simulated_r": 0.21,
        "observed_cost_adjusted_simulated_r": 0.2,
        "observed_stress_simulated_r": 0.17,
        "observed_deconcentrated_cost_adjusted_simulated_r": 0.18,
        "observed_deconcentrated_stress_simulated_r": 0.15,
        "deconcentrated_effective_n": 35.0,
        "effective_n": 40,
        "win_count": 30,
        "loss_count": 10,
        "zero_count": 0,
        "target_first_count": 30,
        "stop_first_count": 10,
        "neither_count": 0,
        "ambiguous_count": 0,
    }
    scored_follow = {
        **base,
        "expanded_market_action_class_performance_row_id": "action-1",
        "action_class": "follow",
        "primary_action_cost_adjusted_simulated_r": 0.18,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_ACTION_CLASS_FOLLOW_PERFORMANCE",
    }
    repair = {
        **base,
        "expanded_market_action_class_performance_row_id": "action-2",
        "input_selection_row_id": "select-2",
        "action_class": "redesign-source-repair",
        "source_path": "source/b.csv",
        "source_file_sha256": "hash-b",
        "primary_action_cost_adjusted_simulated_r": None,
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_ACTION_CLASS_SOURCE_REPAIR",
    }
    expansion = {
        **base,
        "expanded_market_action_class_performance_row_id": "action-3",
        "input_selection_row_id": "select-3",
        "action_class": "redesign-source-expansion",
        "symbol_family": "GBPUSD_6B_FAMILY",
        "symbol": "GBPUSD",
        "source_symbol": "GBPUSD",
        "source_path": "source/c.csv",
        "source_file_sha256": "hash-c",
        "primary_action_cost_adjusted_simulated_r": None,
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_ACTION_CLASS_SOURCE_EXPANSION",
    }

    rows, issues = expanded_market_source_repair_reachability_rows([scored_follow, repair, expansion])
    aggregates = aggregate_expanded_market_source_repair_reachability_rows(rows)
    system = expanded_market_system_source_repair_reachability_rows(rows, aggregates, issues, {"unit": True})

    assert not issues
    assert rows[0]["source_repair_reachability_class"] == "scored-action-carried-forward"
    assert rows[1]["source_repair_reachability_class"] == "source-repair-alternate-scored-action-available"
    assert rows[1]["alternate_source_path_count"] == 1
    assert rows[1]["repair_action_cost_adjusted_simulated_r"] == 0.18
    assert rows[1]["repair_missing_fields"] == []
    assert rows[2]["source_repair_reachability_class"] == "source-expansion-new-source-required"
    assert rows[2]["repair_missing_fields"] == ["additional_replay_source_path_hash_for_scope"]
    assert system[0]["source_repair_reachability_rows"] == 3
    assert system[0]["reachable_repair_rows"] == 2
    assert system[0]["missing_repair_rows"] == 1


def test_expanded_market_alternate_source_scoring_maps_source_repair_proxy_r():
    base = {
        "expanded_market_source_repair_reachability_row_id": "reach-1",
        "input_action_class_performance_row_id": "action-1",
        "input_selection_row_id": "select-1",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "action_class": "redesign-source-repair",
        "source_repair_reachability_class": "source-repair-alternate-source-unscored",
        "performance_source_family": "unit",
        "source_component": "unit",
        "source_path": "source/a.csv",
        "source_file_sha256": "hash-a",
        "source_record_selector": "unit",
        "entry_reference": "unit",
        "entry_reference_time": "2026-01-01T13:00:00Z",
        "proxy_entry_price": 100.0,
        "proxy_denominator_price": 1.0,
        "proxy_target_price": 101.0,
        "proxy_stop_price": 99.0,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "observed_gross_simulated_r": 0.21,
        "observed_cost_adjusted_simulated_r": 0.2,
        "observed_stress_simulated_r": 0.17,
        "observed_deconcentrated_cost_adjusted_simulated_r": 0.18,
        "observed_deconcentrated_stress_simulated_r": 0.15,
        "repair_action_cost_adjusted_simulated_r": None,
        "alternate_source_path_count": 1,
        "alternate_source_paths_sample": ["source/b.csv"],
        "alternate_observed_rows": 4,
        "alternate_observed_deconcentrated_cost_adjusted_simulated_r": 0.07,
        "deconcentrated_effective_n": 35.0,
        "effective_n": 40,
        "win_count": 30,
        "loss_count": 10,
        "zero_count": 0,
        "target_first_count": 30,
        "stop_first_count": 10,
        "neither_count": 0,
        "ambiguous_count": 0,
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_SOURCE_REPAIR_SCORE_ALTERNATE_SOURCE",
    }
    weak_positive = {**base, "expanded_market_source_repair_reachability_row_id": "reach-2", "alternate_observed_deconcentrated_cost_adjusted_simulated_r": 0.03}
    nonpositive = {**base, "expanded_market_source_repair_reachability_row_id": "reach-3", "alternate_observed_deconcentrated_cost_adjusted_simulated_r": -0.02}
    expansion = {
        **base,
        "expanded_market_source_repair_reachability_row_id": "reach-4",
        "action_class": "redesign-source-expansion",
        "source_repair_reachability_class": "source-expansion-new-source-required",
        "alternate_observed_deconcentrated_cost_adjusted_simulated_r": None,
    }

    rows, issues = expanded_market_alternate_source_scoring_rows([base, weak_positive, nonpositive, expansion])
    aggregates = aggregate_expanded_market_alternate_source_scoring_rows(rows)
    system = expanded_market_system_alternate_source_scoring_rows(rows, aggregates, issues, {"unit": True})

    assert not issues
    assert [row["alternate_source_scoring_class"] for row in rows] == [
        "alternate-source-positive-repair",
        "alternate-source-weak-positive-repair",
        "alternate-source-nonpositive-repair",
        "source-expansion-new-source-required",
    ]
    assert rows[0]["alternate_source_proxy_cost_adjusted_simulated_r"] == 0.07
    assert rows[1]["alternate_source_proxy_cost_adjusted_simulated_r"] == 0.03
    assert rows[2]["alternate_source_proxy_cost_adjusted_simulated_r"] == -0.02
    assert rows[3]["alternate_source_missing_fields"] == ["additional_replay_source_path_hash_for_scope"]
    assert system[0]["scored_rows"] == 3
    assert system[0]["missing_rows"] == 1


def test_expanded_market_implementation_priority_promotes_positive_repair_and_preserves_others():
    base = {
        "expanded_market_alternate_source_scoring_row_id": "alt-1",
        "input_source_repair_reachability_row_id": "reach-1",
        "input_action_class_performance_row_id": "action-1",
        "input_selection_row_id": "select-1",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "action_class": "redesign-source-repair",
        "source_repair_reachability_class": "source-repair-alternate-source-unscored",
        "alternate_source_scoring_class": "alternate-source-positive-repair",
        "performance_source_family": "unit",
        "source_component": "unit",
        "source_path": "source/a.csv",
        "source_file_sha256": "hash-a",
        "source_record_selector": "unit",
        "entry_reference": "unit",
        "entry_reference_time": "2026-01-01T13:00:00Z",
        "proxy_entry_price": 100.0,
        "proxy_denominator_price": 1.0,
        "proxy_target_price": 101.0,
        "proxy_stop_price": 99.0,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "observed_gross_simulated_r": 0.21,
        "observed_cost_adjusted_simulated_r": 0.2,
        "observed_stress_simulated_r": 0.17,
        "observed_deconcentrated_cost_adjusted_simulated_r": 0.18,
        "observed_deconcentrated_stress_simulated_r": 0.15,
        "primary_action_cost_adjusted_simulated_r": None,
        "repair_action_cost_adjusted_simulated_r": None,
        "alternate_source_proxy_cost_adjusted_simulated_r": 0.07,
        "alternate_source_path_count": 1,
        "alternate_source_paths_sample": ["source/b.csv"],
        "alternate_observed_rows": 4,
        "alternate_observed_deconcentrated_cost_adjusted_simulated_r": 0.07,
        "deconcentrated_effective_n": 35.0,
        "effective_n": 40,
        "win_count": 30,
        "loss_count": 10,
        "zero_count": 0,
        "target_first_count": 30,
        "stop_first_count": 10,
        "neither_count": 0,
        "ambiguous_count": 0,
        "keep_kill_redesign_implement_decision": "REPAIR_EXPANDED_MARKET_ALTERNATE_SOURCE_POSITIVE_PROXY_R",
    }
    weak = {
        **base,
        "expanded_market_alternate_source_scoring_row_id": "alt-2",
        "alternate_source_scoring_class": "alternate-source-weak-positive-repair",
        "alternate_source_proxy_cost_adjusted_simulated_r": 0.03,
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_ALTERNATE_SOURCE_WEAK_POSITIVE_PROXY_R",
    }
    expansion = {
        **base,
        "expanded_market_alternate_source_scoring_row_id": "alt-3",
        "action_class": "redesign-source-expansion",
        "source_repair_reachability_class": "source-expansion-new-source-required",
        "alternate_source_scoring_class": "source-expansion-new-source-required",
        "alternate_source_proxy_cost_adjusted_simulated_r": None,
        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACQUIRE_NEW_SOURCE",
    }

    rows, issues = expanded_market_implementation_priority_rows([base, weak, expansion])
    aggregates = aggregate_expanded_market_implementation_priority_rows(rows)
    system = expanded_market_system_implementation_priority_rows(rows, aggregates, issues, {"unit": True})

    assert not issues
    assert rows[0]["implementation_priority_class"] == "implementation-priority-positive-alternate-source-repair"
    assert rows[0]["implementation_priority_score"] > rows[0]["alternate_source_proxy_cost_adjusted_simulated_r"]
    assert rows[0]["implementation_missing_fields"] == []
    assert rows[1]["implementation_priority_class"] == "redesign-weak-positive-alternate-source-repair"
    assert rows[2]["implementation_priority_class"] == "source-expansion-acquisition-proof"
    assert rows[2]["implementation_missing_fields"] == ["additional_replay_source_path_hash_for_scope"]
    assert system[0]["implementation_candidate_rows"] == 1
    assert system[0]["preserved_evidence_rows"] == 2


def test_expanded_market_impl_candidates_materialize_positive_priority_rows_with_self_tests():
    base = {
        "expanded_market_implementation_priority_row_id": "priority-1",
        "input_alternate_source_scoring_row_id": "alt-1",
        "input_source_repair_reachability_row_id": "reach-1",
        "input_action_class_performance_row_id": "action-1",
        "input_selection_row_id": "select-1",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "action_class": "redesign-source-repair",
        "source_repair_reachability_class": "source-repair-alternate-source-unscored",
        "alternate_source_scoring_class": "alternate-source-positive-repair",
        "implementation_priority_class": "implementation-priority-positive-alternate-source-repair",
        "implementation_priority_score": 0.08,
        "implementation_priority_tier": "repair-priority-positive",
        "implementation_missing_fields": [],
        "performance_source_family": "unit",
        "source_component": "unit_component",
        "source_path": "source/a.csv",
        "source_file_sha256": "hash-a",
        "source_record_selector": "unit-row-1",
        "entry_reference": "unit-entry",
        "entry_reference_time": "2026-01-01T13:00:00Z",
        "proxy_entry_price": 100.0,
        "proxy_denominator_price": 1.0,
        "proxy_target_price": 101.0,
        "proxy_stop_price": 99.0,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "observed_gross_simulated_r": 0.21,
        "observed_cost_adjusted_simulated_r": 0.2,
        "observed_stress_simulated_r": 0.17,
        "observed_deconcentrated_cost_adjusted_simulated_r": 0.18,
        "observed_deconcentrated_stress_simulated_r": 0.15,
        "alternate_source_proxy_cost_adjusted_simulated_r": 0.07,
        "alternate_source_path_count": 1,
        "alternate_source_paths_sample": ["source/b.csv"],
        "alternate_observed_rows": 4,
        "alternate_observed_deconcentrated_cost_adjusted_simulated_r": 0.07,
        "deconcentrated_effective_n": 35.0,
        "effective_n": 40,
        "win_count": 30,
        "loss_count": 10,
        "zero_count": 0,
        "target_first_count": 30,
        "stop_first_count": 10,
        "neither_count": 0,
        "ambiguous_count": 0,
        "keep_kill_redesign_implement_decision": (
            "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_PRIORITY"
        ),
    }
    evidence_input = {
        **base,
        "expanded_market_implementation_priority_row_id": "priority-2",
        "implementation_priority_class": "kill-nonpositive-alternate-source-repair",
        "implementation_priority_score": -0.02,
        "implementation_priority_tier": "not-new-implementation-priority",
        "alternate_source_proxy_cost_adjusted_simulated_r": -0.02,
        "keep_kill_redesign_implement_decision": (
            "KILL_EXPANDED_MARKET_NONPOSITIVE_ALTERNATE_SOURCE_REPAIR"
        ),
    }

    candidates, evidence, self_tests, issues = expanded_market_impl_candidate_rows([base, evidence_input])
    aggregates = aggregate_expanded_market_impl_candidate_rows(candidates, evidence)
    system = expanded_market_system_impl_candidate_rows(
        candidates,
        evidence,
        self_tests,
        aggregates,
        issues,
        {"unit": True},
    )

    assert not issues
    assert len(candidates) == 1
    assert len(evidence) == 1
    assert self_tests[0]["self_test_status"] == "EXPANDED_MARKET_IMPL_CANDIDATE_SELF_TEST_PASS"
    assert candidates[0]["candidate_cost_adjusted_simulated_r"] == 0.07
    assert expanded_market_impl_candidate_matches(candidates[0], base)
    mismatch = {**base, "source_file_sha256": "other-hash"}
    assert not expanded_market_impl_candidate_matches(candidates[0], mismatch)
    assert evidence[0]["evidence_preservation_class"] == "kill-nonpositive-alternate-source-repair"
    assert system[0]["implementation_candidate_rows"] == 1
    assert system[0]["preserved_evidence_rows"] == 1


def test_expanded_market_impl_candidate_execution_passes_candidate_and_preserves_evidence():
    priority = {
        "expanded_market_implementation_priority_row_id": "priority-1",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "source_path": "source/a.csv",
        "source_file_sha256": "hash-a",
        "source_component": "unit_component",
        "source_record_selector": "unit-row-1",
        "entry_reference": "unit-entry",
        "entry_reference_time": "2026-01-01T13:00:00Z",
        "proxy_entry_price": 100.0,
        "proxy_denominator_price": 1.0,
        "proxy_target_price": 101.0,
        "proxy_stop_price": 99.0,
        "implementation_priority_class": "implementation-priority-positive-alternate-source-repair",
        "implementation_priority_score": 0.08,
        "implementation_priority_tier": "repair-priority-positive",
        "alternate_source_proxy_cost_adjusted_simulated_r": 0.07,
        "observed_cost_adjusted_simulated_r": 0.2,
        "observed_stress_simulated_r": 0.17,
        "observed_deconcentrated_stress_simulated_r": 0.15,
        "deconcentrated_effective_n": 35.0,
        "effective_n": 40,
        "win_count": 30,
        "loss_count": 10,
        "zero_count": 0,
        "target_first_count": 30,
        "stop_first_count": 10,
        "neither_count": 0,
        "ambiguous_count": 0,
    }
    evidence_priority = {
        **priority,
        "expanded_market_implementation_priority_row_id": "priority-2",
        "implementation_priority_class": "kill-nonpositive-alternate-source-repair",
        "implementation_priority_tier": "not-new-implementation-priority",
        "alternate_source_proxy_cost_adjusted_simulated_r": -0.02,
    }
    candidates, evidence, self_tests, candidate_issues = expanded_market_impl_candidate_rows(
        [priority, evidence_priority]
    )

    executions, evidence_exec, controls, issues = expanded_market_impl_candidate_execution_rows(
        candidates,
        [priority, evidence_priority],
        evidence,
        self_tests,
    )
    aggregates = aggregate_expanded_market_impl_candidate_execution_rows(
        executions,
        evidence_exec,
        controls,
    )

    assert not candidate_issues
    assert not issues
    assert len(executions) == 1
    assert executions[0]["candidate_execution_status"] == "EXPANDED_MARKET_IMPL_CANDIDATE_EXECUTION_PASS"
    assert executions[0]["execution_cost_adjusted_simulated_r"] == 0.07
    assert len(evidence_exec) == 1
    assert evidence_exec[0]["evidence_execution_status"] == "PRESERVED_NONCANDIDATE_PRIORITY_EVIDENCE_EXECUTION"
    assert controls[0]["control_status"] == "EXPANDED_MARKET_IMPL_CANDIDATE_CONTROL_PASS"
    assert controls[0]["noncandidate_scope_leakage_count"] == 0
    assert aggregates


def test_expanded_market_repair_application_table_keeps_ready_execution_and_evidence():
    execution = {
        "expanded_market_impl_candidate_execution_row_id": "exec-1",
        "input_implementation_priority_row_id": "priority-1",
        "candidate_execution_status": "EXPANDED_MARKET_IMPL_CANDIDATE_EXECUTION_PASS",
        "candidate_scope_match": True,
        "branch_local_candidate_scope_sha256": "scope-hash",
        "branch_local_code_expression": "scope=scope-hash",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "source_path": "source/a.csv",
        "source_file_sha256": "hash-a",
        "entry_reference": "unit-entry",
        "entry_reference_time": "2026-01-01T13:00:00Z",
        "proxy_entry_price": 100.0,
        "proxy_denominator_price": 1.0,
        "proxy_target_price": 101.0,
        "proxy_stop_price": 99.0,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "execution_cost_adjusted_simulated_r": 0.07,
        "execution_observed_stress_simulated_r": 0.15,
        "candidate_effective_n": 35.0,
        "implementation_priority_class": "implementation-priority-positive-alternate-source-repair",
        "implementation_priority_tier": "repair-priority-positive",
    }
    evidence = {
        "expanded_market_impl_candidate_evidence_execution_row_id": "evidence-exec-1",
        "input_implementation_priority_row_id": "priority-2",
        "evidence_preservation_class": "kill-nonpositive-alternate-source-repair",
        "implementation_priority_tier": "not-new-implementation-priority",
        "keep_kill_redesign_implement_decision": "KILL_EXPANDED_MARKET_NONPOSITIVE_ALTERNATE_SOURCE_REPAIR",
    }
    control = {
        "expanded_market_impl_candidate_control_row_id": "control-1",
        "input_implementation_priority_row_id": "priority-1",
        "control_status": "EXPANDED_MARKET_IMPL_CANDIDATE_CONTROL_PASS",
        "positive_execution_match": True,
        "noncandidate_scope_leakage_count": 0,
    }

    applications, evidence_rows, controls, issues = expanded_market_repair_application_rows(
        [execution],
        [evidence],
        [control],
    )
    aggregates = aggregate_expanded_market_repair_application_rows(
        applications,
        evidence_rows,
        controls,
    )

    assert not issues
    assert applications[0]["repair_application_status"] == "BRANCH_LOCAL_REPAIR_APPLICATION_READY"
    assert applications[0]["repair_application_cost_adjusted_simulated_r"] == 0.07
    assert evidence_rows[0]["repair_application_evidence_status"] == "PRESERVED_NONCANDIDATE_REPAIR_APPLICATION_EVIDENCE"
    assert controls[0]["control_status"] == "EXPANDED_MARKET_REPAIR_APPLICATION_CONTROL_PASS"
    assert aggregates


def test_expanded_market_repair_application_execution_matches_held_execution_and_preserves_evidence():
    held_execution = {
        "expanded_market_impl_candidate_execution_row_id": "exec-1",
        "input_implementation_priority_row_id": "priority-1",
        "branch_local_candidate_scope_sha256": "scope-hash",
        "candidate_execution_status": "EXPANDED_MARKET_IMPL_CANDIDATE_EXECUTION_PASS",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "source_path": "source/a.csv",
        "source_file_sha256": "hash-a",
        "entry_reference": "unit-entry",
        "entry_reference_time": "2026-01-01T13:00:00Z",
        "proxy_entry_price": 100.0,
        "proxy_denominator_price": 1.0,
        "proxy_target_price": 101.0,
        "proxy_stop_price": 99.0,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "execution_cost_adjusted_simulated_r": 0.07,
        "execution_observed_stress_simulated_r": 0.15,
    }
    application = {
        "expanded_market_repair_application_row_id": "application-1",
        "input_impl_candidate_execution_row_id": "exec-1",
        "input_implementation_priority_row_id": "priority-1",
        "repair_application_status": "BRANCH_LOCAL_REPAIR_APPLICATION_READY",
        "repair_application_scope_sha256": "scope-hash",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "repair_application_source_path": "source/a.csv",
        "repair_application_source_file_sha256": "hash-a",
        "repair_application_entry_reference": "unit-entry",
        "repair_application_entry_reference_time": "2026-01-01T13:00:00Z",
        "repair_application_proxy_entry_price": 100.0,
        "repair_application_proxy_denominator_price": 1.0,
        "repair_application_proxy_target_price": 101.0,
        "repair_application_proxy_stop_price": 99.0,
        "repair_application_path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "repair_application_fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "repair_application_cost_adjusted_simulated_r": 0.07,
        "repair_application_stress_simulated_r": 0.15,
        "repair_application_effective_n": 35.0,
        "implementation_priority_class": "implementation-priority-positive-alternate-source-repair",
        "implementation_priority_tier": "repair-priority-positive",
    }
    evidence = {
        "expanded_market_repair_application_evidence_row_id": "evidence-1",
        "input_implementation_priority_row_id": "priority-2",
        "evidence_preservation_class": "kill-nonpositive-alternate-source-repair",
        "implementation_priority_tier": "not-new-implementation-priority",
        "keep_kill_redesign_implement_decision": "KILL_EXPANDED_MARKET_NONPOSITIVE_ALTERNATE_SOURCE_REPAIR",
    }
    control = {
        "expanded_market_repair_application_control_row_id": "control-1",
        "input_repair_application_row_id": "application-1",
        "control_status": "EXPANDED_MARKET_REPAIR_APPLICATION_CONTROL_PASS",
        "noncandidate_scope_leakage_count": 0,
    }

    executions, evidence_exec, controls, issues = expanded_market_repair_application_execution_rows(
        [application],
        [held_execution],
        [evidence],
        [control],
    )
    aggregates = aggregate_expanded_market_repair_application_execution_rows(
        executions,
        evidence_exec,
        controls,
    )

    assert not issues
    assert executions[0]["repair_application_execution_status"] == "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_PASS"
    assert executions[0]["repair_application_execution_match"] is True
    assert evidence_exec[0]["repair_application_execution_evidence_status"] == "PRESERVED_NONCANDIDATE_REPAIR_APPLICATION_EXECUTION_EVIDENCE"
    assert controls[0]["control_status"] == "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_CONTROL_PASS"
    assert aggregates


def test_expanded_market_repair_final_artifacts_keep_ready_execution_and_evidence():
    execution = {
        "expanded_market_repair_application_execution_row_id": "application-exec-1",
        "input_repair_application_row_id": "application-1",
        "input_impl_candidate_execution_row_id": "exec-1",
        "input_implementation_priority_row_id": "priority-1",
        "repair_application_execution_status": "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_PASS",
        "repair_application_scope_sha256": "scope-hash",
        "repair_application_expression": "scope=scope-hash",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "repair_application_source_path": "source/a.csv",
        "repair_application_source_file_sha256": "hash-a",
        "repair_application_entry_reference": "unit-entry",
        "repair_application_entry_reference_time": "2026-01-01T13:00:00Z",
        "repair_application_proxy_entry_price": 100.0,
        "repair_application_proxy_denominator_price": 1.0,
        "repair_application_proxy_target_price": 101.0,
        "repair_application_proxy_stop_price": 99.0,
        "repair_application_path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "repair_application_fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "repair_application_cost_adjusted_simulated_r": 0.07,
        "repair_application_stress_simulated_r": 0.15,
        "repair_application_effective_n": 35.0,
        "implementation_priority_class": "implementation-priority-positive-alternate-source-repair",
        "implementation_priority_tier": "repair-priority-positive",
    }
    evidence = {
        "expanded_market_repair_application_evidence_execution_row_id": "evidence-exec-1",
        "evidence_preservation_class": "kill-nonpositive-alternate-source-repair",
        "implementation_priority_tier": "not-new-implementation-priority",
        "keep_kill_redesign_implement_decision": "KILL_EXPANDED_MARKET_NONPOSITIVE_ALTERNATE_SOURCE_REPAIR",
    }
    control = {
        "expanded_market_repair_application_execution_control_row_id": "control-exec-1",
        "input_repair_application_execution_row_id": "application-exec-1",
        "control_status": "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_CONTROL_PASS",
        "noncandidate_scope_leakage_count": 0,
    }

    artifacts, evidence_rows, controls, issues = expanded_market_repair_final_artifact_rows(
        [execution],
        [evidence],
        [control],
    )
    aggregates = aggregate_expanded_market_repair_final_artifact_rows(
        artifacts,
        evidence_rows,
        controls,
    )

    assert not issues
    assert artifacts[0]["final_repair_artifact_status"] == "BRANCH_LOCAL_REPAIR_FINAL_ARTIFACT_READY"
    assert artifacts[0]["final_repair_artifact_cost_adjusted_simulated_r"] == 0.07
    assert artifacts[0]["final_repair_artifact_function_name"].startswith("apply_expanded_market_repair_")
    assert evidence_rows[0]["final_repair_artifact_evidence_status"] == "PRESERVED_NONCANDIDATE_REPAIR_FINAL_ARTIFACT_EVIDENCE"
    assert controls[0]["control_status"] == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_CONTROL_PASS"
    assert aggregates


def test_expanded_market_repair_final_artifact_execution_matches_held_execution_and_preserves_evidence():
    held = {
        "expanded_market_repair_application_execution_row_id": "application-exec-1",
        "input_repair_application_row_id": "application-1",
        "input_impl_candidate_execution_row_id": "exec-1",
        "input_implementation_priority_row_id": "priority-1",
        "repair_application_execution_status": "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_PASS",
        "repair_application_scope_sha256": "scope-hash",
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "repair_application_source_path": "source/a.csv",
        "repair_application_source_file_sha256": "hash-a",
        "repair_application_entry_reference": "unit-entry",
        "repair_application_entry_reference_time": "2026-01-01T13:00:00Z",
        "repair_application_proxy_entry_price": 100.0,
        "repair_application_proxy_denominator_price": 1.0,
        "repair_application_proxy_target_price": 101.0,
        "repair_application_proxy_stop_price": 99.0,
        "repair_application_path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "repair_application_fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "repair_application_cost_adjusted_simulated_r": 0.07,
        "repair_application_stress_simulated_r": 0.15,
        "implementation_priority_class": "implementation-priority-positive-alternate-source-repair",
        "implementation_priority_tier": "repair-priority-positive",
    }
    artifacts, evidence_rows, controls, artifact_issues = expanded_market_repair_final_artifact_rows(
        [held],
        [{"expanded_market_repair_application_evidence_execution_row_id": "evidence-exec-1"}],
        [
            {
                "expanded_market_repair_application_execution_control_row_id": "control-exec-1",
                "input_repair_application_execution_row_id": "application-exec-1",
                "control_status": "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_CONTROL_PASS",
                "noncandidate_scope_leakage_count": 0,
            }
        ],
    )

    executions, evidence_exec, control_exec, issues = expanded_market_repair_final_artifact_execution_rows(
        artifacts,
        [held],
        evidence_rows,
        controls,
    )
    aggregates = aggregate_expanded_market_repair_final_artifact_execution_rows(
        executions,
        evidence_exec,
        control_exec,
    )

    assert not artifact_issues
    assert not issues
    assert executions[0]["final_artifact_execution_status"] == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_PASS"
    assert executions[0]["final_artifact_execution_match"] is True
    assert evidence_exec[0]["final_artifact_execution_evidence_status"] == "PRESERVED_NONCANDIDATE_REPAIR_FINAL_ARTIFACT_EXECUTION_EVIDENCE"
    assert control_exec[0]["control_status"] == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL_PASS"
    assert aggregates


def test_expanded_market_repair_implementation_handoff_keeps_acceptance_and_preserves_evidence():
    execution = {
        "expanded_market_repair_final_artifact_execution_row_id": "artifact-exec-1",
        "input_repair_final_artifact_row_id": "artifact-1",
        "input_repair_application_execution_row_id": "application-exec-1",
        "input_implementation_priority_row_id": "priority-1",
        "final_artifact_execution_status": "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_PASS",
        "final_repair_artifact_scope_sha256": "artifact-scope-hash",
        "final_repair_artifact_expression": "scope=artifact-scope-hash",
        "final_repair_artifact_function_name": "apply_expanded_market_repair_artifact",
        "final_repair_artifact_source_path": "source/a.csv",
        "final_repair_artifact_source_file_sha256": "hash-a",
        "final_repair_artifact_cost_adjusted_simulated_r": 0.07,
        "final_repair_artifact_stress_simulated_r": 0.15,
        "final_repair_artifact_effective_n": 35.0,
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "repair_application_entry_reference": "unit-entry",
        "repair_application_entry_reference_time": "2026-01-01T13:00:00Z",
        "repair_application_path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "repair_application_fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "repair_application_proxy_entry_price": 100.0,
        "repair_application_proxy_denominator_price": 1.0,
        "repair_application_proxy_target_price": 101.0,
        "repair_application_proxy_stop_price": 99.0,
        "implementation_priority_class": "implementation-priority-positive-alternate-source-repair",
        "implementation_priority_tier": "repair-priority-positive",
    }
    evidence = {
        "expanded_market_repair_final_artifact_evidence_execution_row_id": "evidence-exec-1",
        "evidence_preservation_class": "kill-nonpositive-alternate-source-repair",
        "implementation_priority_tier": "not-new-implementation-priority",
        "keep_kill_redesign_implement_decision": "KILL_EXPANDED_MARKET_NONPOSITIVE_ALTERNATE_SOURCE_REPAIR",
    }
    control = {
        "expanded_market_repair_final_artifact_execution_control_row_id": "control-exec-1",
        "input_repair_final_artifact_execution_row_id": "artifact-exec-1",
        "control_status": "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL_PASS",
        "noncandidate_scope_leakage_count": 0,
    }

    handoffs, evidence_rows, controls, issues = expanded_market_repair_implementation_handoff_rows(
        [execution],
        [evidence],
        [control],
    )
    aggregates = aggregate_expanded_market_repair_implementation_handoff_rows(
        handoffs,
        evidence_rows,
        controls,
    )

    assert not issues
    assert handoffs[0]["implementation_handoff_status"] == "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_HANDOFF_READY"
    assert handoffs[0]["implementation_handoff_acceptance_sha256"]
    assert handoffs[0]["implementation_handoff_scope"]["final_repair_artifact_scope_sha256"] == "artifact-scope-hash"
    assert handoffs[0]["implementation_handoff_cost_adjusted_simulated_r"] == 0.07
    assert evidence_rows[0]["implementation_handoff_evidence_status"] == "PRESERVED_NONCANDIDATE_REPAIR_IMPLEMENTATION_HANDOFF_EVIDENCE"
    assert controls[0]["control_status"] == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_CONTROL_PASS"
    assert controls[0]["implementation_handoff_acceptance_sha256"] == handoffs[0]["implementation_handoff_acceptance_sha256"]
    assert aggregates


def test_expanded_market_repair_implementation_handoff_execution_matches_held_artifact_execution():
    artifact_execution = {
        "expanded_market_repair_final_artifact_execution_row_id": "artifact-exec-1",
        "input_repair_final_artifact_row_id": "artifact-1",
        "input_repair_application_execution_row_id": "application-exec-1",
        "input_implementation_priority_row_id": "priority-1",
        "final_artifact_execution_status": "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_PASS",
        "final_repair_artifact_scope_sha256": "artifact-scope-hash",
        "final_repair_artifact_expression": "scope=artifact-scope-hash",
        "final_repair_artifact_function_name": "apply_expanded_market_repair_artifact",
        "final_repair_artifact_source_path": "source/a.csv",
        "final_repair_artifact_source_file_sha256": "hash-a",
        "final_repair_artifact_cost_adjusted_simulated_r": 0.07,
        "final_repair_artifact_stress_simulated_r": 0.15,
        "final_repair_artifact_effective_n": 35.0,
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "repair_application_entry_reference": "unit-entry",
        "repair_application_entry_reference_time": "2026-01-01T13:00:00Z",
        "repair_application_path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "repair_application_fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "repair_application_proxy_entry_price": 100.0,
        "repair_application_proxy_denominator_price": 1.0,
        "repair_application_proxy_target_price": 101.0,
        "repair_application_proxy_stop_price": 99.0,
        "implementation_priority_class": "implementation-priority-positive-alternate-source-repair",
        "implementation_priority_tier": "repair-priority-positive",
    }
    handoffs, evidence_rows, controls, handoff_issues = expanded_market_repair_implementation_handoff_rows(
        [artifact_execution],
        [
            {
                "expanded_market_repair_final_artifact_evidence_execution_row_id": "evidence-exec-1",
                "keep_kill_redesign_implement_decision": "KILL_EXPANDED_MARKET_NONPOSITIVE_ALTERNATE_SOURCE_REPAIR",
            }
        ],
        [
            {
                "expanded_market_repair_final_artifact_execution_control_row_id": "control-exec-1",
                "input_repair_final_artifact_execution_row_id": "artifact-exec-1",
                "control_status": "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL_PASS",
                "noncandidate_scope_leakage_count": 0,
            }
        ],
    )

    executions, evidence_exec, control_exec, issues = (
        expanded_market_repair_implementation_handoff_execution_rows(
            handoffs,
            [artifact_execution],
            evidence_rows,
            controls,
        )
    )
    aggregates = aggregate_expanded_market_repair_implementation_handoff_execution_rows(
        executions,
        evidence_exec,
        control_exec,
    )

    assert not handoff_issues
    assert not issues
    assert executions[0]["handoff_execution_status"] == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_PASS"
    assert executions[0]["handoff_execution_match"] is True
    assert evidence_exec[0]["implementation_handoff_execution_evidence_status"] == "PRESERVED_NONCANDIDATE_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_EVIDENCE"
    assert control_exec[0]["control_status"] == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_CONTROL_PASS"
    assert aggregates


def test_expanded_market_repair_implementation_acceptance_preserves_contract_and_evidence():
    execution = {
        "expanded_market_repair_implementation_handoff_execution_row_id": "handoff-exec-1",
        "input_repair_implementation_handoff_row_id": "handoff-1",
        "input_repair_final_artifact_execution_row_id": "artifact-exec-1",
        "input_implementation_priority_row_id": "priority-1",
        "handoff_execution_status": "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_PASS",
        "implementation_handoff_acceptance_sha256": "acceptance-hash",
        "implementation_handoff_function_name": "apply_expanded_market_repair_artifact",
        "implementation_handoff_expression": "scope=artifact-scope-hash",
        "implementation_handoff_scope_sha256": "artifact-scope-hash",
        "implementation_handoff_source_path": "source/a.csv",
        "implementation_handoff_source_file_sha256": "hash-a",
        "implementation_handoff_entry_reference": "unit-entry",
        "implementation_handoff_entry_reference_time": "2026-01-01T13:00:00Z",
        "implementation_handoff_path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "implementation_handoff_fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "implementation_handoff_proxy_entry_price": 100.0,
        "implementation_handoff_proxy_denominator_price": 1.0,
        "implementation_handoff_proxy_target_price": 101.0,
        "implementation_handoff_proxy_stop_price": 99.0,
        "implementation_handoff_cost_adjusted_simulated_r": 0.07,
        "implementation_handoff_stress_simulated_r": 0.15,
        "implementation_handoff_effective_n": 35.0,
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "implementation_priority_class": "implementation-priority-positive-alternate-source-repair",
        "implementation_priority_tier": "repair-priority-positive",
    }
    evidence = {
        "expanded_market_repair_implementation_handoff_evidence_execution_row_id": "evidence-exec-1",
        "evidence_preservation_class": "carry-forward-existing-scored-action",
        "implementation_priority_tier": "not-new-implementation-priority",
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_CARRY_FORWARD_EXISTING_SCORED_ACTION",
    }
    control = {
        "expanded_market_repair_implementation_handoff_execution_control_row_id": "control-exec-1",
        "input_repair_implementation_handoff_execution_row_id": "handoff-exec-1",
        "control_status": "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_CONTROL_PASS",
        "noncandidate_scope_leakage_count": 0,
    }

    acceptances, evidence_rows, controls, issues = expanded_market_repair_implementation_acceptance_rows(
        [execution],
        [evidence],
        [control],
    )
    aggregates = aggregate_expanded_market_repair_implementation_acceptance_rows(
        acceptances,
        evidence_rows,
        controls,
    )

    assert not issues
    assert acceptances[0]["implementation_acceptance_status"] == "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_ACCEPTED"
    assert acceptances[0]["implementation_acceptance_contract_sha256"]
    assert acceptances[0]["accepted_cost_adjusted_simulated_r"] == 0.07
    assert evidence_rows[0]["implementation_acceptance_evidence_status"] == "PRESERVED_NONCANDIDATE_REPAIR_IMPLEMENTATION_ACCEPTANCE_EVIDENCE"
    assert controls[0]["control_status"] == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_ACCEPTANCE_CONTROL_PASS"
    assert controls[0]["implementation_acceptance_matches_execution"] is True
    assert aggregates


def test_expanded_market_repair_implementation_acceptance_execution_matches_held_contract():
    held_execution = {
        "expanded_market_repair_implementation_handoff_execution_row_id": "handoff-exec-1",
        "input_repair_implementation_handoff_row_id": "handoff-1",
        "input_repair_final_artifact_execution_row_id": "artifact-exec-1",
        "input_implementation_priority_row_id": "priority-1",
        "handoff_execution_status": "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_PASS",
        "implementation_handoff_acceptance_sha256": "acceptance-hash",
        "implementation_handoff_function_name": "apply_expanded_market_repair_artifact",
        "implementation_handoff_expression": "scope=artifact-scope-hash",
        "implementation_handoff_scope_sha256": "artifact-scope-hash",
        "implementation_handoff_source_path": "source/a.csv",
        "implementation_handoff_source_file_sha256": "hash-a",
        "implementation_handoff_entry_reference": "unit-entry",
        "implementation_handoff_entry_reference_time": "2026-01-01T13:00:00Z",
        "implementation_handoff_path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "implementation_handoff_fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "implementation_handoff_proxy_entry_price": 100.0,
        "implementation_handoff_proxy_denominator_price": 1.0,
        "implementation_handoff_proxy_target_price": 101.0,
        "implementation_handoff_proxy_stop_price": 99.0,
        "implementation_handoff_cost_adjusted_simulated_r": 0.07,
        "implementation_handoff_stress_simulated_r": 0.15,
        "implementation_handoff_effective_n": 35.0,
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market_timeframe": "M15",
        "route_session": "ny_core",
        "horizon_id": "h4",
        "side": "LONG",
        "implementation_priority_class": "implementation-priority-positive-alternate-source-repair",
        "implementation_priority_tier": "repair-priority-positive",
    }
    acceptances, evidence_rows, controls, acceptance_issues = (
        expanded_market_repair_implementation_acceptance_rows(
            [held_execution],
            [{"expanded_market_repair_implementation_handoff_evidence_execution_row_id": "evidence-exec-1"}],
            [
                {
                    "expanded_market_repair_implementation_handoff_execution_control_row_id": "control-exec-1",
                    "input_repair_implementation_handoff_execution_row_id": "handoff-exec-1",
                    "control_status": "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_CONTROL_PASS",
                    "noncandidate_scope_leakage_count": 0,
                }
            ],
        )
    )

    executions, evidence_exec, control_exec, issues = (
        expanded_market_repair_implementation_acceptance_execution_rows(
            acceptances,
            [held_execution],
            evidence_rows,
            controls,
        )
    )
    aggregates = aggregate_expanded_market_repair_implementation_acceptance_execution_rows(
        executions,
        evidence_exec,
        control_exec,
    )

    assert not acceptance_issues
    assert not issues
    assert executions[0]["acceptance_execution_status"] == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_ACCEPTANCE_EXECUTION_PASS"
    assert executions[0]["acceptance_execution_match"] is True
    assert evidence_exec[0]["implementation_acceptance_execution_evidence_status"] == "PRESERVED_NONCANDIDATE_REPAIR_IMPLEMENTATION_ACCEPTANCE_EXECUTION_EVIDENCE"
    assert control_exec[0]["control_status"] == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_ACCEPTANCE_EXECUTION_CONTROL_PASS"
    assert aggregates


def test_expanded_market_source_expansion_execution_scores_alternate_and_gap_rows():
    from collections import defaultdict

    from src.research_infra.moonshot_expanded_market_source_expansion_execution import (
        aggregate_key as source_expansion_aggregate_key,
        aggregate_rows_from_buckets as source_expansion_aggregate_rows_from_buckets,
        alternate_sources_for_row,
        empty_bucket as source_expansion_empty_bucket,
        source_expansion_execution_row,
        source_expansion_gap_row,
        source_index_by_alias_timeframe,
        update_bucket as source_expansion_update_bucket,
    )

    evidence = {
        "expanded_market_repair_implementation_acceptance_evidence_execution_row_id": "evidence-exec-1",
        "input_source_repair_reachability_row_id": "reach-1",
        "input_action_class_performance_row_id": "action-1",
        "evidence_preservation_class": "source-expansion-acquisition-proof",
        "source_repair_reachability_class": "source-expansion-new-source-required",
        "symbol_family": "GBPUSD_6B_FAMILY",
        "symbol": "GBPUSD",
        "source_symbol": "GBPUSD",
        "market_timeframe": "M1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h4",
        "side": "LONG",
        "source_path": "data/original/GBPUSD_M1.csv",
        "source_file_sha256": "original-hash",
        "source_component": "unit_source_component",
        "source_record_selector": "unit-record",
    }
    source = {
        "source_path": "data/alternate/GBPUSD_6B_M1.csv",
        "source_symbol": "GBPUSD_6B",
        "source_timeframe": "M1",
        "source_file_sha256": "alternate-hash",
        "source_access_status": "OHLC_CSV_REACHABLE",
    }
    score = {
        "score_status": "EXPANDED_MARKET_PROXY_R_SCORED",
        "entry_reference": "source_bar_close_then_forward_horizon_path",
        "entry_reference_time": "2026-01-01T00:00:00",
        "proxy_entry_price": 1.25,
        "proxy_denominator_price": 0.001,
        "proxy_target_price": 1.251,
        "proxy_stop_price": 1.249,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "path_order_counts": {"HORIZON_CLOSE_TARGET_PROXY_RESULT": 10},
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.25,
        "cost_adjusted_simulated_r": 0.23,
        "stress_simulated_r": 0.2,
        "win_count": 10,
        "loss_count": 4,
        "zero_count": 0,
        "target_first_count": 10,
        "stop_first_count": 4,
        "neither_count": 0,
        "ambiguous_count": 0,
        "effective_n": 14,
        "duplicate_row_count": 1,
        "effective_n_after_duplicate_collapse": 13,
        "concentration_top_month_share": 0.4,
        "cost_adjustment_r": 0.02,
        "stress_cost_adjustment_r": 0.05,
        "cost_proxy_status": "UNIT_COST_PROXY",
        "cost_proxy_symbol": "GBPUSD",
    }

    source_index = source_index_by_alias_timeframe([source])
    candidates = alternate_sources_for_row(evidence, source_index)
    execution = source_expansion_execution_row(evidence, candidates[0], score, 1)
    gap = source_expansion_gap_row(evidence, 1, 1, ["GBPUSD"], ["data"])
    buckets = defaultdict(source_expansion_empty_bucket)
    source_expansion_update_bucket(
        buckets[source_expansion_aggregate_key(execution, "execution")],
        execution,
        "execution",
    )
    source_expansion_update_bucket(
        buckets[source_expansion_aggregate_key(gap, "gap")],
        gap,
        "gap",
    )
    aggregates = source_expansion_aggregate_rows_from_buckets(buckets)

    assert candidates[0]["source_path"] == "data/alternate/GBPUSD_6B_M1.csv"
    assert execution["source_expansion_input_source_file_sha256"] == "original-hash"
    assert execution["source_expansion_candidate_source_file_sha256"] == "alternate-hash"
    assert execution["cost_adjusted_simulated_r"] == 0.23
    assert execution["missing_simulated_fields"] == []
    assert gap["missing_simulated_fields"] == ["additional_replay_source_path_hash_for_scope"]
    assert any(row["row_kind"] == "execution" and row["effective_n_sum"] == 14 for row in aggregates)
    assert any(row["row_kind"] == "gap" and row["gap_rows"] == 1 for row in aggregates)


def test_expanded_market_source_expansion_deconcentration_removes_dominant_month():
    from datetime import datetime, timedelta

    from src.research_infra.moonshot_expanded_market_source_expansion_deconcentration import (
        aggregate_deconcentration_rows,
        preserved_noncomputable_row,
        scored_deconcentration_row,
    )

    execution = {
        "expanded_market_source_expansion_execution_row_id": "source-exec-1",
        "score_status": "EXPANDED_MARKET_PROXY_R_SCORED",
        "symbol_family": "GBPUSD_6B_FAMILY",
        "symbol": "GBPUSD",
        "source_symbol": "GBPUSD_6B",
        "market_timeframe": "M1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h4",
        "side": "LONG",
        "source_expansion_candidate_source_path": "data/alternate/GBPUSD_6B_M1.csv",
        "source_expansion_candidate_source_file_sha256": "alternate-hash",
        "cost_adjustment_r": 0.01,
        "stress_cost_adjustment_r": 0.03,
        "cost_adjusted_simulated_r": 0.12,
        "stress_simulated_r": 0.1,
        "keep_kill_redesign_implement_decision": (
            "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_CONCENTRATION"
        ),
    }
    rows = []
    start = datetime(2026, 1, 1)
    for index in range(60):
        dt_value = start + timedelta(days=index)
        if index >= 30:
            dt_value = datetime(2026, 2, 1) + timedelta(days=index - 30)
        close = 100.0 + index * 0.1
        rows.append(
            {
                "time": dt_value.isoformat(),
                "dt": dt_value,
                "open": close - 0.05,
                "high": close + 0.2,
                "low": close - 0.2,
                "close": close,
            }
        )

    deconcentrated, month_rows = scored_deconcentration_row(execution, rows, 1)
    gap_preserved = preserved_noncomputable_row(
        {
            "expanded_market_source_expansion_gap_row_id": "gap-1",
            "symbol_family": "GBPUSD_6B_FAMILY",
            "symbol": "GBPUSD",
            "market_timeframe": "M1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h4",
            "side": "LONG",
            "source_path": "data/original/GBPUSD_M1.csv",
            "missing_simulated_fields": ["additional_replay_source_path_hash_for_scope"],
        },
        2,
        "source_gap",
    )
    aggregates = aggregate_deconcentration_rows([deconcentrated, gap_preserved])

    assert deconcentrated["source_expansion_deconcentration_status"] == "SOURCE_EXPANSION_DECONCENTRATION_REPLAYED"
    assert deconcentrated["dominant_month"] == "2026-01"
    assert deconcentrated["deconcentrated_effective_n"] > 0
    assert deconcentrated["deconcentrated_cost_adjusted_simulated_r"] is not None
    assert len(month_rows) == 2
    assert gap_preserved["source_expansion_deconcentration_status"] == "SOURCE_EXPANSION_DECONCENTRATION_LOCAL_SOURCE_GAP_PRESERVED"
    assert sum(row["row_count"] for row in aggregates) == 2


def test_expanded_market_source_expansion_action_execution_preserves_geometry_and_gap_proof():
    from src.research_infra.moonshot_expanded_market_source_expansion_action_execution import (
        action_execution_row,
        aggregate_action_rows,
    )

    deconcentrated = {
        "expanded_market_source_expansion_deconcentration_row_id": "decon-1",
        "input_source_expansion_execution_row_id": "source-exec-1",
        "source_expansion_deconcentration_status": "SOURCE_EXPANSION_DECONCENTRATION_REPLAYED",
        "symbol_family": "GBPUSD_6B_FAMILY",
        "symbol": "GBPUSD",
        "source_symbol": "GBPUSD_6B",
        "market_timeframe": "M1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h4",
        "side": "LONG",
        "source_path": "data/alternate/GBPUSD_6B_M1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "deconcentrated_gross_simulated_r": 0.16,
        "deconcentrated_cost_adjusted_simulated_r": 0.14,
        "deconcentrated_stress_simulated_r": 0.11,
        "deconcentrated_win_count": 30,
        "deconcentrated_loss_count": 10,
        "deconcentrated_zero_count": 0,
        "deconcentrated_average_win": 0.4,
        "deconcentrated_average_loss": -0.25,
        "deconcentrated_target_first_count": 30,
        "deconcentrated_stop_first_count": 10,
        "deconcentrated_neither_count": 0,
        "deconcentrated_ambiguous_count": 0,
        "deconcentrated_effective_n": 40,
        "remaining_top_month_share": 0.5,
        "dominant_month": "2026-01",
        "missing_simulated_fields": [],
        "keep_kill_redesign_implement_decision": (
            "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATED_PROXY_R"
        ),
    }
    source_execution = {
        "expanded_market_source_expansion_execution_row_id": "source-exec-1",
        "entry_reference": "source_bar_close_then_forward_horizon_path",
        "entry_reference_time": "2026-02-01T00:00:00",
        "proxy_entry_price": 1.25,
        "proxy_denominator_price": 0.001,
        "proxy_target_price": 1.251,
        "proxy_stop_price": 1.249,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "duplicate_row_count": 1,
        "effective_n_after_duplicate_collapse": 39,
    }
    month_rows = [
        {
            "month": "2026-02",
            "cost_adjusted_simulated_r": 0.12,
            "gross_simulated_r": 0.14,
            "stress_simulated_r": 0.09,
            "effective_n": 20,
            "path_order_counts": {"HORIZON_CLOSE_TARGET_PROXY_RESULT": 15},
        },
        {
            "month": "2026-03",
            "cost_adjusted_simulated_r": 0.16,
            "gross_simulated_r": 0.18,
            "stress_simulated_r": 0.13,
            "effective_n": 20,
            "path_order_counts": {"HORIZON_CLOSE_TARGET_PROXY_RESULT": 15},
        },
    ]

    action = action_execution_row(deconcentrated, source_execution, month_rows, 1)
    gap = action_execution_row(
        {
            "expanded_market_source_expansion_deconcentration_row_id": "decon-gap-1",
            "input_source_expansion_gap_row_id": "gap-1",
            "source_expansion_deconcentration_status": (
                "SOURCE_EXPANSION_DECONCENTRATION_LOCAL_SOURCE_GAP_PRESERVED"
            ),
            "symbol_family": "GBPUSD_6B_FAMILY",
            "symbol": "GBPUSD",
            "market_timeframe": "M1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h4",
            "side": "LONG",
            "source_path": "data/original/GBPUSD_M1.csv",
            "missing_simulated_fields": ["additional_replay_source_path_hash_for_scope"],
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_LOCAL_SOURCE_GAP"
            ),
        },
        None,
        [],
        2,
    )
    aggregates = aggregate_action_rows([action, gap])

    assert action["keep_kill_redesign_implement_decision"] == (
        "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION"
    )
    assert action["entry_reference"] == "source_bar_close_then_forward_horizon_path"
    assert action["proxy_denominator_price"] == 0.001
    assert action["month_fold_count"] == 2
    assert action["follow_inverse_default_off_avoid_class"] == "follow"
    assert gap["action_execution_status"] == "SOURCE_EXPANSION_ACTION_NONCOMPUTABLE_PRESERVED"
    assert gap["missing_simulated_fields"] == ["additional_replay_source_path_hash_for_scope"]
    assert gap["keep_kill_redesign_implement_decision"] == (
        "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_LOCAL_SOURCE_GAP"
    )
    assert sum(row["row_count"] for row in aggregates) == 2


def test_expanded_market_source_expansion_action_application_applies_rule_and_preserves_gap():
    from src.research_infra.moonshot_expanded_market_source_expansion_action_application import (
        action_rule_row,
        aggregate_application_rows,
        exact_scope_from_execution,
        execution_application_row,
        source_gap_application_row,
    )

    action = {
        "expanded_market_source_expansion_action_execution_row_id": "action-1",
        "input_source_expansion_execution_row_id": "source-exec-1",
        "keep_kill_redesign_implement_decision": (
            "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION"
        ),
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/historical_2026/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "entry_reference": "source_bar_close_then_forward_horizon_path",
        "proxy_denominator_price": 0.18,
        "proxy_target_price": 148.0,
        "proxy_stop_price": 147.6,
        "gross_simulated_r": 0.13,
        "cost_adjusted_simulated_r": 0.12,
        "stress_simulated_r": 0.11,
        "effective_n": 100,
        "month_fold_count": 4,
        "positive_month_share": 1.0,
        "negative_month_share": 0.0,
        "worst_month_cost_adjusted_simulated_r": 0.02,
        "concentration_top_month_share": 0.25,
    }
    rule = action_rule_row(action, 1)
    execution = {
        "expanded_market_source_expansion_execution_row_id": "source-exec-1",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_expansion_candidate_source_path": "data/historical_2026/USDJPY_H1.csv",
        "source_expansion_candidate_source_path_sha256": "path-hash",
        "source_expansion_candidate_source_file_sha256": "file-hash",
        "source_access_status": "OHLC_CSV_REACHABLE",
        "entry_reference": "source_bar_close_then_forward_horizon_path",
        "entry_reference_time": "2025-10-01T00:00:00",
        "proxy_entry_price": 147.8,
        "proxy_denominator_price": 0.18,
        "proxy_target_price": 148.0,
        "proxy_stop_price": 147.6,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "path_order_counts": {"HORIZON_CLOSE_TARGET_PROXY_RESULT": 10},
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.14,
        "cost_adjusted_simulated_r": 0.13,
        "stress_simulated_r": 0.12,
        "win_count": 12,
        "loss_count": 4,
        "zero_count": 0,
        "target_first_count": 12,
        "stop_first_count": 4,
        "neither_count": 0,
        "ambiguous_count": 0,
        "effective_n": 16,
        "duplicate_row_count": 0,
        "effective_n_after_duplicate_collapse": 16,
        "concentration_top_month_share": 0.25,
        "missing_simulated_fields": [],
    }
    assert tuple(rule["rule_expression"]["exact_scope"]) == exact_scope_from_execution(execution)

    applied = execution_application_row(
        execution,
        rule,
        "ACTION_APPLICATION_EXACT_RULE_APPLIED",
        1,
        1,
    )
    gap = source_gap_application_row(
        {
            "expanded_market_source_expansion_gap_row_id": "gap-1",
            "symbol_family": "AUDJPY",
            "symbol": "AUDJPY",
            "source_symbol": "AUDJPY",
            "market_timeframe": "D1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h4",
            "side": "LONG",
            "source_path": "data/historical_2026/AUDJPY_D1.csv",
            "source_path_sha256": "gap-path-hash",
            "source_file_sha256": "gap-file-hash",
            "source_expansion_gap_status": "NO_ALTERNATE_LOCAL_OHLC_SOURCE_FOR_SYMBOL_TIMEFRAME",
            "missing_simulated_fields": ["additional_replay_source_path_hash_for_scope"],
        },
        2,
    )
    aggregates = aggregate_application_rows([applied, gap])

    assert applied["input_action_application_rule_row_id"] == rule[
        "expanded_market_source_expansion_action_application_rule_row_id"
    ]
    assert applied["keep_kill_redesign_implement_decision"] == (
        "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION"
    )
    assert applied["cost_adjusted_simulated_r"] == 0.13
    assert applied["rule_cost_adjusted_simulated_r"] == 0.12
    assert applied["follow_inverse_default_off_avoid_class"] == "follow"
    assert gap["action_application_status"] == "ACTION_APPLICATION_SOURCE_GAP_PRESERVED"
    assert gap["missing_simulated_fields"] == ["additional_replay_source_path_hash_for_scope"]
    assert sum(row["row_count"] for row in aggregates) == 2


def test_expanded_market_source_expansion_action_pack_executes_and_preserves_work():
    from src.research_infra.moonshot_expanded_market_source_expansion_action_packs import (
        action_pack_row,
        action_pack_self_test_row,
        aggregate_action_pack_rows,
        execute_action_pack,
        replay_work_row,
    )

    applied = {
        "expanded_market_source_expansion_action_application_row_id": "app-1",
        "input_source_expansion_execution_row_id": "source-exec-1",
        "input_action_application_rule_row_id": "rule-1",
        "input_source_expansion_action_execution_row_id": "action-exec-1",
        "action_application_status": "ACTION_APPLICATION_EXACT_RULE_APPLIED",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/historical_2026/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "entry_reference": "source_bar_close_then_forward_horizon_path",
        "entry_reference_time": "2025-10-01T00:00:00",
        "proxy_entry_price": 147.8,
        "proxy_denominator_price": 0.18,
        "proxy_target_price": 148.0,
        "proxy_stop_price": 147.6,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.14,
        "cost_adjusted_simulated_r": 0.13,
        "stress_simulated_r": 0.12,
        "rule_cost_adjusted_simulated_r": 0.12,
        "win_count": 12,
        "loss_count": 4,
        "zero_count": 0,
        "target_first_count": 12,
        "stop_first_count": 4,
        "neither_count": 0,
        "ambiguous_count": 0,
        "effective_n": 16,
        "duplicate_row_count": 0,
        "effective_n_after_duplicate_collapse": 16,
        "concentration_top_month_share": 0.25,
        "follow_inverse_default_off_avoid_class": "follow",
        "keep_kill_redesign_implement_decision": (
            "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION"
        ),
    }
    work_source = {
        "expanded_market_source_expansion_action_application_row_id": "app-2",
        "input_source_expansion_gap_row_id": "gap-1",
        "action_application_status": "ACTION_APPLICATION_SOURCE_GAP_PRESERVED",
        "symbol_family": "AUDJPY",
        "symbol": "AUDJPY",
        "source_symbol": "AUDJPY",
        "market_timeframe": "D1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h4",
        "side": "LONG",
        "source_path": "data/historical_2026/AUDJPY_D1.csv",
        "source_path_sha256": "gap-path-hash",
        "source_file_sha256": "gap-file-hash",
        "source_access_status": "NO_ALTERNATE_LOCAL_OHLC_SOURCE_FOR_SYMBOL_TIMEFRAME",
        "fill_status": "NO_FILL_NO_REPLAY_SOURCE",
        "missing_simulated_fields": ["additional_replay_source_path_hash_for_scope"],
        "cost_adjusted_simulated_r": None,
    }

    pack = action_pack_row(applied, 1)
    execution = execute_action_pack(pack, applied)
    self_test = action_pack_self_test_row(pack, applied, 1)
    work = replay_work_row(work_source, 1)
    aggregates = aggregate_action_pack_rows([pack], [work])

    assert pack["action_pack_kind"] == "branch-local-follow-action-pack"
    assert execution["execution_pass"] is True
    assert self_test["self_test_status"] == "ACTION_PACK_SELF_TEST_PASS"
    assert work["work_status"] == "ACTION_PACK_SOURCE_GAP_WORK_PRESERVED"
    assert "alternate_replay_source_for_symbol_timeframe" in work["missing_work_fields"]
    assert sum(row["row_count"] for row in aggregates) == 2


def test_expanded_market_source_expansion_action_pack_execution_scans_candidates():
    from src.research_infra.moonshot_expanded_market_source_expansion_action_pack_execution import (
        aggregate_pack_execution_rows,
        contract_matches,
        pack_execution_row,
        pack_match_rows,
        work_execution_row,
    )

    pack = {
        "expanded_market_source_expansion_action_pack_row_id": "pack-1",
        "input_source_expansion_action_application_row_id": "app-1",
        "action_pack_kind": "branch-local-follow-action-pack",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/historical_2026/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "entry_reference": "source_bar_close_then_forward_horizon_path",
        "proxy_denominator_price": 0.18,
        "path_order_result": "HORIZON_CLOSE_TARGET_PROXY_RESULT",
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": 0.14,
        "cost_adjusted_simulated_r": 0.13,
        "stress_simulated_r": 0.12,
        "effective_n": 16,
        "concentration_top_month_share": 0.25,
        "branch_local_action_pack_match_contract": {
            "symbol_family": "USDJPY_6J",
            "symbol": "USDJPY_6J",
            "source_symbol": "USDJPY",
            "market_timeframe": "H1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h16",
            "side": "LONG",
            "source_path_sha256": "path-hash",
            "source_file_sha256": "file-hash",
            "entry_reference": "source_bar_close_then_forward_horizon_path",
        },
        "branch_local_action_pack_emit_contract": {
            "decision": "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION",
            "cost_adjusted_simulated_r": 0.13,
        },
        "follow_inverse_default_off_avoid_class": "follow",
        "keep_kill_redesign_implement_decision": (
            "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION"
        ),
    }
    matching_application = {
        "expanded_market_source_expansion_action_application_row_id": "app-1",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/historical_2026/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "entry_reference": "source_bar_close_then_forward_horizon_path",
        "gross_simulated_r": 0.14,
        "cost_adjusted_simulated_r": 0.13,
        "stress_simulated_r": 0.12,
        "follow_inverse_default_off_avoid_class": "follow",
        "keep_kill_redesign_implement_decision": (
            "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION"
        ),
    }
    nonmatching_application = {
        **matching_application,
        "expanded_market_source_expansion_action_application_row_id": "app-2",
        "source_path_sha256": "other-path-hash",
    }
    work = {
        "expanded_market_source_expansion_action_pack_work_row_id": "work-1",
        "input_source_expansion_action_application_row_id": "app-3",
        "work_status": "ACTION_PACK_SOURCE_GAP_WORK_PRESERVED",
        "symbol_family": "AUDJPY",
        "symbol": "AUDJPY",
        "source_symbol": "AUDJPY",
        "market_timeframe": "D1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h4",
        "side": "LONG",
        "source_path": "data/historical_2026/AUDJPY_D1.csv",
        "missing_work_fields": ["alternate_replay_source_for_symbol_timeframe"],
        "follow_inverse_default_off_avoid_class": "redesign",
        "keep_kill_redesign_implement_decision": (
            "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_REPLAY_WORK"
        ),
    }

    applications = [matching_application, nonmatching_application]
    execution = pack_execution_row(pack, applications, 1)
    matches = pack_match_rows(pack, execution, {"app-1": matching_application}, 1)
    work_execution = work_execution_row(work, 1)
    aggregates = aggregate_pack_execution_rows([execution], [work_execution])

    assert contract_matches(pack, matching_application) is True
    assert contract_matches(pack, nonmatching_application) is False
    assert execution["action_pack_execution_status"] == "ACTION_PACK_EXECUTION_PASS"
    assert execution["match_count"] == 1
    assert execution["negative_mismatch_count"] == 1
    assert matches[0]["input_source_expansion_action_application_row_id"] == "app-1"
    assert work_execution["work_execution_status"] == "ACTION_PACK_WORK_EXECUTION_PRESERVED"
    assert sum(row["row_count"] for row in aggregates) == 2


def test_expanded_market_source_expansion_action_pack_work_resolution_statuses():
    from src.research_infra.moonshot_expanded_market_source_expansion_action_pack_work_resolution import (
        aggregate_work_resolution_rows,
        work_resolution_row,
    )

    source_proof = {
        "current_source_path_exists": True,
        "current_source_file_sha256": "file-hash",
        "current_source_file_hash_matches_row": True,
        "discovered_same_symbol_timeframe_source_count": 1,
        "discovered_same_symbol_timeframe_source_paths": ["data/USDJPY_H1.csv"],
    }
    numeric_rule_work = {
        "expanded_market_source_expansion_action_pack_work_execution_row_id": "work-exec-1",
        "input_action_pack_work_row_id": "work-1",
        "input_source_expansion_action_application_row_id": "app-1",
        "work_status": "ACTION_PACK_NO_MONTH_STABLE_RULE_WORK_PRESERVED",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "gross_simulated_r": 0.1,
        "cost_adjusted_simulated_r": 0.08,
        "stress_simulated_r": 0.05,
        "effective_n": 100,
        "missing_work_fields": ["month_stable_action_rule_for_scope"],
    }
    replay_work = {
        **numeric_rule_work,
        "expanded_market_source_expansion_action_pack_work_execution_row_id": "work-exec-2",
        "work_status": "ACTION_PACK_NONCOMPUTABLE_REPLAY_WORK_PRESERVED",
        "cost_adjusted_simulated_r": None,
        "missing_work_fields": ["cost_adjusted_simulated_r"],
    }
    source_gap_work = {
        **numeric_rule_work,
        "expanded_market_source_expansion_action_pack_work_execution_row_id": "work-exec-3",
        "work_status": "ACTION_PACK_SOURCE_GAP_WORK_PRESERVED",
        "cost_adjusted_simulated_r": None,
        "missing_work_fields": ["alternate_replay_source_for_symbol_timeframe"],
    }

    numeric_row = work_resolution_row(numeric_rule_work, source_proof, 1)
    replay_row = work_resolution_row(replay_work, source_proof, 2)
    source_row = work_resolution_row(source_gap_work, source_proof, 3)
    aggregates = aggregate_work_resolution_rows([numeric_row, replay_row, source_row])

    assert numeric_row["work_resolution_status"] == (
        "ACTION_PACK_WORK_RESOLUTION_RULE_REDESIGN_NUMERIC_AVAILABLE"
    )
    assert replay_row["work_resolution_status"] == (
        "ACTION_PACK_WORK_RESOLUTION_REPLAY_IMPLEMENTATION_REQUIRED"
    )
    assert source_row["work_resolution_status"] == (
        "ACTION_PACK_WORK_RESOLUTION_SOURCE_ACQUISITION_REQUIRED"
    )
    assert numeric_row["current_source_file_hash_matches_row"] is True
    assert sum(row["row_count"] for row in aggregates) == 3


def test_expanded_market_source_expansion_work_task_materialization_rows():
    from src.research_infra.moonshot_expanded_market_source_expansion_work_task_materialization import (
        aggregate_task_rows,
        replay_task_row,
        rule_candidate_row,
        rule_candidate_self_test_row,
        source_task_row,
    )

    numeric_resolution = {
        "expanded_market_source_expansion_action_pack_work_resolution_row_id": "res-1",
        "input_action_pack_work_execution_row_id": "work-exec-1",
        "work_resolution_status": "ACTION_PACK_WORK_RESOLUTION_RULE_REDESIGN_NUMERIC_AVAILABLE",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "current_source_path_exists": True,
        "current_source_file_sha256": "file-hash",
        "current_source_file_hash_matches_row": True,
        "gross_simulated_r": 0.12,
        "cost_adjusted_simulated_r": 0.11,
        "stress_simulated_r": 0.08,
        "effective_n": 100,
        "missing_work_fields": ["month_stable_action_rule_for_scope"],
    }
    replay_resolution = {
        **numeric_resolution,
        "expanded_market_source_expansion_action_pack_work_resolution_row_id": "res-2",
        "work_resolution_status": "ACTION_PACK_WORK_RESOLUTION_REPLAY_IMPLEMENTATION_REQUIRED",
        "cost_adjusted_simulated_r": None,
        "missing_work_fields": ["cost_adjusted_simulated_r"],
    }
    source_resolution = {
        **numeric_resolution,
        "expanded_market_source_expansion_action_pack_work_resolution_row_id": "res-3",
        "work_resolution_status": "ACTION_PACK_WORK_RESOLUTION_SOURCE_ACQUISITION_REQUIRED",
        "cost_adjusted_simulated_r": None,
        "missing_work_fields": ["alternate_replay_source_for_symbol_timeframe"],
        "discovered_same_symbol_timeframe_source_count": 1,
        "discovered_same_symbol_timeframe_source_paths": ["data/USDJPY_H1.csv"],
    }

    candidate = rule_candidate_row(numeric_resolution, 1)
    self_test = rule_candidate_self_test_row(candidate, numeric_resolution, 1)
    replay_task = replay_task_row(replay_resolution, 1)
    source_task = source_task_row(source_resolution, 1)
    aggregates = aggregate_task_rows([candidate], [replay_task], [source_task])

    assert candidate["rule_candidate_class"] == "rule-redesign-positive-follow-retest"
    assert candidate["keep_kill_redesign_implement_decision"] == (
        "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_POSITIVE_RULE_RETEST"
    )
    assert self_test["self_test_status"] == "SOURCE_EXPANSION_RULE_CANDIDATE_SELF_TEST_PASS"
    assert replay_task["replay_task_status"] == "SOURCE_EXPANSION_REPLAY_IMPLEMENTATION_TASK_MATERIALIZED"
    assert source_task["source_task_status"] == "SOURCE_EXPANSION_SOURCE_ACQUISITION_TASK_MATERIALIZED"
    assert sum(row["row_count"] for row in aggregates) == 3


def test_expanded_market_source_expansion_rule_candidate_execution_scans_rows():
    from src.research_infra.moonshot_expanded_market_source_expansion_rule_candidate_execution import (
        aggregate_rule_execution_rows,
        candidate_matches,
        replay_task_execution_row,
        rule_candidate_execution_row,
        rule_match_rows,
        source_task_execution_row,
    )

    candidate = {
        "expanded_market_source_expansion_rule_candidate_row_id": "rule-1",
        "input_work_resolution_row_id": "res-1",
        "rule_candidate_class": "rule-redesign-positive-follow-retest",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "gross_simulated_r": 0.12,
        "cost_adjusted_simulated_r": 0.11,
        "stress_simulated_r": 0.08,
        "effective_n": 100,
        "branch_local_rule_candidate_match_contract": {
            "symbol_family": "USDJPY_6J",
            "symbol": "USDJPY_6J",
            "source_symbol": "USDJPY",
            "market_timeframe": "H1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h16",
            "side": "LONG",
            "source_path_sha256": "path-hash",
            "source_file_sha256": "file-hash",
            "work_resolution_status": "ACTION_PACK_WORK_RESOLUTION_RULE_REDESIGN_NUMERIC_AVAILABLE",
        },
        "branch_local_rule_candidate_emit_contract": {"cost_adjusted_simulated_r": 0.11},
        "keep_kill_redesign_implement_decision": (
            "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_POSITIVE_RULE_RETEST"
        ),
    }
    matching_work = {
        "expanded_market_source_expansion_action_pack_work_resolution_row_id": "res-1",
        "work_resolution_status": "ACTION_PACK_WORK_RESOLUTION_RULE_REDESIGN_NUMERIC_AVAILABLE",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "gross_simulated_r": 0.12,
        "cost_adjusted_simulated_r": 0.11,
        "stress_simulated_r": 0.08,
    }
    nonmatching_work = {**matching_work, "expanded_market_source_expansion_action_pack_work_resolution_row_id": "res-2", "source_path_sha256": "other"}
    replay_task = {
        "expanded_market_source_expansion_replay_task_row_id": "replay-1",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/USDJPY_H1.csv",
        "missing_work_fields": ["cost_adjusted_simulated_r"],
        "keep_kill_redesign_implement_decision": (
            "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_REPLAY_TASK_MATERIALIZED"
        ),
    }
    source_task = {
        "expanded_market_source_expansion_source_task_row_id": "source-1",
        "symbol_family": "AUDJPY",
        "symbol": "AUDJPY",
        "source_symbol": "AUDJPY",
        "market_timeframe": "D1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h4",
        "side": "LONG",
        "source_path": "data/AUDJPY_D1.csv",
        "missing_work_fields": ["alternate_replay_source_for_symbol_timeframe"],
        "discovered_same_symbol_timeframe_source_paths": ["data/AUDJPY_D1.csv"],
        "keep_kill_redesign_implement_decision": (
            "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_SOURCE_TASK_MATERIALIZED"
        ),
    }

    work_rows = [matching_work, nonmatching_work]
    execution = rule_candidate_execution_row(candidate, work_rows, 1)
    matches = rule_match_rows(candidate, execution, {"res-1": matching_work}, 1)
    replay_execution = replay_task_execution_row(replay_task, 1)
    source_execution = source_task_execution_row(source_task, 1)
    aggregates = aggregate_rule_execution_rows([execution], [replay_execution], [source_execution])

    assert candidate_matches(candidate, matching_work) is True
    assert candidate_matches(candidate, nonmatching_work) is False
    assert execution["rule_candidate_execution_status"] == (
        "SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION_PASS"
    )
    assert execution["match_count"] == 1
    assert execution["negative_mismatch_count"] == 1
    assert matches[0]["input_work_resolution_row_id"] == "res-1"
    assert replay_execution["replay_task_execution_status"] == "SOURCE_EXPANSION_REPLAY_TASK_EXECUTION_PRESERVED"
    assert source_execution["source_task_execution_status"] == "SOURCE_EXPANSION_SOURCE_TASK_EXECUTION_PRESERVED"
    assert sum(row["row_count"] for row in aggregates) == 3


def test_expanded_market_source_expansion_rule_match_performance_rows():
    from src.research_infra.moonshot_expanded_market_source_expansion_rule_match_performance import (
        aggregate_performance_rows,
        new_stats,
        replay_task_performance_row,
        rule_match_performance_row,
        source_task_performance_row,
        update_stats,
    )

    rule_execution = {
        "expanded_market_source_expansion_rule_candidate_execution_row_id": "exec-1",
        "input_rule_candidate_row_id": "rule-1",
        "input_work_resolution_row_id": "res-1",
        "rule_candidate_class": "rule-redesign-positive-follow-retest",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "candidate_rows_scanned": 3,
        "match_count": 3,
        "effective_n": 100,
    }
    matches = [
        {
            "input_work_resolution_row_id": "res-1",
            "source_path_sha256": "path-hash",
            "symbol_family": "USDJPY_6J",
            "side": "LONG",
            "source_file_sha256": "file-hash",
            "gross_simulated_r": 0.20,
            "cost_adjusted_simulated_r": 0.18,
            "stress_simulated_r": 0.15,
        },
        {
            "input_work_resolution_row_id": "res-2",
            "source_path_sha256": "path-hash",
            "symbol_family": "USDJPY_6J",
            "side": "LONG",
            "source_file_sha256": "file-hash",
            "gross_simulated_r": 0.10,
            "cost_adjusted_simulated_r": 0.08,
            "stress_simulated_r": 0.04,
        },
        {
            "input_work_resolution_row_id": "res-3",
            "source_path_sha256": "path-hash",
            "symbol_family": "USDJPY_6J",
            "side": "LONG",
            "source_file_sha256": "file-hash",
            "gross_simulated_r": -0.02,
            "cost_adjusted_simulated_r": -0.01,
            "stress_simulated_r": -0.02,
        },
    ]
    stats = new_stats()
    for match in matches:
        update_stats(stats, match)

    performance = rule_match_performance_row(rule_execution, stats, 1)
    replay_perf = replay_task_performance_row(
        {
            "expanded_market_source_expansion_replay_task_execution_row_id": "replay-1",
            "symbol_family": "USDJPY_6J",
            "symbol": "USDJPY_6J",
            "source_symbol": "USDJPY",
            "market_timeframe": "H1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h16",
            "side": "LONG",
            "missing_work_fields": ["cost_adjusted_simulated_r"],
        },
        1,
    )
    source_perf = source_task_performance_row(
        {
            "expanded_market_source_expansion_source_task_execution_row_id": "source-1",
            "symbol_family": "AUDJPY",
            "symbol": "AUDJPY",
            "source_symbol": "AUDJPY",
            "market_timeframe": "D1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h4",
            "side": "LONG",
            "missing_work_fields": ["alternate_replay_source_for_symbol_timeframe"],
        },
        1,
    )
    aggregates = aggregate_performance_rows([performance], [replay_perf], [source_perf])

    assert performance["observed_match_rows"] == 3
    assert performance["win_count"] == 2
    assert performance["loss_count"] == 1
    assert performance["follow_inverse_default_off_avoid_class"] == "follow"
    assert performance["keep_kill_redesign_implement_decision"] == (
        "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_UNDERPOWERED"
    )
    assert replay_perf["replay_task_performance_status"] == "SOURCE_EXPANSION_REPLAY_TASK_PERFORMANCE_PRESERVED"
    assert source_perf["source_task_performance_status"] == "SOURCE_EXPANSION_SOURCE_TASK_PERFORMANCE_PRESERVED"
    assert sum(row["row_count"] for row in aggregates) == 3


def test_expanded_market_source_expansion_rule_match_action_application_rows():
    from src.research_infra.moonshot_expanded_market_source_expansion_rule_match_action_application import (
        action_self_test_row,
        aggregate_action_rows,
        replay_task_action_row,
        rule_match_action_row,
        source_task_action_row,
    )

    performance = {
        "expanded_market_source_expansion_rule_match_performance_row_id": "perf-1",
        "input_rule_candidate_execution_row_id": "exec-1",
        "rule_candidate_class": "rule-redesign-positive-follow-retest",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "observed_match_rows": 12,
        "effective_n": 12,
        "duplicate_inflation": 1.0,
        "gross_simulated_r": 0.12,
        "cost_adjusted_simulated_r": 0.10,
        "stress_simulated_r": 0.06,
        "gross_simulated_r_expectancy": 0.12,
        "cost_adjusted_simulated_r_expectancy": 0.10,
        "stress_simulated_r_expectancy": 0.06,
        "win_count": 8,
        "loss_count": 4,
        "zero_count": 0,
        "win_rate": 0.667,
        "average_win": 0.20,
        "average_loss": -0.10,
        "dominant_source_path_share": 1.0,
        "dominant_source_file_share": 1.0,
        "follow_inverse_default_off_avoid_class": "follow",
        "keep_kill_redesign_implement_decision": (
            "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_FOLLOW"
        ),
    }
    action = rule_match_action_row(performance, 1)
    self_test = action_self_test_row(action, 1)
    replay_action = replay_task_action_row(
        {
            "expanded_market_source_expansion_replay_task_performance_row_id": "replay-perf-1",
            "symbol_family": "USDJPY_6J",
            "symbol": "USDJPY_6J",
            "source_symbol": "USDJPY",
            "market_timeframe": "H1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h16",
            "side": "LONG",
            "missing_work_fields": ["cost_adjusted_simulated_r"],
        },
        1,
    )
    source_action = source_task_action_row(
        {
            "expanded_market_source_expansion_source_task_performance_row_id": "source-perf-1",
            "symbol_family": "AUDJPY",
            "symbol": "AUDJPY",
            "source_symbol": "AUDJPY",
            "market_timeframe": "D1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h4",
            "side": "LONG",
            "missing_work_fields": ["alternate_replay_source_for_symbol_timeframe"],
        },
        1,
    )
    aggregates = aggregate_action_rows([action], [replay_action], [source_action])

    assert action["rule_match_action_status"] == "SOURCE_EXPANSION_RULE_MATCH_ACTION_FOLLOW_READY"
    assert action["keep_kill_redesign_implement_decision"] == (
        "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_FOLLOW_RULE_ACTION"
    )
    assert self_test["self_test_status"] == "SOURCE_EXPANSION_RULE_MATCH_ACTION_SELF_TEST_PASS"
    assert replay_action["replay_task_action_status"] == "SOURCE_EXPANSION_REPLAY_TASK_ACTION_REQUIRED"
    assert source_action["source_task_action_status"] == "SOURCE_EXPANSION_SOURCE_TASK_ACTION_REQUIRED"
    assert sum(row["row_count"] for row in aggregates) == 3


def test_expanded_market_source_expansion_rule_match_action_execution_rows():
    from src.research_infra.moonshot_expanded_market_source_expansion_rule_match_action_execution import (
        action_matches_performance,
        aggregate_execution_rows,
        ready_action_execution_row,
        ready_action_match_rows,
        redesign_action_execution_row,
        replay_task_execution_row,
        source_task_execution_row,
    )

    performance = {
        "expanded_market_source_expansion_rule_match_performance_row_id": "perf-1",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "cost_adjusted_simulated_r_expectancy": 0.10,
        "stress_simulated_r_expectancy": 0.06,
    }
    action = {
        "expanded_market_source_expansion_rule_match_action_row_id": "action-1",
        "input_rule_match_performance_row_id": "perf-1",
        "rule_match_action_kind": "branch-local-follow-rule-action",
        "rule_match_action_status": "SOURCE_EXPANSION_RULE_MATCH_ACTION_FOLLOW_READY",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "observed_match_rows": 12,
        "effective_n": 12,
        "duplicate_inflation": 1.0,
        "gross_simulated_r": 0.12,
        "cost_adjusted_simulated_r": 0.10,
        "stress_simulated_r": 0.06,
        "gross_simulated_r_expectancy": 0.12,
        "cost_adjusted_simulated_r_expectancy": 0.10,
        "stress_simulated_r_expectancy": 0.06,
        "win_count": 8,
        "loss_count": 4,
        "zero_count": 0,
        "win_rate": 0.667,
        "average_win": 0.20,
        "average_loss": -0.10,
        "follow_inverse_default_off_avoid_class": "follow",
        "keep_kill_redesign_implement_decision": (
            "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_FOLLOW_RULE_ACTION"
        ),
    }
    nonmatching = {**performance, "expanded_market_source_expansion_rule_match_performance_row_id": "perf-2", "side": "SHORT"}
    ready_execution = ready_action_execution_row(action, [performance, nonmatching], 1)
    match_rows = ready_action_match_rows(action, ready_execution, {"perf-1": performance}, 1)
    redesign_execution = redesign_action_execution_row(
        {
            **action,
            "expanded_market_source_expansion_rule_match_action_row_id": "action-2",
            "rule_match_action_status": "SOURCE_EXPANSION_RULE_MATCH_ACTION_MIXED_REDESIGN",
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_MIXED_RULE_ACTION"
            ),
        },
        1,
    )
    replay_execution = replay_task_execution_row(
        {
            "expanded_market_source_expansion_replay_task_action_row_id": "replay-action-1",
            "symbol_family": "USDJPY_6J",
            "symbol": "USDJPY_6J",
            "source_symbol": "USDJPY",
            "market_timeframe": "H1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h16",
            "side": "LONG",
            "missing_work_fields": ["cost_adjusted_simulated_r"],
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_REPLAY_TASK_ACTION"
            ),
        },
        1,
    )
    source_execution = source_task_execution_row(
        {
            "expanded_market_source_expansion_source_task_action_row_id": "source-action-1",
            "symbol_family": "AUDJPY",
            "symbol": "AUDJPY",
            "source_symbol": "AUDJPY",
            "market_timeframe": "D1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h4",
            "side": "LONG",
            "missing_work_fields": ["alternate_replay_source_for_symbol_timeframe"],
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_SOURCE_TASK_ACTION"
            ),
        },
        1,
    )
    aggregates = aggregate_execution_rows(
        [ready_execution], [redesign_execution], [replay_execution], [source_execution]
    )

    assert action_matches_performance(action, performance) is True
    assert action_matches_performance(action, nonmatching) is False
    assert ready_execution["ready_action_execution_status"] == (
        "SOURCE_EXPANSION_RULE_MATCH_READY_ACTION_EXECUTION_PASS"
    )
    assert ready_execution["match_count"] == 1
    assert ready_execution["negative_mismatch_count"] == 1
    assert match_rows[0]["input_rule_match_performance_row_id"] == "perf-1"
    assert redesign_execution["redesign_action_execution_status"] == (
        "SOURCE_EXPANSION_RULE_MATCH_REDESIGN_ACTION_PRESERVED"
    )
    assert replay_execution["replay_task_action_execution_status"] == (
        "SOURCE_EXPANSION_REPLAY_TASK_ACTION_EXECUTION_PRESERVED"
    )
    assert source_execution["source_task_action_execution_status"] == (
        "SOURCE_EXPANSION_SOURCE_TASK_ACTION_EXECUTION_PRESERVED"
    )
    assert sum(row["row_count"] for row in aggregates) == 4


def test_expanded_market_source_expansion_ready_action_implementation_rows():
    from src.research_infra.moonshot_expanded_market_source_expansion_ready_action_implementation import (
        aggregate_implementation_rows,
        implementation_self_test_row,
        ready_implementation_candidate_row,
        redesign_implementation_task_row,
        replay_implementation_task_row,
        source_implementation_task_row,
    )

    ready_execution = {
        "expanded_market_source_expansion_rule_match_ready_action_execution_row_id": "ready-exec-1",
        "input_rule_match_action_row_id": "action-1",
        "input_rule_match_performance_row_id": "perf-1",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "observed_match_rows": 12,
        "effective_n": 12,
        "duplicate_inflation": 1.0,
        "gross_simulated_r": 0.12,
        "cost_adjusted_simulated_r": 0.10,
        "stress_simulated_r": 0.06,
        "gross_simulated_r_expectancy": 0.12,
        "cost_adjusted_simulated_r_expectancy": 0.10,
        "stress_simulated_r_expectancy": 0.06,
        "win_count": 8,
        "loss_count": 4,
        "zero_count": 0,
        "win_rate": 0.667,
        "average_win": 0.20,
        "average_loss": -0.10,
        "match_count": 1,
        "held_performance_rows_scanned": 100,
        "follow_inverse_default_off_avoid_class": "follow",
        "keep_kill_redesign_implement_decision": (
            "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_FOLLOW_RULE_ACTION"
        ),
    }
    candidate = ready_implementation_candidate_row(ready_execution, 1)
    self_test = implementation_self_test_row(candidate, 1)
    redesign = redesign_implementation_task_row(
        {
            "expanded_market_source_expansion_rule_match_redesign_action_execution_row_id": "redesign-1",
            "symbol_family": "USDJPY_6J",
            "symbol": "USDJPY_6J",
            "source_symbol": "USDJPY",
            "market_timeframe": "H1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h16",
            "side": "LONG",
            "observed_match_rows": 3,
            "effective_n": 3,
            "cost_adjusted_simulated_r": 0.02,
            "stress_simulated_r": -0.01,
            "follow_inverse_default_off_avoid_class": "default-off",
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_MIXED_RULE_ACTION"
            ),
        },
        1,
    )
    replay = replay_implementation_task_row(
        {
            "expanded_market_source_expansion_replay_task_action_execution_row_id": "replay-exec-1",
            "symbol_family": "USDJPY_6J",
            "symbol": "USDJPY_6J",
            "source_symbol": "USDJPY",
            "market_timeframe": "H1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h16",
            "side": "LONG",
            "missing_work_fields": ["cost_adjusted_simulated_r"],
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_REPLAY_TASK_ACTION"
            ),
        },
        1,
    )
    source = source_implementation_task_row(
        {
            "expanded_market_source_expansion_source_task_action_execution_row_id": "source-exec-1",
            "symbol_family": "AUDJPY",
            "symbol": "AUDJPY",
            "source_symbol": "AUDJPY",
            "market_timeframe": "D1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h4",
            "side": "LONG",
            "missing_work_fields": ["alternate_replay_source_for_symbol_timeframe"],
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_SOURCE_TASK_ACTION"
            ),
        },
        1,
    )
    aggregates = aggregate_implementation_rows([candidate], [redesign], [replay], [source])

    assert candidate["ready_action_implementation_status"] == (
        "SOURCE_EXPANSION_READY_ACTION_FOLLOW_IMPLEMENTATION_CANDIDATE"
    )
    assert candidate["keep_kill_redesign_implement_decision"] == (
        "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_FOLLOW_READY_ACTION"
    )
    assert self_test["self_test_status"] == "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_SELF_TEST_PASS"
    assert redesign["redesign_implementation_task_status"] == (
        "SOURCE_EXPANSION_REDESIGN_IMPLEMENTATION_TASK_PRESERVED"
    )
    assert replay["replay_implementation_task_status"] == (
        "SOURCE_EXPANSION_REPLAY_IMPLEMENTATION_TASK_PRESERVED"
    )
    assert source["source_implementation_task_status"] == (
        "SOURCE_EXPANSION_SOURCE_IMPLEMENTATION_TASK_PRESERVED"
    )
    assert sum(row["row_count"] for row in aggregates) == 4


def test_expanded_market_source_expansion_ready_action_implementation_execution_rows():
    from src.research_infra.moonshot_expanded_market_source_expansion_ready_action_implementation_execution import (
        aggregate_execution_rows,
        candidate_matches_ready_execution,
        implementation_execution_row,
        implementation_match_rows,
        task_execution_row,
    )

    candidate = {
        "expanded_market_source_expansion_ready_action_implementation_candidate_row_id": "impl-1",
        "input_ready_action_execution_row_id": "ready-exec-1",
        "ready_action_implementation_kind": "branch-local-expanded-market-follow-implementation-candidate",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "observed_match_rows": 12,
        "effective_n": 12,
        "duplicate_inflation": 1.0,
        "gross_simulated_r": 0.12,
        "cost_adjusted_simulated_r": 0.10,
        "stress_simulated_r": 0.06,
        "gross_simulated_r_expectancy": 0.12,
        "cost_adjusted_simulated_r_expectancy": 0.10,
        "stress_simulated_r_expectancy": 0.06,
        "win_count": 8,
        "loss_count": 4,
        "zero_count": 0,
        "win_rate": 0.667,
        "average_win": 0.20,
        "average_loss": -0.10,
        "follow_inverse_default_off_avoid_class": "follow",
        "keep_kill_redesign_implement_decision": (
            "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_FOLLOW_READY_ACTION"
        ),
    }
    ready_row = {
        "expanded_market_source_expansion_rule_match_ready_action_execution_row_id": "ready-exec-1",
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "cost_adjusted_simulated_r_expectancy": 0.10,
        "stress_simulated_r_expectancy": 0.06,
    }
    nonmatching = {**ready_row, "expanded_market_source_expansion_rule_match_ready_action_execution_row_id": "ready-exec-2", "side": "SHORT"}
    execution = implementation_execution_row(candidate, [ready_row, nonmatching], 1)
    matches = implementation_match_rows(candidate, execution, {"ready-exec-1": ready_row}, 1)
    task = task_execution_row(
        {
            "symbol_family": "USDJPY_6J",
            "symbol": "USDJPY_6J",
            "source_symbol": "USDJPY",
            "market_timeframe": "H1",
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h16",
            "side": "LONG",
            "missing_work_fields": ["cost_adjusted_simulated_r"],
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_REPLAY_TASK_ACTION"
            ),
        },
        "replay_implementation_task",
        1,
    )
    aggregates = aggregate_execution_rows([execution], [task])

    assert candidate_matches_ready_execution(candidate, ready_row) is True
    assert candidate_matches_ready_execution(candidate, nonmatching) is False
    assert execution["ready_action_implementation_execution_status"] == (
        "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_EXECUTION_PASS"
    )
    assert execution["match_count"] == 1
    assert execution["negative_mismatch_count"] == 1
    assert matches[0]["input_ready_action_execution_row_id"] == "ready-exec-1"
    assert task["task_execution_status"] == "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_TASK_PRESERVED"
    assert sum(row["row_count"] for row in aggregates) == 2


def test_frozen_universe_implementation_closure_classification_and_coverage():
    from src.research_infra.moonshot_frozen_universe_implementation_closure import (
        classify_row,
        closure_action_row,
        coverage_key,
        coverage_row,
        new_coverage_bucket,
        update_coverage_bucket,
    )

    ready = {
        "ready_action_implementation_execution_status": (
            "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_EXECUTION_PASS"
        ),
        "keep_kill_redesign_implement_decision": (
            "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_FOLLOW_READY_ACTION"
        ),
        "symbol_family": "USDJPY_6J",
        "symbol": "USDJPY_6J",
        "source_symbol": "USDJPY",
        "market_timeframe": "H1",
        "route_session": "ALL_SESSIONS",
        "horizon_id": "h16",
        "side": "LONG",
        "source_path": "data/USDJPY_H1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "cost_adjusted_simulated_r": 0.12,
        "stress_simulated_r": 0.08,
        "effective_n": 12,
        "follow_inverse_default_off_avoid_class": "follow",
    }
    source_gap = {
        "task_execution_status": "SOURCE_EXPANSION_SOURCE_TASK_ACTION_EXECUTION_PRESERVED",
        "keep_kill_redesign_implement_decision": (
            "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_SOURCE_TASK_ACTION"
        ),
        "symbol_family": "AUDJPY",
        "symbol": "AUDJPY",
        "market_timeframe": "D1",
        "missing_work_fields": ["reachable_historical_source_path"],
    }
    mixed = {
        "action_status": "SOURCE_EXPANSION_RULE_MATCH_ACTION_MIXED_REDESIGN",
        "symbol_family": "GBPJPY",
        "market_timeframe": "M15",
        "side": "SHORT",
    }

    ready_class = classify_row(ready, "READY_ACTION_IMPLEMENTATION_EXECUTION_LEDGER.jsonl")
    source_class = classify_row(source_gap, "SOURCE_TASK_ACTION_EXECUTION_LEDGER.jsonl")
    mixed_class = classify_row(mixed, "RULE_MATCH_ACTION_LEDGER.jsonl")
    action = closure_action_row(
        ready,
        "research/path/READY_ACTION_IMPLEMENTATION_EXECUTION_LEDGER.jsonl",
        "READY_ACTION_IMPLEMENTATION_EXECUTION_LEDGER.jsonl",
        "test_role",
        "checkpoint_279",
        1,
    )
    key = coverage_key(ready)
    bucket = new_coverage_bucket(key)
    update_coverage_bucket(bucket, ready, ready_class, "artifact.jsonl", "checkpoint_279")
    covered = coverage_row(bucket, 1)

    assert ready_class["classification"] == "implementation_ready"
    assert source_class["classification"] == "source_repair_required"
    assert source_class["missing_fields"] == ["reachable_historical_source_path"]
    assert mixed_class["classification"] == "redesign_mixed"
    assert action["concrete_outcome"]
    assert covered["row_count"] == 1
    assert covered["classification_counts"] == {"implementation_ready": 1}


def test_frozen_universe_ready_action_runtime_rules_self_test_and_aggregate():
    from src.research_infra.moonshot_frozen_universe_ready_action_runtime import (
        aggregate_rules,
        ready_action_runtime_rule,
        rule_matches_payload,
        self_test_row,
    )

    row = {
        "implementation_ready_bundle_row_id": "ready-1",
        "scorer_filter_router_selector_role": "avoid_filter_failure_intelligence_input",
        "keep_kill_redesign_implement_decision": (
            "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_AVOID_READY_ACTION"
        ),
        "symbol_family": "NAS100_NQ_FAMILY",
        "symbol": "NAS100_NQ",
        "source_symbol": "NAS100",
        "market_timeframe": "M1",
        "route_session": "ny_core",
        "horizon_id": "h16",
        "side": "SHORT",
        "source_path": "data/NAS100_M1.csv",
        "source_path_sha256": "path-hash",
        "source_file_sha256": "file-hash",
        "gross_simulated_r": -0.12,
        "cost_adjusted_simulated_r": -0.14,
        "stress_simulated_r": -0.18,
        "effective_n": 42,
        "source_row_count": 3,
        "source_row_ids_sha256": "row-id-hash",
    }
    rule = ready_action_runtime_rule(row, 1)
    self_test = self_test_row(rule, 1)
    aggregates = aggregate_rules([rule])

    assert rule["action_class"] == "avoid_filter"
    assert rule["missing_match_fields"] == []
    assert rule_matches_payload(rule, rule["match_scope"]) is True
    assert rule_matches_payload(rule, {**rule["match_scope"], "side": "LONG"}) is False
    assert self_test["self_test_status"] == "FROZEN_READY_ACTION_RUNTIME_SELF_TEST_PASS"
    assert aggregates[0]["rule_count"] == 1
    assert aggregates[0]["source_row_count"] == 3


def test_frozen_universe_main_handoff_consumption_order_and_checks():
    from src.research_infra.moonshot_frozen_universe_main_handoff import (
        consumption_order_rows,
        count_check_row,
    )

    cp280_handoff = [
        {"handoff_class": "priority_2_rule_performance", "artifact_paths": ["rule.jsonl"]},
        {"handoff_class": "priority_3_action_application", "artifact_paths": ["action.jsonl"]},
        {"handoff_class": "priority_4_repair_tasks", "artifact_paths": ["repair.jsonl"]},
        {"handoff_class": "priority_5_frozen_closure", "artifact_paths": ["closure.jsonl"]},
    ]
    rows = consumption_order_rows(cp280_handoff, ["runtime.jsonl"])
    check = count_check_row("follow_rule_inputs", 173, 173, "result.json", 1)
    failed = count_check_row("avoid_filter_inputs", 287, 288, "result.json", 2)

    assert [row["handoff_class"] for row in rows] == [
        "ready_runtime_rules_first",
        "rule_performance_evidence_second",
        "action_execution_proof_third",
        "repair_needed_bundle_fourth",
        "full_frozen_closure_fifth",
    ]
    assert rows[0]["artifact_paths"] == ["runtime.jsonl"]
    assert check["check_pass"] is True
    assert failed["check_pass"] is False
