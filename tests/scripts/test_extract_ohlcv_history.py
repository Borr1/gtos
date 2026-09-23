"""Tests for ``scripts/research/extract_ohlcv_history.py`` (F6).

Coverage map
------------
1. Plan-builder: 10 instruments x 4 timeframes = 40 cells; broker aliases
   resolve correctly (US30 -> US30.cash); CSV name override (US30 ->
   US30_cash_*.csv).
2. Dry-run end-to-end: MT5 NOT touched; plan summary printed; exit 0.
3. Idempotent dedup: re-running an extraction does not duplicate bars.
4. Append vs new file: existing CSV preserved, only new bars added.
5. Broker-server epoch -> UTC string normalization (D1 vs intraday).
6. CSV header validation: rejects mismatched header.
7. ``ModuleNotFoundError`` path: missing MT5 package fails clearly with
   the install hint.
8. CLI arg validation: missing instruments / bad TF / start >= end -> 2.

Mocking strategy
----------------
* MT5 is mocked at ``mt5_module`` parameter to ``run_extraction`` /
  ``fetch_bars``; we never call the real ``MetaTrader5`` package in
  tests.
* ``_import_mt5`` is monkeypatched to inject a custom failure or stub.
* All filesystem writes go through ``tmp_path`` (canonical pattern in
  this codebase per ``feedback_pytest_contamination_forensics``).
"""

from __future__ import annotations

import csv
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

# Resolve project root for the script import. The script lives at
# scripts/research/extract_ohlcv_history.py — we add the worktree root
# to sys.path and import via the module path.
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# scripts/ isn't a package; we need to load the file directly. Use a path
# import via importlib so the test file is independent of how the script
# is executed at the CLI.
import importlib.util as _ilu

_SCRIPT_PATH = _PROJECT_ROOT / "scripts" / "research" / "extract_ohlcv_history.py"
_spec = _ilu.spec_from_file_location("extract_ohlcv_history", _SCRIPT_PATH)
assert _spec and _spec.loader
extract = _ilu.module_from_spec(_spec)
# Register in sys.modules BEFORE exec — dataclass(frozen=True) needs to look
# up the module's __dict__ via cls.__module__ at decoration time.
sys.modules["extract_ohlcv_history"] = extract
_spec.loader.exec_module(extract)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_bar(epoch: int, open_: float = 1.0, high: float = 2.0, low: float = 0.5,
              close: float = 1.5, vol: int = 100):
    """Build one MT5-shaped bar dict (we mock numpy structured access)."""
    return {
        "time": epoch,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "tick_volume": vol,
    }


class FakeMT5:
    """Minimal MT5 stub — only the calls extract_ohlcv_history makes."""

    def __init__(self, *, bars_by_request: dict[tuple[str, int], list[dict]] | None = None,
                 fail_select: bool = False):
        self.bars_by_request = bars_by_request or {}
        self.fail_select = fail_select
        self._init_calls = 0
        self.shutdown_calls = 0

    def initialize(self, **kwargs: Any) -> bool:
        self._init_calls += 1
        return True

    def shutdown(self) -> None:
        self.shutdown_calls += 1

    def symbol_info(self, sym: str) -> Any:
        return SimpleNamespace(digits=5, point=1e-5)

    def symbol_select(self, sym: str, enable: bool) -> bool:
        return not self.fail_select

    def last_error(self) -> tuple[int, str]:
        return (-1, "stub")

    def terminal_info(self) -> Any:
        return SimpleNamespace(name="StubMT5")

    def account_info(self) -> Any:
        return SimpleNamespace(login=0, server="Stub-Demo")

    def copy_rates_range(self, symbol: str, tf_const: int,
                         start: datetime, end: datetime):
        bars = self.bars_by_request.get((symbol, tf_const), [])
        if not bars:
            return None
        # Mimic numpy structured array via a list-of-dicts where __getitem__
        # by string name works (the script uses bar["time"] etc.); a dict
        # already supports this.
        return bars


# ---------------------------------------------------------------------------
# Section 1 — plan builder
# ---------------------------------------------------------------------------


def test_plan_builder_creates_one_cell_per_instrument_and_timeframe(tmp_path):
    instruments = ["XAUUSD", "US30", "USDJPY", "GBPJPY", "XAGUSD",
                   "NAS100", "GBPUSD", "EURUSD", "GER40", "UK100"]
    timeframes = ["M15", "H1", "H4", "D1"]
    plan = extract.build_plan(
        instruments=instruments,
        timeframes=timeframes,
        start_utc=datetime(2025, 10, 1, tzinfo=timezone.utc),
        end_utc=datetime(2026, 4, 24, tzinfo=timezone.utc),
        output_dir=tmp_path,
    )
    assert len(plan) == 10 * 4 == 40
    # Every (sym, tf) combination present.
    pairs = {(t.symbol, t.timeframe) for t in plan}
    assert len(pairs) == 40
    # No existing rows on a fresh tmp_path.
    assert all(t.existing_row_count == 0 for t in plan)


def test_plan_builder_resolves_broker_aliases_and_csv_overrides(tmp_path):
    plan = extract.build_plan(
        instruments=["US30", "NAS100", "GER40", "UK100", "XAUUSD"],
        timeframes=["H4"],
        start_utc=datetime(2025, 10, 1, tzinfo=timezone.utc),
        end_utc=datetime(2026, 4, 24, tzinfo=timezone.utc),
        output_dir=tmp_path,
    )
    by_sym = {t.symbol: t for t in plan}
    # Broker mapping
    assert by_sym["US30"].broker_symbol == "US30.cash"
    assert by_sym["NAS100"].broker_symbol == "US100.cash"
    assert by_sym["GER40"].broker_symbol == "GER40.cash"
    assert by_sym["UK100"].broker_symbol == "UK100.cash"
    assert by_sym["XAUUSD"].broker_symbol == "XAUUSD"
    # CSV filename overrides
    assert by_sym["US30"].csv_path.name == "US30_cash_H4.csv"
    assert by_sym["NAS100"].csv_path.name == "NAS100_H4.csv"
    assert by_sym["XAUUSD"].csv_path.name == "XAUUSD_H4.csv"


# ---------------------------------------------------------------------------
# Section 2 — dry-run
# ---------------------------------------------------------------------------


def test_dry_run_skips_mt5_and_returns_zero(tmp_path, capsys, monkeypatch):
    """--dry-run must NOT import MetaTrader5; explicit ImportError if it would."""
    # Block MT5 import — raises if main() touches it.
    def _fail_import():
        raise AssertionError("dry-run must not import MT5")
    monkeypatch.setattr(extract, "_import_mt5", _fail_import)

    rc = extract.main(
        [
            "--start", "2025-10-01",
            "--end", "2026-04-24",
            "--instruments", "XAUUSD,USDJPY",
            "--timeframes", "H4",
            "--output-dir", str(tmp_path),
            "--dry-run",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Extraction plan:" in out
    assert "XAUUSD" in out and "USDJPY" in out
    # No CSV files created.
    assert not list(tmp_path.glob("*.csv"))


# ---------------------------------------------------------------------------
# Section 3 — idempotent dedup
# ---------------------------------------------------------------------------


def test_re_extraction_is_idempotent_on_existing_bars(tmp_path):
    csv_path = tmp_path / "XAUUSD_H4.csv"
    # Seed CSV with one bar.
    extract.write_csv(
        csv_path,
        [["2026-01-02 00:00:00", "4327.16", "4355.98", "4327.05", "4347.92", "17435"]],
    )
    # Mock MT5 returns the SAME bar plus one new bar.
    fake = FakeMT5(
        bars_by_request={
            ("XAUUSD", extract.MT5_TF_CONST["H4"]): [
                _make_bar(int(datetime(2026, 1, 2, 0, tzinfo=timezone.utc).timestamp()),
                          4327.16, 4355.98, 4327.05, 4347.92, 17435),
                _make_bar(int(datetime(2026, 1, 2, 4, tzinfo=timezone.utc).timestamp()),
                          4347.92, 4360.0, 4340.0, 4350.0, 12000),
            ],
        }
    )
    plan = extract.build_plan(
        instruments=["XAUUSD"],
        timeframes=["H4"],
        start_utc=datetime(2025, 10, 1, tzinfo=timezone.utc),
        end_utc=datetime(2026, 1, 3, tzinfo=timezone.utc),
        output_dir=tmp_path,
    )
    results = extract.run_extraction(plan=plan, mt5_module=fake)
    assert len(results) == 1 and results[0].error is None
    assert results[0].rows_fetched == 2
    assert results[0].rows_appended == 1  # only the new bar

    rows, _ = extract.read_existing_csv(csv_path)
    assert len(rows) == 2
    assert rows[0][0] == "2026-01-02 00:00:00"
    assert rows[1][0] == "2026-01-02 04:00:00"
    # Original row preserved byte-for-byte (volume stays 17435, not stub).
    assert rows[0][5] == "17435"


def test_second_run_appends_zero_when_data_unchanged(tmp_path):
    csv_path = tmp_path / "EURUSD_M15.csv"
    extract.write_csv(
        csv_path,
        [["2025-10-15 09:00:00", "1.1", "1.11", "1.09", "1.105", "100"]],
    )
    bar = _make_bar(
        int(datetime(2025, 10, 15, 9, tzinfo=timezone.utc).timestamp()),
        1.1, 1.11, 1.09, 1.105, 100,
    )
    fake = FakeMT5(
        bars_by_request={("EURUSD", extract.MT5_TF_CONST["M15"]): [bar]}
    )
    plan = extract.build_plan(
        instruments=["EURUSD"],
        timeframes=["M15"],
        start_utc=datetime(2025, 10, 1, tzinfo=timezone.utc),
        end_utc=datetime(2025, 10, 16, tzinfo=timezone.utc),
        output_dir=tmp_path,
    )
    # First run
    extract.run_extraction(plan=plan, mt5_module=fake)
    # Second run -- exactly zero bars appended
    plan2 = extract.build_plan(
        instruments=["EURUSD"],
        timeframes=["M15"],
        start_utc=datetime(2025, 10, 1, tzinfo=timezone.utc),
        end_utc=datetime(2025, 10, 16, tzinfo=timezone.utc),
        output_dir=tmp_path,
    )
    results = extract.run_extraction(plan=plan2, mt5_module=fake)
    assert results[0].rows_appended == 0
    rows, _ = extract.read_existing_csv(csv_path)
    assert len(rows) == 1


# ---------------------------------------------------------------------------
# Section 4 — broker-time -> UTC normalization
# ---------------------------------------------------------------------------


def test_format_bar_time_d1_emits_date_only():
    epoch = int(datetime(2025, 11, 15, 14, 30, 0, tzinfo=timezone.utc).timestamp())
    s = extract.format_bar_time(epoch, "D1")
    # D1 omits time-of-day per the existing CSV schema.
    assert s == "2025-11-15"


def test_format_bar_time_intraday_includes_hms():
    epoch = int(datetime(2025, 11, 15, 14, 30, 0, tzinfo=timezone.utc).timestamp())
    for tf in ["M15", "H1", "H4"]:
        s = extract.format_bar_time(epoch, tf)
        assert s == "2025-11-15 14:30:00"


def test_format_bar_time_handles_midnight_boundary():
    # The 2026-01-02 H4 bar is a real data point in existing CSVs.
    epoch = int(datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc).timestamp())
    assert extract.format_bar_time(epoch, "H4") == "2026-01-02 00:00:00"
    assert extract.format_bar_time(epoch, "D1") == "2026-01-02"


# ---------------------------------------------------------------------------
# Section 5 — CSV schema
# ---------------------------------------------------------------------------


def test_write_csv_emits_canonical_header(tmp_path):
    csv_path = tmp_path / "sample.csv"
    extract.write_csv(csv_path, [["2025-10-01", "1", "2", "0.5", "1.5", "10"]])
    with csv_path.open() as f:
        first_line = f.readline().strip()
    assert first_line == "time,open,high,low,close,volume"


def test_read_existing_csv_rejects_mismatched_header(tmp_path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("foo,bar,baz\n1,2,3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected header"):
        extract.read_existing_csv(csv_path)


def test_read_existing_csv_handles_missing_file(tmp_path):
    rows, max_t = extract.read_existing_csv(tmp_path / "missing.csv")
    assert rows == [] and max_t is None


def test_read_existing_csv_handles_empty_file(tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text("", encoding="utf-8")
    rows, max_t = extract.read_existing_csv(p)
    assert rows == [] and max_t is None


def test_csv_columns_match_existing_schema():
    """Guard the CSV schema invariant. If a downstream consumer changes,
    update this test deliberately — it must not silently drift."""
    assert extract.CSV_COLUMNS == ("time", "open", "high", "low", "close", "volume")


# ---------------------------------------------------------------------------
# Section 6 — append-only sorting
# ---------------------------------------------------------------------------


def test_append_preserves_sort_order(tmp_path):
    csv_path = tmp_path / "GBPUSD_H1.csv"
    # Seed with a later bar.
    extract.write_csv(
        csv_path,
        [["2025-12-01 10:00:00", "1.2", "1.21", "1.19", "1.205", "100"]],
    )
    # Fetch returns an EARLIER bar.
    bar = _make_bar(
        int(datetime(2025, 11, 30, 10, tzinfo=timezone.utc).timestamp()),
        1.21, 1.22, 1.20, 1.215, 80,
    )
    fake = FakeMT5(
        bars_by_request={("GBPUSD", extract.MT5_TF_CONST["H1"]): [bar]}
    )
    plan = extract.build_plan(
        instruments=["GBPUSD"],
        timeframes=["H1"],
        start_utc=datetime(2025, 11, 1, tzinfo=timezone.utc),
        end_utc=datetime(2025, 12, 31, tzinfo=timezone.utc),
        output_dir=tmp_path,
    )
    extract.run_extraction(plan=plan, mt5_module=fake)
    rows, _ = extract.read_existing_csv(csv_path)
    # Earlier bar must end up FIRST (chronological sort).
    assert rows[0][0] == "2025-11-30 10:00:00"
    assert rows[1][0] == "2025-12-01 10:00:00"


# ---------------------------------------------------------------------------
# Section 7 — MT5 missing-package path
# ---------------------------------------------------------------------------


def test_import_mt5_raises_with_install_hint(monkeypatch):
    """If MetaTrader5 is unimportable, _import_mt5 raises ModuleNotFoundError
    with the install command in the message."""
    import builtins as _builtins
    real_import = _builtins.__import__

    def fake_import(name, *a, **kw):
        if name == "MetaTrader5":
            raise ImportError("module not found")
        return real_import(name, *a, **kw)
    monkeypatch.setattr(_builtins, "__import__", fake_import)
    with pytest.raises(ModuleNotFoundError, match="pip install MetaTrader5"):
        extract._import_mt5()


def test_main_returns_3_when_mt5_package_missing(tmp_path, monkeypatch):
    def _fail_import():
        raise ModuleNotFoundError(
            "MetaTrader5 package is required for live extraction. "
            "Install with `pip install MetaTrader5`"
        )
    monkeypatch.setattr(extract, "_import_mt5", _fail_import)
    rc = extract.main(
        [
            "--start", "2025-10-01",
            "--end", "2026-04-24",
            "--instruments", "XAUUSD",
            "--timeframes", "H4",
            "--output-dir", str(tmp_path),
        ]
    )
    assert rc == 3


# ---------------------------------------------------------------------------
# Section 8 — CLI arg validation
# ---------------------------------------------------------------------------


def test_main_returns_2_for_empty_instruments(tmp_path):
    rc = extract.main(
        [
            "--start", "2025-10-01",
            "--end", "2026-04-24",
            "--instruments", "",
            "--timeframes", "H4",
            "--output-dir", str(tmp_path),
            "--dry-run",
        ]
    )
    assert rc == 2


def test_main_returns_2_for_unknown_timeframe(tmp_path):
    rc = extract.main(
        [
            "--start", "2025-10-01",
            "--end", "2026-04-24",
            "--instruments", "XAUUSD",
            "--timeframes", "M5",  # unknown
            "--output-dir", str(tmp_path),
            "--dry-run",
        ]
    )
    assert rc == 2


def test_main_returns_2_when_start_ge_end(tmp_path):
    rc = extract.main(
        [
            "--start", "2026-04-24",
            "--end", "2026-04-24",
            "--instruments", "XAUUSD",
            "--timeframes", "H4",
            "--output-dir", str(tmp_path),
            "--dry-run",
        ]
    )
    assert rc == 2


# ---------------------------------------------------------------------------
# Section 9 — full E2E with stub MT5
# ---------------------------------------------------------------------------


def test_full_run_e2e_with_stub(tmp_path, monkeypatch):
    """Fresh extraction (no existing CSV) for two cells; verifies summary."""
    bars = [
        _make_bar(int(datetime(2025, 10, 1, t, tzinfo=timezone.utc).timestamp()),
                  1.0 + t * 0.01, 1.1 + t * 0.01, 0.9 + t * 0.01,
                  1.05 + t * 0.01, 100 + t)
        for t in range(0, 12, 4)
    ]
    fake = FakeMT5(
        bars_by_request={
            ("XAUUSD", extract.MT5_TF_CONST["H4"]): bars,
            ("EURUSD", extract.MT5_TF_CONST["D1"]): [
                _make_bar(int(datetime(2025, 10, 1, tzinfo=timezone.utc).timestamp()),
                          1.0, 1.1, 0.9, 1.05, 200),
            ],
        }
    )
    monkeypatch.setattr(extract, "_import_mt5", lambda: fake)
    rc = extract.main(
        [
            "--start", "2025-10-01",
            "--end", "2025-10-02",
            "--instruments", "XAUUSD,EURUSD",
            "--timeframes", "H4,D1",
            "--output-dir", str(tmp_path),
        ]
    )
    # 2 of the 4 cells have data (XAUUSD H4, EURUSD D1); 2 return None.
    # rc=1 is acceptable here only if any cell errored — none should
    # because empty-data is logged as a warning, not an error.
    assert rc == 0
    # CSVs land at the right paths
    assert (tmp_path / "XAUUSD_H4.csv").exists()
    assert (tmp_path / "EURUSD_D1.csv").exists()
    rows, _ = extract.read_existing_csv(tmp_path / "XAUUSD_H4.csv")
    assert len(rows) == 3  # 0, 4, 8 hour bars
    rows, _ = extract.read_existing_csv(tmp_path / "EURUSD_D1.csv")
    assert len(rows) == 1
    assert rows[0][0] == "2025-10-01"  # D1 date format


# ---------------------------------------------------------------------------
# Section 10 — merge_rows pure-function tests
# ---------------------------------------------------------------------------


def test_merge_rows_preserves_existing_payload_on_collision():
    existing = [["2025-10-01 00:00:00", "1.0", "1.1", "0.9", "1.05", "EXISTING"]]
    incoming = [["2025-10-01 00:00:00", "9.9", "9.9", "9.9", "9.9", "OVERWRITE"]]
    merged, n = extract.merge_rows(existing_rows=existing, new_rows=incoming)
    assert n == 0
    assert merged[0][5] == "EXISTING"  # not overwritten


def test_merge_rows_appends_genuinely_new():
    existing = [["2025-10-01 00:00:00", "1", "1", "1", "1", "10"]]
    incoming = [
        ["2025-10-01 00:00:00", "1", "1", "1", "1", "10"],  # dup
        ["2025-10-02 00:00:00", "2", "2", "2", "2", "20"],  # new
    ]
    merged, n = extract.merge_rows(existing_rows=existing, new_rows=incoming)
    assert n == 1
    assert {r[0] for r in merged} == {"2025-10-01 00:00:00", "2025-10-02 00:00:00"}
