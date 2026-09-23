# Independent replay results for zeta review

## Replay 1: EURUSD L2 h4-vs-d1 conflict, per-day, with epsilon

```
eps=0.0002 (EURUSD 2 pips):
  Full 804 records with epsilon: W=304 L=500 U=0 WR=37.8% R_sum=-44R
  Full 804 records with eps=0 (zeta method): W=364 L=436 U=4 WR=45.5% R_sum=+110R
  Per-day (28 distinct days), eps=0.0002: W=12 L=16 U=0 WR=42.9% R_sum=+2R Exp+0.07R/trade
```

**Effect size deflates by two independent correction mechanisms:**

1. Correlated-sample correction: 804 → 28 independent events (28.7x over-sampling)
2. Epsilon correction (required per CLAUDE.md unresolved #8): +110R → -44R at 2-pip epsilon, +4R at 1-pip

Combined honest estimate: +2R over 28 events ≈ break-even, not +110R.

## Replay 2: NAS100 L2 h4-vs-d1 conflict per-day with epsilon

```
eps=2.0 (NAS100 2 points):
  Per-day (7 distinct days): W=2 L=5 U=0 WR=28.6% R_sum=-2R
  Events: 2026-02-20 L, 2026-03-25 L, 2026-04-06 L, 2026-04-07 L,
          2026-04-08 W, 2026-04-09 W, 2026-04-17 L
```

NAS100 shows no edge in H4-direction trades when properly de-correlated.

## Replay 3: D1 structure direction lag (08_structure_direction_lag.py)

```
NAS100 D1 rolling-60-bar structure:
  2026-03-27: bullish (hh=3 hl=4 lh=7 ll=5)
  2026-03-31: bearish (hh=2 hl=4 lh=7 ll=5) -- flipped
  ... stays bearish ...
  2026-04-17: bearish (hh=1 hl=5 lh=8 ll=4)
  
  NAS100 price on 2026-03-27: 23075
  NAS100 price on 2026-04-17: 26671
  Change: +15.6% rally while D1=bearish for 20 trading days
```

**Mechanism CONFIRMED:** once the bullish regime's HH/HL counts fall below `recent_pairs=3`,
and the prior bearish regime's LH/LL counts exceed 3 within the rolling window, the
structure flips bearish and stays bearish until enough new HH accumulate — which on a
rising D1 can take 2-3 months of clean higher highs.

However, this is not "all-history counts vs tiny threshold" as zeta frames it. The
counts are already windowed (60-bar rolling). The issue is that on a 60-bar D1 window,
old LH/LL from the first half of the window outnumber new HH/HL in the second half
for 2-3 weeks after a regime flip.

## Replay 4: Touch-count inflation from formation+1 vs break+1

```
XAUUSD M15 (last 2000 bars): n_obs=82, avg_formation+1=43.67, avg_break+1=41.89, delta=1.78
NAS100 M15 (last 2000 bars): n_obs=96, avg_formation+1=42.70, avg_break+1=41.00, delta=1.70
EURUSD M15 (last 2000 bars): n_obs=90, avg_formation+1=52.00, avg_break+1=50.03, delta=1.97
```

**Zeta's 1.87 ratio confirmed directionally.** But this is MUCH SMALLER than the
overall touch count (~40-50 overlaps per OB on average). The `_count_touches` gate at
`>= 2` operates on a very different scale than zeta implies.

For UNMITIGATED OBs on H1 (the scale the gate actually operates on):

```
XAUUSD H1: total_obs=79, unmit=3, touch_count distribution {0:1, 1:1, 2-5:1, ...}
NAS100 H1: total_obs=79, unmit=6, touch_count distribution {1:2, 2-5:4, ...}
EURUSD H1: total_obs=74, unmit=6, touch_count distribution {1:3, 2-5:2, 6-20:1, ...}
```

So unmit OBs cluster at tc 1-6 — the gate rejects half or more.

## Replay 5: Research vs production touch-count semantics

Research (`compute_zone_age_v1.py:281-327`): TRANSITION-based, increments only on
outside->inside transitions (`if touching and not in_zone: touch_count += 1`).
Starts at `ob["formation_index"] + 1`.

Production (`market_state.py:483-502`): BAR-OVERLAP-based, increments for every
bar whose range overlaps the OB. Also starts at `formation_index + 1`.

**The research and production use different counting semantics.** A price that
stays INSIDE an OB for 5 bars counts as:
- Research touch=1 (one outside->inside transition)
- Production touch_count=5 (five bars in zone)

This is a bigger semantic mismatch than zeta's "off-by-one" framing. The
72.7%/31.5% research cliff was measured in research semantics; the gate is
calibrated against research results but uses different semantics. The `>= 2`
threshold is essentially "any overlap for 2+ bars post-formation" in production
vs research's "second outside->inside transition".

## Replay 6: OB mitigation wick-vs-body comparison

`market_state.py:418-421, 443-446`: OB mitigation uses wick (range-overlap).
`market_state.py:537-548`: BREAKER block formation uses body-close.

These are DIFFERENT events, not the same event with inconsistent semantics:
- OB mitigation = "has price visited this zone at all?" (freshness tracker)
- Breaker formation = "has price decisively broken through this zone?" (zone flip)

Docstring at `market_state.py:388`: "Mark as mitigated if price has returned to
the OB zone after formation." — consistent with wick-touch (return, not penetration).

Docstring at `market_state.py:511`: "A breaker block forms when an OB is mitigated
(price body closes through the zone)" — consistent with body-close (penetration).

The design is: first wick touch -> OB consumed; first body close through ->
converts to breaker. These capture different structural events.

Zeta's framing as "semantic inconsistency" is misleading; they are intentionally
different. However, one could argue wick-mitigation is TOO aggressive (a 1-pip
wick shouldn't consume an OB) — but that's a CEO-level design decision, not a
"bug fix without approval".

## ADR 003 reference

ADR 003 (2026-04-18) explicitly notes "mitigation semantics" as a flagged
production oddity (line 108) but left it as a "separate follow-up". It was not
deemed a bug. A3 review report (`research/retest_geometry/A3_review_report.md:12`)
mentions mitigation semantics in the context of a look-ahead backtest bug in a
RESEARCH script, not the production code.

No ADR mandates changing `_count_touches` or OB mitigation semantics. The touch-
count gate was shipped in `1a22d92e` (2026-04-17) WITH the current semantics
baked in. The comment block at `market_state.py:466-481` explicitly documents
"Starts at formation_index + 1 (formation candle itself is EXCLUDED)" as INTENDED.
