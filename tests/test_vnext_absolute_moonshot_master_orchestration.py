from scripts import build_vnext_absolute_moonshot_master_orchestration as master


def test_absolute_master_registry_covers_all_18_lanes():
    payload = master.build_outputs(write=False, require_focused_test_result=False)
    registry = payload["registry"]
    lanes = registry["lanes"]

    assert registry["lane_count"] == 18
    assert registry["git"]["head_short"] != "00bb1ac5f"
    assert [lane["lane_id"] for lane in lanes] == [f"{idx:02d}" for idx in range(1, 19)]
    assert all(lane["prompt_path"] for lane in lanes)
    assert all(lane["starter_path"] for lane in lanes)
    assert all(
        lane["route_path"].startswith(
            (
                f"research/operations/vnext_moonshot_lane{lane['lane_id']}_",
                f"research/operations/vnext_absolute_moonshot_lane{lane['lane_id']}_",
            )
        )
        for lane in lanes
    )
    assert all(lane["master_integration_status"] == "terminal_verified_wave1" for lane in lanes[:4])
    assert all(lane["master_integration_status"] == "terminal_verified_wave2" for lane in lanes[4:7])
    assert all(lane["master_integration_status"] == "terminal_verified_wave3" for lane in lanes[7:11])
    assert all(
        payload["registry"]["lanes"][idx]["master_integration_status"] == "terminal_verified_wave4"
        for idx in [15, 16, 17]
    )


def test_absolute_master_dependency_graph_preserves_waves_and_no_future_deps():
    payload = master.build_outputs(write=False, require_focused_test_result=False)
    lanes = {lane["lane_id"]: lane for lane in payload["registry"]["lanes"]}
    graph_nodes = {node["node_id"] for node in payload["graph"]["nodes"]}

    assert "MASTER" in graph_nodes
    assert set(lanes) <= graph_nodes
    for lane in lanes.values():
        for dependency in lane["dependencies"]:
            assert lanes[dependency]["wave"] <= lane["wave"]
    assert lanes["05"]["dependencies"] == ["01", "02", "03", "04"]
    assert lanes["16"]["dependencies"][-3:] == ["09", "10", "11"]
    assert {"16", "17", "18"} <= set(lanes["12"]["dependencies"])
    assert "14" in lanes["15"]["dependencies"]
    assert {"source_capture_repair", "selector_v3", "scheduler_v3", "execution_policy_v3"} <= graph_nodes
    graph_edges = {(edge["from"], edge["to"], edge["edge_type"]) for edge in payload["graph"]["edges"]}
    for gate_id in {"source_capture_repair", "selector_v3", "scheduler_v3", "execution_policy_v3"}:
        assert (gate_id, "12", "post_v3_terminal_input_dependency") in graph_edges
        assert (gate_id, "15", "post_v3_terminal_input_dependency") in graph_edges


def test_absolute_master_wave1_wave2_wave3_terminal_counts_and_post_lane11_state():
    payload = master.build_outputs(write=False, require_focused_test_result=False)
    table = payload["terminal_table"]
    wave2_table = payload["wave2_terminal_table"]
    wave3_table = payload["wave3_terminal_table"]
    post = payload["post_lane11_table"]
    wave4_table = payload["wave4_terminal_table"]
    post_v3_table = payload["post_v3_table"]
    readiness = payload["wave2_readiness"]
    wave3 = payload["wave3_readiness"]
    launch = payload["wave3_launch"]
    post_lane18 = payload["post_lane18_decision"]
    post_v3_launch = payload["post_v3_decision"]
    stale = payload["stale_neutralization"]

    assert table["all_wave1_terminal_verified"] is True
    counts = {row["lane_id"]: row["material_row_counts"] for row in table["wave1_lanes"]}
    assert counts["01"]["source_inventory_rows"] == 12545
    assert counts["01"]["source_gap_rows"] == 975
    assert counts["01"]["downstream_source_contracts"] == 11
    assert counts["02"]["timestamp_inventory_rows"] == 1236093
    assert counts["02"]["asof_contract_rows"] == 7284
    assert counts["03"]["canonical_event_rows"] == 10389561
    assert counts["03"]["canonical_candidate_rows"] == 3761515
    assert counts["03"]["duplicate_groups"] == 724408
    assert counts["03"]["source_inventory_rows"] == 1129
    assert counts["03"]["source_gap_rows"] == 24
    assert counts["03"]["exact_r_rows"] == 36
    assert counts["03"]["proxy_r_rows"] == 2089623
    assert counts["04"]["timeline_rows"] == 289928
    assert counts["04"]["strict_tick_rows"] == 1790
    assert counts["04"]["source_gap_rows"] == 289604
    assert counts["04"]["anatomy_split_rows"] == 1402

    assert wave2_table["all_wave2_terminal_verified"] is True
    wave2_counts = {row["lane_id"]: row["material_row_counts"] for row in wave2_table["wave2_lanes"]}
    assert wave2_counts["05"]["canonical_candidate_feature_rows"] == 3761515
    assert wave2_counts["05"]["timeline_feature_rows"] == 289928
    assert wave2_counts["06"]["label_vector_rows"] == 289928
    assert wave2_counts["06"]["missing_label_gap_rows"] == 3471773
    assert wave2_counts["06"]["broker_real_label_rows"] == 8
    assert wave2_counts["06"]["lane05_consumed"] is True
    assert wave2_counts["06"]["lane07_consumed"] is True
    assert wave2_counts["07"]["symbol_rows"] == 24
    assert wave2_counts["07"]["broker_truth_rows"] == 64
    assert wave2_counts["07"]["cost_rows"] == 53
    assert wave2_counts["07"]["source_gap_rows"] == 221
    assert wave2_counts["07"]["source_coverage_rows"] == 38
    assert readiness["lane_readiness"]["07"]["blocks_lane05_or_lane06"] is False
    assert readiness["lane_readiness"]["07"]["blocks_wave3_when_broker_real_fields_absent"] is False

    assert wave3_table["all_wave3_terminal_verified"] is True
    wave3_counts = {row["lane_id"]: row["material_row_counts"] for row in wave3_table["wave3_lanes"]}
    assert wave3_counts["08"]["replay_rows"] == 289928
    assert wave3_counts["09"]["selector_row_evidence_rows"] == 289928
    assert wave3_counts["10"]["conflict_rows"] == 215495
    assert wave3_counts["11"]["expanded_policy_result_cell_accounting"] == 1026261670

    assert post["all_post_lane11_terminal_verified"] is True
    post_counts = {row["lane_id"]: row["material_row_counts"] for row in post["terminal_lanes"]}
    assert post_counts["09B"]["selector_scheduler_join_rows"] == 289928
    assert post_counts["09B"]["lane11_policy_dependent_rows"] == 110386
    assert post_counts["10B"]["full_anatomy_rows"] == 289928
    assert post_counts["10B"]["repairable_rows"] == 42479
    assert post_counts["11"]["expanded_policy_variant_count"] == 890

    assert wave3["wave3_terminal_verified"] is True
    assert wave3["post_lane11_terminal_verified"] is True
    assert wave3["next_wave_ready_to_open"] is True
    assert wave3["lane_readiness"]["16"]["readiness"] == "ready_next_wave_full_trading_operating_system"
    assert wave3["lane_readiness"]["17"]["launch_phase"] == "wave4_post_lane11_next_wave"
    assert wave3["lane_readiness"]["18"]["required_inputs"][0] == "Lane07"
    assert wave3["lane_readiness"]["12"]["readiness"] == "ready_after_post_v3_master_refresh_ml_subsystem"
    assert wave3["lane_readiness"]["14"]["readiness"] == "ready_post_v3_repair_companion_default_off_design_with_ml_fields_gated"
    assert launch["launch_order"][0]["lanes"] == ["16", "17", "18"]
    assert stale["neutralized_for_master_consumption"] is True
    assert stale["post_v3_neutralized_by_terminal_consumption"] is True

    assert wave4_table["all_wave4_terminal_verified"] is True
    wave4_counts = {row["lane_id"]: row["material_row_counts"] for row in wave4_table["wave4_lanes"]}
    assert wave4_counts["16"]["event_rows"] == 289928
    assert wave4_counts["16"]["source_gap_rows"] == 3761701
    assert wave4_counts["16"]["non_reconstructable_gap_rows"] == 3471773
    assert wave4_counts["17"]["replay_whiteboard_rows"] == 289928
    assert wave4_counts["17"]["source_gap_rows"] == 2101044
    assert wave4_counts["17"]["correlation_pair_rows"] == 276
    assert wave4_counts["18"]["source_gap_rows"] == 1207
    assert wave4_counts["18"]["cost_rows"] == 53
    assert post_lane18["wave4_terminal_verified"] is True
    assert set(post_lane18["next_implementation_gates"]) >= {
        "selector_v3",
        "scheduler_v3",
        "execution_policy_v3",
        "source_capture_repair",
    }
    assert post_lane18["post_v3_terminal_consumed"] is True
    assert post_lane18["decision"] == "post_lane18_v3_and_source_capture_wave_consumed_by_terminal_post_v3_artifacts"

    assert post_v3_table["all_post_v3_terminal_verified"] is True
    post_v3_counts = {row["gate_id"]: row["material_row_counts"] for row in post_v3_table["terminal_routes"]}
    assert post_v3_counts["source_capture_repair"]["superledger_rows"] == 16579491
    assert post_v3_counts["source_capture_repair"]["repaired_rows"] == 2949305
    assert post_v3_counts["source_capture_repair"]["read_only_export_requirement_rows"] == 2823
    assert post_v3_counts["selector_v3"]["full_evidence_rows"] == 289928
    assert post_v3_counts["selector_v3"]["mechanism_action_rows"] == 6488
    assert post_v3_counts["selector_v3"]["exact_r_rows"] == 0
    assert post_v3_counts["selector_v3"]["proxy_r_rows"] == 289917
    assert post_v3_counts["scheduler_v3"]["decision_rows"] == 289928
    assert post_v3_counts["scheduler_v3"]["blocked_edge_rows"] == 179575
    assert post_v3_counts["scheduler_v3"]["source_bound_proxy_rows"] == 289909
    assert post_v3_counts["execution_policy_v3"]["policy_variant_rows"] == 1353
    assert post_v3_counts["execution_policy_v3"]["evaluation_rows"] == 107201
    assert post_v3_counts["execution_policy_v3"]["source_gap_rows"] == 7587
    assert post_v3_launch["post_v3_terminal_verified"] is True
    post_v3_launch_lanes = {lane for phase in post_v3_launch["next_launch_order"] for lane in phase["lanes"]}
    assert {"12", "13", "14", "15"} <= post_v3_launch_lanes


def test_absolute_master_output_contracts_next_wave_and_runtime_boundary_closed():
    payload = master.build_outputs(write=False, require_focused_test_result=False)
    label_fields = set(payload["schemas"]["schemas"]["label_row"])
    replay_fields = set(payload["schemas"]["schemas"]["replay_row"])
    schema_keys = set(payload["schemas"]["schemas"])
    boundary = payload["boundary"]

    assert {"exact_r", "proxy_r", "expectancy_r", "row_level_missing_field_proof"} <= label_fields
    assert {"gross_r", "net_r", "proxy_r", "cost_model_version"} <= replay_fields
    assert {
        "market_whiteboard_row",
        "broker_truth_cost_capture_row",
        "limitation_disposition_row",
        "next_wave_contract_row",
        "selector_v3_contract_row",
        "scheduler_v3_contract_row",
        "execution_policy_v3_contract_row",
        "source_capture_repair_row",
        "post_v3_terminal_route_row",
    } <= schema_keys
    assert payload["limitation_map"]["all_dispositions_allowed"] is True
    assert payload["next_wave"]["next_wave_lanes"] == ["16", "17", "18"]
    assert payload["next_wave"]["not_ml_only_closure"] is True
    assert "subsystem" in payload["next_wave"]["ml_role"]
    assert payload["later_gates"]["gate_count"] >= 8
    assert payload["later_gates"]["wave4_terminal_consumed"] is True
    assert payload["later_gates"]["post_v3_terminal_consumed"] is True
    assert "source_capture_repair" in payload["post_lane18_decision"]["next_implementation_gates"]
    assert payload["result_status"]["production_change_readiness_claim"] is False
    source_families = {row["source_family"] for row in payload["source_map"]["source_families"]}
    assert {
        "absolute_post_lane18_source_capture_repair",
        "absolute_selector_v3_default_off_package",
        "absolute_scheduler_v3_default_off_package",
        "absolute_execution_policy_v3_default_off_package",
    } <= source_families
    assert not any(boundary["attestation"].values())
    assert boundary["evidence_class"] == "master_orchestration_evidence_and_launch_control_only"


def test_absolute_master_verifier_catches_core_contract_without_requiring_junit_first():
    result = master.verify_outputs(write=False, require_focused_test_result=False)

    assert result["ok"], result["issues"]
    assert result["lane_count"] == 18
    assert result["prompt_validation_ok"] is True
