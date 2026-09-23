from __future__ import annotations

import copy
from pathlib import Path

import pytest

from src.models.market_state_models import MarketStateObject
from src.research_infra.replay_prepared_day_pack import (
    FACTORIAL_HARNESS_KEY,
    FACTORIAL_RUNTIME_PREFIX,
    FACTORIAL_SIZING_RUNTIME_KEYS,
    PreparedDayPackError,
    PreparedDayPackReader,
    assert_no_factor_reads,
    factor_neutral_config_root,
    seal_prepared_day_pack,
)


def _mso_payload(*, timestamp: str) -> dict:
    payload = {
        "timestamp_utc": timestamp,
        "timeframes": {
            "M15": {
                "swings": [],
                "structure": {
                    "direction": "insufficient_data",
                    "protected_swing": None,
                    "swing_sequence": [],
                    "hh_count": 0,
                    "hl_count": 0,
                    "lh_count": 0,
                    "ll_count": 0,
                },
                "structure_events": [],
                "order_blocks": [],
                "breaker_blocks": [],
                "fair_value_gaps": [],
                "premium_discount": None,
                "avg_candle_body": 0.0,
                "atr_14": 0.0,
                "clv_current": None,
                "clv_avg_5": None,
                "bvc_buy_fraction": None,
                "net_flow_5": None,
                "atr_session": None,
                "session_vol_ratio": None,
            }
        },
        "session_levels": {
            "asian_high": 1.2,
            "asian_low": 1.1,
            "pdh": 1.3,
            "pdl": 1.0,
            "session_high": None,
            "session_low": None,
            "london_high": None,
            "london_low": None,
        },
        "equal_highs": [],
        "equal_lows": [],
        "liquidity_pools": [],
        "detected_sweeps": [],
        "spread_cents": None,
        "high_impact_events": None,
        "data_quality": {
            "all_timeframes_complete": True,
            "spread_normal": True,
            "mt5_connected": False,
            "timestamp_utc": timestamp,
        },
        "materialize_semantic_diagnostics": False,
        "candidate_ledger_packet_max_bytes": 20_000,
        "scorecard_ledger_packet_max_bytes": 20_000,
        "compact_scorecard_symbol_risk_config": False,
        "scorecard_probe_row_limit": None,
    }
    return MarketStateObject.model_validate(payload).model_dump(mode="json")


def _record(ordinal: int) -> dict:
    minute = 15 * (ordinal + 1)
    timestamp = f"2026-01-02T00:{minute:02d}:00+00:00"
    return {
        "schema": "gtos.replay_acceleration.prepared_window.v1",
        "trading_day": "2026-01-02",
        "window_ordinal": ordinal,
        "decision_time_utc": timestamp,
        "calendar_no_session_breadth_guard": {"active": False},
        "symbols": [
            {
                "symbol": "EURUSD",
                "status": "prepared",
                "asof_row": {
                    "raw_data_status": (
                        "live_equivalent_raw_data_built_and_mso_computed"
                    ),
                    "candidate_count": 1,
                    "decision_time_utc": timestamp,
                },
                "mso_payload": _mso_payload(timestamp=timestamp),
                "candidates": [
                    {
                        "candidate_id": f"candidate-{ordinal}",
                        "symbol": "EURUSD",
                        "decision_time_utc": timestamp,
                        "current_price": 1.125 + ordinal / 10_000,
                    }
                ],
            },
            {
                "symbol": "XAUUSD",
                "status": "source_skipped",
                "asof_row": {
                    "raw_data_status": "ftmo_verified_no_session_day_symbol_skipped",
                    "candidate_count": 0,
                    "decision_time_utc": timestamp,
                },
                "mso_payload": None,
                "candidates": [],
            },
        ],
    }


def _bindings() -> dict:
    return {
        "days": ["2026-01-02"],
        "symbols": ["EURUSD", "XAUUSD"],
        "factor_neutral_config_root_sha256": "a" * 64,
        "source_identity_root_sha256": "b" * 64,
        "max_candidates_per_symbol_window": None,
    }


def test_sealed_pack_root_is_identical_for_one_and_four_workers(tmp_path: Path) -> None:
    records = [_record(0), _record(1), _record(2)]

    one = seal_prepared_day_pack(
        output_dir=tmp_path / "one",
        records=records,
        bindings=_bindings(),
        encoding_worker_count=1,
        target_raw_shard_bytes=3_000,
    )
    four = seal_prepared_day_pack(
        output_dir=tmp_path / "four",
        records=records,
        bindings=_bindings(),
        encoding_worker_count=4,
        target_raw_shard_bytes=3_000,
    )

    assert one == four
    assert one["pack_root_sha256"] == four["pack_root_sha256"]
    assert len(one["shards"]) > 1
    assert all(row["compressed_bytes"] <= 128 * 1024 * 1024 for row in one["shards"])

    reader = PreparedDayPackReader(tmp_path / "four")
    reader.assert_compatible(**_bindings())
    restored = [
        reader.next_window(
            trading_day=row["trading_day"],
            decision_time_utc=row["decision_time_utc"],
            window_ordinal=row["window_ordinal"],
        )
        for row in records
    ]
    reader.finish()
    assert restored == records


def test_pack_rejects_corruption_and_out_of_order_windows(tmp_path: Path) -> None:
    with pytest.raises(PreparedDayPackError, match="window_order_invalid"):
        seal_prepared_day_pack(
            output_dir=tmp_path / "bad-order",
            records=[_record(1), _record(0)],
            bindings=_bindings(),
        )

    manifest = seal_prepared_day_pack(
        output_dir=tmp_path / "corrupt",
        records=[_record(0), _record(1)],
        bindings=_bindings(),
    )
    shard = tmp_path / "corrupt" / manifest["shards"][0]["path"]
    raw = bytearray(shard.read_bytes())
    raw[len(raw) // 2] ^= 1
    shard.write_bytes(raw)

    with pytest.raises(PreparedDayPackError, match="compressed_sha256_mismatch"):
        PreparedDayPackReader(tmp_path / "corrupt")


def test_pack_rejects_mso_payload_that_is_not_an_exact_round_trip(tmp_path: Path) -> None:
    record = _record(0)
    record["symbols"][0]["mso_payload"].pop("equal_highs")

    with pytest.raises(PreparedDayPackError, match="mso_round_trip_mismatch"):
        seal_prepared_day_pack(
            output_dir=tmp_path / "bad-mso",
            records=[record],
            bindings=_bindings(),
        )


def test_reader_rejects_a_resealed_pack_without_the_bound_external_root(
    tmp_path: Path,
) -> None:
    accepted = seal_prepared_day_pack(
        output_dir=tmp_path / "accepted",
        records=[_record(0)],
        bindings=_bindings(),
    )
    changed = _record(0)
    changed["symbols"][0]["candidates"][0]["current_price"] += 0.0001
    resealed = seal_prepared_day_pack(
        output_dir=tmp_path / "resealed",
        records=[changed],
        bindings=_bindings(),
    )
    assert resealed["pack_root_sha256"] != accepted["pack_root_sha256"]

    with pytest.raises(PreparedDayPackError, match="prepared_pack_external_root_mismatch"):
        PreparedDayPackReader(
            tmp_path / "resealed",
            expected_pack_root_sha256=accepted["pack_root_sha256"],
        )


def test_pack_rejects_unknown_status_instead_of_silently_suppressing(
    tmp_path: Path,
) -> None:
    record = _record(0)
    record["symbols"][1]["status"] = "skipped"
    with pytest.raises(PreparedDayPackError, match="prepared_symbol_status_invalid"):
        seal_prepared_day_pack(
            output_dir=tmp_path / "unknown-status",
            records=[record],
            bindings=_bindings(),
        )


@pytest.mark.parametrize(
    ("status", "raw_status"),
    (
        (
            "source_incomplete",
            "source_required_insufficient_live_timeframes",
        ),
        (
            "market_state_failed",
            "source_required_market_state_compute_failed",
        ),
    ),
)
def test_pack_accepts_only_status_specific_finite_source_failures(
    tmp_path: Path,
    status: str,
    raw_status: str,
) -> None:
    record = _record(0)
    symbol = record["symbols"][1]
    symbol["status"] = status
    symbol["asof_row"]["raw_data_status"] = raw_status
    seal_prepared_day_pack(
        output_dir=tmp_path / status,
        records=[record],
        bindings=_bindings(),
    )

    symbol["asof_row"]["raw_data_status"] = (
        "source_required_market_state_failed"
        if status == "source_incomplete"
        else "source_required_insufficient_live_timeframes"
    )
    with pytest.raises(
        PreparedDayPackError,
        match="skipped_symbol_source_contract_invalid",
    ):
        seal_prepared_day_pack(
            output_dir=tmp_path / f"{status}-wrong-raw",
            records=[record],
            bindings=_bindings(),
        )


@pytest.mark.parametrize(
    ("target", "field", "value"),
    (
        ("candidate", "terminal_r", 1.0),
        ("candidate", "cash_pnl", 10.0),
        ("candidate", "mfe_r", 2.0),
        ("candidate", "mae_r", -0.5),
        ("candidate", "close_reason", "target"),
        ("candidate", "fill_price", 1.2),
        ("candidate", "account_balance", 100_000.0),
        ("candidate", "pending_orders", []),
        ("asof", "broker_state", {}),
        ("asof", "reservation_state", {}),
    ),
)
def test_pack_rejects_outcome_account_and_broker_payload_namespaces(
    tmp_path: Path,
    target: str,
    field: str,
    value: object,
) -> None:
    record = _record(0)
    symbol = record["symbols"][0]
    payload = symbol["candidates"][0] if target == "candidate" else symbol["asof_row"]
    payload[field] = value
    with pytest.raises(PreparedDayPackError, match="prepared_postdecision_field_forbidden"):
        seal_prepared_day_pack(
            output_dir=tmp_path / f"forbidden-{target}-{field}",
            records=[record],
            bindings=_bindings(),
        )


def test_pack_rejects_future_source_timestamp(tmp_path: Path) -> None:
    record = _record(0)
    record["symbols"][0]["candidates"][0]["source_asof_utc"] = (
        "2026-01-02T00:16:00+00:00"
    )
    with pytest.raises(PreparedDayPackError, match="prepared_future_timestamp"):
        seal_prepared_day_pack(
            output_dir=tmp_path / "future-source",
            records=[record],
            bindings=_bindings(),
        )


def test_pack_accepts_empty_optional_predecision_timestamp_sentinel(
    tmp_path: Path,
) -> None:
    record = _record(0)
    record["symbols"][0]["candidates"][0]["invalidation_time_utc"] = ""
    manifest = seal_prepared_day_pack(
        output_dir=tmp_path / "optional-empty-time",
        records=[record],
        bindings=_bindings(),
    )
    reader = PreparedDayPackReader(
        tmp_path / "optional-empty-time",
        expected_pack_root_sha256=manifest["pack_root_sha256"],
    )
    reader.next_window(
        trading_day=record["trading_day"],
        decision_time_utc=record["decision_time_utc"],
        window_ordinal=record["window_ordinal"],
    )
    reader.finish()


def test_factor_neutral_root_ignores_only_exact_factor_keys() -> None:
    base = {
        "risk": {"risk_per_trade_pct": 0.1},
        "gtos_vnext_runtime": {
            "ordinary_runtime_key": 7,
            f"{FACTORIAL_RUNTIME_PREFIX}arm_id": "S0R0",
            f"{FACTORIAL_RUNTIME_PREFIX}selection_factor": "S0",
        },
        "broad_live_as_if_replay_harness": {
            "ordinary_harness_key": 11,
            FACTORIAL_HARNESS_KEY: {
                "arm_id": "S0R0",
                "selection_factor": "S0",
            },
        },
    }
    other_arm = copy.deepcopy(base)
    other_arm["gtos_vnext_runtime"].update(
        {
            f"{FACTORIAL_RUNTIME_PREFIX}arm_id": "S1R1",
            f"{FACTORIAL_RUNTIME_PREFIX}selection_factor": "S1",
        }
    )
    other_arm["broad_live_as_if_replay_harness"][FACTORIAL_HARNESS_KEY] = {
        "arm_id": "S1R1",
        "selection_factor": "S1",
    }
    sizing_gate = next(iter(FACTORIAL_SIZING_RUNTIME_KEYS))
    base["gtos_vnext_runtime"][sizing_gate] = False
    other_arm["gtos_vnext_runtime"][sizing_gate] = True

    assert factor_neutral_config_root(base) == factor_neutral_config_root(other_arm)

    changed_real_input = copy.deepcopy(other_arm)
    changed_real_input["gtos_vnext_runtime"]["ordinary_runtime_key"] = 8
    assert factor_neutral_config_root(base) != factor_neutral_config_root(
        changed_real_input
    )

    changed_harness_input = copy.deepcopy(other_arm)
    changed_harness_input["broad_live_as_if_replay_harness"][
        "ordinary_harness_key"
    ] = 12
    assert factor_neutral_config_root(base) != factor_neutral_config_root(
        changed_harness_input
    )


@pytest.mark.parametrize(
    "reads",
    (
        {f"gtos_vnext_runtime.{FACTORIAL_RUNTIME_PREFIX}arm_id"},
        {
            "broad_live_as_if_replay_harness."
            f"{FACTORIAL_HARNESS_KEY}.arm_id"
        },
        {"gtos_vnext_runtime.*"},
        {"*"},
        {
            "gtos_vnext_runtime."
            "scheduler_v4_best_trade_allocator_dynamic_budget_quality_gate_enabled"
        },
    ),
)
def test_factor_read_guard_fails_closed(reads: set[str]) -> None:
    with pytest.raises(PreparedDayPackError, match="factor_read_detected"):
        assert_no_factor_reads(reads)


def test_factor_read_guard_accepts_nonfactor_preparation_reads() -> None:
    assert_no_factor_reads(
        {
            "data.lookback.M15",
            "gtos_vnext_runtime.market_state_side_effect_writes_enabled",
        }
    )


def test_factor_read_guard_accepts_broad_reads_of_factor_free_projection() -> None:
    assert_no_factor_reads(
        {"*", "gtos_vnext_runtime.*"},
        factor_namespace_absent=True,
    )
    with pytest.raises(PreparedDayPackError, match="factor_read_detected"):
        assert_no_factor_reads(
            {f"gtos_vnext_runtime.{FACTORIAL_RUNTIME_PREFIX}arm_id"},
            factor_namespace_absent=True,
        )
    with pytest.raises(PreparedDayPackError, match="factor_read_detected"):
        assert_no_factor_reads(
            {
                "broad_live_as_if_replay_harness."
                f"{FACTORIAL_HARNESS_KEY}.selection_factor"
            },
            factor_namespace_absent=True,
        )
