from collections import Counter

from src.components.ultimate_book import admission
from src.components.ultimate_book.sleeves import candidate_registry


def test_market_expansion_default_off_catalog_is_complete_and_inert():
    specs = candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES
    assert len(specs) == 16
    assert len(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_NAMES) == 16
    assert len(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_M1_SUPPORTED_NAMES) == 15
    assert candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_PROXY_REPAIR_REQUIRED_NAMES == ()
    assert candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_TRANSFORMED_NAMES == (
        "mx_ger40_cash_d1_atr_mean_reversion",
    )
    assert candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_RUNTIME_NAMES == ()
    assert all(spec.activation_weight_now == 0.0 for spec in specs.values())
    assert all(spec.candidate_weight_ceiling == 0.05 for spec in specs.values())
    assert sum(
        spec.evidence_route.endswith("market_expansion_proxy_m1_repair_2026_06_18")
        for spec in specs.values()
    ) == 10
    assert set(specs).isdisjoint(candidate_registry.CANDIDATES)
    assert set(specs).isdisjoint(candidate_registry.CANDIDATE_CONFIDENCE)
    assert set(specs).isdisjoint(candidate_registry.RUNTIME_EXECUTABLE_CANDIDATE_NAMES)


def test_market_expansion_default_off_catalog_matches_design_counts():
    specs = candidate_registry.market_expansion_default_off_specs()
    assert len(specs) == 16
    assert Counter(spec.design_status for spec in specs) == {
        "default_off_spec_design_ready": 15,
        "transformed_context_or_veto_after_exact_m1_repair": 1,
    }
    assert Counter(spec.candidate_seed_weight for spec in specs) == {0.025: 14, 0.0: 2}
    assert Counter(spec.family for spec in specs) == {
        "crypto_alt_or_major": 3,
        "indices_context": 11,
        "jpy_fx": 2,
    }
    assert Counter(spec.mechanism for spec in specs) == {
        "d1_atr_mean_reversion": 4,
        "d1_donchian_20_breakout": 4,
        "d1_volume_surge_reversal": 8,
    }
    assert {spec.file_symbol for spec in specs} == {
        "AUS200_cash",
        "AVAUSD",
        "BTCUSD",
        "CADJPY",
        "ETHUSD",
        "EU50_cash",
        "FRA40_cash",
        "GER40_cash",
        "JP225_cash",
        "NZDJPY",
        "SPN35_cash",
        "US100_cash",
        "US30_cash",
        "US500_cash",
    }
    collision_losers = {spec.tag for spec in specs if not spec.symbol_collision_winner}
    assert collision_losers == {
        "mx_aus200_cash_d1_atr_mean_reversion",
        "mx_ger40_cash_d1_atr_mean_reversion",
    }


def test_market_expansion_default_off_catalog_does_not_enter_effective_registry():
    active = admission.effective_registry(include_candidate_book=True)
    expansion_names = set(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_NAMES)
    assert expansion_names.isdisjoint(active)
    assert expansion_names.isdisjoint(admission.candidate_book_registry())
    assert set(active) >= set(candidate_registry.BOOK_PROMOTION_READY_CANDIDATE_NAMES)
