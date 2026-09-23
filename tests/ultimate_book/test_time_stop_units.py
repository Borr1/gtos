"""The time-stop unit, pinned — Session AQ (B1404).

`SLEEVE_EXIT_PROFILES[...]["time_stop_bars"]` is **M15 bars that PRINTED**, for every
sleeve, whatever grid the sleeve decides on. That is a property of the consumer
(`ExecutionEngine._trading_m15_bars_since` counts M15 stamps and
`check_time_stop_and_close` compares the count to this integer), and it is not visible
anywhere at the declaration site. The fourteen `mx_*` D1 sleeves were declared **96** —
which is the M15-bars-per-D1-bar conversion RATIO, not a horizon — so their live time stop
was one D1 bar against the 80-D1-bar horizon their published economics are measured under.

These tests exist so that cannot happen again, and so that the repair's blast radius is a
measurement rather than a claim:

* the unit is pinned BEHAVIOURALLY, by driving the engine that counts the bars — a test
  that only re-multiplied the same integers would pass against a wrong implementation
  (CLAUDE.md §6);
* every sleeve's emitted integer is pinned against the pre-repair snapshot, so the repair
  is proven to move exactly the fourteen and nothing else;
* the three sleeves trading real money are pinned by name, value and grid.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.components.ultimate_book import execution_packets as EP

# --------------------------------------------------------------------------------------
# The pre-repair snapshot. Read off `git show HEAD~:...execution_packets.py` at the commit
# that introduced the repair; every value here is what the file emitted BEFORE it, so a
# diff against the live dict is the repair's exact blast radius. Do not regenerate this
# table from the module — that would make it a tautology.
# --------------------------------------------------------------------------------------

# STALE-EXPECTATION REPAIR 2026-08-25: the DSP/XA discovery cohorts postdate the frozen
# snapshot, so `test_the_snapshot_still_covers_every_sleeve_in_the_registry` failed on
# membership alone. 25 `dsp_*` sleeves (discovered 2026-08-21 by the displacement
# precondition sweep) + 6 `xa_*` timing setups (2026-08-21), none armed, carried into
# this tree by the f5-live overlay (`338553883`, f5-live@68bad3751). Snapshot EXTENSION
# only, same treatment as the WIDEN tags below: each row is the value the sleeve was
# INTRODUCED with — 32 printed M15 bars on an M15 decision grid (`sleeves/registry.py`
# DISPLACEMENT_BUILT / XA blocks, all TF_M15; `execution_packets.py` "Cohort A: H=32"),
# 32 native bars, inside [1, 80]. The mx-repair blast radius stays exactly the fourteen.
# Hand-written, not derived from the module, per the rule above.
_DSP_XA_COHORT_2026_08_21: tuple[str, ...] = (
    "dsp_climax_flush_to_96low_then_snap", "dsp_london_two_up_into_20high_reverses",
    "dsp_expanding_up_staircase", "dsp_huge_down_hold_then_spring",
    "dsp_already_wide_down_bar_second_wave", "dsp_cascade_last_two_not_yet_four",
    "dsp_close_on_20low_not_a_cascade_then_up", "dsp_wide_down_then_micro_bounce_then_through",
    "dsp_isolated_spike_high", "dsp_bleed_accept_fresh_20low_second_push",
    "dsp_walked_high_accepted_through", "dsp_small_bar_sit_on_20high_rejects",
    "dsp_session_open_already_live", "dsp_climax_onto_20high_then_fade_london",
    "dsp_climax_onto_20high_then_fade_cashhole", "dsp_expanding_two_bar_run_tokyo",
    "dsp_high_vol_doji_after_reclaimed_flush_fx", "dsp_weekend_gap_then_bleed_into_20low",
    "dsp_overnight_box_failed_floor_probe", "dsp_london_bounce_fails_overnight_midpoint",
    "dsp_first_cash_bar_spike_and_flush", "dsp_two_open_bars_down_then_cascade",
    "dsp_isolated_flush_to_20low_snap", "dsp_climax_into_high_then_dump",
    "dsp_climax_2atr_onto_20high_then_fade",
    "xa_huge_20_extreme", "xa_isolated_opposite", "xa_prior_huge",
    "xa_climax_spring", "xa_wide_extreme", "xa_second_leg",
)

PRE_REPAIR_TIME_STOP_BARS: dict[str, int] = {
    "crypto": 1280, "idxrev": 960, "fx_jpy": 48, "fx_jpy_ny": 48,
    "sub_xvol_pullback": 1280, "sub_mid_dn_revert": 1280, "vp_euidx_pocgrav": 960,
    "metals_core": 1280, "metals_softband": 1280, "metals_ob_micro": 1280,
    "energy_agri": 1280, "vol_compression": 7680, "asian_fade": 48,
    "ny_crypto_momentum": 20, "metal_session_reversion": 24, "asia_pdl_fade": 32,
    "orb_crypto_london": 80, "liq_asia_up_low_metal": 16, "kz_london_crypto_low": 32,
    "vss_fxcross_london_up_low": 48,
    # F5 ceremony 20260825 WIDEN tags (snapshot extension; blast-radius rows untouched)
    "asian_fade_widen": 48, "ny_crypto_momentum_widen": 20, "orb_crypto_london_widen": 80,
    # DSP/XA cohorts 2026-08-21 (snapshot extension; see _DSP_XA_COHORT_2026_08_21 above)
    **{s: 32 for s in _DSP_XA_COHORT_2026_08_21},
    # the fourteen market-expansion D1 sleeves, all at the defect value
    **{s: 96 for s in (
        "mx_aus200_cash_d1_volume_surge_reversal",
        "mx_avausd_d1_donchian_20_breakout",
        "mx_btcusd_d1_donchian_20_breakout",
        "mx_cadjpy_d1_volume_surge_reversal",
        "mx_ethusd_d1_donchian_20_breakout",
        "mx_eu50_cash_d1_volume_surge_reversal",
        "mx_fra40_cash_d1_volume_surge_reversal",
        "mx_ger40_cash_d1_volume_surge_reversal",
        "mx_jp225_cash_d1_volume_surge_reversal",
        "mx_nzdjpy_d1_donchian_20_breakout",
        "mx_spn35_cash_d1_volume_surge_reversal",
        "mx_us100_cash_d1_atr_mean_reversion",
        "mx_us30_cash_d1_volume_surge_reversal",
        "mx_us500_cash_d1_atr_mean_reversion")},
}

#: Which decision grid each sleeve's `time_stop_bars` is a horizon ON. Source: the sleeve
#: registry's `SleeveSpec` timeframe (`sleeves/registry.py`), as walked by Session AA and
#: republished in `AD_TIMESTOP_UNITS_V1.json -> sleeve_contracts.*.timeframe`.
GRID_OF: dict[str, str] = {
    "crypto": "H4", "idxrev": "H4", "sub_xvol_pullback": "H4", "sub_mid_dn_revert": "H4",
    "vp_euidx_pocgrav": "H4", "metals_core": "H4", "metals_softband": "H4",
    "metals_ob_micro": "H4", "energy_agri": "H4",
    "vol_compression": "D1",
    "fx_jpy": "M15", "fx_jpy_ny": "M15", "asian_fade": "M15", "ny_crypto_momentum": "M15",
    "metal_session_reversion": "M15", "asia_pdl_fade": "M15", "orb_crypto_london": "M15",
    "asian_fade_widen": "M15", "ny_crypto_momentum_widen": "M15", "orb_crypto_london_widen": "M15",
    "liq_asia_up_low_metal": "M15", "kz_london_crypto_low": "M15",
    "vss_fxcross_london_up_low": "M15",
    # DSP/XA cohorts 2026-08-21: SleeveSpec timeframe TF_M15 for all 31
    # (`sleeves/registry.py` DISPLACEMENT_BUILT / XA blocks).
    **{s: "M15" for s in _DSP_XA_COHORT_2026_08_21},
    **{s: "D1" for s in EP.MARKET_EXPANSION_TARGET2_SLEEVES},
}

#: Both accounts trade these, today, with real money. CLAUDE.md §4.
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback")


# ======================================================================================
# the helper
# ======================================================================================

def test_time_stop_m15_converts_from_the_native_grid():
    assert EP.time_stop_m15(80, "D1") == 7680
    assert EP.time_stop_m15(80, "H4") == 1280
    assert EP.time_stop_m15(32, "M15") == 32
    assert EP.M15_BARS_PER == {"M15": 1, "H4": 16, "D1": 96}


def test_time_stop_m15_refuses_an_unknown_grid_rather_than_under_scaling():
    """An unrecognised grid must RAISE. Defaulting to 1 would silently reproduce the
    defect this helper exists to prevent — a D1 horizon charged in M15 units."""
    with pytest.raises(ValueError, match="unknown decision grid"):
        EP.time_stop_m15(80, "H1")
    with pytest.raises(ValueError):
        EP.time_stop_m15(0, "D1")


# ======================================================================================
# the registry
# ======================================================================================

@pytest.mark.parametrize("sleeve", sorted(GRID_OF))
def test_every_declared_time_stop_is_a_whole_number_of_its_own_bars(sleeve: str):
    """The value must be `n * M15_BARS_PER[grid]` for an integer n, and n must be a
    horizon a human would write — at most the 80-bar research horizon, at least 1."""
    bars = EP.SLEEVE_EXIT_PROFILES[sleeve]["time_stop_bars"]
    per = EP.M15_BARS_PER[GRID_OF[sleeve]]
    assert bars % per == 0, (
        f"{sleeve}: {bars} M15 bars is not a whole number of {GRID_OF[sleeve]} bars"
    )
    native = bars // per
    assert 1 <= native <= EP.RESEARCH_HORIZON_NATIVE_BARS, (
        f"{sleeve}: resolves to {native} {GRID_OF[sleeve]} bars, outside [1, "
        f"{EP.RESEARCH_HORIZON_NATIVE_BARS}]"
    )


def test_the_market_expansion_cohort_carries_the_research_horizon_not_the_ratio():
    """The defect, named. 96 == M15_BARS_PER['D1'] — the ratio, not a horizon."""
    assert EP.M15_BARS_PER["D1"] == 96, "the coincidence this test is about"
    for sleeve in EP.MARKET_EXPANSION_TARGET2_SLEEVES:
        bars = EP.SLEEVE_EXIT_PROFILES[sleeve]["time_stop_bars"]
        assert bars != 96, f"{sleeve} is back on the conversion ratio"
        assert bars == 7680, f"{sleeve} should be 80 D1 bars = 7680 M15 bars, got {bars}"


def test_the_two_d1_sleeves_agree_with_each_other():
    """`vol_compression` had the D1 horizon right all along and the `mx_*` cohort did not.
    They are the same horizon on the same grid, so they must be the same integer."""
    assert (EP.SLEEVE_EXIT_PROFILES["vol_compression"]["time_stop_bars"]
            == EP.SLEEVE_EXIT_PROFILES["mx_btcusd_d1_donchian_20_breakout"]["time_stop_bars"])


def test_the_repair_moves_exactly_the_fourteen_and_nothing_else():
    """The blast radius, as a measurement against the pre-repair snapshot."""
    moved = {s: (PRE_REPAIR_TIME_STOP_BARS[s],
                 EP.SLEEVE_EXIT_PROFILES[s]["time_stop_bars"])
             for s in PRE_REPAIR_TIME_STOP_BARS
             if EP.SLEEVE_EXIT_PROFILES[s]["time_stop_bars"] != PRE_REPAIR_TIME_STOP_BARS[s]}
    assert set(moved) == set(EP.MARKET_EXPANSION_TARGET2_SLEEVES), (
        f"the repair moved {sorted(set(moved) ^ set(EP.MARKET_EXPANSION_TARGET2_SLEEVES))} "
        f"outside the market-expansion cohort"
    )
    assert set(moved.values()) == {(96, 7680)}


def test_the_snapshot_still_covers_every_sleeve_in_the_registry():
    """If a sleeve is added without a snapshot row, the blast-radius test above would
    silently stop covering it."""
    assert set(EP.SLEEVE_EXIT_PROFILES) == set(PRE_REPAIR_TIME_STOP_BARS)
    assert set(EP.SLEEVE_EXIT_PROFILES) == set(GRID_OF)


@pytest.mark.parametrize("sleeve", ARMED)
def test_the_armed_sleeves_are_h4_and_untouched(sleeve: str):
    """Both accounts trade these with real money. This repair must not move them, and the
    reason it does not is structural: they are H4 and 1280 == 80 * 16 was already right."""
    assert GRID_OF[sleeve] == "H4"
    assert EP.SLEEVE_EXIT_PROFILES[sleeve]["time_stop_bars"] == 1280
    assert EP.SLEEVE_EXIT_PROFILES[sleeve]["time_stop_bars"] == PRE_REPAIR_TIME_STOP_BARS[sleeve]
    assert EP.SLEEVE_EXIT_PROFILES[sleeve]["time_stop_bars"] == EP.time_stop_m15(80, "H4")
    assert sleeve not in EP.MARKET_EXPANSION_TARGET2_SLEEVES


# ======================================================================================
# the unit, pinned behaviourally against the engine that counts the bars
# ======================================================================================

@pytest.fixture
def engine(tmp_path, monkeypatch):
    """A real `ExecutionEngine` on the mock broker. Same construction as
    `tests/test_execution.py`'s fixture; the checkpoint path is redirected so a test can
    never write production state."""
    from src.components import execution as _exec_mod
    from src.components.execution import ExecutionEngine
    from src.mt5.mt5_mock import MockMT5

    monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH",
                        str(tmp_path / "execution_checkpoint.json"))
    m = MockMT5(balance=100000.0)
    m.connect()
    return ExecutionEngine(m, {"risk": {"risk_per_trade_pct": 1.0}})


def _m15_feed(entry: datetime, n_after: int) -> list[dict]:
    """`n_after` M15 bars that CLOSED after `entry`, plus one forming bar the counter
    drops and four before-entry bars it must not count."""
    bars = [{"time": (entry - timedelta(minutes=15 * (4 - k))).isoformat()}
            for k in range(4)]
    bars += [{"time": (entry + timedelta(minutes=15 * k)).isoformat()}
             for k in range(1, n_after + 2)]          # +1 forming
    return bars


def _arm(engine, budget: int, entry: datetime) -> None:
    """Put the engine into the state `check_time_stop_and_close` acts on."""
    from src.components.execution import TradeState

    engine.active_trade = TradeState(
        ticket=1, direction="LONG", entry_price=100.0, stop_loss=99.0,
        take_profit_1=102.0, take_profit_2=103.0, take_profit_3=104.0,
        initial_volume=0.1, current_volume=0.1, sl_distance=1.0,
        entry_time=entry.isoformat(),
    )
    engine.active_trade.gtos_vnext_dynamic_policy_applied = True
    engine.active_trade.gtos_vnext_dynamic_policy_selected = "time_stop"
    engine.active_trade.gtos_vnext_dynamic_time_stop_bars = budget


def test_the_budget_is_counted_in_printed_M15_bars_not_in_the_sleeves_own_bars(
    engine, monkeypatch
):
    """THE UNIT, measured rather than asserted.

    Drive the real `check_time_stop_and_close` with the real `mx_btcusd` budget. If the
    engine read the number as D1 bars, 7680 D1 bars of feed would be needed to fire it and
    96 M15 bars would fire nothing under either reading — so the discriminating pair is
    7679 vs 7680 PRINTED M15 bars. Firing at exactly 7680 is what makes `time_stop_m15`'s
    conversion the right one.
    """
    closed: list[str] = []
    monkeypatch.setattr(engine, "close_position",
                        lambda reason: (closed.append(reason), True)[1])
    budget = EP.SLEEVE_EXIT_PROFILES["mx_btcusd_d1_donchian_20_breakout"]["time_stop_bars"]
    assert budget == 7680
    entry = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)

    # 96 printed M15 bars — one D1 bar, the OLD live contract. Must NOT fire.
    _arm(engine, budget, entry)
    engine.mt5.get_candles = lambda sym, tf, n: _m15_feed(entry, 96)
    assert engine.check_time_stop_and_close() is None
    assert closed == []

    # one bar short of the budget. Must NOT fire.
    _arm(engine, budget, entry)
    engine.mt5.get_candles = lambda sym, tf, n: _m15_feed(entry, budget - 1)
    assert engine.check_time_stop_and_close() is None
    assert closed == []

    # exactly the budget. Must fire.
    _arm(engine, budget, entry)
    engine.mt5.get_candles = lambda sym, tf, n: _m15_feed(entry, budget)
    assert engine.check_time_stop_and_close() == "vnext_time_stop"
    assert closed == ["vnext_time_stop"]


def test_the_old_value_would_have_fired_after_one_day_of_printed_bars(engine, monkeypatch):
    """The defect, reproduced against the same engine — this is the measurement behind
    'the live book truncated 72-90 % of the cohort's trades at ~24 h'. 96 printed M15 bars
    on a 24/7 symbol is exactly one D1 bar."""
    closed: list[str] = []
    monkeypatch.setattr(engine, "close_position",
                        lambda reason: (closed.append(reason), True)[1])
    entry = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
    _arm(engine, 96, entry)                       # the pre-repair value
    engine.mt5.get_candles = lambda sym, tf, n: _m15_feed(entry, 96)
    assert engine.check_time_stop_and_close() == "vnext_time_stop"
    assert closed == ["vnext_time_stop"]
