# Phase 3 Raw-OHLC Prospective Validation Lane

**Date:** 2026-05-01
**Spec:** `research/phase_3_external_feed_validation/RAW_OHLC_PROSPECTIVE_VALIDATION_SPEC_V1.json`
**Status:** Registered future/prospective lane
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Purpose

The historical raw-OHLC replay answered a different question than the truth-layer replay: can the selected cohorts still be reconstructed from candle streams without leaking future opportunity labels? The answer was yes for the current lab scaffold.

The next question is whether the result survives data that was not used to form or interpret the cohorts. This file freezes that next lane before future raw-OHLC rows are evaluated.

## Registered Cutoff

Prospective rows must have `candle_close_utc > 2026-04-30T17:00:00+00:00`.

This cutoff comes from the full raw-OHLC replay summary's last input replay clock. Rows at or before that timestamp are historical discovery/diagnostic data for this lane.

## Primary Decision Rule

The primary unit is the five-cohort target family composite, not the best individual child selected after seeing results.

Target family:

| Cohort | Role |
|---|---|
| `USDJPY|tokyo|bearish|D1` | primary controlled child |
| `GBPJPY|tokyo|bullish|D1` | primary controlled child |
| `USDJPY|london|bearish|D1` | cleared non-primary strong lead |
| `USDJPY|tokyo|bearish|H4+H1_consensus` | cleared non-primary strong lead |
| `XAGUSD|london|bullish|D1` | cleared non-primary strong lead |

The primary score is family-level mean resolved R. Individual child cohorts remain diagnostics unless a later registry freezes a child-specific hypothesis before new data.

## Controls

Negative controls:

| Cohort | Role |
|---|---|
| `GBPUSD|london|bearish|H4+H1_consensus` | negative control |
| `USDJPY|london|bullish|D1` | negative control |
| `USDJPY|tokyo|bullish|D1` | negative control |

Blocked dominance-watchlist controls:

| Cohort | Role |
|---|---|
| `NAS100|ny|bullish|D1` | dominance watchlist |
| `US30_cash|ny|bullish|H4+H1_consensus` | dominance watchlist |
| `XAUUSD|ny|bullish|D1` | dominance watchlist |

Blocked controls must remain reported. They cannot be promoted as target evidence from this lane because they were already identified as dominance-watchlist names.

## Minimum Final Readout

Interim readouts may be produced for monitoring, but a final prospective readout requires:

| Requirement | Minimum |
|---|---:|
| Target-family resolved rows | 150 |
| Calendar months after cutoff | 6 |
| Target children with at least 30 resolved rows | 2 |
| Negative-control family resolved rows | 75 |
| Blocked-control family report | required |

The user preference is that final test results must be run on the whole available corpus. Bounded runs are allowed for smoke/debug only.

## Required Report Contents

Every report from this lane must include:

- No-leak integrity summary.
- Data coverage and gaps by symbol/timeframe.
- Target-family summary.
- Negative-control family summary.
- Blocked dominance-control summary.
- Cohort recency detail.
- DSR diagnostic.
- PBO diagnostic.
- effective_N diagnostic.
- Ambiguity ledger.
- Synthesis and next steps, not only tables.
- `NO_PROMOTION_VERDICT` unless a separate future promotion dossier is explicitly built.

## Interpretation Rules

Valid positive evidence:

- Target family mean R is positive.
- Target family beats negative controls.
- DSR, PBO, and effective_N diagnostics move in the right direction on prospective rows.
- Blocked controls are explained rather than ignored.

Invalid positive evidence:

- Picking the best child after looking at prospective results.
- Dropping a weak child from the target family.
- Dropping GBPUSD because it hurts the headline.
- Treating blocked dominance controls as target confirmations.
- Changing periodization, metric, session filters, entry/exit assumptions, or regime definitions after seeing results.

## Synthesis

The historical result opened a validation door, not a promotion door. The cleanest way through that door is a frozen family-composite prospective lane with the same controls kept in view. If the family composite survives there, the later promotion dossier can be built on a much stronger foundation than same-dataset historical diagnostics.
