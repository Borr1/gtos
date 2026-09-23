from src.judgment.host_sites import HOST_SITES, github_live_sites, vps_land_plan


def test_github_symbols_resolve_and_host_lines_stay_mapped():
    live = github_live_sites()
    assert live["UB-AUTH-010"]["github_line"] is not None
    assert live["UB-PLC-017"]["github_line"] is not None
    assert live["F5-JEV-004"]["github_line"] == live["UB-PLC-017"]["github_line"]
    assert live["SEL-V4-002"]["github_line"] is not None
    assert live["SEL-V4-002"]["bound"] is True
    assert live["APLU-OBS-001"]["bound"] is False
    assert live["APLU-OBS-001"]["shadow_only"] is True
    assert live["APLU-OBS-001"]["wired"] is False
    assert live["APLU-OBS-001"]["github_line"] is not None
    assert HOST_SITES["UB-AUTH-010"]["host_line"] == 572
    assert HOST_SITES["UB-PLC-017"]["host_line"] == 9531
    assert HOST_SITES["SEL-V4-002"]["host_line"] == 3598
    plan = vps_land_plan()
    assert plan["do_not_wholesale_copy_book_owner"] is True
    assert plan["host_book_owner_lines"] == 10069
    assert plan["github_book_owner_lines"] != 10069
    assert plan["host_aplus_obs_notes"] == "judgment/astra/lab/wires/HOST_APLU_OBS_LAND.md"
    assert any("APLU-OBS-001" in step for step in plan["land_order"])


def test_github_a1_hooks_exist_on_unbound_sites_only():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    bridge = (root / "src/components/ultimate_book/bridge.py").read_text(encoding="utf-8")
    owner = (root / "src/components/ultimate_book/book_owner.py").read_text(encoding="utf-8")
    selector = (root / "src/components/selector_v4.py").read_text(encoding="utf-8")
    assert "maybe_observe_ub_auth_010" in bridge
    assert "maybe_observe_ub_plc_017" in owner
    assert "maybe_observe_fluid_at_place" in owner
    assert "GTOS_JEV_ALIVE_SHADOW" in owner
    assert "GTOS_JEV_ALIVE_SHADOW" in bridge
    assert "cost_skip = self._spread_cost_screen" in owner
    assert owner.index("maybe_observe_ub_plc_017") > owner.index("cost_skip = self._spread_cost_screen")
    assert "observe_before_continue" in owner
    assert "book_owner_observe_splice" in owner
    assert "GTOS_JEV_A1_OBSERVE_EVERY" in owner
    assert "DIG_MULTI_STAGE_GUARD" not in owner
    assert "from src.judgment.s16" not in owner
    assert "haircut_challenge_unit" in owner
    assert "host_occupancy_governor" in owner
    assert owner.index("host_occupancy_governor") > owner.index("cost_skip = self._spread_cost_screen")
    assert owner.index("haircut_challenge_unit") > owner.index("if cost_skip is not None")
    assert "risk_pct_per_trade" in owner
    execution = (root / "src/components/execution.py").read_text(encoding="utf-8")
    assert "apply_f5_scaler_to_risk_amount" in execution
    assert execution.index("apply_f5_scaler_to_risk_amount") > execution.index(
        "risk_amount = account_balance * (risk_pct / 100)"
    )
    apply_size = (root / "src/judgment/apply_size.py").read_text(encoding="utf-8")
    assert "honor_f5_scaler_risk" in apply_size
    assert "def honor_f5_scaler_risk" in apply_size
    assert "maybe_observe" not in selector
    assert "from src.judgment" not in selector
