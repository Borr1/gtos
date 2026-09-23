from __future__ import annotations

import gzip
import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_full_historical_candidate_generation_replay_2026_05_24/"
    "build_vnext_full_replay_stage02_candidate_generation_2026_05_24.py"
)


def load_stage02_module():
    spec = importlib.util.spec_from_file_location("vnext_full_stage02", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _config():
    return {
        "risk": {
            "min_rr": 1.5,
            "sl_buffer_atr_multiplier": 0.25,
            "sl_buffer_breaker_atr_multiplier": 0.5,
            "sl_buffer_min_ticks": 5,
        },
        "data": {
            "swing_detection_min_bars": {"M15": 2},
            "fvg_min_gap": {"M15": 0.25},
        },
        "instruments": {
            "XAUUSD": {
                "market": {"tick_size": 0.01},
                "data": {"fvg_min_gap": {"M15": 0.25}},
            }
        },
    }


def _denom(row_id: str, ts: str) -> dict:
    return {
        "source_universe_row_id": row_id,
        "source_origin": "market_bar_enumeration",
        "source_id": "csvsrc_test",
        "source_path": "data/test/XAUUSD_M15.csv",
        "source_sha256": "abc123",
        "source_mode": "OHLC_M15_CSV",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "timeframe": "M15",
        "candle_time_utc": ts,
        "date_utc": ts[:10],
        "session_bucket": "london_broad",
    }


def test_generate_source_rows_emits_fvg_candidate_and_skip_from_market_bars():
    stage02 = load_stage02_module()
    candles = [
        {"time": "2026-05-01 07:00:00", "open": 10.0, "high": 10.0, "low": 9.0, "close": 9.5, "volume": 1},
        {"time": "2026-05-01 07:15:00", "open": 10.0, "high": 11.0, "low": 9.8, "close": 10.8, "volume": 1},
        {"time": "2026-05-01 07:30:00", "open": 12.0, "high": 13.0, "low": 12.0, "close": 12.5, "volume": 1},
        {"time": "2026-05-01 07:45:00", "open": 12.4, "high": 12.6, "low": 11.5, "close": 12.1, "volume": 1},
    ]
    denominator_rows = [
        _denom("denom_skip", "2026-05-01 07:00:00"),
        _denom("denom_fvg", "2026-05-01 07:45:00"),
    ]

    rows = list(
        stage02.generate_source_rows(
            candles=candles,
            denominator_rows=denominator_rows,
            config=_config(),
            coverage_index={"XAUUSD": []},
        )
    )

    candidates = [row for row_type, row in rows if row_type == "candidate_generation"]
    dispositions = [row for row_type, row in rows if row_type == "denominator_disposition"]
    explanations = [row for row_type, row in rows if row_type == "decision_explanation"]

    assert len(candidates) == 1
    assert candidates[0]["framework"] == "fvg_fill"
    assert candidates[0]["source_origin"] == "market_bar_enumeration"
    assert candidates[0]["source_universe_row_id"] == "denom_fvg"
    assert candidates[0]["entry_reference"] > candidates[0]["stop_or_invalidation"]
    assert candidates[0]["target_reference"] > candidates[0]["entry_reference"]
    assert {row["candidate_generation_disposition"] for row in dispositions} == {
        "candidate_generated",
        "no_setup_by_asof_market_state",
    }
    assert all(row["lookback_bars"] == 672 for row in dispositions)
    assert all(row["asof_window_start"] == 0 for row in dispositions)
    assert all(
        row["warmup_context_sufficiency_status"]
        == "warmup_context_limited_before_full_m15_lookback"
        for row in dispositions
    )
    assert all(row["denominator_enters_stage02_candidate_denominator"] is False for row in dispositions)
    assert any(row["skip_reason"] == "context_limited_no_setup_not_production_like_denominator" for row in dispositions)
    assert any(row["runtime_trace"]["pre_ai_route_decision"] == "NO_RUNTIME_FUNCTION" for row in explanations)


def test_candidate_required_fields_have_stage02_values():
    stage02 = load_stage02_module()
    denom = _denom("denom_required", "2026-05-01 07:45:00")
    candidate = stage02.candidate_row(
        _config(),
        denom=denom,
        packet_id="msp_test",
        framework="ob_retest",
        side="LONG",
        zone={
            "zone_id": "ob_test",
            "zone_low": 10.0,
            "zone_high": 12.0,
            "formation_time": "2026-05-01 07:00:00",
            "causing_event_type": "BOS",
            "causing_event_time": "2026-05-01 07:30:00",
            "causing_event_index": 2,
            "touch_count_at_candidate": 1,
            "setup_type": "order_block_retest",
            "poi_type": "ob_retest",
        },
        candle_index=3,
        atr_14=1.0,
        market_state_summary={"market_state_status": "asof_built"},
        path_modes=[],
    )

    required = {
        "candidate_id",
        "source_origin",
        "source_universe_row_id",
        "symbol",
        "source_symbol",
        "timeframe",
        "candle_time_utc",
        "session_bucket",
        "side",
        "framework",
        "entry_reference",
        "stop_or_invalidation",
        "target_reference",
        "market_state_packet_id",
        "source_path",
        "source_sha256",
    }
    assert required <= set(candidate)
    assert all(candidate[field] not in (None, "", [], {}) for field in required)
    assert candidate["rr"] >= 1.5
    assert candidate["sl_buffer_used"] > 0


def test_jsonl_gzip_chunk_writer_writes_reconstructable_index(tmp_path):
    stage02 = load_stage02_module()
    logical = tmp_path / "ledger.jsonl"
    with stage02.JsonlGzipChunkWriter(logical, rows_per_chunk=2) as writer:
        for i in range(5):
            writer.write({"i": i, "source_origin": "market_bar_enumeration"})

    index_rows = [json.loads(line) for line in logical.read_text(encoding="utf-8").splitlines()]
    assert [row["row_count"] for row in index_rows] == [2, 2, 1]

    reconstructed = []
    for row in index_rows:
        with gzip.open(tmp_path / Path(row["chunk_path"]).name, "rt", encoding="utf-8") as handle:
            reconstructed.extend(json.loads(line)["i"] for line in handle)
    assert reconstructed == [0, 1, 2, 3, 4]


def test_market_state_and_disposition_rows_carry_lookback_context():
    stage02 = load_stage02_module()
    denom = _denom("denom_context", "2026-05-01 07:45:00")
    summary = {
        "market_state_status": "asof_built",
        "lookback_bars": 672,
        "asof_window_start": 0,
        "asof_window_end": 3,
        "asof_window_start_time_utc": "2026-05-01 07:00:00",
        "asof_window_end_time_utc": "2026-05-01 07:45:00",
        "prior_m15_context_bars": 3,
        "production_context_required_prior_m15_bars": 671,
        "enough_prior_m15_context_for_production_like_decision": False,
        "warmup_context_sufficiency_status": "warmup_context_limited_before_full_m15_lookback",
        "warmup_context_handling": "explicit_context_limited_row_not_silent_true_no_setup",
    }

    packet = stage02.market_state_packet_row(
        denom=denom,
        packet_id="msp_context",
        candle_index=3,
        market_state_summary=summary,
        path_modes=[],
    )
    disposition = stage02.disposition_row(
        denom=denom,
        packet_id="msp_context",
        disposition="no_setup_by_asof_market_state",
        candidate_ids=[],
        frameworks=[],
        market_state_summary=summary,
        path_modes=[],
        skip_reason="context_limited_no_setup_not_production_like_denominator",
    )

    for field in stage02.LOOKBACK_CONTEXT_FIELDS:
        assert field in packet
        assert field in disposition
    assert disposition["denominator_enters_stage02_candidate_denominator"] is False
    assert (
        disposition["denominator_context_sensitivity"]
        == "warmup_context_limited_excluded_from_production_like_stage02_density_denominator"
    )
