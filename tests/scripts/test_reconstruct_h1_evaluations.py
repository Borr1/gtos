"""F8 — Tests for ``scripts/research/reconstruct_h1_evaluations.py``.

Coverage targets (F8 brief: at least 6 tests):

  1. parse_log_file: synthetic log with a single complete cycle yields
     one CandleEval with correct entry/SL/TP1, kill_zone, ai_called.
  2. parse_log_file: pre-screen FAILED yields a record with
     ``pre_screen_fail`` set and ``ai_called=False`` and decision=NO_TRADE.
  3. parse_log_file: malformed log lines (no timestamp, junk text) are
     skipped gracefully without crashing parse_errors.
  4. parse_log_file: missing AI response (only Processing candle +
     align_score, no httpx + no TP1 line) yields a no-signal cycle that
     is filtered out (not yielded).
  5. parse_log_file: missing MSO input — a TP1 placement WITHOUT a prior
     L2_verification or displacement still yields a CandleEval with
     entry/SL/TP1 (we don't require MSO presence to emit).
  6. _existing_eval_keys: dedup set built from a synthetic
     live_evaluations dir contains the (symbol, candle_time_minute) keys.
  7. reconstruct: end-to-end → JSONL files written, deduped against an
     existing canonical record, dry-run mode does NOT write.
  8. CandleEval.synth_overall_reasoning: contains AI prices in a format
     that B7 ``_extract_text_prices`` would pattern-match.
  9. _extract_symbol_from_filename: ``agent_US30_cash_demo.log`` →
     ``"US30_cash"`` (preserve underscore + lowercase suffix).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List

import pytest

from scripts.research.reconstruct_h1_evaluations import (
    CandleEval,
    ParseStats,
    _existing_eval_keys,
    _extract_symbol_from_filename,
    _list_log_files,
    parse_log_file,
    reconstruct,
)


SYNTHETIC_LOG_FULL_CYCLE = """\
2026-04-15 21:15:52,643 INFO [src.components.orchestrator] Processing candle - ny KZ
2026-04-15 21:15:52,741 INFO [src.components.orchestrator] Align score: 3/4 bullish (D1=transitional, H4=bullish, H1=bullish, M15=bullish)
2026-04-15 21:15:52,741 INFO [src.components.orchestrator] Deterministic bias: bullish (source=H4+H1_consensus)
2026-04-15 21:16:09,202 INFO [httpx] HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
2026-04-15 21:16:09,210 WARNING [src.components.primary_analyzer] TP1 placement warning: TP1 at 1.50R (entry=4777.43000, SL=4762.14000, TP1=4800.36500). Minimum should be 2.0R. Safety check will reject this trade.
2026-04-15 21:16:09,241 INFO [src.components.proximity_shadow_logger] PROXIMITY_SHADOW: trade=unknown proximity=far dist_atr=6.43
2026-04-15 21:16:09,242 INFO [src.components.verification] L2 verification FAILED: sl_beyond_ob - SL 4762.14 is NOT below OB low 4762.14 for LONG trade
2026-04-15 21:16:09,268 INFO [src.components.trade_capture] Trade record saved: knowledge_base\\trade_records\\XAUUSD\\2026-04-15_ny_1315.json
2026-04-15 21:30:05,000 INFO [src.components.orchestrator] Processing candle - ny KZ
2026-04-15 21:30:05,059 INFO [src.components.orchestrator] Align score: 3/4 bullish (D1=transitional, H4=bullish, H1=bullish, M15=bullish)
2026-04-15 21:30:23,001 INFO [httpx] HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
2026-04-15 21:30:23,004 WARNING [src.components.primary_analyzer] TP1 placement warning: TP1 at 1.50R (entry=4778.50000, SL=4763.00000, TP1=4800.00000). Minimum should be 2.0R. Safety check will reject this trade.
2026-04-15 21:30:23,027 WARNING [src.components.verification] Displacement ratio mismatch: AI=4.50 MSO=3.60
"""

SYNTHETIC_LOG_PRE_SCREEN_FAIL = """\
2026-04-13 17:15:00,000 INFO [src.components.orchestrator] Processing candle - ny KZ
2026-04-13 17:15:00,059 INFO [src.components.orchestrator] Align score: 2/4 bullish (D1=bearish, H4=bullish, H1=bullish, M15=bullish)
2026-04-13 17:15:47,602 INFO [src.components.orchestrator] Pre-screen FAILED: L2_h4_conflict_bullish_vs_d1_bearish
"""

SYNTHETIC_LOG_NO_AI_NO_PRESCREEN = """\
2026-04-13 18:00:00,000 INFO [src.components.orchestrator] Processing candle - ny KZ
2026-04-13 18:00:00,500 INFO [src.components.orchestrator] Align score: 4/4 bullish (D1=bullish, H4=bullish, H1=bullish, M15=bullish)
"""

SYNTHETIC_LOG_TP1_ONLY_NO_DISPLACEMENT = """\
2026-04-15 22:15:05,000 INFO [src.components.orchestrator] Processing candle - ny KZ
2026-04-15 22:15:24,624 INFO [httpx] HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
2026-04-15 22:15:24,625 WARNING [src.components.primary_analyzer] TP1 placement warning: TP1 at 1.50R (entry=4777.43000, SL=4761.19000, TP1=4801.79000). Minimum should be 2.0R. Safety check will reject this trade.
"""

SYNTHETIC_LOG_GARBAGE_LINES = """\
junk junk junk no timestamp here
2026-04-13 17:15:00 GARBAGE_NO_LEVEL [src.components.orchestrator] Bad line
2026-04-13 17:15:00,000 INFO [src.components.orchestrator] Processing candle - ny KZ
   continuation line with no prefix
not a date 17:15:47,602 INFO [src.components.orchestrator] Pre-screen FAILED: junk_reason
2026-04-13 17:15:47,602 INFO [src.components.orchestrator] Pre-screen FAILED: junk_reason
"""


@pytest.fixture
def synthetic_log_dir(tmp_path: Path) -> Path:
    d = tmp_path / "logs"
    d.mkdir()
    return d


def _write_log(dir_path: Path, name: str, content: str) -> Path:
    p = dir_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_parse_full_cycle_extracts_all_fields(synthetic_log_dir: Path) -> None:
    """Test 1: full evaluation cycle yields a complete CandleEval."""
    p = _write_log(synthetic_log_dir, "agent_XAUUSD.log", SYNTHETIC_LOG_FULL_CYCLE)
    stats = ParseStats()
    cycles = list(parse_log_file(p, start_dt=None, end_dt=None, stats=stats))

    # Two complete cycles in the fixture.
    assert len(cycles) == 2
    first = cycles[0]
    assert first.symbol == "XAUUSD"
    assert first.kill_zone == "ny"
    assert first.daily_bias_direction == "bullish"
    assert first.daily_bias_source == "H4+H1_consensus"
    assert first.align_score == 3
    assert first.align_total == 4
    assert first.ai_called is True
    assert first.ai_http_status == 200
    assert first.entry_price == pytest.approx(4777.43, rel=1e-6)
    assert first.stop_loss == pytest.approx(4762.14, rel=1e-6)
    assert first.take_profit_1 == pytest.approx(4800.365, rel=1e-6)
    assert first.l2_fail_rule == "sl_beyond_ob"
    assert first.l2_sl_value == pytest.approx(4762.14, rel=1e-6)
    assert first.l2_ob_value == pytest.approx(4762.14, rel=1e-6)
    assert first.proximity == "far"
    assert first.dist_atr == pytest.approx(6.43, rel=1e-6)
    assert first.trade_record_path == "XAUUSD/2026-04-15_ny_1315.json"
    assert first.derive_decision() == "CANDIDATE"

    second = cycles[1]
    assert second.displacement_ai == pytest.approx(4.50, rel=1e-6)
    assert second.displacement_mso == pytest.approx(3.60, rel=1e-6)
    assert second.derive_decision() == "CANDIDATE"

    assert stats.candles_started == 2
    assert stats.parse_errors == 0


def test_pre_screen_fail_yields_no_trade(synthetic_log_dir: Path) -> None:
    """Test 2: pre-screen FAILED → record with NO_TRADE decision."""
    p = _write_log(synthetic_log_dir, "agent_XAUUSD.log", SYNTHETIC_LOG_PRE_SCREEN_FAIL)
    cycles = list(parse_log_file(p, start_dt=None, end_dt=None))
    assert len(cycles) == 1
    c = cycles[0]
    assert c.pre_screen_fail == "L2_h4_conflict_bullish_vs_d1_bearish"
    assert c.ai_called is False
    assert c.entry_price is None
    assert c.derive_decision() == "NO_TRADE"
    assert c.has_useful_signal is True


def test_no_ai_no_prescreen_filtered_out(synthetic_log_dir: Path) -> None:
    """Test 3: cycle with only align_score (no AI, no pre-screen, no TP1) is dropped."""
    p = _write_log(
        synthetic_log_dir, "agent_XAUUSD.log", SYNTHETIC_LOG_NO_AI_NO_PRESCREEN,
    )
    stats = ParseStats()
    cycles = list(parse_log_file(p, start_dt=None, end_dt=None, stats=stats))
    # Cycle started but no useful signal → not yielded.
    assert len(cycles) == 0
    assert stats.candles_started == 1
    assert stats.candles_no_signal == 1


def test_tp1_only_no_displacement_still_yields_candidate(
    synthetic_log_dir: Path,
) -> None:
    """Test 4: AI emitted entry/SL/TP1 with no displacement check still yields CANDIDATE."""
    p = _write_log(
        synthetic_log_dir, "agent_XAUUSD.log", SYNTHETIC_LOG_TP1_ONLY_NO_DISPLACEMENT,
    )
    cycles = list(parse_log_file(p, start_dt=None, end_dt=None))
    assert len(cycles) == 1
    c = cycles[0]
    assert c.entry_price == pytest.approx(4777.43, rel=1e-6)
    assert c.stop_loss == pytest.approx(4761.19, rel=1e-6)
    assert c.take_profit_1 == pytest.approx(4801.79, rel=1e-6)
    assert c.derive_decision() == "CANDIDATE"
    # Synth reasoning contains the prices for B7 to extract
    s = c.synth_overall_reasoning()
    assert "4777.43" in s
    assert "4761.19" in s
    assert "4801.79" in s


def test_garbage_lines_handled(synthetic_log_dir: Path) -> None:
    """Test 5: malformed lines do not crash, valid cycle still parses."""
    p = _write_log(synthetic_log_dir, "agent_XAUUSD.log", SYNTHETIC_LOG_GARBAGE_LINES)
    stats = ParseStats()
    cycles = list(parse_log_file(p, start_dt=None, end_dt=None, stats=stats))
    assert len(cycles) == 1
    assert cycles[0].pre_screen_fail == "junk_reason"
    # Lines with non-LINE_PREFIX_RE shape are silently dropped (no crash)
    assert stats.parse_errors == 0


def test_existing_eval_keys_dedup(tmp_path: Path) -> None:
    """Test 6: dedup set built from canonical live_evaluations contains the keys."""
    canonical = tmp_path / "canonical"
    sym_dir = canonical / "XAUUSD"
    sym_dir.mkdir(parents=True)
    rec1 = {
        "candle_time": "2026-04-15T21:15:00+00:00",
        "symbol": "XAUUSD",
        "decision": "NO_TRADE",
    }
    rec2 = {
        "candle_time": "2026-04-15T21:30:00+00:00",
        "symbol": "XAUUSD",
        "decision": "NO_TRADE",
    }
    (sym_dir / "2026-04-15.jsonl").write_text(
        json.dumps(rec1) + "\n" + json.dumps(rec2) + "\n",
        encoding="utf-8",
    )
    keys = _existing_eval_keys(canonical)
    assert ("XAUUSD", "2026-04-15T21:15:00+00:00") in keys
    assert ("XAUUSD", "2026-04-15T21:30:00+00:00") in keys
    assert len(keys) == 2


def test_reconstruct_end_to_end_writes_jsonl_with_dedup(tmp_path: Path) -> None:
    """Test 7: end-to-end reconstruct dedupes against canonical and writes JSONL."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    _write_log(logs_dir, "agent_XAUUSD.log", SYNTHETIC_LOG_FULL_CYCLE)

    canonical = tmp_path / "canonical"
    sym_dir = canonical / "XAUUSD"
    sym_dir.mkdir(parents=True)
    # Canonical record exists for the FIRST cycle (21:15) — should be deduped.
    canonical_rec = {
        "candle_time": "2026-04-15T21:15:00+00:00",
        "symbol": "XAUUSD",
        "decision": "NO_TRADE",
    }
    (sym_dir / "2026-04-15.jsonl").write_text(
        json.dumps(canonical_rec) + "\n", encoding="utf-8",
    )

    output = tmp_path / "out"
    stats = reconstruct(
        logs_dir=logs_dir,
        output_dir=output,
        start=None,
        end=None,
        canonical_evals_dir=canonical,
        dry_run=False,
    )

    # Two cycles emitted; one (21:15) deduped → one written.
    assert stats.candles_emitted == 1
    assert stats.candles_dedup_skipped == 1

    out_file = output / "XAUUSD" / "2026-04-15.jsonl"
    assert out_file.exists()
    lines = [json.loads(l) for l in out_file.read_text().strip().split("\n") if l]
    assert len(lines) == 1
    rec = lines[0]
    assert rec["candle_time"] == "2026-04-15T21:30:00+00:00"
    assert rec["record_source"] == "agent_log_reconstructed"
    assert rec["decision"] == "CANDIDATE"
    assert rec["reconstructed_displacement_ai"] == pytest.approx(4.50, rel=1e-6)


def test_reconstruct_dry_run_does_not_write(tmp_path: Path) -> None:
    """Test 8: dry-run mode emits stats but writes no files."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    _write_log(logs_dir, "agent_XAUUSD.log", SYNTHETIC_LOG_FULL_CYCLE)
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    output = tmp_path / "out"

    stats = reconstruct(
        logs_dir=logs_dir,
        output_dir=output,
        start=None, end=None,
        canonical_evals_dir=canonical,
        dry_run=True,
    )
    assert stats.candles_emitted == 2
    # Output should NOT exist (no writes in dry-run)
    assert not output.exists()


def test_extract_symbol_from_filename_preserves_underscore_suffix() -> None:
    """Test 9: ``agent_US30_cash_demo.log`` → canonical ``US30_cash``."""
    assert _extract_symbol_from_filename("agent_XAUUSD.log") == "XAUUSD"
    assert _extract_symbol_from_filename("agent_XAUUSD_demo.log") == "XAUUSD"
    assert _extract_symbol_from_filename("agent_US30_cash_demo.log") == "US30_cash"
    assert _extract_symbol_from_filename("agent_USDJPY.log") == "USDJPY"
    assert _extract_symbol_from_filename("not_a_match.txt") is None
    assert _extract_symbol_from_filename("agent.log") is None


def test_synth_overall_reasoning_contains_prices_for_b7_extraction() -> None:
    """Test 10: synth_overall_reasoning emits prices in B7-parseable form."""
    ev = CandleEval(
        symbol="XAUUSD",
        candle_time="2026-04-15T21:15:00+00:00",
        log_file="agent_XAUUSD.log",
        entry_price=4777.43,
        stop_loss=4762.14,
        take_profit_1=4800.365,
        displacement_ai=4.5,
        displacement_mso=3.6,
        l2_sl_value=4762.14,
        l2_ob_value=4762.14,
    )
    s = ev.synth_overall_reasoning()
    # Must contain a "Price at <X>" pattern (B7 parses this)
    assert "Price at 4777.43000" in s
    assert "SL placed at 4762.14000" in s
    assert "TP1 at 4800.36500" in s


def test_window_filter_excludes_outside_range(synthetic_log_dir: Path) -> None:
    """Test 11: --start / --end window excludes outside-window cycles."""
    p = _write_log(synthetic_log_dir, "agent_XAUUSD.log", SYNTHETIC_LOG_FULL_CYCLE)
    import datetime as dt
    end_dt = dt.datetime(2026, 4, 15, 21, 20, 0, tzinfo=dt.timezone.utc)
    start_dt = dt.datetime(2026, 4, 15, 21, 0, 0, tzinfo=dt.timezone.utc)
    stats = ParseStats()
    cycles = list(parse_log_file(p, start_dt=start_dt, end_dt=end_dt, stats=stats))
    # First cycle (21:15) is in window; second (21:30) is out
    assert len(cycles) == 1
    assert cycles[0].candle_time.startswith("2026-04-15T21:15")
    assert stats.candles_outside_window == 1


def test_list_log_files_filters_by_pattern(tmp_path: Path) -> None:
    """Test 12: _list_log_files only matches agent_<SYMBOL>(_demo|_mock)?.log."""
    d = tmp_path
    (d / "agent_XAUUSD.log").write_text("", encoding="utf-8")
    (d / "agent_US30_cash_demo.log").write_text("", encoding="utf-8")
    (d / "agent_mock.log").write_text("", encoding="utf-8")
    (d / "tick_capture_XAUUSD.log").write_text("", encoding="utf-8")  # not a match
    (d / "watchdog.log").write_text("", encoding="utf-8")  # not a match
    files = _list_log_files(d)
    names = {p.name for p in files}
    assert "agent_XAUUSD.log" in names
    assert "agent_US30_cash_demo.log" in names
    # ``agent_mock.log`` matches LOG_FILENAME_RE (mock fits suffix) — verify:
    assert "agent_mock.log" not in names  # "mock" is not a SYMBOL stem here
    assert "tick_capture_XAUUSD.log" not in names
    assert "watchdog.log" not in names
