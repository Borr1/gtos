"""Tests for the V1 regime classifier (Wave 1 follow-up, observation-only).

Covers:

1. Insufficient / missing data fail-safes (return ``unclear``).
2. Trending bull H4 swing sequence -> ``trending_bull``.
3. Trending bear H4 swing sequence -> ``trending_bear``.
4. Mixed / weak swings -> ``chop``.
5. Recent counter-direction H4 BOS -> ``reversal_in_progress``.
6. Determinism: same MSO -> same label, repeat invariant.
7. Public-API + dataclass schema invariants.
8. Shadow logger:
   - happy-path JSONL write
   - tmp_path isolation
   - non-blocking on IO failure
   - candle_time fallback chain
   - row schema fields

All file IO is redirected to ``tmp_path`` per the conftest write-guard
contract; no production paths are written by this module.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pytest

from src.components.regime_classifier import (
    CLASSIFIER_VERSION,
    DEFAULT_LOOKBACK_H4,
    DEFAULT_MIN_SWINGS,
    RegimeClassification,
    classify_regime,
)
from src.components import regime_shadow_logger as shadow_mod
from src.components.regime_shadow_logger import (
    SHADOW_LOG_PATH,
    build_regime_row,
    log_classification,
)
from src.models.market_state_models import (
    DataQuality,
    MarketStateObject,
    SessionLevels,
    StructureAnalysis,
    StructureEvent,
    Swing,
    TimeframeState,
)


# ---------------------------------------------------------------------------
# Builder helpers — keep tests readable
# ---------------------------------------------------------------------------

def _swing(index: int, type_: str, price: float) -> Swing:
    return Swing(
        index=index,
        type=type_,
        price=price,
        time=f"2026-04-25T{index % 24:02d}:00:00",
    )


def _bullish_swings(num_pairs: int = 8) -> list[Swing]:
    """Build a clean rising-zigzag — every high is HH, every low is HL."""
    swings: list[Swing] = []
    idx = 0
    for i in range(num_pairs):
        swings.append(_swing(idx, "low", 100.0 + 2 * i))
        idx += 1
        swings.append(_swing(idx, "high", 105.0 + 2 * i))
        idx += 1
    return swings


def _bearish_swings(num_pairs: int = 8) -> list[Swing]:
    """Build a clean falling-zigzag — every low is LL, every high is LH."""
    swings: list[Swing] = []
    idx = 0
    for i in range(num_pairs):
        swings.append(_swing(idx, "high", 200.0 - 2 * i))
        idx += 1
        swings.append(_swing(idx, "low", 195.0 - 2 * i))
        idx += 1
    return swings


def _choppy_swings(num_pairs: int = 8) -> list[Swing]:
    """Build a balanced range-bound pattern.

    Score must land inside the dead zone — equal HH/LH on the highs
    side and equal HL/LL on the lows side. Easiest way: alternate
    higher/lower on each consecutive pair so HH followed by LH cancel,
    and HL followed by LL cancel.

    Pair sequence (high values): 110, 108, 110, 108, 110, 108, ...
    Pair sequence (low values):  100, 102, 100, 102, 100, 102, ...

    Highs: HH (108→110 means LH→HH alternation), LH, HH, LH, ...
    -> hh_count == lh_count over even num_pairs.
    Lows: same logic on the lows side -> hl_count == ll_count.
    Net score = (hh + hl) - (lh + ll) = 0 -> dead zone -> chop.
    """
    if num_pairs % 2:
        raise ValueError("_choppy_swings requires an even num_pairs")
    swings: list[Swing] = []
    idx = 0
    high_a, high_b = 110.0, 108.0
    low_a, low_b = 100.0, 102.0
    for i in range(num_pairs):
        lo = low_a if i % 2 == 0 else low_b
        hi = high_a if i % 2 == 0 else high_b
        swings.append(_swing(idx, "low", lo))
        idx += 1
        swings.append(_swing(idx, "high", hi))
        idx += 1
    return swings


def _build_h4_state(
    swings: list[Swing],
    *,
    direction: str = "bullish",
    atr_14: float = 1.0,
    structure_events: Optional[list[StructureEvent]] = None,
) -> TimeframeState:
    """Build a minimal H4 TimeframeState carrying the needed inputs."""
    structure = StructureAnalysis(
        direction=direction,  # type: ignore[arg-type]
        protected_swing=swings[-2] if len(swings) >= 2 else None,
        swing_sequence=[],
        hh_count=sum(1 for _ in range(len(swings) // 2)) if direction == "bullish" else 0,
        hl_count=sum(1 for _ in range(len(swings) // 2)) if direction == "bullish" else 0,
        lh_count=sum(1 for _ in range(len(swings) // 2)) if direction == "bearish" else 0,
        ll_count=sum(1 for _ in range(len(swings) // 2)) if direction == "bearish" else 0,
    )
    return TimeframeState(
        swings=list(swings),
        structure=structure,
        structure_events=list(structure_events or []),
        atr_14=atr_14,
        avg_candle_body=0.5,
    )


def _empty_h4_state() -> TimeframeState:
    return TimeframeState(
        structure=StructureAnalysis(direction="insufficient_data"),
    )


def _wrap_mso(h4_state: Optional[TimeframeState]) -> MarketStateObject:
    """Wrap a single H4 state into a minimal MSO."""
    timeframes: dict[str, TimeframeState] = {}
    if h4_state is not None:
        timeframes["H4"] = h4_state
    timeframes.setdefault("D1", _empty_h4_state())
    timeframes.setdefault("H1", _empty_h4_state())
    timeframes.setdefault("M15", _empty_h4_state())
    return MarketStateObject(
        timestamp_utc="2026-04-25T14:15:00Z",
        timeframes=timeframes,
        session_levels=SessionLevels(asian_high=0.0, asian_low=0.0, pdh=0.0, pdl=0.0),
        data_quality=DataQuality(
            all_timeframes_complete=True,
            spread_normal=True,
            mt5_connected=True,
            timestamp_utc="2026-04-25T14:15:00Z",
        ),
    )


# ---------------------------------------------------------------------------
# 1) Insufficient / missing data fail-safes
# ---------------------------------------------------------------------------


class TestInsufficientData:
    def test_none_mso_returns_unclear(self):
        result = classify_regime(None)
        assert isinstance(result, RegimeClassification)
        assert result.regime == "unclear"
        assert "MSO is None" in result.reason
        assert result.classifier_version == CLASSIFIER_VERSION

    def test_no_h4_timeframe_returns_unclear(self):
        # Build an MSO without any H4 entry.
        mso = MarketStateObject(
            timestamp_utc="2026-04-25T14:15:00Z",
            timeframes={"H1": _empty_h4_state()},
            session_levels=SessionLevels(asian_high=0.0, asian_low=0.0, pdh=0.0, pdl=0.0),
            data_quality=DataQuality(
                all_timeframes_complete=False,
                spread_normal=True,
                mt5_connected=True,
                timestamp_utc="2026-04-25T14:15:00Z",
            ),
        )
        result = classify_regime(mso)
        assert result.regime == "unclear"
        assert result.raw_features.get("reason_code") == "h4_missing"

    def test_too_few_swings_returns_unclear(self):
        # 2 swings (1 high + 1 low) — well below default min_swings=6.
        swings = [_swing(0, "low", 100.0), _swing(1, "high", 110.0)]
        mso = _wrap_mso(_build_h4_state(swings))
        result = classify_regime(mso)
        assert result.regime == "unclear"
        assert result.raw_features.get("reason_code") == "insufficient_swings"
        assert result.raw_features["swing_count"] == 2
        assert result.raw_features["min_swings_required"] == DEFAULT_MIN_SWINGS

    def test_explicit_min_swings_threshold_honored(self):
        # 6 swings is the default floor; with min_swings=10 the same input
        # falls below the threshold.
        swings = _bullish_swings(num_pairs=3)  # 6 swings total
        mso = _wrap_mso(_build_h4_state(swings))
        # Default => trending_bull.
        assert classify_regime(mso).regime == "trending_bull"
        # Bumped threshold => unclear.
        result = classify_regime(mso, min_swings=10)
        assert result.regime == "unclear"


# ---------------------------------------------------------------------------
# 2) Trending bull
# ---------------------------------------------------------------------------


class TestTrendingBull:
    def test_clean_rising_zigzag(self):
        swings = _bullish_swings(num_pairs=8)
        mso = _wrap_mso(_build_h4_state(swings))
        result = classify_regime(mso)
        assert result.regime == "trending_bull"
        assert result.raw_features["score"] > result.raw_features["dead_zone"]
        assert result.raw_features["h4_direction"] == "bullish"

    def test_score_metadata_populated(self):
        swings = _bullish_swings(num_pairs=10)
        mso = _wrap_mso(_build_h4_state(swings))
        result = classify_regime(mso)
        rf = result.raw_features
        # Every transition is HH or HL => no LH/LL.
        assert rf["lh"] == 0
        assert rf["ll"] == 0
        # Score = (hh + hl) - 0.
        assert rf["score"] == rf["hh"] + rf["hl"]


# ---------------------------------------------------------------------------
# 3) Trending bear
# ---------------------------------------------------------------------------


class TestTrendingBear:
    def test_clean_falling_zigzag(self):
        swings = _bearish_swings(num_pairs=8)
        mso = _wrap_mso(_build_h4_state(swings, direction="bearish"))
        result = classify_regime(mso)
        assert result.regime == "trending_bear"
        assert result.raw_features["score"] < -result.raw_features["dead_zone"]
        assert result.raw_features["h4_direction"] == "bearish"

    def test_no_hh_hl_in_bearish(self):
        swings = _bearish_swings(num_pairs=10)
        mso = _wrap_mso(_build_h4_state(swings, direction="bearish"))
        result = classify_regime(mso)
        rf = result.raw_features
        assert rf["hh"] == 0
        assert rf["hl"] == 0


# ---------------------------------------------------------------------------
# 4) Chop / mixed swings
# ---------------------------------------------------------------------------


class TestChop:
    def test_balanced_swings_collapse_to_chop(self):
        swings = _choppy_swings(num_pairs=8)
        mso = _wrap_mso(_build_h4_state(swings))
        result = classify_regime(mso)
        assert result.regime == "chop"
        # Score must sit inside the dead zone for transitional -> chop.
        assert abs(result.raw_features["score"]) <= result.raw_features["dead_zone"]

    def test_chop_reason_carries_displacement_metric(self):
        swings = _choppy_swings(num_pairs=8)
        mso = _wrap_mso(_build_h4_state(swings, atr_14=2.0))
        result = classify_regime(mso)
        assert result.regime == "chop"
        # raw_features must carry the displacement_atr_ratio for replay.
        assert "displacement_atr_ratio" in result.raw_features

    def test_v2_insufficient_data_reroutes_to_chop(self):
        # 6 highs + 1 low = 7 swings (above min_swings) but v2 needs >=2
        # of EACH side. Reaches the v2 insufficient_data branch and gets
        # routed to chop with a reason marker.
        swings: list[Swing] = []
        for i in range(6):
            swings.append(_swing(i, "high", 100.0 + i))
        swings.append(_swing(6, "low", 95.0))
        mso = _wrap_mso(_build_h4_state(swings))
        # min_swings default = 6, swing_count = 7 → passes the swing-count
        # gate; but v2 sees 6 highs + 1 low which is asymmetric and v2's
        # internal `len(lows) < 2` check trips → insufficient_data.
        result = classify_regime(mso, min_swings=6)
        assert result.regime == "chop"
        assert result.raw_features.get("reason_code") == "v2_insufficient"


# ---------------------------------------------------------------------------
# 5) Reversal in progress
# ---------------------------------------------------------------------------


class TestReversalInProgress:
    def test_recent_bullish_bos_against_bearish_structure(self):
        # Bearish base structure but a recent bullish BOS.
        swings = _bearish_swings(num_pairs=8)
        bullish_bos = StructureEvent(
            type="BOS",
            direction="bullish",  # opposite the bearish structure
            level_broken=swings[-1].price,
            close_price=swings[-1].price + 1.0,
            candle_index=swings[-1].index,
            time=swings[-1].time,
        )
        h4_state = _build_h4_state(
            swings,
            direction="bearish",
            structure_events=[bullish_bos],
        )
        result = classify_regime(_wrap_mso(h4_state))
        assert result.regime == "reversal_in_progress"
        assert result.raw_features["recent_counter_bos_direction"] == "bullish"

    def test_recent_bearish_bos_against_bullish_structure(self):
        swings = _bullish_swings(num_pairs=8)
        bearish_bos = StructureEvent(
            type="BOS",
            direction="bearish",
            level_broken=swings[-1].price,
            close_price=swings[-1].price - 1.0,
            candle_index=swings[-1].index,
            time=swings[-1].time,
        )
        h4_state = _build_h4_state(
            swings,
            direction="bullish",
            structure_events=[bearish_bos],
        )
        result = classify_regime(_wrap_mso(h4_state))
        assert result.regime == "reversal_in_progress"
        assert result.raw_features["recent_counter_bos_direction"] == "bearish"

    def test_old_counter_bos_outside_recency_does_not_flag(self):
        # Bearish base structure, but the only counter-direction BOS
        # happened well outside the recency window.
        swings = _bearish_swings(num_pairs=8)
        # Manually push a synthetic high at index 100; place an old BOS
        # at index 1 (well before the 10-bar recency window from idx 16).
        old_bos = StructureEvent(
            type="BOS",
            direction="bullish",
            level_broken=swings[-1].price,
            close_price=swings[-1].price + 1.0,
            candle_index=1,
            time=swings[1].time,
        )
        h4_state = _build_h4_state(
            swings,
            direction="bearish",
            structure_events=[old_bos],
        )
        result = classify_regime(_wrap_mso(h4_state))
        assert result.regime == "trending_bear"  # no reversal flagged


# ---------------------------------------------------------------------------
# 6) Determinism + dataclass invariants
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_mso_same_label(self):
        swings = _bullish_swings(num_pairs=8)
        mso = _wrap_mso(_build_h4_state(swings))
        results = [classify_regime(mso) for _ in range(5)]
        labels = {r.regime for r in results}
        assert labels == {"trending_bull"}
        # raw_features must also be byte-identical across runs.
        first = json.dumps(results[0].raw_features, sort_keys=True)
        for r in results[1:]:
            assert json.dumps(r.raw_features, sort_keys=True) == first

    def test_classifier_version_constant(self):
        # The constant exposed in __all__ matches what classify_regime emits.
        result = classify_regime(_wrap_mso(_build_h4_state(_bullish_swings())))
        assert result.classifier_version == CLASSIFIER_VERSION
        # Always a non-empty string for stamping purposes.
        assert isinstance(CLASSIFIER_VERSION, str) and CLASSIFIER_VERSION


class TestPublicApiSchema:
    def test_regime_classification_is_frozen(self):
        result = classify_regime(_wrap_mso(_build_h4_state(_bullish_swings())))
        # Frozen dataclass — assignment must raise.
        with pytest.raises((AttributeError, Exception)):
            result.regime = "chop"  # type: ignore[misc]

    def test_default_lookback_constant_matches_signature(self):
        # The classify_regime kwarg default and the exported constant
        # must agree — drift here means orchestrator passes the wrong
        # value when reading from config.
        import inspect

        sig = inspect.signature(classify_regime)
        default = sig.parameters["lookback_h4_candles"].default
        assert default == DEFAULT_LOOKBACK_H4


# ---------------------------------------------------------------------------
# 7) Shadow logger — IO + schema
# ---------------------------------------------------------------------------


class TestShadowLogger:
    def test_writes_one_row_to_tmp_path(self, tmp_path):
        log_path = str(tmp_path / "regime_classifications.jsonl")
        mso = _wrap_mso(_build_h4_state(_bullish_swings()))
        regime = log_classification(
            mso,
            symbol="XAUUSD",
            candle_time="2026-04-25T14:15:00Z",
            log_path=log_path,
        )
        assert regime == "trending_bull"
        rows = Path(log_path).read_text().splitlines()
        assert len(rows) == 1
        parsed = json.loads(rows[0])
        assert parsed["symbol"] == "XAUUSD"
        assert parsed["regime"] == "trending_bull"
        assert parsed["ts"] == "2026-04-25T14:15:00Z"
        assert parsed["classifier_version"] == CLASSIFIER_VERSION
        assert parsed["lookback"] == DEFAULT_LOOKBACK_H4
        assert "raw_features" in parsed
        # Required schema fields per design.
        for k in ("ts", "logged_at", "symbol", "regime", "classifier_version",
                  "lookback", "reason", "raw_features"):
            assert k in parsed

    def test_appends_multiple_rows(self, tmp_path):
        log_path = str(tmp_path / "regime_classifications.jsonl")
        mso_bull = _wrap_mso(_build_h4_state(_bullish_swings()))
        mso_bear = _wrap_mso(_build_h4_state(_bearish_swings(), direction="bearish"))
        log_classification(mso_bull, symbol="XAUUSD",
                           candle_time="2026-04-25T14:15:00Z", log_path=log_path)
        log_classification(mso_bear, symbol="USDJPY",
                           candle_time="2026-04-25T14:30:00Z", log_path=log_path)
        rows = [json.loads(line) for line in Path(log_path).read_text().splitlines()]
        assert len(rows) == 2
        assert rows[0]["regime"] == "trending_bull"
        assert rows[1]["regime"] == "trending_bear"
        assert rows[0]["symbol"] == "XAUUSD"
        assert rows[1]["symbol"] == "USDJPY"

    def test_creates_parent_directory(self, tmp_path):
        nested = tmp_path / "nested" / "deep" / "out.jsonl"
        mso = _wrap_mso(_build_h4_state(_bullish_swings()))
        log_classification(
            mso,
            symbol="XAUUSD",
            candle_time="2026-04-25T14:15:00Z",
            log_path=str(nested),
        )
        assert nested.exists()
        assert nested.read_text().count("\n") == 1

    def test_falls_back_to_mso_timestamp_when_candle_time_omitted(self, tmp_path):
        log_path = str(tmp_path / "out.jsonl")
        mso = _wrap_mso(_build_h4_state(_bullish_swings()))
        # MSO's timestamp_utc is "2026-04-25T14:15:00Z".
        log_classification(mso, symbol="XAUUSD", log_path=log_path)
        parsed = json.loads(Path(log_path).read_text().splitlines()[0])
        assert parsed["ts"] == "2026-04-25T14:15:00Z"

    def test_falls_back_to_now_when_no_timestamps(self, tmp_path):
        # MSO with empty timestamp_utc + no explicit candle_time -> now().
        log_path = str(tmp_path / "out.jsonl")
        mso = _wrap_mso(_build_h4_state(_bullish_swings()))
        # Pydantic model_copy to set timestamp_utc to empty string.
        mso_blank = mso.model_copy(update={"timestamp_utc": ""})
        log_classification(mso_blank, symbol="XAUUSD", log_path=log_path)
        parsed = json.loads(Path(log_path).read_text().splitlines()[0])
        assert parsed["ts"]
        # Should be ISO-ish.
        assert "T" in parsed["ts"]

    def test_io_failure_is_non_blocking(self, monkeypatch, tmp_path, caplog):
        # Force open() to raise inside the logger to exercise the
        # try/except path. The logger MUST NOT propagate the error.
        log_path = str(tmp_path / "out.jsonl")
        original_open = open

        def raising_open(path, mode="r", *a, **kw):
            if str(log_path) in str(path):
                raise OSError("synthetic disk full")
            return original_open(path, mode, *a, **kw)

        monkeypatch.setattr("builtins.open", raising_open)
        import logging
        with caplog.at_level(logging.WARNING, logger=shadow_mod.logger.name):
            result = log_classification(
                _wrap_mso(_build_h4_state(_bullish_swings())),
                symbol="XAUUSD",
                candle_time="2026-04-25T14:15:00Z",
                log_path=log_path,
            )
        assert result is None  # signaled failure but did not raise
        # Warning logged.
        assert any("failed to log classification" in r.getMessage()
                   for r in caplog.records)

    def test_unclear_label_still_logged(self, tmp_path):
        # No H4 timeframe -> unclear; logger writes the row anyway so
        # the analyst sees the unclear-rate over time.
        log_path = str(tmp_path / "out.jsonl")
        mso = MarketStateObject(
            timestamp_utc="2026-04-25T14:15:00Z",
            timeframes={"M15": _empty_h4_state()},
            session_levels=SessionLevels(asian_high=0, asian_low=0, pdh=0, pdl=0),
            data_quality=DataQuality(
                all_timeframes_complete=False, spread_normal=True,
                mt5_connected=True, timestamp_utc="2026-04-25T14:15:00Z",
            ),
        )
        result = log_classification(
            mso, symbol="XAUUSD",
            candle_time="2026-04-25T14:15:00Z",
            log_path=log_path,
        )
        assert result == "unclear"
        parsed = json.loads(Path(log_path).read_text().splitlines()[0])
        assert parsed["regime"] == "unclear"


# ---------------------------------------------------------------------------
# 8) Build-row primitive
# ---------------------------------------------------------------------------


class TestBuildRegimeRow:
    def test_logged_at_default_is_iso_utc(self):
        row = build_regime_row(
            symbol="XAUUSD",
            candle_time="2026-04-25T14:15:00Z",
            regime="trending_bull",
            classifier_version="v1.0-test",
            lookback=20,
            raw_features={"score": 5},
            reason="ok",
        )
        assert isinstance(row["logged_at"], str)
        assert row["ts"] == "2026-04-25T14:15:00Z"
        assert row["regime"] == "trending_bull"
        assert row["raw_features"] == {"score": 5}

    def test_explicit_logged_at_preserved(self):
        row = build_regime_row(
            symbol="XAUUSD",
            candle_time="2026-04-25T14:15:00Z",
            regime="chop",
            classifier_version="v1.0-test",
            lookback=20,
            raw_features={},
            logged_at="2026-04-25T14:15:02+00:00",
        )
        assert row["logged_at"] == "2026-04-25T14:15:02+00:00"
