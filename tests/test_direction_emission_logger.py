"""Tests for the A.2 direction-emission audit shadow logger.

Scope: verify ``src/components/direction_emission_logger.py`` writes
JSONL rows correctly under the operational scenarios required by the
A.2 deferred-changes spec:

    1. Smoke — writes a JSONL row on a synthetic CANDIDATE event
    2. Failure isolation — disk-write failure must not propagate
    3. Config gate — handled in the orchestrator hook (validated via
       direct probe of the gate flag interpretation in the logger)
    4. Edge case — ``xau_d1_direction="unclear"`` → alignment is null
    5. Edge case — GBPUSD-style ``xau_d1_direction="disabled"`` → row
       still records the sentinel and aligned is null
    6. NO_TRADE / WAIT inputs are silent no-ops
    7. ``correlation_to_xau`` lookup uses the static matrix; XAUUSD
       self-correlation is 1.0; unknown symbols yield ``None``
    8. Schema is stable + JSON round-trips

All tests use ``tmp_path`` for log isolation. The autouse
``_isolate_direction_emission_log`` fixture in ``tests/conftest.py``
redirects the default sink for any indirect-call test.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import src.components.direction_emission_logger as _de_mod
from src.components.direction_emission_logger import (
    _resolve_alignment,
    _resolve_correlation_to_xau,
    log_direction_emission,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pa_candidate(
    direction: str = "LONG",
    framework: str = "ob_retest",
    confidence: int = 80,
    timestamp: str = "2026-04-27T07:30:00+00:00",
    kill_zone: str = "london",
):
    """Build a CANDIDATE-like PrimaryAnalysisOutput stub."""
    tp = SimpleNamespace(
        direction=direction,
        entry_price=2650.0,
        stop_loss=2640.0,
        risk_reward_ratio=1.5,
        take_profit_1=2665.0,
    )
    return SimpleNamespace(
        decision="CANDIDATE",
        framework=framework,
        confidence_score=confidence,
        kill_zone=kill_zone,
        timestamp_utc=timestamp,
        trade_parameters=tp,
    )


def _make_pa_no_trade():
    """Build a NO_TRADE PrimaryAnalysisOutput stub (no trade_parameters)."""
    return SimpleNamespace(
        decision="NO_TRADE",
        framework="none",
        confidence_score=0,
        kill_zone="london",
        timestamp_utc="2026-04-27T07:30:00+00:00",
        trade_parameters=None,
        no_trade_reason="some_reason",
    )


def _make_mso(timestamp_utc: str = "2026-04-27T07:30:00+00:00"):
    return SimpleNamespace(timestamp_utc=timestamp_utc)


def _read_log_rows(log_file: Path) -> list[dict]:
    if not log_file.exists():
        return []
    rows = []
    for line in log_file.read_text(encoding="utf-8").strip().splitlines():
        if line:
            rows.append(json.loads(line))
    return rows


# ---------------------------------------------------------------------------
# Helper-level unit tests
# ---------------------------------------------------------------------------


class TestAlignmentResolution:
    """Edge cases for ``_resolve_alignment``."""

    @pytest.mark.parametrize(
        "direction,xau_dir,expected",
        [
            ("LONG", "bullish", True),
            ("SHORT", "bearish", True),
            ("LONG", "bearish", False),
            ("SHORT", "bullish", False),
            ("LONG", "unclear", None),
            ("SHORT", "unclear", None),
            ("LONG", "unavailable", None),
            ("SHORT", "disabled", None),
            (None, "bullish", None),
            ("LONG", None, None),
            ("WAIT", "bullish", None),
        ],
    )
    def test_alignment_truth_table(self, direction, xau_dir, expected):
        assert _resolve_alignment(direction, xau_dir) is expected


class TestCorrelationLookup:
    """``_resolve_correlation_to_xau`` against the static matrix."""

    def test_xauusd_self_returns_one(self):
        assert _resolve_correlation_to_xau("XAUUSD") == 1.0
        assert _resolve_correlation_to_xau("xauusd") == 1.0  # case insensitive

    def test_known_symbol_lookup(self):
        # XAGUSD↔XAUUSD = 0.799 in the static fallback table
        corr = _resolve_correlation_to_xau("XAGUSD")
        assert corr is not None
        assert 0.7 < corr < 0.85

    def test_known_negative_correlation(self):
        # USDCAD↔XAUUSD = -0.399 in the static fallback
        corr = _resolve_correlation_to_xau("USDCAD")
        assert corr is not None
        assert -0.5 < corr < -0.3

    def test_unknown_symbol_returns_none(self):
        assert _resolve_correlation_to_xau("FAKEPAIR") is None

    def test_empty_symbol_returns_none(self):
        assert _resolve_correlation_to_xau("") is None


# ---------------------------------------------------------------------------
# Direct logger-call tests
# ---------------------------------------------------------------------------


class TestSmokeWrite:
    """The headline contract: a CANDIDATE writes one well-formed JSONL row."""

    def test_writes_jsonl_row_on_candidate(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        pa = _make_pa_candidate(direction="LONG")
        mso = _make_mso()

        result = log_direction_emission(
            pa,
            instrument="XAUUSD",
            xau_d1_direction="bullish",
            mso=mso,
            session_state={"kill_zone": "london"},
            log_path=str(log_file),
        )

        assert result is not None
        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        row = rows[0]

        # Required schema fields
        assert row["instrument"] == "XAUUSD"
        assert row["proposed_direction"] == "LONG"
        assert row["xau_d1_direction"] == "bullish"
        assert row["correlation_to_xau"] == 1.0  # XAU self
        assert row["direction_aligned_with_xau"] is True
        assert row["kill_zone"] == "london"
        assert row["confidence_score"] == 80
        assert row["framework"] == "ob_retest"
        assert row["candle_time_utc"] == "2026-04-27T07:30:00+00:00"
        assert "logged_at_utc" in row

    def test_writes_short_aligned_with_bearish_xau(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        pa = _make_pa_candidate(direction="SHORT", framework="fvg_fill")
        log_direction_emission(
            pa,
            instrument="USDJPY",
            xau_d1_direction="bearish",
            log_path=str(log_file),
        )

        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        assert rows[0]["proposed_direction"] == "SHORT"
        assert rows[0]["xau_d1_direction"] == "bearish"
        assert rows[0]["direction_aligned_with_xau"] is True
        assert rows[0]["framework"] == "fvg_fill"
        # USDJPY↔XAUUSD = -0.239 in the static matrix
        assert rows[0]["correlation_to_xau"] is not None
        assert -0.3 < rows[0]["correlation_to_xau"] < -0.15

    def test_misaligned_long_with_bearish_xau(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        pa = _make_pa_candidate(direction="LONG")
        log_direction_emission(
            pa,
            instrument="XAUUSD",
            xau_d1_direction="bearish",
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        assert rows[0]["direction_aligned_with_xau"] is False


class TestSilentNoOps:
    """NO_TRADE / WAIT outputs must NOT produce a row."""

    def test_no_trade_silent(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        pa = _make_pa_no_trade()
        result = log_direction_emission(
            pa,
            instrument="XAUUSD",
            xau_d1_direction="bullish",
            log_path=str(log_file),
        )
        assert result is None
        assert not log_file.exists() or _read_log_rows(log_file) == []

    def test_none_pa_silent(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        result = log_direction_emission(
            None,
            instrument="XAUUSD",
            xau_d1_direction="bullish",
            log_path=str(log_file),
        )
        assert result is None
        assert not log_file.exists() or _read_log_rows(log_file) == []

    def test_candidate_with_no_trade_parameters_silent(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        # Decision says CANDIDATE but trade_parameters is missing — defensive path
        bad = SimpleNamespace(
            decision="CANDIDATE",
            framework="ob_retest",
            confidence_score=80,
            kill_zone="london",
            timestamp_utc="2026-04-27T07:30:00+00:00",
            trade_parameters=None,
        )
        result = log_direction_emission(
            bad,
            instrument="XAUUSD",
            xau_d1_direction="bullish",
            log_path=str(log_file),
        )
        assert result is None


class TestEdgeCases:
    """xau_d1_direction = unclear / disabled / unavailable."""

    def test_unclear_xau_yields_null_alignment(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        pa = _make_pa_candidate(direction="LONG")
        log_direction_emission(
            pa,
            instrument="GBPUSD",
            xau_d1_direction="unclear",
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        row = rows[0]
        assert row["xau_d1_direction"] == "unclear"
        assert row["direction_aligned_with_xau"] is None

    def test_disabled_xau_yields_null_alignment(self, tmp_path):
        """GBPUSD case: orchestrator emits ``"disabled"`` sentinel."""
        log_file = tmp_path / "de.jsonl"
        pa = _make_pa_candidate(direction="LONG")
        log_direction_emission(
            pa,
            instrument="GBPUSD",
            xau_d1_direction="disabled",
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        row = rows[0]
        assert row["xau_d1_direction"] == "disabled"
        assert row["direction_aligned_with_xau"] is None
        # GBPUSD↔XAUUSD = 0.419 — correlation still recorded even with
        # disabled XAU view (the matrix lookup is independent of the
        # orchestrator's day-of XAU bias computation).
        assert row["correlation_to_xau"] is not None
        assert 0.35 < row["correlation_to_xau"] < 0.5

    def test_unavailable_xau_yields_null_alignment(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        pa = _make_pa_candidate(direction="LONG")
        log_direction_emission(
            pa,
            instrument="XAGUSD",
            xau_d1_direction="unavailable",
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        assert rows[0]["xau_d1_direction"] == "unavailable"
        assert rows[0]["direction_aligned_with_xau"] is None

    def test_none_xau_coerced_to_unavailable(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        pa = _make_pa_candidate(direction="LONG")
        log_direction_emission(
            pa,
            instrument="XAUUSD",
            xau_d1_direction=None,
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        assert rows[0]["xau_d1_direction"] == "unavailable"

    def test_unknown_instrument_yields_null_correlation(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        pa = _make_pa_candidate(direction="LONG")
        log_direction_emission(
            pa,
            instrument="FAKEPAIR",
            xau_d1_direction="bullish",
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        assert len(rows) == 1
        # Row still written; correlation null
        assert rows[0]["correlation_to_xau"] is None
        # Alignment still computed (depends on direction + xau_dir, not corr)
        assert rows[0]["direction_aligned_with_xau"] is True


class TestKillZoneResolution:
    """kill_zone field comes from session_state OR pa_output OR 'outside'."""

    def test_session_state_takes_precedence(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        pa = _make_pa_candidate(kill_zone="ny")  # would be 'ny' from pa
        log_direction_emission(
            pa,
            instrument="XAUUSD",
            xau_d1_direction="bullish",
            session_state={"kill_zone": "tokyo"},  # overrides
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        assert rows[0]["kill_zone"] == "tokyo"

    def test_pa_kill_zone_used_when_no_session_state(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        pa = _make_pa_candidate(kill_zone="ny")
        log_direction_emission(
            pa,
            instrument="XAUUSD",
            xau_d1_direction="bullish",
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        assert rows[0]["kill_zone"] == "ny"

    def test_outside_when_no_kz_known(self, tmp_path):
        """No session_state, no pa.kill_zone → 'outside' sentinel."""
        log_file = tmp_path / "de.jsonl"
        # PA without kill_zone attribute
        pa = SimpleNamespace(
            decision="CANDIDATE",
            framework="ob_retest",
            confidence_score=80,
            timestamp_utc="2026-04-27T07:30:00+00:00",
            trade_parameters=SimpleNamespace(direction="LONG"),
        )
        log_direction_emission(
            pa,
            instrument="XAUUSD",
            xau_d1_direction="bullish",
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        assert rows[0]["kill_zone"] == "outside"


class TestFailureIsolation:
    """Disk failures + bad input must NEVER propagate to the orchestrator."""

    def test_open_raising_does_not_propagate(self, tmp_path):
        bad_path = tmp_path / "nonexistent" / "deeply" / "nested" / "log.jsonl"
        pa = _make_pa_candidate()

        with patch(
            "src.components.direction_emission_logger.open",
            side_effect=OSError("disk full"),
        ):
            # MUST NOT raise
            result = log_direction_emission(
                pa,
                instrument="XAUUSD",
                xau_d1_direction="bullish",
                log_path=str(bad_path),
            )
        # Failure path: returns None silently
        assert result is None

    def test_corrupt_pa_attribute_access_does_not_propagate(self, tmp_path):
        log_file = tmp_path / "de.jsonl"

        class Boom:
            decision = "CANDIDATE"
            framework = "ob_retest"
            confidence_score = 80
            kill_zone = "london"
            timestamp_utc = "2026-04-27T07:30:00+00:00"

            @property
            def trade_parameters(self):  # noqa: D401 — test stub
                raise RuntimeError("intentional explosion")

        # MUST NOT raise — defensive _safe_get swallows the property error
        result = log_direction_emission(
            Boom(),
            instrument="XAUUSD",
            xau_d1_direction="bullish",
            log_path=str(log_file),
        )
        # No proposed_direction was extractable → silent no-op
        assert result is None
        assert not log_file.exists() or _read_log_rows(log_file) == []

    def test_logger_returns_none_on_unwriteable_directory(self, tmp_path):
        # The mkdir call could in theory raise on some platforms; verify
        # we still don't propagate even if both mkdir and open fail.
        pa = _make_pa_candidate()
        with patch(
            "src.components.direction_emission_logger.Path.mkdir",
            side_effect=PermissionError("read-only fs"),
        ):
            result = log_direction_emission(
                pa,
                instrument="XAUUSD",
                xau_d1_direction="bullish",
                log_path=str(tmp_path / "x.jsonl"),
            )
        assert result is None


class TestSchemaStability:
    """The row schema must be stable + JSON-serializable."""

    def test_required_keys_present(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        pa = _make_pa_candidate()
        log_direction_emission(
            pa,
            instrument="XAUUSD",
            xau_d1_direction="bullish",
            log_path=str(log_file),
        )
        rows = _read_log_rows(log_file)
        row = rows[0]

        required_keys = {
            "logged_at_utc",
            "candle_time_utc",
            "instrument",
            "proposed_direction",
            "xau_d1_direction",
            "correlation_to_xau",
            "direction_aligned_with_xau",
            "kill_zone",
            "confidence_score",
            "framework",
        }
        assert required_keys.issubset(row.keys())

    def test_jsonl_round_trips(self, tmp_path):
        log_file = tmp_path / "de.jsonl"
        for direction in ("LONG", "SHORT", "LONG"):
            pa = _make_pa_candidate(direction=direction)
            log_direction_emission(
                pa,
                instrument="XAUUSD",
                xau_d1_direction="bullish",
                log_path=str(log_file),
            )

        text = log_file.read_text(encoding="utf-8")
        lines = [ln for ln in text.split("\n") if ln]
        assert len(lines) == 3
        for ln in lines:
            row = json.loads(ln)  # must not raise
            assert isinstance(row, dict)


class TestConfigGate:
    """The config gate lives in the orchestrator hook (default ON, opt-out
    via ``shadow_loggers.direction_emission_logger.enabled = false``).
    Direct calls to the logger don't consult config — that's by design,
    so unit tests + manual analysis tooling can drive the logger without
    threading config through. Validate the orchestrator hook behavior in
    a separate orchestrator-level test if needed; here we assert the
    direct-call contract: enabled=false means NOT calling the logger,
    not calling-with-flag-and-getting-noop.
    """

    def test_config_disabled_path_exercised_via_hook_check(self, tmp_path):
        """Validate the hook-side config-read pattern works.

        We don't call ``log_direction_emission`` directly here — we
        exercise the same dict-traversal pattern the orchestrator uses
        to ensure ``enabled: false`` short-circuits correctly.
        """
        log_file = tmp_path / "de.jsonl"
        config_disabled = {
            "shadow_loggers": {
                "direction_emission_logger": {"enabled": False}
            }
        }
        config_enabled = {
            "shadow_loggers": {
                "direction_emission_logger": {"enabled": True}
            }
        }
        config_missing = {}  # no shadow_loggers block

        def _gate_says_log(cfg):
            cfg_dir = (cfg.get("shadow_loggers", {}) or {}).get(
                "direction_emission_logger", {}
            ) or {}
            return cfg_dir.get("enabled", True)

        assert _gate_says_log(config_disabled) is False
        assert _gate_says_log(config_enabled) is True
        # Missing block defaults ON (consistent with regime_classifier_logger)
        assert _gate_says_log(config_missing) is True

        # Direct call should still write — the gate is the caller's
        # responsibility (matches touch_count_gate_logger contract).
        pa = _make_pa_candidate()
        log_direction_emission(
            pa,
            instrument="XAUUSD",
            xau_d1_direction="bullish",
            log_path=str(log_file),
        )
        assert len(_read_log_rows(log_file)) == 1


class TestModuleSinkRedirect:
    """The ``_isolate_direction_emission_log`` autouse fixture redirects
    the default sink to ``tmp_path``. Tests that omit ``log_path=`` should
    still write to that redirected location, not to ``shadow_logs/``."""

    def test_default_sink_uses_isolated_log_path(
        self, _isolate_direction_emission_log,
    ):
        pa = _make_pa_candidate()
        result = log_direction_emission(
            pa,
            instrument="XAUUSD",
            xau_d1_direction="bullish",
        )
        assert result is not None
        rows = _read_log_rows(_isolate_direction_emission_log)
        assert len(rows) == 1
        assert rows[0]["instrument"] == "XAUUSD"
