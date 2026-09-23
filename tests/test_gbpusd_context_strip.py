"""Tests for GBPUSD cross-instrument (XAUUSD D1 macro) context strip.

The T7 C-gate prompt defines C1/C2/C3 as the AI's ENTIRE decision criteria.
On 2026-04-13 GBPUSD evaluations at 14:00 and 14:15 produced different
decisions on identical C-gate conditions — the AI cited "XAUUSD D1 bearish
macro" as the deciding factor, violating the prompt scope and producing
non-deterministic behavior (see handoff 16 §54-59).

Primary enforcement: ``cross_instrument_context.enabled`` was set to ``false``
for GBPUSD on 2026-04-14. These tests cover the belt-and-suspenders added
2026-04-18 after CEO approval:

1. Top-level ``cross_instrument_context_disabled_for`` list skips the fetch
   in the orchestrator even if someone accidentally flips ``enabled: true``.
2. ``primary_analyzer.build_prompt`` force-empties the block for listed
   symbols, catching batch/test/future callers that bypass the orchestrator.

The rendered GBPUSD prompt must contain no "XAUUSD" string. The rendered
XAUUSD prompt must remain unchanged.
"""
from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.components import primary_analyzer as _primary_analyzer_mod
from src.components.orchestrator import SessionOrchestrator
from src.components.primary_analyzer import PrimaryAnalyzer
from src.components.knowledge_base import KnowledgeBase
from src.prompts.primary_analyzer_prompt import (
    build_system_prompt,
    build_user_message,
    format_cross_instrument_context,
)
from src.utils.config import apply_instrument_overrides


# ── Helpers ───────────────────────────────────────────────────────────

def _load_config(symbol: str | None = None) -> dict:
    """Load the live config file and apply instrument overrides."""
    config_path = Path(__file__).parent.parent / "config" / "agent_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if symbol:
        return apply_instrument_overrides(config, symbol)
    return apply_instrument_overrides(config)  # Base (XAUUSD)


def _make_mso(symbol: str = "GBPUSD"):
    """Build a minimal MSO-like object suitable for build_user_message."""
    if symbol == "XAUUSD":
        session_levels = {
            "asian_high": 2050.0, "asian_low": 2040.0,
            "pdh": 2055.0, "pdl": 2035.0,
        }
    else:
        session_levels = {
            "asian_high": 1.2700, "asian_low": 1.2650,
            "pdh": 1.2750, "pdl": 1.2600,
        }
    return SimpleNamespace(
        timestamp_utc="2026-04-18T14:00:00Z",
        model_dump=lambda mode="json": {
            "timestamp_utc": "2026-04-18T14:00:00Z",
            "session_levels": session_levels,
            "liquidity_pools": [],
            "timeframes": {"D1": {}, "H4": {}, "H1": {}, "M15": {}},
            "detected_sweeps": [],
            "data_quality": {},
        },
    )


@pytest.fixture(autouse=True)
def _isolate_malformed_log(tmp_path, monkeypatch):
    """Prevent tests from writing to production malformed_responses.jsonl."""
    monkeypatch.setattr(
        _primary_analyzer_mod, "_MALFORMED_LOG",
        tmp_path / "malformed_responses.jsonl",
    )
    yield


@pytest.fixture
def kb(tmp_path, monkeypatch):
    """KnowledgeBase backed by tmp dir."""
    import src.utils.file_io as fio
    monkeypatch.setattr(fio, "KNOWLEDGE_BASE_DIR", tmp_path)
    (tmp_path / "pipeline_state").mkdir(parents=True, exist_ok=True)
    return KnowledgeBase(base_path=str(tmp_path))


def _make_analyzer(config, kb):
    """Build a PrimaryAnalyzer with a mocked Anthropic client."""
    with patch("src.llm_backend.Anthropic") as MockCls:
        mock_client = MagicMock()
        MockCls.return_value = mock_client
        return PrimaryAnalyzer(config, kb)


# ── Live config verification ──────────────────────────────────────────

class TestLiveConfigHasStrip:
    """Sanity checks on the actual agent_config.yaml."""

    def test_gbpusd_in_strip_list(self):
        """Live config has GBPUSD in cross_instrument_context_disabled_for."""
        config = _load_config("GBPUSD")
        assert "GBPUSD" in config.get("cross_instrument_context_disabled_for", [])

    def test_xauusd_not_in_strip_list(self):
        """XAUUSD must NOT be in the strip list — it legitimately uses its own data."""
        config = _load_config()  # XAUUSD base
        disabled_for = config.get("cross_instrument_context_disabled_for", [])
        assert "XAUUSD" not in disabled_for


# ── Rendered prompt verification ──────────────────────────────────────

class TestRenderedGBPUSDPromptHasNoXAUUSD:
    """The rendered GBPUSD MSO prompt (system + user) must not contain "XAUUSD"."""

    def test_build_prompt_gbpusd_strips_cross_instrument(self, kb):
        """primary_analyzer.build_prompt force-empties CI context for GBPUSD."""
        config = _load_config("GBPUSD")
        analyzer = _make_analyzer(config, kb)
        mso = _make_mso("GBPUSD")

        # Simulate a buggy caller passing XAUUSD macro content
        buggy_ci = (
            "## Cross-Instrument & Volatility Context\n"
            "XAUUSD D1 structure: bearish (indicates dollar strength)\n"
        )
        prompt = analyzer.build_prompt(
            market_state=mso,
            current_time="2026-04-18T14:00:00Z",
            kill_zone="ny",
            cross_instrument_context=buggy_ci,
        )
        user_msg = prompt["user_message"]
        # The user message must not contain any XAUUSD reference
        assert "XAUUSD" not in user_msg
        # The cross-instrument header should be absent as well
        assert "Cross-Instrument" not in user_msg

    def test_build_prompt_gbpusd_no_ci_passed_remains_clean(self, kb):
        """When no CI context is passed, GBPUSD prompt is trivially clean."""
        config = _load_config("GBPUSD")
        analyzer = _make_analyzer(config, kb)
        mso = _make_mso("GBPUSD")

        prompt = analyzer.build_prompt(
            market_state=mso,
            current_time="2026-04-18T14:00:00Z",
            kill_zone="ny",
            cross_instrument_context="",
        )
        assert "XAUUSD" not in prompt["user_message"]

    def test_full_system_plus_user_has_no_xauusd_for_gbpusd(self, kb):
        """Combined rendered system+user prompt contains no XAUUSD token."""
        config = _load_config("GBPUSD")
        analyzer = _make_analyzer(config, kb)
        mso = _make_mso("GBPUSD")

        prompt = analyzer.build_prompt(
            market_state=mso,
            current_time="2026-04-18T14:00:00Z",
            kill_zone="london",
            cross_instrument_context=(
                "## Cross-Instrument & Volatility Context\n"
                "XAUUSD D1 structure: bullish\n"
            ),
        )
        system_text = prompt["system"][0]["text"]
        user_msg = prompt["user_message"]
        combined = system_text + "\n" + user_msg
        assert "XAUUSD" not in combined, (
            "GBPUSD rendered prompt contains XAUUSD — strip failed"
        )


class TestRenderedXAUUSDPromptUnchanged:
    """XAUUSD prompt assembly must be unaffected by the strip logic."""

    def test_xauusd_strip_does_not_apply(self, kb):
        """CI context passed through unchanged for XAUUSD."""
        config = _load_config()  # XAUUSD base
        analyzer = _make_analyzer(config, kb)
        mso = _make_mso("XAUUSD")

        # XAUUSD legitimately uses its own D1 data; the strip list does not apply.
        ci_text = (
            "## Cross-Instrument & Volatility Context\n"
            "XAUUSD D1 structure: bullish (indicates dollar weakness)\n"
        )
        prompt = analyzer.build_prompt(
            market_state=mso,
            current_time="2026-04-18T14:00:00Z",
            kill_zone="london",
            cross_instrument_context=ci_text,
        )
        # If caller passed the block, it should come through — no strip for XAUUSD.
        assert "XAUUSD D1 structure: bullish" in prompt["user_message"]

    def test_xauusd_base_prompt_naturally_contains_xauusd_in_static(self, kb):
        """Sanity: XAUUSD prompts naturally reference XAUUSD in the domain expertise
        block rendered elsewhere (orchestrator additional_context). Ensures our
        strip didn't accidentally touch the static context path."""
        config = _load_config()  # XAUUSD
        analyzer = _make_analyzer(config, kb)
        mso = _make_mso("XAUUSD")

        prompt = analyzer.build_prompt(
            market_state=mso,
            current_time="2026-04-18T14:00:00Z",
            kill_zone="london",
            additional_context="## Gold Market Expertise\nXAUUSD Asian ranges are references.",
        )
        # additional_context is passed through unchanged for XAUUSD
        assert "XAUUSD" in prompt["user_message"]


# ── Strip-list logic unit tests ───────────────────────────────────────

class TestStripListLogic:
    """Isolated tests of the primary_analyzer strip behavior."""

    def test_strip_when_symbol_in_list(self, kb):
        config = {
            "market": {"symbol": "GBPUSD"},
            "ai": {"primary_model": "claude-sonnet-4-6"},
            "cross_instrument_context_disabled_for": ["GBPUSD"],
        }
        analyzer = _make_analyzer(config, kb)
        mso = _make_mso("GBPUSD")
        prompt = analyzer.build_prompt(
            market_state=mso,
            current_time="2026-04-18T14:00:00Z",
            cross_instrument_context="XAUUSD D1 structure: bullish",
        )
        assert "XAUUSD" not in prompt["user_message"]

    def test_no_strip_when_symbol_not_in_list(self, kb):
        config = {
            "market": {"symbol": "EURUSD"},
            "ai": {"primary_model": "claude-sonnet-4-6"},
            "cross_instrument_context_disabled_for": ["GBPUSD"],
        }
        analyzer = _make_analyzer(config, kb)
        mso = _make_mso("EURUSD")
        prompt = analyzer.build_prompt(
            market_state=mso,
            current_time="2026-04-18T14:00:00Z",
            cross_instrument_context="XAUUSD D1 structure: bearish",
        )
        # EURUSD is not in the list → CI is passed through
        assert "XAUUSD D1 structure: bearish" in prompt["user_message"]

    def test_strip_missing_list_is_noop(self, kb):
        """When the config lacks the strip list entirely, CI is preserved."""
        config = {
            "market": {"symbol": "GBPUSD"},
            "ai": {"primary_model": "claude-sonnet-4-6"},
            # No cross_instrument_context_disabled_for key at all
        }
        analyzer = _make_analyzer(config, kb)
        mso = _make_mso("GBPUSD")
        prompt = analyzer.build_prompt(
            market_state=mso,
            current_time="2026-04-18T14:00:00Z",
            cross_instrument_context="XAUUSD D1 structure: bullish",
        )
        # No strip list → block passed through (relies on legacy per-instrument
        # cross_instrument_context.enabled flag for protection)
        assert "XAUUSD" in prompt["user_message"]

    def test_strip_logs_warning(self, kb, caplog):
        config = {
            "market": {"symbol": "GBPUSD"},
            "ai": {"primary_model": "claude-sonnet-4-6"},
            "cross_instrument_context_disabled_for": ["GBPUSD"],
        }
        analyzer = _make_analyzer(config, kb)
        mso = _make_mso("GBPUSD")
        with caplog.at_level(logging.WARNING, logger="src.components.primary_analyzer"):
            analyzer.build_prompt(
                market_state=mso,
                current_time="2026-04-18T14:00:00Z",
                cross_instrument_context="XAUUSD D1 structure: bullish",
            )
        assert any(
            "Stripping cross_instrument_context for GBPUSD" in rec.getMessage()
            for rec in caplog.records
        )


# ── Orchestrator strip-list logic ─────────────────────────────────────

class TestOrchestratorSkipsFetch:
    """Orchestrator._compute_cross_instrument_context skips fetch for listed symbols."""

    def _make_orch(self, symbol: str, disabled_for: list[str] | None,
                   enabled: bool = True) -> SessionOrchestrator:
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = symbol
        orch._mt5_symbol = symbol
        orch._ci_context_text = "SENTINEL"  # must be overwritten
        orch.session_state = {"date": "2026-04-18"}
        orch.config = {
            "cross_instrument_context": {
                "enabled": enabled,
                "reference_instrument": "XAUUSD",
                "reference_timeframe": "D1",
            },
        }
        if disabled_for is not None:
            orch.config["cross_instrument_context_disabled_for"] = disabled_for
        # Mock MT5 so _compute_cross_instrument_context never hits network
        orch.mt5 = MagicMock()
        orch.mt5.get_candles.return_value = []
        return orch

    def test_gbpusd_in_list_skips_fetch(self):
        orch = self._make_orch("GBPUSD", ["GBPUSD"], enabled=True)
        orch._compute_cross_instrument_context()
        assert orch._ci_context_text == ""
        # MT5 was not queried — strip short-circuits before any fetch
        orch.mt5.get_candles.assert_not_called()

    def test_xauusd_not_in_list_proceeds(self):
        orch = self._make_orch("XAUUSD", ["GBPUSD"], enabled=True)
        orch._compute_cross_instrument_context()
        # XAUUSD does not match the strip list — function proceeds past the
        # short-circuit (empty data causes a later empty return, but mt5 IS called).
        orch.mt5.get_candles.assert_called()

    def test_gbpusd_disabled_flag_also_prevents_fetch(self):
        """Legacy path: enabled=False on per-instrument config also skips."""
        orch = self._make_orch("GBPUSD", disabled_for=None, enabled=False)
        orch._compute_cross_instrument_context()
        assert orch._ci_context_text == ""
        orch.mt5.get_candles.assert_not_called()


# ── End-to-end rendered evidence ──────────────────────────────────────

class TestRenderedEvidence:
    """Render the full GBPUSD prompt with live config and grep XAUUSD."""

    def test_live_gbpusd_rendered_prompt_has_no_xauusd(self, kb):
        """End-to-end: live config + sample MSO + a buggy CI payload → XAUUSD absent."""
        config = _load_config("GBPUSD")
        analyzer = _make_analyzer(config, kb)
        mso = _make_mso("GBPUSD")

        # Even if some upstream caller injects the legacy block, it must be stripped.
        buggy_ci_from_legacy_code = (
            "## Cross-Instrument & Volatility Context\n"
            "XAUUSD D1 structure: bearish (indicates dollar strength)\n\n"
            "DECISION GUIDANCE:\n"
            "- If your proposed trade direction CONFLICTS with XAUUSD D1 direction...\n"
        )
        prompt = analyzer.build_prompt(
            market_state=mso,
            current_time="2026-04-18T14:00:00Z",
            kill_zone="ny",
            cross_instrument_context=buggy_ci_from_legacy_code,
        )
        system_text = prompt["system"][0]["text"]
        user_msg = prompt["user_message"]
        full = system_text + "\n" + user_msg
        assert "XAUUSD" not in full, (
            "Live GBPUSD rendered prompt still contains XAUUSD — strip failed"
        )
