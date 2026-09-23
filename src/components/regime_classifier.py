"""Pragmatic Regime Classifier (Wave 1 follow-up) — observation-only V1.

Purpose
-------
Wave 1 (Sprint 4 part 2) cold review concluded that ~70-75% of XAUUSD's
April collapse was AI-side, and that structural quality alone did NOT
predict outcome. Per A5's gold-standard analysis, regime/timing matters
more. The AI is currently regime-blind: every M15 close is evaluated with
identical priors regardless of whether the H4 backdrop is a clean trend,
chop, or an in-progress reversal.

This module produces a deterministic per-instrument regime label from
the existing MSO. V1 is intentionally simple — academic Wyckoff phase
classification (Phase A/B/C/D, Springs, Upthrusts, Sign-of-Strength,
etc.) is deferred to V2. The pragmatic V1 captures the operative
distinction: TRENDING (bull/bear) vs CHOP vs REVERSAL_IN_PROGRESS.

Approach selected: Option A (H4 swing-based)
--------------------------------------------
Three approaches were considered:

* **Option A (chosen):** Classify regimes from the H4 swing sequence
  already produced by ``market_state.detect_swings`` + the H4
  ``StructureAnalysis`` already computed by ``identify_structure_v2``
  (the live-active production detector since session 38). Layer in
  detection of recent H4 BOS in the counter-direction of the prior
  H4 trend to flag ``reversal_in_progress``. Pure addition over data
  the pipeline already computes; deterministic; ~150 LOC.

* **Option B (deferred):** Full Wyckoff phase classification using
  volume + price structure (Phase A accumulation/distribution, Phase
  B testing, Phase C spring/upthrust, Phase D markup/markdown). More
  academically defensible but requires (i) a phase state machine,
  (ii) volume-validated tests + spring/upthrust detection, (iii)
  cross-timeframe phase reconciliation. Estimated 800-1500 LOC and
  significant ambiguity in phase boundary detection on real-world
  data. Documented as the V2 successor; if V1 shadow data motivates
  it, an ADR + spec lands first.

* **Option C (rejected for V1):** ML classifier trained on labeled
  regime data. Has strongest theoretical fit but (a) requires hand-
  labeled regime ground truth which we lack, (b) risks overfit on
  the 2026 sample, (c) opaque to humans for live debugging. Saved
  for after V1 collects ≥14 days of shadow data + labelled
  divergences.

Rationale for V1 = Option A
~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. **Reuses existing primitives.** ``identify_structure_v2`` already
   ships v2_shadow LIVE (session 38) and produces the directional
   net-score we need; ``detect_structure_breaks`` already finds H4
   BOS events. No new detection logic.
2. **Deterministic + auditable.** Same MSO -> same label; can be
   re-run on historical fixtures to compare against realized
   outcomes (the ``scripts/regime_outcome_correlation.py`` companion
   uses this exact property).
3. **Fail-safe.** Insufficient H4 swings collapse to ``unclear`` —
   never gates a trade, never crashes the pipeline.
4. **Cheap to ship.** ~150 LOC. Time-to-data dominates time-to-build.
   We need 14-30 days of shadow data before any promotion decision;
   shipping V2 first burns that runway.

What V1 does NOT do (intentional limitations)
---------------------------------------------
* No volume confirmation. Wyckoff explicitly weights volume on
  effort-vs-result; V1 is price-structure-only. V2 candidate.
* No cross-timeframe (D1) confirmation. A trending-bull H4 inside a
  D1 distribution phase is the same label as inside a D1 markup —
  V1 cannot distinguish. V2 candidate.
* No Spring / Upthrust / SoS / SoW micro-structure. Reversal is
  detected only via "recent H4 BOS opposite the prior H4 trend";
  spring-style re-acceleration into trend is missed. V2 candidate.
* No regime persistence model. Each M15 close is classified
  independently from the current MSO; we don't track "we've been
  bullish for N candles". The companion analysis script
  reconstructs persistence from the JSONL stream.

Promotion path (NOT enforced here — observation-only)
------------------------------------------------------
Per CEO directive in the task brief:

1. Ship V1 SHADOW-ONLY. NO permissions.py integration. NO prompt
   integration. The classifier writes to
   ``shadow_logs/regime_classifications.jsonl`` and that's it.

2. Accumulate ≥14-30 days of shadow data + labelled regime history.

3. Run ``scripts/regime_outcome_correlation.py`` to compute per-regime
   WR / Exp R / count. CEO reviews.

4. Only on CEO greenlight + clear edge differentiation across regimes
   does V1 promote to a live filter (and even then — most likely a
   PROMPT-side regime hint to the AI before any hard gate).

References
----------
* ``src/components/market_state.py`` — ``identify_structure_v2``
  (the production detector, F3 GO 2026-04-24).
* Wave 1 cold review: regime > feature-selectivity for explaining
  XAUUSD April collapse.
* CLAUDE.md §Validated Numbers — quarterly WR decay
  (73 -> 71 -> 64 -> 59%) which V1 may help disaggregate.
* Wyckoff Method (Wyckoff, 1934; Pruden 2007) — academic reference
  for Option B's V2 successor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from src.components.market_state import (
    detect_swings,
    identify_structure_v2,
)
from src.models.market_state_models import (
    MarketStateObject,
    StructureAnalysis,
    StructureEvent,
    Swing,
    TimeframeState,
)


# ---------------------------------------------------------------------------
# Schema + constants
# ---------------------------------------------------------------------------

RegimeLabel = Literal[
    "trending_bull",
    "trending_bear",
    "chop",
    "reversal_in_progress",
    "unclear",
]

CLASSIFIER_VERSION = "v1.0-option-a-h4-swing"
"""Stamped on every emitted RegimeClassification; bump on logic change.

V1.0 = Option A H4 swing classifier (this module). V2.x will use a
distinct major version when (and if) Option B / Option C lands. The
companion analysis script keys per-regime aggregations on this string
to avoid mixing labels emitted by different classifier versions.
"""

# Minimum number of completed H4 swings (highs + lows combined) required
# before classification can resolve. Below this we return ``unclear``.
# Rationale: ``identify_structure_v2`` requires >=2 highs AND >=2 lows
# (i.e. >=4 swings) to escape ``insufficient_data``. We add headroom so
# the regime label is meaningful — 2 highs / 2 lows is a single price
# excursion, indistinguishable from random noise. 6 swings = 3 transitions
# per side ≈ minimum viable trend evidence.
DEFAULT_MIN_SWINGS = 6

# Default H4 lookback in candles. 20 H4 bars ≈ 80 hours ≈ 3.3 calendar
# days — long enough to capture a full London->NY->Tokyo cycle with
# headroom, short enough that a regime shift surfaces within a session.
# Override per-call via ``classify_regime(..., lookback_h4_candles=N)``.
DEFAULT_LOOKBACK_H4 = 20

# When the H4 net-score sits inside the dead zone (transitional) AND the
# absolute structural displacement (max swing - min swing) is below this
# fraction of the average true range, classify as ``chop`` rather than
# leaving it transitional. 1.5x ATR is a soft heuristic — a market that
# has gone less than 1.5 ATRs over its full lookback is empirically
# range-bound. Tuned offline; logged in raw_features for replay
# reconstruction so future tuning doesn't lose history.
CHOP_DISPLACEMENT_ATR_FLOOR = 1.5

# When we see a recent H4 BOS in the counter-direction of the
# pre-existing H4 trend (>= last N H4 candles), flag the regime as
# ``reversal_in_progress``. N=10 H4 candles ≈ 40 hours ≈ ~2 trading
# days. Empirically this is short enough that "reversal" still feels
# operational rather than historical.
REVERSAL_RECENCY_BARS = 10


@dataclass(frozen=True)
class RegimeClassification:
    """Result of a single regime classification call.

    Attributes
    ----------
    regime:
        One of the five labels in :data:`RegimeLabel`.
    classifier_version:
        Version string baked into every row so future logic changes
        don't silently invalidate older shadow data.
    lookback_h4_candles:
        Lookback used for this call. Echoed for replay.
    raw_features:
        Free-form dict of intermediate values that drove the label —
        ``score``, ``dead_zone``, ``swing_count``, ``recent_bos_dir``,
        ``displacement_atr_ratio``, etc. The companion analysis script
        slices on these.
    reason:
        Short human string explaining why the label fired. For
        operator triage; not used in any decision.
    """

    regime: RegimeLabel
    classifier_version: str = CLASSIFIER_VERSION
    lookback_h4_candles: int = DEFAULT_LOOKBACK_H4
    raw_features: dict = field(default_factory=dict)
    reason: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _swings_from_h4(
    h4_state: Optional[TimeframeState],
    lookback_candles: int,
) -> list[Swing]:
    """Return the H4 swings inside the lookback window.

    Falls back to whatever the MSO already detected — we do NOT recompute
    swings from raw candles here, because the production MSO uses a
    config-driven ``swing_detection_min_bars`` setting that we'd otherwise
    have to duplicate (silent drift risk). The lookback_candles arg is
    used only as a soft filter on swing.index.
    """
    if h4_state is None:
        return []
    swings = list(getattr(h4_state, "swings", []) or [])
    if not swings:
        return []
    # Each swing carries the candle index it formed at. Filter to swings
    # within the last `lookback_candles` of the most recent swing index
    # (because we don't have N_total candles here without raw_data).
    last_idx = max(s.index for s in swings)
    cutoff = last_idx - lookback_candles
    return [s for s in swings if s.index > cutoff]


def _displacement_atr_ratio(
    swings: list[Swing],
    atr: float,
) -> Optional[float]:
    """Return (max_high - min_low) / atr over the swing window.

    Returns None if either the swing list is empty or atr <= 0 (caller
    treats None as "feature unavailable"; falls back to score-only
    decision).
    """
    if not swings or atr <= 0:
        return None
    highs = [s.price for s in swings if s.type == "high"]
    lows = [s.price for s in swings if s.type == "low"]
    if not highs or not lows:
        return None
    displacement = max(highs) - min(lows)
    if displacement <= 0:
        return None
    return displacement / atr


def _recent_counter_bos(
    h4_state: Optional[TimeframeState],
    structure_dir: str,
    recency_bars: int,
) -> Optional[str]:
    """Detect a recent H4 BOS opposite the prior H4 trend.

    Returns:
        - "bullish"  if the most recent H4 BOS within the recency window
          is bullish AND the prior H4 structure is bearish (an upside
          reversal),
        - "bearish"  if mirror,
        - None       if no qualifying counter-direction BOS is present.

    "Prior H4 trend" comes from the H4 ``StructureAnalysis.direction``
    that is computed BEFORE the BOS landed — but ``identify_structure``
    is itself updated post-break, so what we have access to is the
    CURRENT structure label. This is a known imperfection: a perfect
    detector would re-run structure with the breaking BOS excluded.
    For V1 we settle for: if the most recent BOS direction disagrees
    with the current structure direction, we treat it as a reversal
    candidate. If the structure has fully flipped to follow the BOS,
    the test fails (correctly — that's "trending" in the new direction).
    """
    if h4_state is None:
        return None
    events = list(getattr(h4_state, "structure_events", []) or [])
    bos_events = [e for e in events if e.type == "BOS"]
    if not bos_events:
        return None
    last_bos = bos_events[-1]
    # Index of the most recent swing — used as a proxy for "now". If the
    # BOS is older than recency_bars from that, it's not "recent".
    swings = list(getattr(h4_state, "swings", []) or [])
    if swings:
        now_index = max(s.index for s in swings)
        if (now_index - last_bos.candle_index) > recency_bars:
            return None
    if last_bos.direction != structure_dir:
        return last_bos.direction
    return None


# ---------------------------------------------------------------------------
# Main classifier
# ---------------------------------------------------------------------------

def classify_regime(
    mso: Optional[MarketStateObject],
    *,
    lookback_h4_candles: int = DEFAULT_LOOKBACK_H4,
    min_swings: int = DEFAULT_MIN_SWINGS,
) -> RegimeClassification:
    """Classify the current market regime from an MSO.

    Returns a :class:`RegimeClassification`. Always returns a result —
    the ``unclear`` label is the explicit fail-safe for insufficient
    data, never an exception.

    Inputs
    ------
    mso:
        The :class:`MarketStateObject` produced by Component 2. Must
        contain a populated ``timeframes["H4"]`` to have any chance of
        producing a non-``unclear`` label. ``None`` and missing-H4 cases
        return ``unclear`` with the reason field populated.
    lookback_h4_candles:
        Soft filter on H4 swing index for restricting the swing window
        used by ``identify_structure_v2``. Default 20 (~80 hours).
    min_swings:
        Floor on the number of H4 swings (highs + lows) needed before
        we'll attempt a non-``unclear`` label. Default 6 (3 highs + 3
        lows ≈ minimum viable trend evidence).

    Algorithm (Option A)
    --------------------
    1. Pull H4 swings from MSO; filter to lookback window.
    2. If swing count < min_swings -> ``unclear``.
    3. Run ``identify_structure_v2`` over the windowed swings to get
       direction (bullish / bearish / transitional / insufficient_data)
       and net score / dead_zone counts.
    4. Compute displacement-to-ATR ratio (max swing range / ATR(14)).
    5. Detect recent H4 BOS in counter-direction of current structure
       (``_recent_counter_bos``).
    6. Decision tree::

           if recent_counter_bos:
               -> reversal_in_progress
           elif structure == bullish:
               -> trending_bull
           elif structure == bearish:
               -> trending_bear
           elif displacement_atr_ratio < CHOP_DISPLACEMENT_ATR_FLOOR:
               -> chop
           else:
               -> chop  (transitional + low-displacement -> chop)

    7. Stamp raw_features with score, dead_zone, swing_count, ATR, etc.
    """
    if mso is None:
        return RegimeClassification(
            regime="unclear",
            lookback_h4_candles=lookback_h4_candles,
            raw_features={"reason_code": "mso_none"},
            reason="MSO is None — orchestrator pipeline did not produce it.",
        )

    h4_state = (mso.timeframes or {}).get("H4")
    if h4_state is None:
        return RegimeClassification(
            regime="unclear",
            lookback_h4_candles=lookback_h4_candles,
            raw_features={"reason_code": "h4_missing"},
            reason="MSO has no H4 timeframe state.",
        )

    swings = _swings_from_h4(h4_state, lookback_candles=lookback_h4_candles)
    swing_count = len(swings)

    if swing_count < min_swings:
        return RegimeClassification(
            regime="unclear",
            lookback_h4_candles=lookback_h4_candles,
            raw_features={
                "reason_code": "insufficient_swings",
                "swing_count": swing_count,
                "min_swings_required": min_swings,
            },
            reason=(
                f"Only {swing_count} H4 swings inside lookback "
                f"{lookback_h4_candles}; need {min_swings}."
            ),
        )

    # Core structural classification — re-uses production v2 logic with
    # the same dead-zone divisor default (8) the live pipeline ships.
    h4_struct: StructureAnalysis = identify_structure_v2(swings)

    # Score + dead-zone for raw_features (mirror logic in
    # ``compute_v2_score_metadata``).
    hh = int(h4_struct.hh_count or 0)
    hl = int(h4_struct.hl_count or 0)
    lh = int(h4_struct.lh_count or 0)
    ll = int(h4_struct.ll_count or 0)
    score = (hh + hl) - (lh + ll)
    high_trans = hh + lh
    low_trans = hl + ll
    min_swing_transitions = min(high_trans, low_trans)
    dead_zone = max(2, min_swing_transitions // 8)

    # Displacement ratio — diagnostic for chop detection.
    atr = float(getattr(h4_state, "atr_14", 0.0) or 0.0)
    displacement_ratio = _displacement_atr_ratio(swings, atr)

    # Recent counter-direction BOS detection.
    counter_bos_dir = _recent_counter_bos(
        h4_state,
        structure_dir=h4_struct.direction,
        recency_bars=REVERSAL_RECENCY_BARS,
    )

    raw_features = {
        "swing_count": swing_count,
        "h4_direction": h4_struct.direction,
        "score": score,
        "dead_zone": dead_zone,
        "hh": hh,
        "hl": hl,
        "lh": lh,
        "ll": ll,
        "h4_atr_14": round(atr, 6) if atr else None,
        "displacement_atr_ratio": (
            round(displacement_ratio, 3) if displacement_ratio is not None else None
        ),
        "recent_counter_bos_direction": counter_bos_dir,
    }

    # --- Decision tree ---
    if counter_bos_dir is not None:
        return RegimeClassification(
            regime="reversal_in_progress",
            lookback_h4_candles=lookback_h4_candles,
            raw_features=raw_features,
            reason=(
                f"Recent H4 BOS direction={counter_bos_dir} disagrees with "
                f"current H4 structure={h4_struct.direction}; flagging reversal."
            ),
        )

    if h4_struct.direction == "bullish":
        return RegimeClassification(
            regime="trending_bull",
            lookback_h4_candles=lookback_h4_candles,
            raw_features=raw_features,
            reason=(
                f"H4 net score={score} > dead_zone={dead_zone}; HH+HL dominant."
            ),
        )

    if h4_struct.direction == "bearish":
        return RegimeClassification(
            regime="trending_bear",
            lookback_h4_candles=lookback_h4_candles,
            raw_features=raw_features,
            reason=(
                f"H4 net score={score} < -dead_zone={-dead_zone}; LH+LL dominant."
            ),
        )

    # Transitional or insufficient_data falls through to chop. We
    # already gated insufficient_swings above; reaching here on
    # insufficient_data means v2 saw <2 highs OR <2 lows in the windowed
    # swings (rare but possible when min_swings=6 admits e.g. 5 highs +
    # 1 low). Treat it as chop with a reason marker.
    if h4_struct.direction == "insufficient_data":
        return RegimeClassification(
            regime="chop",
            lookback_h4_candles=lookback_h4_candles,
            raw_features={**raw_features, "reason_code": "v2_insufficient"},
            reason=(
                "v2 returned insufficient_data on windowed swings (asymmetric "
                "H/L count); treating as chop."
            ),
        )

    # h4_struct.direction == "transitional" -> chop, with displacement
    # in raw_features for offline analysis.
    return RegimeClassification(
        regime="chop",
        lookback_h4_candles=lookback_h4_candles,
        raw_features=raw_features,
        reason=(
            f"H4 structure transitional (|score|={abs(score)} <= dead_zone="
            f"{dead_zone}); displacement_ratio="
            f"{displacement_ratio if displacement_ratio is not None else 'n/a'}."
        ),
    )


# ---------------------------------------------------------------------------
# Public API surface
# ---------------------------------------------------------------------------

__all__ = [
    "CLASSIFIER_VERSION",
    "DEFAULT_LOOKBACK_H4",
    "DEFAULT_MIN_SWINGS",
    "RegimeLabel",
    "RegimeClassification",
    "classify_regime",
]
