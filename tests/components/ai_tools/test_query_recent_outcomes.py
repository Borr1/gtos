"""Tests for Tool A — query_recent_trade_outcomes (DESIGN.md §2.1).

Per memory project_pytest_contamination_forensics.md, all paths are
tmp_path-rooted; no module-level constants are mutated without
monkeypatch on the module reference.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.components.ai_tools.query_recent_outcomes import (
    QueryRecentTradeOutcomesTool,
    _wilson_ci,
    query_recent_trade_outcomes,
)


def _write_record(
    root: Path,
    symbol: str,
    candle_dt: datetime,
    realized_R: float | None,
    direction: str = "LONG",
    framework: str = "ob_retest",
    has_exit: bool = True,
) -> Path:
    """Helper — write a synthetic trade-record JSON in A3 v1.1 schema."""
    sym_dir = root / symbol
    sym_dir.mkdir(parents=True, exist_ok=True)
    fp = sym_dir / f"{candle_dt.strftime('%Y-%m-%d_%H%M')}.json"
    record = {
        "metadata": {
            "trade_id": fp.stem,
            "date": candle_dt.date().isoformat(),
            "symbol": symbol,
            "kill_zone": "ny",
            "candle_time": candle_dt.isoformat(),
            "capture_version": "1.1",
            "system_version": "test",
        },
        "decision_pipeline": {"final_outcome": "FILLED"},
        "trade_parameters": {"direction": direction},
        "ai_response": {"framework": framework},
        "exit": {"realized_R": realized_R} if has_exit else None,
    }
    fp.write_text(json.dumps(record), encoding="utf-8")
    return fp


# ── Wilson CI ────────────────────────────────────────────────────────


def test_wilson_zero_n():
    lo, hi = _wilson_ci(0, 0)
    assert lo == 0.0 and hi == 1.0


def test_wilson_typical_case():
    # 50% WR over 30 trades — CI should bracket 0.5 narrowly
    lo, hi = _wilson_ci(15, 30)
    assert 0.30 < lo < 0.40
    assert 0.60 < hi < 0.70


def test_wilson_extreme_high_wr():
    lo, hi = _wilson_ci(10, 10)  # 100% WR
    assert lo > 0.6  # CI lower-bound for 10/10 is ~0.72
    assert hi == pytest.approx(1.0)  # may be 0.9999... after float arithmetic


# ── query_recent_trade_outcomes ───────────────────────────────────────


def test_unknown_symbol_returns_error(tmp_path: Path):
    out = query_recent_trade_outcomes("NOTASYMBOL", trade_records_root=tmp_path)
    assert out["error"] == "unknown_symbol"


def test_days_back_out_of_range(tmp_path: Path):
    out_lo = query_recent_trade_outcomes("XAUUSD", days_back=3,
                                         trade_records_root=tmp_path)
    out_hi = query_recent_trade_outcomes("XAUUSD", days_back=200,
                                         trade_records_root=tmp_path)
    assert out_lo["error"] == "days_back_out_of_range"
    assert out_hi["error"] == "days_back_out_of_range"


def test_no_records_dir_returns_zero_clean(tmp_path: Path):
    out = query_recent_trade_outcomes("XAUUSD", trade_records_root=tmp_path)
    assert out["n_trades"] == 0
    assert out["win_rate"] is None
    assert out["exp_R"] is None
    assert out["last_5_outcomes"] == []


def test_empty_dir_returns_zero(tmp_path: Path):
    (tmp_path / "XAUUSD").mkdir()
    out = query_recent_trade_outcomes("XAUUSD", trade_records_root=tmp_path)
    assert out["n_trades"] == 0


def test_filters_out_unfilled_records(tmp_path: Path):
    now = datetime.now(timezone.utc)
    # Two records: one filled with R, one unfilled.
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=1), 1.5)
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=2),
                  None, has_exit=False)
    out = query_recent_trade_outcomes("XAUUSD", trade_records_root=tmp_path,
                                      now=now)
    assert out["n_trades"] == 1
    assert out["win_rate"] == 1.0


def test_window_cutoff_excludes_old_records(tmp_path: Path):
    now = datetime.now(timezone.utc)
    # Inside window
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=5), 1.5)
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=10), -1.0)
    # Outside window
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=40), -1.0)
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=50), -1.0)
    out = query_recent_trade_outcomes("XAUUSD", days_back=30,
                                      trade_records_root=tmp_path, now=now)
    assert out["n_trades"] == 2
    assert out["win_rate"] == 0.5


def test_direction_filter(tmp_path: Path):
    now = datetime.now(timezone.utc)
    _write_record(tmp_path, "USDJPY", now - timedelta(days=1), 1.0,
                  direction="LONG")
    _write_record(tmp_path, "USDJPY", now - timedelta(days=2), -1.0,
                  direction="SHORT")
    _write_record(tmp_path, "USDJPY", now - timedelta(days=3), 1.5,
                  direction="LONG")
    out_long = query_recent_trade_outcomes("USDJPY", direction="LONG",
                                           trade_records_root=tmp_path, now=now)
    out_short = query_recent_trade_outcomes("USDJPY", direction="SHORT",
                                            trade_records_root=tmp_path, now=now)
    assert out_long["n_trades"] == 2 and out_long["win_rate"] == 1.0
    assert out_short["n_trades"] == 1 and out_short["win_rate"] == 0.0


def test_framework_filter(tmp_path: Path):
    now = datetime.now(timezone.utc)
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=1), 1.5,
                  framework="ob_retest")
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=2), 1.0,
                  framework="fvg_fill")
    out = query_recent_trade_outcomes("XAUUSD", framework="ob_retest",
                                      trade_records_root=tmp_path, now=now)
    assert out["n_trades"] == 1
    assert out["last_5_outcomes"][0]["framework"] == "ob_retest"


def test_outcome_clipping_protects_expectancy(tmp_path: Path):
    """Per memory project_distributional_findings.md, R is clipped to ±5R."""
    now = datetime.now(timezone.utc)
    # 10R outlier should clip to 5R; expectancy = (5 + -1 + -1) / 3 = 1.0
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=1), 10.0)
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=2), -1.0)
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=3), -1.0)
    out = query_recent_trade_outcomes("XAUUSD", trade_records_root=tmp_path,
                                      now=now)
    assert out["n_trades"] == 3
    # exp_R should be 1.0, not 2.67 (which the un-clipped average would be)
    assert out["exp_R"] == 1.0


def test_last_5_outcomes_chronological(tmp_path: Path):
    now = datetime.now(timezone.utc)
    # Write 7 records — last_5 should be the 5 most-recent
    for i in range(7):
        _write_record(tmp_path, "XAUUSD", now - timedelta(days=7 - i),
                      float(i))
    out = query_recent_trade_outcomes("XAUUSD", trade_records_root=tmp_path,
                                      now=now)
    assert len(out["last_5_outcomes"]) == 5
    # Chronological — last entry should have R=6.0 (clipped to 5.0) but
    # last_5_outcomes stores raw R, which is 6.0 (un-clipped).
    rs = [o["R"] for o in out["last_5_outcomes"]]
    assert rs[-1] == 6.0
    # Should NOT include the day-7-ago record (R=0)
    assert 0.0 not in rs


def test_wilson_ci_in_output(tmp_path: Path):
    now = datetime.now(timezone.utc)
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=1), 1.5)
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=2), -1.0)
    out = query_recent_trade_outcomes("XAUUSD", trade_records_root=tmp_path,
                                      now=now)
    assert "wilson_95ci" in out
    lo, hi = out["wilson_95ci"]
    assert 0.0 <= lo <= 0.5 <= hi <= 1.0


def test_corrupt_json_skipped_silently(tmp_path: Path):
    now = datetime.now(timezone.utc)
    _write_record(tmp_path, "XAUUSD", now - timedelta(days=1), 1.5)
    # Add a corrupt file
    (tmp_path / "XAUUSD" / "garbage.json").write_text("not json", encoding="utf-8")
    out = query_recent_trade_outcomes("XAUUSD", trade_records_root=tmp_path,
                                      now=now)
    assert out["n_trades"] == 1


def test_tool_class_exposes_anthropic_def():
    tool = QueryRecentTradeOutcomesTool()
    d = tool.to_anthropic_tool_def()
    assert d["name"] == "query_recent_trade_outcomes"
    assert "Use when uncertain" in d["description"]
    assert d["input_schema"]["type"] == "object"
    assert "symbol" in d["input_schema"]["required"]
