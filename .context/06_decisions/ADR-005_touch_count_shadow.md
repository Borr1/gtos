# ADR-005 — Touch-count shadow logger + prompt-nudge decision gate

Status: **DRAFT** — proposed 2026-04-24 from Phase 1 Track A research.
Supersedes: none.
Related: existing `OrderBlock.touch_count` (src/models/market_state_models.py:62),
ADR-004 (v2_shadow promotion), session 37 A5 `guard_candidate_inconsistent_pois`.

## Context

Phase 1 Track A reverse-engineering (branch `research/phase1-track-a-xauusd-reverse`,
2026-04-24) walked 3,302 XAUUSD M15 candles Jan 2 – Apr 13 and labeled each for
primary (2R/1R/12H1), quick (1.5R/1R/4H1), premium (3R/1R/24H1), and anti-pattern
(1R adv/1R fav/8H1). Train (Jan-Feb) vs held-out test (Mar-Apr 13) split, detector_version=v1.

Stratifying TEST-set LONG with proper OB retest (`sl_source=ob`) by
`h1_opp_ob_touch`:

| Touch | n | Primary rate | Wilson 95% CI |
|---:|---:|---:|---|
| 0 (fresh) | 60 | 31.7% | [21.3, 44.2] |
| 1 | 680 | 7.2% | [5.4, 9.5] |
| 2 | 548 | 3.1% | [1.9, 4.9] |
| ≥3 | 284 | 2.1% | [0.8, 4.6] |

Chi-square touch=0 vs touch≥1: p = 2.45e-17 (Bonferroni-corrected ≈ 5e-16 at
factor 20 lenses). See `research/phase1_xauusd_reverse_engineering/SYNTHESIS.md`
§5 for full analysis.

This extends the existing production evidence cited in
`OrderBlock.touch_count` docstring (Touch-1 WR 72.7% n=23,575 vs Touch-2+ WR 31.5%
n=82,572) by measuring the candle-level PRE-trade 2R-before-1R probability,
not post-AI trade outcomes.

## Question

Does GTOS's current production AI (Sonnet 4.6, effort=max) already down-weight
OB retest setups with touch_count >= 2, or does it accept them at roughly the
same rate as touch 0/1?

We don't know. `candidate_features_log.jsonl` records `mso_h1_ob_touch_counts[]`
per candle but only STARTS logging ~2026-04-17 (confirmed by grep on earliest
XAUUSD row). No pre-promotion historical signal, insufficient live data (7 days)
to estimate AI per-touch accept rate.

## Decision

**Ship a research-only shadow logger** that:

1. Extends `candidate_features_logger` to also write the H1 opposing-OB
   touch_count that the AI would see at candle close for the direction being
   evaluated, plus a `nearest_opposing_ob_touch_for_direction` int field (-1
   when no opposing OB exists).
2. Logs the AI decision (CANDIDATE vs NO_TRADE) alongside that touch value.
3. After ≥30 days of data (aiming for ≥100 CANDIDATE + ≥1000 NO_TRADE rows
   per symbol), compute:
   - Accept-rate P(CANDIDATE | touch=0), P(CANDIDATE | touch=1), P(CANDIDATE | touch≥2)
   - WR of resulting filled trades, stratified by touch
   - Whether the AI already discriminates (different accept rates) or not

If the AI does NOT discriminate (accept rates within ±10pp across touch
strata): propose in a FOLLOW-UP ADR a SOFT prompt nudge like "strongly prefer
OBs with touch_count ≤ 1; if touch_count ≥ 2, require exceptional structural
confluence (displacement + FVG-in-impulse + session match)".

If the AI DOES discriminate (touch>=2 accept rate already <50% of touch=0/1):
no action needed — AI is filtering adequately, touch_count feature exposed to
prompt is working.

**Explicitly NOT proposed:**
- A hard deterministic gate rejecting touch≥2 — computation shows net
  −1.0 R/month under 2R:1R with current 62% blended WR, due to frequency
  loss. Violates CEO "high-quality frequency" principle
  (memory `feedback_research_goal_high_quality_frequency.md`).
- A prompt edit now — lack of live signal means we'd be flying blind.

## Rejected alternatives

### Alt A — Hard gate: reject CANDIDATE when `h1_opp_ob_touch >= 2`
Rejected because expected R/mo calculation is net negative:

- Assume XAUUSD 6 trades/mo, ⅓ are touch>=2 (walk distribution). Gate removes
  2/mo.
- WR lift: 62% blended → ~68% on remaining trades (walk data suggests touch 0/1
  setups are stronger).
- Before: 6 × 0.86R = +5.16 R/mo
- After: 4 × 1.04R = +4.16 R/mo
- Net: **−1.0 R/mo**, 95% CI [−3.0, +0.5] (rough, no full bootstrap).
- Violates "high-quality frequency" mandate.
- Pre-v2-promotion timing also risky: touch distribution may shift under v2.

### Alt B — Prompt edit NOW ("strongly prefer touch ≤ 1")
Rejected because:
- No live data on current AI per-touch behaviour. Flying blind.
- Prompt edits require CEO approval (WF-1 discipline, CLAUDE.md §"Requires CEO approval").
- Our 60-sample TEST=April-only touch=0 evidence is temporally narrow.
- Shadow-log-then-decide is the canonical GTOS research pattern (A2, H29,
  BE-shadow, etc. all shipped shadow-first). Follows this pattern.

### Alt C — Add touch_count to primary_analyzer prompt's `static_context` as
an explicit table
Rejected because:
- `static_context` is cached per session per D1/H4 direction change; OB
  touch_count changes per-candle. Would break the session cache assumption.
- touch_count is already accessible in MSO JSON the prompt serializes — the AI
  CAN see it if it's processing the order_blocks[] list. Question is whether
  it USES it. Shadow log answers that without code change.

### Alt D — Re-weight MC classifier confidence by touch_count
Rejected because:
- `confidence_scorer` is in shadow mode (confirmed useless, 98% gives confidence=80).
  Adding touch features won't unblock it at current adoption.
- Fuses two decisions (classifier, AI) muddying attribution.

### Alt E — Defer completely until v2_shadow promotion
Rejected because:
- Touch-count is detector-agnostic — it's measured on OBs detected regardless
  of v1/v2 structure direction labeling.
- Shadow logging NOW means we'll have 30d of data by the time v2 promotes
  (target mid-May 2026). Then we can compare pre/post and quantify whether
  v2 changes the per-touch picture.

## Risks

1. **Shadow logger code defects could leak into production serialization.**
   Mitigation: isolate new fields in `candidate_features_log` as an additive
   schema change (never remove old fields), wrap extraction in try/except
   with null fallback (pattern established by session 37 A5).
2. **30-day window may straddle v2_shadow promotion.** Mitigation: emit
   `detector_version_at_eval` column explicitly so we can split analyses.
3. **Touch-count can be undefined** (no opposing OB → `atr_fallback` SL path).
   Log as -1 and exclude from touch-strata calculations but include in
   counts for completeness.

## Success criteria (for future follow-up ADR)

Trigger a follow-up prompt-nudge ADR if ALL of the following hold after 30 days:
- n ≥ 100 CANDIDATE emissions XAUUSD
- CANDIDATE rate at touch=0 vs touch≥2 differs by ≤10pp (AI not discriminating)
- Filled-trade WR at touch=0/1 materially exceeds WR at touch≥2 by ≥15pp
- No regression in XAUUSD WR vs pre-shadow baseline

Abort if:
- Any of the above fails
- v2_shadow promotion introduces >20pp shift in CANDIDATE-stratum distribution
  (re-start data collection under v2)

## Implementation sketch (not binding)

- One-line addition in `src/components/candidate_features_logger.py` to
  extract nearest opposing-OB touch for the AI's direction (mirror existing
  `mso_h1_nearest_ob_distance_atr` computation pattern; if `ai_direction` is
  unknown at log time, log BOTH directions' opposing-OB touches).
- Test via `tests/components/test_candidate_features_logger.py`.
- CEO review + merge gate: additive shadow logger only. No decision-path change.

## Decision

Pending CEO approval. This ADR is draft output of Phase 1 Track A research,
filed to provide cold context for the next session's go/no-go vote.
