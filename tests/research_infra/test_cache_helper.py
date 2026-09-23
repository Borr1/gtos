"""Unit tests for ``src/research_infra/cache_helper.py`` (T0.3 Phase 1).

Coverage map
------------
- ``build_cache_control``: 5m, 1h, none, invalid -> all three documented
  shapes + ValueError on typos.
- ``annotate_system_blocks``: string input, single-block list input,
  multi-block list input, "none" strips, input-mutation guard, type errors.
- ``CacheMetrics``: empty state, single record, accumulation across many
  records, hit-rate edge cases (0%, 100%, mixed, empty),
  ``summary()`` ttl-dependent cost math, hand-verified totals.

Pure functions only — no API calls, no fixtures with I/O.
"""

from __future__ import annotations

import copy

import pytest

from src.research_infra.cache_helper import (
    CacheMetrics,
    annotate_system_blocks,
    build_cache_control,
)


# ===========================================================================
# build_cache_control
# ===========================================================================


class TestBuildCacheControl:
    """build_cache_control -> three documented shapes + invalid."""

    def test_5m_returns_ephemeral_dict(self):
        assert build_cache_control("5m") == {"type": "ephemeral"}

    def test_5m_is_default(self):
        assert build_cache_control() == {"type": "ephemeral"}

    def test_1h_returns_ephemeral_with_ttl(self):
        assert build_cache_control("1h") == {"type": "ephemeral", "ttl": "1h"}

    def test_none_returns_python_none(self):
        assert build_cache_control("none") is None

    def test_invalid_ttl_raises_value_error(self):
        with pytest.raises(ValueError, match="must be one of"):
            build_cache_control("30m")  # type: ignore[arg-type]

    def test_invalid_type_raises_value_error(self):
        with pytest.raises(ValueError):
            build_cache_control(3600)  # type: ignore[arg-type]


# ===========================================================================
# annotate_system_blocks
# ===========================================================================


class TestAnnotateSystemBlocks:
    """annotate_system_blocks: shape coverage + immutability + edge cases."""

    # ---- string input ----------------------------------------------------

    def test_string_input_5m(self):
        out = annotate_system_blocks("hello world", "5m")
        assert out == [
            {"type": "text", "text": "hello world", "cache_control": {"type": "ephemeral"}}
        ]

    def test_string_input_1h(self):
        out = annotate_system_blocks("hello", "1h")
        assert out == [
            {
                "type": "text",
                "text": "hello",
                "cache_control": {"type": "ephemeral", "ttl": "1h"},
            }
        ]

    def test_string_input_none_strips_cache_control(self):
        out = annotate_system_blocks("hello", "none")
        assert out == [{"type": "text", "text": "hello"}]
        assert "cache_control" not in out[0]

    # ---- single-block list (production shape from primary_analyzer.py) ---

    def test_single_block_list_input_1h(self):
        # Mirrors the exact shape built at primary_analyzer.py:215-221.
        blocks = [
            {
                "type": "text",
                "text": "system text + static context",
                "cache_control": {"type": "ephemeral"},  # the production 5m default
            }
        ]
        out = annotate_system_blocks(blocks, "1h")
        assert out == [
            {
                "type": "text",
                "text": "system text + static context",
                "cache_control": {"type": "ephemeral", "ttl": "1h"},
            }
        ]

    def test_single_block_list_input_none_removes_cc(self):
        blocks = [{"type": "text", "text": "x", "cache_control": {"type": "ephemeral"}}]
        out = annotate_system_blocks(blocks, "none")
        assert out == [{"type": "text", "text": "x"}]

    # ---- multi-block list (only LAST gets annotated) ---------------------

    def test_multi_block_list_only_last_block_gets_cc(self):
        blocks = [
            {"type": "text", "text": "block1"},
            {"type": "text", "text": "block2"},
            {"type": "text", "text": "block3"},
        ]
        out = annotate_system_blocks(blocks, "1h")

        # Last block annotated.
        assert out[-1]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
        # Earlier blocks have no cache_control.
        assert "cache_control" not in out[0]
        assert "cache_control" not in out[1]
        # Text content preserved.
        assert [b["text"] for b in out] == ["block1", "block2", "block3"]

    def test_multi_block_list_strips_pre_existing_cc_from_non_last_blocks(self):
        blocks = [
            {"type": "text", "text": "b1", "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": "b2", "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": "b3"},
        ]
        out = annotate_system_blocks(blocks, "1h")
        assert "cache_control" not in out[0]
        assert "cache_control" not in out[1]
        assert out[2]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}

    def test_multi_block_list_none_strips_all_cc(self):
        blocks = [
            {"type": "text", "text": "b1", "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": "b2"},
            {
                "type": "text",
                "text": "b3",
                "cache_control": {"type": "ephemeral", "ttl": "1h"},
            },
        ]
        out = annotate_system_blocks(blocks, "none")
        for b in out:
            assert "cache_control" not in b

    # ---- immutability ----------------------------------------------------

    def test_does_not_mutate_string_input(self):
        # Strings are immutable in Python anyway, but smoke-test for symmetry.
        s = "hello"
        annotate_system_blocks(s, "1h")
        assert s == "hello"

    def test_does_not_mutate_list_input(self):
        original = [
            {"type": "text", "text": "system", "cache_control": {"type": "ephemeral"}}
        ]
        snapshot = copy.deepcopy(original)
        out = annotate_system_blocks(original, "1h")

        # Caller's list and inner dicts are unchanged.
        assert original == snapshot
        # And the returned object is genuinely independent.
        assert out is not original
        assert out[0] is not original[0]

    def test_does_not_mutate_multi_block_input(self):
        original = [
            {"type": "text", "text": "b1", "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": "b2"},
        ]
        snapshot = copy.deepcopy(original)
        annotate_system_blocks(original, "1h")
        assert original == snapshot

    # ---- error paths -----------------------------------------------------

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            annotate_system_blocks([], "1h")

    def test_invalid_input_type_raises(self):
        with pytest.raises(TypeError, match="expected str or list"):
            annotate_system_blocks(42, "1h")  # type: ignore[arg-type]

    def test_invalid_ttl_propagates_value_error(self):
        with pytest.raises(ValueError):
            annotate_system_blocks("hello", "30m")  # type: ignore[arg-type]


# ===========================================================================
# CacheMetrics
# ===========================================================================


class TestCacheMetricsRecord:
    """record() -> accumulation correctness."""

    def test_empty_state(self):
        m = CacheMetrics()
        assert m.calls == 0
        assert m.uncached_input == 0
        assert m.cache_create == 0
        assert m.cache_read == 0
        assert m.output == 0

    def test_single_record_full_keys(self):
        m = CacheMetrics()
        m.record(
            {
                "input_tokens": 100,
                "cache_creation_input_tokens": 5000,
                "cache_read_input_tokens": 0,
                "output_tokens": 200,
            }
        )
        assert m.calls == 1
        assert m.uncached_input == 100
        assert m.cache_create == 5000
        assert m.cache_read == 0
        assert m.output == 200

    def test_record_handles_missing_keys_as_zero(self):
        # Anthropic omits zero-valued keys in some response shapes.
        m = CacheMetrics()
        m.record({"input_tokens": 50})
        assert m.uncached_input == 50
        assert m.cache_create == 0
        assert m.cache_read == 0
        assert m.output == 0

    def test_record_handles_explicit_none_as_zero(self):
        m = CacheMetrics()
        m.record(
            {
                "input_tokens": None,
                "cache_creation_input_tokens": 100,
                "cache_read_input_tokens": None,
                "output_tokens": 0,
            }
        )
        assert m.uncached_input == 0
        assert m.cache_create == 100
        assert m.cache_read == 0

    def test_accumulation_across_many_records(self):
        m = CacheMetrics()
        # 10 calls: 1 cache-write + 9 cache-reads (typical batch shape).
        m.record({"input_tokens": 200, "cache_creation_input_tokens": 5000, "output_tokens": 150})
        for _ in range(9):
            m.record(
                {"input_tokens": 200, "cache_read_input_tokens": 5000, "output_tokens": 150}
            )

        assert m.calls == 10
        assert m.uncached_input == 200 * 10  # 2000
        assert m.cache_create == 5000  # only the first call
        assert m.cache_read == 5000 * 9  # 45000
        assert m.output == 150 * 10  # 1500

    def test_record_rejects_non_dict(self):
        m = CacheMetrics()
        with pytest.raises(TypeError, match="expected dict"):
            m.record("not a dict")  # type: ignore[arg-type]


class TestCacheMetricsHitRate:
    """hit_rate() -> hand-verified math."""

    def test_empty_metrics_returns_zero_no_division_error(self):
        assert CacheMetrics().hit_rate() == 0.0

    def test_hit_rate_zero_pct_pure_uncached(self):
        # All uncached input, no cache activity at all.
        m = CacheMetrics()
        m.record({"input_tokens": 1000, "output_tokens": 100})
        assert m.hit_rate() == 0.0

    def test_hit_rate_zero_pct_first_call_only_creation(self):
        # First call of a batch -> all tokens go to cache_creation, no reads.
        # hit_rate = 0 / (0 + 5000 + 200) = 0.0
        m = CacheMetrics()
        m.record(
            {"input_tokens": 200, "cache_creation_input_tokens": 5000, "output_tokens": 150}
        )
        assert m.hit_rate() == pytest.approx(0.0)

    def test_hit_rate_100_pct_pure_reads(self):
        # All cache reads, no creation, no uncached.
        m = CacheMetrics()
        m.record({"cache_read_input_tokens": 5000})
        m.record({"cache_read_input_tokens": 5000})
        assert m.hit_rate() == pytest.approx(1.0)

    def test_hit_rate_mixed_hand_verified(self):
        # uncached=200, create=5000, read=45000
        # hit_rate = 45000 / (45000 + 5000 + 200) = 45000 / 50200
        m = CacheMetrics()
        m.record({"input_tokens": 200, "cache_creation_input_tokens": 5000})
        for _ in range(9):
            m.record({"cache_read_input_tokens": 5000})
        # uncached input from later 9 calls is 0 (we omitted input_tokens),
        # so denominator = 200 + 5000 + 45000 = 50200.
        expected = 45000 / 50200
        assert m.hit_rate() == pytest.approx(expected)

    def test_hit_rate_high_90_plus_pct_scenario(self):
        # 50 calls: 1 cache_create call + 49 cache_read calls.
        # uncached=50*200=10000, create=5000, read=49*5000=245000
        # hit_rate = 245000 / (245000 + 5000 + 10000) = 245000/260000 = 0.9423...
        m = CacheMetrics()
        m.record(
            {"input_tokens": 200, "cache_creation_input_tokens": 5000, "output_tokens": 150}
        )
        for _ in range(49):
            m.record(
                {"input_tokens": 200, "cache_read_input_tokens": 5000, "output_tokens": 150}
            )
        rate = m.hit_rate()
        expected = 245000 / 260000
        assert rate == pytest.approx(expected)
        assert rate > 0.94  # >94% hit rate -> well above the 90% threshold

    def test_hit_rate_typical_50_eval_batch(self):
        # Exact batch-API shape that motivates 1h TTL: 1 write, 49 reads,
        # zero uncached input on subsequent calls.
        m = CacheMetrics()
        m.record({"cache_creation_input_tokens": 8000})
        for _ in range(49):
            m.record({"cache_read_input_tokens": 8000})
        # hit_rate = 392000 / (392000 + 8000 + 0) = 0.98
        assert m.hit_rate() == pytest.approx(392000 / 400000)
        assert m.hit_rate() > 0.97


class TestCacheMetricsSummary:
    """summary() -> token totals + cost-equivalent math."""

    def test_summary_keys_are_complete(self):
        m = CacheMetrics()
        m.record({"input_tokens": 100, "cache_read_input_tokens": 1000, "output_tokens": 50})
        s = m.summary("1h")
        for key in (
            "calls",
            "uncached_input_tokens",
            "cache_creation_tokens",
            "cache_read_tokens",
            "output_tokens",
            "hit_rate",
            "ttl_used",
            "estimated_cost_with_cache",
            "estimated_cost_no_cache",
            "estimated_savings",
            "estimated_savings_pct",
        ):
            assert key in s, f"summary missing key {key!r}"

    def test_summary_token_totals_match_record_state(self):
        m = CacheMetrics()
        m.record({"input_tokens": 100, "cache_creation_input_tokens": 5000})
        m.record({"input_tokens": 100, "cache_read_input_tokens": 5000})
        s = m.summary("1h")
        assert s["calls"] == 2
        assert s["uncached_input_tokens"] == 200
        assert s["cache_creation_tokens"] == 5000
        assert s["cache_read_tokens"] == 5000

    def test_summary_1h_cost_math_hand_verified(self):
        # 1 create call (5000 tokens, write_mult=2.00) + 1 read call (5000 tokens, read_mult=0.10)
        # uncached input on both: 200 tokens each = 400 total, mult=1.00
        # output: 150 each = 300 total, mult=5.00
        # cost_with_cache = 400*1.00 + 5000*2.00 + 5000*0.10 + 300*5.00
        #                 = 400 + 10000 + 500 + 1500 = 12400
        # cost_no_cache   = (400 + 5000 + 5000)*1.00 + 300*5.00
        #                 = 10400 + 1500 = 11900
        # savings         = 11900 - 12400 = -500   (NEGATIVE! 1 read isn't enough)
        m = CacheMetrics()
        m.record({"input_tokens": 200, "cache_creation_input_tokens": 5000, "output_tokens": 150})
        m.record({"input_tokens": 200, "cache_read_input_tokens": 5000, "output_tokens": 150})
        s = m.summary("1h")
        assert s["estimated_cost_with_cache"] == pytest.approx(12400.0)
        assert s["estimated_cost_no_cache"] == pytest.approx(11900.0)
        assert s["estimated_savings"] == pytest.approx(-500.0)
        # This confirms the documented break-even of 2 reads for 1h TTL.

    def test_summary_1h_break_even_at_2_reads(self):
        # 1 create + 2 reads -> savings should flip positive (or at least zero).
        m = CacheMetrics()
        m.record({"cache_creation_input_tokens": 5000})
        m.record({"cache_read_input_tokens": 5000})
        m.record({"cache_read_input_tokens": 5000})
        s = m.summary("1h")
        # cost_with_cache = 5000*2.00 + 10000*0.10 = 10000 + 1000 = 11000
        # cost_no_cache   = (5000 + 10000)*1.00 = 15000
        # savings         = 15000 - 11000 = 4000  (positive!)
        assert s["estimated_cost_with_cache"] == pytest.approx(11000.0)
        assert s["estimated_cost_no_cache"] == pytest.approx(15000.0)
        assert s["estimated_savings"] == pytest.approx(4000.0)
        assert s["estimated_savings_pct"] == pytest.approx(4000.0 / 15000.0)

    def test_summary_1h_50_eval_batch_savings_substantial(self):
        # Realistic backtest: 1 create (8000), 49 reads (8000 each), zero
        # uncached, modest output.
        m = CacheMetrics()
        m.record({"cache_creation_input_tokens": 8000, "output_tokens": 100})
        for _ in range(49):
            m.record({"cache_read_input_tokens": 8000, "output_tokens": 100})
        s = m.summary("1h")
        # cost_with_cache = 8000*2.00 + 49*8000*0.10 + 50*100*5.00
        #                 = 16000 + 39200 + 25000 = 80200
        # cost_no_cache   = (8000 + 49*8000)*1.00 + 50*100*5.00
        #                 = 400000 + 25000 = 425000
        assert s["estimated_cost_with_cache"] == pytest.approx(80200.0)
        assert s["estimated_cost_no_cache"] == pytest.approx(425000.0)
        # ~81% cost savings on input+cache-read totals.
        assert s["estimated_savings_pct"] > 0.80

    def test_summary_5m_cost_math(self):
        # Same 1-create/1-read shape as before, but 5m write multiplier (1.25x).
        # cost_with_cache = 400*1.00 + 5000*1.25 + 5000*0.10 + 300*5.00
        #                 = 400 + 6250 + 500 + 1500 = 8650
        # cost_no_cache   = unchanged = 11900
        m = CacheMetrics()
        m.record({"input_tokens": 200, "cache_creation_input_tokens": 5000, "output_tokens": 150})
        m.record({"input_tokens": 200, "cache_read_input_tokens": 5000, "output_tokens": 150})
        s = m.summary("5m")
        assert s["estimated_cost_with_cache"] == pytest.approx(8650.0)
        assert s["estimated_cost_no_cache"] == pytest.approx(11900.0)

    def test_summary_none_collapses_write_to_base(self):
        # ttl_used="none" -> create_mult is base 1.00. With zero create tokens
        # (the "none" path always has zero in cache_create on real usage), the
        # summary degenerates cleanly.
        m = CacheMetrics()
        m.record({"input_tokens": 1000, "output_tokens": 200})
        s = m.summary("none")
        # cost_with_cache = 1000*1.00 + 0 + 0 + 200*5.00 = 1000 + 1000 = 2000
        # cost_no_cache   = same
        assert s["estimated_cost_with_cache"] == pytest.approx(2000.0)
        assert s["estimated_cost_no_cache"] == pytest.approx(2000.0)
        assert s["estimated_savings"] == pytest.approx(0.0)

    def test_summary_empty_metrics_safe(self):
        m = CacheMetrics()
        s = m.summary("1h")
        assert s["calls"] == 0
        assert s["estimated_cost_with_cache"] == 0.0
        assert s["estimated_cost_no_cache"] == 0.0
        assert s["estimated_savings"] == 0.0
        assert s["estimated_savings_pct"] == 0.0
        assert s["hit_rate"] == 0.0
