import yaml

from src.components.ultimate_book.admission import (
    CANDIDATE_BOOK_PROFILE,
    GovernorState,
    TradeIntent,
    admit_and_size,
    effective_registry,
)
from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
from src.components.ultimate_book.bridge import (
    DEFAULT_CONFIG,
    evaluate_vnext_ultimate_book_admission,
)
from src.components.ultimate_book.sleeves import candidate_registry
from src.components.ultimate_book.sleeves.registry import CANDIDATE_BUILT, active_specs
from src.components.ultimate_book import execution_packets as EP


EXECUTABLE = {
    "vol_compression",
    "asian_fade",
    "ny_crypto_momentum",
    "metal_session_reversion",
    "asia_pdl_fade",
    "orb_crypto_london",
    "liq_asia_up_low_metal",
    "kz_london_crypto_low",
    "vss_fxcross_london_up_low",
}

NO_BROKER_TP_NATIVE = {
    "asian_fade",
    "ny_crypto_momentum",
    "metal_session_reversion",
    "kz_london_crypto_low",
}

READY_SUBSET = {
    "kz_london_crypto_low",
    "metal_session_reversion",
    "ny_crypto_momentum",
    "orb_crypto_london",
}

FULL_CANDIDATE_ALLOWLIST = {
    "asia_pdl_fade",
    "asian_fade",
    "asian_fade_widen",
    "kz_london_crypto_low",
    "liq_asia_up_low_metal",
    "metal_session_reversion",
    "ny_crypto_momentum",
    "ny_crypto_momentum_widen",
    "orb_crypto_london",
    "orb_crypto_london_widen",
    "vol_compression",
    "vss_fxcross_london_up_low",
}


def _state():
    return GovernorState(
        equity=100000.0,
        high_water=100000.0,
        realized_today_pct=0.0,
        open_risk_pct=0.0,
        max_dd_reference_equity=100000.0,
    )


def test_candidate_runtime_catalog_is_exact_native_exit_set():
    assert set(candidate_registry.RUNTIME_EXECUTABLE_CANDIDATE_NAMES) == EXECUTABLE
    assert candidate_registry.CANDIDATE_RUNTIME_BLOCKERS == {}
    assert "vol_squeeze" not in candidate_registry.RUNTIME_EXECUTABLE_CANDIDATE_NAMES
    assert "ny_index_momentum" not in candidate_registry.RUNTIME_EXECUTABLE_CANDIDATE_NAMES
    assert "structural_retest" not in candidate_registry.RUNTIME_EXECUTABLE_CANDIDATE_NAMES


def test_effective_registry_admits_candidates_only_under_candidate_flag():
    off = effective_registry(include_clean3=False, include_clean4=False)
    on = effective_registry(include_clean3=False, include_clean4=False, include_candidate_book=True)
    subset = effective_registry(
        include_clean3=False,
        include_clean4=False,
        include_candidate_book=True,
        candidate_book_sleeves=sorted(READY_SUBSET),
    )

    assert not (EXECUTABLE & set(off))
    assert EXECUTABLE <= set(on)
    assert all(on[name].confidence == candidate_registry.CANDIDATE_CONFIDENCE[name] for name in EXECUTABLE)
    assert READY_SUBSET <= set(subset)
    assert not ((EXECUTABLE - READY_SUBSET) & set(subset))


def test_generation_specs_keep_candidates_default_off_and_have_warmups():
    default_names = {spec.tag for spec in active_specs(None)}
    candidate_names = {spec.tag for spec in active_specs(None, include_candidate_book=True)}
    subset_names = {
        spec.tag
        for spec in active_specs(
            None,
            include_candidate_book=True,
            candidate_book_sleeves=sorted(READY_SUBSET),
        )
    }

    assert not (EXECUTABLE & default_names)
    assert EXECUTABLE <= candidate_names
    assert READY_SUBSET <= subset_names
    assert not ((EXECUTABLE - READY_SUBSET) & subset_names)
    assert set(CANDIDATE_BUILT) == EXECUTABLE
    assert all(CANDIDATE_BUILT[name].bar_count > 0 for name in EXECUTABLE)
    assert CANDIDATE_BUILT["vss_fxcross_london_up_low"].aux_count > 0


def test_admission_fail_closes_candidate_when_flag_off_and_sizes_when_on():
    intent = TradeIntent(
        sleeve="vol_compression",
        symbol="BTCUSD",
        direction=1,
        decision_day="2026-06-18",
        stop_dist=100.0,
        target_dist=300.0,
    )

    off = admit_and_size([intent], _state(), profile="balanced_0p75")
    assert off["units"][0]["sized"] is False
    assert off["units"][0]["reason"] == "fail_closed:unknown_sleeve:vol_compression"

    on = admit_and_size([intent], _state(), profile="balanced_0p75", include_candidate_book=True)
    unit = on["units"][0]
    assert unit["sized"] is True
    assert unit["confidence"] == 0.4
    assert unit["risk_pct_per_trade"] == 0.003

    subset_off = admit_and_size(
        [intent],
        _state(),
        profile="balanced_0p75",
        include_candidate_book=True,
        candidate_book_sleeves=sorted(READY_SUBSET),
    )
    assert subset_off["units"][0]["sized"] is False
    assert subset_off["units"][0]["reason"] == "fail_closed:unknown_sleeve:vol_compression"

    subset_intent = TradeIntent(
        sleeve="ny_crypto_momentum",
        symbol="BTCUSD",
        direction=1,
        decision_day="2026-06-18",
        stop_dist=100.0,
        target_dist=None,
    )
    subset_on = admit_and_size(
        [subset_intent],
        _state(),
        profile="balanced_0p75",
        include_candidate_book=True,
        candidate_book_sleeves=sorted(READY_SUBSET),
    )
    assert subset_on["candidate_book_sleeves"] == sorted(READY_SUBSET)
    assert subset_on["units"][0]["sized"] is True
    assert subset_on["units"][0]["confidence"] == candidate_registry.CANDIDATE_CONFIDENCE["ny_crypto_momentum"]


def test_bridge_defaults_stay_off_but_active_yaml_arms_exact_candidate_book():
    cfg = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))["gtos_vnext_runtime"]
    assert DEFAULT_CONFIG["ultimate_book_include_candidate_book"] is False
    assert DEFAULT_CONFIG["ultimate_book_candidate_book_profile"] == CANDIDATE_BOOK_PROFILE
    assert DEFAULT_CONFIG["ultimate_book_candidate_book_sleeves"] == []
    assert cfg["ultimate_book_include_candidate_book"] is True
    assert cfg["ultimate_book_candidate_book_profile"] == CANDIDATE_BOOK_PROFILE
    assert set(cfg["ultimate_book_candidate_book_sleeves"]) == FULL_CANDIDATE_ALLOWLIST
    assert len(cfg["ultimate_book_candidate_book_sleeves"]) == len(FULL_CANDIDATE_ALLOWLIST)


def test_bridge_reports_candidate_book_and_fail_closes_unknown_profile():
    intent = TradeIntent(
        sleeve="vol_compression",
        symbol="BTCUSD",
        direction=1,
        decision_day="2026-06-18",
        stop_dist=100.0,
        target_dist=300.0,
    )
    cfg = {"gtos_vnext_runtime": {"ultimate_book_profile": "balanced_0p75"}}
    dec = evaluate_vnext_ultimate_book_admission(config=cfg, intents=[intent], governor_state=_state())
    assert dec.include_candidate_book is False
    assert dec.candidate_book_profile == CANDIDATE_BOOK_PROFILE
    assert dec.candidate_book_sleeves == ()

    bad = {
        "gtos_vnext_runtime": {
            "ultimate_book_profile": "balanced_0p75",
            "ultimate_book_include_candidate_book": True,
            "ultimate_book_candidate_book_profile": "unknown",
        }
    }
    bad_dec = evaluate_vnext_ultimate_book_admission(config=bad, intents=[intent], governor_state=_state())
    assert bad_dec.decision_status == "fail_closed_unknown_candidate_book_profile"
    assert bad_dec.runtime_effect_now is False

    bad_sleeve = {
        "gtos_vnext_runtime": {
            "ultimate_book_profile": "balanced_0p75",
            "ultimate_book_include_candidate_book": True,
            "ultimate_book_candidate_book_sleeves": ["not_a_real_candidate"],
        }
    }
    bad_sleeve_dec = evaluate_vnext_ultimate_book_admission(
        config=bad_sleeve, intents=[intent], governor_state=_state()
    )
    assert bad_sleeve_dec.decision_status == "fail_closed_unknown_candidate_book_sleeves"
    assert bad_sleeve_dec.runtime_effect_now is False


def test_bridge_recognizes_f5_widen_candidate_sleeves():
    widen_names = {
        "asian_fade_widen",
        "ny_crypto_momentum_widen",
        "orb_crypto_london_widen",
    }
    intents = [
        TradeIntent(
            sleeve=name,
            symbol="EURUSD" if name == "asian_fade_widen" else "BTCUSD",
            direction=1,
            decision_day="2026-08-20",
            stop_dist=0.001 if name == "asian_fade_widen" else 100.0,
            target_dist=0.002 if name == "asian_fade_widen" else 200.0,
        )
        for name in sorted(widen_names)
    ]
    cfg = {
        "gtos_vnext_runtime": {
            "ultimate_book_profile": "balanced_0p75",
            "ultimate_book_include_candidate_book": True,
            "ultimate_book_candidate_book_sleeves": sorted(widen_names),
        }
    }

    decision = evaluate_vnext_ultimate_book_admission(
        config=cfg, intents=intents, governor_state=_state()
    )

    assert decision.decision_status == "shadow_book_disabled"
    assert {
        sleeve
        for unit in decision.would_units
        for sleeve in unit["sleeve_members"]
    } == widen_names
    assert all(unit["sized"] is True for unit in decision.would_units)


def test_engine_active_names_follow_same_candidate_flag():
    off = UltimateBookLiveEngine({"ultimate_book_include_candidate_book": False}, object(), "/tmp")
    on = UltimateBookLiveEngine({"ultimate_book_include_candidate_book": True}, object(), "/tmp")
    subset = UltimateBookLiveEngine({
        "ultimate_book_include_candidate_book": True,
        "ultimate_book_candidate_book_sleeves": sorted(READY_SUBSET),
    }, object(), "/tmp")

    assert not (EXECUTABLE & off._active_sleeve_names())
    assert EXECUTABLE <= on._active_sleeve_names()
    assert READY_SUBSET <= subset._active_sleeve_names()
    assert not ((EXECUTABLE - READY_SUBSET) & subset._active_sleeve_names())


def test_candidate_exit_profiles_are_native_not_default_or_fake_targets():
    fixed_target_expected = {
        "vol_compression": {"final_target_r": 3.0, "time_stop_bars": 7680},
        "asia_pdl_fade": {"final_target_r": 3.0, "time_stop_bars": 32},
        "orb_crypto_london": {"final_target_r": 2.0, "time_stop_bars": 80},
        "liq_asia_up_low_metal": {"final_target_r": 3.0, "time_stop_bars": 16},
        "vss_fxcross_london_up_low": {"final_target_r": 2.0, "time_stop_bars": 48},
    }
    no_tp_expected = {
        "asian_fade": {"policy": "trailing_runner", "trigger_r": 0.5, "trail_gap_r": 0.5, "time_stop_bars": 48},
        "metal_session_reversion": {"policy": "trailing_runner", "trigger_r": 0.6, "trail_gap_r": 0.5, "time_stop_bars": 24},
        "ny_crypto_momentum": {"policy": "time_stop", "time_stop_bars": 20},
        "kz_london_crypto_low": {"policy": "time_stop", "time_stop_bars": 32},
    }
    for sleeve, expected in fixed_target_expected.items():
        prof = EP.SLEEVE_EXIT_PROFILES[sleeve]
        assert prof["policy"] == "time_stop"
        assert prof["final_from_intent"] is True
        assert prof["final_target_r"] == expected["final_target_r"]
        assert prof["time_stop_bars"] == expected["time_stop_bars"]

    for sleeve, expected in no_tp_expected.items():
        prof = EP.SLEEVE_EXIT_PROFILES[sleeve]
        assert prof["policy"] == expected["policy"]
        assert prof["final_target_r"] is None
        assert prof["broker_take_profit_mode"] == "none"
        assert prof["time_stop_bars"] == expected["time_stop_bars"]
        if "trigger_r" in expected:
            assert prof["trigger_r"] == expected["trigger_r"]
            assert prof["trail_gap_r"] == expected["trail_gap_r"]
    assert NO_BROKER_TP_NATIVE <= set(EP.SLEEVE_EXIT_PROFILES)
