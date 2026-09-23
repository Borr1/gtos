# KB: Hidden Conditional Edges in the "Dead-on-Average" Classes
Route: final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
Classes investigated: fx, jpy_fx, index, crypto. H4 bars, 2015-2026. Leak-free `geometry_lib.simulate`.
Doctrine: pick on TRAIN (entry yr<=2024), report SAME rule on 2025 & 2026 separately + per-year + per-symbol.
Winsorize R to [-1.3,+5]. Real per-class cost (fx .160, jpy_fx .115, index .064, crypto .095 global-median).
HOLDS gate = TRAIN R>0 AND 2025 R>0 AND 2026 R>0.

## 0. HARNESS VALIDATION (control — proves the rig finds edge where it exists)
Same engine, same cost/sign convention, on metals continuation (stretch>=1ATR bar -> enter dir, stop1ATR tgt1.5R):
  XAGUSD CONT: TRAIN +0.031 | 2025 +0.153(n123) | 2026 +0.091(n77)  -> HOLDS (genuine trend edge)
  XAUUSD CONT: TRAIN -0.077 | 2025 +0.182 | 2026 +0.242
  USOIL  CONT: TRAIN -0.010 | 2025 +0.092 | 2026 -0.161
Metals/energy trend on H4; the rig confirms it. The negatives below on fx/jpy/index/crypto are therefore
real anti-edges, not a broken harness or sign bug.

## 1. DATA REALITY (binding constraint on what "forward holdout" can even mean)
Only fx + jpy_fx have deep train history. Most index/crypto symbols are 2025-2026 ONLY (no train):
  fx train-deep: EURUSD(15.5k), GBPUSD(10.4k), USDCHF(10.4k), AUDUSD(6.2k), USDCAD/NZDUSD/EURGBP(4-5k).
  jpy_fx train-deep: USDJPY(13.9k), AUDJPY(7k), CHFJPY(6.2k), EURJPY(4k), GBPJPY(2.4k).
  index train-deep: NAS100 only (4628, from 2022). EU50/FRA40/N25 thin (~1.2k from 2024).
                    GER40, JP225, US30, UK100, SPX500, AUS200, DXY = 2025-2026 ONLY (zero train).
  crypto train-deep: XTZUSD(2976). BTC/ADA/DASH small 2024 train. DOT/LTC/ETH = no train.
=> For index/crypto, "TRAIN<=2024" is mostly NAS100/XTZUSD + a little EU50/N25. Any index/crypto
   "forward positive" with no train is a single-regime confound by construction. Treated as such below.

## 2. UNDERSTANDING PER CLASS (what is actually true, with reasoning)

### fx (EURUSD,GBPUSD,AUDUSD,NZDUSD,USDCAD,USDCHF,EURGBP,USDSGD,USDCNH)
- Both directions lose on H4 with any fixed geometry. Continuation TRAIN ~ -0.18 every year; fade
  TRAIN ~ -0.17 every year; both forward ~ -0.10 to -0.23. NOT a regime thing — uniformly negative
  across ALL 11 years. WHY: H4 FX majors are close to a random walk net of the ~0.16R round-trip cost;
  no persistent body-momentum or body-reversion at 4h. London/NY/Asia slicing, DOW slicing, vol-regime
  slicing, exhaustion(2-3 consec bars), low-vol range-fade — all stay negative on TRAIN. The cost is the
  killer: at ~50% win a 1R target needs >0.58 hit rate just to break even; FX delivers ~0.49.
- HONEST VERDICT fx: NO conditional edge found in any session/DOW/vol/structure/geometry tested. The
  highest-cost class; the bar is highest and it clears none of it.

### jpy_fx (USDJPY,EURJPY,GBPJPY,AUDJPY,CHFJPY)
- Slightly less negative than fx (cost .115). Continuation TRAIN ~ -0.10, fade TRAIN ~ -0.16; forward
  bounces around zero in 2025 for a few cuts (jpy fade London 2025 +0.01, NY 2025 -0.02) but TRAIN is
  negative on those same cuts, and 2026 craters (-0.27 to -0.32). WHY the 2025 wobble: 2025 had two-sided
  JPY intervention/carry chop that briefly rewarded fades; 2026 (BoJ normalization trend) punished them.
  No cut is positive on TRAIN.
- HONEST VERDICT jpy_fx: NO stable conditional edge. The 2025-only fade positives are regime noise that
  reverse in 2026 — exactly the forward-only confound to distrust.

### index (NAS100,SPX500,GER40,US30,UK100,JP225,EU50,FRA40,N25,US2000,AUS200,DXY)
- The LEAST-dead class and the most interesting story, but still no deployable edge under doctrine.
- Continuation is an anti-edge (TRAIN -0.06, gets worse forward). Indices do NOT trend-continue on H4.
- Fade/mean-reversion is where the structure lives: win rates run 54-62% on low-vol prior-day-extreme
  fades (range days revert to mid — real microstructure). BUT the geometry can't monetize it: tight
  scalp target + cost turns 60% win into negative R. Low-vol PD-fade by symbol: EU50 +0.016(w62%),
  FRA40 -0.017(w60%), N25 0.000(w61%), AUS200 -0.003(w60%) — clustered at breakeven, not above cost.
- THE BIG TRAP (documented so we don't deploy it): index EXHAUSTION-FADE (after 2 consecutive same-dir
  bars with cumulative move>=2ATR, fade next bar, stop1.5ATR tgt1R) reads:
      2022 -0.206(n74) | 2023 -0.225(n70) | 2024 -0.212(n217) | 2025 +0.030(n470) | 2026 +0.092(n335)
  Every TRAIN year negative, both FORWARD years positive. This is a clean REGIME FLIP, not an edge:
  2022-24 = relentless index bull (fading exhaustion got run over); 2025-26 = choppier/mean-reverting
  regime. FAILS the train gate. DO NOT TRADE on the forward numbers — single-regime confound.

### crypto (BTC,ETH,ADA,DOT,LTC,DASH,XTZ)
- Train is mostly XTZUSD (only deep-history crypto). Both directions negative on the little train there is
  (XTZ cont/fade TRAIN -0.06 to -0.19). Forward is a grab-bag of single-regime positives with no train
  anchor (crypto Mon-fade 2025 +0.04 / 2026 +0.06 but TRAIN -0.28; crypto London08 breakout TRAIN +0.03
  but forward negative). WHY: crypto H4 is high-vol, fat-tailed, and the available history is one regime;
  nothing is verifiable as a train->forward edge with this data.
- HONEST VERDICT crypto: insufficient train history to certify ANY rule. All forward positives are
  single-regime. Not "dead" — UNTESTABLE on holdout with current data.

## 3. THE RULE(S) THAT HOLD FORWARD
NONE. Across the full investigation (details in §5), ZERO conditions cleared the gate
(TRAIN R>0 AND 2025 R>0 AND 2026 R>0) in fx / jpy_fx / index / crypto. Every candidate that was
forward-positive was TRAIN-negative (regime confound); every candidate that was TRAIN-positive went
forward-negative (overfit). This is reported honestly, not as a global average — it is conditional-by-
conditional and it fails conditionally.

The ONE quasi-positive but REJECTED thread (logged for monitoring, NOT for deployment):
  INDEX exhaustion-fade — positive 2025+2026, negative every train year. Reason for rejection: regime
  flip (2022-24 bull -> 2025-26 chop). If index character STAYS mean-reverting, revisit; treat as a
  regime hypothesis, not an edge.

## 4. WHAT WAS TESTED AND HONESTLY DOES NOT HOLD (so we don't retread)
All with leak-free entry at i+1 open, winsorized, real cost, train/2025/2026 split:
- [no edge] Stretch-bar CONTINUATION (body>=1.0/1.5 ATR), all 4 classes, stop1ATR tgt1R, all sessions.
- [no edge] Stretch-bar FADE (reversion), all 4 classes, all sessions.
- [no edge] Conditional slices: SESSION (Asia/London/NY) x VOL-REGIME (lo/mid/hi tercile, leak-free
  100-bar ATR percentile) x DAY-OF-WEEK (Mon-Fri), fade & cont, all 4 classes. ~120 cells, 0 hold.
- [no edge] Geometry sweep: fade stretch_k{0.8,1.2} x stop{1.0,1.5,2.0}ATR x tgt{0.5,0.75,1.0}ATR x
  maxbars12. 0 cells hold any class.
- [no edge] Pullback-CONTINUATION in HTF trend (30/40-bar trend, pullback bar 0.5/0.8ATR, stop1-1.5,
  tgt1.5/2.5R, maxbars40), all 4 classes. Strongly negative (fx/jpy TRAIN -0.10 to -0.20).
- [no edge] Structural SWEEP-RECLAIM FADE at prior-day & prior-session extremes (ICT liquidity grab),
  tgt 0.75/1.0/1.5R, all 4 classes.
- [no edge] SESSION-OPEN BREAKOUT continuation (first London/NY/Asia bar breaking prior-session range),
  tgt 1.0/1.5/2.5R, all 4 classes, all open hours.
- [no edge] Per-symbol momentum-continuation w/ TRAILING RUNNER, trend-aligned (let winners run) —
  uniformly NEGATIVE per symbol (trail gap bleeds, markets whipsaw). Worst performer of all.
- [no edge] Per-symbol FADE w/ trailing runner.
- [no edge] EXHAUSTION FADE (2-3 consec same-dir bars, cumulative 1.5/2.0/2.5 ATR, +/- low-vol filter),
  fx/jpy/crypto all negative train+forward; index = regime flip only (rejected, §2/§3).
- [no edge] LOW-VOL PRIOR-DAY EXTREME FADE (range-day reversion, scalp target). High win rate (54-62%)
  but negative R after cost in all 4 classes — geometry cannot monetize the hit rate.
Framing: this is "no edge found in conditions X" with the conditions enumerated — not "the class is dead."
The microstructure (index range-day reversion, jpy carry-chop) is real; it is just not monetizable at H4
with fixed structural geometry net of the route's real costs.

## 5. NEXT THREADS WORTH PURSUING (highest EV first)
1. INDEX REGIME-GATED REVERSION (most promising real lead). The index exhaustion/range fade is genuinely
   mean-reverting IN the 2025-26 regime. Build a LEAK-FREE regime classifier (e.g. rolling realized-vol
   of vol, or trend-strength of the index ITSELF over trailing 60-120 bars) and only fade when the index
   is in a "choppy/range" state. Test whether the 2022-24 losses were ALL in the classifier's "trend"
   state — if so the rule survives on train *conditioned on regime* and becomes deployable. This is the
   one place the average truly hides a pocket.
2. SUB-H4 timing on index reversion. The 54-62% win rate exists but H4 geometry wastes it. Re-test the
   low-vol PD-extreme fade on M15/M1 (route has microstructure engines + native ledgers) with a tighter
   structural stop — the hit rate may clear cost at finer granularity where target/stop ratio improves.
3. CROSS-SECTIONAL index reversion (pairs/dispersion): long the most-oversold index vs short the most-
   overbought same-session (EU50 vs GER40 vs FRA40 are highly correlated). Dollar-neutral strips the
   beta/regime confound that killed the directional fade — the relative reversion may be train-stable.
4. CARRY/overnight for jpy_fx specifically (held positions, not H4 bar signals) — bar-signal momentum is
   dead but the carry term is structural; route already has wave7_carry_overnight, extend it.
5. DO NOT re-run: any fixed-geometry directional H4 bar signal on fx/jpy/index/crypto. Exhaustively
   falsified above. FX in particular is the highest-cost, lowest-signal class — deprioritize entirely.

## Artifacts produced this investigation
PROBE_REVERSION_SESSION.json, PROBE_CONDITIONAL_SLICES.json, PROBE_GEOMETRY_SWEEP.json,
PROBE_STRUCTURAL.json, PROBE_PERSYM_RUNNER.json, PROBE_FINAL_SELECTIVE.json
Code: dead_class_harness.py (+ probe_*.py) in route dir.
