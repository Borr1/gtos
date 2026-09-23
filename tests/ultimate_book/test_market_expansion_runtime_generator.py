from dataclasses import dataclass

import yaml

from src.components.ultimate_book.admission import (
    GovernorLimits,
    GovernorState,
    MARKET_EXPANSION_PROFILE,
    SizedUnit,
    TradeIntent,
    admit_and_size,
    effective_registry,
)
from src.components.ultimate_book.book_owner import _bridge_telemetry
from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
from src.components.ultimate_book.bridge import DEFAULT_CONFIG, evaluate_vnext_ultimate_book_admission
from src.components.ultimate_book.launcher import BookLauncher
from src.components.ultimate_book.sleeves import candidate_registry, market_expansion_d1
from src.components.ultimate_book.sleeves.registry import (
    CANDIDATE_BUILT,
    MARKET_EXPANSION_BUILT,
    active_specs,
)
from src.components.ultimate_book import execution_packets as EP


EXPANSION = set(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_COLLISION_WINNER_NAMES)


@dataclass(frozen=True)
class Bar:
    o: float
    h: float
    l: float
    c: float
    v: float = 100.0


def _state():
    return GovernorState(
        equity=100000.0,
        high_water=100000.0,
        realized_today_pct=0.0,
        open_risk_pct=0.0,
        max_dd_reference_equity=100000.0,
    )


def _base_bars(n=25):
    return [Bar(100.0, 101.0, 99.0, 100.0, 100.0 + i) for i in range(n)]


def test_market_expansion_runtime_catalog_is_isolated_from_candidate_book():
    assert len(EXPANSION) == 14
    assert set(MARKET_EXPANSION_BUILT) == EXPANSION
    assert not (EXPANSION & set(CANDIDATE_BUILT))

    default_names = {spec.tag for spec in active_specs(None)}
    candidate_names = {spec.tag for spec in active_specs(None, include_candidate_book=True)}
    empty_expansion = {
        spec.tag
        for spec in active_specs(
            None,
            include_market_expansion_book=True,
            market_expansion_sleeves=[],
        )
    }
    one = "mx_btcusd_d1_donchian_20_breakout"
    one_expansion = {
        spec.tag
        for spec in active_specs(
            None,
            include_market_expansion_book=True,
            market_expansion_sleeves=[one],
        )
    }

    assert not (EXPANSION & default_names)
    assert not (EXPANSION & candidate_names)
    assert not (EXPANSION & empty_expansion)
    assert one_expansion == default_names | {one}


def test_effective_registry_and_admission_require_explicit_market_expansion_flag_and_allowlist():
    tag = "mx_us500_cash_d1_atr_mean_reversion"
    intent = TradeIntent(
        sleeve=tag,
        symbol="US500_cash",
        direction=-1,
        decision_day="2026-06-18",
        stop_dist=50.0,
        target_dist=100.0,
    )

    off = effective_registry(include_candidate_book=True)
    assert tag not in off
    on = effective_registry(include_market_expansion_book=True, market_expansion_sleeves=[tag])
    assert on[tag].confidence == 0.025
    assert on[tag].asset_class == "indices_context"

    fail_closed = admit_and_size([intent], _state(), profile="balanced_0p75")
    assert fail_closed["units"][0]["sized"] is False
    assert fail_closed["units"][0]["reason"] == f"fail_closed:unknown_sleeve:{tag}"

    sized = admit_and_size(
        [intent],
        _state(),
        profile="balanced_0p75",
        include_market_expansion_book=True,
        market_expansion_sleeves=[tag],
    )
    unit = sized["units"][0]
    assert sized["market_expansion_sleeves"] == [tag]
    assert unit["sized"] is True
    assert unit["cluster"] == "indices_context"
    assert unit["confidence"] == 0.025
    assert unit["risk_pct_per_trade"] == 0.0001875


def test_bridge_defaults_off_and_fail_closes_market_expansion_misconfiguration():
    tag = "mx_btcusd_d1_donchian_20_breakout"
    intent = TradeIntent(
        sleeve=tag,
        symbol="BTCUSD",
        direction=1,
        decision_day="2026-06-18",
        stop_dist=100.0,
        target_dist=200.0,
    )
    cfg = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))["gtos_vnext_runtime"]
    assert DEFAULT_CONFIG["ultimate_book_include_market_expansion_book"] is False
    assert DEFAULT_CONFIG["ultimate_book_market_expansion_profile"] == MARKET_EXPANSION_PROFILE
    assert DEFAULT_CONFIG["ultimate_book_market_expansion_policy"] == "explicit_allowlist"
    assert DEFAULT_CONFIG["ultimate_book_market_expansion_sleeves"] == []
    assert cfg.get("ultimate_book_include_market_expansion_book") is True
    assert cfg.get("ultimate_book_market_expansion_policy") == "positive_weighted12_after_swap"
    assert cfg.get("ultimate_book_market_expansion_sleeves") == []

    empty_allowlist = {
        "gtos_vnext_runtime": {
            "ultimate_book_profile": "balanced_0p75",
            "ultimate_book_include_market_expansion_book": True,
        }
    }
    dec = evaluate_vnext_ultimate_book_admission(
        config=empty_allowlist,
        intents=[intent],
        governor_state=_state(),
    )
    assert dec.decision_status == "fail_closed_market_expansion_requires_explicit_sleeves"
    assert dec.runtime_effect_now is False

    bad_profile = {
        "gtos_vnext_runtime": {
            "ultimate_book_profile": "balanced_0p75",
            "ultimate_book_include_market_expansion_book": True,
            "ultimate_book_market_expansion_profile": "unknown",
            "ultimate_book_market_expansion_sleeves": [tag],
        }
    }
    dec = evaluate_vnext_ultimate_book_admission(
        config=bad_profile,
        intents=[intent],
        governor_state=_state(),
    )
    assert dec.decision_status == "fail_closed_unknown_market_expansion_profile"

    bad_sleeve = {
        "gtos_vnext_runtime": {
            "ultimate_book_profile": "balanced_0p75",
            "ultimate_book_include_market_expansion_book": True,
            "ultimate_book_market_expansion_sleeves": ["not_real"],
        }
    }
    dec = evaluate_vnext_ultimate_book_admission(
        config=bad_sleeve,
        intents=[intent],
        governor_state=_state(),
    )
    assert dec.decision_status == "fail_closed_unknown_market_expansion_sleeves"

    valid_shadow = {
        "gtos_vnext_runtime": {
            "ultimate_book_profile": "balanced_0p75",
            "ultimate_book_include_market_expansion_book": True,
            "ultimate_book_market_expansion_sleeves": [tag],
        }
    }
    dec = evaluate_vnext_ultimate_book_admission(
        config=valid_shadow,
        intents=[intent],
        governor_state=_state(),
    )
    assert dec.decision_status == "shadow_book_disabled"
    assert dec.include_market_expansion_book is True
    assert dec.market_expansion_sleeves == (tag,)
    assert dec.would_units[0]["sized"] is True


def test_market_expansion_conditioned_policy_aliases_resolve_fail_closed():
    robust = candidate_registry.MARKET_EXPANSION_CONDITIONED_POLICIES["robust6_every_split_positive"]
    positive12 = candidate_registry.MARKET_EXPANSION_CONDITIONED_POLICIES["positive_weighted12_after_swap"]
    assert len(robust) == 6
    assert len(positive12) == 12
    assert set(robust) < set(positive12)

    tag = "mx_btcusd_d1_donchian_20_breakout"
    intent = TradeIntent(
        sleeve=tag,
        symbol="BTCUSD",
        direction=1,
        decision_day="2026-06-18",
        stop_dist=100.0,
        target_dist=200.0,
    )
    robust_policy = {
        "gtos_vnext_runtime": {
            "ultimate_book_profile": "balanced_0p75",
            "ultimate_book_include_market_expansion_book": True,
            "ultimate_book_market_expansion_policy": "robust6_every_split_positive",
        }
    }
    dec = evaluate_vnext_ultimate_book_admission(
        config=robust_policy,
        intents=[intent],
        governor_state=_state(),
    )
    assert dec.decision_status == "shadow_book_disabled"
    assert dec.market_expansion_policy == "robust6_every_split_positive"
    assert dec.market_expansion_sleeves == robust
    assert dec.would_units[0]["sized"] is True

    unknown_policy = {
        "gtos_vnext_runtime": {
            "ultimate_book_profile": "balanced_0p75",
            "ultimate_book_include_market_expansion_book": True,
            "ultimate_book_market_expansion_policy": "not_a_policy",
        }
    }
    dec = evaluate_vnext_ultimate_book_admission(
        config=unknown_policy,
        intents=[intent],
        governor_state=_state(),
    )
    assert dec.decision_status == "fail_closed_unknown_market_expansion_policy"
    assert dec.reason == "unknown_market_expansion_policy:not_a_policy"

    mismatched_policy = {
        "gtos_vnext_runtime": {
            "ultimate_book_profile": "balanced_0p75",
            "ultimate_book_include_market_expansion_book": True,
            "ultimate_book_market_expansion_policy": "robust6_every_split_positive",
            "ultimate_book_market_expansion_sleeves": ["mx_avausd_d1_donchian_20_breakout"],
        }
    }
    dec = evaluate_vnext_ultimate_book_admission(
        config=mismatched_policy,
        intents=[intent],
        governor_state=_state(),
    )
    assert dec.decision_status == "fail_closed_market_expansion_policy_sleeve_mismatch"
    assert dec.reason == "market_expansion_policy_sleeve_mismatch:robust6_every_split_positive"


def test_active_market_expansion_bridge_telemetry_exposes_reload_parity_flags():
    cfg = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
    runtime = cfg["gtos_vnext_runtime"]
    tag = "mx_btcusd_d1_donchian_20_breakout"
    intent = TradeIntent(
        sleeve=tag,
        symbol="BTCUSD",
        direction=1,
        decision_day="2026-06-18",
        stop_dist=100.0,
        target_dist=200.0,
    )
    dec = evaluate_vnext_ultimate_book_admission(
        config=cfg,
        intents=[intent],
        governor_state=_state(),
        limits=GovernorLimits(derisk_mode=runtime["ultimate_book_derisk_mode"]),
    )
    telemetry = _bridge_telemetry(dec)

    assert dec.runtime_effect_now is True
    assert telemetry["include_candidate_book"] is True
    assert telemetry["include_market_expansion_book"] is True
    assert telemetry["market_expansion_policy"] == "positive_weighted12_after_swap"
    assert tag in telemetry["market_expansion_sleeves"]
    assert telemetry["kelly_lite"] is True
    assert telemetry["kelly_conservative"] is True
    assert telemetry["kelly_running_count"] is True
    assert telemetry["stress_derisk"] is True
    assert telemetry["derisk_mode"] == "smooth"
    assert telemetry["drop_w7_symbols"] is True
    assert telemetry["metals_confluence_gate"] is True


def test_market_expansion_named_policy_feeds_generation_and_launcher_schedule(tmp_path):
    positive12 = candidate_registry.MARKET_EXPANSION_CONDITIONED_POLICIES["positive_weighted12_after_swap"]
    cfg = {
        "ultimate_book_include_market_expansion_book": True,
        "ultimate_book_market_expansion_policy": "positive_weighted12_after_swap",
        "ultimate_book_market_expansion_sleeves": [],
    }
    eng = UltimateBookLiveEngine(cfg, object(), str(tmp_path))
    active = eng._active_sleeve_names()
    assert set(positive12) <= active

    class _Owner:
        base_config = {"gtos_vnext_runtime": cfg}

    launcher = BookLauncher(
        _Owner(),
        object(),
        lambda s: s,
        repo_root=str(tmp_path),
        tags=None,
        poll_seconds=0.01,
    )
    assert 16408 in launcher._tf_tags
    assert set(positive12) <= set(launcher._tf_tags[16408])


def test_bridge_wires_sqrt_n_pooling_flag_into_sized_unit_reasons():
    tag = "mx_us500_cash_d1_atr_mean_reversion"
    intents = [
        TradeIntent(
            sleeve=tag,
            symbol="US500_cash",
            direction=-1,
            decision_day="2026-06-18",
            stop_dist=50.0,
            target_dist=100.0,
        ),
        TradeIntent(
            sleeve=tag,
            symbol="US500_cash",
            direction=-1,
            decision_day="2026-06-18",
            stop_dist=50.0,
            target_dist=100.0,
        ),
    ]
    dec = evaluate_vnext_ultimate_book_admission(
        config={
            "gtos_vnext_runtime": {
                "ultimate_book_profile": "balanced_0p75",
                "ultimate_book_include_market_expansion_book": True,
                "ultimate_book_market_expansion_policy": "positive_weighted12_after_swap",
                "ultimate_book_sqrt_n_pooling": True,
            }
        },
        intents=intents,
        governor_state=_state(),
    )
    assert dec.sqrt_n_pooling is True
    assert dec.would_units[0]["n_trades"] == 2
    assert "sqrtN_pool_n2" in dec.would_units[0]["overlays_applied"]


def test_market_expansion_d1_generator_uses_latest_closed_bar_for_next_open_donchian():
    bars = _base_bars()
    bars[-1] = Bar(100.0, 106.0, 104.0, 105.0, 130.0)
    tag = "mx_avausd_d1_donchian_20_breakout"
    intent = market_expansion_d1.generate_for_tag(
        tag,
        "AVAUSD",
        bars,
        "2026-06-17",
        bar_time="2026-06-17T00:00:00+00:00",
    )
    assert intent is not None
    assert intent.sleeve == tag
    assert intent.direction == 1
    assert intent.decision_day == "2026-06-18"
    assert intent.stop_dist > 0
    assert intent.target_dist == 2.0 * intent.stop_dist

    weekend_skip = market_expansion_d1.generate_for_tag(
        tag,
        "AVAUSD",
        bars,
        "2026-06-12",
        bar_time="2026-06-12T00:00:00+00:00",
        runtime_now="2026-06-15T00:01:00+00:00",
    )
    assert weekend_skip is not None
    assert weekend_skip.decision_day == "2026-06-15"


def test_market_expansion_d1_generator_atr_reversion_and_volume_surge_fade_prior_move():
    atr_bars = _base_bars()
    atr_bars[-2] = Bar(100.0, 101.0, 99.0, 100.0, 120.0)
    atr_bars[-1] = Bar(100.0, 111.0, 109.0, 110.0, 130.0)
    atr_intent = market_expansion_d1.generate_for_tag(
        "mx_us100_cash_d1_atr_mean_reversion",
        "US100_cash",
        atr_bars,
        "2026-06-17",
    )
    assert atr_intent is not None
    assert atr_intent.direction == -1
    assert atr_intent.decision_day == "2026-06-18"

    vol_bars = _base_bars()
    vol_bars[-2] = Bar(100.0, 101.0, 99.0, 100.0, 122.0)
    vol_bars[-1] = Bar(100.0, 103.0, 101.0, 102.0, 200.0)
    vol_intent = market_expansion_d1.generate_for_tag(
        "mx_us30_cash_d1_volume_surge_reversal",
        "US30_cash",
        vol_bars,
        "2026-06-17",
    )
    assert vol_intent is not None
    assert vol_intent.direction == -1
    assert vol_intent.target_dist == 2.0 * vol_intent.stop_dist


def test_market_expansion_exit_profiles_are_explicit_target2_and_packet_uses_intent_target():
    # `time_stop_bars` moved 96 -> 7680 on 2026-07-30 (Session AQ, B1404). It is in M15
    # PRINTED bars (execution.py:8953-8958), so 96 was the D1->M15 conversion RATIO written
    # into the field that wants the converted VALUE — a live time stop of ONE D1 bar against
    # the 80-D1-bar horizon every published economic number for these sleeves is measured
    # under. The unit is pinned behaviourally in tests/ultimate_book/test_time_stop_units.py.
    assert set(EP.MARKET_EXPANSION_TARGET2_SLEEVES) == EXPANSION
    for tag in EXPANSION:
        prof = EP.SLEEVE_EXIT_PROFILES[tag]
        assert prof == {
            "policy": "time_stop",
            "final_from_intent": True,
            "final_target_r": 2.0,
            "time_stop_bars": EP.time_stop_m15(EP.RESEARCH_HORIZON_NATIVE_BARS, "D1"),
        }
        assert prof["time_stop_bars"] == 7680

    tag = "mx_btcusd_d1_donchian_20_breakout"
    su = SizedUnit(
        cluster="crypto_alt_or_major",
        sleeve_members=(tag,),
        n_trades=1,
        confidence=0.025,
        risk_pct_per_trade=0.0001875,
        unit_risk_pct=0.0001875,
        sized=True,
        reason="sized",
    )
    intent = TradeIntent(
        sleeve=tag,
        symbol="BTCUSD",
        direction=1,
        decision_day="2026-06-18",
        stop_dist=100.0,
        target_dist=200.0,
    )
    account = {
        "current_equity": 100000.0,
        "balance": 100000.0,
        "account_login": 531325516,
        "day_start_equity_or_balance_baseline": 100000.0,
        "daily_reset_window_id": "2026-06-18",
    }
    params = EP.build_book_trade_params(
        su,
        intent,
        {"entry_price": 65000.0, "risk_distance": 100.0, "stop_loss": 64900.0},
        account,
        profile_namespace="operator_profile",
    )
    assert params["gtos_vnext_dynamic_policy_selected"] == "time_stop"
    assert params["gtos_vnext_dynamic_final_target_r"] == 2.0
    # 7680 M15 printed bars = the 80-D1-bar research horizon (B1404, see above).
    assert params["gtos_vnext_dynamic_time_stop_bars"] == 7680
    assert params["take_profit_1"] == 65200.0
