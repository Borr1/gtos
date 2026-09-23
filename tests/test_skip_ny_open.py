"""Tests for 13:00 UTC NY open candle skip filter (Task 1).

Config-shape note (R2 fix, fix/r2-skip-first-ny-candle)
=======================================================
``apply_instrument_overrides`` in ``src/utils/config.py`` flattens the
matching ``instruments.<symbol>`` block onto the top-level config and
POPS ``instruments``. So at runtime, ``self.config["skip_first_ny_candle"]``
holds the flag value — NOT ``self.config["instruments"][symbol]
["skip_first_ny_candle"]`` (which is always absent).

The prior test fixture built the nested shape, matching the nested
lookup in the original (broken) orchestrator code. Both were wrong
in the same way — which is exactly how the bug escaped coverage. This
fixture now builds the FLATTENED shape (post-``apply_instrument_overrides``)
so tests exercise the same ``self.config`` shape production sees.

Wake-time vs candle-start semantics (E.2 fix, 2026-04-26)
=========================================================
``_next_m15_close`` returns ``close_time + 5s``. The orchestrator wakes
at 13:15:05 UTC to evaluate the M15 bar that just closed — i.e. the
13:00-13:15 NY-open candle. So the skip MUST fire at wake-times in
[13:15, 13:30), NOT [13:00, 13:15). The pre-fix code compared the wake
time directly against the candle's START window and never fired.

These tests use wake-times that match the production cadence
(close_time + 5s): 13:00:05, 13:15:05, 13:30:05, ...
"""

from datetime import datetime, timezone
from unittest.mock import patch

from src.components.orchestrator import SessionOrchestrator, LOCK_DIR


def _make_orchestrator(symbol="XAUUSD", skip_first_ny=True):
    """Create a minimal orchestrator with NY KZ config.

    Config shape mirrors what ``apply_instrument_overrides`` produces:
    the per-instrument flag is flattened to the top level and the
    ``instruments`` section is popped.
    """
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch._symbol = symbol
    orch._mt5_symbol = symbol
    orch._kz_windows = {
        "london": {
            "start_min": 7 * 60,
            "end_min": 9 * 60 + 30,
            "core_end_min": 9 * 60 + 30,
            "crosses_midnight": False,
        },
        "ny": {
            "start_min": 13 * 60,
            "end_min": 17 * 60,
            "core_end_min": 15 * 60 + 30,
            "crosses_midnight": False,
        },
    }
    orch.config = {
        "market": {"symbol": symbol},
        "skip_first_ny_candle": skip_first_ny,
    }
    orch.candle_log = []
    return orch


class TestSkipFirstNYCandle:
    def test_skip_xauusd_at_1315_05(self):
        """XAUUSD at wake 13:15:05 UTC should be skipped — this wake evaluates
        the 13:00-13:15 NY-open candle (the one with 0% WR, n=7)."""
        orch = _make_orchestrator("XAUUSD", skip_first_ny=True)
        with patch("src.components.orchestrator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 27, 13, 15, 5, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert orch._should_skip_first_ny_candle("ny") is True

    def test_no_skip_xauusd_at_1300_05(self):
        """XAUUSD at wake 13:00:05 UTC should NOT be skipped — this wake
        evaluates the 12:45-13:00 candle (pre-NY, before the open candle)."""
        orch = _make_orchestrator("XAUUSD", skip_first_ny=True)
        with patch("src.components.orchestrator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 27, 13, 0, 5, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert orch._should_skip_first_ny_candle("ny") is False

    def test_no_skip_xauusd_at_1330_05(self):
        """XAUUSD at wake 13:30:05 UTC should NOT be skipped — this wake
        evaluates the 13:15-13:30 candle (later than the NY-open candle)."""
        orch = _make_orchestrator("XAUUSD", skip_first_ny=True)
        with patch("src.components.orchestrator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 27, 13, 30, 5, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert orch._should_skip_first_ny_candle("ny") is False

    def test_no_skip_xauusd_at_1400(self):
        """XAUUSD at 14:00 UTC should NOT be skipped (well past first candle)."""
        orch = _make_orchestrator("XAUUSD", skip_first_ny=True)
        with patch("src.components.orchestrator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 27, 14, 0, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert orch._should_skip_first_ny_candle("ny") is False

    def test_no_skip_us30(self):
        """US30 should NOT be skipped (config says false) — even at the
        wake time that would otherwise trigger the skip."""
        orch = _make_orchestrator("US30_cash", skip_first_ny=False)
        with patch("src.components.orchestrator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 27, 13, 15, 5, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert orch._should_skip_first_ny_candle("ny") is False

    def test_no_skip_london_kz(self):
        """Skip should only apply to NY KZ, not London."""
        orch = _make_orchestrator("XAUUSD", skip_first_ny=True)
        with patch("src.components.orchestrator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 27, 7, 15, 5, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert orch._should_skip_first_ny_candle("london") is False

    def test_no_skip_when_not_configured(self):
        """If the flag is absent from config, default to no skip."""
        orch = _make_orchestrator("GBPUSD", skip_first_ny=False)
        # Remove the flag entirely to exercise the default path.
        orch.config.pop("skip_first_ny_candle", None)
        with patch("src.components.orchestrator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 27, 13, 15, 5, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert orch._should_skip_first_ny_candle("ny") is False

    def test_skip_xauusd_at_1329_59(self):
        """Boundary: 13:29:59 is the last second still inside the skip window."""
        orch = _make_orchestrator("XAUUSD", skip_first_ny=True)
        with patch("src.components.orchestrator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 27, 13, 29, 59, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert orch._should_skip_first_ny_candle("ny") is True

    def test_no_skip_xauusd_at_1314_59(self):
        """Boundary: 13:14:59 is BEFORE the skip window — that wake would
        evaluate the 12:45-13:00 candle (pre-NY)."""
        orch = _make_orchestrator("XAUUSD", skip_first_ny=True)
        with patch("src.components.orchestrator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 27, 13, 14, 59, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert orch._should_skip_first_ny_candle("ny") is False


class TestSkipFirstNYCandleConfigMergeRegression:
    """Regression tests for R2 fix (``fix/r2-skip-first-ny-candle``).

    The original lookup at ``self.config.get("instruments", {}).get(symbol, {})``
    always returned empty because ``apply_instrument_overrides`` pops
    ``instruments`` during config merge. These tests lock in the fix by
    round-tripping through the real merge layer.
    """

    def test_merged_config_exposes_flag_at_top_level(self, tmp_path, monkeypatch):
        """After ``apply_instrument_overrides``, XAUUSD's
        ``skip_first_ny_candle: true`` surfaces as top-level ``True``."""
        from src.utils import config as config_mod

        raw_config = {
            "market": {"symbol": "XAUUSD"},
            "instruments": {
                "XAUUSD": {
                    "skip_first_ny_candle": True,
                    "market": {"symbol": "XAUUSD"},
                },
                "US30_cash": {
                    "skip_first_ny_candle": False,
                    "market": {"symbol": "US30_cash"},
                },
            },
        }

        merged_xauusd = config_mod.apply_instrument_overrides(raw_config, "XAUUSD")
        assert merged_xauusd.get("skip_first_ny_candle") is True
        assert "instruments" not in merged_xauusd  # popped during merge

        merged_us30 = config_mod.apply_instrument_overrides(raw_config, "US30_cash")
        assert merged_us30.get("skip_first_ny_candle") is False
        assert "instruments" not in merged_us30

    def test_skip_fires_with_merged_config_xauusd(self, tmp_path, monkeypatch):
        """End-to-end: raw YAML-shape → ``apply_instrument_overrides`` →
        orchestrator.config → skip fires at wake 13:15:05 UTC for XAUUSD."""
        from src.utils import config as config_mod

        raw_config = {
            "market": {"symbol": "XAUUSD"},
            "instruments": {
                "XAUUSD": {
                    "skip_first_ny_candle": True,
                    "market": {"symbol": "XAUUSD"},
                },
            },
        }
        merged = config_mod.apply_instrument_overrides(raw_config, "XAUUSD")

        orch = _make_orchestrator("XAUUSD", skip_first_ny=True)
        orch.config = merged  # inject real-merged config

        with patch("src.components.orchestrator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 27, 13, 15, 5, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert orch._should_skip_first_ny_candle("ny") is True

    def test_skip_does_not_fire_with_merged_config_us30(self, tmp_path, monkeypatch):
        """End-to-end negative: US30_cash's ``skip_first_ny_candle: false``
        still reaches the orchestrator as ``False`` (would-be skip window)."""
        from src.utils import config as config_mod

        raw_config = {
            "market": {"symbol": "XAUUSD"},
            "instruments": {
                "XAUUSD": {"skip_first_ny_candle": True, "market": {"symbol": "XAUUSD"}},
                "US30_cash": {"skip_first_ny_candle": False, "market": {"symbol": "US30_cash"}},
            },
        }
        merged = config_mod.apply_instrument_overrides(raw_config, "US30_cash")

        orch = _make_orchestrator("US30_cash", skip_first_ny=False)
        orch.config = merged

        with patch("src.components.orchestrator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 27, 13, 15, 5, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert orch._should_skip_first_ny_candle("ny") is False

    def test_old_nested_shape_does_not_silently_enable_skip(self):
        """Regression guard: if something accidentally reintroduces a
        ``self.config['instruments'][symbol]`` nested structure (e.g., a
        stale test fixture or a manual override that forgot to flatten),
        the orchestrator still respects the top-level flag. An explicit
        top-level ``False`` must NOT be overridden by a nested ``True``."""
        orch = _make_orchestrator("XAUUSD", skip_first_ny=False)
        # Reintroduce the stale nested structure — with a contradictory True.
        orch.config["instruments"] = {"XAUUSD": {"skip_first_ny_candle": True}}
        with patch("src.components.orchestrator.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 27, 13, 15, 5, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            # The flattened (top-level) value wins — nested is ignored.
            assert orch._should_skip_first_ny_candle("ny") is False
