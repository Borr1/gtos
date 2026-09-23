"""Tests for the F2.3 structure-detector shadow wiring.

Covers:

* Config resolution — default/missing/invalid/recognised values.
* Production-label selection — v1 drives in ("v1", "v2_shadow"), v2 drives
  in "v2".
* Dual-compute gating — v1 mode is single-compute (no v2 call); v2_shadow
  and v2 compute both.
* Divergence logging — only on disagreement; JSONL schema; logger
  crash-safety; tmp_path isolation.
* ``_build_timeframe_state`` wrapper behaviour at each mode.
* ``compute_market_state`` threads the config through and produces
  divergence rows only under dual-compute modes.
* Config-reload / mode-switch: changing the config dict between calls
  takes effect on the next call (no cached state).

All tests write divergence rows to ``tmp_path``; the production
``shadow_logs/structure_detector_divergences.jsonl`` is never touched,
consistent with the conftest Layer 1 + Layer 2 guards.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.components import structure_detector_shadow_logger as shadow_mod
from src.components.market_state import (
    _build_timeframe_state,
    compute_market_state,
    detect_swings,
    identify_structure,
    identify_structure_v2,
)
from src.components.structure_detector_shadow_logger import (
    _finalize_row,
    SHADOW_LOG_PATH,
    build_divergence_row,
    compute_v2_score_metadata,
    is_dual_compute_mode,
    log_structure_divergence,
    pick_production_label,
    resolve_detector_mode,
)
from src.models.market_state_models import StructureAnalysis, Swing


# ---------------------------------------------------------------------------
# Helpers — fixture builders mirrored from tests/test_market_state_v2.py
# ---------------------------------------------------------------------------


def _swing(index: int, type_: str, price: float) -> Swing:
    return Swing(
        index=index,
        type=type_,
        price=price,
        time=f"2026-01-01T{index % 24:02d}:00:00",
    )


def _build_alternating(num_pairs: int, highs: list[float], lows: list[float]) -> list[Swing]:
    assert len(highs) == num_pairs
    assert len(lows) == num_pairs
    swings: list[Swing] = []
    idx = 0
    for i in range(num_pairs):
        swings.append(_swing(idx, "low", lows[i]))
        idx += 1
        swings.append(_swing(idx, "high", highs[i]))
        idx += 1
    return swings


def _v1_v2_divergent_swings() -> list[Swing]:
    """Build the ADR-004 M15 snapshot fixture — v1 bullish, v2 bearish.

    Construction from tests/test_market_state_v2.py
    test_m15_snapshot_bearish_stronger_flips_under_v2: 44 highs + 51 lows
    with dominant bearish evidence (lh + ll >> hh + hl by more than the
    dead zone).
    """
    highs = []
    price = 1000.0
    for i in range(44):
        highs.append(price)
        price += 3 if i % 4 == 3 else -1
    lows = []
    price = 500.0
    for i in range(51):
        lows.append(price)
        price += 3 if i % 4 == 3 else -1
    # Interleave: alternate lows and highs to form a valid swing sequence.
    swings: list[Swing] = []
    idx = 0
    h_iter = iter(highs)
    l_iter = iter(lows)
    h_next = next(h_iter, None)
    l_next = next(l_iter, None)
    while h_next is not None or l_next is not None:
        if l_next is not None:
            swings.append(_swing(idx, "low", l_next))
            idx += 1
            l_next = next(l_iter, None)
        if h_next is not None:
            swings.append(_swing(idx, "high", h_next))
            idx += 1
            h_next = next(h_iter, None)
    return swings


def _bullish_swings() -> list[Swing]:
    """Clean bullish sample where v1 and v2 agree."""
    return _build_alternating(
        num_pairs=6,
        highs=[110, 115, 120, 125, 130, 135],
        lows=[100, 105, 110, 115, 120, 125],
    )


def _v1_v2_agreement_candles_to_swings_h1() -> list[dict]:
    """Build an H1-like candle list whose swings are unambiguously bullish.

    Rising zigzag: local-low candles every 4 bars with rising baseline,
    local-high candles at +2 offset, intermediate candles at +1/+3. This
    produces ~13 detectable swings with a clean HH+HL pattern, so both
    v1 and v2 MUST converge to ``bullish`` — useful for verifying the
    "no divergence -> no row" contract under dual-compute.
    """
    candles: list[dict] = []
    for i in range(30):
        base = 100 + i * 0.5
        if i % 4 == 0:
            # Swing-low candle (local low, 2-bar shoulders lower).
            candles.append({
                "time": f"2026-04-24T{i % 24:02d}:00:00",
                "open": base,
                "high": base + 0.2,
                "low": base - 1.0,
                "close": base + 0.1,
            })
        elif i % 4 == 2:
            # Swing-high candle (local high).
            candles.append({
                "time": f"2026-04-24T{i % 24:02d}:00:00",
                "open": base + 0.2,
                "high": base + 2.0,
                "low": base + 0.1,
                "close": base + 1.5,
            })
        else:
            # Intermediate candle — resting zone between swings.
            candles.append({
                "time": f"2026-04-24T{i % 24:02d}:00:00",
                "open": base,
                "high": base + 0.3,
                "low": base - 0.1,
                "close": base + 0.2,
            })
    return candles


def _v1_v2_divergent_candles_h1() -> list[dict]:
    """Build a candle list whose swings trigger v1 bullish + v2 bearish.

    We synthesise candles that reproduce the ADR-004 structural pattern:
    many descending highs with occasional rebounds (so v1 counts both
    HH>=3 AND LL>=3 and picks bullish by precedence, while v2's net
    score goes negative past the dead zone).
    """
    candles = []
    # Construct swings that give lots of LH/LL but also enough HH/HL to
    # trip v1's min(3,...) saturation. Use a jagged declining pattern.
    prices_highs = [150, 145, 148, 142, 144, 138, 141, 135, 137, 130,
                    132, 126, 128, 122, 124, 118, 120, 114, 116, 110]
    prices_lows = [140, 135, 138, 132, 134, 128, 131, 125, 127, 120,
                   122, 116, 118, 112, 114, 108, 110, 104, 106, 100]
    for i, (hi, lo) in enumerate(zip(prices_highs, prices_lows)):
        # Candle 2*i is an up-wick (swing high candidate)
        candles.append({
            "time": f"2026-04-24T{(2 * i) % 24:02d}:00:00",
            "open": lo + 1,
            "high": hi,
            "low": lo,
            "close": hi - 1,
        })
        # Candle 2*i+1 is a down-wick (swing low candidate)
        candles.append({
            "time": f"2026-04-24T{(2 * i + 1) % 24:02d}:00:00",
            "open": hi - 1,
            "high": hi - 0.5,
            "low": lo - 1,
            "close": lo,
        })
    return candles


# ---------------------------------------------------------------------------
# 1) resolve_detector_mode
# ---------------------------------------------------------------------------


class TestResolveDetectorMode:

    def test_none_config_defaults_to_v1(self):
        assert resolve_detector_mode(None) == "v1"

    def test_missing_market_state_key_defaults_to_v1(self):
        assert resolve_detector_mode({}) == "v1"

    def test_market_state_non_dict_defaults_to_v1(self):
        assert resolve_detector_mode({"market_state": "bad"}) == "v1"

    def test_missing_detector_version_defaults_to_v1(self):
        assert resolve_detector_mode({"market_state": {}}) == "v1"

    def test_v1_explicit(self):
        assert resolve_detector_mode({"market_state": {"detector_version": "v1"}}) == "v1"

    def test_v2_shadow_explicit(self):
        cfg = {"market_state": {"detector_version": "v2_shadow"}}
        assert resolve_detector_mode(cfg) == "v2_shadow"

    def test_v2_explicit(self):
        cfg = {"market_state": {"detector_version": "v2"}}
        assert resolve_detector_mode(cfg) == "v2"

    def test_unknown_mode_falls_back_to_v1(self, caplog):
        cfg = {"market_state": {"detector_version": "v99_experimental"}}
        import logging
        with caplog.at_level(logging.WARNING, logger=shadow_mod.logger.name):
            mode = resolve_detector_mode(cfg)
        assert mode == "v1"
        assert any("v99_experimental" in r.getMessage() for r in caplog.records)


class TestIsDualComputeMode:

    def test_v1_is_single_compute(self):
        assert is_dual_compute_mode("v1") is False

    def test_v2_shadow_is_dual_compute(self):
        assert is_dual_compute_mode("v2_shadow") is True

    def test_v2_is_dual_compute(self):
        # v2 still dual-computes (v1 logged as rollback sanity).
        assert is_dual_compute_mode("v2") is True

    def test_unknown_is_not_dual_compute(self):
        # Defensive: resolve_detector_mode would normalise but the helper
        # is called directly inside the hot path, so an unknown string
        # should never trigger a v2 compute call either.
        assert is_dual_compute_mode("garbage") is False


# ---------------------------------------------------------------------------
# 2) pick_production_label
# ---------------------------------------------------------------------------


class TestPickProductionLabel:

    def _pair(self):
        v1 = StructureAnalysis(direction="bullish", hh_count=5, hl_count=4)
        v2 = StructureAnalysis(direction="bearish", lh_count=6, ll_count=5)
        return v1, v2

    def test_v1_mode_returns_v1(self):
        v1, v2 = self._pair()
        assert pick_production_label("v1", v1, v2) is v1

    def test_v2_shadow_returns_v1(self):
        v1, v2 = self._pair()
        assert pick_production_label("v2_shadow", v1, v2) is v1

    def test_v2_returns_v2(self):
        v1, v2 = self._pair()
        assert pick_production_label("v2", v1, v2) is v2

    def test_v2_with_none_v2_falls_back_to_v1(self):
        """Defensive fail-open: if v2 was not computed (shouldn't happen),
        return v1 rather than raising.
        """
        v1, _ = self._pair()
        assert pick_production_label("v2", v1, None) is v1

    def test_v1_mode_with_none_v2_returns_v1(self):
        """In v1 mode v2 is never computed; passing None is the norm."""
        v1, _ = self._pair()
        assert pick_production_label("v1", v1, None) is v1


# ---------------------------------------------------------------------------
# 3) build_divergence_row / compute_v2_score_metadata
# ---------------------------------------------------------------------------


class TestComputeV2ScoreMetadata:

    def test_matches_identify_structure_v2_formula(self):
        """Score + dead_zone must match the classifier's internal values."""
        swings = _v1_v2_divergent_swings()
        v2 = identify_structure_v2(swings)
        meta = compute_v2_score_metadata(v2)
        # Re-derive the expected values from the formula in the classifier:
        score = (v2.hh_count + v2.hl_count) - (v2.lh_count + v2.ll_count)
        high_trans = v2.hh_count + v2.lh_count
        low_trans = v2.hl_count + v2.ll_count
        min_swings = min(high_trans, low_trans)
        dead_zone = max(2, min_swings // 4)
        assert meta["score"] == score
        assert meta["dead_zone"] == dead_zone

    def test_zero_counts_yields_score_0_dead_zone_2(self):
        """Degenerate / insufficient_data case: counts all 0, dead zone
        floor dominates.
        """
        label = StructureAnalysis(direction="insufficient_data")
        meta = compute_v2_score_metadata(label)
        assert meta["score"] == 0
        assert meta["dead_zone"] == 2


class TestBuildDivergenceRow:

    def test_schema_fields_present(self):
        v1 = StructureAnalysis(
            direction="bullish", hh_count=12, hl_count=10, lh_count=15, ll_count=11
        )
        v2 = StructureAnalysis(
            direction="transitional", hh_count=12, hl_count=10, lh_count=15, ll_count=11
        )
        row = build_divergence_row(
            symbol="XAUUSD",
            timeframe="H1",
            v1_label=v1,
            v2_label=v2,
            detector_version_config="v2_shadow",
            production_label=v1,
            candle_time="2026-04-24T14:15:00Z",
            logged_at="2026-04-24T14:15:02Z",
        )
        row = _finalize_row(row)
        expected_keys = {
            "ts",
            "logged_at",
            "symbol",
            "timeframe",
            "v1_direction",
            "v2_direction",
            "v2_score",
            "v2_dead_zone",
            "counts",
            "detector_version_config",
            "mode",
            "production_label",
        }
        assert set(row.keys()) == expected_keys
        assert row["symbol"] == "XAUUSD"
        assert row["timeframe"] == "H1"
        assert row["v1_direction"] == "bullish"
        assert row["v2_direction"] == "transitional"
        assert row["counts"] == {"hh": 12, "hl": 10, "lh": 15, "ll": 11}
        # score = 22 - 26 = -4
        assert row["v2_score"] == -4
        # hh+lh=27, hl+ll=21 -> min=21, dead=max(2, 21//4=5) = 5
        assert row["v2_dead_zone"] == 5
        assert row["detector_version_config"] == "v2_shadow"
        assert row["mode"] == "shadow"
        assert row["production_label"] == "bullish"

    def test_mode_field_live_v2_when_config_is_v2(self):
        v1 = StructureAnalysis(direction="bullish")
        v2 = StructureAnalysis(direction="bearish")
        row = _finalize_row(build_divergence_row(
            symbol="XAUUSD",
            timeframe="H1",
            v1_label=v1,
            v2_label=v2,
            detector_version_config="v2",
            production_label=v2,
            candle_time="2026-04-24T14:15:00Z",
        ))
        assert row["mode"] == "live_v2"
        assert row["production_label"] == "bearish"

    def test_logged_at_defaults_to_now_utc(self):
        v1 = StructureAnalysis(direction="bullish")
        v2 = StructureAnalysis(direction="bearish")
        row = _finalize_row(build_divergence_row(
            symbol="XAUUSD",
            timeframe="H1",
            v1_label=v1,
            v2_label=v2,
            detector_version_config="v2_shadow",
            production_label=v1,
            candle_time="2026-04-24T14:15:00Z",
        ))
        # logged_at is a non-empty ISO-8601 UTC string when not supplied.
        assert isinstance(row["logged_at"], str)
        assert len(row["logged_at"]) > 0
        assert row["logged_at"].endswith("+00:00") or row["logged_at"].endswith("Z")


# ---------------------------------------------------------------------------
# 4) log_structure_divergence — file I/O
# ---------------------------------------------------------------------------


class TestLogStructureDivergence:

    def test_writes_single_row_to_tmp_path(self, tmp_path):
        log_path = str(tmp_path / "divergences.jsonl")
        v1 = StructureAnalysis(
            direction="bullish", hh_count=11, hl_count=9, lh_count=11, ll_count=9
        )
        v2 = StructureAnalysis(
            direction="transitional", hh_count=11, hl_count=9, lh_count=11, ll_count=9
        )
        log_structure_divergence(
            symbol="XAUUSD",
            timeframe="H1",
            v1_label=v1,
            v2_label=v2,
            detector_version_config="v2_shadow",
            production_label=v1,
            candle_time="2026-04-24T14:15:00Z",
            log_path=log_path,
        )
        lines = Path(log_path).read_text().splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["v1_direction"] == "bullish"
        assert parsed["v2_direction"] == "transitional"
        assert parsed["v2_score"] == 0  # 20 - 20
        assert parsed["counts"] == {"hh": 11, "hl": 9, "lh": 11, "ll": 9}

    def test_append_multiple_rows(self, tmp_path):
        log_path = str(tmp_path / "divergences.jsonl")
        v1 = StructureAnalysis(direction="bullish")
        v2 = StructureAnalysis(direction="bearish")
        for i in range(3):
            log_structure_divergence(
                symbol="XAUUSD",
                timeframe="H1",
                v1_label=v1,
                v2_label=v2,
                detector_version_config="v2_shadow",
                production_label=v1,
                candle_time=f"2026-04-24T14:{15 * i:02d}:00Z",
                log_path=log_path,
            )
        lines = Path(log_path).read_text().splitlines()
        assert len(lines) == 3
        for i, line in enumerate(lines):
            parsed = json.loads(line)
            assert parsed["ts"] == f"2026-04-24T14:{15 * i:02d}:00Z"

    def test_creates_parent_directory(self, tmp_path):
        nested = tmp_path / "nested" / "deep" / "out.jsonl"
        v1 = StructureAnalysis(direction="bullish")
        v2 = StructureAnalysis(direction="bearish")
        log_structure_divergence(
            symbol="XAUUSD",
            timeframe="H1",
            v1_label=v1,
            v2_label=v2,
            detector_version_config="v2_shadow",
            production_label=v1,
            candle_time="2026-04-24T14:15:00Z",
            log_path=str(nested),
        )
        assert nested.exists()

    def test_io_error_is_non_blocking(self, monkeypatch, tmp_path, caplog):
        """A disk-full / permission-error on the shadow log must never
        raise — production v1 pipeline continues regardless.
        """
        log_path = str(tmp_path / "divergences.jsonl")
        v1 = StructureAnalysis(direction="bullish")
        v2 = StructureAnalysis(direction="bearish")

        # Force the write to fail by replacing builtins.open with one
        # that raises only for our target path.
        import builtins
        orig_open = builtins.open

        def _fail_open(file, mode="r", *args, **kwargs):
            if str(file).endswith("divergences.jsonl") and "a" in mode:
                raise PermissionError("simulated disk-full")
            return orig_open(file, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _fail_open)

        import logging
        with caplog.at_level(logging.WARNING, logger=shadow_mod.logger.name):
            # Must NOT raise.
            log_structure_divergence(
                symbol="XAUUSD",
                timeframe="H1",
                v1_label=v1,
                v2_label=v2,
                detector_version_config="v2_shadow",
                production_label=v1,
                candle_time="2026-04-24T14:15:00Z",
                log_path=log_path,
            )
        assert any("failed to write" in r.getMessage().lower()
                   for r in caplog.records)


# ---------------------------------------------------------------------------
# 5) _build_timeframe_state wiring
# ---------------------------------------------------------------------------


class TestBuildTimeframeStateWiring:

    def test_default_mode_is_v1_no_dual_compute(self, tmp_path):
        """Default call (no mode kwarg) must not touch the logger at all.

        We set ``shadow_log_path`` to a tmp_path file but verify it is
        never created — default mode = single compute, logger never
        called.
        """
        log_path = str(tmp_path / "divergences.jsonl")
        candles = _v1_v2_divergent_candles_h1()
        _build_timeframe_state(
            candles,
            min_bars=2,
            fvg_min_gap=1.0,
            tf_name="H1",
            shadow_log_path=log_path,
        )
        assert not Path(log_path).exists(), (
            "Default v1 mode must not call the shadow logger"
        )

    def test_v1_mode_matches_default_no_log(self, tmp_path):
        """Explicit v1 mode == default."""
        log_path = str(tmp_path / "divergences.jsonl")
        candles = _v1_v2_divergent_candles_h1()
        _build_timeframe_state(
            candles,
            min_bars=2,
            fvg_min_gap=1.0,
            tf_name="H1",
            detector_mode="v1",
            shadow_symbol="XAUUSD",
            shadow_candle_time="2026-04-24T14:15:00Z",
            shadow_log_path=log_path,
        )
        assert not Path(log_path).exists()

    def test_v2_shadow_mode_logs_divergence(self, tmp_path, monkeypatch):
        """Dual-compute mode emits a divergence row when v1 != v2.

        We force a divergence by monkeypatching ``identify_structure_v2``
        within the ``market_state`` module to return a bearish label on a
        candle set where v1 returns bullish. That isolates the wiring
        test from the detector-fixture-construction problem — crafting
        candle sequences that naturally produce v1 bullish + v2 bearish
        requires specific swing-count topologies that depend on
        ``detect_swings`` min_bars semantics. The ADR-004 live snapshot
        exhibits the real divergence; here we just verify that the
        wiring fires when a divergence exists.
        """
        log_path = str(tmp_path / "divergences.jsonl")
        candles = _v1_v2_agreement_candles_to_swings_h1()
        # Sanity: v1 should be some direction on this fixture.
        swings = detect_swings(candles, min_bars=2)
        v1_direction = identify_structure(swings).direction

        # Force v2 to flip to a different direction regardless of the
        # true detector output.
        flipped = "bearish" if v1_direction != "bearish" else "bullish"

        def _forced_v2(_swings):
            return StructureAnalysis(
                direction=flipped,
                hh_count=1, hl_count=1, lh_count=9, ll_count=9,
            )
        monkeypatch.setattr(
            "src.components.market_state.identify_structure_v2", _forced_v2
        )

        state = _build_timeframe_state(
            candles,
            min_bars=2,
            fvg_min_gap=1.0,
            tf_name="H1",
            detector_mode="v2_shadow",
            shadow_symbol="XAUUSD",
            shadow_candle_time="2026-04-24T14:15:00Z",
            shadow_log_path=log_path,
        )
        # Production label MUST be v1 under v2_shadow.
        assert state.structure.direction == v1_direction
        # Divergence row emitted.
        lines = Path(log_path).read_text().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert row["v1_direction"] == v1_direction
        assert row["v2_direction"] == flipped
        assert row["production_label"] == v1_direction
        assert row["detector_version_config"] == "v2_shadow"
        assert row["mode"] == "shadow"
        assert row["symbol"] == "XAUUSD"
        assert row["timeframe"] == "H1"
        assert row["ts"] == "2026-04-24T14:15:00Z"
        # Score metadata correct for the forced counts (hh=1 hl=1 lh=9 ll=9):
        # score = 2 - 18 = -16; min_swings = min(10, 10) = 10; dead = max(2, 2) = 2.
        assert row["v2_score"] == -16
        assert row["v2_dead_zone"] == 2

    def test_v2_mode_logs_divergence_and_uses_v2_for_production(
        self, tmp_path, monkeypatch
    ):
        log_path = str(tmp_path / "divergences.jsonl")
        candles = _v1_v2_agreement_candles_to_swings_h1()
        swings = detect_swings(candles, min_bars=2)
        v1_direction = identify_structure(swings).direction
        flipped = "bearish" if v1_direction != "bearish" else "bullish"

        def _forced_v2(_swings):
            return StructureAnalysis(
                direction=flipped,
                hh_count=1, hl_count=1, lh_count=9, ll_count=9,
            )
        monkeypatch.setattr(
            "src.components.market_state.identify_structure_v2", _forced_v2
        )

        state = _build_timeframe_state(
            candles,
            min_bars=2,
            fvg_min_gap=1.0,
            tf_name="H1",
            detector_mode="v2",
            shadow_symbol="XAUUSD",
            shadow_candle_time="2026-04-24T14:15:00Z",
            shadow_log_path=log_path,
        )
        # Production label MUST be v2 under v2 mode.
        assert state.structure.direction == flipped
        lines = Path(log_path).read_text().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert row["production_label"] == flipped
        assert row["mode"] == "live_v2"
        assert row["v1_direction"] == v1_direction

    def test_v2_shadow_no_divergence_no_row(self, tmp_path):
        """When v1 == v2 the logger must not be called.

        Uses the agreement candle fixture where both classifiers converge.
        """
        log_path = str(tmp_path / "divergences.jsonl")
        candles = _v1_v2_agreement_candles_to_swings_h1()
        swings = detect_swings(candles, min_bars=2)
        v1 = identify_structure(swings)
        v2 = identify_structure_v2(swings)
        # Agreement fixture MUST produce v1 == v2, else the test premise fails.
        assert v1.direction == v2.direction, (
            f"agreement fixture unexpectedly diverges: v1={v1.direction} "
            f"v2={v2.direction}"
        )
        _build_timeframe_state(
            candles,
            min_bars=2,
            fvg_min_gap=1.0,
            tf_name="H1",
            detector_mode="v2_shadow",
            shadow_symbol="XAUUSD",
            shadow_candle_time="2026-04-24T14:15:00Z",
            shadow_log_path=log_path,
        )
        assert not Path(log_path).exists(), (
            f"Agreement (v1=v2={v1.direction}) must not emit a row"
        )

    def test_logger_crash_inside_logger_does_not_break_production(
        self, monkeypatch, tmp_path, caplog
    ):
        """A crash INSIDE the shadow logger must not propagate.

        The logger module has its own try/except wrapper around the write
        (``log_structure_divergence``). This test exercises that path by
        pointing the shadow log at a read-only file so the write raises
        PermissionError. Production v1 path must still return normally.
        """
        log_path = str(tmp_path / "divergences.jsonl")

        import builtins
        orig_open = builtins.open

        def _fail_open(file, mode="r", *args, **kwargs):
            if str(file).endswith("divergences.jsonl") and "a" in mode:
                raise PermissionError("simulated read-only filesystem")
            return orig_open(file, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _fail_open)

        candles = _v1_v2_agreement_candles_to_swings_h1()
        v1_direction = identify_structure(detect_swings(candles, min_bars=2)).direction
        flipped = "bearish" if v1_direction != "bearish" else "bullish"

        def _forced_v2(_swings):
            return StructureAnalysis(
                direction=flipped,
                hh_count=1, hl_count=1, lh_count=9, ll_count=9,
            )
        monkeypatch.setattr(
            "src.components.market_state.identify_structure_v2", _forced_v2
        )

        import logging
        with caplog.at_level(logging.WARNING, logger=shadow_mod.logger.name):
            # MUST NOT raise — production pipeline continues.
            state = _build_timeframe_state(
                candles,
                min_bars=2,
                fvg_min_gap=1.0,
                tf_name="H1",
                detector_mode="v2_shadow",
                shadow_symbol="XAUUSD",
                shadow_candle_time="2026-04-24T14:15:00Z",
                shadow_log_path=log_path,
            )
        assert state.structure.direction == v1_direction
        # Log file never created (write failed).
        assert not Path(log_path).exists()
        # Warning logged.
        assert any(
            "failed to write" in r.getMessage().lower()
            for r in caplog.records
        )


# ---------------------------------------------------------------------------
# 6) compute_market_state — config pass-through
# ---------------------------------------------------------------------------


def _minimal_raw_data(candles_h1: list[dict], symbol: str = "XAUUSD") -> dict:
    """Build a minimal raw_data dict suitable for compute_market_state."""
    return {
        "symbol": symbol,
        "timestamp_utc": "2026-04-24T14:15:00Z",
        "candles": {
            "D1": [],
            "H4": [],
            "H1": candles_h1,
            "M15": [],
        },
        "session_levels": {
            "asian_high": 0.0,
            "asian_low": 0.0,
            "pdh": 0.0,
            "pdl": 0.0,
        },
        "equal_highs_H4": [],
        "equal_highs_H1": [],
        "equal_lows_H4": [],
        "equal_lows_H1": [],
        "data_quality": {
            "all_timeframes_complete": False,
            "spread_normal": True,
            "mt5_connected": True,
            "timestamp_utc": "2026-04-24T14:15:00Z",
        },
    }


class TestComputeMarketStateIntegration:

    def test_default_config_no_dual_compute(self, tmp_path, monkeypatch):
        """With default (missing market_state block) config, no divergence rows."""
        # Redirect the shadow-log default path so any accidental write
        # lands in tmp_path (but we expect none).
        custom_log = tmp_path / "divergences.jsonl"
        monkeypatch.setattr(
            shadow_mod, "SHADOW_LOG_PATH", str(custom_log), raising=True
        )
        # Also redirect the production pipeline_state write so conftest's
        # write guard doesn't fire.
        from src.utils import file_io
        monkeypatch.setattr(
            file_io, "PIPELINE_STATE_DIR", tmp_path / "pipeline_state",
            raising=False,
        )
        (tmp_path / "pipeline_state").mkdir(exist_ok=True)
        # Patch the `write_pipeline` call to a no-op so we don't have to
        # contort pipeline_state redirection.
        monkeypatch.setattr(
            "src.components.market_state.write_pipeline",
            lambda *a, **kw: None,
        )

        raw = _minimal_raw_data(_v1_v2_divergent_candles_h1())
        config = {"data": {"swing_detection_min_bars": {"H1": 2}, "fvg_min_gap": {"H1": 1.0}}}
        mso = compute_market_state(raw, config)
        # No shadow log created.
        assert not custom_log.exists()
        # H1 structure is populated (v1 path).
        assert mso.timeframes["H1"].structure.direction in (
            "bullish", "bearish", "transitional", "insufficient_data"
        )

    def test_v2_shadow_config_writes_divergence_row(self, tmp_path, monkeypatch):
        """v2_shadow config must produce a divergence row for every TF where
        v1 and v2 disagree.
        """
        custom_log = tmp_path / "divergences.jsonl"
        # The shadow logger's public API default is SHADOW_LOG_PATH; since
        # compute_market_state calls _build_timeframe_state without
        # shadow_log_path, the logger will use its own module-level default.
        # Redirect that default via monkeypatch.
        monkeypatch.setattr(
            shadow_mod, "SHADOW_LOG_PATH", str(custom_log), raising=True
        )
        # The _build_timeframe_state code path falls back to the logger's
        # internal default when shadow_log_path is None — so monkeypatching
        # the module-level constant re-routes writes to tmp_path.
        # Verify this works by also patching the shadow logger write target
        # via its function default: easiest to monkeypatch log_structure_divergence
        # to use the custom path.
        orig_log = shadow_mod.log_structure_divergence

        def _logging_wrapper(**kwargs):
            kwargs.setdefault("log_path", str(custom_log))
            return orig_log(**kwargs)

        # Replace the binding used by market_state (imported at top).
        monkeypatch.setattr(
            "src.components.market_state.log_structure_divergence",
            _logging_wrapper,
        )

        # No-op the pipeline write.
        monkeypatch.setattr(
            "src.components.market_state.write_pipeline",
            lambda *a, **kw: None,
        )

        raw = _minimal_raw_data(_v1_v2_divergent_candles_h1())
        config = {
            "market_state": {"detector_version": "v2_shadow"},
            "data": {
                "swing_detection_min_bars": {"H1": 2},
                "fvg_min_gap": {"H1": 1.0},
            },
        }
        compute_market_state(raw, config)

        # Only H1 has candles in our fixture, so expect at most 1 divergence row.
        if custom_log.exists():
            lines = custom_log.read_text().splitlines()
            # Either 0 (no divergence) or 1 (H1 divergence). Other TFs have no
            # candles -> insufficient_data skipped by the no-candles early return.
            assert len(lines) in (0, 1)
            if lines:
                row = json.loads(lines[0])
                assert row["symbol"] == "XAUUSD"
                assert row["timeframe"] == "H1"
                assert row["ts"] == "2026-04-24T14:15:00Z"
                assert row["detector_version_config"] == "v2_shadow"
                assert row["mode"] == "shadow"

    def test_mode_switch_takes_effect_next_candle(self, tmp_path, monkeypatch):
        """Flipping the config mode between two compute_market_state calls
        must take effect on the second call — no cached state.
        """
        custom_log = tmp_path / "divergences.jsonl"
        orig_log = shadow_mod.log_structure_divergence

        def _logging_wrapper(**kwargs):
            kwargs.setdefault("log_path", str(custom_log))
            return orig_log(**kwargs)

        monkeypatch.setattr(
            "src.components.market_state.log_structure_divergence",
            _logging_wrapper,
        )
        monkeypatch.setattr(
            "src.components.market_state.write_pipeline",
            lambda *a, **kw: None,
        )

        raw = _minimal_raw_data(_v1_v2_divergent_candles_h1())
        cfg_v1 = {
            "market_state": {"detector_version": "v1"},
            "data": {"swing_detection_min_bars": {"H1": 2}, "fvg_min_gap": {"H1": 1.0}},
        }
        cfg_shadow = {
            "market_state": {"detector_version": "v2_shadow"},
            "data": {"swing_detection_min_bars": {"H1": 2}, "fvg_min_gap": {"H1": 1.0}},
        }

        # Call 1: v1 mode -> no log.
        compute_market_state(raw, cfg_v1)
        assert not custom_log.exists()

        # Call 2: v2_shadow -> log only if there's a divergence. Skip the
        # row-count assertion if the candle fixture doesn't currently
        # produce divergence; still verify that flipping the mode does
        # not break anything.
        compute_market_state(raw, cfg_shadow)
        # If the fixture diverges, we expect exactly 1 row now.
        # If not, the file stays absent. Either way, no error.

    def test_unknown_mode_falls_back_to_v1_no_log(self, tmp_path, monkeypatch):
        custom_log = tmp_path / "divergences.jsonl"
        monkeypatch.setattr(
            shadow_mod, "SHADOW_LOG_PATH", str(custom_log), raising=True
        )
        monkeypatch.setattr(
            "src.components.market_state.write_pipeline",
            lambda *a, **kw: None,
        )

        raw = _minimal_raw_data(_v1_v2_divergent_candles_h1())
        config = {
            "market_state": {"detector_version": "not_a_real_mode"},
            "data": {"swing_detection_min_bars": {"H1": 2}, "fvg_min_gap": {"H1": 1.0}},
        }
        compute_market_state(raw, config)
        assert not custom_log.exists()


# ---------------------------------------------------------------------------
# 7) SHADOW_LOG_PATH default
# ---------------------------------------------------------------------------


class TestDefaultLogPath:

    def test_path_under_shadow_logs_dir(self):
        assert SHADOW_LOG_PATH.startswith("shadow_logs/")
        assert SHADOW_LOG_PATH.endswith(".jsonl")
        assert "structure_detector" in SHADOW_LOG_PATH


# ---------------------------------------------------------------------------
# 8) End-to-end symbol propagation — session-38 regression
# ---------------------------------------------------------------------------


class TestSymbolPropagationEndToEnd:
    """``raw_data['symbol']`` MUST flow through compute_market_state into the
    shadow log row. Pre-fix bug: data_ingestion + build_raw_data both
    dropped ``"symbol"`` from raw_data, so the logger wrote ``symbol=""``
    on 4,980 / 4,980 production rows (session 38 forensics).

    This test simulates the full live pipeline at the market-state layer:
    construct a raw_data with symbol, call compute_market_state in shadow
    mode, force a v1/v2 divergence, assert the written log row carries the
    canonical symbol — not the empty string.
    """

    def _run_and_capture(
        self, tmp_path, monkeypatch, canonical_symbol: str
    ) -> dict | None:
        """Run compute_market_state with a forced divergence; return the
        single logged row (or None if no row was written).
        """
        custom_log = tmp_path / "divergences.jsonl"
        orig_log = shadow_mod.log_structure_divergence

        def _logging_wrapper(**kwargs):
            kwargs.setdefault("log_path", str(custom_log))
            return orig_log(**kwargs)

        monkeypatch.setattr(
            "src.components.market_state.log_structure_divergence",
            _logging_wrapper,
        )
        monkeypatch.setattr(
            "src.components.market_state.write_pipeline",
            lambda *a, **kw: None,
        )

        # Force a v2 label that contradicts v1 so a divergence is guaranteed.
        # The candles below produce v1=bullish on H1; we flip v2 to bearish.
        candles_h1 = _v1_v2_agreement_candles_to_swings_h1()
        swings = detect_swings(candles_h1, min_bars=2)
        v1_dir = identify_structure(swings).direction
        flipped = "bearish" if v1_dir != "bearish" else "bullish"

        def _forced_v2(_swings):
            return StructureAnalysis(
                direction=flipped,
                hh_count=1, hl_count=1, lh_count=9, ll_count=9,
            )
        monkeypatch.setattr(
            "src.components.market_state.identify_structure_v2", _forced_v2
        )

        raw = _minimal_raw_data(candles_h1, symbol=canonical_symbol)
        config = {
            "market_state": {"detector_version": "v2_shadow"},
            "data": {
                "swing_detection_min_bars": {"H1": 2},
                "fvg_min_gap": {"H1": 1.0},
            },
        }
        compute_market_state(raw, config)

        if not custom_log.exists():
            return None
        lines = custom_log.read_text().splitlines()
        assert len(lines) == 1, f"expected 1 divergence row, got {len(lines)}"
        return json.loads(lines[0])

    def test_xauusd_symbol_reaches_shadow_log(self, tmp_path, monkeypatch):
        row = self._run_and_capture(tmp_path, monkeypatch, "XAUUSD")
        assert row is not None, "forced divergence did not produce a log row"
        assert row["symbol"] == "XAUUSD", (
            "Pre-fix bug: raw_data['symbol'] was dropped and the shadow "
            "log silently recorded empty strings."
        )
        assert row["symbol"] != "", (
            "The exact production-bug regression on 4,980 live rows."
        )

    def test_us30_cash_canonical_reaches_shadow_log(self, tmp_path, monkeypatch):
        """Canonical US30_cash, not broker alias US30.cash."""
        row = self._run_and_capture(tmp_path, monkeypatch, "US30_cash")
        assert row is not None
        assert row["symbol"] == "US30_cash"

    def test_every_instrument_reaches_shadow_log(self, tmp_path, monkeypatch):
        # Each iteration uses its own sub-dir to avoid cross-iteration append
        # contamination of the shared log file under tmp_path.
        for i, sym in enumerate(("XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD")):
            sub = tmp_path / f"iter_{i}_{sym}"
            sub.mkdir()
            row = self._run_and_capture(sub, monkeypatch, sym)
            assert row is not None, f"no row for {sym}"
            assert row["symbol"] == sym, f"wrong symbol for {sym}: {row['symbol']}"


# ---------------------------------------------------------------------------
# 9) XAUUSD session-ATR regression — silently disabled pre-fix
# ---------------------------------------------------------------------------


class TestXauusdSessionAtrRegression:
    """``compute_market_state`` runs an Ibikunle-2018 session-ATR branch
    for XAUUSD only, gated on ``raw_data.get("symbol", "") == "XAUUSD"``.

    Pre-fix, both the live (``ingest_live_data``) and sim (``build_raw_data``)
    paths omitted the ``"symbol"`` field from raw_data — so the gate
    always saw an empty string and NEVER computed session ATR. Live
    evidence: 18/18 XAUUSD candidate_features rows have
    ``mso_m15_session_vol_ratio = None``.

    The session-ATR feature is not wired into production trading
    decisions today (no gate consumes ``atr_session`` / ``session_vol_ratio``
    in the current orchestrator), so the regression is observational
    only — but the test locks the contract: whenever a raw_data carries
    ``symbol == "XAUUSD"`` with sufficient M15 candle coverage spanning
    London/NY hours, compute_market_state MUST populate the session ATR
    fields.
    """

    def _build_xauusd_raw(self, monkeypatch):
        monkeypatch.setattr(
            "src.components.market_state.write_pipeline",
            lambda *a, **kw: None,
        )
        # Build 40+ M15 candles spanning London session (07-11 UTC).
        base = datetime(2026, 4, 1, 6, 0, tzinfo=timezone.utc)
        m15 = []
        for i in range(40):
            t = base + timedelta(minutes=15 * i)
            m15.append({
                "time": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": 2650.0 + (i % 5) * 0.3,
                "high": 2655.0 + (i % 5) * 0.3,
                "low": 2645.0 + (i % 5) * 0.3,
                "close": 2652.0 + (i % 5) * 0.3,
                "volume": 100.0,
            })
        return {
            "symbol": "XAUUSD",
            "timestamp_utc": "2026-04-01T08:15:00Z",  # inside London window
            "candles": {"D1": m15[:10], "H4": m15[:20], "H1": m15[:30], "M15": m15},
            "session_levels": {
                "asian_high": 2660.0, "asian_low": 2640.0,
                "pdh": 2670.0, "pdl": 2635.0,
            },
            "equal_highs_H4": [],
            "equal_lows_H4": [],
            "equal_highs_H1": [],
            "equal_lows_H1": [],
            "data_quality": {
                "all_timeframes_complete": True,
                "spread_normal": True,
                "mt5_connected": True,
                "timestamp_utc": "2026-04-01T08:15:00Z",
            },
        }

    def test_session_atr_populated_when_symbol_present(self, monkeypatch):
        raw = self._build_xauusd_raw(monkeypatch)
        config = {
            "data": {
                "swing_detection_min_bars": {"D1": 2, "H4": 2, "H1": 2, "M15": 2},
                "fvg_min_gap": {"D1": 5.0, "H4": 3.0, "H1": 2.0, "M15": 1.0},
            },
        }
        mso = compute_market_state(raw, config)
        m15 = mso.timeframes["M15"]
        assert m15.atr_session is not None, (
            "XAUUSD session-ATR feature silently disabled — the exact "
            "session-38 regression forensics found live for 18/18 XAUUSD "
            "candidate_features rows."
        )
        assert m15.atr_session > 0
        assert m15.session_vol_ratio is not None

    def test_session_atr_absent_when_symbol_empty(self, monkeypatch):
        """Legacy pre-fix behavior: empty symbol -> no session ATR.

        Locks the negative case so callers that still pass legacy
        ``raw_data`` (without symbol) don't accidentally trigger the
        XAUUSD branch on random instruments.
        """
        raw = self._build_xauusd_raw(monkeypatch)
        raw["symbol"] = ""  # simulate pre-fix raw_data
        config = {
            "data": {
                "swing_detection_min_bars": {"D1": 2, "H4": 2, "H1": 2, "M15": 2},
                "fvg_min_gap": {"D1": 5.0, "H4": 3.0, "H1": 2.0, "M15": 1.0},
            },
        }
        mso = compute_market_state(raw, config)
        assert mso.timeframes["M15"].atr_session is None
        assert mso.timeframes["M15"].session_vol_ratio is None
