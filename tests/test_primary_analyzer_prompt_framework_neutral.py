"""HALLUC-1 framework-neutral prompt tests (GBPJPY 2026-04-28 fix).

Multi-framework dispatch suppression bug: the user-message last line used
to hardcode "Evaluate this M15 candle for the OB Retest setup" — biasing
the AI toward emitting ``framework: "ob_retest"`` even when its
qualification reasoning showed a different framework was the right one.

This test module verifies the four prompt-side fixes from
``research/halluc1_gbpjpy_deep_dive_2026-04-28/REPORT.md``:

  * Priority 1   — line 1426 framework-neutral wording.
  * Priority 2a  — ``_format_tf`` exposes mitigated OBs as a flagged section.
  * Priority 3   — SELF-CHECK item #7 enforces framework-vs-reasoning
                   consistency + at-least-one qualified framework on
                   CANDIDATE.
"""

from __future__ import annotations

import pytest

from src.prompts import primary_analyzer_prompt


# ---------------------------------------------------------------------------
# Shared MSO fixture — minimal Pydantic-free dict, matches what
# ``build_dynamic_context`` consumes via ``model_dump(mode="json")``.
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_mso():
    """Return a minimal MarketStateObject sufficient for build_user_message."""
    from src.models.market_state_models import (
        DataQuality,
        MarketStateObject,
        SessionLevels,
        StructureAnalysis,
        TimeframeState,
    )

    bullish = StructureAnalysis(direction="bullish")
    return MarketStateObject(
        timestamp_utc="2026-04-28T01:30:00Z",
        timeframes={
            "D1": TimeframeState(structure=bullish),
            "H4": TimeframeState(structure=bullish),
            "H1": TimeframeState(structure=bullish),
            "M15": TimeframeState(structure=bullish),
        },
        session_levels=SessionLevels(
            asian_high=215.827, asian_low=215.662,
            pdh=216.050, pdl=215.421,
        ),
        data_quality=DataQuality(
            all_timeframes_complete=True,
            spread_normal=True,
            mt5_connected=True,
            timestamp_utc="2026-04-28T01:30:00Z",
        ),
    )


# ---------------------------------------------------------------------------
# Priority 1 — user-message framework neutrality
# ---------------------------------------------------------------------------

class TestUserMessageFrameworkNeutral:

    def test_user_message_does_not_name_a_specific_framework_as_default(self, sample_mso):
        """The user-message last line must not hardcode any framework's name
        as the default. Pre-fix wording: "for the OB Retest setup"."""
        msg = primary_analyzer_prompt.build_user_message(
            sample_mso, {}, "2026-04-28T01:30:00Z", kill_zone="tokyo",
        )
        # All three "for the X setup" phrasings would re-create the same
        # bias for whichever framework was named.
        assert "for the OB Retest setup" not in msg
        assert "for the FVG Fill setup" not in msg
        assert "for the Breaker setup" not in msg
        assert "for the Breaker Re-Entry setup" not in msg

    def test_user_message_references_parallel_evaluation(self, sample_mso):
        """The user-message must explicitly reference the system-prompt's
        PARALLEL EVALUATION block so the AI understands the multi-
        framework dispatch contract."""
        msg = primary_analyzer_prompt.build_user_message(
            sample_mso, {}, "2026-04-28T01:30:00Z", kill_zone="tokyo",
        )
        # The literal block name "PARALLEL EVALUATION" must appear so the
        # AI's instruction-following links the user-message anchor back to
        # the system prompt's Step C dispatch logic.
        assert "PARALLEL" in msg, (
            "user message must reference the PARALLEL EVALUATION block to "
            "preserve the multi-framework dispatch contract"
        )

    def test_user_message_preserves_kill_zone_interpolation(self, sample_mso):
        """Kill-zone substring must still flow into the user message."""
        msg = primary_analyzer_prompt.build_user_message(
            sample_mso, {}, "2026-04-28T01:30:00Z", kill_zone="tokyo",
        )
        assert "tokyo" in msg, "kill_zone interpolation must be preserved"

    def test_user_message_preserves_json_output_anchor(self, sample_mso):
        """The "Output your analysis as JSON" anchor must be kept so the
        AI's schema-emission cue is unchanged."""
        msg = primary_analyzer_prompt.build_user_message(
            sample_mso, {}, "2026-04-28T01:30:00Z", kill_zone="london",
        )
        assert "Output your analysis as JSON" in msg


# ---------------------------------------------------------------------------
# Priority 2a — _format_tf renders mitigated OBs as flagged subsection
# ---------------------------------------------------------------------------

class TestFormatTfMitigatedObs:

    def _tf_data(self, obs: list[dict]) -> dict:
        """Build a minimal tf_data dict for _format_tf."""
        return {
            "structure": {"direction": "bullish", "protected_swing": {}},
            "structure_events": [],
            "order_blocks": obs,
            "breaker_blocks": [],
            "fair_value_gaps": [],
            "avg_candle_body": 0.05,
            "atr_14": 0.10,
        }

    def test_format_tf_renders_mitigated_obs_when_present(self):
        """When all H1 OBs are mitigated (trending market), _format_tf
        must still render them as a flagged subsection so the AI can see
        OB exhaustion is the regime."""
        mitigated_ob = {
            "type": "bullish",
            "high": 215.500,
            "low": 215.450,
            "open": 215.475,
            "close": 215.480,
            "causing_event_type": "BOS",
            "touch_count": 2,
            "formation_time": "2026-04-25T08:00",
            "mitigated": True,
        }
        rendered = primary_analyzer_prompt._format_tf(
            "H1", self._tf_data([mitigated_ob]),
        )
        assert "Mitigated OBs (" in rendered, (
            "_format_tf must render a 'Mitigated OBs (' subsection when "
            "all OBs in tf_data have mitigated=True"
        )
        # The OB high/low values must be visible (not just the count) so
        # the AI can see what was retested.
        assert "215.5" in rendered
        # The flag must communicate why these OBs aren't eligible for
        # ob_retest framework.
        assert "already retested" in rendered or "not eligible" in rendered

    def test_format_tf_does_not_render_mitigated_section_when_empty(self):
        """When no OBs are mitigated, the 'Mitigated OBs' subsection must
        NOT appear (avoids visual noise on healthy markets)."""
        unmitigated_ob = {
            "type": "bullish",
            "high": 215.500,
            "low": 215.450,
            "open": 215.475,
            "close": 215.480,
            "causing_event_type": "BOS",
            "touch_count": 1,
            "formation_time": "2026-04-25T08:00",
            "mitigated": False,
        }
        rendered = primary_analyzer_prompt._format_tf(
            "H1", self._tf_data([unmitigated_ob]),
        )
        assert "Mitigated OBs (" not in rendered, (
            "_format_tf must NOT render a 'Mitigated OBs' subsection when "
            "no OB has mitigated=True"
        )
        # Sanity — the unmitigated OB still appears.
        assert "Unmitigated OBs (" in rendered

    def test_format_tf_renders_both_subsections_when_mixed(self):
        """When some OBs are mitigated and others aren't, both subsections
        appear so the AI sees the full picture."""
        unmitigated_ob = {
            "type": "bullish", "high": 215.700, "low": 215.650,
            "open": 215.680, "close": 215.660, "causing_event_type": "BOS",
            "touch_count": 1, "formation_time": "2026-04-27T09:00",
            "mitigated": False,
        }
        mitigated_ob = {
            "type": "bullish", "high": 215.500, "low": 215.450,
            "open": 215.475, "close": 215.480, "causing_event_type": "BOS",
            "touch_count": 2, "formation_time": "2026-04-25T08:00",
            "mitigated": True,
        }
        rendered = primary_analyzer_prompt._format_tf(
            "H1", self._tf_data([unmitigated_ob, mitigated_ob]),
        )
        assert "Unmitigated OBs (1):" in rendered
        assert "Mitigated OBs (1," in rendered

    def test_format_tf_caps_mitigated_obs_to_last_5(self):
        """The mitigated subsection must be bounded to last 5 entries
        (matching the unmitigated cap) so MSO size stays bounded."""
        # Use price spacing wide enough that the default ``.2f`` price
        # format renders each entry distinctly. The default price format
        # is XAUUSD-style 2-decimals, so spacing of 0.01 gives unique
        # rendered values 215.50, 215.51, ..., 215.59.
        many_mitigated = [
            {
                "type": "bullish", "high": 215.50 + i * 0.01,
                "low": 215.40 + i * 0.01,
                "open": 215.45 + i * 0.01, "close": 215.48 + i * 0.01,
                "causing_event_type": "BOS", "touch_count": 2,
                "formation_time": f"2026-04-25T{i:02d}:00",
                "mitigated": True,
            }
            for i in range(10)
        ]
        rendered = primary_analyzer_prompt._format_tf(
            "H1", self._tf_data(many_mitigated),
        )
        # The header must show the full count
        assert "Mitigated OBs (10," in rendered
        # But the rendered details must come from only the last 5 entries.
        # The earliest 5 (i=0..4 -> 215.50..215.54) should NOT appear in
        # detail rows; the latest 5 (i=5..9 -> 215.55..215.59) should
        # be rendered.
        # Use formation_time as the discriminator (unique per entry).
        assert "2026-04-25T00:00" not in rendered  # i=0 dropped
        assert "2026-04-25T04:00" not in rendered  # i=4 dropped
        assert "2026-04-25T09:00" in rendered      # i=9 latest kept
        assert "2026-04-25T05:00" in rendered      # i=5 oldest kept


# ---------------------------------------------------------------------------
# Priority 3 — SELF-CHECK item enforcing framework consistency
# ---------------------------------------------------------------------------

class TestSelfCheckFrameworkConsistency:

    def test_self_check_includes_framework_consistency_assertion(self):
        """The system prompt's SELF-CHECK block must contain the new item
        asserting framework-vs-reasoning consistency."""
        sp = primary_analyzer_prompt.SYSTEM_PROMPT
        # The SELF-CHECK block exists.
        assert "BEFORE RETURNING YOUR RESPONSE — SELF-CHECK" in sp
        # New item present (item 7 in the numbered list).
        assert "7. Framework consistency" in sp
        # Item names the wrapper-vs-reasoning assertion.
        assert "framework" in sp.lower()
        # Item asserts at-least-one qualified entry on CANDIDATE.
        assert "frameworks_evaluated" in sp
        assert "qualified" in sp

    def test_self_check_count_label_updated(self):
        """The references to 'six SELF-CHECK items' must be updated to
        'seven' to keep the count accurate after item 7 is added."""
        sp = primary_analyzer_prompt.SYSTEM_PROMPT
        assert "seven SELF-CHECK" in sp
        # Old "six SELF-CHECK" wording should be gone.
        assert "six SELF-CHECK" not in sp
        # Inline ranges that say (1-6) should be updated to (1-7) — the
        # template uses the en-dash (U+2013) for ranges.
        assert "1–7" in sp or "1-7" in sp, (
            "self-check range label should be updated to include item 7"
        )
