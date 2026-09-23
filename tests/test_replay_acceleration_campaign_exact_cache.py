from __future__ import annotations

import copy

import pytest

from src.research import moonshot_scheduler_v4_best_trade_allocator as scheduler
from src.models.market_state_models import StructureAnalysis, TimeframeState
from src.research_infra import (
    replay_acceleration_attempt5_typed_sparse_runner as runner,
)
from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp


def _config() -> dict:
    return {
        "market": {"symbol": "XAUUSD"},
        "risk": {
            "risk_per_trade_pct": 0.1,
            "max_daily_loss_pct": 4.0,
        },
        "instruments": {
            "XAUUSD": {
                "market": {
                    "mt5_symbol": "XAUUSD",
                    "point": 0.01,
                    "spread": 20,
                },
                "risk": {"risk_per_trade_pct": 0.1},
            }
        },
        "gtos_vnext_runtime": {
            "timewarp_replay_risk_profile_path": "config/profiles/ftmo.yaml",
            "scheduler_v4_best_trade_allocator_enabled": True,
            "scheduler_v4_best_trade_allocator_apply_to_execution": True,
            "scheduler_v4_best_trade_allocator_live_activation_allowed": False,
            "scheduler_v4_best_trade_allocator_portfolio_ceiling_pct": 4.0,
            "scheduler_v4_best_trade_allocator_correlation_cluster_ceiling_pct": 1.5,
        },
    }


def _d1_candles(*times: str) -> list[dict]:
    return [
        {
            "time": timestamp,
            "time_utc": timestamp,
            "open": 100.0 + index,
            "high": 101.0 + index,
            "low": 99.0 + index,
            "close": 100.5 + index,
            "volume": 100 + index,
        }
        for index, timestamp in enumerate(times)
    ]


def _d1_source_identity(
    candles: list[dict],
    *,
    source_path: str = "/fixture/XAUUSD_D1.csv",
    source_hash: str = "a" * 64,
) -> dict:
    return {
        "source_path": source_path,
        "source_hash": source_hash,
        "source_broker": "FTMO",
        "source_role": "owner_authorized_research_hydration",
        "requested_count": len(candles),
        "returned_count": len(candles),
        "latest_closed_time": candles[-1]["time_utc"],
    }


def _d1_build_parameters(*, min_bars: int = 2) -> dict:
    return {
        "min_bars": min_bars,
        "fvg_min_gap": 0.0,
        "tf_name": "D1",
        "detector_mode": "v1",
        "detector_dead_zone_divisor": 8,
        "shadow_symbol": "XAUUSD",
        "shadow_candle_time": "2026-01-02T00:15:00+00:00",
        "shadow_log_path": None,
        "shadow_logging_enabled": False,
    }


def _empty_timeframe_state() -> TimeframeState:
    return TimeframeState(
        structure=StructureAnalysis(direction="insufficient_data")
    )


def test_campaign_exact_cache_memoizes_exact_outputs_by_strong_config_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config()
    calls = {
        "scheduler": 0,
        "risk": 0,
        "replay_symbol": 0,
        "broker_symbol": 0,
    }
    original_scheduler = timewarp._scheduler_config_uncached
    original_risk = timewarp._risk_pct_for_symbol_uncached
    original_replay_symbol = timewarp._replay_symbol_config_uncached
    original_broker_symbol = timewarp._broker_symbol_config_uncached

    def counted_scheduler(bound_config):
        calls["scheduler"] += 1
        return original_scheduler(bound_config)

    def counted_risk(bound_config, symbol, *, profile_override=None):
        calls["risk"] += 1
        return original_risk(
            bound_config,
            symbol,
            profile_override=profile_override,
        )

    def counted_replay_symbol(bound_config, symbol):
        calls["replay_symbol"] += 1
        return original_replay_symbol(bound_config, symbol)

    def counted_broker_symbol(bound_config, symbol):
        calls["broker_symbol"] += 1
        return original_broker_symbol(bound_config, symbol)

    monkeypatch.setattr(timewarp, "_scheduler_config_uncached", counted_scheduler)
    monkeypatch.setattr(timewarp, "_risk_pct_for_symbol_uncached", counted_risk)
    monkeypatch.setattr(
        timewarp,
        "_replay_symbol_config_uncached",
        counted_replay_symbol,
    )
    monkeypatch.setattr(
        timewarp,
        "_broker_symbol_config_uncached",
        counted_broker_symbol,
    )

    cache = timewarp.CampaignExactCache.from_config(config)
    with timewarp.activate_campaign_exact_cache(cache, config):
        scheduler_first = timewarp.scheduler_config(config)
        scheduler_second = timewarp.scheduler_config(config)
        typed_first = timewarp.typed_scheduler_config(config)
        typed_second = timewarp.typed_scheduler_config(config)
        risk_first = timewarp.risk_pct_for_symbol(config, "XAUUSD")
        risk_second = timewarp.risk_pct_for_symbol(config, "XAUUSD")
        limits_first = timewarp.configured_runtime_risk_limits(
            config,
            symbol="XAUUSD",
        )
        limits_second = timewarp.configured_runtime_risk_limits(
            config,
            symbol="XAUUSD",
        )
        replay_first = timewarp.replay_symbol_config(config, "XAUUSD")
        replay_second = timewarp.replay_symbol_config(config, "XAUUSD")
        broker_first = timewarp._broker_symbol_config(config, "XAUUSD")
        broker_second = timewarp._broker_symbol_config(config, "XAUUSD")

        assert scheduler_first is scheduler_second
        assert typed_first is typed_second
        assert risk_first is risk_second
        assert limits_first is limits_second
        assert replay_first is replay_second
        assert broker_first is broker_second

    assert calls == {
        "scheduler": 1,
        "risk": 1,
        "replay_symbol": 1,
        "broker_symbol": 1,
    }
    audit = cache.audit(config)
    assert audit["config_root_sha256"] == timewarp.stable_sha256(config)
    assert len(audit["risk_profile_sha256"]) == 64
    assert audit["miss_counts"] == {
        "broker_symbol_config": 1,
        "replay_symbol_config": 1,
        "risk_limits": 1,
        "risk_pct": 1,
        "scheduler_config": 1,
        "typed_scheduler_config": 1,
    }
    assert timewarp.active_campaign_exact_cache() is None


def test_campaign_exact_cache_reuses_equal_hash_preimages_and_detects_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config()
    cache = timewarp.CampaignExactCache.from_config(config)
    original_uncached = timewarp._stable_sha256_uncached
    calls = 0

    def counted_uncached(payload: object) -> str:
        nonlocal calls
        calls += 1
        return original_uncached(payload)

    first_payload = {
        "schema": "runtime_quality_contract_v2",
        "candidate_id": "candidate:exact-hash-cache",
        "decision_time_utc": "2026-01-02T10:00:00+00:00",
        "quality": {"expected_net_r": 1.25, "probability": 0.8},
    }
    equal_copy = copy.deepcopy(first_payload)

    with timewarp.activate_campaign_exact_cache(cache, config):
        monkeypatch.setattr(timewarp, "_stable_sha256_uncached", counted_uncached)
        baseline_digest = timewarp.stable_sha256(first_payload)
        assert timewarp.stable_sha256(equal_copy) == baseline_digest
        equal_copy["quality"]["expected_net_r"] = -9.0
        mutated_digest = timewarp.stable_sha256(equal_copy)
        assert mutated_digest != baseline_digest
        assert calls == 2
        assert cache.exact_hash_hits == 1
        assert cache.exact_hash_misses == 2

    assert timewarp.active_campaign_exact_cache() is None


def test_campaign_exact_cache_rejects_equal_but_different_config_reference() -> None:
    config = _config()
    cache = timewarp.CampaignExactCache.from_config(config)
    equal_copy = copy.deepcopy(config)

    with timewarp.activate_campaign_exact_cache(cache, config):
        with pytest.raises(
            timewarp.CampaignExactCacheError,
            match="config_reference_mismatch",
        ):
            timewarp.scheduler_config(equal_copy)


def test_campaign_exact_cache_rejects_config_and_cached_output_mutation() -> None:
    config = _config()
    cache = timewarp.CampaignExactCache.from_config(config)
    with timewarp.activate_campaign_exact_cache(cache, config):
        cached = timewarp.replay_symbol_config(config, "XAUUSD")

    config["risk"]["max_daily_loss_pct"] = 3.5
    with pytest.raises(
        timewarp.CampaignExactCacheError,
        match="config_root_mismatch",
    ):
        cache.validate_boundary(config)

    clean_config = _config()
    clean_cache = timewarp.CampaignExactCache.from_config(clean_config)
    with timewarp.activate_campaign_exact_cache(clean_cache, clean_config):
        cached = timewarp.replay_symbol_config(clean_config, "XAUUSD")
    cached["market"]["symbol"] = "MUTATED"
    with pytest.raises(
        timewarp.CampaignExactCacheError,
        match="cached_output_mutated",
    ):
        clean_cache.validate_boundary(clean_config)


def test_campaign_exact_cache_binds_expected_and_immutable_risk_payload() -> None:
    config = _config()
    _path, expected_sha = timewarp._risk_profile_file_binding(config)
    cache = timewarp.CampaignExactCache.from_config(
        config,
        expected_risk_profile_sha256=expected_sha,
    )

    exposed = cache.risk_profile_payload
    exposed["risk"]["risk_per_trade_pct"] = 99.0
    assert cache.risk_profile_payload["risk"]["risk_per_trade_pct"] != 99.0
    cache._risk_profile_payload["risk"]["risk_per_trade_pct"] = 98.0
    with pytest.raises(
        timewarp.CampaignExactCacheError,
        match="risk_profile_payload_root_mismatch",
    ):
        cache.validate_boundary(config)

    with pytest.raises(
        timewarp.CampaignExactCacheError,
        match="risk_profile_expected_sha256_mismatch",
    ):
        timewarp.CampaignExactCache.from_config(
            config,
            expected_risk_profile_sha256="0" * 64,
        )


def test_campaign_exact_cache_owner_closes_every_registered_cache() -> None:
    config = _config()
    with timewarp.own_campaign_exact_caches():
        cache = timewarp.CampaignExactCache.from_config(config)
        assert cache.closed is False
    assert cache.closed is True


def test_runner_closes_cache_on_early_engine_return(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config()
    created = []

    def early_return(_args):
        created.append(timewarp.CampaignExactCache.from_config(config))
        return {"status": "early_checkpoint"}

    monkeypatch.setattr(runner, "_run_typed_sparse_attempt5", early_return)
    assert runner.run_replay_engine(object()) == {"status": "early_checkpoint"}
    assert len(created) == 1
    assert created[0].closed is True


def test_campaign_exact_cache_context_resets_and_closes_after_exception() -> None:
    config = _config()
    cache = timewarp.CampaignExactCache.from_config(config)

    with pytest.raises(RuntimeError, match="boom"):
        with timewarp.activate_campaign_exact_cache(cache, config):
            assert timewarp.active_campaign_exact_cache() is cache
            raise RuntimeError("boom")

    assert timewarp.active_campaign_exact_cache() is None
    assert cache.closed is True


def test_d1_market_state_cache_returns_fresh_copies_and_detects_private_mutation() -> None:
    config = _config()
    cache = timewarp.CampaignExactCache.from_config(config)
    candles = _d1_candles(
        "2025-12-31T00:00:00+00:00",
        "2026-01-01T00:00:00+00:00",
    )

    def build() -> TimeframeState:
        return TimeframeState(
            structure=StructureAnalysis(direction="bullish")
        )

    first = cache.d1_timeframe_state(
        config,
        symbol="XAUUSD",
        candles=candles,
        source_identity=_d1_source_identity(candles),
        build_parameters=_d1_build_parameters(),
        side_effect_writes_enabled=False,
        builder=build,
    )
    first.structure.direction = "bearish"
    second = cache.d1_timeframe_state(
        config,
        symbol="XAUUSD",
        candles=candles,
        source_identity=_d1_source_identity(candles),
        build_parameters=_d1_build_parameters(),
        side_effect_writes_enabled=False,
        builder=build,
    )
    assert second.structure.direction == "bullish"
    assert cache.market_state_cache_audit() == {
        "d1_hits": 1,
        "d1_misses": 1,
        "d1_builds": 1,
        "d1_evictions": 0,
        "d1_entries": 1,
    }

    cache._timeframe_state_by_symbol_timeframe[("XAUUSD", "D1")][
        "payload"
    ].structure.direction = "bearish"
    with pytest.raises(
        timewarp.CampaignExactCacheError,
        match="cached_output_mutated:closed_timeframe_state:XAUUSD:D1",
    ):
        cache.validate_boundary(config)


def test_d1_market_state_cache_rebuilds_on_same_endpoint_source_identity_change() -> None:
    config = _config()
    cache = timewarp.CampaignExactCache.from_config(config)
    candles = _d1_candles(
        "2025-12-31T00:00:00+00:00",
        "2026-01-01T00:00:00+00:00",
    )
    kwargs = {
        "symbol": "XAUUSD",
        "build_parameters": _d1_build_parameters(),
        "side_effect_writes_enabled": False,
        "builder": _empty_timeframe_state,
    }
    cache.d1_timeframe_state(
        config,
        candles=candles,
        source_identity=_d1_source_identity(candles),
        **kwargs,
    )
    cache.d1_timeframe_state(
        config,
        candles=candles,
        source_identity=_d1_source_identity(
            candles,
            source_path="/fixture-successor/XAUUSD_D1.csv",
            source_hash="b" * 64,
        ),
        **kwargs,
    )

    assert cache.market_state_cache_audit() == {
        "d1_hits": 0,
        "d1_misses": 2,
        "d1_builds": 2,
        "d1_evictions": 1,
        "d1_entries": 1,
    }


def test_closed_timeframe_cache_does_not_rehash_rows_on_exact_hit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config()
    cache = timewarp.CampaignExactCache.from_config(config)
    candles = _d1_candles(
        "2025-12-31T00:00:00+00:00",
        "2026-01-01T00:00:00+00:00",
    )
    source_identity = _d1_source_identity(candles)
    original_stable_sha256 = timewarp.stable_sha256
    selected_row_hash_calls = 0

    def counted_stable_sha256(value):
        nonlocal selected_row_hash_calls
        if (
            isinstance(value, list)
            and value
            and isinstance(value[0], dict)
            and "time_utc" in value[0]
            and "open" in value[0]
        ):
            selected_row_hash_calls += 1
        return original_stable_sha256(value)

    monkeypatch.setattr(timewarp, "stable_sha256", counted_stable_sha256)
    for _ in range(2):
        cache.d1_timeframe_state(
            config,
            symbol="XAUUSD",
            candles=candles,
            source_identity=source_identity,
            build_parameters=_d1_build_parameters(),
            side_effect_writes_enabled=False,
            builder=_empty_timeframe_state,
        )

    assert selected_row_hash_calls == 0
    assert cache.market_state_cache_audit()["d1_hits"] == 1


def test_d1_market_state_cache_evicts_on_endpoint_or_semantic_key_change() -> None:
    config = _config()
    cache = timewarp.CampaignExactCache.from_config(config)
    first_candles = _d1_candles("2025-12-31T00:00:00+00:00")
    second_candles = _d1_candles(
        "2025-12-31T00:00:00+00:00",
        "2026-01-01T00:00:00+00:00",
    )
    build_count = 0

    def build() -> TimeframeState:
        nonlocal build_count
        build_count += 1
        return _empty_timeframe_state()

    cache.d1_timeframe_state(
        config,
        symbol="XAUUSD",
        candles=first_candles,
        source_identity=_d1_source_identity(first_candles),
        build_parameters=_d1_build_parameters(),
        side_effect_writes_enabled=False,
        builder=build,
    )
    cache.d1_timeframe_state(
        config,
        symbol="XAUUSD",
        candles=second_candles,
        source_identity=_d1_source_identity(second_candles),
        build_parameters=_d1_build_parameters(),
        side_effect_writes_enabled=False,
        builder=build,
    )
    cache.d1_timeframe_state(
        config,
        symbol="XAUUSD",
        candles=second_candles,
        source_identity=_d1_source_identity(
            second_candles,
            source_path="/fixture-successor/XAUUSD_D1.csv",
            source_hash="b" * 64,
        ),
        build_parameters=_d1_build_parameters(min_bars=3),
        side_effect_writes_enabled=False,
        builder=build,
    )

    assert build_count == 3
    assert cache.market_state_cache_audit() == {
        "d1_hits": 0,
        "d1_misses": 3,
        "d1_builds": 3,
        "d1_evictions": 2,
        "d1_entries": 1,
    }
    cache.close()
    assert cache.market_state_cache_audit()["d1_entries"] == 0


def test_d1_market_state_cache_rejects_side_effect_or_shadow_logging() -> None:
    config = _config()
    cache = timewarp.CampaignExactCache.from_config(config)
    candles = _d1_candles("2026-01-01T00:00:00+00:00")

    with pytest.raises(
        timewarp.CampaignExactCacheError,
        match="d1_market_state_side_effects_must_be_disabled",
    ):
        cache.d1_timeframe_state(
            config,
            symbol="XAUUSD",
            candles=candles,
            source_identity=_d1_source_identity(candles),
            build_parameters=_d1_build_parameters(),
            side_effect_writes_enabled=True,
            builder=_empty_timeframe_state,
        )

    shadow_parameters = _d1_build_parameters()
    shadow_parameters["shadow_logging_enabled"] = True
    with pytest.raises(
        timewarp.CampaignExactCacheError,
        match="d1_market_state_side_effects_must_be_disabled",
    ):
        cache.d1_timeframe_state(
            config,
            symbol="XAUUSD",
            candles=candles,
            source_identity=_d1_source_identity(candles),
            build_parameters=shadow_parameters,
            side_effect_writes_enabled=False,
            builder=_empty_timeframe_state,
        )


def test_pretyped_scheduler_preserves_exact_raw_package_runtime_authority() -> None:
    raw_config = {
        "enabled": True,
        "apply_to_execution": True,
        "live_activation_allowed": False,
        "ultimate_candidate_package_final_package_selected": True,
        "ultimate_candidate_package_apply_to_execution": True,
        "ultimate_candidate_package_live_activation_allowed": True,
    }
    window = {
        "decision_window_id": "window:task3-empty",
        "candidate_set_id": "set:task3-empty",
        "asof_utc": "2026-01-02T00:00:00+00:00",
        "candidates": [],
        "open_positions": [],
        "pending_orders": [],
        "evidence_class": "unit",
        "source_status": "complete",
        "missing_runtime_truth": [],
    }

    legacy = scheduler.allocate_decision_window(window, raw_config)
    typed = scheduler.SchedulerV4Config.from_mapping(raw_config)
    cached = scheduler.allocate_decision_window(
        window,
        typed,
        raw_config=raw_config,
    )

    assert cached == legacy
    assert cached["package_runtime_authority_enabled"] is True


def test_shared_contract_reuses_prebuilt_profile_config_and_binds_risk_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config()
    monkeypatch.setattr(
        runner,
        "build_config",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("profile config rebuilt")
        ),
    )

    contract = runner.broad_replay_shared_execution_contract(
        profiles=(runner.PROFILE_REPAIRED,),
        active_symbols=("XAUUSD",),
        execution_options={"task3": True},
        runtime_input_contract={"schema": "unit.runtime", "valid": True},
        profile_configs={runner.PROFILE_REPAIRED: config},
    )

    assert contract["exact_profile_config_roots_sha256"] == {
        runner.PROFILE_REPAIRED: runner.stable_sha256(config)
    }
    risk_path, risk_sha = timewarp._risk_profile_file_binding(config)
    assert contract["exact_risk_profile_bindings"] == {
        runner.PROFILE_REPAIRED: {
            "path": str(risk_path.relative_to(runner.ROOT)),
            "sha256": risk_sha,
        }
    }
    assert set(contract["config_file_hashes"]) == {
        "config/agent_config.yaml",
        "config/profiles/operator_profile.yaml",
    }


def test_shared_semantic_digest_excludes_exact_diagnostic_config_root() -> None:
    config = _config()

    def contract(bound_config: dict) -> dict:
        return runner.broad_replay_shared_execution_contract(
            profiles=(runner.PROFILE_REPAIRED,),
            active_symbols=("XAUUSD",),
            execution_options={"task3": True},
            runtime_input_contract={"schema": "unit.runtime", "valid": True},
            profile_configs={runner.PROFILE_REPAIRED: bound_config},
        )

    first = contract(config)
    diagnostic_change = copy.deepcopy(config)
    diagnostic_change.setdefault("gtos_vnext_runtime", {})[
        "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
        "selected_policy_expected_net_source_artifact_sha256"
    ] = "a" * 64
    second = contract(diagnostic_change)

    assert (
        first["shared_execution_contract_digest_sha256"]
        == second["shared_execution_contract_digest_sha256"]
    )
    assert (
        first["exact_profile_config_roots_sha256"]
        != second["exact_profile_config_roots_sha256"]
    )
