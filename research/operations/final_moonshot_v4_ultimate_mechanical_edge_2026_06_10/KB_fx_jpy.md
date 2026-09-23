# KB: FX / JPY conditional sleeves done right

Track: FX/JPY conditional sleeves. Builder pass 2026-06-15. Probes `_fxjpy_probe1..12`.
Doctrine: build & improve, no kill verdicts; per-YEAR / per-REGIME never averages-as-verdict;
no lookahead; forward holdout mandatory; size by confidence, delete nothing.

Baseline to beat/extend: commodity FVG continuation + ac60>=0.10 gate = +0.865R fwd, 78% win.
Cost model: w1.cost_for(JPY pairs)=0.1148R/trade (large relative to FX H4 drift — this is
the single most important fact for FX).

---

## DELIVERED RULE (best forward-validated FX/JPY conditional)

### R1 — JPY London-open momentum continuation (M15)  [improvement, small/confidence-weighted size]

**Rule (exact):**
- Symbols: **GBPJPY, USDJPY** (the high-vol JPY majors).
- Timeframe: **M15**. Server time (MT5 export; NY vol peaks 16:00 server, so London ~08:00 server).
- Trigger: at the **first M15 bar of the London session at/after server-hour 8**, define the
  **1-hour opening impulse** = close of the 4th London M15 bar (`iw`) minus open of the 1st London
  M15 bar (`i0`). Direction `d = sign(impulse)`.
- Entry: at the **close of bar `iw`** (i.e. once the first London hour is closed), in direction `d`.
- Geometry: **stop = 1.0 * ATR14(M15, iw)**, **target = 2.5 * ATR14(M15, iw)**, time-stop maxbars=48 (12h).
- One trade per symbol per day. Cost = w1.cost_for (0.1148R), winsorize net R to [-1.3,+5].

**Forward result (M15 data window 2025-06-02 .. 2026-06-10 — see CAVEAT, this IS forward holdout):**
- Combined GBPJPY+USDJPY: **+0.168R/trade, n=530 (~490 trades/yr), 36.8% win.**
- Per CALENDAR YEAR: 2025 **+0.179R** (n=304), 2026 **+0.152R** (n=226). Both years positive.
- Per SYMBOL: GBPJPY **+0.219R** (n=265, 38.1% win), USDJPY **+0.116R** (n=265, 35.5% win).
- Per MONTH stability: **12 of 13 months positive** (the strongest robustness signal available
  with no train window). Negative months were chop (2025-08, -0.14R).
- Net **+88.8R over 530 trades** in the one forward year.

**Why it works / regime:** JPY crosses show genuine *intraday directional persistence* off the
London open that the H4 grid cannot see (the whole move is inside one H4 bar). It is JPY-SPECIFIC:
the identical setup on PURE FX (AUDUSD/EURUSD/GBPUSD/...) is **-0.17R** — a clean falsification
control. It concentrates in the high-vol majors (GBPJPY/USDJPY); AUDJPY/EURJPY were ~flat-to-neg.
Wider target (t2.5/t3.0) beats t1.5/t2.0 because the win rate is low (~37%) and the edge is in the
right tail (riding the London trend day), not hit-rate. **Trailing stops HURT** (-0.11 to -0.17R):
they give back the trail gap; a fixed wide target captures the tail better here.

**CAVEAT (honest):** M15 FX data only exists 2025-06..2026-06 in this repo (one forward year,
no train window). So this is forward-but-single-window — confound risk that 2025-26 was an
unusually trendy JPY regime (USDJPY/GBPJPY had large directional swings on BoJ/rate divergence).
Mitigation evidence that it is NOT one-regime luck: (a) positive in BOTH calendar years,
(b) 12/13 months positive, (c) clean PURE-FX falsification control, (d) per-symbol consistency.
Recommendation: **deploy at small confidence-weighted size** (breadth sleeve), re-validate the
moment older M15 history is exported. trades/yr ~490 — high frequency, good breadth contribution.

**Sizing/optionality (kept, smaller size):**
- Trend-gated variant (only ride impulses aligned with M15 trend over 20 bars): +0.158R, n=337,
  9/13 months+ — slightly higher per-trade but lower breadth/consistency. Use as a high-conviction
  sub-sleeve if size-constrained.
- Adding CHFJPY (G+U+CHF, trend-gated): +0.142R n=506 — keeps breadth, CHFJPY ~flat so dilutive.

---

## LEARNINGS (where it did NOT work, and what the trades taught us) — nothing deleted

### L1 — Naive H4 session-of-day continuation/reversion is uniformly NEGATIVE (probe1,2).
Every hour {0,4,8,12,16,20}, both cont and rev, FX: TRAIN/FWD all between -0.10 and -0.23R.
Lesson: H4 entry-at-close with no structure is pure cost bleed; the bar already contains the move.
Session edges need INTRADAY resolution (-> R1 on M15). H4 is the wrong tool for session timing.

### L2 — FX reversion is dead, even regime-filtered (probe2,3 + prior hunt_reversion_regime_filtered).
Fading extremes (|z|>=2, RSI confirm) forward = -0.25R FX / -0.115R jpy_fx. Pullback-into-extreme
entries (catching the knife) = -0.15 to -0.22R. Adding range/low-ADX filters makes it WORSE: in the
tightest ranges a 2-sigma move is disproportionately a real breakout that the stop catches. The
"reversion done right needs a range filter" thesis is falsified on this data. CONFIRMED-reversion
(bar i extended, bar i+1 closes back through midpoint) with WIDE target turned marginally forward-+
only at tiny sample (n=17-77) with noisy train (year R from -0.66 to +0.12) — not robust.
Lesson: in FX, what looks like a fadeable extreme is more often the start of a trend leg.

### L3 — The metals FVG-continuation mechanic FAILS on FX, and the ac60 gate INVERTS (probe4).
FVG-retest continuation + scale-out exit: FX ac>=-1 fwd -0.275R; **adding ac60>=0.10 makes it
WORSE** (FX -0.39R, JPY -0.70R). This is the decisive cross-asset learning: the persistence-regime
gate is asset-class-specific. High ac60 in metals = trend continues; high ac60 in FX = the FVG
retest is catching exhaustion. FX momentum does not persist like commodity momentum.
Mean ac60: JPY -0.017, PURE FX -0.020 (vs commodities positive) — FX is structurally more random.

### L4 — JPY day-of-week / carry drift is REAL but sub-cost as an every-bar entry (probe5b,9,10).
Raw H4 mean bar return (ATR units): JPY Mon +0.042, Tue +0.017, Wed +0.030, Thu/Fri -0.009;
PURE FX much weaker. Early-week long bias is real (risk-on/carry roll). BUT traded as a full
ATR-stop long on every early-week bar it is -0.03 to -0.10R: the 0.04-ATR drift cannot overcome
0.1148R cost + ATR-stop variance. Making it SELECTIVE (carry-long pullback-resumption in uptrend
on Mon-Wed) gives a TRAIN-positive (+0.023R lb40) that COLLAPSES forward to -0.318R — classic
non-stationary threshold-on-train failure (2025 was -0.29R, opposite of train). EURJPY was the only
fwd-positive symbol but n=25 (noise). Lesson: DOW is a tilt, not a standalone trigger; would only
be usable as a small directional FILTER on top of an already-positive entry (e.g. bias R1 longs
slightly on Mon-Wed) — left as future work.

### L5 — Asian-range breakout on H4 is dead; on M15 it is also negative (probe7,11).
H4 "London bar breaks Asian range" = -0.10 to -0.27R (H4 too coarse — breakout is inside the bar).
On M15 (proper resolution) the first-London-breakout-of-Asian-range is still negative
(JPY best -0.05R, FX -0.12R). The Asian range is too well-defended; the directional edge is in the
IMPULSE (R1), not in the level break. Lesson: trade the momentum, not the level, at the London open.

### L6 — HTF trend-following & trend-pullback-resumption on FX/JPY do not survive forward (probe4,8).
Plain HTF-trend continuation (metals 0.5/2.0 geometry) FX/JPY: -0.06 to -0.17R. Trend-pullback
resumption: TRAIN ~-0.08 to -0.11R, FWD -0.18 to -0.42R (gets worse forward). Lesson: FX trends are
too whippy on H4 for mechanical trend-follow; the edge needs the intraday session anchor (R1).

---

## NEXT STEPS
1. Export older FX M15/M1 history (pre-2025) to convert R1 from forward-only-window to true
   train/forward holdout. This is the single highest-value data ask for FX.
2. Stack the L4 DOW tilt onto R1 (bias/size London longs up Mon-Wed) and measure month-consistency.
3. Test R1 on the NY open (server ~12:00-16:00) for a second daily JPY session entry (breadth).
4. M1 (2024-01..2026-06) gives a partial train window for R1 — re-run R1 logic on M1-aggregated-to-M15
   to get a 2024 holdout slice.

## FILES
- Probes: `_fxjpy_harness.py`, `_fxjpy_probe1..10.py` (H4), `_fxjpy_probe11_m15.py`,
  `_fxjpy_probe12_m15refine.py` (M15 — R1 lives here).
- Confirmed baseline comparator: KB_commodity_regime.md / KB_commodity_setups.md.
