# KB — State-Dependent Exits (trade management as a function of market state)

Investigator: quant / exits-as-state. Date 2026-06-14.
Entry set held FIXED: `gold_sleeve_strategy.fvg_signals` (vol-gated H4 FVG-retest continuation)
across the commodities+metals pocket where the entry edge lives:
`CORN_c, COTTON_c, HEATOIL_c, NATGAS_cash, UKOIL_cash, USOIL_cash, XAG{USD,EUR,AUD}, XAU{USD,EUR,AUD}, XCUUSD`.
n=910 entries (TRAIN<=2024 n=400; 2025 n=319; 2026 n=191). by class: metals 622 / energy 192 / agri 96.
Stop = structural (R-unit = stop_dist). Cost = `w1.cost_for(sym)` scaled by stop tightness
(`base * 0.5*ATR/stop_dist`; median 0.021R — structural stops here are WIDER than the 0.5ATR
reference, so R-cost is small). Net R winsorized to [-1.3,+5]. maxbars=80.
All exit sims run on a per-bar engine that is PARITY-PROVEN against `geometry_lib.simulate`
for fixed-target full-position (910/910 trades, maxdiff 0.0). Pessimistic same-bar: stop wins ties.

---

## 1. UNDERSTANDING — where price actually goes after entry, by regime

Forward-path stats (R-units, R=stop_dist), all entries:
- **MFE** median 3.74R (p25 1.52 / p75 7.89 / p90 14.9). **MAE** median 2.71R (p25 1.15 / p75 5.06).
- MFE>=1R reached by 83% (median 6 bars), >=1.5R by 75% (9 bars), >=2R by 68% (12 bars).
- NOTE: this is the OPPOSITE pocket from the prior exit-oracle note (which had MFE~0.66R and said
  2R overshoots). Here the structural stop is wide and these are strong-continuation trades, so MFE
  in R-units is LARGE and fixed-2R is too TIGHT for the runners. The "median +0.49–0.72R left on
  the table vs 2R" finding does NOT transfer to this entry/stop construction — verified, not assumed.

**Give-back problem (the real leak):** of the 621 trades that reach >=2R MFE, the pessimistic 2R
target only BOOKS the win on 57% — the other 43% peak >=2R then revert through the stop on a later
(or same, wide) bar. Identical 57% at MFE>=3R and >=4R. So price routinely visits profit it never pays.

**Vol regime is the dominant state variable** (volrat = ATR14 / SMA100(ATR14); gate already requires >=1.2):
| volrat | n | MFE_med | MAE_med | term_med | reach2R | 2R per-trade R |
|---|---|---|---|---|---|---|
| 1.2–1.35 (LOW) | 407 | 4.33R | 2.85R | +0.77R | 75% | +0.302 |
| 1.35–1.6 (MID) | 315 | 3.51R | 2.70R | +0.07R | 65% | +0.095 |
| 1.6–2.0 (HI)   | 103 | 2.46R | 2.53R | -0.43R | 56% | +0.160 |
| 2.0+ (XHI)     | 85  | 2.98R | 2.86R | -0.34R | 64% | +0.271 |
- LOW-vol entries develop the **biggest, slowest trends** (MFE 4.3R, terminal still +0.77R) → want
  DEEP targets + room to run. HI-vol entries **pop-or-revert** (MFE 2.5R, terminal NEGATIVE) → want
  a QUICKER target and an early bail.
- Trend-alignment (signed 30-bar move/ATR) does NOT discriminate: 836/910 entries are already
  "strong-trend" because the gate+HTF-trend filter pre-selects them. Vol is the live lever, not trend.

**Early-progress is the single most predictive no-lookahead signal** (uses only MFE-so-far + bars):
| signal | n | 2R per-trade R | win% |
|---|---|---|---|
| reached +1R MFE by bar 3 | 281 | **+1.093** | 70% |
| did NOT reach +1R by bar 3 | 629 | **-0.183** | 28% |
| reached +1R by bar 5 | 375 | +1.008 | 67% |
| not by bar 5 | 535 | -0.347 | 22% |
A trade that hasn't moved in your favour fast is, with high probability, dead.

**Why fixed-2R is wrong here:** it is simultaneously (a) too tight for LOW-vol runners (caps a 4R+
move at 2R) and (b) too loose for HI-vol pops that never get there and revert to -1R; and (c) it
banks NOTHING on the 43% of trades that touch 2R+ then give it all back.

---

## 2. THE EXIT POLICY (state-dependent; thresholds from TRAIN only)

Two deliverables — a primary (max R) and a conservative (max FTMO-safety). Both are **scale-out +
deep runner**, tiered by entry vol. Mechanics: at entry, place structural 1R stop. Scale 50% off at
the first leg target; move runner stop to break-even (BE); let runner go to a deep fixed target.
No trailing (trailing was tested and DESTROYS this edge — see §4).

**PRIMARY — `STATE_D`** (best R, still cuts DD in half):
```
volrat < 1.35 (LOW): scale 50% @ +1.5R, BE on runner, runner target +4.0R
1.35–1.60   (MID): scale 50% @ +1.5R, BE on runner, runner target +3.0R
volrat >= 1.60 (HI): scale 50% @ +1.0R, BE on runner, runner target +2.5R
```

**CONSERVATIVE — `STATE_D_cons`** (best FTMO profile, highest win rate, lowest variance):
```
LOW: scale 50% @ +1.0R, BE, runner +3.0R
MID: scale 50% @ +1.0R, BE, runner +2.5R
HI : scale 50% @ +1.0R, BE, runner +2.0R
```

Rule uses ONLY entry-state volrat (known at entry) + running MFE/MAE/bar-count during the trade.
No future bars. Thresholds (1.35/1.60 vol cuts, scale & runner levels) fixed on TRAIN<=2024 and
applied unchanged to 2025/2026.

---

## 3. NUMBERS — fixed-2R baseline vs state-dependent (SAME 910 entries)

Per-trade R / win% / per-trade std / worst-trade. Winsorized [-1.3,+5].

| policy | TRAIN R (w%) | 2025 R (w%) | 2026 R (w%) | ALL R (w%) | ALL std | worst |
|---|---|---|---|---|---|---|
| **fixed_2R (baseline)** | +0.0757 (37.5) | +0.1511 (39.2) | +0.4740 (49.7) | +0.1858 (40.7) | 1.45 | -1.13 |
| **STATE_D (primary)** | **+0.1763 (47.8)** | **+0.2587 (49.5)** | **+0.5656 (53.9)** | **+0.2869 (49.7)** | 1.44 | -1.13 |
| **STATE_D_cons** | +0.1672 (53.2) | +0.1983 (53.0) | +0.4924 (61.8) | +0.2464 (54.9) | **1.24** | -1.13 |

Total R (ALL): baseline +169R → STATE_D **+261R** (+54%) → STATE_D_cons +224R (+33%).
**Paired uplift STATE_D vs 2R: +0.101R/trade, t≈4.56 (n=910).** D_cons: +0.061R/trade, t≈2.76.
STATE_D beats baseline in EVERY partition (train, 2025, 2026) — clean forward holdout.

Per-year per-trade R (n):
- 2R:   15:-0.33 16:-0.01 17:+0.75 18:+0.78 19:-0.12 20:+0.15 21:-0.09 22:+0.06 23:-0.20 24:+0.18 25:+0.15 26:+0.47 → **7/12 positive years**
- D:    15:-0.16 16:+0.05 17:+1.03 18:+0.62 19:-0.03 20:+0.32 21:+0.04 22:+0.30 23:-0.13 24:+0.20 25:+0.26 26:+0.57 → **9/12 positive** (only 2015 n13, 2019 n46, 2023 n29 negative — all small-n train)
- Dc:   15:-0.11 16:+0.15 17:+0.67 18:+0.64 19:+0.03 20:+0.25 21:+0.05 22:+0.24 23:-0.05 24:+0.20 25:+0.20 26:+0.49 → **10/12 positive**

**Variance / drawdown (correlated-risk-unit equity, same model as `gold_sleeve_strategy.backtest`):**
| policy | maxDD @0.25% risk | maxDD @1% risk | full-loss freq (R<=-0.9) |
|---|---|---|---|
| fixed_2R | 7.31% | 26.89% | 57.6% |
| STATE_D | **3.64%** | **13.89%** | 49.6% |
| STATE_D_cons | **3.24%** | **12.74%** | 49.6% |

Worst-day % identical across policies (-0.275% @0.25%) — the worst single cluster is a stop day
either way; the policies don't worsen tail-day risk, they cut DRAWDOWN by halving it.

R-distribution (why DD drops): D median R = **-0.207** vs 2R median **-1.012** — the scale-out
converts a large mass of full-loss trades into partial-win/scratch (banks 0.5–0.75R before the
runner fails). p95: D 2.73R vs 2R 1.99R (D also captures deeper runners). So D is *both* higher
mean *and* lower variance — strictly better for FTMO.

Per-class FORWARD (>=2025), D vs 2R: metals +0.385 (w51%) vs +0.226 (w41%); energy +0.424 vs +0.382;
agri +0.234 (w48%) vs +0.291 (n69, the only class D slightly trails — tiny sample). Metals (the
dominant sleeve) benefits most.

---

## 4. CAVEATS

- **TRAILING and partial-then-trail are NEGATIVE on this entry** (verified): pure-trail arm1.0/gap1.0
  = -0.21R; partial@2R+BE+trail = -0.20R. The structural stop is wide and these are slow continuations;
  any chandelier/BE-then-trail gets shaken out on normal noise (median MAE 2.71R) before the move
  develops. The winning structure is scale-out + BE + DEEP FIXED runner target. Do not "improve" D by
  adding a trail.
- **Same-bar optimism risk is bounded.** Engine is pessimistic (stop before fav each bar). A
  maximally-harsh stress where the runner dies at BE on ANY return to entry still gives D train
  +0.117 (vs baseline +0.076) and ALL +0.191 (vs +0.186) at win 49.7%. The realistic D sits between
  this floor and the engine number; the win-rate gain is real (banked scale leg), not a fill artifact.
- **Threshold-robust:** sweeping vol cuts over (1.30/1.55)…(1.45/1.70) keeps ALL R in +0.276…+0.314,
  all beating baseline in train and forward. Not knife-edge.
- **TRAIN is small (n=400) and noisy** — per-regime "optimal" static targets on train alone overfit
  (MID bucket is barely positive at any target). D deliberately uses a low-parameter monotone vol→depth
  mapping rather than the train-argmax, which is why it generalizes forward.
- **Forward has more entries than train** (510 fwd vs 400 train) and is metals-heavy; the edge is
  concentrated in metals+energy. Agri is too thin to trust per-class.
- Costs are scaled-from-fill medians, not live spreads; metals R-cost is tiny here (~0.02R) so cost
  is not driving the ranking. Slippage on the deeper runner target is not separately modeled.
- This is exit-only research on a held-fixed entry; it does not change live wiring. R-unit absolute
  size is small per the gold-sleeve sizing study (FTMO-safe ~0.02–0.06%/mo); D improves the *shape*.

---

## 5. NEXT

1. Wire `STATE_D` / `STATE_D_cons` as the default exit manager for the gold/commodity sleeve
   (replace flat 2R in `gold_sleeve_strategy`) — the scale-out is implementable with one partial fill
   + BE move + deep limit; no intrabar trailing needed.
2. Add the **early-progress time-stop as a HI-vol-only overlay** (bar5 < +1R → exit at close): it was
   train-positive on HI-vol and neutral elsewhere; quantify on live-realistic fills before adding to
   LOW/MID (it cuts LOW-vol slow winners — do NOT apply universally).
3. Re-run D on the BROADER entry set (sweep/reclaim setup_A2, and the universe-wide FVG) to test
   whether vol→depth + scale-out transfers beyond the commodity pocket — exits lift every sleeve.
4. Stress D under M1-intrabar realism (`study_m1_intrabar_realism.py`) to price the scale-leg fill and
   the runner-target slippage; confirm the +0.101R uplift survives realistic execution.
5. Monte-Carlo the D equity curve through the FTMO challenge gate (`challenge_montecarlo.py`) at the
   approved risk to confirm the halved maxDD translates to a higher challenge-pass probability.
