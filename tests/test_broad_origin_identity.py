"""Behavioral contract for broad-origin emission and executable identity.

The producer keeps ``candidate_id`` only as a legacy compatibility field.  A
target/stop-invariant source lineage and a final executable-instance hash are
the v1 authorities at downstream boundaries.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.components.broad_origin_emission_contract import (
    ALLOW_FORMING_BAR_KEY,
    BREAKER_BUFFER_ADR006,
    BREAKER_BUFFER_LEGACY_GENERIC,
    BREAKER_STOP_BUFFER_SOURCE_KEY,
    RUNTIME_SECTION,
    SESSION_NAMING_CONTINUOUS,
    SESSION_NAMING_KEY,
    SESSION_NAMING_LEGACY_SENTINEL,
    WAVE21_FULL_FLOW_TRUTH_MODE_KEY,
    BroadOriginEmissionPolicy,
)
from src.components.candidate_identity import (
    EMISSION_LINEAGE_ID_PREFIX,
    EXECUTABLE_INSTANCE_ID_PREFIX,
    EXECUTABLE_STATUS_NOT_FINAL,
    build_emission_lineage_fields,
    build_executable_instance_fields,
    build_selector_input_geometry_fields,
    candidate_identity_contract_failures,
    canonical_identity_sha256,
)
from src.components.broader_origin_generators import (
    SESSION_WINDOWS,
    TARGET_POLICY_ENABLE_KEY,
    Bar,
    BarSeries,
    _generate_cross_asset_candidate,
    generate_live_broader_origin_candidates,
)
from src.research_infra.completed_bar_witness import (
    COMPLETION_SEMANTICS,
    ROW_WITNESS_FIELD,
    WITNESS_TYPE,
)


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _bars(
    *,
    latest_open: str = "2026-05-26T13:00:00Z",
    count: int = 60,
    close: float = 100.0,
    width: float = 1.0,
) -> list[dict]:
    latest = _dt(latest_open)
    start = latest - timedelta(minutes=15 * (count - 1))
    return [
        {
            "time": (start + timedelta(minutes=15 * index))
            .astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "open": close,
            "high": close + width / 2,
            "low": close - width / 2,
            "close": close,
        }
        for index in range(count)
    ]


def _raw(
    symbol: str,
    bars: list[dict],
    *,
    declared_close: str | None = None,
) -> dict:
    latest = _dt(bars[-1]["time"])
    return {
        "symbol": symbol,
        "candle_open_utc": latest.isoformat(),
        "candle_close_utc": declared_close
        or (latest + timedelta(minutes=15)).isoformat(),
        "candles": {"M15": bars},
    }


def _truth_raw(
    symbol: str,
    bars: list[dict],
    *,
    declared_close: str | None = None,
) -> dict:
    """Witnessed four-timeframe raw fixture satisfying merged truth-mode source
    validation (all consumed timeframes present, every row completion-witnessed).

    Mirrors the fixture contract of ``tests/test_broader_origin_generators.py``;
    added at wave-21 integration when the merged generator began validating the
    full consumed-timeframe set in truth mode (this file predates that check).
    """

    raw = _raw(symbol, copy.deepcopy(bars), declared_close=declared_close)
    timeframes = ("D1", "H4", "H1", "M15")
    raw["candles"] = {
        timeframe: copy.deepcopy(bars) for timeframe in timeframes
    }
    for timeframe, witnessed in raw["candles"].items():
        for ordinal, row in enumerate(witnessed):
            predecessor = _dt(row["time"])
            successor = predecessor + timedelta(minutes=15)
            row[ROW_WITNESS_FIELD] = {
                "witness_type": WITNESS_TYPE,
                "completion_semantics": COMPLETION_SEMANTICS,
                "timeframe": timeframe,
                "predecessor_source_ordinal": ordinal,
                "successor_source_ordinal": ordinal + 1,
                "predecessor_open_utc": predecessor.isoformat(),
                "successor_open_utc": successor.isoformat(),
                "successor_market_values_consumed": False,
            }
    witnessed = raw["candles"]["M15"]
    latest = _dt(witnessed[-1]["time"])
    raw.update(
        {
            "source_truth_scope": "unit_source_bound_truth",
            "source_hashes_by_timeframe": {
                timeframe: (str(index + 1) * 64)[:64]
                for index, timeframe in enumerate(timeframes)
            },
            "decision_rows_used_by_timeframe": {
                timeframe: len(witnessed) for timeframe in timeframes
            },
            "decision_max_source_time_utc_by_timeframe": {
                timeframe: latest.isoformat() for timeframe in timeframes
            },
            "decision_completion_witness_by_timeframe": {
                timeframe: copy.deepcopy(
                    raw["candles"][timeframe][-1][ROW_WITNESS_FIELD]
                )
                for timeframe in timeframes
            },
            "decision_completed_bar_selection": (
                "observed_successor_open_utc_upper_bound"
            ),
        }
    )
    return raw


def _run(
    raw: dict,
    *,
    config: dict,
    symbol: str = "XAUUSD",
    mso=None,
    now: str | datetime | None = None,
    audit: dict | None = None,
) -> list[dict]:
    return generate_live_broader_origin_candidates(
        raw_data=raw,
        mso=mso,
        config=config,
        symbol=symbol,
        kill_zone="ny",
        now_utc=now or raw["candle_close_utc"],
        generation_audit=audit,
    )


def _family(rows: list[dict], name: str) -> dict:
    return next(row for row in rows if row["origin_family"] == name)


def _sweep_candidate(*, min_rr: float = 0.5, runtime: dict | None = None) -> dict:
    bars = _bars()
    bars[-1].update(
        {"open": 100.2, "high": 101.8, "low": 99.9, "close": 100.4}
    )
    config = {"risk": {"min_rr": min_rr}}
    if runtime is not None:
        config[RUNTIME_SECTION] = dict(runtime)
    return _family(
        _run(_raw("XAUUSD", bars), config=config),
        "liquidity_sweep_reclaim",
    )


def test_lineage_survives_target_and_stop_policy_but_exact_instance_does_not() -> None:
    legacy = _sweep_candidate(min_rr=0.5)
    declared_target = _sweep_candidate(
        min_rr=0.5,
        runtime={TARGET_POLICY_ENABLE_KEY: True},
    )
    wider_stop = _sweep_candidate(
        min_rr=0.5,
        runtime={"moonshot_broader_origin_stop_width_atr_scale": 2.0},
    )

    assert legacy["take_profit_1"] != declared_target["take_profit_1"]
    assert legacy["candidate_id"] != declared_target["candidate_id"]
    assert legacy["candidate_id"] == wider_stop["candidate_id"]
    assert legacy["stop_loss"] != wider_stop["stop_loss"]
    assert {
        row["emission_lineage_id"]
        for row in (legacy, declared_target, wider_stop)
    } == {legacy["emission_lineage_id"]}
    assert {
        row["emission_lineage_hash_sha256"]
        for row in (legacy, declared_target, wider_stop)
    } == {legacy["emission_lineage_hash_sha256"]}
    assert all(
        row["executable_instance_status"] == EXECUTABLE_STATUS_NOT_FINAL
        and row["executable_instance_hash_sha256"] is None
        for row in (legacy, declared_target, wider_stop)
    )

    def final_hash(row: dict) -> str:
        final = {**row, "order_type": row["candidate_order_type_hint"]}
        if final["order_type"] == "LIMIT":
            final["time_in_force"] = "GTC"
        return str(
            build_executable_instance_fields(final)[
                "executable_instance_hash_sha256"
            ]
        )

    assert len(
        {
            final_hash(row)
            for row in (legacy, declared_target, wider_stop)
        }
    ) == 3
    assert all(
        row["candidate_identity_contract_status"]
        == "valid_emission_v1_exec_not_final"
        for row in (legacy, declared_target, wider_stop)
    )


def test_legacy_candidate_id_algorithm_is_unchanged_for_compatibility() -> None:
    candidate = _sweep_candidate(min_rr=0.5)
    payload = {
        "origin_family": candidate["origin_family"],
        "symbol": candidate["symbol"],
        "side": candidate["side"],
        "candle_open_utc": candidate["candle_open_utc"],
        "entry": round(candidate["entry_price"], 10),
        "stop": round(candidate["stop_loss"], 10),
        "target": round(candidate["take_profit_1"], 10),
    }
    material = json.dumps(
        payload, sort_keys=True, default=str, separators=(",", ":")
    ).encode("utf-8")
    assert candidate["candidate_id"] == (
        "broadorigin_" + hashlib.sha256(material).hexdigest()[:24]
    )
    assert candidate["candidate_id_contract_status"] == (
        "legacy_compatibility_alias_not_lineage_or_executable_authority"
    )


def _identity_row() -> dict:
    row = {
        "origin_family": "current_fvg_fill",
        "emission_generation_side": "buy",
        "poi_id": "poi-stable-1",
        "candle_open_utc": "2026-05-26T13:00:00.123456+00:00",
        "decision_time_utc": "2026-05-26T13:15:00Z",
        "symbol": "US30.CASH",
        "side": "LONG",
        "entry_price": 100.0,
        "stop_loss": 99.0,
        "take_profit_1": 101.5,
        "order_type": "LIMIT",
        "time_in_force": "GTC",
        "trade_parameters": {
            "entry_price": 100.0,
            "stop_loss": 99.0,
            "take_profit_1": 101.5,
        },
    }
    row.update(build_emission_lineage_fields(row))
    row.update(build_executable_instance_fields(row))
    return row


@pytest.mark.parametrize(
    "field,value",
    [
        ("decision_time_utc", "2026-05-26T13:16:00Z"),
        ("symbol", "NAS100"),
        ("side", "SHORT"),
        ("entry_price", 100.25),
        ("stop_loss", 98.75),
        ("take_profit_1", 102.0),
        ("order_type", "MARKET"),
    ],
)
def test_executable_hash_binds_every_final_atom(field: str, value: object) -> None:
    base = _identity_row()
    changed = copy.deepcopy(base)
    changed[field] = value
    rebuilt = build_executable_instance_fields(changed)
    assert rebuilt["executable_instance_hash_sha256"] != base[
        "executable_instance_hash_sha256"
    ]


def test_identity_ids_are_prefixes_of_full_hashes_and_aliases_are_canonical() -> None:
    row = _identity_row()
    assert row["emission_lineage_id"] == (
        EMISSION_LINEAGE_ID_PREFIX
        + row["emission_lineage_hash_sha256"][:24]
    )
    assert row["executable_instance_id"] == (
        EXECUTABLE_INSTANCE_ID_PREFIX
        + row["executable_instance_hash_sha256"][:24]
    )
    alias = copy.deepcopy(row)
    alias["order_type"] = "BUY_LIMIT"
    assert build_executable_instance_fields(alias)[
        "executable_instance_hash_sha256"
    ] == row["executable_instance_hash_sha256"]


def test_identity_preserves_subsecond_time_and_broker_symbol_punctuation() -> None:
    row = _identity_row()
    later = copy.deepcopy(row)
    later["decision_time_utc"] = "2026-05-26T13:15:00.000001Z"
    assert build_executable_instance_fields(later)[
        "executable_instance_hash_sha256"
    ] != row["executable_instance_hash_sha256"]

    punctuation = copy.deepcopy(row)
    punctuation["symbol"] = "US30_CASH"
    punctuation.update(build_emission_lineage_fields(punctuation))
    assert punctuation["emission_lineage_hash_sha256"] != row[
        "emission_lineage_hash_sha256"
    ]


def test_canonical_identity_rejects_implicit_stringification_and_nonfinite_numbers() -> None:
    with pytest.raises(TypeError):
        canonical_identity_sha256({"unsupported": object()})
    with pytest.raises(ValueError):
        canonical_identity_sha256({"not_a_number": float("nan")})


def test_pending_order_requires_explicit_tif_and_expiry_or_gtc() -> None:
    row = _identity_row()
    no_tif = copy.deepcopy(row)
    no_tif.pop("time_in_force")
    assert "time_in_force" in build_executable_instance_fields(no_tif)[
        "executable_instance_missing_atoms"
    ]

    day = copy.deepcopy(row)
    day["time_in_force"] = "DAY"
    assert "expiry_time_utc_or_gtc" in build_executable_instance_fields(day)[
        "executable_instance_missing_atoms"
    ]
    day["expiry_time_utc"] = "2026-05-26T20:00:00Z"
    assert build_executable_instance_fields(day)[
        "executable_instance_status"
    ] == "materialized"


def test_source_salt_is_policy_outcome_free_and_lineage_ignores_target_stop() -> None:
    candidate = {
        "origin_family": "liquidity_sweep_reclaim",
        "emission_generation_side": "SHORT",
        "symbol": "XAUUSD",
        "candle_open_utc": "2026-05-26T13:00:00Z",
        "emission_source_salt": {"setup": "prior_high_reclaim"},
        "entry_price": 100.0,
        "stop_loss": 101.0,
        "take_profit_1": 98.5,
    }
    before = build_emission_lineage_fields(candidate)
    after = build_emission_lineage_fields(
        {**candidate, "stop_loss": 102.0, "take_profit_1": 95.0}
    )
    assert before["emission_lineage_hash_sha256"] == after[
        "emission_lineage_hash_sha256"
    ]
    with pytest.raises(ValueError, match="forbidden policy/outcome key"):
        build_emission_lineage_fields(
            {**candidate, "emission_source_salt": {"target_rr": 1.5}}
        )


def test_claimed_v1_tamper_and_post_stamp_geometry_mutation_fail_closed() -> None:
    row = _identity_row()
    assert candidate_identity_contract_failures(row) == ()

    tampered = copy.deepcopy(row)
    tampered["executable_instance_hash_sha256"] = "0" * 64
    failures = candidate_identity_contract_failures(tampered)
    assert "executable_instance_hash_sha256_current_projection_mismatch" in failures

    mutated = copy.deepcopy(row)
    mutated["take_profit_1"] = 109.0
    failures = candidate_identity_contract_failures(mutated)
    assert "executable_instance_hash_sha256_current_projection_mismatch" in failures
    assert "executable_instance_atoms_current_projection_mismatch" in failures

    partial_claim = copy.deepcopy(row)
    partial_claim["executable_instance_status"] = "missing_required_atoms"
    assert (
        "executable_instance_status_current_projection_mismatch"
        in candidate_identity_contract_failures(partial_claim)
    )

    assert candidate_identity_contract_failures(
        {"candidate_id": "legacy-only", "take_profit_1": 999.0}
    ) == ()


@pytest.mark.parametrize(
    "field,value",
    [
        ("origin_family", "current_ob_retest"),
        ("symbol", "NAS100"),
        ("emission_generation_side", "SHORT"),
        ("poi_id", "poi-stable-2"),
    ],
)
def test_lineage_validator_rebuilds_from_current_family_and_source(
    field: str,
    value: str,
) -> None:
    row = _identity_row()
    row[field] = value
    failures = candidate_identity_contract_failures(
        row,
        require_emission=True,
        require_executable=True,
    )
    assert "emission_lineage_hash_sha256_current_projection_mismatch" in failures
    assert "emission_lineage_atoms_current_projection_mismatch" in failures


def test_selector_snapshot_uses_shared_non_authoritative_geometry_contract() -> None:
    row = _identity_row()
    fields = build_selector_input_geometry_fields(row)
    assert fields["selector_input_geometry_status"] == "materialized"
    assert fields["selector_input_geometry_sha256"]
    assert fields["selector_input_geometry_atoms"]["take_profit_1"] == 101.5
    assert fields["selector_input_geometry_missing_atoms"] == []


def test_audit_is_json_and_deepcopy_safe_without_changing_candidate_bytes() -> None:
    bars = _bars(close=100.0, width=0.2)
    raw = _raw("US30_CASH", bars)
    breaker = SimpleNamespace(
        zone_low=99.5,
        zone_high=99.9,
        direction="bullish",
        is_retested=False,
        formation_time="2026-05-26T09:00:00Z",
        mitigation_time="2026-05-26T10:00:00Z",
        causing_event="bos",
        original_ob_direction="bearish",
    )
    mso = SimpleNamespace(
        timestamp_utc=raw["candle_close_utc"],
        timeframes={
            "M15": SimpleNamespace(atr_14=1.0, fair_value_gaps=[]),
            "H1": SimpleNamespace(order_blocks=[], breaker_blocks=[breaker]),
        },
    )
    config = {
        "risk": {"min_rr": 1.5, "sl_buffer_atr_multiplier": 0.25},
        "model_a": {"enabled_frameworks": ["breaker_re_entry"]},
        "gate1": {"poi_proximity_tolerance_pct": 0.05},
    }
    without_audit = _run(raw, config=config, symbol="US30_CASH", mso=mso)
    audit: dict = {}
    with_audit = _run(
        raw,
        config=config,
        symbol="US30_CASH",
        mso=mso,
        audit=audit,
    )
    canonical = lambda value: json.dumps(  # noqa: E731
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assert canonical(with_audit) == canonical(without_audit)
    assert len(with_audit) == len(without_audit)
    assert type(audit["current_framework_admission"]["target_rr"]) is float
    assert copy.deepcopy(audit) == audit
    assert json.loads(json.dumps(audit, sort_keys=True)) == audit


def test_forming_bar_is_current_default_and_completed_only_is_explicit() -> None:
    bars = _bars(latest_open="2026-05-26T10:00:00Z")
    bars[-1].update(
        {"open": 100.2, "high": 101.8, "low": 99.9, "close": 100.4}
    )
    raw = _raw("XAUUSD", bars, declared_close="2026-05-26T10:07:00Z")
    default_audit: dict = {}
    _run(
        raw,
        config={"risk": {"min_rr": 1.5}},
        now="2026-05-26T10:07:00Z",
        audit=default_audit,
    )
    closed_audit: dict = {}
    _run(
        raw,
        config={
            "risk": {"min_rr": 1.5},
            RUNTIME_SECTION: {ALLOW_FORMING_BAR_KEY: False},
        },
        now="2026-05-26T10:07:00Z",
        audit=closed_audit,
    )
    assert default_audit["selected_closed_bar"]["selected_via"] == (
        "explicit_forming_bar_research_contract"
    )
    assert default_audit["selected_closed_bar"][
        "selected_bar_completeness_status"
    ] == "forming_bar_explicit_research_mode"
    assert closed_audit["selected_closed_bar"]["selected_via"] == (
        "closed_bar_walkback"
    )
    assert closed_audit["selected_closed_bar"][
        "selected_bar_completeness_status"
    ] == "completed_bar_only"


@pytest.mark.parametrize(
    "decision_time,expected_open",
    [
        # Strictly before the 10:00 bar's close: the stream still contains a
        # row whose completion witness (successor open 10:15) is not observable
        # as-of the decision time.  The merged wave-21 truth contract defines
        # this as a fail-closed source terminal, NOT a silent walk-back to the
        # 09:45 bar — a forming bar in a truth-mode stream is a chronology
        # violation.  (Pre-integration this file asserted the walk-back; the
        # full-system-coherence contract supersedes it.)
        ("2026-05-26T10:14:59.999999Z", None),
        ("2026-05-26T10:15:00Z", "2026-05-26T10:00:00Z"),
        ("2026-05-26T10:15:00.000001Z", "2026-05-26T10:00:00Z"),
    ],
)
def test_truth_mode_completed_bar_boundary_is_exact(
    decision_time: str,
    expected_open: str | None,
) -> None:
    bars = _bars(latest_open="2026-05-26T10:00:00Z")
    raw = _truth_raw("XAUUSD", bars, declared_close="2026-05-26T10:15:00Z")
    audit: dict = {}
    out = _run(
        raw,
        config={
            "risk": {"min_rr": 1.5},
            RUNTIME_SECTION: {WAVE21_FULL_FLOW_TRUTH_MODE_KEY: True},
        },
        now=decision_time,
        audit=audit,
    )
    if expected_open is None:
        assert out == []
        assert audit["status"] == "NOT_EVALUABLE_SOURCE_CHRONOLOGY"
        assert audit["source_terminal"] is True
        assert "completion_witness_adjacency_invalid" in audit[
            "source_terminal_reason"
        ]
        assert "selected_closed_bar" not in audit
        return
    selected = audit["selected_closed_bar"]
    assert selected["selected_closed_bar_open_utc"] == expected_open
    assert selected["forming_bar_excluded_count"] == 0
    assert selected["truth_mode_enabled"] is True
    assert selected["allow_forming_bar"] is False


@pytest.mark.parametrize("future_delta", [timedelta(microseconds=1), timedelta(seconds=1)])
def test_truth_mode_cross_asset_future_leader_asof_has_zero_tolerance(
    future_delta: timedelta,
) -> None:
    """The legacy two-second clock-skew allowance cannot leak into truth mode."""

    lag_rows = _bars(latest_open="2026-05-26T13:00:00Z")
    lag_rows[-1].update(
        {"open": 100.0, "high": 100.4, "low": 99.6, "close": 100.2}
    )
    leader_rows = _bars(
        latest_open="2026-05-26T13:00:00Z",
        close=50.0,
    )
    leader_rows[-3].update(
        {"open": 50.0, "high": 50.5, "low": 49.5, "close": 50.0}
    )
    leader_rows[-2].update(
        {"open": 50.0, "high": 52.4, "low": 49.8, "close": 52.0}
    )
    decision_time = _dt("2026-05-26T13:00:00Z") - future_delta
    lag_series = BarSeries(
        symbol="XAUUSD",
        timeframe="M15",
        bars=tuple(
            Bar(
                time=_dt(row["time"]).replace(tzinfo=None),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
            )
            for row in lag_rows
        ),
        source_path_feature_status="fixture_complete",
        session_windows=SESSION_WINDOWS["XAUUSD"],
        decision_time_utc=decision_time,
    )
    kwargs = {
        "lag_series": lag_series,
        "lag_index": len(lag_series.bars) - 1,
        "target_rr": 1.5,
        "kill_zone": "ny",
        "cross_asset_raw_data": {"XAGUSD": _raw("XAGUSD", leader_rows)},
        "now_utc": _dt("2026-05-26T13:15:00Z"),
        "config": {"risk": {"min_rr": 1.5}},
    }

    # Same source is admitted only by the deliberately retained legacy skew
    # allowance, proving the truth result is the chronology guard and not an
    # unrelated fixture failure.
    assert _generate_cross_asset_candidate(
        **kwargs,
        policy=BroadOriginEmissionPolicy(truth_mode_enabled=False),
    ) is not None
    assert _generate_cross_asset_candidate(
        **kwargs,
        policy=BroadOriginEmissionPolicy(
            truth_mode_enabled=True,
            allow_forming_bar=False,
        ),
    ) is None


def test_24h_session_rename_is_opt_in_and_geometry_is_invariant() -> None:
    bars = _bars(latest_open="2026-05-26T13:00:00Z")
    bars[-1].update(
        {"open": 100.2, "high": 101.8, "low": 99.9, "close": 100.4}
    )
    raw = _raw("BTCUSD", bars)
    base = {"risk": {"min_rr": 1.5}}
    legacy = _family(
        _run(raw, config=base, symbol="BTCUSD"),
        "liquidity_sweep_reclaim",
    )
    continuous = _family(
        _run(
            raw,
            config={
                **base,
                RUNTIME_SECTION: {
                    SESSION_NAMING_KEY: SESSION_NAMING_CONTINUOUS
                },
            },
            symbol="BTCUSD",
        ),
        "liquidity_sweep_reclaim",
    )
    assert legacy["session"] == "off_configured_session"
    assert continuous["session"] == "continuous_24h"
    assert legacy["source_fields"]["session_naming_policy"] == (
        SESSION_NAMING_LEGACY_SENTINEL
    )
    assert continuous["source_fields"]["session_naming_policy"] == (
        SESSION_NAMING_CONTINUOUS
    )
    for field in (
        "candidate_id",
        "entry_price",
        "stop_loss",
        "take_profit_1",
        "emission_lineage_id",
        "executable_instance_id",
    ):
        assert legacy[field] == continuous[field]


def test_breaker_specific_buffer_is_opt_in_and_exact_identity_tracks_geometry() -> None:
    bars = _bars(close=100.0, width=0.2)
    raw = _raw("US30_CASH", bars)
    breaker = SimpleNamespace(
        zone_low=99.5,
        zone_high=99.9,
        direction="bullish",
        is_retested=False,
        formation_time="2026-05-26T09:00:00Z",
        mitigation_time="2026-05-26T10:00:00Z",
        causing_event="bos",
        original_ob_direction="bearish",
    )
    mso = SimpleNamespace(
        timestamp_utc=raw["candle_close_utc"],
        timeframes={
            "M15": SimpleNamespace(atr_14=1.0, fair_value_gaps=[]),
            "H1": SimpleNamespace(order_blocks=[], breaker_blocks=[breaker]),
        },
    )
    base = {
        "risk": {
            "min_rr": 1.5,
            "sl_buffer_atr_multiplier": 0.25,
            "sl_buffer_breaker_atr_multiplier": 0.75,
        },
        "model_a": {"enabled_frameworks": ["breaker_re_entry"]},
        "gate1": {"poi_proximity_tolerance_pct": 0.05},
    }
    legacy = _family(
        _run(raw, config=base, symbol="US30_CASH", mso=mso),
        "current_breaker_re_entry",
    )
    adr006 = _family(
        _run(
            raw,
            config={
                **base,
                RUNTIME_SECTION: {
                    BREAKER_STOP_BUFFER_SOURCE_KEY: BREAKER_BUFFER_ADR006
                },
            },
            symbol="US30_CASH",
            mso=mso,
        ),
        "current_breaker_re_entry",
    )
    assert legacy["source_fields"]["stop_buffer_atr"] == 0.25
    assert legacy["source_fields"]["stop_buffer_source"] == (
        "risk.sl_buffer_atr_multiplier"
    )
    assert adr006["source_fields"]["stop_buffer_atr"] == 0.75
    assert adr006["source_fields"]["stop_buffer_source"] == (
        "risk.sl_buffer_breaker_atr_multiplier"
    )
    assert legacy["candidate_id"] != adr006["candidate_id"]
    assert legacy["emission_lineage_id"] == adr006["emission_lineage_id"]
    assert legacy["stop_loss"] != adr006["stop_loss"]
    def finalized_id(row: dict) -> str:
        final = {
            **row,
            "order_type": row["candidate_order_type_hint"],
            "time_in_force": "GTC",
        }
        return str(build_executable_instance_fields(final)["executable_instance_id"])

    assert finalized_id(legacy) != finalized_id(adr006)


def test_absent_p1_modes_equal_explicit_current_defaults() -> None:
    bars = _bars()
    bars[-1].update(
        {"open": 100.2, "high": 101.8, "low": 99.9, "close": 100.4}
    )
    raw = _raw("XAUUSD", bars)
    implicit = _run(raw, config={"risk": {"min_rr": 1.5}})
    explicit = _run(
        raw,
        config={
            "risk": {"min_rr": 1.5},
            RUNTIME_SECTION: {
                SESSION_NAMING_KEY: SESSION_NAMING_LEGACY_SENTINEL,
                BREAKER_STOP_BUFFER_SOURCE_KEY: BREAKER_BUFFER_LEGACY_GENERIC,
                ALLOW_FORMING_BAR_KEY: True,
            },
        },
    )
    assert implicit == explicit
