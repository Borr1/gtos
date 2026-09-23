"""Tests for ``scripts/divergence_classification_summary.py``.

Covers:
* Parser — sample heading regex, checkbox detection, label → category.
* Unclassified / malformed / unknown-label branches.
* Aggregation — overall stats, per-instrument, per-timeframe.
* Promotion-gate logic — N + rate + per-instrument floor combos.
* End-to-end parse_all over synthetic week_*.md files.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts import divergence_classification_summary as mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sample_block(
    idx: int,
    symbol: str = "XAUUSD",
    tf: str = "H1",
    checked: str = None,
    ts: str = "2026-04-24 14:15 UTC",
) -> str:
    """Render a minimal sample block matching the sampler's contract.

    ``checked`` can be one of: "v1", "v2", "both", "ambiguous", None.
    ``None`` → all boxes unchecked (unclassified). "two" → v1 + v2 both
    ticked (malformed). "unknown" → emits an extra unknown-label box
    ticked (malformed).
    """
    mk = lambda flag: "[x]" if flag else "[ ]"
    if checked == "v1":
        v1, v2, both, amb = True, False, False, False
    elif checked == "v2":
        v1, v2, both, amb = False, True, False, False
    elif checked == "both":
        v1, v2, both, amb = False, False, True, False
    elif checked == "ambiguous":
        v1, v2, both, amb = False, False, False, True
    elif checked == "two":
        v1, v2, both, amb = True, True, False, False
    else:
        v1, v2, both, amb = False, False, False, False

    extra = ""
    if checked == "unknown":
        extra = "\n- [x] some bogus label not in the map"

    return (
        f"## Sample {idx} — {symbol} {tf} {ts}\n"
        "\n"
        "- **v1 direction:** bullish | **v2 direction:** bearish\n"
        "- **score:** -5 | **dead_zone:** 8 | **counts:** hh=8 hl=6 lh=10 ll=11\n"
        "- **production_label:** bullish (v1 drives in v2_shadow mode)\n"
        "\n"
        "**Window context** (50 candles, X → Y):\n"
        "- Price range: 2640.00 → 2650.00 (close 2645.00)\n"
        "\n"
        "**Classification** (check ONE):\n"
        f"- {mk(v1)} v1 correct (bullish was right)\n"
        f"- {mk(v2)} v2 correct (bearish was right)\n"
        f"- {mk(both)} both wrong (should have been transitional/ranging)\n"
        f"- {mk(amb)} ambiguous (genuinely could go either way){extra}\n"
        "\n"
        "---\n"
    )


def _write_week(dir_: Path, label: str, blocks: list[str]) -> Path:
    dir_.mkdir(parents=True, exist_ok=True)
    path = dir_ / f"week_{label}.md"
    path.write_text(
        f"# Divergence Sampling — week {label}\n\n---\n\n" + "\n".join(blocks),
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# 1) parse_digest — per-block behaviour
# ---------------------------------------------------------------------------


class TestParseDigest:

    def test_parses_one_v2_correct_block(self, tmp_path):
        path = _write_week(tmp_path, "2026-17", [_sample_block(1, checked="v2")])
        result = mod.parse_digest(path)
        assert result.total_samples == 1
        assert len(result.classifications) == 1
        c = result.classifications[0]
        assert c.category == "v2_correct"
        assert c.symbol == "XAUUSD"
        assert c.timeframe == "H1"
        assert c.week == "2026-17"
        assert c.sample_index == 1

    def test_unclassified_block_counted_but_not_recorded(self, tmp_path):
        path = _write_week(tmp_path, "2026-17", [_sample_block(1, checked=None)])
        result = mod.parse_digest(path)
        assert result.total_samples == 1
        assert result.unclassified == 1
        assert len(result.classifications) == 0

    def test_two_boxes_checked_malformed(self, tmp_path):
        path = _write_week(tmp_path, "2026-17", [_sample_block(1, checked="two")])
        result = mod.parse_digest(path)
        assert result.malformed == 1
        assert len(result.classifications) == 0
        assert any("2 boxes checked" in w for w in result.warnings)

    def test_unknown_label_malformed(self, tmp_path):
        path = _write_week(tmp_path, "2026-17", [_sample_block(1, checked="unknown")])
        result = mod.parse_digest(path)
        assert result.malformed == 1
        assert len(result.classifications) == 0
        assert any("unknown label" in w for w in result.warnings)

    def test_multiple_blocks_mixed(self, tmp_path):
        blocks = [
            _sample_block(1, symbol="XAUUSD", tf="H1", checked="v2"),
            _sample_block(2, symbol="USDJPY", tf="M15", checked="v1"),
            _sample_block(3, symbol="GBPJPY", tf="H1", checked="both"),
            _sample_block(4, symbol="XAUUSD", tf="M15", checked="ambiguous"),
            _sample_block(5, symbol="GBPUSD", tf="H1", checked=None),
        ]
        path = _write_week(tmp_path, "2026-17", blocks)
        result = mod.parse_digest(path)
        assert result.total_samples == 5
        assert result.unclassified == 1
        assert result.malformed == 0
        assert len(result.classifications) == 4
        cats = [c.category for c in result.classifications]
        assert cats == ["v2_correct", "v1_correct", "both_wrong", "ambiguous"]


# ---------------------------------------------------------------------------
# 2) Stats aggregation
# ---------------------------------------------------------------------------


def _make_class(sym: str, tf: str, cat: str) -> mod.Classification:
    return mod.Classification(symbol=sym, timeframe=tf, category=cat,
                              week="2026-17", sample_index=1)


class TestAggregations:

    def test_overall_excludes_ambiguous_from_rate(self):
        classes = [
            _make_class("XAUUSD", "H1", "v2_correct"),
            _make_class("XAUUSD", "H1", "v2_correct"),
            _make_class("XAUUSD", "H1", "v2_correct"),
            _make_class("XAUUSD", "H1", "v1_correct"),
            _make_class("XAUUSD", "H1", "ambiguous"),
            _make_class("XAUUSD", "H1", "ambiguous"),
        ]
        stats = mod.compute_overall_stats(classes)
        assert stats["total"] == 6
        assert stats["rate_denom"] == 4  # 3 v2 + 1 v1 + 0 both (no ambiguous)
        # 3 / 4 = 75%
        assert stats["v2_correct_rate"] == pytest.approx(0.75)

    def test_per_instrument_breakdown(self):
        classes = [
            _make_class("XAUUSD", "H1", "v2_correct"),
            _make_class("XAUUSD", "H1", "v1_correct"),
            _make_class("USDJPY", "H1", "v2_correct"),
            _make_class("USDJPY", "H1", "v2_correct"),
        ]
        per_sym = mod.compute_per_instrument(classes)
        assert set(per_sym.keys()) == {"XAUUSD", "USDJPY"}
        assert per_sym["XAUUSD"]["v2_correct_rate"] == pytest.approx(0.5)
        assert per_sym["USDJPY"]["v2_correct_rate"] == pytest.approx(1.0)

    def test_zero_denominator_safe(self):
        # All ambiguous → rate_denom=0, rate=0.0 (no div by zero crash).
        classes = [
            _make_class("XAUUSD", "H1", "ambiguous"),
            _make_class("XAUUSD", "H1", "ambiguous"),
        ]
        stats = mod.compute_overall_stats(classes)
        assert stats["rate_denom"] == 0
        assert stats["v2_correct_rate"] == 0.0


# ---------------------------------------------------------------------------
# 3) Promotion-gate logic
# ---------------------------------------------------------------------------


class TestPromotionGate:

    def test_not_ready_when_count_below_threshold(self):
        classes = [_make_class("XAUUSD", "H1", "v2_correct") for _ in range(50)]
        overall = mod.compute_overall_stats(classes)
        per_sym = mod.compute_per_instrument(classes)
        ready, reasons = mod.check_promotion_ready(overall, per_sym)
        assert not ready
        assert any("total_classified 50" in r for r in reasons)

    def test_not_ready_when_rate_below_threshold(self):
        # 100 classifications, 70% v2-correct → fails 80% gate.
        classes = [_make_class("XAUUSD", "H1", "v2_correct") for _ in range(70)]
        classes += [_make_class("XAUUSD", "H1", "v1_correct") for _ in range(30)]
        overall = mod.compute_overall_stats(classes)
        per_sym = mod.compute_per_instrument(classes)
        ready, reasons = mod.check_promotion_ready(overall, per_sym)
        assert not ready
        assert any("overall_v2_correct_rate" in r for r in reasons)

    def test_not_ready_when_per_instrument_below_floor(self):
        # Overall > 80% but one instrument at 55% (below 60% floor).
        # XAUUSD: 90/100 = 90%, USDJPY: 11/20 = 55% < 60%.
        # Combined: 101/120 = 84.2% (clears overall gate).
        classes = (
            [_make_class("XAUUSD", "H1", "v2_correct") for _ in range(90)]
            + [_make_class("XAUUSD", "H1", "v1_correct") for _ in range(10)]
            + [_make_class("USDJPY", "H1", "v2_correct") for _ in range(11)]
            + [_make_class("USDJPY", "H1", "v1_correct") for _ in range(9)]
        )
        overall = mod.compute_overall_stats(classes)
        assert overall["total"] == 120
        assert overall["v2_correct_rate"] > 0.80
        per_sym = mod.compute_per_instrument(classes)
        ready, reasons = mod.check_promotion_ready(overall, per_sym)
        assert not ready
        assert any("USDJPY" in r for r in reasons)

    def test_ready_when_all_gates_pass(self):
        classes = (
            [_make_class("XAUUSD", "H1", "v2_correct") for _ in range(50)]
            + [_make_class("XAUUSD", "H1", "v1_correct") for _ in range(5)]
            + [_make_class("USDJPY", "H1", "v2_correct") for _ in range(45)]
            + [_make_class("USDJPY", "H1", "v1_correct") for _ in range(5)]
        )
        # Total 105, overall 95/100 = 95%, both instruments ≥ 80%.
        overall = mod.compute_overall_stats(classes)
        per_sym = mod.compute_per_instrument(classes)
        ready, reasons = mod.check_promotion_ready(overall, per_sym)
        assert ready, f"Unexpected reasons: {reasons}"
        assert reasons == []

    def test_instrument_with_zero_decisive_not_gated(self):
        # USDJPY only has "ambiguous" classifications → denom=0 → skipped
        # from per-instrument gate.
        classes = (
            [_make_class("XAUUSD", "H1", "v2_correct") for _ in range(90)]
            + [_make_class("XAUUSD", "H1", "v1_correct") for _ in range(10)]
            + [_make_class("USDJPY", "H1", "ambiguous") for _ in range(5)]
        )
        overall = mod.compute_overall_stats(classes)
        per_sym = mod.compute_per_instrument(classes)
        ready, reasons = mod.check_promotion_ready(overall, per_sym)
        assert ready, f"Unexpected reasons: {reasons}"


# ---------------------------------------------------------------------------
# 4) parse_all + render_summary end-to-end
# ---------------------------------------------------------------------------


class TestEndToEnd:

    def test_parse_all_across_two_weeks(self, tmp_path):
        _write_week(tmp_path, "2026-17", [
            _sample_block(1, symbol="XAUUSD", tf="H1", checked="v2"),
            _sample_block(2, symbol="XAUUSD", tf="H1", checked="v1"),
        ])
        _write_week(tmp_path, "2026-18", [
            _sample_block(1, symbol="USDJPY", tf="M15", checked="v2"),
        ])
        result = mod.parse_all(tmp_path)
        assert result.total_samples == 3
        assert len(result.classifications) == 3
        cats = [c.category for c in result.classifications]
        assert sorted(cats) == ["v1_correct", "v2_correct", "v2_correct"]

    def test_missing_digest_dir_graceful(self, tmp_path):
        result = mod.parse_all(tmp_path / "does_not_exist")
        assert result.classifications == []
        assert any("does not exist" in w for w in result.warnings)

    def test_render_summary_shows_not_ready_by_default(self, tmp_path):
        _write_week(tmp_path, "2026-17", [
            _sample_block(1, symbol="XAUUSD", tf="H1", checked="v2"),
        ])
        result = mod.parse_all(tmp_path)
        rendered = mod.render_summary(result)
        assert "Total classified:" in rendered
        assert "NOT READY" in rendered
        # 1/100 — should cite the total_classified gate.
        assert "total_classified 1" in rendered

    def test_render_summary_headers_present(self, tmp_path):
        _write_week(tmp_path, "2026-17", [
            _sample_block(1, checked="v2"),
            _sample_block(2, checked="v1"),
        ])
        result = mod.parse_all(tmp_path)
        rendered = mod.render_summary(result)
        assert "# Divergence classification summary" in rendered
        assert "## Per-outcome" in rendered
        assert "## Per-instrument" in rendered
        assert "## Per-timeframe" in rendered
        assert "## Promotion gate" in rendered


# ---------------------------------------------------------------------------
# 5) Label-to-category mapping
# ---------------------------------------------------------------------------


class TestLabelMapping:

    def test_v1_label(self):
        assert mod._label_to_category("v1 correct (bullish was right)") == "v1_correct"

    def test_v2_label(self):
        assert mod._label_to_category("v2 correct (bearish was right)") == "v2_correct"

    def test_both_wrong_label(self):
        assert mod._label_to_category("both wrong (should have been transitional)") == "both_wrong"

    def test_ambiguous_label(self):
        assert mod._label_to_category("ambiguous (could go either way)") == "ambiguous"

    def test_case_insensitive(self):
        assert mod._label_to_category("V1 Correct") == "v1_correct"

    def test_unknown_returns_none(self):
        assert mod._label_to_category("gibberish") is None
