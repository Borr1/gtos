from __future__ import annotations

import csv
import datetime as dt
import json

from scripts.research import build_d11_missing_old_labels as mod


def _bos(symbol: str = "GBPJPY") -> mod.BOSEvent:
    return mod.BOSEvent(
        symbol=symbol,
        bos_time=dt.datetime(2022, 1, 3, 8, 0, tzinfo=dt.timezone.utc),
        bos_index=10,
        direction="LONG",
        swing_level_broken=151.2,
        swing_time=dt.datetime(2022, 1, 3, 6, 0, tzinfo=dt.timezone.utc),
        anchor_swing_price=150.0,
        anchor_swing_time=dt.datetime(2022, 1, 3, 5, 0, tzinfo=dt.timezone.utc),
        anchor_swing_index=7,
        bos_close=151.5,
        bos_high=151.7,
        bos_low=150.9,
        atr_at_bos=0.4,
        ob_high=150.8,
        ob_low=150.2,
        ob_index=8,
        ob_time=dt.datetime(2022, 1, 3, 7, 0, tzinfo=dt.timezone.utc),
    )


def test_normalize_symbol_preserves_us30_cash_canonical():
    assert mod.normalize_symbol("US30_cash") == "US30_cash"
    assert mod.normalize_symbol("US30_CASH") == "US30_cash"
    assert mod.symbol_file_stem("US30_cash") == "US30_cash"


def test_build_missing_labels_uses_local_sources_and_keeps_source_flags(tmp_path, monkeypatch):
    source_dir = tmp_path / "historical"
    source_dir.mkdir()
    for stem in ("GBPJPY", "US30_cash"):
        (source_dir / f"{stem}_H1.csv").write_text("time,open,high,low,close,volume\n", encoding="utf-8")
        (source_dir / f"{stem}_M15.csv").write_text("time,open,high,low,close,volume\n", encoding="utf-8")

    def fake_extract(path, *, symbol, start, end):
        return [_bos(symbol)]

    def fake_outcome(bos, h1_path, *, m15_ohlcv_dir):
        return mod.Outcome(
            bos_id=f"{mod.normalize_symbol(bos.symbol)}|{bos.bos_time.isoformat()}",
            strategy="ob_retest",
            skip_reason=None,
            entry=150.7,
            sl=150.1,
            tp=151.6,
            rr=1.5,
            outcome="TP",
            realized_r=1.5,
            bars_in_trade=4,
            exit_time="2022-01-03T09:00:00+00:00",
        )

    monkeypatch.setattr(mod, "extract_bos_events", fake_extract)
    monkeypatch.setattr(mod, "find_ob_retest_outcome", fake_outcome)

    payload = mod.build_missing_labels(source_dir=source_dir, regime_path=tmp_path / "missing.jsonl")

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["source_flags"]["mechanical_vs_live_like"] == "mechanical_f11_ob_retest_filled_only"
    assert payload["total_filled"] == 2
    assert {row["symbol"] for row in payload["csv_rows"]} == {"GBPJPY", "US30_cash"}
    assert all(row["source"] == "f11_mechanical_d11_missing_old_labels" for row in payload["csv_rows"])


def test_write_outputs_refuses_overwrite_and_writes_reports(tmp_path):
    payload = {
        "schema_version": "test",
        "generated_at_utc": "2026-05-03T00:00:00+00:00",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "hypothesis_before_outputs": "test hypothesis",
        "source_flags": {"source_period": "old", "mechanical_vs_live_like": "mechanical"},
        "symbol_summaries": {
            "GBPJPY": {
                "status": "OK",
                "bos": 1,
                "filled": 1,
                "no_entry": 0,
                "skipped": 0,
                "h1_path": "h1",
                "m15_path": "m15",
            }
        },
        "total_bos": 1,
        "total_jsonl_rows": 1,
        "total_filled": 1,
        "jsonl_rows": [{"bos": {"symbol": "GBPJPY"}, "ob_retest": {"outcome": "TP"}}],
        "csv_rows": [
            {
                "trade_id": "a",
                "source": "f11_mechanical_d11_missing_old_labels",
                "date_iso": "2022-01-03T08:00:00+00:00",
                "symbol": "GBPJPY",
                "instrument_class": "fx",
                "direction_long_short": "LONG",
                "kill_zone": "london",
                "hour_utc": 8,
                "day_of_week": 0,
                "framework": "ob_retest",
                "setup_grade": "",
                "regime_tag": "",
                "counter_direction_flag": 0,
                "ob_distance_atr": 0.0,
                "ob_age_candles": 4,
                "displacement_quality_score": 0.5,
                "fvg_present": 0,
                "touch_count": 0,
                "ai_confidence": -1,
                "walk_level_signal": -1,
                "cross_instrument_xau_dir": "",
                "realized_r": 1.5,
                "win_label": 1,
            }
        ],
    }

    paths = mod.write_outputs(
        payload,
        output_dir=tmp_path,
        label_stem="labels",
        report_json=tmp_path / "report.json",
        report_md=tmp_path / "report.md",
    )

    with paths["csv"].open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    report = json.loads(paths["report_json"].read_text(encoding="utf-8"))

    assert rows[0]["symbol"] == "GBPJPY"
    assert report["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert "DONE_SUPPLEMENT_GENERATED" in paths["report_md"].read_text(encoding="utf-8")

    try:
        mod.write_outputs(
            payload,
            output_dir=tmp_path,
            label_stem="labels",
            report_json=tmp_path / "report.json",
            report_md=tmp_path / "report.md",
        )
    except FileExistsError as exc:
        assert "Refusing to overwrite" in str(exc)
    else:
        raise AssertionError("expected FileExistsError")
