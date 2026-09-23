from src.research.universal_candidate_origin_registry import family_names, required_origin_families


def test_universal_registry_contains_current_and_non_boxed_families() -> None:
    names = set(family_names())
    assert {"ob_retest", "fvg_fill", "breaker_re_entry"} <= names
    assert "liquidity_sweep_reclaim" in names
    assert "orderflow_depth_imbalance_proxy" in names
    assert "cross_asset_lead_lag" in names
    assert "path_hazard_early_failure" in names
    assert len(names) == len(required_origin_families())


def test_universal_registry_is_default_off_research_contract() -> None:
    for family in required_origin_families():
        assert family.source_requirements
        assert family.asof_controls
        assert family.next_replay_action
        assert family.current_gtos_status != "active_runtime_change"
