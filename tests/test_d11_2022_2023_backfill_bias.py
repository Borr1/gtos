from __future__ import annotations

import csv
import json

from scripts import analyze_d11_2022_2023_backfill_bias as mod


def test_period_label_parses_expected_year_buckets():
    assert mod.period_label(mod.parse_dt("2022-01-01T00:00:00+00:00")) == "2022-2023"
    assert mod.period_label(mod.parse_dt("2024-12-31 23:00:00")) == "2024-2025"
    assert mod.period_label(mod.parse_dt("2026-05-01T00:00:00Z")) == "2026"


def test_summarize_ohlc_rows_flags_invalid_and_duplicates():
    ts = mod.parse_dt("2022-01-01T00:00:00+00:00")
    rows = [
        {"time": ts, "open": 1.0, "high": 1.2, "low": 0.9, "close": 1.1, "volume": 10.0},
        {"time": ts, "open": 1.0, "high": 0.8, "low": 0.9, "close": 1.1, "volume": 0.0},
        {"time": mod.parse_dt("2022-01-01T00:15:00+00:00"), "open": 1.1, "high": 1.1, "low": 1.1, "close": 1.1, "volume": 5.0},
    ]

    out = mod.summarize_ohlc_rows(rows)

    assert out["rows"] == 3
    assert out["duplicate_timestamps"] == 1
    assert out["invalid_ohlc_rows"] == 1
    assert out["zero_range_rows"] == 1
    assert out["nonpositive_volume_rows"] == 1


def test_load_mechanical_jsonl_events_preserves_ambiguous_state(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(
        json.dumps(
            {
                "bos": {"symbol": "XAUUSD", "bos_time": "2022-01-05T04:00:00+00:00", "direction": "LONG"},
                "ob_retest": {
                    "bos_id": "XAUUSD|2022-01-05T04:00:00+00:00",
                    "outcome": "SAME_BAR",
                    "skip_reason": "FILL_AND_TPSL_SAME_BAR",
                    "realized_r": None,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    events = mod.load_mechanical_jsonl_events(path, source_name="test")
    summary = mod.summarize_event_population(events)

    assert events[0]["period"] == "2022-2023"
    assert summary["same_bar_or_ambiguous"] == 1
    assert summary["filled_resolved"] == 0


def test_label_coverage_flags_ohlc_present_without_labels():
    old_rows = [{"symbol": "XAUUSD"}]
    ohlc = {
        "old_m15_summary": [
            {"symbol": "XAUUSD", "rows": 2000},
            {"symbol": "GBPJPY", "rows": 2000},
        ],
        "coverage_flags": [],
    }

    flags = mod.label_coverage_flags(old_rows, ohlc)

    assert {
        "symbol": "GBPJPY",
        "flag": "OHLC_PRESENT_BUT_OLD_MECHANICAL_LABELS_MISSING",
        "m15_rows_2022_2023": 2000,
    } in flags


def test_build_payload_preserves_no_promotion_and_missing_label_flag(tmp_path, monkeypatch):
    old_csv = tmp_path / "old.csv"
    with old_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["trade_id", "date_iso", "symbol", "direction_long_short", "kill_zone", "realized_r", "source"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "trade_id": "a",
                "date_iso": "2022-01-01T00:00:00+00:00",
                "symbol": "XAUUSD",
                "direction_long_short": "LONG",
                "kill_zone": "other",
                "realized_r": "1.5",
                "source": "f11_mechanical",
            }
        )
    old_jsonl = tmp_path / "old.jsonl"
    old_jsonl.write_text(
        json.dumps(
            {
                "bos": {"symbol": "XAUUSD", "bos_time": "2022-01-01T00:00:00+00:00", "direction": "LONG"},
                "ob_retest": {"outcome": "TP", "realized_r": 1.5},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    recent_jsonl = tmp_path / "recent.jsonl"
    recent_jsonl.write_text(
        json.dumps(
            {
                "bos": {"symbol": "XAUUSD", "bos_time": "2026-01-01T00:00:00+00:00", "direction": "LONG"},
                "ob_retest": {"outcome": "SL", "realized_r": -1.0},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    trade_index = tmp_path / "trade_index.json"
    trade_index.write_text(json.dumps({"trades": []}), encoding="utf-8")
    empty_jsonl = tmp_path / "empty.jsonl"
    empty_jsonl.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        mod,
        "build_ohlc_audit",
        lambda: {
            "rows": [],
            "old_m15_summary": [{"symbol": "XAUUSD", "rows": 2000}, {"symbol": "GBPJPY", "rows": 2000}],
            "coverage_flags": [],
        },
    )

    payload = mod.build_payload(
        old_trade_csv=old_csv,
        old_trade_jsonl=old_jsonl,
        recent_f11_population=recent_jsonl,
        trade_index_path=trade_index,
        old_regime_backfill=empty_jsonl,
        recent_regime_backfill=empty_jsonl,
        live_regime_log=empty_jsonl,
    )

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["bias_readout"]["headline_verdict"] == "USABLE_WITH_DOWNSAMPLING_AND_SOURCE_FLAGS_NOT_LIVE_EQUIVALENT"
    assert any(flag["symbol"] == "GBPJPY" for flag in payload["bias_readout"]["label_bias_flags"])
