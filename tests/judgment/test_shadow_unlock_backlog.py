"""Pin remaining SHADOW axes. No invented HIGH / trail / Friday / empty spine."""

from src.judgment.fluid_gates import lookup
from src.judgment.fluid_pipeline import may_auto_apply
from src.judgment.host_events import TRAIL_EPS, sl_differs
from src.judgment.shadow_unlock import (
    CHAIR_LANDED_EXTRA_FX,
    FX_LAND_FIRST,
    RESEARCH_ONLY,
    SHADOW_REMAIN,
    measure_shadow_unlock,
)


def test_inventory_remaining_shadow_and_research_only():
    receipt = measure_shadow_unlock()
    inv = receipt["inventory"]
    assert inv["n_fluid"] == 48
    assert inv["n_envelope"] == 8
    assert inv["by_status"] == {"APPLIED_NAMED": 44, "PROVED_SHADOW": 1, "SHADOW": 3}
    assert inv["shadow"] == list(SHADOW_REMAIN)
    assert inv["research_only"] == list(RESEARCH_ONLY)
    assert inv["proved_shadow"] == ["SEL-V4-002"]
    assert lookup("SEL-V4-002")["research_only"] is True
    assert lookup("SEL-V4-002")["status"] == "PROVED_SHADOW"
    assert may_auto_apply("SEL-V4-002") is False
    for gid in SHADOW_REMAIN:
        assert lookup(gid)["status"] == "SHADOW"
        assert may_auto_apply(gid) is False


def test_no_shadow_field_can_be_honestly_filled():
    receipt = measure_shadow_unlock()
    assert receipt["any_honest_fill"] is False
    assert receipt["filled_this_pass"] == []
    assert receipt["no_news_protocol_invented"] is True
    for gid in SHADOW_REMAIN:
        axis = receipt["shadow_axes"][gid]
        assert axis["can_honestly_fill_from_existing_challenge_state"] is False
        assert axis["invent_forbidden"] is True
        assert axis["prove_blocked"] is True
        assert axis["reasons"]


def test_trail_has_ten_false_and_no_named_move():
    receipt = measure_shadow_unlock()
    trail = receipt["shadow_axes"]["FLUID-HLD-005"]
    assert trail["pack"]["n_decidable"] == 10
    assert trail["pack"]["n_distinct"] == 1
    assert trail["pack"]["vals"] == {"false": 10}
    assert trail["event_column"]["n_stop_move_tickets"] == 10
    assert trail["event_column"]["n_trail_true_vs_deal_orig"] == 0
    assert trail["deal_column"]["n_differ_gt_eps"] == 0
    assert trail["deal_column"]["n_missing_final_sl"] == 46
    assert sl_differs(4336.90, 4336.905) is False
    assert TRAIL_EPS == 0.05


def test_friday_cutoff_absent_asia_friday_is_not_the_state():
    receipt = measure_shadow_unlock()
    friday = receipt["shadow_axes"]["FLUID-HLD-008"]
    assert friday["friday_cutoff_n"] == 0
    assert friday["pack"]["vals"] == {"false": 97}
    hours = {row["utc_hour"] for row in friday["friday_rows_on_pack"]}
    assert hours
    assert max(hours) < 16
    assert all(row["named"] == "asia" for row in friday["friday_rows_on_pack"])


def test_spine_empty_never_true_on_this_challenge_tape():
    receipt = measure_shadow_unlock()
    spine = receipt["shadow_axes"]["FLUID-NWS-005"]
    assert receipt["pack"]["n_news_empty"] == 0
    assert spine["n_deal_asofs_spine_empty"] == 0
    assert spine["pack"]["vals"] == {"false": 97}
    assert spine["host_news_never_read"] is True


def test_multi_instrument_chair_fx_tape_raises_non_xau_sufficient():
    receipt = measure_shadow_unlock()
    multi = receipt["multi_instrument"]
    pack = receipt["pack"]
    assert "XAUUSD" in multi["landed_symbols"]
    assert multi["tape_present"]["XAUUSD"] is True
    for sym in FX_LAND_FIRST + CHAIR_LANDED_EXTRA_FX:
        assert multi["tape_present"][sym] is True
    assert multi["tape_present"]["US30"] is True
    assert multi["tape_present"]["BTCUSD"] is False
    assert multi["tape_present"]["UK100"] is False
    assert multi["tape_present"]["ETHUSD"] is False
    assert pack["n_xau_sufficient"] == 28
    assert pack["n_non_xau_sufficient"] == 45
    assert pack["n_missing_m15_h4"] == 6
    assert pack["sufficient_by_symbol"]["US30.cash"] == 14
    assert pack["sufficient_by_symbol"]["EURUSD"] == 11
    assert pack["sufficient_by_symbol"]["USDJPY"] == 11
    assert pack["sufficient_by_symbol"]["GBPUSD"] == 7
    assert pack["sufficient_by_symbol"]["EURGBP"] == 2
    assert "GBPJPY" not in pack["symbols"]
    sel = receipt["research_only"]["SEL-V4-002"]["pack"]
    assert sel["n_decidable"] >= 28
    assert sel["n_distinct"] >= 2
    assert receipt["any_honest_fill"] is False
    assert receipt["filled_this_pass"] == []
